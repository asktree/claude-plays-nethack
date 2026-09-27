"""Special levels drawn from NetHack 3.6.7's fixed maps (dat/*.des).

The Valley, Medusa's island, the Castle, the Wizard's Tower, Vlad's Tower,
the quest, Minetown... are built from fixed MAP blocks. identify() slides
each candidate map over the screen and picks the map and offset whose walls,
floors and water agree best with what you have seen; then the whole layout
(unseen rooms, secret doors, fixed traps, stairs, portals) is known:
show() lists it in screen coordinates and route()/walk() plan over it —
through dark and never-seen parts — like a player with the map on the desk.

Data: src/nh/data/desmaps.json (scripts/gen_desmaps.py). A map only covers
its MAP block: the random maze or filler around it is not in it, and some
levels have random variants (identify() picks the best-matching one).
"""

from __future__ import annotations

import heapq
import json
from pathlib import Path

from . import ctx

_DATA = Path(__file__).resolve().parents[2] / "src" / "nh" / "data" / "desmaps.json"
_MAPS: list | None = None

BROWN = 3
_MAP_CLS = {"-": "wall", "|": "wall", "S": "sdoor", "H": "scorr", ".": "floor", "B": "floor", "#": "floor",
            "{": "floor", "\\": "floor", "K": "floor", "A": "floor", "C": "floor", "+": "door", "}": "water",
            "P": "water", "W": "water", "L": "lava", "I": "floor", "T": "tree", "F": "bars", " ": "stone"}
# screen class -> map class -> score
_SCORE = {
    "wall": {"wall": 2, "sdoor": 2, "stone": -1, "floor": -3, "door": -1, "water": -3, "lava": -3, "tree": -1,
             "bars": -1, "scorr": -1},
    "floor": {"floor": 1, "door": 1, "sdoor": 0, "scorr": 1, "wall": -3, "water": -1, "lava": -2, "stone": -1,
              "tree": -1, "bars": -1},
    "door": {"door": 2, "sdoor": 2, "wall": -1, "floor": 0, "stone": -2, "water": -3, "lava": -3, "tree": -2,
             "bars": -2, "scorr": -1},
    "water": {"water": 2, "floor": -2, "wall": -3, "stone": -2, "door": -3, "sdoor": -3, "lava": -1, "tree": -2,
              "bars": -2, "scorr": -2},
    "lava": {"lava": 2, "water": -1, "floor": -2, "wall": -3, "stone": -2, "door": -3, "sdoor": -3, "tree": -2,
             "bars": -2, "scorr": -2},
    "tree": {"tree": 2, "floor": -1, "wall": -1, "stone": -1},
    "bars": {"bars": 2, "wall": -1, "floor": -1, "stone": -1},
}
_CONTEXT = [   # level key prefix -> .des files worth trying first
    ("Gehennom", ("gehennom.des", "yendor.des")),
    ("Vlad's Tower", ("tower.des",)),
    ("Fort Ludios", ("knox.des",)),
    ("The Gnomish Mines", ("mines.des",)),
    ("Sokoban", ("sokoban.des",)),
    ("The Dungeons of Doom", ("medusa.des", "castle.des", "bigroom.des", "oracle.des")),
    ("The Elemental Planes", ("endgame.des",)),
    ("The Quest", ("Valkyrie.des",)),
]
ENDGAME = ("Earth", "Air", "Fire", "Water", "Astral Plane")


def maps() -> list:
    global _MAPS
    if _MAPS is None:
        _MAPS = json.loads(_DATA.read_text())["maps"]
        for m in _MAPS:
            m["_cells"] = [(x, y, _MAP_CLS[ch]) for y, row in enumerate(m["rows"]) for x, ch in enumerate(row)
                           if ch in _MAP_CLS]
            m["w"] = max((len(r) for r in m["rows"]), default=0)
            m["h"] = len(m["rows"])
    return _MAPS


def _screen_cls(s) -> dict:
    """{(x, y): class} for the map cells you can read on screen (monsters/objects/blank: unknown)."""
    scr = s.screen
    out = {}
    for y in range(1, 22):
        row = scr.row(y)
        for x, ch in enumerate(row):
            col = scr.color_at(x, y)
            if ch in "-|":
                out[(x, y)] = "door" if col == BROWN else "wall"
            elif ch == "+" and col == BROWN:
                out[(x, y)] = "door"
            elif ch in ".<>_{\\^":
                out[(x, y)] = "floor"
            elif ch == "#":
                out[(x, y)] = ("tree" if col == 2 else "bars" if col == 6 else "door" if col == BROWN
                               else "floor" if col in (7, 8, 15) else None)
            elif ch == "}":
                out[(x, y)] = "lava" if col in (1, 9) else "water"
    return {c: v for c, v in out.items() if v is not None}


def _candidates(key: str, names=None) -> list:
    if names:
        want = {names} if isinstance(names, str) else set(names)
        return [m for m in maps() if m["level"] in want]
    files = next((f for pre, f in _CONTEXT if key.startswith(pre)), None)
    if key in ENDGAME:
        files = ("endgame.des",)
    return [m for m in maps() if files is None or m["file"] in files]


