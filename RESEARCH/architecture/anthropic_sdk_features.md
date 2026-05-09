# Anthropic SDK Features — Caching, Structured Outputs, Tools (2026)

**Compiled:** 2026-05-09
**Refresh by:** 2026-08-09 (3 months — Anthropic features ship fast; check at end of each quarter)
**Linked ADRs:** ADR-0001 (tool integration), ADR-0002 (tiered model strategy), ADR-0008 (agentic harness)

## Summary

The Anthropic Python SDK in 2026 supports three features that are load-bearing for Darkhorse:

1. **Prompt caching** — both 5-minute and 1-hour TTL, costs are 1.25x / 2x for write and 0.10x for read. The 1-hour cache is the right SKU for stable doctrine + journal context.
2. **Structured outputs** — `output_config.format` for JSON mode and `strict: true` for tool schemas. GA on Opus 4.7, Sonnet 4.6/4.5, Haiku 4.5.
3. **Tool use** — native `tools=[]` parameter with type definitions. Full agentic loop is `client.messages.create` with tools and `stop_reason: "tool_use"` handling.

These three features collectively enable a multi-agent harness in plain Python with no framework dependency, and they are the primary reason Darkhorse uses the SDK directly rather than going through LangGraph or another abstraction layer.

## Sources reviewed

- Anthropic Claude API docs — Prompt caching (`platform.claude.com/docs/en/build-with-claude/prompt-caching`)
- Anthropic Claude API docs — Structured outputs (`platform.claude.com/docs/en/build-with-claude/structured-outputs`)
- AI Magicx, "Prompt Caching for Claude: Cut Your API Bill 60% in Production" (2026)
- Anthropic SDK Python source (`anthropic` PyPI package)

## Key findings

### 1. Prompt caching mechanics

Cache control is set per content block via `cache_control={"type": "ephemeral"}`. The TTL is configurable:

- **5-minute cache:** 1.25x write cost, 0.1x read cost. TTL refreshes on every cache hit.
- **1-hour cache:** 2x write cost, 0.1x read cost. TTL refreshes on every cache hit.

For Darkhorse, the 1-hour cache is right because:
- Routines fire 5 times/day across ~10 hours; each routine reads the cache within a window where it's still warm.
- Doctrine + last-30-day-journal context (~25K tokens) writes once per hour at 2x ($10/MTok at Opus rates), reads ~5x within that hour at 0.1x ($0.50/MTok). Net cost vs no-cache: ~73% reduction.

What we cache (per `riskMitigation.md` §2.4):
- All doctrine files (`doctrine/*.md`)
- Last-30-days journal compressed summary
- Tool definitions
- Universe + S&P 500 constituents

What we don't cache:
- Current positions (read fresh each routine)
- News results (per-routine)
- Live quotes (per-routine)
- The user message (per-routine)

Critical observability: log `usage.cache_creation_input_tokens` and `usage.cache_read_input_tokens` on every call. If cache_read_input_tokens trends to zero, the cache is missing — investigate within 24 hours.

### 2. Structured outputs — two surfaces

The structured-outputs feature has two distinct modes:

**a) JSON output mode** via `output_config.format`:
```python
response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=2048,
    output_config={
        "format": {
            "type": "json",
            "schema": Decision.model_json_schema(),
        }
    },
    system=...,
    messages=...,
)
```
The model emits JSON valid against the supplied JSON Schema. Decode with `Decision.model_validate_json(response.content[0].text)`.

For Darkhorse: this is how the risk-manager produces the Decision JSON the harness then runs through `validate_order`. The model literally cannot emit invalid `side` (must be in enum), invalid `qty` type, etc. — the schema enforces it.

**b) Strict tool use** via `strict: true` per tool:
```python
tools = [
    {
        "name": "submit_order",
        "description": "Submit an order to Alpaca after validate_order passes.",
        "input_schema": SubmitOrderInput.model_json_schema(),
        "strict": True,
    },
]
```
With `strict: true`, the model's tool-call arguments are guaranteed to match the input schema. No more "the model called the tool but with `qty: '5 shares'` instead of `qty: 5`."

For Darkhorse: every tool definition uses `strict: true`. This is non-negotiable; it eliminates a whole class of hallucination bugs.

### 3. Model availability matrix

Confirmed GA as of mid-2026:

| Feature | Opus 4.7 | Sonnet 4.6 | Sonnet 4.5 | Haiku 4.5 |
|---|---|---|---|---|
| Prompt caching (5min + 1h) | ✓ | ✓ | ✓ | ✓ |
| Structured outputs (JSON mode) | ✓ | ✓ | ✓ | ✓ |
| Strict tool use | ✓ | ✓ | ✓ | ✓ |
| Beta header required | No | No | No | No |

