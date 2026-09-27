"""Game driver: send keys to the tmux terminal, wait for the game to settle,
auto-dismiss --More--, collect messages, and produce snapshots.

Safety rule: we never send a key until the previous one has settled into a
recognized waiting state (or a generous timeout expires), so a keystroke
can't land in a prompt we haven't seen yet.
"""

from __future__ import annotations

import copy
import json
import os
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from .keys import describe_bytes, parse_keys
from .parse import (MAP_BOTTOM, MAP_TOP, MONSTER_CHARS, MORE, State, Status, classify, parse_status)
from .screen import Screen
from .tmuxterm import TmuxTerminal


@dataclass
class Timing:
    first: float = 0.5     # max wait for the first output byte after a send
    quiet: float = 0.04    # output must be silent this long to count as settled
    max_wait: float = 8.0  # hard cap for one settle
    recheck: int = 10      # extra settle rounds when the screen looks mid-draw

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
    under: str | None = None   # remembered map feature under the hero ('<', '>', '{', '_', '\\')
    engulfed: bool = False     # the hero is inside a monster (the /-\\ ring is drawn around '@')

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
        """Monsters that are not tame/peaceful/statues, optionally within
        radius. Excludes what can't be judged: 'I' markers (unseen, maybe a
        peaceful) and anything seen while hallucinating."""
        out = []
        for m in self.monsters:
            d = m.get("desc", "")
            if m.get("statue") or m.get("pet") or d.startswith("tame ") or d.startswith("peaceful "):
                continue
            if m.get("unseen") or m.get("hallu"):
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


def _explosion_frame(scr: Screen) -> bool:
    """True if an explosion animation (explode.c: a 3x3 ring of / - \\ |
    glyphs around a blank centre) is on the map. The corners are the tell:
    '/' top-left and bottom-right, '\\' top-right and bottom-left, all in one
    colour; at least three must match (part of a blast can be out of sight)."""
    rows = [scr.row(y) for y in range(scr.height)]
    want = ((-1, -1, "/"), (1, -1, "\\"), (-1, 1, "\\"), (1, 1, "/"))
    for y in range(MAP_TOP + 1, MAP_BOTTOM):
        if "/" not in rows[y - 1] + rows[y + 1] and "\\" not in rows[y - 1] + rows[y + 1]:
            continue
        for x in range(1, scr.width - 1):
            if rows[y][x] == "@":
                continue      # engulfed: the same ring drawn around the hero is the engulfer
            hits = [scr.fg[y + dy][x + dx] for dx, dy, ch in want if rows[y + dy][x + dx] == ch]
            if len(hits) >= 3 and len(set(hits)) == 1:
                return True
    return False


HERO_RACE, HERO_ROLE = "dwarf", "valkyrie"
# genociding your own race's base monster or your role's player-monster kills
# you (read.c: i == urace.malenum || i == urole.malenum); class genocide of
# their classes (h, @) includes them
_SELF_CLASSES = {"h", "@"}
_SELF_NAMES = {HERO_RACE, HERO_RACE + "s", "dwarves", HERO_ROLE, HERO_ROLE + "s"}


def _genocide_danger(prompt: str, answer: str) -> str:
    a = answer.replace("\r", "").replace("\n", "").strip().lower()
    if not a or a.startswith("\x1b"):
        return ""
    if "class" in prompt.lower():
        cls = a if len(a) == 1 else None
        if cls is None:
            from .danger import monster_record
            name = a[:-1] if a.endswith("s") and monster_record(a[:-1]) else a
            rec = monster_record(name) or monster_record(a.replace("ves", "f"))
            cls = rec.get("symbol") if rec else None
            if cls is None and name in _SELF_NAMES:
                cls = "h"
        if cls in _SELF_CLASSES:
            return (f"refusing genocide answer {answer.strip()!r}: it resolves to class {cls!r}, which contains "
                    f"your own race ({HERO_RACE}) or role ({HERO_ROLE}) — you would die. Blessed genocide: "
                    "answer 'L' (liches) or ';' (sea monsters).")
        return ""
    if a in _SELF_NAMES:
        return (f"refusing to genocide {a!r}: that is your own race/role — you would die. Uncursed genocide: "
                "'master mind flayer' or 'mind flayer'.")
    return ""


