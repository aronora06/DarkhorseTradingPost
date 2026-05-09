# RESEARCH/hypotheses/

One file per registered hypothesis. The hypothesis registry is what separates *learning* from *drift*: every doctrine change, prompt revision, or architectural swap is supposed to test something specific, and the something it tests lives here.

If a doctrine PR doesn't reference a hypothesis, that's a flag for review — it may be undisciplined evolution rather than learning.

## File format

See `../../plans/dataSchema.md` §8 for the canonical schema. In short:

```markdown
---
hypothesis_id: H_NNN
title: Concise one-line statement of the claim
status: open | supported | falsified | abandoned | superseded
opened: YYYY-MM-DD
research_question: RQ-N (link to charter)
falsification_criterion: |
  Specific, measurable evidence that would prove this hypothesis wrong.
  Bad: "The system performs poorly."
  Good: "Side-by-side paper shadow shows single-agent max DD ≤ multi-agent max DD AND single-agent Sharpe ≥ multi-agent Sharpe over ≥ 60 trading days."
related_decisions: []
related_lessons: []
re_check_date: YYYY-MM-DD
---

## H_NNN — <title>

[Long-form discussion: motivation, prior work, expected effect size, why this is worth testing.]

## Evidence accumulated

(Updated as data comes in. Don't rewrite history; append.)

## Resolution

(Filled in when status moves from `open` to terminal: supported / falsified / abandoned. Cite the data.)
```

## Naming

- **IDs are monotonic.** `H_001`, `H_002`, …. Once assigned, never reused, even if the hypothesis is abandoned.
- **Filename matches ID:** `H_005.md`.

## Initial hypotheses (from researchCharter.md)

These should be filed in Phase 1 from the research charter's RQs:

- **H1** — multi-agent harness produces non-negative Sharpe vs SPY (RQ1)
- **H2** — calibration drifts toward overconfidence without intervention (RQ2)
- **H3** — distilled+sunset lessons outperform raw-journal context (RQ3)
- **H4** — recency bias dominates large-loss causal share (RQ4)
- **H5** — tiered+cached strategy yields edge:cost ≥ 5:1 (RQ5)
- **H6** — multi-agent debate beats single-agent on max DD with equal-or-better Sharpe (RQ6)

Plus any architectural hypotheses that emerge from monthly competitive-landscape reviews.

## Status discipline

- **Open** is the default. Most hypotheses live here for months.
- **Supported / falsified** are terminal. Once moved here, the resolution is final and immutable; a later finding contradicting it becomes a new hypothesis (with a `superseded_by` link in the old).
- **Abandoned** means we stopped testing without resolution — usually because the test became impossible (e.g., the relevant feature was removed). Document why.
- **Superseded** means a later, refined hypothesis replaced this one. Link both directions.
