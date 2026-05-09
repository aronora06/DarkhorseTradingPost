# RESEARCH/

The research output of Darkhorse Trading Outpost. This directory is the **outside view** (what we read) and the **continuous record** (what we observe) of the project as a research effort.

It is distinct from `plans/` (technical design), `doctrine/` (rules the agent reads), and `memory/` (the agent's own journal and lessons). Where those describe and run the system, `RESEARCH/` is where we *study* it.

See `plans/researchCharter.md` for the framing — research questions, hypotheses, success/failure criteria, and the year-1 publication target.

## Structure

| Subdirectory | What lives here | Cadence |
|---|---|---|
| [`papers/`](./papers/) | One-page summaries of source papers we've read (FINSABER, TradeTrap, FinMem, etc.) | Continuous, denser in Phase 1 |
| [`hypotheses/`](./hypotheses/) | One file per registered hypothesis (`H_NNN.md`) with status and falsification criteria | Continuous |
| [`practitioner_dossiers/`](./practitioner_dossiers/) | Synthesized practitioner consensus on specific topics (drawdown halts, universe selection) | Phase 1, refreshed annually |
| [`competitive_landscape/`](./competitive_landscape/) | Monthly agentic-trading landscape reviews (`YYYY-MM.md`) — what others are building, what to adopt | Monthly (Phase 6 onward) |
| [`monthly/`](./monthly/) | Monthly retrospectives (~2 pages) — calibration, costs, lesson churn, notable trades | Monthly (Phase 5 onward) |
| [`quarterly/`](./quarterly/) | Quarterly retrospectives (~5–10 pages) — hypothesis status, evidence per RQ, reasoning audits | Quarterly (Phase 6 onward) |
| [`annual/`](./annual/) | Year-N reports designed to be publication-ready | Annually |
| [`architecture/`](./architecture/) | Architecture-research notes (multi-agent debate, prompt caching, structured outputs) | Phase 2, then as-needed |

## Conventions

- **Filenames:** kebab-case for descriptive files (`drawdown-halts.md`); structured IDs for registry-style files (`H_005.md`, `2026-08.md`).
- **Frontmatter:** all hypothesis files use YAML frontmatter as defined in `plans/dataSchema.md` §8. Other files may but aren't required to.
- **Cite by relative path:** when a research note references doctrine, plans, or another research note, use a relative link.
- **Anonymizable from day 1:** any artifact that may end up in the year-1 publication (per `plans/researchCharter.md` "Publication Readiness") must be written so it can be anonymized without rewriting. That means percentages, not dollar amounts, in trade-level analysis; multiples-of-starting-NAV, not absolute NAV.
- **Negative results are kept.** A falsified hypothesis is marked falsified and remains in the registry, not deleted. The same holds for retired lessons in `memory/<sleeve>/lessons.md`.

## What is *not* here

- **The journal.** Lives in `memory/<sleeve>/journal/` — that's the source of truth, not a research output. `memory/` is gitignored; it is the agent's working memory, not the research corpus.
- **Doctrine.** Lives in `doctrine/`. The research observes doctrine evolution; it does not contain doctrine.
- **Code.** Lives in `src/`. Research notes may reference code modules but should not contain code beyond illustrative snippets.

## Reading order for a new contributor

1. `../plans/researchCharter.md` — the framing
2. `../plans/learningSystem.md` — how research feeds back into the system
3. `hypotheses/` — what we're currently testing
4. The most recent `quarterly/` retrospective
5. The most recent `competitive_landscape/` review

If those five give a coherent picture, the research record is healthy.
