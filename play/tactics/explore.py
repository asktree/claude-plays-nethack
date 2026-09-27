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

import re

from . import ctx
from .mapview import DIR_KEY, is_closed_door
from .nav import NavError

from .benign import BENIGN  # noqa: E402

FAIL_HINTS = ("A boulder blocks your path", "in vain", "cannot move past", "carrying too much")


def _dir_key(frm, to):
    dx, dy = to[0] - frm[0], to[1] - frm[1]
    return DIR_KEY.get((max(-1, min(1, dx)), max(-1, min(1, dy))), ".")


def _adjacent_closed_door(s, target):
    """The closed door next to the hero (orthogonal), preferring `target`.
    After "That door is closed." any brown '+' beside you counts, even one
    the screen heuristic took for a spellbook."""
    hx, hy = s.hero
    orth = [(hx + dx, hy + dy) for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1))]
    cands = [c for c in orth if is_closed_door(s, *c)] or \
            [c for c in orth if s.screen.at(*c) == "+" and s.screen.color_at(*c) == 3]
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


def _on_known_ground(s, x, y) -> bool:
    """Next to map you know (a walkable square, wall or door): detected gold
    or objects shown by magic inside solid rock / a closed vault aren't."""
    from .mapview import is_walkable
    return any(is_walkable(s, x + dx, y + dy, allow_monsters=True) or s.screen.at(x + dx, y + dy) in "|-+"
               for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)


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
        if o["ch"] in "0`" or (x, y) in bad or (x, y) in getattr(s, "solid_mem", ()) \
                or not _on_known_ground(s, x, y):
            continue
        # a blank square beside it that you were never next to (standing next to the pile shows the
        # pile, not what lies beyond it in a dark corridor)
        if any(s.screen.at(x + dx, y + dy) == " " and (x + dx, y + dy) not in near
               for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1))):
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
        if c in bad:
            skip.add(c)                  # the frontier itself is an avoided square
            if c not in why["avoided"]:
                why["avoided"].append(c)
            continue
        if c in skip:
            continue
        if bad and hero is not None:
            av = frozenset(set(bad) - {c})
            # (the second check lets the route cross '^': a frontier behind one known trap or hole
            # is "reachable only across an avoided square", not "unknown" — NetHack's travel would
            # otherwise guess toward it and wander)
            if (bfs_path(s, hero, c, avoid=av, allow_monsters=True) is None
                    and bfs_path(s, hero, c, allow_monsters=True, allow_traps=True) is not None):
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


def explore(max_legs: int = 150, skip: set | None = None, auto_fight: bool = True, medusa_ok: bool = False,
            cross_traps=False):
    """(skip: extra squares never to target; known traps and avoid() squares
    are always skipped. auto_fight: fight adjacent hostiles that are all
    trivial for you (combat.auto_fightable: newts, rats, jackals...) on the
    spot, and don't pause when such a monster comes into view; anything
    else still pauses / stops as before. cross_traps=True: when the only
    frontiers left lie behind known traps, trek() to them across the ones
    trap_crossable() allows for you (squeaky boards, arrow traps, pits...;
    or a list of trap names), then explore on.)"""
    import contextlib
    from .nav import bad_squares
    ctx.require_command("explore()")
    from .nav import _medusa_check, engulfed_check
    engulfed_check(ctx.last(), "explore()")
    _medusa_check(ctx.last(), (-1, -1), "explore()", medusa_ok)
    skip0 = set(skip or ())
    skip = skip0 | bad_squares()
    if auto_fight and ctx.monster_filter:
        from .combat import not_auto_fightable
        guard = ctx.monster_filter(not_auto_fightable)
    else:
        guard = contextlib.nullcontext()
    with guard:
        r = _explore(max_legs, skip, auto_fight)
        tried: set = set()
        for _round in range(4):
            if not cross_traps or not r.get("avoided") or not r["reason"].startswith(("blocked", "explored")):
                break
            from .nav import trek
            from .mapview import dist as _d
            s = ctx.last()
            if s.state.kind != "command" or s.hero is None:
                break
            moved = False
            for c in sorted((c for c in r["avoided"] if c not in tried), key=lambda c: _d(c, s.hero))[:3]:
                tried.add(c)
                try:
                    s2 = trek(*c, cross_traps=cross_traps)
                except NavError as e:
                    print(f"explore: no crossing toward {c}: {e}")
                    continue
                if s2.state.kind != "command" or s2.hero != s.hero:
                    moved = True
                    break
            if not moved or ctx.last().state.kind != "command":
                break
            r = _explore(max_legs, skip0 | bad_squares(), auto_fight)
        return r


