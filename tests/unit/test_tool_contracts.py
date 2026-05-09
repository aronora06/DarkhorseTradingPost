"""Tool contract tests for deterministic Phase 3.4 boundaries."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from darkhorse.risk import OrderRequest, OrderType, Side, Sleeve, ValidationContext
from darkhorse.tools import (
    TOOL_CONTRACTS,
    AlpacaSubmitOrderInput,
    BrokerEnvironment,
    NewsArticle,
    NewsSearchInput,
    QuoteInput,
    contract_json_schemas,
)


def _base_order() -> OrderRequest:
    return OrderRequest(
        sleeve=Sleeve.CORE,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=1,
        limit_price=Decimal("100"),
        estimated_notional_usd=Decimal("100"),
    )


def _base_context() -> ValidationContext:
    return ValidationContext(
        core_nav_usd=Decimal("900"),
        satellite_nav_usd=Decimal("100"),
        account_equity_usd=Decimal("1000"),
        core_allowed_symbols=frozenset({"AAPL", "SPY"}),
        satellite_allowed_symbols=frozenset({"AAPL", "SPY"}),
        pdt_restricted=False,
        day_trades_in_rolling_5_sessions=0,
        order_would_be_day_trade=False,
    )


def test_contracts_reject_extra_fields() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        QuoteInput.model_validate({"symbol": "aapl", "unexpected": True})


def test_symbol_inputs_are_nfkc_normalized_and_uppercase() -> None:
    quote = QuoteInput.model_validate({"symbol": " ａapl "})
    assert quote.symbol == "AAPL"


def test_news_contract_normalizes_text_and_symbols() -> None:
    article = NewsArticle(
        title="ＡＡＰＬ update",
        url="https://example.test/aapl",
        source="Example",
        published_at=datetime(2026, 5, 9, tzinfo=UTC),
        summary="Fullwidth ＳＰＹ text",
        cited_symbols=(" ａapl ", "spy"),
    )
    request = NewsSearchInput(query=" ＡＡＰＬ earnings ", symbols=(" ａapl ",))

    assert article.title == "AAPL update"
    assert article.summary == "Fullwidth SPY text"
    assert article.cited_symbols == ("AAPL", "SPY")
    assert request.query == "AAPL earnings"
    assert request.symbols == ("AAPL",)


def test_submit_order_contract_requires_built_validation_context() -> None:
    payload = AlpacaSubmitOrderInput(
        environment=BrokerEnvironment.PAPER,
        order=_base_order(),
        validation_context=_base_context(),
        client_order_id="abc123",
    )

    assert payload.order.symbol == "AAPL"
    assert payload.validation_context.core_allowed_symbols == frozenset({"AAPL", "SPY"})
    assert payload.dry_run is False


def test_submit_order_contract_rejects_non_alpaca_safe_client_order_id() -> None:
    with pytest.raises(ValidationError):
        AlpacaSubmitOrderInput(
            environment=BrokerEnvironment.PAPER,
            order=_base_order(),
            validation_context=_base_context(),
            client_order_id="x" * 49,
        )


def test_contract_json_schemas_cover_registered_tools() -> None:
    schemas = contract_json_schemas()

    assert set(schemas) == set(TOOL_CONTRACTS)
    quote_input_schema = schemas["data.quote"]["input"]
    assert quote_input_schema["additionalProperties"] is False
