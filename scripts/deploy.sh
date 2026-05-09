#!/usr/bin/env bash
# Deploy Darkhorse to the Linode production host via Tailscale SSH.
#
# Prerequisites:
#   - Tailscale running on both your Mac and the Linode host
#   - SSH access to the Linode host via Tailscale hostname
#   - The repo cloned at /opt/darkhorse on the remote host
#   - uv installed on the remote host
#
# Usage:
#   ./scripts/deploy.sh              # deploys HEAD of main
#   ./scripts/deploy.sh abc1234      # deploys specific SHA
#
# Per ADR-0010: manual SSH-via-Tailscale deploy.

set -euo pipefail

REMOTE_HOST="${DARKHORSE_DEPLOY_HOST:-darkhorse-prod}"
REMOTE_DIR="/opt/darkhorse"
SHA="${1:-HEAD}"
DISCORD_WEBHOOK_URL="${DISCORD_WEBHOOK_URL:-}"

echo "==> Deploying Darkhorse to ${REMOTE_HOST} at SHA ${SHA}"

if [ "$SHA" = "HEAD" ]; then
    SHA=$(git rev-parse HEAD)
    echo "    Resolved HEAD to ${SHA}"
fi

echo "==> Fetching latest on remote..."
ssh "$REMOTE_HOST" "cd ${REMOTE_DIR} && git fetch origin"

echo "==> Checking out ${SHA}..."
ssh "$REMOTE_HOST" "cd ${REMOTE_DIR} && git checkout ${SHA}"

echo "==> Syncing dependencies..."
ssh "$REMOTE_HOST" "cd ${REMOTE_DIR} && uv sync --frozen"

echo "==> Saving deploy marker (previous SHA for rollback)..."
ssh "$REMOTE_HOST" "cat ${REMOTE_DIR}/.deploy-sha 2>/dev/null > ${REMOTE_DIR}/.deploy-sha.prev || true"
ssh "$REMOTE_HOST" "echo ${SHA} > ${REMOTE_DIR}/.deploy-sha"

echo "==> Restarting services..."
ssh "$REMOTE_HOST" "sudo systemctl restart darkhorse-scheduler 2>/dev/null || echo '    darkhorse-scheduler not found (expected pre-Phase 3.5)'"
ssh "$REMOTE_HOST" "sudo systemctl restart darkhorse-web 2>/dev/null || echo '    darkhorse-web not found (expected pre-Phase 6)'"

echo "==> Smoke test..."
if ssh "$REMOTE_HOST" "curl -sf http://localhost:8000/healthz > /dev/null 2>&1"; then
    echo "    /healthz OK"
else
    echo "    /healthz not available (expected pre-Phase 6)"
fi

DEPLOY_TIME=$(date -Iseconds)
echo "==> Deployed ${SHA} at ${DEPLOY_TIME}"

if [ -n "$DISCORD_WEBHOOK_URL" ]; then
    curl -sf -X POST -H "Content-Type: application/json" \
        -d "{\"content\":\"Deployed \`${SHA:0:7}\` at ${DEPLOY_TIME}\"}" \
        "$DISCORD_WEBHOOK_URL" > /dev/null 2>&1 || echo "    Discord notify failed (non-fatal)"
fi

echo "==> Done."
