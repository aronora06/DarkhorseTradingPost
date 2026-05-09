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
# Record new cassettes (requires ANTHROPIC_API_KEY in .env):
uv run python -m darkhorse.testing.record <cassette_name>

# Run tests using recorded cassettes (no API key needed):
uv run pytest tests/unit/test_cassette.py -v
```

Cassettes live in `tests/cassettes/`. The `CassetteTransport` (httpx-based) supports both `record` and `replay` modes. See `src/darkhorse/testing/cassette.py`.

## Current Runtime Status

**Phase 3.1-3.4 substantially complete (2026-05-09).** Implemented:
- Deterministic risk modules (`validate_order`, sizing, drawdown, kill_switch, wind_down) with 96% coverage.
- Core utilities (config, idempotency, journal, audit, calibration, notify, schemas).
- Deterministic tool wrappers (Alpaca, assets, data, news) with strict contracts.
- Routine composition with full risk state: drawdown/halt flags, wind-down, daily loss halt, trades-today, journal/audit envelopes.
- Cassette/replay scaffolding for testing Anthropic interactions.
- Phase 4 $50 Core deployment cap wired end-to-end.
- 119 tests, 90% package coverage, 96% risk coverage.
- All API keys verified (smoke tests).

**Next:** Build the production Anthropic harness and begin paper trading (Phase 4a). Paper trading proceeds immediately using the Alpaca paper account. Live trading (Phase 4b) activates once the Alpaca live account is approved and paper trading has proven clean.

**Not yet built:** Production Anthropic harness, real LLM tool loop, paper/live order execution from a routine, scheduler, FastAPI dashboard, Hetzner deployment.
