#!/usr/bin/env bash
# Launch gamer-Claude in game/ to start a NetHack session.
#
# Usage:
#   ./run.sh                          # fresh game, default prompt
#   ./run.sh "your prompt"            # fresh game, custom prompt
#   ./run.sh --resume                 # resume the most recent trajectory
#                                     # AND the Claude session that was
#                                     # last driving it (no extra prompt)
#   ./run.sh --resume "your prompt"   # same + send the prompt as next msg
#
# The --resume flow:
#   1. Sets NETHACK_TRAJ=latest so the MCP server replays the newest
#      trajectory file in game/trajectory/.
#   2. Scans that trajectory for the most-recent `claude_session` event
#      (logged by the PreToolUse hook in game/hooks/log_claude_session.py)
#      and passes its session_id to `claude --resume <id>` so the same
#      conversation picks up where it left off. Falls back to a fresh
#      claude convo if no claude_session events were recorded.
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

DEFAULT_PROMPT="You are playing NetHack. Your game is already started — call observe() to see your character, then play. Take it turn by turn — observe, decide, act. Do your best to play strategically optimally, and ultimately win."

if [[ "${1:-}" == "--resume" ]]; then
    export NETHACK_TRAJ=latest
    shift

    # Find the Claude session_id that last drove the most-recent trajectory.
    LATEST_TRAJ=$(ls -t trajectory/*.jsonl 2>/dev/null | head -1 || true)
    SESSION_ID=""
    if [[ -n "$LATEST_TRAJ" ]]; then
        SESSION_ID=$(python3 - "$LATEST_TRAJ" <<'PY'
import json, sys
last = ""
with open(sys.argv[1]) as f:
    for line in f:
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("event") == "claude_session":
            last = obj.get("session_id") or last
print(last)
PY
)
    fi

    PROMPT="${1:-}"
    if [[ -n "$SESSION_ID" ]]; then
        # Resume Claude convo. Only pass the prompt if the user explicitly
        # gave one — bare --resume just continues the conversation.
        if [[ -n "$PROMPT" ]]; then
            exec claude --resume "$SESSION_ID" "$PROMPT"
        else
            exec claude --resume "$SESSION_ID"
        fi
    fi
    # No claude_session events recorded (legacy trajectory) — resume the
    # game but start a fresh Claude convo with the default or given prompt.
    exec claude "${PROMPT:-$DEFAULT_PROMPT}"
fi

PROMPT="${1:-$DEFAULT_PROMPT}"
exec claude "$PROMPT"
