#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_VENV_PYTHON="$BACKEND_DIR/.venv/bin/python"
BACKEND_API_URL="${BACKEND_API_URL:-http://localhost:8000}"
ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-http://localhost:3000}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
PROXY_ENABLED="${PROXY_ENABLED:-1}"
PROXY_HOST="${PROXY_HOST:-0.0.0.0}"
PROXY_PORT="${PROXY_PORT:-8888}"

cleanup_done=0
backend_pid=""
frontend_pid=""

ensure_port_free() {
  local port="$1"
  local name="$2"
  local use_sudo="${3:-}"
  local process_info

  if [ "$use_sudo" = "sudo" ]; then
    process_info="$(sudo lsof -nP -iTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
  else
    process_info="$(lsof -nP -iTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
  fi
  if [ -z "$process_info" ]; then
    return 0
  fi

  echo "$name cannot start because port $port is already in use."
  echo "$process_info"
  echo "Stop the existing process on port $port and run ./scripts/dev-local-capture.sh again."
  exit 1
}

get_lan_ip() {
  local default_iface=""

  default_iface="$(route -n get default 2>/dev/null | awk '/interface:/{print $2; exit}')"
  if [ -n "$default_iface" ] && ipconfig getifaddr "$default_iface" >/dev/null 2>&1; then
    ipconfig getifaddr "$default_iface"
    return 0
  fi

  for iface in en0 en1 bridge100; do
    if ipconfig getifaddr "$iface" >/dev/null 2>&1; then
      ipconfig getifaddr "$iface"
      return 0
    fi
  done
  return 1
}

cleanup() {
  if [ "$cleanup_done" -eq 1 ]; then
    return
  fi

  cleanup_done=1

  if [ -n "$backend_pid" ]; then
    sudo pkill -P "$backend_pid" 2>/dev/null || true
    sudo kill "$backend_pid" 2>/dev/null || true
    kill "$backend_pid" 2>/dev/null || true
  fi

  if [ -n "$frontend_pid" ]; then
    pkill -P "$frontend_pid" 2>/dev/null || true
    kill "$frontend_pid" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

if [ ! -x "$BACKEND_VENV_PYTHON" ]; then
  echo "Backend dependencies are missing."
  echo "Run ./scripts/setup-local.sh first."
  exit 1
fi

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  echo "Frontend dependencies are missing."
  echo "Run ./scripts/setup-local.sh first."
  exit 1
fi

if [ -x "$FRONTEND_DIR/node_modules/.bin/next" ]; then
  frontend_cmd=("$FRONTEND_DIR/node_modules/.bin/next" dev --turbo --hostname "$FRONTEND_HOST" --port "$FRONTEND_PORT")
else
  echo "Next.js local binary is missing."
  echo "Run ./scripts/setup-local.sh first."
  exit 1
fi

echo "Requesting admin access for packet capture..."
sudo -v

ensure_port_free "$FRONTEND_PORT" "Frontend"
ensure_port_free "8000" "Backend" "sudo"
ensure_port_free "$PROXY_PORT" "Proxy" "sudo"

lan_ip="$(get_lan_ip || true)"

echo "Starting backend with admin permissions on http://localhost:8000"
(
  cd "$BACKEND_DIR"
  exec sudo env ALLOWED_ORIGINS="$ALLOWED_ORIGINS" PROXY_ENABLED="$PROXY_ENABLED" PROXY_HOST="$PROXY_HOST" PROXY_PORT="$PROXY_PORT" \
    "$BACKEND_VENV_PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
) &
backend_pid=$!

echo "Starting frontend on http://localhost:3000"
(
  cd "$FRONTEND_DIR"
  export BACKEND_API_URL="$BACKEND_API_URL"
  export NEXT_PUBLIC_API_URL="$BACKEND_API_URL"
  exec "${frontend_cmd[@]}"
) &
frontend_pid=$!

echo
echo "ChaosFaction capture mode is starting."
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
if [ -n "$lan_ip" ]; then
  if [ "$PROXY_ENABLED" = "1" ]; then
    echo "Proxy:    $lan_ip:$PROXY_PORT"
  fi
fi
echo "Packet capture should work if macOS grants access to /dev/bpf."
if [ "$PROXY_ENABLED" = "1" ] && [ -n "$lan_ip" ]; then
  echo "On your phone Wi-Fi settings, set Manual Proxy -> Server $lan_ip Port $PROXY_PORT."
  echo "Leave Unused Sites empty unless your phone requires otherwise."
  echo "Then browse watched sites on the phone; only the Mac dashboard needs to stay open."
  echo "If the phone loses access later, unblock the site from the Mac dashboard or set the phone proxy back to None."
else
  echo "Phone traffic only appears in captures if the phone is routing traffic through this machine."
fi
echo "Press Ctrl+C to stop both processes."

while kill -0 "$backend_pid" 2>/dev/null && kill -0 "$frontend_pid" 2>/dev/null; do
  sleep 1
done

if ! kill -0 "$backend_pid" 2>/dev/null; then
  echo "Backend process stopped."
fi

if ! kill -0 "$frontend_pid" 2>/dev/null; then
  echo "Frontend process stopped."
fi

exit 1
