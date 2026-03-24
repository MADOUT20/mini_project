#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_VENV_PYTHON="$BACKEND_DIR/.venv/bin/python"
BACKEND_API_URL="${BACKEND_API_URL:-http://localhost:8000}"
ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-http://localhost:3000}"

cleanup_done=0
backend_pid=""
frontend_pid=""

cleanup() {
  if [ "$cleanup_done" -eq 1 ]; then
    return
  fi

  cleanup_done=1

  if [ -n "$backend_pid" ]; then
    kill "$backend_pid" 2>/dev/null || true
  fi

  if [ -n "$frontend_pid" ]; then
    kill "$frontend_pid" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

if [ "${1:-}" = "--check" ]; then
  if [ -x "$BACKEND_VENV_PYTHON" ]; then
    echo "Backend: ready ($BACKEND_VENV_PYTHON)"
  elif python3 -c "import fastapi, uvicorn, dotenv" >/dev/null 2>&1; then
    echo "Backend: ready (system python)"
  else
    echo "Backend: missing dependencies. Run ./scripts/setup-local.sh first."
    exit 1
  fi

  if [ -d "$FRONTEND_DIR/node_modules" ]; then
    echo "Frontend: ready"
  else
    echo "Frontend: missing dependencies. Run ./scripts/setup-local.sh first."
    exit 1
  fi

  exit 0
fi

if [ -x "$BACKEND_VENV_PYTHON" ]; then
  backend_cmd=("$BACKEND_VENV_PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload)
elif python3 -c "import fastapi, uvicorn, dotenv" >/dev/null 2>&1; then
  backend_cmd=(python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload)
else
  echo "Backend dependencies are missing."
  echo "Run ./scripts/setup-local.sh first."
  exit 1
fi

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  echo "Frontend dependencies are missing."
  echo "Run ./scripts/setup-local.sh first."
  exit 1
fi

if command -v pnpm >/dev/null 2>&1; then
  frontend_cmd=(pnpm dev)
else
  frontend_cmd=(npm run dev)
fi

echo "Starting backend on http://localhost:8000"
(
  cd "$BACKEND_DIR"
  export ALLOWED_ORIGINS="$ALLOWED_ORIGINS"
  "${backend_cmd[@]}"
) &
backend_pid=$!

echo "Starting frontend on http://localhost:3000"
(
  cd "$FRONTEND_DIR"
  export BACKEND_API_URL="$BACKEND_API_URL"
  export NEXT_PUBLIC_API_URL="$BACKEND_API_URL"
  "${frontend_cmd[@]}"
) &
frontend_pid=$!

echo
echo "ChaosFaction is starting without Docker."
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "Press Ctrl+C to stop both processes."
echo
echo "Note: packet capture on macOS may still need admin permissions."
echo "If sniffing fails locally, the UI still works, but packet capture may need Docker or elevated privileges."

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
