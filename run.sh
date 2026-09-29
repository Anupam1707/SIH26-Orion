#!/usr/bin/env bash
# Starts the MuleTrail backend (:8000) and frontend (:5173). Ctrl+C stops both.
# Works on macOS/Linux and Git Bash. On Windows PowerShell use .\run.ps1 instead.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
backend="$root/backend"
frontend="$root/frontend"

if [ -x "$backend/.venv/Scripts/python.exe" ]; then
  py="$backend/.venv/Scripts/python.exe"   # Windows layout (Git Bash)
else
  py="$backend/.venv/bin/python"
fi

if [ ! -x "$py" ]; then
  echo "Creating backend virtualenv..."
  if command -v py >/dev/null 2>&1; then
    py -3.11 -m venv "$backend/.venv"
  elif command -v python3.11 >/dev/null 2>&1; then
    python3.11 -m venv "$backend/.venv"
  else
    python3 -m venv "$backend/.venv"
  fi
  [ -x "$backend/.venv/Scripts/python.exe" ] && py="$backend/.venv/Scripts/python.exe" || py="$backend/.venv/bin/python"
  "$py" -m pip install -q -r "$backend/requirements.txt"
fi
[ -d "$frontend/node_modules" ] || (cd "$frontend" && npm install)

(cd "$backend" && "$py" -m app.precompute)

pids=()
cleanup() { for p in "${pids[@]:-}"; do [ -n "$p" ] && kill "$p" 2>/dev/null || true; done; }
trap cleanup EXIT INT TERM

(cd "$backend" && exec "$py" -m uvicorn app.main:app --host 127.0.0.1 --port 8000) &
pids+=($!)
(cd "$frontend" && exec npm run dev -- --host 127.0.0.1) &
pids+=($!)

echo
echo "ORION is starting:  http://127.0.0.1:5173   (API: http://127.0.0.1:8000/health)"
echo "Press Ctrl+C to stop both."
wait -n
