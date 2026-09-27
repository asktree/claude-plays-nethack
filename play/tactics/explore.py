"""Exploration built on NetHack's own frontier finder.

In a position prompt, the 'x' key jumps the cursor to the nearest map spot
(door, doorway, floor, corridor) that borders never-seen stone — computed by
the game from its real vision memory (levl[][].seenv), not guessed from the
screen. Repeating 'x' cycles through further ones; when the cursor comes back
to the hero there is nothing left to explore.

Blind spot: the game's finder only considers squares *displayed* as terrain,
so a corridor square with an object lying on it is skipped. We add those
ourselves (object squares next to blank space that we haven't stood next to).
"""

from __future__ import annotations

from . import ctx
from .mapview import DIR_KEY, is_closed_door
from .nav import NavError

from .benign import BENIGN  # noqa: E402

FAIL_HINTS = ("A boulder blocks your path", "in vain", "cannot move past", "carrying too much")


def _dir_key(frm, to):
    dx, dy = to[0] - frm[0], to[1] - frm[1]
    return DIR_KEY.get((max(-1, min(1, dx)), max(-1, min(1, dy))), ".")


def _adjacent_closed_door(s, target):
    """The closed door next to the hero (orthogonal), preferring `target`."""
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
    return spots + [c for c in object_frontiers() if c not in spots]


def object_frontiers(s=None):
    """Object-covered squares bordering blank (maybe unexplored) space that
    we haven't stood next to — NetHack's own finder can't see these."""
    s = s or ctx.last()
    visited = ctx.game.visited.get(ctx.game.level_key(s.status), set())
    near = set()
    for (vx, vy) in visited:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                near.add((vx + dx, vy + dy))
    from .nav import bad_squares
    bad = bad_squares(s)
    out = []
    for o in s.objects:
        x, y = o["x"], o["y"]
        if o["ch"] in "0`" or (x, y) in near or (x, y) in bad:
            continue
        if any(s.screen.at(x + dx, y + dy) == " " for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1))):
            out.append((x, y))
    h = s.hero or ctx.game.hero_pos
    if h:
        out.sort(key=lambda c: max(abs(c[0] - h[0]), abs(c[1] - h[1])))
    return out


def _pick_target(skip, bad=frozenset(), why=None):
    """Open the travel prompt and place the cursor on the nearest usable
    frontier: not in `skip` and, when there are squares to avoid, reachable
    around them (checked on our side, inside the same prompt — no game time).
    Returns the target (cursor left there) or None (prompt closed).
    why["avoided"] collects frontiers cut off by avoided squares,
    why["seen"] every frontier NetHack offered."""
    why = why if why is not None else {}
    why.setdefault("avoided", [])
    s = ctx.do("_", quiet=True)
    if s.state.kind != "getpos":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        return None
    hero = ctx.game.hero_pos
    from .mapview import bfs_path
    seen = []
    for _ in range(20):
        s = ctx.do("x", quiet=True)
        c = s.screen.cursor
        if c == hero or c in seen:
            break
        seen.append(c)
        if c in skip:
            continue
        if bad and hero is not None:
            av = frozenset(set(bad) - {c})
            if (bfs_path(s, hero, c, avoid=av, allow_monsters=True) is None
                    and bfs_path(s, hero, c, allow_monsters=True) is not None):
                skip.add(c)
                why["avoided"].append(c)
                continue
        why["seen"] = seen
        return c
    why["seen"] = seen
    # NetHack found nothing new: try object-covered frontier squares
    for c in object_frontiers():
        if c not in skip:
            from .nav import cursor_to
            cursor_to(*c)
            return c
    ctx.do("<Esc>", quiet=True)
    return None


def explore(max_legs: int = 150, skip: set | None = None):
    """(skip: extra squares never to target; known traps and avoid() squares
    are always skipped.)"""
    from .nav import bad_squares
    ctx.require_command("explore()")
    skip = set(skip or ()) | bad_squares()
    return _explore(max_legs, skip)


