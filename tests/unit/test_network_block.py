"""Tests for the global no-live-network guard."""

from __future__ import annotations

import httpx
import pytest


def test_default_http_transport_is_blocked() -> None:
    with httpx.Client() as client, pytest.raises(RuntimeError, match="Live network calls"):
        client.get("https://example.com")


def test_mock_transport_is_allowed() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        response = client.get("https://example.test")

    assert response.json() == {"ok": True}
