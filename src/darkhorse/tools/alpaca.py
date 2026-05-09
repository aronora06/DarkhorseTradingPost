"""Deterministic Alpaca Trading API wrapper.

All order submissions run through `validate_order()` before any broker request.
"""

from __future__ import annotations

import time
from decimal import Decimal
from typing import Any

import httpx

from darkhorse.config import Settings, get_settings
from darkhorse.risk import OrderType, ValidationVerdict, validate_order
from darkhorse.tools._contracts import (
    AlpacaAccountInput,
    AlpacaAccountOutput,
    AlpacaCancelOrderInput,
    AlpacaCancelOrderOutput,
    AlpacaPosition,
    AlpacaPositionsInput,
    AlpacaPositionsOutput,
    AlpacaSubmitOrderInput,
    AlpacaSubmitOrderOutput,
    BrokerEnvironment,
    utc_now,
)

_LIVE_BASE_URL = "https://api.alpaca.markets"
_PAPER_BASE_URL = "https://paper-api.alpaca.markets"


def fetch_account(
    payload: AlpacaAccountInput,
    *,
    settings: Settings | None = None,
    client: httpx.Client | None = None,
    timeout_s: float = 10.0,
    retry_delays_s: tuple[float, ...] = (1.0, 3.0),
) -> AlpacaAccountOutput:
    """Fetch the broker account snapshot for live or paper trading."""

    data = _request_json(
        "GET",
        "/v2/account",
        payload.environment,
        settings=settings,
        client=client,
        timeout_s=timeout_s,
        retry_delays_s=retry_delays_s,
    )
    return AlpacaAccountOutput(
        environment=payload.environment,
        account_id=str(data["id"]),
        status=str(data["status"]),
        cash_usd=_decimal(data["cash"]),
        buying_power_usd=_decimal(data["buying_power"]),
        equity_usd=_decimal(data["equity"]),
        pattern_day_trader=bool(data["pattern_day_trader"]),
        daytrade_count=_optional_int(data.get("daytrade_count")),
        trading_blocked=bool(data["trading_blocked"]),
        as_of=utc_now(),
    )


def fetch_positions(
    payload: AlpacaPositionsInput,
    *,
    settings: Settings | None = None,
    client: httpx.Client | None = None,
    timeout_s: float = 10.0,
    retry_delays_s: tuple[float, ...] = (1.0, 3.0),
) -> AlpacaPositionsOutput:
    """Fetch open Alpaca positions."""

    data = _request_json_list(
        "GET",
        "/v2/positions",
        payload.environment,
        settings=settings,
        client=client,
        timeout_s=timeout_s,
        retry_delays_s=retry_delays_s,
    )
    positions = tuple(
        AlpacaPosition(
            symbol=str(row["symbol"]),
            qty=_decimal(row["qty"]),
            market_value_usd=_decimal(row["market_value"]),
            avg_entry_price_usd=_optional_decimal(row.get("avg_entry_price")),
            unrealized_pl_usd=_optional_decimal(row.get("unrealized_pl")),
        )
        for row in data
    )
    return AlpacaPositionsOutput(
        environment=payload.environment,
        as_of=utc_now(),
        positions=positions,
    )


def submit_order(
    payload: AlpacaSubmitOrderInput,
    *,
    settings: Settings | None = None,
    client: httpx.Client | None = None,
    timeout_s: float = 10.0,
    retry_delays_s: tuple[float, ...] = (1.0, 3.0),
) -> AlpacaSubmitOrderOutput:
    """Validate, then submit an order to Alpaca if it passes all local gates."""

    validation = validate_order(payload.order, payload.validation_context)
    if validation.verdict is not ValidationVerdict.PASS:
        return AlpacaSubmitOrderOutput(
            environment=payload.environment,
            validation=validation,
            submitted=False,
            client_order_id=payload.client_order_id,
            status="blocked_by_validate_order",
        )

    if payload.dry_run:
        return AlpacaSubmitOrderOutput(
            environment=payload.environment,
            validation=validation,
            submitted=False,
            client_order_id=payload.client_order_id,
            status="dry_run",
        )

    data = _request_json(
        "POST",
        "/v2/orders",
        payload.environment,
        settings=settings,
        client=client,
        timeout_s=timeout_s,
        retry_delays_s=retry_delays_s,
        json=_order_body(payload),
    )
    return AlpacaSubmitOrderOutput(
        environment=payload.environment,
        validation=validation,
        submitted=True,
        broker_order_id=str(data["id"]),
        client_order_id=str(data.get("client_order_id") or payload.client_order_id),
        status=str(data["status"]),
        submitted_at=utc_now(),
    )


