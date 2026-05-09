"""Deterministic market data tools."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

import httpx

from darkhorse.config import Settings, get_settings
from darkhorse.tools._contracts import (
    BarsInput,
    BarsOutput,
    DataProvider,
    PriceBar,
    QuoteInput,
    QuoteOutput,
    TimeFrame,
    utc_now,
)

_FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
_YAHOO_BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"


def fetch_quote(
    payload: QuoteInput,
    *,
    settings: Settings | None = None,
    client: httpx.Client | None = None,
    timeout_s: float = 10.0,
    stale_after_s: int = 15 * 60,
) -> QuoteOutput:
    """Fetch a quote from Finnhub, falling back to Yahoo Finance chart data."""

    active_settings = settings or get_settings()
    with _client(client, timeout_s) as http_client:
        if payload.preferred_provider is DataProvider.FINNHUB:
            try:
                return _fetch_finnhub_quote(payload, active_settings, http_client, stale_after_s)
            except (httpx.HTTPError, KeyError, TypeError, ValueError):
                return _fetch_yahoo_quote(payload, http_client, stale_after_s)
        return _fetch_yahoo_quote(payload, http_client, stale_after_s)


def fetch_bars(
    payload: BarsInput,
    *,
    settings: Settings | None = None,
    client: httpx.Client | None = None,
    timeout_s: float = 10.0,
    stale_after_s: int = 60 * 60,
) -> BarsOutput:
    """Fetch OHLCV bars from Finnhub, falling back to Yahoo Finance chart data."""

    active_settings = settings or get_settings()
    with _client(client, timeout_s) as http_client:
        if payload.preferred_provider is DataProvider.FINNHUB:
            try:
                return _fetch_finnhub_bars(payload, active_settings, http_client, stale_after_s)
            except (httpx.HTTPError, KeyError, TypeError, ValueError):
                return _fetch_yahoo_bars(payload, http_client, stale_after_s)
        return _fetch_yahoo_bars(payload, http_client, stale_after_s)


def _fetch_finnhub_quote(
    payload: QuoteInput,
    settings: Settings,
    client: httpx.Client,
    stale_after_s: int,
) -> QuoteOutput:
    response = client.get(
        f"{_FINNHUB_BASE_URL}/quote",
        params={
            "symbol": payload.symbol,
            "token": settings.finnhub_api_key.get_secret_value(),
        },
    )
    response.raise_for_status()
    data = response.json()
    timestamp = datetime.fromtimestamp(int(data["t"]), UTC)
    fetched_at = utc_now()
    return QuoteOutput(
        symbol=payload.symbol,
        provider=DataProvider.FINNHUB,
        bid_usd=None,
        ask_usd=None,
        last_usd=Decimal(str(data["c"])),
        volume=None,
        market_timestamp=timestamp,
        fetched_at=fetched_at,
        is_stale=_is_stale(timestamp, fetched_at, stale_after_s),
    )


def _fetch_yahoo_quote(
    payload: QuoteInput,
    client: httpx.Client,
    stale_after_s: int,
) -> QuoteOutput:
    response = client.get(
        f"{_YAHOO_BASE_URL}/{payload.symbol}",
        params={"range": "1d", "interval": "1m"},
    )
    response.raise_for_status()
    result = _first_chart_result(response.json())
    meta = result["meta"]
    timestamp = datetime.fromtimestamp(int(meta["regularMarketTime"]), UTC)
    fetched_at = utc_now()
    return QuoteOutput(
        symbol=payload.symbol,
        provider=DataProvider.YFINANCE,
        last_usd=Decimal(str(meta["regularMarketPrice"])),
        market_timestamp=timestamp,
        fetched_at=fetched_at,
        is_stale=_is_stale(timestamp, fetched_at, stale_after_s),
    )


def _fetch_finnhub_bars(
    payload: BarsInput,
    settings: Settings,
    client: httpx.Client,
    stale_after_s: int,
) -> BarsOutput:
    response = client.get(
        f"{_FINNHUB_BASE_URL}/stock/candle",
        params={
            "symbol": payload.symbol,
            "resolution": _finnhub_resolution(payload.timeframe),
            "from": int(payload.start.timestamp()),
            "to": int(payload.end.timestamp()),
            "token": settings.finnhub_api_key.get_secret_value(),
        },
    )
    response.raise_for_status()
    data = response.json()
    if data.get("s") != "ok":
        raise ValueError("Finnhub candles unavailable")
    bars = tuple(
        PriceBar(
            timestamp=datetime.fromtimestamp(int(ts), UTC),
            open_usd=Decimal(str(open_)),
            high_usd=Decimal(str(high)),
            low_usd=Decimal(str(low)),
            close_usd=Decimal(str(close)),
            volume=int(volume),
        )
        for ts, open_, high, low, close, volume in zip(
            data["t"],
            data["o"],
            data["h"],
            data["l"],
            data["c"],
            data["v"],
            strict=True,
        )
    )
    fetched_at = utc_now()
    return BarsOutput(
        symbol=payload.symbol,
        provider=DataProvider.FINNHUB,
        timeframe=payload.timeframe,
        bars=bars,
        fetched_at=fetched_at,
        is_stale=_bars_are_stale(bars, fetched_at, stale_after_s),
    )


def _fetch_yahoo_bars(
    payload: BarsInput,
    client: httpx.Client,
    stale_after_s: int,
) -> BarsOutput:
    response = client.get(
        f"{_YAHOO_BASE_URL}/{payload.symbol}",
        params={
            "period1": int(payload.start.timestamp()),
            "period2": int(payload.end.timestamp()),
            "interval": _yahoo_interval(payload.timeframe),
        },
    )
    response.raise_for_status()
    result = _first_chart_result(response.json())
    quote = result["indicators"]["quote"][0]
    bars = tuple(
        PriceBar(
            timestamp=datetime.fromtimestamp(int(ts), UTC),
            open_usd=Decimal(str(open_)),
            high_usd=Decimal(str(high)),
            low_usd=Decimal(str(low)),
            close_usd=Decimal(str(close)),
            volume=int(volume or 0),
        )
        for ts, open_, high, low, close, volume in zip(
            result["timestamp"],
            quote["open"],
            quote["high"],
            quote["low"],
            quote["close"],
            quote["volume"],
            strict=True,
        )
        if None not in (open_, high, low, close)
    )
    fetched_at = utc_now()
    return BarsOutput(
        symbol=payload.symbol,
        provider=DataProvider.YFINANCE,
        timeframe=payload.timeframe,
        bars=bars,
        fetched_at=fetched_at,
        is_stale=_bars_are_stale(bars, fetched_at, stale_after_s),
    )


def _first_chart_result(data: dict[str, Any]) -> dict[str, Any]:
    result = data["chart"]["result"]
    if not result:
        raise ValueError("Yahoo chart returned no result")
    return cast(dict[str, Any], result[0])


def _finnhub_resolution(timeframe: TimeFrame) -> str:
    return {
        TimeFrame.ONE_MINUTE: "1",
        TimeFrame.FIVE_MINUTES: "5",
        TimeFrame.FIFTEEN_MINUTES: "15",
        TimeFrame.ONE_HOUR: "60",
        TimeFrame.ONE_DAY: "D",
    }[timeframe]


def _yahoo_interval(timeframe: TimeFrame) -> str:
    return {
        TimeFrame.ONE_MINUTE: "1m",
        TimeFrame.FIVE_MINUTES: "5m",
        TimeFrame.FIFTEEN_MINUTES: "15m",
        TimeFrame.ONE_HOUR: "60m",
        TimeFrame.ONE_DAY: "1d",
    }[timeframe]


def _is_stale(timestamp: datetime, fetched_at: datetime, stale_after_s: int) -> bool:
    return (fetched_at - timestamp).total_seconds() > stale_after_s


def _bars_are_stale(bars: tuple[PriceBar, ...], fetched_at: datetime, stale_after_s: int) -> bool:
    if not bars:
        return True
    return _is_stale(bars[-1].timestamp, fetched_at, stale_after_s)


class _ClientContext:
    def __init__(self, client: httpx.Client | None, timeout_s: float) -> None:
        self._client = client
        self._timeout_s = timeout_s
        self._owned: httpx.Client | None = None

    def __enter__(self) -> httpx.Client:
        if self._client is not None:
            return self._client
        self._owned = httpx.Client(timeout=self._timeout_s)
        return self._owned

    def __exit__(self, *_exc: object) -> None:
        if self._owned is not None:
            self._owned.close()


def _client(client: httpx.Client | None, timeout_s: float) -> _ClientContext:
    return _ClientContext(client, timeout_s)