def _explore(max_legs: int, skip: set, auto_fight: bool = False):
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
    why = {"avoided": [], "squeeze": []}
    boulders_hit: list = []
    cleared: set = set()             # 'I' markers explore already tried to clear (once each)
    stuck = 0

    def result(reason):
        now = ctx.last()
        # (a door that has opened since — unlocked, kicked, or opened by a monster — isn't locked any more)
        still = [d for d in locked if now is None or now.screen.at(*d) == "+"]
        return {"reason": reason, "legs": legs, "unreachable": unreachable, "locked": still,
                "avoided": why["avoided"], "boulders": boulders_hit + [b for b in _boulder_leads()
                                                                        if b not in boulders_hit]}

    def finished():
        left = []
        now = ctx.last()
        # a locked door only blocks while unseen ground lies next to it (p3: the room behind one was
        # explored through its other doorways, yet the verdict still blamed the door)
        live = [d for d in locked if any(now.screen.at(d[0] + dx, d[1] + dy) == " "
                                         for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        if live:
            left.append(f"locked doors {live} (unlock(x, y) with a key/lock pick/credit card, or "
                        "kick_door(x, y) from an orthogonally adjacent square — never a shop door ('Closed for "
                        "inventory'), and no kicking anywhere in Minetown)")
        for c in _trap_frontiers(now, bad_squares()):
            # a known trap with unseen ground beyond it (p1 shift 28: the sleeping gas trap (48,13) was the
            # only way east): NetHack's frontier finder never offers a trap square, so name it here
            if c not in why["avoided"]:
                why["avoided"].append(c)
        niches = dict(getattr(ctx.last(), "niche_mem", None) or {})
        if niches:
            # a trapped closet is one square with nothing behind it: not a frontier worth reporting
            why["avoided"] = [c for c in why["avoided"] if c not in niches]
        if why["avoided"]:
            from .nav import special_room_zone
            zone = special_room_zone()
            in_room = [c for c in why["avoided"] if c in zone]
            others = [c for c in why["avoided"] if c not in zone]
            bad = sorted(c for c in bad_squares() if c not in zone)
            fd = getattr(ctx.last(), "feature_desc", None) or {}
            minor = [c for c in bad if re.search(r"\b(?:dart|arrow|squeaky board|rust|falling rock|bear) trap\b|"
                                                 r"squeaky board", fd.get(c, ""))]
            kinds = sorted(set(zone.values()))
            if others:
                left.append(f"frontiers {others} only reachable across avoided squares {bad}"
                            + (f" or the {'/'.join(kinds)} kept out" if kinds else "")
                            + (f" — {', '.join(f'{c} {fd[c]}' for c in minor[:3])} is a minor trap: cross it on "
                               "purpose with travel next to it, then step_onto(x, y) (a bear trap holds you a few "
                               "turns; a falling rock hurts without a helmet)" if minor else ""))
            if in_room:
                left.append(f"{len(in_room)} frontier(s) inside the {'/'.join(sorted({zone[c] for c in in_room}))} "
                            f"(e.g. {in_room[:3]}): kept out while its monsters live — forget_room() to go in")
        if unreachable:
            left.append(f"frontiers {unreachable} travel couldn't reach")
        if why["squeeze"]:
            left.append(f"the known routes squeeze diagonally between rock at {sorted(set(why['squeeze']))[:6]}: "
                        "NetHack refuses that while your inventory weighs more than 600 — drop heavy things "
                        "(or dig / find another way)")
        bl = boulders_hit + [b for b in _boulder_leads() if b not in boulders_hit]
        if bl:
            lev = "Lev" in (ctx.last().status.conditions if ctx.last().status.ok else ())
            left.append(f"boulders {bl} in the way / next to unexplored space ("
                        + ("you are LEVITATING: you can't push boulders now" if lev else
                           "travel never pushes: step into one to push it if the square beyond is free; in "
                           "Sokoban follow the solution") + ")")
        hint = _hidden_stairs_hint()
        if not left:
            de = dead_ends()
            r = result("explored (no reachable frontier left) — search for hidden passages: "
                       + (f"corridor dead ends {de}, then " if de else "") + "closets / room walls facing "
                       "unexplored space" + hint)
            r["dead_ends"] = de
            return r
        r = result("blocked: " + "; ".join(left) + hint)
        r["dead_ends"] = dead_ends()
        return r

    fights = 0
    idle, last_mark = 0, None
    known0, stale, legs0 = -1, 0, 0    # map squares shown; legs in a row that showed nothing new
    while legs < max_legs:
        s = ctx.last()
        if s.state.kind != "command":
            return result(f"not at command prompt ({s.state.kind}: {s.state.prompt!r})")
        # no-progress breaker: the same square and turn for several rounds, with no target
        # ruled out in between (skip/locked growing is progress), means a loop
        mark = (s.hero, s.status.turn, len(skip), len(locked))
        idle = idle + 1 if mark == last_mark else 0
        last_mark = mark
        if idle >= 6:
            return result(f"stuck: no move and no game time for {idle} rounds at {s.hero} "
                          f"(last messages: {s.messages}) — look at the screen and act by hand")
        from nh.parse import MAP_BOTTOM as _MB, MAP_TOP as _MT
        known = sum(1 for y in range(_MT + 1, _MB + 1) for ch in s.screen.row(y) if ch != " ")
        if legs > legs0:                       # (only travel legs count; fights and door-opening don't)
            stale = stale + 1 if known <= known0 else 0
            legs0 = legs
        known0 = max(known0, known)
        if stale >= 12:
            avoided = sorted(bad_squares())
            return result(f"stuck: {stale} legs in a row showed nothing new — NetHack's travel is guessing "
                          f"its way to frontiers it can't reach (frontiers: {frontiers()[:6]}; avoided squares on "
                          f"the way: {avoided[:8]}): cross a trap/hole on purpose (step_onto), dig around it, "
                          "or search for a hidden passage")
        if auto_fight and fights < 30:
            from .combat import fight_trivial
            fs = fight_trivial(s)
            if fs is not None:
                fights += 1
                continue
        hero = s.hero
        bad = bad_squares()
        target = _pick_target(skip, bad, why)
        if target is None:
            # NetHack's own finder skips squares with objects on them and misses some dark-maze edges:
            # try the screen frontiers (walkable squares beside never-seen space) before giving up
            from .mapview import bfs_path as _bfs, dist as _dist
            cur = ctx.last()
            sf = screen_frontiers(cur)
            why["avoided"] += [c for c in sf if c in bad and c not in why["avoided"]]
            extra = [c for c in sf if c not in skip and c not in bad and c != cur.hero
                     and cur.hero is not None and _bfs(cur, cur.hero, c, allow_monsters=True) is not None]
            if not extra:
                return finished()
            if stale >= 4:
                # NetHack sees no frontier and the last legs to screen edges showed nothing new: what's
                # left is dark room floor you haven't stood next to, not unexplored ground
                r = finished()
                r["reason"] += (f" (NetHack reports no unexplored spot; {len(extra)} dark edge square(s) like "
                                f"{extra[:4]} were left unvisited after {stale} legs showed nothing new)")
                return r
            tgt = min(extra, key=lambda c: _dist(c, cur.hero))
            skip.add(tgt)
            try:
                s = travel(*tgt)
            except NavError as e:
                if _cleared_I(tgt, e, cleared):
                    skip.discard(tgt)
                    continue
                unreachable.append(tgt)
                continue
            legs += 1
            if s.state.kind != "command":
                return result(f"stopped: {s.state.kind} {s.state.prompt!r}")
            continue
        bad = bad - {target}
        cur = ctx.last()
        direct = bfs_path(cur, hero, target, allow_monsters=True) if (bad and hero) else None
        if direct and any(c in bad for c in direct):
            ctx.do("<Esc>", quiet=True)          # close the travel prompt; walk a detour instead
            try:
                s = travel(*target)
            except NavError as e:
                if _cleared_I(target, e, cleared):
                    continue
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
            known = ctx.game.locked_doors.setdefault(ctx.game.level_key(s.status), set()) \
                if hasattr(ctx.game, "locked_doors") else set()
            opened = False
            for _try in range(6):
                if door is None or door in known:
                    break
                if _try == 0:
                    print(f"explore(): opening the door at {door}")   # (a booby-trapped one goes KABOOM)
                s = ctx.do(_dir_key(s.hero, door), ok=BENIGN)
                text = " ".join(s.messages)
                if "This door is locked" in text:
                    known.add(door)
                    break
                if "The door opens" in text or s.state.kind != "command":
                    opened = "The door opens" in text
                    break
            if not opened:
                # locked (or won't open): leave this frontier — it lies beyond that door
                if door is not None and door not in locked and door in known:
                    locked.append(door)
                if door is not None:
                    skip.add(door)
                skip.add(target)
            continue
        if "This door is locked" in text:
            if target not in locked:
                locked.append(target)
            skip.add(target)
            continue
        if "outside?" in text and ("leave your" in text.lower() or "leave the" in text.lower()):
            # shk.c: "Will you please leave your pick-axe outside?" — the shopkeeper blocks the door
            return result("blocked: a shopkeeper won't let you in with a digging tool — bag_put() it or drop it "
                          "outside the door, then explore() again (or skip the shop)")
        if s.hero == hero and not text:
            from .nav import _passive_only
            blk = blockers(s)
            hostile = [m for m in blk if not m.get("peaceful") and not _passive_only(m)]
            if hostile and auto_fight and fights < 30:
                from .combat import fight_trivial
                fs = fight_trivial(ctx.last())      # it may have been labelled only now (a newcomer)
                if fs is not None:
                    fights += 1
                    continue
            if hostile:
                return result(f"blocked: hostile {_mdesc(hostile)} adjacent — travel never starts next to "
                              "one; fight() it or step away, then explore() again")
            if blk:
                # a peaceful (or a floating eye / mold: no active attack) next to you: NetHack's travel
                # won't start, but plain steps along our own route (never into a monster) get you away
                from .mapview import bfs_path as _bfs
                from .nav import walk_path
                own = _bfs(ctx.last(), hero, target, avoid=frozenset(bad_squares() - {target}),
                           allow_monsters=False, allow_pets=True) if hero else None
                if own and stuck < 3:
                    try:
                        s2 = walk_path(own[:3])
                    except NavError:
                        s2 = None
                    if s2 is not None and s2.hero != hero:
                        stuck += 1
                        continue
                ctx.do(".", ok=BENIGN)            # ...else give it a turn to move off
                stuck += 1
                if stuck > 5:
                    return result(f"blocked: {_mdesc(blk)} stays next to you; step around it, then explore()")
                continue
        if "blocks your path" in text and "boulder" not in text:
            # a peaceful (e.g. shopkeeper) in the way: wait a turn and retry
            ctx.do(".", ok=BENIGN)
            stuck += 1
            if stuck > 3:
                skip.add(target)
                stuck = 0
            continue
        if s.hero != hero and s.hero != target and not text:
            stuck = 0
            continue                      # a leg toward the target: keep going
        if s.hero == hero and not any(h in text for h in FAIL_HINTS) and hero is not None:
            # NetHack's travel only paths over squares you have *seen*; a displayed but
            # never-walked dark corridor can still be walked: try our own route
            from .nav import walk_path
            own = bfs_path(ctx.last(), hero, target, avoid=frozenset(bad_squares() - {target}),
                           allow_monsters=False, allow_pets=True)
            if own:
                try:
                    s = walk_path(own[:8])
                except NavError as e:
                    # (p3 shift 10: "can't squeeze diagonally" with a pack over 600 escaped explore() —
                    # skip that frontier and name the squeeze in the verdict)
                    from .mapview import squeeze_steps
                    sq = squeeze_steps(ctx.last(), own, hero)
                    why["squeeze"].extend(sq)
                    if not sq:
                        print(f"explore: our own route to {target} failed ({e}) — skipping it")
                    unreachable.append(target)
                    skip.add(target)
                    continue
                if s.hero != hero:
                    stuck = 0
                    continue
        if any(h in text for h in FAIL_HINTS) or s.hero == hero:
            if "boulder" in text and s.hero is not None:
                hx, hy = s.hero
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if (dx or dy) and s.screen.at(hx + dx, hy + dy) == "0" and (hx + dx, hy + dy) not in boulders_hit:
                            boulders_hit.append((hx + dx, hy + dy))
            unreachable.append(target)
            skip.add(target)
            if s.hero is not None:
                from .mapview import squeeze_steps
                own = bfs_path(ctx.last(), s.hero, target, allow_monsters=True)
                why["squeeze"].extend(squeeze_steps(ctx.last(), own, s.hero))
            continue
        stuck = 0
    return result("max_legs reached")


def _cleared_I(target, err, tried: set) -> bool:
    """travel() refused a target holding a remembered 'I' (p1 shift 29: explore stalled on stale markers
    from a telepathy scan): search next to it once (clear_I) — True when it is gone and the target is free."""
    if "holds an 'I'" not in str(err) or target in tried:
        return False
    tried.add(target)
    from .nav import clear_I
    try:
        return clear_I(*target)
    except NavError as e:
        print(f"explore: couldn't clear the 'I' at {target}: {e}")
        return False


def _trap_frontiers(s, bad) -> list:
    """Avoided squares (known traps, avoid() squares) that border never-seen
    ground and that you can reach (crossing only known traps): the way on may
    lie across one of them. (Blanks next to a square you stood on are seen
    rock, as for screen_frontiers.)"""
    from nh.parse import MAP_BOTTOM, MAP_TOP
    from .mapview import bfs_path
    if s is None or s.hero is None:
        return []
    near = {(vx + dx, vy + dy) for (vx, vy) in ctx.game.visited.get(ctx.game.level_key(s.status), set())
            for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    mem = getattr(s, "floor_mem", ())
    out = []
    for c in sorted(bad):
        x, y = c
        if c == s.hero or not any(s.screen.at(x + dx, y + dy) == " " and s.screen.color_at(x + dx, y + dy) != 6
                                  and (x + dx, y + dy) not in near and (x + dx, y + dy) not in mem
                                  and MAP_TOP < y + dy <= MAP_BOTTOM and 0 < x + dx < 79
                                  for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1))):
            continue
        if bfs_path(s, s.hero, c, allow_monsters=True, allow_traps=True) is not None:
            out.append(c)
    return out


def screen_frontiers(s=None) -> list:
    """Walkable squares next to blank (never displayed) space, from the
    screen: where unexplored ground may continue. Blank squares next to a
    square you have stood on are seen rock and don't count."""
    from nh.parse import MAP_BOTTOM, MAP_TOP
    from .mapview import is_walkable
    s = s or ctx.last()
    near = set()
    for (vx, vy) in ctx.game.visited.get(ctx.game.level_key(s.status), set()):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                near.add((vx + dx, vy + dy))
    mem = getattr(s, "floor_mem", ())      # Rogue level: dark-room floor seen before shows blank again
    out = []
    for y in range(MAP_TOP + 1, MAP_BOTTOM + 1):
        for x in range(1, 79):
            if not is_walkable(s, x, y, allow_monsters=True):
                continue
            if any(s.screen.at(x + dx, y + dy) == " " and (x + dx, y + dy) not in near
                   and (x + dx, y + dy) not in mem and MAP_TOP < y + dy <= MAP_BOTTOM
                   for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1))):
                out.append((x, y))
    return out


