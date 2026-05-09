"""Dry-run routine composition before production LLM orchestration exists."""

from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path
from typing import Protocol

import httpx
import structlog
from pydantic import BaseModel, ConfigDict

from darkhorse.audit import append_audit_record
from darkhorse.config import Settings, get_settings
from darkhorse.journal import append_jsonl_record
from darkhorse.risk import (
    ValidationContext,
    core_drawdown_flags,
    evaluate_kill_switch,
    satellite_drawdown_flags,
    soft_wind_down_core_to_spy,
)
from darkhorse.tools import (
    AlpacaAccountInput,
    AlpacaAccountOutput,
    AlpacaPositionsInput,
    AlpacaPositionsOutput,
    AssetListRefreshOutput,
    BrokerEnvironment,
    fetch_account,
    fetch_positions,
    load_latest_asset_list,
)

logger = structlog.get_logger(__name__)


class AccountFetcher(Protocol):
    def __call__(
        self,
        payload: AlpacaAccountInput,
        *,
        settings: Settings | None = None,
        client: httpx.Client | None = None,
    ) -> AlpacaAccountOutput: ...


class PositionsFetcher(Protocol):
    def __call__(
        self,
        payload: AlpacaPositionsInput,
        *,
        settings: Settings | None = None,
        client: httpx.Client | None = None,
    ) -> AlpacaPositionsOutput: ...


class AssetListLoader(Protocol):
    def __call__(self, input_dir: Path = Path("data/assets")) -> AssetListRefreshOutput: ...


class DrawdownState(BaseModel):
    """Optional persisted drawdown/performance state fed into composition."""

    model_config = ConfigDict(extra="forbid")

    core_high_water_mark_usd: Decimal | None = None
    satellite_high_water_mark_usd: Decimal | None = None
    core_equity_usd: Decimal | None = None
    satellite_equity_usd: Decimal | None = None
    rolling_6m_sharpe_vs_spy: float | None = None
    core_total_return_since_start: Decimal | None = None
    daily_pnl_core_usd: Decimal | None = None
    daily_pnl_satellite_usd: Decimal | None = None
    trades_today_core: int = 0
    trades_today_satellite: int = 0


class RoutineCompositionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    routine: str = "market_open"
    sleeve: str = "core"
    environment: BrokerEnvironment = BrokerEnvironment.PAPER
    asset_dir: Path = Path("data/assets")
    dry_run: bool = True
    darkhorse_kill_env: str | None = None
    audit_dir: Path | None = None
    journal_dir: Path | None = None


class RoutineCompositionSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    routine: str
    sleeve: str
    environment: BrokerEnvironment
    dry_run: bool
    kill_switch_trading_allowed: bool
    kill_switch_reasons: tuple[str, ...]
    account_status: str
    account_trading_blocked: bool
    positions_count: int
    allowed_symbol_count: int
    core_drawdown_halt: bool
    core_uncle_triggered: bool
    satellite_uncle_triggered: bool
    core_soft_wind_down_spy_only: bool
    core_daily_loss_halt: bool
    satellite_daily_loss_halt: bool
    validation_context: ValidationContext
    audit_path: Path | None = None
    journal_path: Path | None = None


