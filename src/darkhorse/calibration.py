"""Calibration log writer (`plans/dataSchema.md` §2)."""

from __future__ import annotations

from pathlib import Path

from darkhorse.journal import append_jsonl_record
from darkhorse.schemas.calibration import CalibrationJournalRecordV1


def append_calibration_record(path: Path, record: CalibrationJournalRecordV1) -> bool:
    return append_jsonl_record(path, record, dedupe_key="calibration_id")
