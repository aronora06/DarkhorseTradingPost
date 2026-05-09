# Darkhorse Trading Outpost — Development Phase Checklist

This is the master executable to-do list. Read [`initialPlan.md`](./initialPlan.md) for architectural rationale and [`riskMitigation.md`](./riskMitigation.md) for the cost/risk playbook. This file is what we *do*; those files are what we *decided*.

## Operating Principle: Real-Money From Day 1 of Trading

Phases 0–3 are pre-trading and pre-cost: no agent runs, no tokens burn, no subscriptions accruing. From Phase 4 onward, the agent operates against **real money** in the live Alpaca account. We do not run an extended paper-only phase — every dollar of operational cost should produce real signal.

What we do instead:
- **Capital ramps within the live account** from $50 → $900 Core, gated by observed behavior (Phase 4 → Phase 8).
- **A paper-shadow account runs concurrently** throughout, using the same prompts and routines, as a free divergence detector.
- **Architectural changes (new prompt, new model, new tool) run in paper-shadow for ≥ 2 weeks** before being merged into the live path. The live system continues unchanged during validation windows.

## How to Use This Document

- Phases run sequentially; some sub-tasks parallelize where called out.
- Every phase has explicit **exit criteria** — we don't move on until they're met.
- Boxes get checked as work completes. Date the check next to it: `[x] (2026-05-12)`.
- "Codify" means *write down or implement in code*, not just "research and decide."
- Aaron is the human-in-the-loop; anywhere it says "Aaron approves" or "PR-merged by Aaron," that gate is non-negotiable.
- If a check needs to be unchecked, leave a strikethrough note: `[ ] ~~previously done, undone because X~~`.

---

## Phase 0 — Project Steering & Documentation

**Goal:** Lock the steering documents in place before any other work. **No costs accruing.**

- [x] (2026-05-08) `plans/initialPlan.md` written and reviewed by Aaron
- [x] (2026-05-08) `plans/riskMitigation.md` written and reviewed by Aaron
- [x] (2026-05-08) `plans/devPhaseChecklist.md` (this file) written and reviewed by Aaron
- [x] (2026-05-08) `plans/researchCharter.md` written and reviewed by Aaron
- [x] (2026-05-08) `plans/learningSystem.md` written and reviewed by Aaron
- [x] (2026-05-08) `plans/frontendAndHosting.md` written and reviewed by Aaron
- [x] (2026-05-08) `plans/dataSchema.md` written and reviewed by Aaron
- [x] (2026-05-08) `plans/glossary.md` written and reviewed by Aaron
- [x] (2026-05-08) `suggestedNextSteps.md` written and reviewed by Aaron (lives at root level)
- [x] (2026-05-08) `README.md` at project root, indexing all the above
- [x] (2026-05-08) `plans/decisions/0000-template.md` ADR template committed
- [x] (2026-05-08) `RESEARCH/` directory structure created (papers/, hypotheses/, monthly/, quarterly/, annual/, competitive_landscape/, practitioner_dossiers/)
- [x] (2026-05-08) `git init`, push to private GitHub repo (private; direct pushes to `main` permitted — agent-proposed doctrine changes still flow through draft PRs per `learningSystem.md`)
- [x] (2026-05-08) `.gitignore` covers `.env`, `secrets/`, `__pycache__`, etc.

**Exit criteria:** All steering docs exist on `main`, reviewed by Aaron, with no open questions blocking Phase 1.

---

## Phase 1 — Risk Mitigation Research & Codification

**Goal:** Translate `riskMitigation.md` from prose into testable specifications and concrete artifacts. **No costs accruing.**

**Status: COMPLETE — Aaron Parker signed off doctrine + Markdown test specs on 2026-05-09.**

### 1.1 Research

