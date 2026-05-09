"""Discord notify (mocked HTTP)."""

from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from darkhorse import notify


def test_notify_discord_invokes_post(monkeypatch: pytest.MonkeyPatch) -> None:
    mock = MagicMock()
    monkeypatch.setattr(notify, "_post_with_client", mock)
    notify.notify_discord_text("https://discord.test/webhook", "hello world")
    mock.assert_called_once()
    _client, url, payload = mock.call_args[0]
    assert url == "https://discord.test/webhook"
    assert payload["content"] == "hello world"


def test_notify_dead_letter_on_total_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(*_a: object, **_k: object) -> None:
        raise httpx.HTTPError("network down")

    monkeypatch.setattr(notify, "_post_with_client", boom)
    dl = tmp_path / "dead.jsonl"
    with pytest.raises(httpx.HTTPError):
        notify.notify_discord_text("https://discord.test/webhook", "oops", dead_letter_path=dl)
    text = dl.read_text(encoding="utf-8")
    assert "oops" in text
    assert "network down" in text
