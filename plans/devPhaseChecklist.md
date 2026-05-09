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
- [ ] Tool contract definitions: Python type stubs in `src/darkhorse/tools/_contracts.py` for every tool (Phase 3 deliverable)
- [ ] Prompt skeletons: empty-but-structured `prompts/system_core.md`, `system_satellite.md`, `researcher.md`, `bull_analyst.md`, `bear_analyst.md`, `risk_manager.md`, `reflection.md`, `monthly_competitive_review.md` (Phase 3 deliverable)
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

- [ ] Python project initialized per ADR-0007: `pyproject.toml` (single config source), `uv` env management, `ruff`, `pytest`, `mypy --strict`, Hypothesis, pydantic v2, pydantic-settings, structlog, httpx, tenacity
- [ ] `src/darkhorse/` package layout per ADR-0007 §"Repository layout"
- [ ] Pre-commit hooks: ruff, mypy, pytest-on-changed-files, gitleaks (no-secrets check)
- [ ] CI: GitHub Actions per ADR-0010 — ruff, mypy, pytest, coverage report on every PR
- [ ] `.env.example` committed with every variable documented per ADR-0012

### 3.2 Risk modules

- [ ] `src/darkhorse/risk/sizing.py` with full unit tests
- [ ] `src/darkhorse/risk/drawdown.py` — HWM tracking, halt firing, uncle-point firing — tests cover the recovery-without-HWM-reset rule
- [ ] `src/darkhorse/risk/kill_switch.py` — checks `KILLSWITCH` file, env var, optional remote endpoint
- [ ] `src/darkhorse/risk/validate_order.py` — every rule from the spec; bypass attempts fail loudly
- [ ] `src/darkhorse/risk/wind_down.py` — implements the `riskMitigation.md` §6 wind-down rule (so it can fire from day 1 of live)
- [ ] Property-based tests using Hypothesis on validate_order rules (per ADR-0009)

### 3.3 Core utilities

- [ ] `src/darkhorse/journal.py` — append-only JSONL writer, schema-validated, daily file rotation
- [ ] `src/darkhorse/calibration.py` — confidence vs realized P&L tracker
- [ ] `src/darkhorse/idempotency.py` — deterministic `client_order_id` derivation
- [ ] `src/darkhorse/notify.py` — Discord webhook wrapper with retry + dead-letter (per ADR-0011)
- [ ] `src/darkhorse/config.py` — pydantic-settings loader (per ADR-0012)
- [ ] `src/darkhorse/audit.py` — append-only audit log writer
- [ ] `src/darkhorse/schemas/` — pydantic models for every JSONL/MD shape (per `dataSchema.md`)

### 3.4 Tools (deterministic only — no LLM)

- [ ] `src/darkhorse/tools/_contracts.py` — pydantic input/output models for every tool, `strict: true`-ready
- [ ] `src/darkhorse/tools/alpaca.py` — connect to live + paper, fetch account, fetch positions, place order, cancel order. Every order routes through `validate_order()`. Tests use Alpaca's paper sandbox.
- [ ] `src/darkhorse/tools/data.py` — Finnhub quotes + bars, yfinance fallback. Cache results within a routine.
- [ ] `src/darkhorse/tools/news.py` — Sonar Finance Search wrapper, Tavily fallback. Unicode-NFKC normalize all returned text. Validate ticker mentions against the asset list.
- [ ] `src/darkhorse/tools/snaptrade.py` — read-only Fidelity holdings (deferred until SnapTrade-Fidelity link is approved)
- [ ] Asset-list refresher: weekly job pulls Alpaca's `assets` endpoint, writes `data/assets/YYYY-MM-DD.json`

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

- [ ] **Alpaca live account funded with $1,000.** Real money in. The capital is in the account; deployment ramps from $50 in Phase 4.

**Exit criteria:** `pytest` green, `mypy --strict` clean, manually-submitted bad orders rejected by `validate_order` 100% of the time across the property-based test suite. Discord webhook fires test message. Alpaca live + paper accounts both connect successfully. Linode reachable via Tailscale. Live account funded with $1,000 sitting as cash.

---

## Phase 4 — First Live Trade at Micro-Size

**Goal:** Smallest viable agent making real trades with real money. Catch bugs at the smallest possible cost.

