# Darkhorse Trading Outpost

Aaron Parker's personal AI trading assistant. Real money ($1,000 trading capital + ~$100/year operational costs), real guardrails, deliberate research framing.

This is **not** a SaaS product, **not** a research demo, and **not** a generic "I made an AI trader" project. It's a single-user system designed to make trading decisions on Aaron's behalf within strict, code-enforced limits — and to teach us something about how agentic LLM systems behave when the stakes are real. The system proves itself on paper trading first, then transitions to live trading at micro-size ($50 Core deployed) once the Alpaca live account is approved and paper results are clean. Capital ramps within the live account from $50 to $900 over Phase 4b–8.

Year-1 ambition: produce data and findings sufficient for a credible research publication on the experiment.

## Status

**Phase 0 — Steering documentation: complete (2026-05-08).** All steering docs in `plans/` reviewed and signed off. Repo is private on GitHub; Aaron pushes directly to `main`. Agent-proposed doctrine changes still flow through draft PRs as the discipline mechanism.

**Phase 2 — Architecture Research & Codification: substantially complete (2026-05-09).** The master architecture is documented at `docs/architecture.md`. Twelve foundational ADRs are filed under `plans/decisions/` covering hosting, harness pattern, Python tooling, testing strategy, deployment, observability, and configuration. Architecture notes live under `RESEARCH/architecture/` (including TradingAgents debate mapping + agent failure-mode synthesis). Remaining Phase 2 prototyping notes (`structured_outputs.md`, `prompt_caching.md`, etc.) are optional depth — track in `plans/devPhaseChecklist.md`.

**Phase 1 — Risk Mitigation Research & Codification: complete (2026-05-09).** Doctrine approved and indexed under [`doctrine/`](doctrine/); Markdown test specs approved under [`tests/specs/`](tests/specs/) (human sign-off recorded in `plans/devPhaseChecklist.md` §1.4). Practitioner dossiers, adversarial catalog, and major-risk paper summaries live under [`RESEARCH/`](RESEARCH/). Populate [`doctrine/satellite_watchlist.md`](doctrine/satellite_watchlist.md) before Satellite goes live (Phase 9 path). Account setups: [`accountSetup.md`](accountSetup.md).

**Phase 3 — Foundations Build: complete (2026-05-09).** Python scaffold (ADR-0007), **`validate_order`** + sibling risk modules (**`sizing`**, **`drawdown`**, **`kill_switch`**, **`wind_down`**), **`config`**, **`idempotency`**, **`journal` / `audit` / `calibration`**, **`notify`**, schemas, CI + pre-commit, deterministic tool contracts and wrappers (**Alpaca**, **assets**, **data**, **news**), prompt skeletons, full routine composition with drawdown/wind-down/halt flags + journal/audit envelopes, cassette/replay test scaffolding, Phase 4 $50 deployment cap, and pytest network guardrails. **All API keys configured and verified** (Anthropic, Alpaca paper, Perplexity, Tavily, Finnhub, Discord). Alpaca live account pending authorization.

**Phase 4a — Production Harness + Paper Trading Pipeline: implemented (2026-05-09).** Production Anthropic harness (`src/darkhorse/harness.py`, 784 lines): researcher (Sonnet 4.6) with native tool loop + risk-manager (Opus 4.7) with structured JSON output, prompt caching (1h TTL), per-call cost telemetry, tenacity retry, structlog. End-to-end `market_open` routine: compose risk state → researcher → risk-manager → confidence gate (0.70) → `validate_order` Python wall → `submit_order` to Alpaca paper → journal + audit + Discord notify. Expanded production prompts (`system_core.md`, `researcher.md`, `risk_manager.md`) with doctrine injection, decision schemas, and hard boundaries. **159 tests, 88.85% package coverage, 96.32% risk coverage.** Next: first live paper run, initial cassette recording, local scheduler, 5-day paper proving period (Phase 4a exit criteria).

## Documents

### Steering (the "what" and "why")

1. **[plans/initialPlan.md](plans/initialPlan.md)** — what we're building, the high-level decisions
2. **[plans/riskMitigation.md](plans/riskMitigation.md)** — what could go wrong and how we limit damage; tiered model strategy and cost controls
3. **[plans/researchCharter.md](plans/researchCharter.md)** — the research framing: hypotheses, success/failure criteria, outputs
4. **[plans/learningSystem.md](plans/learningSystem.md)** — meta-learning architecture (the system gets smarter over time, deliberately)
5. **[plans/frontendAndHosting.md](plans/frontendAndHosting.md)** — dashboard requirements (canonical hosting choice now lives in ADR-0005)
6. **[plans/dataSchema.md](plans/dataSchema.md)** — telemetry/journaling formats that enable the learning system
7. **[plans/glossary.md](plans/glossary.md)** — vocabulary

### Operational (the executable list and sequencing)

8. **[plans/devPhaseChecklist.md](plans/devPhaseChecklist.md)** — the executable to-do list across all phases
9. **[suggestedNextSteps.md](suggestedNextSteps.md)** — sequencing recommendations and the §1 design-decision sign-offs (lives at root for visibility; this is the active week-by-week plan)
10. **[accountSetup.md](accountSetup.md)** — per-account setup checklist with detailed steps, info to capture, env-var mapping, and verification

