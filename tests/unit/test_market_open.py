"""End-to-end market_open routine tests with fully mocked Anthropic + broker."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx

from darkhorse.config import Settings
from darkhorse.routines.market_open import (
    _build_journal_record,
    _build_order_from_decision,
    _journal_and_audit,
    _notify_safe,
    run_market_open,
)
from darkhorse.tools import (
    AssetClass,
    AssetListRefreshOutput,
    BrokerEnvironment,
    TradableAsset,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        anthropic_api_key="sk-test-ant",
        alpaca_live_api_key="live-key",
        alpaca_live_secret_key="live-secret",
        alpaca_paper_api_key="paper-key",
        alpaca_paper_secret_key="paper-secret",
        perplexity_api_key="pplx",
        tavily_api_key="tvly",
        finnhub_api_key="finn",
        snaptrade_client_id="snap",
        snaptrade_consumer_key="snapc",
        discord_webhook_url="https://discord.test/webhook",
        killswitch_path=tmp_path / "KILLSWITCH",
        remote_kill_url=None,
        journal_dir=tmp_path / "memory",
        dead_letter_dir=tmp_path / "dead_letter",
    )


def _write_asset_list(asset_dir: Path) -> None:
    asset_dir.mkdir(parents=True)
    payload = AssetListRefreshOutput(
        environment=BrokerEnvironment.PAPER,
        fetched_at=datetime(2026, 5, 9, tzinfo=UTC),
        output_path=str(asset_dir / "2026-05-09.json"),
        assets=(
            TradableAsset(
                symbol="AAPL",
                asset_class=AssetClass.US_EQUITY,
                name="Apple Inc.",
                exchange="NASDAQ",
                tradable=True,
            ),
            TradableAsset(
                symbol="SPY",
                asset_class=AssetClass.ETF,
                name="SPDR S&P 500",
                exchange="NYSE",
                tradable=True,
            ),
        ),
    )
    (asset_dir / "2026-05-09.json").write_text(
        payload.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )


def _anthropic_response(
    text: str,
    *,
    stop_reason: str = "end_turn",
    tool_use_blocks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    content: list[dict[str, Any]] = []
    if tool_use_blocks:
        content.extend(tool_use_blocks)
    if text:
        content.append({"type": "text", "text": text})
    return {
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "content": content,
        "model": "claude-sonnet-4-6",
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {
            "input_tokens": 100,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
            "output_tokens": 50,
        },
    }


def _no_trade_decision() -> str:
    return json.dumps(
        {
            "action": "NO_TRADE",
            "ticker": None,
            "qty": None,
            "order_type": None,
            "limit_price": None,
            "time_in_force": "day",
            "confidence": 0.3,
            "expected_horizon_days": None,
            "expected_outcome_pct": None,
            "thesis_summary": "Insufficient evidence.",
            "reasoning_trace": {},
            "market_order_exception": False,
            "lessons_referenced": [],
            "anti_patterns_flagged": [],
        }
    )


def _buy_decision(*, confidence: float = 0.85) -> str:
    return json.dumps(
        {
            "action": "BUY",
            "ticker": "AAPL",
            "qty": 1,
            "order_type": "limit",
            "limit_price": "45.00",
            "time_in_force": "day",
            "confidence": confidence,
            "expected_horizon_days": 30,
            "expected_outcome_pct": 5.0,
            "thesis_summary": "Strong momentum.",
            "reasoning_trace": {"base_rate": "bullish"},
            "market_order_exception": False,
            "lessons_referenced": [],
            "anti_patterns_flagged": [],
        }
    )


def _build_transports(
    decision_json: str,
) -> tuple[httpx.MockTransport, httpx.MockTransport]:
    """Build mocked Anthropic and broker transports."""
    anthropic_calls: dict[str, int] = {"n": 0}

    researcher_resp = _anthropic_response("Research complete. Market is flat.")
    risk_manager_resp = _anthropic_response(decision_json)
    anthropic_responses = [researcher_resp, risk_manager_resp]

    def anthropic_handler(request: httpx.Request) -> httpx.Response:
        idx = min(anthropic_calls["n"], len(anthropic_responses) - 1)
        anthropic_calls["n"] += 1
        return httpx.Response(200, json=anthropic_responses[idx])

    def broker_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v2/account":
            return httpx.Response(
                200,
                json={
                    "id": "acct_123",
                    "status": "ACTIVE",
                    "cash": "1000.00",
                    "buying_power": "995.00",
                    "equity": "1000.00",
                    "pattern_day_trader": False,
                    "daytrade_count": 0,
                    "trading_blocked": False,
                },
            )
        if request.url.path == "/v2/positions":
            return httpx.Response(200, json=[])
        if request.url.path == "/v2/orders":
            return httpx.Response(
                200,
                json={
                    "id": "order_abc123",
                    "client_order_id": "test_coid",
                    "status": "accepted",
                    "symbol": "AAPL",
                    "qty": "1",
                    "side": "buy",
                    "type": "limit",
                    "limit_price": "45.00",
                },
            )
        if "discord" in str(request.url):
            return httpx.Response(204)
        return httpx.Response(404)

    return httpx.MockTransport(anthropic_handler), httpx.MockTransport(broker_handler)


def _load_test_assets(asset_dir: Path) -> Any:
    from darkhorse.tools.assets import load_latest_asset_list

    return load_latest_asset_list(asset_dir)


# ---------------------------------------------------------------------------
# run_market_open: NO_TRADE path
# ---------------------------------------------------------------------------


def test_run_market_open_no_trade(tmp_path: Path) -> None:
    asset_dir = tmp_path / "assets"
    _write_asset_list(asset_dir)
    settings = _settings(tmp_path)

    anthropic_transport, broker_transport = _build_transports(_no_trade_decision())

    with (
        httpx.Client(transport=anthropic_transport) as anthropic_client,
        httpx.Client(transport=broker_transport) as broker_client,
    ):
        record = run_market_open(
            settings=settings,
            broker_client=broker_client,
            anthropic_http_client=anthropic_client,
            asset_loader=lambda _input_dir=asset_dir: _load_test_assets(asset_dir),
        )

    assert record is not None
    assert record.action == "NO_TRADE"
    assert record.validate_order_passed is False

    journal_dir = tmp_path / "memory" / "core" / "journal"
    assert any(journal_dir.glob("*.jsonl"))


# ---------------------------------------------------------------------------
# run_market_open: confidence gate
# ---------------------------------------------------------------------------


def test_run_market_open_confidence_gate(tmp_path: Path) -> None:
    """BUY decision below 0.70 confidence is blocked."""
    asset_dir = tmp_path / "assets"
    _write_asset_list(asset_dir)
    settings = _settings(tmp_path)

    anthropic_transport, broker_transport = _build_transports(_buy_decision(confidence=0.55))

    with (
        httpx.Client(transport=anthropic_transport) as anthropic_client,
        httpx.Client(transport=broker_transport) as broker_client,
    ):
        record = run_market_open(
            settings=settings,
            broker_client=broker_client,
            anthropic_http_client=anthropic_client,
            asset_loader=lambda _input_dir=asset_dir: _load_test_assets(asset_dir),
        )

    assert record is not None
    assert record.action == "BUY"
    assert record.validate_order_passed is False
    assert "confidence_below_threshold" in str(record.risk_checks)


# ---------------------------------------------------------------------------
# run_market_open: BUY path (dry_run)
# ---------------------------------------------------------------------------


def test_run_market_open_buy_dry_run(tmp_path: Path) -> None:
    """BUY with sufficient confidence passes validation and does a dry run."""
    asset_dir = tmp_path / "assets"
    _write_asset_list(asset_dir)
    settings = _settings(tmp_path)

    anthropic_transport, broker_transport = _build_transports(_buy_decision())

    with (
        httpx.Client(transport=anthropic_transport) as anthropic_client,
        httpx.Client(transport=broker_transport) as broker_client,
    ):
        record = run_market_open(
            settings=settings,
            broker_client=broker_client,
            anthropic_http_client=anthropic_client,
            asset_loader=lambda _input_dir=asset_dir: _load_test_assets(asset_dir),
            dry_run=True,
        )

    assert record is not None
    assert record.action == "BUY"
    assert record.ticker == "AAPL"


# ---------------------------------------------------------------------------
# run_market_open: BUY path (paper submit)
# ---------------------------------------------------------------------------


def test_run_market_open_buy_paper_submit(tmp_path: Path) -> None:
    """BUY with sufficient confidence submits to Alpaca paper."""
    asset_dir = tmp_path / "assets"
    _write_asset_list(asset_dir)
    settings = _settings(tmp_path)

    anthropic_transport, broker_transport = _build_transports(_buy_decision())

    with (
        httpx.Client(transport=anthropic_transport) as anthropic_client,
        httpx.Client(transport=broker_transport) as broker_client,
    ):
        record = run_market_open(
            settings=settings,
            broker_client=broker_client,
            anthropic_http_client=anthropic_client,
            asset_loader=lambda _input_dir=asset_dir: _load_test_assets(asset_dir),
            dry_run=False,
        )

    assert record is not None
    assert record.action == "BUY"
    assert record.alpaca is not None
    assert record.alpaca.broker_order_id == "order_abc123"

    journal_dir = tmp_path / "memory" / "core" / "journal"
    assert any(journal_dir.glob("*.jsonl"))
    audit_dir = tmp_path / "memory" / "audit"
    assert any(audit_dir.glob("*.jsonl"))


# ---------------------------------------------------------------------------
# run_market_open: kill switch blocks trading
# ---------------------------------------------------------------------------


def test_run_market_open_kill_switch_blocks(tmp_path: Path) -> None:
    """Kill switch active -> NO_TRADE returned by composition, run_market_open returns None."""
    asset_dir = tmp_path / "assets"
    _write_asset_list(asset_dir)
    settings = _settings(tmp_path)
    settings.killswitch_path.write_text("kill\n", encoding="utf-8")

    anthropic_transport, broker_transport = _build_transports(_no_trade_decision())

    with (
        httpx.Client(transport=anthropic_transport) as anthropic_client,
        httpx.Client(transport=broker_transport) as broker_client,
    ):
        record = run_market_open(
            settings=settings,
            broker_client=broker_client,
            anthropic_http_client=anthropic_client,
            asset_loader=lambda _input_dir=asset_dir: _load_test_assets(asset_dir),
        )

    assert record is None


# ---------------------------------------------------------------------------
# Helper unit tests
# ---------------------------------------------------------------------------


def test_build_order_from_decision_buy() -> None:
    from darkhorse.harness import LLMDecisionOutput
    from darkhorse.risk import ValidationContext
    from darkhorse.routines.composition import RoutineCompositionSnapshot

    decision = LLMDecisionOutput.model_validate_json(_buy_decision())
    ctx = ValidationContext(
        core_nav_usd=Decimal("900"),
        satellite_nav_usd=Decimal("100"),
        account_equity_usd=Decimal("1000"),
        core_allowed_symbols=frozenset({"AAPL"}),
        satellite_allowed_symbols=frozenset(),
        pdt_restricted=True,
        day_trades_in_rolling_5_sessions=0,
        order_would_be_day_trade=False,
    )
    snapshot = RoutineCompositionSnapshot(
        routine="market_open",
        sleeve="core",
        environment=BrokerEnvironment.PAPER,
        dry_run=True,
        kill_switch_trading_allowed=True,
        kill_switch_reasons=(),
        account_status="ACTIVE",
        account_trading_blocked=False,
        positions_count=0,
        allowed_symbol_count=1,
        core_drawdown_halt=False,
        core_uncle_triggered=False,
        satellite_uncle_triggered=False,
        core_soft_wind_down_spy_only=False,
        core_daily_loss_halt=False,
        satellite_daily_loss_halt=False,
        validation_context=ctx,
    )
    order, _ = _build_order_from_decision(decision=decision, snapshot=snapshot)
    assert order is not None
    assert order.symbol == "AAPL"
    assert order.qty == 1
    assert order.limit_price == Decimal("45.00")


def test_build_order_from_decision_no_trade_returns_none() -> None:
    from darkhorse.harness import LLMDecisionOutput
    from darkhorse.risk import ValidationContext
    from darkhorse.routines.composition import RoutineCompositionSnapshot

    decision = LLMDecisionOutput.model_validate_json(_no_trade_decision())
    ctx = ValidationContext(
        core_nav_usd=Decimal("900"),
        satellite_nav_usd=Decimal("100"),
        account_equity_usd=Decimal("1000"),
        core_allowed_symbols=frozenset(),
        satellite_allowed_symbols=frozenset(),
        pdt_restricted=True,
        day_trades_in_rolling_5_sessions=0,
        order_would_be_day_trade=False,
    )
    snapshot = RoutineCompositionSnapshot(
        routine="market_open",
        sleeve="core",
        environment=BrokerEnvironment.PAPER,
        dry_run=True,
        kill_switch_trading_allowed=True,
        kill_switch_reasons=(),
        account_status="ACTIVE",
        account_trading_blocked=False,
        positions_count=0,
        allowed_symbol_count=0,
        core_drawdown_halt=False,
        core_uncle_triggered=False,
        satellite_uncle_triggered=False,
        core_soft_wind_down_spy_only=False,
        core_daily_loss_halt=False,
        satellite_daily_loss_halt=False,
        validation_context=ctx,
    )
    order, _ = _build_order_from_decision(decision=decision, snapshot=snapshot)
    assert order is None


def test_notify_safe_swallows_errors(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _notify_safe(settings, "test message")


def test_journal_and_audit_writes_files(tmp_path: Path) -> None:
    from darkhorse.harness import HarnessResult, LLMDecisionOutput
    from darkhorse.risk import ValidationContext
    from darkhorse.routines.composition import RoutineCompositionConfig, RoutineCompositionSnapshot

    settings = _settings(tmp_path)
    decision = LLMDecisionOutput.model_validate_json(_no_trade_decision())
    ctx = ValidationContext(
        core_nav_usd=Decimal("900"),
        satellite_nav_usd=Decimal("100"),
        account_equity_usd=Decimal("1000"),
        core_allowed_symbols=frozenset(),
        satellite_allowed_symbols=frozenset(),
        pdt_restricted=True,
        day_trades_in_rolling_5_sessions=0,
        order_would_be_day_trade=False,
    )
    snapshot = RoutineCompositionSnapshot(
        routine="market_open",
        sleeve="core",
        environment=BrokerEnvironment.PAPER,
        dry_run=True,
        kill_switch_trading_allowed=True,
        kill_switch_reasons=(),
        account_status="ACTIVE",
        account_trading_blocked=False,
        positions_count=0,
        allowed_symbol_count=0,
        core_drawdown_halt=False,
        core_uncle_triggered=False,
        satellite_uncle_triggered=False,
        core_soft_wind_down_spy_only=False,
        core_daily_loss_halt=False,
        satellite_daily_loss_halt=False,
        validation_context=ctx,
    )
    from darkhorse.harness import CallCost

    harness_result = HarnessResult(
        decision=decision,
        research_text="test",
        total_cost=CallCost(),
        researcher_iterations=1,
        model_assignments={"researcher": "sonnet", "risk_manager": "opus"},
        tools_used=[],
    )

    record = _build_journal_record(harness_result, snapshot, settings)
    config = RoutineCompositionConfig(
        journal_dir=tmp_path / "journal",
        audit_dir=tmp_path / "audit",
    )
    _journal_and_audit(record, config, settings)

    assert any((tmp_path / "journal").glob("*.jsonl"))
    assert any((tmp_path / "audit").glob("*.jsonl"))
