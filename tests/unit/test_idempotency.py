"""Deterministic ids (`tests/specs/idempotency.md`)."""

from darkhorse.idempotency import client_order_id_for_alpaca, intent_hash


def test_intent_hash_stable_excluding_timestamp() -> None:
    a = {"action": "BUY", "timestamp": "2026-01-01T00:00:00Z", "ticker": "AAPL"}
    b = {"action": "BUY", "timestamp": "2026-02-01T00:00:00Z", "ticker": "AAPL"}
    assert intent_hash(a) == intent_hash(b)


def test_intent_hash_changes_with_intent() -> None:
    a = {"action": "BUY", "ticker": "AAPL"}
    b = {"action": "SELL", "ticker": "AAPL"}
    assert intent_hash(a) != intent_hash(b)


def test_client_order_id_length_and_stability() -> None:
    x = client_order_id_for_alpaca(
        routine="market_open",
        trade_date="2026-05-09",
        sleeve="core",
        symbol="aapl",
        intent_hash_hex="abc123",
    )
    y = client_order_id_for_alpaca(
        routine="market_open",
        trade_date="2026-05-09",
        sleeve="core",
        symbol="AAPL",
        intent_hash_hex="abc123",
    )
    assert len(x) == 48
    assert x == y
