"""CLI for re-recording Anthropic cassettes.

Usage::

    # Minimal probe (default):
    uv run python -m darkhorse.testing.record <cassette_name>

    # Full market_open routine:
    uv run python -m darkhorse.testing.record <cassette_name> --routine market_open

The probe mode sends a single cheap request to verify API credentials.
The ``market_open`` mode runs the complete routine so every Anthropic
round-trip (researcher + risk-manager) is captured for deterministic replay.

Broker, data, and news HTTP calls still go live on their own clients --
the cassette only intercepts Anthropic API traffic.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx

from darkhorse.testing.cassette import CassetteTransport, save_cassette


def _run_probe(client: httpx.Client, *, model: str, prompt: str) -> None:
    """Fire a single cheap Anthropic call to verify API connectivity."""
    from darkhorse.config import get_settings

    settings = get_settings()
    api_key = settings.anthropic_api_key.get_secret_value()

    response = client.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 64,
            "system": prompt,
            "messages": [{"role": "user", "content": "ping"}],
        },
    )
    response.raise_for_status()
    print("Probe complete.")


def _run_market_open(client: httpx.Client) -> None:
    """Run the full market_open routine with cassette recording."""
    from darkhorse.routines.market_open import run_market_open

    print("Running market_open routine (this makes live Anthropic + data calls)...")
    record = run_market_open(anthropic_http_client=client)

    if record is None:
        print("Routine returned None (composition layer blocked trading).")
    else:
        print(f"Routine finished: action={record.action}, ticker={record.ticker}")


_VALID_ROUTINES = ("probe", "market_open")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Record an Anthropic API cassette for deterministic replay.",
    )
    parser.add_argument(
        "cassette_name",
        help="Name for the cassette (written to tests/cassettes/<name>.json).",
    )
    parser.add_argument(
        "--routine",
        default="probe",
        choices=_VALID_ROUTINES,
        help="Which routine to record. 'probe' (default) sends a single cheap "
        "request; 'market_open' captures the full routine.",
    )
    parser.add_argument(
        "--prompt",
        default="Respond with exactly: CASSETTE_PROBE_OK",
        help="System prompt for the probe recording (ignored for market_open).",
    )
    parser.add_argument(
        "--model",
        default="claude-haiku-4-5-20250514",
        help="Model for the probe recording (ignored for market_open).",
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

    with httpx.Client(transport=transport) as client:
        if args.routine == "market_open":
            _run_market_open(client)
        else:
            _run_probe(client, model=args.model, prompt=args.prompt)

    entries = transport._entries  # noqa: SLF001
    print(f"Recorded {len(entries)} interaction(s).")

    save_cassette(cassette_path, entries)
    print(f"Saved to {cassette_path}")


if __name__ == "__main__":
    main(sys.argv[1:])
