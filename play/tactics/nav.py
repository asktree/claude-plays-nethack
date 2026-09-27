"""Navigation tactics: cursor positioning, travel, farlook, stepping."""

from __future__ import annotations

from . import ctx
from .benign import BENIGN
from .mapview import DIR_KEY, bfs_path, dist, find, nearest


class NavError(Exception):
    pass


def _cursor_keys(cx, cy, tx, ty) -> str:
    """Keys that move the getpos cursor from (cx,cy) to (tx,ty).
    Capital letters move 8 cells (truncated at map edges, so we verify)."""
    keys = []
    dx, dy = tx - cx, ty - cy
    while abs(dx) >= 8 and abs(dy) >= 8:
        k = DIR_KEY[((dx > 0) - (dx < 0), (dy > 0) - (dy < 0))].upper()
        keys.append(k)
        dx -= 8 * ((dx > 0) - (dx < 0))
        dy -= 8 * ((dy > 0) - (dy < 0))
    while abs(dx) >= 8:
        keys.append("L" if dx > 0 else "H")
        dx -= 8 if dx > 0 else -8
    while abs(dy) >= 8:
        keys.append("J" if dy > 0 else "K")
        dy -= 8 if dy > 0 else -8
    while dx and dy:
        keys.append(DIR_KEY[((dx > 0) - (dx < 0), (dy > 0) - (dy < 0))])
        dx -= (dx > 0) - (dx < 0)
        dy -= (dy > 0) - (dy < 0)
    while dx:
        keys.append("l" if dx > 0 else "h")
        dx -= (dx > 0) - (dx < 0)
    while dy:
        keys.append("j" if dy > 0 else "k")
        dy -= (dy > 0) - (dy < 0)
    return "".join(keys)


def cursor_to(tx, ty, rounds=5):
    """In a getpos prompt, move the cursor to (tx, ty). Returns final snap."""
    s = ctx.last()
    for _ in range(rounds):
        if s.state.kind != "getpos":
            if s.state.kind != "command":
                ctx.do("<Esc>", quiet=True)
            raise NavError(f"not in a position prompt (state={s.state.kind}: {s.state.prompt!r})")
        cx, cy = s.screen.cursor
        if (cx, cy) == (tx, ty):
            return s
        s = ctx.do(_cursor_keys(cx, cy, tx, ty), quiet=True)
    if s.screen.cursor != (tx, ty):
        ctx.do("<Esc>", quiet=True)
        raise NavError(f"could not place cursor at {(tx, ty)} (at {s.screen.cursor})")
    return s


def farlook(x, y) -> str:
    """Describe what's displayed at (x, y) using ';' (takes no game time)."""
    s = ctx.do(";", quiet=True)
    if s.state.kind != "getpos":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        raise NavError(f"';' did not open a position prompt: {s.state.kind} {s.state.prompt!r}")
    cursor_to(x, y)
    s = ctx.do(".", quiet=True)
    txt = " ".join(s.messages).strip()
    if s.state.kind not in ("command",):
        # e.g. a lingering prompt; get back to the map
        ctx.do("<Esc>", quiet=True)
    return txt


def bad_squares(s=None) -> set:
    """Known trap squares (incl. ones hidden under objects; read from the
    game's own memory via #terrain on each level) + the player's avoid set
    for the current level. Both persist across daemon restarts."""
    s = s or ctx.last()
    lv = ctx.game.level_key(s.status)
    mimics = {(m["x"], m["y"]) for m in (s.monsters or []) if m.get("mimic")}
    return set(ctx.game.traps.get(lv, set())) | set(ctx.game.avoid.get(lv, set())) | mimics


def avoid(*cells, clear=False):
    """Mark squares to avoid on this level: avoid((19,6), (20,6)). Honoured by
    travel(), explore() and walk_path(); remembered across daemon restarts.
    avoid() lists all bad squares; avoid(clear=True) forgets this level's
    avoid set (traps stay)."""
    s = ctx.last()
    st = ctx.game.avoid.setdefault(ctx.game.level_key(s.status), set())
    if clear:
        st.clear()
    for c in cells:
        st.add(tuple(c))
    return sorted(bad_squares(s))


