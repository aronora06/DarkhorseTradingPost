"""Asset-list refresh and whitelist helpers."""

from __future__ import annotations

from pathlib import Path

import httpx

from darkhorse.config import Settings
from darkhorse.tools import AssetListRefreshInput, BrokerEnvironment
from darkhorse.tools.assets import (
    latest_tradable_symbols,
    load_latest_asset_list,
    refresh_asset_list,
)


def _settings() -> Settings:
    return Settings(
        anthropic_api_key="sk-test-ant",
        alpaca_live_api_key="live-key",
        alpaca_live_secret_key="live-secret",
        alpaca_paper_api_key="paper-key",
        alpaca_paper_secret_key="paper-secret",
        perplexity_api_key="pplx",
        tavily_api_key="tvly",
        finnhub_api_key="finn",
        snaptrade_client_id="snap",
        snaptrade_consumer_key="snapc",
        discord_webhook_url="https://discord.test/webhook",
    )


def test_refresh_asset_list_writes_normalized_assets(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v2/assets"
        assert request.url.params["status"] == "active"
        return httpx.Response(
            200,
            json=[
                {
                    "symbol": " aapl ",
                    "class": "us_equity",
                    "name": "Apple Inc.",
                    "exchange": "NASDAQ",
                    "status": "active",
                    "tradable": True,
                    "marginable": True,
                    "shortable": True,
                    "fractionable": True,
                },
                {
                    "symbol": "OLD",
                    "class": "us_equity",
                    "status": "inactive",
                    "tradable": True,
                },
            ],
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = refresh_asset_list(
            AssetListRefreshInput(environment=BrokerEnvironment.PAPER),
            output_dir=tmp_path,
            settings=_settings(),
            client=client,
            retry_delays_s=(0,),
        )

    assert len(result.assets) == 1
    assert result.assets[0].symbol == "AAPL"
    assert Path(result.output_path).is_file()
    loaded = load_latest_asset_list(tmp_path)
    assert loaded.assets[0].name == "Apple Inc."
    assert latest_tradable_symbols(tmp_path) == frozenset({"AAPL"})
