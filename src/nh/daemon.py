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
        timing = Timing.remote() if self.meta.get("kind") == "remote" else Timing.local()
        self.term = TmuxTerminal(self.meta["tmux_session"], self.dir / "raw.log",
                                 width=self.meta.get("width", 80), height=self.meta.get("height", 24))
        self.game = Game(self.term, timing, log_path=self.dir / "events.jsonl")
        self.kernel = Kernel(self.game)
        self.tracker = MonsterTracker(self.game)
        self.game.tracker = self.tracker
        self.memory = Tracker(self.game, self.dir / "harness_state.json")
        self.game.on_step.append(self.memory.on_step)
        # make repo-level tactic/view packages importable in the kernel
        for p in (REPO_ROOT / "play", REPO_ROOT / "src"):
            if str(p) not in sys.path:
                sys.path.insert(0, str(p))
        self.kernel.ns["GAME_NAME"] = name
        self.kernel.ns["META"] = self.meta
        self._bootstrap_kernel()
        self.stop = False

    def _bootstrap_kernel(self):
        boot = REPO_ROOT / "play" / "kernel_boot.py"
        if boot.exists():
            try:
                code = compile(boot.read_text(), str(boot), "exec")
                exec(code, self.kernel.ns)
            except Exception:
                self.game.log_event({"ev": "boot_error", "tb": traceback.format_exc()})

    def render(self, snap, mode="crop") -> str:
        if snap is not None and snap.state.kind == "command" and self.memory.need_overview \
                and not self.kernel.busy():
            try:
                self.memory.refresh_overview()
            except Exception as e:  # noqa: BLE001
                self.game.log_event({"ev": "overview_error", "err": repr(e)})
        text = render.render(snap, mode=mode, mons=snap.monsters if snap is not None else None,
                             hero=self.game.hero_pos)
        where = self.memory.state.get("current_level")
        if where and mode != "brief":
            text = text.replace("\n", f"\nwhere: {where}\n", 1)
        return text

    # ------------------------------------------------------------ handlers
    def handle(self, req: dict) -> dict:
        op = req.get("op")
        mode = req.get("mode", "crop")
        if op == "ping":
            return {"ok": True, "text": f"nh daemon {self.name} alive (pid {os.getpid()})"}
        if op == "obs":
            self.kernel.drop()
            snap = self.game.look()
            self.kernel.ns["obs"] = snap
            return {"ok": True, "text": self.render(snap, mode=req.get("mode", "full"))}
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
                                         monsters=req.get("monsters", True), hp_pause=req.get("hp_pause"))
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
        lines.append("  -> nh cont (resume) | nh cont --reply KEYS | any other command drops it")
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
