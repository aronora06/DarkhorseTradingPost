# RESEARCH/annual/

Annual reports. One file: `year-N.md`. Designed from day 1 to be **publication-ready** (per `../../plans/researchCharter.md` "Publication Readiness").

The year-1 annual report is the principal research output of the project. If the year-1 retrospective decides to continue, year-2 follows the same structure but builds on prior findings rather than restarting them.

## What "publication-ready" means

An arXiv preprint, optionally a workshop submission (FinNLP, ICLR/NeurIPS workshops on agents, ACL workshops on financial NLP, KDD finance track). It is not the *Journal of Finance*. It is a methodology + observations paper on what one disciplined personal-LLM-trading experiment looked like over a year.

The annual report should be writable into a paper draft with minimal restructuring. The whole reason `dataSchema.md` was designed up-front is to make this possible.

## File format

```markdown
# Year-N Annual Report — Darkhorse Trading Outpost

**Compiled:** YYYY-MM-DD
**Year span:** YYYY-MM-DD to YYYY-MM-DD
**Status:** draft | review | final
**Anonymization:** percentages-only / full-disclosure / mixed (decided per Aaron's call at month 11)

## Abstract
~250 words. What we built, what we found, the continue / wind-down decision.

## 1. Introduction
- Motivation, scope, what makes this study novel as a methodology demonstration.
- Explicit non-claims (we did not invent a strategy, we did not run a fund, we did not fine-tune anything).

## 2. System design
Synthesized from `plans/initialPlan.md`, `docs/architecture.md`, `plans/learningSystem.md`. ~3–5 pages.

## 3. Research questions and hypotheses
Synthesized from `plans/researchCharter.md` and `RESEARCH/hypotheses/`. Status of each hypothesis at year-end with cited evidence.

## 4. Methodology
- Episodic journal format (cite `dataSchema.md`).
- Calibration tracking.
- Side-by-side comparisons.
- Adversarial testing.
- FINSABER-discipline backtesting.

## 5. Results — quantitative
- Sharpe vs SPY (RQ1) with full equity curve.
- Calibration trajectory (RQ2).
- Cost analysis (RQ5).
- Multi-agent vs single-agent paper-shadow result (RQ6).

## 6. Results — qualitative
- Reasoning-pattern evolution across the four quarterly snapshots (RQ7).
- Notable lessons promoted, falsified, retired.
- Anti-pattern catalog: what attacks the system actually faced vs what we anticipated.

## 7. What we learned about agentic-trading systems at retail scale
The forward-looking section. What would we tell someone considering a similar project?

## 8. Limitations and threats to validity
Honest accounting:
- Single-account N=1.
- Single year, possibly single regime.
- Look-ahead bias, even with FINSABER discipline, cannot be fully eliminated.
- The reasoning audit is performed by another Claude on the same training distribution.

## 9. Continue / wind-down decision
Per `riskMitigation.md` §6 wind-down rule and the charter's continuation criteria. Cite the rolling 6-month Sharpe, hypothesis resolution counts, cost-to-edge ratio.

## 10. Reproducibility
- Repo URL, commit hash of the year-end state.
- `dataSchema.md` reference for journal/calibration formats.
- Anonymization choices.

## Acknowledgments
- Practitioners cited in the dossiers.
- Source papers.
- (Optional) advisors / co-authors.

## References
Bibliography in standard academic format.
```

## Discipline

- **Drafted, not started, at month 11.** The annual report is a *synthesis* of monthlies, quarterlies, and competitive-landscape reviews. If those have been kept current, the annual is written in two weeks, not two months.
- **Anonymization decided once, applied uniformly.** Per the charter, the anonymization plan is finalized at month 11 (Aaron's call); the report is then drafted entirely in the chosen anonymization mode rather than mixing.
- **Negative results lead.** If RQ1 is falsified (Sharpe vs SPY < 0), that goes in the abstract and section 1. The honest negative result is the more interesting paper.
