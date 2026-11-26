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

need uv "Install uv from https://docs.astral.sh/uv/getting-started/installation/"
need npm "Install Node.js 20+ from https://nodejs.org/"

if [ ! -f "$ROOT/.env" ]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
  echo "Created .env from .env.example. Set CTF_WORKBENCH_SESSION_SECRET before starting."
fi

echo "Installing Python dependencies..."
uv sync --group dev

echo "Installing frontend dependencies..."
npm --prefix "$ROOT/apps/web" install

echo "Install complete. Run ./scripts/dev.sh"
