"""Exploration built on NetHack's own frontier finder.

In a position prompt, the 'x' key jumps the cursor to the nearest map spot
(door, doorway, floor, corridor) that borders never-seen stone — computed by
the game from its real vision memory (levl[][].seenv), not guessed from the
screen. Repeating 'x' cycles through further ones; when the cursor comes back
to the hero there is nothing left to explore.
"""

from __future__ import annotations

from . import ctx
from .nav import NavError, cursor_to

# Routine messages that shouldn't interrupt exploring.
BENIGN = [
    r"^The door opens\.",
    r"^You see here ",
    r"^You see no objects here",
    r"^There is a (doorway|broken door|open door) here",
    r"^You swap places with ",
    r"^You stop\. .* is in your way",
    r"^You move .* out of your way",
    r"^There are (several|many) objects here",
    r"^You hear (a door open|some noises|the footsteps|a water|bubbling|the splashing|a gurgling|a chugging)",
    r"^\$ - \d+ gold pieces?\.",
    r"^You find ",   # hidden things found by searching are shown on the map
    r"^You stop in front of the door\.",
    r"^That door is closed\.",
    r"^The door resists!",
    r"^(The |Your )?[\w' -]+ (picks up|drops|eats) ",
    r"^You hear some noises in the distance",
    r"^You have a (sad|strange) feeling for a moment",
]


def _dir_key(frm, to):
    from .mapview import DIR_KEY
    dx, dy = to[0] - frm[0], to[1] - frm[1]
    return DIR_KEY.get((max(-1, min(1, dx)), max(-1, min(1, dy))), ".")


def _adjacent_closed_door(s, target):
    """The closed door next to the hero (orthogonal), preferring `target`."""
    from .mapview import is_closed_door
    hx, hy = s.hero
    cands = [(hx + dx, hy + dy) for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1))
             if is_closed_door(s, hx + dx, hy + dy)]
    if target in cands:
        return target
    return cands[0] if cands else None


def frontiers(limit: int = 12):
    """List NetHack's unexplored-frontier spots, nearest first. No game time."""
    s = ctx.do("_", quiet=True)
    if s.state.kind != "getpos":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        raise NavError(f"travel prompt did not open ({s.state.kind})")
    start = s.screen.cursor
    hero = ctx.game.hero_pos
    spots = []
    for _ in range(limit):
        s = ctx.do("x", quiet=True)
        c = s.screen.cursor
        if c == hero or c in spots or c == start and spots:
            break
        spots.append(c)
    ctx.do("<Esc>", quiet=True)
    return spots


def explore(max_legs: int = 40, skip: set | None = None):
    """Travel to unexplored frontiers until none remain (or max_legs).

    Returns a dict: {"reason": ..., "legs": n, "unreachable": [...]}.
    Inside `nh exec` it pauses like any do() on anything unusual (combat,
    HP loss, new monsters, non-routine messages)."""
    skip = set(skip or ())
    legs = 0
    unreachable = []
    locked = []
    while legs < max_legs:
        s = ctx.last()
        if s.state.kind != "command":
            return {"reason": f"not at command prompt ({s.state.kind})", "legs": legs,
                    "unreachable": unreachable}
        hero = s.hero
        # choose the nearest frontier not known to be unreachable
        s = ctx.do("_", quiet=True)
        if s.state.kind != "getpos":
            return {"reason": "travel prompt failed", "legs": legs, "unreachable": unreachable}
        target = None
        seen = []
        for _ in range(15):
            s = ctx.do("x", quiet=True)
            c = s.screen.cursor
            if c == hero or c in seen:
                break
            seen.append(c)
            if c not in skip:
                target = c
                break
        if target is None:
            ctx.do("<Esc>", quiet=True)
            return {"reason": "explored (no reachable frontier left)", "legs": legs,
                    "unreachable": unreachable, "locked": locked}
        s = ctx.do(".", ok=BENIGN)
        legs += 1
        if s.state.kind != "command":
            return {"reason": f"stopped: {s.state.kind} {s.state.prompt!r}", "legs": legs,
                    "unreachable": unreachable}
        text = " ".join(s.messages)
        if ("You stop in front of the door" in text or "That door is closed" in text) \
                and s.hero is not None:
            door = _adjacent_closed_door(s, target)
            for _try in range(6):
                if door is None:
                    break
                key = _dir_key(s.hero, door)
                s = ctx.do(key, ok=BENIGN)
                text = " ".join(s.messages)
                if "This door is locked" in text:
                    locked.append(door)
                    skip.add(door)
                    break
                if "The door opens" in text or s.state.kind != "command":
                    break
            continue
        if "This door is locked" in text:
            locked.append(target)
            skip.add(target)
            continue
        if s.hero == hero:
            # no movement: unreachable by travel (or blocked by a monster)
            unreachable.append(target)
            skip.add(target)
            continue
        if s.hero != target and s.hero is not None:
            # stopped short (door opened, something seen...). Try again next leg.
            pass
    return {"reason": "max_legs reached", "legs": legs, "unreachable": unreachable, "locked": locked}