def head_to(x: int, y: int, max_legs: int = 30):
    """Make for (x, y) across unexplored space (mazes, the Mines, Gehennom):
    while no known path leads there, travel to the frontier square (walkable,
    beside never-seen space) nearest to (x, y) and look again; once a known
    path exists, travel() the rest. Each leg is a travel() (pauses, auto-fight
    and the never-attack rules as usual). Returns the final snap; NavError when
    no reachable frontier is left or after max_legs."""
    from .mapview import bfs_path, dist
    from .nav import engulfed_check, travel
    target = (x, y)
    tried: set = set()
    s = ctx.last()
    engulfed_check(s, f"head_to{target}")
    for _leg in range(max_legs):
        s = ctx.last()
        if s.state.kind != "command" or s.hero is None:
            return s
        if s.hero == target:
            return s
        if bfs_path(s, s.hero, target, allow_monsters=True) is not None:
            return travel(x, y)
        fr = [c for c in screen_frontiers(s) if c not in tried and c != s.hero
              and bfs_path(s, s.hero, c, allow_monsters=True) is not None]
        if not fr:
            raise NavError(f"head_to{target}: no reachable frontier left (tried {len(tried)}) — search for "
                           "hidden passages, dig, or pick another target")
        best = min(fr, key=lambda c: (dist(c, target), dist(c, s.hero)))
        tried.add(best)
        ctx.activity(f"head_to{target}: leg {_leg + 1} to frontier {best}")
        try:
            s = travel(*best)
        except NavError as e:
            print(f"head_to: frontier {best} unreachable ({e}); trying another")
            continue
        if s.state.kind != "command":
            return s
    raise NavError(f"head_to{target}: not there after {max_legs} legs (at {ctx.last().hero})")


