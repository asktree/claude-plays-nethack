"""Persistent Python kernel with pause-on-event execution.

`exec(code)` runs player code in a worker thread. Inside it, every `do(keys)`
performs one game step and then checks for events worth a human look:
messages, HP loss, new monsters, status conditions, level change, game over.
On such an event the worker parks inside `do()` and control returns to the
player with the reason. `cont()` resumes; any other request abandons the
parked code (the game state is consistent at the pause boundary).
"""

from __future__ import annotations

import builtins
import io
import linecache
import queue
import re
import sys
import threading
import time
import traceback
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable

from .game import Game, Snap
from .keys import parse_keys
from .parse import MAP_BOTTOM, MAP_TOP, MONSTER_CHARS, HUNGER, ENCUMBRANCE

_HUNGER_RANK = {"": 0, "Satiated": 0, "Hungry": 1, "Weak": 2, "Fainting": 3, "Fainted": 4}


# Messages that never need a human look by themselves (pets, routine
# noises). They're still shown in the output; they just don't pause an exec.
DEFAULT_BENIGN = [re.compile(p) for p in (
    r"^(The |Your )?[\w' -]+ (picks up|drops|eats|is eating|finishes eating) ",
    r"^You swap places with ",
    # monster-vs-monster melee (mhitm.c), usually your pet's fights; a death, stoning or
    # swallowing still pauses
    r"^(?:The |Your )?[\w' -]+? (?:misses|bites|stings|butts|touches|hits|squeezes) "
    r"(?:the [\w' -]+|it|itself|himself|herself)\.$",
    r"^You stop\. .* is in your way",
    r"^You stop\.$",                                   # "You stop.  Your kitten is in your way." is split
    r"^(Your|The) .* is in your way\.$",
    r"^(Your|The) .* is in the way!$",                 # uhitm.c: 1/7 of pet swaps fail (or in a shop)
    r"^(Your|The) .* doesn't seem to move!$",          # a frozen pet you tried to swap with
    r"^You move .* out of your way",
    r"^You see here ",
    r"^Things that are here:",
    # level sounds (sounds.c dosounds): recorded per level by the tracker (`nh info`);
    # the beehive and barracks sounds still pause
    r"^You hear (bubbling water|water falling on coins|the splashing of a naiad|a soda fountain|a slow drip|"
    r"a gurgling noise|dishes being washed|the tones of courtly conversation|a sceptre pounded|"
    r"Queen Beruthiel's cats|mosquitoes|Donald Duck|someone counting money|the quarterback calling|"
    r"someone searching|the footsteps of a guard on patrol|Ebenezer Scrooge|a sound reminiscent of|"
    r"Doctor Dolittle|someone cursing shoplifters|the chime of a cash register|Neiman and Marcus|"
    r"someone praising|someone beseeching|an animal carcass being offered|a strident plea|"
    r"a strange wind|convulsive ravings|snoring snakes|someone say|a loud ZOT|crashing rock)",
    r"^You smell marsh gas",
    r"^You suddenly realize it is unnaturally quiet",
    r"on the back of your .* (stand|stands) up",
    r"^You see no objects here",
    r"^There (is|are) (a|an|several|many|\d+) .* here\.?$",
    r"^You hear (some noises|a door open|the footsteps of a guard|bubbling water|water falling|the splashing|a gurgling|a slow drip|a chugging|someone counting money|the chime of a cash register|someone cursing shoplifters)",
    r"^You hear some noises in the distance",
    r"^\$ - (\d+|a) gold pieces?\.",
    r"^[a-zA-Z] - (?!.*\b(cursed|loadstone)\b).*\.$",   # pickup/inventory result "i - a scroll ..."
    r"^The door opens\.",
    r"^You stop in front of the door\.",
    r"^You are in full health\.",                      # a counted search/rest stops at full HP
    r"^You drop (?!.*\b(?:loadstone)\b).*\.$",          # result of your own drop command
    r"^Your (?!wielded ).*\b(corpse|corpses|egg|eggs)\b.* rots? away\.$",   # carried food rotting
)]


class Abandon(BaseException):
    """Raised inside a parked worker to unwind it."""


class PauseRequested(Exception):
    pass


class _ThreadStdout(io.TextIOBase):
    """sys.stdout proxy: writes from registered threads go to their buffers."""

    def __init__(self, real):
        self.real = real
        self.buffers: dict[int, io.StringIO] = {}

    def write(self, s):
        buf = self.buffers.get(threading.get_ident())
        if buf is not None:
            return buf.write(s)
        return self.real.write(s)

    def flush(self):
        try:
            self.real.flush()
        except Exception:
            pass


