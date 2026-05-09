"""Harness production tests — all Anthropic/broker calls mocked via httpx.MockTransport."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx
import pytest

from darkhorse.config import Settings
from darkhorse.harness import (
    CallCost,
    HarnessConfig,
    LLMDecisionOutput,
    RoutineCostCapExceeded,
    _accumulate_cost,
    _api_tool_name,
    _build_researcher_system,
    _build_risk_manager_system,
    _contract_tool_name,
    _is_retryable_anthropic,
    build_anthropic_tools,
    build_snapshot_summary,
    build_tool_definitions,
    compute_call_cost,
    execute_tool_call,
    generate_decision_id,
    run_harness_session,
    run_placeholder_session,
    run_researcher,
    run_risk_manager,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _test_settings(tmp_path: Path) -> Settings:
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
        killswitch_path=tmp_path / "KILLSWITCH",
        remote_kill_url=None,
    )


def _anthropic_message_response(
    *,
    text: str = "Test response",
    stop_reason: str = "end_turn",
    model: str = "claude-sonnet-4-6",
    input_tokens: int = 100,
    output_tokens: int = 50,
    cache_creation: int = 0,
    cache_read: int = 0,
    tool_use_blocks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a canned Anthropic messages API response."""
    content: list[dict[str, Any]] = []
    if tool_use_blocks:
        content.extend(tool_use_blocks)
    if text:
        content.append({"type": "text", "text": text})

    return {
        "id": "msg_test_001",
        "type": "message",
        "role": "assistant",
        "content": content,
        "model": model,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {
            "input_tokens": input_tokens,
            "cache_creation_input_tokens": cache_creation,
            "cache_read_input_tokens": cache_read,
            "output_tokens": output_tokens,
        },
    }


def _no_trade_decision_json() -> str:
    return json.dumps(
        {
            "action": "NO_TRADE",
            "ticker": None,
            "qty": None,
            "order_type": None,
            "limit_price": None,
            "time_in_force": "day",
            "confidence": 0.3,
            "expected_horizon_days": None,
            "expected_outcome_pct": None,
            "thesis_summary": "Insufficient evidence for any trade.",
            "reasoning_trace": {"base_rate": "flat", "spy_comparison": "hold"},
            "market_order_exception": False,
            "lessons_referenced": [],
            "anti_patterns_flagged": [],
        }
    )


def _buy_decision_json() -> str:
    return json.dumps(
        {
            "action": "BUY",
            "ticker": "AAPL",
            "qty": 1,
            "order_type": "limit",
            "limit_price": "45.00",
            "time_in_force": "day",
            "confidence": 0.85,
            "expected_horizon_days": 30,
            "expected_outcome_pct": 5.0,
            "thesis_summary": "Strong earnings momentum with reasonable valuation.",
            "reasoning_trace": {"base_rate": "bullish", "spy_comparison": "outperform"},
            "market_order_exception": False,
            "lessons_referenced": [],
            "anti_patterns_flagged": [],
        }
    )


# ---------------------------------------------------------------------------
# Backward compat tests (Phase 3)
# ---------------------------------------------------------------------------


def test_build_tool_definitions_from_contracts() -> None:
    definitions = build_tool_definitions()
    names = {definition.name for definition in definitions}

    assert "alpaca.submit_order" in names
    assert "news.search" in names
    submit = next(
        definition for definition in definitions if definition.name == "alpaca.submit_order"
    )
    assert submit.input_schema["additionalProperties"] is False


def test_placeholder_session_has_no_llm_side_effect() -> None:
    result = run_placeholder_session(HarnessConfig(routine="market_open", sleeve="core"))
    assert result == {
        "routine": "market_open",
        "sleeve": "core",
        "dry_run": True,
        "status": "harness_not_started",
    }


# ---------------------------------------------------------------------------
# Tool name mapping
# ---------------------------------------------------------------------------


def test_api_tool_name_converts_dots_to_underscores() -> None:
    assert _api_tool_name("data.quote") == "data_quote"
    assert _api_tool_name("alpaca.submit_order") == "alpaca_submit_order"


