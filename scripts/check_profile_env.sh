#!/usr/bin/env bash
set -euo pipefail

PROFILE="${HERMES_PROFILE:-personal}"
PROFILE_ROOT="${HERMES_PROFILE_ROOT:-$HOME/.hermes/profiles/$PROFILE}"
ENV_FILE="$PROFILE_ROOT/.env"
HERMES_REPO="${HERMES_REPO:-/Users/lucas/Documents/hermes-agent}"

if [ ! -f "$ENV_FILE" ]; then
  echo "[ERROR] Missing env file: $ENV_FILE"
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

MISSING=()
ERRORS=()
WARNINGS=()
PRIMARY_PLATFORM=""

require_key() {
  local key="$1"
  local val="${!key:-}"
  if [ -z "${val// }" ]; then
    MISSING+=("$key")
  fi
}

detect_primary_platform() {
  local configured="${HERMES_PRIMARY_PLATFORM:-$PRIMARY_PLATFORM}"
  if [ -n "${configured// }" ]; then
    PRIMARY_PLATFORM="$(echo "$configured" | tr '[:upper:]' '[:lower:]')"
    return
  fi

  if [ -n "${FEISHU_APP_ID:-}" ] || [ -n "${FEISHU_APP_SECRET:-}" ]; then
    PRIMARY_PLATFORM="feishu"
    return
  fi
  if [ -n "${QQ_APP_ID:-}" ] || [ -n "${QQ_CLIENT_SECRET:-}" ]; then
    PRIMARY_PLATFORM="qqbot"
    return
  fi
  if [ -n "${WEIXIN_ACCOUNT_ID:-}" ] || [ -n "${WEIXIN_TOKEN:-}" ]; then
    PRIMARY_PLATFORM="weixin"
    return
  fi

  PRIMARY_PLATFORM="feishu"
}

validate_feishu() {
  require_key "FEISHU_APP_ID"
  require_key "FEISHU_APP_SECRET"
  require_key "FEISHU_CONNECTION_MODE"

  if [ -n "${FEISHU_CONNECTION_MODE:-}" ]; then
    case "${FEISHU_CONNECTION_MODE}" in
      websocket|webhook)
        ;;
      *)
        ERRORS+=("FEISHU_CONNECTION_MODE must be websocket|webhook, got '${FEISHU_CONNECTION_MODE}'")
        ;;
    esac
  fi

  if [ "${FEISHU_CONNECTION_MODE:-}" = "webhook" ]; then
    if [ -z "${FEISHU_WEBHOOK_PORT:-}" ]; then
      ERRORS+=("FEISHU_WEBHOOK_PORT is required when FEISHU_CONNECTION_MODE=webhook")
    elif ! [[ "${FEISHU_WEBHOOK_PORT}" =~ ^[0-9]+$ ]]; then
      ERRORS+=("FEISHU_WEBHOOK_PORT must be numeric, got '${FEISHU_WEBHOOK_PORT}'")
    fi

    if [ -z "${FEISHU_WEBHOOK_PATH:-}" ]; then
      ERRORS+=("FEISHU_WEBHOOK_PATH is required when FEISHU_CONNECTION_MODE=webhook")
    elif [[ "${FEISHU_WEBHOOK_PATH}" != /* ]]; then
      ERRORS+=("FEISHU_WEBHOOK_PATH must start with '/', got '${FEISHU_WEBHOOK_PATH}'")
    fi

    if [ -z "${FEISHU_ENCRYPT_KEY:-}" ]; then
      WARNINGS+=("FEISHU_ENCRYPT_KEY is empty (recommended to set in webhook mode)")
    fi

    if [ -z "${FEISHU_VERIFICATION_TOKEN:-}" ]; then
      WARNINGS+=("FEISHU_VERIFICATION_TOKEN is empty (recommended to set in webhook mode)")
    fi
  fi

  if [ -n "${FEISHU_GROUP_POLICY:-}" ]; then
    case "${FEISHU_GROUP_POLICY}" in
      open|allowlist|disabled)
        ;;
      *)
        ERRORS+=("FEISHU_GROUP_POLICY must be open|allowlist|disabled, got '${FEISHU_GROUP_POLICY}'")
        ;;
    esac
  fi

  if [ "${FEISHU_GROUP_POLICY:-allowlist}" = "allowlist" ] && [ -z "${FEISHU_ALLOWED_USERS:-}" ]; then
    WARNINGS+=("FEISHU_GROUP_POLICY=allowlist but FEISHU_ALLOWED_USERS is empty")
  fi

  if [ -n "${FEISHU_APP_ID:-}" ]; then
    PROFILES_HOME="${HERMES_HOME_BASE:-$HOME/.hermes/profiles}"
    if [ -d "$PROFILES_HOME" ]; then
      for candidate_env in "$PROFILES_HOME"/*/.env; do
        [ -f "$candidate_env" ] || continue
        candidate_profile="$(basename "$(dirname "$candidate_env")")"
        if [ "$candidate_profile" = "$PROFILE" ]; then
          continue
        fi

        candidate_app_id="$(awk -F= '/^FEISHU_APP_ID=/{print $2; exit}' "$candidate_env" | tr -d '[:space:]')"
        if [ -n "$candidate_app_id" ] && [ "$candidate_app_id" = "${FEISHU_APP_ID}" ]; then
          WARNINGS+=("FEISHU_APP_ID is shared with profile '$candidate_profile' ($candidate_env); concurrent gateway runs may conflict")
        fi
      done
    fi
  fi
}

validate_qqbot() {
  require_key "QQ_APP_ID"
  require_key "QQ_CLIENT_SECRET"

  if [ -z "${QQ_ALLOWED_USERS:-}" ] && [ "${QQ_ALLOW_ALL_USERS:-false}" != "true" ]; then
    WARNINGS+=("QQ_ALLOWED_USERS is empty and QQ_ALLOW_ALL_USERS is not true (DM access may be denied by gateway policy)")
  fi
}

validate_weixin() {
  require_key "WEIXIN_ACCOUNT_ID"
  require_key "WEIXIN_TOKEN"

  if [ -n "${WEIXIN_DM_POLICY:-}" ]; then
    case "${WEIXIN_DM_POLICY}" in
      open|allowlist|disabled|pairing)
        ;;
      *)
        ERRORS+=("WEIXIN_DM_POLICY must be open|allowlist|disabled|pairing, got '${WEIXIN_DM_POLICY}'")
        ;;
    esac
  fi

  if [ -n "${WEIXIN_GROUP_POLICY:-}" ]; then
    case "${WEIXIN_GROUP_POLICY}" in
      open|allowlist|disabled)
        ;;
      *)
        ERRORS+=("WEIXIN_GROUP_POLICY must be open|allowlist|disabled, got '${WEIXIN_GROUP_POLICY}'")
        ;;
    esac
  fi

  if [ "${WEIXIN_DM_POLICY:-open}" = "allowlist" ] && [ -z "${WEIXIN_ALLOWED_USERS:-}" ]; then
    WARNINGS+=("WEIXIN_DM_POLICY=allowlist but WEIXIN_ALLOWED_USERS is empty")
  fi

  if [ "${WEIXIN_GROUP_POLICY:-disabled}" = "allowlist" ] && [ -z "${WEIXIN_GROUP_ALLOWED_USERS:-}" ]; then
    WARNINGS+=("WEIXIN_GROUP_POLICY=allowlist but WEIXIN_GROUP_ALLOWED_USERS is empty")
  fi
}

