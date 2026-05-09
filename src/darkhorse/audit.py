"""System audit log (`plans/dataSchema.md` §9)."""

from __future__ import annotations

from pathlib import Path

from darkhorse.journal import append_jsonl_record
from darkhorse.schemas.audit import AuditLogRecordV1


def append_audit_record(path: Path, record: AuditLogRecordV1) -> None:
    """Append one audit event (no dedupe — each event is unique by ``event_id``)."""
    append_jsonl_record(path, record, dedupe_key=None)
