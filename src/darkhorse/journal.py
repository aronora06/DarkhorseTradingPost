"""Append-only JSONL writers with optional dedupe (`plans/dataSchema.md`, ID-03)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


def append_jsonl_record(
    path: Path,
    record: BaseModel,
    *,
    dedupe_key: str | None = "intent_fingerprint",
) -> bool:
    """Validate ``record``, append one JSON line.

    If ``dedupe_key`` is set and a prior line already contains the same value for
    that JSON field, returns False without writing (ID-03).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = record.model_dump(mode="json")
    if dedupe_key:
        fingerprint = payload.get(dedupe_key)
        if (
            fingerprint is not None
            and path.is_file()
            and _file_has_field_value(path, dedupe_key, fingerprint)
        ):
            logger.info("journal_deduped", path=str(path), **{dedupe_key: fingerprint})
            return False

    line = json.dumps(payload, ensure_ascii=False)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    return True


def _file_has_field_value(path: Path, key: str, value: object) -> bool:
    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("journal_line_invalid_json", path=str(path))
                continue
            if obj.get(key) == value:
                return True
    return False
