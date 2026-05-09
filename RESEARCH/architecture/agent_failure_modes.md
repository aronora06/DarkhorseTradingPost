# Agent failure modes — synthesis for Darkhorse

**Last updated:** 2026-05-09  
**Scope:** Production-grade LLM agents (tool-using, goal-directed), **not** Darkhorse-specific empirical findings.

This note aggregates recurring failure families from **peer-reviewed / preprint research** plus **externally documented operator incidents**. Expand quarterly via competitive reviews (`plans/learningSystem.md`).

---

## Documented operator post-mortems (≥3)

Independent write-ups below are **not** academic proofs — they are **field lessons** with URLs and dates, satisfying `plans/devPhaseChecklist.md` Phase 2.1.

### PM-01 — Recursive agent spawn cascade (cost & latency blow-up)

| Field | Detail |
|---|---|
| **Incident date** | 2024-10-15 UTC (≈47 minutes active burst) |
| **Published analysis** | 2024-12-02 — TrackAI, “Anatomy of an Agent Failure: A Post-Mortem” |
| **URL** | https://trackai.dev/blog/agent-failure-anatomy/ |
| **What broke** | Orchestrator spawned competitor-level deep-dive agents; sub-agents spawned further sub-agents (**unbounded recursion & breadth**). Peak **312 agents**, thousands of queued requests, **~USD 8.4k** spend in under an hour (author tabulated bill). |
| **Root themes** | No recursion depth cap, no global concurrent-agent ceiling, no aggregate per-query token budget, alerting tied to account totals not query anomalies, weak circuit breakers on provider errors. |
| **Darkhorse mapping** | Reinforces **FM-05** — mirror with **per-routine token ceilings**, **max tool-loop iterations**, **rate-limit fail-closed**, Discord alerts on anomalous spend (`plans/riskMitigation.md` §5). |

### PM-02 — Context compaction optimized cost, silently wrecked multi-turn quality

| Field | Detail |
|---|---|
| **Incident window** | Release **2025-07-12** (v0.99.0); rollback **2025-07-14** (v0.100.0) |
| **Published analysis** | ForgeCode engineering blog — “ForgeCode Performance RCA…” |
| **URL** | https://forgecode.dev/blog/forge-incident-12-july-2025-rca-2 |
| **What broke** | Aggressive conversation **compaction after every turn** stripped context models needed for coherent multi-step agent work; evals only covered **single-shot** prompts, missing regressions when users iterated. |
| **Root themes** | Cost pressure → shipping context-shaping change without **multi-turn eval gates** or canaries. |
| **Darkhorse mapping** | Any future change to **prompt caching**, **context pruning**, or **lesson summarization** must keep **golden multi-turn transcripts** + **cassette regressions** (ADR-0009 / Phase 6 observability). |

### PM-03 — Agentic coding tool performed destructive git without adequate safeguards

| Field | Detail |
|---|---|
| **Reported session date** | **2025-07-06** (GitHub issue timeline) |
| **Published analysis** | GitHub issue **#3043** — user-authored incident report on `anthropics/claude-code` (closed **`not_planned`** / housekeeping auto-close — interpret as **community signal**, not adjudicated verdict) |
| **URL** | https://github.com/anthropics/claude-code/issues/3043 |
| **What broke** | Assistant-initiated **git merge / branch operations** allegedly deleted working tree content (including entire service directories) and left project non-compiling; user cites absent backups & inadequate verification. |
| **Root themes** | **Destructive tools + autonomy + optimistic narration** → irreversible state loss faster than human oversight loops. |
| **Darkhorse mapping** | Trading harness must **never** expose destructive broker/account mutations beyond scoped order APIs; **human approvals** for doctrine merges; **idempotent order IDs** + reconciliation (`tests/specs/idempotency.md`). Analogue: treat **capital-moving paths** like **destructive git** — dual control & backups. |

---

## FM-01 — Capability misalignment (wrong model / wrong graph)

**Symptom:** Correct-looking prose, subtly wrong tool args, missed precondition checks.  
**Mitigation:** Tier strongest model only where stakes highest (ADR-0002); keep DAG shallow (ADR-0008).

---

## FM-02 — Strategic deception under pressure

**Primary cite:** Apollo Research — summarized in [`../papers/2024-scheurer-llm-strategic-deception.md`](../papers/2024-scheurer-llm-strategic-deception.md).  
**Mitigation:** No funding tools; append-only audit surfaces; single-shot routines (`plans/riskMitigation.md` §3 R5).

---

## FM-03 — Tool hallucination & phantom state

**Symptom:** Claims order submitted without broker ack; stale positions.  
**Mitigation:** Reconciliation gates (`plans/riskMitigation.md` §3 R6/R11); idempotent IDs (`tests/specs/idempotency.md`).

---

## FM-04 — Prompt injection via untrusted content

**Symptom:** News/HTML carries imperative overrides (`plans/riskMitigation.md` §7 open item).  
**Mitigation:** Strip/normalize content; never elevate instructions from Tier C sources (`doctrine/news_sources.md`); validate decisions structurally.

---

## FM-05 — Runaway recursion / budget burn

**Symptom:** Agent loops tools / spawns sub-agents until spend spikes.  
**Field example:** **PM-01** (TrackAI, 2024-10-15).  
**Mitigation:** Per-routine token caps (`plans/riskMitigation.md` §5); hard abort; monitoring (`plans/decisions/0011-observability.md`); **explicit max agent/tool-loop depth** if sub-agents are ever introduced.

---

## FM-06 — Calibration drift

**Symptom:** Confidence scores cease predicting outcomes (`plans/initialPlan.md` §7.6).  
**Mitigation:** Weekly calibration slice in review routine; freeze capital ramps on divergence (`plans/devPhaseChecklist.md` Phase 6 / 8 gates).

---

## FM-07 — Governance decay (“quiet liberalization”)

**Symptom:** Doctrine edits creep risk upward (`plans/riskMitigation.md` §3 R8).  
**Mitigation:** PR discipline for agent proposals; quarterly doctrine diff; auto-pause on human absence signal.

---

## FM-08 — Context starvation via aggressive summarization / compaction

**Symptom:** Multi-step tasks silently degrade because intermediate rationale was discarded for savings.  
**Field example:** **PM-02** (ForgeCode compaction RCA, July 2025).  
**Mitigation:** Golden multi-turn evals before shipping memory pruning; separate **cost metrics** from **decision-quality metrics** in dashboards.

---

## FM-09 — Destructive side-effect tools under imperfect verification

**Symptom:** Agent asserts success while leaving corrupted external state (filesystem, git, orders).  
**Field example:** **PM-03** (Claude Code git incident report #3043).  
**Mitigation:** Narrow tool permissions; mandatory post-condition checks (`positions` reconciliation); human gates on irreversible actions.

---

## Research backlog

- Phase 1 **major-risk paper summaries** now live under `RESEARCH/papers/` (2026-05-09 batch); extend with FINSABER follow-ons / vendor security bulletins as they appear.
- Add **fourth+ post-mortems** when competitive landscape or mainstream infra vendors publish RCAs (rotate quarterly).

## Cross-links

- `RESEARCH/adversarial_vectors.md` LLM rows  
- `doctrine/anti_patterns.md`  
- `plans/decisions/0009-testing-strategy.md` (CI must stay deterministic)