def walk_path(path, ok=None):
    """Walk a list of cells one step at a time, verifying each arrival."""
    s = ctx.last()
    for cell in path:
        h = s.hero
        if h is None:
            return s
        key = DIR_KEY.get((cell[0] - h[0], cell[1] - h[1]))
        if key is None:
            raise NavError(f"walk_path: {cell} is not adjacent to {h}")
        s = ctx.do(key, ok=ok if ok is not None else BENIGN)
        if s.hero != cell:
            return s
    return s


def blockers(s=None) -> list:
    """Non-tame monsters next to the hero. NetHack's travel/run never starts
    beside one (lookaround() stops before the first step, silently)."""
    s = s or ctx.last()
    return [m for m in (s.monsters or []) if m.get("dist") == 1 and not m.get("tame")
            and not m.get("pet") and not m.get("statue")]


def _mdesc(ms) -> str:
    return ", ".join(f"{m.get('desc') or m['ch']} at ({m['x']},{m['y']})" for m in ms)


LEG = 8          # max squares per travel leg, so the kernel looks around between legs
LEG_DANGER = 4   # ... while a hostile is in view or was seen in the last 30 turns


def leg_cap(s=None) -> int:
    """How far one travel leg may go right now. NetHack's travel only stops
    for a monster that is already adjacent, so a fast monster (a yellow light,
    speed 13) can close in and attack during one long leg; short legs give the
    harness a look (and a 'new monster' pause) every few squares."""
    s = s or ctx.last()
    if s.hostiles():
        return LEG_DANGER
    tr = getattr(ctx.game, "tracker", None)
    turn = s.status.turn or 0
    if tr is not None:
        for r in tr.gone(turn):
            d = r.get("desc") or ""
            if turn - (r.get("turn") or 0) <= 30 and not d.startswith(("peaceful ", "tame ")) \
                    and not r.get("statue"):
                return LEG_DANGER
    return LEG


def waypoint(s, target, cap):
    """The square `cap` steps along our known-map path toward target (or the
    target itself if it's closer / there's no known path)."""
    if s.hero is None or cap is None:
        return target
    path = bfs_path(s, s.hero, target, allow_monsters=True)
    if not path or len(path) <= cap:
        return target
    occupied = {(m["x"], m["y"]) for m in (s.monsters or []) if not m.get("tame")}
    for i in range(cap - 1, -1, -1):
        if path[i] not in occupied:
            return path[i]
    return target


def travel(x, y, max_legs=40, max_dist=None, wait_peaceful=3, leg=None, auto_fight=True):
    """Travel to (x, y) with NetHack's `_` command (auto-pathing over known
    map; stops when something interesting happens). Re-issues while making
    progress. Returns the final Snap (check .hero, .messages).
    auto_fight: hostiles next to you that are all trivial for you
    (combat.auto_fightable) are fought on the spot, and such monsters coming
    into view don't pause; anything else pauses / raises as before.
    max_dist: refuse (NavError) if the known-map path is longer than this —
    a guard against burning many turns on a far-away target.
    If the hero doesn't move at all, raises NavError saying why (a hostile
    adjacent; a peaceful that stays in the way after `wait_peaceful` waits;
    no known path) instead of returning silently.
    Long trips go in legs of at most leg_cap() squares (8, or 4 with a
    hostile around) so a monster coming into view pauses the script early;
    leg=0 disables that."""
    import contextlib
    ctx.require_command("travel()")
    if auto_fight and ctx.monster_filter:
        from .combat import not_auto_fightable
        guard = ctx.monster_filter(not_auto_fightable)
    else:
        guard = contextlib.nullcontext()
    with guard:
        return _travel(x, y, max_legs, max_dist, wait_peaceful, leg, auto_fight)


