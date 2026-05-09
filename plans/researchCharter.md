# Darkhorse Trading Outpost — Research Charter

## Purpose

Darkhorse Trading Outpost is, primarily, **Aaron Parker's personal trading assistant**. It is also, deliberately, a **research vehicle** for understanding how agentic LLM systems behave when given a real (small) capital allocation, real adversarial inputs, real costs, and a long observation window.

Both purposes are real, but they are not symmetric:

- The trading purpose **constrains** the research — we don't run experiments that risk the capital irresponsibly.
- The research purpose **shapes** the trading — we build for observability, learnability, and reproducibility even when a simpler design would suffice for trading alone.

This charter exists so that, six months in, when we're tempted to skip a journal entry or merge a doctrine change without a falsification criterion, we have a written reminder of what we're actually trying to learn.

## Principal Investigator

**Aaron Parker** (aaron@aulendur.com). Sole decision-maker on doctrine, mandate, capital, and publication. The agent has no authority over its own design.

## Time Horizon

**Year 1 (May 2026 – May 2027):** primary research window. Quarterly retrospectives. Annual report at the one-year mark with a continue/wind-down decision.

**Beyond year 1:** continuation is not assumed; it is a decision the year-1 retrospective makes.

## Research Questions

These are the questions Darkhorse exists to help answer. Each is paired with a measurable target.

### RQ1 — Can a multi-agent LLM harness produce risk-adjusted edge for a retail account?

- **Measure:** rolling 6-month Sharpe vs SPY, net of all costs (compute, spread, slippage, taxes).
- **Success:** Sharpe vs SPY ≥ 0 over the 6-month rolling window for ≥ 80% of measurement points in year 1.
- **Failure:** Sharpe vs SPY < 0 sustained → wind-down per `riskMitigation.md` §6.

### RQ2 — How does calibration drift over time without intervention?

- **Measure:** confidence-stratified hit rate (≥0.7 confidence cohort win rate; ≥0.85 cohort win rate). Tracked weekly, smoothed over 4-week windows.
- **Hypothesis (H2):** without active doctrine intervention, calibration drifts toward overconfidence as the agent accumulates "evidence" from past wins.
- **Falsification:** calibration error (predicted - realized) stays within ±5pp over a quarter without doctrine change → H2 falsified.

### RQ3 — What memory architectures actually produce learning vs accumulation?

- **Measure:** outcome quality on cohorts of decisions made *after* a relevant lesson was added to memory, vs cohorts before.
- **Hypothesis (H3):** distilled, decayed, sunset-able lessons produce measurable improvement; raw appended journal context does not.
- **Falsification:** post-lesson cohorts show no statistically distinguishable improvement vs pre-lesson cohorts on matched setups.

### RQ4 — Where do recency bias, look-ahead bias, and adversarial inputs cause the largest realized losses?

- **Measure:** post-mortem categorization of every losing trade > 1% of sleeve NAV. Tag with primary causal factor.
- **Hypothesis (H4):** recency bias on news will dominate; adversarial inputs will be near-zero (because of guardrails); look-ahead bias will be invisible in live (only visible in backtests).
- **Falsification:** any other factor exceeds 30% of large-loss share.

### RQ5 — What is the cost-to-edge ratio at different model tiers and caching strategies?

- **Measure:** monthly compute spend / annualized realized edge (in dollars).
- **Hypothesis (H5):** the tiered Opus/Sonnet/Haiku + 1h cache strategy produces edge:cost ≥ 5:1; all-Opus uncached is < 1:1.
- **Falsification:** measured ratios contradict this.

### RQ6 — Does multi-agent debate (bull/bear/risk-manager) outperform a single-agent baseline on the same inputs?

- **Measure:** parallel paper accounts running single-agent vs multi-agent, identical universe, identical schedule, for ≥ 60 trading days.
- **Hypothesis (H6):** multi-agent produces lower max DD and equal-or-better Sharpe.
- **Falsification:** single-agent matches or beats on both metrics → reconsider the architecture.

