"""Order validation — risk lives in code (`tests/specs/validate_order.md` + doctrine/).

Every rejection must cite a stable rule id for logs, tests, and audits.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Final

from pydantic import BaseModel, Field

_SPY: Final[str] = "SPY"


class ValidationVerdict(StrEnum):
    PASS = "pass"
    REJECT = "reject"
    DEFER = "defer"


class Sleeve(StrEnum):
    CORE = "core"
    SATELLITE = "satellite"


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    LIMIT = "limit"
    MARKET = "market"


class RiskLimits(BaseModel):
    """Tunable thresholds — defaults match Phase 1 doctrine / `config/settings.toml`."""

    core_max_single_name_pct: Decimal = Decimal("0.12")
    satellite_max_single_name_pct: Decimal = Decimal("0.50")
    satellite_first_tranche_max_pct: Decimal = Decimal("0.25")
    max_trades_per_day_per_sleeve: int = 3
    pdt_account_equity_threshold_usd: Decimal = Decimal("25000")
    pdt_buffered_day_trade_block_at: int = 2
    buying_power_buffer_usd: Decimal = Decimal("5")


class OrderRequest(BaseModel):
    """Intent to trade after sizing; still subject to hard gates."""

    sleeve: Sleeve
    symbol: str
    side: Side
    order_type: OrderType
    qty: int = Field(ge=1)
    limit_price: Decimal | None = None
    """Required when ``order_type`` is limit (caller must enforce)."""

    estimated_notional_usd: Decimal = Field(gt=Decimal("0"))
    market_order_exception: bool = False
    """Risk-manager flag: market allowed (`doctrine/core_sleeve.md` + `riskMitigation` R4)."""

    satellite_first_tranche: bool = False
    """If true, Satellite entries are capped at first-tranche % (`satellite_sleeve.md`)."""

    wind_down_liquidation: bool = False
    """Human/system exception: uncle / mechanical SPY conversion path only."""


class ValidationContext(BaseModel):
    model_config = {"frozen": False}

    core_nav_usd: Decimal = Field(gt=Decimal("0"))
    satellite_nav_usd: Decimal = Field(gt=Decimal("0"))
    account_equity_usd: Decimal = Field(gt=Decimal("0"))

    core_allowed_symbols: frozenset[str]
    satellite_allowed_symbols: frozenset[str]

    symbol_passes_core_price_liquidity: bool = True
    symbol_passes_satellite_price_liquidity: bool = True
    core_symbol_in_earnings_window: bool = False
    symbol_is_otc_or_penny: bool = False

    pdt_restricted: bool
    """True when equity is under PDT threshold (derived by caller)."""

    day_trades_in_rolling_5_sessions: int | None
    """Broker count; ``None`` = unknown / ambiguous."""

    order_would_be_day_trade: bool

    core_daily_loss_halt_today: bool = False
    satellite_daily_loss_halt_today: bool = False

    core_drawdown_halt: bool = False
    core_uncle_triggered: bool = False
    satellite_uncle_triggered: bool = False

    kill_switch_or_trading_paused: bool = False

    core_soft_wind_down_spy_only: bool = False
    """Rolling Sharpe wind-down (`plans/riskMitigation.md` §6)."""

    core_hard_wind_down_liquidate_to_spy: bool = False
    """Uncle / governance liquidation posture — only SPY + mechanical exits."""

    trades_today_in_sleeve: int = 0

    buying_power_usd: Decimal | None = None
    current_position_qty_for_symbol: int | None = None
    """Shares held in this sleeve:symbol; optional naked-short guard."""

    max_core_deploy_usd: Decimal | None = None
    """Phase 4 micro-cap: total Core notional already deployed + this order cap."""


def validate_order(
    order: OrderRequest,
    ctx: ValidationContext,
    limits: RiskLimits | None = None,
) -> ValidationResult:
    """Return PASS / REJECT / DEFER with rule id and message.

    Caller supplies account-derived flags; this function is pure (no I/O).
    """
    lim = limits or RiskLimits()
    sym = order.symbol.strip().upper()
    order = order.model_copy(update={"symbol": sym})

    checks: list[tuple[str, str, ValidationVerdict]] = [
        *_halt_and_wind_down_checks(order, ctx),
        *_pdt_checks(order, ctx, lim),
        *_universe_and_filter_checks(order, ctx),
        *_sizing_checks(order, ctx, lim),
        *_order_type_and_cadence_checks(order, ctx, lim),
        *_buying_power_checks(order, ctx, lim),
        *_position_continuity_checks(order, ctx),
    ]

    for rule_id, message, verdict in checks:
        return ValidationResult(verdict=verdict, rule_id=rule_id, message=message)

    return ValidationResult(
        verdict=ValidationVerdict.PASS,
        rule_id="R-VOK",
        message="all gates passed",
    )


class ValidationResult(BaseModel):
    verdict: ValidationVerdict
    rule_id: str
    message: str


def _halt_and_wind_down_checks(
    order: OrderRequest,
    ctx: ValidationContext,
) -> list[tuple[str, str, ValidationVerdict]]:
    out: list[tuple[str, str, ValidationVerdict]] = []
    if ctx.kill_switch_or_trading_paused:
        out.append(
            (
                "KS-GLOBAL",
                "trading paused / kill-switch active",
                ValidationVerdict.REJECT,
            ),
        )
        return out

    uncle_hit = ctx.core_uncle_triggered or ctx.satellite_uncle_triggered
    if uncle_hit and not order.wind_down_liquidation:
        out.append(
            (
                "R-V05-UNCLE",
                "uncle point active — discretionary orders blocked pending human reset",
                ValidationVerdict.REJECT,
            ),
        )
        return out

    if ctx.core_hard_wind_down_liquidate_to_spy and not order.wind_down_liquidation:
        out.append(
            (
                "WD-HARD",
                "hard wind-down — only mechanical liquidation orders permitted",
                ValidationVerdict.REJECT,
            ),
        )
        return out

    if ctx.core_soft_wind_down_spy_only and order.sleeve is Sleeve.CORE:
        if order.side is Side.BUY and order.symbol != _SPY:
            out.append(
                (
                    "WD-SOFT",
                    "soft wind-down — Core buys limited to SPY only",
                    ValidationVerdict.REJECT,
                ),
            )
        if order.side is Side.SELL and order.symbol == _SPY:
            out.append(
                (
                    "WD-SOFT",
                    "soft wind-down — disallow selling SPY (index posture)",
                    ValidationVerdict.REJECT,
                ),
            )

    dd_halt_blocks_buys = order.sleeve is Sleeve.CORE and ctx.core_drawdown_halt
    if dd_halt_blocks_buys and order.side is Side.BUY:
        out.append(
            (
                "R-V05-DD-HALT",
                "Core drawdown halt — risk-increasing orders blocked",
                ValidationVerdict.REJECT,
            ),
        )

    daily_halt = (
        ctx.core_daily_loss_halt_today
        if order.sleeve is Sleeve.CORE
        else ctx.satellite_daily_loss_halt_today
    )
    if daily_halt and order.side is Side.BUY:
        out.append(
            (
                "R-V04-DAILY-LOSS",
                "daily loss kill active — opening buys blocked (flatten-only via sells)",
                ValidationVerdict.REJECT,
            ),
        )

    return out


def _pdt_checks(
    order: OrderRequest,
    ctx: ValidationContext,
    lim: RiskLimits,
) -> list[tuple[str, str, ValidationVerdict]]:
    if not ctx.pdt_restricted or not ctx.order_would_be_day_trade:
        return []

    if ctx.day_trades_in_rolling_5_sessions is None:
        return [
            (
                "R-V03-PDT-UNKNOWN",
                "PDT buffer: broker day-trade count unavailable — NO_TRADE pending reconciliation",
                ValidationVerdict.DEFER,
            ),
        ]

    if ctx.day_trades_in_rolling_5_sessions >= lim.pdt_buffered_day_trade_block_at:
        return [
            (
                "R-V03-PDT",
                "PDT buffer: at broker day-trade limit for rolling window — day trade blocked",
                ValidationVerdict.REJECT,
            ),
        ]
    return []


def _universe_and_filter_checks(
    order: OrderRequest,
    ctx: ValidationContext,
) -> list[tuple[str, str, ValidationVerdict]]:
    if ctx.symbol_is_otc_or_penny:
        return [("R-V02-OTC", "symbol fails exchange / price floor", ValidationVerdict.REJECT)]

    if order.sleeve is Sleeve.CORE:
        if order.symbol not in ctx.core_allowed_symbols:
            return [("R-V02-CORE-UNIVERSE", "symbol not Core-eligible", ValidationVerdict.REJECT)]
        if not ctx.symbol_passes_core_price_liquidity:
            msg = "symbol fails Core price/liquidity filters"
            return [("R-V02-CORE-FILTER", msg, ValidationVerdict.REJECT)]
        if ctx.core_symbol_in_earnings_window:
            return [
                ("R-V02-EARNINGS", "Core: symbol inside earnings window", ValidationVerdict.REJECT),
            ]
    else:
        if order.symbol not in ctx.satellite_allowed_symbols:
            msg = "symbol not Satellite-eligible (extension / filters)"
            return [("R-V02-SAT-UNIVERSE", msg, ValidationVerdict.REJECT)]
        if not ctx.symbol_passes_satellite_price_liquidity:
            msg = "symbol fails Satellite price/liquidity filters"
            return [("R-V02-SAT-FILTER", msg, ValidationVerdict.REJECT)]
    return []


def _cap_pct_for_order(order: OrderRequest, lim: RiskLimits) -> Decimal:
    if order.sleeve is Sleeve.CORE:
        return lim.core_max_single_name_pct
    if order.satellite_first_tranche:
        return lim.satellite_first_tranche_max_pct
    return lim.satellite_max_single_name_pct


def _sleeve_nav(order: OrderRequest, ctx: ValidationContext) -> Decimal:
    return ctx.core_nav_usd if order.sleeve is Sleeve.CORE else ctx.satellite_nav_usd


def _sizing_checks(
    order: OrderRequest,
    ctx: ValidationContext,
    lim: RiskLimits,
) -> list[tuple[str, str, ValidationVerdict]]:
    if order.side is Side.SELL:
        return []

    sleeve_nav = _sleeve_nav(order, ctx)
    cap_pct = _cap_pct_for_order(order, lim)
    max_usd = (sleeve_nav * cap_pct).quantize(Decimal("0.01"))

    if order.estimated_notional_usd > max_usd:
        msg = (
            f"notional {order.estimated_notional_usd} exceeds sleeve cap "
            f"{max_usd} ({cap_pct} of NAV)"
        )
        return [
            (
                "R-V01-NOTIONAL",
                msg,
                ValidationVerdict.REJECT,
            ),
        ]

    max_core = ctx.max_core_deploy_usd
    if (
        order.sleeve is Sleeve.CORE
        and max_core is not None
        and order.estimated_notional_usd > max_core
    ):
        return [
            (
                "R-V01-PHASE-CAP",
                f"Core deployment cap exceeded (limit {max_core})",
                ValidationVerdict.REJECT,
            ),
        ]
    return []


def _order_type_and_cadence_checks(
    order: OrderRequest,
    ctx: ValidationContext,
    lim: RiskLimits,
) -> list[tuple[str, str, ValidationVerdict]]:
    if order.order_type is OrderType.MARKET and not order.market_order_exception:
        msg = "market orders blocked without risk-manager exception flag"
        return [("R-V06-MARKET", msg, ValidationVerdict.REJECT)]

    if order.order_type is OrderType.LIMIT and order.limit_price is None:
        return [
            ("R-V06-LIMIT", "limit order requires limit_price", ValidationVerdict.REJECT),
        ]

    if ctx.trades_today_in_sleeve >= lim.max_trades_per_day_per_sleeve:
        return [
            (
                "R-V06-CADENCE",
                f"max trades per day for sleeve reached ({lim.max_trades_per_day_per_sleeve})",
                ValidationVerdict.REJECT,
            ),
        ]
    return []


def _buying_power_checks(
    order: OrderRequest,
    ctx: ValidationContext,
    lim: RiskLimits,
) -> list[tuple[str, str, ValidationVerdict]]:
    if order.side is not Side.BUY:
        return []
    if ctx.buying_power_usd is None:
        return []

    available = ctx.buying_power_usd - lim.buying_power_buffer_usd
    if order.estimated_notional_usd > available:
        return [
            (
                "SZ-04-BP",
                "insufficient buying power after buffer",
                ValidationVerdict.REJECT,
            ),
        ]
    return []


def _position_continuity_checks(
    order: OrderRequest,
    ctx: ValidationContext,
) -> list[tuple[str, str, ValidationVerdict]]:
    if order.side is not Side.SELL:
        return []
    if ctx.current_position_qty_for_symbol is None:
        return []
    if order.qty > ctx.current_position_qty_for_symbol:
        return [
            (
                "R-V01-SHORT",
                "sell qty exceeds tracked position (naked short / state mismatch)",
                ValidationVerdict.REJECT,
            ),
        ]
    return []
