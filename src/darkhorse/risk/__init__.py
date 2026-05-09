"""Risk boundaries: validation, sizing, halts, wind-down."""

from darkhorse.risk.drawdown import (
    CORE_DD_HALT_FRACTION,
    CORE_UNCLE_FRACTION,
    SATELLITE_UNCLE_FRACTION,
    core_drawdown_flags,
    drawdown_fraction,
    next_high_water_mark,
    satellite_drawdown_flags,
)
from darkhorse.risk.kill_switch import (
    KillSwitchReport,
    evaluate_kill_switch,
    monthly_spend_exceeds_cap,
    stale_human_review_pause,
)
from darkhorse.risk.sizing import (
    buying_power_headroom,
    core_max_sector_usd,
    core_max_single_name_usd,
    order_fits_buying_power,
    satellite_max_position_usd,
    sector_would_breach_cap,
)
from darkhorse.risk.validate_order import (
    OrderRequest,
    OrderType,
    RiskLimits,
    Side,
    Sleeve,
    ValidationContext,
    ValidationResult,
    ValidationVerdict,
    validate_order,
)
from darkhorse.risk.wind_down import soft_wind_down_core_to_spy

__all__ = [
    "CORE_DD_HALT_FRACTION",
    "CORE_UNCLE_FRACTION",
    "KillSwitchReport",
    "OrderRequest",
    "OrderType",
    "SATELLITE_UNCLE_FRACTION",
    "RiskLimits",
    "Side",
    "Sleeve",
    "ValidationContext",
    "ValidationResult",
    "ValidationVerdict",
    "buying_power_headroom",
    "core_drawdown_flags",
    "core_max_sector_usd",
    "core_max_single_name_usd",
    "drawdown_fraction",
    "evaluate_kill_switch",
    "monthly_spend_exceeds_cap",
    "next_high_water_mark",
    "order_fits_buying_power",
    "satellite_drawdown_flags",
    "satellite_max_position_usd",
    "sector_would_breach_cap",
    "soft_wind_down_core_to_spy",
    "stale_human_review_pause",
    "validate_order",
]
