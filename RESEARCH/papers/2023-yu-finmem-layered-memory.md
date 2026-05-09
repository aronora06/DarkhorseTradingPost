# FinMem: A Performance-Enhanced LLM Trading Agent with Layered Memory and Character Design

**Authors:** Yangyang Yu, Haohang Li, Zhi Chen, Yuechen Jiang, Yang Li, Denghui Zhang, Rong Liu, Jordan W. Suchow, Khaldoun Khashanah  
**Venue:** arXiv preprint **2311.13743**; additionally presented/discussed in **AAAI Symposium Series** / **ICLR 2024 workshop** tracks (see institutional indexes — cite arXiv as stable PDF)  
**Year:** 2023 (arXiv); workshop appearances 2024  
**Link:** https://arxiv.org/abs/2311.13743 — OpenReview workshop thread (example): https://openreview.net/forum?id=sstfVOwbiG  
**Read on:** 2026-05-09

## Claim

Generic LLMs need **purpose-built agent scaffolding** for trading: **profiling** (character / operational stance), **layered memory** (hierarchical assimilation of multi-source financial cues), and **decision-making** that converts memories into actions. FinMem emphasizes **interpretable memory structure** and adjustable **cognitive span**, claiming competitive trading metrics vs algorithmic baselines on scalable historical equity data when memory + persona are tuned.

## Evidence

Architecture paper + empirical comparisons against multiple algorithmic agents; stresses memory span tuning & character settings as performance levers. Strength: connects **human-trader cognitive limits** to engineering choices. Weakness: empirical section predates newest foundation models — absolute returns **do not transfer**; architectural lessons might.

## What we take from it

- Informs ADR-0003 (“JSONL + Markdown source of truth, SQLite mirror”) — FinMem’s lesson is **explicit memory layers**, not “hope the context window remembers.”
- Supports compiling **compressed doctrine + rolling journal summaries** into stable cached contexts (`plans/riskMitigation.md` §2.4).
- Caution: layered memory + narrative reflection can amplify **false-confidence stories** — pair with **calibration tracking** (`plans/initialPlan.md` §7.6) and **Haiku-tier summarization** only where bounded.

## What we don't take from it

- We do **not** adopt FinMem’s full persona/memory machinery verbatim — Darkhorse memory contracts live in `plans/dataSchema.md` + forthcoming code.
- No endorsement of their baseline trading performance as **live-edge**.

## Open questions

- Where should **lesson promotion** gate sit relative to FinMem-style continuous self-edit (`plans/learningSystem.md` slow promotion path)?
- How to **test memory replay deterministically** under ADR-0009 (cassette / fixtures)?

## Cross-links

- `plans/decisions/0003-memory-architecture.md`  
- `plans/dataSchema.md`