_STDOUT = None


def _install_stdout():
    global _STDOUT
    if _STDOUT is None:
        _STDOUT = _ThreadStdout(sys.stdout)
        sys.stdout = _STDOUT
    return _STDOUT


def monster_counts(snap: Snap) -> Counter:
    c: Counter = Counter()
    scr = snap.screen
    hero = snap.hero
    for y in range(MAP_TOP, MAP_BOTTOM + 1):
        row = scr.row(y)
        for x, ch in enumerate(row):
            if ch in MONSTER_CHARS and (hero is None or (x, y) != hero):
                c[(ch, scr.color_at(x, y), scr.reverse_at(x, y))] += 1
    return c


@dataclass
class PauseInfo:
    reason: str
    snap: Snap
    where: list[dict] = field(default_factory=list)


class Kernel:
    def __init__(self, game: Game):
        self.game = game
        self.ns: dict[str, Any] = {"__name__": "__nhkernel__", "__builtins__": builtins}
        self.worker: threading.Thread | None = None
        self.events: queue.Queue = queue.Queue()
        self.resume = threading.Event()
        self.abandon_flag = False
        self.autocontinue: list[re.Pattern] = []
        self.pause_on_monsters = True
        self.parked = False        # True while an exec worker waits at a pause point
        self.hp_pause = 0.7        # pause on HP loss when HP < this fraction of max...
        self.hp_hit_pause = 0.15   # ...or when one step costs >= this fraction of max
        self.budget_steps = 400
        self.budget_seconds = 110.0
        self._steps = 0
        self._t0 = 0.0
        self._prev: Snap | None = None
        self._pending_reply: str | None = None
        self.code_counter = 0
        self._stdout = _install_stdout()
        self._install_api()

    # ------------------------------------------------------------------ api
    def _install_api(self) -> None:
        k = self

        def do(keys: str, *, force: bool = False, quiet: bool = False, ok=None, multi: bool = False,
               secret: bool = False) -> Snap:
            """Send keys (see nh.keys notation); returns the settled snapshot.

            quiet=True: messages from this step don't pause an exec (HP loss,
            new monsters, status changes and game over still do). For
            information-only keystrokes like farlook or inventory display.
            ok=[regex,...]: messages matching any of these don't pause (this
            step only), on top of the exec's autocontinue list."""
            return k._do(keys, force=force, quiet=quiet, ok=ok, multi=multi, secret=secret)

        def look() -> Snap:
            """Re-capture the screen without sending anything."""
            s = k.game.look()
            k.ns["obs"] = s
            return s

        def pause(reason: str = "script pause") -> None:
            """Hand control back to the player (inside exec)."""
            k._maybe_pause(reason, k.game.last or k.game.look(), force=True)

        def note(text: str) -> None:
            k.game.log_event({"ev": "note", "ts": round(time.time(), 3), "text": text})

        self.ns.update(do=do, look=look, pause=pause, note=note, game=self.game)
        self.ns["obs"] = self.game.last

    # --------------------------------------------------------- stepping
    def in_worker(self) -> bool:
        return self.worker is not None and threading.current_thread() is self.worker

    def _do(self, keys: str, force: bool = False, quiet: bool = False, ok=None, multi: bool = False,
            secret: bool = False) -> Snap:
        data = parse_keys(keys) if isinstance(keys, str) else keys
        _guard_dangerous(data, force)
        cur = self.game.last or self.game.look()
        if self.in_worker():
            if self.abandon_flag:
                raise Abandon()
            # prompt-swallow check: a [yn]-style prompt ignores other keys
            if cur.state.kind == "yn" and data:
                if cur.state.choices == "yes/no":       # typed answer: "yes<CR>" / "no<CR>" / <Esc>
                    allowed = set("yYnN\x1b\r\n")
                else:
                    allowed = set(cur.state.choices.replace(" ", "")) | {"\x1b", "\r", "\n"}
                if chr(data[0]) not in allowed:
                    self._maybe_pause(
                        f"prompt open: {cur.state.prompt!r} accepts [{cur.state.choices}] "
                        f"but code sent {keys!r} (not sent). Answer with cont(reply=...)", cur, force=True,
                        sent=False)
                    cur = self.game.last or cur
            self._steps += 1
        before = self.game.last
        snap = self.game.step(data, multi=multi, secret=secret, force=force)
        self.ns["obs"] = snap
        if self.in_worker():
            self._check_events(before, snap, quiet=quiet, ok=ok)
            if snap.state.kind == "command" and (self._steps >= self.budget_steps or
                                                 time.monotonic() - self._t0 >= self.budget_seconds):
                # (only at the command prompt: never park a script inside a menu/cursor prompt)
                self._maybe_pause(
                    f"budget: {self._steps} steps / {time.monotonic() - self._t0:.0f}s in this exec "
                    f"— cont() to keep going", snap, force=True)
        return snap

    def _check_events(self, before: Snap | None, snap: Snap, quiet: bool = False, ok=None) -> None:
        reasons = []
        if snap.state.kind in ("gameover", "dead"):
            reasons.append("GAME OVER" if snap.state.kind == "gameover" else "TERMINAL DEAD")
        extra = [re.compile(p) if isinstance(p, str) else p for p in (ok or [])]
        msgs = [m for m in snap.messages
                if not any(p.search(m) for p in self.autocontinue)
                and not any(p.search(m) for p in extra)
                and not any(p.search(m) for p in DEFAULT_BENIGN)]
        if msgs and not quiet:
            reasons.append("message")
        trapmsg = [m for m in snap.messages if self.game._TRAP_MSG.search(m)
                   and not m.startswith("There is")]
        if trapmsg and snap.hero is not None and not quiet:
            reasons.append(f"trap at {snap.hero}")
        if snap.state.kind == "getlin" and (snap.state.prompt or "").startswith("Call ") \
                and not (before is not None and before.state.kind == "getlin"):
            # e.g. a scroll of scare monster crumbled on pickup: the game asks you to name
            # the type; the script's next keys would be typed into this prompt
            reasons.append(f"naming prompt open: {snap.state.prompt!r} — type a name + <CR> or <Esc>")
        if before is not None and before.status.ok and snap.status.ok:
            b, a = before.status, snap.status
            if a.hp < b.hp:
                big_hit = (b.hp - a.hp) >= max(4, self.hp_hit_pause * max(1, a.hpmax))
                low = a.hp < self.hp_pause * max(1, a.hpmax)
                if big_hit or low:
                    reasons.append(f"HP {b.hp}->{a.hp}/{a.hpmax}")
            new_conds = [c for c in a.conditions if c not in b.conditions]
            if new_conds:
                reasons.append("status: +" + ",".join(new_conds))
            if _HUNGER_RANK.get(a.hunger, 0) > _HUNGER_RANK.get(b.hunger, 0):
                reasons.append(f"hunger: {a.hunger}")
            if a.encumbrance != b.encumbrance:
                reasons.append(f"encumbrance: {a.encumbrance or 'unencumbered'}")
            if a.ldesc != b.ldesc:
                reasons.append(f"level: {b.ldesc} -> {a.ldesc}")
            if a.xl != b.xl:
                reasons.append(f"XL {b.xl}->{a.xl}")
            if a.polymorphed != b.polymorphed or (a.polymorphed and a.hd != b.hd):
                reasons.append(f"polymorphed (HD:{a.hd}; own XL {a.xl})" if a.polymorphed
                               else "back in your own form")
        if self.pause_on_monsters and snap.state.kind == "command":
            if snap.monsters:
                new = [m for m in snap.monsters if m.get("new") and not m.get("statue")
                       and not m.get("tame") and not m.get("peaceful")]
                if new:
                    reasons.append("new monster: " + ", ".join(
                        f"{m.get('desc') or m['ch']} at ({m['x']},{m['y']})" for m in new[:4]))
            elif before is not None and before.state.kind == "command" and self.game.tracker is None:
                prev = monster_counts(before)
                now = monster_counts(snap)
                new = [f"{ch}" for (ch, col, rev), n in now.items() if n > prev.get((ch, col, rev), 0) and not rev]
                if new:
                    reasons.append("new monster in view: " + ",".join(sorted(set(new))))
        if reasons:
            self._maybe_pause("; ".join(reasons), snap)

    def _maybe_pause(self, reason: str, snap: Snap, force: bool = False, sent: bool = True) -> None:
        if not self.in_worker():
            return
        where = _user_frames()
        self.events.put(("paused", PauseInfo(reason=reason, snap=snap, where=where)))
        self.resume.clear()
        self.parked = True
        try:
            self.resume.wait()
        finally:
            self.parked = False
        if self.abandon_flag:
            raise Abandon()
        # reset budget on every resume
        self._steps = 0
        self._t0 = time.monotonic()
        if self._pending_reply is not None:
            r, self._pending_reply = self._pending_reply, None
            snap2 = self.game.step(parse_keys(r))
            self.ns["obs"] = snap2

    # ---------------------------------------------------------- exec api
    def busy(self) -> bool:
        return self.worker is not None and self.worker.is_alive()

    def start_exec(self, code: str, autocontinue: list[str] | None = None,
                   monsters: bool = True, hp_pause: float | None = None) -> dict:
        self.drop()
        self.autocontinue = [re.compile(p) for p in (autocontinue or [])]
        self.pause_on_monsters = monsters
        self.hp_pause = 0.7 if hp_pause is None else float(hp_pause)
        self.code_counter += 1
        fname = f"<exec-{self.code_counter}>"
        linecache.cache[fname] = (len(code), None, code.splitlines(True), fname)
        try:
            compiled = compile(code, fname, "exec")
        except SyntaxError as e:
            return {"status": "error", "error": f"SyntaxError: {e}", "stdout": ""}
        self.abandon_flag = False
        self.events = queue.Queue()
        self._steps = 0
        self._t0 = time.monotonic()
        buf = io.StringIO()

        def run():
            self._stdout.buffers[threading.get_ident()] = buf
            try:
                result = None
                exec(compiled, self.ns)
                result = self.ns.pop("_result", None)
                self.events.put(("done", {"result": result}))
            except Abandon:
                self.events.put(("abandoned", {}))
            except BaseException as e:  # noqa: BLE001
                tb = traceback.format_exc(limit=8)
                self.events.put(("error", {"error": f"{type(e).__name__}: {e}", "traceback": tb}))
            finally:
                self._stdout.buffers.pop(threading.get_ident(), None)

        self._buf = buf
        self.worker = threading.Thread(target=run, name="nh-exec", daemon=True)
        self.worker.start()
        return self._wait()

    def cont(self, reply: str | None = None, autocontinue: list[str] | None = None) -> dict:
        if not self.busy():
            return {"status": "error", "error": "nothing is paused", "stdout": ""}
        if autocontinue is not None:
            self.autocontinue = [re.compile(p) for p in autocontinue]
        self._pending_reply = reply
        self.resume.set()
        return self._wait()

    def _wait(self) -> dict:
        while True:
            try:
                kind, info = self.events.get(timeout=0.5)
            except queue.Empty:
                if not self.worker.is_alive():
                    kind, info = "error", {"error": "worker died"}
                else:
                    continue
            out = self._buf.getvalue()
            self._buf.seek(0)
            self._buf.truncate()
            if kind == "paused":
                return {"status": "paused", "reason": info.reason, "snap": info.snap,
                        "where": info.where, "stdout": out}
            if kind == "done":
                self.worker = None
                return {"status": "done", "result": info.get("result"), "stdout": out,
                        "snap": self.game.last}
            if kind == "abandoned":
                self.worker = None
                return {"status": "abandoned", "stdout": out, "snap": self.game.last}
            self.worker = None
            return {"status": "error", "error": info.get("error"), "traceback": info.get("traceback", ""),
                    "stdout": out, "snap": self.game.last}

    def drop(self) -> str:
        """Abandon a paused exec, if any."""
        if not self.busy():
            self.worker = None
            return ""
        self.abandon_flag = True
        self.resume.set()
        self.worker.join(timeout=10)
        self.worker = None
        # drain
        while not self.events.empty():
            try:
                self.events.get_nowait()
            except queue.Empty:
                break
        return "dropped paused exec"

    # direct (non-exec) step used by `nh do`
    def direct_do(self, keys: str, force: bool = False, multi: bool = False) -> Snap:
        self.drop()
        data = parse_keys(keys)
        _guard_dangerous(data, force)
        snap = self.game.step(data, multi=multi, force=force)
        self.ns["obs"] = snap
        return snap


_DANGEROUS = [
    (re.compile(rb"#\s*quit", re.I), "#quit ends the game"),
    (re.compile(rb"\x1bq"), "M-q is #quit"),
    (re.compile(rb"^\xf1"), "M-q is #quit"),
]


def _guard_dangerous(data: bytes, force: bool) -> None:
    if force:
        return
    for rx, why in _DANGEROUS:
        if rx.search(data):
            raise PermissionError(f"refusing to send {data!r}: {why}. Pass force=True if you really mean it.")


def _user_frames() -> list[dict]:
    frames = []
    for fs in traceback.extract_stack()[:-2]:
        if fs.filename.startswith("<exec-") or "/tactics/" in fs.filename:
            frames.append({"file": fs.filename, "line": fs.lineno, "code": (fs.line or "").strip()})
    return frames[-6:]
