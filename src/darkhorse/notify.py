"""Outbound notifications (`plans/decisions/0011-observability.md`)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import structlog
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


def _retryable_http(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return isinstance(exc, (httpx.TimeoutException, httpx.TransportError))


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception(_retryable_http),
)
def _post_with_client(client: httpx.Client, url: str, payload: dict[str, Any]) -> None:
    response = client.post(url, json=payload)
    response.raise_for_status()


def notify_discord_text(
    webhook_url: str,
    content: str,
    *,
    dead_letter_path: Path | None = None,
    timeout_s: float = 10.0,
) -> None:
    """Post plain-text content to a Discord webhook.

    Discord caps message length; content is truncated defensively.
    """
    payload = {"content": content[:2000]}
    try:
        with httpx.Client(timeout=timeout_s) as client:
            _post_with_client(client, webhook_url, payload)
    except Exception as exc:
        logger.error("discord_notify_failed", error=str(exc))
        if dead_letter_path is not None:
            _append_dead_letter(dead_letter_path, content, str(exc))
        raise


def _append_dead_letter(path: Path, content: str, error: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(
        {
            "at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "error": error,
            "content_preview": content[:500],
        },
        ensure_ascii=False,
    )
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
