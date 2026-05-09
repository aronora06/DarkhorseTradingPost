"""Production Anthropic harness — thin LLM loop with deterministic risk walls.

ADR-0008: custom harness, no framework (reconsider split if >1000 lines).
Architecture: researcher (Sonnet) gathers context via tools, risk-manager (Opus)
produces a structured decision, Python validates before any order submission.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from decimal import Decimal
from typing import Any, Literal

import anthropic
import httpx
import structlog
from pydantic import BaseModel, ConfigDict, Field
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from darkhorse.config import REPO_ROOT, Settings, get_settings
from darkhorse.tools import TOOL_CONTRACTS, ToolContractModel
from darkhorse.tools._contracts import utc_now

logger = structlog.get_logger(__name__)

_MAX_TOOL_ITERATIONS: int = 10
_CONFIDENCE_THRESHOLD: float = 0.70

RESEARCHER_TOOLS: frozenset[str] = frozenset(
    {
        "data.quote",
        "data.bars",
        "news.search",
        "alpaca.account",
        "alpaca.positions",
    }
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class HarnessConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    routine: str
    sleeve: Literal["core", "satellite"]
    dry_run: bool = True


class ToolDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]


class LLMDecisionOutput(BaseModel):
    """Schema the risk-manager emits via structured output.

    Fields are non-nullable to satisfy Anthropic's grammar compiler.
    Empty strings / 0 values represent "not applicable" for NO_TRADE.
    """

    model_config = ConfigDict(extra="forbid")

    action: Literal["BUY", "SELL", "NO_TRADE"]
    ticker: str = ""
    qty: int = Field(default=0, ge=0)
    order_type: Literal["limit", "market", "none"] = "none"
    limit_price: str = ""
    time_in_force: Literal["day", "gtc"] = "day"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    expected_horizon_days: int = Field(default=0, ge=0)
    expected_outcome_pct: float = 0.0
    thesis_summary: str = ""
    reasoning_steps: list[str] = Field(default_factory=list)
    market_order_exception: bool = False
    lessons_referenced: list[str] = Field(default_factory=list)
    anti_patterns_flagged: list[str] = Field(default_factory=list)


class ModelPricing(BaseModel):
    """Per-token USD costs for a model (prices per token, not per MTok)."""

    model_config = ConfigDict(extra="forbid")

    input_per_token: Decimal
    output_per_token: Decimal
    cache_write_per_token: Decimal
    cache_read_per_token: Decimal


class CallCost(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    usd: Decimal = Decimal("0")


class HarnessResult(BaseModel):
    """Full result of a harness session including decision and telemetry."""

    model_config = ConfigDict(extra="forbid")

    decision: LLMDecisionOutput
    research_text: str
    total_cost: CallCost
    researcher_iterations: int
    model_assignments: dict[str, str]
    tools_used: list[dict[str, Any]]


class RoutineCostCapExceeded(Exception):
    """Raised when cumulative routine cost exceeds the configured cap."""


# ---------------------------------------------------------------------------
# Pricing tables (per-token, derived from per-MTok published rates)
# ---------------------------------------------------------------------------

_MTOK = Decimal("1000000")

MODEL_PRICING: dict[str, ModelPricing] = {
    "claude-opus-4-7": ModelPricing(
        input_per_token=Decimal("15") / _MTOK,
        output_per_token=Decimal("75") / _MTOK,
        cache_write_per_token=Decimal("30") / _MTOK,
        cache_read_per_token=Decimal("1.50") / _MTOK,
    ),
    "claude-sonnet-4-6": ModelPricing(
        input_per_token=Decimal("3") / _MTOK,
        output_per_token=Decimal("15") / _MTOK,
        cache_write_per_token=Decimal("6") / _MTOK,
        cache_read_per_token=Decimal("0.30") / _MTOK,
    ),
    "claude-haiku-4-5-20251001": ModelPricing(
        input_per_token=Decimal("0.80") / _MTOK,
        output_per_token=Decimal("4") / _MTOK,
        cache_write_per_token=Decimal("1.60") / _MTOK,
        cache_read_per_token=Decimal("0.08") / _MTOK,
    ),
}


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------


def _api_tool_name(contract_name: str) -> str:
    """Convert dot-separated contract name to Anthropic-compatible underscore name."""
    return contract_name.replace(".", "_")


def _contract_tool_name(api_name: str) -> str:
    """Reverse of ``_api_tool_name``."""
    return api_name.replace("_", ".", 1)


def build_tool_definitions() -> tuple[ToolDefinition, ...]:
    """Build strict tool schema definitions from registered Pydantic contracts."""
    return tuple(
        ToolDefinition(
            name=name,
            input_schema=_strict_schema(input_model),
            output_schema=_strict_schema(output_model),
        )
        for name, (input_model, output_model) in sorted(TOOL_CONTRACTS.items())
    )


def build_anthropic_tools(
    allowed: frozenset[str] = RESEARCHER_TOOLS,
) -> list[dict[str, Any]]:
    """Build Anthropic ``tools=[...]`` payload with ``strict: true``."""
    tools: list[dict[str, Any]] = []
    for name, (input_model, _output_model) in sorted(TOOL_CONTRACTS.items()):
        if name not in allowed:
            continue
        schema = _strict_schema(input_model)
        tools.append(
            {
                "name": _api_tool_name(name),
                "description": _tool_description(name),
                "input_schema": schema,
                "strict": True,
            }
        )
    return tools


def _strict_schema(model: type[ToolContractModel]) -> dict[str, Any]:
    schema = model.model_json_schema()
    schema["additionalProperties"] = False
    _strip_unsupported_numeric_constraints(schema)
    return schema


_UNSUPPORTED_NUMERIC_KEYS: frozenset[str] = frozenset(
    {"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum"}
)

_CONSTRAINED_TYPES: frozenset[str] = frozenset({"integer", "number"})


def _strip_unsupported_numeric_constraints(node: dict[str, Any]) -> None:
    """Anthropic rejects minimum/maximum on integer and number type properties."""
    if node.get("type") in _CONSTRAINED_TYPES:
        for key in _UNSUPPORTED_NUMERIC_KEYS:
            node.pop(key, None)
    for value in node.values():
        if isinstance(value, dict):
            _strip_unsupported_numeric_constraints(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _strip_unsupported_numeric_constraints(item)


_DECISION_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "action",
        "ticker",
        "qty",
        "order_type",
        "limit_price",
        "time_in_force",
        "confidence",
        "expected_horizon_days",
        "expected_outcome_pct",
        "thesis_summary",
        "reasoning_steps",
        "market_order_exception",
        "lessons_referenced",
        "anti_patterns_flagged",
    ],
    "properties": {
        "action": {"type": "string", "enum": ["BUY", "SELL", "NO_TRADE"]},
        "ticker": {"type": "string", "description": "Symbol or empty string for NO_TRADE"},
        "qty": {"type": "integer", "description": "Shares, 0 for NO_TRADE"},
        "order_type": {"type": "string", "enum": ["limit", "market", "none"]},
        "limit_price": {"type": "string", "description": "Decimal string or empty"},
        "time_in_force": {"type": "string", "enum": ["day", "gtc"]},
        "confidence": {"type": "number"},
        "expected_horizon_days": {"type": "integer"},
        "expected_outcome_pct": {"type": "number"},
        "thesis_summary": {"type": "string"},
        "reasoning_steps": {"type": "array", "items": {"type": "string"}},
        "market_order_exception": {"type": "boolean"},
        "lessons_referenced": {"type": "array", "items": {"type": "string"}},
        "anti_patterns_flagged": {"type": "array", "items": {"type": "string"}},
    },
}


_TOOL_DESCRIPTIONS: dict[str, str] = {
    "data.quote": "Fetch the latest quote for a symbol (Finnhub with Yahoo fallback).",
    "data.bars": "Fetch OHLCV price bars for a symbol over a date range.",
    "news.search": "Search recent financial news for a query and optional symbols.",
    "alpaca.account": "Fetch the current Alpaca broker account snapshot.",
    "alpaca.positions": "Fetch all open Alpaca positions.",
}


def _tool_description(name: str) -> str:
    return _TOOL_DESCRIPTIONS.get(name, f"Tool: {name}")


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------


def execute_tool_call(
    tool_name: str,
    tool_input: dict[str, Any],
    *,
    settings: Settings | None = None,
    broker_client: httpx.Client | None = None,
    allowed_symbols: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Dispatch a tool call to the corresponding implementation.

    Validates input via the pydantic contract, calls the tool, serialises output.
    """
    from darkhorse.tools._contracts import (
        BarsInput,
        NewsSearchInput,
        QuoteInput,
    )
    from darkhorse.tools.alpaca import fetch_account, fetch_positions
    from darkhorse.tools.data import fetch_bars, fetch_quote
    from darkhorse.tools.news import search_news

    contract_name = _contract_tool_name(tool_name)
    contract_pair = TOOL_CONTRACTS.get(contract_name)
    if contract_pair is None:
        return {"error": f"Unknown tool: {tool_name}"}

    input_model_cls, _output_model_cls = contract_pair

    try:
        validated_input = input_model_cls.model_validate(tool_input)
    except Exception as exc:
        return {"error": f"Invalid input for {tool_name}: {exc}"}

    active_settings = settings or get_settings()
    try:
        output: ToolContractModel
        if contract_name == "data.quote" and isinstance(validated_input, QuoteInput):
            output = fetch_quote(validated_input, settings=active_settings, client=broker_client)
        elif contract_name == "data.bars" and isinstance(validated_input, BarsInput):
            output = fetch_bars(validated_input, settings=active_settings, client=broker_client)
        elif contract_name == "news.search" and isinstance(validated_input, NewsSearchInput):
            output = search_news(
                validated_input,
                allowed_symbols=allowed_symbols,
                settings=active_settings,
                client=broker_client,
            )
        elif contract_name == "alpaca.account":
            output = fetch_account(
                validated_input,  # type: ignore[arg-type]
                settings=active_settings,
                client=broker_client,
            )
        elif contract_name == "alpaca.positions":
            output = fetch_positions(
                validated_input,  # type: ignore[arg-type]
                settings=active_settings,
                client=broker_client,
            )
        else:
            return {"error": f"Tool {tool_name} has no dispatch implementation"}
    except Exception as exc:
        logger.warning("tool_execution_error", tool=tool_name, error=str(exc))
        return {"error": f"Tool execution failed: {exc}"}

    raw: dict[str, Any] = json.loads(output.model_dump_json())
    return raw


