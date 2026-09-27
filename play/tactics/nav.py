"""Navigation tactics: cursor positioning, travel, farlook, stepping."""

from __future__ import annotations

from . import ctx
from .benign import BENIGN
from .mapview import DIR_KEY, bfs_path, dist, find, nearest


class NavError(Exception):
    pass


class PetLost(NavError):
    """travel(with_pet=True): the pet dropped out of view."""


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
    with ctx.no_monster_pauses():
        return _farlook(x, y)


def _farlook(x, y) -> str:
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
    tr = getattr(ctx.game, "tracker", None)
    lab = tr.relabel(x, y, txt) if tr is not None and hasattr(tr, "relabel") else None
    if lab:
        # the obs shows it at once (an explicit look beats a label inherited from a look-alike)
        from nh.danger import note_for
        cur = ctx.last()
        xl = cur.status.xl if cur.status.ok else None
        for m in cur.monsters or []:
            if (m["x"], m["y"]) == (x, y):
                m.update(desc=lab, note=note_for(lab, xl), tame=lab.startswith("tame "),
                         peaceful=lab.startswith("peaceful "))
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


def occupants(s, cell) -> list:
    """Monsters (not your pet, not statues) displayed on `cell`, including a
    remembered unseen 'I': a plain step there attacks whatever is there."""
    cell = tuple(cell)
    return [m for m in (s.monsters or []) if (m["x"], m["y"]) == cell and not m.get("tame")
            and not m.get("pet") and not m.get("statue")]


def _check_free(s, cell, who: str):
    """Movement helpers never attack: refuse a plain step onto a monster."""
    occ = occupants(s, cell)
    if occ:
        m = occ[0]
        what = "a remembered unseen monster ('I')" if m["ch"] == "I" else _mdesc(occ)
        raise NavError(f"{who}: {what} is on {tuple(cell)} — a plain step there would attack it; stopped at "
                       f"{s.hero}. " + ("Wait a turn ('.') or go around." if m.get("peaceful") else
                                        "fight() it if it's hostile and safe to melee, wait, or go around."))


def walk_path(path, ok=None):
    """Walk a list of cells one step at a time, verifying each arrival.
    Never steps onto a monster (NavError instead; pets swap places)."""
    s = ctx.last()
    for cell in path:
        h = s.hero
        if h is None:
            return s
        key = DIR_KEY.get((cell[0] - h[0], cell[1] - h[1]))
        if key is None:
            raise NavError(f"walk_path: {cell} is not adjacent to {h}")
        _check_free(s, cell, "walk_path")
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


