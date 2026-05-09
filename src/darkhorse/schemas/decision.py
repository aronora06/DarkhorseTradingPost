"""Pydantic models for journal decision lines (`plans/dataSchema.md` §1)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ToolUseRecordV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    result_hash: str | None = None


class AlpacaOrderRecordV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_order_id: str | None = None
    broker_order_id: str | None = None
    submitted_at: str | None = None
    fill_status: str | None = None


class CostRecordV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_tokens: int = Field(default=0, ge=0)
    cached_input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    total_usd: str = "0"


class DecisionJournalRecordV1(BaseModel):
    """Validated record for `memory/<sleeve>/journal/YYYY-MM-DD.jsonl`.

    The schema supports minimal Phase 3 tests and the richer Phase 4 journal shape
    needed for reconstruction, cost telemetry, and publication-ready evidence.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    decision_id: str
    timestamp: str
    sleeve: Literal["core", "satellite"]
    routine: str
    doctrine_version: str
    prompt_version: str
    model_assignments: dict[str, str] = Field(default_factory=dict)
    ticker: str | None = None
    action: str
    qty: str | None = None
    order_type: str | None = None
    limit_price: str | None = None
    time_in_force: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    expected_horizon_days: int | None = Field(default=None, ge=0)
    expected_outcome_pct: float | None = None
    thesis_summary: str | None = None
    reasoning_steps: list[str] = Field(default_factory=list)
    research_context: str | None = None
    tools_used: tuple[ToolUseRecordV1, ...] = Field(default_factory=tuple)
    intent_fingerprint: str = Field(description="Idempotency / dedupe key for this intent")
    validate_order_passed: bool
    risk_checks: dict[str, Any] = Field(default_factory=dict)
    lessons_referenced: tuple[str, ...] = Field(default_factory=tuple)
    anti_patterns_flagged: tuple[str, ...] = Field(default_factory=tuple)
    alpaca: AlpacaOrderRecordV1 | None = None
    cost: CostRecordV1 | None = None
    outcome: dict[str, Any] | None = None