def _travel(x, y, max_legs, max_dist, wait_peaceful, leg, auto_fight):
    s = ctx.last()
    occ = [m for m in (s.monsters or []) if (m["x"], m["y"]) == (x, y) and not m.get("tame")
           and not m.get("pet") and not m.get("statue")]
    if occ and s.hero != (x, y):
        raise NavError(f"travel target {(x, y)} is occupied by {_mdesc(occ)} (travelling there would bump "
                       "into it and waste a turn)")
    if max_dist is not None and s.hero is not None:
        path = bfs_path(s, s.hero, (x, y), allow_monsters=True)
        if path is None or len(path) > max_dist:
            raise NavError(f"travel to {(x, y)}: path length {None if path is None else len(path)} > max_dist {max_dist}")
    # NetHack's travel avoids traps it displays, but not traps hidden under
    # objects or squares we chose to avoid: if the direct route crosses one,
    # walk our own detour step by step instead.
    bad = {c for c in bad_squares(s) if c != (x, y)}
    if bad and s.hero is not None:
        direct = bfs_path(s, s.hero, (x, y), allow_monsters=True)
        if direct and any(c in bad for c in direct):
            detour = bfs_path(s, s.hero, (x, y), avoid=frozenset(bad), allow_monsters=False)
            if detour is None:
                raise NavError(f"travel to {(x, y)}: every known route crosses an avoided square {sorted(bad)}")
            return walk_path(detour)
    waits = 0
    for _ in range(max_legs):
        h0 = s.hero
        if h0 == (x, y):
            return s
        if auto_fight:
            from .combat import fight_trivial
            fs = fight_trivial(s)
            if fs is not None:
                s = fs
                if s.state.kind != "command":
                    return s
                continue
        cap = leg_cap(s) if leg is None else (leg or None)
        tx, ty = waypoint(s, (x, y), cap)
        if (tx, ty) == (x, y) and h0 is not None and max(abs(x - h0[0]), abs(y - h0[1])) == 1:
            # last square by a plain step: NetHack's travel never picks anything up
            # (it sets 'nopick'), a plain move autopicks gold and thrown weapons
            s = _final_step(s, (x, y))
            if s.hero == (x, y) or s.state.kind != "command":
                return s
            if s.hero == h0:
                if _pet_in_way(s.messages) and waits < wait_peaceful + 2:
                    waits += 1
                    s = ctx.do("s", ok=BENIGN)
                    continue
                hostile = [m for m in blockers(s) if not m.get("peaceful")]
                raise NavError(f"travel to {(x, y)}: the last step from {h0} failed"
                               + (f" (hostile {_mdesc(hostile)} adjacent)" if hostile else "")
                               + (f"; messages: {s.messages}" if s.messages else ""))
            continue
        if (tx, ty) == (x, y) and h0 is not None:
            path = bfs_path(s, h0, (x, y), allow_monsters=True)
            if path and len(path) >= 2:
                tx, ty = path[-2]          # stop one short; the last step is a plain move
        s = ctx.do("_", quiet=True)
        if s.state.kind != "getpos":
            return s
        cursor_to(tx, ty)
        s = ctx.do(".", ok=BENIGN)
        if s.state.kind != "command":
            return s
        h1 = s.hero
        if h1 == (x, y) or h1 is None:
            return s
        if h1 == h0:
            blk = blockers(s)
            hostile = [m for m in blk if not m.get("peaceful")]
            if hostile:
                raise NavError(f"travel to {(x, y)} did not move: hostile {_mdesc(hostile)} adjacent — "
                               "travel never starts next to one. Fight it (fight()) or step away by hand.")
            if blk and waits < wait_peaceful:
                waits += 1
                print(f"travel: waiting a turn for {_mdesc(blk)} to move")
                s = ctx.do("s", ok=BENIGN)      # give the peaceful a turn to move off
                continue
            if blk:
                raise NavError(f"travel to {(x, y)} did not move: {_mdesc(blk)} stays next to you; "
                               "step around it by hand.")
            if any("door is closed" in m for m in s.messages):
                s = _open_door_toward(s, (x, y))    # travel never opens doors (autoopen is for plain steps)
                continue
            if _pet_in_way(s.messages):
                if waits < wait_peaceful + 2:
                    waits += 1
                    s = ctx.do("s", ok=BENIGN)      # your pet is in the way (1/7 of swaps fail; never in shops)
                    continue
                raise NavError(f"travel to {(x, y)} did not move: your pet stays in the way ({s.messages}); "
                               "step around it by hand")
            raise NavError(f"travel to {(x, y)} did not move (no known path?)"
                           + (f"; messages: {s.messages}" if s.messages else ""))
        if _notable(s.messages):
            return s   # something happened en route; let the caller look
    return s


