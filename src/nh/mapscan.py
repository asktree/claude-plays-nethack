"""Pure scans of the map area of a snapshot: monsters, objects, features."""

from __future__ import annotations

from .parse import MAP_BOTTOM, MAP_TOP, MONSTER_CHARS
from .screen import COLOR_NAMES

OBJECT_CLASSES = {
    ")": "weapon", "[": "armor", "%": "food", "?": "scroll", "/": "wand", "=": "ring",
    "!": "potion", '"': "amulet/web", "(": "tool", "*": "gem/rock", "$": "gold",
    "`": "boulder/stone", "0": "boulder", "+": "spellbook",
}
FEATURES = {
    "<": "up stairs", ">": "down stairs", "{": "fountain", "_": "altar", "\\": "throne",
    "^": "trap", "}": "water/lava",
}
BROWN = 3
NO_OVERLAY = ("command", "yn", "direction", "object", "getlin", "extcmd", "count", "getpos")
# drawing.c defsyms: what a '^' of each colour can be
TRAP_BY_COLOR = {
    6: "arrow/dart/bear trap", 7: "falling rock/rolling boulder/statue trap", 3: "squeaky board/hole/trap door",
    1: "land mine", 12: "sleeping gas/magic trap/anti-magic field", 4: "rust trap", 9: "fire trap",
    0: "pit/spiked pit", 8: "pit/spiked pit", 5: "teleportation trap/level teleporter", 13: "magic portal",
    10: "polymorph trap",
}
VIBRATING_SQUARE_COLOR = 5     # a magenta '~' (a long worm's tail is brown)
# the Rogue level (drawing.c init_r_symbols): no colours; stairs up AND down are '%', every door is a
# doorless doorway '+', food ':', amulets ',', armor ']', gold and gems '*', boulders '`'
ROGUE_OBJECTS = {")": "weapon", "]": "armor", ":": "food", "?": "scroll", "/": "wand", "=": "ring", "!": "potion",
                 ",": "amulet", "(": "tool", "*": "gold/gem", "`": "boulder", "+": "spellbook"}
# remembered features (Game.terrain_seen / Snap.feature_mem) by their glyph
MEM_NAMES = {"<": "up stairs", ">": "down stairs", "{": "fountain", "_": "altar", "\\": "throne",
             "^": "magic portal", "~": "vibrating square"}


_ON_FLOOR = set(".") | set(OBJECT_CLASSES) | set(MONSTER_CHARS) | {"@"}


def _door_like(scr, x, y) -> bool:
    """A brown '+' is a closed door unless it lies out in the open: a door
    sits in a wall line, so at most two of its four sides (room / corridor
    side) are floor; a spellbook on a room floor has three or four floor
    sides (things lying or standing there count as floor). A door at a
    corridor end whose walls you haven't seen yet ('#' / blank beside it)
    stays a door (p2 shift 4: that one was taken for a book and explore()
    kept bumping into it)."""
    wall = "|-+"
    if (scr.at(x - 1, y) in wall and scr.at(x + 1, y) in wall) or \
            (scr.at(x, y - 1) in wall and scr.at(x, y + 1) in wall):
        return True              # in a wall line (a book in a room corner has walls on two ADJACENT sides)
    floorish = sum(1 for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))
                   if scr.at(x + dx, y + dy) in _ON_FLOOR and not (dx == dy == 0))
    return floorish <= 1


def _hero(snap, hero):
    return snap.hero or hero


def _rows(snap):
    """Map rows not covered by a wrapped message."""
    return range(MAP_TOP + getattr(snap.state, "msg_rows", 0), MAP_BOTTOM + 1)


