"""PreToolUse hook (Claude Code, NOT a server-internal hook): tags the
active trajectory file with which Claude conversation is currently driving.

Wired in `game/.claude/settings.json` under PreToolUse for
`mcp__nethack__.*` — fires once per gamer tool call, before MCP runs.

Why
---
The MCP server can't see Claude's session id; it only sees stdio bytes.
On `--resume` and especially with subagents, multiple Claude sessions
can interleave writes to the same trajectory file with no marker
distinguishing them. This hook drops a `claude_session` event into the
trajectory whenever the driving session (or its model) changes, so
post-mortem tooling can map any step event → the conversation jsonl that
caused it and know which model was playing.

How
---
1. Read stdin JSON (Claude Code passes `session_id`, `transcript_path`,
   `cwd`, ...).
2. Find the active trajectory file:
   - `NETHACK_TRAJECTORY_DIR` env var if set, else `<cwd>/trajectory/`
   - newest-mtime *.jsonl in that dir
3. Resolve the driving model: last assistant message's `message.model`
   in the transcript. Tail-read (last 64KB) so cost stays flat as the
   transcript grows. Effort has no transcript trace, so it comes from
   `NETHACK_CLAUDE_EFFORT` (exported by run.sh's --effort flag) — best
   effort: absent when the session wasn't launched through run.sh.
4. Scan the trajectory for the last `claude_session` event.
5. If absent, or session_id / model / effort differs, append a new
   event. A mid-run `/model` switch therefore gets its own event.

Hook errors are swallowed (return 0) — never block the gamer's tool call
on bookkeeping.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


# --- trajectory file resolution -------------------------------------------

def _trajectory_dir(cwd: str) -> Path:
    override = os.environ.get("NETHACK_TRAJECTORY_DIR")
    if override:
        return Path(override)
    return Path(cwd) / "trajectory"


def _active_trajectory(traj_dir: Path) -> Path | None:
    """Newest-mtime *.jsonl in the trajectory dir. None if no trajectory
    has been opened yet (game hasn't started)."""
    if not traj_dir.is_dir():
        return None
    candidates = sorted(
        traj_dir.glob("*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


# --- model resolution ------------------------------------------------------

def _model_from_transcript(transcript_path: str | None) -> str | None:
    """Model id of the most recent assistant message in the Claude session
    transcript, or None if unavailable. Reads only the file tail: assistant
    messages are frequent, so the last 64KB virtually always contains one,
    and transcripts grow to many MB over a long game."""
    if not transcript_path:
        return None
    try:
        with open(transcript_path, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            fh.seek(max(0, size - 65536))
            chunk = fh.read().decode("utf-8", errors="replace")
    except OSError:
        return None
    lines = chunk.splitlines()
    if size > 65536 and lines:
        lines = lines[1:]  # first line of the tail chunk may be partial
    for line in reversed(lines):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = obj.get("message")
        if isinstance(msg, dict) and msg.get("model"):
            return msg["model"]
    return None


# --- claude_session event handling ----------------------------------------

def _last_claude_session(path: Path) -> tuple[str | None, str | None, str | None]:
    """(session_id, model, effort) of the most recent claude_session event
    in the trajectory, or (None, None, None) if none recorded yet. Forward
    scan: trajectory files are append-only and small enough in practice."""
    last: tuple[str | None, str | None, str | None] = (None, None, None)
    try:
        with path.open() as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("event") == "claude_session":
                    last = (obj.get("session_id"), obj.get("model"), obj.get("effort"))
    except OSError:
        return (None, None, None)
    return last


def _append_claude_session(
    path: Path, session_id: str, model: str | None, effort: str | None
) -> None:
    event = {
        "t": time.time(),
        "event": "claude_session",
        "session_id": session_id,
    }
    if model:
        event["model"] = model
    if effort:
        event["effort"] = effort
    with path.open("a") as fh:
        fh.write(json.dumps(event) + "\n")


# --- entry point ----------------------------------------------------------

def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0
    session_id = payload.get("session_id")
    cwd = payload.get("cwd") or os.getcwd()
    if not session_id:
        return 0
    traj_path = _active_trajectory(_trajectory_dir(cwd))
    if traj_path is None:
        return 0
    model = _model_from_transcript(payload.get("transcript_path"))
    effort = os.environ.get("NETHACK_CLAUDE_EFFORT") or None
    last_sid, last_model, last_effort = _last_claude_session(traj_path)
    # Re-append on a model/effort change too (mid-run /model switch, or a
    # model backfill once the transcript has its first assistant message).
    # An unknown value (None) never counts as a change.
    if (
        last_sid == session_id
        and (model is None or model == last_model)
        and (effort is None or effort == last_effort)
    ):
        return 0
    _append_claude_session(traj_path, session_id, model, effort)
    return 0


if __name__ == "__main__":
    sys.exit(main())
