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
#   ./run.sh --model fable            # gamer model override: alias (fable,
#                                     # opus, sonnet) or full model id.
#                                     # Beats the settings.json default.
#                                     # Combines with --resume and a prompt.
#   ./run.sh --effort high            # reasoning effort override (low,
#                                     # medium, high, xhigh, max). Also
#                                     # exported as NETHACK_CLAUDE_EFFORT so
#                                     # the session hook logs it into the
#                                     # trajectory's claude_session events
#                                     # (the CLI doesn't record effort in
#                                     # transcripts, so this flag is the
#                                     # only source we can log from).
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

# Parse flags (any order); the remaining positional arg is the prompt.
RESUME=0
MODEL=""
EFFORT=""
PROMPT=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --resume)   RESUME=1; shift ;;
        --model)    MODEL="${2:?--model needs a value (e.g. fable)}"; shift 2 ;;
        --model=*)  MODEL="${1#--model=}"; shift ;;
        --effort)   EFFORT="${2:?--effort needs a value (low|medium|high|xhigh|max)}"; shift 2 ;;
        --effort=*) EFFORT="${1#--effort=}"; shift ;;
        *)          PROMPT="$1"; shift ;;
    esac
done

# macOS ships bash 3.2, where "${CLAUDE_FLAGS[@]}" on an empty array trips
# `set -u` — hence the ${arr[@]+...} expansion idiom at each use site.
CLAUDE_FLAGS=()
if [[ -n "$MODEL" ]]; then
    CLAUDE_FLAGS=(--model "$MODEL")
fi
if [[ -n "$EFFORT" ]]; then
    CLAUDE_FLAGS+=(--effort "$EFFORT")
    # The CLI doesn't write effort into session transcripts, so the
    # log_claude_session hook reads it from this env var instead.
    export NETHACK_CLAUDE_EFFORT="$EFFORT"
fi

if [[ "$RESUME" == 1 ]]; then
    export NETHACK_TRAJ=latest

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

    if [[ -n "$SESSION_ID" ]]; then
        # Resume Claude convo. Only pass the prompt if the user explicitly
        # gave one — bare --resume just continues the conversation.
        if [[ -n "$PROMPT" ]]; then
            exec claude --resume "$SESSION_ID" ${CLAUDE_FLAGS[@]+"${CLAUDE_FLAGS[@]}"} "$PROMPT"
        else
            exec claude --resume "$SESSION_ID" ${CLAUDE_FLAGS[@]+"${CLAUDE_FLAGS[@]}"}
        fi
    fi
    # No claude_session events recorded (legacy trajectory) — resume the
    # game but start a fresh Claude convo with the default or given prompt.
    exec claude ${CLAUDE_FLAGS[@]+"${CLAUDE_FLAGS[@]}"} "${PROMPT:-$DEFAULT_PROMPT}"
fi

exec claude ${CLAUDE_FLAGS[@]+"${CLAUDE_FLAGS[@]}"} "${PROMPT:-$DEFAULT_PROMPT}"
