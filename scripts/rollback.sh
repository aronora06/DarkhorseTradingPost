#!/usr/bin/env bash
# Rollback Darkhorse on the Linode production host to the previous deploy.
#
# Reads the previous SHA from /opt/darkhorse/.deploy-sha.prev (written by
# deploy.sh) and re-deploys to that SHA. Idempotent — running rollback
# twice in a row is a no-op (the "previous" stays the same).
#
# Usage:
#   ./scripts/rollback.sh
#
# Per ADR-0010: manual SSH-via-Tailscale rollback.

set -euo pipefail

REMOTE_HOST="${DARKHORSE_DEPLOY_HOST:-darkhorse-prod}"
REMOTE_DIR="/opt/darkhorse"
DISCORD_WEBHOOK_URL="${DISCORD_WEBHOOK_URL:-}"

echo "==> Reading previous deploy SHA from ${REMOTE_HOST}..."
PREV_SHA=$(ssh "$REMOTE_HOST" "cat ${REMOTE_DIR}/.deploy-sha.prev 2>/dev/null || echo ''")

if [ -z "$PREV_SHA" ]; then
    echo "ERROR: No previous deploy SHA found at ${REMOTE_DIR}/.deploy-sha.prev"
    echo "       Cannot rollback — no prior deployment recorded."
    exit 1
fi

echo "==> Rolling back to ${PREV_SHA}"

echo "==> Checking out ${PREV_SHA}..."
ssh "$REMOTE_HOST" "cd ${REMOTE_DIR} && git checkout ${PREV_SHA}"

echo "==> Syncing dependencies..."
ssh "$REMOTE_HOST" "cd ${REMOTE_DIR} && uv sync --frozen"

echo "==> Updating deploy marker..."
ssh "$REMOTE_HOST" "echo ${PREV_SHA} > ${REMOTE_DIR}/.deploy-sha"

echo "==> Restarting services..."
ssh "$REMOTE_HOST" "sudo systemctl restart darkhorse-scheduler 2>/dev/null || echo '    darkhorse-scheduler not found (expected pre-Phase 3.5)'"
ssh "$REMOTE_HOST" "sudo systemctl restart darkhorse-web 2>/dev/null || echo '    darkhorse-web not found (expected pre-Phase 6)'"

echo "==> Smoke test..."
if ssh "$REMOTE_HOST" "curl -sf http://localhost:8000/healthz > /dev/null 2>&1"; then
    echo "    /healthz OK"
else
    echo "    /healthz not available (expected pre-Phase 6)"
fi

ROLLBACK_TIME=$(date -Iseconds)
echo "==> Rolled back to ${PREV_SHA} at ${ROLLBACK_TIME}"

if [ -n "$DISCORD_WEBHOOK_URL" ]; then
    curl -sf -X POST -H "Content-Type: application/json" \
        -d "{\"content\":\"Rolled back to \`${PREV_SHA:0:7}\` at ${ROLLBACK_TIME}\"}" \
        "$DISCORD_WEBHOOK_URL" > /dev/null 2>&1 || echo "    Discord notify failed (non-fatal)"
fi

echo "==> Done."
