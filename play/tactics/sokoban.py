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
           r"You hear a monster behind the boulder", r"Perhaps that's why you cannot move it",
           r"The boulder falls into and plugs a hole", r"plugs? a (hole|trap door)",
           r"The boulder fills a pit", r"fills a (pit|hole)",
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


def _solid(s, x, y):
    """Rock, walls, boulders: what the no-diagonal-squeeze rule counts."""
    return s.screen.at(x, y) in " |-0#+}"


def _blocked(s, x, y, allow_goal=None):
    ch = s.screen.at(x, y)
    if (x, y) == allow_goal:
        return False
    if ch in " |-0^#+}":
        return True    # rock/walls/boulders/holes/corridor-looking bars/doors/water
    if ch in MONSTER_CHARS and (x, y) != s.hero and not s.screen.reverse_at(x, y):
        return True    # a monster that isn't our pet (pets just swap places)
    return False


def route(s, start, goal, ignore_monsters=False):
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
            if (nx, ny) in prev:
                continue
            if _blocked(s, nx, ny, allow_goal=goal) and not (ignore_monsters and _occupied(s, nx, ny)):
                continue
            if dx and dy and _solid(s, cur[0] + dx, cur[1]) and _solid(s, cur[0], cur[1] + dy):
                continue   # can't squeeze diagonally between boulders/walls in Sokoban
            prev[(nx, ny)] = cur
            q.append((nx, ny))
    return None


def _occupied(s, x, y):
    ch = s.screen.at(x, y)
    return ch in MONSTER_CHARS and (x, y) != s.hero and not s.screen.reverse_at(x, y)


def walk(keys: str):
    """Walk a key path one step at a time, verifying each step moved us.
    Never steps into a (non-pet) monster: waits for it to move, else pauses."""
    s = ctx.last()
    for k in keys:
        before = s.hero
        if before is None:
            ctx.pause(f"walk: not at the command prompt ({s.state.kind}: {s.state.prompt!r})")
            return ctx.last()
        dx, dy = KEY_DIR[k]
        dest = (before[0] + dx, before[1] + dy)
        waited = 0
        while _occupied(s, *dest) and waited < 4:
            s = ctx.do("s", ok=PUSH_OK)
            waited += 1
        if _occupied(s, *dest):
            ctx.pause(f"walk: {s.screen.at(*dest)!r} at {dest} is in the way (not attacking it)")
            return ctx.last()
        s = ctx.do(k, ok=PUSH_OK)
        if s.hero != dest:
            if s.state.kind != "command":
                ctx.do("<Esc>", quiet=True)   # e.g. an attack confirmation: decline
            ctx.pause(f"walk: step {k!r} from {before} didn't arrive (now at {ctx.last().hero})")
            return ctx.last()
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
        if s.hero is None:
            ctx.pause(f"push: not at the command prompt ({s.state.kind}: {s.state.prompt!r})")
            return ctx.last(), b
        if s.hero != stand:
            path = route(s, s.hero, stand)
            waited = 0
            while path is None and waited < 8 and route(s, s.hero, stand, ignore_monsters=True):
                s = ctx.do("s", ok=PUSH_OK)      # a monster blocks the way: give it time to move
                waited += 1
                path = route(s, s.hero, stand)
            if path is None:
                ctx.pause(f"push: no safe route from {s.hero} to {stand} (to push {b} {d})")
                return ctx.last(), b
            s = walk(path)
            if s.hero != stand:
                return s, b
        s = ctx.do(d, ok=PUSH_OK)
        text = " ".join(s.messages)
        waits = 0
        while "behind the boulder" in text and waits < 6:
            # something (often the pet) is on the far side: wait and retry
            ctx.do("s", ok=PUSH_OK)
            waits += 1
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


_WIKI = {"r": "l", "l": "h", "u": "k", "d": "j"}


def push_wiki(bx: int, by: int, moves: str):
    """Push using the wiki's solution notation: r/l/u/d (right/left/up/down),
    spaces ignored, a trailing '*' (fills a pit) ignored. Example: the wiki's
    'D rlll llll' for the boulder you identified as D at (41,9) is
    push_wiki(41, 9, 'rlll llll'). NOTE: wiki 'l' = LEFT (vi-key 'h')."""
    keys = "".join(_WIKI[c] for c in moves.lower() if c in _WIKI)
    return push(bx, by, keys)
