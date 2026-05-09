# Darkhorse Trading Outpost

Aaron Parker's personal AI trading assistant. Real money ($1,000 trading capital + ~$100/year operational costs), real guardrails, deliberate research framing.

This is **not** a SaaS product, **not** a research demo, and **not** a generic "I made an AI trader" project. It's a single-user system designed to make trading decisions on Aaron's behalf within strict, code-enforced limits — and to teach us something about how agentic LLM systems behave when the stakes are real. **Real money from day 1 of trading**: no extended paper-only phase, costs only accrue when real signal is being collected. Capital ramps within the live account from $50 to $900 over Phase 4–8.

Year-1 ambition: produce data and findings sufficient for a credible research publication on the experiment.

## Status

**Phase 0 — Steering documentation: complete (2026-05-08).** All steering docs in `plans/` reviewed and signed off. Repo is private on GitHub; Aaron pushes directly to `main`. Agent-proposed doctrine changes still flow through draft PRs as the discipline mechanism.

**Phase 2 — Architecture Research & Codification: substantially complete (2026-05-09).** The master architecture is documented at `docs/architecture.md`. Twelve foundational ADRs are filed under `plans/decisions/` covering hosting, harness pattern, Python tooling, testing strategy, deployment, observability, and configuration. Six architecture research notes live under `RESEARCH/architecture/`. Phase 2's remaining deeper-paper-reads (TradingAgents, agent failure modes) continue in parallel and will inform ADR re-checks at the 6-month mark.

**Phase 1 — Risk Mitigation Research & Codification: in progress.** No costs accruing yet. Account setups (Alpaca, Anthropic, Perplexity, SnapTrade, Discord) are running in parallel given their lead times. See `plans/devPhaseChecklist.md` for the executable list and `plans/suggestedNextSteps.md` §2–3 for the recommended week-by-week sequence.

**Phase 3 — Foundations Build: ready to start once Phase 1 doctrine is codified.** All architecture decisions are in place to begin scaffolding `src/darkhorse/`.

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
9. **[plans/suggestedNextSteps.md](plans/suggestedNextSteps.md)** — sequencing recommendations and the §1 design-decision sign-offs

### Architecture (the "how it's built")

10. **[docs/architecture.md](docs/architecture.md)** — master architecture: component diagrams, data flow, layer responsibilities, extensibility hooks
11. **[plans/decisions/](plans/decisions/)** — Architecture Decision Records (ADRs). Twelve foundational ADRs (`0001`–`0012`) cover hosting, harness, tooling, testing, deployment, observability, and configuration. Template at `0000-template.md`.
12. **[RESEARCH/architecture/](RESEARCH/architecture/)** — research notes that informed the ADRs (frameworks, tooling, hosting comparison, testing strategies, Anthropic SDK features, frontend stack)
13. **[docs/](docs/)** — active reference documentation for the running system (architecture, runbooks, troubleshooting). Currently has `architecture.md`; runbook/setup/troubleshooting docs added as code is built in Phase 3+.

### Research record

13. **[RESEARCH/](RESEARCH/)** — papers read, hypotheses, dossiers, retrospectives, competitive landscape, annual reports

### Reading order for new contributors

`initialPlan.md` → `architecture.md` → relevant ADRs → relevant `RESEARCH/architecture/` notes → code. If those give you a coherent mental model in <2 hours, the docs are healthy.

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

Don't yet. Phase 0 is locked, but Phase 1 (Risk Mitigation Research & Codification) and Phase 2 (Architecture Research & Codification) precede any code. Code begins in Phase 3 (Foundations Build) — see `plans/devPhaseChecklist.md`.

## License

Private repository. No license granted. This is Aaron's personal capital.