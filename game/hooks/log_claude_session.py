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
trajectory whenever the driving session changes, so post-mortem tooling
can map any step event → the conversation jsonl that caused it.

How
---
1. Read stdin JSON (Claude Code passes `session_id`, `cwd`, ...).
2. Find the active trajectory file:
   - `NETHACK_TRAJECTORY_DIR` env var if set, else `<cwd>/trajectory/`
   - newest-mtime *.jsonl in that dir
3. Scan the trajectory for the last `claude_session` event.
4. If absent or session_id differs, append a new event.

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


# --- claude_session event handling ----------------------------------------

def _last_claude_session(path: Path) -> str | None:
    """Find the session_id of the most recent claude_session event in the
    trajectory, or None if none recorded yet. Forward scan: trajectory
    files are append-only and small enough in practice."""
    last: str | None = None
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
                    last = obj.get("session_id")
    except OSError:
        return None
    return last


def _append_claude_session(path: Path, session_id: str) -> None:
    event = {
        "t": time.time(),
        "event": "claude_session",
        "session_id": session_id,
    }
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
    if _last_claude_session(traj_path) == session_id:
        return 0
    _append_claude_session(traj_path, session_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