# ---------------------------------------------------------------------------
# Doctrine context loading
# ---------------------------------------------------------------------------

_DOCTRINE_DIR = REPO_ROOT / "doctrine"
_PROMPTS_DIR = REPO_ROOT / "prompts"


def load_doctrine_context() -> str:
    """Read all doctrine/*.md files and return concatenated text."""
    parts: list[str] = []
    for md_path in sorted(_DOCTRINE_DIR.glob("*.md")):
        if md_path.name == "README.md":
            continue
        content = md_path.read_text(encoding="utf-8").strip()
        parts.append(f"## {md_path.stem}\n\n{content}")
    return "\n\n---\n\n".join(parts)


def load_prompt(name: str) -> str:
    """Read a prompt file from ``prompts/<name>.md``."""
    path = _PROMPTS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8").strip()


# ---------------------------------------------------------------------------
# Cost telemetry
# ---------------------------------------------------------------------------


def compute_call_cost(usage: anthropic.types.Usage, model: str) -> CallCost:
    """Compute USD cost from Anthropic usage response and model pricing."""
    pricing = MODEL_PRICING.get(model)
    if pricing is None:
        logger.warning("unknown_model_pricing", model=model)
        return CallCost(
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cache_creation_input_tokens=usage.cache_creation_input_tokens or 0,
            cache_read_input_tokens=usage.cache_read_input_tokens or 0,
        )

    cache_create = usage.cache_creation_input_tokens or 0
    cache_read = usage.cache_read_input_tokens or 0
    usd = (
        Decimal(str(cache_create)) * pricing.cache_write_per_token
        + Decimal(str(cache_read)) * pricing.cache_read_per_token
        + Decimal(str(usage.input_tokens)) * pricing.input_per_token
        + Decimal(str(usage.output_tokens)) * pricing.output_per_token
    )

    return CallCost(
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cache_creation_input_tokens=cache_create,
        cache_read_input_tokens=cache_read,
        usd=usd.quantize(Decimal("0.000001")),
    )


