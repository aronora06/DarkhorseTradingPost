# ADR-0011: Observability — structlog + JSONL + Discord + /healthz

## Status

`accepted` (2026-05-09)

## Context

Observability requirements (from `../initialPlan.md` cross-cutting rules and `../riskMitigation.md`):

- Every routine must produce a reconstructable journal of what was decided and why
- Per-call cost telemetry for the cap enforcement and the RQ5 hypothesis
- Failures must be loud (Discord, never silent)
- A health endpoint for external watchers (Cloudflare Worker, Mac launchd)
- An audit log separate from the journal for privileged actions
- Structured logs that pair cleanly with our JSONL philosophy

We deliberately avoid heavyweight observability stacks (OTel collector, Prometheus, Grafana, Loki) at v1 — the operational burden vastly exceeds the value at single-user single-VPS scale.

## Decision

**Six-piece observability stack, all lightweight:**

| Concern | Tool | Where |
|---|---|---|
| Application logs | **structlog** with JSON renderer | stdout → systemd journal |
| Decision journal (L1) | **JSONL writer** with schema validation | `memory/<sleeve>/journal/YYYY-MM-DD.jsonl` |
| Cost telemetry | **JSONL writer** | `memory/cost/YYYY-MM-DD.jsonl` |
| Audit log | **Append-only JSONL writer** | `memory/audit/YYYY-MM-DD.jsonl` |
| Alerts | **Discord webhook** with severity colors + retry | Single Discord channel |
| Liveness / heartbeat | **FastAPI `/healthz`** endpoint + external watchers | Cloudflare Worker + Mac launchd |

**structlog configuration:**
- All logs are JSON in production (greppable from `journalctl`)
- Bind context per-routine: `routine`, `sleeve`, `doctrine_version`, `prompt_version`
- Log level: `INFO` default, `DEBUG` enabled via env var
- Every LLM call logs: model, role, input_tokens, cache_creation_tokens, cache_read_tokens, output_tokens, usd_cost, duration_ms

**Discord integration:**
- One channel per environment (we have one environment in v1: production)
- Webhook URL stored in `/etc/darkhorse/.env`
- `src/darkhorse/notify.py` wraps the webhook with severity → color mapping (green = info, yellow = warning, red = error)
- Retry with exponential backoff (3 attempts, 1/3/9s); on permanent failure, write to a local dead-letter file at `memory/dead_letter/discord-YYYY-MM-DD.jsonl`
- Routine-level alerts include: routine name, sleeve, link/path to the journal entry, exception class if any

**Health endpoint:**
- `GET /healthz` returns 200 with JSON `{"status": "ok", "timestamp": "...", "last_routine_at": "..."}`
- Cloudflare Worker pings every 5 minutes, alerts Discord after 3 consecutive failures
- Mac launchd job pings every 30 minutes during market hours (per `../riskMitigation.md` §3 R12)

**Cost telemetry:**
- Per-routine record per `../dataSchema.md` §7 (Cost Telemetry)
- Daily aggregation in the dashboard's Costs page
- Monthly cap enforcement: Anthropic Console hard cap at $10/month; structlog tripwire at 50% / 75% / 90% of cap

**What we deliberately don't do:**
- No OpenTelemetry collector. Single-process app; in-process structured logs are sufficient.
- No Prometheus scrape. SQLite mirror + dashboard's Costs page covers the use case.
- No external log aggregator (Loki, Datadog). systemd journal + the JSONL files are enough; if we ever need cross-host aggregation we'd revisit.

## Consequences

### Positive

- **Single-process simplicity.** No collectors, no agent processes, no separate observability infrastructure.
- **Greppable, durable.** Every log line is JSON; every JSONL file is line-by-line readable.
- **Phone-friendly alerts.** Discord push notifications work on Aaron's phone; one channel keeps signal high.
- **Reconstructable.** `git log doctrine/` + journal JSONL + audit JSONL + cost JSONL + structlog stdout = full forensic reconstruction of any decision.
- **No vendor lock-in.** structlog is BSD; Discord webhook is a simple HTTP call; JSONL is a file format.

### Negative / costs

- No fancy dashboards across multiple instances. We have one instance; not a cost.
- Log rotation is on Aaron, via journald + a cron tar+gzip job. systemd does most of this for us.
- Dead-letter handling needs occasional cleanup. A weekly cron prunes Dead-letter files older than 30 days that are confirmed delivered or expired.

### Neutral

- We accept the dashboard is the sole "visualization" tool. No Grafana, no Datadog. The dashboard reads the same JSONL + SQLite that everything else writes to.

## Alternatives considered

- **OpenTelemetry collector + Jaeger/Tempo.** Distributed tracing for a single-process app is overkill. Reject.
- **Prometheus + Grafana.** Pull-based metrics for a service that emits metrics structurally to JSONL is unnecessary work. Reject.
- **Sentry / Honeycomb / Datadog.** Vendor lock-in, monthly costs, more surface than benefit. Reject for v1; revisit if/when we have multi-host or higher uptime requirements.
- **Plain `logging` instead of structlog.** Workable but every log call gets verbose. structlog's binding context (every log line includes routine + sleeve + doctrine_version automatically) is worth the small dependency.
- **Loguru.** Nice ergonomics, less structured. structlog wins on cross-team standards (everyone knows what JSON logs look like).

## Falsification criterion

This decision is wrong if:

- A production incident reveals we couldn't reconstruct what happened from the available logs.
- Discord alert delivery fails > 5% of the time over a week (suggests we need a more robust dead-letter path).
- Log volume on the VPS exceeds disk budget (would force log rotation tuning or external aggregation).
- The dashboard's Costs page is too slow to be useful (suggests SQLite mirror needs more aggressive indexing).

## Linked hypotheses

- `../../RESEARCH/hypotheses/H_005.md` — Tiered+cached strategy yields edge:cost ≥ 5:1 (RQ5). Cost telemetry is the data substrate for measuring this.

## Re-check date

2026-11-09 (6 months).

## References

- `../dataSchema.md` §7 (cost telemetry), §9 (audit log)
- `../riskMitigation.md` §3 R6/R12 (failure modes that require Discord alerting and heartbeat watching)
- `../frontendAndHosting.md` "Monitoring" section
- structlog docs (https://www.structlog.org/)
