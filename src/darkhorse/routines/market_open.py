"""Market-open routine — production paper trading pipeline.

Phase 4a flow: compose risk state -> harness (researcher + risk-manager) ->
validate_order -> submit to Alpaca paper -> journal + audit + Discord notify.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

import httpx
import structlog

from darkhorse.audit import append_audit_record
from darkhorse.config import Settings, get_settings
from darkhorse.harness import (
    HarnessResult,
    RoutineCostCapExceeded,
    build_snapshot_summary,
    generate_decision_id,
    run_harness_session,
)
from darkhorse.idempotency import client_order_id_for_alpaca, intent_hash
from darkhorse.journal import append_jsonl_record
from darkhorse.notify import notify_discord_text
from darkhorse.risk import (
    OrderRequest,
    OrderType,
    Side,
    Sleeve,
    ValidationVerdict,
    validate_order,
)
from darkhorse.routines.composition import (
    AssetListLoader,
    RoutineCompositionConfig,
    RoutineCompositionSnapshot,
    compose_routine_snapshot,
)
from darkhorse.routines.envelopes import _short_git_sha
from darkhorse.schemas.audit import AuditLogRecordV1
from darkhorse.schemas.decision import (
    AlpacaOrderRecordV1,
    CostRecordV1,
    DecisionJournalRecordV1,
    ToolUseRecordV1,
)
from darkhorse.tools import BrokerEnvironment, utc_now
from darkhorse.tools._contracts import AlpacaSubmitOrderInput
from darkhorse.tools.alpaca import submit_order

logger = structlog.get_logger(__name__)

_CONFIDENCE_THRESHOLD: float = 0.70


# ---------------------------------------------------------------------------
# Dry-run snapshot (Phase 3 backward compat)
# ---------------------------------------------------------------------------


def run_market_open_snapshot(
    *,
    settings: Settings | None = None,
    client: httpx.Client | None = None,
    asset_loader: AssetListLoader | None = None,
) -> RoutineCompositionSnapshot:
    """Build the market-open risk snapshot in dry-run mode."""
    config = RoutineCompositionConfig(
        routine="market_open",
        environment=BrokerEnvironment.PAPER,
        dry_run=True,
    )
    if asset_loader is not None:
        return compose_routine_snapshot(
            config,
            settings=settings,
            client=client,
            asset_loader=asset_loader,
        )
    return compose_routine_snapshot(
        config,
        settings=settings,
        client=client,
    )


# ---------------------------------------------------------------------------
# Full production pipeline
# ---------------------------------------------------------------------------


def run_market_open(
    *,
    settings: Settings | None = None,
    broker_client: httpx.Client | None = None,
    anthropic_http_client: httpx.Client | None = None,
    asset_loader: AssetListLoader | None = None,
    dry_run: bool = False,
) -> DecisionJournalRecordV1 | None:
    """End-to-end market-open routine for paper trading.

    Returns the journal record, or None if composition blocks trading early
    (the NO_TRADE is already journaled by composition layer in that case).
    """
    active_settings = settings or get_settings()
    log = logger.bind(routine="market_open", sleeve="core")

    config = RoutineCompositionConfig(
        routine="market_open",
        sleeve="core",
        environment=BrokerEnvironment.PAPER,
        dry_run=dry_run,
        audit_dir=active_settings.journal_dir / "audit",
        journal_dir=active_settings.journal_dir / "core" / "journal",
    )

    log.info("market_open_start")

    if asset_loader is not None:
        snapshot = compose_routine_snapshot(
            config,
            settings=active_settings,
            client=broker_client,
            asset_loader=asset_loader,
        )
    else:
        snapshot = compose_routine_snapshot(
            config,
            settings=active_settings,
            client=broker_client,
        )

    trading_blocked = (
        not snapshot.kill_switch_trading_allowed
        or snapshot.account_trading_blocked
        or snapshot.core_drawdown_halt
        or snapshot.core_uncle_triggered
        or snapshot.satellite_uncle_triggered
    )

    if trading_blocked:
        log.info("market_open_blocked", reasons=snapshot.kill_switch_reasons)
        _notify_safe(
            active_settings,
            f"Core market_open: NO_TRADE — blocked ({', '.join(snapshot.kill_switch_reasons)})",
        )
        return None

    positions_list: list[dict[str, Any]] = []
    snapshot_summary = build_snapshot_summary(
        account_equity=snapshot.validation_context.account_equity_usd,
        buying_power=snapshot.validation_context.buying_power_usd or Decimal("0"),
        positions=positions_list,
        sleeve="core",
        core_nav=snapshot.validation_context.core_nav_usd,
        satellite_nav=snapshot.validation_context.satellite_nav_usd,
        kill_switch_ok=snapshot.kill_switch_trading_allowed,
        drawdown_halt=snapshot.core_drawdown_halt,
        deploy_cap=snapshot.validation_context.max_core_deploy_usd,
    )

    try:
        harness_result = run_harness_session(
            snapshot_summary=snapshot_summary,
            allowed_symbols=snapshot.validation_context.core_allowed_symbols,
            settings=active_settings,
            anthropic_http_client=anthropic_http_client,
            broker_http_client=broker_client,
        )
    except RoutineCostCapExceeded as exc:
        log.error("market_open_cost_cap_exceeded", error=str(exc))
        _notify_safe(active_settings, f"Core market_open: ABORTED — cost cap exceeded: {exc}")
        return None
    except Exception as exc:
        log.error("market_open_harness_error", error=str(exc))
        _notify_safe(active_settings, f"Core market_open: ERROR — {exc}")
        raise

    decision = harness_result.decision
    log.info(
        "market_open_decision",
        action=decision.action,
        ticker=decision.ticker,
        confidence=decision.confidence,
    )

    record = _build_journal_record(harness_result, snapshot, active_settings)

    if decision.action == "NO_TRADE":
        record = record.model_copy(update={"validate_order_passed": False})
        _journal_and_audit(record, config, active_settings)
        _notify_safe(
            active_settings,
            f"Core market_open: NO_TRADE — {decision.thesis_summary[:200]}",
        )
        return record

    if decision.confidence < _CONFIDENCE_THRESHOLD:
        record = record.model_copy(
            update={
                "validate_order_passed": False,
                "risk_checks": {
                    "reason": "confidence_below_threshold",
                    "confidence": decision.confidence,
                },
            }
        )
        _journal_and_audit(record, config, active_settings)
        _notify_safe(
            active_settings,
            f"Core market_open: NO_TRADE — confidence {decision.confidence:.2f} "
            f"below {_CONFIDENCE_THRESHOLD}",
        )
        return record

    order, validation_ctx_updates = _build_order_from_decision(
        decision=harness_result.decision,
        snapshot=snapshot,
    )
    if order is None:
        record = record.model_copy(
            update={
                "validate_order_passed": False,
                "risk_checks": {"reason": "invalid_decision_fields"},
            }
        )
        _journal_and_audit(record, config, active_settings)
        _notify_safe(active_settings, "Core market_open: NO_TRADE — invalid decision fields")
        return record

    validation_result = validate_order(order, snapshot.validation_context)

    if validation_result.verdict is not ValidationVerdict.PASS:
        record = record.model_copy(
            update={
                "validate_order_passed": False,
                "risk_checks": {
                    "verdict": validation_result.verdict.value,
                    "rule_id": validation_result.rule_id,
                    "message": validation_result.message,
                },
            }
        )
        log.info(
            "market_open_validation_rejected",
            rule_id=validation_result.rule_id,
            message=validation_result.message,
        )
        _journal_and_audit(record, config, active_settings)
        _notify_safe(
            active_settings,
            f"Core market_open: REJECTED by {validation_result.rule_id} — "
            f"{validation_result.message}",
        )
        return record

    intent_fp = record.intent_fingerprint
    coid = client_order_id_for_alpaca(
        routine="market_open",
        trade_date=utc_now().strftime("%Y-%m-%d"),
        sleeve="core",
        symbol=order.symbol,
        intent_hash_hex=intent_fp,
    )

    submit_payload = AlpacaSubmitOrderInput(
        environment=BrokerEnvironment.PAPER,
        order=order,
        validation_context=snapshot.validation_context,
        client_order_id=coid,
        dry_run=dry_run,
    )
    submit_result = submit_order(submit_payload, settings=active_settings, client=broker_client)

    alpaca_record = AlpacaOrderRecordV1(
        client_order_id=submit_result.client_order_id,
        broker_order_id=submit_result.broker_order_id,
        submitted_at=(
            submit_result.submitted_at.isoformat() if submit_result.submitted_at else None
        ),
        fill_status=submit_result.status,
    )
    record = record.model_copy(
        update={
            "validate_order_passed": submit_result.submitted
            or submit_result.validation.verdict is ValidationVerdict.PASS,
            "alpaca": alpaca_record,
            "risk_checks": {
                "verdict": submit_result.validation.verdict.value,
                "rule_id": submit_result.validation.rule_id,
                "message": submit_result.validation.message,
            },
        }
    )
    _journal_and_audit(record, config, active_settings)

    status = "SUBMITTED" if submit_result.submitted else "DRY_RUN"
    _notify_safe(
        active_settings,
        f"Core market_open: {decision.action} {decision.ticker} x{decision.qty} — "
        f"{status} — {decision.thesis_summary[:150]}",
    )
    log.info(
        "market_open_complete",
        action=decision.action,
        ticker=decision.ticker,
        submitted=submit_result.submitted,
        cost_usd=str(harness_result.total_cost.usd),
    )
    return record


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_journal_record(
    result: HarnessResult,
    snapshot: RoutineCompositionSnapshot,
    settings: Settings,
) -> DecisionJournalRecordV1:
    """Map harness result into a journal record (pre-validation/submission)."""
    decision = result.decision
    git_sha = _short_git_sha()
    decision_id = generate_decision_id()

    tools_used = tuple(
        ToolUseRecordV1(tool=t["tool"], args=t.get("args", {})) for t in result.tools_used
    )
    cost = CostRecordV1(
        input_tokens=result.total_cost.input_tokens,
        cached_input_tokens=result.total_cost.cache_read_input_tokens,
        output_tokens=result.total_cost.output_tokens,
        total_usd=str(result.total_cost.usd),
    )

    payload_for_hash: dict[str, Any] = {
        "schema_version": "1.0",
        "sleeve": snapshot.sleeve,
        "routine": snapshot.routine,
        "action": decision.action,
        "ticker": decision.ticker,
        "qty": str(decision.qty) if decision.qty else None,
        "order_type": decision.order_type,
        "limit_price": decision.limit_price,
        "confidence": decision.confidence,
        "thesis_summary": decision.thesis_summary,
        "doctrine_version": git_sha,
        "prompt_version": git_sha,
    }
    fingerprint = intent_hash(payload_for_hash)

    return DecisionJournalRecordV1(
        schema_version="1.0",
        decision_id=decision_id,
        timestamp=utc_now().isoformat().replace("+00:00", "Z"),
        sleeve=snapshot.sleeve,  # type: ignore[arg-type]
        routine=snapshot.routine,
        doctrine_version=git_sha,
        prompt_version=git_sha,
        model_assignments=result.model_assignments,
        ticker=decision.ticker,
        action=decision.action,
        qty=str(decision.qty) if decision.qty else None,
        order_type=decision.order_type,
        limit_price=decision.limit_price,
        time_in_force=decision.time_in_force,
        confidence=decision.confidence,
        expected_horizon_days=decision.expected_horizon_days,
        expected_outcome_pct=decision.expected_outcome_pct,
        thesis_summary=decision.thesis_summary,
        reasoning_trace=decision.reasoning_trace,
        tools_used=tools_used,
        intent_fingerprint=fingerprint,
        validate_order_passed=False,
        risk_checks={},
        lessons_referenced=tuple(decision.lessons_referenced),
        anti_patterns_flagged=tuple(decision.anti_patterns_flagged),
        cost=cost,
    )


def _build_order_from_decision(
    *,
    decision: Any,
    snapshot: RoutineCompositionSnapshot,
) -> tuple[OrderRequest | None, dict[str, Any]]:
    """Convert LLM decision to an OrderRequest. Returns (order, ctx_updates) or (None, {})."""
    if decision.ticker is None or decision.qty is None or decision.order_type is None:
        return None, {}

    try:
        side = Side(decision.action.lower())
    except ValueError:
        return None, {}

    try:
        order_type = OrderType(decision.order_type)
    except ValueError:
        return None, {}

    limit_price = Decimal(decision.limit_price) if decision.limit_price else None
    estimated_notional = Decimal(str(decision.qty)) * (limit_price if limit_price else Decimal("0"))

    return OrderRequest(
        sleeve=Sleeve.CORE,
        symbol=decision.ticker.upper(),
        side=side,
        order_type=order_type,
        qty=decision.qty,
        limit_price=limit_price,
        estimated_notional_usd=max(estimated_notional, Decimal("0.01")),
        market_order_exception=decision.market_order_exception,
    ), {}


def _journal_and_audit(
    record: DecisionJournalRecordV1,
    config: RoutineCompositionConfig,
    settings: Settings,
) -> None:
    """Write journal + audit records."""
    today = utc_now().strftime("%Y-%m-%d")

    journal_dir = config.journal_dir or settings.journal_dir / config.sleeve / "journal"
    journal_path = journal_dir / f"{today}.jsonl"
    append_jsonl_record(journal_path, record)
    logger.debug("decision_journaled", path=str(journal_path))

    audit_dir = config.audit_dir or settings.journal_dir / "audit"
    audit_path = audit_dir / f"{today}.jsonl"
    audit_record = AuditLogRecordV1(
        schema_version="1.0",
        event_id=f"aud_{uuid.uuid4().hex[:12]}",
        timestamp=utc_now().isoformat().replace("+00:00", "Z"),
        actor="harness",
        actor_method="run_market_open",
        action=f"decision_{record.action.lower()}",
        from_state=None,
        to_state="submitted" if record.alpaca is not None else "journaled",
        reason_provided=record.thesis_summary or record.action,
    )
    append_audit_record(audit_path, audit_record)
    logger.debug("decision_audited", path=str(audit_path))


def _notify_safe(settings: Settings, message: str) -> None:
    """Send Discord notification, swallowing errors to avoid crashing the routine."""
    try:
        notify_discord_text(
            settings.discord_webhook_url.get_secret_value(),
            message,
            dead_letter_path=settings.dead_letter_dir / "discord.jsonl",
        )
    except Exception as exc:
        logger.error("discord_notify_failed", error=str(exc))


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entrypoint for ``python -m darkhorse.routines.market_open``."""
    run_market_open()


if __name__ == "__main__":
    main()
