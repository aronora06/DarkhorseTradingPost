# ADR-0003: Memory Architecture — JSONL Source of Truth + SQLite Mirror

## Status

`accepted` (2026-05-09)

## Context

The system needs durable memory at five layers (per `../learningSystem.md` §"Memory Layers"):

- **L1 Episodic** — every decision with full reasoning trace
- **L2 Semantic** — distilled lessons
- **L3 Anti-patterns** — named failure modes
- **L4 Reasoning patterns** — quarterly snapshots of how the agent thinks
- **L5 Doctrine** — the constitution

Plus operational data: calibration log, post-mortems, hypothesis registry, cost telemetry, audit log.

Two storage strategies were considered:
1. **Database-first** — everything in SQLite (or Postgres) with rows as the source of truth.
2. **File-first** — JSONL and Markdown as the source of truth, with a query-optimized mirror built nightly.

## Decision

**File-first, JSONL+Markdown as source of truth, SQLite as a query-optimized read mirror.** Decision schemas are version-pinned per `../dataSchema.md`.

| Layer | Path | Format | Source of truth |
|---|---|---|---|
| L1 Episodic | `memory/<sleeve>/journal/YYYY-MM-DD.jsonl` | JSONL, append-only | **Yes** |
| L2 Semantic | `memory/<sleeve>/lessons.md` | Markdown with YAML frontmatter | **Yes** |
| L3 Anti-patterns | `doctrine/anti_patterns.md` | Markdown with YAML frontmatter | **Yes** (lives in doctrine) |
| L4 Reasoning patterns | `memory/<sleeve>/reasoning_patterns/YYYY-Qn.md` | Markdown | **Yes** |
| L5 Doctrine | `doctrine/*.md` | Markdown, git-versioned | **Yes** |
| Calibration log | `memory/<sleeve>/calibration.jsonl` | JSONL | **Yes** |
| Post-mortems | `memory/<sleeve>/post_mortems/pmt_NNN.md` | Markdown | **Yes** |
| Hypotheses | `RESEARCH/hypotheses/H_NNN.md` | Markdown | **Yes** |
| Cost telemetry | `memory/cost/YYYY-MM-DD.jsonl` | JSONL | **Yes** |
| Audit log | `memory/audit/YYYY-MM-DD.jsonl` | JSONL, append-only | **Yes** |
| **Query mirror** | `memory/index.sqlite` | SQLite | **No** — rebuild from above |

All schemas are JSON Schema files in `schemas/`, validated on every write.

## Consequences

### Positive

- **Greppable, durable, portable.** The system's memory survives any database corruption — `git`, `tar`, `rsync` are sufficient backup tools.
- **Append-only safety.** JSONL files are written line-by-line; partial writes are recoverable, and a process crash mid-write never corrupts existing entries.
- **Human-readable.** Aaron can `cat` a journal file and read it. Doctrine, lessons, and post-mortems are markdown and render naturally on GitHub.
- **Schema-validated.** Every write goes through pydantic models (`schemas/`). Invalid entries fail loudly to Discord rather than silently corrupting state.
- **The query mirror is rebuildable.** If SQLite goes wrong, regenerate from JSONL in minutes.
- **Git-friendly.** Doctrine and lessons live in git. The journal is gitignored (private trading data) but its structure is in the repo.

### Negative / costs

- Two storage layers to maintain: writers go to JSONL and (eventually) into SQLite. Slight write amplification, but the mirror is built nightly, not on every write.
- Complex queries (cross-period analysis, multi-condition filters) need the mirror to be fast. Cold-start the mirror or a routine analysis fights against JSONL.
- Schema migrations require a one-shot migration script per breaking change.

### Neutral

- We accept that some "data" is markdown and human-edited. That's a feature for L2 and L5 — we want lessons and doctrine to be edited via PR with review, not appended programmatically.

## Alternatives considered

- **SQLite-as-source-of-truth.** Faster queries, but committing it to git is awkward (binary blob, merge conflicts), backup is heavier, and a single corruption event hits everything. Rejected.
- **Postgres from day 1.** Overkill at this scale; introduces operational surface (server process, backups, migrations) for benefits we won't use. Reconsider if dashboard query latency becomes a problem at >1 GB journal size (years away).
- **Vector DB for semantic memory.** Tempting for "fuzzy lesson lookup," but lessons are read into context wholesale via prompt caching, not retrieved by similarity. Adds operational burden for no clear benefit. Defer.
- **Pure markdown for episodic.** Considered briefly — would be the most human-friendly. Rejected because the journal needs strict schema validation and structured fields for the calibration writer and analytics; markdown free-form is too flexible and would drift.

## Falsification criterion

This decision is wrong if:

- Dashboard query latency exceeds 2 seconds on common pages with the SQLite mirror, indicating SQLite is no longer sufficient.
- Journal write throughput becomes a bottleneck (very unlikely at our routine cadence).
- Schema migrations occur >2x per year — indicates the schema design itself needs revisiting.

In any of those cases, file ADR-NNNN to evolve the storage layer (likely to Postgres or a hybrid).

## Linked hypotheses

- `../../RESEARCH/hypotheses/H_003.md` — Distilled+sunset lessons outperform raw-journal context (RQ3). The memory architecture is the precondition for testing this; H_003 cannot be answered without L1+L2 working as designed.

## Re-check date

2026-11-09 (6 months).

## References

- `../dataSchema.md` (every schema, frozen)
- `../learningSystem.md` (L1–L5 layers and what each is for)
- `../../RESEARCH/architecture/python_project_tooling_2026.md` (pydantic v2 for schemas)