def travel(x, y, max_legs=40, max_dist=None, wait_peaceful=3, leg=None, auto_fight=True, with_pet=False):
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
    leg=0 disables that.
    with_pet=True (or a number of turns, default 12): bring your pet along —
    3-square legs, and after each leg wait ('.') while the pet is more than 2
    squares behind (not with a hostile within 3); raises NavError if the pet
    drops out of view. Without a pet in view it travels normally."""
    import contextlib
    ctx.require_command("travel()")
    if auto_fight and ctx.monster_filter:
        from .combat import not_auto_fightable
        guard = ctx.monster_filter(not_auto_fightable)
    else:
        guard = contextlib.nullcontext()
    pet_budget = None
    if with_pet:
        if _pets(ctx.last()):
            pet_budget = [12 if with_pet is True else int(with_pet)]
            leg = 3 if leg is None else leg
        else:
            print("travel(with_pet): no pet in view — travelling without waiting for one")
    with guard:
        return _travel(x, y, max_legs, max_dist, wait_peaceful, leg, auto_fight, pet_budget)


def _pets(s) -> list:
    return [m for m in (s.monsters or []) if (m.get("tame") or m.get("pet")) and not m.get("statue")]


def _keep_pet(s, budget: list):
    """with_pet travel, after a leg: wait while the pet is > 2 squares away
    (budget[0] = turns left for waiting). Returns the snap; raises NavError
    when the pet is out of view afterwards."""
    while budget[0] > 0 and s.state.kind == "command":
        pets = _pets(s)
        if any(m.get("dist") is not None and m["dist"] <= 2 for m in pets):
            return s
        if s.hostiles(3):
            return s                         # don't dawdle next to hostiles
        s = ctx.do(".", ok=BENIGN)
        budget[0] -= 1
    if s.state.kind == "command" and not _pets(s):
        raise PetLost(f"travel(with_pet): your pet is out of view (you are at {s.hero}) — go back for it, "
                      "or travel(x, y) without with_pet to leave it")
    return s


def engulfed_check(s, who: str):
    if getattr(s, "engulfed", False):
        raise NavError(f"{who}: you are ENGULFED — nothing to walk to; fight() hits the engulfer from inside "
                       "(or wait to be expelled)")


def _travel(x, y, max_legs, max_dist, wait_peaceful, leg, auto_fight, pet_budget=None):
    s = ctx.last()
    engulfed_check(s, f"travel{(x, y)}")
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
    waits = sidesteps = backoffs = fallbacks = 0
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
            # a peaceful stepped onto the target: wait for it (a plain step into it is refused)
            peace = [m for m in (s.monsters or []) if (m["x"], m["y"]) == (x, y) and m.get("peaceful")
                     and not m.get("tame") and not m.get("pet")]
            if peace:
                if waits < wait_peaceful:
                    waits += 1
                    print(f"travel: waiting a turn for {_mdesc(peace)} to leave the target square")
                    s = ctx.do(".", ok=BENIGN)
                    continue
                raise NavError(f"travel to {(x, y)}: {_mdesc(peace)} stays on the target square")
            # last square by a plain step: NetHack's travel never picks anything up
            # (it sets 'nopick'), a plain move autopicks gold and thrown weapons
            s = _final_step(s, (x, y))
            if s.hero == (x, y) or s.state.kind != "command":
                return s
            if s.hero == h0:
                if _pet_in_way(s.messages) and waits < wait_peaceful + 2:
                    waits += 1
                    s = ctx.do(".", ok=BENIGN)
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
        if h0 is not None and dist((tx, ty), h0) == 1:
            # findtravelpath(): "if travel to adjacent, just go there" — a plain move with travel's
            # nopick flag: a monster there gets "You move right into it" (a wasted turn; an engulfer
            # engulfs you). Step there ourselves, checked
            s = _final_step(s, (tx, ty))
            if s.state.kind != "command" or s.hero == (x, y):
                return s
            if s.hero == h0:
                raise NavError(f"travel to {(x, y)}: the step to {(tx, ty)} failed"
                               + (f"; messages: {s.messages}" if s.messages else ""))
            continue
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
        if h1 != h0 and pet_budget is not None:
            s = _keep_pet(s, pet_budget)
            if s.state.kind != "command":
                return s
        if h1 == h0:
            blk = blockers(s)
            hostile = [m for m in blk if not m.get("peaceful")]
            if hostile:
                raise NavError(f"travel to {(x, y)} did not move: hostile {_mdesc(hostile)} adjacent — "
                               "travel never starts next to one. Fight it (fight()) or step away by hand.")
            if blk and sidesteps < 6:
                # lookaround(): NetHack's travel never starts next to a non-tame monster, even one
                # that isn't in the way — plain steps along our own route (never into it) do
                own = bfs_path(s, h0, (x, y), avoid=frozenset(bad_squares(s) - {(x, y)}), allow_monsters=False)
                if own:
                    sidesteps += 1
                    try:
                        s2 = walk_path(own[:2])
                    except NavError:
                        s2 = ctx.last()
                    if s2.hero != h0:
                        s = s2
                        continue
            if blk and waits < wait_peaceful:
                waits += 1
                print(f"travel: waiting a turn for {_mdesc(blk)} to move")
                s = ctx.do(".", ok=BENIGN)      # give the peaceful a turn to move off
                continue
            if blk and backoffs < 2:
                # it blocks the only way (a 1-wide corridor): step back so it can come out, then retry
                ref = _refuge(s, blk, (x, y))
                if ref is not None:
                    backoffs += 1
                    waits = 0
                    print(f"travel: {_mdesc(blk)} blocks the way — stepping back to {ref} to let it pass")
                    try:
                        s = walk_path([ref])
                    except NavError:
                        s = ctx.last()
                    for _w in range(3):
                        if s.state.kind != "command" or \
                                bfs_path(s, s.hero, (x, y), allow_monsters=False) is not None:
                            break
                        s = ctx.do(".", ok=BENIGN)
                    continue
            if blk:
                raise NavError(f"travel to {(x, y)} did not move: {_mdesc(blk)} stays next to you "
                               f"(the only known route passes {sorted((m['x'], m['y']) for m in blk)}); "
                               "wait, go around, or dig past it.")
            if any("door is closed" in m for m in s.messages):
                try:
                    s = _open_door_toward(s, (x, y))    # travel never opens doors (autoopen is for plain steps)
                except NavError as e:
                    # NetHack's travel plans through closed doors, ours doesn't: walk around a locked one
                    cur = ctx.last()
                    own = bfs_path(cur, cur.hero, (x, y), avoid=frozenset(bad_squares(cur) - {(x, y)}),
                                   allow_monsters=False) if "locked" in str(e) and cur.hero else None
                    if not own:
                        raise
                    print(f"{e} — walking around it by our own route ({len(own)} steps)")
                    s = walk_path(own)
                    if s.hero == (x, y) or s.state.kind != "command":
                        return s
                continue
            if _pet_in_way(s.messages):
                if waits < wait_peaceful + 2:
                    waits += 1
                    s = ctx.do(".", ok=BENIGN)      # your pet is in the way (1/7 of swaps fail; never in shops)
                    continue
                raise NavError(f"travel to {(x, y)} did not move: your pet stays in the way ({s.messages}); "
                               "step around it by hand")
            own = bfs_path(s, h0, (x, y), avoid=frozenset(bad_squares(s) - {(x, y)}), allow_monsters=False)
            if own and fallbacks < 3:
                # NetHack's travel planned through something it then can't pass ("A boulder blocks
                # your path." — TEST_TRAV lets boulders through): walk our own route a stretch
                fallbacks += 1
                print(f"travel: NetHack's travel didn't move ({s.messages or 'no message'}) — walking our own "
                      f"route ({len(own)} steps)")
                s = walk_path(own[:8])
                if s.hero == (x, y) or s.state.kind != "command":
                    return s
                if s.hero != h0:
                    continue
            over_traps = bfs_path(s, h0, (x, y), allow_monsters=True, allow_traps=True)
            traps_on = [c for c in (over_traps or []) if s.screen.at(*c) == "^"]
            if bfs_path(s, h0, (x, y), allow_monsters=True) is None and traps_on:
                raise NavError(f"travel to {(x, y)}: the only known route crosses the known trap(s) at {traps_on} "
                               "(travel never steps on a known trap) — farlook() them: step over one on purpose "
                               "with do(dir, force=True) if it's harmless for you (e.g. levitating over a trap "
                               "door), or find another way")
            raise NavError(f"travel to {(x, y)} did not move (no known path?"
                           + (" — the map you know doesn't connect to it: explore() to find the way, or "
                              f"head_to({x}, {y}) across the unexplored part)"
                              if bfs_path(s, h0, (x, y), allow_monsters=True) is None else ")")
                           + (f"; messages: {s.messages}" if s.messages else ""))
        if _notable(s.messages) and not s.paused:
            return s   # something happened en route; let the caller look (unless the exec
                       # already paused on it and the player chose to go on)
    return s


def _refuge(s, blk, target):
    """A free square next to you, away from the blocking monster(s), where
    you can stand aside so a peaceful in a corridor can come out: the
    farthest from them, then the most open. None if there is none."""
    from .mapview import is_walkable
    h = s.hero
    if h is None:
        return None
    bad = bad_squares(s)
    occupied = {(m["x"], m["y"]) for m in (s.monsters or [])}
    best = None
    for (dx, dy) in DIR_KEY:
        c = (h[0] + dx, h[1] + dy)
        if c in bad or c in occupied or not is_walkable(s, *c, allow_monsters=False):
            continue
        away = min(dist(c, (m["x"], m["y"])) for m in blk)
        if away <= 1:
            continue                                   # still next to it: travel wouldn't start either
        room = sum(1 for (ex, ey) in DIR_KEY if is_walkable(s, c[0] + ex, c[1] + ey, allow_monsters=False))
        key = (away, room)
        if best is None or key > best[0]:
            best = (key, c)
    return best[1] if best else None


_PET_IN_WAY = ("is in your way", "is in the way!", "doesn't seem to move!", "Pardon me, ")
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
    _check_free(s, target, "travel's last step")       # e.g. a cockatrice stepped onto the target
    s = ctx.do(DIR_KEY[(dx, dy)], ok=BENIGN + [_DIAG_DOOR])
    if s.hero == h0 and dx and dy and any("move diagonally" in m for m in s.messages):
        pets = {(m["x"], m["y"]) for m in (s.monsters or []) if m.get("tame") or m.get("pet")}
        for mid in ((h0[0] + dx, h0[1]), (h0[0], h0[1] + dy)):
            if (is_walkable(s, *mid, allow_monsters=False) or mid in pets) and not is_door(s, *mid):
                s = ctx.do(DIR_KEY[(mid[0] - h0[0], mid[1] - h0[1])], ok=BENIGN)
                if s.hero == mid and s.state.kind == "command":
                    _check_free(s, target, "travel's last step")
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
    known = getattr(ctx.game, "locked_doors", {}).setdefault(ctx.game.level_key(s.status), set()) \
        if hasattr(ctx.game, "locked_doors") else set()
    if door in known:
        raise NavError(f"travel: the door at {door} is locked (known) — unlock{door} with a key, "
                       f"kick_door{door} (never a shop door or in Minetown), or go another way")
    key = DIR_KEY[(door[0] - h[0], door[1] - h[1])]
    for _ in range(6):
        s = ctx.do(key, ok=BENIGN + [r"^The door opens\.", r"^The door resists", r"^This door is locked"])
        text = " ".join(s.messages)
        if "locked" in text:
            known.add(door)
            raise NavError(f"travel: the door at {door} is locked — unlock{door} with a key, kick_door{door} "
                           "(never a shop door or in Minetown), or go another way")
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
    (inside exec) like any do(). Never attacks: NavError if a monster (not
    your pet) is on the next square — do('F' + direction) to attack."""
    from .mapview import KEY_DIR
    s = ctx.last()
    for _ in range(n):
        if s.hero is not None and direction in KEY_DIR:
            dx, dy = KEY_DIR[direction]
            _check_free(s, (s.hero[0] + dx, s.hero[1] + dy), "step()")
        s = ctx.do(direction)
    return s


