"""Risk: kill-switch (`tests/specs/kill_switch.md`)."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

from darkhorse.risk.kill_switch import (
    evaluate_kill_switch,
    monthly_spend_exceeds_cap,
    stale_human_review_pause,
)


def test_kill_file_blocks(tmp_path: Path) -> None:
    kf = tmp_path / "KILLSWITCH"
    kf.write_text("", encoding="utf-8")
    r = evaluate_kill_switch(
        killswitch_path=kf,
        darkhorse_kill_env=None,
    )
    assert not r.trading_allowed
    assert "kill file" in r.reasons[0]


def test_env_kill_blocks(tmp_path: Path) -> None:
    r = evaluate_kill_switch(
        killswitch_path=tmp_path / "missing",
        darkhorse_kill_env="1",
    )
    assert not r.trading_allowed
    assert any("DARKHORSE_KILL" in x for x in r.reasons)


def test_remote_kill_body(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="true")

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        r = evaluate_kill_switch(
            killswitch_path=tmp_path / "missing",
            darkhorse_kill_env=None,
            remote_kill_url="https://example.test/kill",
            http_client=client,
        )
    assert not r.trading_allowed


def test_stale_review() -> None:
    now = datetime(2026, 5, 9, tzinfo=UTC)
    old = now - timedelta(days=20)
    assert stale_human_review_pause(
        now_utc=now,
        last_doctrine_activity_utc=old,
        last_journal_activity_utc=old,
        stale_after=timedelta(days=14),
    )
    assert not stale_human_review_pause(
        now_utc=now,
        last_doctrine_activity_utc=None,
        last_journal_activity_utc=old,
        stale_after=timedelta(days=14),
    )


def test_monthly_spend_cap() -> None:
    assert monthly_spend_exceeds_cap(spend_usd_this_month=11.0, monthly_cap_usd=10.0)
    assert not monthly_spend_exceeds_cap(spend_usd_this_month=None, monthly_cap_usd=10.0)
