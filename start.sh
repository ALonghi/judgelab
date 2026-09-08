#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
if [[ ! -x .venv/bin/python ]]; then
  PY=""
  for candidate in python3.13 python3.14 python3.15 python3; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3,13))'; then
      PY="$candidate"; break
    fi
  done
  if [[ -z "$PY" ]]; then
    printf 'Python 3.13+ was not found. Install it, then run this launcher again.\n' >&2
    exit 1
  fi
  "$PY" -m venv .venv
fi
if ! .venv/bin/python run.py --check >/dev/null 2>&1; then
  echo 'Installing the practice dependencies (internet is needed for this step)…'
  .venv/bin/python -m pip install -r requirements.txt
fi
exec .venv/bin/python run.py "$@"
