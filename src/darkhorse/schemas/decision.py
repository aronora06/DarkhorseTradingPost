"""Pydantic models for journal decision lines (`plans/dataSchema.md` §1)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class DecisionJournalRecordV1(BaseModel):
    """Minimal validated record for `memory/<sleeve>/journal/YYYY-MM-DD.jsonl`."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    decision_id: str
    timestamp: str
    sleeve: Literal["core", "satellite"]
    routine: str
    doctrine_version: str
    prompt_version: str
    ticker: str | None = None
    action: str
    intent_fingerprint: str = Field(description="Idempotency / dedupe key for this intent")
    validate_order_passed: bool
    risk_checks: dict[str, Any] = Field(default_factory=dict)
    alpaca: dict[str, Any] | None = None
