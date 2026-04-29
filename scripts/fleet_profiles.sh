#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-status}"
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROFILES_RAW="${HERMES_PROFILES:-personal heidou mei}"
DASHBOARD_PORT_MAP="${HERMES_DASHBOARD_PORT_MAP:-personal=9129,heidou=9130,mei=9131}"
START_DASHBOARD="${START_DASHBOARD:-1}"

read -r -a PROFILES <<<"$PROFILES_RAW"

port_for() {
  local profile="$1"
  local default_port="${2:-9129}"
  local IFS=','
  for pair in $DASHBOARD_PORT_MAP; do
    local key="${pair%%=*}"
    local value="${pair#*=}"
    if [ "$key" = "$profile" ] && [ -n "$value" ]; then
      echo "$value"
      return 0
    fi
  done
  echo "$default_port"
}

run_gateway() {
  local action="$1"
  local profile="$2"
  echo "== [$profile] gateway $action =="
  HERMES_PROFILE="$profile" "$ROOT_DIR/scripts/gateway_profile.sh" "$action"
}

run_dashboard() {
  local action="$1"
  local profile="$2"
  local port
  port="$(port_for "$profile")"
  echo "== [$profile] dashboard $action (port=$port) =="
  HERMES_PROFILE="$profile" HERMES_DASHBOARD_PORT="$port" \
    "$ROOT_DIR/scripts/dashboard_profile.sh" "$action"
}

for profile in "${PROFILES[@]}"; do
  case "$ACTION" in
    start)
      run_gateway start "$profile"
      if [ "$START_DASHBOARD" = "1" ]; then
        run_dashboard start "$profile"
      fi
      ;;
    stop)
      if [ "$START_DASHBOARD" = "1" ]; then
        run_dashboard stop "$profile" || true
      fi
      run_gateway stop "$profile" || true
      ;;
    restart)
      run_gateway restart "$profile"
      if [ "$START_DASHBOARD" = "1" ]; then
        run_dashboard restart "$profile"
      fi
      ;;
    status)
      run_gateway status "$profile" || true
      if [ "$START_DASHBOARD" = "1" ]; then
        run_dashboard status "$profile" || true
      fi
      ;;
    logs)
      echo "== [$profile] gateway logs =="
      HERMES_PROFILE="$profile" "$ROOT_DIR/scripts/gateway_profile.sh" logs || true
      ;;
    *)
      echo "Usage: $0 {start|stop|restart|status|logs}"
      exit 1
      ;;
  esac
done
