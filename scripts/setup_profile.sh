#!/usr/bin/env bash
set -euo pipefail

PROFILE_NAME="${1:-personal}"
HERMES_HOME_BASE="${HERMES_HOME_BASE:-$HOME/.hermes/profiles}"
PROFILE_DIR="$HERMES_HOME_BASE/$PROFILE_NAME"
RUNTIME_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROFILE_TEMPLATE_DIR="$RUNTIME_ROOT/profiles/$PROFILE_NAME"

if [ ! -d "$PROFILE_TEMPLATE_DIR" ]; then
  echo "[warn] Missing profile template dir: $PROFILE_TEMPLATE_DIR"
  echo "[warn] Falling back to: $RUNTIME_ROOT/profiles/personal"
  PROFILE_TEMPLATE_DIR="$RUNTIME_ROOT/profiles/personal"
fi

mkdir -p "$PROFILE_DIR" "$PROFILE_DIR/plugins" "$PROFILE_DIR/skills" "$PROFILE_DIR/logs" "$PROFILE_DIR/run"

if [ ! -f "$PROFILE_DIR/config.yaml" ]; then
  cp "$PROFILE_TEMPLATE_DIR/config.yaml" "$PROFILE_DIR/config.yaml"
fi
if [ ! -f "$PROFILE_DIR/.env" ]; then
  cp "$PROFILE_TEMPLATE_DIR/.env.example" "$PROFILE_DIR/.env"
fi
if [ ! -f "$PROFILE_DIR/SOUL.md" ]; then
  cp "$PROFILE_TEMPLATE_DIR/SOUL.md" "$PROFILE_DIR/SOUL.md"
fi

HERMES_PROFILE="$PROFILE_NAME" HERMES_PROFILE_ROOT="$PROFILE_DIR" "$RUNTIME_ROOT/scripts/link_profile_assets.sh"

echo "Profile ready: $PROFILE_DIR"
echo "Template     : $PROFILE_TEMPLATE_DIR"
echo "Next: edit $PROFILE_DIR/.env, then run:"
echo "  HERMES_PROFILE=$PROFILE_NAME $RUNTIME_ROOT/scripts/check_profile_env.sh"
echo "  HERMES_PROFILE=$PROFILE_NAME $RUNTIME_ROOT/scripts/gateway_profile.sh start"
