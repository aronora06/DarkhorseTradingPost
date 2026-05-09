# Adversarial News and Lost Profits: Manipulating Headlines in LLM-Driven Algorithmic Trading

**Authors:** Advije Rizvani, Giovanni Apruzzese, Pavel Laskov  
**Venue:** arXiv preprint  
**Year:** 2026  
**Link:** https://arxiv.org/abs/2601.13082 — author page mirror: https://www.giovanniapruzzese.com/publications/satml26b  
**Read on:** 2026-05-09

## Claim

Financial ATS increasingly fuse price signals with **LLM-derived news sentiment**. Attackers who can influence headlines consumers/scrapers pick up **without needing direct ATS access** can inject **human-imperceptible textual manipulations** — notably **Unicode homoglyph substitutions** that derail **stock-name recognition** and **hidden-text clauses** that flip sentiment — misleading downstream LLMs. The authors implement a realistic Backtrader ATS combining an **LSTM price forecaster** with LLM sentiment modules (FinBERT, FinGPT, FinLLaMA, multiple general LLMs) and report economically large degradation: **up to ~17.7 percentage points** annual return reduction over **14 months** under their attack scenario definitions; they also argue practical feasibility via scraping/platform observations and practitioner survey (paper abstract).

## Evidence

Controlled replay experiments on historical data with explicit threat model (“single-day headline manipulation window”). Strength: bridges classical adversarial NLP to **portfolio metrics**. Limits: synthetic ATS may differ from Darkhose stack; headline injection feasibility depends on **your ingestion chain** (Bloomberg terminal vs web scrape vs Sonar).

## What we take from it

- Direct scientific support for **`NFKC` normalization**, **allow-listed tickers**, and **never trusting scraped HTML** without sanitization — already listed in `plans/riskMitigation.md` §3 **R10**.
- Strengthens **`NEWS-*`** rows in `RESEARCH/adversarial_vectors.md` with citable numbers for stakeholder conversations.
- Motivates adversarial weekly fixtures mimicking homoglyph tickers + hidden clauses (`tests/specs/adversarial.md`).

## What we don't take from it

- Numeric **17.7 pp** is **not** a forecast for Aaron’s $1k sleeve — different models, costs, and safeguards.
- Hidden-text attacks against **API-grounded** finance search may differ from HTML scraping setups — we still normalize & cite-check.

## Open questions

- How does Perplexity/Tavily rendering strip invisible characters vs raw HTML pipelines assumed in paper?
- Joint attacks: homoglyphs **plus** prompt injection paragraphs (`NEWS-01`).

## Cross-links

- `RESEARCH/adversarial_vectors.md` §News & narrative  
- `doctrine/news_sources.md`
