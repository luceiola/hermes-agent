#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-start}"
PROFILE="${HERMES_PROFILE:-personal}"
HERMES_REPO="${HERMES_REPO:-/Users/lucas/Documents/hermes-agent}"
PROFILE_ROOT="${HERMES_PROFILE_ROOT:-$HOME/.hermes/profiles/$PROFILE}"
ENV_FILE="$PROFILE_ROOT/.env"
RUN_DIR="$PROFILE_ROOT/run"
LOG_FILE="${HERMES_GATEWAY_LOG:-$PROFILE_ROOT/logs/gateway.log}"
PID_FILE="$RUN_DIR/gateway.pid"
BIN="$HERMES_REPO/.venv/bin/python"
PATTERN="hermes_cli.main --profile $PROFILE gateway run"

is_running() {
  local pid="$1"
  [ -n "$pid" ] && ps -p "$pid" >/dev/null 2>&1
}

load_env() {
  if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
  fi
}

start_gateway() {
  mkdir -p "$RUN_DIR" "$(dirname "$LOG_FILE")"
  if [ "${HERMES_SKIP_ENV_CHECK:-0}" != "1" ]; then
    HERMES_PROFILE="$PROFILE" HERMES_PROFILE_ROOT="$PROFILE_ROOT" "$(cd "$(dirname "$0")" && pwd)/check_profile_env.sh"
  fi
  load_env
  export HERMES_HOME="$PROFILE_ROOT"

  if [ ! -x "$BIN" ]; then
    echo "Hermes python not found: $BIN"
    return 1
  fi

  if [ -f "$PID_FILE" ]; then
    local existing
    existing="$(cat "$PID_FILE" 2>/dev/null || true)"
    if is_running "$existing"; then
      echo "Gateway already running (PID $existing)"
      return 0
    fi
  fi

  nohup "$BIN" -m hermes_cli.main --profile "$PROFILE" gateway run </dev/null >>"$LOG_FILE" 2>&1 &
  local pid="$!"
  echo "$pid" > "$PID_FILE"
  sleep 2

  if is_running "$pid"; then
    echo "Gateway started (PID $pid)"
    echo "Log: $LOG_FILE"
  else
    echo "Gateway failed to start. Last logs:"
    tail -n 80 "$LOG_FILE" || true
    rm -f "$PID_FILE"
    return 1
  fi
}

stop_gateway() {
  local pid=""
  if [ -f "$PID_FILE" ]; then
    pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  fi
  if [ -z "$pid" ] || ! is_running "$pid"; then
    pid="$(pgrep -f "$PATTERN" | head -n1 || true)"
  fi

  if [ -z "$pid" ] || ! is_running "$pid"; then
    rm -f "$PID_FILE"
    echo "Gateway is not running"
    return 0
  fi

  kill "$pid" >/dev/null 2>&1 || true
  for _ in $(seq 1 20); do
    if ! is_running "$pid"; then
      break
    fi
    sleep 0.5
  done
  if is_running "$pid"; then
    kill -9 "$pid" >/dev/null 2>&1 || true
  fi

  rm -f "$PID_FILE"
  echo "Gateway stopped (PID $pid)"
}

status_gateway() {
  local pid=""
  if [ -f "$PID_FILE" ]; then
    pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  fi
  if [ -z "$pid" ] || ! is_running "$pid"; then
    pid="$(pgrep -f "$PATTERN" | head -n1 || true)"
    if [ -n "$pid" ]; then
      echo "$pid" > "$PID_FILE"
    fi
  fi

  if [ -n "$pid" ] && is_running "$pid"; then
    echo "Gateway is running (PID $pid)"
    echo "Log: $LOG_FILE"
  else
    echo "Gateway is not running"
    echo "Log: $LOG_FILE"
  fi
}

case "$ACTION" in
  start)
    start_gateway
    ;;
  stop)
    stop_gateway
    ;;
  restart)
    stop_gateway || true
    start_gateway
    ;;
  status)
    status_gateway
    ;;
  logs)
    tail -n 120 "$LOG_FILE"
    ;;
  logs-follow)
    tail -f "$LOG_FILE"
    ;;
  *)
    echo "Usage: HERMES_PROFILE=<name> $0 {start|stop|restart|status|logs|logs-follow}"
    exit 1
    ;;
esac
