# Runbook

Day-to-day commands for developing and verifying Darkhorse locally. Run all commands from the repository root unless a step says otherwise.

## Local Setup

1. Install `uv` if it is not already available:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install dependencies and create the local virtual environment:

   ```bash
   uv sync
   ```

3. Create a local environment file for secrets and machine-specific values:

   ```bash
   cp .env.example .env
   ```

   Never commit `.env`. Fill in real values only on machines that need to call external services.

## Quality Gates

These commands match the CI gates. Run them before opening or merging a PR:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src
uv run pytest -ra --cov=darkhorse --cov-report=term-missing --cov-fail-under=88
uv run pytest -q tests/property/test_validate_order_properties.py tests/unit/test_drawdown.py tests/unit/test_kill_switch.py tests/unit/test_sizing.py tests/unit/test_validate_order.py tests/unit/test_wind_down.py --cov=darkhorse.risk --cov-report=term-missing --cov-fail-under=95
```

Use `uv run ruff format .` when you want Ruff to rewrite formatting locally.

## Pre-Commit

Install the hooks once per clone:

```bash
uv tool install pre-commit
pre-commit install
```

Run the full hook set manually:

```bash
pre-commit run --all-files
```

The configured hooks run Ruff, gitleaks, mypy, and pytest. If `gitleaks` reports a secret, rotate that secret before committing even if you remove it from the diff.

## CI

GitHub Actions runs on pushes to `main` and on pull requests:

1. `uv sync --frozen`
2. `uv run ruff check .`
3. `uv run ruff format --check .`
4. `uv run mypy --strict src`
5. `uv run pytest -ra --cov=darkhorse --cov-report=term-missing --cov-fail-under=88`
6. `uv run pytest -q tests/property/test_validate_order_properties.py tests/unit/test_drawdown.py tests/unit/test_kill_switch.py tests/unit/test_sizing.py tests/unit/test_validate_order.py tests/unit/test_wind_down.py --cov=darkhorse.risk --cov-report=term-missing --cov-fail-under=95`

CI must remain deterministic. Do not add tests that require live broker, LLM, news, or market-data credentials unless they are skipped by default and enabled by an explicit environment flag.

The pytest suite blocks real HTTP by default in `tests/conftest.py`. Unit tests that touch broker, news, market-data, Discord, or kill-switch HTTP paths must inject `httpx.MockTransport`. Live smoke tests must be skipped by default and require `DARKHORSE_ALLOW_NETWORK_TESTS=1`.

## API Smoke Tests

Verify all external API connections are working (requires real keys in `.env`):

```bash
DARKHORSE_ALLOW_NETWORK_TESTS=1 uv run pytest tests/smoke/ -v
```

This tests Anthropic, Alpaca paper, Perplexity Sonar, Tavily, Finnhub, and Discord. These tests are automatically skipped in CI and normal test runs. Run them after rotating keys, setting up a new machine, or updating `.env`.

**Current status (2026-05-09):** All connections verified. Alpaca paper account is ACTIVE with $1,000 paper equity. Alpaca live keys are placeholder values pending account authorization.

## Settings

Runtime settings load from two repository-root files:

- `config/settings.toml` for committed defaults and numeric guardrails.
- `.env` for secrets and machine-specific overrides.

Tests that mutate environment variables or settings files should call `clear_settings_cache()` from `darkhorse.config` before re-reading settings.

## Cassette Testing

The cassette/replay system records Anthropic API interactions for deterministic CI replay:

```bash
# Record a minimal API probe cassette (requires ANTHROPIC_API_KEY in .env):
uv run python -m darkhorse.testing.record <cassette_name>

# Record a full market_open routine cassette (captures all Anthropic calls):
uv run python -m darkhorse.testing.record <cassette_name> --routine market_open

# Run tests using recorded cassettes (no API key needed):
uv run pytest tests/unit/test_cassette.py -v
```

Cassettes live in `tests/cassettes/`. The `CassetteTransport` (httpx-based) supports both `record` and `replay` modes. See `src/darkhorse/testing/cassette.py`. The `--routine market_open` mode runs the full end-to-end pipeline and captures all researcher + risk-manager Anthropic round-trips; broker/data/news calls go live on their own clients.

## Current Runtime Status

**Phase 4a in progress (2026-05-09).** The production Anthropic harness, end-to-end paper trading pipeline, and first successful paper runs are complete. Working toward 5 clean trading days.

- **Production harness** (`src/darkhorse/harness.py`): researcher (Sonnet 4.6) with native tool loop (max 10 iterations) + risk-manager (Opus 4.7) with structured JSON output. Prompt caching (1h TTL), per-call cost telemetry with SHA-256 result hashes, tenacity retry, structlog.
- **End-to-end `market_open` routine** (`src/darkhorse/routines/market_open.py`): compose risk state → researcher → risk-manager → confidence gate (0.70) → `validate_order` → `submit_order` to Alpaca paper → journal + audit + Discord notify.
- **Journal records now include:** full researcher narrative (`research_context`, ~11K chars), SHA-256 tool result hashes, per-decision LLM cost breakdown (input/cached/output tokens + USD total), model assignments, reasoning steps, anti-pattern flags.
- **First paper runs completed (2026-05-09):** 4 runs total (2 composition-blocked, 2 full harness runs). Both harness runs returned NO_TRADE with detailed reasoning (weekend + pre-CPI uncertainty). Cost: $0.46 and $0.69 per run.
- **Cassette recorded:** `tests/cassettes/market_open_initial.json` — 5 Anthropic interactions (4 researcher + 1 risk-manager), 31KB. Record CLI supports `--routine market_open` for full-pipeline captures.
- Deterministic risk modules (`validate_order`, sizing, drawdown, kill_switch, wind_down) with 96.32% coverage.
- Phase 4 $50 Core deployment cap wired end-to-end.
- **166 tests, 89.49% package coverage, 96.32% risk coverage.**
- All API keys verified (smoke tests). Alpaca paper account ACTIVE with $1,000 paper equity.

**Next:** Set up local scheduler (launchd) for 9:35 AM ET weekday runs, accumulate 5 clean trading days, daily Discord recap review. See `suggestedNextSteps.md` §4.2.

**Not yet built:** Local scheduler activation, SnapTrade wrapper, FastAPI dashboard, Linode deployment.
