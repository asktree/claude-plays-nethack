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

FEATURE_CHARS = {"<": "up stairs", ">": "down stairs", "{": "fountain", "_": "altar", "\\": "throne",
                 "#": None}


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
        if st.ok and st.ldesc and st.ldesc != self._last_ldesc:
            self._last_ldesc = st.ldesc
            self.need_overview = True
        if snap.state.kind == "command" and st.ok:
            key = self.state.get("current_level") or st.ldesc
            lv = self.state["levels"].setdefault(key, {"first_turn": st.turn})
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
            changed = True
        if changed:
            self.save()

    def refresh_overview(self):
        """Run ^O (no game time) and record branch/level. Call only in command state."""
        saved = self.game.last
        snap = self.game.step(b"\x0f")
        text = "\n".join(snap.messages)
        if snap.state.kind not in ("command",):
            self.game.step(b"\x1b")
        self.game.last = saved
        self.need_overview = False
        if not text:
            return
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
        self.save()

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
            out.append(f"{key}: T{lv.get('first_turn')}-{lv.get('last_turn')} {fs}")
        return "\n".join(out) or "(no levels recorded)"
