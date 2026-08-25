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
# Cells the gamer has learned to avoid (known trap squares whose '^' is hidden
# under an object, etc). Kernel code may add to this set: walk_to.AVOID.add((r, c)).
AVOID: set = set()
DIRS = {
    (-1, 0): "north", (1, 0): "south", (0, -1): "west", (0, 1): "east",
    (-1, 1): "ne", (1, 1): "se", (1, -1): "sw", (-1, -1): "nw",
}


def _more_pending(screen: str) -> bool:
    """--More-- on screen, including the case where a long message wrapped at
    the right edge and the marker is split across two lines ("--Mo" / "re--")."""
    if "--More--" in screen:
        return True
    lines = screen.split("\n")
    for i, ln in enumerate(lines[:-1]):
        tail = ln.rstrip()
        # The obs screen is 79 cols wide while the tty is 80, so the split can
        # look like "--" / "ore--" (the 'M' clipped) as well as "--Mo" / "re--".
        if tail.endswith("--") or tail.endswith("--M") or tail.endswith("--Mo") or tail.endswith("--Mor") or tail.endswith("--More"):
            nxt = lines[i + 1].lstrip("°").lstrip()
            for frag in ("More--", "ore--", "re--", "e--"):
                if nxt.startswith(frag):
                    return True
    return False


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
    if "peaceful" in dl:
        return False  # never bump a peaceful (triggers 'Really attack?'); re-plan around it
    try:
        from nle import nethack as _nh
        g = obs.get("glyphs")
        if g is not None and _nh.glyph_is_monster(g[r][c]) and "tame" not in dl:
            return False  # never walk into a hostile (passive attackers like blue jellies!)
    except Exception:
        pass
    if "bars" in dl or "tree" in dl or ch in "}" or "water" in dl or "lava" in dl:
        return False  # iron bars / trees / water / lava
    if "door" in dl:
        return "closed" not in dl and "locked" not in dl and "broken" not in dl or "doorway" in dl or "broken" in dl
    if ch in WALL:
        return False
    if seen is not None and not seen[r][c]:
        return False
    if ch == "^" or "trap" in dl or (r, c) in AVOID:
        return False  # known trap: never path through it (target cell is exempt in path_to)
    for w in ("pit", "hole", "trap door", "web", "bear trap", "land mine", "magic portal"):
        if dl == w or dl.startswith(w + " ") or dl.endswith(" " + w):
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
        # The cell under @ describes the occupant, not the terrain, so for the
        # START cell only, treat a wall-flanked position as a door (walls on
        # both N/S or both W/E). Elsewhere trust the description: applying the
        # wall-flanked heuristic to arbitrary cells wrongly forbids diagonals
        # through narrow cave gaps in the Mines.
        if desc is not None and _is_door(desc[r][c]):
            return True
        # Wall-flanked cells are doors in rooms-and-corridors levels (dungeon
        # 0 = Dungeons of Doom, also Sokoban etc.) even when an object hides
        # the door description; in the Gnomish Mines (dungeon 2) narrow cave
        # gaps look the same and are NOT doors, so only trust it for @'s cell.
        flanked = (wall(r - 1, c) and wall(r + 1, c)) or (wall(r, c - 1) and wall(r, c + 1))
        if not flanked:
            return False
        if (r, c) == start:
            return True
        dnum = int((obs.get("blstats") or {}).get("dungeon_number", 0) or 0)
        return dnum != 2

    def _solid(rr, cc):
        if not (0 <= rr < len(chars) and 0 <= cc < len(chars[rr])):
            return True
        chv = chars[rr][cc]
        return chv in BLANK or chr(chv) in WALL

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
            if diag and _solid(r + dr, c) and _solid(r, c + dc):
                # squeezing diagonally between two wall/rock cells needs
                # inventory weight <= 600; assume the gamer is heavier
                continue
            if (nr, nc) != (tr, tc) and not _passable(obs, nr, nc):
                continue
            if (nr, nc) == (tr, tc) and not _passable(obs, nr, nc):
                # allow stepping "into" a closed door target (opens it), or onto
                # a trap the caller explicitly targeted, but nothing else
                dl = ((desc[nr][nc] if desc else "") or "").lower()
                if "door" not in dl and "trap" not in dl:
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


def _cur(snap: dict[str, Any], observe) -> tuple[int, int]:
    """Player position. obs['cursor'] occasionally reflects the tty cursor
    (parked on the message line) rather than @; if the cursor cell isn't
    '@', fall back to blstats x/y, then to scanning chars for '@'."""
    r, c = int(snap["cursor"][0]), int(snap["cursor"][1])
    chars = snap.get("chars") or []
    if 0 <= r < len(chars) and 0 <= c < len(chars[r]) and chars[r][c] == ord("@"):
        return r, c
    bl = snap.get("blstats") or {}
    if "x" in bl and "y" in bl:
        r2, c2 = int(bl["y"]), int(bl["x"])
        for rr, cc in ((r2, c2), (r2 - 1, c2), (r2, c2 - 1), (r2 - 1, c2 - 1)):
            if 0 <= rr < len(chars) and 0 <= cc < len(chars[rr]) and chars[rr][cc] == ord("@"):
                return rr, cc
    for rr in range(len(chars)):
        for cc in range(len(chars[rr])):
            if chars[rr][cc] == ord("@"):
                return rr, cc
    return r, c


def walk_to(row: int, col: int, *, max_steps: int = 60, do=None, observe=None) -> dict[str, Any]:
    """Walk to (row, col) along a BFS path over known terrain, one do() per
    step. Re-plans every step (pets move, doors open). Returns the last
    snapshot. Raises RuntimeError if no known path exists."""
    if do is None or observe is None:
        do, observe = _kernel()
    snap = observe()
    stuck = 0
    for _ in range(max_steps):
        cur = _cur(snap, observe)
        snap["cursor"] = list(cur)
        if cur == (row, col):
            return snap
        path = path_to(snap, row, col)
        if path is None:
            raise RuntimeError(f"walk_to({row},{col}): no known path from {cur}")
        nr, nc = path[0]
        snap = do(DIRS[(nr - cur[0], nc - cur[1])])
        # Landing on a pile of 3+ objects opens a "Things that are here:"
        # popup whose --More-- the harness doesn't always pump; while it's
        # up, every keystroke is swallowed. Dismiss it (ESC is safe here).
        if _more_pending(snap.get("screen") or ""):
            snap = do("Command.ESC")
        new = _cur(snap, observe)
        if new == cur:
            stuck += 1
            if stuck >= 2:
                return snap
        else:
            stuck = 0
    return snap
