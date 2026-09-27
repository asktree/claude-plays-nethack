"""Per-game daemon: owns the tmux terminal + kernel, serves the `nh` CLI.

Protocol: one JSON request per connection on run/<game>/daemon.sock; the
reply is one JSON object {ok, text, ...}. Requests are served one at a time.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import signal
import socket
import sys
import threading
import time
import traceback
from pathlib import Path

from . import render
from .game import Game, Timing
from .kernel import Kernel
from .monitor import MonsterTracker
from .tracker import Tracker
from .paths import game_dir, load_meta, REPO_ROOT
from .tmuxterm import TmuxTerminal


class Daemon:
    def __init__(self, name: str):
        self.name = name
        self.dir = game_dir(name)
        self.meta = load_meta(name)
        from . import danger
        danger.HERO_GENDER = (self.meta.get("character") or {}).get("gender") or danger.HERO_GENDER
        timing = Timing.remote() if self.meta.get("kind") == "remote" else Timing.local()
        self.term = TmuxTerminal(self.meta["tmux_session"], self.dir / "raw.log",
                                 width=self.meta.get("width", 80), height=self.meta.get("height", 24))
        self.game = Game(self.term, timing, log_path=self.dir / "events.jsonl")
        self.kernel = Kernel(self.game)
        self._core_loaded = self._tactics_loaded = time.time()   # (the stale-code note in obs)
        self.tracker = MonsterTracker(self.game)
        self.game.tracker = self.tracker
        self.memory = Tracker(self.game, self.dir / "harness_state.json")
        self.game.memory = self.memory        # tactics read/write the harness memory through it
        self.game.on_step.append(self.memory.on_step)
        # make repo-level tactic/view packages importable in the kernel
        for p in (REPO_ROOT / "play", REPO_ROOT / "src"):
            if str(p) not in sys.path:
                sys.path.insert(0, str(p))
        self.kernel.ns["GAME_NAME"] = name
        self.kernel.ns["META"] = self.meta
        self._bootstrap_kernel()
        self.stop = False
        self.keepalive_after = float(os.environ.get("NH_KEEPALIVE_AFTER", "1200"))  # seconds of silence
        if self.meta.get("kind") == "remote":
            threading.Thread(target=self._keepalive_loop, name="nh-keepalive", daemon=True).start()

    def _keepalive_loop(self):
        """Public servers hang up after 30 min without game output (Hardfought:
        1800 s). When the game has been silent for keepalive_after seconds and
        sits at the command prompt, send ^R (redraw: no game time, produces
        output). Never touch a prompt/menu -- a hangup there only cancels the
        prompt, but typing into it could do real damage."""
        while not self.stop:
            time.sleep(30)
            try:
                idle = time.time() - self.term.raw_log.stat().st_mtime
            except FileNotFoundError:
                continue
            if idle < self.keepalive_after:
                continue
            if not self.game.lock.acquire(timeout=5):
                continue
            try:
                snap = self.game.capture()
                if snap.state.kind == "command":
                    self.game.send_bytes(b"\x12")
                    self.game.log_event({"ev": "keepalive", "ts": time.time(), "idle": round(idle)})
                else:
                    self.game.log_event({"ev": "keepalive_skipped", "ts": time.time(), "idle": round(idle),
                                         "state": snap.state.kind, "prompt": snap.state.prompt})
            except Exception as e:  # noqa: BLE001
                self.game.log_event({"ev": "keepalive_error", "err": repr(e)})
            finally:
                self.game.lock.release()

    def _bootstrap_kernel(self):
        boot = REPO_ROOT / "play" / "kernel_boot.py"
        if boot.exists():
            try:
                code = compile(boot.read_text(), str(boot), "exec")
                exec(code, self.kernel.ns)
            except Exception:
                self.game.log_event({"ev": "boot_error", "tb": traceback.format_exc()})

    @staticmethod
    def _code_mtime(sub: str) -> float:
        """Newest modification time of the harness's Python files under `sub` (src/nh or play/tactics)."""
        try:
            # (the CLI and the build/generator scripts never run inside a daemon: editing them isn't news)
            return max((p.stat().st_mtime for p in (REPO_ROOT / sub).rglob("*.py")
                        if p.name not in ("cli.py", "__main__.py")), default=0.0)
        except OSError:
            return 0.0

    def _stale_code_note(self) -> str:
        """'' unless harness code on disk is newer than what this daemon runs (edited after start/reload)."""
        core = self._code_mtime("src/nh") > self._core_loaded + 1
        tact = self._code_mtime("play/tactics") > self._tactics_loaded + 1
        if not (core or tact):
            return ""
        return ("!! harness code on disk is newer than this daemon's"
                + (" core (src/nh: only a daemon restart loads it — tell the orchestrator)" if core else "")
                + (" helpers (play/tactics: `bin/nh reload` between execs loads them)" if tact else ""))

    def render(self, snap, mode="crop") -> str:
        if snap is not None and snap.state.kind == "command" and self.memory.need_overview \
                and (not self.kernel.busy() or self.kernel.parked):
            key0 = self.game.level_key(snap.status) if snap.status.ok else None
            try:
                self.memory.refresh_overview()
                if key0 is not None and self.game.level_key(snap.status) != key0:
                    self.game.reannotate(snap)
            except Exception as e:  # noqa: BLE001
                self.game.log_event({"ev": "overview_error", "err": repr(e)})
        text = render.render(snap, mode=mode, mons=snap.monsters if snap is not None else None,
                             hero=self.game.hero_pos)
        where = self.memory.state.get("current_level")
        if where and mode != "brief":
            dm = (getattr(self.game, "desmap_ids", None) or {}).get(where)
            if dm and dm.get("level") and not dm.get("ambiguous"):
                where = f"{where} ({dm['level']} map at offset ({dm.get('ox')},{dm.get('oy')}): desmap.show())"
            text = text.replace("\n", f"\nwhere: {where}\n", 1)
        stale = self._stale_code_note()
        if stale:
            text = text.replace("\n", f"\n{stale}\n", 1) if "\n" in text else text + "\n" + stale
        return text

    # ------------------------------------------------------------ handlers
    def handle(self, req: dict) -> dict:
        op = req.get("op")
        mode = req.get("mode", "crop")
        if op == "ping":
            return {"ok": True, "text": f"nh daemon {self.name} alive (pid {os.getpid()})"}
        if op == "obs":
            # looking sends no keys: a paused exec stays paused (the worker waits on its resume event and
            # holds no lock), so `nh obs` then `nh cont` works
            snap = self.game.look()
            self.kernel.ns["obs"] = snap
            text = self.render(snap, mode=req.get("mode", "full"))
            if self.kernel.busy():
                text += "\n(an exec is PAUSED — `nh cont` resumes it; `nh do`/`exec` would drop it)"
            return {"ok": True, "text": text}
        if op == "screen":
            snap = self.game.look()
            return {"ok": True, "text": render.render_screen(snap)}
        if op == "do":
            try:
                snap = self.kernel.direct_do(req["keys"], force=req.get("force", False),
                                             multi=req.get("multi", False))
            except PermissionError as e:
                return {"ok": False, "text": str(e)}
            return {"ok": True, "text": self.render(snap, mode=mode)}
        if op == "exec":
            out = self.kernel.start_exec(req["code"], autocontinue=req.get("autocontinue"),
                                         monsters=req.get("monsters", True), hp_pause=req.get("hp_pause"),
                                         at_prompt=req.get("at_prompt", False))
            return {"ok": out["status"] in ("done", "paused"), "text": _fmt_exec(out, mode, self.render)}
        if op == "cont":
            out = self.kernel.cont(reply=req.get("reply"), autocontinue=req.get("autocontinue"))
            return {"ok": out["status"] in ("done", "paused"), "text": _fmt_exec(out, mode, self.render)}
        if op == "drop":
            return {"ok": True, "text": self.kernel.drop() or "nothing paused"}
        if op == "info":
            return {"ok": True, "text": self.memory.summary() + "\n\nlevels:\n" + self.memory.levels_text()
                    + ("\n\noverview (T:%s):\n%s" % (self.memory.state.get("overview_turn"),
                                                     self.memory.state.get("overview", "")))}
        if op == "history":
            n = int(req.get("n", 30))
            lines = [f"T:{t} {m}" for (t, m) in self.game.history[-n:]]
            return {"ok": True, "text": "\n".join(lines) or "(no messages yet)"}
        if op == "reload":
            names = [m for m in list(sys.modules) if m.split(".")[0] in ("tactics", "views", "nhlib")]
            reloaded = []
            for m in sorted(names):
                try:
                    importlib.reload(sys.modules[m])
                    reloaded.append(m)
                except Exception as e:  # noqa: BLE001
                    reloaded.append(f"{m} FAILED: {e}")
            self._bootstrap_kernel()
            self._tactics_loaded = time.time()
            return {"ok": True, "text": "reloaded: " + ", ".join(reloaded)}
        if op == "shutdown":
            self.kernel.drop()
            self.stop = True
            return {"ok": True, "text": "daemon stopping (tmux session left running)"}
        return {"ok": False, "text": f"unknown op {op!r}"}

    # ------------------------------------------------------------ server
    def serve(self):
        sock_path = self.dir / "daemon.sock"
        if sock_path.exists():
            sock_path.unlink()
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(str(sock_path))
        my_inode = sock_path.stat().st_ino
        srv.listen(8)
        srv.settimeout(1.0)
        (self.dir / "daemon.pid").write_text(str(os.getpid()))
        self.game.log_event({"ev": "daemon_start", "ts": time.time(), "pid": os.getpid()})
        while not self.stop:
            try:
                conn, _ = srv.accept()
            except socket.timeout:
                continue
            with conn:
                try:
                    data = b""
                    conn.settimeout(30)
                    while not data.endswith(b"\n"):
                        chunk = conn.recv(65536)
                        if not chunk:
                            break
                        data += chunk
                    req = json.loads(data.decode() or "{}")
                    try:
                        resp = self.handle(req)
                    except Exception as e:  # noqa: BLE001
                        resp = {"ok": False, "text": f"daemon error: {type(e).__name__}: {e}\n"
                                                     + traceback.format_exc(limit=6)}
                    conn.settimeout(None)
                    conn.sendall((json.dumps(resp) + "\n").encode())
                except Exception:  # noqa: BLE001
                    self.game.log_event({"ev": "conn_error", "tb": traceback.format_exc()})
        srv.close()
        try:
            if sock_path.stat().st_ino == my_inode:   # don't delete a successor's socket
                sock_path.unlink()
        except FileNotFoundError:
            pass


def _fmt_exec(out: dict, mode: str, render_fn) -> str:
    st = out["status"]
    lines = []
    if st == "paused":
        lines.append(f"[exec PAUSED] {out['reason']}")
        for fr in out.get("where", []):
            lines.append(f"  at {fr['file']}:{fr['line']}  {fr['code']}")
        lines.append("  -> nh cont (resume) | nh cont --reply KEYS | nh obs/screen keep it | do/exec drop it")
    elif st == "done":
        lines.append("[exec done]" + (f" result={out['result']!r}" if out.get("result") is not None else ""))
    elif st == "abandoned":
        lines.append("[exec abandoned]")
    else:
        lines.append(f"[exec ERROR] {out.get('error')}")
        if out.get("traceback"):
            lines.append(out["traceback"].rstrip())
    if out.get("stdout"):
        lines.append("--- stdout ---")
        lines.append(out["stdout"].rstrip())
        lines.append("--------------")
    snap = out.get("snap")
    if snap is not None:
        lines.append(render_fn(snap, mode=mode))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", required=True)
    args = ap.parse_args()
    d = Daemon(args.game)
    signal.signal(signal.SIGTERM, lambda *a: setattr(d, "stop", True))
    d.serve()


if __name__ == "__main__":
    main()