def compose_routine_snapshot(
    config: RoutineCompositionConfig | None = None,
    *,
    settings: Settings | None = None,
    client: httpx.Client | None = None,
    account_fetcher: AccountFetcher = fetch_account,
    positions_fetcher: PositionsFetcher = fetch_positions,
    asset_loader: AssetListLoader = load_latest_asset_list,
    drawdown_state: DrawdownState | None = None,
) -> RoutineCompositionSnapshot:
    """Load deterministic routine state and build a risk context without trading."""

    active_config = config or RoutineCompositionConfig()
    active_settings = settings or get_settings()
    dd = drawdown_state or DrawdownState()

    kill_report = evaluate_kill_switch(
        killswitch_path=active_settings.killswitch_path,
        darkhorse_kill_env=_darkhorse_kill_env(active_config),
        remote_kill_url=active_settings.remote_kill_url,
        http_client=client,
    )
    assets = asset_loader(active_config.asset_dir)
    allowed_symbols = frozenset(asset.symbol for asset in assets.assets if asset.tradable)
    account = account_fetcher(
        AlpacaAccountInput(environment=active_config.environment),
        settings=active_settings,
        client=client,
    )
    positions = positions_fetcher(
        AlpacaPositionsInput(environment=active_config.environment),
        settings=active_settings,
        client=client,
    )

    core_dd_halt, core_uncle = _compute_drawdown_flags(
        dd.core_high_water_mark_usd, dd.core_equity_usd, sleeve="core"
    )
    _, sat_uncle = _compute_drawdown_flags(
        dd.satellite_high_water_mark_usd, dd.satellite_equity_usd, sleeve="satellite"
    )
    wind_down_spy = soft_wind_down_core_to_spy(
        dd.rolling_6m_sharpe_vs_spy, dd.core_total_return_since_start
    )
    core_daily_halt = _daily_loss_halt(
        dd.daily_pnl_core_usd,
        Decimal(str(active_settings.core_sleeve_target_usd)),
        Decimal(str(active_settings.daily_loss_kill_pct_core)),
    )
    sat_daily_halt = _daily_loss_halt(
        dd.daily_pnl_satellite_usd,
        Decimal(str(active_settings.satellite_sleeve_target_usd)),
        Decimal(str(active_settings.daily_loss_kill_pct_satellite)),
    )

    validation_context = build_validation_context_from_account(
        account,
        settings=active_settings,
        allowed_symbols=allowed_symbols,
        kill_switch_or_trading_paused=(
            (not kill_report.trading_allowed) or account.trading_blocked
        ),
        core_drawdown_halt=core_dd_halt,
        core_uncle_triggered=core_uncle,
        satellite_uncle_triggered=sat_uncle,
        core_soft_wind_down_spy_only=wind_down_spy,
        core_daily_loss_halt_today=core_daily_halt,
        satellite_daily_loss_halt_today=sat_daily_halt,
        trades_today_in_sleeve=(
            dd.trades_today_core if active_config.sleeve == "core" else dd.trades_today_satellite
        ),
    )
    snapshot = RoutineCompositionSnapshot(
        routine=active_config.routine,
        sleeve=active_config.sleeve,
        environment=active_config.environment,
        dry_run=active_config.dry_run,
        kill_switch_trading_allowed=kill_report.trading_allowed,
        kill_switch_reasons=kill_report.reasons,
        account_status=account.status,
        account_trading_blocked=account.trading_blocked,
        positions_count=len(positions.positions),
        allowed_symbol_count=len(allowed_symbols),
        core_drawdown_halt=core_dd_halt,
        core_uncle_triggered=core_uncle,
        satellite_uncle_triggered=sat_uncle,
        core_soft_wind_down_spy_only=wind_down_spy,
        core_daily_loss_halt=core_daily_halt,
        satellite_daily_loss_halt=sat_daily_halt,
        validation_context=validation_context,
    )
    logger.info(
        "routine_composition_snapshot",
        routine=snapshot.routine,
        sleeve=snapshot.sleeve,
        environment=snapshot.environment.value,
        dry_run=snapshot.dry_run,
        kill_switch_trading_allowed=snapshot.kill_switch_trading_allowed,
        account_status=snapshot.account_status,
        positions_count=snapshot.positions_count,
        allowed_symbol_count=snapshot.allowed_symbol_count,
        core_drawdown_halt=snapshot.core_drawdown_halt,
        core_uncle_triggered=snapshot.core_uncle_triggered,
        satellite_uncle_triggered=snapshot.satellite_uncle_triggered,
        core_soft_wind_down_spy_only=snapshot.core_soft_wind_down_spy_only,
    )

    snapshot = _write_envelope_records(snapshot, active_config, active_settings)
    return snapshot


