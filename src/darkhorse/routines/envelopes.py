"""Envelope builders for audit and journal records emitted by routines."""

from __future__ import annotations

import subprocess
import uuid

from darkhorse.idempotency import intent_hash
from darkhorse.routines.composition import RoutineCompositionSnapshot
from darkhorse.schemas.audit import AuditLogRecordV1
from darkhorse.schemas.decision import DecisionJournalRecordV1
from darkhorse.tools import utc_now


def _short_git_sha() -> str:
    """Best-effort short SHA of HEAD; returns ``"unknown"`` if git is unavailable."""
    try:
        result = subprocess.run(  # noqa: S603
            ["git", "rev-parse", "--short", "HEAD"],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() or "unknown"
    except Exception:  # noqa: BLE001
        return "unknown"


def build_routine_start_audit(snapshot: RoutineCompositionSnapshot) -> AuditLogRecordV1:
    """Create an audit record for routine entry."""
    flags: list[str] = []
    if not snapshot.kill_switch_trading_allowed:
        flags.append("kill_switch_blocked")
    if snapshot.core_drawdown_halt:
        flags.append("core_drawdown_halt")
    if snapshot.core_uncle_triggered:
        flags.append("core_uncle")
    if snapshot.satellite_uncle_triggered:
        flags.append("satellite_uncle")
    if snapshot.core_soft_wind_down_spy_only:
        flags.append("core_soft_wind_down")

    return AuditLogRecordV1(
        schema_version="1.0",
        event_id=f"aud_{uuid.uuid4().hex[:12]}",
        timestamp=utc_now().isoformat().replace("+00:00", "Z"),
        actor="harness",
        actor_method="compose_routine_snapshot",
        action="routine_started",
        from_state=None,
        to_state=", ".join(flags) if flags else "trading_allowed",
        reason_provided=f"routine={snapshot.routine} sleeve={snapshot.sleeve}",
    )


def build_no_trade_decision(
    snapshot: RoutineCompositionSnapshot,
    reason: str,
) -> DecisionJournalRecordV1:
    """Create a minimal NO_TRADE decision record when composition blocks trading."""
    now = utc_now().isoformat().replace("+00:00", "Z")
    decision_id = f"dec_{now[:10]}_{uuid.uuid4().hex[:8]}"
    git_sha = _short_git_sha()

    risk_checks = {
        "kill_switch_trading_allowed": snapshot.kill_switch_trading_allowed,
        "core_drawdown_halt": snapshot.core_drawdown_halt,
        "core_uncle_triggered": snapshot.core_uncle_triggered,
        "satellite_uncle_triggered": snapshot.satellite_uncle_triggered,
        "core_soft_wind_down_spy_only": snapshot.core_soft_wind_down_spy_only,
        "core_daily_loss_halt": snapshot.core_daily_loss_halt,
        "satellite_daily_loss_halt": snapshot.satellite_daily_loss_halt,
        "reason": reason,
    }

    payload = {
        "schema_version": "1.0",
        "decision_id": decision_id,
        "timestamp": now,
        "sleeve": snapshot.sleeve,
        "routine": snapshot.routine,
        "doctrine_version": git_sha,
        "prompt_version": git_sha,
        "action": "NO_TRADE",
        "validate_order_passed": False,
        "risk_checks": risk_checks,
    }
    fingerprint = intent_hash(payload)

    return DecisionJournalRecordV1(
        schema_version="1.0",
        decision_id=decision_id,
        timestamp=now,
        sleeve=snapshot.sleeve,  # type: ignore[arg-type]
        routine=snapshot.routine,
        doctrine_version=git_sha,
        prompt_version=git_sha,
        action="NO_TRADE",
        validate_order_passed=False,
        risk_checks=risk_checks,
        intent_fingerprint=fingerprint,
    )
