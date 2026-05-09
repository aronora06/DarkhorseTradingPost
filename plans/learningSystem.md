# Darkhorse Trading Outpost — Learning System Design

## What "Learning" Means Here

Aaron's stated goal: a system that doesn't just remember recent decisions, but that **incrementally adjusts how it does analysis** — a learning entity whose behavior slowly optimizes over a long horizon as it discovers good and bad analysis approaches.

Be honest about what's achievable: **we cannot fine-tune the model.** The base LLM weights are frozen. What we can change, and what "learning" means in this system, is everything that flows *into* the model:

- The **doctrine** it reads as system prompt
- The **lessons** distilled from past decisions
- The **anti-patterns** it's warned to avoid
- The **prompts** that structure its reasoning steps
- The **tools** it has access to and when
- The **context** it's given (which prior decisions, in what shape)

So Darkhorse "learns" in the same sense a doctor learns over a career: not by changing biology, but by accumulating cases, distilling principles, retiring rules that stopped working, and refining the questions they ask. The model is the doctor; the doctrine, lessons, and prompts are everything they've come to think.

## Core Design Principles

1. **Distillation, not accumulation.** A bigger memory file is not a smarter system. Lessons must be compressed; raw journal does not get fed back wholesale.
2. **Falsifiable lessons only.** Every lesson states what would prove it wrong. Lessons that can't be falsified are slogans, not knowledge.
3. **Sunset by default.** Lessons have expiration dates and re-validation requirements. The market regime that produced a lesson may not be the regime in which it's applied.
4. **Calibration over confidence.** Track predicted vs realized; trust the system more in cohorts where it's been right, less where it's been wrong.
5. **Reasoning audits, not just outcome audits.** *How* the agent reasoned matters as much as *what* it concluded. Bad reasoning that got lucky is still bad reasoning.
6. **Aaron-gated doctrine evolution.** The agent proposes; Aaron disposes. No auto-merging.
7. **Evidence-weighted updates.** Live > paper > backtest > narration. The learning system uses this ordering when deciding whether to act on a signal.

## Memory Layers (and What Each Is For)

### L1 — Episodic (raw journal)

**Purpose:** durable, append-only record of every decision and its context. Source of truth for everything else.

**Format:** JSONL, one decision per line, daily-rotated files in `memory/<sleeve>/journal/YYYY-MM-DD.jsonl`.

**Retention:** indefinite. This is the audit trail.

**Read by:** weekly review (sampled), reasoning audits, calibration analysis. **Not** by routine decision-making — it's too long and too noisy to feed in raw.

### L2 — Semantic (lessons)

**Purpose:** distilled, named, falsifiable rules about how to analyze and decide. The level of abstraction is a paragraph, not a tweet and not an essay.

**Format:** `memory/<sleeve>/lessons.md`, one lesson per heading. Each lesson has:
- Title
- Hypothesis (what it claims)
- Evidence basis (which journal entries support it; date range)
- Falsification criterion (what would prove it wrong)
- Sunset date (re-validation required by this date)
- Status: `active | retired | falsified | superseded-by-Lxxx`

**Retention:** lessons live until falsified, retired, or superseded.

**Read by:** every routine, via prompt cache.

### L3 — Anti-patterns (failure modes)

**Purpose:** named recurring failure modes the agent should explicitly avoid. Lessons say "do this"; anti-patterns say "watch for this trap."

**Format:** `doctrine/anti_patterns.md` (yes — promoted into doctrine, because anti-patterns are durable). Each entry:
- Name
- Description
- Telltale signs
- Mitigation (what the agent does when it notices)
- Origin (which post-mortem produced it)

**Retention:** indefinite, but reviewed annually.

**Read by:** every routine, via prompt cache.

### L4 — Reasoning patterns

**Purpose:** track *how* the agent reasons, not just what it decides. Catalog the reasoning styles that recur, so we can see when style drifts.

