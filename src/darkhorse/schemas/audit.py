"""Audit log JSONL schema (`plans/dataSchema.md` §9)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class AuditLogRecordV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    event_id: str
    timestamp: str
    actor: str
    actor_method: str
    action: str
    from_state: str | None = None
    to_state: str | None = None
    reason_provided: str | None = None
    ip: str | None = None
