"""Tests for the cassette record/replay transport."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from darkhorse.testing.cassette import (
    CassetteMissError,
    CassetteTransport,
    load_cassette,
    save_cassette,
    stable_request_hash,
)


def _make_request(body: dict[str, Any]) -> httpx.Request:
    return httpx.Request(
        method="POST",
        url="https://api.anthropic.com/v1/messages",
        headers={"content-type": "application/json"},
        content=json.dumps(body).encode("utf-8"),
    )


SAMPLE_BODY: dict[str, Any] = {
    "model": "claude-haiku-4-5-20250514",
    "max_tokens": 64,
    "system": "Respond with exactly: PROBE",
    "messages": [{"role": "user", "content": "ping"}],
}

SAMPLE_RESPONSE_BODY: dict[str, Any] = {
    "id": "msg_test_001",
    "type": "message",
    "role": "assistant",
    "content": [{"type": "text", "text": "PROBE"}],
    "model": "claude-haiku-4-5-20250514",
    "stop_reason": "end_turn",
    "usage": {"input_tokens": 10, "output_tokens": 3},
}


def _seed_cassette(path: Path, body: dict[str, Any]) -> str:
    """Write a one-entry cassette and return its request hash."""
    req_hash = stable_request_hash(body)
    entries = [
        {
            "request_hash": req_hash,
            "request_summary": {
                "model": body.get("model"),
                "url": "https://api.anthropic.com/v1/messages",
                "max_tokens": body.get("max_tokens"),
            },
            "response": {
                "status_code": 200,
                "headers": {"content-type": "application/json"},
                "body": SAMPLE_RESPONSE_BODY,
            },
        },
    ]
    save_cassette(path, entries)
    return req_hash


class TestStableRequestHash:
    def test_same_inputs_same_hash(self) -> None:
        h1 = stable_request_hash(SAMPLE_BODY)
        h2 = stable_request_hash(SAMPLE_BODY)
        assert h1 == h2

    def test_ignores_ephemeral_fields(self) -> None:
        with_stream = {**SAMPLE_BODY, "stream": True, "metadata": {"user_id": "x"}}
        assert stable_request_hash(SAMPLE_BODY) == stable_request_hash(with_stream)

    def test_different_model_different_hash(self) -> None:
        other = {**SAMPLE_BODY, "model": "claude-opus-4-7-20250514"}
        assert stable_request_hash(SAMPLE_BODY) != stable_request_hash(other)

    def test_different_messages_different_hash(self) -> None:
        other = {**SAMPLE_BODY, "messages": [{"role": "user", "content": "pong"}]}
        assert stable_request_hash(SAMPLE_BODY) != stable_request_hash(other)


class TestSaveLoadCassette:
    def test_round_trip(self, tmp_path: Path) -> None:
        path = tmp_path / "test.json"
        entries = [{"request_hash": "abc", "response": {"status_code": 200, "body": {}}}]
        save_cassette(path, entries)
        loaded = load_cassette(path)
        assert loaded == entries

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        path = tmp_path / "sub" / "deep" / "test.json"
        save_cassette(path, [])
        assert path.is_file()


class TestCassetteTransportReplay:
    def test_returns_recorded_response(self, tmp_path: Path) -> None:
        cassette_path = tmp_path / "replay.json"
        _seed_cassette(cassette_path, SAMPLE_BODY)

        transport = CassetteTransport(cassette_path)
        request = _make_request(SAMPLE_BODY)
        response = transport.handle_request(request)

        assert response.status_code == 200
        data = json.loads(response.content.decode("utf-8"))
        assert data["id"] == "msg_test_001"
        assert data["content"][0]["text"] == "PROBE"

    def test_raises_on_miss(self, tmp_path: Path) -> None:
        cassette_path = tmp_path / "empty.json"
        save_cassette(cassette_path, [])

        transport = CassetteTransport(cassette_path)
        request = _make_request(SAMPLE_BODY)

        with pytest.raises(CassetteMissError, match="No cassette entry"):
            transport.handle_request(request)

    def test_raises_on_nonexistent_file(self, tmp_path: Path) -> None:
        cassette_path = tmp_path / "does_not_exist.json"
        transport = CassetteTransport(cassette_path)
        request = _make_request(SAMPLE_BODY)

        with pytest.raises(CassetteMissError, match="No cassette entry"):
            transport.handle_request(request)


class TestCassetteTransportRecord:
    def test_records_new_interaction(self, tmp_path: Path) -> None:
        cassette_path = tmp_path / "record.json"

        live_responses: list[httpx.Response] = [
            httpx.Response(
                200,
                headers={"content-type": "application/json"},
                json=SAMPLE_RESPONSE_BODY,
            ),
        ]

        class FakeLiveTransport(httpx.BaseTransport):
            def handle_request(self, request: httpx.Request) -> httpx.Response:
                return live_responses.pop(0)

        transport = CassetteTransport(
            cassette_path,
            record=True,
            live_transport=FakeLiveTransport(),
        )
        request = _make_request(SAMPLE_BODY)
        response = transport.handle_request(request)

        assert response.status_code == 200
        assert cassette_path.is_file()

        entries = load_cassette(cassette_path)
        assert len(entries) == 1
        assert entries[0]["request_hash"] == stable_request_hash(SAMPLE_BODY)
        assert entries[0]["response"]["body"]["id"] == "msg_test_001"

    def test_replays_after_recording(self, tmp_path: Path) -> None:
        cassette_path = tmp_path / "record_then_replay.json"
        _seed_cassette(cassette_path, SAMPLE_BODY)

        transport = CassetteTransport(
            cassette_path,
            record=True,
            live_transport=None,
        )
        request = _make_request(SAMPLE_BODY)
        response = transport.handle_request(request)
        assert response.status_code == 200

    def test_record_without_transport_raises(self, tmp_path: Path) -> None:
        cassette_path = tmp_path / "no_transport.json"
        transport = CassetteTransport(
            cassette_path,
            record=True,
            live_transport=None,
        )

        unknown_body = {**SAMPLE_BODY, "model": "claude-opus-4-7-20250514"}
        request = _make_request(unknown_body)

        with pytest.raises(CassetteMissError, match="live_transport"):
            transport.handle_request(request)


class TestExampleCassette:
    """Validates the committed seed cassette is well-formed."""

    def test_example_cassette_loads(self) -> None:
        path = Path("tests/cassettes/_example.json")
        entries = load_cassette(path)
        assert len(entries) == 1
        assert "request_hash" in entries[0]
        assert entries[0]["response"]["status_code"] == 200
        assert entries[0]["response"]["body"]["content"][0]["text"] == "CASSETTE_PROBE_OK"
