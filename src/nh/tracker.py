"""Automatic harness-side memory: dungeon overview, per-level features,
prayers. Persisted in run/<game>/harness_state.json so it survives daemon
restarts. The player sees it via `nh info` and in obs headers.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from .game import Game, Snap
from .parse import MAP_BOTTOM, MAP_TOP

_DUNGEON_HDR = re.compile(r"^(?P<name>[A-Z][A-Za-z' ]+?):(?: levels? (?P<a>\d+)(?: up)? to (?P<b>\d+))?\s*$")
_LEVEL_LINE = re.compile(r"^(?:Level (?P<n>\d+)|(?P<plane>Plane of \w+|Astral Plane|Home \d+))(?::| \[)(?P<rest>.*)$")

# level sounds (sounds.c dosounds) -> what they reveal about the level
SOUNDS = [
    (r"bubbling water|water falling on coins|splashing of a naiad|a soda fountain", "fountain"),
    (r"a slow drip|a gurgling noise|dishes being washed", "sink"),
    (r"courtly conversation|sceptre pounded|Off with|Queen Beruthiel", "THRONE ROOM (court: many monsters)"),
    (r"mosquitoes|marsh gas|Donald Duck", "swamp"),
    (r"counting money|quarterback|someone searching|footsteps of a guard|Ebenezer Scrooge", "vault (gold + guard)"),
    (r"low buzzing|angry drone|bees in your", "BEEHIVE (killer bees: poison)"),
    (r"unnaturally quiet|on the back of your", "graveyard/morgue (undead)"),
    (r"blades being honed|loud snoring|dice being thrown|General MacArthur", "BARRACKS (soldiers)"),
    (r"elephant stepping on a peanut|seal barking|Doctor Dolittle", "zoo (sleeping monsters + gold)"),
    (r"cursing shoplifters|chime of a cash register|Neiman and Marcus", "shop"),
    (r"someone praising|someone beseeching|carcass being offered|plea for donations", "temple (priest)"),
    (r"a strange wind|convulsive ravings|snoring snakes|No more woodchucks|a loud ZOT", "Oracle"),
    (r"crashing rock", "something digging (dwarf with a pick?)"),
    (r"howling at the moon", "WERE-CREATURE (lycanthropy)"),
]

FEATURE_CHARS = {"<": "up stairs", ">": "down stairs", "{": "fountain", "_": "altar", "\\": "throne",
                 "^": "magic portal", "~": "vibrating square", "#": None}
_TRAP_WORDS = ("trap", "pit", "hole", "board", "portal", "web", "field", "mine", "teleporter")

# traps worth a line in the level record (feature_desc names): the Castle's way down, portals
NOTABLE_TRAPS = ("trap door", "hole", "level teleporter", "magic portal")


# a monster in view set off / got caught in a trap (trap.c mintrap): the game now
# knows that trap, but the monster (or what it drops) may hide the '^' — re-read #terrain
# detect.c find_trap(): a search found a trap next to you — which square isn't said, and an object lying on it
# hides its '^' (p3 shift 14 #551: a scroll on a land mine; travel's last step walked onto it): re-read #terrain
FOUND_TRAP_RE = re.compile(
    r"^You find an? (?:arrow trap|dart trap|falling rock trap|squeaky board|bear trap|land mine|rolling boulder "
    r"trap|sleeping gas trap|rust trap|fire trap|pit|spiked pit|hole|trap door|teleportation trap|level "
    r"teleporter|magic portal|web|statue trap|magic trap|anti-magic field|polymorph trap)\.")

MON_TRAP_RE = re.compile(
    r"(?:falls|tumbles) into (?:a|an|your) pit|is caught in (?:a|an|your) (?:bear trap|spider web)|"
    r"evades (?:a|an|your) bear trap|tears through (?:a|an|your) spider web|avoids (?:a|an|your) spider web|"
    r"^A board beneath .* squeaks|triggers a trap but nothing happens|triggers (?:a|an|your) land mine|"
    r"^Click! .* triggers|seems to be yanked down|doesn't fall (?:into the pit|through the hole)|"
    r"^A gush of water hits (?!you)|erupts from the .* under (?!you)|"
    r"^A trigger appears in a pile of soil|pulls free\.\.\.|eats a bear trap|munches on some spikes")


class Tracker:
    def __init__(self, game: Game, path: Path):
        self.game = game
        self.path = Path(path)
        self.state = {"prayers": [], "levels": {}, "overview": "", "overview_turn": None,
                      "current_level": None, "current_branch": None, "notes": []}
        if self.path.exists():
            try:
                self.state.update(json.loads(self.path.read_text()))
            except Exception:
                pass
        self._last_ldesc = None
        self.need_overview = True
        self._refreshing = False
        self.scanned: set[str] = set()     # level keys whose traps were read via #terrain this session
        self._refit: set = set()           # (level, cell, old name) trap names dropped for a misfitting colour
        self._found_trap = None            # (name, hero square) of the last "You find a <trap>." (a search)
        if self.state.get("intrinsics") is not None and hasattr(game, "intrinsics"):
            game.intrinsics = set(self.state["intrinsics"])
        if self.state.get("quest_given"):
            game.quest_given = True
        # restore level identity and per-level trap/avoid memory
        if self.state.get("current_level") and self.state.get("current_ldesc"):
            game.level_name = self.state["current_level"]
            game.level_name_ldesc = self.state["current_ldesc"]
        feat_ch = {"up stairs": "<", "down stairs": ">", "fountain": "{", "altar": "_", "throne": "\\",
                   "magic portal": "^", "vibrating square": "~"}
        for key, lv in self.state["levels"].items():
            for fname, fcells in lv.get("features", {}).items():
                if fname in feat_ch:
                    for c in fcells:
                        game.terrain_seen.setdefault(key, {}).setdefault(tuple(c), feat_ch[fname])
            for attr in ("traps", "avoid", "solid"):
                cells = {tuple(c) for c in lv.get(attr, [])}
                if cells and hasattr(game, attr):
                    getattr(game, attr).setdefault(key, set()).update(cells)
            if lv.get("kills") and hasattr(game, "kills"):
                game.kills[key] = [(n, (x, y), t) for n, x, y, t in lv["kills"]]
            if lv.get("shops") and hasattr(game, "shops"):
                game.shops[key] = [list(e) for e in lv["shops"]]
            if lv.get("feature_desc") and hasattr(game, "feature_desc"):
                game.feature_desc[key] = {tuple(int(v) for v in c.split(",")): d
                                          for c, d in lv["feature_desc"].items()}
            for c in lv.get("doors", []):
                game.terrain_seen.setdefault(key, {}).setdefault(tuple(c), "D")
            if lv.get("niches") and hasattr(game, "niches"):
                game.niches[key] = {tuple(int(v) for v in c.split(",")): k for c, k in lv["niches"].items()}
            ses = lv.get("sessile")
            if ses and ses.get("ldesc") and getattr(game, "tracker", None) is not None \
                    and isinstance(getattr(game.tracker, "sessile", None), dict):
                mem = game.tracker.sessile.setdefault(ses["ldesc"], {})
                for x, y, ch, color, desc in ses.get("cells", []):
                    mem.setdefault((x, y), {"ch": ch, "color": color, "x": x, "y": y, "desc": desc,
                                            "statue": False})
            if lv.get("rooms") and isinstance(getattr(game, "special_rooms", None), dict):
                game.special_rooms[key] = {tuple(int(v) for v in c.split(",")): {
                    "kind": r[0], "prev": tuple(r[1]) if r[1] else None, "turn": r[2]} for c, r in lv["rooms"].items()}
            if lv.get("mimics") and isinstance(getattr(game, "mimics", None), dict):
                game.mimics[key] = {tuple(int(v) for v in c.split(",")): k for c, k in lv["mimics"].items()}
            if lv.get("desmap"):
                if getattr(game, "desmap_ids", None) is None:
                    game.desmap_ids = {}
                game.desmap_ids.setdefault(key, dict(lv["desmap"]))
            if lv.get("flags") and hasattr(game, "level_flags"):
                game.level_flags.setdefault(key, set()).update(lv["flags"])
            if lv.get("stairs_to") and hasattr(game, "stair_links"):
                game.stair_links[key] = {tuple(int(v) for v in c.split(",")): dest
                                         for c, dest in lv["stairs_to"].items()}

    def save(self):
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, indent=1))
        tmp.replace(self.path)

    # called after every settled step
    def on_step(self, snap: Snap):
        st = snap.status
        changed = False
        for m in snap.messages:
            if m.startswith("You begin praying to"):
                self.state["prayers"].append({"turn": st.turn, "msg": m, "outcome": ""})
                changed = True
            elif self.state["prayers"] and not self.state["prayers"][-1].get("outcome"):
                if any(k in m for k in ("You feel a hopeful feeling", "You feel much better",
                                        "You feel that", "is displeased", "You feel guilty",
                                        "reconciliation", "You feel a feeling of hopelessness",
                                        "glow", "You feel less", "Your stomach feels content",
                                        "You are surrounded by a shimmering light", "You feel as if")):
                    self.state["prayers"][-1]["outcome"] = m
                    changed = True
        for m in snap.messages:
            # pray.c dosacrifice(): what a sacrifice says about the prayer timeout
            kind = ("zero" if re.search(r"four-leaf clover|brushed your (?:foot|feet)|feeling of reconciliation", m)
                    else "reset" if re.search(r"^An object appears at your feet|Use my gift wisely", m)
                    else "reduced" if re.search(r"^You have a hopeful feeling", m) else None)
            if kind and not (self.state.get("prayer_evidence")
                             and self.state["prayer_evidence"][-1] == {"turn": st.turn, "kind": kind}):
                self.state.setdefault("prayer_evidence", []).append({"turn": st.turn, "kind": kind})
                changed = True
        if "For what do you wish?" in (snap.state.prompt or "") and \
                (not self.state.get("wishes") or self.state["wishes"][-1].get("turn") != st.turn):
            self.state.setdefault("wishes", []).append({"turn": st.turn})
            changed = True
        for m in snap.messages:
            # pray.c pleased(): once a demigod (wizard.c wizdead(): the Wizard of Yendor died; spell.c: the
            # invocation) and again once crowned, every prayer adds rnz(1000) to the prayer timeout
            key = ("demigod" if (re.search(r"^You (?:kill|destroy) the Wizard of Yendor\b|"
                                           r"^The Wizard of Yendor (?:is killed|dies)", m)
                                 or Game._INVOKED.search(m)) else
                   "crowned" if re.search(r"I crown thee\.\.\.|Thou shalt be my Envoy of Balance|"
                                          r"Thou art chosen to (?:steal|take) souls", m) else None)
            if key and not self.state.get(key):
                self.state[key] = {"turn": st.turn, "msg": m}
                changed = True
        if st.ok and st.ldesc and st.ldesc != self._last_ldesc:
            self._last_ldesc = st.ldesc
            self.need_overview = True
        found = next((mm for mm in (FOUND_TRAP_RE.search(m) for m in snap.messages) if mm), None)
        if found and snap.hero is not None:
            self._found_trap = (found.group(0)[len("You find "):].rstrip(".").split(" ", 1)[1], snap.hero)
        if st.ok and any(MON_TRAP_RE.search(m) or FOUND_TRAP_RE.search(m) or Game._INVOKED.search(m)
                         for m in snap.messages):
            # (the invocation rebuilds the area around the new stairs: a ring of fire traps, a moat)
            self.scanned.discard(self.game.level_key(st))
            self.need_overview = True        # the refresh re-reads this level's traps
        if snap.state.kind == "command" and st.ok and self.need_overview and not self._refreshing:
            # learn the level's name right away (^O takes no game time), so
            # this step's features/traps are filed under the right level
            try:
                self.refresh_overview()
            except Exception as e:  # noqa: BLE001
                self.game.log_event({"ev": "overview_error", "err": repr(e)})
        if snap.state.kind == "command" and st.ok and not self._refreshing:
            try:
                self._describe_features(snap)
            except Exception as e:  # noqa: BLE001
                self.game.log_event({"ev": "feature_desc_error", "err": repr(e)})
        if snap.state.kind == "command" and st.ok:
            key = self.game.level_key(st)
            lv = self.state["levels"].setdefault(key, {"first_turn": st.turn})
            for m in snap.messages:
                if m.startswith("You hear") or m.startswith("You smell") or "unnaturally quiet" in m \
                        or "on the back of your" in m:
                    for pat, what in SOUNDS:
                        if re.search(pat, m):
                            heard = lv.setdefault("sounds", [])
                            if what not in heard:
                                heard.append(what)
            lv["last_turn"] = st.turn
            lv["ldesc"] = st.ldesc
            if not getattr(snap, "engulfed", False):
                # the game's per-level feature memory (colour-checked, pruned when a fountain dries
                # up; the engulf ring's corners and ray animations are no thrones)
                seen = getattr(self.game, "terrain_seen", {}).get(key, {})
                feats: dict = {}
                for (x, y), ch in sorted(seen.items(), key=lambda kv: (kv[0][1], kv[0][0])):
                    name = FEATURE_CHARS.get(ch)
                    if name:
                        feats.setdefault(name, []).append([x, y])
                fd = getattr(self.game, "feature_desc", {}).get(key, {})
                for (x, y), d in sorted(fd.items(), key=lambda kv: (kv[0][1], kv[0][0])):
                    nm = next((n for n in NOTABLE_TRAPS if n in d), None)
                    if nm and [x, y] not in feats.get(nm, []):
                        feats.setdefault(nm, []).append([x, y])
                bridges = list((lv.get("features") or {}).get("drawbridge", []))
                for f in snap.features:
                    if "drawbridge" in f["name"] and [f["x"], f["y"]] not in bridges:
                        bridges.append([f["x"], f["y"]])
                if bridges:
                    feats["drawbridge"] = bridges
                lv["features"] = feats
                lv["doors"] = sorted([x, y] for (x, y), ch in seen.items() if ch == "D")
                lv["map"] = [snap.screen.row(y).rstrip() for y in range(MAP_TOP, MAP_BOTTOM + 1)]
            for attr in ("traps", "avoid", "solid"):
                cells = sorted(getattr(self.game, attr, {}).get(key, ()))
                if cells or attr in lv:
                    lv[attr] = [list(c) for c in cells]
            kills = getattr(self.game, "kills", {}).get(key)
            if kills:
                lv["kills"] = [[n, c[0], c[1], t] for n, c, t in kills]
            shops = getattr(self.game, "shops", {}).get(key)
            if shops:
                lv["shops"] = [list(e) for e in shops]
            fd = getattr(self.game, "feature_desc", {}).get(key)
            if fd:
                lv["feature_desc"] = {f"{c[0]},{c[1]}": d for c, d in fd.items()}
            ni = getattr(self.game, "niches", {}).get(key)
            if ni:
                lv["niches"] = {f"{c[0]},{c[1]}": k for c, k in ni.items()}
            mon = getattr(self.game, "tracker", None)
            ses = (getattr(mon, "sessile", None) or {}).get(snap.status.ldesc) if mon is not None else None
            if ses is not None and (ses or lv.get("sessile")):
                # molds/jellies seen here (the monster tracker's memory; a daemon restart would lose it)
                lv["sessile"] = {"ldesc": snap.status.ldesc,
                                 "cells": [[c[0], c[1], r.get("ch"), r.get("color"), r.get("desc")]
                                           for c, r in sorted(ses.items())]}
            sr = getattr(self.game, "special_rooms", {}).get(key)
            if sr or lv.get("rooms"):
                lv["rooms"] = {f"{c[0]},{c[1]}": [r.get("kind"), list(r["prev"]) if r.get("prev") else None,
                                                  r.get("turn")] for c, r in (sr or {}).items()}
            mi = getattr(self.game, "mimics", {}).get(key)
            if mi or lv.get("mimics"):
                lv["mimics"] = {f"{c[0]},{c[1]}": k for c, k in (mi or {}).items()}
            dm = (getattr(self.game, "desmap_ids", None) or {}).get(key)
            if dm and not dm.get("ambiguous"):
                lv["desmap"] = {k: dm[k] for k in ("level", "index", "ox", "oy") if k in dm}
            fl = getattr(self.game, "level_flags", {}).get(key)
            if fl:
                lv["flags"] = sorted(fl)
            for lk, links in getattr(self.game, "stair_links", {}).items():
                if links:
                    self.state["levels"].setdefault(lk, {})["stairs_to"] = {f"{c[0]},{c[1]}": d
                                                                           for c, d in links.items()}
            changed = True
        intr = sorted(getattr(self.game, "intrinsics", ()))
        if intr != self.state.get("intrinsics"):
            self.state["intrinsics"] = intr
            changed = True
        if changed:
            self.save()

    # a '^' of these colours can only be one trap type (mapscan.TRAP_BY_COLOR); others get looked at
    _ONE_TRAP_COLOR = (1, 4, 9, 10, 13)

    @staticmethod
    def _trap_fits(name: str, col) -> bool:
        """Does a remembered trap name fit the colour its '^' shows now? (An unknown colour: yes.)"""
        from .mapscan import trap_names_for_color
        names = trap_names_for_color(col)
        n = (name or "").lower()
        return not names or not any(w in n for w in _TRAP_WORDS) or any(c in n for c in names)

    def _describe_features(self, snap, limit: int = 6) -> None:
        """Look once (';', no game time) at traps whose colour leaves several
        types, and at altars (alignment): game.feature_desc[level]."""
        st = snap.status
        if "Hallu" in st.conditions or getattr(snap, "engulfed", False) or not hasattr(self.game, "feature_desc"):
            return
        from .game import feature_at
        key = self.game.level_key(st)
        known = self.game.feature_desc.setdefault(key, {})
        todo = []
        for y in range(MAP_TOP + 1 + snap.state.msg_rows, MAP_BOTTOM + 1):
            row = snap.screen.row(y)
            for x, ch in enumerate(row):
                if (x, y) == snap.hero:
                    continue
                if (x, y) in known and ch == "^" and not getattr(snap, "rogue", False) \
                        and not self._trap_fits(known[(x, y)], snap.screen.color_at(x, y)) \
                        and (key, (x, y), known[(x, y)]) not in self._refit:
                    # another trap now (a land mine blown into a pit; the qa10 check: a wished trap replaced a bear
                    # trap): forget the old name — a one-colour type names itself, others are looked at again
                    # (once per name: a look that names a misfit again is believed)
                    self._refit.add((key, (x, y), known.pop((x, y))))
                if (x, y) in known:
                    # the Astral Plane's high altars show their alignment only from next to them
                    h = snap.hero
                    if not (known[(x, y)].startswith("aligned") and h
                            and max(abs(x - h[0]), abs(y - h[1])) <= 1):
                        continue
                if ch == "^" and snap.screen.color_at(x, y) not in self._ONE_TRAP_COLOR:
                    todo.append((x, y))
                elif ch == "_" and feature_at(snap.screen, x, y):
                    todo.append((x, y))
                elif ch == "%" and getattr(snap, "rogue", False):
                    todo.append((x, y))        # the Rogue level's stairs (up and down both '%')
                elif ch == "+" and snap.screen.color_at(x, y) == 3 and not getattr(snap, "rogue", False):
                    from .mapscan import _door_like
                    if not _door_like(snap.screen, x, y) and \
                            (getattr(snap, "feature_mem", None) or {}).get((x, y)) != "D":
                        todo.append((x, y))    # a brown '+' out of a wall line: a closed door or a spellbook?
        if not todo:
            return
        h = snap.hero
        todo.sort(key=lambda c: max(abs(c[0] - h[0]), abs(c[1] - h[1])) if h else 0)
        self._refreshing = True
        saved = self.game.last
        n_hist = len(self.game.history)
        try:
            raw = self.game.describe_cells(todo[:limit])
        finally:
            del self.game.history[n_hist:]
            self.game.last = saved
            self._refreshing = False
        from .monitor import _clean
        feats = self.game.terrain_seen.setdefault(key, {}) if hasattr(self.game, "terrain_seen") else {}
        for c, d in raw.items():
            d = _clean(d or "")
            if d and (("trap" in d or "pit" in d or "hole" in d or "board" in d or "portal" in d
                       or "web" in d or "field" in d or "mine" in d) or "altar" in d):
                known[c] = d
            elif d and getattr(snap, "rogue", False) and snap.screen.at(*c) == "%":
                known[c] = d                  # "staircase down" / "food ration" (asked once)
                if "staircase down" in d or "ladder down" in d:
                    feats[c] = ">"
                elif "staircase up" in d or "ladder up" in d:
                    feats[c] = "<"
            elif d and snap.screen.at(*c) == "+":
                known[c] = d                  # "closed door" / "broken door"... or a spellbook (asked once)
                if "door" in d:
                    feats[c] = "D"

    def refresh_overview(self):
        """Run ^O (no game time) and record branch/level; on a level not yet
        scanned this session, also read its known traps via #terrain. Call
        only in command state."""
        if self._refreshing:
            return
        self._refreshing = True
        try:
            self._refresh_overview()
        finally:
            self._refreshing = False

    def _refresh_overview(self):
        saved = self.game.last
        ldesc = saved.status.ldesc if saved is not None and saved.status.ok else None
        n_hist = len(self.game.history)
        snap = self.game.step(b"\x0f")
        text = "\n".join(snap.messages)
        if snap.state.kind not in ("command",):
            self.game.step(b"\x1b")
        del self.game.history[n_hist:]        # the overview isn't a game message
        self.game.last = saved
        self.need_overview = False
        if text and ldesc:
            self._parse_overview(text, snap, ldesc)
        key = self.game.level_key()
        if key and key not in self.scanned and saved is not None and saved.status.ok \
                and not {"Hallu", "Conf", "Stun"} & set(saved.status.conditions):
            found = self.game.terrain_scan()
            self.game.last = saved
            if found is not None:
                self.scanned.add(key)
                old = set(self.game.traps.get(key, ()))
                self.game.traps.setdefault(key, set()).update(found["traps"])
                name, at = getattr(self, "_found_trap", None) or (None, None)
                self._found_trap = None
                new = [c for c in set(found["traps"]) - old
                       if at is not None and max(abs(c[0] - at[0]), abs(c[1] - at[1])) <= 1]
                if name and len(new) == 1 and hasattr(self.game, "feature_desc"):
                    self.game.feature_desc.setdefault(key, {})[new[0]] = name     # "You find a land mine."
                if hasattr(self.game, "merge_terrain"):
                    self.game.merge_terrain(key, found, getattr(snap, "hero", None))
                else:
                    self.game.terrain_seen.setdefault(key, {}).update(found["features"])
        self.save()

    def drop_cells(self, key: str, cells) -> None:
        """Game._prune_features() dropped remembered features on arrival: drop them from the saved level too,
        or a daemon restart would load them back before the next step saves the level."""
        lv = self.state["levels"].get(key)
        cells = {tuple(c) for c in cells}
        if not lv or not cells:
            return
        feats = lv.get("features") or {}
        for name in list(feats):
            feats[name] = [c for c in feats[name] if tuple(c) not in cells]
            if not feats[name]:
                del feats[name]
        if "doors" in lv:
            lv["doors"] = [c for c in lv["doors"] if tuple(c) not in cells]
        if lv.get("stairs_to"):
            lv["stairs_to"] = {k: v for k, v in lv["stairs_to"].items()
                               if tuple(int(n) for n in k.split(",")) not in cells}
        self.save()

    def _parse_overview(self, text: str, snap, ldesc: str):
        self.state["overview"] = text
        self.state["overview_turn"] = snap.status.turn
        if re.search(r"^\s*(?:Given quest by|Completed quest for) ", text, re.M):
            # dungeon.c print_mapseen(): the quest home level once the leader assigned the quest
            self.state["quest_given"] = True
            self.game.quest_given = True
        branch = None
        lines = [ln.strip() for ln in text.splitlines()]
        for i, line in enumerate(lines):
            m = _DUNGEON_HDR.match(line)
            if m:
                branch = m.group("name")
                continue
            if "<- You are here" in line:
                # the notes under the level line: "A primitive area." is the Rogue level (drawn with other
                # symbols and no colours; its arrival message comes only on the first visit)
                notes = []
                for nxt in lines[i + 1:]:
                    if nxt.startswith("Level ") or _DUNGEON_HDR.match(nxt) or _LEVEL_LINE.match(nxt):
                        break
                    notes.append(nxt)
                rogue = "[rogue]" in line or any("A primitive area" in n for n in notes)
                lm = re.match(r"^(Level (\d+)|[A-Z][\w ]+?)(?::| \[| \")", line)
                lvl = lm.group(1) if lm else line.split(":")[0]
                self.state["current_branch"] = branch
                self.state["current_level"] = f"{branch} / {lvl}"
                self.state["current_ldesc"] = ldesc
                self.game.level_name = self.state["current_level"]
                self.game.level_name_ldesc = ldesc
                # merge anything filed under the provisional key (the ldesc)
                name = self.state["current_level"]
                self.game.rekey_level(ldesc, name)
                if rogue and hasattr(self.game, "level_flags"):
                    self.game.level_flags.setdefault(name, set()).add("rogue")
                levels = self.state["levels"]
                if ldesc in levels and ldesc != name:
                    prov = levels.pop(ldesc)
                    lv = levels.setdefault(name, {"first_turn": prov.get("first_turn")})
                    for k, cells in prov.get("features", {}).items():
                        lst = lv.setdefault("features", {}).setdefault(k, [])
                        lst.extend(c for c in cells if c not in lst)
                    for k in ("map", "last_turn", "ldesc"):
                        if k in prov:
                            lv[k] = prov[k]

    def summary(self) -> str:
        st = self.game.last.status if self.game.last else None
        turn = st.turn if st else None
        lines = []
        if self.state.get("current_level"):
            lines.append(f"where: {self.state['current_level']}")
        pr = self.state["prayers"]
        if pr:
            last = pr[-1]
            ago = (turn - last["turn"]) if (turn and last.get("turn")) else None
            lines.append(f"prayers: {len(pr)}; last at T:{last['turn']}"
                         + (f" ({ago} turns ago)" if ago is not None else "")
                         + (f" -> {last['outcome']}" if last.get("outcome") else ""))
        else:
            lines.append("prayers: none yet (first prayer is safe from about T:300 when in real trouble)")
        return "\n".join(lines)

    def levels_text(self) -> str:
        out = []
        for key, lv in self.state["levels"].items():
            f = dict(lv.get("features", {}))
            fd = lv.get("feature_desc") or {}
            if f.get("altar"):
                # "altar [[39, 7], ...]" -> with the alignment learned by looking ("lawful high altar")
                f["altar"] = [fd.get(f"{x},{y}", "altar") + f" ({x},{y})" for x, y in f["altar"]]
            fs = ", ".join(f"{k} {v}" for k, v in f.items() if v)
            snd = ("; heard: " + ", ".join(lv["sounds"])) if lv.get("sounds") else ""
            out.append(f"{key}: T{lv.get('first_turn')}-{lv.get('last_turn')} {fs}{snd}")
        return "\n".join(out) or "(no levels recorded)"
