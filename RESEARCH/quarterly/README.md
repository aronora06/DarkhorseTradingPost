# RESEARCH/quarterly/

Quarterly retrospectives. ~5–10 pages each. The middle layer between monthlies (operational) and the annual report (publication-grade).

The quarterly is where research questions get serious treatment. It's where hypotheses move from "open" to "supported" or "falsified" with cited evidence. It's where the reasoning-pattern audit (L4) gets written and read.

See `../../plans/researchCharter.md` "Outputs → Research" for the cadence and what each level does differently.

## File format

`YYYY-Qn.md` (e.g. `2026-Q3.md`), one per quarter, written within two weeks of quarter-end.

```markdown
# Quarterly Retrospective — YYYY-Qn

**Compiled:** YYYY-MM-DD
**Quarter span:** YYYY-MM-DD to YYYY-MM-DD

## Executive summary
One paragraph. The quarter in 5 sentences.

## Hypotheses status
Per-hypothesis update with evidence accumulated:
- H_001 — status, key data points, link to detail.
- H_002 — ...

## Evidence per research question
For each RQ in `../../plans/researchCharter.md` §"Research Questions":
- **RQ1:** measurement, current value, trend.
- **RQ2:** ...
- (Link to underlying data in `memory/` or `RESEARCH/`.)

## Calibration trend
Quarterly view of calibration drift per confidence bucket. Charts may be embedded as static images in this directory.

## Side-by-side experiment results
Any architectural variants tested in paper-shadow this quarter (single-agent vs multi-agent, prompt revisions, model swaps). Results table; recommendation per variant.

## Reasoning-pattern audit
Embed or link the L4 snapshot from `memory/<sleeve>/reasoning_patterns/YYYY-Qn.md`. Comment on any visible style drift.

## Doctrine evolution this quarter
- Doctrine PRs merged: N (list)
- Doctrine PRs rejected: N (list with reasoning)
- `git log doctrine/` digest.

## Cost analysis
- Spend by month, by provider.
- Edge:cost ratio (annualized) — concrete numbers for RQ5.

## Design changes proposed for next quarter
What we want to change going forward, why, and what hypothesis the change tests.

## Risks / red flags
Anything that would warrant pausing the size ramp, reconsidering wind-down, or filing an ADR.
```

## Discipline

- **Hypothesis resolution is binding.** Once a hypothesis is marked supported or falsified in a quarterly, that resolution is final. Future contradicting evidence becomes a new hypothesis, not a revision of the old.
- **Evidence ordering matters.** Per the research charter, live ≥ 60d > paper ≥ 30d > backtest > narration. Don't cite single-week paper runs as if they were live evidence.
- **Charts are optional.** A retrospective with no charts and clear prose is fine. A retrospective with charts and unclear prose is not.
- **The reasoning audit feeds in here.** The quarterly should always reference the latest reasoning-pattern snapshot. If the agent's reasoning style is drifting, the quarterly is the venue for noticing it.
