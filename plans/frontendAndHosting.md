# Darkhorse Trading Outpost — Frontend & Hosting Plan

## Goals

A single-user dashboard that lets Aaron see live state at a glance from anywhere, plus the production hosting setup the agent runs on.

The dashboard is a **read-mostly observability tool** with two write actions: toggle the kill-switch, approve/reject doctrine PRs. Everything else the agent does autonomously; Aaron's job is to watch and intervene when needed.

## Non-Goals

- Multi-user / public access
- Real-time charting at sub-second resolution (we trade slow; the dashboard updates every few minutes)
- Order entry by Aaron through the UI (intentional — orders are the agent's job; Aaron's tool for taking control is the kill-switch, not a manual order panel)
- Beautiful design. Useful > pretty.

## Information Architecture

Pages, in priority order:

### 1. Home / Overview

The page Aaron opens 90% of the time. Designed to take 30 seconds to read.

- Total NAV, today's P&L, MTD P&L, vs SPY MTD
- Sleeve cards: Core ($X / $900, +/-Y%), Satellite ($X / $100, +/-Y%)
- Kill-switch status: green / red, with toggle (confirm modal)
- Halt status: any active halts, with reason and unfreeze button
- Last 3 decisions feed (ticker, action, confidence, time)
- Cost MTD vs cap

### 2. Portfolio detail

- Per-sleeve: positions, cost basis, current value, unrealized P&L, % of sleeve, days held
- Cash by sleeve
- Top contributors / detractors today

### 3. Performance

- Equity curve per sleeve, plus blended, plus SPY benchmark, configurable window
- Drawdown chart per sleeve with halt and uncle-point thresholds drawn as horizontal lines
- Rolling Sharpe vs SPY (6-month, 3-month)
- Trades per week, win rate, average winner, average loser

### 4. Calibration

- Confidence-bucket histogram with realized win rate per bucket
- Calibration error over time (rolling 4-week)
- Highlight buckets currently in alert (>10pp drift)

### 5. Decisions feed

- Reverse-chronological journal feed
- Each entry expandable to show: full reasoning, sub-agent debate (bull/bear), risk-manager verdict, outcome (if horizon elapsed)
- Filters: sleeve, action (BUY/SELL/NO_TRADE), ticker, confidence range, outcome (winner/loser/open)

### 6. Lessons & doctrine

- Active lessons with sunset dates
- Retired/falsified history
- Doctrine version history (`git log doctrine/`)
- Open doctrine PRs awaiting Aaron's review (link to GitHub)

### 7. Anti-patterns

- Browse the catalog
- Click an entry → see all decisions tagged with this anti-pattern in their post-mortems

### 8. Costs

- Spend MTD by provider (Anthropic, Perplexity, Tavily, Finnhub)
- Spend by routine (which routine is consuming the most tokens?)
- Cache hit rate by routine
- Per-decision cost histogram
- Tripwire status from `riskMitigation.md` §5

### 9. System health

- Last firing time of each routine
- Routine success/failure rate over the last 30 days
- Tool error rates (Alpaca 5xx count, Sonar timeouts, etc.)
- Backup status (last successful backup, size)
- Heartbeat watchers status

## Technology Stack

### Backend

**FastAPI** in `src/darkhorse/web/app.py`. Same Python project as the agent — shares config, database, journal readers. No separate service.

Read endpoints query the journal (JSONL or SQLite-indexed view of it), positions snapshots, calibration log, doctrine git history. Write endpoints are limited to kill-switch toggle and doctrine-PR approval.

### Frontend

**HTMX + Alpine.js + Tailwind**, server-rendered from FastAPI via Jinja templates. Reasoning:

- Single user, no SPA complexity needed
- Charts via Plotly.js (loaded once, hydrated server-side data)
- HTMX gives interactivity (live updates via polling or SSE) without a build pipeline
- Total dependencies: <500KB
- Aaron can read the entire frontend in one sitting

**Reject:** Next.js, full React SPA — overkill for a single-user dashboard. Adds a build pipeline, deployment complexity, and a JS ecosystem to keep updated. The minute the frontend needs heavy interactivity (e.g., custom chart interactions), revisit.

**Charts:** Plotly.js for the equity curve, drawdown chart, and calibration. Chart.js as a fallback if Plotly is too heavy.

### Database

**SQLite** for v1. The journal stays in JSONL (source of truth, durable, greppable), and a SQLite mirror is built nightly for fast queries. The dashboard reads from SQLite; nothing important *only* lives there.

If/when SQLite stops cutting it (multi-GB journal, complex analytic queries), upgrade to Postgres on the same VPS.

### Auth

**Tailscale-only access initially.** The dashboard binds to the Tailscale interface; not reachable from the public internet. Aaron's phone is on the tailnet via the Tailscale app. This is the simplest possible auth: presence on the tailnet *is* the credential.

**Optional follow-up:** Cloudflare Access (free tier, up to 50 users) for browser-anywhere access without VPN. Requires a Cloudflare Tunnel. Worth doing once Aaron has used the Tailscale-only setup for a month and decides if he wants public-internet reachability.

**Reject:** custom session-cookie auth, OAuth-with-Google homebrew. Single-user app; we shouldn't be writing auth code.

## Hosting

### Provider

> **Hosting decision now codified in [ADR-0005](decisions/0005-hosting.md): Linode Nanode 1GB in Newark US ($5/mo, 1 vCPU / 1 GB RAM / 25 GB SSD / 1 TB bandwidth).** Aaron chose Linode for familiarity and US billing. Hetzner CX22 remains the documented fallback. See `RESEARCH/architecture/hosting_comparison.md` for the full comparison.

