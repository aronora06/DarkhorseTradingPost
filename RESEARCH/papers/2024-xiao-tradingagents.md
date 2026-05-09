# TradingAgents: Multi-Agents LLM Financial Trading Framework

**Authors:** Yijia Xiao, Edward Sun, Di Luo, Wei Wang  
**Venue:** arXiv preprint  
**Year:** 2024 (revised through 2025)  
**Link:** https://arxiv.org/abs/2412.20138  
**Read on:** 2026-05-09

## Claim

A multi-agent LLM architecture mirroring **sell-side / HF-style specialization** (fundamental, sentiment, news, technical analysts → bull/bear researchers → trader → risk managers → fund manager) yields **better trading metrics** (return, Sharpe, drawdown) than single-agent or unstructured multi-agent baselines, partly by combining **structured outputs** with natural-language debate to mitigate communication degradation (“telephone effect”).

## Evidence

Simulation/backtest-style experiments vs multiple LLM baselines on historical financial data; metrics include cumulative return, Sharpe, maximum drawdown (paper asserts notable improvements — exact magnitudes depend on dataset / prompt / symbol universe and must be treated as **non-transferable** evidence quality).

## What we take from it

- Validates Darkhorse’s **researcher → bull/bear → risk-manager** sequencing (`plans/initialPlan.md` §3.3) as directionally sound — not because their headline returns replicate, but because **role separation + explicit disagreement** addresses known single-agent bias modes.
- Supports investing in **structured decision payloads** after debate rather than raw prose-only execution (`doctrine/style_guide.md`).
- Reinforces need for **risk role isolation** (risk-manager on stronger model tier per ADR-0002).

## What we don't take from it

- Their reported **absolute returns** — microstructure, costs, and adversarial reality differ from backtest LLM loops.
- Full **seven-role** sprawl day-one — cost/latency inappropriate at $1k AUM; prefer minimal viable debate graph per ADR-0008.
- Any reliance on **tools / data sources** enumerated in their framework but absent from our audited stack.

## Open questions

- How sensitive are gains to **prompt leakage** of future data in LLM training windows? (Parallels FINSABER concerns — orthogonal validation needed.)
- Debate length vs **cache economics** — multi-turn chains burn tokens; Darkhorse leans on caching stable doctrine (`plans/riskMitigation.md` §2.4).

## Cross-links

- `RESEARCH/architecture/multi_agent_debate.md`  
- `plans/decisions/0008-agentic-harness-pattern.md`
