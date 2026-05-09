# Hosting Comparison — 2026

**Compiled:** 2026-05-09
**Refresh by:** 2026-11-09
**Linked ADRs:** ADR-0005 (hosting)

## Summary

The original `plans/frontendAndHosting.md` recommended Linode Nanode 1GB at $5/month. A targeted 2026 review surfaces a meaningfully better option: **Hetzner Cloud Ashburn (US East)**, which now offers a CX22 equivalent at ~$4.20/month with **2 vCPU, 4GB RAM, 40GB NVMe storage, and 20TB bandwidth**.

Compared head-to-head:

| Spec | Linode Nanode 1GB ($5/mo) | Hetzner CX22 Ashburn (~$4.20/mo) |
|---|---|---|
| vCPU | 1 | 2 |
| RAM | 1 GB | 4 GB |
| Storage | 25 GB SSD | 40 GB NVMe |
| Bandwidth | 1 TB/mo | 20 TB/mo |
| Latency to Alpaca (NYC region) | Newark — comparable | Ashburn VA — comparable |
| US data center | Yes (Newark, Dallas, etc.) | Yes (Ashburn VA, since 2024) |
| Enterprise pedigree | Akamai (parent) | Hetzner (German operator, 30+ years) |

Hetzner Ashburn delivers 4x RAM, 2x CPU, NVMe storage, and 20x bandwidth at lower price.

The PaaS alternatives (Fly.io, Railway, Render) are all >$25/month for comparable resources and add operational complexity (state migrations, vendor-specific deploy tooling) without solving any problem we have. Reject for v1.

## Sources reviewed

- experte.com, "Cheap VPS 2026: Which VPS Offers the Best Value for Money?" (2026)
- DigitalOcean, "Top 10 Linode Alternatives for Cloud Computing in 2026"
- Northflank, "6 best Railway alternatives in 2026"
- Hetzner Cloud locations docs (Ashburn US East datacenter, code `ash`)
- Danube Data, "Railway/Render/Fly.io alternatives 2026"

## Key findings

### 1. Hetzner now has US East presence

Hetzner Cloud opened the Ashburn VA datacenter (`ash-dc1`) in 2024–2025 with full feature parity (Cloud Shared, Cloud Dedicated AMD, Volumes, Networks, Load Balancers, Firewalls, Snapshots, Floating IPs, Placement Groups). The original objection to Hetzner — "EU latency to Alpaca" — no longer applies.

Ashburn is the same metro as Equinix DC2, where most US financial market data infrastructure lives. Latency to Alpaca's APIs from Ashburn is essentially equivalent to Linode Newark.

### 2. Pricing-per-spec

At the $4–6/mo tier, Hetzner is the value leader by a wide margin. The legacy Linode advantage (Akamai network, US-centric pedigree) doesn't translate into measurable benefit for our workload — a single Python service + FastAPI + SQLite + nginx, low constant load, occasional bursts during routine execution.

The extra RAM matters: multi-agent debate with prompt caching means concurrent sub-agent calls hold meaningful state in process memory. 1 GB on Linode is workable but tight. 4 GB on Hetzner is comfortable headroom.

### 3. PaaS options are overpriced for our shape

| Platform | Comparable tier | Monthly cost |
|---|---|---|
| Fly.io | 2 vCPU / 4 GB | $30–50 |
| Railway | 2 vCPU / 4 GB | $25–40 |
| Render | Production tier | $25–85 |

PaaS earns its premium for teams that need git-push deploy, autoscale, multi-region, managed databases, and zero ops. Darkhorse needs none of those — single user, one machine, manual deploys, SQLite. The operational simplicity of "ssh in, git pull, restart" beats the ergonomics of `git push origin main` triggering a Railway deploy when the underlying machine is small enough for a single human to fully understand.

### 4. Reliability considerations

- Linode (Akamai) — 99.99% SLA on instances, mature US presence.
- Hetzner — 99.9% SLA on cloud, generally well-regarded reliability over a long history. Ashburn is newer; track for first 6 months.
- Railway — recent reliability issues, including Dec 2025 EU build outages. Avoid as a v1 dependency.
- Fly.io — stable but pricier and unnecessary for our shape.

### 5. Migration cost is low

The architecture is provider-agnostic: Ubuntu LTS, systemd, nginx, Tailscale, SQLite, Python via uv. Moving from one VPS to another is `tar + restore + reconfigure DNS` — a few hours of downtime, no data loss as long as backups are current. This means the choice is reversible.

## Implications for Darkhorse

**Recommendation:** Switch the hosting choice from Linode Nanode 1GB to **Hetzner Cloud CX22 Ashburn** (~$4.20/mo).

Updates required:
- ADR-0005 codifies the new choice with the comparison data above.
- `plans/frontendAndHosting.md` updated to reference the ADR for the final hosting call (light touch — keep the alternatives discussion).
- `plans/devPhaseChecklist.md` Phase 3.5 wording updated: "Linode" → "Hetzner Ashburn (or alternative per ADR-0005)".

Watch list:
- First 6 months at Hetzner Ashburn — note any reliability incidents in monthly retrospectives.
- If Hetzner pricing changes meaningfully or Ashburn is sunset, fall back to Linode Newark or DigitalOcean.

## Cost summary at chosen stack

| Item | Monthly |
|---|---|
| Hetzner CX22 Ashburn | ~$4.20 |
| Backblaze B2 backups | <$0.10 |
| Tailscale (free tier) | $0 |
| Cloudflare Tunnel + Access (free tier) | $0 |
| Domain (optional) | ~$1 amortized |
| **Total infra** | **~$5.30/month** |

Combined with API spend (~$3/mo per `riskMitigation.md` §2), total operational cost: **~$8.30/month** (was projected ~$9 with Linode). Saves ~$0.70/mo and gains 4x RAM, 2x CPU, NVMe.

## Open questions

- **Backup destination.** Backblaze B2 is excellent. Hetzner also offers Storage Box products that may be cheaper for in-region backups; verify in Phase 3.5.
- **DNS / TLS.** Cloudflare DNS + Caddy/nginx with Let's Encrypt is the obvious path. Tailscale TLS works for tailnet hostnames but doesn't cover any public name we'd want.
- **Hetzner's networking quirks.** They have IPv6-only options at lower price. v1 needs IPv4 (Alpaca, Tailscale clients). Confirm the Ashburn CX22 default includes IPv4.
