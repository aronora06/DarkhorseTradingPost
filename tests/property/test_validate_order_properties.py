"""Property tests for `validate_order` (ADR-0009, `tests/specs/validate_order.md`)."""

from __future__ import annotations

from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

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

_symbols = st.sampled_from(["SPY", "AAPL", "MSFT", "PLTR"])
_side = st.sampled_from(Side)


def _ctx(*, kill: bool = False) -> ValidationContext:
    core = frozenset({"SPY", "AAPL", "MSFT", "PLTR"})
    return ValidationContext(
        core_nav_usd=Decimal("900"),
        satellite_nav_usd=Decimal("100"),
        account_equity_usd=Decimal("1000"),
        core_allowed_symbols=core,
        satellite_allowed_symbols=core,
        pdt_restricted=False,
        day_trades_in_rolling_5_sessions=0,
        order_would_be_day_trade=False,
        kill_switch_or_trading_paused=kill,
    )


@given(
    sym=_symbols,
    side=_side,
    qty=st.integers(min_value=1, max_value=20),
    limit_price=st.decimals(
        min_value=Decimal("1"),
        max_value=Decimal("500"),
        places=2,
        allow_nan=False,
    ),
    notional=st.decimals(
        min_value=Decimal("1"),
        max_value=Decimal("108"),
        places=2,
        allow_nan=False,
    ),
)
def test_kill_switch_rejects_any_order(
    sym: str,
    side: Side,
    qty: int,
    limit_price: Decimal,
    notional: Decimal,
) -> None:
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol=sym,
        side=side,
        order_type=OrderType.LIMIT,
        qty=qty,
        limit_price=limit_price,
        estimated_notional_usd=notional,
    )
    r = validate_order(order, _ctx(kill=True))
    assert r.verdict is ValidationVerdict.REJECT
    assert r.rule_id == "KS-GLOBAL"


@given(
    notional=st.decimals(
        min_value=Decimal("109"),
        max_value=Decimal("500"),
        places=2,
        allow_nan=False,
    ),
)
def test_core_buy_above_single_name_cap_rejects(notional: Decimal) -> None:
    order = OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("200"),
        estimated_notional_usd=notional,
    )
    r = validate_order(order, _ctx(), RiskLimits())
    assert r.verdict is ValidationVerdict.REJECT
    assert r.rule_id == "R-V01-NOTIONAL"
