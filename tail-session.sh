#!/usr/bin/env bash
# Tail the gamer-Claude's session jsonl (raw) — the same log view.py reads
# for the activity panel, but unfiltered so you can see the full message
# structure (tool_use blocks, signatures, attachments, permission events, etc.)
#
# Usage:
#   ./tail-session.sh            # raw, follow latest jsonl
#   ./tail-session.sh -j         # pipe through jq for pretty-printing
#   ./tail-session.sh -j '.type' # custom jq filter (e.g. just message types)
#   ./tail-session.sh -s         # SPEECH ONLY: msg-timestamp + assistant text
#                                # (best for eyeballing lag against UI)
#   ./tail-session.sh -t         # prefix each line with [HH:MM:SS] reception time
#                                # (compare msg-timestamp vs reception-time)
#   ./tail-session.sh -a         # advisor session dir instead of gamer

set -euo pipefail

DIR="$HOME/.claude/projects/-Users-em-Coding-claude-plays-nethack-game"
JQ_ARG=""
USE_JQ=0
USE_TIME=0
SPEECH=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    -j) USE_JQ=1; shift; if [[ $# -gt 0 && "$1" != -* ]]; then JQ_ARG="$1"; shift; fi ;;
    -a) DIR="$HOME/.claude/projects/-Users-em-Coding-claude-plays-nethack"; shift ;;
    -t) USE_TIME=1; shift ;;
    -s) SPEECH=1; shift ;;
    -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ $SPEECH -eq 1 ]]; then
  USE_JQ=1
  JQ_ARG='select(.type=="assistant") | .timestamp as $t | .message.content[]? | select(.type=="text") | "\($t)  \(.text)"'
fi

LATEST="$(ls -t "$DIR"/*.jsonl 2>/dev/null | head -1 || true)"
if [[ -z "$LATEST" ]]; then
  echo "No jsonl found in $DIR — start a session first." >&2
  exit 1
fi

echo "tailing: $LATEST" >&2
echo "(re-run when a new session starts — this script follows one file)" >&2
echo >&2

stamp() {
  if [[ $USE_TIME -eq 1 ]]; then
    while IFS= read -r line; do
      printf '[%s] %s\n' "$(date +%H:%M:%S)" "$line"
    done
  else
    cat
  fi
}

if [[ $USE_JQ -eq 1 ]]; then
  if [[ -n "$JQ_ARG" ]]; then
    tail -F -n 50 "$LATEST" | jq -r --unbuffered "$JQ_ARG" | stamp
  else
    tail -F -n 50 "$LATEST" | jq --unbuffered . | stamp
  fi
else
  tail -F -n 50 "$LATEST" | stamp
fi
