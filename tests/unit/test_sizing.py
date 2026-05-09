"""Risk: sizing (`tests/specs/sizing.md`)."""

from decimal import Decimal

from darkhorse.risk.sizing import (
    buying_power_headroom,
    core_max_sector_usd,
    core_max_single_name_usd,
    order_fits_buying_power,
    satellite_max_position_usd,
    sector_would_breach_cap,
)


def test_core_caps() -> None:
    nav = Decimal("900")
    assert core_max_single_name_usd(nav) == Decimal("108.00")
    assert core_max_sector_usd(nav) == Decimal("225.00")


def test_satellite_first_tranche_vs_full() -> None:
    nav = Decimal("100")
    assert satellite_max_position_usd(nav, first_tranche=True) == Decimal("25.00")
    assert satellite_max_position_usd(nav, first_tranche=False) == Decimal("50.00")


def test_buying_power() -> None:
    assert buying_power_headroom(Decimal("100"), Decimal("5")) == Decimal("95")
    assert order_fits_buying_power(Decimal("90"), Decimal("100"), Decimal("5"))
    assert not order_fits_buying_power(Decimal("96"), Decimal("100"), Decimal("5"))


def test_sector_breach() -> None:
    assert not sector_would_breach_cap(Decimal("200"), Decimal("20"), Decimal("900"))
    assert sector_would_breach_cap(Decimal("220"), Decimal("10"), Decimal("900"))
