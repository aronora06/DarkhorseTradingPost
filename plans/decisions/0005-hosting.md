# ADR-0005: Hosting — Linode Nanode 1GB (Newark US)

## Status

`superseded` (2026-05-09) — **Aaron chose Linode** over the previously accepted Hetzner CX22 recommendation. Rationale: familiarity, US billing, proven US East presence, and $5/mo is within budget. The original Hetzner analysis is preserved in `../../RESEARCH/architecture/hosting_comparison.md` for reference.

## Context

The agent + dashboard need a hosted environment that:
- Runs systemd timers on a reliable schedule (5 routines/day during US market hours)
- Hosts FastAPI dashboard accessible to Aaron via Tailscale
- Stores SQLite mirror + JSONL journal durably
- Has low-enough operational burden that one person manages it
- Costs ≤ ~$10/month total infrastructure

Initial research recommended Hetzner CX22 in Ashburn on price/performance grounds. Aaron prefers Linode for simplicity, US billing, and established track record.

## Decision

**Linode Nanode 1GB in Newark US, $5/month.** Specs: 1 vCPU, 1 GB RAM, 25 GB SSD, 1 TB bandwidth.

Provisioning:
- Ubuntu 24.04 LTS
- Tailscale installed; SSH disabled on public interfaces
- nginx (or Caddy) reverse proxy, HTTPS via Let's Encrypt
- systemd services for: scheduler, FastAPI app, watchdogs
- Daily encrypted backup to Backblaze B2 (`age`-encrypted)

## Consequences

### Positive

- **Proven US East infrastructure** — Linode (now Akamai) has operated in Newark for over a decade. Extensive community documentation.
- **US billing in USD** — no EUR conversion or international billing complications.
- **Newark datacenter is close to Alpaca's primary US infra** (Ashburn VA / Equinix DC2). Latency ~15-30ms expected.
- 1 GB RAM is sufficient for the single-agent harness + FastAPI dashboard. If multi-agent debate (Phase 5) proves tight, upgrade to Linode 2GB ($12/mo) is a one-click resize.
- 1 TB bandwidth is more than sufficient for our use case (API calls + dashboard).

### Negative / costs

- **1 GB RAM is tighter than the Hetzner CX22's 4 GB.** May need an upgrade for multi-agent debate in Phase 5. The upgrade path is straightforward (Linode resize).
- **$0.80/mo more expensive** than Hetzner CX22 (~$4.20) for less specs. Acceptable given the simplicity/familiarity benefits.
- **25 GB SSD vs 40 GB NVMe.** Sufficient for JSONL + SQLite; monitor disk usage monthly.

### Neutral

- Linode was acquired by Akamai in 2023. No impact on VPS pricing or service quality observed through 2026.

## Alternatives considered

- **Hetzner Cloud CX22 ($4.20).** Better specs for less money. Rejected by Aaron in favor of familiarity and US billing.
- **DigitalOcean Basic Droplet ($6).** Comparable to Linode. No advantage over Linode at this tier.
- **Vultr ($2.50–$5).** Competitive pricing. Less established than Linode. Acceptable fallback.
- **Fly.io / Railway / Render ($25–85/mo).** PaaS. Overpriced for our shape.
- **AWS Lightsail ($5).** Vendor lock-in to AWS ecosystem with no offsetting benefit.
- **Aaron's own machine.** Per `../initialPlan.md` §10 and `../frontendAndHosting.md`, rejected — laptops sleep, miss routines.

## Falsification criterion

This decision is wrong if:

- Linode Newark experiences ≥ 1 multi-hour outage in any month during Phase 4–6.
- 1 GB RAM proves insufficient for the harness and requires an upgrade sooner than Phase 5.
- Latency to Alpaca API consistently exceeds 50 ms p95.

In any case, Hetzner CX22 Ashburn remains the documented fallback. The migration is a tarball + DNS swap, ~2 hours of downtime.

## Linked hypotheses

None. Hosting is operational infrastructure, not a research variable.

## Re-check date

2026-11-09 (6 months).

## References

- `../../RESEARCH/architecture/hosting_comparison.md` (research note with full comparison table)
- `../frontendAndHosting.md` (deployment pattern, monitoring, secrets)
- Linode Nanode docs: https://www.linode.com/pricing/
