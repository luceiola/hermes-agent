#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROFILE="${HERMES_PROFILE:-personal}"
PROFILE_ROOT="${HERMES_PROFILE_ROOT:-$HOME/.hermes/profiles/$PROFILE}"
SKILL_SRC_DIR="${HERMES_SKILLS_SOURCE_DIR:-$ROOT_DIR/skills/$PROFILE}"
SKILL_DEST_LINK="$PROFILE_ROOT/skills/$PROFILE"

if [ ! -d "$SKILL_SRC_DIR" ]; then
  echo "[warn] Missing skills source for profile '$PROFILE': $SKILL_SRC_DIR"
  echo "[warn] Falling back to personal skills"
  SKILL_SRC_DIR="$ROOT_DIR/skills/personal"
  SKILL_DEST_LINK="$PROFILE_ROOT/skills/personal"
fi

mkdir -p "$PROFILE_ROOT/skills"

ln -sfn "$SKILL_SRC_DIR" "$SKILL_DEST_LINK"

echo "Linked skill : $SKILL_DEST_LINK -> $SKILL_SRC_DIR"
