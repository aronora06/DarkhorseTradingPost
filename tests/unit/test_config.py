"""`config.Settings` loads secrets + `config/settings.toml`."""

from __future__ import annotations

import pytest

from darkhorse.config import Settings, clear_settings_cache, get_settings


def _set_minimal_env(monkeypatch: pytest.MonkeyPatch) -> None:
    secrets = {
        "ANTHROPIC_API_KEY": "sk-test-ant",
        "ALPACA_LIVE_API_KEY": "live(key",
        "ALPACA_LIVE_SECRET_KEY": "live(sec",
        "ALPACA_PAPER_API_KEY": "paper(key",
        "ALPACA_PAPER_SECRET_KEY": "paper(sec",
        "PERPLEXITY_API_KEY": "pplx",
        "TAVILY_API_KEY": "tvly",
        "FINNHUB_API_KEY": "finn",
        "SNAPTRADE_CLIENT_ID": "snap",
        "SNAPTRADE_CONSUMER_KEY": "snapc",
        "DISCORD_WEBHOOK_URL": "https://discord.test/webhook",
    }
    for key, val in secrets.items():
        monkeypatch.setenv(key, val)


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> None:
    clear_settings_cache()
    yield
    clear_settings_cache()


def test_settings_core_targets_from_toml(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_minimal_env(monkeypatch)
    s = Settings()
    assert s.core_sleeve_target_usd == 900
    assert s.satellite_sleeve_target_usd == 100
    assert s.stale_review_days == 14


def test_get_settings_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_minimal_env(monkeypatch)
    a = get_settings()
    b = get_settings()
    assert a is b
