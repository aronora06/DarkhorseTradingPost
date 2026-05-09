"""Deterministic ids for Alpaca + journal dedupe (`tests/specs/idempotency.md`)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

# Timestamps / broker fields must not affect intent identity (ID-01).
_DEFAULT_TRANSIENT_KEYS: frozenset[str] = frozenset(
    {
        "timestamp",
        "decision_id",
        "outcome",
        "cost",
        "alpaca",
        "risk_checks",
    }
)


def intent_hash(
    decision_payload: dict[str, Any],
    *,
    extra_transient_keys: frozenset[str] | None = None,
) -> str:
    """Stable sha256 over JSON with sorted keys, excluding transient fields."""
    exclude = _DEFAULT_TRANSIENT_KEYS | (extra_transient_keys or frozenset())
    trimmed = {k: decision_payload[k] for k in sorted(decision_payload) if k not in exclude}
    canonical = json.dumps(trimmed, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def client_order_id_for_alpaca(
    *,
    routine: str,
    trade_date: str,
    sleeve: str,
    symbol: str,
    intent_hash_hex: str,
) -> str:
    """Deterministic id ≤ 48 chars (Alpaca limit).

    Uses a SHA-256 digest of normalized components so retries stay idempotent.
    """
    payload = f"{routine}\x1e{trade_date}\x1e{sleeve}\x1e{symbol.upper()}\x1e{intent_hash_hex}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:48]
    return digest
