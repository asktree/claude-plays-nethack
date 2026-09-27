"""Navigation tactics: cursor positioning, travel, farlook, stepping."""

from __future__ import annotations

import re

from . import ctx
from .benign import BENIGN
from .mapview import DIR_KEY, KEY_DIR, bfs_path, dist, find, nearest


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
                m.update(desc=lab, note=note_for(lab, xl, getattr(ctx.game, "intrinsics", ())),
                         tame=lab.startswith("tame "), peaceful=lab.startswith("peaceful "), looked=True)
    return txt


def bad_squares(s=None) -> set:
    """Known trap squares (incl. ones hidden under objects; read from the
    game's own memory via #terrain on each level) + the player's avoid set
    for the current level + mimics (in view, or remembered hiding as an
    object: obs 'mimics remembered here') and sessile hostiles + the special
    rooms announced here (zoo, anthole, beehive...: special_room_zone(),
    while you are outside them). All but the ones in view persist across
    daemon restarts."""
    s = s or ctx.last()
    lv = ctx.game.level_key(s.status)
    from nh.monitor import _stationary
    mimics = {(m["x"], m["y"]) for m in (s.monsters or []) if m.get("mimic")
              or (not m.get("tame") and not m.get("peaceful") and _stationary(m.get("desc") or ""))}
    mimics |= set(known_mimics(s))
    sessile = getattr(getattr(ctx.game, "tracker", None), "sessile", None) or {}
    from .mapview import is_door
    for c, rec in (sessile.get(s.status.ldesc if s.status.ok else "") or {}).items():
        # a mold/jelly remembered out of view (p3 shift 10: travel beside one) — in rooms only: a stale
        # record (a pet killed it unseen) must never close a corridor or doorway
        if not (rec.get("statue") or c == s.hero) and s.screen.at(*c) != "#" and not is_door(s, *c):
            mimics.add(c)
    zone = set(special_room_zone(s))
    return set(ctx.game.traps.get(lv, set())) | set(ctx.game.avoid.get(lv, set())) | mimics | zone


# sp_lev.c create_room(): a random room is at most 14 squares wide and 6 high inside (special rooms are picked
# among those; the Castle's and Fort Ludios's are bigger but lit, so their walls are known)
_ROOM_W, _ROOM_H = 14, 6


def special_room_zone(s=None, outside_only: bool = True) -> dict:
    """{(x, y): kind} the squares of the special rooms announced on this
    level (treasure zoo, anthole, beehive, barracks, cockatrice nest, throne
    room, leprechaun hall, graveyard — NetHack says it only once per room):
    its known floor (up to its walls), the never-seen squares on its side of
    the entry wall within a room's size (a dark room), and its doorways.
    Empty while you stand in it (outside_only), so you can walk out."""
    s = s or ctx.last()
    mem = getattr(s, "room_mem", None)
    if mem is None:
        store = getattr(ctx.game, "special_rooms", None) or {}
        mem = store.get(ctx.game.level_key(s.status), {}) if s.status.ok else {}
    out: dict = {}
    for entry, info in (mem or {}).items():
        cells = _room_cells(s, tuple(entry), info.get("prev"))
        if outside_only and s.hero in cells:
            continue
        for c in cells:
            out.setdefault(c, info.get("kind") or "special room")
    return out


def _room_cells(s, entry, prev) -> set:
    from .mapview import DIRS4, in_map, is_door, is_wall
    ex, ey = entry

    def ch(c):
        return s.screen.at(*c)

    def blocked(c):
        return not in_map(*c) or not 1 <= c[1] <= 21 or is_wall(s, *c) \
            or (ch(c) == "#" and s.screen.color_at(*c) in (7, 8, 15))

    def blank(c):
        return ch(c) == " " and s.screen.color_at(*c) != 6

    def doorish(c):
        return is_door(s, *c) or (ch(c) == "." and (
            (is_wall(s, c[0] - 1, c[1]) and is_wall(s, c[0] + 1, c[1]))
            or (is_wall(s, c[0], c[1] - 1) and is_wall(s, c[0], c[1] + 1))))
    # the side of the entry the room lies on: away from where you came from (a doorway in a wall line)
    axis = sign = None
    if prev is not None:
        dx, dy = ex - prev[0], ey - prev[1]
        vert_wall = is_wall(s, ex, ey - 1) or is_wall(s, ex, ey + 1)
        horiz_wall = is_wall(s, ex - 1, ey) or is_wall(s, ex + 1, ey)
        if dx and (vert_wall or not horiz_wall):
            axis, sign = 0, (1 if dx > 0 else -1)
        elif dy:
            axis, sign = 1, (1 if dy > 0 else -1)
    at_door = axis is not None and doorish(entry)

    def side_ok(c):
        if not at_door:
            return True
        d = (c[axis] - entry[axis]) * sign
        return d > 0 or (d == 0 and doorish(c))        # (on the entry's wall line: only its doorways)
    # a door in a vertical wall: the room reaches 14 squares across and 5 rows up/down from it; in a
    # horizontal wall 13 across and 6 deep
    rw, rh = (_ROOM_W, _ROOM_H - 1) if axis == 0 else (_ROOM_W - 1, _ROOM_H) if axis == 1 else (_ROOM_W, _ROOM_H)

    def in_box(c):
        return abs(c[0] - ex) <= rw and abs(c[1] - ey) <= rh
    cells = {entry}
    if at_door:
        seeds = [(ex + (sign if axis == 0 else 0), ey + (sign if axis == 1 else 0))]
    else:
        seeds = [c for c in ((ex + dx, ey + dy) for dx, dy in DIRS4) if c != prev]
    # 1) the room's known squares, up to its walls and doorways (no size limit: a lit room shows its walls)
    q = [c for c in seeds if not blocked(c) and not blank(c) and side_ok(c)]
    seen = set(q) | {entry}
    fringe = [c for c in seeds if blank(c) and side_ok(c) and in_box(c)]
    while q and len(cells) < 600:
        c = q.pop()
        cells.add(c)
        if doorish(c) and c != entry:
            continue                 # another doorway of the room: part of it, not a way through
        for dx, dy in DIRS4:
            n = (c[0] + dx, c[1] + dy)
            if n in seen or n == prev or blocked(n) or not side_ok(n):
                continue
            seen.add(n)
            if blank(n):
                if in_box(n):
                    fringe.append(n)
                continue
            q.append(n)
    # 2) never-seen squares next to it on its side, within a room's size (a dark room's unseen floor)
    q = [c for c in fringe]
    seen |= set(q)
    while q:
        c = q.pop()
        cells.add(c)
        for dx, dy in DIRS4:
            n = (c[0] + dx, c[1] + dy)
            if n in seen or n == prev or blocked(n) or not side_ok(n) or not in_box(n):
                continue
            seen.add(n)
            if blank(n):
                q.append(n)
            elif doorish(n):
                cells.add(n)         # a doorway found at the edge of the unseen part
    return cells


def special_rooms(s=None) -> list:
    """The special rooms announced on this level: [{'kind', 'entry', 'turn', 'squares'}]."""
    s = s or ctx.last()
    mem = getattr(s, "room_mem", None) or (getattr(ctx.game, "special_rooms", {}) or {}).get(
        ctx.game.level_key(s.status), {})
    return [{"kind": r.get("kind"), "entry": c, "turn": r.get("turn"),
             "squares": len(_room_cells(s, tuple(c), r.get("prev")))} for c, r in mem.items()]


def forget_room(x: int | None = None, y: int | None = None) -> list:
    """Stop avoiding a special room (its monsters are dead, or you go in on purpose): the one entered at
    (x, y), else the one nearest to you. Returns special_rooms()."""
    s = ctx.last()
    store = getattr(ctx.game, "special_rooms", None)
    key = ctx.game.level_key(s.status)
    rooms = (store or {}).get(key) or {}
    if not rooms:
        return []
    if x is None or y is None:
        h = s.hero or (0, 0)
        c = min(rooms, key=lambda c: max(abs(c[0] - h[0]), abs(c[1] - h[1])))
    else:
        c = min(rooms, key=lambda c: max(abs(c[0] - x), abs(c[1] - y)))
    info = rooms.pop(c)
    print(f"forget_room: no longer avoiding the {info.get('kind')} entered at {c}")
    if getattr(s, "room_mem", None) is not None:
        s.room_mem.pop(c, None)
    return special_rooms()


def known_mimics(s=None) -> dict:
    """{(x, y): 'giant mimic'} mimics remembered on this level (seen unmasked; one hides again as an
    object, a boulder or stairs where it sits and never moves while hiding). Forgotten when seen killed,
    or when a look from next to the square shows it gone. forget_mimic(x, y) drops one by hand."""
    s = s or ctx.last()
    mem = getattr(s, "mimic_mem", None)
    if mem is None:          # (a daemon without the memory)
        store = getattr(ctx.game, "mimics", None) or {}
        mem = store.get(ctx.game.level_key(s.status), {}) if s.status.ok else {}
    return dict(mem)


