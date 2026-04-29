#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-status}"
PROFILE="${HERMES_PROFILE:-personal}"
HERMES_REPO="${HERMES_REPO:-/Users/lucas/Documents/hermes-agent}"
BIN="$HERMES_REPO/.venv/bin/python"

if [ ! -x "$BIN" ]; then
  echo "Hermes python not found: $BIN"
  exit 1
fi

case "$ACTION" in
  gateway)
    exec "$BIN" -m hermes_cli.main --profile "$PROFILE" gateway run
    ;;
  dashboard)
    exec "$BIN" -m hermes_cli.main --profile "$PROFILE" dashboard --host 127.0.0.1 --port "${HERMES_DASHBOARD_PORT:-9129}" --no-open
    ;;
  status)
    exec "$BIN" -m hermes_cli.main --profile "$PROFILE" status
    ;;
  *)
    echo "Usage: HERMES_PROFILE=<name> $0 {gateway|dashboard|status}"
    exit 1
    ;;
esac
