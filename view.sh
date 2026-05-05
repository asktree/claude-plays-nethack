#!/usr/bin/env bash
# Live-watch TUI for NetHack: colored map + inventory + auto-derived legend
# + interleaved action/reasoning log. Runs in its own terminal alongside ./run.sh.
set -euo pipefail

cd "$(dirname "$0")"
source .venv/bin/activate
exec python3 -m claude_plays_nethack.view