def remember_mimic(x: int, y: int, name: str = "giant mimic") -> dict:
    """Record a mimic you know hides at (x, y) on this level (from your notes: a daemon restart before
    this memory existed lost it). Returns known_mimics()."""
    s = ctx.last()
    store = getattr(ctx.game, "mimics", None)
    if not isinstance(store, dict) or not s.status.ok:
        raise NavError("remember_mimic(): this daemon has no mimic memory (restart it)")
    store.setdefault(ctx.game.level_key(s.status), {})[(x, y)] = name
    if isinstance(getattr(s, "mimic_mem", None), dict):
        s.mimic_mem[(x, y)] = name
    return known_mimics(s)


def forget_mimic(x: int, y: int) -> bool:
    """Drop a remembered mimic at (x, y) on this level (you know it's gone). Returns whether one was there."""
    s = ctx.last()
    store = getattr(ctx.game, "mimics", None)
    if not isinstance(store, dict) or not s.status.ok:
        return False
    key = ctx.game.level_key(s.status)
    hit = store.get(key, {}).pop((x, y), None) is not None
    if key in store and not store[key]:
        del store[key]
    if hit and isinstance(getattr(s, "mimic_mem", None), dict):
        s.mimic_mem.pop((x, y), None)
    return hit


def squeaky_boards(s=None) -> set:
    """Known squeaky boards on this level (feature_desc): harmless to cross — they only squeak and wake
    monsters nearby — but travel and the step guard avoid every known trap."""
    s = s or ctx.last()
    fd = getattr(s, "feature_desc", None) or {}
    return {c for c, d in fd.items() if "squeaky board" in (d or "")}


def _walk_over(path, boards: set):
    """walk_path() that steps onto the given squeaky boards on purpose (force=True past the trap guard)."""
    s = ctx.last()
    for cell in path:
        h = s.hero
        if h is None:
            return s
        key = DIR_KEY.get((cell[0] - h[0], cell[1] - h[1]))
        if key is None:
            raise NavError(f"walk: {cell} is not adjacent to {h}")
        _check_free(s, cell, "travel")
        s = ctx.do(key, ok=BENIGN + [r"^A board beneath you squeaks", r"^You hear a (?:distant )?squeak"],
                   force=cell in boards, expect=("trap",) if cell in boards else ())
        if s.hero != cell:
            return s
    return s


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


def _peacefuls_at(s, cell) -> list:
    """Peaceful (not tame) monsters standing on `cell`."""
    return [m for m in (s.monsters or []) if (m["x"], m["y"]) == tuple(cell) and m.get("peaceful")
            and not m.get("tame") and not m.get("pet")]


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
        for _w in range(3):
            occ = occupants(s, cell)
            if not occ or not all(m.get("peaceful") for m in occ):
                break
            s = ctx.do(".", ok=BENIGN)             # a wandering peaceful on the next square: give it a turn
            if s.state.kind != "command":
                return s
        _check_free(s, cell, "walk_path")
        s = ctx.do(key, ok=ok if ok is not None else BENIGN)
        if s.hero != cell:
            if s.state.kind == "command" and s.hero == h and any(
                    m.startswith(("You are carrying too much to get through", "You try to squeeze")) for m in
                    s.messages or []):
                # hack.c test_move(): no diagonal squeeze between rock/boulders over 600 weight
                raise NavError(f"walk_path: can't squeeze diagonally from {h} to {cell} ({s.messages[-1]!r}) — "
                               "drop heavy things (the pack is over 600) or take another way")
            return s
    return s