def _branch(key: str | None) -> str:
    """'The Gnomish Mines / Level 3' -> 'The Gnomish Mines' ('' if unknown)."""
    return key.split(" / ")[0] if key and " / " in key else ""


def _pick_stairs(ch: str, cells: list, to: str | None, s) -> tuple:
    """Choose among several known staircases using where each was seen to
    lead (game.stair_links, learned whenever you take or arrive on one).
    Returns (cell, note)."""
    here = ctx.game.level_key(s.status)
    links = getattr(ctx.game, "stair_links", {}).get(here, {})
    known = {c: links[c] for c in cells if c in links}
    if to:
        match = [c for c in cells if to.lower() in known.get(c, "").lower()]
        if match:
            return match[0], f"leads to {known[match[0]]}"
        unknown = [c for c in cells if c not in known]
        if len(unknown) == 1:
            return unknown[0], f"not yet used; by elimination the one toward {to!r}"
        raise NavError(f"no known {ch!r} here leading to {to!r}: "
                       + ", ".join(f"{c} -> {known.get(c, 'unknown')}" for c in cells)
                       + " — travel(x, y) to the right one and press it yourself")
    if len(cells) == 1:
        return cells[0], ""
    mine = _branch(here)
    same = [c for c in cells if mine and _branch(known.get(c)) == mine]
    if same:
        return same[0], f"stays in {mine} (leads to {known[same[0]]})"
    other = [c for c in cells if c in known]
    unknown = [c for c in cells if c not in known]
    if other and unknown:
        return unknown[0], (f"the other {ch} at {other[0]} leads to {known[other[0]]}; pass to='...' to take a "
                            "branch on purpose")
    print(f"stairs: {len(cells)} {ch!r} here ({', '.join(map(str, cells))}) and where they lead is unknown — "
          f"taking the nearest; one of them is a branch (^O overview shows which branches start here)")
    return cells[0], ""


