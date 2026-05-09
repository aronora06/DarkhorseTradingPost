# ADR-0012: Configuration & Secrets — pydantic-settings + .env + settings.toml

## Status

`accepted` (2026-05-09)

## Context

The system has three categories of "configuration":

1. **Secrets** — API keys (Anthropic, Alpaca, Perplexity, Tavily, Finnhub, SnapTrade, Discord webhook). Must never enter source control.
2. **Environment-specific config** — DB paths, host bindings, environment tags ("production" vs "dev"). Vary by environment but aren't secret.
3. **Tunable parameters** — cap thresholds, retry counts, cache TTLs, schedule offsets. Stable across environments; edited deliberately by Aaron.

These need to be loaded with type safety, fail loudly on misconfiguration, and be easy for Aaron to edit without redeploying code.

## Decision

**Three-source configuration loaded by pydantic-settings into a single typed Settings model:**

| Source | Format | Purpose | Location |
|---|---|---|---|
| `.env` | KEY=VALUE | Secrets | Production: `/etc/darkhorse/.env` (mode 600, root-owned); Dev: project root `.env` (gitignored) |
| `settings.toml` | TOML | Tunable parameters | `config/settings.toml`, committed to git |
| Environment variables | KEY=VALUE | Override anything for ad-hoc / test | Shell env at process start |

**Precedence (highest first):** environment variable > `.env` > `settings.toml` > pydantic field default.

**Settings model:**
```python
# src/darkhorse/config.py
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        toml_file="config/settings.toml",
        env_nested_delimiter="__",
    )

    # Secrets (loaded from .env)
    anthropic_api_key: SecretStr
    alpaca_live_api_key: SecretStr
    alpaca_live_secret_key: SecretStr
    alpaca_paper_api_key: SecretStr
    alpaca_paper_secret_key: SecretStr
    perplexity_api_key: SecretStr
    tavily_api_key: SecretStr
    finnhub_api_key: SecretStr
    snaptrade_client_id: SecretStr
    snaptrade_consumer_key: SecretStr
    discord_webhook_url: SecretStr

    # Tunable (loaded from settings.toml or env)
    core_sleeve_target_usd: int = 900
    satellite_sleeve_target_usd: int = 100
    max_position_pct_core: float = 0.10
    max_position_pct_satellite: float = 0.50
    daily_loss_kill_pct_core: float = 0.02
    daily_loss_kill_pct_satellite: float = 0.10
    drawdown_halt_pct_core: float = 0.15
    confidence_floor: float = 0.7
    monthly_compute_cap_usd: float = 10.0
    routine_cost_cap_usd: float = 0.50

    # Environment-specific (env or env var)
    env: str = "production"  # "production" | "dev"
    journal_dir: Path = Path("memory")
    sqlite_mirror_path: Path = Path("memory/index.sqlite")
```

**Loading rule:** `Settings()` is called once at process start. Any required field missing → fail fast with a clear error message. No silent defaults for secrets.

**File locations on production:**
- `/opt/darkhorse/` — code (read-only by service user)
- `/etc/darkhorse/.env` — secrets (mode 600, root)
- `/var/lib/darkhorse/memory/` — runtime state (writable by service user)
- `/var/log/darkhorse/` — logs (managed by systemd journal)

The Settings model knows nothing about file paths — those are passed in from the systemd unit's `Environment=` directives, which point to the right `/etc/darkhorse/.env` and `config/settings.toml`.

## Consequences

### Positive

- **Type-safe config.** Every parameter has a type and a sensible default; pydantic validates at load.
- **No string-typed config.** `settings.daily_loss_kill_pct_core: float` not `getenv("DAILY_LOSS_KILL_PCT_CORE", "0.02")`.
- **Three sources, clear precedence.** Aaron always knows which source wins.
- **Secrets never in code or git.** Pre-commit hook enforces no `.env` files in commits.
- **`SecretStr` prevents accidental logging.** `print(settings)` emits `'***'` for secret fields.
- **Re-loadable.** A doctrine PR that changes `daily_loss_kill_pct_core` is a `settings.toml` edit, not a code change. Restart the service to pick it up.

### Negative / costs

- One more dependency (`pydantic-settings`). Worth it for the type safety.
- Editing `settings.toml` and forgetting to restart the service is a foot-gun. Mitigated by a deploy script reminder and a `last_loaded_at` timestamp in the dashboard.

### Neutral

- We don't do live config reloads. settings.toml change → systemctl restart. Acceptable; we don't have hot-path config that changes mid-routine.

## File templates

**`.env.example`** (committed; the real `.env` is gitignored):
```env
# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Alpaca (live)
ALPACA_LIVE_API_KEY=...
ALPACA_LIVE_SECRET_KEY=...

# Alpaca (paper)
ALPACA_PAPER_API_KEY=...
ALPACA_PAPER_SECRET_KEY=...

# Research / news
PERPLEXITY_API_KEY=...
TAVILY_API_KEY=...
FINNHUB_API_KEY=...

# SnapTrade (Fidelity read-only)
SNAPTRADE_CLIENT_ID=...
SNAPTRADE_CONSUMER_KEY=...

# Notifications
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

**`config/settings.toml`**:
```toml
core_sleeve_target_usd = 900
satellite_sleeve_target_usd = 100
max_position_pct_core = 0.10
max_position_pct_satellite = 0.50
daily_loss_kill_pct_core = 0.02
daily_loss_kill_pct_satellite = 0.10
drawdown_halt_pct_core = 0.15
confidence_floor = 0.7
monthly_compute_cap_usd = 10.0
routine_cost_cap_usd = 0.50
```

**Pre-commit secret check:**
- gitleaks (or detect-secrets) configured in `.pre-commit-config.yaml`
- Matches Anthropic / Alpaca key prefixes; refuses commit on match

## Alternatives considered

- **All in `.env`, no TOML.** Workable but tunable parameters are all strings; loses type safety; bigger `.env` is hard to read.
- **All in `settings.toml`, secrets included.** Rejected: secrets must never be in committed files. The TOML file is gitted.
- **`hydra` for config composition.** Powerful for ML experiments; overkill for our shape. Reject.
- **`dynaconf`.** Capable but pydantic-settings is sufficient and tightly integrated with pydantic v2 (we use that everywhere else).
- **Vault / Doppler / 1Password CLI for secrets.** Real value at multi-host scale; one VPS doesn't justify the integration cost. Defer.
- **AWS Secrets Manager / Hetzner equivalent.** Same logic. We can revisit if the project grows operationally.

## Falsification criterion

This decision is wrong if:

- A secret accidentally lands in source control (catastrophic; would force a rotation and pre-commit reinforcement).
- Config drift between `.env` and `settings.toml` becomes a recurring source of bugs (e.g., the code reads from `.env` but Aaron edited `settings.toml`).
- Aaron finds himself frequently restarting the service to reload config for routine adjustments (would push us toward live config reload).

## Linked hypotheses

None.

## Re-check date

2026-11-09 (6 months).

## References

- `../riskMitigation.md` §5 (spending caps and tripwires — the parameters live in settings.toml)
- `../frontendAndHosting.md` "Secrets" section
- pydantic-settings docs
- gitleaks / detect-secrets docs
