# RESEARCH/papers/

One-page summaries of source papers we've read. The point is not to reproduce the paper — it is to have, in our own words, what the paper claims, what evidence it offers, and what we are taking from it for Darkhorse.

## Conventions

- **One file per paper.** Filename is `YYYY-firstauthor-keyword.md` (e.g. `2025-li-finsaber-llm-investing-long-run.md`).
- **Cite the paper at the top.** Title, authors, venue, year, link to arXiv or DOI.
- **Length: one page.** If a paper deserves more than a page, write a separate deep-dive note in `RESEARCH/architecture/` and link to it.

## Required sections

```markdown
# <paper title>

**Authors:** ...
**Venue:** ...
**Year:** ...
**Link:** ...
**Read on:** YYYY-MM-DD

## Claim
One paragraph: what does the paper assert?

## Evidence
One paragraph: what data / experiments support the claim? How robust?

## What we take from it
Bullets: specifically how this informs Darkhorse — doctrine, prompts, architecture, anti-patterns, or tests. Each bullet should map to a file or test we plan to write.

## What we don't take from it
Bullets: where the paper's conclusions don't apply to our setting (different scale, different model, different mandate).

## Open questions
Bullets: things we'd want to test if we had the data.
```

## Phase 1 reading list (initial)

Per `../../plans/devPhaseChecklist.md` §1.1, summaries are filed for the seed risks below (`Summaries filed` table — refreshed **2026-05-09**).

- **Look-ahead bias** — FINSABER (`2025-li-finsaber-llm-investing-long-run.md`)
- **Perturbation cascades** — TradeTrap (`2025-yan-tradetrap-trading-agents.md`)
- **Strategic deception** — Apollo / Scheurer et al. (`2024-scheurer-llm-strategic-deception.md`)
- **Adversarial inputs** — Rizvani et al., homoglyph & hidden-text headline attacks (`2026-rizvani-adversarial-news-algorithmic-trading.md`)
- **Memory architecture** — FinMem (`2023-yu-finmem-layered-memory.md`)

Add to this list as new relevant work appears in the monthly competitive-landscape reviews.

## Summaries filed (incremental)

| File | Topic |
|---|---|
| [`2023-yu-finmem-layered-memory.md`](2023-yu-finmem-layered-memory.md) | FinMem — layered memory + profiling + decision modules |
| [`2024-scheurer-llm-strategic-deception.md`](2024-scheurer-llm-strategic-deception.md) | Apollo Research — strategic deception under pressure (ICLR 2024 LLMAgents oral) |
| [`2024-xiao-tradingagents.md`](2024-xiao-tradingagents.md) | TradingAgents multi-agent trading framework (arXiv:2412.20138) |
| [`2025-li-finsaber-llm-investing-long-run.md`](2025-li-finsaber-llm-investing-long-run.md) | FINSABER — long-horizon LLM investing evaluation & biases |
| [`2025-yan-tradetrap-trading-agents.md`](2025-yan-tradetrap-trading-agents.md) | TradeTrap — perturbation cascades in LLM trading agents |
| [`2026-rizvani-adversarial-news-algorithmic-trading.md`](2026-rizvani-adversarial-news-algorithmic-trading.md) | Adversarial news headline attacks vs LLM-driven ATS |
