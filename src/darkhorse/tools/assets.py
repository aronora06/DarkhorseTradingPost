"""Asset-list refresh and whitelist helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from darkhorse.config import Settings
from darkhorse.tools._contracts import (
    AssetClass,
    AssetListRefreshInput,
    AssetListRefreshOutput,
    TradableAsset,
    utc_now,
)
from darkhorse.tools.alpaca import _request_json_list


def refresh_asset_list(
    payload: AssetListRefreshInput,
    *,
    output_dir: Path = Path("data/assets"),
    settings: Settings | None = None,
    client: httpx.Client | None = None,
    timeout_s: float = 10.0,
    retry_delays_s: tuple[float, ...] = (1.0, 3.0),
) -> AssetListRefreshOutput:
    """Fetch Alpaca assets and write `data/assets/YYYY-MM-DD.json`."""

    path = "/v2/assets"
    if payload.active_only:
        path += "?status=active"
    rows = _request_json_list(
        "GET",
        path,
        payload.environment,
        settings=settings,
        client=client,
        timeout_s=timeout_s,
        retry_delays_s=retry_delays_s,
    )
    assets = tuple(_asset_from_row(row) for row in rows if _include_asset(row, payload.active_only))
    now = utc_now()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{now.date().isoformat()}.json"
    result = AssetListRefreshOutput(
        environment=payload.environment,
        fetched_at=now,
        output_path=str(output_path),
        assets=assets,
    )
    output_path.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return result


def load_latest_asset_list(input_dir: Path = Path("data/assets")) -> AssetListRefreshOutput:
    """Load the newest asset-list JSON file by filename date."""

    candidates = sorted(input_dir.glob("*.json"))
    if not candidates:
        raise FileNotFoundError(f"no asset-list JSON files in {input_dir}")
    data = json.loads(candidates[-1].read_text(encoding="utf-8"))
    return AssetListRefreshOutput.model_validate(data)


def latest_tradable_symbols(input_dir: Path = Path("data/assets")) -> frozenset[str]:
    """Return tradable symbols from the latest persisted asset list."""

    asset_list = load_latest_asset_list(input_dir)
    return frozenset(asset.symbol for asset in asset_list.assets if asset.tradable)


def _include_asset(row: dict[str, Any], active_only: bool) -> bool:
    if not active_only:
        return True
    return str(row.get("status", "active")).lower() == "active"


def _asset_from_row(row: dict[str, Any]) -> TradableAsset:
    asset_class = _asset_class(row.get("class"))
    return TradableAsset(
        symbol=str(row["symbol"]),
        asset_class=asset_class,
        name=str(row.get("name") or row["symbol"]),
        exchange=_optional_str(row.get("exchange")),
        tradable=bool(row.get("tradable", False)),
        marginable=_optional_bool(row.get("marginable")),
        shortable=_optional_bool(row.get("shortable")),
        fractionable=_optional_bool(row.get("fractionable")),
    )


def _asset_class(value: object) -> AssetClass:
    raw = str(value or "").lower()
    try:
        return AssetClass(raw)
    except ValueError:
        return AssetClass.OTHER


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_bool(value: object) -> bool | None:
    if value is None:
        return None
    return bool(value)
