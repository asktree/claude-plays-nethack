"""Monster tracking with automatic farlook.

Each visible monster glyph gets a NetHack description ("peaceful dwarf",
"tame kitten", "jackal") via ';' the first time it appears; the description
follows the glyph as it moves (same char+color within a few squares).
Monsters that step out of view and come back within ~40 turns are
recognized as re-seen, not new. Farlook takes no game time.

Each monster dict: ch, x, y, color, pet (inverse video), dist, desc,
note (danger note), statue, new (True only the first time it is seen),
peaceful, tame.
"""

from __future__ import annotations

from .danger import note_for
from .mapscan import monsters_in_view

MAX_LOOKS_PER_UPDATE = 6
RESEEN_TURNS = 40


class MonsterTracker:
    def __init__(self, game):
        self.game = game
        self.known: list[dict] = []    # monsters visible at the previous update
        self.recent: list[dict] = []   # monsters seen recently on this level (for re-sightings)
        self.level = None

    def reset(self):
        self.known, self.recent = [], []

    @staticmethod
    def _match(m, pool, maxd):
        best = None
        for k in pool:
            if k["ch"] == m["ch"] and k["color"] == m["color"]:
                d = max(abs(k["x"] - m["x"]), abs(k["y"] - m["y"]))
                if d <= maxd and (best is None or d < best[0]):
                    best = (d, k)
        return best[1] if best else None

    def update(self, snap, allow_farlook: bool = True) -> list[dict]:
        if snap.state.kind != "command":
            return []
        st = snap.status
        lvl = st.ldesc
        if lvl != self.level:
            self.level = lvl
            self.reset()
        turn = st.turn or 0
        mons = monsters_in_view(snap)
        unclaimed = list(self.known)
        need = []
        for m in mons:
            k = self._match(m, unclaimed, 3)
            if k is not None:
                unclaimed.remove(k)
                m["desc"] = k.get("desc", "")
                m["statue"] = k.get("statue", False)
                m["new"] = False
                continue
            r = self._match(m, [x for x in self.recent if turn - x.get("turn", 0) <= RESEEN_TURNS], 8)
            if r is not None and r.get("desc"):
                m["desc"] = r["desc"]
                m["statue"] = r.get("statue", False)
                m["new"] = False
                continue
            need.append(m)
        looks = 0
        for m in sorted(need, key=lambda e: e["dist"] if e["dist"] is not None else 99):
            m["new"] = True
            if not allow_farlook or looks >= MAX_LOOKS_PER_UPDATE:
                m["desc"] = ""
                continue
            m["desc"] = _clean(self.game.farlook(m["x"], m["y"]))
            m["statue"] = "statue of" in m["desc"]
            if m["statue"]:
                m["new"] = False
            looks += 1
        xl = st.xl if st.ok else None
        for m in mons:
            d = m.get("desc", "")
            m["tame"] = d.startswith("tame ")
            m["peaceful"] = d.startswith("peaceful ")
            if d and not m.get("statue"):
                m["note"] = note_for(d, xl)
        # memory for re-sightings
        for m in mons:
            if m.get("desc"):
                self.recent = [x for x in self.recent if not (x["ch"] == m["ch"] and x["color"] == m["color"]
                                                               and abs(x["x"] - m["x"]) <= 1
                                                               and abs(x["y"] - m["y"]) <= 1)]
                self.recent.append({"ch": m["ch"], "color": m["color"], "x": m["x"], "y": m["y"],
                                    "desc": m["desc"], "statue": m.get("statue", False), "turn": turn})
        self.recent = [x for x in self.recent if turn - x.get("turn", 0) <= RESEEN_TURNS][-60:]
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
