"""Hook: every Command.SEARCH bumps the per-cell count in search_memory.

Wired automatically — the gamer doesn't need to remember to record. This
keeps `views.likely_secret_doors` accurate even when searches are issued via
bare `do("Command.SEARCH")` calls outside of any tactic.
"""

from __future__ import annotations

from typing import Any

from claude_plays_nethack.server import register_hook  # type: ignore
import search_memory  # game/search_memory.py — on sys.path via GAME_DIR


def _record_if_search(payload: dict[str, Any]) -> None:
    if payload.get("action_name") != "Command.SEARCH":
        return
    pre = payload.get("pre_obs") or {}
    bl = pre.get("blstats") or {}
    cursor = pre.get("cursor") or [0, 0]
    search_memory.record_search(
        dungeon=bl.get("dungeon_number", 0),
        dlevel=bl.get("level_number", 0),
        row=int(cursor[0]),
        col=int(cursor[1]),
    )


register_hook("post_do", _record_if_search)