def _engulfed(scr: Screen, hero) -> bool:
    """The swallow display: a ring of / - \\ | around the hero (corners are
    the tell, as for explosions, but the centre is '@')."""
    if hero is None:
        return False
    x, y = hero
    want = ((-1, -1, "/"), (1, -1, "\\"), (-1, 1, "\\"), (1, 1, "/"))
    return sum(1 for dx, dy, ch in want if scr.at(x + dx, y + dy) == ch) >= 3


def _split_top(text: str) -> list[str]:
    """tty packs several short messages on one line separated by 2+ spaces."""
    parts = [p.strip() for p in re.split(r"\s{2,}", text.strip()) if p.strip()]
    out: list[str] = []
    for p in parts:
        # re-join quoted speech that contains a double space ("Hello!  Welcome...")
        if out and out[-1].count('"') % 2 == 1:
            out[-1] += "  " + p
        else:
            out.append(p)
    return out


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
        self.terrain_seen: dict[str, dict] = {}   # level key -> {(x, y): feature char} (stairs, fountains...)
        self.real_xl: int | None = None    # last XL read while not polymorphed
        self.last_status: Status | None = None
        # Level identity for per-level memory: "Dlvl:3" is ambiguous (main
        # dungeon vs Gnomish Mines), so the memory tracker sets the ^O
        # overview name ("The Gnomish Mines / Level 3") for the ldesc it saw.
        self.level_name: str | None = None
        self.level_name_ldesc: str | None = None
        self._settled_raw = -1            # raw-log size at the last settled capture

    def level_key(self, status: Status | None = None) -> str:
        """Key for per-level memory (traps, avoid, visited): the overview
        name of the current level when known, else the status ldesc."""
        st = status if status is not None else (self.last.status if self.last is not None else None)
        ld = st.ldesc if st is not None else ""
        if self.level_name and self.level_name_ldesc == ld:
            return self.level_name
        return ld

    def rekey_level(self, old: str, new: str) -> None:
        """Merge per-level memory recorded under a provisional key."""
        if old == new:
            return
        for d in (self.traps, self.avoid, self.visited):
            if old in d:
                d.setdefault(new, set()).update(d.pop(old))
        if old in self.terrain_seen:
            self.terrain_seen.setdefault(new, {}).update(self.terrain_seen.pop(old))

    FEATURE_CHARS = "<>{_\\"

    def _remember_terrain(self, snap: Snap, messages: list[str]) -> None:
        """Remember stairs/fountains/altars/thrones per level so the one under
        the hero (hidden by the '@') is still known: sets snap.under."""
        if snap.hero is None or not snap.status.ok or _engulfed(snap.screen, snap.hero):
            return
        feats = self.terrain_seen.setdefault(self.level_key(snap.status), {})
        for y in range(MAP_TOP + snap.state.msg_rows, MAP_BOTTOM + 1):
            row = snap.screen.row(y)
            for x, ch in enumerate(row):
                if ch in self.FEATURE_CHARS:
                    feats[(x, y)] = ch
        for c in list(feats):
            if c != snap.hero and snap.screen.at(*c) in ".#" and c[1] > snap.state.msg_rows:
                del feats[c]           # e.g. a fountain that dried up
        if any("dries up" in m for m in messages):
            feats.pop(snap.hero, None)
        snap.under = feats.get(snap.hero)

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
        if status.ok:
            if status.hd is None:
                self.real_xl = status.xl
            else:
                # polymorphed: the status line shows HD instead of Xp; keep the
                # hero's own level in .xl so scripts keyed on it stay sane
                status.polymorphed = True
                status.xl = self.real_xl or 0
            self.last_status = status
        elif st.kind not in ("command", "unknown") and self.last_status is not None:
            # a menu/text window covers the status lines: report the last
            # readable status, flagged stale
            status = copy.copy(self.last_status)
            status.conditions = list(status.conditions)
            status.stale = True
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
            # At the command prompt the cursor sits on the hero, drawn as '@'
            # unless polymorphed (status shows HD) or hallucinating. Anything
            # else means the final redraw/cursor placement hasn't arrived yet
            # (seen after a --More-- interrupted a travel).
            st = snap.status
            if ch != "@" and st.hd is None and "Hallu" not in st.conditions:
                return False
            if cy == 1:
                return False   # the hero never stands on map row 1 (level edge): likely wrapped text
            if _explosion_frame(snap.screen):
                return False   # an explosion animation is still on screen (explode() puts the cursor on @)
        return True

    def _settle(self, size0: int, expect_output: bool = True) -> Snap:
        t = self.timing
        first = t.first if expect_output else min(t.first, t.quiet * 4)
        self.term.wait_quiet(size0, first, t.quiet, t.max_wait)
        snap = self.capture()
        self._settled_raw = self.term.raw_size()
        stable = 0
        for _ in range(t.recheck):
            if self._plausible(snap):
                break
            size1 = self.term.raw_size()
            self.term.wait_quiet(size1, t.quiet * 3, t.quiet, t.max_wait)
            prev, snap = snap, self.capture()
            self._settled_raw = self.term.raw_size()
            # an implausible screen that no longer changes is the real one
            # (invisible hero with no '@' drawn, odd displays): stop waiting
            if snap.screen.chars == prev.screen.chars and snap.screen.cursor == prev.screen.cursor \
                    and self.term.raw_size() == size1:
                stable += 1
                if stable >= 3:
                    break
            else:
                stable = 0
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
    # ---- safety guards (refuse keystrokes that are classic instant deaths) ----
    NEVER_MELEE = ("floating eye", "gas spore", "green slime")
    _MOVE = {ord("h"): (-1, 0), ord("j"): (0, 1), ord("k"): (0, -1), ord("l"): (1, 0),
             ord("y"): (-1, -1), ord("u"): (1, -1), ord("b"): (-1, 1), ord("n"): (1, 1)}
    _CORPSE_Q = re.compile(r"There (?:is|are) (?:an? |\d+ )?(.+?) corpses? here; eat (?:it|one)\?")

    def _guard(self, snap: "Snap", unit: bytes, force: bool) -> None:
        if force or not unit:
            return
        k = snap.state.kind
        if k == "command":
            key = unit[1] if unit[:1] == b"F" and len(unit) > 1 else unit[0] if len(unit) == 1 else None
            step = unit[1] if unit[:1] == b"m" and len(unit) == 2 else unit[0] if len(unit) == 1 else None
            if step in self._MOVE and snap.hero is not None and snap.status.ok:
                dx, dy = self._MOVE[step]
                tx, ty = snap.hero[0] + dx, snap.hero[1] + dy
                if (tx, ty) in self.traps.get(self.level_key(snap.status), ()):
                    raise PermissionError(
                        f"refusing to step onto the known trap at {(tx, ty)} (NetHack doesn't ask). Go around "
                        "(travel() avoids traps), or force=True if you mean it (jumping into a hole/trap "
                        "door on purpose, entering a magic portal).")
            conds = set(snap.status.conditions) if snap.status.ok else set()
            if key in self._MOVE and snap.hero is not None:
                dx, dy = self._MOVE[key]
                tx, ty = snap.hero[0] + dx, snap.hero[1] + dy
                target = snap.screen.at(tx, ty)
                if "Hallu" in conds and target in MONSTER_CHARS:
                    raise PermissionError(
                        f"refusing to attack/move into the monster at {(tx, ty)} while hallucinating: you can't "
                        "tell what it is (a peaceful? a floating eye?) and NetHack does NOT ask 'Really attack?' "
                        "while you hallucinate. Wait it out, cure it (unicorn horn), or force=True if it is "
                        "certainly hostile (it attacked you).")
                if "Blind" in conds and target == "I":
                    raise PermissionError(
                        f"refusing to attack the remembered unseen monster 'I' at {(tx, ty)} while blind: it may be "
                        "a peaceful (shopkeeper, priest, watchman) and NetHack does not ask when it can't see "
                        "it. force=True if it is attacking you.")
            if step in self._MOVE and snap.hero is not None and conds & {"Conf", "Stun"}:
                from .danger import base_name
                near = [m for m in snap.monsters or [] if m.get("dist") == 1 and not m.get("tame")
                        and (m.get("peaceful") or base_name(m.get("desc") or "") in self.NEVER_MELEE)]
                if near:
                    raise PermissionError(
                        "refusing to move while " + "/".join(sorted(conds & {"Conf", "Stun"})) + " next to "
                        + ", ".join(f"the {m.get('desc')} at ({m['x']},{m['y']})" for m in near)
                        + ": your step can go astray into it, and NetHack attacks without asking while you "
                        "are confused/stunned. Wait ('s') until it wears off, or force=True.")
            if key in self._MOVE and snap.hero is not None and "Blind" not in conds:
                dx, dy = self._MOVE[key]
                tx, ty = snap.hero[0] + dx, snap.hero[1] + dy
                for m in snap.monsters or []:
                    if (m["x"], m["y"]) == (tx, ty):
                        from .danger import base_name
                        name = base_name(m.get("desc") or "")
                        if name in self.NEVER_MELEE:
                            raise PermissionError(
                                f"refusing to attack/move into the {name} at {(tx, ty)}: meleeing it is a "
                                f"classic death ({'paralysis' if name == 'floating eye' else 'explosion' if name == 'gas spore' else 'sliming'}). "
                                "Use ranged attacks or go around. force=True overrides.")
        elif k in ("getlin", "object") and "genocide" in (snap.state.prompt or "").lower():
            why = _genocide_danger(snap.state.prompt, unit.decode(errors="replace"))
            if why:
                raise PermissionError(why + " force=True overrides.")
        elif k in ("yn", "getlin") and unit[:1] in (b"y", b"Y") and "Really attack" in (snap.state.prompt or ""):
            # NetHack only asks this about peaceful monsters
            raise PermissionError(
                "refusing to confirm 'Really attack ...?': the target is PEACEFUL. Killing peacefuls costs "
                "alignment and Luck, angers your god, and in Minetown the Watch; a shopkeeper or priest "
                "will kill you. Answer no (<Esc>). force=True overrides.")
        elif k == "yn" and unit[:1] in (b"y", b"Y"):
            m = self._CORPSE_Q.search(snap.state.prompt or "")
            if m:
                try:
                    from .data.corpses import corpse_verdict
                    from .danger import base_name
                    name = base_name(m.group(1))
                    v = corpse_verdict(name, hero_race="dwarf", hero_role="Valkyrie", age_turns=0,
                                       has_poison_res=False)
                    verdict = getattr(v.verdict, "value", v.verdict)
                except Exception:
                    return
                if verdict == "NEVER":
                    raise PermissionError(f"refusing to eat the {name} corpse: " + "; ".join(v.reasons)
                                          + " — force=True overrides.")

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
             multi: bool = False, secret: bool = False, force: bool = False) -> Snap:
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
            cur = self.last
            if cur is None or (self.term is not None and self.term.raw_size() != self._settled_raw):
                cur = self.capture()      # output arrived since we last looked: decide on the real screen
            kind = cur.state.kind
            if not force and data:
                if kind == "dead":
                    raise PermissionError("the game process has exited (terminal dead): nothing to send. "
                                          "Look at `nh screen`; reconnect/restart per the runbook.")
                if kind == "gameover" and any(b not in b"ynqYNQ \r\n\x1b" for b in data):
                    raise PermissionError("the game is over: only y/n/q, space, Enter or Esc answer the end-of-game "
                                          "questions. Never start a new game without the human's go-ahead. "
                                          "force=True to send other keys.")
                if kind == "dgl":
                    raise PermissionError("this is the server lobby (dgamelaunch), not the game: a key here can "
                                          "start a game, enter a tournament or change settings. Use the "
                                          "tactics.server helpers, or force=True after reading the screen.")
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
                try:
                    self._guard(snap, unit, force)
                except PermissionError as e:
                    if not sent_any:
                        raise
                    unsent = data[i:]
                    stop_reason = str(e)
                    break
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
                    self.visited.setdefault(self.level_key(snap.status), set()).add(snap.hero)
                    moved = cur.status.ok and cur.status.ldesc != snap.status.ldesc
                    self._note_traps(snap, messages, moved_level=moved)
                    self._remember_terrain(snap, messages)
            if snap.hero is not None:
                snap.engulfed = _engulfed(snap.screen, snap.hero)
            if self.tracker is not None and snap.state.kind == "command":
                try:
                    snap.monsters = self.tracker.update(snap)
                except Exception as e:  # noqa: BLE001
                    self.log_event({"ev": "tracker_error", "err": repr(e)})
            elif snap.state.kind in ("yn", "direction", "object", "getlin", "count", "getpos") \
                    and cur is not None and cur.monsters:
                snap.monsters = cur.monsters   # a prompt takes no time: the last labels still apply
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

    # Messages meaning the hero is standing on a trap *now* (teleporters, trap
    # doors, holes and portals move you away, so they're not listed; their '^'
    # is picked up from the map or the per-level #terrain scan instead).
    _TRAP_MSG = re.compile(
        r"(^There is an? .*\b(trap|pit|web)\b.* here\.|^You escape an? |An arrow shoots out at you|"
        r"A little dart shoots out at you|bear trap closes on your|You are caught in an? bear trap|"
        r"^You (fall|step|tumble|jump|land) into an? pit|on a set of sharp iron spikes|A board beneath you|"
        r"loose board below you|crease in the linoleum|spider web!|A cloud of gas puts you to sleep|"
        r"You are enveloped in a cloud of gas|A gush of water hits|tower of flame|momentarily lethargic|"
        r"momentarily blinded by a flash of light|You trigger a rolling boulder trap|triggered an? land mine|"
        r"You (step onto|float over|fly over|feel) an? polymorph trap|^You (float|fly) over an? )")

    def _note_traps(self, snap: Snap, messages: list[str], moved_level: bool = False) -> None:
        """Remember trap squares per level: every displayed '^', and the hero's
        square when a trap message fires there (objects can hide a trap)."""
        if snap.hero is not None and _engulfed(snap.screen, snap.hero):
            return
        lv = self.level_key(snap.status)
        known = self.traps.setdefault(lv, set())
        # a seen trap stays drawn as '^' unless something stands/lies on it:
        # plain floor/corridor there means it's gone (disarmed, used up, filled)
        for c in list(known):
            if c != snap.hero and snap.screen.at(*c) in ".#" and c[1] > snap.state.msg_rows:
                known.discard(c)
        for y in range(1 + snap.state.msg_rows, 22):
            row = snap.screen.row(y)
            x = row.find("^")
            while x >= 0:
                known.add((x, y))
                x = row.find("^", x + 1)
        if not moved_level and snap.hero is not None and any(self._TRAP_MSG.search(m) for m in messages):
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

    def terrain_traps(self) -> set | None:
        """Every trap the hero knows on this level, from NetHack's own memory:
        #terrain -> "known map without monsters and objects" shows remembered
        traps even under objects (and webs as '"'). No game time. Returns
        the set of trap squares, or None if the view couldn't be read (e.g.
        hallucinating/confused: "You are too disoriented for this.")."""
        with self.lock:
            saved = self.last
            try:
                s = self.send_bytes(b"#terrain\r")
                if s.state.kind != "menu" or not s.state.menu:
                    self._leave_getpos(s)
                    return None
                letter = None
                for it in s.state.menu.selectable():
                    if "without monsters and objects" in it.text:
                        letter = it.letter
                if letter is None:
                    self.send_bytes(b"\x1b")
                    return None
                s = self.send_bytes(letter.encode())
                for _ in range(3):
                    if s.state.kind not in ("more", "text"):
                        break
                    s = self.send_bytes(s.state.dismiss.encode())
                found = None
                browsing = "Showing known terrain" in s.screen.row(0) or s.state.kind == "getpos"
                if browsing:
                    found = set()
                    for y in range(MAP_TOP + 1, MAP_BOTTOM + 1):
                        row = s.screen.row(y)
                        for x, ch in enumerate(row):
                            if ch == "^" or ch == '"':
                                found.add((x, y))
                self._leave_getpos(s, in_getpos=browsing)
                self.log_event({"ev": "terrain_traps", "ts": round(time.time(), 3),
                                "traps": sorted(found) if found is not None else None})
                return found
            finally:
                self.last = saved

    def describe_cells(self, cells: list[tuple[int, int]]) -> dict:
        """Describe several map cells in one ';' session: turn on getpos
        autodescribe ('#'), move the cursor to each cell and read NetHack's
        own description off the top line ("peaceful dwarf", "jackal"), then
        turn autodescribe off again and leave with ESC. No game time. Costs
        about one keystroke per cell instead of ~4 for separate farlooks.
        Returns {(x, y): raw description}; cells it couldn't read are
        missing. A single cell uses farlook() (cheaper for one)."""
        cells = list(dict.fromkeys(cells))
        if len(cells) <= 1:
            return {c: self.farlook(*c) for c in cells}
        out: dict = {}
        with self.lock:
            saved = self.last
            try:
                s = self.send_bytes(b";")
                if s.state.kind != "getpos":
                    if s.state.kind != "command":
                        self.send_bytes(b"\x1b")
                    return out
                on = False
                for _ in range(2):
                    s = self.send_bytes(b"#")
                    top = s.screen.row(0)
                    if "Automatic description" not in top:
                        break
                    if " is on" in top:
                        on = True
                        break
                if not on:
                    self._leave_getpos(s, in_getpos=True)
                    return {c: self.farlook(*c) for c in cells}
                for (x, y) in cells:
                    for _ in range(3):
                        cx, cy = s.screen.cursor
                        if (cx, cy) == (x, y):
                            break
                        s = self.send_bytes(_cursor_keys(cx, cy, x, y).encode())
                    if s.screen.cursor == (x, y) and s.state.kind == "getpos":
                        out[(x, y)] = s.screen.row(0).strip()
                    elif s.state.kind != "getpos":
                        break
                # autodescribe off again (prints its message plus the goal
                # prompt, usually with a --More-- between them), then leave
                if s.state.kind == "getpos":
                    s = self.send_bytes(b"#")
                    for _ in range(3):
                        if s.state.kind not in ("more", "text"):
                            break
                        s = self.send_bytes(s.state.dismiss.encode())
                    if "is on" in s.screen.row(0):   # we toggled the wrong way: once more
                        s = self.send_bytes(b"#")
                self._leave_getpos(s, in_getpos=True)
                self.log_event({"ev": "describe", "ts": round(time.time(), 3),
                                "cells": {f"{x},{y}": d for (x, y), d in out.items()}})
                return out
            finally:
                self.last = saved

    def _leave_getpos(self, s: Snap, in_getpos: bool = False) -> Snap:
        """Back to the command prompt from a position prompt (or a --More--
        on the way out). in_getpos=True: we know a position prompt is open,
        so send ESC even if the screen reads like the command state."""
        for i in range(4):
            if in_getpos and i == 0 and s.state.kind not in ("more", "text"):
                s = self.send_bytes(b"\x1b")
                continue
            if s.state.kind == "command" and not self.getpos_active and self._plausible(s):
                break
            if s.state.kind in ("more", "text"):
                s = self.send_bytes(s.state.dismiss.encode())
            else:
                s = self.send_bytes(b"\x1b")
        return s

    def look(self) -> Snap:
        """Capture without sending anything."""
        with self.lock:
            snap = self.capture()
            if self.last is not None:
                snap.messages = []
            if snap.hero is not None:
                self.hero_pos = snap.hero
                snap.engulfed = _engulfed(snap.screen, snap.hero)
                self._remember_terrain(snap, [])
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
