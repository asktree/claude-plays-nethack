#!/usr/bin/env bash
# Launch gamer-Claude in game/ to start a NetHack session.
#
# Usage:
#   ./run.sh                          # fresh game, default prompt
#   ./run.sh "your prompt"            # fresh game, custom prompt
#   ./run.sh --resume                 # resume the most recent trajectory
#                                     # (= NETHACK_TRAJ=latest)
#   ./run.sh --resume "your prompt"   # resume + custom prompt
#
# Other env vars the harness honors (set before invoking ./run.sh):
#   NETHACK_TRAJ=<path>          resume a specific trajectory
#   NETHACK_REPLAY_TO=<n>        replay first n steps then branch + go live
#   NETHACK_SEED_CORE=<int>      pin core seed for fresh runs
#   NETHACK_SEED_DISP=<int>      pin disp seed (defaults to core)
#   NETHACK_SEED=<int>           shorthand: sets both core and disp
#   NETHACK_CHARACTER=<spec>     "@" (random, default) or e.g. "val-hum-fem-law"
set -euo pipefail

cd "$(dirname "$0")/game"

if [[ "${1:-}" == "--resume" ]]; then
    export NETHACK_TRAJ=latest
    shift
fi

PROMPT="${1:-You are playing NetHack. Your game is already started — call observe() to see your character, then play. Take it turn by turn — observe, decide, act. Do your best to play strategically optimally, and ultimately win.}"

exec claude "$PROMPT"