def _accumulate_cost(total: CallCost, call: CallCost) -> CallCost:
    return CallCost(
        input_tokens=total.input_tokens + call.input_tokens,
        output_tokens=total.output_tokens + call.output_tokens,
        cache_creation_input_tokens=(
            total.cache_creation_input_tokens + call.cache_creation_input_tokens
        ),
        cache_read_input_tokens=total.cache_read_input_tokens + call.cache_read_input_tokens,
        usd=total.usd + call.usd,
    )


# ---------------------------------------------------------------------------
# Retry predicate
# ---------------------------------------------------------------------------


def _is_retryable_anthropic(exc: BaseException) -> bool:
    if isinstance(exc, anthropic.RateLimitError):
        return True
    return isinstance(exc, anthropic.InternalServerError)


def _log_retry(state: RetryCallState) -> None:
    logger.warning(
        "anthropic_retry",
        attempt=state.attempt_number,
        error=str(state.outcome.exception()) if state.outcome else "unknown",
    )


# ---------------------------------------------------------------------------
# System prompt builders
# ---------------------------------------------------------------------------


def _build_researcher_system(
    doctrine: str,
    researcher_prompt: str,
    snapshot_summary: str,
) -> list[dict[str, Any]]:
    """Build the system prompt blocks for the researcher role."""
    return [
        {
            "type": "text",
            "text": f"<doctrine>\n{doctrine}\n</doctrine>",
            "cache_control": {"type": "ephemeral", "ttl": "1h"},
        },
        {
            "type": "text",
            "text": f"<role_instructions>\n{researcher_prompt}\n</role_instructions>",
        },
        {
            "type": "text",
            "text": f"<current_state>\n{snapshot_summary}\n</current_state>",
        },
    ]


