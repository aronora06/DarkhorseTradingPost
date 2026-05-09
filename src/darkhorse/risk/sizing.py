"""Position sizing helpers (`tests/specs/sizing.md`, `doctrine/core_sleeve.md`)."""

from __future__ import annotations

from decimal import Decimal


def core_max_single_name_usd(core_nav_usd: Decimal, *, pct: Decimal = Decimal("0.12")) -> Decimal:
    """SZ-01 — max dollars of new risk per Core name (default 12% NAV)."""
    return (core_nav_usd * pct).quantize(Decimal("0.01"))


def core_max_sector_usd(core_nav_usd: Decimal, *, pct: Decimal = Decimal("0.25")) -> Decimal:
    """SZ-02 — max dollars per GICS sector (25% NAV)."""
    return (core_nav_usd * pct).quantize(Decimal("0.01"))


def satellite_max_position_usd(
    satellite_nav_usd: Decimal,
    *,
    first_tranche: bool,
    full_pct: Decimal = Decimal("0.50"),
    first_tranche_pct: Decimal = Decimal("0.25"),
) -> Decimal:
    """SZ-03 — Satellite concentration cap."""
    pct = first_tranche_pct if first_tranche else full_pct
    return (satellite_nav_usd * pct).quantize(Decimal("0.01"))


def buying_power_headroom(buying_power_usd: Decimal, buffer_usd: Decimal) -> Decimal:
    """SZ-04 — spendable notional after buffer."""
    return buying_power_usd - buffer_usd


def order_fits_buying_power(
    notional_usd: Decimal,
    buying_power_usd: Decimal,
    buffer_usd: Decimal,
) -> bool:
    """SZ-04 — True if ``notional`` fits under ``buying_power - buffer``."""
    return notional_usd <= buying_power_headroom(buying_power_usd, buffer_usd)


def sector_would_breach_cap(
    current_sector_exposure_usd: Decimal,
    proposed_add_usd: Decimal,
    core_nav_usd: Decimal,
    *,
    max_sector_pct: Decimal = Decimal("0.25"),
) -> bool:
    """SZ-02 — True if adding exposure would exceed sector cap."""
    cap = core_max_sector_usd(core_nav_usd, pct=max_sector_pct)
    projected = current_sector_exposure_usd + proposed_add_usd
    return projected > cap
