"""Market data tool tests with mocked HTTP."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import httpx

from darkhorse.config import Settings
from darkhorse.tools import BarsInput, DataProvider, QuoteInput, TimeFrame
from darkhorse.tools.data import fetch_bars, fetch_quote


def _settings() -> Settings:
    return Settings(
        anthropic_api_key="sk-test-ant",
        alpaca_live_api_key="live-key",
        alpaca_live_secret_key="live-secret",
        alpaca_paper_api_key="paper-key",
        alpaca_paper_secret_key="paper-secret",
        perplexity_api_key="pplx",
        tavily_api_key="tvly",
        finnhub_api_key="finn",
        snaptrade_client_id="snap",
        snaptrade_consumer_key="snapc",
        discord_webhook_url="https://discord.test/webhook",
    )


def test_fetch_quote_uses_finnhub() -> None:
    ts = int(datetime(2026, 5, 9, 13, 35, tzinfo=UTC).timestamp())

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/quote"
        assert request.url.params["symbol"] == "AAPL"
        assert request.url.params["token"] == "finn"
        return httpx.Response(200, json={"c": 189.5, "t": ts})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        quote = fetch_quote(
            QuoteInput(symbol="aapl"),
            settings=_settings(),
            client=client,
            stale_after_s=10**9,
        )

    assert quote.symbol == "AAPL"
    assert quote.provider is DataProvider.FINNHUB
    assert quote.last_usd == Decimal("189.5")
    assert quote.is_stale is False


def test_fetch_quote_falls_back_to_yahoo() -> None:
    calls = 0
    ts = int(datetime(2026, 5, 9, 13, 35, tzinfo=UTC).timestamp())

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503)
        assert request.url.host == "query1.finance.yahoo.com"
        return httpx.Response(
            200,
            json={
                "chart": {
                    "result": [
                        {
                            "meta": {
                                "regularMarketPrice": 190.25,
                                "regularMarketTime": ts,
                            },
                        },
                    ],
                },
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        quote = fetch_quote(
            QuoteInput(symbol="AAPL"),
            settings=_settings(),
            client=client,
            stale_after_s=10**9,
        )

    assert calls == 2
    assert quote.provider is DataProvider.YFINANCE
    assert quote.last_usd == Decimal("190.25")


def test_fetch_bars_uses_finnhub_candles() -> None:
    start = datetime(2026, 5, 9, 13, 30, tzinfo=UTC)
    end = datetime(2026, 5, 9, 13, 35, tzinfo=UTC)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/stock/candle"
        assert request.url.params["resolution"] == "5"
        return httpx.Response(
            200,
            json={
                "s": "ok",
                "t": [int(start.timestamp())],
                "o": [100.0],
                "h": [101.0],
                "l": [99.5],
                "c": [100.5],
                "v": [12345],
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        bars = fetch_bars(
            BarsInput(symbol="AAPL", timeframe=TimeFrame.FIVE_MINUTES, start=start, end=end),
            settings=_settings(),
            client=client,
            stale_after_s=10**9,
        )

    assert bars.provider is DataProvider.FINNHUB
    assert len(bars.bars) == 1
    assert bars.bars[0].close_usd == Decimal("100.5")
