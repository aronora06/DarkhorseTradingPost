"""Journal, audit, calibration appenders."""

from pathlib import Path

from darkhorse.audit import append_audit_record
from darkhorse.calibration import append_calibration_record
from darkhorse.journal import append_jsonl_record
from darkhorse.schemas.audit import AuditLogRecordV1
from darkhorse.schemas.calibration import CalibrationJournalRecordV1
from darkhorse.schemas.decision import DecisionJournalRecordV1


def _decision_row(*, fp: str = "fp-main") -> DecisionJournalRecordV1:
    return DecisionJournalRecordV1(
        schema_version="1.0",
        decision_id="dec_x",
        timestamp="2026-05-09T12:00:00Z",
        sleeve="core",
        routine="market_open",
        doctrine_version="d1",
        prompt_version="p1",
        ticker="AAPL",
        action="BUY",
        intent_fingerprint=fp,
        validate_order_passed=True,
    )


def test_journal_dedupes_on_intent_fingerprint(tmp_path: Path) -> None:
    path = tmp_path / "journal.jsonl"
    row = _decision_row()
    assert append_jsonl_record(path, row) is True
    assert append_jsonl_record(path, row) is False


def test_decision_schema_accepts_phase4_evidence_fields() -> None:
    row = _decision_row()
    payload = row.model_dump(mode="json")
    payload.update(
        {
            "model_assignments": {"risk_manager": "claude-opus-4-7"},
            "confidence": 0.78,
            "tools_used": [
                {"tool": "data.quote", "args": {"symbol": "AAPL"}, "result_hash": "sha256:x"},
            ],
            "alpaca": {"client_order_id": "client-1", "fill_status": "pending"},
            "cost": {
                "input_tokens": 10,
                "cached_input_tokens": 5,
                "output_tokens": 3,
                "total_usd": "0.01",
            },
            "outcome": None,
        },
    )

    validated = DecisionJournalRecordV1.model_validate(payload)
    assert validated.model_assignments["risk_manager"] == "claude-opus-4-7"
    assert validated.tools_used[0].tool == "data.quote"
    assert validated.alpaca is not None
    assert validated.alpaca.client_order_id == "client-1"


def test_audit_always_appends(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    evt = AuditLogRecordV1(
        schema_version="1.0",
        event_id="aud_1",
        timestamp="2026-05-09T12:00:00Z",
        actor="test",
        actor_method="pytest",
        action="kill_switch_toggle",
    )
    append_audit_record(path, evt)
    append_audit_record(path, evt)
    assert path.read_text(encoding="utf-8").count("\n") == 2


def test_calibration_dedupes(tmp_path: Path) -> None:
    path = tmp_path / "cal.jsonl"
    row = CalibrationJournalRecordV1(
        schema_version="1.0",
        calibration_id="cal_1",
        decision_id="dec_1",
        sleeve="core",
        decision_timestamp="2026-05-09T12:00:00Z",
        predicted_confidence=0.7,
        doctrine_version="d",
        prompt_version="p",
    )
    assert append_calibration_record(path, row) is True
    assert append_calibration_record(path, row) is False
