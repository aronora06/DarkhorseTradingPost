# Agentic Harness Patterns (2026)

**Compiled:** 2026-05-09
**Refresh by:** 2026-11-09 (6 months — this layer of the stack moves fast)
**Linked ADRs:** ADR-0008 (agentic harness pattern), ADR-0001 (tool integration)

## Summary

The agentic-LLM framework landscape consolidated significantly in 2025–2026. As of mid-2026, **LangGraph dominates** with ~34.5M monthly downloads and is the de facto production default for complex agent state machines. **OpenAI Agents SDK**, **CrewAI**, **AutoGen**, **Google ADK**, **Pydantic AI**, and **Mastra** occupy meaningful but smaller shares of the ecosystem.

For Darkhorse, the core question is: does our agent flow benefit from a framework, or does a thin custom harness win on simplicity, control, and Anthropic-feature parity?

The answer for this project is **custom**, but only because the flow is simple, single-provider, and risk-management-heavy. If those constraints relax (multi-provider, persistent multi-turn state, dynamic tool routing), LangGraph becomes the right call.

## Sources reviewed

- AWS Builder Center, "Picking an AI Agent Framework in 2026" (May 2026)
- Data Science Collective, "12 Best AI Agent Frameworks in 2026" (Medium, 2026)
- Openlayer, "10 best AI agent frameworks Feb 2026"
- Firecrawl, "The Best Open Source Frameworks For Building AI Agents in 2026"
- Anthropic Claude API docs (`platform.claude.com/docs`) — prompt caching + structured outputs
- TradingAgents paper + repo (referenced from `plans/initialPlan.md` §3.3)

## Key findings

### 1. The framework spectrum

Frameworks differ along three axes that matter for Darkhorse:

| Framework | State model | Multi-provider | Anthropic feature parity | Operational weight |
|---|---|---|---|---|
| **LangGraph** | Explicit state graph (nodes + edges) | Strong | Good but lags Anthropic SDK | Medium-high |
| **OpenAI Agents SDK** | Implicit (tool-loop) | OpenAI-first | None | Low |
| **CrewAI** | Role-based crews | Provider-agnostic | Lags | Medium |
| **AutoGen** | Conversation-based | Strong | Lags | Medium-high |
| **Pydantic AI** | Type-safe function calls | Strong | Catching up | Low |
| **Custom (Anthropic SDK)** | Whatever you write | Single-provider | Native, immediate | Whatever you make it |

For multi-step debate flows with persistent state across turns, LangGraph is genuinely useful — its state graph makes the flow legible, and the checkpointing primitives are good. For one-shot routines that wake up, decide, and exit (Darkhorse's pattern), the state machine is overhead.

### 2. Anthropic features lag in frameworks

The 1-hour prompt cache (released late 2025) and the structured-outputs beta (`output_config.format: json` and `strict: true`) are **first-class on the Anthropic SDK** but reach LangGraph and similar frameworks weeks-to-months later, sometimes via opaque adapter layers that don't expose all knobs.

For Darkhorse, where:
- Prompt caching is a 60–90% cost lever (per Anthropic's docs and the AI Magicx 2026 piece) — not a nice-to-have
- Structured outputs are how `validate_order` gets a guaranteed-valid decision JSON

…native SDK use is materially safer than going through a framework adapter.

### 3. Multi-agent debate as a pattern (TradingAgents)

The TradingAgents paper popularized the researcher → bull/bear → risk-manager debate flow. Empirically (per the paper) it produces lower max-drawdown vs single-agent baselines. The pattern itself is implementation-agnostic — it does **not** require LangGraph. It can be implemented as:

```python
async def routine() -> Decision:
    research = await researcher(state)
    bull, bear = await asyncio.gather(
        bull_analyst(research),
        bear_analyst(research),
    )
    return await risk_manager(research, bull, bear)
```

That is the entire orchestration. Adding LangGraph here adds nodes, edges, a state schema, and a runtime — for a flow that is one function with `gather`.

### 4. When frameworks earn their cost

LangGraph (or a peer) starts paying for itself when:

- Flows branch dynamically based on intermediate results
- Long-running agent loops with persistent state across hours/days
- Human-in-the-loop interrupts that require checkpointing
- Multi-provider failover at the orchestration layer
- Many (>10) tools with dynamic routing
- The team is large enough that a shared abstraction beats per-developer custom code

Darkhorse hits **none** of these in v1. We have 4 fixed roles, 5 fixed routines, single provider (Anthropic), ~10 tools with deterministic routing, and one developer.

### 5. Failure-mode considerations

Production agent post-mortems (Apollo, multiple Anthropic-published analyses) consistently identify:

- **Silent prompt-cache misses** as a top cost surprise. Custom code can log cache_creation_input_tokens vs cache_read_input_tokens directly; framework adapters often hide this.
- **Tool-call argument hallucination** as a top failure mode. Strict schema validation at the call boundary catches this; frameworks vary in how strict their tool layer is.
- **Multi-turn context bloat** when state isn't actively pruned. Routines that wake-decide-exit avoid this entirely.

Custom code with explicit observability lets us see and address all three. A framework adds an extra debugging layer between us and the failure.

## Implications for Darkhorse

- **Build a custom thin harness** in `src/harness.py` — likely <500 lines.
- **Use the Anthropic Python SDK directly** for `messages.create`, structured outputs, and prompt caching.
- **Implement multi-agent debate as plain Python** (asyncio.gather for parallel sub-agents, sequential for researcher → debate → risk-manager).
- **Keep tools as Python functions** registered with the SDK's `tools=[]` parameter; defer MCP integration.
- **Instrument cache hit-rate per call** — log `usage.cache_creation_input_tokens` and `usage.cache_read_input_tokens` to cost telemetry.
- **Re-evaluate annually.** The framework landscape will keep moving; if our flow grows in complexity, LangGraph becomes a real option.

## Open questions

- **Pydantic AI as a middle ground?** It's lighter than LangGraph, type-safe, and less opaque. Worth a 1-day spike if custom harness becomes painful.
- **Anthropic Skills / Agent Builder primitives.** As Anthropic ships higher-level orchestration primitives (Claude Code routines, Agent SDK, etc.), some of the harness logic may move down into the platform. Track this in the monthly competitive-landscape review.
- **MCP for tool integration.** Alpaca ships an official MCP server. If MCP adoption broadens, we revisit (see ADR-0001).

## Reading list (Phase 2 deep-dives)

- TradingAgents paper — deeper read for `multi_agent_debate.md`
- Anthropic prompt-caching docs (saved at `agent-tools/af4d0f7a...txt` from this research session) — pull into `prompt_caching.md`
- Anthropic structured-outputs docs (saved at `agent-tools/bef2b693...txt`) — pull into `structured_outputs.md`
- 3+ public agent post-mortems — pull into `agent_failure_modes.md`
