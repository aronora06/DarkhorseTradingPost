"""Tests for routine audit and journal envelope builders."""

from __future__ import annotations

from decimal import Decimal

from darkhorse.risk import ValidationContext
from darkhorse.routines.composition import RoutineCompositionSnapshot
from darkhorse.routines.envelopes import build_no_trade_decision, build_routine_start_audit
from darkhorse.tools import BrokerEnvironment


def _snapshot(
    *,
    kill_allowed: bool = True,
    core_dd_halt: bool = False,
    core_uncle: bool = False,
    sat_uncle: bool = False,
    wind_down: bool = False,
) -> RoutineCompositionSnapshot:
    ctx = ValidationContext(
        core_nav_usd=Decimal("900"),
        satellite_nav_usd=Decimal("100"),
        account_equity_usd=Decimal("1000"),
        core_allowed_symbols=frozenset({"AAPL"}),
        satellite_allowed_symbols=frozenset({"AAPL"}),
        pdt_restricted=True,
        day_trades_in_rolling_5_sessions=0,
        order_would_be_day_trade=False,
        kill_switch_or_trading_paused=not kill_allowed,
        buying_power_usd=Decimal("995"),
    )
    return RoutineCompositionSnapshot(
        routine="market_open",
        sleeve="core",
        environment=BrokerEnvironment.PAPER,
        dry_run=True,
        kill_switch_trading_allowed=kill_allowed,
        kill_switch_reasons=() if kill_allowed else ("test kill",),
        account_status="ACTIVE",
        account_trading_blocked=False,
        positions_count=0,
        allowed_symbol_count=1,
        core_drawdown_halt=core_dd_halt,
        core_uncle_triggered=core_uncle,
        satellite_uncle_triggered=sat_uncle,
        core_soft_wind_down_spy_only=wind_down,
        core_daily_loss_halt=False,
        satellite_daily_loss_halt=False,
        validation_context=ctx,
    )


class TestBuildRoutineStartAudit:
    def test_normal_trading_allowed(self) -> None:
        record = build_routine_start_audit(_snapshot())
        assert record.schema_version == "1.0"
        assert record.actor == "harness"
        assert record.action == "routine_started"
        assert record.to_state == "trading_allowed"
        assert record.event_id.startswith("aud_")
        assert record.timestamp.endswith("Z")

    def test_kill_switch_blocked(self) -> None:
        record = build_routine_start_audit(_snapshot(kill_allowed=False))
        assert "kill_switch_blocked" in (record.to_state or "")

    def test_drawdown_flags_in_state(self) -> None:
        record = build_routine_start_audit(_snapshot(core_dd_halt=True, sat_uncle=True))
        state = record.to_state or ""
        assert "core_drawdown_halt" in state
        assert "satellite_uncle" in state

    def test_wind_down_in_state(self) -> None:
        record = build_routine_start_audit(_snapshot(wind_down=True))
        assert "core_soft_wind_down" in (record.to_state or "")


class TestBuildNoTradeDecision:
    def test_produces_valid_record(self) -> None:
        record = build_no_trade_decision(_snapshot(kill_allowed=False), "kill switch active")
        assert record.schema_version == "1.0"
        assert record.action == "NO_TRADE"
        assert record.validate_order_passed is False
        assert record.sleeve == "core"
        assert record.routine == "market_open"
        assert record.decision_id.startswith("dec_")
        assert record.timestamp.endswith("Z")
        assert len(record.intent_fingerprint) == 64

    def test_risk_checks_capture_reason(self) -> None:
        record = build_no_trade_decision(_snapshot(core_dd_halt=True), "core drawdown halt active")
        assert record.risk_checks["core_drawdown_halt"] is True
        assert record.risk_checks["reason"] == "core drawdown halt active"

    def test_same_intent_produces_same_fingerprint(self) -> None:
        """Two NO_TRADE decisions for the same routine/sleeve are the same intent."""
        r1 = build_no_trade_decision(_snapshot(kill_allowed=False), "kill switch")
        r2 = build_no_trade_decision(_snapshot(kill_allowed=False), "kill switch again")
        assert r1.intent_fingerprint == r2.intent_fingerprint

    def test_different_sleeve_produces_different_fingerprint(self) -> None:
        snap_core = _snapshot(kill_allowed=False)
        snap_sat = _snapshot(kill_allowed=False)
        snap_sat = snap_sat.model_copy(update={"sleeve": "satellite"})
        r1 = build_no_trade_decision(snap_core, "kill switch")
        r2 = build_no_trade_decision(snap_sat, "kill switch")
        assert r1.intent_fingerprint != r2.intent_fingerprint