def test_contract_tool_name_reverses_mapping() -> None:
    assert _contract_tool_name("data_quote") == "data.quote"
    assert _contract_tool_name("news_search") == "news.search"


# ---------------------------------------------------------------------------
# build_anthropic_tools
# ---------------------------------------------------------------------------


def test_build_anthropic_tools_strict_schemas() -> None:
    tools = build_anthropic_tools()
    assert len(tools) == 5

    names = {t["name"] for t in tools}
    assert names == {"data_quote", "data_bars", "news_search", "alpaca_account", "alpaca_positions"}

    for tool in tools:
        assert tool["strict"] is True
        assert "input_schema" in tool
        assert "name" in tool
        assert "description" in tool


def test_build_anthropic_tools_excludes_submit_order() -> None:
    tools = build_anthropic_tools()
    names = {t["name"] for t in tools}
    assert "alpaca_submit_order" not in names
    assert "alpaca_cancel_order" not in names


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------


def test_execute_tool_call_unknown_tool() -> None:
    result = execute_tool_call("nonexistent_tool", {})
    assert "error" in result
    assert "Unknown tool" in result["error"]


def test_execute_tool_call_invalid_input() -> None:
    result = execute_tool_call("data_quote", {"bad_field": "value"})
    assert "error" in result
    assert "Invalid input" in result["error"]


def test_execute_tool_call_routes_to_quote(tmp_path: Path) -> None:
    """Test that data_quote dispatches to fetch_quote via MockTransport."""

    def handler(request: httpx.Request) -> httpx.Response:
        if "finnhub" in str(request.url):
            return httpx.Response(
                200,
                json={"c": 150.0, "h": 152.0, "l": 149.0, "o": 150.5, "t": 1715270400},
            )
        return httpx.Response(404)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = execute_tool_call(
            "data_quote",
            {"symbol": "AAPL"},
            settings=_test_settings(tmp_path),
            broker_client=client,
        )

    assert "error" not in result
    assert result["symbol"] == "AAPL"
    assert "last_usd" in result