def build_validation_context_from_account(
    account: AlpacaAccountOutput,
    *,
    settings: Settings,
    allowed_symbols: frozenset[str],
    kill_switch_or_trading_paused: bool,
    core_drawdown_halt: bool = False,
    core_uncle_triggered: bool = False,
    satellite_uncle_triggered: bool = False,
    core_soft_wind_down_spy_only: bool = False,
    core_daily_loss_halt_today: bool = False,
    satellite_daily_loss_halt_today: bool = False,
    trades_today_in_sleeve: int = 0,
) -> ValidationContext:
    """Map broker/settings state into the pure `validate_order()` context."""

    pdt_threshold = Decimal(str(settings.pdt_account_equity_threshold_usd))
    max_core_deploy: Decimal | None = None
    if settings.phase_core_deploy_cap_usd is not None:
        max_core_deploy = Decimal(str(settings.phase_core_deploy_cap_usd))
    return ValidationContext(
        core_nav_usd=Decimal(str(settings.core_sleeve_target_usd)),
        satellite_nav_usd=Decimal(str(settings.satellite_sleeve_target_usd)),
        account_equity_usd=account.equity_usd,
        core_allowed_symbols=allowed_symbols,
        satellite_allowed_symbols=allowed_symbols,
        pdt_restricted=account.equity_usd < pdt_threshold,
        day_trades_in_rolling_5_sessions=account.daytrade_count,
        order_would_be_day_trade=False,
        kill_switch_or_trading_paused=kill_switch_or_trading_paused,
        buying_power_usd=account.buying_power_usd,
        core_drawdown_halt=core_drawdown_halt,
        core_uncle_triggered=core_uncle_triggered,
        satellite_uncle_triggered=satellite_uncle_triggered,
        core_soft_wind_down_spy_only=core_soft_wind_down_spy_only,
        core_daily_loss_halt_today=core_daily_loss_halt_today,
        satellite_daily_loss_halt_today=satellite_daily_loss_halt_today,
        trades_today_in_sleeve=trades_today_in_sleeve,
        max_core_deploy_usd=max_core_deploy,
    )


def _write_envelope_records(
    snapshot: RoutineCompositionSnapshot,
    config: RoutineCompositionConfig,
    settings: Settings,
) -> RoutineCompositionSnapshot:
    """Emit audit + optional NO_TRADE journal records; return snapshot with paths set."""
    from darkhorse.routines.envelopes import build_no_trade_decision, build_routine_start_audit
    from darkhorse.tools import utc_now

    audit_dir = config.audit_dir or settings.journal_dir / "audit"
    today = utc_now().strftime("%Y-%m-%d")
    audit_path = audit_dir / f"{today}.jsonl"

    audit_record = build_routine_start_audit(snapshot)
    append_audit_record(audit_path, audit_record)
    logger.debug("routine_audit_written", audit_path=str(audit_path))

    journal_path: Path | None = None
    trading_blocked = (
        not snapshot.kill_switch_trading_allowed
        or snapshot.account_trading_blocked
        or snapshot.core_drawdown_halt
        or snapshot.core_uncle_triggered
        or snapshot.satellite_uncle_triggered
    )
    if trading_blocked:
        reasons: list[str] = []
        if not snapshot.kill_switch_trading_allowed:
            reasons.append("kill_switch")
        if snapshot.account_trading_blocked:
            reasons.append("account_trading_blocked")
        if snapshot.core_drawdown_halt:
            reasons.append("core_drawdown_halt")
        if snapshot.core_uncle_triggered:
            reasons.append("core_uncle")
        if snapshot.satellite_uncle_triggered:
            reasons.append("satellite_uncle")

        jnl_dir = config.journal_dir or settings.journal_dir / config.sleeve / "journal"
        journal_path = jnl_dir / f"{today}.jsonl"
        no_trade = build_no_trade_decision(snapshot, ", ".join(reasons))
        append_jsonl_record(journal_path, no_trade)
        logger.info("routine_no_trade_journaled", journal_path=str(journal_path))

    return snapshot.model_copy(update={"audit_path": audit_path, "journal_path": journal_path})


def _compute_drawdown_flags(
    hwm_usd: Decimal | None,
    equity_usd: Decimal | None,
    *,
    sleeve: str,
) -> tuple[bool, bool]:
    """Return ``(halt, uncle)`` if HWM and equity are known, else ``(False, False)``."""
    if hwm_usd is None or equity_usd is None or hwm_usd <= 0:
        return False, False
    if sleeve == "satellite":
        return satellite_drawdown_flags(hwm_usd, equity_usd)
    return core_drawdown_flags(hwm_usd, equity_usd)


def _daily_loss_halt(
    daily_pnl_usd: Decimal | None,
    sleeve_nav_usd: Decimal,
    daily_loss_kill_pct: Decimal,
) -> bool:
    """True when daily P&L loss exceeds the sleeve's daily kill threshold."""
    if daily_pnl_usd is None or sleeve_nav_usd <= 0:
        return False
    loss_threshold = -(sleeve_nav_usd * daily_loss_kill_pct)
    return daily_pnl_usd <= loss_threshold


def _darkhorse_kill_env(config: RoutineCompositionConfig) -> str | None:
    if config.darkhorse_kill_env is not None:
        return config.darkhorse_kill_env
    return os.getenv("DARKHORSE_KILL")
