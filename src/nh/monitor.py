"""Monster tracking with automatic farlook.

Each visible monster gets a NetHack description ("peaceful dwarf", "tame
kitten", "jackal") read with ';' (several at once through getpos
autodescribe), and an id that follows it while it stays in view.

Identity is carried from one update to the next only when it is
unambiguous. Monsters are matched per glyph+colour within a radius that
grows with the turns elapsed; matches form clusters, and a cluster is
trusted without looking only if its previous members all had the same
description and no extra monster appeared in it. Otherwise (a werejackal
next to the jackals it summoned; peaceful and hostile gnomes side by side;
a newcomer beside a known monster) every member is looked at again.

A monster that comes back into view within ~40 turns is recognised as
re-seen, but a remembered *peaceful* identity is re-checked with a look
first: a hostile dwarf must never inherit a peaceful dwarf's label. Pets
(highlighted) keep their tame label.

Each monster dict: id, ch, x, y, color, pet (inverse video), dist, desc,
note (danger note), statue, new (True only the first time it is seen),
peaceful, tame.
"""

from __future__ import annotations

import re

from .danger import note_for
from .mapscan import monsters_in_view

MAX_LOOKS_PER_UPDATE = 8
RESEEN_TURNS = 40
RESEEN_DIST = 8


def _cheb(a, b) -> int:
    return max(abs(a["x"] - b["x"]), abs(a["y"] - b["y"]))


def _friendly(desc: str) -> bool:
    return desc.startswith("peaceful ") or desc.startswith("tame ")


