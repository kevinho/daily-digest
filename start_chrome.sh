#!/usr/bin/env bash
set -euo pipefail

CHROME_BIN=${CHROME_BIN:-"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"}
USER_DATA_DIR=${USER_DATA_DIR:-"/Users/hechangbin/Library/Application Support/Google/Chrome"}
DEBUG_PORT=${DEBUG_PORT:-9222}

"$CHROME_BIN" \
  --remote-debugging-port="$DEBUG_PORT" \
  --user-data-dir="$USER_DATA_DIR" \
  --no-first-run \
  --no-default-browser-check \
  >/dev/null 2>&1 &
PID=$!
echo "Started Chrome (PID=$PID) with remote debugging on port $DEBUG_PORT using $USER_DATA_DIR"