### Architecture (the "how it's built")

11. **[docs/architecture.md](docs/architecture.md)** — master architecture: component diagrams, data flow, layer responsibilities, extensibility hooks
12. **[plans/decisions/](plans/decisions/)** — Architecture Decision Records (ADRs). Twelve foundational ADRs (`0001`–`0012`) cover hosting, harness, tooling, testing, deployment, observability, and configuration. Template at `0000-template.md`.
13. **[doctrine/](doctrine/)** — Phase 1+ codified trading constitution (risk policy, sleeves, universe, watchlist template, news tiers, style guide); **Phase 1 approved 2026-05-09**
14. **[tests/specs/](tests/specs/)** — Markdown specifications Phase 3 Python tests implement (`validate_order`, halts, sizing, idempotency, adversarial hooks); **Phase 1 approved 2026-05-09**
15. **[RESEARCH/architecture/](RESEARCH/architecture/)** — research notes that informed the ADRs (frameworks, tooling, hosting comparison, testing strategies, Anthropic SDK features, frontend stack)
16. **[docs/](docs/)** — active reference documentation for the running system (architecture, runbooks, troubleshooting). Currently has `architecture.md` and `runbook.md`; setup/troubleshooting docs will be added as code is built in Phase 3+.

### Research record

17. **[RESEARCH/](RESEARCH/)** — papers read, hypotheses, dossiers, retrospectives, competitive landscape, annual reports

### Reading order for new contributors

`initialPlan.md` → `docs/architecture.md` → `doctrine/` (especially `risk_policy.md`) → relevant ADRs → relevant `RESEARCH/architecture/` notes → code. If those give you a coherent mental model in <2 hours, the docs are healthy.

Agent-to-agent handoffs are generated in chat for Aaron to copy into the next session. Do not commit transient handoff or next-agent backlog files.

## Core Principles (the Constitution)

1. Risk lives in code, not prompts
2. Stateless agents, durable memory
3. Tested before live; paper trading proves the system, then live ramps by size ($50 → $900)
4. Idempotent and reconstructable
5. Two sleeves, two policies, one harness
6. The kill-switch is real
7. Default action under uncertainty is NO_TRADE
8. Cost discipline (target ≤ 0.5% of NAV/yr in compute)

See `plans/initialPlan.md` §2 for full elaboration.

## Capital & Sleeves

- **Total:** $1,000 starting capital
- **Core sleeve:** $900 (90%) — conservative, beats SPY net of costs
- **Satellite sleeve:** $100 (10%) — risk capital, higher-conviction trades, total loss survivable

## Key External Accounts

All API keys configured in `.env` and verified via smoke tests (2026-05-09) except Alpaca live (pending account authorization). See [`accountSetup.md`](accountSetup.md) for full details.

| Service | Status |
|---|---|
| Anthropic (Haiku/Sonnet/Opus) | ✅ verified |
| Alpaca paper | ✅ verified ($1k paper equity) |
| Alpaca live | ⏳ pending authorization |
| Perplexity Sonar | ✅ verified |
| Tavily | ✅ verified |
| Finnhub | ✅ verified |
| Discord webhook | ✅ verified |
| SnapTrade → Fidelity | deferred |

## Building

**Phase 4a is implemented** (production harness + paper trading pipeline built **2026-05-09**). Python 3.13, `uv`, Ruff, mypy `--strict`, pytest + Hypothesis (ADR-0007); **no live LLM or broker calls in CI** (ADR-0009). See [`plans/devPhaseChecklist.md`](plans/devPhaseChecklist.md) Phase 4a.

**Local dev (from repo root):**

1. Install [uv](https://docs.astral.sh/uv/) (Astral’s installer or `pip install uv`).
2. `uv sync` — creates `.venv` and installs the project + dev tools from `uv.lock`.
3. `uv run ruff check .` / `uv run ruff format .` — lint & format.
4. `uv run mypy --strict src` — typecheck.
5. `uv run pytest -ra --cov=darkhorse --cov-report=term-missing --cov-fail-under=88` — tests (package coverage gate enforced).
6. `uv run pytest -q tests/property/test_validate_order_properties.py tests/unit/test_drawdown.py tests/unit/test_kill_switch.py tests/unit/test_sizing.py tests/unit/test_validate_order.py tests/unit/test_wind_down.py --cov=darkhorse.risk --cov-report=term-missing --cov-fail-under=95` — focused risk coverage gate.
7. `DARKHORSE_ALLOW_NETWORK_TESTS=1 uv run pytest tests/smoke/ -v` — API connectivity smoke tests (requires real keys in `.env`; skipped automatically in CI).
8. Optional: `pre-commit install` — runs Ruff, gitleaks, mypy, pytest on commit (see `.pre-commit-config.yaml`).

`Settings` (`src/darkhorse/config.py`) loads `config/settings.toml` and repo-root `.env` (see `.env.example`). Risk helpers live under `src/darkhorse/risk/`; deterministic broker/data/news wrappers live under `src/darkhorse/tools/`; journals use `src/darkhorse/schemas/` + `journal.py`.

Copy `.env.example` → `.env` for real keys (never commit `.env`).

## License

Private repository. No license granted. This is Aaron's personal capital.