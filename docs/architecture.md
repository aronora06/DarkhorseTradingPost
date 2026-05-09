# Darkhorse Trading Outpost — Architecture

This document is the master architectural reference for the Darkhorse codebase. It is intended to be read end-to-end by any developer (today, future-Aaron, or a future contributor) who needs to understand the shape of the system before writing or modifying code.

It is **not** a steering document — those live in `plans/initialPlan.md`, `plans/riskMitigation.md`, `plans/researchCharter.md`, and `plans/learningSystem.md`. This document operationalizes those into the concrete architecture we will build.

The "why" of every load-bearing choice lives in an ADR under `plans/decisions/`. This document is the "what" plus quick rationale plus pointers; the ADRs are where reasoning lives.

## Table of Contents

1. [Goals & Non-goals](#1-goals--non-goals)
2. [Architectural Principles](#2-architectural-principles)
3. [System at a Glance](#3-system-at-a-glance)
4. [Layers](#4-layers)
5. [Data Flow — Per-Routine Sequence](#5-data-flow--per-routine-sequence)
6. [Tech Stack](#6-tech-stack)
7. [Repository Layout](#7-repository-layout)
8. [Deployment Topology](#8-deployment-topology)
9. [Security Posture](#9-security-posture)
10. [Extensibility Hooks](#10-extensibility-hooks)
11. [Anti-Architecture (What We Explicitly Don't Do)](#11-anti-architecture-what-we-explicitly-dont-do)
12. [ADR Index](#12-adr-index)
13. [Open Architectural Questions](#13-open-architectural-questions)

---

## 1. Goals & Non-goals

### Goals

- **Real money trading** at micro-size from Phase 4 onward, ramping to full $1,000 by Phase 8.
- **Multi-agent debate** (researcher → bull/bear → risk-manager) producing schema-validated decisions.
- **Code-enforced risk discipline**: every order passes through `validate_order()` regardless of what the LLM emitted.
- **Stateless routines, durable memory**: each routine wakes with no memory and reads its world from disk.
- **Observable everything**: every decision reconstructable; every cost accounted for; every failure loud.
- **Single-developer maintainable**: Aaron is the only operator. The architecture must reward "I can hold this in my head."
- **Year-1 publication-ready**: data formats, journal shapes, and anonymization paths designed in from day 1, not retrofitted.
- **Extensibility**: new tools, new sleeves, new harness variants, new model tiers can be added without re-architecting.

### Non-goals

- Multi-tenant SaaS
- Sub-second decision latency
- Auto-scaling, multi-region, multi-AZ
- Order entry by Aaron through the dashboard (intentional — orders are the agent's job)
- Container orchestration (k8s, Nomad)
- Feature flags / experimentation platforms
- A "platform" that other people could deploy (this is a personal trading assistant)

## 2. Architectural Principles

These principles are non-negotiable and should be cited in code review when a change appears to violate one. Drawn from `initialPlan.md` §2 and operationalized here:

1. **Risk lives in code, not prompts.** Every order passes through `src/darkhorse/risk/validate_order.py`. The LLM cannot prompt-engineer its way around an `if` statement.
2. **Stateless agents, durable memory.** No long-lived agent processes; routines wake, read disk, decide, write disk, exit.
3. **Tested before live; ramp by size.** Risk modules unit-tested before any agent code exists. From Phase 4: real money at micro-size, ramping with paper-shadow as the divergence detector.
4. **Idempotent and reconstructable.** Deterministic `client_order_id` per intent; every decision journaled with full reasoning trace.
5. **Two sleeves, two policies, one harness.** Shared infrastructure, separate doctrine, separate journals, separate limits.
6. **The kill-switch is real.** File flag, env var, or external endpoint — checked on every routine entry. The agent cannot disable it.
7. **Default action under uncertainty is NO_TRADE.** Doing nothing is a feature.
8. **Cost discipline.** Tiered models + 1-hour prompt cache; target ≤ 0.5% of NAV/yr in compute.
9. **Falsifiable changes.** Every doctrine PR, every prompt change, every architectural shift specifies what would have to be true for it to be wrong.
10. **Anonymizable from day 1.** Every artifact (journal, calibration, retro) is publication-anonymizable without retrofitting.

## 3. System at a Glance

```
                                     ┌───────────────────────┐
                                     │  systemd timers (VPS) │
                                     │  + GitHub Actions     │
                                     │    cron (backup)      │
                                     └───────────┬───────────┘
                                                 │ fires routine
                                                 ▼
        ┌─────────────────────────────────────────────────────────────────┐
        │                       ROUTINE ENTRY POINT                        │
        │ (pre_market | market_open | midday_scan | end_of_day | weekly)  │
        └────────────┬───────────────────────────────────────┬────────────┘
                     │ load context                          │ check kill-switch
                     ▼                                       ▼
        ┌────────────────────────┐                ┌────────────────────────┐
        │ Doctrine (read-only)   │                │ KILLSWITCH file / env  │
        │ Lessons / anti-pat'rns │                │ + remote endpoint      │
        │ (cached, 1h TTL)       │                │ → if on, log & exit    │
        └────────────┬───────────┘                └────────────────────────┘
                     │
                     ▼
        ┌─────────────────────────────────────────────────────────────────┐
        │                      HARNESS  (src/darkhorse/harness.py)        │
        │                                                                 │
        │   ┌─────────────┐    ┌──────────┐    ┌──────────┐    ┌────────┐ │
        │   │ Researcher  │ →  │   Bull   │ ↘                            │
        │   │ (Sonnet 4.6)│    │ Analyst  │   ↘                          │
        │   └─────────────┘    │(Sonnet)  │     → Risk-Manager (Opus 4.7)│
        │                      └──────────┘   ↗                          │
        │                      ┌──────────┐ ↗                            │
        │                      │   Bear   │                              │
        │                      │ Analyst  │                              │
        │                      │(Sonnet)  │                              │
        │                      └──────────┘                              │
        │                                                                │
        │                            ↓ Decision JSON (structured output) │
        └────────────┬───────────────────────────────────────┬───────────┘
                     │                                       │
                     ▼                                       ▼
        ┌────────────────────────┐                ┌────────────────────────┐
        │ validate_order()       │                │ tools/                 │
        │  (Python wall — risk   │ ←─ tool calls ─│  alpaca, data, news,   │
        │   policy in code)      │  during debate │  snaptrade, journal    │
        └────────────┬───────────┘                └────────────────────────┘
                     │ if pass
                     ▼
        ┌────────────────────────┐
        │ alpaca.submit_order()  │
        │  (live and/or paper-   │
        │   shadow accounts)     │
        └────────────┬───────────┘
                     │
                     ▼
        ┌─────────────────────────────────────────────────────────────────┐
        │                       MEMORY LAYER (durable)                    │
        │                                                                 │
        │  L1 Episodic   memory/<sleeve>/journal/YYYY-MM-DD.jsonl         │
        │  L2 Semantic   memory/<sleeve>/lessons.md                       │
        │  L3 Anti-pat   doctrine/anti_patterns.md (PR-edited)            │
        │  L4 Reasoning  memory/<sleeve>/reasoning_patterns/YYYY-Qn.md    │
        │  L5 Doctrine   doctrine/*.md (git-versioned)                    │
        │  Calibration   memory/<sleeve>/calibration.jsonl                │
        │  Cost          memory/cost/YYYY-MM-DD.jsonl                     │
        │  Audit         memory/audit/YYYY-MM-DD.jsonl                    │
        │  SQLite mirror memory/index.sqlite (read-only, rebuilt nightly) │
        └─────────────────────────────────────────────────────────────────┘
                     │
                     ▼
        ┌─────────────────────────────────────────────────────────────────┐
        │              OBSERVABILITY  (src/darkhorse/notify.py)           │
        │  structlog (JSON logs)  →  systemd journal                      │
        │  Discord webhook         →  Aaron's phone                       │
        │  /healthz endpoint       →  Cloudflare Worker + Mac launchd     │
        │  Cost telemetry          →  dashboard Costs page                │
        └─────────────────────────────────────────────────────────────────┘
                     ▲
                     │ reads
        ┌────────────┴───────────────────────────────────────────────────┐
        │      DASHBOARD (src/darkhorse/web/app.py — FastAPI + HTMX)     │
        │      Tailscale-only, served from same Python process           │
        └────────────────────────────────────────────────────────────────┘
```

## 4. Layers

The system is best understood as eight layers, each with a single responsibility. Layers below the harness are deterministic; the harness is the only non-deterministic component.

### 4.1 Risk Layer

**Path:** `src/darkhorse/risk/`

The **safety wall.** Every order, every halt check, every sizing computation passes through this layer. None of these functions call an LLM; all are pure Python with full unit-test and property-test coverage.

| Module | Purpose |
|---|---|
| `validate_order.py` | Final pre-broker check. Asserts position cap, sleeve cap, daily-loss kill state, drawdown halt state, kill-switch state, ticker whitelist, PDT safety, idempotency. |
| `sizing.py` | Per-sleeve sizing math. Translates "% of sleeve NAV" into integer share quantities given a price. |
| `kill_switch.py` | Three-source check: `KILLSWITCH` file at repo root, `DARKHORSE_KILLSWITCH` env var, optional remote `/killswitch` endpoint. ANY positive → halt. |
| `drawdown.py` | High-water mark tracking. Fires daily-loss kill, drawdown halt, uncle point. **HWM does not reset after halt.** |
| `wind_down.py` | Implements `riskMitigation.md` §6 wind-down rule. If 6-month rolling Sharpe vs SPY < 0, Core converts to SPY. Self-firing from day 1 of live. |

The risk layer **never reads the doctrine** at runtime. The numbers it enforces are in `config/settings.toml` (`max_position_pct_core`, `daily_loss_kill_pct_core`, etc.), loaded once at process start. This means:
- Doctrine changes that affect risk numbers go through PR review AND require a config restart.
- The risk layer cannot be subverted by a doctrine edit alone — it requires a deliberate redeploy.

ADR references: `0009-testing-strategy.md`.

### 4.2 Tools Layer

**Path:** `src/darkhorse/tools/`

The agent's hands. Tools are typed Python functions registered with the Anthropic SDK's `tools=[...]` parameter. Every tool has:
- A pydantic input model (in `_contracts.py`)
- A pydantic output model
- A docstring that doubles as the agent-facing description
- `strict: true` schema enforcement at the SDK boundary

| Module | Purpose |
|---|---|
| `alpaca.py` | Account, positions, orders. Every order routes through `validate_order` before reaching Alpaca. Connects to live and paper accounts via separate clients. |
| `data.py` | Market data: Finnhub (paid tier free), yfinance fallback. Returns timestamps for staleness detection. |
| `news.py` | Sonar Finance Search + Tavily fallback. Unicode-NFKC normalize all returned text before it enters the prompt. Validate cited tickers against the asset list. |
| `snaptrade.py` | Read-only Fidelity holdings via SnapTrade. For sizing context only — agent cannot trade Fidelity. |
| `journal.py` | Internally-used tool the agent does not call directly; the harness writes through this. |

Caching at the tool layer: each tool result is memoized within a single routine invocation (never across routines). News and quotes are fetched once; intra-routine the same call returns the cached result.

ADR references: `0001-tool-integration-anthropic-sdk-vs-mcp.md`.

### 4.3 Harness Layer

**Path:** `src/darkhorse/harness.py`

The orchestrator. Implements the multi-agent debate flow as plain async Python — no framework. Lives in a single ~500-line file by design.

Responsibilities:
- Loading doctrine, lessons, anti-patterns, recent journal summary, current positions
- Setting up the prompt cache write (1-hour TTL) on stable context
- Calling sub-agents in the correct order (researcher → parallel bull/bear → risk-manager)
- Constraining the risk-manager output via `output_config.format` (JSON Schema)
- Capturing per-call cost telemetry from `usage.cache_*_tokens` and `usage.{input,output}_tokens`
- Wrapping every call in `tenacity.AsyncRetrying` (1s/3s/9s on RateLimitError, OverloadedError, 5xx)
- Writing the decision JSON through `validate_order` → broker → journal
- Logging structured events at every step

ADR references: `0008-agentic-harness-pattern.md`, `0002-tiered-model-strategy.md`.

### 4.4 Memory Layer

**Path:** `src/darkhorse/memory/` (readers + mirror); `memory/` (runtime data, gitignored)

Five logical layers (per `learningSystem.md` §"Memory Layers"):

- **L1 Episodic** — `memory/<sleeve>/journal/YYYY-MM-DD.jsonl` (append-only, source of truth)
- **L2 Semantic** — `memory/<sleeve>/lessons.md` (markdown with YAML frontmatter; PR-edited)
- **L3 Anti-patterns** — `doctrine/anti_patterns.md` (promoted to doctrine; PR-edited)
- **L4 Reasoning patterns** — `memory/<sleeve>/reasoning_patterns/YYYY-Qn.md` (Aaron-only)
- **L5 Doctrine** — `doctrine/*.md` (git-versioned)

Plus operational layers:
- Calibration log (`memory/<sleeve>/calibration.jsonl`)
- Post-mortems (`memory/<sleeve>/post_mortems/pmt_NNN.md`)
- Hypothesis registry (`RESEARCH/hypotheses/H_NNN.md`)
- Cost telemetry (`memory/cost/YYYY-MM-DD.jsonl`)
- Audit log (`memory/audit/YYYY-MM-DD.jsonl`)

The **SQLite mirror** at `memory/index.sqlite` is rebuilt nightly from JSONL files. It serves dashboard queries only; nothing important *only* lives in SQLite.

ADR references: `0003-memory-architecture.md`. Schema reference: `dataSchema.md`.

### 4.5 Routines Layer

**Path:** `src/darkhorse/routines/`

Five scheduled entry points + one monthly:

| Routine | Schedule | What it does |
|---|---|---|
| `pre_market.py` | 8:30 AM ET weekdays | Read overnight news, update watchlist, draft theses |
| `market_open.py` | 9:35 AM ET weekdays | Execute high-conviction trades from pre-market draft |
| `midday_scan.py` | 12:30 PM ET weekdays | Review open positions vs theses, scan for new setups |
| `end_of_day.py` | 4:05 PM ET weekdays | Close any day-trade flags, write the journal entry |
| `weekly_review.py` | Friday 5:00 PM ET | Compile lessons, calibration check, doctrine PRs |
| `monthly_competitive_review.py` | First weekend of month | Scan agentic-trading landscape; propose adoptions |

Each routine is a CLI entry point: `python -m darkhorse.routines.market_open`. The systemd timer fires this command. The routine is fully stateless: reads world from disk, runs through harness, writes back to disk, exits.

ADR references: `0006-scheduler.md`.

### 4.6 Web Layer

**Path:** `src/darkhorse/web/`

FastAPI app serving the dashboard. Same Python project as the agent; shares config, schemas, journal readers. Bound to the Tailscale interface only.

Pages (per `frontendAndHosting.md`): Overview, Portfolio, Performance, Calibration, Decisions, Lessons & Doctrine, Anti-Patterns, Costs, System Health.

Two write actions: kill-switch toggle, doctrine PR approval/rejection.

Frontend: Jinja2 templates, HTMX 2.x, Alpine.js, Tailwind CSS + DaisyUI, Plotly.js (charts only, conditionally loaded).

ADR references: `0004-frontend-stack.md`.

### 4.7 Learning Layer

**Path:** `src/darkhorse/learning/`

The meta-cognitive layer that operates on the journal to produce lessons, anti-patterns, calibration analyses, and the quarterly reasoning audit. Per `learningSystem.md` §"Specific Mechanisms":

| Module | Purpose |
|---|---|
| `distillation.py` | Weekly: read journal, extract candidate lessons, open draft PRs |
| `decay.py` | Daily check for sunset-due lessons; trigger re-validation |
| `calibration_analysis.py` | Weekly: confidence-bucket hit rates; drift alerts |
| `anti_pattern_extraction.py` | Triggered: post-mortem on losing trade > 1% NAV |
| `reasoning_audit.py` | Quarterly: Haiku-driven sample of N=50 journal entries, categorize reasoning patterns |

These are routines themselves but live in their own module to separate "learn from past" from "decide for now."

### 4.8 Evaluation Layer

**Path:** `src/darkhorse/evaluation/`

Backtesting and adversarial testing. Run via Phase 7 gate before the size ramp; periodically thereafter.

| Module | Purpose |
|---|---|
| `backtest_finsaber.py` | Walk-forward backtest, post-cutoff data only, full universe including delistings, anonymized in-cutoff windows |
| `adversarial.py` | Unicode homoglyph tickers, prompt-injection in news, stale quotes, malformed tool returns |

ADR references: `0009-testing-strategy.md`.

## 5. Data Flow — Per-Routine Sequence

### Standard routine (e.g., `market_open`):

```
1. systemd timer fires: python -m darkhorse.routines.market_open
2. Settings() loads env + settings.toml; pydantic validates
3. structlog binds context: routine=market_open, sleeve=core, doctrine_version=<sha>
4. kill_switch.is_on() — if true, log "halted by kill-switch", exit 0
5. drawdown.is_halted(sleeve) — if true, log "halted by drawdown", exit 0
6. Load doctrine + active lessons + anti-patterns into context (cache write, 1h TTL)
7. Load current positions from Alpaca (no cache; fresh each routine)
8. Load 30-day journal summary (in cache)
9. Run harness:
   a. researcher (Sonnet 4.6) — reads context, surveys news + setups, returns findings
   b. parallel { bull (Sonnet 4.6), bear (Sonnet 4.6) } — each consumes researcher output
   c. risk_manager (Opus 4.7) — consumes researcher + bull + bear, emits Decision JSON
      via output_config.format with strict schema
10. validate_order(decision) — if rejected, log reason, journal NO_TRADE entry, return
11. alpaca.submit_order(decision) — live account; client_order_id is deterministic
12. Parallel: alpaca.submit_order on paper-shadow account (using same decision)
13. journal.append(decision_with_outcome_pending) to memory/<sleeve>/journal/YYYY-MM-DD.jsonl
14. Cost telemetry written to memory/cost/YYYY-MM-DD.jsonl
15. structlog emit "routine complete"; Discord webhook for daily recap (end_of_day only)
16. exit 0
```

If any step fails, it fails loud:
- Exception → structlog ERROR + Discord webhook RED
- routine returns non-zero exit code
- systemd `OnFailure=` unit kicks a Discord notification
- The next routine reconciles state via the positions endpoint before placing any new order

### Post-horizon outcome backfill:

A separate routine (likely part of `end_of_day.py` or a daily cron) finds journal entries whose `expected_horizon_days` has elapsed without a recorded outcome, computes the realized P&L, and writes the outcome back. This produces the calibration log.

### Weekly review:

```
1. Friday 5:00 PM ET: weekly_review.py
2. Read past 7 days of journal entries
3. Read calibration log; compute drift per confidence bucket
4. Run distillation pass (Haiku 4.5) on the journal sample
5. Produce candidate lessons; validate each has hypothesis + falsification + sunset
6. Open draft PRs (via gh CLI) to memory/<sleeve>/lessons.md
7. Discord summary with PR links
```

## 6. Tech Stack

Lock-in summary, with ADR refs:

| Concern | Choice | ADR |
|---|---|---|
| Language | Python 3.13 | `0007` |
| Package manager | uv | `0007` |
| Lint + format | Ruff | `0007` |
| Type checker | mypy --strict | `0007` |
| Test framework | pytest + Hypothesis | `0007`, `0009` |
| Data validation | pydantic v2 | `0007` |
| Settings | pydantic-settings | `0012` |
| Logging | structlog | `0011` |
| HTTP | httpx | `0007` |
| Retries | tenacity | `0008` |
| LLM provider (premium) | Anthropic Opus 4.7 | `0002` |
| LLM provider (workhorse) | Anthropic Sonnet 4.6 | `0002` |
| LLM provider (cheap) | Anthropic Haiku 4.5 | `0002` |
| Agent harness | Custom thin wrapper | `0008` |
| Tool integration | Anthropic SDK native | `0001` |
| Web framework | FastAPI | `0004` |
| Templating | Jinja2 | `0004` |
| Frontend interactivity | HTMX 2.x + Alpine.js | `0004` |
| Styling | Tailwind CSS + DaisyUI | `0004` |
| Charts | Plotly.js (CDN, conditional) | `0004` |
| Memory source-of-truth | JSONL + Markdown | `0003` |
| Memory query mirror | SQLite | `0003` |
| Hosting | Hetzner Cloud CX22 (Ashburn US) | `0005` |
| Scheduler | systemd timers | `0006` |
| Auth | Tailscale presence | `0004`, `0005` |
| Notifications | Discord webhook | `0011` |
| CI | GitHub Actions | `0010` |
| CD | Manual SSH via Tailscale | `0010` |
| Backups | Backblaze B2 (age-encrypted) | `0005` |
| Health monitoring | /healthz + Cloudflare Worker + Mac launchd | `0011` |

Total runtime infrastructure cost target: ~$5/mo. Total compute cost target: ~$3/mo. **Total: ~$8/mo, ≈ 0.8% of NAV/yr.**

## 7. Repository Layout

(See `0007-python-project-layout.md` for the full version. Summary here.)

```
DarkhorseTradingOutpost/
├── pyproject.toml          # single config source
├── uv.lock
├── README.md
├── src/darkhorse/          # the importable package (src layout)
│   ├── config.py           # pydantic-settings
│   ├── harness.py          # multi-agent orchestration
│   ├── routines/           # 5 scheduled + 1 monthly
│   ├── tools/              # alpaca, data, news, snaptrade
│   ├── risk/               # validate_order, sizing, drawdown, kill_switch, wind_down
│   ├── learning/           # distillation, decay, calibration, anti-pattern, reasoning audit
│   ├── evaluation/         # backtest, adversarial
│   ├── memory/             # readers, mirror builder
│   ├── schemas/            # pydantic models for every shape
│   └── web/                # FastAPI dashboard
├── tests/
│   ├── unit/
│   ├── property/
│   ├── cassettes/          # recorded LLM I/O for harness regression
│   └── adversarial/
├── prompts/                # markdown system + role prompts (not Python)
├── doctrine/               # markdown rules (not Python)
├── memory/                 # gitignored, runtime
├── data/                   # gitignored, runtime
├── plans/                  # this directory
│   ├── architecture.md     # this file
│   ├── decisions/          # ADRs 0000-NNNN
│   └── ...
├── RESEARCH/               # research record
└── KILLSWITCH              # file-flag
```

## 8. Deployment Topology

```
                  Aaron's phone / laptop
                          │
                          │  Tailscale
                          ▼
                  ┌──────────────────┐
                  │   tailnet        │
                  └────────┬─────────┘
                           │
                           ▼
   ┌────────────────────────────────────────────────────────────┐
   │  Hetzner CX22, Ashburn US (Ubuntu 24.04 LTS)               │
   │                                                             │
   │  ┌──────────────────┐    ┌──────────────────┐              │
   │  │ systemd timers    │ →  │ python -m darkh- │              │
   │  │ (5 routines/day)  │    │ orse.routines... │              │
   │  └──────────────────┘    └────────┬─────────┘              │
   │                                    │                        │
   │                                    ▼                        │
   │  ┌──────────────────────────────────────────────┐           │
   │  │ /opt/darkhorse        — code (read-only)     │           │
   │  │ /etc/darkhorse/.env   — secrets (mode 600)   │           │
   │  │ /var/lib/darkhorse/   — runtime data         │           │
   │  │ /var/log/darkhorse/   — logs (systemd)       │           │
   │  └──────────────────────────────────────────────┘           │
   │                                                             │
   │  ┌──────────────────┐    ┌──────────────────┐              │
   │  │ uvicorn          │ ←  │ nginx (or Caddy)  │ ← Tailscale  │
   │  │ darkhorse.web    │    │ TLS, /healthz,    │   interface  │
   │  └──────────────────┘    │ static, prox      │              │
   │                          └──────────────────┘              │
   │                                                             │
   │  ┌──────────────────┐                                       │
   │  │ daily cron:      │  ──→  Backblaze B2 (age-encrypted)   │
   │  │ tar+age+upload   │                                       │
   │  └──────────────────┘                                       │
   └────────────────────────────────────────────────────────────┘
                           │
                           ▼ (egress)
   ┌────────────────────────────────────────────────────────────┐
   │   External services (over public internet)                  │
   │   - Anthropic API                                           │
   │   - Alpaca API (live + paper)                               │
   │   - Perplexity Sonar API                                    │
   │   - Tavily, Finnhub                                         │
   │   - SnapTrade (Fidelity read-only)                          │
   │   - Discord webhook                                         │
   │   - GitHub (manual deploy via SSH/Tailscale)                │
   └────────────────────────────────────────────────────────────┘

   Independent watchers:
   ┌──────────────────────┐    ┌──────────────────────┐
   │ Cloudflare Worker    │    │ Mac launchd job      │
   │ pings /healthz q5min │    │ pings /healthz q30min│
   │ → Discord on failure │    │ → Discord on failure │
   └──────────────────────┘    └──────────────────────┘
```

## 9. Security Posture

- **Tailscale-only access.** Dashboard binds to the tailnet interface; no public exposure.
- **SSH disabled on public interfaces.** Only Tailscale-routed SSH allowed.
- **Secrets in `/etc/darkhorse/.env` (mode 600, root-owned).** Never in source control. Pre-commit hook enforces.
- **Service runs as a dedicated non-root user** with read-only access to code, write access to `/var/lib/darkhorse/`.
- **The agent has no funding capability.** It cannot move money between accounts, cannot deposit/withdraw. Restricted to order placement/cancellation/query within a pre-funded account.
- **The kill-switch is a file plus an env var.** Either is sufficient; both can be flipped without redeploy.
- **HTTPS everywhere.** Let's Encrypt for any public name; Tailscale TLS for tailnet hostnames.
- **Backups are encrypted with `age`.** Backblaze B2 keys are read-only-write-only (cannot delete prior backups).
- **No outbound trust assumptions.** All news content is Unicode-NFKC normalized; all tickers validated against the Alpaca asset list before validate_order accepts them.

ADR references: `0005-hosting.md`, `0011-observability.md`, `0012-configuration-and-secrets.md`. Risk references: `riskMitigation.md` §3 R5 (deception), R10 (adversarial), R11 (idempotency), R14 (data residency).

## 10. Extensibility Hooks

Where to plug in new things without re-architecting:

### New tool

1. Create `src/darkhorse/tools/newtool.py`.
2. Define `NewToolInput`, `NewToolOutput` pydantic models.
3. Register in the harness tool list with `strict: true`.
4. Add unit tests in `tests/unit/tools/`.
5. Add adversarial fixtures in `tests/adversarial/`.

### New sleeve

1. Add `<new_sleeve>` to the `Sleeve` enum.
2. Add `<new_sleeve>_*` parameters to `Settings`.
3. Add `doctrine/<new_sleeve>_sleeve.md` and `prompts/system_<new_sleeve>.md`.
4. Configure `validate_order` rules for the new sleeve.
5. Memory paths automatically pick up new sleeves via configuration.

### New agent role

1. Add the prompt in `prompts/<role>.md`.
2. Add the role to harness orchestration (e.g., a "skeptic" sub-agent in addition to bull/bear).
3. Update Decision schema if the new role's output shape requires it.
4. Cassette tests update.

### New model tier or model swap

1. Update `Settings` model defaults (e.g., `risk_manager_model: str = "claude-opus-4-8"`).
2. Run a 2-week paper-shadow window with the new model.
3. ADR-NNNN updates `0002-tiered-model-strategy.md`.

### New harness pattern (e.g., from a competitive-landscape adoption)

1. Build the variant in a feature branch.
2. Run side-by-side paper-shadow comparison for ≥ 2 weeks.
3. If the variant wins on the registered hypothesis, merge.
4. The harness's interface (input: state; output: Decision JSON via validate_order) is what's stable; the internals can change.

### New scheduling (e.g., event-driven trigger)

1. Implement the trigger in `src/darkhorse/triggers/`.
2. Add a systemd `Path=` unit or a Cloudflare Worker that POSTs to a private endpoint.
3. The endpoint enqueues a routine; the existing harness handles it.

## 11. Anti-Architecture (What We Explicitly Don't Do)

- **No microservices.** One Python process running multiple systemd services on one VPS. Splitting is harm not help at this scale.
- **No orchestration framework (LangGraph, CrewAI, etc.).** Custom thin harness for v1. Re-evaluate annually. (`0008`)
- **No MCP servers as primary tool integration.** Native SDK tools. Re-evaluate as MCP matures. (`0001`)
- **No vector database.** Lessons are read into context wholesale via prompt caching, not retrieved by similarity.
- **No NoSQL.** SQLite mirror is sufficient; if it isn't, Postgres beats Mongo at our shape.
- **No SPA frontend.** Single-user dashboard; HTMX is correct. (`0004`)
- **No container orchestration.** Native systemd. (`0006`)
- **No auto-deploy on merge.** Manual deploy via SSH; Aaron is the gate. (`0010`)
- **No live LLM tests in CI.** Cassettes for orchestration; paper-shadow for behavior. (`0009`)
- **No auto-merging doctrine PRs.** Aaron disposes. (`learningSystem.md`)
- **No fully autonomous mode.** The agent runs on a leash that Aaron periodically tightens.

## 12. ADR Index

All ADRs in `plans/decisions/`. Each is independently readable.

| # | Title | Status | Re-check |
|---|---|---|---|
| 0001 | Tool Integration — Anthropic SDK Native (defer MCP) | accepted | 2026-11-09 |
| 0002 | Tiered Model Strategy | accepted | 2026-08-09 |
| 0003 | Memory Architecture — JSONL + SQLite Mirror | accepted | 2026-11-09 |
| 0004 | Frontend Stack — FastAPI + HTMX + Alpine + Tailwind + DaisyUI | accepted | 2026-11-09 |
| 0005 | Hosting — Hetzner CX22 (Ashburn US) | accepted | 2026-11-09 |
| 0006 | Scheduler — systemd Timers | accepted | 2026-11-09 |
| 0007 | Python Project Layout & Tooling | accepted | 2026-11-09 |
| 0008 | Agentic Harness Pattern — Custom Thin Wrapper | accepted | 2026-08-09 |
| 0009 | Testing Strategy | accepted | 2026-11-09 |
| 0010 | Deployment Pipeline | accepted | 2026-11-09 |
| 0011 | Observability | accepted | 2026-11-09 |
| 0012 | Configuration & Secrets | accepted | 2026-11-09 |

Re-check dates collapse to 2026-08-09 (quarterly model + harness review) and 2026-11-09 (6-month broader re-check).

## 13. Open Architectural Questions

These are tracked here so they don't get lost. Each will resolve into an ADR when decided.

| # | Question | Earliest decision date | Owner |
|---|---|---|---|
| AQ-001 | When (if ever) does MCP integration become net-positive? | Phase 6+ | Aaron, informed by monthly competitive review |
| AQ-002 | Does the harness need a shared "session" abstraction once we have >5 roles? | Phase 6+ | Aaron, informed by harness LOC |
| AQ-003 | Polars for calibration analysis — adopt now or when journal hits 1M rows? | Phase 6 | Aaron |
| AQ-004 | Cloudflare Access vs Tailscale-only at month 6 — do we want browser-anywhere? | Phase 6 | Aaron |
| AQ-005 | When does SQLite stop being enough? Postgres trigger threshold? | Phase 10+ | Aaron |
| AQ-006 | Does the Satellite sleeve need a dedicated harness variant (more concentrated, shorter horizon)? | Phase 9 | Aaron |
| AQ-007 | Auto-deploy on merge to main — at what cadence does manual become the bottleneck? | Phase 10+ | Aaron |
| AQ-008 | Cassette format and refresh tooling — JSON files vs custom format? Iterate after 50 cassettes exist. | Phase 5 | Aaron |
| AQ-009 | Anthropic Skills / first-party Agent SDK — when does it subsume our harness? | Quarterly review | Aaron |
| AQ-010 | Multi-provider fallback (Anthropic → OpenAI on outage)? Worth the prompt-portability cost? | Phase 10+ | Aaron |

These are checked at each quarterly retrospective. Open questions that haven't been touched in 6 months are either answered, retired, or escalated to "decide now."

---

## Reading order for a new contributor

1. `initialPlan.md` — what we're building
2. This file (`architecture.md`) — how it's built
3. The ADRs whose subjects you're touching (each is ~200 lines)
4. The relevant `RESEARCH/architecture/*.md` notes
5. The relevant `src/darkhorse/<module>/` code

If those five give you a coherent mental model in <2 hours, the architecture is healthy. If they don't, file an issue and we fix the docs.