def _lev_drowner_zone(s) -> dict:
    """{(x, y): 'kraken at (x, y)'} squares (water or not) a drowner seen now or lately can reach: while
    levitating over water an eel/kraken next to you can still wrap and drown you (mhitu.c AD_WRAP checks only
    ITS square). Only the water connected to its own (a kraken walled into an inner pool can't come out:
    p2 shift 28), within a few squares of where it was, plus the squares next to that water."""
    from nh.danger import base_name
    turn = s.status.turn if s.status.ok else None
    seen = [(m["x"], m["y"], 0, base_name(m.get("desc") or "")) for m in s.monsters or []
            if not (m.get("tame") or m.get("peaceful")) and base_name(m.get("desc") or "") in DROWNERS]
    tr = getattr(ctx.game, "tracker", None)
    if tr is not None and hasattr(tr, "gone") and turn is not None:
        for r in tr.gone(turn):
            d = r.get("desc") or ""
            ago = turn - r.get("turn", turn)
            if base_name(d) in DROWNERS and 0 <= ago <= EEL_MEMORY and not d.startswith(("tame ", "peaceful ")):
                seen.append((r["x"], r["y"], ago, base_name(d)))
    out: dict = {}
    for ex, ey, ago, name in seen:
        reach = 2 + (0 if ago == 0 else min(6, 1 + ago // 2))
        # its water body (8-connected '}' from its square), within `reach`
        body, q = {(ex, ey)}, [(ex, ey)]
        while q:
            cx, cy = q.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    n = (cx + dx, cy + dy)
                    if n not in body and s.screen.at(*n) == "}" and max(abs(n[0] - ex), abs(n[1] - ey)) <= reach:
                        body.add(n)
                        q.append(n)
        why = f"{name} at ({ex},{ey})" + (f", {ago} turns ago" if ago else "")
        for (wx, wy) in body:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    out.setdefault((wx + dx, wy + dy), why)
    return out


def _lev_path(s, start, goal, unknown_cost: int = 3, avoid=frozenset()):
    """Cheapest 8-connected route for a LEVITATING/flying hero: floor, water and lava ('}') cost 1, never-seen
    squares `unknown_cost` (they may be rock: a failed step says "It's solid stone." and is remembered),
    walls/closed doors/boulders/trees/bars/traps/monsters/avoided squares blocked; no diagonal steps into or
    out of doorways or between two known solid squares. Returns the cells after start, or None."""
    import heapq
    from .mapview import DIRS8, cell, in_map, is_door, is_walkable
    bad = (bad_squares(s) | set(avoid)) - {goal}
    solid = set(getattr(s, "solid_mem", ()) or ())
    mons = {(m["x"], m["y"]) for m in s.monsters or [] if not (m.get("tame") or m.get("pet") or m.get("statue"))}

    def cost(c):
        if c in solid or c in bad or (c in mons and c != goal) or not in_map(*c) or not 1 <= c[1] <= 21:
            return None
        ch = cell(s, *c)
        if ch == "}":
            return 1
        if ch == " ":
            return 1 if s.screen.color_at(*c) == 6 else unknown_cost     # (cyan blank: open air)
        if ch in "0`" or ch == "^":
            return None
        return 1 if is_walkable(s, *c, allow_monsters=True) or c == goal else None

    def known_solid(c):
        ch = cell(s, *c)
        return c in solid or (ch in "|-" and s.screen.color_at(*c) not in (3, 15)) or (ch == "#" and
                                                                                     s.screen.color_at(*c) == 2)
    best = {start: 0}
    prev = {start: None}
    q = [(0, start)]
    while q:
        d, cur = heapq.heappop(q)
        if cur == goal:
            path = [cur]
            while prev[path[-1]] != start:
                path.append(prev[path[-1]])
            return list(reversed(path))
        if d > best.get(cur, 1 << 30):
            continue
        for dx, dy in DIRS8:
            nxt = (cur[0] + dx, cur[1] + dy)
            w = cost(nxt)
            if w is None:
                continue
            if dx and dy and (is_door(s, *cur) or is_door(s, *nxt)
                              or (known_solid((cur[0] + dx, cur[1])) and known_solid((cur[0], cur[1] + dy)))):
                continue
            nd = d + w
            if nd < best.get(nxt, 1 << 30):
                best[nxt] = nd
                prev[nxt] = cur
                heapq.heappush(q, (nd, nxt))
    return None


def levitate_to(x: int, y: int, max_steps: int = 300, near_water: bool = False, unknown_cost: int = 3):
    """While LEVITATING (or flying): go to (x, y) straight over water/lava and
    never-seen squares — NetHack's travel plans only over squares you have
    seen (p2 shift 26: travel on Medusa's level led back to a locked door).
    Walks 4 checked steps at a time and re-plans (a step into unseen rock is
    remembered as solid). Keeps 1+ squares away from eels/krakens seen now or
    lately — their wrap drowns you even while levitating (near_water=True
    ignores them). Stops (NavError) when levitation ends: over water/lava
    that is a fall into it, so mind the ring/boots/potion timeout. Returns
    the final Snap."""
    s = ctx.require_command("levitate_to()")
    goal = (x, y)
    fails = 0
    for _ in range(max_steps):
        s = ctx.last()
        if s.state.kind != "command" or s.hero is None or s.hero == goal:
            return s
        conds = set(s.status.conditions) if s.status.ok else set()
        if not conds & {"Lev", "Fly"}:
            raise NavError(f"levitate_to{goal}: you are not levitating or flying now (at {s.hero}) — put the "
                           "ring/boots on or quaff first; on water that means you just fell in")
        zmap = {} if near_water else {c: w for c, w in _lev_drowner_zone(s).items() if c not in (s.hero, goal)}
        zone = set(zmap)
        path = _lev_path(s, s.hero, goal, unknown_cost, avoid=zone)
        if path is None and zone:
            wet = _lev_path(s, s.hero, goal, unknown_cost)
            if wet is not None:
                hit = [c for c in wet if c in zone]
                raise NavError(f"levitate_to{goal}: the only way passes {hit[0]}, within reach of the "
                               f"{zmap[hit[0]]} (its wrap drowns you even while levitating). Kill it, wait "
                               "for it to move off, or levitate_to(..., near_water=True)")
        if path is None:
            raise NavError(f"levitate_to{goal}: no way from {s.hero} over the known map (walls, closed doors, "
                           "boulders, traps and monsters block; unseen squares count as open)")
        h0 = s.hero
        try:
            s = walk_path(path[:4])
        except NavError as e:
            fails += 1
            if fails >= 4:
                raise NavError(f"levitate_to{goal}: stuck at {h0}: {e}") from None
            continue
        if s.hero == h0:
            if any(m in ("It's solid stone.", "It's a wall.") for m in s.messages or []):
                continue            # an unseen square was rock: remembered (solid_mem), the next plan avoids it
            fails += 1
            if fails >= 4:
                raise NavError(f"levitate_to{goal}: no progress from {h0} ({s.messages or 'no message'})")
        else:
            fails = 0
    return ctx.last()


# hack.c moverock(): what a push can say
_PUSH_OK = [r"^With (?:great )?effort you move the boulder", r"^You try to move the boulder, but in vain",
            r"^You hear a monster behind the boulder", r"^Perhaps that's why you cannot move",
            r"boulder (?:falls into|fills|plugs|sinks)", r"^There is a large splash", r"^Kerplunk",
            r"^The boulder triggers", r"^You push the boulder", r"^However, you can squeeze yourself",
            r"^You don't have enough leverage", r"^You're too small to push"]


def push_boulder(direction: str, n: int = 1):
    """Push the boulder next to you `n` times toward `direction` (hjklyubn;
    outside Sokoban diagonals work too — in Sokoban use sokoban.push()).
    Before each push it checks the boulder's square and the one beyond: a
    monster standing there (a giant can stand on a boulder square) would be
    ATTACKED by a plain step (p2 shift 27: a stone giant) — it stops and
    says so instead. Stops when the boulder doesn't move (something behind
    it, "in vain", it fell into water/a hole/a trap). Returns the final Snap."""
    if direction not in KEY_DIR:
        raise ValueError(f"push_boulder: direction must be one of hjklyubn, not {direction!r}")
    dx, dy = KEY_DIR[direction]
    s = ctx.require_command("push_boulder()")
    for i in range(n):
        s = ctx.last()
        if s.state.kind != "command" or s.hero is None:
            return s
        hx, hy = s.hero
        b, beyond = (hx + dx, hy + dy), (hx + 2 * dx, hy + 2 * dy)
        occ = [m for m in s.monsters or [] if (m["x"], m["y"]) in (b, beyond) and not m.get("statue")]
        if occ:
            ctx.pause(f"push_boulder: {_mdesc(occ)} — a step {direction!r} would "
                      + ("attack it" if any((m["x"], m["y"]) == b for m in occ) else "shove the boulder into it")
                      + " (peaceful or not); deal with it first")
            return ctx.last()
        if s.screen.at(*b) not in "0`":
            print(f"push_boulder: no boulder at {b} (it shows {s.screen.at(*b)!r}) — {i} push(es) done")
            return s
        s = ctx.do(direction, ok=_PUSH_OK)
        text = " ".join(s.messages)
        if s.hero != b:
            print(f"push_boulder: the boulder at {b} didn't move ({text or 'no message'}) — {i} push(es) done")
            return s
        if s.screen.at(*beyond) not in "0`":
            print(f"push_boulder: the boulder is gone from view after push {i + 1} ({text or 'no message'})")
            return s
    return ctx.last()


def clear_I(x: int, y: int) -> bool:
    """Clear a remembered-unseen-monster marker 'I' at (x, y) the safe way:
    walk next to it and search once — detect.c dosearch0() erases an 'I'
    with nothing under it (unmap_invisible) and only FEELS a real invisible
    monster there, never attacking it (a step or F there would attack even a
    peaceful). One game turn. Returns True when the marker is gone."""
    s = ctx.require_command("clear_I()")
    if s.screen.at(x, y) != "I":
        return True
    if "Blind" in (s.status.conditions if s.status.ok else ()):
        raise NavError(f"clear_I{(x, y)}: you are Blind — searching doesn't clear markers then")
    h = s.hero
    if h is None:
        return False
    if max(abs(h[0] - x), abs(h[1] - y)) > 1:
        from .mapview import is_walkable
        spots = sorted(((x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy),
                       key=lambda c: max(abs(c[0] - h[0]), abs(c[1] - h[1])))
        spots = [c for c in spots if is_walkable(s, *c, allow_monsters=False) and s.screen.at(*c) != "I"
                 and bfs_path(s, h, c, avoid=frozenset(bad_squares(s) - {c}), allow_pets=True) is not None]
        if not spots:
            raise NavError(f"clear_I{(x, y)}: no reachable square next to it")
        s = travel(*spots[0])
        if s.hero is None or max(abs(s.hero[0] - x), abs(s.hero[1] - y)) > 1:
            return False
    s = ctx.do("s", ok=BENIGN + [r"^You feel an unseen monster", r"^You find "])
    gone = s.screen.at(x, y) != "I"
    print(f"clear_I{(x, y)}: " + ("the marker was stale — gone" if gone else
                                  "still 'I' after a search: something invisible IS there (maybe peaceful) — "
                                  "look before attacking"))
    return gone


# trap.c: what stepping on a known trap costs you, by type — trek()/explore(cross_traps=True) cross only these
def trap_crossable(name: str, st=None) -> bool:
    """May trek() step on a known trap of this type? Harmless or minor for you now: a squeaky board, an
    arrow trap, an anti-magic field, a pit; a falling rock / rolling boulder trap with HP to spare; a dart
    trap or spiked pit only with poison resistance (a poisoned hit can kill outright); teleport/level
    teleporter/polymorph traps only with magic resistance (worn/wielded, per inventory()); a sleeping gas
    trap only with sleep resistance. Never: magic trap, fire trap, land mine, bear trap, web, rust trap,
    hole, trap door, magic portal, statue trap."""
    n = (name or "").lower().strip()
    res = getattr(ctx.game, "intrinsics", None) or set()
    mr = bool(getattr(ctx.game, "magic_res", False))
    st = st or ctx.last().status
    hp = st.hp if st is not None and st.ok else 0
    if n in ("squeaky board", "arrow trap", "anti-magic field", "pit"):
        return True
    if n == "falling rock trap":
        return hp >= 20
    if n == "rolling boulder trap":
        return hp >= 40
    if n in ("dart trap", "spiked pit"):
        return "poison" in res
    if n in ("teleportation trap", "level teleporter", "polymorph trap"):
        return mr
    if n == "sleeping gas trap":
        return "sleep" in res
    return False


def _trap_names(s) -> dict:
    """{(x, y): 'dart trap'} known trap types on this level (farlook / #terrain descriptions)."""
    fd = getattr(ctx.game, "feature_desc", {}) or {}
    key = ctx.game.level_key(s.status) if s.status.ok else None
    return {c: d for c, d in (fd.get(key) or {}).items() if re.search(r"\btrap\b|\bboard\b|\bpit\b|field", d or "")}


def trek(x: int, y: int, cross_traps=True, max_legs: int = 30):
    """travel() to (x, y) that may CROSS known traps when no way around
    them is known: travel to the square before each one, then step onto it
    (step_onto). cross_traps=True: the types trap_crossable() allows for you
    now; or a list of trap names ('dart trap', 'rust trap'...) to allow. A
    route around the traps is always preferred. Returns the final Snap;
    NavError when even crossing the allowed traps finds no way."""
    goal = (x, y)
    s = ctx.require_command("trek()")

    def ok(c, names, st):
        d = names.get(c)
        return d is not None and (trap_crossable(d, st) if cross_traps is True else d in tuple(cross_traps or ()))

    def finish(s):
        # (a crossable trap as the goal itself — a frontier behind nothing but it: step onto it at the end)
        names = _trap_names(s)
        if s.hero is not None and s.hero != goal and max(abs(s.hero[0] - x), abs(s.hero[1] - y)) == 1 \
                and ok(goal, names, s.status):
            print(f"trek: stepping onto the {names[goal]} at {goal}")
            s = step_onto(x, y)
        return s
    for _ in range(max_legs):
        s = ctx.last()
        if s.state.kind != "command" or s.hero is None or s.hero == goal:
            return s
        bad = bad_squares(s) - {goal}
        names = _trap_names(s)
        allow = {c for c in bad if ok(c, names, s.status)}
        around = bfs_path(s, s.hero, goal, avoid=frozenset(bad), allow_pets=True)
        if around is not None:
            return finish(travel(x, y))
        path = bfs_path(s, s.hero, goal, avoid=frozenset(bad - allow), allow_traps=True, allow_pets=True)
        if path is None:
            blocking = sorted(c for c in bad if c in names)
            raise NavError(f"trek{goal}: no way even across the traps you may cross; known traps: "
                           + ", ".join(f"{c} {names[c]}" for c in blocking[:6])
                           + " (trap_crossable() says which are allowed; cross_traps=['...'] adds more)")
        idx = next((i for i, c in enumerate(path) if c in allow), None)
        if idx is None:
            return finish(travel(x, y))
        if idx == 0:
            print(f"trek: stepping onto the {names[path[0]]} at {path[0]}")
            s = step_onto(*path[0])
            continue
        s = travel(*path[idx - 1])
        if s.hero != path[idx - 1]:
            return s                  # stopped short (a monster, a message): the caller looks
    return ctx.last()


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


def travel(x, y, max_legs=40, max_dist=None, wait_peaceful=3, leg=None, auto_fight=True, with_pet=False,
           fight_through=False, near_exploders=False, water_plane=False, medusa_ok=False, quest_ok=False,
           near_water=False, pass_hostile=False):
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
    drops out of view. Without a pet in view it travels normally.
    fight_through=True: when a hostile next to you stops the trip, fight() it
    (all its checks apply) and go on, instead of raising NavError.
    pass_hostile=True: when a hostile next to you stops the trip, walk past it
    with plain steps along your own route (never into it, never attacking) —
    for a sleeping monster you'd rather not wake (Stealth keeps it asleep).
    It refuses (NavError) to take a leg that passes within 2 squares of a known
    exploder (yellow/black light, sphere, gas spore): kill it at range first;
    near_exploders=True overrides.
    On the Plane of Water it refuses (the air bubbles drift and travel walks
    you into the water: soaked scrolls/potions, rust, drowning without
    magical breathing): step() inside your bubble; water_plane=True overrides.
    On a probable Medusa level it refuses while you are neither blind nor
    wearing known reflection (medusa_ok=True overrides; back to the up stairs
    is always allowed); it refuses to end next to the quest leader unless you
    are ready (XL14+, piously aligned: piety(); quest_ok=True overrides). A
    trap square as target: it stops next to it (step onto it yourself). It
    stops (NavError) if the level changes under it.
    Water with a drowning monster (eel_zone(): a giant/electric eel or kraken
    seen there lately): a route passing next to that water walks a detour
    around it; with no detour it refuses while the eel is in view next to the
    way, else warns and goes on (near_water=True skips all that)."""
    import contextlib
    ctx.require_command("travel()")
    s0 = ctx.last()
    if s0.status.ok and s0.status.ldesc == "Water" and not water_plane:
        raise NavError("travel() on the Plane of Water: the air bubbles drift every turn and travel walks you into "
                       "the water (\"You plunge into the water\": scrolls blank, potions dilute, iron rusts; "
                       "without magical breathing you may DROWN). Move with step(dir) inside your bubble toward "
                       "the portal, waiting ('.') for bubbles to line up; travel(..., water_plane=True) only with "
                       "magical breathing and your scrolls/potions in a bag")
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
    _medusa_check(s0, (x, y), "travel()", medusa_ok)
    _leader_check(s0, (x, y), "travel()", quest_ok)
    tr = _trap_target(s0, (x, y))
    if tr is not None:
        print(f"travel: {(x, y)} is a known trap square — going next to it, {tr}; step onto it yourself with "
              f"step('{DIR_KEY[(x - tr[0], y - tr[1])]}', force=True) if you mean to (portal, trap door)")
        x, y = tr
    with guard:
        return _travel(x, y, max_legs, max_dist, wait_peaceful, leg, auto_fight, pet_budget,
                       fight_through, near_exploders, near_water, pass_hostile)


def _medusa_check(s, target, who: str, ok: bool) -> None:
    """Refuse to move around a probable Medusa level unprotected (not blind, no known reflection)."""
    if ok or not getattr(s, "medusa_risk", False):
        return
    mem = (getattr(s, "feature_mem", None) or {})
    if mem.get(tuple(target)) == "<" or (s.hero is not None and dist(s.hero, target) <= 1):
        return                         # back to the up stairs, or one square next to you
    raise NavError(f"{who}: this is probably MEDUSA'S LEVEL and you are neither blind nor wearing known "
                   "reflection — her gaze stones you the moment you see each other (within ~8 squares). Apply a "
                   "blindfold/towel first (telepathy shows monsters), or wear a shield of reflection / silver "
                   "dragon scale mail (inventory() records it), or pass medusa_ok=True if you know you are "
                   "protected (an unidentified amulet of reflection) or Medusa is dead")


def _quest_leader(s):
    from nh.danger import base_name, quest_role
    for m in s.monsters or []:
        if m.get("peaceful") and quest_role(base_name(m.get("desc") or "")) == "leader":
            return m
    return None


def _leader_check(s, target, who: str, ok: bool, route=None) -> None:
    """Walking next to the quest leader IS the visit: only when ready (XL14+ and piously aligned —
    each visit with a lower alignment record counts, 7 and you're expelled for good)."""
    if ok:
        return
    ld = _quest_leader(s)
    if ld is None or s.hero is None:
        return
    lp = (ld["x"], ld["y"])
    cells = [tuple(target)] + list(route or bfs_path(s, s.hero, tuple(target), allow_monsters=True) or [])
    if not any(dist(c, lp) <= 1 for c in cells):
        return
    xl = s.status.xl if s.status.ok else 0
    piety = getattr(ctx.game, "piety", None)
    if xl >= 14 and piety == "piously":
        return
    why = (f"you are XL{xl}: below XL14 it just sends you away (no harm, a wasted trip)" if xl < 14 else
           f"your alignment is {'unknown' if piety is None else repr(piety)}: below 'piously' (record 20) the "
           "visit counts as one of 7 tries — after 7 you're EXPELLED FOR GOOD (no Bell of Opening, no "
           "ascension). Check with piety() (a stethoscope applied to yourself)")
    raise NavError(f"{who}: the way passes next to the quest leader {ld.get('desc')} at {lp} — being next to it "
                   f"is the visit. {why}; quest_ok=True to go anyway")


def _trap_target(s, target):
    """A known trap square as target (travel's last step would be refused): the best free square next
    to it, or None."""
    target = tuple(target)
    traps = set(ctx.game.traps.get(ctx.game.level_key(s.status), set())) if hasattr(ctx.game, "traps") else set()
    if s.hero is None or s.hero == target or not (target in traps or s.screen.at(*target) == "^"):
        return None
    from .mapview import is_walkable, neighbors
    best = None
    for c in neighbors(*target):
        if c == s.hero:
            return c
        if c in traps or not is_walkable(s, *c, allow_monsters=False):
            continue
        p = bfs_path(s, s.hero, c, allow_monsters=True)
        if p is not None and (best is None or len(p) < best[0]):
            best = (len(p), c)
    return best[1] if best else None


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


_HEADING = [False]   # travel() falling back to head_to(): never again from inside it
DROWNERS = ("giant eel", "electric eel", "kraken")
EEL_MEMORY = 80      # turns an out-of-view eel keeps its stretch of water dangerous


def _water(s) -> set:
    """Water squares of this level: shown now ('}' not red: lava is red), or remembered under an 'I'/a
    monster drawn on them."""
    key = ctx.game.level_key(s.status)
    out = set(getattr(ctx.game, "water_seen", {}).get(key, set()))
    for y in range(1, 22):
        row = s.screen.row(y)
        x = row.find("}")
        while x >= 0:
            if s.screen.color_at(x, y) != 1:
                out.add((x, y))
            x = row.find("}", x + 1)
    return out


def _in_water(s, m, water=None) -> bool:
    water = _water(s) if water is None else water
    c = (m["x"], m["y"])
    return c in water or sum(1 for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                             if (dx or dy) and (c[0] + dx, c[1] + dy) in water) >= 5


def eel_level(s=None) -> str:
    """Why this level's water should be taken to hide drowning sea monsters, or ''. Their moats are
    stocked with giant eels / krakens / sharks created HIDDEN under the water: the Castle, Medusa's
    island, and everything in Gehennom (the Wizard's Tower and fake-tower moats, Juiblex's swamp); on
    any level once a wrap attempt ("brushes against your leg") or a sea monster was met."""
    s = s or ctx.last()
    key = ctx.game.level_key(s.status)
    flags = set(getattr(ctx.game, "level_flags", {}).get(key, ()))
    if "eels" in flags:
        return "sea monsters met on this level"
    if flags & {"castle", "medusa", "medusa?"}:
        return "this level's moat" if "castle" in flags else "Medusa's water"
    if key.startswith("Gehennom"):
        return "Gehennom's moats"
    m = re.search(r"^The Dungeons of Doom / Level (\d+)$", key)
    if m and int(m.group(1)) > 15:
        # mklev.c: below depth 15 a special room can be a SWAMP (mkroom.c mkswamp(): a checkerboard of pools
        # with giant eels, piranhas and electric eels in them, hidden)
        return "a deep level (swamp rooms hide eels)"
    return ""


def drowners_adjacent(s=None) -> list:
    """Hostile sea monsters next to you that can wrap and drown you: a giant/electric eel or kraken, or an
    unseen 'I' in the water (a hidden one that just attacked). Only while you stand next to water."""
    from nh.danger import base_name
    s = s or ctx.last()
    if s.hero is None:
        return []
    water = _water(s)
    hx, hy = s.hero
    if not any((hx + dx, hy + dy) in water for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy):
        return []
    out = []
    for m in s.monsters or []:
        if m.get("dist") != 1 or m.get("tame") or m.get("peaceful") or m.get("statue"):
            continue
        if base_name(m.get("desc") or "") in DROWNERS or (m.get("unseen") and _in_water(s, m, water)):
            out.append(m)
    return out


def _eel_zone(s) -> dict:
    """{(x, y): (why, visible)}: see eel_zone()."""
    from nh.danger import base_name
    turn = s.status.turn if s.status.ok else None
    water = _water(s)
    seen = []
    for m in s.monsters or []:
        if m.get("tame") or m.get("peaceful"):
            continue
        bn = base_name(m.get("desc") or "")
        if bn in DROWNERS:
            seen.append((m["x"], m["y"], 0, bn))
        elif m.get("unseen") and _in_water(s, m, water):
            seen.append((m["x"], m["y"], 0, "unseen monster in the water ('I': a hidden eel/kraken?)"))
    tr = getattr(ctx.game, "tracker", None)
    if tr is not None and hasattr(tr, "gone") and turn is not None:
        for r in tr.gone(turn):
            d = r.get("desc") or ""
            bn = base_name(d)
            ago = turn - r.get("turn", turn)
            if bn in DROWNERS and 0 <= ago <= EEL_MEMORY and not d.startswith(("tame ", "peaceful ")):
                seen.append((r["x"], r["y"], ago, bn))
    out: dict = {}

    def mark_around(wx, wy, why, visible):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                c = (wx + dx, wy + dy)
                if s.screen.at(*c) not in "} " and c not in water and 1 <= c[1] <= 21:
                    if c not in out or (visible and not out[c][1]):
                        out[c] = (why, visible)

    for ex, ey, ago, bn in seen:
        reach = 1 if ago == 0 else min(6, 1 + ago // 2)
        why = f"{bn} at ({ex},{ey})" if ago == 0 else f"{bn} last seen at ({ex},{ey}) {ago} turns ago"
        for wy in range(ey - reach, ey + reach + 1):
            for wx in range(ex - reach, ex + reach + 1):
                if (wx, wy) == (ex, ey) or (wx, wy) in water:
                    mark_around(wx, wy, why, ago == 0)
    presumed = eel_level(s)
    if presumed:
        for (wx, wy) in water:
            mark_around(wx, wy, f"water that may hide eels/krakens ({presumed})", False)
    return out


def eel_zone(s=None) -> dict:
    """Land squares next to water where a drowning monster (giant/electric
    eel, kraken) is now or was seen lately: {(x, y): "why"}. Its wrap attack
    from the water drowns you on its next hit (levitation doesn't help), and
    it hides under the surface, so the water around its last sighting stays
    dangerous a while (reach grows ~1 square per 2 turns since, up to 6). An
    unseen 'I' in the water counts as one. On the Castle's and Medusa's
    levels, in Gehennom, and on any level where one was met, ALL water
    counts (their moats hold sea monsters created hidden: eel_level())."""
    s = s or ctx.last()
    return {c: why for c, (why, _vis) in _eel_zone(s).items()}


def _exploders_near(s, cells, radius: int = 2) -> list:
    """Known exploding monsters (a yellow light's blinding burst) within
    `radius` of any of `cells`."""
    from nh.danger import explodes_at_you
    ex = [m for m in (s.monsters or []) if not m.get("tame") and not m.get("peaceful") and m.get("desc")
          and explodes_at_you(m["desc"])]
    return [m for m in ex if any(dist((m["x"], m["y"]), c) <= radius for c in cells)]


def _travel(x, y, max_legs, max_dist, wait_peaceful, leg, auto_fight, pet_budget=None,
            fight_through=False, near_exploders=False, near_water=False, pass_hostile=False):
    s = ctx.last()
    engulfed_check(s, f"travel{(x, y)}")
    occ = [m for m in (s.monsters or []) if (m["x"], m["y"]) == (x, y) and not m.get("tame")
           and not m.get("pet") and not m.get("statue")]
    if occ and s.hero != (x, y):
        if all(m.get("unseen") or m["ch"] == "I" for m in occ):
            raise NavError(f"travel target {(x, y)} holds an 'I' — a REMEMBERED unseen monster, maybe long gone: "
                           f"clear_I({x}, {y}) walks next to it and searches once (a stale marker vanishes; a real "
                           "invisible monster is only felt, never attacked), then travel again")
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
    zone = {} if near_water or s.hero is None else {c: w for c, w in _eel_zone(s).items()
                                                    if c not in (s.hero, (x, y))}

    def eel_guard(path):
        """A route walked by hand (over a squeaky board) gets the same drowning check as travel's own
        (QA round 7: go_up() crossed a board next to a kraken moat without a word)."""
        hit = [c for c in path or [] if c in zone]
        if not hit:
            return
        vis = [c for c in hit if zone[c][1]]
        if vis:
            raise NavError(f"travel to {(x, y)}: the only known way passes {vis[0]}, next to the water with "
                           f"the {zone[vis[0]][0]} — its wrap drowns you (levitation doesn't help). Kill it or "
                           "freeze the water (cold ray) first, wait for it to leave, or travel(..., near_water=True)")
        print(f"travel: WARNING — the only known way passes {hit[0]}, next to {zone[hit[0]][0]}; going on "
              "(\"brushes against your leg\" / \"swings itself around you\" = step away from the water NOW)")

    if bad and s.hero is not None and bfs_path(s, s.hero, (x, y), allow_monsters=True) is None:
        # the only way may cross a displayed trap: fine if all of them are squeaky boards (they only squeak)
        wide = bfs_path(s, s.hero, (x, y), allow_monsters=True, allow_traps=True)
        on = [c for c in wide or [] if c in bad]
        boards = squeaky_boards(s)
        if on and set(on) <= boards:
            eel_guard(wide)
            print(f"travel: the only known way crosses the squeaky board(s) {on} — harmless (it squeaks and "
                  "wakes monsters nearby): walking over")
            return _walk_over(wide, boards)
        if on:
            # (NetHack's own travel won't cross a known trap either: it would just say "no known path")
            fd = getattr(s, "feature_desc", None) or {}
            what = ", ".join(f"{c} {fd.get(c) or 'trap'}" for c in on[:3])
            raise NavError(f"travel to {(x, y)}: the only known way crosses the known trap(s) {what} — cross it "
                           "on purpose (travel next to it, then step_onto(x, y): check what it does to you first), "
                           "or dig / find another way")
    if zone:
        direct = bfs_path(s, s.hero, (x, y), avoid=frozenset(bad), allow_monsters=True)
        hit = [c for c in direct or [] if c in zone]
        if hit:
            detour = bfs_path(s, s.hero, (x, y), avoid=frozenset(bad | set(zone)), allow_monsters=False,
                              allow_pets=True)
            if detour is not None:
                print(f"travel: detour of {len(detour)} steps away from the water by {hit[0]} — {zone[hit[0]][0]} "
                      "(a wrap from the water drowns you); travel(..., near_water=True) takes the short way")
                return walk_path(detour)
            vis = [c for c in hit if zone[c][1]]
            if vis:
                raise NavError(f"travel to {(x, y)}: the only known way passes {vis[0]}, next to the water with "
                               f"the {zone[vis[0]][0]} — its wrap drowns you (levitation doesn't help). Kill it or "
                               "freeze the water (cold ray) first, wait for it to leave, or travel(..., "
                               "near_water=True)")
            print(f"travel: WARNING — the only known way passes {hit[0]}, next to {zone[hit[0]][0]}; going on "
                  "(\"brushes against your leg\" / \"swings itself around you\" = step away from the water NOW)")
    if bad and s.hero is not None:
        direct = bfs_path(s, s.hero, (x, y), allow_monsters=True)
        if direct and any(c in bad for c in direct):
            for _try in range(6):
                cur = ctx.last()
                detour = bfs_path(cur, cur.hero, (x, y), avoid=frozenset(bad), allow_monsters=False, allow_pets=True)
                on = [c for c in direct if c in bad]
                boards = squeaky_boards(cur)
                if detour is None and on and set(on) <= boards:
                    # a squeaky board only squeaks (wakes monsters nearby): cross it rather than fail
                    over = bfs_path(cur, cur.hero, (x, y), avoid=frozenset(bad - boards), allow_monsters=False,
                                    allow_pets=True) or direct
                    eel_guard(over)
                    print(f"travel: the only known way crosses the squeaky board(s) {on} — harmless (it squeaks "
                          "and wakes monsters nearby): walking over")
                    return _walk_over(over, boards)
                if detour is None:
                    manual = set(ctx.game.avoid.get(ctx.game.level_key(cur.status), set()))
                    zone = set(special_room_zone(cur))
                    lst = sorted(bad)
                    raise NavError(f"travel to {(x, y)}: every known route crosses an avoided square — the direct "
                                   f"one crosses {on[:6]} (traps, avoid() squares, mimics, stationary hostiles, "
                                   f"special rooms: {lst[:12]}" + (f" ... and {len(lst) - 12} more" if len(lst) > 12
                                                                   else "") + ")"
                                   + (f"; {len(manual)} of them are your manual avoid() squares — avoid(clear=True) "
                                      "forgets them" if manual else "")
                                   + ("; a special room's squares count too — forget_room()" if zone & set(on)
                                      else ""))
                try:
                    return walk_path(detour)
                except NavError:
                    from .combat import fight_trivial
                    if not auto_fight or fight_trivial(ctx.last()) is None:
                        raise                  # not a trivial monster in the way: your call
            raise NavError(f"travel to {(x, y)}: the detour kept being blocked")
    waits = sidesteps = backoffs = fallbacks = fights = 0
    start = s.hero
    lvl0 = s.status.ldesc if s.status.ok else None
    for _ in range(max_legs):
        h0 = s.hero
        if lvl0 and s.status.ok and s.status.ldesc != lvl0:
            raise NavError(f"travel to {(x, y)}: the level changed under you ({lvl0} -> {s.status.ldesc}: a trap "
                           "door, a level teleporter, an expulsion...) — the target was on the old level; look "
                           "around first")
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
        if not near_exploders and h0 is not None:
            route = bfs_path(s, h0, (tx, ty), allow_monsters=True) or []
            ex = _exploders_near(s, [h0] + route[:8])
            if ex:
                raise NavError(f"travel to {(x, y)}: the way passes within 2 squares of {_mdesc(ex)}, which "
                               "EXPLODES next to you (a yellow light blinds you ~100 turns) — kill it at range "
                               "(throw/zap/fire), wait for it to come and fight from where it can't reach you, or "
                               "travel(..., near_exploders=True)")
        if (tx, ty) == (x, y) and h0 is not None and max(abs(x - h0[0]), abs(y - h0[1])) == 1:
            # a peaceful stepped onto the target: wait for it (a plain step into it is refused)
            peace = _peacefuls_at(s, (x, y))
            if peace:
                if waits < wait_peaceful:
                    waits += 1
                    print(f"travel: waiting a turn for {_mdesc(peace)} to leave the target square")
                    s = ctx.do(".", ok=BENIGN)
                    continue
                raise NavError(f"travel to {(x, y)}: {_mdesc(peace)} stays on the target square (waited "
                               f"{waits} turns; you are next to it at {h0})")
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
            # stop one short (the last step is a plain move) — on a free square when one will do
            path = bfs_path(s, h0, (x, y), allow_monsters=False, allow_pets=True) or \
                bfs_path(s, h0, (x, y), allow_monsters=True)
            if path and len(path) >= 2:
                tx, ty = path[-2]
        if h0 is not None and dist((tx, ty), h0) == 1:
            # findtravelpath(): "if travel to adjacent, just go there" — a plain move with travel's
            # nopick flag: a monster there gets "You move right into it" (a wasted turn; an engulfer
            # engulfs you). Step there ourselves, checked
            peace = _peacefuls_at(s, (tx, ty))
            if peace:
                # e.g. a peaceful in the doorway in front of the stairs: it usually moves on
                if waits < wait_peaceful:
                    waits += 1
                    print(f"travel: waiting a turn for {_mdesc(peace)} to move off {(tx, ty)}")
                    s = ctx.do(".", ok=BENIGN)
                    continue
                raise NavError(f"travel to {(x, y)}: {_mdesc(peace)} stays on {(tx, ty)}, the next square "
                               f"(waited {waits} turns) — wait longer or go around")
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
            if hostile and fight_through and fights < 12:
                from .combat import fight
                fights += 1
                print(f"travel: fighting {_mdesc(hostile)} on the way (fight_through)")
                s = fight()
                if s.state.kind != "command" or s.adjacent_hostiles():
                    return s             # fight() stopped (HP, passive, a new threat): your call
                continue
            if hostile and not all(_passive_only(m) for m in hostile) and not pass_hostile:
                raise NavError(f"travel to {(x, y)} did not move: hostile {_mdesc(hostile)} adjacent — "
                               "travel never starts next to one. Fight it (fight()), step away by hand, "
                               "travel(..., fight_through=True), or travel(..., pass_hostile=True) to walk past "
                               "it on your own route without attacking (a SLEEPING one: Stealth keeps it asleep)")
            # (a floating eye, a mold: no active attack — step away along our own route like past a peaceful)
            if blk and sidesteps < 6:
                # lookaround(): NetHack's travel never starts next to a non-tame monster, even one
                # that isn't in the way — plain steps along our own route (never into it) do
                own = bfs_path(s, h0, (x, y), avoid=frozenset(bad_squares(s) - {(x, y)}), allow_monsters=False,
                               allow_pets=True)
                if own:
                    sidesteps += 1
                    try:
                        s2 = walk_path(own[:2])
                    except NavError:
                        s2 = ctx.last()
                    if s2.hero != h0:
                        s = s2
                        continue
            from nh.monitor import _stationary
            if blk and waits < wait_peaceful and not all(_stationary(m.get("desc") or "") for m in blk):
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
                                   allow_monsters=False, allow_pets=True) if "locked" in str(e) and cur.hero else None
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
            own = bfs_path(s, h0, (x, y), avoid=frozenset(bad_squares(s) - {(x, y)}), allow_monsters=False,
                           allow_pets=True)
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
            if not _HEADING[0] and s.state.kind == "command" and s.hero is not None \
                    and bfs_path(s, s.hero, (x, y), allow_monsters=True) is None:
                # the way there runs through ground you haven't seen (a dark hall): NetHack's travel only
                # guesses; go frontier by frontier toward it instead
                from .explore import head_to
                print(f"travel: no known path to {(x, y)} from {s.hero} — making for it across unexplored ground "
                      "(head_to)")
                _HEADING[0] = True
                try:
                    return head_to(x, y)
                finally:
                    _HEADING[0] = False
            raise NavError(_no_path_msg(s, h0, (x, y), start))
        if _notable(s.messages) and not s.paused:
            # something happened en route; let the caller look (unless the exec
            # already paused on it and the player chose to go on)
            print(f"travel: stopped at {s.hero} short of {(x, y)} on {_notable(s.messages)} — look, then "
                  "travel again")
            return s
    return s


def _no_path_msg(s, h0, target, start=None, bad=None) -> str:
    """Why travel can't get there, and what would: the traps/water the only
    known route crosses (the invocation's ring of fire traps and moat), or
    that the known map doesn't connect (and whether anything is left to
    explore). bad: known trap/avoid squares (default bad_squares(); a trap
    hidden under an object is one too)."""
    x, y = target
    here = s.hero or h0
    if bad is None:
        try:
            bad = bad_squares(s)
        except Exception:  # noqa: BLE001
            bad = set()
    bad = frozenset(c for c in bad if c != tuple(target))
    head = (f"travel to {target} stopped at {here}: NetHack's travel guessed its way from {start} and has no "
            "known path on from here" if start is not None and here != start else
            f"travel to {target} did not move: no known path")
    msgs = f"; messages: {s.messages}" if s.messages else ""
    if bfs_path(s, h0, target, allow_monsters=True, avoid=bad) is not None:
        return head + " (a route exists on the map you know — something on it stops travel: look at it)" + msgs
    wide = None
    for traps, water in ((True, False), (False, True), (True, True)):     # the fewest kinds of hazard
        wide = bfs_path(s, h0, target, allow_monsters=True, allow_traps=traps, allow_water=water,
                        avoid=frozenset() if traps else bad)
        if wide is not None:
            break
    if wide is not None:
        traps_on = [c for c in wide if s.screen.at(*c) == "^" or c in bad]
        water_on = [c for c in wide if s.screen.at(*c) == "}"]
        bits = ([f"the known trap(s) at {traps_on[:4]}"] if traps_on else []) + \
               ([f"water/lava at {water_on[:3]}" + (" ..." if len(water_on) > 3 else "")] if water_on else [])
        how = []
        if traps_on:
            how.append("farlook() the trap(s) and step onto one on purpose with do(dir, force=True) / "
                       "step_onto(x, y) if it's survivable for you (a fire trap with fire resistance only "
                       "burns scrolls/potions/spellbooks; levitating floats over holes, trap doors and pits)")
        if water_on:
            how.append("cross the water: FREEZE it (zap a wand of cold / frost horn across it: \"The moat is "
                       "bridged with ice!\" — nothing to take off afterwards), or levitate (a ring on your LEFT "
                       "hand: a cursed weapon locks a right-hand ring on) / water walking, and take the "
                       "levitation off before the stairs")
        tip = (" — the invocation stairs are always ringed by fire traps and a 2-wide moat: step onto one fire "
               "trap on purpose, freeze the moat (or levitate, ring on the left hand), then go_up()"
               if traps_on and water_on else "")
        return f"{head}: the only known route crosses {' and '.join(bits)}: " + "; ".join(how) + tip + msgs
    rolled = bfs_path(s, h0, target, allow_monsters=True, allow_traps=True, allow_water=True, allow_boulders=True)
    if rolled is not None:
        rocks = [c for c in rolled if s.screen.at(*c) in "0`"]
        if rocks:
            return (f"{head}: the only known route passes the boulder(s) at {rocks[:4]}: push one by stepping into "
                    "it (a boulder with another boulder or a wall behind it won't move), smash it (force bolt, "
                    "wand of striking), or dig around it" + msgs)
    try:
        from .explore import screen_frontiers
        open_edges = bool(screen_frontiers(s))
    except Exception:  # noqa: BLE001
        open_edges = True
    maze = ""
    try:
        if ctx.game.level_key(s.status).startswith("Gehennom"):
            maze = ("; in Gehennom's mazes digging is often quickest: dig(dir) with a pick-axe or zap digging "
                    "sideways through the maze wall toward it (Vlad's Tower, the Wizard's Tower and some lairs are "
                    "undiggable)")
    except Exception:  # noqa: BLE001
        pass
    if open_edges:
        return (f"{head} — the map you know doesn't connect to it: explore() to find the way, or head_to{target} "
                "across the unexplored part" + maze + msgs)
    return (f"{head} — the known map doesn't connect to it and has no unexplored edge left: search() walls and "
            "dead ends for hidden doors/passages, dig through (not on undiggable levels), or teleport/levitate"
            + maze + msgs)


def _passive_only(m) -> bool:
    """A monster with no active attack (floating eye, molds, gas spore): it
    can't hurt you if you don't hit it, so travel may step away from it."""
    from nh.danger import base_name, monster_record
    rec = monster_record(base_name(m.get("desc") or ""))
    return bool(rec) and all(a.get("type") in ("AT_NONE", "AT_BOOM") for a in rec.get("attacks", []))


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
    lev = "Lev" in (s.status.conditions if s.status.ok else ())
    kick = ("unlock{0} with a key, zap striking/force bolt at it, or land first (levitating: no floor to brace "
            "a kick on)" if lev else "unlock{0} with a key, kick_door{0} (never a shop door or in Minetown)").format(door)
    if door in known:
        raise NavError(f"travel: the door at {door} is locked (known) — {kick}, or go another way")
    key = DIR_KEY[(door[0] - h[0], door[1] - h[1])]
    for _ in range(6):
        s = ctx.do(key, ok=BENIGN + [r"^The door opens\.", r"^The door resists", r"^This door is locked"])
        text = " ".join(s.messages)
        if "locked" in text:
            known.add(door)
            raise NavError(f"travel: the door at {door} is locked — {kick}, or go another way")
        if "door opens" in text or not is_closed_door(s, *door):
            return s
    raise NavError(f"travel: the door at {door} won't open (stuck?)")


def _notable(messages) -> list:
    """Messages that aren't routine for walking around (BENIGN + the kernel's
    DEFAULT_BENIGN, and what the running exec autocontinues (-a) or a level
    sound already paused for on this level): anything left deserves the
    caller's attention."""
    import re
    from nh.kernel import DEFAULT_BENIGN
    pats = [re.compile(p) for p in BENIGN]
    quiet = set(ctx.quiet_messages(messages)) if ctx.quiet_messages is not None else set()
    return [m for m in messages or [] if not any(p.search(m) for p in pats)
            and not any(p.search(m) for p in DEFAULT_BENIGN) and m not in quiet]


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


def step_onto(x: int, y: int, force: bool = True, quest_ok: bool = False):
    """One plain step onto the ADJACENT square (x, y) — the way onto a trap
    target (a magic portal, a trap door, a hole, a fire trap you resist) once
    travel() has stopped next to it. Raises NavError if you are not next to
    it (travel may have stopped short: a monster, a message), so a forced
    step never goes off in the wrong direction. force=True (the default)
    passes the trap/water step guards; never the never-attack check."""
    s = ctx.require_command("step_onto()")
    h = s.hero
    if h is None or max(abs(x - h[0]), abs(y - h[1])) != 1:
        raise NavError(f"step_onto({x}, {y}): you are at {h}, not next to it — travel there first (travel() may "
                       "have stopped short)")
    from .mapview import DIR_KEY
    return step(DIR_KEY[(x - h[0], y - h[1])], force=force, quest_ok=quest_ok)


def step(direction: str, n: int = 1, force: bool = False, quest_ok: bool = False):
    """Move one square n times (direction: y k u h l b j n). Stops on messages
    (inside exec) like any do(). Never attacks: NavError if a monster (not
    your pet) is on the next square — do('F' + direction) to attack.
    force=True passes the harness's step guards (a known trap, water) — never
    the never-attack check."""
    from .mapview import KEY_DIR
    s = ctx.last()
    for _ in range(n):
        if s.hero is not None and direction in KEY_DIR:
            dx, dy = KEY_DIR[direction]
            _check_free(s, (s.hero[0] + dx, s.hero[1] + dy), "step()")
            _leader_check(s, (s.hero[0] + dx, s.hero[1] + dy), "step()", quest_ok, route=[])
        s = ctx.do(direction, force=force)
    return s


def _branch(key: str | None) -> str:
    """'The Gnomish Mines / Level 3' -> 'The Gnomish Mines' ('' if unknown)."""
    return key.split(" / ")[0] if key and " / " in key else ""


# travel()/head_to() failures that mean "no way there" (not a monster or a guard): another staircase may do
_UNREACHABLE = re.compile(r"no reachable frontier|no known path|no (?:known )?route|every known route|"
                          r"not there after|kept being blocked|did not reach", re.I)


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
    if len(unknown) > 1:
        # a LADDER is drawn like stairs (Vlad's Tower, the Wizard's Tower inside): look (no game time)
        ladders = []
        for c in unknown:
            if c != s.hero:
                try:
                    # "< a staircase up or a ladder up (ladder up)": the symbol's generic text names both;
                    # the square's own description is the part in parentheses (an object lying there hides it)
                    spec = re.findall(r"\(([^()]*)\)", farlook(*c) or "")
                    if spec and re.match(r"ladder (?:up|down)$", spec[-1].strip()):
                        ladders.append(c)
                except Exception:  # noqa: BLE001
                    pass
        if ladders and len(ladders) < len(unknown):
            print(f"stairs: {ladders} {'is a ladder' if len(ladders) == 1 else 'are ladders'} (a tower's) — "
                  "not taking it unless nothing else is left")
            unknown = [c for c in unknown if c not in ladders]
            cells = [c for c in cells if c not in ladders] + ladders
            if not other and len(unknown) == 1:
                return unknown[0], "the only staircase (the other is a ladder)"
    if other and unknown:
        return unknown[0], (f"the other {ch} at {other[0]} leads to {known[other[0]]}; pass to='...' to take a "
                            "branch on purpose")
    print(f"stairs: {len(cells)} {ch!r} here ({', '.join(map(str, cells))}) and where they lead is unknown — "
          f"taking the nearest, {cells[0]}; one may be a branch staircase or a tower ladder (overview() says which branch starts on "
          f"this level; go_{'down' if ch == '>' else 'up'}(to='Mines'/'Sokoban'/'Dungeons') once one is known, "
          "or travel to the other one and press it yourself)")
    return cells[0], ""


# do.c goto_level(): the climb itself (verbose); falling down while Burdened costs 1-3 HP (the HP rules
# still apply) — anything else on arrival still pauses
_STAIRS_OK = [r"^(?:With great effort, you|You) (?:climb|float|fly) up(?: along)? the (?:stairs|ladder)\.$",
              r"^You (?:fly|float) down (?:along )?the (?:stairs|ladder)\.$", r"^You fall down the (?:stairs|ladder)\.$",
              r"^You (?:descend the stairs|climb down the ladder)\.$",
              r"^You can't go (?:down|up) here\.$",      # handled below: the stairs memory was wrong
              r"^(?:The |Your )?[\w' -]+ is still eating\.$"]   # your pet stays behind (said above)


def _forget_stairs(cell, ch: str) -> None:
    """The stairs memory was wrong ("You can't go down here."): forget that
    square and read the game's own map (#terrain, no game time) again."""
    g = ctx.game
    key = g.level_key(ctx.last().status)
    mem = g.terrain_seen.get(key, {})
    if mem.get(tuple(cell)) == ch:
        del mem[tuple(cell)]
    g.stair_links.get(key, {}).pop(tuple(cell), None)
    found = g.terrain_scan() if hasattr(g, "terrain_scan") else None
    if found:
        g.terrain_seen.setdefault(key, {}).update(
            {c: v for c, v in found["features"].items() if not (v == ch and c == tuple(cell))})
    if hasattr(g, "_annotate"):
        g._annotate(ctx.last())          # the obs shows the corrected memory at once


def _use_stairs(ch: str, tries: int = 4, wait_pet: int = 0, to: str | None = None, with_pet=None,
                _retried: bool = False, pass_hostile: bool = False):
    s = ctx.last()
    engulfed_check(s, "go_down()" if ch == ">" else "go_up()")
    if s.status.ok and "Lev" in s.status.conditions:
        raise NavError("you are LEVITATING: you can't reach the stairs (\"You are floating high above the "
                       "stairs\") — remove the ring/boots of levitation or wait for it to wear off")
    cells = known_cells(ch, s, rescan=True)
    if not cells:
        raise NavError(f"no {ch!r} known on this level" + (_ways_down_hint(s) if ch == ">" else ""))
    fallback: list = []
    if s.hero is not None and len(cells) > 1:
        # a ladder inside the sealed Wizard's Tower seen from outside (or its ladder from inside the maze
        # around it), stairs behind water: choose among the ones reachable over the known map; the rest
        # are tried only if those turn out unreachable
        reach = [c for c in cells if c == s.hero or bfs_path(s, s.hero, c, allow_monsters=True) is not None]
        if reach and len(reach) < len(cells) and not to:
            fallback = [c for c in cells if c not in reach]
            cells = reach
        elif reach:
            cells = reach + [c for c in cells if c not in reach]
    target, note = _pick_stairs(ch, cells, to, s)
    if note:
        print(f"stairs: using the {ch} at {target}: {note}")
    others = [c for c in cells + fallback if c != target] if not to else []
    had_pet = [m for m in _pets(s) if m.get("dist") is not None and m["dist"] <= 7]
    auto = with_pet is None
    if auto:
        with_pet = bool(wait_pet and had_pet)       # it's with you now: keep it in tow
    for _ in range(tries):
        if s.hero == target:
            break
        try:
            s = travel(*target, with_pet=with_pet, pass_hostile=pass_hostile)
        except PetLost as e:
            if not auto:
                raise
            print(f"stairs: {e} — going on without it")
            with_pet = False
            s = ctx.last()
            continue
        except NavError as e:
            if others and _UNREACHABLE.search(str(e)):
                nxt = others.pop(0)
                print(f"stairs: can't get to the {ch} at {target} ({str(e)[:90]}) — trying the {ch} at {nxt}")
                target = nxt
                s = ctx.last()
                continue
            raise
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
    d0 = s.status.dlvl if s.status.ok else None
    s = ctx.do(ch, expect=("level",), ok=_STAIRS_OK)   # the level change is the point: no pause for it
    cur = ctx.last()
    if ch == "<" and d0 and cur.status.ok and cur.status.dlvl and cur.status.dlvl > d0:
        # (a script loop must not carry on as if it had climbed: its next go_down() would run down here)
        raise NavError(f"stairs: the MYSTERIOUS FORCE (you carry the Amulet) sent you DOWN, Dlvl {d0} -> "
                       f"{cur.status.dlvl}, to a random spot: find this level's '<' (known_cells('<') / explore()) "
                       "and climb again")
    if ch == "<" and d0 and cur.status.ok and cur.status.dlvl == d0 and cur.status.ldesc == ld0 \
            and any(m.startswith("A mysterious force momentarily surrounds you") for m in cur.messages):
        raise NavError(f"stairs: the MYSTERIOUS FORCE (you carry the Amulet) kept you on Dlvl {d0}, moved to "
                       f"{cur.hero}: go back to the '<' and climb again")
    if cur.state.kind == "command" and ld0 is not None and cur.status.ok and cur.status.ldesc == ld0:
        if not _retried and any(m.startswith(("You can't go down here", "You can't go up here"))
                                for m in cur.messages):
            # the remembered stairs were not there (e.g. you had arrived NEXT TO them: a monster took the
            # arrival square): forget that square, re-read the map, try once more
            print(f"stairs: no {ch} at {target} after all — forgetting it and re-reading the map (#terrain)")
            _forget_stairs(target, ch)
            return _use_stairs(ch, tries, wait_pet, to, with_pet, _retried=True, pass_hostile=pass_hostile)
        raise NavError(f"pressed {ch!r} at {target} but you are still on {ld0}"
                       + (f": {cur.messages}" if cur.messages else "") + " — look at why before going on")
    return s


def _ways_down_hint(s) -> str:
    """No '>' known: trap doors/holes you know of also lead down — on the
    Castle (the drawbridge level) they are the only way into Gehennom."""
    fd = getattr(s, "feature_desc", None) or {}
    holes = sorted(c for c, d in fd.items() if "trap door" in d or d.strip() == "hole" or d.endswith(" hole"))
    castle = "castle" in getattr(s, "flags", ()) or any("drawbridge" in f["name"] for f in s.features)
    if holes:
        return (f" — but trap door(s)/hole(s) are known at {holes[:5]}: they lead down (step in on purpose with "
                "step_onto(x, y)); " + ("this is the Castle: its trap doors are the ONLY way down, into the "
                                              "Valley of the Dead (Gehennom) — ready for it?" if castle else
                                              "you land somewhere random below"))
    if castle:
        return (" — this is the Castle (drawbridge): it has no down stairs and its floor can't be dug; the way "
                "into Gehennom is the row of trap doors in the corridor behind the throne room's east wall (a "
                "secret door), which runs to the fortress's east door. Find them (explore / magic mapping)")
    return " — explore() to find one"


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
    from nh.monitor import _stationary
    for i in range(turns):
        if [m for m in s.hostiles(2) if not _stationary(m.get("desc") or "")]:
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


def go_down(wait_pet: int = 6, to: str | None = None, with_pet=None, pass_hostile: bool = False):
    """Travel to a '>' (re-travelling after routine stops), check you are on
    it, then descend. Raises NavError instead of pressing '>' anywhere else.
    With several '>' on the level it takes the one that stays in this branch
    (learned from stairs you took or arrived on), or the one toward `to`
    (a substring of the destination: 'Mines', 'Dungeons', 'Sokoban').
    wait_pet: if your pet is in view nearby but not next to you, wait up to
    this many turns for it (0: don't). with_pet: travel in pet-keeping legs
    (see travel()); default: yes when wait_pet and your pet is within 7
    squares at the start. Says so when it leaves the pet behind.
    pass_hostile=True: walk past a hostile that stops the trip (see travel())."""
    return _use_stairs(">", wait_pet=wait_pet, to=to, with_pet=with_pet, pass_hostile=pass_hostile)


def descend(levels: int = 1, wait_pet: int = 6, to: str | None = None):
    """go_down() `levels` times in a row (the Dungeons' main stairs by default,
    or toward `to`). The level changes don't pause; newcomers farther than 6
    squares without a danger note wait until they come near (defer_far);
    anything dangerous, adjacent, HP loss or a message still pauses. Stops
    early (returns) at a prompt or when a go_down() stops short. Returns the
    last snap."""
    import contextlib
    far = getattr(ctx, "defer_far", None)
    s = ctx.last()
    with (far(6) if far is not None else contextlib.nullcontext()):
        for i in range(levels):
            ld0 = ctx.last().status.ldesc
            s = go_down(wait_pet=wait_pet, to=to)
            if s.state.kind != "command" or ctx.last().status.ldesc == ld0:
                return s
            print(f"descend(): {ld0} -> {ctx.last().status.ldesc} ({i + 1}/{levels})")
    return s


def go_up(wait_pet: int = 6, to: str | None = None, with_pet=None, pass_hostile: bool = False):
    """Like go_down() for '<' (e.g. go_up(to='Sokoban') on the Oracle-below level)."""
    return _use_stairs("<", wait_pet=wait_pet, to=to, with_pet=with_pet, pass_hostile=pass_hostile)


def kick_door(x, y, tries: int = 8):
    """Kick the (adjacent) door at (x, y) until it opens/breaks. Never do this
    to shop doors (angers the shopkeeper) or in Minetown (angers the Watch)."""
    s = ctx.last()
    h = s.hero
    if h is None or max(abs(x - h[0]), abs(y - h[1])) != 1:
        raise NavError(f"kick_door: {(x, y)} is not adjacent to you at {h}")
    if getattr(s, "medusa_risk", False):
        raise NavError("kick_door: probably MEDUSA'S LEVEL and you're neither blind nor reflecting — the kick "
                       "wakes her and opens a line of sight: blindfold or reflection first")
    if s.status.ok and "Lev" in s.status.conditions:
        raise NavError("kick_door: you are levitating — no floor to brace a kick on; unlock it, zap striking / "
                       "force bolt, or land first")
    key = DIR_KEY[(x - h[0], y - h[1])]
    for _ in range(tries):
        s = ctx.do("<C-d>", quiet=True)
        if s.state.kind != "direction":
            if any("in no shape for kicking" in m for m in s.messages):
                print("kick_door: WOUNDED LEGS (a xan's sting, a trap, a fall...) — no kicking until they heal "
                      "(some dozens of turns; a unicorn horn doesn't help): unlock(x, y) with a key/lock pick, "
                      "#force the lock of a box, zap striking / force bolt at the door, or dig around it")
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
