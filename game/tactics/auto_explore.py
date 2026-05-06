"""auto_explore(): repeatedly travel toward the nearest unexplored frontier
until the level is fully explored or something interesting happens.

Stops on:
  - no remaining frontier cells reachable from `@`
  - any hostile in view (matches safe_do semantics — let the gamer decide)
  - max_iters reached (safety cap to prevent runaway)
  - no progress in last iteration (cursor didn't change after travel_to)

Returns a summary dict with `reason`, `iters`, `targets` (list of (r,c) tried).
"""

from __future__ import annotations

import sys
from typing import Any

from .safe_do import _hostile_set
from .travel_to import travel_to


def _resolve_kernel():
    frame = sys._getframe(2).f_globals
    do = frame.get("do")
    observe = frame.get("observe")
    if do is None or observe is None:
        raise RuntimeError("auto_explore must be called inside game.exec()")
    return do, observe


def _nearest_frontier(obs: dict[str, Any]) -> tuple[int, int, int] | None:
    """Return (distance, row, col) of the nearest unexplored frontier, or None."""
    chars = obs.get("chars") or []
    seen = obs.get("seen") or []
    if not chars or not seen:
        return None
    cursor = obs.get("cursor") or [0, 0]
    py, px = int(cursor[0]), int(cursor[1])
    h = len(chars)
    w = len(chars[0]) if chars else 0
    walkable = set(".#+<>")
    best: tuple[int, int, int] | None = None
    for r in range(1, min(22, h)):
        for c in range(w):
            ch_int = chars[r][c]
            ch = chr(ch_int) if ch_int else " "
            if ch not in walkable:
                continue
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < len(seen[nr] if nr < len(seen) else []):
                    if not seen[nr][nc]:
                        d = max(abs(r - py), abs(c - px))
                        if best is None or d < best[0]:
                            best = (d, r, c)
                        break
    return best


def auto_explore(*, max_iters: int = 30, do=None, observe=None) -> dict[str, Any]:
    if do is None or observe is None:
        do, observe = _resolve_kernel()

    targets: list[tuple[int, int]] = []
    last_pos: tuple[int, int] | None = None
    for i in range(max_iters):
        obs = observe()

        # Hostile-in-view check matches safe_do semantics. If anything is
        # visible, halt and let the gamer decide.
        threats = _hostile_set(obs)
        if threats:
            top = sorted(threats)[:3]
            descr = ", ".join(f"'{ch}' at ({r},{c})" for ch, (r, c) in top)
            return {
                "reason": f"hostile in view: {descr}",
                "iters": i, "targets": targets,
            }

        frontier = _nearest_frontier(obs)
        if frontier is None:
            return {
                "reason": "level fully explored from current position",
                "iters": i, "targets": targets,
            }
        d, tr, tc = frontier

        # No-progress check: if the last iteration tried to travel but cursor
        # didn't move, we're stuck (door we can't open, blocked path, etc.).
        cursor = obs.get("cursor") or [0, 0]
        cur_pos = (int(cursor[0]), int(cursor[1]))
        if last_pos is not None and cur_pos == last_pos:
            return {
                "reason": f"no progress (stuck at {cur_pos}, target was unreachable)",
                "iters": i, "targets": targets,
            }
        last_pos = cur_pos

        targets.append((tr, tc))
        travel_to(tr, tc, do=do, observe=observe)

    return {
        "reason": f"max_iters={max_iters} reached",
        "iters": max_iters, "targets": targets,
    }
