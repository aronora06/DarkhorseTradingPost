# Darkhorse Trading Outpost

Aaron Parker's personal AI trading assistant. Real money ($1,000 trading capital + ~$100/year operational costs), real guardrails, deliberate research framing.

This is **not** a SaaS product, **not** a research demo, and **not** a generic "I made an AI trader" project. It's a single-user system designed to make trading decisions on Aaron's behalf within strict, code-enforced limits — and to teach us something about how agentic LLM systems behave when the stakes are real. **Real money from day 1 of trading**: no extended paper-only phase, costs only accrue when real signal is being collected. Capital ramps within the live account from $50 to $900 over Phase 4–8.

Year-1 ambition: produce data and findings sufficient for a credible research publication on the experiment.

## Status

**Phase 0 — Steering documentation: complete (2026-05-08).** All steering docs in `plans/` reviewed and signed off. Repo is private on GitHub; Aaron pushes directly to `main`. Agent-proposed doctrine changes still flow through draft PRs as the discipline mechanism.

**Phase 2 — Architecture Research & Codification: substantially complete (2026-05-09).** The master architecture is documented at `docs/architecture.md`. Twelve foundational ADRs are filed under `plans/decisions/` covering hosting, harness pattern, Python tooling, testing strategy, deployment, observability, and configuration. Architecture notes live under `RESEARCH/architecture/` (including TradingAgents debate mapping + agent failure-mode synthesis). Remaining Phase 2 prototyping notes (`structured_outputs.md`, `prompt_caching.md`, etc.) are optional depth — track in `plans/devPhaseChecklist.md`.

**Phase 1 — Risk Mitigation Research & Codification: complete (2026-05-09).** Doctrine approved and indexed under [`doctrine/`](doctrine/); Markdown test specs approved under [`tests/specs/`](tests/specs/) (human sign-off recorded in `plans/devPhaseChecklist.md` §1.4). Practitioner dossiers, adversarial catalog, and major-risk paper summaries live under [`RESEARCH/`](RESEARCH/). Populate [`doctrine/satellite_watchlist.md`](doctrine/satellite_watchlist.md) before Satellite goes live (Phase 9 path). Account setups: [`accountSetup.md`](accountSetup.md).

**Phase 3 — Foundations Build: cleared to start.** Per checklist, Phase 3 does not require every optional Phase 2 research stub (`structured_outputs.md`, `prompt_caching.md`, …) — those continue in parallel. First implementation targets: `pyproject.toml` + `src/darkhorse/` scaffold (ADR-0007), then `validate_order` + tests (`plans/devPhaseChecklist.md` Phase 3).

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
16. **[docs/](docs/)** — active reference documentation for the running system (architecture, runbooks, troubleshooting). Currently has `architecture.md`; runbook/setup/troubleshooting docs added as code is built in Phase 3+.

### Research record

17. **[RESEARCH/](RESEARCH/)** — papers read, hypotheses, dossiers, retrospectives, competitive landscape, annual reports

### Reading order for new contributors

`initialPlan.md` → `docs/architecture.md` → `doctrine/` (especially `risk_policy.md`) → relevant ADRs → relevant `RESEARCH/architecture/` notes → code. If those give you a coherent mental model in <2 hours, the docs are healthy.

## Core Principles (the Constitution)

1. Risk lives in code, not prompts
2. Stateless agents, durable memory
3. Tested before live; ramp by size, not by paper-vs-live (real money from day 1 of agent operation)
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

## Key External Accounts (set up status)

See `plans/initialPlan.md` §5 for the full list and ordering.

## Building

**Phase 1 is complete** (doctrine + Markdown specs signed off **2026-05-09**). **Phase 3 — Foundations Build** is next: scaffold `src/darkhorse/` (ADR-0007), implement risk modules from `tests/specs/` — **still no agent / no live LLM in CI** until those milestones say otherwise. See [`plans/devPhaseChecklist.md`](plans/devPhaseChecklist.md) Phase 3.

## License

Private repository. No license granted. This is Aaron's personal capital.