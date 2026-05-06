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


def _best_frontier(obs: dict[str, Any]) -> tuple[int, int, str] | None:
    """Return (row, col, glyph) of the best frontier to head toward, or None.

    Sort key: (is_door, distance). All non-door walkable frontiers come first
    by distance, then closed doors. Doors are blind risk surfaces — only try
    them when the safe (non-door) frontier is exhausted.
    """
    chars = obs.get("chars") or []
    seen = obs.get("seen") or []
    if not chars or not seen:
        return None
    cursor = obs.get("cursor") or [0, 0]
    py, px = int(cursor[0]), int(cursor[1])
    h = len(chars)
    w = len(chars[0]) if chars else 0
    walkable = set(".#+<>")
    candidates: list[tuple[int, int, int, int, str]] = []  # (is_door, distance, r, c, glyph)
    for r in range(1, min(22, h)):
        for c in range(w):
            ch_int = chars[r][c]
            ch = chr(ch_int) if ch_int else " "
            if ch not in walkable:
                continue
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and nr < len(seen) and 0 <= nc < len(seen[nr]):
                    if not seen[nr][nc]:
                        d = max(abs(r - py), abs(c - px))
                        candidates.append((1 if ch == "+" else 0, d, r, c, ch))
                        break
    if not candidates:
        return None
    candidates.sort()  # non-doors (0) first by distance, then doors (1)
    _, _, r, c, ch = candidates[0]
    return (r, c, ch)


def _open_adjacent_door(do, observe) -> str | None:
    """If a closed `+` is adjacent to @, walk into it (auto-opens or attempts).

    Returns the direction we tried, or None if no `+` was adjacent.
    """
    obs = observe()
    chars = obs.get("chars") or []
    cursor = obs.get("cursor") or [0, 0]
    cy, cx = int(cursor[0]), int(cursor[1])
    h, w = len(chars), len(chars[0]) if chars else 0
    for dr, dc, dname in (
        (-1, 0, "north"), (1, 0, "south"),
        (0, -1, "west"), (0, 1, "east"),
    ):
        nr, nc = cy + dr, cx + dc
        if 0 <= nr < h and 0 <= nc < w:
            ch_int = chars[nr][nc]
            ch = chr(ch_int) if ch_int else " "
            if ch == "+":
                do(dname)  # NetHack auto-opens (or asks for unlock if locked)
                return dname
    return None


def auto_explore(
    *,
    max_iters: int = 30,
    open_doors: bool = True,
    do=None,
    observe=None,
) -> dict[str, Any]:
    """Explore until done, hostile in view, or stuck.

    Frontier preference: non-door walkable cells first by distance, then closed
    doors. Doors are blind risk surfaces — handled only when safe frontier is
    exhausted, so we don't poke our head into a `+` while there's a corridor
    we could be exploring instead.

    `open_doors=True`: when a travel attempt makes no progress AND there's a
    closed door adjacent, walks into it (NetHack auto-opens, or attempts to
    unlock). On the next iteration, the newly-revealed cells become frontiers.
    """
    if do is None or observe is None:
        do, observe = _resolve_kernel()

    targets: list[tuple[int, int, str]] = []  # (r, c, glyph)
    last_pos: tuple[int, int] | None = None
    just_opened_door = False
    for i in range(max_iters):
        obs = observe()

        # Hostile-in-view check matches safe_do semantics.
        threats = _hostile_set(obs)
        if threats:
            top = sorted(threats)[:3]
            descr = ", ".join(f"'{ch}' at ({r},{c})" for ch, (r, c) in top)
            return {"reason": f"hostile in view: {descr}", "iters": i, "targets": targets}

        frontier = _best_frontier(obs)
        if frontier is None:
            return {"reason": "level fully explored from current position",
                    "iters": i, "targets": targets}
        tr, tc, glyph = frontier

        # No-progress check. If we didn't move since last iter AND we didn't
        # *just* open a door (that doesn't change cursor pos), we're stuck —
        # try opening an adjacent door. If even that fails, bail.
        cursor = obs.get("cursor") or [0, 0]
        cur_pos = (int(cursor[0]), int(cursor[1]))
        if last_pos is not None and cur_pos == last_pos and not just_opened_door:
            if open_doors:
                opened = _open_adjacent_door(do, observe)
                if opened:
                    just_opened_door = True
                    targets.append((cur_pos[0], cur_pos[1], f"door-{opened}"))
                    continue
            return {"reason": f"no progress (stuck at {cur_pos}, target was unreachable)",
                    "iters": i, "targets": targets}
        last_pos = cur_pos
        just_opened_door = False

        targets.append((tr, tc, glyph))
        travel_to(tr, tc, do=do, observe=observe)

    return {"reason": f"max_iters={max_iters} reached",
            "iters": max_iters, "targets": targets}
