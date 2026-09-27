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


_ON_FLOOR = set(".") | set(OBJECT_CLASSES) | set(MONSTER_CHARS) | {"@"}


def _door_like(scr, x, y) -> bool:
    """A brown '+' is a closed door unless it lies out in the open: a door
    sits in a wall line, so at most two of its four sides (room / corridor
    side) are floor; a spellbook on a room floor has three or four floor
    sides (things lying or standing there count as floor). A door at a
    corridor end whose walls you haven't seen yet ('#' / blank beside it)
    stays a door (p2 shift 4: that one was taken for a book and explore()
    kept bumping into it)."""
    floorish = sum(1 for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))
                   if scr.at(x + dx, y + dy) in _ON_FLOOR and not (dx == dy == 0))
    return floorish <= 2


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
            if ch not in MONSTER_CHARS and ch != "]":
                continue
            if hero and (x, y) == hero:
                continue
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
    for y in _rows(snap):
        row = scr.row(y)
        for x, ch in enumerate(row):
            if ch not in OBJECT_CLASSES:
                continue
            col = scr.color_at(x, y)
            if ch == "+" and col == BROWN and _door_like(scr, x, y):
                continue  # a door, not a spellbook
            if ch == '"' and col in (7, 8):
                kind = "web?"
            elif ch == "0" and col in (6, 14):
                kind = "iron ball"          # heavy iron ball (cyan); boulders are gray
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
    for y in _rows(snap):
        row = scr.row(y)
        for x, ch in enumerate(row):
            name = FEATURES.get(ch)
            col = scr.color_at(x, y)
            if name is None:
                if ch == "+" and col == BROWN and _door_like(scr, x, y):
                    name = "closed door"
                elif ch in "|-" and col == BROWN:
                    name = "open door"
                elif ch == "#" and col == 2:
                    name = "tree"
                elif ch == "#" and col == 6:
                    name = "iron bars"
                else:
                    continue
            if ch == "}":
                name = "lava" if col in (1, 9) else "water"
            d = max(abs(x - hero[0]), abs(y - hero[1])) if hero else None
            out.append({"ch": ch, "x": x, "y": y, "name": name, "dist": d,
                        "color": COLOR_NAMES[col] if 0 <= col < 16 else str(col)})
    under = getattr(snap, "under", None)
    if under and hero and FEATURES.get(under):
        out.append({"ch": under, "x": hero[0], "y": hero[1], "name": FEATURES[under] + " (under you)",
                    "dist": 0, "color": ""})
    out.sort(key=lambda e: (e["dist"] if e["dist"] is not None else 99, e["y"], e["x"]))
    return out
