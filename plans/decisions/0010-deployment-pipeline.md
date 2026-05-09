# ADR-0010: Deployment Pipeline — GitHub Actions CI + Manual SSH Deploy

## Status

`accepted` (2026-05-09)

## Context

The system needs:
- **CI** that runs tests on every PR and on push to `main`, providing the gate for code quality
- **CD** (continuous deployment) — but the question is whether to automate it

For a single-developer, single-environment, low-cadence (small commits, weekly-ish doctrine merges) project, the operational simplicity of manual deploys often beats automation. The cost of manual deploys is small (~2 minutes per deploy) and the failure modes are debuggable in real time.

## Decision

**CI: GitHub Actions on PR + push to main. CD: manual SSH-via-Tailscale deploy in v1, with a helper script.**

Pipeline stages:

1. **CI on PR** (GitHub Actions, blocks merge if any fails):
   - Checkout
   - `uv sync --frozen`
   - `uv run ruff check`
   - `uv run ruff format --check`
   - `uv run mypy --strict src/`
   - `uv run pytest -ra` (unit + property + cassette tests)
   - Package coverage report; fail if `darkhorse` coverage < 88%
   - Dedicated risk coverage gate; fail if `darkhorse.risk` coverage < 95%
   - Estimated runtime: <2 minutes

2. **Post-merge to main** (GitHub Actions, no auto-deploy):
   - Same checks as PR (defense in depth)
   - Build wheel artifact
   - Discord webhook notification: "main updated, ready to deploy"
   - **No automatic deploy to production.** Aaron deploys manually when ready.

3. **Manual deploy** (Aaron, via SSH over Tailscale):
   ```bash
   ./scripts/deploy.sh
   ```
   The script does:
   - SSH to Hetzner via Tailscale hostname
   - `cd /opt/darkhorse && git fetch && git checkout <SHA>`
   - `uv sync --frozen`
   - `systemctl restart darkhorse-web` (or whichever services changed)
   - Smoke-test `curl https://darkhorse.<tailnet>/healthz`
   - Post Discord webhook: "deployed <SHA> at <time>"

4. **Rollback** (manual):
   ```bash
   ./scripts/rollback.sh
   ```
   Reverts to the previous deployed SHA, restarts services. Idempotent.

## Consequences

### Positive

- **Simple mental model.** "Run the deploy script when I'm ready." No mystery-deploy from a merged PR.
- **No production credentials in CI.** No need to manage Tailscale auth keys, SSH keys, or systemd remote-management permissions in GitHub Actions.
- **Aaron is in the loop.** Doctrine changes don't auto-deploy — they go through merge → manual deploy, with an explicit sanity check before production sees the change.
- **Rollback is a single command.** No git-revert-and-redeploy gymnastics.
- **CI is fast.** 2-minute PR feedback loop.

### Negative / costs

- Manual deploys mean deploying takes ~2 minutes of Aaron's attention. Not free.
- A bug fixed in `main` is not in production until Aaron deploys. Acceptable for our cadence; would be a problem at higher commit frequencies.
- Aaron has to remember to deploy. Mitigation: Discord notification on push to `main`.

### Neutral

- CD automation is a Phase 11+ enhancement. We accept manual now and revisit later.

## Alternatives considered

- **Auto-deploy on merge to main.** Standard for SaaS. Rejected for v1: requires storing SSH keys or a Tailscale OAuth-key in GitHub Secrets, adds operational surface. Trade isn't worth it at single-user, single-environment cadence.
- **GitHub Actions self-hosted runner on the VPS.** Would let `gh` CLI do deploys without exporting secrets. Rejected: complicates the runner setup, hijacks the production VPS for CI compute. Cleaner to keep CI on GitHub-hosted runners and deploy manually.
- **Argo CD / Flux / GitOps.** Overengineered for one VPS. Reject.
- **Container deploys (Docker / Podman).** Adds a containerization layer for marginal benefit at this scale. Native systemd services on Ubuntu LTS are simpler and we don't need the isolation. Defer until we have multiple deployable artifacts.
- **Heroku-style git push origin main → deploy.** Tied to PaaS providers, which we rejected in `0005-hosting.md`.

## Falsification criterion

This decision is wrong if:

- Aaron consistently forgets to deploy after merging fixes (manual gate becomes the bottleneck).
- Manual deploy time exceeds 5 minutes regularly (script complexity is wrong).
- A deployment-introduced production bug occurs that automation would have caught at the deploy step (e.g., dependency mismatch, missing migration).

In any of those cases, file ADR-NNNN to add auto-deploy.

## Linked hypotheses

None.

## Re-check date

2026-11-09 (6 months) — re-evaluate after Phase 5–6 has produced ~50–100 deploys of operational data.

## References

- `../frontendAndHosting.md` "Deployment Flow" section (original analysis)
- `../../plans/decisions/0005-hosting.md` (target environment)
- GitHub Actions docs
