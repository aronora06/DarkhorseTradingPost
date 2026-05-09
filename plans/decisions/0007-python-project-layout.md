# ADR-0007: Python Project Layout & Tooling

## Status

`accepted` (2026-05-09)

## Context

Phase 3 begins by initializing the Python project. The 2026 Python tooling landscape has consolidated dramatically — what previously required pyenv + pip + virtualenv + poetry + black + isort + flake8 + mypy is now a four-tool stack from primarily one vendor (Astral).

The decision is which tools to commit to and how to lay out the repository so it doesn't fight us in 12 months.

## Decision

**Stack:**

| Concern | Tool | Rationale |
|---|---|---|
| Package + env management | **uv** | 10–100x faster than Poetry; manages Python versions, deps, lockfile |
| Lint + format | **Ruff** | Replaces black, isort, flake8, pylint, pydocstyle; ms-fast |
| Type checking | **mypy --strict** | Mature; Astral's `Ty` is interesting but still preview |
| Test framework | **pytest** | + pytest-asyncio, pytest-cov |
| Property tests | **Hypothesis** | Adversarial input space for `validate_order` |
| Data validation | **pydantic v2** | Schemas, settings, decision JSON, every typed boundary |
| Settings | **pydantic-settings** | Typed env + TOML config |
| Logging | **structlog** | Structured logs that pair with our JSONL philosophy |
| HTTP | **httpx** | Async-native, retries via tenacity |
| Retries | **tenacity** | Standard async retry decorator |
| Pre-commit | **pre-commit** | Run ruff + mypy locally before commit |

Single-file configuration: everything in `pyproject.toml`.

**Repository layout** (src/ pattern):

```
DarkhorseTradingOutpost/
├── pyproject.toml
├── uv.lock
├── README.md
├── .python-version              # uv-managed
├── src/
│   └── darkhorse/
│       ├── __init__.py
│       ├── config.py             # pydantic-settings loader
│       ├── harness.py            # multi-agent orchestration
│       ├── journal.py            # JSONL writer + schemas
│       ├── calibration.py
│       ├── idempotency.py
│       ├── notify.py             # Discord webhook
│       ├── audit.py
│       ├── routines/
│       │   ├── pre_market.py
│       │   ├── market_open.py
│       │   ├── midday_scan.py
│       │   ├── end_of_day.py
│       │   ├── weekly_review.py
│       │   └── monthly_competitive_review.py
│       ├── tools/
│       │   ├── _contracts.py      # pydantic types for every tool
│       │   ├── alpaca.py
│       │   ├── data.py
│       │   ├── news.py
│       │   └── snaptrade.py
│       ├── risk/
│       │   ├── validate_order.py
│       │   ├── sizing.py
│       │   ├── kill_switch.py
│       │   ├── drawdown.py
│       │   └── wind_down.py
│       ├── learning/
│       │   ├── distillation.py
│       │   ├── decay.py
│       │   ├── calibration_analysis.py
│       │   ├── anti_pattern_extraction.py
│       │   └── reasoning_audit.py
│       ├── evaluation/
│       │   ├── backtest_finsaber.py
│       │   └── adversarial.py
│       ├── memory/
│       │   ├── reader.py          # JSONL → SQLite mirror
│       │   └── mirror.py          # SQLite query helpers
│       ├── schemas/               # pydantic models for every JSONL/MD shape
│       │   ├── decision.py
│       │   ├── calibration.py
│       │   ├── lesson.py
│       │   └── ...
│       └── web/
│           ├── app.py
│           ├── routes/
│           ├── templates/
│           └── static/
├── tests/
│   ├── unit/
│   ├── property/
│   ├── cassettes/                # recorded LLM I/O for harness regression tests
│   └── adversarial/
├── prompts/                       # markdown prompts (not Python)
├── doctrine/                      # markdown rules (not Python)
├── memory/                        # gitignored, runtime
├── data/                          # gitignored, runtime (asset lists, etc.)
├── plans/                         # this directory
├── RESEARCH/                      # research record
└── KILLSWITCH                     # file-flag the harness checks each tick
```

**Python version:** 3.13 (latest stable LTS-track as of 2026).

## Consequences

### Positive

- One config file. New contributors (or future-Aaron) read `pyproject.toml` and understand the toolchain.
- Sub-second lint feedback. CI pipelines stay under 2 minutes total.
- src/ layout prevents accidental local-import bugs that show up only when packaged.
- Type checking with `mypy --strict` catches a category of bugs (None-handling, return-type drift) that are otherwise found in production.
- Hypothesis tests on `validate_order` push us toward provable correctness on the load-bearing risk module.
- Pydantic v2 means every cross-boundary value (config, decisions, tool calls, journal entries) is validated. Bad data fails at the boundary, not deep in business logic.

### Negative / costs

- `mypy --strict` will complain about edge cases where types are awkward (third-party libraries without stubs, dynamic patterns). Mitigated with `# type: ignore[reason]` comments — sparingly, with reasons.
- Ruff's rule set is opinionated; some rules will conflict with stylistic preferences. Configurable, but expect a few rule disablements early.
- `uv` is newer than pip/poetry; if Astral disappears, migration is real but bounded (uv.lock is documented format).

### Neutral

- We accept being on Python 3.13. Older deployment environments (which we don't have) would need backports.

## Alternatives considered

- **Poetry instead of uv.** Mature, widely-known. Rejected: 10–100x slower dependency resolution, more complex configuration, less momentum in 2026.
- **pip + requirements.txt.** Simplest possible. Rejected: no lockfile, painful dependency resolution, no environment management.
- **Hatch instead of uv.** Underrated, similar feature set. Rejected: less momentum, different mental model from where the ecosystem is heading.
- **Black + isort + flake8 instead of Ruff.** Three tools when one is sufficient. Rejected.
- **Pylint instead of (or in addition to) Ruff.** Slower, more pedantic. Rejected; Ruff covers ~95% of common Pylint rules.
- **Ty instead of mypy.** Astral's new type checker. Tempting (it's fast) but still preview as of mid-2026 with incomplete typing surface coverage. Defer until stable.
- **Flat repo layout (no src/).** Simpler at first glance. Rejected: classic foot-gun where local imports work in dev and break in production.
- **Python 3.12.** Current LTS-track, more conservative. Rejected: 3.13 brings type-system improvements (PEP 696 generic defaults, etc.) we'll use, and pinning forward avoids a forced upgrade in 6 months.

## Falsification criterion

This decision is wrong if:

- `mypy --strict` runs > 60 seconds on the full repo (would force a strictness reduction).
- `uv` has a multi-week broken-on-Linux-CI episode we can't work around.
- A core dependency (anthropic, fastapi, alpaca-py) drops Python 3.13 support — would force a Python downgrade.

## Linked hypotheses

None directly. This is foundational tooling.

## Re-check date

2026-11-09 (6 months) — re-evaluate as Astral's `Ty` matures and any 3.14 features become compelling.

## References

- `../../RESEARCH/architecture/python_project_tooling_2026.md` (research note that informed this decision)
- KDnuggets, "Python Project Setup 2026: uv + Ruff + Ty + Polars"
- AlgoMart, "How to Structure Python Projects in 2026 Without Regretting It Later"
