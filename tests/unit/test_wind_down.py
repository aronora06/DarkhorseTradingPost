"""Risk: soft wind-down (`plans/riskMitigation.md` §6)."""

from decimal import Decimal

from darkhorse.risk.wind_down import soft_wind_down_core_to_spy


def test_wind_down_when_underperforming_but_not_deep_drawdown() -> None:
    assert soft_wind_down_core_to_spy(-0.01, Decimal("-0.05"))


def test_no_wind_down_when_sharpe_positive() -> None:
    assert not soft_wind_down_core_to_spy(0.1, Decimal("-0.05"))


def test_no_wind_down_when_missing_inputs() -> None:
    assert not soft_wind_down_core_to_spy(None, Decimal("-0.05"))
    assert not soft_wind_down_core_to_spy(-0.1, None)


def test_no_wind_down_when_drawdown_past_floor() -> None:
    assert not soft_wind_down_core_to_spy(-0.1, Decimal("-0.11"))