def _use_stairs(ch: str, tries: int = 4, wait_pet: int = 0, to: str | None = None, with_pet=None):
    s = ctx.last()
    engulfed_check(s, "go_down()" if ch == ">" else "go_up()")
    if s.status.ok and "Lev" in s.status.conditions:
        raise NavError("you are LEVITATING: you can't reach the stairs (\"You are floating high above the "
                       "stairs\") — remove the ring/boots of levitation or wait for it to wear off")
    cells = known_cells(ch, s, rescan=True)
    if not cells:
        raise NavError(f"no {ch!r} known on this level")
    if s.hero is not None and len(cells) > 1:
        # unreachable ones last (a ladder inside the sealed Wizard's Tower, stairs behind water)
        reach = [c for c in cells if c == s.hero or bfs_path(s, s.hero, c, allow_monsters=True) is not None]
        if reach:
            cells = reach + [c for c in cells if c not in reach]
    target, note = _pick_stairs(ch, cells, to, s)
    if note:
        print(f"stairs: using the {ch} at {target}: {note}")
    had_pet = [m for m in _pets(s) if m.get("dist") is not None and m["dist"] <= 7]
    auto = with_pet is None
    if auto:
        with_pet = bool(wait_pet and had_pet)       # it's with you now: keep it in tow
    for _ in range(tries):
        if s.hero == target:
            break
        try:
            s = travel(*target, with_pet=with_pet)
        except PetLost as e:
            if not auto:
                raise
            print(f"stairs: {e} — going on without it")
            with_pet = False
            s = ctx.last()
            continue
        if s.state.kind != "command":
            return s                     # a prompt interrupted: let the caller look
        s = ctx.last()
        if _notable(s.messages) and s.hero != target and not s.paused:
            return s                     # something happened on the way (not already seen in a pause)
    if s.hero != target:
        raise NavError(f"did not reach the {ch} at {target} (you are at {s.hero}); nothing pressed")
    if wait_pet:
        s = _wait_for_pet(s, wait_pet)
        if s.state.kind != "command" or s.hero != target:
            return s
    if had_pet and not any(m.get("dist") == 1 for m in _pets(s)):
        print(f"stairs: your pet ({had_pet[0].get('desc') or had_pet[0]['ch']}) is not next to you — "
              f"taking the {ch} without it (it stays on this level)")
    ld0 = s.status.ldesc if s.status.ok else None
    s = ctx.do(ch)
    cur = ctx.last()
    if cur.state.kind == "command" and ld0 is not None and cur.status.ok and cur.status.ldesc == ld0:
        raise NavError(f"pressed {ch!r} at {target} but you are still on {ld0}"
                       + (f": {cur.messages}" if cur.messages else "") + " — look at why before going on")
    return s