### RQ7 — What happens to agent reasoning style over a long observation window?

- **Measure:** quarterly read of N=50 randomly sampled journal entries; categorize reasoning patterns; compare quarter-over-quarter.
- This is qualitative, exploratory. No falsification criterion. Output is a quarterly research note.

## Hypotheses Registry

All hypotheses are tracked in `RESEARCH/hypotheses/` — one file per hypothesis, with status (open / falsified / supported / abandoned), evidence accumulated, and a re-check date.

Doctrine changes that test a hypothesis must reference it explicitly. A doctrine change without a referenced hypothesis is treated as drift, not learning.

## Methodology

### Observational

- Every routine writes a structured JSONL journal entry with full reasoning context.
- Calibration log accumulates predicted-confidence-vs-realized-outcome pairs.
- Cost/spend telemetry logged per provider per routine.

### Quasi-experimental

- Side-by-side paper accounts for any architectural change before it lands in live (single-agent vs multi-agent, model swap, prompt revision).
- Doctrine changes go live in paper for ≥ 2 weeks before live exposure.

### Adversarial

- Weekly adversarial test suite: homoglyph tickers, prompt-injected news, fabricated headlines.
- New attack vectors added as they appear in literature or red-team observations.

### Backtesting (with discipline)

- Post-training-cutoff data only.
- Walk-forward, no peeking.
- Anonymized backtests for in-cutoff periods (replace tickers and dates).
- Backtest results are inputs to hypotheses, not standalone publishable findings.

## What Counts as Evidence

Decisions about doctrine, architecture, and continuation are weighted by evidence type:

| Evidence | Weight |
|---|---|
| Live-account realized P&L over ≥ 60 trading days | Highest |
| Side-by-side paper comparison ≥ 30 trading days | High |
| Out-of-sample backtest, FINSABER discipline | Medium |
| In-sample backtest | Low (mostly null) |
| Single-week paper run | Suggestive only |
| LLM-narrated reasoning ("I think this works") | None — must be backed by data |

## Outputs

### Operational

- Daily Discord recap (audience: Aaron, ~2 min read)
- Weekly review report in repo (audience: Aaron + future-Aaron)

### Research — three retrospective cadences

The retrospective rhythm is **monthly → quarterly → annual**, with each cadence doing a different job. Lower cadences feed higher ones — the annual report draws on 12 monthlies and 4 quarterlies, not on raw journal data.

- **Monthly retrospective** in `RESEARCH/monthly/YYYY-MM.md` (~2 pages):
  - This month's calibration drift summary
  - Cost analysis vs cap; cache hit rates
  - Lesson churn: proposed / merged / falsified counts; any promoted to doctrine
  - Anti-pattern additions
  - Competitive landscape review summary (1-paragraph digest of the monthly web review; full review lives in `RESEARCH/competitive_landscape/`)
  - Notable trades and what we learned from them
  - One open question or hypothesis worth attention next month
- **Quarterly retrospective** in `RESEARCH/quarterly/YYYY-Qn.md` (~5–10 pages):
  - Hypotheses status across the quarter (open / supported / falsified / abandoned)
  - Evidence accumulated per RQ
  - Calibration trend over the quarter
  - Side-by-side experiment results (architectural variants tested)
  - Reasoning-pattern snapshot (the quarterly L4 audit feeds directly here)
  - Design changes proposed for next quarter
- **Annual report** in `RESEARCH/annual/year-N.md` (publication-quality):
  - Synthesis of all 12 monthlies and 4 quarterlies
  - Continue / wind-down decision per `riskMitigation.md` §6
  - **Designed from day 1 to be publication-ready** (see Publication Readiness below)

### Publication Readiness (year-1 target)

Aaron's stated goal: at the year-1 mark, we want the data and the writeup to support a credible research publication on this experiment. Achieving that requires *designing for it from the first commit*, not retrofitting at the end.

