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

from .danger import base_name, note_for, risky_lookalike
from .mapscan import monsters_in_view

MAX_LOOKS_PER_UPDATE = 12
RESEEN_TURNS = 150     # a hostile re-entering view this soon and this near keeps its label...
RESEEN_DIST = 12       # ...unless a dangerous species looks just like it (danger.risky_lookalike)
SAME_SQUARE_TURNS = 2000   # ...and one back on the very square it was last seen on, for this long
VAMP_WOLF_NOTE = ("down here a wolf may be a shape-shifted VAMPIRE LORD (or Vlad): killing this form raises "
                  "the vampire at full HP next to you (level-drain bite)")
RETURN_TURNS = 600     # a looked-at monster back in view FAR from its last sighting: the same species seen
                       # on this level this recently (and out of view now) is taken to be it (no "new" again)


_KILL_RES = [
    re.compile(r"^You (?:kill|destroy) (?:the |an? |poor )?(?P<n>.+?)!$"),
    re.compile(r"^(?:The |An? )?(?P<n>.+?) (?:is|are) (?:killed|destroyed)!"),
    re.compile(r"^(?:The |An? )?(?P<n>.+?) dies!"),
    re.compile(r"^(?:The |Your |An? )?.+? (?:kills|destroys) (?:the |an? )?(?P<n>.+?)[.!]$"),
]


def killed_names(messages) -> list[str]:
    """Monster names reported killed in these messages ("You kill the
    jackal!", "The kitten kills the newt.", "The gnome is killed!")."""
    from .danger import base_name
    out = []
    for msg in messages or []:
        for rx in _KILL_RES:
            m = rx.search(msg)
            if m and m.group("n") not in ("it", "them"):
                out.append(base_name(m.group("n")))
                break
    return out


# makemon.c grow_up(): "Your kitten grows up into a housecat.", "The gnome becomes a
# gnome lord.", "The gnome changes into a male gnome lord."
_GROW_RE = re.compile(r"^(?P<the>Your |The )?(?P<old>.+?) (?:grows up into|becomes|changes into) "
                      r"an? (?:male |female )?(?P<new>[a-z][a-z' -]*?)\.$")


def _stationary(desc: str) -> bool:
    """Monsters that never move (molds, lichens are slow but move): remember
    them at their square for the whole visit to the level."""
    from .danger import base_name, monster_record
    rec = monster_record(base_name(desc)) if desc else None
    return bool(rec) and rec.get("speed", 1) == 0


def _cheb(a, b) -> int:
    return max(abs(a["x"] - b["x"]), abs(a["y"] - b["y"]))


def _friendly(desc: str) -> bool:
    return desc.startswith("peaceful ") or desc.startswith("tame ")


def _richer(old: str, new: str) -> str:
    """Keep the fuller of two labels of the same monster: an Astral high
    priest shows its god only from next to it ("peaceful high priestess of
    Tyr" vs "peaceful high priestess" from afar)."""
    if old and new and old != new and old.startswith(new + " of "):
        return old
    return new


def _monster_desc(desc: str) -> bool:
    """Does a look's text name a monster (not an object lying there)?"""
    from .danger import base_name, monster_record
    d = desc or ""
    return bool(monster_record(base_name(d))) or d.startswith(("peaceful ", "tame ")) or " called " in d


def _kind(desc: str) -> tuple:
    """Identity for matching: species and tame/peaceful/hostile, ignoring how
    it was seen ('leprechaun [seen: telepathy]' is still a leprechaun) and
    farlook suffixes ('trapped in a pit')."""
    from .danger import base_name
    d = desc or ""
    return (base_name(d), "tame" if d.startswith("tame ") else "peaceful" if d.startswith("peaceful ") else "")


