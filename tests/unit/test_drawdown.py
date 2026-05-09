"""Risk: drawdown & HWM (`tests/specs/drawdown.md`)."""

from decimal import Decimal

import pytest

from darkhorse.risk.drawdown import (
    core_drawdown_flags,
    drawdown_fraction,
    next_high_water_mark,
    satellite_drawdown_flags,
)


def test_hwm_only_increases() -> None:
    hwm = Decimal("1000")
    assert next_high_water_mark(hwm, Decimal("900")) == Decimal("1000")
    assert next_high_water_mark(hwm, Decimal("1100")) == Decimal("1100")


def test_recovery_does_not_shrink_hwm() -> None:
    hwm = Decimal("1000")
    hwm = next_high_water_mark(hwm, Decimal("800"))
    assert hwm == Decimal("1000")
    hwm = next_high_water_mark(hwm, Decimal("950"))
    assert hwm == Decimal("1000")


def test_core_dd_halt_threshold() -> None:
    hwm = Decimal("1000")
    halt, uncle = core_drawdown_flags(hwm, Decimal("850.01"))
    assert not halt
    assert not uncle
    halt2, uncle2 = core_drawdown_flags(hwm, Decimal("850.00"))
    assert halt2
    assert not uncle2


def test_core_uncle_threshold() -> None:
    hwm = Decimal("1000")
    halt, uncle = core_drawdown_flags(hwm, Decimal("750.00"))
    assert halt
    assert uncle
    assert drawdown_fraction(hwm, Decimal("750")) == Decimal("-0.25")


def test_satellite_skips_dd_halt_respects_uncle() -> None:
    hwm = Decimal("100")
    _, u81 = satellite_drawdown_flags(hwm, Decimal("19"))  # −81%
    assert u81 is True
    _, u80 = satellite_drawdown_flags(hwm, Decimal("20"))  # −80%
    assert u80 is True


def test_drawdown_fraction_rejects_non_positive_hwm() -> None:
    with pytest.raises(ValueError, match="positive"):
        drawdown_fraction(Decimal("0"), Decimal("100"))
