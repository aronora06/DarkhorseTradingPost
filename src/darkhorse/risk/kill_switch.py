"""Kill-switch & pause evaluation (`tests/specs/kill_switch.md`, `doctrine/risk_policy.md` §7)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import structlog

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class KillSwitchReport:
    """Whether trading is allowed and human-readable reasons if not."""

    trading_allowed: bool
    reasons: tuple[str, ...]


def evaluate_kill_switch(
    *,
    killswitch_path: Path,
    darkhorse_kill_env: str | None,
    remote_kill_url: str | None = None,
    http_client: httpx.Client | None = None,
) -> KillSwitchReport:
    """KS-01 / KS-02 / optional remote URL with body ``kill`` / ``1`` / ``true``."""
    reasons: list[str] = []

    if killswitch_path.is_file():
        reasons.append(f"kill file present: {killswitch_path}")

    if darkhorse_kill_env is not None and darkhorse_kill_env.strip() == "1":
        reasons.append("DARKHORSE_KILL=1")

    if remote_kill_url:
        remote_reason = _remote_kill_reason(remote_kill_url, http_client=http_client)
        if remote_reason:
            reasons.append(remote_reason)

    if reasons:
        return KillSwitchReport(trading_allowed=False, reasons=tuple(reasons))
    return KillSwitchReport(trading_allowed=True, reasons=())


def _remote_kill_reason(url: str, *, http_client: httpx.Client | None) -> str | None:
    try:
        client = http_client or httpx.Client(timeout=2.0)
        own = http_client is None
        try:
            response = client.get(url)
        finally:
            if own:
                client.close()
    except httpx.HTTPError as exc:
        logger.warning("remote_kill_check_failed", url=url, error=str(exc))
        return f"remote kill check failed (blocking): {exc}"

    if response.status_code != 200:
        return f"remote kill endpoint non-200 ({response.status_code}): {url}"

    body = response.text.strip().lower()
    if body in {"1", "true", "kill", "yes"}:
        return f"remote kill asserted by body from {url}"
    return None


def stale_human_review_pause(
    *,
    now_utc: datetime,
    last_doctrine_activity_utc: datetime | None,
    last_journal_activity_utc: datetime | None,
    stale_after: timedelta,
) -> bool:
    """KS-03 — pause if both activity clocks exist and are older than ``stale_after``."""
    if last_doctrine_activity_utc is None or last_journal_activity_utc is None:
        return False
    oldest = min(last_doctrine_activity_utc, last_journal_activity_utc)
    if oldest.tzinfo is None:
        oldest = oldest.replace(tzinfo=UTC)
    return now_utc - oldest > stale_after


def monthly_spend_exceeds_cap(
    *,
    spend_usd_this_month: float | None,
    monthly_cap_usd: float,
) -> bool:
    """KS-04 — pause when spend is known and over cap."""
    if spend_usd_this_month is None:
        return False
    return spend_usd_this_month > monthly_cap_usd
