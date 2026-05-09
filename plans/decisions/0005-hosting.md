# ADR-0005: Hosting — Hetzner Cloud CX22 (Ashburn US)

## Status

`accepted` (2026-05-09) — supersedes the Linode recommendation in `../frontendAndHosting.md`.

## Context

The agent + dashboard need a hosted environment that:
- Runs systemd timers on a reliable schedule (5 routines/day during US market hours)
- Hosts FastAPI dashboard accessible to Aaron via Tailscale
- Stores SQLite mirror + JSONL journal durably
- Has low-enough operational burden that one person manages it
- Costs ≤ ~$10/month total infrastructure

Original recommendation in `../frontendAndHosting.md` (written before the 2026-05-09 hosting research) was **Linode Nanode 1GB at $5/month**. A 2026 review surfaced a meaningfully better option.

## Decision

**Hetzner Cloud CX22 in Ashburn US East, ~$4.20/month.** Specs: 2 vCPU, 4 GB RAM, 40 GB NVMe, 20 TB bandwidth.

Provisioning:
- Ubuntu 24.04 LTS
- Tailscale installed; SSH disabled on public interfaces
- nginx (or Caddy) reverse proxy, HTTPS via Let's Encrypt
- systemd services for: scheduler, FastAPI app, watchdogs
- Daily encrypted backup to Backblaze B2 (`age`-encrypted)

## Consequences

### Positive

- **4× RAM, 2× CPU, NVMe storage, 20× bandwidth at lower price** vs Linode Nanode 1GB.
- **Same metro as Alpaca's primary US infra** (Ashburn VA / Equinix DC2). Latency to broker APIs is comparable to Linode Newark.
- 4 GB RAM is comfortable headroom for multi-agent debate with prompt caching; 1 GB on Linode would be tight.
- NVMe storage means SQLite query latency stays low even as the journal grows.
- 20 TB egress means we never worry about bandwidth costs on backups, dashboards, or API egress to providers.

### Negative / costs

- Hetzner is newer in the US (Ashburn opened 2024–2025). 6 months of operating data on the new region < the multi-decade history of Linode/AWS/DO in US East. Mitigated by the low cost of switching (provider-agnostic stack).
- Billing in EUR (minor accounting nuisance — auto-converted by Hetzner to USD on invoices).
- Less brand recognition in US-centric documentation. Migration tutorials assume Linode/DO; we'll write our own setup notes.

### Neutral

- Some Hetzner products are IPv6-only at lower price tiers. The CX22 default includes IPv4; verify at provisioning time.

## Alternatives considered

- **Linode Nanode 1GB ($5).** Original recommendation. Rejected on price/performance grounds. Acceptable fallback.
- **DigitalOcean Basic Droplet ($6).** Comparable to Linode. Rejected for the same price/performance reason.
- **Vultr ($2.50–$5).** Comparable specs to Linode at competitive prices. Less reputational track record than Linode/Hetzner. Acceptable fallback.
- **Fly.io ($30–50/mo).** PaaS with global deploy. Overpriced and over-engineered for our shape. Rejected.
- **Railway ($25–40/mo).** PaaS. Recent reliability issues (Dec 2025 EU outages). Rejected.
- **Render ($25–85/mo).** PaaS. Overpriced for our shape. Rejected.
- **AWS Lightsail ($5).** Vendor lock-in to AWS ecosystem with no offsetting benefit. Rejected.
- **Aaron's own machine.** Per `../initialPlan.md` §10 and `../frontendAndHosting.md`, rejected — laptops sleep, miss routines.

## Falsification criterion

This decision is wrong if:

- Hetzner Ashburn experiences ≥ 1 multi-hour outage in any month during Phase 4–6.
- Latency to Alpaca API consistently exceeds 50 ms p95 (vs ~15–25 ms expected).
- A pricing change or sunset announcement affects Ashburn or the CX22 tier.

In any case, fall back to Linode Newark. The migration is a tarball + DNS swap, ~2 hours of downtime.

## Linked hypotheses

None. Hosting is operational infrastructure, not a research variable.

## Re-check date

2026-11-09 (6 months).

## References

- `../../RESEARCH/architecture/hosting_comparison.md` (research note with full comparison table)
- `../frontendAndHosting.md` (deployment pattern, monitoring, secrets)
- Hetzner Cloud locations docs (Ashburn `ash-dc1`)
