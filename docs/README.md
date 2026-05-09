# docs/

Active reference documentation for the running Darkhorse system. This directory complements `plans/` and `RESEARCH/` and serves a different purpose:

| Directory | Purpose | Lifecycle |
|---|---|---|
| `plans/` | **Steering and decisions** — what we're building, why, and what trade-offs we accepted. ADRs in `plans/decisions/`. | Written once, edited deliberately. |
| `docs/` | **Active reference** — how the running system works, how to operate it, how to extend it. | Living documents; updated as code changes. |
| `doctrine/` (repo root) | **Codified rules** the harness loads — risk policy, sleeves, universe, watchlist template, news tiers. Complements `plans/`; numeric mirrors land in `config/` at Phase 3. | Versioned with git; material edits via PR discipline. |
| `RESEARCH/` | **Research record** — papers, hypotheses, retrospectives, competitive landscape, dossiers. | Append-mostly; immutable history. |

If you're trying to understand "what we decided and why," start in `plans/`. If you're trying to understand "how do I make this code do X," start here.

## Current contents

| File | Purpose |
|---|---|
| [`architecture.md`](architecture.md) | The master architectural reference for the codebase: layers, data flow, deployment topology, extensibility hooks, ADR index |
| [`runbook.md`](runbook.md) | Local setup, quality gates, pre-commit, CI, cassette testing, API smoke tests, and current Phase 4a runtime status |

**Related (outside `docs/`):** [`doctrine/`](../doctrine/) — trading constitution Markdown (**Phase 1 approved 2026-05-09**); [`tests/specs/`](../tests/specs/) — Markdown specs implemented by Phase 3 tests (**same sign-off**).

## Planned additions (as code is built)

These remaining documents will live here as Phase 3+ delivers more of the system.

| File | Purpose | Phase |
|---|---|---|
| `setup.md` | One-shot environment setup for a new VPS (Ubuntu, Tailscale, systemd units, secrets, first run) | Phase 3.5 |
| `developer-onboarding.md` | First-day guide for a new contributor (or future-Aaron returning after a long break) | Phase 3 |
| `troubleshooting.md` | Common failure modes and how to investigate (broker outage, cache misses, halt unfreeze, kill-switch flow) | Phase 4+ |
| `tool-contracts.md` | Auto-generated reference of every tool's input/output schema | Phase 3 (generated) |
| `api-reference.md` | FastAPI dashboard endpoint reference, auto-generated from OpenAPI | Phase 6 (generated) |
| `prompts/` (subdirectory) | Annotated copies of the production prompts with edit history and reasoning | Phase 5 |

## Conventions

- **Living, not historical.** Documents here reflect the *current* system. Use `git log <file>` for history; do not preserve outdated content with strikethroughs.
- **Concrete over abstract.** Examples, command snippets, file paths. If a section says "configure logging," it shows the config. If it says "run a routine manually," it shows the exact command.
- **Cross-link to ADRs and code.** Every architectural choice referenced here links to the ADR (in `plans/decisions/`) and the relevant code module (in `src/darkhorse/`).
- **Markdown, no auto-generators yet.** Hand-written until we have enough surface to justify auto-generation (likely Phase 6+).
- **Write for future-Aaron.** Assume the reader is competent but has been away from this project for 6+ months.
- **No agent handoff files.** Agent-to-agent handoffs are generated in chat for Aaron to copy into the next session; do not commit transient next-agent backlog documents.
