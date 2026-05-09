"""Alpaca tool wrapper tests with mocked HTTP."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

import httpx
import pytest

from darkhorse.config import Settings
from darkhorse.risk import OrderRequest, OrderType, Side, Sleeve, ValidationContext
from darkhorse.tools._contracts import (
    AlpacaAccountInput,
    AlpacaCancelOrderInput,
    AlpacaPositionsInput,
    AlpacaSubmitOrderInput,
    BrokerEnvironment,
)
from darkhorse.tools.alpaca import cancel_order, fetch_account, fetch_positions, submit_order


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


def _order(**overrides: object) -> OrderRequest:
    base: dict[str, object] = {
        "sleeve": Sleeve.CORE,
        "symbol": "AAPL",
        "side": Side.BUY,
        "order_type": OrderType.LIMIT,
        "qty": 1,
        "limit_price": Decimal("100"),
        "estimated_notional_usd": Decimal("100"),
    }
    base.update(overrides)
    return OrderRequest.model_validate(base)


def _context(**overrides: object) -> ValidationContext:
    base: dict[str, object] = {
        "core_nav_usd": Decimal("900"),
        "satellite_nav_usd": Decimal("100"),
        "account_equity_usd": Decimal("1000"),
        "core_allowed_symbols": frozenset({"AAPL", "SPY"}),
        "satellite_allowed_symbols": frozenset({"AAPL", "SPY"}),
        "pdt_restricted": False,
        "day_trades_in_rolling_5_sessions": 0,
        "order_would_be_day_trade": False,
    }
    base.update(overrides)
    return ValidationContext.model_validate(base)


def test_fetch_account_maps_alpaca_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "paper-api.alpaca.markets"
        assert request.headers["APCA-API-KEY-ID"] == "paper-key"
        return httpx.Response(
            200,
            json={
                "id": "acct_123",
                "status": "ACTIVE",
                "cash": "1000.00",
                "buying_power": "995.00",
                "equity": "1000.00",
                "pattern_day_trader": False,
                "daytrade_count": 1,
                "trading_blocked": False,
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        account = fetch_account(
            AlpacaAccountInput(environment=BrokerEnvironment.PAPER),
            settings=_settings(),
            client=client,
        )

    assert account.account_id == "acct_123"
    assert account.buying_power_usd == Decimal("995.00")
    assert account.daytrade_count == 1


def test_fetch_positions_maps_position_rows() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[
                {
                    "symbol": "aapl",
                    "qty": "2",
                    "market_value": "400.50",
                    "avg_entry_price": "190.25",
                    "unrealized_pl": "20.00",
                },
            ],
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        positions = fetch_positions(
            AlpacaPositionsInput(environment=BrokerEnvironment.PAPER),
            settings=_settings(),
            client=client,
        )

    assert len(positions.positions) == 1
    assert positions.positions[0].symbol == "AAPL"
    assert positions.positions[0].market_value_usd == Decimal("400.50")


def test_submit_order_rejects_locally_without_http() -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500)

    payload = AlpacaSubmitOrderInput(
        environment=BrokerEnvironment.PAPER,
        order=_order(),
        validation_context=_context(kill_switch_or_trading_paused=True),
        client_order_id="reject-local",
    )
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = submit_order(payload, settings=_settings(), client=client)

    assert calls == 0
    assert result.submitted is False
    assert result.status == "blocked_by_validate_order"
    assert result.validation.rule_id == "KS-GLOBAL"


def test_submit_order_passes_validation_then_posts_to_alpaca() -> None:
    seen_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v2/orders"
        assert request.headers["APCA-API-SECRET-KEY"] == "paper-secret"
        seen_body.update(json.loads(request.content.decode("utf-8")))
        return httpx.Response(
            200,
            json={
                "id": "order_123",
                "client_order_id": "client-123",
                "status": "accepted",
            },
        )

    payload = AlpacaSubmitOrderInput(
        environment=BrokerEnvironment.PAPER,
        order=_order(),
        validation_context=_context(),
        client_order_id="client-123",
    )
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = submit_order(payload, settings=_settings(), client=client)

    assert result.submitted is True
    assert result.broker_order_id == "order_123"
    assert result.validation.rule_id == "R-VOK"
    assert seen_body == {
        "symbol": "AAPL",
        "qty": "1",
        "side": "buy",
        "type": "limit",
        "time_in_force": "day",
        "client_order_id": "client-123",
        "limit_price": "100",
    }


def test_submit_order_retries_transient_server_errors() -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503)
        return httpx.Response(
            200,
            json={
                "id": "order_retry",
                "client_order_id": "client-retry",
                "status": "accepted",
            },
        )

    payload = AlpacaSubmitOrderInput(
        environment=BrokerEnvironment.PAPER,
        order=_order(),
        validation_context=_context(),
        client_order_id="client-retry",
    )
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = submit_order(
            payload,
            settings=_settings(),
            client=client,
            retry_delays_s=(0,),
        )

    assert calls == 2
    assert result.submitted is True
    assert result.broker_order_id == "order_retry"


def test_submit_order_does_not_retry_client_errors() -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(422, json={"message": "bad order"})

    payload = AlpacaSubmitOrderInput(
        environment=BrokerEnvironment.PAPER,
        order=_order(),
        validation_context=_context(),
        client_order_id="client-error",
    )
    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as client,
        pytest.raises(httpx.HTTPStatusError),
    ):
        submit_order(
            payload,
            settings=_settings(),
            client=client,
            retry_delays_s=(0,),
        )

    assert calls == 1


def test_cancel_order_deletes_broker_order() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/v2/orders/order_123"
        return httpx.Response(204)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = cancel_order(
            AlpacaCancelOrderInput(
                environment=BrokerEnvironment.PAPER,
                broker_order_id="order_123",
            ),
            settings=_settings(),
            client=client,
        )

    assert result.canceled is True
    assert result.status == "canceled"