def monsters_in_view(snap, radius: int | None = None, hero=None) -> list[dict]:
    """Letters on the map other than the hero, with color and pet highlight,
    plus ']' (in 3.6 only a mimic posing as a "strange object" looks like
    that). Only meaningful when no menu/text window overlays the map."""
    if snap.state.kind not in NO_OVERLAY or getattr(snap, "engulfed", False):
        return []
    scr = snap.screen
    hero = _hero(snap, hero)
    res = []
    for y in _rows(snap):
        row = scr.row(y)
        for x, ch in enumerate(row):
            if ch not in MONSTER_CHARS and (ch != "]" or getattr(snap, "rogue", False)):
                continue
            if hero and (x, y) == hero:
                continue
            if ch == "~" and scr.color_at(x, y) == VIBRATING_SQUARE_COLOR:
                continue          # the vibrating square, not a worm tail
            d = max(abs(x - hero[0]), abs(y - hero[1])) if hero else None
            if radius is not None and d is not None and d > radius:
                continue
            col = scr.color_at(x, y)
            res.append({"ch": ch, "x": x, "y": y,
                        "color": COLOR_NAMES[col] if 0 <= col < 16 else str(col),
                        "pet": scr.reverse_at(x, y), "dist": d})
    res.sort(key=lambda e: (e["dist"] if e["dist"] is not None else 99, e["y"], e["x"]))
    return res


def objects_in_view(snap, hero=None) -> list[dict]:
    """Object glyphs on the map (what the game displays: the top item of a
    pile; piles are shown in inverse video with hilite_pile)."""
    if snap.state.kind not in NO_OVERLAY or getattr(snap, "engulfed", False):
        return []
    scr = snap.screen
    hero = _hero(snap, hero)
    out = []
    rogue = getattr(snap, "rogue", False)
    for y in _rows(snap):
        row = scr.row(y)
        for x, ch in enumerate(row):
            if rogue:
                if ch not in ROGUE_OBJECTS or (ch == "+" and _door_like(scr, x, y)) \
                        or (hero and (x, y) == hero):
                    continue
                if ch == ":" and any((m["x"], m["y"]) == (x, y) for m in snap.monsters or []):
                    continue          # a ':' the monster tracker kept is a lizard/newt, not food
                d = max(abs(x - hero[0]), abs(y - hero[1])) if hero else None
                out.append({"ch": ch, "x": x, "y": y, "kind": ROGUE_OBJECTS[ch], "pile": False, "color": "",
                            "dist": d})
                continue
            if ch not in OBJECT_CLASSES:
                continue
            col = scr.color_at(x, y)
            if ch == "+" and col == BROWN and _door_like(scr, x, y):
                continue  # a door, not a spellbook
            if ch == '"' and col in (7, 8):
                kind = "web?"
            elif ch == "0" and col in (6, 14):
                kind = "iron ball"          # heavy iron ball (cyan); boulders are gray
            elif ch == "*" and col == 7:
                kind = "rock/gray stone"    # gems and glass are coloured; gray '*' is a rock or a gray
                                            # stone (luck/load/touchstone, flint: kick before picking up)
            elif ch == "*":
                kind = "gem/glass"
            else:
                kind = OBJECT_CLASSES[ch]
            d = max(abs(x - hero[0]), abs(y - hero[1])) if hero else None
            out.append({"ch": ch, "x": x, "y": y, "kind": kind, "pile": scr.reverse_at(x, y),
                        "color": COLOR_NAMES[col] if 0 <= col < 16 else str(col), "dist": d})
    out.sort(key=lambda e: (e["dist"] if e["dist"] is not None else 99, e["y"], e["x"]))
    return out


