#!/usr/bin/env bash
set -euo pipefail

PROFILE="${HERMES_PROFILE:-personal}"
PROFILE_ROOT="${HERMES_PROFILE_ROOT:-$HOME/.hermes/profiles/$PROFILE}"
RUNTIME_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

RESTART_GATEWAY="${RESTART_GATEWAY:-1}"
RESTART_DASHBOARD="${RESTART_DASHBOARD:-0}"
SYNC_CONFIG="${SYNC_CONFIG:-1}"

PROFILE_TEMPLATE_DIR="$RUNTIME_ROOT/profiles/$PROFILE"
if [ ! -d "$PROFILE_TEMPLATE_DIR" ]; then
  echo "[warn] Missing profile template dir: $PROFILE_TEMPLATE_DIR"
  echo "[warn] Falling back to: $RUNTIME_ROOT/profiles/personal"
  PROFILE_TEMPLATE_DIR="$RUNTIME_ROOT/profiles/personal"
fi

SRC_SOUL="$PROFILE_TEMPLATE_DIR/SOUL.md"
DST_SOUL="$PROFILE_ROOT/SOUL.md"

if [ ! -f "$SRC_SOUL" ]; then
  echo "[ERROR] Missing source SOUL: $SRC_SOUL"
  exit 1
fi

mkdir -p "$PROFILE_ROOT"

cp "$SRC_SOUL" "$DST_SOUL"
echo "[sync] SOUL updated: $DST_SOUL"

if [ "$SYNC_CONFIG" = "1" ]; then
  SRC_CONFIG="$PROFILE_TEMPLATE_DIR/config.yaml"
  DST_CONFIG="$PROFILE_ROOT/config.yaml"
  if [ -f "$SRC_CONFIG" ]; then
    cp "$SRC_CONFIG" "$DST_CONFIG"
    echo "[sync] config updated: $DST_CONFIG"
  fi
fi

HERMES_PROFILE="$PROFILE" HERMES_PROFILE_ROOT="$PROFILE_ROOT" "$RUNTIME_ROOT/scripts/link_profile_assets.sh"

if [ "$RESTART_GATEWAY" = "1" ]; then
  HERMES_PROFILE="$PROFILE" HERMES_PROFILE_ROOT="$PROFILE_ROOT" \
    "$RUNTIME_ROOT/scripts/gateway_profile.sh" restart
fi

if [ "$RESTART_DASHBOARD" = "1" ]; then
  HERMES_PROFILE="$PROFILE" HERMES_PROFILE_ROOT="$PROFILE_ROOT" \
    "$RUNTIME_ROOT/scripts/dashboard_profile.sh" restart
fi

echo "[done] profile sync complete for '$PROFILE'"
echo "       template=$PROFILE_TEMPLATE_DIR"
echo "       SOUL: $DST_SOUL"
echo "       GATEWAY_RESTARTED=$RESTART_GATEWAY DASHBOARD_RESTARTED=$RESTART_DASHBOARD"
