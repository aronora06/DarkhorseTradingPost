# ADR-NNNN: Title of the decision

> Copy this file to `NNNN-short-kebab-title.md` (e.g. `0001-alpaca-mcp-vs-wrapper.md`) and fill it in. Use the next unused number — the index is monotonic and gaps are not reused. ADR numbers, once assigned, are permanent even if the ADR is later superseded.

## Status

One of: `proposed | accepted | superseded by ADR-NNNN | deprecated | rejected`

When superseding, link both ways: this ADR points to its successor; the successor points back here.

## Context

What is the problem we're solving? What constraints apply? What forces are at play (cost, capability, complexity, security, time)? Cite specific sections of the steering docs (`initialPlan.md`, `riskMitigation.md`, etc.) that frame the problem.

Keep this section honest about uncertainty. If the decision is provisional because we don't yet have data, say so.

## Decision

The chosen option, stated as a single declarative sentence at the top, then explained.

If the decision implies code changes, name the modules involved. If it implies doctrine changes, name the doctrine files involved.

## Consequences

### Positive

- What this gives us.

### Negative / costs

- What this costs us. Be specific about dollars, time, complexity, lock-in.

### Neutral

- What this changes that isn't obviously better or worse, but is worth noting for future readers.

## Alternatives considered

For each non-trivial alternative:

- **Option name** — one-paragraph description, why we didn't choose it.

A decision without considered alternatives is not a decision; it's a default.

## Falsification criterion

> **What would have to be true for this decision to be wrong?**

This is the single most important section. Every architectural decision in this project is provisional — the project will run for at least a year, and we should know in advance what evidence would invalidate the choice we're making today.

Examples:
- "If cache hit rate stays below 60% for two consecutive weeks despite tuning, the tiered+cached strategy is wrong."
- "If `validate_order` rejects ≥ 5% of agent-emitted orders due to rules the agent could legitimately follow, the rules are too strict."
- "If we hit the systemd timer's reliability ceiling more than once a quarter, we should reconsider Claude Code routines."

If you can't write a falsification criterion, the decision may not be testable, and the ADR should be rewritten until it is.

## Linked hypotheses (optional)

If this decision tests a research hypothesis from `researchCharter.md` or `RESEARCH/hypotheses/`, link it here:

- `RESEARCH/hypotheses/H_NNN.md` — short description of the link.

A doctrine or architecture change that *should* be testing a hypothesis but isn't is treated as drift, not learning.

## Re-check date

`YYYY-MM-DD` — the date by which we will re-evaluate this decision against evidence accumulated. For most ADRs this is a quarter or two out. For decisions with long feedback loops (model strategy, hosting), it may be a year.

## References

- Source papers, blog posts, prior art that informed the decision.
- Internal docs (always link by relative path): `../initialPlan.md`, `../riskMitigation.md`, etc.