**Format:** `memory/<sleeve>/reasoning_patterns/YYYY-Qn.md`, auto-generated quarterly by a Haiku-driven audit pass over a random sample of journal entries.

**Retention:** quarterly snapshots; growing history.

**Read by:** Aaron (mostly), and the quarterly retrospective routine. Not fed back into the agent directly — feeding the agent its own reasoning style risks compounding feedback loops.

### L5 — Doctrine (the constitution)

**Purpose:** the slow-changing rules that govern everything. Position sizing, sleeve mandates, universe filters, halt thresholds.

**Format:** `doctrine/*.md`. Version-controlled in git. Doctrine version pinned in every journal entry.

**Retention:** forever, with `git log` as the change history.

**Read by:** every routine, via prompt cache. Aaron edits via PR; the agent can *propose* edits as draft PRs.

## The Learning Loop

The agent learns from two sources: its own experience (the inside view) and the broader field (the outside view). Both feed into the same doctrine, lessons, and anti-pattern stores via Aaron-gated PRs.

```
        INSIDE VIEW                                 OUTSIDE VIEW
  ┌──────────────────────────┐              ┌──────────────────────────┐
  │  L1 Episodic journal     │              │  Monthly competitive     │
  │  (own decisions + P&L)   │              │  landscape review (web)  │
  └────────────┬─────────────┘              └────────────┬─────────────┘
               │                                         │
       ┌───────┼───────┬─────────────┐                   │
       ▼       ▼       ▼             ▼                   ▼
  ┌────────┐ ┌─────┐ ┌────────┐ ┌────────────┐  ┌─────────────────────┐
  │Calibr- │ │Weekly│ │Quarterly│ │Post-mortem │  │Adoption candidates: │
  │ation   │ │review│ │reasoning│ │(triggered) │  │new techniques /     │
  │analysis│ │      │ │audit    │ │            │  │harnesses / models   │
  └───┬────┘ └──┬──┘ └────┬────┘ └─────┬──────┘  └──────────┬──────────┘
      │         │         │             │                    │
      │     ┌───┴───┐     │       ┌─────┴─────┐              │
      ▼     ▼       ▼     ▼       ▼           ▼              ▼
  ┌────────┐ ┌──────────┐ ┌──────────────┐ ┌──────────────────┐
  │Anomaly │ │ Proposed │ │  Reasoning   │ │ Proposed         │
  │ flags  │ │ lessons  │ │  snapshot    │ │ anti-patterns /  │
  │        │ │          │ │  (L4 only)   │ │ adoption PRs     │
  └────┬───┘ └─────┬────┘ └──────────────┘ └────────┬─────────┘
       │           │                                │
       │           └───────────┬────────────────────┘
       │                       ▼
       │       ┌────────────────────────────────────┐
       │       │  Draft PR opened by agent          │
       │       │  (every PR cites a hypothesis)     │
       │       └─────────────────┬──────────────────┘
       │                         ▼
       │       ┌────────────────────────────────────┐
       │       │  Aaron reviews, merges or          │
       │       │  rejects with reasoning            │
       │       └─────────────────┬──────────────────┘
       │                         │
       │           ┌─────────────┴─────────────┐
       │           ▼                           ▼
       │     ┌──────────────┐           ┌────────────────────┐
       └────▶│  L2 lessons  │           │  L3 anti-patterns  │
             │  updated     │           │  updated           │
             └──────┬───────┘           └─────────┬──────────┘
                    │                             │
                    └──────────────┬──────────────┘
                                   ▼
                    ┌──────────────────────────────┐
                    │  Cached into next routine's  │
                    │  prompt context              │
                    └──────────────────────────────┘
```

## Specific Mechanisms

### 1. Calibration tracking

Every decision logs: predicted confidence (0.0–1.0), the action taken, expected horizon, expected outcome. After the horizon, log the realized outcome.

Calibration analysis runs weekly:
- Bin decisions by confidence bucket (0.5, 0.6, 0.7, 0.8, 0.9, 0.95+)
- Compute realized hit rate per bucket
- Compute calibration error (predicted - realized)
- Report drift over rolling 4 / 12 / 26 weeks

