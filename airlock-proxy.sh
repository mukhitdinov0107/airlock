#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"

if [[ ! -x "$PYTHON" ]]; then
  echo "Airlock environment missing at $ROOT/.venv" >&2
  exit 1
fi

cd "$ROOT"
exec "$PYTHON" -m airlock.proxy