**Original recommendation: Linode (Akamai) Nanode 1GB — $5/month** in a US region (Newark or Dallas, depending on Alpaca's data center latency — verify in Phase 7).

Specs: 1 vCPU, 1GB RAM, 25GB SSD, 1TB egress. Sufficient for the agent + FastAPI + SQLite + nginx. RAM is the binding constraint; if multi-agent debate consumes more than expected, upgrade to 2GB ($12/mo).

### Alternatives considered

- **Hetzner CX22** (~€4/mo, 4GB RAM, 2 vCPU) — previously recommended in ADR-0005 (since superseded by Linode). Remains the documented fallback.
- **Vultr Regular Cloud** ($5/mo, 1GB) — comparable to Linode.
- **AWS Lightsail** ($5/mo) — vendor lock-in to AWS ecosystem, and the savings aren't worth it for a single instance.
- **Fly.io** — interesting for stateless apps; our app has state; not the right fit.
- **Aaron's own machine** — rejected. Personal trading on a laptop that goes to sleep is a recipe for missed routines.

### OS & runtime

- Ubuntu 24.04 LTS (or whatever's current LTS in Phase 7)
- Python via `uv` (fastest install + reproducible)
- systemd services for the agent scheduler, the FastAPI app, the watchdogs
- nginx as reverse proxy (or Caddy for simpler HTTPS)

### Routine scheduling

Two paths considered:

1. **Claude Code routines (cloud-hosted by Anthropic)** — what the reference video uses. Pros: zero infra. Cons: opaque failure modes, no local logs, depends on Claude Code's reliability.
2. **systemd timers on the VPS** — more control, all logs local, can run any model not just Claude. But we lose the ergonomic of "edit a routine, push to Anthropic."

**Decision (subject to ADR-0006 in Phase 2):** primary scheduler is **systemd timers on the VPS**, calling our own Python entry points which then call Claude/whichever model. This gives us full visibility and lets us swap models freely. Claude Code routines remain available as a backup scheduler for redundancy if we want.

### Networking

- Tailscale installed on the VPS, on Aaron's Mac, on Aaron's phone
- Public SSH disabled; SSH only via Tailscale
- nginx binds the dashboard to the Tailscale interface only
- HTTPS via Let's Encrypt + Tailscale TLS (Tailscale issues certs for tailnet hostnames)
- Alpaca API egress goes out via the public interface (necessary)

### Backups

- Daily cron job (3 AM ET) tarballs `memory/`, `doctrine/`, journal SQLite mirror, config (excluding secrets), encrypts with `age`, uploads to **Backblaze B2** (~$0.006/GB/month — pennies for our volume)
- Retention: 30 daily, 12 monthly
- Restore drill quarterly: spin a fresh VPS, pull latest backup, confirm system runs

### Monitoring

- **Discord webhook** for all alerts (single channel, color-coded by severity)
- **Cloudflare Worker (free tier)** pings the FastAPI `/healthz` endpoint every 5 min; alerts if 3 consecutive failures
- **Local launchd job on Aaron's Mac** independently pings the same endpoint as a redundant watcher
- **Anthropic spend monitor** — daily script that pulls usage and alerts at 50%, 75%, 90% of monthly cap
- **systemd unit health** — service failures trigger systemd `OnFailure=` units that post to Discord

### Secrets

- `.env` file in `/etc/darkhorse/`, owned by root, mode 600
- Never in source control (verified by pre-commit hook)
- Rotation policy: annual for API keys; immediate on any suspected leak

## Cost Estimate

(Updated post ADR-0005 revision to use the Linode pricing. Hetzner pricing preserved for fallback reference.)

| Item | Monthly |
|---|---|
| Linode Nanode 1GB Newark (per ADR-0005) | $5.00 |
| _Fallback: Hetzner Cloud CX22 Ashburn_ | _~$4.20_ |
| Backblaze B2 backups | <$0.10 |
| Tailscale (free tier) | $0 |
| Cloudflare Tunnel + Access (free tier) | $0 |
| Domain name (optional, for tailnet hostname) | ~$1/mo amortized |
| **Total infra (Linode)** | **~$6.10/month** |

Plus the API costs in `riskMitigation.md` §2 (~$3/mo target). **Total operational cost: ~$8.30/month**, or ~0.83% of NAV/yr at $1k starting capital.

## Deployment Flow

For a single-developer project, Continuous Deployment is overkill. The flow:

1. Local: edit, test (`pytest`, `mypy`)
2. Push to GitHub
3. SSH to VPS via Tailscale, `git pull`
4. systemd: `systemctl restart darkhorse-web` (or whichever service changed)
5. Smoke test via dashboard
6. If anything breaks: `git revert`, repeat

A future-Aaron improvement is GitHub Actions auto-deploy via Tailscale, but that's a Phase 11+ nicety.

## Failure Modes & Responses

| Failure | Response |
|---|---|
| VPS down | Routines miss, journals stale; Cloudflare Worker pages Aaron; restart or rebuild from backup |
| nginx misconfig | Dashboard down but agent runs unaffected; fix offline, restart |
| Anthropic API outage | Routines fail loud, Discord alert, no trades that cycle |
| Alpaca outage | Same — fail loud, no trades, reconcile next routine |
| SQLite corruption | Rebuild from JSONL journal (the source of truth) |
| Tailscale outage | Aaron can't access dashboard; Cloudflare Access fallback (if enabled) |
| Disk full | systemd alerts via OnFailure; rotate backups, prune old logs |
| Backup failure | Discord alert; investigate within 24h; if persistent, fail back to local-only and address root cause |

## Open Decisions for Phase 7

- Linode Newark latency check against Alpaca's API
- Whether to use Caddy (simpler HTTPS) or nginx (more control)
- Plotly vs Chart.js (start with Plotly, fall back if perf issue)
- Cloudflare Access enable/skip at launch