def _best_offset(m: dict, seen: dict) -> tuple:
    """(score, ox, oy, good, bad, runner_up_score) of the best placement of map m."""
    best = (-10 ** 9, 0, 0, 0, 0)
    second = -10 ** 9
    w, h = m["w"], m["h"]
    for oy in range(1, max(2, 23 - h)):
        for ox in range(0, max(1, 81 - w)):
            score = good = bad = 0
            for x, y, cls in m["_cells"]:
                sc = seen.get((x + ox, y + oy))
                if sc is None:
                    continue
                v = _SCORE.get(sc, {}).get(cls, 0)
                score += v
                if v > 0:
                    good += 1
                elif v < 0:
                    bad += 1
            if score > best[0]:
                second = max(second, best[0])
                best = (score, ox, oy, good, bad)
            elif score > second:
                second = score
    return best + (second,)


def identify(names=None, s=None, min_score: int = 30, remember: bool = True) -> dict | None:
    """Which fixed map is this level (and where on the screen)? Slides the candidate maps (by the level's
    branch, or `names` like 'valley' / ['medusa-1', 'medusa-2']) over what you have seen and returns the best
    {"level", "index", "ox", "oy", "score", "good", "bad"} — screen (x, y) = map (x + ox, y + oy) — or None
    when nothing fits well enough (see more of the level first). Remembered per level."""
    s = s or ctx.last()
    key = ctx.game.level_key(s.status)
    seen = _screen_cls(s)
    best = None
    runner = -10 ** 9
    for m in _candidates(key, names):
        sc, ox, oy, good, bad, second = _best_offset(m, seen)
        if best is None or sc > best["score"]:
            if best is not None and (best["rows"] != m["rows"]):
                runner = max(runner, best["score"])      # (identical maps, e.g. fakewiz1/2: not a rival)
            best = {"level": m["level"], "index": m["index"], "ox": ox, "oy": oy, "score": sc, "good": good,
                    "bad": bad, "rows": m["rows"]}
            runner = max(runner, second)
        elif m["rows"] != best["rows"]:
            runner = max(runner, sc)
    if best is None or best["score"] < min_score or best["bad"] * 4 > best["good"]:
        return None
    best.pop("rows")
    if runner >= best["score"] - max(4, best["score"] // 10):
        best["ambiguous"] = True       # another placement fits almost as well: see more of the level first
        return best
    if remember:
        store = getattr(ctx.game, "desmap_ids", None)
        if store is None:
            ctx.game.desmap_ids = store = {}
        store[key] = best
    return best


def _current(s=None, names=None) -> tuple:
    s = s or ctx.last()
    key = ctx.game.level_key(s.status)
    found = (getattr(ctx.game, "desmap_ids", None) or {}).get(key) if not names else None
    found = found or identify(names=names, s=s)
    if found is None:
        raise RuntimeError("desmap: no fixed map matches this level yet (see more of it, or pass names=...)")
    if found.get("ambiguous"):
        raise RuntimeError(f"desmap: the view fits {found['level']} at ({found['ox']},{found['oy']}) but another "
                           "placement fits almost as well — see more of the level first")
    m = next(mm for mm in maps() if mm["level"] == found["level"] and mm["index"] == found["index"])
    return m, found


def layout(s=None, names=None) -> dict:
    """{(x, y) screen: map char} of the identified map."""
    m, f = _current(s, names)
    return {(x + f["ox"], y + f["oy"]): ch for y, row in enumerate(m["rows"]) for x, ch in enumerate(row)
            if ch != "x"}


def features(s=None, names=None) -> list:
    """The map's fixed features in SCREEN coordinates: [{kind, x, y, detail}] (stairs, ladders, traps, doors
    with their state, altars, portals, branch stairs, drawbridges, named monsters' starting squares)."""
    m, f = _current(s, names)
    return [dict(ft, x=ft["x"] + f["ox"], y=ft["y"] + f["oy"]) for ft in m["features"]]


def show(s=None, names=None) -> str:
    """One line per feature, plus the secret doors of the map; prints and returns it."""
    s = s or ctx.last()
    m, f = _current(s, names)
    lay = layout(s, names)
    secret = sorted(c for c, ch in lay.items() if ch == "S")
    lines = [f"{m['level']} (map {m['index']}, from {m['file']}) at offset ({f['ox']},{f['oy']}), "
             f"match {f['good']} good / {f['bad']} bad"]
    for ft in features(s, names):
        lines.append(f"  {ft['kind']:10} ({ft['x']},{ft['y']}) {ft['detail']}")
    if secret:
        lines.append(f"  secret doors: {secret[:20]}" + (" ..." if len(secret) > 20 else ""))
    txt = "\n".join(lines)
    print(txt)
    return txt


def route(x: int, y: int, s=None, names=None, allow_water: bool = False, trap_cost: int = 30) -> dict:
    """Cheapest path from you to (x, y) over what you have seen AND the identified map (unseen and dark parts
    included). Known traps and the map's fixed traps cost `trap_cost` extra steps each (crossed only when there
    is no other way); undiscovered secret doors on it cost 20 and are listed in "secret" (search next to them
    before walking through). No diagonal moves into or out of doorways. Returns {"path", "secret", "traps"}
    or raises RuntimeError when there is no way even on the map."""
    from .mapview import is_door, is_walkable
    from .nav import bad_squares
    s = s or ctx.last()
    lay = layout(s, names)
    hero = s.hero
    if hero is None:
        raise RuntimeError("desmap.route: where are you?")
    feats = features(s, names)
    traps = {(ft["x"], ft["y"]) for ft in feats if ft["kind"] == "trap"} | set(bad_squares(s))
    goal = (x, y)

    def passable(c) -> bool:
        ch = lay.get(c)
        shown = s.screen.at(*c)
        if shown not in " " and is_walkable(s, *c, allow_monsters=True):
            return ch not in ("-", "|") or shown not in "-|"
        if shown in "-|" and s.screen.color_at(*c) != BROWN:
            return ch == "S"                     # a secret door not found yet
        if shown == "}":
            return allow_water
        if shown != " ":
            return ch in (".", "B", "#", "+", "{", "\\", "K", "I", "S", "H") or c == goal
        return ch in (".", "B", "#", "+", "{", "\\", "K", "I", "S", "H") or (allow_water and ch in "}PW")

    def doorish(c) -> bool:
        return lay.get(c) in ("+", "S") or is_door(s, *c)

    dist = {hero: 0}
    prev: dict = {hero: None}
    pq = [(0, hero)]
    while pq:
        d, p = heapq.heappop(pq)
        if p == goal:
            break
        if d > dist[p]:
            continue
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if not dx and not dy:
                    continue
                n = (p[0] + dx, p[1] + dy)
                if not (0 <= n[0] < 80 and 1 <= n[1] <= 21) or not passable(n):
                    continue
                if dx and dy and (doorish(p) or doorish(n)):
                    continue
                cost = 1
                if n in traps and n != goal:
                    cost += trap_cost
                if lay.get(n) == "S" and s.screen.at(*n) in "-|" and s.screen.color_at(*n) != BROWN:
                    cost += 20
                if d + cost < dist.get(n, 10 ** 9):
                    dist[n] = d + cost
                    prev[n] = p
                    heapq.heappush(pq, (d + cost, n))
    if goal not in prev:
        raise RuntimeError(f"desmap.route: no way to {goal} on the map either"
                           + ("" if allow_water else " (allow_water=True if you can cross water)"))
    path = []
    p = goal
    while p is not None:
        path.append(p)
        p = prev[p]
    path = path[::-1][1:]
    secret = [c for c in path if lay.get(c) == "S" and s.screen.at(*c) in "-|" and s.screen.color_at(*c) != BROWN]
    return {"path": path, "secret": secret, "traps": [c for c in path if c in traps]}


def walk(x: int, y: int, max_steps: int = 80, names=None, allow_water: bool = False, fight: bool = True):
    """Walk the route() to (x, y) one checked step at a time (walk_path: never onto a monster), re-planning as
    the map fills in. Stops next to an undiscovered secret door on the way (search there: search(10)), before
    a trap it would have to cross (step_onto() it on purpose), at a locked door (unlock()), or when something
    happens. fight=True: trivial hostiles next to you (combat.auto_fightable: 'trivial' threat, no passive
    attack, no danger note) are fought on the way; anything else stops the walk. Returns the final snap."""
    from .nav import NavError, walk_path
    from .combat import fight_trivial
    s = ctx.last()
    steps = fights = 0
    while steps < max_steps:
        s = ctx.last()
        if s.state.kind != "command" or s.hero == (x, y):
            return s
        if fight and fights < 12 and s.adjacent_hostiles():
            if fight_trivial(s) is not None:
                fights += 1
                continue
        r = route(x, y, s=s, names=names, allow_water=allow_water)
        path = r["path"]
        stop = len(path)
        for i, c in enumerate(path):
            if c in r["secret"] or c in r["traps"]:
                stop = i
                break
        if stop == 0:
            c = path[0]
            what = ("an undiscovered SECRET DOOR: search here (search(10)) until it shows"
                    if c in r["secret"] else "a trap on the only way: step_onto(x, y) if you mean to cross it")
            print(f"desmap.walk: next square {c} is {what}")
            return s
        chunk = path[:min(stop, 8)]
        h0 = s.hero
        try:
            s = walk_path(chunk)
        except NavError as e:
            s = ctx.last()
            if fight and fights < 12 and s.adjacent_hostiles() and fight_trivial(s) is not None:
                fights += 1
                continue
            print(f"desmap.walk: stopped — {e}")
            return ctx.last()
        steps += len(chunk)
        if s.hero == h0:
            print(f"desmap.walk: no progress at {s.hero} ({s.messages or 'no message'})")
            return s
        if s.messages and any("locked" in m for m in s.messages):
            print("desmap.walk: a locked door — unlock() it (or kick) and walk again")
            return s
    return s
