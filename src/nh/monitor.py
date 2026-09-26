"""Monster tracking with automatic farlook.

Each visible monster glyph gets a NetHack description ("peaceful dwarf",
"tame kitten", "jackal") via ';' the first time it appears; the description
follows the glyph as it moves (same char+color within 2 squares). Farlook
takes no game time.
"""

from __future__ import annotations

from .danger import note_for
from .game import Game, Snap
from .parse import MAP_BOTTOM, MAP_TOP
from .render import monsters_in_view

MAX_LOOKS_PER_UPDATE = 5


class MonsterTracker:
    def __init__(self, game: Game):
        self.game = game
        self.known: list[dict] = []   # monsters from the previous update, with 'desc'
        self.level = None

    def reset(self):
        self.known = []

    def update(self, snap: Snap, allow_farlook: bool = True) -> list[dict]:
        if snap.state.kind != "command":
            return []
        lvl = snap.status.ldesc
        if lvl != self.level:
            self.level = lvl
            self.known = []
        mons = monsters_in_view(snap)
        unclaimed = list(self.known)
        need = []
        for m in mons:
            best = None
            for k in unclaimed:
                if k["ch"] == m["ch"] and k["color"] == m["color"]:
                    d = max(abs(k["x"] - m["x"]), abs(k["y"] - m["y"]))
                    if d <= 2 and (best is None or d < best[0]):
                        best = (d, k)
            if best is not None:
                m["desc"] = best[1].get("desc", "")
                unclaimed.remove(best[1])
            else:
                need.append(m)
        looks = 0
        for m in sorted(need, key=lambda e: e["dist"] if e["dist"] is not None else 99):
            if not allow_farlook or looks >= MAX_LOOKS_PER_UPDATE:
                m["desc"] = ""
                continue
            m["desc"] = _clean(self.game.farlook(m["x"], m["y"]))
            if m["desc"].startswith("statue of") or " statue of " in m["desc"]:
                m["statue"] = True
            looks += 1
        xl = snap.status.xl if snap.status.ok else None
        for m in mons:
            if m.get("desc") and not m.get("statue"):
                m["note"] = note_for(m["desc"], xl)
        self.known = [m for m in mons if m.get("desc")]
        return mons


def _clean(desc: str) -> str:
    """';' output looks like "f   a cat or other feline (tame kitten) [seen: normal vision]".
    Keep the specific parenthetical ("tame kitten", "peaceful dwarf",
    "statue of a grid bug") plus any unusual [seen: ...] sense."""
    import re
    d = desc.strip()
    for junk in ("(For instructions type a ?)", "Pick an object.", "--More--"):
        d = d.replace(junk, " ").strip()
    if len(d) > 2 and d[1] == " ":
        d = d[1:].strip()
    seen = ""
    m = re.search(r"\[seen: ([^\]]*)\]", d)
    if m:
        seen = m.group(1)
        d = (d[: m.start()] + d[m.end():]).strip()
    m = re.search(r"\((.*)\)\s*$", d)
    core = m.group(1).strip() if m else d
    if seen and seen not in ("normal vision", "normal vision, infravision", "infravision"):
        core += f" [seen: {seen}]"
    return core
