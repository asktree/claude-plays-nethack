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
Squares that the level file changes at random (IF [50%] { TERRAIN ... } — the
Valley's and Baalzebub's walls, Fort Ludios' secret doors, Minetown) are
"variant" squares: a group of them changes together, and one of them seen on
screen settles its whole group (variants() / show()); route() treats the
unsettled ones as uncertain (passable at a cost, re-planned once seen).
"""

from __future__ import annotations

import heapq
import json
import re
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
            _prepare(m)
    return _MAPS


def _prepare(m: dict) -> None:
    """Cells for matching, and the variant groups: m["_groups"] = [{"p", "pair", "cells": {(x, y): alt}}],
    m["_var"] = {(x, y): [group indices]}. A REPLACE_TERRAIN entry becomes one group per square."""
    rows = m["rows"]
    groups = []
    for g in m.get("variants") or []:
        if "replace" in g:
            x1, y1, x2, y2, src, dst = g["replace"]
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    if 0 <= y < len(rows) and 0 <= x < len(rows[y]) and rows[y][x] == src:
                        groups.append({"p": g["p"], "pair": None, "cells": {(x, y): dst}})
        else:
            groups.append({"p": g["p"], "pair": g.get("pair"), "cells": {(c[0], c[1]): c[2] for c in g["cells"]}})
    # ("pair" indices refer to the file's list, where a replace entry is one item: re-map them)
    remap = {}
    j = 0
    for i, g in enumerate(m.get("variants") or []):
        if "replace" in g:
            x1, y1, x2, y2, src, _dst = g["replace"]
            j += sum(1 for y in range(min(y1, y2), max(y1, y2) + 1) for x in range(min(x1, x2), max(x1, x2) + 1)
                     if 0 <= y < len(rows) and 0 <= x < len(rows[y]) and rows[y][x] == src)
        else:
            remap[i] = j
            j += 1
    for g in groups:
        if g["pair"] is not None:
            g["pair"] = remap.get(g["pair"])
    var: dict = {}
    for gi, g in enumerate(groups):
        for c in g["cells"]:
            var.setdefault(c, []).append(gi)
    m["_groups"], m["_var"] = groups, var
    m["_cells"] = [(x, y, _MAP_CLS[ch]) for y, row in enumerate(rows) for x, ch in enumerate(row)
                   if ch in _MAP_CLS and (x, y) not in var]
    # a variant square matches whichever of its possible terrains fits best
    m["_vcells"] = []
    for (x, y), gis in var.items():
        chs = {rows[y][x] if 0 <= y < len(rows) and x < len(rows[y]) else " "}
        chs |= {groups[gi]["cells"][(x, y)] for gi in gis}
        cls = tuple(sorted({_MAP_CLS[ch] for ch in chs if ch in _MAP_CLS}))
        if cls:
            m["_vcells"].append((x, y, cls))
    m["w"] = max((len(r) for r in rows), default=0)
    m["h"] = len(rows)


def _screen_cls(s) -> dict:
    """{(x, y): class} for the map cells you can read on screen (monsters/objects/blank: unknown)."""
    scr = s.screen
    out = {}
    for y in range(1, 22):
        row = scr.row(y)
        for x, ch in enumerate(row):
            col = scr.color_at(x, y)
            if ch in "-|":
                out[(x, y)] = "door" if col == BROWN else "floor" if (ch == "|" and col == 15) else "wall"
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


MIN_CELLS = 20      # smaller maps (Juiblex's 8x5 stair pockets of 'x') match any floor anywhere: never candidates


# dungeon.def: where the Dungeons of Doom's special levels can be (bigrm @ (10,3); medusa @ (-5,4) and the castle
# @ (-1,0) at the bottom of a 25-29 level dungeon). p4 shift 3 #551/#2062: ordinary DL7 and the Oracle level (DL9)
# were taken for bigrm-1, and travel() walked its map into solid rock. (The Oracle's own map isn't in the data: its
# centre is a ROOM, not a MAP.)
_DEPTHS = (("bigrm", 10, 12), ("medusa", 20, 60), ("castle", 24, 60))


def _depth_ok(level: str, key: str) -> bool:
    m = re.match(r"The Dungeons of Doom / Level (\d+)$", key or "")
    if not m:
        return True
    n = int(m.group(1))
    return all(lo <= n <= hi for pre, lo, hi in _DEPTHS if level.startswith(pre))


def _candidates(key: str, names=None) -> list:
    if names:
        want = {names} if isinstance(names, str) else set(names)
        return [m for m in maps() if m["level"] in want and _size(m) >= MIN_CELLS]
    files = next((f for pre, f in _CONTEXT if key.startswith(pre)), None)
    if key in ENDGAME:
        files = ("endgame.des",)
    return [m for m in maps() if (files is None or m["file"] in files) and _size(m) >= MIN_CELLS
            and _depth_ok(m["level"], key)]


def _size(m: dict) -> int:
    return len(m.get("_cells") or ()) + len(m.get("_vcells") or ())


_OV_HDR = re.compile(r"^(?P<name>[A-Z][A-Za-z' ]+?):(?: levels? (?P<a>\d+)(?: up)? to (?P<b>\d+))?\s*$")
_OV_LEVEL = re.compile(r"^Level (?P<n>\d+)(?::| \[)")


def _overview_sections(text: str) -> dict:
    """^O overview text -> {branch: {"a", "b", "levels": {n: [note lines]}}}, plus "_lines"."""
    out: dict = {"_lines": []}
    sec, lvl = None, None
    for raw in (text or "").splitlines():
        line = raw.strip()
        out["_lines"].append(line)
        h = _OV_HDR.match(line)
        if h and not line.startswith("Level "):
            sec = out.setdefault(h.group("name"), {"a": None, "b": None, "levels": {}})
            sec["a"] = int(h.group("a")) if h.group("a") else None
            sec["b"] = int(h.group("b")) if h.group("b") else None
            lvl = None
            continue
        lm = _OV_LEVEL.match(line)
        if lm and sec is not None:
            lvl = sec["levels"].setdefault(int(lm.group("n")), [])
            continue
        if lvl is not None:
            lvl.append(line)
    return out


def certain_level(key: str | None = None, s=None) -> str | None:
    """The .des level this level MUST be, from the dungeon's structure (nothing seen needed): the Valley (the
    first level of Gehennom, or ^O's "Valley of the Dead."), Moloch's Sanctum and the Castle (their ^O notes),
    Fort Ludios, the Planes, the three levels of Vlad's Tower (counted up from its entry: tower1 is Vlad's),
    the quest home (quest level 1) and locate level (quest level 3). None otherwise."""
    if key is None:
        s = s or ctx.last()
        key = ctx.game.level_key(s.status) if s is not None and s.status.ok else None
    if not key:
        return None
    ends = {"Earth": "earth", "Air": "air", "Fire": "fire", "Water": "water", "Astral Plane": "astral"}
    if key in ends:
        return ends[key]
    if key.startswith("Fort Ludios"):
        return "knox"
    km = re.match(r"^(?P<b>.+?) / Level (?P<n>\d+)$", key)
    if not km:
        return None
    branch, n = km.group("b"), int(km.group("n"))
    mem = getattr(ctx.game, "memory", None)
    ov = _overview_sections(((getattr(mem, "state", None) or {}).get("overview") or "") if mem is not None else "")
    sec = ov.get(branch) or {"a": None, "levels": {}}
    notes = " ".join(sec["levels"].get(n, []))
    for note, name in (("Valley of the Dead", "valley"), ("Moloch's Sanctum", "sanctum"), ("The castle", "castle")):
        if note in notes:
            return name
    if branch == "Gehennom" and sec.get("a") is not None and n == sec["a"]:
        return "valley"                       # dungeon.def: LEVEL "valley" @ (1, 0)
    inv = ((getattr(mem, "state", None) or {}).get("invoked") or {}).get("level") if mem is not None else None
    if branch == "Gehennom" and inv == f"Gehennom / Level {n - 1}":
        return "sanctum"                      # the invocation's stairs lead down into it (dungeon.def: the last level)
    if branch == "Vlad's Tower":
        # built upward from its entry (dungeon.def ENTRY -1: the bottom, tower3); ^O never numbers this branch
        # (its deepest level reached IS the entry), so the entry is the branch stairs' level, else the deepest
        # tower level listed
        a = None
        for line in ov["_lines"]:
            bm = re.search(r"to Vlad's Tower, level (\d+)", line)
            if bm:
                a = int(bm.group(1))
        if a is None and sec["levels"]:
            a = max(sec["levels"])
        if a is not None and 1 <= n - a + 3 <= 3:
            return f"tower{n - a + 3}"
    if branch == "The Quest" and n in (1, 3):
        pre = next((m["level"].split("-")[0] for m in maps() if m["file"] == "Valkyrie.des"), "Val")
        return f"{pre}-{'strt' if n == 1 else 'loca'}"
    return None


def tower_interior(s=None):
    """(x1, y1, x2, y2) screen box inside the Wizard's Tower walls on wizard1-3 (yendor.des: a 28x13 walled map,
    undiggable, no door out) once identify() has placed the level; else None."""
    s = s or ctx.last()
    if s is None or not s.status.ok:
        return None
    v = (getattr(ctx.game, "desmap_ids", None) or {}).get(ctx.game.level_key(s.status)) or {}
    if v.get("level") not in ("wizard1", "wizard2", "wizard3") or v.get("ambiguous"):
        return None
    ox, oy = v["ox"], v["oy"]
    return ox + 1, oy + 1, ox + 26, oy + 11


# *.des TELEPORT_REGION with an excluded area (map-relative): mkmaze.c fixup_special() makes it the level's
# updest/dndest, and teleport.c tele_jump_ok() then keeps a monster teleported inside it (rloc) INSIDE it and
# one outside it out (p2 shift 33 #240: a wand of teleportation only reshuffled a fake tower's monsters)
TELE_BOXES = {"wizard1": (0, 0, 27, 12), "wizard2": (0, 0, 27, 12), "wizard3": (0, 0, 27, 12),
              "fakewiz1": (2, 2, 6, 6), "fakewiz2": (2, 2, 6, 6), "castle": (1, 1, 61, 15)}


def tele_box(s=None):
    """The screen box (x1, y1, x2, y2) of this level's teleport-restricted area when desmap placed a level that
    has one (the Wizard's Tower levels, the fake towers, the Castle), else None."""
    s = s or ctx.last()
    if s is None or not s.status.ok:
        return None
    ident = (getattr(ctx.game, "desmap_ids", None) or {}).get(ctx.game.level_key(s.status)) or {}
    box = TELE_BOXES.get(ident.get("level"))
    if box is None or ident.get("ambiguous") or ident.get("ox") is None or ident.get("oy") is None:
        return None
    ox, oy = ident["ox"], ident["oy"]
    return (ox + box[0], oy + box[1], ox + box[2], oy + box[3])


def in_box(box, c) -> bool:
    return box is not None and c is not None and box[0] <= c[0] <= box[2] and box[1] <= c[1] <= box[3]


_CHAIN = {"wizard2": 1, "wizard3": 2}      # dungeon.def CHAINLEVEL: levels right below wizard1


def _depth(key: str | None):
    m = re.search(r" / Level (\d+)$", key or "")
    return int(m.group(1)) if m else None


def _chain_ok(level: str, key: str) -> bool:
    """wizard2 / wizard3 lie one / two levels below wizard1: once wizard1 is placed, only there."""
    if level not in _CHAIN:
        return True
    ids = getattr(ctx.game, "desmap_ids", None) or {}
    base = next((k for k, v in ids.items() if v.get("level") == "wizard1" and not v.get("ambiguous")), None)
    if base is None:
        return True
    bd, kd = _depth(base), _depth(key)
    return bd is None or kd is None or kd == bd + _CHAIN[level]


def _identify_certain(name: str, seen: dict):
    """The level is certainly `name`: place its (largest) map at the spot the level generator uses, unless what
    you see plainly contradicts it. None when the map has no fixed spot (slide it as usual then)."""
    cands = [m for m in maps() if m["level"] == name and _size(m) >= MIN_CELLS]
    if not cands:
        return None
    m = max(cands, key=_size)
    fo = fixed_offset(m)
    if fo is None:
        return None
    sc, good, bad = _score_at(m, seen, *fo)
    if bad >= 4 and bad * 2 > good:
        return None
    return {"level": m["level"], "index": m["index"], "ox": fo[0], "oy": fo[1], "score": sc, "good": good,
            "bad": bad, "fixed": True, "certain": True}


def _cdiv(a: int, b: int) -> int:
    """C integer division (truncates toward zero)."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


X_MAZE_MAX, Y_MAZE_MAX, ROWNO = 78, 20, 21      # decl.c: (COLNO - 1) & ~1, (ROWNO - 1) & ~1


def fixed_offset(m: dict):
    """Screen offset (ox, oy) where the level generator puts map m: sp_lev.c spo_map() places a map with a
    named GEOMETRY (left/half-left/center/half-right/right, top/center/bottom) at a fixed (xstart, ystart)
    — forced odd — and the tty shows level x in column x-1, level y in row y+1. (Checked against the
    Castle, the Valley, Juiblex's swamp, Orcus Town, Vlad's Tower and the Wizard's Tower.) None when the
    geometry isn't a named alignment."""
    geo = (m.get("geometry") or "").replace(" ", "").lower()
    if "," not in geo or "(" in geo:
        return None
    h, v = geo.split(",", 1)
    xs = m.get("w") or max((len(r) for r in m["rows"]), default=0)
    ys = m.get("h") or len(m["rows"])
    X, Y = X_MAZE_MAX, Y_MAZE_MAX
    xstart = {"left": 1 if m.get("init") else 3, "half-left": 2 + _cdiv(X - 2 - xs, 4),
              "center": 2 + _cdiv(X - 2 - xs, 2), "half-right": 2 + _cdiv((X - 2 - xs) * 3, 4),
              "right": X - xs - 1}.get(h)
    ystart = {"top": 3, "center": 2 + _cdiv(Y - 2 - ys, 2), "bottom": Y - ys - 1}.get(v)
    if xstart is None or ystart is None:
        return None
    if xstart % 2 == 0:
        xstart += 1
    if ystart % 2 == 0:
        ystart += 1
    if ystart < 0 or ystart + ys > ROWNO:
        ystart += -2 if ystart > 0 else 2
        if ys == ROWNO:
            ystart = 0
    return xstart - 1, ystart + 1


def _score_at(m: dict, seen: dict, ox: int, oy: int) -> tuple:
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
    for x, y, clss in m.get("_vcells", ()):
        sc = seen.get((x + ox, y + oy))
        if sc is None:
            continue
        v = max(_SCORE.get(sc, {}).get(cls, 0) for cls in clss)
        score += v
        if v > 0:
            good += 1
        elif v < 0:
            bad += 1
    return score, good, bad


def _best_offset(m: dict, seen: dict) -> tuple:
    """(score, ox, oy, good, bad, runner_up_score) of the best placement of map m anywhere on screen."""
    best = (-10 ** 9, 0, 0, 0, 0)
    second = -10 ** 9
    w, h = m["w"], m["h"]
    fo = fixed_offset(m)
    # a map with a named GEOMETRY sits only where the level generator puts it (p2 shift 31: wizard2 slid onto
    # a random maze at (1,1)): try that spot (and next to it, in case) only
    ys = range(max(1, fo[1] - 2), fo[1] + 3) if fo else range(1, max(2, 23 - h))
    xs = range(max(0, fo[0] - 2), fo[0] + 3) if fo else range(0, max(1, 81 - w))
    for oy in ys:
        for ox in xs:
            score, good, bad = _score_at(m, seen, ox, oy)
            if score > best[0]:
                second = max(second, best[0])
                best = (score, ox, oy, good, bad)
            elif score > second:
                second = score
    return best + (second,)


def _identify_fixed(cands: list, seen: dict):
    """The candidate map that fits what you see at the spot the level generator puts it (fixed_offset):
    a dozen matching squares are enough there (a dark level seen from a few squares), as long as no other
    map fits its own spot about as well. None otherwise (identify() then slides the maps freely)."""
    best, runner = None, -10 ** 9
    for m in cands:
        fo = fixed_offset(m)
        if fo is None:
            continue
        sc, good, bad = _score_at(m, seen, *fo)
        if best is None or sc > best["score"]:
            if best is not None and best["rows"] != m["rows"]:
                runner = max(runner, best["score"])
            best = {"level": m["level"], "index": m["index"], "ox": fo[0], "oy": fo[1], "score": sc,
                    "good": good, "bad": bad, "rows": m["rows"], "fixed": True}
        elif m["rows"] != best["rows"]:
            runner = max(runner, sc)
    if best is None or best["score"] < 12 or best["good"] < 6 or best["bad"] * 4 > best["good"] \
            or runner >= best["score"] - max(4, best["score"] // 10):
        return None
    return best


def identify(names=None, s=None, min_score: int = 30, remember: bool = True) -> dict | None:
    """Which fixed map is this level (and where on the screen)? Slides the candidate maps (by the level's
    branch, or `names` like 'valley' / ['medusa-1', 'medusa-2']) over what you have seen and returns the best
    {"level", "index", "ox", "oy", "score", "good", "bad"} — screen (x, y) = map (x + ox, y + oy) — or None
    when nothing fits well enough (see more of the level first). Remembered per level."""
    s = s or ctx.last()
    key = ctx.game.level_key(s.status)
    seen = _screen_cls(s)
    if not names:
        cert = certain_level(key, s)
        found = _identify_certain(cert, seen) if cert else None
        if found is not None:
            # (p2 shift 29 #14: a dark Valley arrival, ~9 squares seen — the level is certain, its spot fixed)
            if remember:
                store = getattr(ctx.game, "desmap_ids", None)
                if store is None:
                    ctx.game.desmap_ids = store = {}
                store[key] = found
            return found
        if cert and all(fixed_offset(m) is None for m in maps() if m["level"] == cert):
            names = cert                         # (no fixed spot: slide just that map)
    best = None
    runner = -10 ** 9
    cands = _candidates(key, names)
    if not names:
        # each special level exists once: one already placed on ANOTHER level isn't this one (p1: a wide-
        # corridor filler maze looked like Asmodeus's lair, met 6 levels up). Not for maps that repeat.
        taken = {v["level"] for k, v in (getattr(ctx.game, "desmap_ids", None) or {}).items()
                 if k != key and not v.get("ambiguous")}
        cands = [m for m in cands if m["level"] not in taken or m["level"].startswith(("fakewiz", "bigrm"))]
        cands = [m for m in cands if _chain_ok(m["level"], key)]
    fixed = _identify_fixed(cands, seen)
    if fixed is not None:
        best = fixed
    else:
        for m in cands:
            sc, ox, oy, good, bad, second = _best_offset(m, seen)
            if best is None or sc > best["score"]:
                if best is not None and (best["rows"] != m["rows"]):
                    runner = max(runner, best["score"])      # (identical maps, e.g. fakewiz1/2: not a rival)
                best = {"level": m["level"], "index": m["index"], "ox": ox, "oy": oy, "score": sc, "good": good,
                        "bad": bad, "rows": m["rows"]}
                runner = max(runner, second)
            elif m["rows"] != best["rows"]:
                runner = max(runner, sc)
        if best is None or best["score"] < min_score or best["bad"] * 4 > best["good"] \
                or (best["level"].startswith("bigrm") and best["bad"] * 10 > best["good"]):
            # (the Big Room is one open lit room: walls or rock inside it are a strong no)
            return None
    best.pop("rows", None)
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
    m = next((mm for mm in maps() if mm["level"] == found["level"] and mm["index"] == found.get("index", mm["index"])),
             None)
    if m is None:
        raise RuntimeError(f"desmap: no map {found['level']} #{found.get('index')} in the data")
    return m, found


def layout(s=None, names=None) -> dict:
    """{(x, y) screen: map char} of the identified map (variant squares: as far as settled — see variants())."""
    s = s or ctx.last()
    m, f = _current(s, names)
    lay = {(x + f["ox"], y + f["oy"]): ch for y, row in enumerate(m["rows"]) for x, ch in enumerate(row)
           if ch != "x"}
    for gi, state in enumerate(_settle(m, f, s)):
        if state:
            for (x, y), alt in m["_groups"][gi]["cells"].items():
                lay[(x + f["ox"], y + f["oy"])] = alt
    return lay


def _settle(m: dict, f: dict, s) -> list:
    """Per variant group: True (it happened: seen squares show its terrain), False (seen squares show the
    map's own), None (nothing seen that tells). An IF branch and its ELSE settle each other."""
    groups = m.get("_groups") or []
    if not groups:
        return []
    seen = _screen_cls(s)
    rows = m["rows"]
    out: list = [None] * len(groups)
    for gi, g in enumerate(groups):
        yes = no = 0
        for (x, y), alt in g["cells"].items():
            sc = seen.get((x + f["ox"], y + f["oy"]))
            if sc is None:
                continue
            base = rows[y][x] if 0 <= y < len(rows) and x < len(rows[y]) else " "
            sa = _SCORE.get(sc, {}).get(_MAP_CLS.get(alt, "stone"), 0)
            sb = _SCORE.get(sc, {}).get(_MAP_CLS.get(base, "stone"), 0)
            if sa > 0 >= sb:
                yes += 1
            elif sb > 0 >= sa:
                no += 1
        if yes or no:
            out[gi] = yes >= no
    for gi, g in enumerate(groups):
        pr = g.get("pair")
        if pr is not None and 0 <= pr < len(out) and out[gi] is None and out[pr] is not None:
            out[gi] = not out[pr]
    return out


def variants(s=None, names=None) -> list:
    """The identified map's random-terrain groups in SCREEN coordinates: [{"p", "state", "cells": {(x, y):
    (map char, alternative)}}] — state True/False once a square of the group has been seen, else None."""
    s = s or ctx.last()
    m, f = _current(s, names)
    rows = m["rows"]
    out = []
    for g, st in zip(m.get("_groups") or [], _settle(m, f, s)):
        out.append({"p": g["p"], "state": st,
                    "cells": {(x + f["ox"], y + f["oy"]): (rows[y][x] if x < len(rows[y]) else " ", alt)
                              for (x, y), alt in g["cells"].items()}})
    return out


def _uncertain(s=None, names=None) -> dict:
    """{(x, y) screen: (set of possible map chars, chance it is NOT walkable)} for variant squares not settled
    yet (a 50% wall: 0.5; a 10% sprinkled tree on floor: 0.1)."""
    s = s or ctx.last()
    out: dict = {}
    for v in variants(s, names):
        if v["state"] is not None:
            continue
        p = v["p"] / 100.0
        for c, (base, alt) in v["cells"].items():
            walk_b, walk_a = base in _WALK_CH, alt in _WALK_CH
            block = p if walk_b and not walk_a else (1 - p) if walk_a and not walk_b else 0.0
            chs, b0 = out.get(c, ({base}, 0.0))
            out[c] = (chs | {alt}, max(b0, block))
    return out


def features(s=None, names=None) -> list:
    """The map's fixed features in SCREEN coordinates: [{kind, x, y, detail}] (stairs, ladders, traps, doors
    with their state, altars, portals, branch stairs, drawbridges, named monsters' starting squares)."""
    m, f = _current(s, names)
    return [dict(ft, x=ft["x"] + f["ox"], y=ft["y"] + f["oy"]) for ft in m["features"]]


# secret doors the .des maps don't place at a fixed square: (map rectangle of the room, walls, source)
RANDOM_SDOORS = {
    "wizard1": ((12, 1, 20, 9), "south, east or west", "mkmaze.c fixup_special(): the Wizard's room"),
    "wizard3": ((20, 6, 26, 11), "north or west", "yendor.des ROOMDOOR: the portal room"),
}


def random_sdoor_hint(m: dict, f: dict) -> str:
    """'' or where an unplaced secret door of this map is (screen coordinates)."""
    r = RANDOM_SDOORS.get(m["level"])
    if not r:
        return ""
    (x1, y1, x2, y2), walls, what = r
    return (f"{what} ({x1 + f['ox']},{y1 + f['oy']})-({x2 + f['ox']},{y2 + f['oy']}) has ONE secret door at a "
            f"random spot of its {walls} wall — search along those walls (it isn't in the map)")


def show(s=None, names=None) -> str:
    """One line per feature, plus the secret doors of the map; prints and returns it."""
    s = s or ctx.last()
    m, f = _current(s, names)
    lay = layout(s, names)
    secret = sorted(c for c, ch in lay.items() if ch == "S")
    # (a placement remembered from a certain level / an older harness has no match counts: p3 shift 15 #1076)
    lines = [f"{m['level']} (map {m['index']}, from {m['file']}) at offset ({f['ox']},{f['oy']})"
             + (f", match {f['good']} good / {f['bad']} bad" if "good" in f and "bad" in f else "")]
    for ft in features(s, names):
        detail = ft["detail"] or ("a staircase or portal to another dungeon branch (overview() names it)"
                                  if ft["kind"] == "branch" else "")
        lines.append(f"  {ft['kind']:10} ({ft['x']},{ft['y']}) {detail}")
    if secret:
        lines.append(f"  secret doors: {secret[:20]}" + (" ..." if len(secret) > 20 else ""))
    groups = [v for v in variants(s, names) if len(v["cells"]) > 1 or v["p"] >= 50]
    for v in groups[:8]:
        state = {True: "HAPPENED (seen)", False: "did not happen (seen)", None: "not seen yet"}[v["state"]]
        parts = []
        for c, (base, alt) in sorted(v["cells"].items(), key=lambda kv: (kv[0][1], kv[0][0]))[:6]:
            parts.append(f"{c} {_CH_NAME.get(base, repr(base))}->{_CH_NAME.get(alt, repr(alt))}")
        lines.append(f"  random terrain ({v['p']}%, {state}): " + ", ".join(parts)
                     + (" ..." if len(v["cells"]) > 6 else ""))
    small = sum(1 for v in variants(s, names) if len(v["cells"]) == 1 and v["p"] < 50)
    if small:
        lines.append(f"  + {small} single squares that may randomly differ (trees/clouds/pools sprinkled by "
                     "the level file)")
    hint = random_sdoor_hint(m, f)
    if hint:
        lines.append(f"  note: {hint}")
    txt = "\n".join(lines)
    print(txt)
    return txt


_WALK_CH = (".", "B", "#", "+", "{", "\\", "K", "I", "S", "H")
_CH_NAME = {"-": "wall", "|": "wall", ".": "floor", "B": "floor", "S": "secret door", "+": "door", "}": "water",
            "P": "pool", "L": "lava", "T": "tree", "C": "cloud", "\\": "throne", "#": "corridor", " ": "rock",
            "F": "iron bars", "W": "water", "H": "secret corridor"}
UNCERTAIN_COST = 12      # extra steps for a variant square not settled yet, times its chance of being a wall


_STUCK_BOULDERS: dict = {}      # level key -> boulder squares a push failed at ("You try to move the boulder, but in vain.")


def _stuck_boulders(s) -> set:
    g = getattr(ctx, "game", None)
    key = g.level_key(s.status) if g is not None and hasattr(g, "level_key") and s.status.ok else None
    return {c for c in _STUCK_BOULDERS.get(key, set()) if s.screen.at(*c) == "0"}


def route(x: int, y: int, s=None, names=None, allow_water: bool = False, trap_cost: int = 30) -> dict:
    """Cheapest path from you to (x, y) over what you have seen AND the identified map (unseen and dark parts
    included). Known traps and the map's fixed traps cost `trap_cost` extra steps each (crossed only when there
    is no other way); undiscovered secret doors on it cost 20 and are listed in "secret" (search next to them
    before walking through). Variant squares not settled yet (a random 50% wall: variants()) cost a few steps
    extra and are listed in "uncertain" (walk() re-plans when it sees them). No diagonal moves into or out of
    doorways. Returns {"path", "secret", "traps", "uncertain"} or raises RuntimeError when there is no way even
    on the map."""
    from .mapview import is_door, is_walkable
    from .nav import bad_squares
    s = s or ctx.last()
    lay = layout(s, names)
    unc = _uncertain(s, names)
    hero = s.hero
    if hero is None:
        raise RuntimeError("desmap.route: where are you?")
    feats = features(s, names)
    traps = {(ft["x"], ft["y"]) for ft in feats if ft["kind"] == "trap"} | set(bad_squares(s))
    goal = (x, y)
    water_hit = [False]
    stuck = _stuck_boulders(s)

    def passable(c) -> bool:
        if c in stuck and c != goal:
            return False                         # a boulder that wouldn't move (something behind it)
        ch = lay.get(c)
        chs = unc[c][0] if c in unc else {ch}
        shown = s.screen.at(*c)
        if shown == "^" and (ch is None or ch not in ("-", "|", " ")):
            return True                          # a known trap (in the filler too): costs trap_cost below
        if shown not in " " and is_walkable(s, *c, allow_monsters=True):
            return ch not in ("-", "|") or shown not in "-|"
        if shown in "-|" and s.screen.color_at(*c) != BROWN:
            return "S" in chs                    # a secret door not found yet
        if shown == "}":
            water_hit[0] = water_hit[0] or not allow_water
            return allow_water
        if shown != " ":
            return any(v in _WALK_CH for v in chs if v) or c == goal
        if any(v is not None and v in "}PW" for v in chs) and not allow_water \
                and not any(v in _WALK_CH for v in chs if v):
            water_hit[0] = True
        return any(v in _WALK_CH for v in chs if v) or (allow_water and any(v and v in "}PW" for v in chs))

    def hidden_door(c) -> bool:
        """A secret door of the map not found yet: still drawn as wall, or not seen at all."""
        chs = unc[c][0] if c in unc else {lay.get(c)}
        return "S" in chs and (s.screen.at(*c) == " " or (s.screen.at(*c) in "-|"
                                                          and s.screen.color_at(*c) != BROWN))

    def uncertain(c) -> bool:
        return c in unc and unc[c][1] > 0 and s.screen.at(*c) == " "

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
                if (n in traps or s.screen.at(*n) == "^") and n != goal:
                    cost += trap_cost
                if hidden_door(n):
                    cost += 20
                if uncertain(n) and n != goal:
                    cost += round(UNCERTAIN_COST * unc[n][1])
                if d + cost < dist.get(n, 10 ** 9):
                    dist[n] = d + cost
                    prev[n] = p
                    heapq.heappush(pq, (d + cost, n))
    if goal not in prev:
        try:
            hint = random_sdoor_hint(*_current(s, names))
        except Exception:  # noqa: BLE001
            hint = ""
        raise RuntimeError(f"desmap.route: no way to {goal} on the map either"
                           + (f" ({hint})" if hint else "")
                           + (" (water is in the way: allow_water=True if you can cross it)" if water_hit[0]
                              else " — the way runs through ground outside the fixed map that you haven't seen "
                                   "(a maze or filler: explore() it), or through rock (dig), or it is sealed"))
    path = []
    p = goal
    while p is not None:
        path.append(p)
        p = prev[p]
    path = path[::-1][1:]
    secret = [c for c in path if hidden_door(c) and not (uncertain(c) and lay.get(c) != "S")]
    return {"path": path, "secret": secret, "traps": [c for c in path if c in traps or s.screen.at(*c) == "^"],
            "uncertain": [c for c in path if uncertain(c)]}


def walk(x: int, y: int, max_steps: int = 80, names=None, allow_water: bool = False, fight: bool = True):
    """Walk the route() to (x, y) one checked step at a time (walk_path: never onto a monster), re-planning as
    the map fills in. Stops next to an undiscovered secret door on the way (search there: search(10)), before
    a trap it would have to cross (step_onto() it on purpose), at a locked door (unlock()), or when something
    happens. fight=True: trivial hostiles next to you (combat.auto_fightable: 'trivial' threat, no passive
    attack, no danger note) are fought on the way; anything else stops the walk. Returns the final snap."""
    import contextlib
    from .nav import NavError, walk_path
    from .combat import fight_trivial, not_auto_fightable
    mf = getattr(ctx, "monster_filter", None)
    # (like travel's auto_fight: trivial newcomers don't pause, they get fought when they come next to you)
    with (mf(not_auto_fightable) if fight and mf is not None else contextlib.nullcontext()):
        return _walk(x, y, max_steps, names, allow_water, fight, NavError, walk_path, fight_trivial)


def _peaceful_on(s, cells) -> list:
    """Peaceful (not tame) monsters standing on any of `cells`."""
    cells = set(map(tuple, cells))
    return [m for m in s.monsters or [] if m.get("peaceful") and not m.get("tame") and not m.get("pet")
            and (m["x"], m["y"]) in cells]


def _let_pass(s, blk, target, chunk, walk_path, NavError):
    """Step aside from the peaceful(s) `blk` (nav._refuge: a free square next to you, away from them) and wait up
    to 3 turns for the planned squares to clear. Returns the final snap."""
    from .benign import BENIGN
    from .nav import _mdesc, _refuge
    ref = _refuge(s, blk, target)
    if ref is not None:
        print(f"desmap.walk: {_mdesc(blk)} blocks the way — stepping back to {ref} to let it pass")
        try:
            s = walk_path([ref])
        except NavError:
            s = ctx.last()
    else:
        print(f"desmap.walk: {_mdesc(blk)} blocks the way — waiting for it")
    for _w in range(3):
        if s.state.kind != "command" or not _peaceful_on(s, chunk):
            break
        s = ctx.do(".", ok=BENIGN)
    return s


def _walk(x, y, max_steps, names, allow_water, fight, NavError, walk_path, fight_trivial):
    s = ctx.last()
    steps = fights = opened = backoffs = pit_tries = 0
    stuck_at = None                      # the boulder this walk found immovable (re-planned around once)
    while steps < max_steps:
        s = ctx.last()
        if s.state.kind != "command" or s.hero == (x, y):
            return s
        adj = s.adjacent_hostiles()
        if adj:
            if fight and fights < 12 and fight_trivial(s) is not None:
                fights += 1
                continue
            # a hostile that isn't trivial (or fight=False): never walk on beside it (QA round 7: two more
            # steps with a master lich next to you)
            print("desmap.walk: stopped — " + ", ".join(f"{m.get('desc') or m['ch']} at ({m['x']},{m['y']})"
                                                         for m in adj[:3])
                  + " next to you (not a trivial one): fight it or get away yourself, then walk again")
            return s
        try:
            r = route(x, y, s=s, names=names, allow_water=allow_water)
        except RuntimeError as e:
            if stuck_at is None:
                raise
            raise NavError(f"desmap.walk: the boulder at {stuck_at} won't move (something behind it) and there "
                           f"is no way around it ({e}) — dig/force-fight it apart, or another way") from None
        path = r["path"]
        stop = len(path)
        for i, c in enumerate(path):
            if c in r["secret"] or c in r["traps"] or (i > 0 and c in r.get("uncertain", ())):
                stop = i                      # (an unsettled 50% wall: walk up to it — seen, it settles)
                break
        if stop == 0:
            c = path[0]
            what = ("an undiscovered SECRET DOOR: search here (search(10)) until it shows"
                    if c in r["secret"] else "a trap on the only way: step_onto(x, y) if you mean to cross it")
            print(f"desmap.walk: next square {c} is {what}")
            return s
        chunk = path[:min(stop, 8)]
        h0 = s.hero
        from .nav import lurk_on_leg, lurk_pause
        hits = lurk_on_leg(s, h0, chunk[-1], path=chunk)
        if hits:
            lurk_pause("desmap.walk", hits, h0, chunk[-1])
            s = ctx.last()
            if s.state.kind != "command":
                return s
            continue
        try:
            s = walk_path(chunk)
        except NavError as e:
            s = ctx.last()
            if fight and fights < 12 and s.adjacent_hostiles() and fight_trivial(s) is not None:
                fights += 1
                continue
            if backoffs < 2 and s.state.kind == "command" and _peaceful_on(s, chunk):
                # (walk_path already waited 3 turns) a peaceful in a 1-wide corridor (p2 shift 31: a dwarf lord
                # in Vlad's Tower): like travel(), step back so it can come out, wait for it, then re-plan
                backoffs += 1
                s = _let_pass(s, _peaceful_on(s, chunk), (x, y), chunk, walk_path, NavError)
                continue
            print(f"desmap.walk: stopped — {e}")
            return ctx.last()
        steps += len(chunk)
        if s.hero == h0:
            if any("door opens" in m for m in s.messages or []) and opened < 4:
                opened += 1
                continue                         # the step opened a door in the way: walk on through it
            from .nav import _in_pit, _pet_in_way
            if _pet_in_way(s.messages) and pit_tries < 10:
                # "You stop.  Your dog is in the way!" (live shift 4 #138: a retry worked) — try again
                pit_tries += 1
                continue
            if _in_pit(s.messages) and pit_tries < 10:
                # trap.c climb_pit(): climbing out takes a few turns (p1 shift 39 #606: one "You are still in a
                # pit." ended the walk; travel() keeps climbing too)
                pit_tries += 1
                continue
            if any(re.search(r"You try to move the boulder, but in vain|Perhaps that's why you cannot move "
                             r"past it|You don't have enough leverage to push", m) for m in s.messages or []) \
                    and chunk and s.status.ok:
                # (p1 shift 36 #546: 18 walks in a row pushed the same immovable boulder while fire giants
                # zapped) — never that square again while the boulder is there: re-plan around it, or say so
                b = tuple(chunk[0])
                key = ctx.game.level_key(s.status)
                if b not in _STUCK_BOULDERS.setdefault(key, set()):
                    _STUCK_BOULDERS[key].add(b)
                    stuck_at = b
                    print(f"desmap.walk: the boulder at {b} won't move — re-planning around it")
                    continue
                raise NavError(f"desmap.walk: the boulder at {b} won't move (something behind it) and the "
                               "fixed map has no way around it — dig/force-fight it apart, or another way")
            print(f"desmap.walk: no progress at {s.hero} ({s.messages or 'no message'})")
            return s
        if s.messages and any("locked" in m for m in s.messages):
            print("desmap.walk: a locked door — unlock() it (or kick) and walk again")
            return s
    return s
