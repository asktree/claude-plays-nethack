"""Game driver: send keys to the tmux terminal, wait for the game to settle,
auto-dismiss --More--, collect messages, and produce snapshots.

Safety rule: we never send a key until the previous one has settled into a
recognized waiting state (or a generous timeout expires), so a keystroke
can't land in a prompt we haven't seen yet.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from .keys import describe_bytes, parse_keys
from .parse import (MAP_BOTTOM, MAP_TOP, MORE, State, Status, classify, parse_status)
from .screen import Screen
from .tmuxterm import TmuxTerminal


@dataclass
class Timing:
    first: float = 0.5     # max wait for the first output byte after a send
    quiet: float = 0.04    # output must be silent this long to count as settled
    max_wait: float = 8.0  # hard cap for one settle
    recheck: int = 6       # extra settle rounds when the screen looks mid-draw

    @classmethod
    def local(cls) -> "Timing":
        return cls(first=0.5, quiet=0.04, max_wait=8.0)

    @classmethod
    def remote(cls) -> "Timing":
        return cls(first=2.5, quiet=0.18, max_wait=20.0, recheck=8)


@dataclass
class Snap:
    screen: Screen
    state: State
    status: Status
    messages: list[str] = field(default_factory=list)   # messages seen during this step
    keys: str = ""
    elapsed: float = 0.0
    n: int = 0              # global step counter
    unsent: str = ""        # keys NOT sent because the game state made them unsafe
    stop_reason: str = ""
    monsters: list = field(default_factory=list)   # set by the MonsterTracker (command state)

    def __repr__(self) -> str:
        st = self.status.short() if self.status.ok else "?"
        return (f"<Snap #{self.n} {self.state.kind} {st} hero={self.hero} "
                f"msgs={self.messages!r}{' PROMPT=' + repr(self.state.prompt) if self.state.kind != 'command' else ''}>")

    @property
    def objects(self) -> list:
        """Object glyphs on the map: [{ch, x, y, kind, pile, color, dist}]."""
        from .mapscan import objects_in_view
        return objects_in_view(self)

    @property
    def features(self) -> list:
        """Stairs, fountains, altars, doors, traps, water... [{ch, x, y, name, dist}]."""
        from .mapscan import features_in_view
        return features_in_view(self)

    @property
    def menu(self):
        """Parsed menu/text window (items with letter/text/selected/header) or None."""
        return self.state.menu

    def hostiles(self, radius: int | None = None) -> list:
        """Monsters that are not tame/peaceful/statues, optionally within radius."""
        out = []
        for m in self.monsters:
            d = m.get("desc", "")
            if m.get("statue") or m.get("pet") or d.startswith("tame ") or d.startswith("peaceful "):
                continue
            if radius is not None and (m.get("dist") is None or m["dist"] > radius):
                continue
            out.append(m)
        return out

    def adjacent_hostiles(self) -> list:
        return self.hostiles(radius=1)

    @property
    def kind(self) -> str:
        return self.state.kind

    @property
    def hero(self) -> tuple[int, int] | None:
        if self.state.kind in ("command",):
            cx, cy = self.screen.cursor
            if MAP_TOP <= cy <= MAP_BOTTOM:
                return (cx, cy)
        return None

    @property
    def message(self) -> str:
        return " | ".join(self.messages)

    @property
    def prompt(self) -> str:
        return self.state.prompt if self.state.kind not in ("command",) else ""


_DIRS = {(-1, -1): "y", (0, -1): "k", (1, -1): "u", (-1, 0): "h", (1, 0): "l",
         (-1, 1): "b", (0, 1): "j", (1, 1): "n"}


def _sgn(v: int) -> int:
    return (v > 0) - (v < 0)


def _cursor_keys(cx: int, cy: int, tx: int, ty: int) -> str:
    """getpos cursor keys from (cx,cy) to (tx,ty); capitals move 8."""
    keys = []
    dx, dy = tx - cx, ty - cy
    while abs(dx) >= 8 and abs(dy) >= 8:
        keys.append(_DIRS[(_sgn(dx), _sgn(dy))].upper())
        dx -= 8 * _sgn(dx)
        dy -= 8 * _sgn(dy)
    while abs(dx) >= 8:
        keys.append("L" if dx > 0 else "H")
        dx -= 8 * _sgn(dx)
    while abs(dy) >= 8:
        keys.append("J" if dy > 0 else "K")
        dy -= 8 * _sgn(dy)
    while dx and dy:
        keys.append(_DIRS[(_sgn(dx), _sgn(dy))])
        dx -= _sgn(dx)
        dy -= _sgn(dy)
    while dx:
        keys.append("l" if dx > 0 else "h")
        dx -= _sgn(dx)
    while dy:
        keys.append("j" if dy > 0 else "k")
        dy -= _sgn(dy)
    return "".join(keys)


def _split_top(text: str) -> list[str]:
    """tty packs several short messages on one line separated by 2+ spaces."""
    parts = [p.strip() for p in re.split(r"\s{2,}", text.strip()) if p.strip()]
    return parts


class Game:
    """Owns the terminal; every key goes through here (single-threaded use)."""

    def __init__(self, term: TmuxTerminal, timing: Timing, log_path: Path | None = None):
        self.term = term
        self.timing = timing
        self.log_path = Path(log_path) if log_path else None
        self.lock = threading.RLock()
        self.n = 0
        self.last: Snap | None = None
        self.history: list[tuple[int | None, str]] = []   # (turn, message)
        self.max_history = 2000
        self.on_step = []   # callbacks(snap) after every settled step
        self.hero_pos: tuple[int, int] | None = None   # last known hero position
        # getpos (cursor-selection) mode can't always be read off the screen
        # (autodescribe rewrites the top line), so we track it: set when a
        # position prompt appears, cleared by a pick key or ESC.
        self.getpos_active = False
        self.tracker = None   # MonsterTracker, attached by the daemon
        self.visited: dict[str, set] = {}   # level (ldesc) -> hero positions seen in command state
        self.traps: dict[str, set] = {}     # level (ldesc) -> squares known to hold traps
        self.avoid: dict[str, set] = {}     # level (ldesc) -> squares the player asked to avoid

    # ---- low level ---------------------------------------------------------
    def capture(self) -> Snap:
        scr = self.term.capture()
        st = classify(scr)
        if st.kind == "getpos":
            self.getpos_active = True
        elif st.kind == "command" and self.getpos_active:
            st.kind = "getpos"
        elif st.kind not in ("command", "getpos"):
            self.getpos_active = False
        status = parse_status(scr)
        snap = Snap(screen=scr, state=st, status=status, n=self.n)
        return snap

    def _plausible(self, snap: Snap) -> bool:
        k = snap.state.kind
        if k == "unknown":
            return False
        if k == "command":
            cx, cy = snap.screen.cursor
            ch = snap.screen.at(cx, cy)
            if ch == " ":
                return False
            if not snap.status.ok:
                return False
        return True

    def _settle(self, size0: int, expect_output: bool = True) -> Snap:
        t = self.timing
        first = t.first if expect_output else min(t.first, t.quiet * 4)
        self.term.wait_quiet(size0, first, t.quiet, t.max_wait)
        snap = self.capture()
        for _ in range(t.recheck):
            if self._plausible(snap):
                break
            size1 = self.term.raw_size()
            self.term.wait_quiet(size1, t.quiet * 3, t.quiet, t.max_wait)
            snap = self.capture()
        return snap

    def send_bytes(self, data: bytes) -> Snap:
        """Send raw bytes, settle, capture. No --More-- handling."""
        with self.lock:
            if self.getpos_active and any(b in b".,;:\x1b" for b in data):
                self.getpos_active = False
            size0 = self.term.raw_size()
            self.term.send(data)
            return self._settle(size0)

    # ---- the main entry point ---------------------------------------------
    def _next_unit(self, data: bytes, i: int, kind: str) -> int:
        """End index of the next input unit starting at data[i], given the
        state the game is in right now."""
        n = len(data)
        c = data[i]
        if kind in ("getlin", "extcmd", "menu", "count", "dgl"):
            j = data.find(b"\r", i)
            return n if j < 0 else j + 1
        if kind == "getpos":
            j = i
            while j < n and data[j] not in b".,;:\x1b":
                j += 1
            return min(n, j + 1)
        if kind == "command":
            if c == ord("#"):
                j = data.find(b"\r", i)
                return n if j < 0 else j + 1
            if 48 <= c <= 57:           # count prefix + command
                j = i
                while j < n and 48 <= data[j] <= 57:
                    j += 1
                return min(n, j + 1)
            if c in b"FmMgG" and i + 1 < n:   # prefixes that take a direction
                return i + 2
        return i + 1

    def step(self, keys: str | bytes, auto_more: bool = True, max_more: int = 60,
             multi: bool = False, secret: bool = False) -> Snap:
        """Send keys; follow --More-- pages (collecting their text) until the
        game waits for real input. Returns the final snapshot, whose
        .messages lists every message shown during the step.

        Keys are sent one logical unit at a time (a command, a prompt answer,
        a line of text). If the game comes back to the command prompt while
        keys remain (i.e. a command finished earlier than the caller
        expected), or a [yn] prompt is open that the next key can't answer,
        the rest is NOT sent (snap.unsent / snap.stop_reason explain).
        multi=True allows several commands in one call (e.g. 'hhhh')."""
        with self.lock:
            data = keys if isinstance(keys, bytes) else parse_keys(keys)
            t0 = time.monotonic()
            self.n += 1
            messages: list[str] = []
            cur = self.last if self.last is not None else self.capture()
            kind = cur.state.kind
            i = 0
            snap = cur
            unsent = b""
            stop_reason = ""
            sent_any = False
            if "Destroy old game?" in (cur.state.prompt or "") and data[:1] in (b"y", b"Y"):
                raise PermissionError("refusing to answer 'y' to 'Destroy old game?' -- that erases the "
                                      "game in progress. Answer 'n' and investigate.")
            if cur.state.kind == "dgl" and "STALE-PROCESS" in (cur.state.prompt or ""):
                raise PermissionError("stale-process countdown on screen: any key aborts the recovery. "
                                      "Wait ~20s (use `nh screen` to watch), then continue.")
            while i < len(data):
                if sent_any:
                    if kind == "command" and not multi:
                        unsent = data[i:]
                        stop_reason = "the game returned to the command prompt before these keys were sent"
                        break
                    if kind == "yn":
                        allowed = set(snap.state.choices.replace(" ", "")) | {"\x1b", "\r"}
                        if chr(data[i]) not in allowed and "yes" not in snap.state.choices:
                            unsent = data[i:]
                            stop_reason = f"a [yn] prompt is open ({snap.state.prompt!r}) and {chr(data[i])!r} doesn't answer it"
                            break
                    if kind in ("gameover", "dead"):
                        unsent = data[i:]
                        stop_reason = f"state is {kind}"
                        break
                j = self._next_unit(data, i, kind)
                unit = data[i:j]
                i = j
                snap = self.send_bytes(unit)
                sent_any = True
                pages = 0
                while auto_more and snap.state.kind in ("more", "text") and pages < max_more:
                    txt = snap.state.more_text
                    if snap.state.kind == "more":
                        messages.extend(_split_top(txt))
                    elif txt:
                        messages.append(txt)
                    snap = self.send_bytes(snap.state.dismiss.encode())
                    pages += 1
                kind = snap.state.kind
            if snap.state.kind == "gameover" and snap.state.prompt:
                messages.append(snap.state.prompt)
            elif snap.state.kind == "command":
                top = snap.screen.row(0).strip()
                if top:
                    messages.extend(_split_top(top))
            snap.messages = messages
            snap.keys = "<secret>" if secret else describe_bytes(data[: len(data) - len(unsent)])
            snap.unsent = describe_bytes(unsent)
            snap.stop_reason = stop_reason
            snap.elapsed = time.monotonic() - t0
            snap.n = self.n
            if snap.hero is not None:
                self.hero_pos = snap.hero
                if snap.status.ok:
                    self.visited.setdefault(snap.status.ldesc, set()).add(snap.hero)
                    self._note_traps(snap, messages)
            if self.tracker is not None and snap.state.kind == "command":
                try:
                    snap.monsters = self.tracker.update(snap)
                except Exception as e:  # noqa: BLE001
                    self.log_event({"ev": "tracker_error", "err": repr(e)})
            for m in messages:
                self.history.append((snap.status.turn, m))
            if len(self.history) > self.max_history:
                del self.history[: len(self.history) - self.max_history]
            self.last = snap
            self._log(snap)
            for cb in list(self.on_step):
                try:
                    cb(snap)
                except Exception:
                    pass
            return snap

    _TRAP_MSG = re.compile(r"(trap|An arrow shoots out|A little dart shoots out|A trap door|A bear trap|"
                           r"You fall into a pit|land on a set of sharp iron spikes|A board beneath you|"
                           r"You are caught in a|A cloud of gas|You feel a wrenching|flash of light|"
                           r"You step onto a polymorph trap|magic trap|anti-magic field|A gush of water|"
                           r"rust trap|fire trap|A tower of flame)", re.I)

    def _note_traps(self, snap: Snap, messages: list[str]) -> None:
        """Remember trap squares per level: every displayed '^', and the hero's
        square when a trap message fires there (objects can hide a trap)."""
        lv = snap.status.ldesc
        known = self.traps.setdefault(lv, set())
        for y in range(1 + snap.state.msg_rows, 22):
            row = snap.screen.row(y)
            x = row.find("^")
            while x >= 0:
                known.add((x, y))
                x = row.find("^", x + 1)
        if any(self._TRAP_MSG.search(m) for m in messages) and snap.hero is not None:
            known.add(snap.hero)

    def farlook(self, x: int, y: int) -> str:
        """Describe screen cell (x, y) via ';' without disturbing self.last.
        Takes no game time. Only valid in command state."""
        with self.lock:
            saved = self.last
            try:
                s = self.send_bytes(b";")
                if s.state.kind != "getpos":
                    if s.state.kind != "command":
                        self.send_bytes(b"\x1b")
                    return ""
                for _ in range(4):
                    cx, cy = s.screen.cursor
                    if (cx, cy) == (x, y):
                        break
                    s = self.send_bytes(_cursor_keys(cx, cy, x, y).encode())
                if s.screen.cursor != (x, y):
                    self.send_bytes(b"\x1b")
                    return ""
                s = self.send_bytes(b".")
                texts = []
                n = 0
                while s.state.kind in ("more", "text") and n < 10:
                    texts.append(s.state.more_text)
                    s = self.send_bytes(b"\r")
                    n += 1
                if s.state.kind == "command":
                    top = s.screen.row(0).strip()
                    if top:
                        texts.append(top)
                else:
                    self.send_bytes(b"\x1b")
                desc = " ".join(t for t in texts if t).strip()
                self.log_event({"ev": "farlook", "ts": round(time.time(), 3), "x": x, "y": y, "desc": desc})
                return desc
            finally:
                self.last = saved

    def look(self) -> Snap:
        """Capture without sending anything."""
        with self.lock:
            snap = self.capture()
            if self.last is not None:
                snap.messages = []
            if snap.hero is not None:
                self.hero_pos = snap.hero
            if self.tracker is not None and snap.state.kind == "command":
                try:
                    snap.monsters = self.tracker.update(snap)
                except Exception as e:  # noqa: BLE001
                    self.log_event({"ev": "tracker_error", "err": repr(e)})
            self.last = snap
            return snap

    # ---- logging -----------------------------------------------------------
    def _log(self, snap: Snap) -> None:
        if not self.log_path:
            return
        rec = {
            "ev": "step", "n": snap.n, "ts": round(time.time(), 3), "keys": snap.keys,
            "kind": snap.state.kind, "prompt": snap.state.prompt if snap.state.kind != "command" else "",
            "messages": snap.messages, "status": snap.status.short() if snap.status.ok else None,
            "turn": snap.status.turn, "cursor": list(snap.screen.cursor),
            "elapsed": round(snap.elapsed, 3),
            "screen": snap.screen.text,
        }
        self.log_event(rec)

    def log_event(self, rec: dict) -> None:
        if not self.log_path:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a") as f:
            f.write(json.dumps(rec) + "\n")
