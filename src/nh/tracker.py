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
                 "#": None}


# a monster in view set off / got caught in a trap (trap.c mintrap): the game now
# knows that trap, but the monster (or what it drops) may hide the '^' — re-read #terrain
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
        # restore level identity and per-level trap/avoid memory
        if self.state.get("current_level") and self.state.get("current_ldesc"):
            game.level_name = self.state["current_level"]
            game.level_name_ldesc = self.state["current_ldesc"]
        feat_ch = {"up stairs": "<", "down stairs": ">", "fountain": "{", "altar": "_", "throne": "\\"}
        for key, lv in self.state["levels"].items():
            for fname, fcells in lv.get("features", {}).items():
                if fname in feat_ch:
                    for c in fcells:
                        game.terrain_seen.setdefault(key, {}).setdefault(tuple(c), feat_ch[fname])
            for attr in ("traps", "avoid"):
                cells = {tuple(c) for c in lv.get(attr, [])}
                if cells:
                    getattr(game, attr).setdefault(key, set()).update(cells)

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
        if "For what do you wish?" in (snap.state.prompt or "") and \
                (not self.state.get("wishes") or self.state["wishes"][-1].get("turn") != st.turn):
            self.state.setdefault("wishes", []).append({"turn": st.turn})
            changed = True
        if st.ok and st.ldesc and st.ldesc != self._last_ldesc:
            self._last_ldesc = st.ldesc
            self.need_overview = True
        if st.ok and any(MON_TRAP_RE.search(m) for m in snap.messages):
            self.scanned.discard(self.game.level_key(st))
            self.need_overview = True        # the refresh re-reads this level's traps
        if snap.state.kind == "command" and st.ok and self.need_overview and not self._refreshing:
            # learn the level's name right away (^O takes no game time), so
            # this step's features/traps are filed under the right level
            try:
                self.refresh_overview()
            except Exception as e:  # noqa: BLE001
                self.game.log_event({"ev": "overview_error", "err": repr(e)})
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
            feats = lv.setdefault("features", {})
            for y in range(MAP_TOP, MAP_BOTTOM + 1):
                row = snap.screen.row(y)
                for x, ch in enumerate(row):
                    if ch in "<>{_\\":
                        name = FEATURE_CHARS[ch]
                        lst = feats.setdefault(name, [])
                        if [x, y] not in lst:
                            lst.append([x, y])
            lv["map"] = [snap.screen.row(y).rstrip() for y in range(MAP_TOP, MAP_BOTTOM + 1)]
            for attr in ("traps", "avoid"):
                cells = sorted(getattr(self.game, attr).get(key, ()))
                if cells or attr in lv:
                    lv[attr] = [list(c) for c in cells]
            changed = True
        if changed:
            self.save()

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
                self.game.traps.setdefault(key, set()).update(found["traps"])
                self.game.terrain_seen.setdefault(key, {}).update(found["features"])
        self.save()

    def _parse_overview(self, text: str, snap, ldesc: str):
        self.state["overview"] = text
        self.state["overview_turn"] = snap.status.turn
        branch = None
        for line in text.splitlines():
            line = line.strip()
            m = _DUNGEON_HDR.match(line)
            if m:
                branch = m.group("name")
                continue
            if "<- You are here" in line:
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
            f = lv.get("features", {})
            fs = ", ".join(f"{k} {v}" for k, v in f.items() if v)
            snd = ("; heard: " + ", ".join(lv["sounds"])) if lv.get("sounds") else ""
            out.append(f"{key}: T{lv.get('first_turn')}-{lv.get('last_turn')} {fs}{snd}")
        return "\n".join(out) or "(no levels recorded)"
