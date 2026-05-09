"""Shared pytest guardrails."""

from __future__ import annotations

import os

import httpx
import pytest


@pytest.fixture(autouse=True)
def block_live_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail tests that accidentally use real HTTP instead of MockTransport."""

    if os.getenv("DARKHORSE_ALLOW_NETWORK_TESTS") == "1":
        return

    def blocked_request(_self: httpx.HTTPTransport, request: httpx.Request) -> httpx.Response:
        raise RuntimeError(
            "Live network calls are disabled in tests. Inject httpx.MockTransport "
            f"or set DARKHORSE_ALLOW_NETWORK_TESTS=1 for an explicit smoke test: {request.url}"
        )

    async def blocked_async_request(
        _self: httpx.AsyncHTTPTransport,
        request: httpx.Request,
    ) -> httpx.Response:
        raise RuntimeError(
            "Live network calls are disabled in tests. Inject httpx.MockTransport "
            f"or set DARKHORSE_ALLOW_NETWORK_TESTS=1 for an explicit smoke test: {request.url}"
        )

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", blocked_request)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", blocked_async_request)
