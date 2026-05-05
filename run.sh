#!/usr/bin/env bash
# Launch gamer-Claude in game/ to start a NetHack session.
# Usage: ./run.sh                 # default starting prompt
#        ./run.sh "your prompt"   # custom starting prompt
set -euo pipefail

cd "$(dirname "$0")/game"

PROMPT="${1:-Start a new NetHack game with reset(), then play. Take it turn by turn — observe, decide, act. Do your best to play strategically optimally, and ultimately win. As much as possible, think out loud in speech blocks rather than thinking blocks}"

exec claude "$PROMPT"
