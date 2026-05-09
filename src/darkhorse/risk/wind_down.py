"""Rolling performance wind-down rule (`plans/riskMitigation.md` §6)."""

from __future__ import annotations

from decimal import Decimal


def soft_wind_down_core_to_spy(
    rolling_6m_sharpe_vs_spy: float | None,
    core_total_return_since_start: Decimal | None,
    *,
    return_floor: Decimal = Decimal("-0.10"),
) -> bool:
    """True when Core should convert to SPY-only posture (soft wind-down).

    Condition (from risk mitigation §6): rolling 6-month Sharpe vs SPY is
    **strictly negative** and Core sleeve return since experiment start is
    **strictly greater than** ``return_floor`` (default −10%, i.e. not deeper
    than −10% drawdown from start).

    Missing inputs return False (no signal).
    """
    if rolling_6m_sharpe_vs_spy is None or core_total_return_since_start is None:
        return False
    if rolling_6m_sharpe_vs_spy >= 0:
        return False
    return core_total_return_since_start > return_floor