**What "credible research publication" means here:** an arXiv preprint, optionally a workshop submission (FinNLP, ICLR/NeurIPS workshops on agents, ACL workshops on financial NLP, KDD finance track). It is not the *Journal of Finance*. It is a methodology + observations paper on what one disciplined personal-LLM-trading experiment looked like over a year.

**Data required by month 12 to support such a publication:**

| Artifact | How collected | Purpose in paper |
|---|---|---|
| Full episodic journal (every decision with reasoning trace) | Continuous, from Phase 4 onward | Methodology reproducibility; sample reasoning |
| Calibration log over the full year | Continuous | Calibration-drift analysis; RQ2 |
| Hypothesis registry with falsification outcomes | Continuous, per `dataSchema.md` §8 | Honest reporting of what we tested vs concluded |
| Side-by-side comparison data (single-agent vs multi-agent paper shadow) | Continuous from Phase 5 | RQ6 result with statistical power |
| Monthly competitive landscape reviews | Monthly | Related-work section; what we adopted vs ignored |
| Quarterly reasoning-pattern snapshots | Quarterly | Qualitative finding on style evolution; RQ7 |
| Cost telemetry per routine over the year | Continuous | RQ5 result with concrete numbers |
| Adversarial test outcomes (weekly) | Weekly | Robustness section |
| Audit log (every halt, every kill-switch toggle, every doctrine merge) | Continuous | Honest reporting of human-in-loop interventions |
| Wind-down event (if it fired) | If applicable | The negative-result section that makes the paper honest |

**Anonymization plan for any public release:**
- Position sizes expressed as % of sleeve NAV, never $
- Account NAV expressed as multiples of starting NAV, never $
- Tickers retained (the experiment is on real public companies; ticker hallucination claims require real tickers to be credible)
- Aaron's identity: optional disclosure (his call at month 11)

**Operationally:** every artifact above must be produced from day 1 in a format that is publication-anonymizable. We do not retrofit JSON schemas at month 11 to remove dollar amounts.

### Public Releases (decided per quarter, default no during year 1)

- Public writeups *during* year 1 are opt-in per quarter. Default is not to publish — we want a complete dataset, not a running commentary.
- If we publish during year 1: workshop-paper format only, conservative claims, full anonymization.
- If we publish at year-end: arXiv preprint as the primary output. Optional submission to a workshop based on what the data supports.

## Ethical & Practical Boundaries

- **Aaron's own capital only.** No outside money. No "I'm running this for friends." No solicitation.
- **No advice claims.** Outputs are research artifacts and personal-trading logs, not recommendations.
- **No production-grade SLAs.** This is a research system that happens to trade real money. Outages happen; we design to fail safe, not to never fail.
- **Open scientific habits.** If a hypothesis is falsified, it is recorded as falsified, not quietly removed. Negative results are research products.
- **No secrets in research outputs.** Position-level data and account credentials never leave the repo's private space.

## Anti-Goals (what we are NOT doing)

- Building a SaaS / multi-tenant trading product
- Optimizing for high-frequency / sub-second decisions
- Chasing the latest model on day-of-release without a paper window
- Producing trading "signals" for distribution
- Making this a fund or any structure that takes outside capital
- Letting the research framing become an excuse for not enforcing the risk discipline

## Continuation Criteria

At the year-1 mark, Darkhorse continues only if **all** of the following are true:

1. The wind-down rule (`riskMitigation.md` §6) has not fired.
2. At least three of RQ1–RQ6 have meaningful evidence accumulated (supported, falsified, or refined).
3. Aaron actively wants to continue (the boredom-failure-mode mitigation in `riskMitigation.md` R16).
4. Cost-to-edge ratio is sustainable for the next year.

If any are false, the system winds down to SPY-Core + Satellite-sandbox or fully off, and the year-1 report is the final research artifact.
