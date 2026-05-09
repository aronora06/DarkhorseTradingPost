# Can LLM-based Financial Investing Strategies Outperform the Market in Long Run?

**Authors:** Weixian Waylon Li, Hyeonjun Kim, Mihai Cucuringu, Tiejun Ma  
**Venue:** ACM SIGKDD Conference on Knowledge Discovery and Data Mining (KDD), 2026 (Jeju; acceptance noted by authors / community trackers as of late 2025)  
**Year:** 2026 (preprint circulated 2025)  
**Link:** https://arxiv.org/abs/2505.07078 — code: https://github.com/waylonli/FINSABER  
**Read on:** 2026-05-09

## Claim

Most published evaluations of **LLM timing-based investing** are unreliable because they run on **narrow time windows** and **small stock universes**, inflating performance via **survivorship bias** and **data snooping**. The authors propose **FINSABER**, a backtesting framework that stresses these strategies over roughly **two decades** and **100+ symbols**, and report that prior “LLM beats the market” impressions **deteriorate** under that broader evaluation. Regime analysis further suggests LLM timing strategies tend to be **too conservative in bull markets** (trail passive benchmarks) and **too aggressive in bear markets** (heavy losses).

## Evidence

Framework paper + systematic historical backtests (cross-section and horizon explicitly broader than typical LLM-fin papers). Strength: directly targets **evaluation hygiene** rather than a single strategy hype. Caveats: implementation details, exact universe construction, and LLM prompt/version choices determine quantitative headlines — treat numeric claims as **conditional on their experimental stack**, not universal truths.

## What we take from it

- Institutionalizes what `plans/riskMitigation.md` §3 **R1/R15** already assume: **post-cutoff discipline**, **full-universe / delisting awareness**, and **walk-forward skepticism** are non-optional for any LLM investing claim.
- Reinforces Darkhorse’s stance: **live micro-size + cost containment** beats trusting optimistic LLM backtests.
- Informs Phase 7 evaluation design (`plans/devPhaseChecklist.md`): any internal backtest harness should cite FINSABER-style **breadth + horizon** requirements when interpreting results.

## What we don't take from it

- We do **not** treat their regime conclusions as forecasts for *our* prompts or sleeves — we are not reproducing their agent architecture.
- We do **not** use “LLMs fail in long run” as an excuse to skip **code-enforced risk** — orthogonal layers.

## Open questions

- How sensitive are conclusions to **specific model versions** (GPT vs Claude vs open weights) at identical prompts?
- Does framework account for **corporate actions / tradability** at full fidelity for 100+ names over two decades?

## Cross-links

- `plans/riskMitigation.md` §3 R1, R15  
- `RESEARCH/architecture/testing_ai_agents.md` (evaluation posture)
