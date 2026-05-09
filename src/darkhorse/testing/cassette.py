"""Cassette record/replay transport for deterministic Anthropic SDK tests.

ADR-0009 specifies a custom replay layer (<=200 lines) that intercepts
Anthropic API calls through httpx, matching by a stable request hash
and failing loud on cache miss rather than falling through to live.

Cassette files live at ``tests/cassettes/<name>.json``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import httpx


class CassetteMissError(Exception):
    """Raised in replay mode when no recorded response matches the request."""


CassetteEntry = dict[str, Any]

_CASSETTE_DIR = Path("tests/cassettes")


def stable_request_hash(body: dict[str, Any]) -> str:
    """SHA-256 over the semantically meaningful parts of an Anthropic request body.

    Excludes ephemeral fields (``stream``, ``metadata``) so the same logical
    request always produces the same hash regardless of SDK version or timestamp.
    """
    canonical: dict[str, Any] = {}
    for key in ("model", "system", "messages", "tools", "max_tokens", "output_config"):
        if key in body:
            canonical[key] = body[key]
    raw = json.dumps(canonical, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_cassette(path: Path) -> list[CassetteEntry]:
    """Read a cassette JSON file.  Returns a list of entry dicts."""
    with path.open("r", encoding="utf-8") as fh:
        data: list[CassetteEntry] = json.load(fh)
    return data


def save_cassette(path: Path, entries: list[CassetteEntry]) -> None:
    """Write cassette entries to *path* with human-readable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(entries, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def _build_replay_response(entry: CassetteEntry) -> httpx.Response:
    """Reconstruct an ``httpx.Response`` from a cassette entry's ``response``."""
    resp_data = entry["response"]
    return httpx.Response(
        status_code=resp_data.get("status_code", 200),
        headers=resp_data.get("headers", {"content-type": "application/json"}),
        json=resp_data.get("body", {}),
    )


def _extract_body(request: httpx.Request) -> dict[str, Any]:
    """Parse the JSON body from an httpx Request."""
    raw = request.content.decode("utf-8") if request.content else "{}"
    result: dict[str, Any] = json.loads(raw)
    return result


class CassetteTransport(httpx.BaseTransport):
    """httpx transport that replays or records Anthropic API interactions.

    Parameters
    ----------
    cassette_path:
        Path to the JSON cassette file.
    record:
        If ``True``, unknown requests are forwarded to *live_transport* and the
        round-trip is appended to the cassette.  If ``False`` (default), unknown
        requests raise ``CassetteMissError``.
    live_transport:
        The real transport to delegate to in record mode.  Ignored in replay mode.
    """

    def __init__(
        self,
        cassette_path: Path,
        *,
        record: bool = False,
        live_transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._path = cassette_path
        self._record = record
        self._live = live_transport

        self._entries: list[CassetteEntry] = (
            load_cassette(cassette_path) if cassette_path.is_file() else []
        )

        self._lookup: dict[str, CassetteEntry] = {e["request_hash"]: e for e in self._entries}

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        body = _extract_body(request)
        req_hash = stable_request_hash(body)

        if req_hash in self._lookup:
            return _build_replay_response(self._lookup[req_hash])

        if not self._record:
            raise CassetteMissError(
                f"No cassette entry for request hash {req_hash}. "
                f"Re-record with: uv run python -m darkhorse.testing.record"
            )

        if self._live is None:
            raise CassetteMissError("Record mode requires a live_transport but none was provided.")

        response = self._live.handle_request(request)
        response.read()
        resp_body: dict[str, Any] = json.loads(
            response.content.decode("utf-8") if response.content else "{}"
        )
        entry: CassetteEntry = {
            "request_hash": req_hash,
            "request_summary": {
                "model": body.get("model"),
                "url": str(request.url),
                "max_tokens": body.get("max_tokens"),
            },
            "response": {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": resp_body,
            },
        }
        self._entries.append(entry)
        self._lookup[req_hash] = entry
        save_cassette(self._path, self._entries)
        return response