def _build_risk_manager_system(
    doctrine: str,
    risk_manager_prompt: str,
) -> list[dict[str, Any]]:
    """Build the system prompt blocks for the risk-manager role."""
    return [
        {
            "type": "text",
            "text": f"<doctrine>\n{doctrine}\n</doctrine>",
            "cache_control": {"type": "ephemeral", "ttl": "1h"},
        },
        {
            "type": "text",
            "text": f"<role_instructions>\n{risk_manager_prompt}\n</role_instructions>",
        },
    ]


# ---------------------------------------------------------------------------
# Core LLM loop
# ---------------------------------------------------------------------------


@retry(
    retry=retry_if_exception(_is_retryable_anthropic),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=9),
    before_sleep=_log_retry,
    reraise=True,
)
def _create_message(
    client: anthropic.Anthropic,
    **kwargs: Any,
) -> anthropic.types.Message:
    """Single Anthropic API call wrapped in retry logic."""
    result: anthropic.types.Message = client.messages.create(**kwargs)
    return result


def run_researcher(
    *,
    anthropic_client: anthropic.Anthropic,
    model: str,
    system_blocks: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    user_message: str,
    settings: Settings | None = None,
    broker_client: httpx.Client | None = None,
    allowed_symbols: frozenset[str] | None = None,
    cost_cap_usd: Decimal | None = None,
) -> tuple[str, CallCost, int, list[dict[str, Any]]]:
    """Run the researcher tool loop. Returns (text, cost, iterations, tools_used)."""
    log = logger.bind(role="researcher", model=model)
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_message}]
    total_cost = CallCost()
    tools_used: list[dict[str, Any]] = []

    for iteration in range(1, _MAX_TOOL_ITERATIONS + 1):
        log.info("researcher_iteration", iteration=iteration)

        response = _create_message(
            anthropic_client,
            model=model,
            max_tokens=4096,
            system=system_blocks,
            messages=messages,
            tools=tools,
        )

        call_cost = compute_call_cost(response.usage, model)
        total_cost = _accumulate_cost(total_cost, call_cost)
        log.debug(
            "researcher_api_call",
            iteration=iteration,
            stop_reason=response.stop_reason,
            cost_usd=str(call_cost.usd),
        )

        if cost_cap_usd is not None and total_cost.usd > cost_cap_usd:
            raise RoutineCostCapExceeded(
                f"Routine cost {total_cost.usd} exceeded cap {cost_cap_usd}"
            )

        messages.append({"role": "assistant", "content": _serialise_content(response.content)})

        if response.stop_reason == "end_turn":
            text = _extract_text(response.content)
            return text, total_cost, iteration, tools_used

        if response.stop_reason == "tool_use":
            tool_results: list[dict[str, Any]] = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                tool_args: dict[str, Any] = dict(block.input)
                result = execute_tool_call(
                    block.name,
                    tool_args,
                    settings=settings,
                    broker_client=broker_client,
                    allowed_symbols=allowed_symbols,
                )
                result_json = json.dumps(result, default=str, sort_keys=True)
                result_hash = hashlib.sha256(result_json.encode()).hexdigest()[:16]
                tools_used.append(
                    {"tool": block.name, "args": block.input, "result_hash": result_hash}
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_json,
                    }
                )
            messages.append({"role": "user", "content": tool_results})
            continue

        raise RuntimeError(f"Unexpected stop_reason from researcher: {response.stop_reason}")

    text = _extract_text_from_messages(messages)
    log.warning("researcher_max_iterations", iterations=_MAX_TOOL_ITERATIONS)
    return text, total_cost, _MAX_TOOL_ITERATIONS, tools_used


