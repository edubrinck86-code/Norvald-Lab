#!/usr/bin/env bash
set -euo pipefail
LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$LAB_ROOT"
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi
if [ ! -f .venv/.lab-installed ]; then
  .venv/bin/python -m pip install -e '.[dev]'
  touch .venv/.lab-installed
fi
exec .venv/bin/python -m norvald_lab "$@"