_PET_IN_WAY = ("is in your way", "is in the way!", "doesn't seem to move!")
_DIAG_DOOR = r"^You can't move diagonally (?:out of|into) an intact doorway\."


def _pet_in_way(messages) -> bool:
    return any(p in m for m in messages or [] for p in _PET_IN_WAY)


def _final_step(s, target):
    """One plain step onto the adjacent target (picks up gold/thrown weapons,
    unlike travel). A diagonal into or out of a door square is illegal: then
    go round by the orthogonal square that isn't wall."""
    from .mapview import is_door, is_walkable
    h0 = s.hero
    dx, dy = target[0] - h0[0], target[1] - h0[1]
    s = ctx.do(DIR_KEY[(dx, dy)], ok=BENIGN + [_DIAG_DOOR])
    if s.hero == h0 and dx and dy and any("move diagonally" in m for m in s.messages):
        pets = {(m["x"], m["y"]) for m in (s.monsters or []) if m.get("tame") or m.get("pet")}
        for mid in ((h0[0] + dx, h0[1]), (h0[0], h0[1] + dy)):
            if (is_walkable(s, *mid, allow_monsters=False) or mid in pets) and not is_door(s, *mid):
                s = ctx.do(DIR_KEY[(mid[0] - h0[0], mid[1] - h0[1])], ok=BENIGN)
                if s.hero == mid and s.state.kind == "command":
                    s = ctx.do(DIR_KEY[(target[0] - mid[0], target[1] - mid[1])], ok=BENIGN)
                return s
    return s


def _open_door_toward(s, target):
    """Open the closed door next to you that lies toward target, by stepping
    into it (autoopen). Raises NavError if it is locked or won't open."""
    from .mapview import is_closed_door
    h = s.hero
    doors = [(h[0] + dx, h[1] + dy) for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1))
             if is_closed_door(s, h[0] + dx, h[1] + dy)]
    if not doors:
        raise NavError(f"travel: 'That door is closed' but no closed door next to {h}")
    door = min(doors, key=lambda d: dist(d, target))
    key = DIR_KEY[(door[0] - h[0], door[1] - h[1])]
    for _ in range(6):
        s = ctx.do(key, ok=BENIGN + [r"^The door opens\.", r"^The door resists", r"^This door is locked"])
        text = " ".join(s.messages)
        if "locked" in text:
            raise NavError(f"travel: the door at {door} is locked — kick_door{door} (never a shop door or "
                           "in Minetown), or go another way")
        if "door opens" in text or not is_closed_door(s, *door):
            return s
    raise NavError(f"travel: the door at {door} won't open (stuck?)")


def _notable(messages) -> list:
    """Messages that aren't routine for walking around (BENIGN + the kernel's
    DEFAULT_BENIGN): anything left deserves the caller's attention."""
    import re
    from nh.kernel import DEFAULT_BENIGN
    pats = [re.compile(p) for p in BENIGN]
    return [m for m in messages or [] if not any(p.search(m) for p in pats)
            and not any(p.search(m) for p in DEFAULT_BENIGN)]


