"""Sokoban helpers: a checked boulder-push executor.

You (the player) decide WHAT to push, using the level's known solution
(knowledge/wiki/Sokoban_Level_*.txt). This module handles HOW: walking to
the right side of the boulder without disturbing anything, pushing, and
verifying every result. It stops (pauses) on anything unexpected.

Sokoban rules that matter (3.6): boulders can only be pushed orthogonally;
you can't move diagonally between two boulders/walls; holes (^) swallow a
boulder and become floor; destroying boulders / reading earth costs Luck.
Symbols with our options: boulder '0', hole/trap '^'.
"""

from __future__ import annotations

from collections import deque

from . import ctx
from .mapview import DIR_KEY, KEY_DIR, MONSTER_CHARS

PUSH_OK = [r"With great effort you move the boulder", r"You try to move the boulder",
           r"The boulder falls into and plugs a hole", r"plugs? a (hole|trap door)",
           r"You hear the boulder", r"There is a boulder in your way",
           r"You swap places with", r"You stop\. .* is in your way"]

_ORTHO = {"h": (-1, 0), "l": (1, 0), "k": (0, -1), "j": (0, 1)}
_ALIASES = {"left": "h", "right": "l", "up": "k", "down": "j", "w": "h", "e": "l", "n": "k", "s": "j",
            "L": "h", "R": "l", "U": "k", "D": "j"}


def _norm(d: str) -> str:
    d = _ALIASES.get(d, d)
    if d not in _ORTHO:
        raise ValueError(f"push direction must be one of h/j/k/l (got {d!r})")
    return d


def _blocked(s, x, y, allow_goal=None):
    ch = s.screen.at(x, y)
    if (x, y) == allow_goal:
        return False
    if ch in " |-0^#+}":
        return True    # rock/walls/boulders/holes/corridor-looking bars/doors/water
    if ch in MONSTER_CHARS and (x, y) != s.hero:
        return True
    return False


def route(s, start, goal):
    """Shortest walk avoiding boulders/holes/monsters, honoring the Sokoban
    'no diagonal squeeze' rule. Returns a string of move keys, or None."""
    q = deque([start])
    prev = {start: None}
    while q:
        cur = q.popleft()
        if cur == goal:
            keys = []
            while prev[cur] is not None:
                p = prev[cur]
                keys.append(DIR_KEY[(cur[0] - p[0], cur[1] - p[1])])
                cur = p
            return "".join(reversed(keys))
        for (dx, dy), key in DIR_KEY.items():
            nx, ny = cur[0] + dx, cur[1] + dy
            if (nx, ny) in prev or _blocked(s, nx, ny, allow_goal=goal):
                continue
            if dx and dy and _blocked(s, cur[0] + dx, cur[1]) and _blocked(s, cur[0], cur[1] + dy):
                continue   # can't squeeze diagonally in Sokoban
            prev[(nx, ny)] = cur
            q.append((nx, ny))
    return None


def walk(keys: str):
    """Walk a key path one step at a time, verifying each step moved us."""
    s = ctx.last()
    for k in keys:
        before = s.hero
        s = ctx.do(k, ok=PUSH_OK)
        dx, dy = KEY_DIR[k]
        if s.hero != (before[0] + dx, before[1] + dy):
            ctx.pause(f"walk: step {k!r} from {before} didn't arrive (now at {s.hero})")
            return s
    return s


def push(bx: int, by: int, dirs: str):
    """Push the boulder at (bx, by) along `dirs` (e.g. 'hhk' = left, left, up).
    Walks to the correct side before each push. Returns (final_snap, boulder_pos
    or None if it plugged a hole)."""
    b = (bx, by)
    s = ctx.last()
    if s.screen.at(bx, by) != "0":
        raise ValueError(f"no boulder '0' at {b} (found {s.screen.at(bx, by)!r})")
    for d in dirs:
        d = _norm(d)
        dx, dy = _ORTHO[d]
        stand = (b[0] - dx, b[1] - dy)
        s = ctx.last()
        if s.hero != stand:
            path = route(s, s.hero, stand)
            if path is None:
                ctx.pause(f"push: no safe route from {s.hero} to {stand} (to push {b} {d})")
                return ctx.last(), b
            s = walk(path)
            if s.hero != stand:
                return s, b
        s = ctx.do(d, ok=PUSH_OK)
        text = " ".join(s.messages)
        nb = (b[0] + dx, b[1] + dy)
        if "plug" in text or "fills" in text:
            return s, None
        if s.screen.at(*nb) == "0" and s.hero == b:
            b = nb
            continue
        ctx.pause(f"push: boulder {b} did not move {d} as expected (messages: {text!r})")
        return ctx.last(), b
    return ctx.last(), b


def board(s=None) -> str:
    """The Sokoban board region of the map with coordinates (boulders 0, holes ^)."""
    s = s or ctx.last()
    rows = [(y, s.screen.row(y)) for y in range(1, 22)]
    rows = [(y, r) for y, r in rows if r.strip()]
    if not rows:
        return "(empty map)"
    x0 = min(len(r) - len(r.lstrip()) for _, r in rows)
    x1 = max(len(r.rstrip()) for _, r in rows)
    tens = "".join(str((x // 10) % 10) if x % 10 == 0 else " " for x in range(x0, x1))
    ones = "".join(str(x % 10) for x in range(x0, x1))
    out = ["    " + tens, "    " + ones]
    out += [f"{y:>2}  {r[x0:x1]}" for y, r in rows]
    return "\n".join(out)
