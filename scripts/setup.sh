#!/usr/bin/env bash
# One-time setup for running the harness on a new machine (macOS or Linux).
#   scripts/setup.sh          # checks tools, creates .venv, runs unit tests
# For LOCAL practice games you also need a NetHack 3.6.7 build:
#   scripts/build_nethack.sh  # ~1 min; installs to ~/.local/nethack-3.6.7
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
need() { command -v "$1" >/dev/null 2>&1 || { echo "MISSING: $1 ($2)"; exit 1; }; }
need tmux "macOS: brew install tmux"
need ssh "OpenSSH client"
need git ""
PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)'; then
    PY="$c"; break
  fi
done
[ -n "$PY" ] || { echo "MISSING: Python >= 3.10 (macOS: brew install python@3.12)"; exit 1; }
[ -d .venv ] || "$PY" -m venv .venv
.venv/bin/python3 -m pip install -q --upgrade pip pytest >/dev/null
echo "python: $(.venv/bin/python3 --version), tmux: $(tmux -V), $(ssh -V 2>&1)"
PYTHONPATH=src .venv/bin/python3 -m pytest -q tests/test_nh_parse.py tests/test_nh_data.py 2>&1 | tail -2
mkdir -p play/secrets && chmod 700 play/secrets
echo "setup OK. Next: see play/ORCHESTRATOR.md"