All features have moved from beta to GA; no `anthropic-beta` header required as of mid-2026. (Verify quarterly — beta-to-GA transitions are fast but Anthropic does occasionally introduce new betas that we'd want.)

### 4. Tool use loop pattern

Standard agentic loop in the SDK:

```python
async def tool_loop(client, system, messages, tools, max_iter=10):
    for _ in range(max_iter):
        resp = await client.messages.create(
            model="claude-opus-4-7",
            max_tokens=4096,
            system=system,
            messages=messages,
            tools=tools,
        )
        messages.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason == "end_turn":
            return resp
        if resp.stop_reason == "tool_use":
            tool_results = await execute_tools(resp.content)
            messages.append({"role": "user", "content": tool_results})
            continue
        raise RuntimeError(f"Unexpected stop_reason: {resp.stop_reason}")
    raise RuntimeError("Exceeded max tool-use iterations")
```

This is the entirety of "agentic loop" we need. ~30 lines of Python. The harness wraps this with cost telemetry, idempotency, and the multi-agent debate orchestration.

### 5. Multi-agent debate as concurrent SDK calls

`asyncio.gather` over independent `client.messages.create` calls gives us parallel sub-agents at no SDK-level cost beyond rate limits. Anthropic rate limits at the org level; for our routine cadence (5/day, 4 concurrent sub-agents per routine, ~30 calls/day) we're 2 orders of magnitude under any tier limit.

```python
research = await researcher_call(state)
bull, bear = await asyncio.gather(
    bull_call(research),
    bear_call(research),
)
decision = await risk_manager_call(research, bull, bear)
```

### 6. Cost accounting endpoints

The response includes `usage`:
```python
{
    "input_tokens": 28543,
    "cache_creation_input_tokens": 0,         # 0 if cache hit
    "cache_read_input_tokens": 21034,         # >0 if cache hit
    "output_tokens": 4120,
}
```

Per-routine cost calculation:
```python
def usd_cost(usage, model_prices):
    return (
        usage.cache_creation_input_tokens * model_prices.cache_write
        + usage.cache_read_input_tokens * model_prices.cache_read
        + usage.input_tokens * model_prices.input
        + usage.output_tokens * model_prices.output
    )
```

Log this per call to `memory/cost/YYYY-MM-DD.jsonl` per the schema in `dataSchema.md` §7.

### 7. Error envelopes

The SDK raises specific exceptions:

- `RateLimitError` — back off and retry (tenacity is the right wrapper)
- `OverloadedError` — system busy; same as rate limit, but with longer backoff
- `APIStatusError` — 5xx; retry with exponential backoff
- `BadRequestError` — schema or context-length issue; fail loud
- `AuthenticationError` — credentials problem; fail loud, no retry

For Darkhorse: wrap calls in `tenacity.AsyncRetrying` with exponential backoff (1s, 3s, 9s) on `RateLimitError`, `OverloadedError`, and 5xx `APIStatusError`. Fail loud on `BadRequestError` and `AuthenticationError` — those are bugs, not transient issues.

## Implications for Darkhorse

Locked harness primitives:
- **Prompt caching:** 1-hour TTL, doctrine + journal-summary + tool definitions in cache. Per-call cache-hit telemetry is mandatory.
- **Structured outputs:** JSON mode for the risk-manager's decision; `strict: true` on every tool definition.
- **Tool loop:** standard SDK pattern, ~30 lines wrapped in retry + observability.
- **Concurrent sub-agents:** `asyncio.gather` for parallel bull/bear.
- **Cost telemetry:** per-call usd cost computed from `usage` and logged to JSONL.
- **Retry policy:** tenacity, 3 attempts with 1/3/9s backoff, on transient errors only.

## Open questions

- **Anthropic's "Skills" / higher-level agent primitives.** Track whether Anthropic ships an Agent SDK that subsumes our harness. If it has cache + structured outputs + tool loop with similar control, consider migration in Phase 6+. Note adoption candidates in the monthly competitive-landscape review.
- **Computer use / Claude Code MCP integration.** Not relevant for Darkhorse v1; we don't need browser automation.
- **Fallback to a second provider.** OpenAI GPT-5.5 is comparable on agentic benchmarks. A "if Anthropic is down" fallback is nice but adds prompt-portability work. Defer; rely on routines failing loud and missing one cycle.
