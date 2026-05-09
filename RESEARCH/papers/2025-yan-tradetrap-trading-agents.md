# TradeTrap: Are LLM-based Trading Agents Truly Reliable and Faithful?

**Authors:** Lewen Yan, Jilin Mei, Tianyi Zhou, Lige Huang, Jie Zhang, Dongrui Liu, Jing Shao (Shanghai AI Laboratory)  
**Venue:** arXiv preprint  
**Year:** 2025  
**Link:** https://arxiv.org/abs/2512.02261 — code: https://github.com/Yanlewen/TradeTrap  
**Read on:** 2026-05-09  
**Content note:** Authors flag that the paper may contain upsetting examples.

## Claim

LLM-based **autonomous trading agents** are increasingly plausible for real markets, but their **robustness under perturbations** is under-studied. **TradeTrap** stress-tests agents across four pipeline stages — **market intelligence**, **strategy formulation**, **portfolio & ledger handling**, and **trade execution** — using controlled system-level perturbations in a **closed-loop historical backtest** on real U.S. equity data. Small disruptions at **one** stage can **cascade** through the loop, producing **extreme concentration**, **runaway exposure**, and **large drawdowns** across multiple agent designs.

## Evidence

Unified evaluation harness comparing clean vs perturbed runs with identical initial conditions; vulnerability classes discussed include tool/MCP-path manipulation, prompt injection, memory/state tampering, and execution-path misuse (see their Figure 1 taxonomy). Empirical claims are **simulation-level** (not live brokerage proof), but the **system-level framing** matches how Darkhorse composes tools + state + LLM reasoning.

## What we take from it

- Validates investment in **`validate_order`** as a **non-bypassable wall** and in **adversarial fixtures** (`RESEARCH/adversarial_vectors.md`, `tests/specs/adversarial.md`).
- Supports ADR-0001 posture: **native SDK tools with tight contracts** beat opaque tool chains that are harder to audit under perturbation.
- Motivates Phase 7 **TradeTrap-style red teaming** (subset of attacks) whenever agent/tool topology changes.

## What we don't take from it

- We **hard-pass** models/providers banned by doctrine (`plans/riskMitigation.md` §2.3); their experiments may include models we will never run — skip transferring numeric “attack success rates.”
- Cascade severity depends on **their** agent implementations; Darkhorse must measure on **our** harness.

## Open questions

- Which perturbation classes map 1:1 to **news ingestion** vs **broker API** faults in our stack?
- Can property-based tests approximate **state tampering** without live LLM calls (ADR-0009)?

## Cross-links

- `RESEARCH/adversarial_vectors.md`  
- `plans/decisions/0009-testing-strategy.md`
