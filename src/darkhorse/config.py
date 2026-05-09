"""Typed application settings (`plans/decisions/0012-configuration-and-secrets.md`)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_TOML = REPO_ROOT / "config" / "settings.toml"
ENV_FILE = REPO_ROOT / ".env"


class Settings(BaseSettings):
    """Load precedence (low → high): constructor → ``settings.toml`` → ``.env`` → process env."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    anthropic_api_key: SecretStr
    alpaca_live_api_key: SecretStr
    alpaca_live_secret_key: SecretStr
    alpaca_paper_api_key: SecretStr
    alpaca_paper_secret_key: SecretStr
    perplexity_api_key: SecretStr
    tavily_api_key: SecretStr
    finnhub_api_key: SecretStr
    snaptrade_client_id: SecretStr
    snaptrade_consumer_key: SecretStr
    discord_webhook_url: SecretStr

    env: str = Field(default="production", description='"production" | "dev"')
    journal_dir: Path = Field(default=Path("memory"))
    sqlite_mirror_path: Path = Field(default=Path("memory/index.sqlite"))
    killswitch_path: Path = Field(default=Path("KILLSWITCH"))
    remote_kill_url: str | None = Field(default=None)
    dead_letter_dir: Path = Field(default=Path("memory/_dead_letter"))

    core_sleeve_target_usd: int = 900
    satellite_sleeve_target_usd: int = 100
    max_position_pct_core: float = 0.12
    max_position_pct_satellite: float = 0.50
    satellite_first_tranche_max_pct: float = 0.25
    buying_power_buffer_usd: float = 5.0
    daily_loss_kill_pct_core: float = 0.02
    daily_loss_kill_pct_satellite: float = 0.10
    drawdown_halt_pct_core: float = 0.15
    max_trades_per_day_per_sleeve: int = 3
    pdt_account_equity_threshold_usd: float = 25000.0
    pdt_buffered_day_trade_block_at: int = 2
    monthly_compute_cap_usd: float = 10.0
    routine_cost_cap_usd: float = 0.50
    stale_review_days: int = 14

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            TomlConfigSettingsSource(settings_cls, SETTINGS_TOML),
            dotenv_settings,
            env_settings,
            file_secret_settings,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Process-wide cached settings (`Settings()` loads once)."""
    return Settings()


def clear_settings_cache() -> None:
    """Call from tests when env vars change between cases."""
    get_settings.cache_clear()
