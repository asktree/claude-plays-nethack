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


def _hero(snap, hero):
    return snap.hero or hero


def _rows(snap):
    """Map rows not covered by a wrapped message."""
    return range(MAP_TOP + getattr(snap.state, "msg_rows", 0), MAP_BOTTOM + 1)


def monsters_in_view(snap, radius: int | None = None, hero=None) -> list[dict]:
    """Letters on the map other than the hero, with color and pet highlight.
    Only meaningful when no menu/text window overlays the map."""
    if snap.state.kind not in NO_OVERLAY:
        return []
    scr = snap.screen
    hero = _hero(snap, hero)
    res = []
    for y in _rows(snap):
        row = scr.row(y)
        for x, ch in enumerate(row):
            if ch not in MONSTER_CHARS:
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
    if snap.state.kind not in NO_OVERLAY:
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
            if ch == "+" and col == BROWN:
                continue  # a door, not a spellbook
            if ch == '"' and col in (7, 8):
                kind = "web?"
            else:
                kind = OBJECT_CLASSES[ch]
            d = max(abs(x - hero[0]), abs(y - hero[1])) if hero else None
            out.append({"ch": ch, "x": x, "y": y, "kind": kind, "pile": scr.reverse_at(x, y),
                        "color": COLOR_NAMES[col] if 0 <= col < 16 else str(col), "dist": d})
    out.sort(key=lambda e: (e["dist"] if e["dist"] is not None else 99, e["y"], e["x"]))
    return out


def features_in_view(snap, hero=None) -> list[dict]:
    if snap.state.kind not in NO_OVERLAY:
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
                if ch == "+" and col == BROWN:
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
    out.sort(key=lambda e: (e["dist"] if e["dist"] is not None else 99, e["y"], e["x"]))
    return out
