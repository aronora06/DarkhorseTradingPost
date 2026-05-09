"""High water mark & drawdown gates (`tests/specs/drawdown.md`, `doctrine/risk_policy.md`)."""

from __future__ import annotations

from decimal import Decimal

# Peak-to-trough fractions (negative): equity_dd = (E - P) / P
CORE_DD_HALT_FRACTION = Decimal("-0.15")
CORE_UNCLE_FRACTION = Decimal("-0.25")
SATELLITE_UNCLE_FRACTION = Decimal("-0.80")


def next_high_water_mark(previous_hwm_usd: Decimal, observed_equity_usd: Decimal) -> Decimal:
    """DD-01 / DD-05 — HWM never drops; recovery does not reset peak (use max with prior peak)."""
    return max(previous_hwm_usd, observed_equity_usd)


def drawdown_fraction(high_water_mark_usd: Decimal, equity_usd: Decimal) -> Decimal:
    """DD-01 — (E_t - P) / P."""
    if high_water_mark_usd <= 0:
        msg = "high_water_mark_usd must be positive"
        raise ValueError(msg)
    return (equity_usd - high_water_mark_usd) / high_water_mark_usd


def core_drawdown_flags(
    high_water_mark_usd: Decimal,
    equity_usd: Decimal,
    *,
    halt_fraction: Decimal = CORE_DD_HALT_FRACTION,
    uncle_fraction: Decimal = CORE_UNCLE_FRACTION,
) -> tuple[bool, bool]:
    """Return ``(core_dd_halt, core_uncle)`` from current equity vs HWM.

    DD-02 — at −15% (inclusive): drawdown halt.
    DD-03 — at −25% (inclusive): uncle.
    """
    dd = drawdown_fraction(high_water_mark_usd, equity_usd)
    halt = dd <= halt_fraction
    uncle = dd <= uncle_fraction
    return halt, uncle


def satellite_drawdown_flags(
    high_water_mark_usd: Decimal,
    equity_usd: Decimal,
    *,
    uncle_fraction: Decimal = SATELLITE_UNCLE_FRACTION,
) -> tuple[bool, bool]:
    """DD-04 — Satellite skips Core DD halt; uncle only at −80% (inclusive)."""
    dd = drawdown_fraction(high_water_mark_usd, equity_usd)
    return False, dd <= uncle_fraction