- [x] (2026-05-09) Read at least 2 source papers per major risk: FINSABER (look-ahead), TradeTrap (perturbation cascades), Apollo Research deception, adversarial-news (Unicode homoglyphs), FinMem (memory architecture) — see `RESEARCH/papers/` one-pagers dated batch **2026-05-09**
- [x] (2026-05-09) Notes filed under `RESEARCH/papers/` with one-page summary per paper (major-risk seed set + TradingAgents framework summary)
- [x] (2026-05-09) Practitioner consensus dossier on drawdown halts (Kaufman, Tharp, Clenow, Robot Wealth) — `RESEARCH/practitioner_dossiers/drawdown_halts.md`
- [x] (2026-05-09) Practitioner consensus dossier on universe selection at small account sizes — `RESEARCH/practitioner_dossiers/universe_small_account.md`
- [x] (2026-05-09) Supplemental dossier — execution sizing & PDT framing — `RESEARCH/practitioner_dossiers/sizing_and_pdt.md`
- [x] (2026-05-09) Compile a list of every adversarial input vector we'll test against — `RESEARCH/adversarial_vectors.md`

### 1.2 Codified doctrine

- [x] (2026-05-09) `doctrine/risk_policy.md` — daily loss kill, drawdown halt, uncle point thresholds (numbers from initialPlan §8) with the *reason* for each number
- [x] (2026-05-09) `doctrine/core_sleeve.md` — Core mandate, sizing rules, no-fly list
- [x] (2026-05-09) `doctrine/satellite_sleeve.md` — Satellite mandate, sizing rules, allowed asset classes
- [x] (2026-05-09) `doctrine/universe.md` — S&P 500 + filters for Core, S&P 500 + extension list for Satellite
- [x] (2026-05-09) `doctrine/satellite_watchlist.md` — initial 25-name extension list (Aaron drafts; agent will challenge once it exists)
- [x] (2026-05-09) `doctrine/news_sources.md` — whitelisted sources + how to handle uncited claims
- [x] (2026-05-09) `doctrine/style_guide.md` — JSON shape for decisions, journal entry format, doctrine version pinning rules
- [x] (2026-05-09) `doctrine/anti_patterns.md` — initial anti-pattern catalog seeded from research papers

### 1.3 Test specifications

- [x] (2026-05-09) `tests/specs/validate_order.md` — every rule with passing/failing examples
- [x] (2026-05-09) `tests/specs/kill_switch.md`
- [x] (2026-05-09) `tests/specs/drawdown.md`
- [x] (2026-05-09) `tests/specs/sizing.md`
- [x] (2026-05-09) `tests/specs/idempotency.md`
- [x] (2026-05-09) `tests/specs/adversarial.md`

### 1.4 Human gate — Aaron review (exit requirement)

- [x] (2026-05-09) Aaron reviewed and approved the **`doctrine/`** bundle (see `doctrine/README.md` sign-off line)
- [x] (2026-05-09) Aaron reviewed and approved all files under **`tests/specs/`**

**Exit criteria:** All doctrine files exist, all test specs exist, Aaron has reviewed both — **SATISFIED (2026-05-09)**. No code in Phase 1 — correct.

**Operational follow-ups (not Phase 1 blockers):**

- Populate `doctrine/satellite_watchlist.md` with real symbols + theses **before Satellite sleeve goes live** (Phase 9 path); template-only is acceptable through Phase 3–8.
- Steering **open questions** in `plans/initialPlan.md` §9 (options policy, tax-lot detail v2) remain for future doctrine PRs — they do not reopen Phase 1.

---

## Phase 2 — Architecture Research & Codification

**Goal:** Lock the architecture before writing modules. **No costs accruing.**

### 2.1 Research

