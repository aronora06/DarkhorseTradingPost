# ADR-0006: Scheduler — systemd Timers (with GitHub Actions as Backup)

## Status

`accepted` (2026-05-09)

## Context

The agent runs 5 scheduled routines per weekday during US market hours (`../initialPlan.md` §3.2):

| Routine | Time (US Eastern) |
|---|---|
| `pre_market.py` | 8:30 AM |
| `market_open.py` | 9:35 AM |
| `midday_scan.py` | 12:30 PM |
| `end_of_day.py` | 4:05 PM |
| `weekly_review.py` | Friday 5:00 PM |

Plus the monthly competitive-landscape review (first weekend of each month) and event-driven triggers (Alpaca WebSocket position alerts).

Three scheduling strategies were considered:
1. **Cloud cron** — Claude Code routines (cloud-hosted by Anthropic) or similar
2. **Self-hosted cron** — systemd timers or cron on the VPS
3. **Serverless cron** — Cloudflare Workers Cron Triggers, GitHub Actions cron

## Decision

**Primary: systemd timers on the VPS. Backup: GitHub Actions cron.**

systemd timers are the load-bearing scheduler. GitHub Actions cron acts as a redundant heartbeat: if a systemd timer fails to fire, the GitHub Actions job notices the absence of a fresh journal entry and posts to Discord.

Local launchd job on Aaron's Mac provides a third layer of heartbeat watching per `../riskMitigation.md` §3 R12.

## Consequences

### Positive

- **Full local logs.** systemd captures stdout/stderr per unit; `journalctl -u darkhorse-market-open.timer` shows exactly when each routine fired and what it printed.
- **Model-agnostic.** systemd just runs `python -m darkhorse.routines.market_open`; we can swap models, add new routines, or disable a routine without coordinating with a third-party scheduler.
- **Failure modes are visible.** systemd has `OnFailure=` units that trigger a Discord notification on any unit failure — a first-class observability hook.
- **No additional dependencies.** systemd is already on the host OS. No vendor SDK to learn.
- **Belt-and-suspenders heartbeat.** The Cloudflare Worker watcher pings the FastAPI `/healthz` endpoint; a separate GitHub Actions cron checks for fresh journal entries; the local Mac launchd job independently watches both. Three failure paths to detect missed routines.

### Negative / costs

- Operating systemd timers requires comfort with the unit-file format. The learning curve is real; mitigation is a single template Aaron writes once and forks per routine.
- Time-zone handling. systemd timers run in the host's TZ (or UTC). We'll set the host to `America/New_York` for clarity (US market schedule); UTC alternative documented for any future multi-region setup.
- Daylight saving transitions. systemd handles them correctly when the host TZ is `America/New_York`; verify in unit tests for the schedule.

### Neutral

- We're not using Claude Code routines for the v1 scheduler. They remain available as an alternative if systemd reliability disappoints. The doctrine and prompts are scheduler-agnostic — porting between schedulers is a config change, not a code change.

## Alternatives considered

- **Claude Code routines as primary.** Pros: zero VPS infra for scheduling, declarative routine config. Cons: opaque failure modes ("did it run?"), no local logs, dependent on Claude Code's reliability + Anthropic's billing model evolution. Rejected as primary; remains a viable backup.
- **GitHub Actions cron as primary.** Pros: no VPS dependency for scheduling. Cons: no SSH-into-the-job for debugging; running an LLM-heavy routine in GitHub Actions is wasteful (cold start + container provisioning per routine); rate-limit concerns with multiple jobs/day. Rejected as primary; serves as backup heartbeat.
- **Cloudflare Workers Cron Triggers as primary.** Pros: free tier covers our usage, fast cold start. Cons: 30-second compute limit per invocation, awkward for long-running multi-agent debate flows. Use Workers for the heartbeat watcher, not the scheduler.
- **Plain cron.** systemd timers are strictly more featureful (proper logging, OnFailure hooks, calendar specifications) without being meaningfully harder. Choose systemd over cron.

## Falsification criterion

This decision is wrong if:

- systemd timer reliability falls below 99% (≥1 missed routine per 100 scheduled). Indicates infrastructure or systemd-config issue.
- Migrating between routines (adding, modifying, removing) becomes a >30-minute operation, indicating the unit-file template hasn't been factored well.
- Daylight-saving transitions cause a missed routine in March or November.

In any case, evaluate moving primary scheduling to Claude Code routines or GitHub Actions cron.

## Linked hypotheses

None.

## Re-check date

2026-11-09 (6 months) — after Phase 4–6 has produced reliability data.

## References

- `../frontendAndHosting.md` "Routine scheduling" section (original analysis)
- `../riskMitigation.md` §3 R12 (silent cron failure mitigation)
- systemd.timer(5) man page