def test_execute_tool_call_routes_to_account(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v2/account":
            return httpx.Response(
                200,
                json={
                    "id": "acct_123",
                    "status": "ACTIVE",
                    "cash": "1000.00",
                    "buying_power": "995.00",
                    "equity": "1000.00",
                    "pattern_day_trader": False,
                    "daytrade_count": 1,
                    "trading_blocked": False,
                },
            )
        return httpx.Response(404)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = execute_tool_call(
            "alpaca_account",
            {"environment": "paper"},
            settings=_test_settings(tmp_path),
            broker_client=client,
        )

    assert "error" not in result
    assert result["status"] == "ACTIVE"
    assert result["equity_usd"] == "1000.00"


# ---------------------------------------------------------------------------
# Cost computation
# ---------------------------------------------------------------------------


def test_compute_call_cost_accuracy() -> None:
    """Verify USD math from token counts against known Sonnet pricing."""

    class FakeUsage:
        input_tokens = 1000
        output_tokens = 500
        cache_creation_input_tokens = 200
        cache_read_input_tokens = 800
        cache_creation: object = None
        inference_geo: object = None
        server_tool_use: object = None
        service_tier: object = None

    cost = compute_call_cost(FakeUsage(), "claude-sonnet-4-6")  # type: ignore[arg-type]

    assert cost.input_tokens == 1000
    assert cost.output_tokens == 500
    assert cost.cache_creation_input_tokens == 200
    assert cost.cache_read_input_tokens == 800
    assert cost.usd > Decimal("0")

    mtok = Decimal("1000000")
    expected = (
        Decimal("200") * Decimal("6") / mtok
        + Decimal("800") * Decimal("0.30") / mtok
        + Decimal("1000") * Decimal("3") / mtok
        + Decimal("500") * Decimal("15") / mtok
    )
    assert cost.usd == expected.quantize(Decimal("0.000001"))


def test_compute_call_cost_unknown_model() -> None:
    class FakeUsage:
        input_tokens = 100
        output_tokens = 50
        cache_creation_input_tokens = 0
        cache_read_input_tokens = 0
        cache_creation: object = None
        inference_geo: object = None
        server_tool_use: object = None
        service_tier: object = None

    cost = compute_call_cost(FakeUsage(), "unknown-model")  # type: ignore[arg-type]
    assert cost.usd == Decimal("0")
    assert cost.input_tokens == 100


def test_accumulate_cost() -> None:
    a = CallCost(input_tokens=100, output_tokens=50, usd=Decimal("0.01"))
    b = CallCost(input_tokens=200, output_tokens=100, usd=Decimal("0.02"))
    total = _accumulate_cost(a, b)
    assert total.input_tokens == 300
    assert total.output_tokens == 150
    assert total.usd == Decimal("0.03")


# ---------------------------------------------------------------------------
# LLMDecisionOutput
# ---------------------------------------------------------------------------


def test_llm_decision_output_no_trade_parses() -> None:
    decision = LLMDecisionOutput.model_validate_json(_no_trade_decision_json())
    assert decision.action == "NO_TRADE"
    assert decision.ticker is None
    assert decision.confidence == 0.3


def test_llm_decision_output_buy_parses() -> None:
    decision = LLMDecisionOutput.model_validate_json(_buy_decision_json())
    assert decision.action == "BUY"
    assert decision.ticker == "AAPL"
    assert decision.qty == 1
    assert decision.confidence == 0.85


def test_llm_decision_output_rejects_invalid_confidence() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        LLMDecisionOutput.model_validate_json(
            json.dumps(
                {
                    "action": "BUY",
                    "confidence": 1.5,
                    "thesis_summary": "test",
                }
            )
        )


# ---------------------------------------------------------------------------
# Snapshot summary
# ---------------------------------------------------------------------------


def test_build_snapshot_summary() -> None:
    summary = build_snapshot_summary(
        account_equity=Decimal("1000"),
        buying_power=Decimal("995"),
        positions=[{"symbol": "AAPL", "qty": "1", "market_value_usd": "190"}],
        deploy_cap=Decimal("50"),
    )
    assert "Account equity: $1000" in summary
    assert "AAPL" in summary
    assert "Phase deployment cap: $50" in summary


def test_generate_decision_id_format() -> None:
    did = generate_decision_id()
    assert did.startswith("dec_")
    assert len(did) > 10


# ---------------------------------------------------------------------------
# System prompt builders
# ---------------------------------------------------------------------------


def test_build_researcher_system_has_doctrine_and_cache() -> None:
    blocks = _build_researcher_system("doctrine text", "researcher instructions", "state")
    assert len(blocks) == 3
    assert "doctrine text" in blocks[0]["text"]
    assert blocks[0]["cache_control"]["type"] == "ephemeral"
    assert blocks[0]["cache_control"]["ttl"] == "1h"
    assert "researcher instructions" in blocks[1]["text"]
    assert "cache_control" not in blocks[1]


def test_build_risk_manager_system_has_doctrine_and_cache() -> None:
    blocks = _build_risk_manager_system("doctrine text", "risk manager instructions")
    assert len(blocks) == 2
    assert blocks[0]["cache_control"]["ttl"] == "1h"


# ---------------------------------------------------------------------------
# Retry predicate
# ---------------------------------------------------------------------------


def _make_httpx_response(status_code: int) -> httpx.Response:
    """Build an httpx Response with a dummy request attached (required by Anthropic SDK)."""
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx.Response(status_code, request=request)
    return response


def test_retryable_on_rate_limit() -> None:
    import anthropic

    exc = anthropic.RateLimitError(
        message="rate limit",
        response=_make_httpx_response(429),
        body=None,
    )
    assert _is_retryable_anthropic(exc) is True


def test_retryable_on_internal_server_error() -> None:
    import anthropic

    exc = anthropic.InternalServerError(
        message="overloaded",
        response=_make_httpx_response(529),
        body=None,
    )
    assert _is_retryable_anthropic(exc) is True


def test_not_retryable_on_bad_request() -> None:
    import anthropic

    exc = anthropic.BadRequestError(
        message="bad request",
        response=_make_httpx_response(400),
        body=None,
    )
    assert _is_retryable_anthropic(exc) is False


def test_not_retryable_on_auth_error() -> None:
    import anthropic

    exc = anthropic.AuthenticationError(
        message="auth error",
        response=_make_httpx_response(401),
        body=None,
    )
    assert _is_retryable_anthropic(exc) is False


# ---------------------------------------------------------------------------
# run_researcher (mocked Anthropic)
# ---------------------------------------------------------------------------


def _anthropic_mock_transport(
    responses: list[dict[str, Any]],
) -> httpx.MockTransport:
    """Create a MockTransport that returns canned Anthropic responses in sequence."""
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        idx = min(call_count["n"], len(responses) - 1)
        call_count["n"] += 1
        return httpx.Response(200, json=responses[idx])

    return httpx.MockTransport(handler)


def test_researcher_tool_loop_end_turn(tmp_path: Path) -> None:
    """Researcher gets end_turn on first call — no tool use needed."""
    import anthropic

    response = _anthropic_message_response(text="Research complete: market is flat.")
    transport = _anthropic_mock_transport([response])

    with httpx.Client(transport=transport) as http_client:
        client = anthropic.Anthropic(api_key="sk-test", http_client=http_client)
        text, cost, iterations, tools_used = run_researcher(
            anthropic_client=client,
            model="claude-sonnet-4-6",
            system_blocks=[{"type": "text", "text": "test"}],
            tools=[],
            user_message="Run research.",
        )

    assert "Research complete" in text
    assert iterations == 1
    assert len(tools_used) == 0
    assert cost.input_tokens == 100


def test_researcher_tool_loop_with_tool_use(tmp_path: Path) -> None:
    """Researcher uses a tool, then ends."""
    import anthropic

    tool_response = _anthropic_message_response(
        text="",
        stop_reason="tool_use",
        tool_use_blocks=[
            {
                "type": "tool_use",
                "id": "toolu_001",
                "name": "alpaca_account",
                "input": {"environment": "paper"},
            }
        ],
    )
    final_response = _anthropic_message_response(text="Account has $1000 equity.")
    transport = _anthropic_mock_transport([tool_response, final_response])

    def broker_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v2/account":
            return httpx.Response(
                200,
                json={
                    "id": "acct_123",
                    "status": "ACTIVE",
                    "cash": "1000.00",
                    "buying_power": "995.00",
                    "equity": "1000.00",
                    "pattern_day_trader": False,
                    "daytrade_count": 0,
                    "trading_blocked": False,
                },
            )
        return httpx.Response(404)

    with httpx.Client(transport=transport) as http_client:
        client = anthropic.Anthropic(api_key="sk-test", http_client=http_client)
        with httpx.Client(transport=httpx.MockTransport(broker_handler)) as broker:
            text, cost, iterations, tools_used = run_researcher(
                anthropic_client=client,
                model="claude-sonnet-4-6",
                system_blocks=[{"type": "text", "text": "test"}],
                tools=build_anthropic_tools(),
                user_message="Run research.",
                settings=_test_settings(tmp_path),
                broker_client=broker,
            )

    assert "Account has $1000 equity" in text
    assert iterations == 2
    assert len(tools_used) == 1
    assert tools_used[0]["tool"] == "alpaca_account"


# ---------------------------------------------------------------------------
# run_risk_manager (mocked Anthropic)
# ---------------------------------------------------------------------------


def test_risk_manager_structured_output_no_trade(tmp_path: Path) -> None:
    import anthropic

    response = _anthropic_message_response(text=_no_trade_decision_json())
    transport = _anthropic_mock_transport([response])

    with httpx.Client(transport=transport) as http_client:
        client = anthropic.Anthropic(api_key="sk-test", http_client=http_client)
        decision, cost = run_risk_manager(
            anthropic_client=client,
            model="claude-opus-4-7",
            system_blocks=[{"type": "text", "text": "test"}],
            research_text="Market is flat.",
            snapshot_summary="Equity: $1000",
        )

    assert decision.action == "NO_TRADE"
    assert cost.input_tokens == 100


def test_risk_manager_structured_output_buy(tmp_path: Path) -> None:
    import anthropic

    response = _anthropic_message_response(text=_buy_decision_json())
    transport = _anthropic_mock_transport([response])

    with httpx.Client(transport=transport) as http_client:
        client = anthropic.Anthropic(api_key="sk-test", http_client=http_client)
        decision, cost = run_risk_manager(
            anthropic_client=client,
            model="claude-opus-4-7",
            system_blocks=[{"type": "text", "text": "test"}],
            research_text="AAPL showing strength.",
            snapshot_summary="Equity: $1000",
        )

    assert decision.action == "BUY"
    assert decision.ticker == "AAPL"
    assert decision.confidence == 0.85


# ---------------------------------------------------------------------------
# run_harness_session (full pipeline, mocked)
# ---------------------------------------------------------------------------


def _full_mock_transport(
    researcher_text: str = "Research done.",
    decision_json: str | None = None,
) -> httpx.MockTransport:
    """Mock both researcher and risk-manager Anthropic calls."""
    if decision_json is None:
        decision_json = _no_trade_decision_json()

    responses = [
        _anthropic_message_response(text=researcher_text, model="claude-sonnet-4-6"),
        _anthropic_message_response(text=decision_json, model="claude-opus-4-7"),
    ]
    return _anthropic_mock_transport(responses)


def test_harness_session_no_trade(tmp_path: Path) -> None:
    transport = _full_mock_transport()
    settings = _test_settings(tmp_path)

    with httpx.Client(transport=transport) as http_client:
        result = run_harness_session(
            snapshot_summary="Equity: $1000",
            allowed_symbols=frozenset({"AAPL", "SPY"}),
            settings=settings,
            anthropic_http_client=http_client,
        )

    assert result.decision.action == "NO_TRADE"
    assert result.total_cost.usd > Decimal("0")
    assert result.researcher_iterations == 1


def test_harness_session_buy_decision(tmp_path: Path) -> None:
    transport = _full_mock_transport(
        researcher_text="AAPL earnings strong.",
        decision_json=_buy_decision_json(),
    )
    settings = _test_settings(tmp_path)

    with httpx.Client(transport=transport) as http_client:
        result = run_harness_session(
            snapshot_summary="Equity: $1000",
            allowed_symbols=frozenset({"AAPL", "SPY"}),
            settings=settings,
            anthropic_http_client=http_client,
        )

    assert result.decision.action == "BUY"
    assert result.decision.ticker == "AAPL"
    assert result.model_assignments["researcher"] == "claude-sonnet-4-6"
    assert result.model_assignments["risk_manager"] == "claude-opus-4-7"


def test_harness_session_cost_cap_exceeded(tmp_path: Path) -> None:
    transport = _full_mock_transport()
    settings = _test_settings(tmp_path)

    with httpx.Client(transport=transport) as http_client, pytest.raises(RoutineCostCapExceeded):
        run_harness_session(
            snapshot_summary="Equity: $1000",
            allowed_symbols=frozenset({"AAPL"}),
            settings=settings,
            anthropic_http_client=http_client,
            cost_cap_usd=Decimal("0.000001"),
        )


# ---------------------------------------------------------------------------
# Doctrine / prompt loading
# ---------------------------------------------------------------------------


def test_load_doctrine_context_returns_text() -> None:
    from darkhorse.harness import load_doctrine_context

    doctrine = load_doctrine_context()
    assert "risk_policy" in doctrine
    assert "core_sleeve" in doctrine
    assert len(doctrine) > 100


def test_load_prompt_returns_text() -> None:
    from darkhorse.harness import load_prompt

    prompt = load_prompt("researcher")
    assert "Researcher" in prompt
    assert len(prompt) > 50