**Action triggers:**
- If a confidence bucket's calibration error > 10pp for 2 consecutive weekly reports → flag for doctrine review (the agent is over- or under-confident in that cohort)
- If overall calibration error stays > 5pp for 4 weeks → freeze new live capital, force a doctrine review

### 2. Lesson distillation

Once per week, the reflection routine (`weekly_review.py`) runs Haiku 4.5 over the past week's journal entries plus any open anomaly flags from calibration analysis. It produces:

- Candidate lessons: "I noticed pattern X across these journal entries — proposed lesson Y."
- Each candidate lesson must include: title, hypothesis, evidence (specific journal entries cited by ID), falsification criterion, suggested sunset date.

Distillation rules (enforced by the prompt and validated by a Python check):

- A candidate lesson must be supported by ≥ 5 journal entries OR ≥ 1 large-loss post-mortem.
- A candidate lesson must propose a specific change to doctrine, prompts, or anti-patterns — not just an observation.
- A candidate lesson must not contradict an active lesson without explicit reference and a "supersedes" relationship.
- A candidate lesson without a falsification criterion is rejected at the validator step before reaching Aaron.

The agent opens a draft PR. Aaron reviews and either merges (lesson goes live), edits-and-merges, or closes-with-reasoning (the rejection itself becomes a journal entry — it's data).

### 3. Lesson sunset & re-validation

Every lesson carries a sunset date, default 6 months from creation. When a lesson reaches sunset:

- The reflection routine runs a re-validation pass: does the original hypothesis still hold against post-creation journal entries?
- Outcomes:
  - **Confirmed:** sunset extended by another 6 months
  - **Refined:** new lesson supersedes the old, old marked superseded
  - **Falsified:** old lesson marked falsified and removed from active context (kept in history)

Lessons that have been re-validated 3 times and are still confirmed get **promoted to doctrine** — they become rules, not lessons. This is the long-horizon optimization Aaron asked for: knowledge that has survived multiple regimes earns a higher status.

### 4. Anti-pattern extraction

Triggered by:
- A losing trade > 1% of sleeve NAV (auto)
- A daily-loss kill firing (auto)
- A drawdown-halt firing (auto)
- Aaron manually requesting a post-mortem on a specific decision

The post-mortem routine reads the relevant journal entries, plus the surrounding market context, plus current lessons/anti-patterns, and asks: was this an instance of a known anti-pattern, a new one, or just bad luck?

If new: proposes an addition to `doctrine/anti_patterns.md` via PR. If known: reinforces the entry's "telltale signs" with the new instance.

### 5. Monthly competitive landscape review (agentic web review)

Once per month, a dedicated routine performs a deep web review of the agentic-trading and agent-architecture landscape. The point: Darkhorse should not learn only from its own journal — the field is moving, and we should systematically scan for techniques, harnesses, and approaches we could borrow.

**Routine:** `monthly_competitive_review.py` (runs first weekend of each month).

**Process:**
1. **Aggregate sources** via Sonar Deep Research + Tavily + Exa:
   - New / trending GitHub repos in agentic trading, multi-agent finance frameworks
   - arXiv papers from the last 30 days (LLM + finance, agent architectures, calibration, memory)
   - Hacker News and Reddit discussions on personal AI traders and post-mortems
   - Blog posts from credible practitioners (Robot Wealth, QuantConnect, Anthropic/OpenAI cookbooks, MindStudio)
   - Anthropic / OpenAI / Google updates on agent primitives, structured outputs, caching
   - New broker APIs or data providers
2. **Filter to relevance** for Darkhorse (multi-agent harness, retail-scale, US equities, Claude-based).
3. **Deep-read** the top 3–5 items: full paper, full repo skim, post-mortem reading.
4. **Produce a structured report** in `RESEARCH/competitive_landscape/YYYY-MM.md` containing:
   - One-line summary per item reviewed
   - Deep-dive on top 3–5
   - Transferable techniques: what could we adopt?
   - Explicit recommendation: adopt / experiment / monitor / ignore — with reasoning
   - Falsifiable hypotheses any adoption would test (registered in `RESEARCH/hypotheses/` if adopted)

**Cost budget:** ~$2 per monthly review (Sonar Deep Research is more expensive per call). One-time cost; one routine; one output. Worth it.

**Aaron's role:** read the report, decide on adoptions, file PRs for any techniques worth trying. Adoptions go through the same paper-shadow validation as any other architectural change.

**Why this matters:** Without this, Darkhorse risks becoming a beautifully-engineered local optimum — improving against its own journal but missing better ideas in the broader field. The competitive-landscape review is the *outside view* on the system; everything else is the inside view.

### 6. Reasoning audits

Quarterly. A Haiku-driven pass reads N=50 randomly sampled journal entries (stratified across confidence buckets and outcomes) and categorizes the reasoning style:

- Did the agent consider the bear case substantively, or as boilerplate?
- Did the agent cite sources, or assert?
- Did the agent reference the 30-day base rate prompt, or skip it?
- What weight did the agent place on news vs fundamentals vs technicals?

The output is a categorized snapshot in `memory/<sleeve>/reasoning_patterns/YYYY-Qn.md`. **This is for Aaron's eyes**, not for the agent's prompt. We do not feed the agent its own reasoning style — that's a feedback loop with bad equilibria.

If an audit reveals a systematic reasoning weakness (e.g., "the agent treats the bear case as a 1-sentence afterthought 80% of the time"), Aaron decides whether to evolve the prompts or doctrine to compensate.

### 7. Prompt evolution

The prompts in `prompts/*.md` are versioned. Changes go through PR. Prompt evolution is one of the slowest learning levers but one of the most powerful — restructuring how the agent reasons is the closest we can get to "teaching" it.

Examples of prompt evolution we expect over time:

- Adding forced reasoning steps as anti-patterns accumulate ("before deciding, explicitly list the three most likely ways this thesis is wrong")
- Refining the JSON schema for decisions as we learn what fields actually predict outcomes
- Adjusting the bull/bear debate format (e.g., requiring the bear to argue first if calibration shows over-bullishness)

Every prompt change is a hypothesis. The hypothesis must be registered in `RESEARCH/hypotheses/`, tested in paper for ≥ 2 weeks, and either accepted or rolled back with evidence cited.

### 8. Doctrine promotion path

The path from observation to durable rule:

```
journal entry → distilled lesson → re-validated lesson (3x) → doctrine rule
```

This is deliberately slow. A pattern that earns its way to doctrine has survived ≥ 18 months of re-validation and produced consistent evidence in that window. Doctrine is supposed to be sticky.

## What This System Will NOT Do

Honesty about limits:

- **Will not fine-tune the model.** Frozen weights.
- **Will not develop "intuitions" the model doesn't already have.** It can only restructure inputs.
- **Will not reliably catch its own systematic flaws.** The reasoning audit is performed by another Claude on the same training distribution. Some blind spots are shared. This is why Aaron-in-the-loop matters.
- **Will not learn faster than the data accumulates.** At 5 routines/day in v1, "fast" learning is months, not weeks.
- **Will not become competitive with professional quant teams.** This is a personal learning system, not a fund.

## What Success Looks Like

A year in, we'd expect to see:

- A `lessons.md` with ~10–30 active lessons, ~5–10 retired, ~3–5 promoted to doctrine
- An `anti_patterns.md` with ~10 well-documented entries, each cited in real journal entries
- A calibration curve that has detectably tightened from baseline
- A quarterly reasoning-patterns history that shows visible style evolution
- A small but real set of falsified hypotheses — because falsification is evidence the system has integrity

If after a year we have only "everything still active, calibration unchanged, no falsifications" — the learning system didn't work. That outcome is itself a research finding (RQ3 in `researchCharter.md`).
