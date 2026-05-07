#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROFILE="${HERMES_PROFILE:-heidou}"

usage() {
  cat <<'EOF'
Usage:
  HERMES_PROFILE=heidou scripts/vocab_extract.sh --image-url <url>
  HERMES_PROFILE=heidou scripts/vocab_extract.sh --image-file <path>

Extra args are forwarded to:
  python3 -m tools.vocab_extractor
EOF
}

if [ "$#" -eq 0 ]; then
  usage
  exit 1
fi

cd "$ROOT_DIR"
python3 -m tools.vocab_extractor --profile "$PROFILE" "$@"