def known_cells(ch: str, s=None, rescan: bool = False) -> list:
    """Cells showing `ch` now, plus (for stairs/fountains/altars/thrones)
    remembered ones hidden under objects, monsters or you. Nearest first.
    rescan=True: if none is known, read the game's own terrain memory first
    (#terrain, no game time) — it knows stairs under objects you've seen."""
    s = s or ctx.last()

    def cells_now():
        cells = set(find(s, ch))
        mem = getattr(ctx.game, "terrain_seen", {}).get(ctx.game.level_key(s.status), {})
        cells |= {c for c, v in mem.items() if v == ch}
        return cells
    cells = cells_now()
    if not cells and rescan and ch in "<>{_\\" and hasattr(ctx.game, "rescan_terrain"):
        ctx.game.rescan_terrain()
        cells = cells_now()
    h = s.hero or ctx.game.hero_pos
    return sorted(cells, key=lambda c: dist(c, h) if h else 0)


def travel_to(ch: str, index: int = 0, color_num: int | None = None):
    """Travel to the index-th nearest cell showing `ch` (e.g. '>', '<', '{');
    stairs/fountains/altars hidden under objects or monsters count too."""
    s = ctx.last()
    cells = find(s, ch, color_num) if color_num is not None else known_cells(ch, s, rescan=True)
    h = s.hero
    if not cells or h is None:
        raise NavError(f"no {ch!r} on the map")
    cells.sort(key=lambda c: dist(c, h))
    if index >= len(cells):
        raise NavError(f"only {len(cells)} {ch!r} on the map")
    return travel(*cells[index])


def step(direction: str, n: int = 1):
    """Move one square n times (direction: y k u h l b j n). Stops on messages
    (inside exec) like any do()."""
    s = ctx.last()
    for _ in range(n):
        s = ctx.do(direction)
    return s


def _use_stairs(ch: str, tries: int = 4):
    s = ctx.last()
    cells = known_cells(ch, s, rescan=True)
    if not cells:
        raise NavError(f"no {ch!r} known on this level")
    target = cells[0]
    for _ in range(tries):
        if s.hero == target:
            break
        s = travel(*target)
        if s.state.kind != "command":
            return s                     # a prompt interrupted: let the caller look
        s = ctx.last()
        if _notable(s.messages) and s.hero != target:
            return s                     # something happened on the way
    if s.hero != target:
        raise NavError(f"did not reach the {ch} at {target} (you are at {s.hero}); nothing pressed")
    return ctx.do(ch)


def go_down():
    """Travel to the nearest '>' (re-travelling after routine stops), check
    you are on it, then descend. Raises NavError instead of pressing '>'
    anywhere else."""
    return _use_stairs(">")


def go_up():
    """Like go_down() for '<'."""
    return _use_stairs("<")


def kick_door(x, y, tries: int = 8):
    """Kick the (adjacent) door at (x, y) until it opens/breaks. Never do this
    to shop doors (angers the shopkeeper) or in Minetown (angers the Watch)."""
    s = ctx.last()
    h = s.hero
    if h is None or max(abs(x - h[0]), abs(y - h[1])) != 1:
        raise NavError(f"kick_door: {(x, y)} is not adjacent to you at {h}")
    key = DIR_KEY[(x - h[0], y - h[1])]
    for _ in range(tries):
        s = ctx.do("<C-d>", quiet=True)
        if s.state.kind != "direction":
            return s
        s = ctx.do(key, ok=[r"^WHAMM", r"crashes open", r"^As you kick the door, it (crashes|shatters)"])
        text = " ".join(s.messages)
        if "crashes open" in text or "shatters" in text or "breaks" in text or ctx.last().screen.at(x, y) != "+":
            return s
    return s


def path_to(x, y, avoid_bad: bool = True) -> list:
    """Our known-map path from you to (x, y) (list of cells, excluding your
    square; [] if you're there; None if no known path). Honours known traps
    and avoid() squares unless avoid_bad=False. Walk it with walk_path(path)
    (one checked step at a time) or path_to(...)[:n] for the first n steps."""
    s = ctx.last()
    if s.hero is None:
        return None
    bad = frozenset(c for c in bad_squares(s) if c != (x, y)) if avoid_bad else frozenset()
    return bfs_path(s, s.hero, (x, y), avoid=bad, allow_monsters=False)
