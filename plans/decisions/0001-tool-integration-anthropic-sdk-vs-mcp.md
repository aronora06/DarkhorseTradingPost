# ADR-0001: Tool Integration — Anthropic SDK Native Tools (defer MCP)

## Status

`accepted` (2026-05-09)

## Context

Alpaca, Perplexity, and several other vendors now ship official MCP (Model Context Protocol) servers. Two integration paths are available:

1. **MCP route** — run vendor MCP servers as subprocesses; have the Anthropic-compatible MCP client connect; tools are discovered and invoked via the protocol.
2. **Native SDK route** — define each tool as a Python function plus an `input_schema`; pass them to `client.messages.create(tools=[...])`; handle `stop_reason: "tool_use"` in our harness.

Both routes are technically supported. The decision affects: harness complexity, debuggability, dependency surface, and latency.

## Decision

**Use the Anthropic Python SDK's native tool-use surface for v1.** All tools are Python functions in `src/darkhorse/tools/` with `input_schema` and `strict: true`. MCP integration is **deferred** until a concrete need arises (e.g., a third-party tool we'd otherwise have to wrap).

## Consequences

### Positive

- Single-process architecture: harness, tools, and risk validation all in one Python process. No subprocess management, no IPC.
- First-class access to Anthropic features: prompt caching, structured outputs, `strict: true` tool schemas — all immediately available, no protocol-layer translation.
- Easier debugging: a tool failure is a Python stack trace, not a protocol error from a subprocess.
- Tool contracts are typed Python (pydantic models). Mypy enforces correctness at edit time.
- Tool implementations can share helpers (the same `httpx.Client` for both Finnhub and SnapTrade, the same retry logic).

### Negative / costs

- We don't get the "free" tooling that comes with vendor-shipped MCP servers — we have to write the wrapper for each tool ourselves.
- If a third-party adds a feature to their MCP server (new endpoints, better error reporting), we don't get it automatically.
- We can't share tools across other Anthropic clients (e.g., Claude Desktop) without re-implementation.

### Neutral

- The MCP protocol is still maturing. Our tool surface is small (~10 tools); the cost of writing wrappers is bounded.
- A future pivot to MCP is mechanical: each Python tool becomes an MCP server endpoint. The harness change is small (swap native tool-use for MCP-aware tool-use).

## Alternatives considered

- **All-MCP (use vendor servers everywhere).** Adds subprocess management, increases latency per tool call (IPC), and locks us into the maturity curve of each vendor's server. Rejected for v1 — defer to a Phase 6+ revisit if MCP becomes the default integration path.
- **Hybrid (Alpaca via MCP, others native).** Briefly considered. Rejected because consistency is better than micro-optimization; we'd debug two layers instead of one.

## Falsification criterion

This decision is wrong if any of the following occur:

- We need to integrate >3 third-party tools with high-quality MCP servers and writing native wrappers is consuming meaningful engineering time (>1 day per tool).
- A vendor's MCP server gains capabilities we'd want and that aren't trivially mirrored in the SDK pattern (e.g., bidirectional streaming, server-side caching).
- The tool surface grows to >25 tools and per-tool wrapper boilerplate becomes the dominant maintenance load.

In any of those cases, file ADR-NNNN to migrate to MCP.

## Linked hypotheses

None directly. This is a foundational architectural choice rather than a research hypothesis. Adoption candidates from the monthly competitive-landscape review may surface MCP-related techniques worth testing.

## Re-check date

2026-11-09 (6 months) — re-evaluate as part of the Phase 6 architecture review.

## References

- `../../RESEARCH/architecture/agentic_harness_patterns.md` (research note that informed this decision)
- `../../RESEARCH/architecture/anthropic_sdk_features.md` (native tool-use mechanics)
- `../initialPlan.md` §3.3 (multi-agent decision flow)
- Anthropic API docs: tool use, structured outputs, prompt caching