def run_risk_manager(
    *,
    anthropic_client: anthropic.Anthropic,
    model: str,
    system_blocks: list[dict[str, Any]],
    research_text: str,
    snapshot_summary: str,
    cost_cap_usd: Decimal | None = None,
    accumulated_cost: CallCost | None = None,
) -> tuple[LLMDecisionOutput, CallCost]:
    """Run the risk-manager with structured output. Returns (decision, cost)."""
    log = logger.bind(role="risk_manager", model=model)
    log.info("risk_manager_start")

    response = _create_message(
        anthropic_client,
        model=model,
        max_tokens=2048,
        system=system_blocks,
        messages=[
            {
                "role": "user",
                "content": (
                    f"<research_context>\n{research_text}\n</research_context>\n\n"
                    f"<portfolio_state>\n{snapshot_summary}\n</portfolio_state>\n\n"
                    "Based on the research context and portfolio state above, "
                    "produce your trading decision as JSON."
                ),
            }
        ],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": _DECISION_OUTPUT_SCHEMA,
            }
        },
    )

    call_cost = compute_call_cost(response.usage, model)
    log.debug("risk_manager_api_call", cost_usd=str(call_cost.usd))

    if cost_cap_usd is not None and accumulated_cost is not None:
        combined = _accumulate_cost(accumulated_cost, call_cost)
        if combined.usd > cost_cap_usd:
            raise RoutineCostCapExceeded(f"Routine cost {combined.usd} exceeded cap {cost_cap_usd}")

    text = _extract_text(response.content)
    decision = LLMDecisionOutput.model_validate_json(text)
    log.info(
        "risk_manager_decision",
        action=decision.action,
        ticker=decision.ticker,
        confidence=decision.confidence,
    )
    return decision, call_cost


# ---------------------------------------------------------------------------
# Full session orchestrator
# ---------------------------------------------------------------------------


