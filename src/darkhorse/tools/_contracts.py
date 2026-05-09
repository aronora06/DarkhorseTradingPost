"""Pydantic contracts for deterministic tool boundaries.

These models describe the JSON shapes accepted and returned by broker/data/news
tools. Implementations live in sibling modules; this file stays side-effect free.
"""

from __future__ import annotations

import unicodedata
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from darkhorse.risk.validate_order import OrderRequest, ValidationContext, ValidationResult


class ToolContractModel(BaseModel):
    """Base model for tool schemas that should reject unplanned fields."""

    model_config = ConfigDict(extra="forbid")


class BrokerEnvironment(StrEnum):
    LIVE = "live"
    PAPER = "paper"


class TimeFrame(StrEnum):
    ONE_MINUTE = "1Min"
    FIVE_MINUTES = "5Min"
    FIFTEEN_MINUTES = "15Min"
    ONE_HOUR = "1Hour"
    ONE_DAY = "1Day"


class NewsRecency(StrEnum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class DataProvider(StrEnum):
    FINNHUB = "finnhub"
    YFINANCE = "yfinance"


class NewsProvider(StrEnum):
    SONAR = "sonar"
    TAVILY = "tavily"


class AssetClass(StrEnum):
    US_EQUITY = "us_equity"
    ETF = "etf"
    CRYPTO = "crypto"
    OTHER = "other"


class AlpacaAccountInput(ToolContractModel):
    environment: BrokerEnvironment


class AlpacaAccountOutput(ToolContractModel):
    environment: BrokerEnvironment
    account_id: str
    status: str
    currency: Literal["USD"] = "USD"
    cash_usd: Decimal
    buying_power_usd: Decimal
    equity_usd: Decimal
    pattern_day_trader: bool
    daytrade_count: int | None = Field(default=None, ge=0)
    trading_blocked: bool
    as_of: datetime


class AlpacaPositionsInput(ToolContractModel):
    environment: BrokerEnvironment


class AlpacaPosition(ToolContractModel):
    symbol: str
    qty: Decimal
    market_value_usd: Decimal
    avg_entry_price_usd: Decimal | None = None
    unrealized_pl_usd: Decimal | None = None
    sector: str | None = None

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return _normalize_symbol(value)


class AlpacaPositionsOutput(ToolContractModel):
    environment: BrokerEnvironment
    as_of: datetime
    positions: tuple[AlpacaPosition, ...]


class AlpacaSubmitOrderInput(ToolContractModel):
    """Order submission payload after the harness has built risk context.

    The harness owns deterministic `client_order_id` derivation from the decision
    intent; this boundary enforces Alpaca's 48-character limit before submit.
    """

    environment: BrokerEnvironment
    order: OrderRequest
    validation_context: ValidationContext
    client_order_id: str = Field(min_length=1, max_length=48)
    dry_run: bool = False


class AlpacaSubmitOrderOutput(ToolContractModel):
    environment: BrokerEnvironment
    validation: ValidationResult
    submitted: bool
    broker_order_id: str | None = None
    client_order_id: str | None = None
    status: str | None = None
    submitted_at: datetime | None = None


class AlpacaCancelOrderInput(ToolContractModel):
    environment: BrokerEnvironment
    broker_order_id: str


class AlpacaCancelOrderOutput(ToolContractModel):
    environment: BrokerEnvironment
    broker_order_id: str
    canceled: bool
    status: str
    canceled_at: datetime | None = None


class QuoteInput(ToolContractModel):
    symbol: str
    preferred_provider: DataProvider = DataProvider.FINNHUB

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return _normalize_symbol(value)


class QuoteOutput(ToolContractModel):
    symbol: str
    provider: DataProvider
    bid_usd: Decimal | None = None
    ask_usd: Decimal | None = None
    last_usd: Decimal
    volume: int | None = Field(default=None, ge=0)
    market_timestamp: datetime
    fetched_at: datetime
    is_stale: bool

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return _normalize_symbol(value)


class BarsInput(ToolContractModel):
    symbol: str
    timeframe: TimeFrame
    start: datetime
    end: datetime
    preferred_provider: DataProvider = DataProvider.FINNHUB

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return _normalize_symbol(value)


class PriceBar(ToolContractModel):
    timestamp: datetime
    open_usd: Decimal
    high_usd: Decimal
    low_usd: Decimal
    close_usd: Decimal
    volume: int = Field(ge=0)


class BarsOutput(ToolContractModel):
    symbol: str
    provider: DataProvider
    timeframe: TimeFrame
    bars: tuple[PriceBar, ...]
    fetched_at: datetime
    is_stale: bool

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return _normalize_symbol(value)


class NewsSearchInput(ToolContractModel):
    query: str = Field(min_length=1, max_length=500)
    symbols: tuple[str, ...] = Field(default_factory=tuple)
    recency: NewsRecency = NewsRecency.WEEK
    max_results: int = Field(default=10, ge=1, le=25)
    preferred_provider: NewsProvider = NewsProvider.SONAR

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        return _normalize_text(value).strip()

    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(_normalize_symbol(symbol) for symbol in value)


class NewsArticle(ToolContractModel):
    title: str
    url: str
    source: str
    published_at: datetime | None = None
    summary: str
    cited_symbols: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("title", "source", "summary")
    @classmethod
    def normalize_text_fields(cls, value: str) -> str:
        return _normalize_text(value)

    @field_validator("cited_symbols")
    @classmethod
    def normalize_symbols(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(_normalize_symbol(symbol) for symbol in value)


class NewsSearchOutput(ToolContractModel):
    query: str
    provider: NewsProvider
    fetched_at: datetime
    articles: tuple[NewsArticle, ...]
    rejected_symbols: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        return _normalize_text(value).strip()

    @field_validator("rejected_symbols")
    @classmethod
    def normalize_rejected_symbols(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(_normalize_symbol(symbol) for symbol in value)


class SnapTradeHoldingsInput(ToolContractModel):
    account_id: str | None = None


class SnapTradeHolding(ToolContractModel):
    symbol: str
    qty: Decimal
    market_value_usd: Decimal
    institution: str
    as_of: datetime

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return _normalize_symbol(value)


class SnapTradeHoldingsOutput(ToolContractModel):
    fetched_at: datetime
    holdings: tuple[SnapTradeHolding, ...]


class AssetListRefreshInput(ToolContractModel):
    environment: BrokerEnvironment = BrokerEnvironment.PAPER
    active_only: bool = True


class TradableAsset(ToolContractModel):
    symbol: str
    asset_class: AssetClass
    name: str
    exchange: str | None = None
    tradable: bool
    marginable: bool | None = None
    shortable: bool | None = None
    fractionable: bool | None = None

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return _normalize_symbol(value)


class AssetListRefreshOutput(ToolContractModel):
    environment: BrokerEnvironment
    fetched_at: datetime
    output_path: str
    assets: tuple[TradableAsset, ...]


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for tool implementations."""

    return datetime.now(UTC)


def _normalize_symbol(value: str) -> str:
    symbol = unicodedata.normalize("NFKC", value).strip().upper()
    if not symbol:
        raise ValueError("symbol must not be empty")
    return symbol


def _normalize_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


ToolInput = (
    AlpacaAccountInput
    | AlpacaPositionsInput
    | AlpacaSubmitOrderInput
    | AlpacaCancelOrderInput
    | QuoteInput
    | BarsInput
    | NewsSearchInput
    | SnapTradeHoldingsInput
    | AssetListRefreshInput
)

ToolOutput = (
    AlpacaAccountOutput
    | AlpacaPositionsOutput
    | AlpacaSubmitOrderOutput
    | AlpacaCancelOrderOutput
    | QuoteOutput
    | BarsOutput
    | NewsSearchOutput
    | SnapTradeHoldingsOutput
    | AssetListRefreshOutput
)


TOOL_CONTRACTS: dict[str, tuple[type[ToolContractModel], type[ToolContractModel]]] = {
    "alpaca.account": (AlpacaAccountInput, AlpacaAccountOutput),
    "alpaca.positions": (AlpacaPositionsInput, AlpacaPositionsOutput),
    "alpaca.submit_order": (AlpacaSubmitOrderInput, AlpacaSubmitOrderOutput),
    "alpaca.cancel_order": (AlpacaCancelOrderInput, AlpacaCancelOrderOutput),
    "data.quote": (QuoteInput, QuoteOutput),
    "data.bars": (BarsInput, BarsOutput),
    "news.search": (NewsSearchInput, NewsSearchOutput),
    "snaptrade.holdings": (SnapTradeHoldingsInput, SnapTradeHoldingsOutput),
    "assets.refresh": (AssetListRefreshInput, AssetListRefreshOutput),
}


def contract_json_schemas() -> dict[str, dict[str, Any]]:
    """Return JSON schemas keyed by tool name for documentation or SDK registration."""

    return {
        name: {
            "input": input_model.model_json_schema(),
            "output": output_model.model_json_schema(),
        }
        for name, (input_model, output_model) in TOOL_CONTRACTS.items()
    }