def cancel_order(
    payload: AlpacaCancelOrderInput,
    *,
    settings: Settings | None = None,
    client: httpx.Client | None = None,
    timeout_s: float = 10.0,
    retry_delays_s: tuple[float, ...] = (1.0, 3.0),
) -> AlpacaCancelOrderOutput:
    """Cancel an Alpaca order by broker order id."""

    _request_no_content(
        "DELETE",
        f"/v2/orders/{payload.broker_order_id}",
        payload.environment,
        settings=settings,
        client=client,
        timeout_s=timeout_s,
        retry_delays_s=retry_delays_s,
    )
    return AlpacaCancelOrderOutput(
        environment=payload.environment,
        broker_order_id=payload.broker_order_id,
        canceled=True,
        status="canceled",
        canceled_at=utc_now(),
    )


def _order_body(payload: AlpacaSubmitOrderInput) -> dict[str, str]:
    order = payload.order
    body = {
        "symbol": order.symbol,
        "qty": str(order.qty),
        "side": order.side.value,
        "type": order.order_type.value,
        "time_in_force": "day",
        "client_order_id": payload.client_order_id,
    }
    if order.order_type is OrderType.LIMIT:
        if order.limit_price is None:
            raise ValueError("limit_price is required for limit orders")
        body["limit_price"] = str(order.limit_price)
    return body


def _request_json(
    method: str,
    path: str,
    environment: BrokerEnvironment,
    *,
    settings: Settings | None,
    client: httpx.Client | None,
    timeout_s: float,
    retry_delays_s: tuple[float, ...],
    json: dict[str, str] | None = None,
) -> dict[str, Any]:
    response = _request(
        method,
        path,
        environment,
        settings=settings,
        client=client,
        timeout_s=timeout_s,
        retry_delays_s=retry_delays_s,
        json=json,
    )
    data = response.json()
    if not isinstance(data, dict):
        raise TypeError("expected Alpaca JSON object")
    return data


def _request_json_list(
    method: str,
    path: str,
    environment: BrokerEnvironment,
    *,
    settings: Settings | None,
    client: httpx.Client | None,
    timeout_s: float,
    retry_delays_s: tuple[float, ...],
) -> list[dict[str, Any]]:
    response = _request(
        method,
        path,
        environment,
        settings=settings,
        client=client,
        timeout_s=timeout_s,
        retry_delays_s=retry_delays_s,
    )
    data = response.json()
    if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
        raise TypeError("expected Alpaca JSON array of objects")
    return data


def _request_no_content(
    method: str,
    path: str,
    environment: BrokerEnvironment,
    *,
    settings: Settings | None,
    client: httpx.Client | None,
    timeout_s: float,
    retry_delays_s: tuple[float, ...],
) -> None:
    _request(
        method,
        path,
        environment,
        settings=settings,
        client=client,
        timeout_s=timeout_s,
        retry_delays_s=retry_delays_s,
    )


def _request(
    method: str,
    path: str,
    environment: BrokerEnvironment,
    *,
    settings: Settings | None,
    client: httpx.Client | None,
    timeout_s: float,
    retry_delays_s: tuple[float, ...],
    json: dict[str, str] | None = None,
) -> httpx.Response:
    url = f"{_base_url(environment)}{path}"
    headers = _headers(environment, settings or get_settings())
    if client is not None:
        return _request_with_retries(client, method, url, headers, json, retry_delays_s)

    with httpx.Client(timeout=timeout_s) as local_client:
        return _request_with_retries(local_client, method, url, headers, json, retry_delays_s)


def _request_with_retries(
    client: httpx.Client,
    method: str,
    url: str,
    headers: dict[str, str],
    json: dict[str, str] | None,
    retry_delays_s: tuple[float, ...],
) -> httpx.Response:
    attempts = len(retry_delays_s) + 1
    for attempt in range(attempts):
        try:
            response = client.request(method, url, headers=headers, json=json)
            response.raise_for_status()
        except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
            if attempt >= len(retry_delays_s) or not _is_retryable_http(exc):
                raise
            delay_s = retry_delays_s[attempt]
            if delay_s > 0:
                time.sleep(delay_s)
            continue
        return response
    raise RuntimeError("unreachable Alpaca retry state")


def _is_retryable_http(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return isinstance(exc, (httpx.TimeoutException, httpx.TransportError))


def _base_url(environment: BrokerEnvironment) -> str:
    if environment is BrokerEnvironment.LIVE:
        return _LIVE_BASE_URL
    return _PAPER_BASE_URL


def _headers(environment: BrokerEnvironment, settings: Settings) -> dict[str, str]:
    if environment is BrokerEnvironment.LIVE:
        key = settings.alpaca_live_api_key.get_secret_value()
        secret = settings.alpaca_live_secret_key.get_secret_value()
    else:
        key = settings.alpaca_paper_api_key.get_secret_value()
        secret = settings.alpaca_paper_secret_key.get_secret_value()
    return {
        "APCA-API-KEY-ID": key,
        "APCA-API-SECRET-KEY": secret,
        "Accept": "application/json",
    }


def _decimal(value: object) -> Decimal:
    return Decimal(str(value))


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return _decimal(value)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(str(value))