- [ ] `src/harness.py` — session setup, doctrine loader, prompt-cache enrolment, structured-output enrolment, error envelopes
- [ ] `prompts/system_core.md` — full doctrine pasted in via cache, decision JSON schema, "30-day base rate" forced section, "default action is NO_TRADE" reinforced
- [ ] `src/routines/market_open.py` — single-agent (no debate yet), Core sleeve only, writes to `memory/core/journal/YYYY-MM-DD.jsonl`
- [ ] **Hard-coded position cap of $50 in `validate_order` for Phase 4.** The agent cannot deploy more than $50 of Core capital regardless of what it requests. Rest of Core stays as cash.
- [ ] systemd timer fires `market_open.py` at 9:35 AM ET weekdays (live mode)
- [ ] **Paper-shadow account configured.** Same routine fires against the paper account in parallel; results journaled to `memory/core/paper_shadow/journal/YYYY-MM-DD.jsonl`
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
- [ ] Multi-agent orchestration in `src/harness.py` — researcher → parallel bull/bear → risk-manager
- [ ] Risk-manager runs Opus 4.7; sub-agents run Sonnet 4.6
- [ ] Anthropic 1-hour prompt cache enabled on doctrine + journal context
- [ ] Structured outputs beta enabled on the risk-manager's decision JSON
- [ ] Cache hit-rate telemetry logged per routine; if <60% hit rate after 1 week, debug
- [ ] Side-by-side single-agent paper account continues alongside multi-agent live (RQ6 data collection starts here)

### 5.2 Full routine schedule

- [ ] `pre_market.py` (8:30 AM ET)
- [ ] `market_open.py` updated to use full debate flow (9:35 AM ET)
- [ ] `midday_scan.py` (12:30 PM ET)
- [ ] `end_of_day.py` (4:05 PM ET)
- [ ] `weekly_review.py` (Fri 5:00 PM ET) — runs Haiku 4.5, compiles lessons, proposes doctrine PRs
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

- [ ] `src/learning/distillation.py` — lesson distillation
- [ ] `src/learning/decay.py` — lesson sunset/re-validation policy
- [ ] `src/learning/calibration_analysis.py` — calibration drift detection
- [ ] `src/learning/anti_pattern_extraction.py` — automated post-mortem trigger
- [ ] `src/learning/reasoning_audit.py` — quarterly Haiku-driven critique pass
- [ ] `src/routines/monthly_competitive_review.py` — agentic web review per `learningSystem.md` §5
- [ ] First scheduled monthly competitive-landscape review fires on schedule
- [ ] First quarterly retrospective routine wired (will fire at quarter-end)
- [ ] Hypothesis registry online: `RESEARCH/hypotheses/` with at least the initial hypotheses from `researchCharter.md` filed

### 6.2 Dashboard

- [ ] FastAPI app in `src/web/app.py` with read endpoints per `frontendAndHosting.md`
- [ ] Write endpoints: KILLSWITCH toggle, doctrine-PR approval/rejection
- [ ] Tailscale-only auth wired
- [ ] Dashboard pages: Overview, Portfolio Detail, Performance, Calibration, Decisions Feed, Lessons & Doctrine, Anti-Patterns, Costs, System Health
- [ ] Aaron can open the dashboard from his phone via Tailscale
- [ ] Backups confirmed restorable from a fresh VPS (quarterly drill scheduled)

**Exit criteria:** Learning system has produced at least one merged doctrine change traceable to a calibration-drift detection or competitive-landscape adoption. First monthly competitive-landscape review filed. Dashboard usable by Aaron from phone. Backup restore drill passed.

---

## Phase 7 — Backtest + Adversarial Gate

**Goal:** Subject the system to FINSABER-style backtesting and an adversarial test suite. Outcome **gates** the size ramp in Phase 8.

- [ ] `src/evaluation/backtest_finsaber.py` — walk-forward, post-cutoff data only, full universe including delistings
- [ ] Baseline: SPY buy-and-hold over the same windows
- [ ] Backtest produces a written report — Sharpe vs SPY, max DD vs SPY, drawdown profile, trades per period, calibration on backtested data
- [ ] Adversarial suite in `src/evaluation/adversarial.py` — Unicode homoglyph tickers, fabricated headlines with hidden-text injection, stale quotes, bad tool returns
- [ ] Adversarial pass rate must be 100% — `validate_order` blocks every malicious order
- [ ] Stress windows tested explicitly: most recent post-cutoff drawdown period, sideways period, bull period
- [ ] Cost-per-decision measured against the budget; project full-year cost

**Exit criteria:** Risk-adjusted edge non-negative vs SPY on out-of-sample backtest. Adversarial 100%. Cost projection within budget. **Aaron makes an explicit go/no-go call on the size ramp.**

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
