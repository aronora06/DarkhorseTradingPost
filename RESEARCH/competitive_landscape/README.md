# RESEARCH/competitive_landscape/

Monthly reviews of the agentic-trading and agent-architecture landscape. Output of the `monthly_competitive_review.py` routine (Phase 6+) plus any ad-hoc deep-dives on specific systems we want to understand.

This is the **outside view** on Darkhorse: what is the broader field doing, and what should we steal? Without this, the project risks becoming a beautifully-engineered local optimum.

See `../../plans/learningSystem.md` §5 for the routine specification.

## File format

`YYYY-MM.md` per monthly review. Optional `<slug>.md` files for ad-hoc deep-dives.

```markdown
# Competitive Landscape Review — YYYY-MM

**Compiled:** YYYY-MM-DD
**Routine run:** monthly_competitive_review.py (or "manual" if ad-hoc)
**Cost of this review:** $X.XX

## Scope
What sources were aggregated this month (GitHub, arXiv, HN, Reddit, blogs, vendor updates).

## One-line summaries
- Item 1 — one line.
- Item 2 — one line.
- (Aim for 15–30 lines; this is the inventory.)

## Deep dives (3–5 items)

### <Item title>
**Source:** ...
**Why we deep-read:** ...
**What it claims / does:** ...
**Transferable to Darkhorse:** yes / no / partially — and how.
**Recommendation:** adopt | experiment | monitor | ignore — with reasoning.
**Hypothesis (if adopting):** link to `RESEARCH/hypotheses/H_NNN.md`.

## Adoption candidates summary
Table of adopt / experiment / monitor / ignore decisions for this month, for skim-reading later.

## Open questions for next month
What we'd want to revisit or follow up on.
```

## Discipline

- **No adoption without a paper-shadow validation window.** Per the `initialPlan.md` cross-cutting rules, anything we adopt runs in paper-shadow ≥ 2 weeks before live exposure.
- **No adoption without a hypothesis.** If the change isn't testing something specific, it's drift.
- **The "ignore" category is not pejorative.** It means "interesting but not for us at this scale / mandate." Documenting why we don't adopt is as valuable as documenting why we do.
- **Compounding over time.** A reference made in a previous month is fair game to re-cite. Cross-link liberally.

## When the routine doesn't fire

Pre-Phase 6 (before the routine exists), any landscape research lives here as ad-hoc files. Once the routine fires, ad-hoc reviews become rare — they're for between-cycle deep-dives only.