detect_primary_platform

case "$PRIMARY_PLATFORM" in
  feishu)
    validate_feishu
    ;;
  qq|qqbot)
    PRIMARY_PLATFORM="qqbot"
    validate_qqbot
    ;;
  weixin|wechat)
    PRIMARY_PLATFORM="weixin"
    validate_weixin
    ;;
  *)
    ERRORS+=("Unsupported HERMES_PRIMARY_PLATFORM='$PRIMARY_PLATFORM' (expected feishu|qqbot|weixin)")
    ;;
esac

HAS_MODEL_KEY=0
for key in OPENAI_API_KEY OPENROUTER_API_KEY ANTHROPIC_API_KEY DEEPSEEK_API_KEY GEMINI_API_KEY AZURE_OPENAI_API_KEY ARK_API_KEY; do
  if [ -n "${!key:-}" ]; then
    HAS_MODEL_KEY=1
    break
  fi
done
if [ "$HAS_MODEL_KEY" -eq 0 ]; then
  MISSING+=("OPENAI_API_KEY(or another provider key)")
fi

if [ "${#MISSING[@]}" -gt 0 ]; then
  ERRORS+=("Missing required keys: ${MISSING[*]}")
fi

if [ ! -x "$HERMES_REPO/.venv/bin/python" ]; then
  ERRORS+=("Hermes python not found: $HERMES_REPO/.venv/bin/python")
fi

if [ "${#ERRORS[@]}" -gt 0 ]; then
  echo "[ERROR] Profile env validation failed for '$PROFILE'"
  for err in "${ERRORS[@]}"; do
    echo "  - ${err}"
  done
  exit 1
fi

echo "[OK] Profile env validation passed for '$PROFILE' (platform=$PRIMARY_PLATFORM)"
if [ "${#WARNINGS[@]}" -gt 0 ]; then
  echo "[WARN]"
  for warn in "${WARNINGS[@]}"; do
    echo "  - ${warn}"
  done
fi
