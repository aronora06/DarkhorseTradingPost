# ADR-0008: Agentic Harness Pattern — Custom Thin Wrapper Around Anthropic SDK

## Status

`accepted` (2026-05-09)

## Context

The agentic-LLM framework landscape has consolidated. As of mid-2026, **LangGraph** is the de facto production default (~34.5M monthly downloads), with OpenAI Agents SDK, CrewAI, AutoGen, Pydantic AI, Mastra, and Google ADK as significant alternatives.

For Darkhorse, the question is binary: do we build on a framework or write a custom thin harness around the Anthropic Python SDK?

This decision is load-bearing — it shapes how every routine is implemented, how observability and idempotency are wired, and what we owe a future-Aaron coming back to the code in a year.

## Decision

**Custom thin harness, no framework.** All multi-agent orchestration is plain Python (asyncio + Anthropic SDK). The harness lives in `src/darkhorse/harness.py` and is expected to stay <500 lines.

Specifically:
- `client.messages.create` for every LLM call
- `asyncio.gather` for parallel sub-agents
- Native `tools=[...]` for tool integration with `strict: true` schemas
- `output_config.format` for structured-output decision JSON
- `cache_control={"type": "ephemeral"}` with 1-hour TTL for stable context
- `tenacity.AsyncRetrying` for transient-error retries
- Per-call cost telemetry from `usage.cache_*_tokens` and `usage.{input,output}_tokens`
- Per-call structured logging via `structlog` with routine/sleeve/role context

## Consequences

### Positive

- **Direct access to Anthropic features.** Prompt caching, structured outputs, and `strict: true` tool schemas — all first-class on the SDK, all available immediately, with full control over their parameters.
- **Debuggability.** A harness bug is a Python stack trace in our code, not a framework's internals.
- **Doctrine-aligned.** "Risk lives in code, not prompts" (`../initialPlan.md` §2.1). A custom harness keeps `validate_order` enforcement in deterministic Python, no framework abstraction in between.
- **Cost.** No framework overhead per call. The harness footprint is the SDK plus tenacity plus structlog — nothing else.
- **Future-Aaron friendly.** ~500 lines of harness code is a single afternoon of reading. LangGraph's surface area is much larger.

### Negative / costs

- We don't get framework-level features for free: distributed tracing integration, persistent state checkpointing, dynamic flow branching, multi-provider failover. We have to design and implement anything we want.
- We ship our own observability primitives. Structured logs + cost telemetry + JSONL journal cover the v1 surface; if we need distributed tracing later (we won't, single-process) we'd add OpenTelemetry by hand.
- Migrating to a framework later is non-trivial. The cost of "build custom now, migrate later" is real if the project grows.

### Neutral

- The flow we need is simple enough that the framework's value-add is marginal. Frameworks earn their cost when flows are complex. We accept that calculus may shift.

## Alternatives considered

### LangGraph

The dominant 2026 framework. Excellent for explicit state-graph orchestration, multi-step branching, persistent state, human-in-the-loop checkpoints.

Why not for v1: our flow is researcher → parallel(bull, bear) → risk-manager. Three nodes, deterministic edges, no checkpointing needed. The state graph adds cognitive overhead and a runtime dependency for a flow that is one async function with `gather`.

When to revisit: if we add dynamic flow branching, multi-turn agents that hold state across hours, or grow to >5 agent roles. Track in monthly competitive-landscape reviews.

### OpenAI Agents SDK

OpenAI-first. Rejected: we're Anthropic-first per `0002-tiered-model-strategy.md`.

### CrewAI

Role-based crews abstraction. Rejected: adds vocabulary ("crew", "task", "agent") for what we already express clearly in Python functions. Provider-agnostic in theory but Anthropic feature parity lags.

### AutoGen

Microsoft. Conversation-based abstraction. Rejected: heavier than we need; conversation-graph metaphor doesn't match our wake-decide-exit routine pattern.

### Pydantic AI

Lighter than LangGraph, type-safe, less opaque. Genuinely interesting; the gap between Pydantic AI and a custom harness is small. Rejected for v1 because the gap goes the wrong way — we still pay framework abstraction cost without gaining capabilities our flow uses. **Worth a 1-day spike if custom harness becomes painful** (>500 lines, repeated boilerplate, opacity).

### Anthropic's own future Agent SDK

Anthropic has shipped Claude Code routines and is actively expanding agentic primitives. Likely there will be a higher-level Anthropic Agent SDK by end of 2026. **Track in the monthly competitive-landscape review.** If/when it ships with first-class caching, structured outputs, tool loops, and observability, evaluate as a primary harness.

## Falsification criterion

This decision is wrong if any of:

- The harness exceeds 1000 lines and the bulk is orchestration boilerplate (not business logic).
- We hit a flow shape (dynamic branching, persistent multi-turn state) that's awkward to express in plain async Python.
- A bug in the harness takes >1 day of investigation to find — indicates the abstraction is missing.
- Multiple agent roles share infrastructure that we re-implement per role rather than factoring.
- Anthropic ships a first-party agent SDK that subsumes our harness with similar control.

In any of those cases, file ADR-NNNN to migrate to LangGraph, Pydantic AI, or whatever Anthropic ships.

## Linked hypotheses

- `../../RESEARCH/hypotheses/H_006.md` — Multi-agent debate beats single-agent on max DD with equal-or-better Sharpe (RQ6). The harness is the substrate that supports testing this hypothesis; the hypothesis is about the *flow*, not the framework.

## Re-check date

2026-08-09 (3 months) — quarterly architecture review. Hard re-check at every monthly competitive-landscape review.

## References

- `../../RESEARCH/architecture/agentic_harness_patterns.md` (research note with framework comparison)
- `../../RESEARCH/architecture/anthropic_sdk_features.md` (SDK features that make custom viable)
- `../initialPlan.md` §3.3 (multi-agent decision flow)
- `../riskMitigation.md` §2.4 (prompt caching strategy)
- LangGraph docs (alternative considered)
- Pydantic AI docs (alternative considered)