def run_harness_session(
    *,
    snapshot_summary: str,
    allowed_symbols: frozenset[str],
    settings: Settings | None = None,
    anthropic_http_client: httpx.Client | None = None,
    broker_http_client: httpx.Client | None = None,
    researcher_model: str = "claude-sonnet-4-6",
    risk_manager_model: str = "claude-opus-4-7",
    cost_cap_usd: Decimal | None = None,
) -> HarnessResult:
    """Orchestrate researcher -> risk-manager and return the decision.

    Does NOT validate, submit, journal, or notify — the caller (market_open)
    owns those steps so that the harness stays <500 lines and testable.
    """
    active_settings = settings or get_settings()
    log = logger.bind(routine="harness_session")

    cap = cost_cap_usd
    if cap is None:
        cap = Decimal(str(active_settings.routine_cost_cap_usd))

    anthropic_client = anthropic.Anthropic(
        api_key=active_settings.anthropic_api_key.get_secret_value(),
        http_client=anthropic_http_client,
    )

    doctrine = load_doctrine_context()
    researcher_prompt = load_prompt("researcher")
    risk_manager_prompt = load_prompt("risk_manager")
    tools = build_anthropic_tools()

    researcher_system = _build_researcher_system(doctrine, researcher_prompt, snapshot_summary)
    user_msg = (
        f"Today is {utc_now().strftime('%Y-%m-%d')}. "
        "Run the market_open routine for the Core sleeve. "
        "Use your tools to gather current market data, news, account state, "
        "and positions. Summarise your findings for the risk manager."
    )

    log.info("researcher_phase_start", model=researcher_model)
    research_text, researcher_cost, iterations, tools_used = run_researcher(
        anthropic_client=anthropic_client,
        model=researcher_model,
        system_blocks=researcher_system,
        tools=tools,
        user_message=user_msg,
        settings=active_settings,
        broker_client=broker_http_client,
        allowed_symbols=allowed_symbols,
        cost_cap_usd=cap,
    )
    log.info(
        "researcher_phase_done",
        iterations=iterations,
        cost_usd=str(researcher_cost.usd),
        tools_used_count=len(tools_used),
    )

    risk_system = _build_risk_manager_system(doctrine, risk_manager_prompt)

    log.info("risk_manager_phase_start", model=risk_manager_model)
    decision, rm_cost = run_risk_manager(
        anthropic_client=anthropic_client,
        model=risk_manager_model,
        system_blocks=risk_system,
        research_text=research_text,
        snapshot_summary=snapshot_summary,
        cost_cap_usd=cap,
        accumulated_cost=researcher_cost,
    )

    total_cost = _accumulate_cost(researcher_cost, rm_cost)
    log.info(
        "harness_session_complete",
        action=decision.action,
        total_cost_usd=str(total_cost.usd),
    )

    return HarnessResult(
        decision=decision,
        research_text=research_text,
        total_cost=total_cost,
        researcher_iterations=iterations,
        model_assignments={
            "researcher": researcher_model,
            "risk_manager": risk_manager_model,
        },
        tools_used=tools_used,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_placeholder_session(config: HarnessConfig) -> dict[str, str | bool]:
    """Legacy placeholder — kept for backward compatibility with Phase 3 tests."""
    return {
        "routine": config.routine,
        "sleeve": config.sleeve,
        "dry_run": config.dry_run,
        "status": "harness_not_started",
    }


def build_snapshot_summary(
    account_equity: Decimal,
    buying_power: Decimal,
    positions: list[dict[str, Any]],
    *,
    sleeve: str = "core",
    core_nav: Decimal = Decimal("900"),
    satellite_nav: Decimal = Decimal("100"),
    kill_switch_ok: bool = True,
    drawdown_halt: bool = False,
    deploy_cap: Decimal | None = None,
) -> str:
    """Build a human-readable snapshot summary for LLM context."""
    lines = [
        f"Sleeve: {sleeve}",
        f"Account equity: ${account_equity}",
        f"Buying power: ${buying_power}",
        f"Core NAV target: ${core_nav}",
        f"Satellite NAV target: ${satellite_nav}",
        f"Kill switch OK: {kill_switch_ok}",
        f"Drawdown halt: {drawdown_halt}",
    ]
    if deploy_cap is not None:
        lines.append(f"Phase deployment cap: ${deploy_cap}")
    lines.append(f"Open positions ({len(positions)}):")
    for pos in positions:
        lines.append(
            f"  {pos.get('symbol', '?')}: {pos.get('qty', '?')} shares, "
            f"${pos.get('market_value_usd', '?')} mkt value"
        )
    if not positions:
        lines.append("  (none)")
    return "\n".join(lines)


def generate_decision_id() -> str:
    """Generate a unique decision ID for journal records."""
    now = utc_now().strftime("%Y-%m-%d")
    return f"dec_{now}_{uuid.uuid4().hex[:8]}"


def _serialise_content(content: list[Any]) -> list[dict[str, Any]]:
    """Convert Anthropic content blocks to JSON-serialisable dicts for message history."""
    result: list[dict[str, Any]] = []
    for block in content:
        if block.type == "text":
            result.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            result.append(
                {
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                }
            )
        else:
            result.append({"type": block.type})
    return result


def _extract_text(content: list[Any]) -> str:
    """Pull the first text block from an Anthropic response."""
    for block in content:
        if block.type == "text":
            return str(block.text)
    return ""


def _extract_text_from_messages(messages: list[dict[str, Any]]) -> str:
    """Extract text from the last assistant message in the conversation."""
    for msg in reversed(messages):
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content", [])
        if isinstance(content, str):
            return content
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                return str(block.get("text", ""))
    return ""
