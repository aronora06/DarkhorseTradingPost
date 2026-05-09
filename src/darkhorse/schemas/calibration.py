"""Calibration JSONL schema (`plans/dataSchema.md` §2)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CalibrationJournalRecordV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    calibration_id: str
    decision_id: str
    sleeve: Literal["core", "satellite"]
    decision_timestamp: str
    horizon_end: str | None = None
    predicted_confidence: float
    predicted_outcome_pct: float | None = None
    realized_outcome_pct: float | None = None
    outcome_class: str | None = None
    doctrine_version: str
    prompt_version: str
    tags: list[str] = Field(default_factory=list)