- [x] (2026-05-09) High-level review of agentic-LLM frameworks (LangGraph, OpenAI Agents SDK, CrewAI, AutoGen, Pydantic AI, Mastra) and rationale for custom thin harness — `RESEARCH/architecture/agentic_harness_patterns.md`
- [x] (2026-05-09) Python project tooling validation (uv, Ruff, mypy, pytest) — `RESEARCH/architecture/python_project_tooling_2026.md`
- [x] (2026-05-09) Hosting comparison (Linode vs Hetzner Ashburn vs PaaS) — `RESEARCH/architecture/hosting_comparison.md`
- [x] (2026-05-09) Testing strategies for LLM-driven systems (assertllm, agentpytest, cassette pattern) — `RESEARCH/architecture/testing_ai_agents.md`
- [x] (2026-05-09) Anthropic SDK features (1h prompt cache, structured outputs, strict tool use, tool loop) — `RESEARCH/architecture/anthropic_sdk_features.md`
- [x] (2026-05-09) Frontend dashboard stack (FastAPI + HTMX + Alpine + Tailwind + DaisyUI) — `RESEARCH/architecture/frontend_dashboard_stack.md`
- [x] (2026-05-09) Deeper read: TradingAgents repo + paper, debate-flow design choices — `RESEARCH/architecture/multi_agent_debate.md` (see also `RESEARCH/papers/2024-xiao-tradingagents.md`)
- [ ] Deeper read: Anthropic structured outputs (with a tiny prototype) — `RESEARCH/architecture/structured_outputs.md`
- [ ] Deeper read: Anthropic prompt caching, calculate expected cache hit rates — `RESEARCH/architecture/prompt_caching.md`
- [ ] Read Alpaca official MCP server docs (validates ADR-0001 deferral) — feeds re-check
- [ ] Read Claude Code routines docs (for backup-scheduler use)
- [x] (2026-05-09) Read at least 3 production agent post-mortems, document common failure modes — `RESEARCH/architecture/agent_failure_modes.md` §Documented operator post-mortems (TrackAI 2024-10-15; ForgeCode RCA 2025-07-12; Claude Code gh#3043 2025-07-06)

### 2.2 Architecture artifacts

- [x] (2026-05-09) `docs/architecture.md` populated — component diagram, data flow, sequence diagrams for each routine, tool contracts (moved from `plans/architecture.md` to `docs/architecture.md` to separate active code reference from steering plans)
- [x] (2026-05-08) `plans/dataSchema.md` finalized
- [x] (2026-05-09) Tool contract definitions: Python type stubs in `src/darkhorse/tools/_contracts.py` for every planned deterministic tool (Phase 3 deliverable)
- [x] (2026-05-09) Prompt skeletons: empty-but-structured `prompts/system_core.md`, `system_satellite.md`, `researcher.md`, `bull_analyst.md`, `bear_analyst.md`, `risk_manager.md`, `reflection.md`, `monthly_competitive_review.md` (Phase 3 deliverable)
- [x] (2026-05-09) `plans/decisions/0001-tool-integration-anthropic-sdk-vs-mcp.md` (replaces planned `0001-alpaca-mcp-vs-wrapper.md`)
- [x] (2026-05-09) `plans/decisions/0002-tiered-model-strategy.md`
- [x] (2026-05-09) `plans/decisions/0003-memory-architecture.md`
- [x] (2026-05-09) `plans/decisions/0004-frontend-stack.md`
- [x] (2026-05-09) `plans/decisions/0005-hosting.md`
- [x] (2026-05-09) `plans/decisions/0006-scheduler.md` (was planned as `0006-scheduler-systemd-vs-claude-code-routines.md`)
- [x] (2026-05-09) `plans/decisions/0007-python-project-layout.md`
- [x] (2026-05-09) `plans/decisions/0008-agentic-harness-pattern.md`
- [x] (2026-05-09) `plans/decisions/0009-testing-strategy.md`
- [x] (2026-05-09) `plans/decisions/0010-deployment-pipeline.md`
- [x] (2026-05-09) `plans/decisions/0011-observability.md`
- [x] (2026-05-09) `plans/decisions/0012-configuration-and-secrets.md`

**Exit criteria:** Architecture docs reviewed by Aaron, ADRs filed (✓), prompt skeletons exist (Phase 3), tool contracts are typed (Phase 3). Phase 2 research complete enough to begin Phase 3 build; deeper paper-reads continue in parallel and feed back into ADR re-checks.

---

## Phase 3 — Foundations Build + Hosting

**Goal:** Implement the load-bearing risk modules and stand up the production environment. **No agent code, no LLM calls.** This phase ends with everything in place to run the agent — but the agent has not yet run.

### 3.1 Repo scaffolding

- [x] (2026-05-09) Python project initialized per ADR-0007: `pyproject.toml` (single config source), `uv` env management, `ruff`, `pytest`, `mypy --strict`, Hypothesis, pydantic v2, pydantic-settings, structlog, httpx, tenacity
- [x] (2026-05-09) `src/darkhorse/` package layout per ADR-0007 §"Repository layout"
- [x] (2026-05-09) Pre-commit hooks: ruff, mypy, full pytest, gitleaks (no-secrets check)
- [x] (2026-05-09) CI: GitHub Actions per ADR-0010 — ruff, mypy, pytest, coverage report on every PR
- [x] (2026-05-09) `.env.example` committed with every variable documented per ADR-0012

### 3.2 Risk modules

- [x] (2026-05-09) `src/darkhorse/risk/sizing.py` with full unit tests
- [x] (2026-05-09) `src/darkhorse/risk/drawdown.py` — HWM tracking, halt firing, uncle-point firing — tests cover the recovery-without-HWM-reset rule
- [x] (2026-05-09) `src/darkhorse/risk/kill_switch.py` — checks `KILLSWITCH` file, env var, optional remote endpoint
- [x] (2026-05-09) `src/darkhorse/risk/validate_order.py` — every rule from the spec; bypass attempts fail loudly
- [x] (2026-05-09) `src/darkhorse/risk/wind_down.py` — implements the `riskMitigation.md` §6 wind-down rule (so it can fire from day 1 of live)
- [x] (2026-05-09) Property-based tests using Hypothesis on validate_order rules (per ADR-0009)

### 3.3 Core utilities

- [x] (2026-05-09) `src/darkhorse/journal.py` — append-only JSONL writer, schema-validated, daily file rotation
- [x] (2026-05-09) `src/darkhorse/calibration.py` — confidence vs realized P&L tracker
- [x] (2026-05-09) `src/darkhorse/idempotency.py` — deterministic `client_order_id` derivation
- [x] (2026-05-09) `src/darkhorse/notify.py` — Discord webhook wrapper with retry + dead-letter (per ADR-0011)
- [x] (2026-05-09) `src/darkhorse/config.py` — pydantic-settings loader (per ADR-0012)
- [x] (2026-05-09) `src/darkhorse/audit.py` — append-only audit log writer
- [x] (2026-05-09) `src/darkhorse/schemas/` — pydantic models for shipped JSONL shapes (decision, audit, calibration); extend as new persisted artifacts ship

### 3.4 Tools (deterministic only — no LLM)

- [x] (2026-05-09) `src/darkhorse/tools/_contracts.py` — pydantic input/output models for every planned deterministic tool, `strict: true`-ready
- [x] (2026-05-09) `src/darkhorse/tools/alpaca.py` — connect to live + paper, fetch account, fetch positions, place order, cancel order. Every order routes through `validate_order()`. Unit tests use mocked HTTP; optional paper sandbox smoke test stays env-gated and skipped in CI.
- [x] (2026-05-09) `src/darkhorse/tools/data.py` — Finnhub quotes + bars, Yahoo Finance-compatible fallback. Cache results within a routine.
- [x] (2026-05-09) `src/darkhorse/tools/news.py` — Sonar Finance Search wrapper, Tavily fallback. Unicode-NFKC normalize all returned text. Validate ticker mentions against the asset list.
- [ ] `src/darkhorse/tools/snaptrade.py` — read-only Fidelity holdings (deferred until SnapTrade-Fidelity link is approved)
- [x] (2026-05-09) Asset-list refresher: weekly job pulls Alpaca's `assets` endpoint, writes `data/assets/YYYY-MM-DD.json`
- [x] (2026-05-09) `src/darkhorse/routines/market_open.py` dry-run composition skeleton: loads settings, kill-switch state, asset whitelist, account, positions, and builds `ValidationContext`; no LLM calls and no broker submission.
- [x] (2026-05-09) Cassette/replay scaffolding: `CassetteTransport` (httpx-based record/replay), record CLI, seed cassette, 13 tests. Ready for production harness.
- [x] (2026-05-09) Drawdown/wind-down state wired into routine composition: `DrawdownState`, `core_drawdown_flags()`, `satellite_drawdown_flags()`, `soft_wind_down_core_to_spy()`, daily loss halt, trades-today-in-sleeve all flow into `ValidationContext`.
- [x] (2026-05-09) Journal/audit envelopes: `build_routine_start_audit()`, `build_no_trade_decision()` emit audit/journal records from composition on every run.
- [x] (2026-05-09) Phase 4 $50 Core deployment cap wired end-to-end: `phase_core_deploy_cap_usd` in Settings/TOML → `max_core_deploy_usd` on `ValidationContext` → `R-V01-PHASE-CAP` in `validate_order`.
- [x] (2026-05-09) API connections verified: Anthropic, Alpaca paper, Perplexity Sonar, Tavily, Finnhub, Discord — all keys in `.env`, smoke tests at `tests/smoke/test_api_connections.py`.
- [x] (2026-05-09) `anthropic` SDK added as runtime dependency (v0.100+).

### 3.5 Hosting & infrastructure

- [ ] Hetzner Cloud CX22 in Ashburn US provisioned (per ADR-0005), Ubuntu 24.04 LTS
- [ ] Tailscale installed; SSH disabled on public interfaces
- [ ] systemd skeleton for the scheduler, the FastAPI app, the watchdogs
- [ ] nginx/Caddy reverse proxy configured
- [ ] HTTPS via Let's Encrypt or Tailscale TLS
- [ ] Daily backup job to Backblaze B2 (encrypted with `age`)
- [ ] Cloudflare Worker (free) heartbeat watcher pinging `/healthz`
- [ ] Local launchd job on Aaron's Mac as a redundant heartbeat watcher
- [ ] `.env` deployed to `/etc/darkhorse/`, mode 600, root-owned

### 3.6 Account funding

- [ ] **Alpaca live account funded with $1,000.** Live account setup is in progress, awaiting authorization. This does **not** block Phase 4a (paper trading). Real money deployment happens in Phase 4b once the live account is approved and paper trading has proven clean.

**Exit criteria (updated for paper-first approach):** `pytest` green, `mypy --strict` clean, `validate_order` rejects 100% of property-based adversarial inputs. Discord webhook fires test message. Alpaca paper account connects successfully. All API keys verified via smoke tests. Phase 3.5 hosting can proceed in parallel.

---

## Phase 4a — First Paper Trade (Agent Proving Ground)

**Goal:** Get the agent making real decisions against the Alpaca paper account. Validate the entire pipeline end-to-end before any real money touches it. This phase proceeds immediately — it does not require the Alpaca live account.

- [x] (2026-05-09) `src/darkhorse/harness.py` — production Anthropic loop: researcher (Sonnet 4.6) with tool loop, risk-manager (Opus 4.7) with structured JSON output, prompt caching (1h TTL), per-call cost telemetry, tenacity retry, structlog. 784 lines.
- [x] (2026-05-09) `prompts/system_core.md` — full doctrine injection, decision JSON schema, 30-day base rate, NO_TRADE default, hard boundaries, Phase 4 constraints, anti-pattern catalog reference.
- [x] (2026-05-09) `prompts/researcher.md` — tool usage protocol, output structure (account/market/durable/headlines/gaps/tools-used), data quality requirements.
- [x] (2026-05-09) `prompts/risk_manager.md` — decision JSON schema with field rules, confidence calibration (0.70), reasoning checklist, Python-validates hard boundary.
- [x] (2026-05-09) `src/darkhorse/routines/market_open.py` — end-to-end pipeline: compose → harness → confidence gate → validate_order → submit_order (Alpaca paper) → journal + audit + Discord notify. 159 tests, 88.85% coverage.
- [x] (2026-05-09) **$50 deployment cap wired into `validate_order`** via `R-V01-PHASE-CAP` and `phase_core_deploy_cap_usd` in Settings.
- [ ] Record initial cassettes from a live harness run (`uv run python -m darkhorse.testing.record market_open_initial`)
- [ ] First successful end-to-end paper run: agent fetches state, decides, validates, places paper order (or NO_TRADE) ≤ $50, journals
- [ ] Local scheduler (cron/launchd on Mac) fires `market_open.py` at 9:35 AM ET weekdays in paper mode
- [ ] Run for **5 trading days minimum** on paper. Aaron reads every journal entry.
- [ ] Daily Discord recap includes: paper decision, cost, any errors
- [ ] Anti-pattern catalog updated based on observations from those 5 days

**Exit criteria:** 5 clean paper trading days at $50 max deployed. Every decision reconstructable from the journal. Zero `validate_order` bypasses. Zero hallucinated tickers. Zero unintended day-trades. Token spend within budget. Discord daily recap fires reliably.

---

## Phase 4b — First Live Trade at Micro-Size

**Goal:** Once the Alpaca live account is approved/funded AND Phase 4a has proven clean, activate live trading at micro-size. This phase cannot begin until both conditions are met.

**Prerequisites:**
- Phase 4a exit criteria met (5 clean paper days)
- Alpaca live account approved, funded with $1,000, API keys in `.env`
- Live connectivity verified via `DARKHORSE_ALLOW_NETWORK_TESTS=1 uv run pytest tests/smoke/ -v`

- [ ] Switch `market_open.py` to live mode (`BrokerEnvironment.LIVE`)
- [ ] **Paper-shadow account runs in parallel.** Same routine fires against paper; results journaled to `memory/core/paper_shadow/journal/YYYY-MM-DD.jsonl`
- [ ] First successful end-to-end live run: agent fetches state, decides, validates, places live order (or NO_TRADE) ≤ $50, journals
- [ ] Run for **5 trading days minimum**. Aaron reads every journal entry and every paper-shadow entry.
- [ ] Daily Discord recap includes: live decision, paper-shadow decision, divergence flag if they disagree
- [ ] Anti-pattern catalog updated based on observations from those 5 days

**Exit criteria:** 5 clean live trading days at $50 max deployed. Every decision reconstructable from the journal. Zero `validate_order` bypasses. Zero hallucinated tickers. Zero unintended day-trades. Token spend within budget. Live-vs-paper-shadow divergences explained or zero. Discord daily recap fires reliably.

---

## Phase 5 — Multi-Agent Debate + Full Schedule (Still Micro-Size)

**Goal:** Full architecture per `initialPlan.md` §3.3. All five routines. Multi-agent debate. Tiered model strategy. **Capital deployment unchanged at $50** — debugging the architecture, not stretching the capital.

### 5.1 Multi-agent flow

- [ ] `prompts/researcher.md`, `bull_analyst.md`, `bear_analyst.md`, `risk_manager.md` written
- [ ] Multi-agent orchestration in `src/darkhorse/harness.py` — researcher → parallel bull/bear → risk-manager
- [ ] Risk-manager runs Opus 4.7; sub-agents run Sonnet 4.6
- [ ] Anthropic 1-hour prompt cache enabled on doctrine + journal context
- [ ] Structured outputs enabled on the risk-manager's decision JSON
- [ ] Cache hit-rate telemetry logged per routine; if <60% hit rate after 1 week, debug
- [ ] Side-by-side single-agent paper account continues alongside multi-agent live (RQ6 data collection starts here)

### 5.2 Full routine schedule

- [ ] `src/darkhorse/routines/pre_market.py` (8:30 AM ET)
- [ ] `src/darkhorse/routines/market_open.py` updated to use full debate flow (9:35 AM ET)
- [ ] `src/darkhorse/routines/midday_scan.py` (12:30 PM ET)
- [ ] `src/darkhorse/routines/end_of_day.py` (4:05 PM ET)
- [ ] `src/darkhorse/routines/weekly_review.py` (Fri 5:00 PM ET) — runs Haiku 4.5, compiles lessons, proposes doctrine PRs
- [ ] All five routines registered in systemd

### 5.3 Both sleeves operational, Satellite at $0

- [ ] Core running live at $50 max deployed, paper-shadow in parallel
- [ ] Satellite *configured* but with $0 deployment cap in `validate_order` (it observes, journals, but cannot trade yet)
- [ ] Separate journals per sleeve
- [ ] Sleeve-specific system prompts wired
- [ ] Cross-sleeve fund-transfer attempts rejected by `validate_order`

### 5.4 Calibration loop active

- [ ] Calibration log populated on every decision
- [ ] Weekly review reads journal, extracts patterns, writes lesson PRs
- [ ] Doctrine edit PRs auto-opened by the agent (via GitHub Actions)
- [ ] Aaron merges intentionally; auto-merge disabled

**Exit criteria:** 2 calendar weeks live with the full schedule. Live-vs-paper divergences zero or explained. Calibration data accumulating. Weekly review produces lessons Aaron found useful (subjective, must be yes). No drawdown-halt firing.

---

## Phase 6 — Learning System + Full Dashboard

**Goal:** Stand up the meta-learning machinery and the dashboard. **Capital still $50.**

### 6.1 Learning system

- [ ] `src/darkhorse/learning/distillation.py` — lesson distillation
- [ ] `src/darkhorse/learning/decay.py` — lesson sunset/re-validation policy
- [ ] `src/darkhorse/learning/calibration_analysis.py` — calibration drift detection
- [ ] `src/darkhorse/learning/anti_pattern_extraction.py` — automated post-mortem trigger
- [ ] `src/darkhorse/learning/reasoning_audit.py` — quarterly Haiku-driven critique pass
- [ ] `src/darkhorse/routines/monthly_competitive_review.py` — agentic web review per `learningSystem.md` §5
- [ ] First scheduled monthly competitive-landscape review fires on schedule
- [ ] First quarterly retrospective routine wired (will fire at quarter-end)
- [ ] Hypothesis registry online: `RESEARCH/hypotheses/` with at least the initial hypotheses from `researchCharter.md` filed

### 6.2 Dashboard

- [ ] FastAPI app in `src/darkhorse/web/app.py` with read endpoints per `frontendAndHosting.md`
- [ ] Write endpoints: KILLSWITCH toggle, doctrine-PR approval/rejection
- [ ] Tailscale-only auth wired
- [ ] Dashboard pages: Overview, Portfolio Detail, Performance, Calibration, Decisions Feed, Lessons & Doctrine, Anti-Patterns, Costs, System Health
- [ ] Aaron can open the dashboard from his phone via Tailscale
- [ ] Backups confirmed restorable from a fresh VPS (quarterly drill scheduled)

**Exit criteria:** Learning system has produced at least one merged doctrine change traceable to a calibration-drift detection or competitive-landscape adoption. First monthly competitive-landscape review filed. Dashboard usable by Aaron from phone. Backup restore drill passed.

---

## Phase 7 — Backtest + Adversarial Gate

**Goal:** Subject the system to FINSABER-style backtesting and an adversarial test suite. Outcome **gates** the size ramp in Phase 8.

- [ ] `src/darkhorse/evaluation/backtest_finsaber.py` — walk-forward, post-cutoff data only, full universe including delistings
- [ ] Baseline: SPY buy-and-hold over the same windows
- [ ] Backtest produces a written report — Sharpe vs SPY, max DD vs SPY, drawdown profile, trades per period, calibration on backtested data
- [ ] Adversarial suite in `src/darkhorse/evaluation/adversarial.py` — Unicode homoglyph tickers, fabricated headlines with hidden-text injection, stale quotes, bad tool returns
- [ ] Adversarial pass rate must be 100% — `validate_order` blocks every malicious order
- [ ] Stress windows tested explicitly: most recent post-cutoff drawdown period, sideways period, bull period
- [ ] Cost-per-decision measured against the budget; project full-year cost

**Exit criteria:** Risk-adjusted edge non-negative vs SPY on out-of-sample backtest. Adversarial 100%. Cost projection within budget. RQ6 side-by-side paper data is accumulating but is not expected to have its full 60-trading-day window yet. **Aaron makes an explicit go/no-go call on the size ramp.**

---

## Phase 8 — Core Ramp

**Goal:** Deploy more capital incrementally. Each step is a real-money increase.

- [ ] Live deployment $50 → **$200** (one-step ramp), hold ≥ 1 calendar week
- [ ] Live-vs-paper-shadow divergence still zero or explained
- [ ] No halt firings during the week
- [ ] Live deployment $200 → **$500**, hold ≥ 1 calendar week
- [ ] Live deployment $500 → **$900** (full Core), hold ≥ 1 calendar week
- [ ] Drawdown thresholds re-checked at full size — abort and revert if anything looks wrong
- [ ] Daily Discord recap continues to include live-vs-paper divergence count

**Exit criteria:** Core sleeve at full $900 deployment for ≥ 1 calendar week without incident. No unexplained live-vs-paper divergences. Calibration consistent with paper-shadow.

---

## Phase 9 — Satellite Activation

**Goal:** Bring Satellite online at full size.

- [ ] Core has been at full $900 deployment for ≥ 30 calendar days without incident
- [ ] Satellite extension list reviewed and refreshed before activation
- [ ] `validate_order` Satellite cap raised from $0 to $100 (full Satellite)
- [ ] Satellite goes live at $100 (it's small enough that the gradual ramp doesn't add value)
- [ ] First Satellite-specific weekly review confirms separate journal, separate lessons, separate calibration

**Exit criteria:** Both sleeves live at intended size. ≥ 30 calendar days each at full size before considering this phase complete and moving to Phase 10.

---

## Phase 10 — Continuous Iteration & Research Output

**Goal:** Operate, learn, publish. This phase has no end date — it is the steady state.

### Recurring rituals

- [ ] **Daily:** Discord recap reviewed by Aaron (under 2 minutes)
- [ ] **Weekly:** doctrine PR queue reviewed; merge or reject with reasoning
- [ ] **Monthly:** monthly retrospective written to `RESEARCH/monthly/YYYY-MM.md`; competitive-landscape review fires; cost review; calibration drift check
- [ ] **Quarterly:** quarterly retrospective; full FINSABER re-backtest; regime check; model-version review (is Sonnet 4.7 worth swapping in?); adversarial re-test; reasoning-pattern audit
- [ ] **Annual (month 12):** annual report written, designed publication-ready per `researchCharter.md`. Continue / wind-down decision.

### Year-1 publication readiness

- [ ] All artifacts from `researchCharter.md` "Publication Readiness" table being collected continuously, not retrofitted
- [ ] By month 6: review whether the data trajectory supports a credible publication; if not, intervene early
- [ ] By month 11: anonymization plan confirmed; Aaron decides on identity disclosure
- [ ] By month 12: annual report draft circulated; publication target chosen (arXiv preprint, optional workshop)

### Wind-down readiness

- [ ] `riskMitigation.md` §6 wind-down rule active and tested
- [ ] If/when wind-down fires: Core converts to SPY, Satellite stays as sandbox, retrospective written

---

## Cross-Cutting Concerns (apply everywhere)

These are not phase-bound; they apply continuously and should be checked during code review.

- [ ] No new doctrine rule lands without a falsification criterion
- [ ] No new tool lands without a unit test that proves `validate_order` still catches bad outputs from it
- [ ] No new prompt change lands without a paper-shadow observation period of ≥ 2 weeks
- [ ] No new model swap lands without a side-by-side paper-shadow comparison
- [ ] No memory file grows unbounded — every memory artifact has a distillation/sunset policy
- [ ] No secret in source control — verified by pre-commit hook
- [ ] No silent failures — every error path logs to Discord and to the journal
- [ ] No live-vs-paper-shadow divergence ignored — every divergence either gets a written explanation or triggers an investigation
- [ ] Every artifact format is publication-anonymizable from day 1 (no retrofitting of dollar amounts to percentages at month 11)
