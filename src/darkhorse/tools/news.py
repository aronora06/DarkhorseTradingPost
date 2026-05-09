"""Deterministic news search tools with Unicode normalization."""

from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any

import httpx
import structlog

from darkhorse.config import Settings, get_settings
from darkhorse.tools._contracts import (
    NewsArticle,
    NewsProvider,
    NewsSearchInput,
    NewsSearchOutput,
    utc_now,
)

_SONAR_URL = "https://api.perplexity.ai/chat/completions"
_TAVILY_URL = "https://api.tavily.com/search"
logger = structlog.get_logger(__name__)


def search_news(
    payload: NewsSearchInput,
    *,
    allowed_symbols: frozenset[str] | None = None,
    settings: Settings | None = None,
    client: httpx.Client | None = None,
    timeout_s: float = 20.0,
) -> NewsSearchOutput:
    """Search finance news, normalize text, and reject off-whitelist symbols."""

    active_settings = settings or get_settings()
    with _client(client, timeout_s) as http_client:
        if payload.preferred_provider is NewsProvider.SONAR:
            try:
                articles = _search_sonar(payload, active_settings, http_client)
                return _output(payload, NewsProvider.SONAR, articles, allowed_symbols)
            except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
                logger.warning(
                    "sonar_news_fallback_to_tavily",
                    query=payload.query,
                    recency=payload.recency.value,
                    error=str(exc),
                )
                articles = _search_tavily(payload, active_settings, http_client)
                return _output(payload, NewsProvider.TAVILY, articles, allowed_symbols)
        articles = _search_tavily(payload, active_settings, http_client)
        return _output(payload, NewsProvider.TAVILY, articles, allowed_symbols)


def _search_sonar(
    payload: NewsSearchInput,
    settings: Settings,
    client: httpx.Client,
) -> tuple[NewsArticle, ...]:
    response = client.post(
        _SONAR_URL,
        headers={"Authorization": f"Bearer {settings.perplexity_api_key.get_secret_value()}"},
        json={
            "model": "sonar",
            "messages": [{"role": "user", "content": payload.query}],
            "max_tokens": 800,
            "search_recency_filter": payload.recency.value,
        },
    )
    response.raise_for_status()
    data = response.json()
    if "articles" in data:
        return tuple(_article_from_mapping(row) for row in data["articles"][: payload.max_results])

    content = str(data["choices"][0]["message"]["content"])
    citations = data.get("citations") or []
    return tuple(
        _sonar_citation_to_article(citation, content, payload)
        for citation in citations[: payload.max_results]
    )


def _sonar_citation_to_article(
    citation: Any,
    content: str,
    payload: NewsSearchInput,
) -> NewsArticle:
    """Handle both string-URL and dict citations from Sonar."""
    if isinstance(citation, str):
        return NewsArticle(
            title=payload.query,
            url=citation,
            source="Perplexity Sonar",
            published_at=None,
            summary=content,
            cited_symbols=payload.symbols,
        )
    return NewsArticle(
        title=str(citation.get("title") or payload.query),
        url=str(citation["url"]),
        source=str(citation.get("source") or "Perplexity Sonar"),
        published_at=_optional_datetime(citation.get("published_at")),
        summary=content,
        cited_symbols=payload.symbols,
    )


def _search_tavily(
    payload: NewsSearchInput,
    settings: Settings,
    client: httpx.Client,
) -> tuple[NewsArticle, ...]:
    response = client.post(
        _TAVILY_URL,
        json={
            "api_key": settings.tavily_api_key.get_secret_value(),
            "query": payload.query,
            "max_results": payload.max_results,
            "include_answer": True,
            "topic": "news",
            "time_range": payload.recency.value,
        },
    )
    response.raise_for_status()
    data = response.json()
    rows = data.get("results", [])[: payload.max_results]
    return tuple(_article_from_mapping(row) for row in rows)


def _article_from_mapping(row: dict[str, Any]) -> NewsArticle:
    return NewsArticle(
        title=str(row.get("title") or row.get("url") or "Untitled"),
        url=str(row["url"]),
        source=str(row.get("source") or row.get("publisher") or "unknown"),
        published_at=_optional_datetime(row.get("published_at") or row.get("published_date")),
        summary=str(row.get("summary") or row.get("content") or row.get("answer") or ""),
        cited_symbols=tuple(str(symbol) for symbol in row.get("cited_symbols", ())),
    )


def _output(
    payload: NewsSearchInput,
    provider: NewsProvider,
    articles: tuple[NewsArticle, ...],
    allowed_symbols: frozenset[str] | None,
) -> NewsSearchOutput:
    accepted_articles: list[NewsArticle] = []
    rejected_symbols: set[str] = set()
    allowed = allowed_symbols
    for article in articles:
        accepted, rejected = _partition_symbols(article.cited_symbols, allowed)
        rejected_symbols.update(rejected)
        accepted_articles.append(article.model_copy(update={"cited_symbols": accepted}))

    _accepted_query_symbols, rejected_query_symbols = _partition_symbols(payload.symbols, allowed)
    rejected_symbols.update(rejected_query_symbols)
    return NewsSearchOutput(
        query=payload.query,
        provider=provider,
        fetched_at=utc_now(),
        articles=tuple(accepted_articles),
        rejected_symbols=tuple(sorted(rejected_symbols)),
    )


def _partition_symbols(
    symbols: tuple[str, ...],
    allowed_symbols: frozenset[str] | None,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if allowed_symbols is None:
        return symbols, ()
    accepted = tuple(symbol for symbol in symbols if symbol in allowed_symbols)
    rejected = tuple(symbol for symbol in symbols if symbol not in allowed_symbols)
    return accepted, rejected


def _optional_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    raw = str(value)
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        pass
    try:
        return parsedate_to_datetime(raw)
    except (ValueError, TypeError):
        return None


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
