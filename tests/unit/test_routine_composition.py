"""Routine composition tests with mocked broker state."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import httpx
import pytest

from darkhorse.config import Settings
from darkhorse.routines import (
    DrawdownState,
    RoutineCompositionConfig,
    compose_routine_snapshot,
    run_market_open_snapshot,
)
from darkhorse.tools import (
    AssetClass,
    AssetListRefreshOutput,
    BrokerEnvironment,
    TradableAsset,
)


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
                symbol="OLD",
                asset_class=AssetClass.US_EQUITY,
                name="Inactive",
                tradable=False,
            ),
        ),
    )
    (asset_dir / "2026-05-09.json").write_text(
        payload.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )


def test_compose_routine_snapshot_builds_validation_context(tmp_path: Path) -> None:
    asset_dir = tmp_path / "assets"
    _write_asset_list(asset_dir)
    seen_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(request.url.path)
        assert request.headers["APCA-API-KEY-ID"] == "paper-key"
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
                    "daytrade_count": 1,
                    "trading_blocked": False,
                },
            )
        if request.url.path == "/v2/positions":
            return httpx.Response(
                200,
                json=[
                    {
                        "symbol": "AAPL",
                        "qty": "1",
                        "market_value": "190.00",
                    },
                ],
            )
        raise AssertionError(f"unexpected HTTP request: {request.url}")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        snapshot = compose_routine_snapshot(
            RoutineCompositionConfig(
                routine="market_open",
                environment=BrokerEnvironment.PAPER,
                asset_dir=asset_dir,
                darkhorse_kill_env="0",
            ),
            settings=_settings(tmp_path),
            client=client,
        )

    assert seen_paths == ["/v2/account", "/v2/positions"]
    assert snapshot.dry_run is True
    assert snapshot.sleeve == "core"
    assert snapshot.kill_switch_trading_allowed is True
    assert snapshot.positions_count == 1
    assert snapshot.allowed_symbol_count == 1
    assert snapshot.core_drawdown_halt is False
    assert snapshot.core_uncle_triggered is False
    assert snapshot.satellite_uncle_triggered is False
    assert snapshot.core_soft_wind_down_spy_only is False
    assert snapshot.core_daily_loss_halt is False
    assert snapshot.satellite_daily_loss_halt is False
    assert snapshot.validation_context.core_allowed_symbols == frozenset({"AAPL"})
    assert snapshot.validation_context.buying_power_usd == Decimal("995.00")
    assert snapshot.validation_context.pdt_restricted is True


def test_compose_routine_snapshot_blocks_when_kill_file_exists(tmp_path: Path) -> None:
    asset_dir = tmp_path / "assets"
    _write_asset_list(asset_dir)
    settings = _settings(tmp_path)
    settings.killswitch_path.write_text("kill\n", encoding="utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v2/account":
            return httpx.Response(
                200,
                json={
                    "id": "acct_123",
                    "status": "ACTIVE",
                    "cash": "1000.00",
                    "buying_power": "995.00",
                    "equity": "26000.00",
                    "pattern_day_trader": False,
                    "daytrade_count": 0,
                    "trading_blocked": False,
                },
            )
        if request.url.path == "/v2/positions":
            return httpx.Response(200, json=[])
        raise AssertionError(f"unexpected HTTP request: {request.url}")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        snapshot = compose_routine_snapshot(
            RoutineCompositionConfig(asset_dir=asset_dir, darkhorse_kill_env="0"),
            settings=settings,
            client=client,
        )

    assert snapshot.kill_switch_trading_allowed is False
    assert snapshot.kill_switch_reasons == (f"kill file present: {settings.killswitch_path}",)
    assert snapshot.validation_context.kill_switch_or_trading_paused is True
    assert snapshot.validation_context.pdt_restricted is False


def test_compose_routine_snapshot_reads_kill_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asset_dir = tmp_path / "assets"
    _write_asset_list(asset_dir)
    monkeypatch.setenv("DARKHORSE_KILL", "1")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v2/account":
            return httpx.Response(
                200,
                json={
                    "id": "acct_123",
                    "status": "ACTIVE",
                    "cash": "1000.00",
                    "buying_power": "995.00",
                    "equity": "26000.00",
                    "pattern_day_trader": False,
                    "daytrade_count": 0,
                    "trading_blocked": False,
                },
            )
        if request.url.path == "/v2/positions":
            return httpx.Response(200, json=[])
        raise AssertionError(f"unexpected HTTP request: {request.url}")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        snapshot = compose_routine_snapshot(
            RoutineCompositionConfig(asset_dir=asset_dir),
            settings=_settings(tmp_path),
            client=client,
        )

    assert snapshot.kill_switch_trading_allowed is False
    assert snapshot.kill_switch_reasons == ("DARKHORSE_KILL=1",)


def test_run_market_open_snapshot_uses_paper_dry_run(tmp_path: Path) -> None:
    asset_dir = Path("unused")

    def load_assets(_input_dir: Path = asset_dir) -> AssetListRefreshOutput:
        payload_path = tmp_path / "asset-list.json"
        return AssetListRefreshOutput(
            environment=BrokerEnvironment.PAPER,
            fetched_at=datetime(2026, 5, 9, tzinfo=UTC),
            output_path=str(payload_path),
            assets=(
                TradableAsset(
                    symbol="AAPL",
                    asset_class=AssetClass.US_EQUITY,
                    name="Apple Inc.",
                    tradable=True,
                ),
            ),
        )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v2/account":
            return httpx.Response(
                200,
                json={
                    "id": "acct_123",
                    "status": "ACTIVE",
                    "cash": "1000.00",
                    "buying_power": "995.00",
                    "equity": "26000.00",
                    "pattern_day_trader": False,
                    "daytrade_count": 0,
                    "trading_blocked": False,
                },
            )
        if request.url.path == "/v2/positions":
            return httpx.Response(200, json=[])
        raise AssertionError(f"unexpected HTTP request: {request.url}")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        snapshot = run_market_open_snapshot(
            settings=_settings(tmp_path),
            client=client,
            asset_loader=load_assets,
        )

    assert snapshot.routine == "market_open"
    assert snapshot.environment is BrokerEnvironment.PAPER
    assert snapshot.dry_run is True


def test_compose_with_core_drawdown_halt(tmp_path: Path) -> None:
    """Core drawdown halt fires when equity falls 15% below HWM."""
    asset_dir = tmp_path / "assets"
    _write_asset_list(asset_dir)

    dd = DrawdownState(
        core_high_water_mark_usd=Decimal("900"),
        core_equity_usd=Decimal("750"),
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v2/account":
            return httpx.Response(
                200,
                json={
                    "id": "acct_123",
                    "status": "ACTIVE",
                    "cash": "750.00",
                    "buying_power": "745.00",
                    "equity": "750.00",
                    "pattern_day_trader": False,
                    "daytrade_count": 0,
                    "trading_blocked": False,
                },
            )
        if request.url.path == "/v2/positions":
            return httpx.Response(200, json=[])
        raise AssertionError(f"unexpected HTTP request: {request.url}")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        snapshot = compose_routine_snapshot(
            RoutineCompositionConfig(asset_dir=asset_dir, darkhorse_kill_env="0"),
            settings=_settings(tmp_path),
            client=client,
            drawdown_state=dd,
        )

    assert snapshot.core_drawdown_halt is True
    assert snapshot.core_uncle_triggered is False
    assert snapshot.validation_context.core_drawdown_halt is True


def test_compose_with_satellite_uncle(tmp_path: Path) -> None:
    """Satellite uncle triggers at -80%."""
    asset_dir = tmp_path / "assets"
    _write_asset_list(asset_dir)

    dd = DrawdownState(
        satellite_high_water_mark_usd=Decimal("100"),
        satellite_equity_usd=Decimal("15"),
    )

    def handler(request: httpx.Request) -> httpx.Response:
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
        raise AssertionError(f"unexpected HTTP request: {request.url}")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        snapshot = compose_routine_snapshot(
            RoutineCompositionConfig(asset_dir=asset_dir, darkhorse_kill_env="0"),
            settings=_settings(tmp_path),
            client=client,
            drawdown_state=dd,
        )

    assert snapshot.satellite_uncle_triggered is True
    assert snapshot.validation_context.satellite_uncle_triggered is True


def test_compose_with_soft_wind_down(tmp_path: Path) -> None:
    """Core soft wind-down fires when Sharpe < 0 and return above floor."""
    asset_dir = tmp_path / "assets"
    _write_asset_list(asset_dir)

    dd = DrawdownState(
        rolling_6m_sharpe_vs_spy=-0.5,
        core_total_return_since_start=Decimal("-0.05"),
    )

    def handler(request: httpx.Request) -> httpx.Response:
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
        raise AssertionError(f"unexpected HTTP request: {request.url}")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        snapshot = compose_routine_snapshot(
            RoutineCompositionConfig(asset_dir=asset_dir, darkhorse_kill_env="0"),
            settings=_settings(tmp_path),
            client=client,
            drawdown_state=dd,
        )

    assert snapshot.core_soft_wind_down_spy_only is True
    assert snapshot.validation_context.core_soft_wind_down_spy_only is True


def test_compose_with_daily_loss_halt(tmp_path: Path) -> None:
    """Daily loss halt fires when intraday P&L exceeds the kill threshold."""
    asset_dir = tmp_path / "assets"
    _write_asset_list(asset_dir)

    dd = DrawdownState(daily_pnl_core_usd=Decimal("-20"))

    def handler(request: httpx.Request) -> httpx.Response:
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
        raise AssertionError(f"unexpected HTTP request: {request.url}")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        snapshot = compose_routine_snapshot(
            RoutineCompositionConfig(asset_dir=asset_dir, darkhorse_kill_env="0"),
            settings=_settings(tmp_path),
            client=client,
            drawdown_state=dd,
        )

    assert snapshot.core_daily_loss_halt is True
    assert snapshot.validation_context.core_daily_loss_halt_today is True


def test_compose_trades_today_flows_through(tmp_path: Path) -> None:
    """trades_today_in_sleeve flows from DrawdownState into ValidationContext."""
    asset_dir = tmp_path / "assets"
    _write_asset_list(asset_dir)

    dd = DrawdownState(trades_today_core=2)

    def handler(request: httpx.Request) -> httpx.Response:
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
        raise AssertionError(f"unexpected HTTP request: {request.url}")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        snapshot = compose_routine_snapshot(
            RoutineCompositionConfig(asset_dir=asset_dir, darkhorse_kill_env="0", sleeve="core"),
            settings=_settings(tmp_path),
            client=client,
            drawdown_state=dd,
        )

    assert snapshot.validation_context.trades_today_in_sleeve == 2


def test_compose_writes_audit_record(tmp_path: Path) -> None:
    """Every composition run writes an audit record."""
    asset_dir = tmp_path / "assets"
    _write_asset_list(asset_dir)

    def handler(request: httpx.Request) -> httpx.Response:
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
        raise AssertionError(f"unexpected HTTP request: {request.url}")

    audit_dir = tmp_path / "audit"
    settings = _settings(tmp_path)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        snapshot = compose_routine_snapshot(
            RoutineCompositionConfig(
                asset_dir=asset_dir,
                darkhorse_kill_env="0",
                audit_dir=audit_dir,
            ),
            settings=settings,
            client=client,
        )

    assert snapshot.audit_path is not None
    assert snapshot.audit_path.is_file()
    import json

    lines = snapshot.audit_path.read_text().strip().split("\n")
    record = json.loads(lines[0])
    assert record["action"] == "routine_started"
    assert record["actor"] == "harness"
    assert snapshot.journal_path is None


def test_compose_writes_no_trade_journal_when_blocked(tmp_path: Path) -> None:
    """Kill switch triggers NO_TRADE journal + audit."""
    asset_dir = tmp_path / "assets"
    _write_asset_list(asset_dir)
    settings = _settings(tmp_path)
    settings.killswitch_path.write_text("kill\n", encoding="utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
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
        raise AssertionError(f"unexpected HTTP request: {request.url}")

    audit_dir = tmp_path / "audit"
    journal_dir = tmp_path / "journal"
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        snapshot = compose_routine_snapshot(
            RoutineCompositionConfig(
                asset_dir=asset_dir,
                darkhorse_kill_env="0",
                audit_dir=audit_dir,
                journal_dir=journal_dir,
            ),
            settings=settings,
            client=client,
        )

    assert snapshot.audit_path is not None
    assert snapshot.audit_path.is_file()
    assert snapshot.journal_path is not None
    assert snapshot.journal_path.is_file()

    import json

    journal_lines = snapshot.journal_path.read_text().strip().split("\n")
    record = json.loads(journal_lines[0])
    assert record["action"] == "NO_TRADE"
    assert record["validate_order_passed"] is False
    assert "kill_switch" in record["risk_checks"]["reason"]


def test_phase_core_deploy_cap_flows_to_validation_context(tmp_path: Path) -> None:
    """phase_core_deploy_cap_usd from Settings flows into max_core_deploy_usd."""
    asset_dir = tmp_path / "assets"
    _write_asset_list(asset_dir)
    settings = _settings(tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
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
        raise AssertionError(f"unexpected HTTP request: {request.url}")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        snapshot = compose_routine_snapshot(
            RoutineCompositionConfig(asset_dir=asset_dir, darkhorse_kill_env="0"),
            settings=settings,
            client=client,
        )

    assert snapshot.validation_context.max_core_deploy_usd == Decimal("50.0")


def test_phase_core_deploy_cap_none_when_unset(tmp_path: Path) -> None:
    """When phase_core_deploy_cap_usd is None, max_core_deploy_usd is None."""
    asset_dir = tmp_path / "assets"
    _write_asset_list(asset_dir)
    settings = _settings(tmp_path)
    settings.phase_core_deploy_cap_usd = None

    def handler(request: httpx.Request) -> httpx.Response:
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
        raise AssertionError(f"unexpected HTTP request: {request.url}")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        snapshot = compose_routine_snapshot(
            RoutineCompositionConfig(asset_dir=asset_dir, darkhorse_kill_env="0"),
            settings=settings,
            client=client,
        )

    assert snapshot.validation_context.max_core_deploy_usd is None


def test_validate_order_rejects_above_phase_cap() -> None:
    """R-V01-PHASE-CAP rejects Core buy exceeding the $50 cap end-to-end."""
    from darkhorse.risk import (
        OrderRequest,
        OrderType,
        Side,
        Sleeve,
        ValidationContext,
        validate_order,
    )

    ctx = ValidationContext(
        core_nav_usd=Decimal("900"),
        satellite_nav_usd=Decimal("100"),
        account_equity_usd=Decimal("1000"),
        core_allowed_symbols=frozenset({"AAPL"}),
        satellite_allowed_symbols=frozenset({"AAPL"}),
        pdt_restricted=True,
        day_trades_in_rolling_5_sessions=0,
        order_would_be_day_trade=False,
        buying_power_usd=Decimal("995"),
        max_core_deploy_usd=Decimal("50"),
    )
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("75"),
        estimated_notional_usd=Decimal("75"),
    )
    result = validate_order(order, ctx)
    assert result.verdict.value == "reject"
    assert result.rule_id == "R-V01-PHASE-CAP"


def test_validate_order_passes_within_phase_cap() -> None:
    """Order within the $50 cap passes R-V01-PHASE-CAP."""
    from darkhorse.risk import (
        OrderRequest,
        OrderType,
        Side,
        Sleeve,
        ValidationContext,
        validate_order,
    )

    ctx = ValidationContext(
        core_nav_usd=Decimal("900"),
        satellite_nav_usd=Decimal("100"),
        account_equity_usd=Decimal("1000"),
        core_allowed_symbols=frozenset({"AAPL"}),
        satellite_allowed_symbols=frozenset({"AAPL"}),
        pdt_restricted=True,
        day_trades_in_rolling_5_sessions=0,
        order_would_be_day_trade=False,
        buying_power_usd=Decimal("995"),
        max_core_deploy_usd=Decimal("50"),
    )
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("45"),
        estimated_notional_usd=Decimal("45"),
    )
    result = validate_order(order, ctx)
    assert result.verdict.value == "pass"
    assert result.rule_id == "R-VOK"
