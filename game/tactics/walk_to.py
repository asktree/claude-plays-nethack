"""walk_to(row, col): BFS over the *known* map, then step manually.

Why not just travel_to()? NetHack's Travel refuses to swap places with a
pet ("You stop.  Sirius is in the way!") and halts silently whenever any
monster is in view. In a 1-wide corridor with a pet tagging along, Travel
can fail to move at all. Manual moves swap with the pet, so a python-side
path + single-step moves is far more robust in that situation.

Rules encoded:
  - passable = floor/corridor/stairs/altar/fountain/etc, any door cell, and
    any cell currently hiding terrain under a monster/item glyph (checked via
    `descriptions`). Walls, blank rock, and never-seen cells are not.
  - no diagonal step into or out of a door cell (NetHack rule).
  - stops early (returns the snapshot) if the step didn't change position
    twice in a row — something is blocking; the caller decides.
"""

from __future__ import annotations

from collections import deque
from typing import Any

WALL = set("-|")
BLANK = {0, 0x20}
DIRS = {
    (-1, 0): "north", (1, 0): "south", (0, -1): "west", (0, 1): "east",
    (-1, 1): "ne", (1, 1): "se", (1, -1): "sw", (-1, -1): "nw",
}


def _kernel():
    import sys
    g = sys._getframe(2).f_globals
    return g.get("do"), g.get("observe")


def _is_door(desc: str) -> bool:
    d = (desc or "").lower()
    return "door" in d and "doorway" not in d and "broken" not in d


def _passable(obs: dict[str, Any], r: int, c: int) -> bool:
    chars, seen, desc = obs["chars"], obs.get("seen"), obs.get("descriptions")
    if not (0 <= r < len(chars) and 0 <= c < len(chars[r])):
        return False
    ch_int = chars[r][c]
    if ch_int in BLANK:
        return False
    ch = chr(ch_int)
    d = (desc[r][c] if desc else "") or ""
    dl = d.lower()
    if "door" in dl:
        return "closed" not in dl and "locked" not in dl and "broken" not in dl or "doorway" in dl or "broken" in dl
    if ch in WALL:
        return False
    if seen is not None and not seen[r][c]:
        return False
    return True


def path_to(obs: dict[str, Any], tr: int, tc: int) -> list[tuple[int, int]] | None:
    """BFS shortest path (list of cells, excluding start) or None."""
    cur = obs["cursor"]
    start = (int(cur[0]), int(cur[1]))
    if start == (tr, tc):
        return []
    desc = obs.get("descriptions")

    chars = obs["chars"]

    def wall(r, c):
        return 0 <= r < len(chars) and 0 <= c < len(chars[r]) and chr(chars[r][c]) in WALL

    def door(r, c):
        # The cell under @ (or a monster) describes the occupant, not the
        # terrain, so also treat any wall-flanked cell as a door: walls on
        # both N/S or both W/E means a doorway in a room wall. Conservative —
        # doorless/broken doorways allow diagonals but we skip them too.
        if desc is not None and _is_door(desc[r][c]):
            return True
        return (wall(r - 1, c) and wall(r + 1, c)) or (wall(r, c - 1) and wall(r, c + 1))

    prev = {start: None}
    q = deque([start])
    while q:
        r, c = q.popleft()
        for (dr, dc) in DIRS:
            nr, nc = r + dr, c + dc
            if (nr, nc) in prev:
                continue
            diag = dr != 0 and dc != 0
            if diag and (door(r, c) or (0 <= nr < len(chars) and 0 <= nc < len(chars[nr]) and door(nr, nc))):
                continue
            if (nr, nc) != (tr, tc) and not _passable(obs, nr, nc):
                continue
            if (nr, nc) == (tr, tc) and not _passable(obs, nr, nc):
                # allow stepping "into" a closed door target (opens it) but nothing else
                dl = ((desc[nr][nc] if desc else "") or "").lower()
                if "door" not in dl:
                    continue
            prev[(nr, nc)] = (r, c)
            if (nr, nc) == (tr, tc):
                out = [(nr, nc)]
                p = (r, c)
                while p != start:
                    out.append(p); p = prev[p]
                return out[::-1]
            q.append((nr, nc))
    return None


def walk_to(row: int, col: int, *, max_steps: int = 60, do=None, observe=None) -> dict[str, Any]:
    """Walk to (row, col) along a BFS path over known terrain, one do() per
    step. Re-plans every step (pets move, doors open). Returns the last
    snapshot. Raises RuntimeError if no known path exists."""
    if do is None or observe is None:
        do, observe = _kernel()
    snap = observe()
    stuck = 0
    for _ in range(max_steps):
        cur = (int(snap["cursor"][0]), int(snap["cursor"][1]))
        if cur == (row, col):
            return snap
        path = path_to(snap, row, col)
        if path is None:
            raise RuntimeError(f"walk_to({row},{col}): no known path from {cur}")
        nr, nc = path[0]
        snap = do(DIRS[(nr - cur[0], nc - cur[1])])
        new = (int(snap["cursor"][0]), int(snap["cursor"][1]))
        if new == cur:
            stuck += 1
            if stuck >= 2:
                return snap
        else:
            stuck = 0
    return snap
