#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "$1 is not on PATH. $2" >&2
    exit 1
  fi
}

port_in_use() {
  local port="$1"
  if command -v python3 >/dev/null 2>&1; then
    python3 - "$port" <<'PY'
import socket, sys
port = int(sys.argv[1])
s = socket.socket()
try:
    s.bind(("127.0.0.1", port))
except OSError:
    raise SystemExit(0)
finally:
    s.close()
raise SystemExit(1)
PY
  else
    return 1
  fi
}

need uv "Install uv, then run ./scripts/setup.sh"
need npm "Install Node.js 20+, then run ./scripts/setup.sh"

if [ ! -f "$ROOT/.env" ]; then
  echo "Missing .env. Copy .env.example to .env, set CTF_WORKBENCH_SESSION_SECRET (>= 32 chars), then retry." >&2
  exit 1
fi

API_PORT=8745
WEB_PORT=5173
if port_in_use "$API_PORT"; then
  echo "127.0.0.1:$API_PORT is already in use. Stop that process or change CTF_WORKBENCH_BIND_PORT." >&2
  exit 1
fi
if port_in_use "$WEB_PORT"; then
  echo "127.0.0.1:$WEB_PORT is already in use. Stop that process or change the Vite port." >&2
  exit 1
fi

API_PID=""
WORKER_PID=""
cleanup() {
  if [ -n "$API_PID" ]; then kill "$API_PID" 2>/dev/null || true; fi
  if [ -n "$WORKER_PID" ]; then kill "$WORKER_PID" 2>/dev/null || true; fi
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "API     http://127.0.0.1:$API_PORT/api/v1/health"
echo "UI      http://127.0.0.1:$WEB_PORT"
echo "Ctrl+C stops only these processes."

uv run python -m ctf_workbench.api &
API_PID=$!
uv run python -m ctf_workbench.jobs &
WORKER_PID=$!
npm --prefix "$ROOT/apps/web" run dev