class MonsterTracker:
    def __init__(self, game):
        self.game = game
        self.known: list[dict] = []        # monsters visible at the previous update
        self.recent: dict[int, dict] = {}  # id -> last sighting, for monsters seen recently on this level
        self.level = None
        self.next_id = 1
        self.last_turn: int | None = None
        self.visible_ids: set[int] = set()
        self.mixed: dict = {}
        self._was_hallu = False
        self._engulfer: str | None = None
        self.mimics_seen: set = set()      # (level, x, y) of ']' already reported
        self._relook_all = False           # set for one update after a were-creature shape change
        self.rogue_objects: set = set()    # (level, x, y) of ':' found to be food on the Rogue level

    def reset(self):
        self.known, self.recent = [], {}
        self.visible_ids = set()
        self.mixed: dict = {}    # (ch, color) -> {"friendly", "hostile"} labels seen on this level

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
        hero = getattr(snap, "hero", None)
        if getattr(snap, "engulfed", False) and hero is not None:
            # inside a monster: only its interior is drawn; keep the level memory as it is
            if self._engulfer is None:
                d = _clean(self.game.farlook(hero[0], hero[1] - 1)) if hasattr(self.game, "farlook") else ""
                self._engulfer = d or "engulfing monster"
            return [{"ch": "", "x": hero[0], "y": hero[1], "color": "", "pet": False, "dist": 0, "id": -1,
                     "desc": self._engulfer, "new": False, "statue": False, "tame": False, "peaceful": False,
                     "engulfer": True, "note": "you are ENGULFED by it: attack with F + any direction"}]
        self._engulfer = None
        if "Hallu" in st.conditions:
            # names and glyphs are random: don't look, don't learn, don't flag anything new
            self._was_hallu = True
            mons = monsters_in_view(snap)
            for m in mons:
                m.update(id=None, desc="", new=False, statue=False, tame=False, peaceful=False, hallu=True,
                         note="hallucinating: identity unknown (could be peaceful, or a floating eye)")
            return mons
        if self._was_hallu:
            self._was_hallu = False
            self.reset()                 # labels from before/while hallucinating: look at everything again
        self._relook_all = False
        self._apply_growth(getattr(snap, "messages", None))
        if any(re.search(r" releases you\.$|^You (?:get|are) released|^You pull free", x)
               for x in getattr(snap, "messages", None) or []):
            for k in self.known:       # the "holding you" part of a label is stale now
                if ", holding you" in (k.get("desc") or ""):
                    k["desc"] = k["desc"].replace(", holding you", "")
                    r = self.recent.get(k.get("id"))
                    if r is not None:
                        r["desc"] = k["desc"]
        dt = 1 if self.last_turn is None else max(1, turn - self.last_turn)
        radius = min(10, max(3, 2 * dt + 1))
        allm = monsters_in_view(snap)
        rogue = getattr(snap, "rogue", False)
        if rogue:
            # the Rogue level draws food as ':' like a lizard: squares already looked at and found to
            # hold an object are skipped while the ':' stays there
            allm = [m for m in allm if not (m["ch"] == ":" and (self.level, m["x"], m["y"]) in self.rogue_objects)]
        special = [m for m in allm if m["ch"] in "I]"]
        mons = [m for m in allm if m["ch"] not in "I]"]
        for m in mons:
            m.update(id=None, desc="", new=False, statue=False)
        for m in special:
            if m["ch"] == "I":
                note = "an unseen monster was here (blind/invisible): could be anything, even a peaceful"
                if "telepathy" in (getattr(self.game, "intrinsics", None) or ()) and "Blind" not in st.conditions:
                    note += (" — if your telepathy (blind, or extrinsic) doesn't show it, it's MINDLESS: a BLACK "
                             "LIGHT explodes into hallucination (step away), or a stalker")
                m.update(id=None, desc="remembered, unseen monster", new=False, statue=False, unseen=True,
                         tame=False, peaceful=False, note=note)
            else:
                key = (self.level, m["x"], m["y"])
                m.update(id=None, desc="mimic (posing as a strange object ']')", new=key not in self.mimics_seen,
                         statue=False, tame=False, peaceful=False, mimic=True,
                         note="MIMIC: touching it sticks you to it; kill it from range or keep away")
                self.mimics_seen.add(key)

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
                kinds = {_kind(k.get("desc", "")) for k in kc}
                if len(kinds) == 1 and len(mc) <= len(kc) and all(k.get("desc") for k in kc) \
                        and not self._relook_all:
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
            if self._relook_all:
                to_look.append(m)        # a shape change: no label may be inherited this time
                continue
            recs = [r for i, r in self.recent.items()
                    if i not in claimed and r["ch"] == m["ch"] and r["color"] == m["color"] and r.get("desc")
                    and ((turn - r.get("turn", 0) <= RESEEN_TURNS and _cheb(m, r) <= RESEEN_DIST)
                         or ((r["x"], r["y"]) == (m["x"], m["y"])
                             and (_stationary(r["desc"]) or turn - r.get("turn", 0) <= SAME_SQUARE_TURNS)))]
            if recs:
                resight[id(m)] = recs
            descs = {r["desc"] for r in recs}
            kinds = {_kind(r["desc"]) for r in recs}
            if m.get("pet") and any(d.startswith("tame ") for d in descs):
                r = min((r for r in recs if r["desc"].startswith("tame ")), key=lambda r: _cheb(m, r))
                m.update(id=r["id"], desc=r["desc"])
                claimed.add(r["id"])
            elif recs and all(r.get("statue") and (r["x"], r["y"]) == (m["x"], m["y"]) for r in recs):
                r = recs[0]
                m.update(id=r["id"], desc=r["desc"], statue=True)
                claimed.add(r["id"])
            elif len(kinds) == 1 and not _friendly(next(iter(descs))) \
                    and len(self.mixed.get((m["ch"], m["color"]), ())) < 2 \
                    and not risky_lookalike(m["ch"], m["color"], next(iter(descs))):
                # re-seen hostile: keep the label (a wrong 'hostile' label is the safe mistake),
                # unless this glyph comes in both peaceful and hostile kinds on this level
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

        if rogue:
            for m in [m for m in mons if m["ch"] == ":" and m.get("desc") and not _monster_desc(m["desc"])]:
                self.rogue_objects.add((self.level, m["x"], m["y"]))
                mons.remove(m)
                if m in loners:
                    loners.remove(m)
                for mc, _kc in undecided:
                    if m in mc:
                        mc.remove(m)

        # resolve ambiguous clusters: previous identities go to the nearest
        # member with the same description; members left over are new
        for mc, kc in undecided:
            members = [m for m in mc if id(m) in looked]
            for k in sorted(kc, key=lambda k: min((_cheb(m, k) for m in mc), default=99)):
                same = [m for m in members if m["id"] is None and _kind(m["desc"]) == _kind(k.get("desc", ""))]
                if same:
                    m = min(same, key=lambda e: _cheb(e, k))
                    m["id"] = k["id"]
                    m["desc"] = _richer(k.get("desc", ""), m["desc"])
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
            same = [r for r in recs if _kind(r["desc"]) == _kind(m["desc"]) and r["id"] not in claimed]
            if m["desc"] and not same and not m.get("statue"):
                # a wanderer back in view far from where it was last seen (the Rogue level's long corridors,
                # big rooms): the same species, out of view now and seen here lately, is most likely it
                taken = {k.get("id") for k in mons if k.get("id") is not None}
                same = [r for i, r in self.recent.items()
                        if i not in claimed and i not in taken and r.get("desc") and not r.get("statue")
                        and _kind(r["desc"]) == _kind(m["desc"]) and turn - r.get("turn", 0) <= RETURN_TURNS]
            if m["desc"] and same:
                r = min(same, key=lambda r: _cheb(m, r))
                m["id"] = r["id"]
                m["desc"] = _richer(r.get("desc", ""), m["desc"])
                claimed.add(r["id"])
                continue
            bn = base_name(m.get("desc") or "")
            were = [(i, r) for i, r in self.recent.items() if bn.startswith("were") and i not in claimed
                    and i not in {k["id"] for k in mons if k.get("id") is not None}
                    and base_name(r.get("desc", "")) == bn and _cheb(m, r) <= 3] if bn else []
            if were:
                # "The werejackal changes into a jackal.": the same monster with a new glyph
                i, r = min(were, key=lambda ir: _cheb(m, ir[1]))
                m["id"] = i
                claimed.add(i)
            else:
                m["new"] = not m.get("statue")

        xl = st.xl if st.ok else None
        lk = self.game.level_key() if hasattr(self.game, "level_key") else ""
        no_tele = "Sokoban" in (lk or "")
        for m in mons:
            if m["id"] is None:
                m["id"] = self._new_id()
            d = m.get("desc", "")
            m["tame"] = d.startswith("tame ")
            m["peaceful"] = d.startswith("peaceful ")
            if d and not m.get("statue"):
                m["note"] = note_for(d, xl, getattr(self.game, "intrinsics", ()))
                if (lk or "").startswith(("Gehennom", "Vlad's Tower")) and not _friendly(d) \
                        and base_name(d) == "wolf":
                    # 3.6.7 vampire shape-shifting: a vampire lord (1 in 10) or Vlad without the Candelabrum
                    # (1 in 3) becomes a wolf; its "death" raises the vampire at full HP next to you
                    m["note"] = ((m["note"] + " — ") if m["note"] else "") + VAMP_WOLF_NOTE
                if no_tele and "telep" in m["note"]:
                    m["note"] += " — BUT teleporting is blocked in Sokoban: corner it and kill it"

        flags = getattr(self.game, "level_flags", None)
        if flags is not None and hasattr(self.game, "level_key"):
            lk = self.game.level_key()
            if any(m.get("desc") and not m.get("statue") and "Medusa" in m["desc"] for m in mons):
                flags.setdefault(lk, set()).add("medusa")
            if any(re.search(r"(?:kill|destroy) Medusa|Medusa is (?:killed|turned to stone)|Medusa dies", x)
                   for x in getattr(snap, "messages", None) or []):
                flags.setdefault(lk, set()).add("medusa_dead")
        for m in mons:
            if m.get("desc") and not m.get("statue"):
                self.mixed.setdefault((m["ch"], m["color"]), set()).add(
                    "friendly" if _friendly(m["desc"]) else "hostile")
        for m in mons:
            if m.get("desc"):
                self.recent[m["id"]] = {"id": m["id"], "ch": m["ch"], "color": m["color"], "x": m["x"],
                                        "y": m["y"], "desc": m["desc"], "statue": m.get("statue", False),
                                        "turn": turn}
        new_visible = {m["id"] for m in mons}
        self._forget_killed(killed_names(getattr(snap, "messages", None)), self.visible_ids - new_visible,
                            snap.hero, turn)
        self.visible_ids = new_visible
        stale = [i for i, r in self.recent.items()
                 if i not in self.visible_ids and turn - r.get("turn", 0) > SAME_SQUARE_TURNS
                 and not _stationary(r.get("desc", ""))]
        for i in stale:
            del self.recent[i]
        if len(self.recent) > 80:
            for i in sorted(self.recent, key=lambda i: self.recent[i].get("turn", 0))[: len(self.recent) - 80]:
                del self.recent[i]
        self.known = [m for m in mons if m.get("desc")]
        self.last_turn = turn
        pets = [m for m in mons if m.get("tame") or m.get("pet")]
        for m in special:
            m["id"] = self._new_id()
            if m.get("mimic") and any(_cheb(m, p) <= 1 for p in pets):
                m["note"] += " — YOUR PET IS NEXT TO IT and may attack it, waking it beside you: step away"
        return mons + special

    def _apply_growth(self, messages) -> None:
        """A monster that grew up keeps its glyph (kitten -> housecat): rename
        its record so the label doesn't stay "tame kitten". If it's unclear
        which record (two of that kind, or a named pet), clear the candidates'
        labels so they get looked at again."""
        from .danger import base_name
        for msg in messages or []:
            mm = _GROW_RE.search(msg)
            if not mm:
                continue
            old, new = mm.group("old").lower(), mm.group("new")
            if old.startswith("were") or new == "human":
                # were.c new_were(): "The werejackal changes into a jackal/human." — the same
                # monster (both forms are 'werejackal') with a new glyph: look at everything again
                self._relook_all = True
                continue
            recs = [k for k in self.known if base_name(k.get("desc", "")) == old]
            if not recs and not mm.group("the"):
                # a named pet ("Fluffy grows up into a housecat."): relook the tame ones
                recs = [k for k in self.known if k.get("desc", "").startswith("tame ")]
                old = None
            for k in recs:
                if len(recs) == 1 and old:
                    k["desc"] = k["desc"].replace(old, new, 1)
                else:
                    k["desc"] = ""
                r = self.recent.get(k.get("id"))
                if r is not None:
                    if k["desc"]:
                        r["desc"] = k["desc"]
                    else:
                        del self.recent[k["id"]]

    def _forget_killed(self, names: list[str], vanished: set, hero, turn: int | None = None) -> None:
        """A killed monster must not be 're-seen' later: drop its record
        (prefer one that vanished this step, nearest the hero), so the next
        monster of that species counts as new. The kill (name, square, turn)
        goes to the game's memory: it dates the corpse."""
        from .danger import base_name
        record = getattr(self.game, "record_kill", None)
        for name in names:
            cands = [(i, r) for i, r in self.recent.items() if base_name(r.get("desc", "")) == name
                     and i not in self.visible_ids - vanished]
            if not cands:
                continue
            hx, hy = hero if hero else (0, 0)
            cands.sort(key=lambda ir: (ir[0] not in vanished, max(abs(ir[1]["x"] - hx), abs(ir[1]["y"] - hy)),
                                       -ir[1].get("turn", 0)))
            r = self.recent.pop(cands[0][0])
            if record is not None and cands[0][0] in vanished:
                record(name, (r["x"], r["y"]), turn)

    def relabel(self, x: int, y: int, raw: str) -> str | None:
        """An explicit farlook at (x, y) said `raw`: the monster tracked there
        now carries that label (a resurfaced snake, a look-alike). Returns the
        new label, or None if no tracked monster stands there."""
        d = _clean(raw or "")
        if not d or "statue of" in d:
            return None
        for m in self.known:
            if (m["x"], m["y"]) == (x, y):
                d = _richer(m.get("desc", ""), d)
                m["desc"] = d
                rec = self.recent.get(m.get("id"))
                if rec is not None:
                    rec["desc"] = d
                return d
        return None

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