def features_in_view(snap, hero=None) -> list[dict]:
    if snap.state.kind not in NO_OVERLAY or getattr(snap, "engulfed", False):
        return []
    scr = snap.screen
    hero = _hero(snap, hero)
    out = []
    rogue = getattr(snap, "rogue", False)
    fmem = getattr(snap, "feature_mem", None) or {}
    for y in _rows(snap):
        row = scr.row(y)
        for x, ch in enumerate(row):
            name = FEATURES.get(ch)
            col = scr.color_at(x, y)
            if rogue and ch in "%+^":
                if ch == "+" and _door_like(scr, x, y):
                    name = "doorway"
                elif ch == "%":
                    known = fmem.get((x, y))
                    name = (MEM_NAMES[known] + " (shown as %)" if known in ("<", ">") else
                            "stairs, up or down (Rogue level '%': not looked at yet)")
                elif ch == "^":
                    name = "trap (no colours on the Rogue level)"
                else:
                    continue
                desc = (getattr(snap, "feature_desc", None) or {}).get((x, y))
                if desc and ch == "^":
                    name = desc
                d = max(abs(x - hero[0]), abs(y - hero[1])) if hero else None
                out.append({"ch": ch, "x": x, "y": y, "name": name, "dist": d, "color": ""})
                continue
            if name is None:
                if ch == "+" and col == BROWN and _door_like(scr, x, y):
                    name = "closed door"
                elif ch in "|-" and col == BROWN:
                    name = "open door"
                elif ch == "#" and col == 2:
                    name = "tree"
                elif ch == "#" and col == 6:
                    name = "iron bars"
                elif ch == "#" and col == BROWN:
                    name = "raised drawbridge"
                elif ch == "." and col == BROWN:
                    name = "lowered drawbridge (never stand on it or in its gate when it may be raised)"
                elif ch == "~" and col == VIBRATING_SQUARE_COLOR:
                    name = "vibrating square"
                else:
                    continue
            if ch == "}":
                name = "lava" if col in (1, 9) else "water"
            if ch == "^":
                name = TRAP_BY_COLOR.get(col, "trap")
                if col not in (1, 4, 9, 10, 13):
                    name = "trap: " + name
            desc = (getattr(snap, "feature_desc", None) or {}).get((x, y))
            if desc and ch in "^_\"":
                name = desc
            d = max(abs(x - hero[0]), abs(y - hero[1])) if hero else None
            out.append({"ch": ch, "x": x, "y": y, "name": name, "dist": d,
                        "color": COLOR_NAMES[col] if 0 <= col < 16 else str(col)})
    under = getattr(snap, "under", None)
    fdesc = getattr(snap, "feature_desc", None) or {}
    if under and hero and MEM_NAMES.get(under):
        name = fdesc.get(hero) if under == "_" and fdesc.get(hero) else MEM_NAMES[under]
        out.append({"ch": under, "x": hero[0], "y": hero[1], "name": name + " (under you)",
                    "dist": 0, "color": ""})
    # remembered features the map doesn't show now: under an object or a monster (stairs under a
    # scroll, an altar under its priest), or a magic portal on the Planes of Air/Water (no map memory)
    shown = {(f["x"], f["y"]) for f in out}
    top = MAP_TOP + getattr(snap.state, "msg_rows", 0)
    for (x, y), ch in (getattr(snap, "feature_mem", None) or {}).items():
        if (x, y) in shown or (hero and (x, y) == hero) or ch not in MEM_NAMES or not top <= y <= MAP_BOTTOM:
            continue
        now = scr.at(x, y)
        if now == ch or (getattr(snap, "rogue", False) and now == "%" and ch in "<>"):
            continue                      # shown as itself (listed above, or not a feature by colour)
        why = ("under a monster" if now in MONSTER_CHARS or now in "I@" else
               "under an object" if now in OBJECT_CLASSES else "remembered")
        name = fdesc.get((x, y)) if ch == "_" and fdesc.get((x, y)) else MEM_NAMES[ch]
        if ch == "_":
            # a temple priest standing on its altar names the altar's god ("high priest of Tyr")
            import re as _re
            pri = next((m.get("desc") for m in getattr(snap, "monsters", None) or []
                        if (m["x"], m["y"]) == (x, y) and _re.search(r"priest(?:ess)? of ", m.get("desc") or "")), None)
            if pri:
                why += f": its priest ({pri.split(' of ', 1)[1]}'s) stands on it"
        d = max(abs(x - hero[0]), abs(y - hero[1])) if hero else None
        out.append({"ch": ch, "x": x, "y": y, "name": f"{name} ({why})", "dist": d, "color": ""})
    out.sort(key=lambda e: (e["dist"] if e["dist"] is not None else 99, e["y"], e["x"]))
    return out