class MonsterTracker:
    def __init__(self, game):
        self.game = game
        self.known: list[dict] = []        # monsters visible at the previous update
        self.recent: dict[int, dict] = {}  # id -> last sighting, for monsters seen recently on this level
        self.level = None
        self.next_id = 1
        self.last_turn: int | None = None
        self.visible_ids: set[int] = set()

    def reset(self):
        self.known, self.recent = [], {}
        self.visible_ids = set()

    def gone(self, turn: int | None = None) -> list[dict]:
        """Monsters seen recently on this level that are not in view now:
        [{id, ch, color, x, y, desc, turn}] (last known position and turn)."""
        out = [dict(r) for i, r in self.recent.items() if i not in self.visible_ids]
        if turn is not None:
            out = [r for r in out if turn - r.get("turn", 0) <= RESEEN_TURNS]
        return sorted(out, key=lambda r: -r.get("turn", 0))

    def _new_id(self) -> int:
        i = self.next_id
        self.next_id += 1
        return i

    @staticmethod
    def _clusters(members: list[dict], cands: list[dict], radius: int) -> list[tuple[list, list]]:
        """Connected components of the 'within radius' graph between this
        update's monsters and the previous update's (same glyph+colour)."""
        nodes = [("m", i) for i in range(len(members))] + [("k", i) for i in range(len(cands))]
        parent = {n: n for n in nodes}

        def find(n):
            while parent[n] != n:
                parent[n] = parent[parent[n]]
                n = parent[n]
            return n

        for i, m in enumerate(members):
            for j, k in enumerate(cands):
                if _cheb(m, k) <= radius:
                    parent[find(("m", i))] = find(("k", j))
        comps: dict = {}
        for n in nodes:
            comps.setdefault(find(n), ([], []))
            (comps[find(n)][0] if n[0] == "m" else comps[find(n)][1]).append(
                members[n[1]] if n[0] == "m" else cands[n[1]])
        return list(comps.values())

    def update(self, snap, allow_farlook: bool = True) -> list[dict]:
        if snap.state.kind != "command" or not snap.status.ok:
            return []
        st = snap.status
        if st.ldesc != self.level:
            self.level = st.ldesc
            self.reset()
            self.last_turn = None
        turn = st.turn or 0
        dt = 1 if self.last_turn is None else max(1, turn - self.last_turn)
        radius = min(10, max(3, 2 * dt + 1))
        mons = monsters_in_view(snap)
        for m in mons:
            m.update(id=None, desc="", new=False, statue=False)

        groups: dict = {}
        for m in mons:
            groups.setdefault((m["ch"], m["color"]), ([], []))[0].append(m)
        for k in self.known:
            if (k["ch"], k["color"]) in groups:
                groups[(k["ch"], k["color"])][1].append(k)

        claimed: set[int] = set()
        undecided: list[tuple[list, list]] = []   # clusters to resolve after looking
        loners: list[dict] = []                   # no previous monster nearby
        for members, cands in groups.values():
            for mc, kc in self._clusters(members, cands, radius):
                if not mc:
                    continue
                if not kc:
                    loners.extend(mc)
                    continue
                claimed.update(k["id"] for k in kc)
                descs = {k.get("desc", "") for k in kc}
                if len(descs) == 1 and len(mc) <= len(kc) and "" not in descs:
                    # unambiguous: everyone here is what was here before
                    free = list(kc)
                    for m in sorted(mc, key=lambda e: min(_cheb(e, k) for k in kc)):
                        k = min(free, key=lambda c: _cheb(m, c))
                        free.remove(k)
                        m.update(id=k["id"], desc=k["desc"], statue=k.get("statue", False))
                else:
                    undecided.append((mc, kc))

        # re-sightings and newcomers
        to_look: list[dict] = [m for mc, _ in undecided for m in mc]
        resight: dict[int, list[dict]] = {}      # id(m) -> candidate records
        for m in loners:
            recs = [r for i, r in self.recent.items()
                    if i not in claimed and r["ch"] == m["ch"] and r["color"] == m["color"]
                    and turn - r.get("turn", 0) <= RESEEN_TURNS and _cheb(m, r) <= RESEEN_DIST
                    and r.get("desc")]
            if recs:
                resight[id(m)] = recs
            descs = {r["desc"] for r in recs}
            if m.get("pet") and any(d.startswith("tame ") for d in descs):
                r = min((r for r in recs if r["desc"].startswith("tame ")), key=lambda r: _cheb(m, r))
                m.update(id=r["id"], desc=r["desc"])
                claimed.add(r["id"])
            elif recs and all(r.get("statue") and (r["x"], r["y"]) == (m["x"], m["y"]) for r in recs):
                r = recs[0]
                m.update(id=r["id"], desc=r["desc"], statue=True)
                claimed.add(r["id"])
            elif len(descs) == 1 and not _friendly(next(iter(descs))):
                # re-seen hostile: keep the label (a wrong 'hostile' label is the safe mistake)
                r = min(recs, key=lambda r: _cheb(m, r))
                m.update(id=r["id"], desc=r["desc"])
                claimed.add(r["id"])
            else:
                to_look.append(m)

        # look (closest first)
        looked: set[int] = set()
        if to_look:
            to_look.sort(key=lambda e: e["dist"] if e["dist"] is not None else 99)
            batch = to_look[:MAX_LOOKS_PER_UPDATE] if allow_farlook else []
            descs = self._describe([(m["x"], m["y"]) for m in batch]) if batch else {}
            for m in batch:
                d = descs.get((m["x"], m["y"]))
                if d:
                    m["desc"] = d
                    m["statue"] = "statue of" in d
                    looked.add(id(m))

        # resolve ambiguous clusters: previous identities go to the nearest
        # member with the same description; members left over are new
        for mc, kc in undecided:
            members = [m for m in mc if id(m) in looked]
            for k in sorted(kc, key=lambda k: min((_cheb(m, k) for m in mc), default=99)):
                same = [m for m in members if m["id"] is None and m["desc"] == k.get("desc")]
                if same:
                    m = min(same, key=lambda e: _cheb(e, k))
                    m["id"] = k["id"]
            for m in mc:
                if id(m) not in looked:
                    # over the look budget: borrow the nearest previous description
                    # (unconfirmed; it gets looked at on a later update)
                    k = min(kc, key=lambda c: _cheb(m, c))
                    m.update(desc=k.get("desc", ""), statue=k.get("statue", False))
                elif m["id"] is None:
                    m["new"] = not m.get("statue")

        for m in loners:
            if m["id"] is not None:
                continue
            recs = resight.get(id(m), [])
            same = [r for r in recs if r["desc"] == m["desc"] and r["id"] not in claimed]
            if m["desc"] and same:
                r = min(same, key=lambda r: _cheb(m, r))
                m["id"] = r["id"]
                claimed.add(r["id"])
            else:
                m["new"] = not m.get("statue")

        xl = st.xl if st.ok else None
        for m in mons:
            if m["id"] is None:
                m["id"] = self._new_id()
            d = m.get("desc", "")
            m["tame"] = d.startswith("tame ")
            m["peaceful"] = d.startswith("peaceful ")
            if d and not m.get("statue"):
                m["note"] = note_for(d, xl)

        for m in mons:
            if m.get("desc"):
                self.recent[m["id"]] = {"id": m["id"], "ch": m["ch"], "color": m["color"], "x": m["x"],
                                        "y": m["y"], "desc": m["desc"], "statue": m.get("statue", False),
                                        "turn": turn}
        self.visible_ids = {m["id"] for m in mons}
        stale = [i for i, r in self.recent.items()
                 if i not in self.visible_ids and turn - r.get("turn", 0) > RESEEN_TURNS]
        for i in stale:
            del self.recent[i]
        if len(self.recent) > 80:
            for i in sorted(self.recent, key=lambda i: self.recent[i].get("turn", 0))[: len(self.recent) - 80]:
                del self.recent[i]
        self.known = [m for m in mons if m.get("desc")]
        self.last_turn = turn
        return mons

    def _describe(self, cells: list[tuple[int, int]]) -> dict:
        fn = getattr(self.game, "describe_cells", None)
        if fn is not None:
            raw = fn(cells)
        else:
            raw = {c: self.game.farlook(*c) for c in cells}
        return {c: _clean(d) for c, d in raw.items() if d and _clean(d)}


def _clean(desc: str) -> str:
    """';' output looks like "f   a cat or other feline (tame kitten) [seen: normal vision]";
    getpos autodescribe shows just "tame kitten". Keep the specific
    parenthetical ("tame kitten", "peaceful dwarf", "statue of a grid bug")
    plus any unusual [seen: ...] sense."""
    d = desc.strip()
    for junk in ("(For instructions type a ?)", "Pick an object.", "--More--", "(illegal)", "(no travel path)"):
        d = d.replace(junk, " ").strip()
    if len(d) > 2 and d[1] == " " and not d[0].isalpha():
        d = d[1:].strip()
    elif len(d) > 2 and d[1] == " " and d[0].isalpha() and re.match(r"^\w\s{2,}", d):
        d = d[1:].strip()     # a letter glyph followed by the column gap
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
