# RESEARCH/architecture/

Architecture-research notes. Where deeper-than-one-page architectural reading and prototyping lives, separate from `papers/` (which is academic) and `competitive_landscape/` (which is monthly outside-view).

These notes are the load-bearing reading we do *before* filing an ADR. An ADR cites the relevant note here as part of its "References" section.

## When to write a note here

When a Phase 2 architectural decision needs more than a one-paragraph summary to inform it. Phase 2 specifically calls for:

- `multi_agent_debate.md` — TradingAgents repo + paper review
- `structured_outputs.md` — Anthropic structured outputs beta + tiny working example
- `prompt_caching.md` — Anthropic 1h cache, expected hit rates, cost math
- `agent_failure_modes.md` — at least 3 production agent post-mortems

Add notes here when an architectural question warrants the same treatment.

## File format

Free-form, but include at minimum:

```markdown
# <topic>

**Compiled:** YYYY-MM-DD
**Refresh by:** YYYY-MM-DD (default: 6 months — model & API surfaces evolve fast)
**Linked ADRs:** ADR-NNNN, ADR-NNNN

## Summary
2–3 paragraphs. What's the current state of the art on this topic for our use case?

## Sources reviewed
List with links and brief annotation.

## Key findings
Bullets, with citations.

## Implications for Darkhorse
Specific design choices this informs.

## Open questions
What we don't yet know, what we'd test if we had data.

## Code snippets (optional)
Minimal working examples, with provider/version pinned.
```

## Discipline

- **Reviewed at refresh.** API surfaces and best practices change quickly. A note from a year ago may be stale.
- **No ADR without a note (when applicable).** If an ADR's reasoning fits in the ADR itself, fine. If it requires more context, the note lives here.
- **Cite specific commits / versions.** "Anthropic structured outputs beta header `structured-outputs-2025-11-13`" not "the structured outputs beta."
