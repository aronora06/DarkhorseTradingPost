"""CLI for re-recording Anthropic cassettes.

Usage::

    uv run python -m darkhorse.testing.record <cassette_name>

This sends a minimal probe request to the Anthropic API using real credentials
from ``.env`` and writes the response to ``tests/cassettes/<cassette_name>.json``.

For full test-specific cassettes, run pytest with ``DARKHORSE_RECORD_CASSETTES=1``
(once a harness test suite exists that uses ``CassetteTransport`` in record mode).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx

from darkhorse.testing.cassette import CassetteTransport, save_cassette


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Record an Anthropic API cassette for deterministic replay.",
    )
    parser.add_argument(
        "cassette_name",
        help="Name for the cassette (written to tests/cassettes/<name>.json).",
    )
    parser.add_argument(
        "--prompt",
        default="Respond with exactly: CASSETTE_PROBE_OK",
        help="System prompt for the recording probe.",
    )
    parser.add_argument(
        "--model",
        default="claude-haiku-4-5-20250514",
        help="Model to record against (cheapest by default).",
    )
    args = parser.parse_args(argv)

    cassette_path = Path("tests/cassettes") / f"{args.cassette_name}.json"
    print(f"Recording cassette to {cassette_path} ...")

    live_transport = httpx.HTTPTransport()
    transport = CassetteTransport(
        cassette_path,
        record=True,
        live_transport=live_transport,
    )

    from darkhorse.config import get_settings

    settings = get_settings()
    api_key = settings.anthropic_api_key.get_secret_value()

    with httpx.Client(transport=transport) as client:
        response = client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": args.model,
                "max_tokens": 64,
                "system": args.prompt,
                "messages": [{"role": "user", "content": "ping"}],
            },
        )
        response.raise_for_status()

    entries = transport._entries  # noqa: SLF001
    print(f"Recorded {len(entries)} interaction(s).")

    save_cassette(cassette_path, entries)
    print(f"Saved to {cassette_path}")


if __name__ == "__main__":
    main(sys.argv[1:])
