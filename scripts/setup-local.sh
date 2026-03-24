#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/.venv"
PYTHON_CMD=""

find_python() {
  for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

if ! PYTHON_CMD="$(find_python)"; then
  echo "A supported Python interpreter is required to set up the backend."
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is required to set up the frontend."
  exit 1
fi

echo "Using Python: $PYTHON_CMD ($("$PYTHON_CMD" --version 2>&1))"
echo "Creating backend virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
  "$PYTHON_CMD" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "Installing backend dependencies..."
python -m pip install --upgrade pip
python -m pip install -r "$BACKEND_DIR/requirements.txt"

echo "Installing frontend dependencies..."
if command -v pnpm >/dev/null 2>&1; then
  (
    cd "$FRONTEND_DIR"
    pnpm install --frozen-lockfile
  )
else
  (
    cd "$FRONTEND_DIR"
    npm install
  )
fi

if [ ! -f "$FRONTEND_DIR/.env.local" ]; then
  cat > "$FRONTEND_DIR/.env.local" <<'EOF'
BACKEND_API_URL=http://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
fi

if [ ! -f "$BACKEND_DIR/.env" ]; then
  cat > "$BACKEND_DIR/.env" <<'EOF'
ALLOWED_ORIGINS=http://localhost:3000
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
ENVIRONMENT=development
EOF
fi

echo
echo "Local setup is complete."
echo "Next time, start everything with:"
echo "  ./scripts/dev-local.sh"
echo "If you want packet capture on macOS, use:"
echo "  ./scripts/dev-local-capture.sh"
echo
echo "Optional backend dev tools can be installed with:"
echo "  ./backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt"
