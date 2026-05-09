# Darkhorse Trading Outpost

Aaron Parker's personal AI trading assistant. Real money ($1,000 trading capital + ~$100/year operational costs), real guardrails, deliberate research framing.

This is **not** a SaaS product, **not** a research demo, and **not** a generic "I made an AI trader" project. It's a single-user system designed to make trading decisions on Aaron's behalf within strict, code-enforced limits — and to teach us something about how agentic LLM systems behave when the stakes are real. **Real money from day 1 of trading**: no extended paper-only phase, costs only accrue when real signal is being collected. Capital ramps within the live account from $50 to $900 over Phase 4–8.

Year-1 ambition: produce data and findings sufficient for a credible research publication on the experiment.

## Status

**Phase 0 — Steering documentation: complete (2026-05-08).** All steering docs in `plans/` have been reviewed and signed off. Design decisions called out in `plans/suggestedNextSteps.md` §1 have been accepted. The ADR template is in place at `plans/decisions/0000-template.md` and the `RESEARCH/` directory structure is staged for Phase 1 deliverables. Repo is private on GitHub; Aaron pushes directly to `main`. Agent-proposed doctrine changes still flow through draft PRs as the discipline mechanism (see `plans/learningSystem.md`).

**Currently entering Phase 1 — Risk Mitigation Research & Codification.** No costs accruing yet. See `plans/devPhaseChecklist.md` Phase 1 for deliverables; see `plans/suggestedNextSteps.md` §2–3 for the recommended week-by-week sequence.

## Documents

Read in this order:

1. **[plans/initialPlan.md](plans/initialPlan.md)** — what we're building, the architecture, the decisions
2. **[plans/riskMitigation.md](plans/riskMitigation.md)** — what could go wrong and how we limit damage; tiered model strategy and cost controls
3. **[plans/researchCharter.md](plans/researchCharter.md)** — the research framing: hypotheses, success/failure criteria, outputs
4. **[plans/learningSystem.md](plans/learningSystem.md)** — meta-learning architecture (the system gets smarter over time, deliberately)
5. **[plans/devPhaseChecklist.md](plans/devPhaseChecklist.md)** — the executable to-do list across all phases
6. **[plans/frontendAndHosting.md](plans/frontendAndHosting.md)** — dashboard spec + Linode infrastructure
7. **[plans/dataSchema.md](plans/dataSchema.md)** — telemetry/journaling formats that enable the learning system
8. **[plans/glossary.md](plans/glossary.md)** — vocabulary
9. **[plans/suggestedNextSteps.md](plans/suggestedNextSteps.md)** — sequencing recommendations and the §1 design-decision sign-offs
10. **[plans/architecture.md](plans/architecture.md)** — component diagrams, data flow, sequence diagrams (populated in Phase 2)
11. **[plans/decisions/](plans/decisions/)** — Architecture Decision Records (ADRs) accumulated over time; template at `0000-template.md`
12. **[RESEARCH/](RESEARCH/)** — the research record: papers read, hypotheses, dossiers, retrospectives, competitive landscape

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