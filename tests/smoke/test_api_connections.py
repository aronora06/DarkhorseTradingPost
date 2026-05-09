"""Smoke tests that verify real API connectivity.

These tests are **skipped by default** in CI and local runs.  To run them:

    DARKHORSE_ALLOW_NETWORK_TESTS=1 uv run pytest tests/smoke/ -v

They require a populated ``.env`` file with real API keys.
"""

from __future__ import annotations

import os

import httpx
import pytest

_SKIP_REASON = "Requires DARKHORSE_ALLOW_NETWORK_TESTS=1 and real API keys in .env"
_skip_unless_network = pytest.mark.skipif(
    os.getenv("DARKHORSE_ALLOW_NETWORK_TESTS") != "1",
    reason=_SKIP_REASON,
)

pytestmark = _skip_unless_network


@pytest.fixture()
def settings():  # type: ignore[no-untyped-def]
    from darkhorse.config import Settings, clear_settings_cache

    clear_settings_cache()
    s = Settings()
    yield s
    clear_settings_cache()


class TestAnthropicConnection:
    def test_anthropic_api_key_works(self, settings):  # type: ignore[no-untyped-def]
        """Send a minimal Haiku request to verify the Anthropic API key."""
        api_key = settings.anthropic_api_key.get_secret_value()
        assert api_key and not api_key.startswith("sk-ant-api03-...")

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 16,
                    "messages": [{"role": "user", "content": "Reply OK"}],
                },
            )
            assert response.status_code == 200, f"Anthropic API error: {response.text}"
            body = response.json()
            assert body["type"] == "message"
            print(f"  Anthropic OK — model={body['model']}, tokens={body['usage']}")


class TestAlpacaPaperConnection:
    def test_paper_account_accessible(self, settings):  # type: ignore[no-untyped-def]
        """Fetch the paper account to verify Alpaca paper keys."""
        api_key = settings.alpaca_paper_api_key.get_secret_value()
        secret_key = settings.alpaca_paper_secret_key.get_secret_value()
        assert api_key and not api_key.startswith("PK...")

        with httpx.Client(timeout=15.0) as client:
            response = client.get(
                "https://paper-api.alpaca.markets/v2/account",
                headers={
                    "APCA-API-KEY-ID": api_key,
                    "APCA-API-SECRET-KEY": secret_key,
                },
            )
            assert response.status_code == 200, f"Alpaca paper error: {response.text}"
            body = response.json()
            assert body["status"] == "ACTIVE"
            print(f"  Alpaca paper OK — equity=${body['equity']}, status={body['status']}")

    def test_paper_positions_accessible(self, settings):  # type: ignore[no-untyped-def]
        """Fetch paper positions (may be empty)."""
        api_key = settings.alpaca_paper_api_key.get_secret_value()
        secret_key = settings.alpaca_paper_secret_key.get_secret_value()

        with httpx.Client(timeout=15.0) as client:
            response = client.get(
                "https://paper-api.alpaca.markets/v2/positions",
                headers={
                    "APCA-API-KEY-ID": api_key,
                    "APCA-API-SECRET-KEY": secret_key,
                },
            )
            assert response.status_code == 200, f"Alpaca positions error: {response.text}"
            positions = response.json()
            print(f"  Alpaca paper positions OK — count={len(positions)}")


class TestPerplexityConnection:
    def test_sonar_api_works(self, settings):  # type: ignore[no-untyped-def]
        """Send a minimal Sonar request to verify the Perplexity API key."""
        api_key = settings.perplexity_api_key.get_secret_value()
        assert api_key and not api_key.startswith("pplx-...")

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "sonar",
                    "messages": [{"role": "user", "content": "What is SPY trading at?"}],
                },
            )
            assert response.status_code == 200, f"Perplexity error: {response.text}"
            body = response.json()
            assert "choices" in body
            print(f"  Perplexity Sonar OK — model={body.get('model')}")


class TestTavilyConnection:
    def test_tavily_search_works(self, settings):  # type: ignore[no-untyped-def]
        """Send a minimal Tavily search to verify the API key."""
        api_key = settings.tavily_api_key.get_secret_value()
        assert api_key and not api_key.startswith("tvly-...")

        with httpx.Client(timeout=20.0) as client:
            response = client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": "AAPL stock news",
                    "max_results": 1,
                },
            )
            assert response.status_code == 200, f"Tavily error: {response.text}"
            body = response.json()
            assert "results" in body
            print(f"  Tavily OK — results={len(body['results'])}")


class TestFinnhubConnection:
    def test_finnhub_quote_works(self, settings):  # type: ignore[no-untyped-def]
        """Fetch a Finnhub quote to verify the API key."""
        api_key = settings.finnhub_api_key.get_secret_value()
        assert api_key and api_key != "..."

        with httpx.Client(timeout=15.0) as client:
            response = client.get(
                "https://finnhub.io/api/v1/quote",
                params={"symbol": "AAPL", "token": api_key},
            )
            assert response.status_code == 200, f"Finnhub error: {response.text}"
            body = response.json()
            assert body.get("c", 0) > 0, f"Finnhub returned zero price: {body}"
            print(f"  Finnhub OK — AAPL current=${body['c']}")


class TestDiscordWebhook:
    def test_discord_webhook_sends(self, settings):  # type: ignore[no-untyped-def]
        """Send a test message to the Discord webhook."""
        webhook_url = settings.discord_webhook_url.get_secret_value()
        assert webhook_url and "discord.com/api/webhooks/" in webhook_url

        with httpx.Client(timeout=15.0) as client:
            response = client.post(
                webhook_url,
                json={"content": "[Darkhorse Smoke Test] API connection verified."},
            )
            assert response.status_code in (200, 204), (
                f"Discord webhook error: {response.status_code} {response.text}"
            )
            print("  Discord webhook OK — message sent")
