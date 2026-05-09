"""Unit tests for `validate_order` (behavior from `tests/specs/validate_order.md`)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from darkhorse.risk import (
    OrderRequest,
    OrderType,
    RiskLimits,
    Side,
    Sleeve,
    ValidationContext,
    ValidationVerdict,
    validate_order,
)


def _base_ctx(**overrides: object) -> ValidationContext:
    core = frozenset({"SPY", "AAPL", "MSFT"})
    sat = frozenset({"SPY", "AAPL", "MSFT", "PLTR"})
    base = dict(
        core_nav_usd=Decimal("900"),
        satellite_nav_usd=Decimal("100"),
        account_equity_usd=Decimal("1000"),
        core_allowed_symbols=core,
        satellite_allowed_symbols=sat,
        pdt_restricted=False,
        day_trades_in_rolling_5_sessions=0,
        order_would_be_day_trade=False,
    )
    base.update(overrides)
    return ValidationContext.model_validate(base)


def test_core_buy_under_cap_passes() -> None:
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="aapl",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("100"),
        estimated_notional_usd=Decimal("100"),
    )
    r = validate_order(order, _base_ctx())
    assert r.verdict is ValidationVerdict.PASS


def test_core_buy_over_single_name_cap_rejected() -> None:
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("200"),
        estimated_notional_usd=Decimal("120"),
    )
    r = validate_order(order, _base_ctx())
    assert r.verdict is ValidationVerdict.REJECT
    assert r.rule_id == "R-V01-NOTIONAL"


def test_satellite_buy_over_50pct_rejected() -> None:
    order = OrderRequest(
        sleeve=Sleeve.SATELLITE,
        symbol="PLTR",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("60"),
        estimated_notional_usd=Decimal("60"),
    )
    r = validate_order(order, _base_ctx())
    assert r.verdict is ValidationVerdict.REJECT
    assert r.rule_id == "R-V01-NOTIONAL"


def test_satellite_first_tranche_cap_25pct() -> None:
    order = OrderRequest(
        sleeve=Sleeve.SATELLITE,
        symbol="PLTR",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("25"),
        estimated_notional_usd=Decimal("25"),
        satellite_first_tranche=True,
    )
    r = validate_order(order, _base_ctx())
    assert r.verdict is ValidationVerdict.PASS

    order_big = order.model_copy(update={"estimated_notional_usd": Decimal("26")})
    r2 = validate_order(order_big, _base_ctx())
    assert r2.verdict is ValidationVerdict.REJECT


def test_otc_rejected() -> None:
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="PINK",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=10,
        limit_price=Decimal("1"),
        estimated_notional_usd=Decimal("10"),
    )
    ctx = _base_ctx(
        symbol_is_otc_or_penny=True,
        core_allowed_symbols=frozenset({"PINK"}),
    )
    r = validate_order(order, ctx)
    assert r.verdict is ValidationVerdict.REJECT
    assert r.rule_id == "R-V02-OTC"


def test_core_earnings_window_rejected() -> None:
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("100"),
        estimated_notional_usd=Decimal("50"),
    )
    r = validate_order(order, _base_ctx(core_symbol_in_earnings_window=True))
    assert r.verdict is ValidationVerdict.REJECT
    assert r.rule_id == "R-V02-EARNINGS"


def test_satellite_extension_not_on_watchlist_rejected() -> None:
    order = OrderRequest(
        sleeve=Sleeve.SATELLITE,
        symbol="XYZ",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("10"),
        estimated_notional_usd=Decimal("10"),
    )
    ctx = _base_ctx(satellite_allowed_symbols=frozenset({"SPY", "AAPL"}))
    r = validate_order(order, ctx)
    assert r.verdict is ValidationVerdict.REJECT
    assert r.rule_id == "R-V02-SAT-UNIVERSE"


@pytest.mark.parametrize(
    ("count", "expected"),
    [
        (2, ValidationVerdict.REJECT),
        (1, ValidationVerdict.PASS),
    ],
)
def test_pdt_day_trade_buffer(count: int, expected: ValidationVerdict) -> None:
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("10"),
        estimated_notional_usd=Decimal("10"),
    )
    ctx = _base_ctx(
        pdt_restricted=True,
        order_would_be_day_trade=True,
        day_trades_in_rolling_5_sessions=count,
    )
    r = validate_order(order, ctx)
    assert r.verdict is expected


def test_pdt_unknown_defers() -> None:
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("10"),
        estimated_notional_usd=Decimal("10"),
    )
    ctx = _base_ctx(
        pdt_restricted=True,
        order_would_be_day_trade=True,
        day_trades_in_rolling_5_sessions=None,
    )
    r = validate_order(order, ctx)
    assert r.verdict is ValidationVerdict.DEFER
    assert r.rule_id == "R-V03-PDT-UNKNOWN"


def test_daily_loss_halt_blocks_core_buy() -> None:
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("10"),
        estimated_notional_usd=Decimal("10"),
    )
    ctx = _base_ctx(core_daily_loss_halt_today=True)
    r = validate_order(order, ctx)
    assert r.verdict is ValidationVerdict.REJECT
    assert r.rule_id == "R-V04-DAILY-LOSS"


def test_daily_loss_halt_allows_sell() -> None:
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="AAPL",
        side=Side.SELL,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("10"),
        estimated_notional_usd=Decimal("10"),
    )
    ctx = _base_ctx(core_daily_loss_halt_today=True, current_position_qty_for_symbol=2)
    r = validate_order(order, ctx)
    assert r.verdict is ValidationVerdict.PASS


def test_core_drawdown_halt_blocks_buy_allows_sell() -> None:
    buy = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("10"),
        estimated_notional_usd=Decimal("10"),
    )
    ctx = _base_ctx(core_drawdown_halt=True)
    assert validate_order(buy, ctx).verdict is ValidationVerdict.REJECT

    sell = buy.model_copy(update={"side": Side.SELL})
    ctx2 = _base_ctx(core_drawdown_halt=True, current_position_qty_for_symbol=2)
    assert validate_order(sell, ctx2).verdict is ValidationVerdict.PASS


def test_uncle_blocks_discretionary() -> None:
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("10"),
        estimated_notional_usd=Decimal("10"),
    )
    ctx = _base_ctx(core_uncle_triggered=True)
    r = validate_order(order, ctx)
    assert r.verdict is ValidationVerdict.REJECT
    assert r.rule_id == "R-V05-UNCLE"


def test_uncle_allows_flagged_liquidation() -> None:
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="SPY",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("500"),
        estimated_notional_usd=Decimal("100"),
        wind_down_liquidation=True,
    )
    ctx = _base_ctx(core_uncle_triggered=True)
    r = validate_order(order, ctx)
    assert r.verdict is ValidationVerdict.PASS


def test_market_without_exception_rejected() -> None:
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        qty=1,
        limit_price=None,
        estimated_notional_usd=Decimal("50"),
    )
    r = validate_order(order, _base_ctx())
    assert r.verdict is ValidationVerdict.REJECT
    assert r.rule_id == "R-V06-MARKET"


def test_max_trades_per_day() -> None:
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("10"),
        estimated_notional_usd=Decimal("10"),
    )
    ctx = _base_ctx(trades_today_in_sleeve=3)
    r = validate_order(order, ctx, RiskLimits(max_trades_per_day_per_sleeve=3))
    assert r.verdict is ValidationVerdict.REJECT
    assert r.rule_id == "R-V06-CADENCE"


def test_kill_switch_rejects() -> None:
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("10"),
        estimated_notional_usd=Decimal("10"),
    )
    r = validate_order(order, _base_ctx(kill_switch_or_trading_paused=True))
    assert r.verdict is ValidationVerdict.REJECT
    assert r.rule_id == "KS-GLOBAL"


def test_soft_wind_down_spy_only() -> None:
    buy_spy = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="spy",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("500"),
        estimated_notional_usd=Decimal("50"),
    )
    ctx_soft = _base_ctx(core_soft_wind_down_spy_only=True)
    assert validate_order(buy_spy, ctx_soft).verdict is ValidationVerdict.PASS

    buy_aapl = buy_spy.model_copy(update={"symbol": "AAPL", "limit_price": Decimal("200")})
    r = validate_order(buy_aapl, _base_ctx(core_soft_wind_down_spy_only=True))
    assert r.verdict is ValidationVerdict.REJECT

    sell_spy = buy_spy.model_copy(update={"side": Side.SELL})
    ctx_sell = _base_ctx(
        core_soft_wind_down_spy_only=True,
        current_position_qty_for_symbol=5,
    )
    r2 = validate_order(sell_spy, ctx_sell)
    assert r2.verdict is ValidationVerdict.REJECT


def test_phase4_core_cap() -> None:
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("60"),
        estimated_notional_usd=Decimal("60"),
    )
    r = validate_order(order, _base_ctx(max_core_deploy_usd=Decimal("50")))
    assert r.verdict is ValidationVerdict.REJECT
    assert r.rule_id == "R-V01-PHASE-CAP"


def test_core_symbol_not_in_universe() -> None:
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="XYZ",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("10"),
        estimated_notional_usd=Decimal("10"),
    )
    r = validate_order(order, _base_ctx())
    assert r.verdict is ValidationVerdict.REJECT
    assert r.rule_id == "R-V02-CORE-UNIVERSE"


def test_core_liquidity_filter_rejected() -> None:
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("100"),
        estimated_notional_usd=Decimal("50"),
    )
    ctx = _base_ctx(symbol_passes_core_price_liquidity=False)
    r = validate_order(order, ctx)
    assert r.verdict is ValidationVerdict.REJECT
    assert r.rule_id == "R-V02-CORE-FILTER"


def test_satellite_liquidity_filter_rejected() -> None:
    order = OrderRequest(
        sleeve=Sleeve.SATELLITE,
        symbol="PLTR",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("20"),
        estimated_notional_usd=Decimal("20"),
    )
    ctx = _base_ctx(symbol_passes_satellite_price_liquidity=False)
    r = validate_order(order, ctx)
    assert r.verdict is ValidationVerdict.REJECT
    assert r.rule_id == "R-V02-SAT-FILTER"


def test_hard_wind_down_blocks_without_exception() -> None:
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("10"),
        estimated_notional_usd=Decimal("10"),
    )
    ctx = _base_ctx(core_hard_wind_down_liquidate_to_spy=True)
    r = validate_order(order, ctx)
    assert r.verdict is ValidationVerdict.REJECT
    assert r.rule_id == "WD-HARD"


def test_limit_order_requires_price() -> None:
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=None,
        estimated_notional_usd=Decimal("10"),
    )
    r = validate_order(order, _base_ctx())
    assert r.verdict is ValidationVerdict.REJECT
    assert r.rule_id == "R-V06-LIMIT"


def test_naked_short_guard() -> None:
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="AAPL",
        side=Side.SELL,
        order_type=OrderType.LIMIT,
        qty=5,
        limit_price=Decimal("10"),
        estimated_notional_usd=Decimal("50"),
    )
    ctx = _base_ctx(current_position_qty_for_symbol=2)
    r = validate_order(order, ctx)
    assert r.verdict is ValidationVerdict.REJECT
    assert r.rule_id == "R-V01-SHORT"


def test_buying_power_sufficient_continues() -> None:
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("50"),
        estimated_notional_usd=Decimal("50"),
    )
    r = validate_order(
        order,
        _base_ctx(buying_power_usd=Decimal("200")),
        RiskLimits(buying_power_buffer_usd=Decimal("5")),
    )
    assert r.verdict is ValidationVerdict.PASS


def test_buying_power_buffer() -> None:
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("100"),
        estimated_notional_usd=Decimal("100"),
    )
    r = validate_order(
        order,
        _base_ctx(buying_power_usd=Decimal("104")),
        RiskLimits(buying_power_buffer_usd=Decimal("5")),
    )
    assert r.verdict is ValidationVerdict.REJECT
    assert r.rule_id == "SZ-04-BP"
