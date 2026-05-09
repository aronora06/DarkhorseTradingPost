# Python Project Tooling — 2026 State of Practice

**Compiled:** 2026-05-09
**Refresh by:** 2026-11-09
**Linked ADRs:** ADR-0007 (Python project layout)

## Summary

The 2026 canonical Python tooling stack has consolidated around **uv + Ruff + mypy + pytest**, with `pyproject.toml` as the single source of configuration truth. This stack collapses what was previously seven-or-more overlapping tools (pyenv, pip, virtualenv, poetry, black, isort, flake8, mypy) into four cohesive tools, three of which (uv, Ruff, Ty) come from the same vendor (Astral) and integrate seamlessly.

For Darkhorse, this is the right call. The stack is mature enough to bet on, fast enough to keep CI cheap, and minimal enough that the entire toolchain configuration fits in `pyproject.toml`.

## Sources reviewed

- KDnuggets, "Python Project Setup 2026: uv + Ruff + Ty + Polars" (2026)
- AlgoMart on Medium, "How to Structure Python Projects in 2026 Without Regretting It Later" (Apr 2026)
- discuss.python.org, "Starting a new Python project, do I need all these tools?" (2026)
- Simone Carolini on Medium, "Modern Python Code Quality Setup: uv, ruff, and mypy"
- Astral docs (uv, ruff, ty)

## Key findings

### 1. uv is the package manager

`uv` from Astral is now the consensus package and project manager. Reported benchmarks: 10–100x faster dependency resolution than Poetry, single binary install, full pyproject.toml support, lockfile-based reproducibility, drop-in for `pip install`, `pipx`, `python -m venv`, and most of `poetry`.

Operational characteristics:
- Single command surface: `uv sync`, `uv add`, `uv remove`, `uv run`
- `uv.lock` for reproducible installs (gitted)
- Manages Python interpreter versions (replaces pyenv)
- Workspace support if/when we split into multi-package layout (we won't in v1)

### 2. Ruff is the linter + formatter

Ruff replaces black, isort, flake8, pylint (mostly), and pydocstyle. It runs in milliseconds rather than seconds, and Astral has continued to expand its rule coverage so it's now a fully credible flake8/pylint replacement, not just a fast subset.

For Darkhorse: enable formatter + a sensible rule set. Recommended rule groups:
- `E`, `W` — pycodestyle errors and warnings
- `F` — pyflakes
- `I` — isort
- `N` — pep8-naming
- `B` — bugbear
- `UP` — pyupgrade
- `RUF` — ruff-specific
- `S` — bandit (security) — important for a system that handles secrets

### 3. Type checking — mypy stays for now, Ty is interesting

Ty is Astral's new Rust-implemented type checker, in preview as of mid-2026. It's blazingly fast but still lacks coverage of some advanced typing constructs that mypy handles. The 2026 consensus is "use mypy for production, watch Ty."

For Darkhorse: `mypy --strict` for now. Re-evaluate in 6 months. `Ty` should be a one-line config swap if we choose to switch.

### 4. pytest remains the test framework

No challenger has emerged. The 2026 additions worth using:
- `pytest-cov` for coverage
- `pytest-asyncio` for async test support
- `Hypothesis` for property-based tests (especially `validate_order`)
- `assertllm` or similar for deterministic LLM-output assertions (see `testing_ai_agents.md`)

### 5. pyproject.toml as center of gravity

Everything goes in `pyproject.toml`:
- `[project]` — package metadata and runtime deps
- `[dependency-groups]` (PEP 735) — dev/test/docs groups
- `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.ruff.format]` — Ruff config
- `[tool.mypy]` — type-check config
- `[tool.pytest.ini_options]` — test config
- `[tool.uv]` — uv-specific (e.g., dev dependencies if not using PEP 735 groups)

Single-file config means a new contributor (or future-Aaron) reads one file to understand the toolchain.

### 6. Project layout — src/ vs flat

The src/ layout is consensus best practice in 2026:

```
DarkhorseTradingOutpost/
├── pyproject.toml
├── uv.lock
├── README.md
├── src/
│   └── darkhorse/         # the importable package
│       ├── __init__.py
│       ├── harness.py
│       ├── routines/
│       ├── tools/
│       ├── risk/
│       └── ...
├── tests/
│   ├── unit/
│   ├── property/
│   └── integration/
├── prompts/               # not Python; doctrine-adjacent
├── doctrine/              # not Python; the rules
├── memory/                # gitignored, runtime
└── plans/                 # docs
```

Rationale for src/:
- Prevents accidentally importing the local copy when tests run
- Forces installation (via `uv sync`), which catches packaging mistakes
- Standard for libraries; also fine for applications

The existing `initialPlan.md` §3.1 sketch shows directories without `src/` — we'll formalize this in ADR-0007.

### 7. Optional but interesting

- **Polars** for any dataframe work (calibration analysis, backtesting). Lazy execution + Rust core, much faster than pandas for our scale. Defer until we have a concrete use case.
- **structlog** for structured logging — pairs cleanly with our JSONL journal philosophy.
- **pydantic v2** for data validation, schemas, settings.
- **pydantic-settings** for typed env/config loading.
- **rich** or **textual** for any CLI tooling we add.

## Implications for Darkhorse

Locked tooling for Phase 3:
- **uv** for environments and deps
- **Ruff** for lint + format (configured in pyproject.toml)
- **mypy --strict** for type checking
- **pytest** + Hypothesis + pytest-asyncio for tests
- **pre-commit** to run ruff + mypy + pytest-on-changed-files locally
- **GitHub Actions** to run the full suite on push/PR
- **pyproject.toml** as the single config source
- **src/darkhorse/** layout

## Open questions

- **Polars now or later?** Defer. We don't yet have dataframe-heavy work.
- **Ty when?** Watch the changelog. Switch when it covers our typing surface and Astral declares it stable.
- **Tox / nox?** Skip. Single Python version, single environment in v1.

## Sample pyproject.toml skeleton

```toml
[project]
name = "darkhorse"
version = "0.0.0"
description = "Personal AI trading assistant — see plans/initialPlan.md"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
  "anthropic>=0.50",
  "pydantic>=2.9",
  "pydantic-settings>=2.6",
  "fastapi>=0.115",
  "jinja2>=3.1",
  "uvicorn[standard]>=0.32",
  "structlog>=24.4",
  "httpx>=0.27",
  "alpaca-py>=0.40",
  "tenacity>=9.0",
  "tomli>=2.0",
]

[dependency-groups]
dev = [
  "ruff>=0.7",
  "mypy>=1.13",
  "pytest>=8.3",
  "pytest-asyncio>=0.24",
  "pytest-cov>=6.0",
  "hypothesis>=6.115",
  "pre-commit>=4.0",
]

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "B", "UP", "RUF", "S"]

[tool.mypy]
strict = true
python_version = "3.13"

[tool.pytest.ini_options]
asyncio_mode = "auto"
addopts = "-ra --cov=darkhorse --cov-report=term-missing"
testpaths = ["tests"]
```
