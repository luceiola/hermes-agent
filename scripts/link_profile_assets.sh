#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROFILE="${HERMES_PROFILE:-personal}"
PROFILE_ROOT="${HERMES_PROFILE_ROOT:-$HOME/.hermes/profiles/$PROFILE}"
SKILL_SRC_DIR="${HERMES_SKILLS_SOURCE_DIR:-$ROOT_DIR/skills/$PROFILE}"
SKILL_DEST_LINK="$PROFILE_ROOT/skills/$PROFILE"
PROFILE_LINKS_FILE="${HERMES_PROFILE_LINKS_FILE:-$ROOT_DIR/profiles/$PROFILE/links.env}"

link_pairs() {
  local destination_root="$1"
  local pairs="$2"
  local link_kind="$3"
  local IFS=','

  [ -n "$pairs" ] || return 0
  mkdir -p "$destination_root"

  for pair in $pairs; do
    [ -n "$pair" ] || continue
    local name="${pair%%=*}"
    local target="${pair#*=}"
    if [ -z "$name" ] || [ -z "$target" ] || [ "$name" = "$target" ]; then
      echo "[warn] Invalid $link_kind mapping '$pair' (expected name=/abs/path)"
      continue
    fi
    if [ ! -e "$target" ]; then
      echo "[warn] Missing $link_kind target for '$name': $target"
      continue
    fi
    ln -sfn "$target" "$destination_root/$name"
    echo "Linked $link_kind : $destination_root/$name -> $target"
  done
}

if [ ! -d "$SKILL_SRC_DIR" ]; then
  echo "[warn] Missing skills source for profile '$PROFILE': $SKILL_SRC_DIR"
  echo "[warn] Falling back to personal skills"
  SKILL_SRC_DIR="$ROOT_DIR/skills/personal"
  SKILL_DEST_LINK="$PROFILE_ROOT/skills/personal"
fi

mkdir -p "$PROFILE_ROOT/skills"

ln -sfn "$SKILL_SRC_DIR" "$SKILL_DEST_LINK"

echo "Linked skill : $SKILL_DEST_LINK -> $SKILL_SRC_DIR"

if [ -f "$PROFILE_LINKS_FILE" ]; then
  source "$PROFILE_LINKS_FILE"
  link_pairs "$PROFILE_ROOT/skills" "${EXTRA_SKILL_LINKS:-}" "skill"
  link_pairs "$PROFILE_ROOT/plugins" "${EXTRA_PLUGIN_LINKS:-}" "plugin"
fi
