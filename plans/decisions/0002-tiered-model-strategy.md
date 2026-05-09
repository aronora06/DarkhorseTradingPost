# ADR-0002: Tiered Model Strategy

## Status

`accepted` (2026-05-09)

## Context

At Opus-4.7-everywhere prices, naive daily token spend would be ~$27/month — 2.7% NAV/yr at $1k AUM, roughly the alpha we're hoping to generate. That cost-to-edge ratio is unacceptable. The pricing landscape (per `../riskMitigation.md` §2.1) shows wide variance across model families with comparable agentic capability.

The decision is which model to assign to which agent role, and how to use prompt caching to cut cost without sacrificing capability where it matters.

## Decision

**Three-tier model assignment with 1-hour prompt caching.**

| Tier | Role(s) | Model | Why |
|---|---|---|---|
| Premium | Risk-manager (final decision) | **Claude Opus 4.7** | Highest-stakes call. 87.6% SWE-bench Verified, leads MCP-Atlas tool-use. Cache cuts cost ~88%. |
| Workhorse | Researcher, Bull analyst, Bear analyst | **Claude Sonnet 4.6** | 79.6% SWE-bench Verified, 5x cheaper than Opus, shares Anthropic cache namespace. |
| Cheap | Journal compilation, weekly reflection, ticker normalization, monthly competitive-landscape summary, quarterly reasoning audit | **Claude Haiku 4.5** | $1/$5 per MTok input/output, 4–5× faster than Sonnet. |

**Prompt caching:** Anthropic 1-hour TTL cache, applied to doctrine + last-30-days journal summary + tool definitions. Per `../riskMitigation.md` §2.4, this delivers ~73% cost reduction on input tokens.

**Hard pass:** China-hosted models (DeepSeek, Kimi, Qwen) and self-hosted models. Rationale documented in `../riskMitigation.md` §2.3 and signed off in `../suggestedNextSteps.md` §1.3.

**Optional cheap-for-bulk** (not v1): Gemini 3.1 Flash-Lite for pre-screen / news scan if/when bulk text processing becomes a bottleneck. US-hosted, native search grounding. Defer until profiling shows a need.

## Consequences

### Positive

- Per-routine cost ~$0.018, daily ~$0.09, monthly ~$2.70 — 0.27% NAV/yr (10x improvement vs all-Opus).
- Single-vendor (Anthropic) means cache namespace is shared across roles; sub-agents share the cached doctrine context with the risk-manager.
- Models share architecture and prompt conventions; doctrine and prompts work across the tier without per-model rewriting.
- Capability matched to stakes: the final go/no-go uses the smartest model; sub-agent debate uses the model with the best cost/capability ratio; bookkeeping uses the cheapest.

### Negative / costs

- Single-vendor dependency. If Anthropic has a multi-day outage, every model in the stack is affected.
- Sonnet is "good enough" for sub-agent debate but is empirically a step below Opus on subtle reasoning. Calibration analysis must catch any systematic Sonnet-driven bias.
- Haiku for the weekly review means lessons are distilled by a cheap model. Aaron's review is the corrective; if Haiku-distilled lessons consistently miss the point, escalate to Sonnet for that role.

### Neutral

- The "Sonnet 4.7" upgrade question (when it ships) becomes a quarterly review item, not a continuous concern.

## Alternatives considered

- **All-Opus.** Maximum capability, 10x the cost. Rejected on cost-to-edge grounds.
- **All-Sonnet.** ~3x cheaper than the tiered strategy at the cost of dropping Opus on the most consequential call. Rejected — the risk-manager is the place we explicitly want the best model.
- **GPT-5.5 for the risk-manager.** Comparable agentic capability per benchmarks (82.7% SWE-bench), but introduces a second provider with its own SDK, prompt conventions, and rate limits. Adds operational complexity for marginal capability difference. Defer.
- **Open-weights models via DeepInfra/Together.** Worth tracking but the per-MTok pricing is not actually cheaper than Haiku at our scale, and the tooling lags. Re-evaluate annually.

## Falsification criterion

This decision is wrong if:

- Cache hit rate stays below 60% for 2 consecutive weeks despite tuning. (Expected: 65–75%.)
- Edge:cost ratio (annualized realized edge / annual compute spend) is < 5:1 over a 6-month window. (RQ5 / H5.)
- A specific Sonnet-driven failure pattern appears in calibration analysis (e.g., over-bullish bias in sub-agents that Opus-as-risk-manager fails to correct).
- A new model release shifts the price/capability frontier materially (e.g., Sonnet 4.7 reaches Opus 4.7 capability at half the price).

## Linked hypotheses

- `../../RESEARCH/hypotheses/H_005.md` — Tiered+cached strategy yields edge:cost ≥ 5:1 (RQ5).

## Re-check date

2026-08-09 (3 months) — quarterly model-version review, per `../devPhaseChecklist.md` Phase 10 recurring rituals.

## References

- `../riskMitigation.md` §2 (full pricing landscape and rationale)
- `../../RESEARCH/architecture/anthropic_sdk_features.md` (caching mechanics)
- Anthropic Claude Opus 4.7 / Sonnet 4.6 / Haiku 4.5 model cards