def _wait_for_pet(s, turns: int):
    """A pet only follows you down/up the stairs when it is next to you. If
    one is in view nearby but not adjacent, wait up to `turns` turns for it
    (it may be eating: "is still eating"); say what happened."""
    def pets(snap):
        return [m for m in (snap.monsters or []) if (m.get("tame") or m.get("pet")) and not m.get("statue")]
    near = [m for m in pets(s) if m.get("dist") is not None and 1 < m["dist"] <= 7]
    if any(m.get("dist") == 1 for m in pets(s)):
        return s
    if not near:
        far = pets(s)
        if far:
            print(f"stairs: your pet ({far[0].get('desc') or far[0]['ch']} at ({far[0]['x']},{far[0]['y']})) is "
                  f"{far[0].get('dist')} squares away — not waiting (only for a pet within 7)")
        return s
    for i in range(turns):
        if s.hostiles(2):
            print("stairs: a hostile is close — not waiting for the pet")
            return s
        s = ctx.do(".", ok=BENIGN)
        if s.state.kind != "command":
            return s
        if any(m.get("dist") == 1 for m in pets(s)):
            print(f"stairs: waited {i + 1} turn(s); your pet is next to you and comes along")
            return s
    left = pets(s)
    print("stairs: your pet " + (f"({left[0].get('desc')} at ({left[0]['x']},{left[0]['y']})) " if left else "")
          + f"didn't come next to you in {turns} turns — it stays behind")
    return s


def go_down(wait_pet: int = 6, to: str | None = None, with_pet=None):
    """Travel to a '>' (re-travelling after routine stops), check you are on
    it, then descend. Raises NavError instead of pressing '>' anywhere else.
    With several '>' on the level it takes the one that stays in this branch
    (learned from stairs you took or arrived on), or the one toward `to`
    (a substring of the destination: 'Mines', 'Dungeons', 'Sokoban').
    wait_pet: if your pet is in view nearby but not next to you, wait up to
    this many turns for it (0: don't). with_pet: travel in pet-keeping legs
    (see travel()); default: yes when wait_pet and your pet is within 7
    squares at the start. Says so when it leaves the pet behind."""
    return _use_stairs(">", wait_pet=wait_pet, to=to, with_pet=with_pet)


def go_up(wait_pet: int = 6, to: str | None = None, with_pet=None):
    """Like go_down() for '<' (e.g. go_up(to='Sokoban') on the Oracle-below level)."""
    return _use_stairs("<", wait_pet=wait_pet, to=to, with_pet=with_pet)


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


def path_to(x, y, avoid_bad: bool = True, through_monsters: bool = False) -> list:
    """Our known-map path from you to (x, y) (list of cells, excluding your
    square; [] if you're there; None if no known path). Honours known traps
    and avoid() squares unless avoid_bad=False. Monsters block it unless
    through_monsters=True (then None really means "no known route", and
    occupants(s, cell) on the path shows who is in the way). Walk it with
    walk_path(path) (one checked step at a time; stops before a monster)."""
    s = ctx.last()
    if s.hero is None:
        return None
    bad = frozenset(c for c in bad_squares(s) if c != (x, y)) if avoid_bad else frozenset()
    return bfs_path(s, s.hero, (x, y), avoid=bad, allow_monsters=through_monsters)