def _explore(max_legs: int, skip: set):
    """Travel to unexplored frontiers until none remain (or max_legs).

    Returns a dict: {"reason", "legs", "unreachable", "locked", "avoided"}.
    "reason" starts with "explored" only when nothing is left that could be
    reached; when locked doors, avoided squares or an adjacent monster stop
    it, it says "blocked: ..." with what to do. Inside `nh exec` it pauses
    like any do() on anything unusual (combat, big HP loss, new hostile
    monsters, non-routine messages). Locked doors are never kicked
    automatically (shop doors, Minetown): use kick_door(x, y) yourself."""
    from .mapview import bfs_path
    from .nav import _mdesc, bad_squares, blockers, travel
    legs = 0
    unreachable, locked = [], []
    why = {"avoided": []}
    boulders_hit: list = []
    stuck = 0

    def result(reason):
        return {"reason": reason, "legs": legs, "unreachable": unreachable, "locked": locked,
                "avoided": why["avoided"], "boulders": boulders_hit + [b for b in _boulder_leads()
                                                                        if b not in boulders_hit]}

    def finished():
        left = []
        if locked:
            left.append(f"locked doors {locked} (kick_door(x, y) from an orthogonally adjacent square — "
                        "never a shop door ('Closed for inventory') or anywhere in Minetown)")
        if why["avoided"]:
            left.append(f"frontiers {why['avoided']} only reachable across avoided squares {sorted(bad_squares())}")
        if unreachable:
            left.append(f"frontiers {unreachable} travel couldn't reach")
        bl = boulders_hit + [b for b in _boulder_leads() if b not in boulders_hit]
        if bl:
            left.append(f"boulders {bl} in the way / next to unexplored space (travel never pushes: step into "
                        "one to push it if the square beyond is free; in Sokoban follow the solution)")
        if not left:
            return result("explored (no reachable frontier left) — search dead ends / closets for hidden passages")
        return result("blocked: " + "; ".join(left))

    while legs < max_legs:
        s = ctx.last()
        if s.state.kind != "command":
            return result(f"not at command prompt ({s.state.kind}: {s.state.prompt!r})")
        hero = s.hero
        bad = bad_squares()
        target = _pick_target(skip, bad, why)
        if target is None:
            return finished()
        bad = bad - {target}
        cur = ctx.last()
        direct = bfs_path(cur, hero, target, allow_monsters=True) if (bad and hero) else None
        if direct and any(c in bad for c in direct):
            ctx.do("<Esc>", quiet=True)          # close the travel prompt; walk a detour instead
            try:
                s = travel(*target)
            except NavError:
                skip.add(target)
                unreachable.append(target)
                continue
        else:
            from .nav import cursor_to, leg_cap, waypoint
            wp = waypoint(cur, target, leg_cap(cur))
            if wp != target:
                cursor_to(*wp)            # a short leg: look around before going further
            s = ctx.do(".", ok=BENIGN)
        legs += 1
        if s.state.kind != "command":
            return result(f"stopped: {s.state.kind} {s.state.prompt!r}")
        text = " ".join(s.messages)
        if ("You stop in front of the door" in text or "That door is closed" in text) and s.hero is not None:
            door = _adjacent_closed_door(s, target)
            for _try in range(6):
                if door is None:
                    break
                s = ctx.do(_dir_key(s.hero, door), ok=BENIGN)
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
        if s.hero == hero and not text:
            blk = blockers(s)
            hostile = [m for m in blk if not m.get("peaceful")]
            if hostile:
                return result(f"blocked: hostile {_mdesc(hostile)} adjacent — travel never starts next to "
                              "one; fight() it or step away, then explore() again")
            if blk:
                ctx.do("s", ok=BENIGN)            # a peaceful in the way: give it a turn
                stuck += 1
                if stuck > 3:
                    return result(f"blocked: {_mdesc(blk)} stays next to you; step around it, then explore()")
                continue
        if "blocks your path" in text and "boulder" not in text:
            # a peaceful (e.g. shopkeeper) in the way: wait a turn and retry
            ctx.do("s", ok=BENIGN)
            stuck += 1
            if stuck > 3:
                skip.add(target)
                stuck = 0
            continue
        if s.hero != hero and s.hero != target and not text:
            stuck = 0
            continue                      # a leg toward the target: keep going
        if any(h in text for h in FAIL_HINTS) or s.hero == hero:
            if "boulder" in text and s.hero is not None:
                hx, hy = s.hero
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if (dx or dy) and s.screen.at(hx + dx, hy + dy) == "0" and (hx + dx, hy + dy) not in boulders_hit:
                            boulders_hit.append((hx + dx, hy + dy))
            unreachable.append(target)
            skip.add(target)
            continue
        stuck = 0
    return result("max_legs reached")


def _boulder_leads(s=None) -> list:
    """Boulders ('0') next to never-seen space: possibly the only way on
    (NetHack's frontier finder ignores squares with objects on them)."""
    s = s or ctx.last()
    out = []
    for o in s.objects:
        if o["ch"] != "0":
            continue
        x, y = o["x"], o["y"]
        if any(s.screen.at(x + dx, y + dy) == " " for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1))):
            out.append((x, y))
    return out


def search_until_change(max_turns: int = 30, step: int = 5):
    """Search in place in bursts until the map changes (hidden door/passage
    found) or max_turns pass. Returns (found: bool, snap)."""
    s = ctx.last()
    before = [s.screen.row(y) for y in range(1, 22)]
    done = 0
    while done < max_turns:
        s = ctx.do(f"{step}s", ok=[r"^You find "])
        done += step
        now = [s.screen.row(y) for y in range(1, 22)]
        if any("You find" in m for m in s.messages):
            return True, s
        changed = sum(1 for a, b in zip(before, now) for ca, cb in zip(a, b)
                      if ca == " " and cb in "#.|-+")
        if changed >= 1:
            return True, s
        if s.state.kind != "command":
            return False, s
    return False, s
