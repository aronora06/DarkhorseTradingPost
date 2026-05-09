#!/usr/bin/env bash
# Wrapper for launchd — runs market_open on weekdays only.
#
# Usage (manual):
#   ./scripts/run_market_open.sh
#
# Called automatically by the launchd plist at 9:35 AM local time.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

DAY_OF_WEEK=$(date +%u)  # 1=Monday … 7=Sunday
if [ "$DAY_OF_WEEK" -ge 6 ]; then
    echo "$(date -Iseconds) — Weekend (day $DAY_OF_WEEK), skipping."
    exit 0
fi

echo "$(date -Iseconds) — Starting market_open routine"
uv run python -m darkhorse.routines.market_open
EXIT_CODE=$?
echo "$(date -Iseconds) — market_open exited with code $EXIT_CODE"
exit $EXIT_CODE