def dead_ends(s=None, limit: int = 8) -> list:
    """Corridor squares ('#') with at most one walkable neighbour: corridors
    that just stop, the first places to search for a hidden passage
    (search(15) standing on one). Nearest first."""
    from nh.parse import MAP_BOTTOM, MAP_TOP
    from .mapview import is_walkable, neighbors
    s = s or ctx.last()
    out = []
    for y in range(MAP_TOP, MAP_BOTTOM + 1):
        for x, ch in enumerate(s.screen.row(y)):
            if ch != "#" or s.screen.color_at(x, y) not in (7, 8, 15):
                continue                     # corridors only (not trees, sinks, bars)
            if sum(1 for c in neighbors(x, y) if is_walkable(s, *c)) <= 1:
                out.append((x, y))
    h = s.hero
    if h is not None and h not in out:
        # the square you stand on shows '@', not '#': a corridor end with you on it counts too
        nb = [c for c in neighbors(*h) if is_walkable(s, *c)]
        if len(nb) <= 1 and all(s.screen.at(*c) == "#" for c in nb):
            out.append(h)
    if h:
        out.sort(key=lambda c: max(abs(c[0] - h[0]), abs(c[1] - h[1])))
    return out[:limit]


def _hidden_stairs_hint() -> str:
    """If no down stairs are known on this level, name the object squares you
    haven't stood on: stairs under an object or a statue don't show."""
    from .nav import find, known_cells
    s = ctx.last()
    known = known_cells(">", s, rescan=True)      # (#terrain, no game time: stairs under gold you've seen)
    if known:
        shown = set(find(s, ">"))
        hidden = [c for c in known if c not in shown]
        if shown or not hidden:
            return ""
        return (f" — the down stairs are at {hidden[0]}, hidden under an object or monster (the game's own "
                "map, #terrain): travel_to('>') / go_down() use it")
    visited = ctx.game.visited.get(ctx.game.level_key(s.status), set())
    cands = [(o["x"], o["y"]) for o in s.objects if (o["x"], o["y"]) not in visited and o["ch"] not in "0`"
             and _on_known_ground(s, o["x"], o["y"])]
    cands += [(m["x"], m["y"]) for m in s.monsters if m.get("statue") and (m["x"], m["y"]) not in visited]
    if not cands:
        return " — no down stairs seen yet"
    return (" — no down stairs seen yet: stairs can hide under objects and statues; step onto / here() these: "
            + str(cands[:12]))


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
