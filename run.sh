#!/usr/bin/env bash
# Launch gamer-Claude in game/ to start a NetHack session.
# Usage: ./run.sh                 # default starting prompt
#        ./run.sh "your prompt"   # custom starting prompt
set -euo pipefail

cd "$(dirname "$0")/game"

PROMPT="${1:-You are playing NetHack. Your game is already started — call observe() to see your character, then play. Take it turn by turn — observe, decide, act. Do your best to play strategically optimally, and ultimately win.}"

exec claude "$PROMPT"
