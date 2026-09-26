"""A game terminal living in a tmux session.

Why tmux: the connection (local nethack process, or ssh to a public server)
outlives harness restarts, and humans can watch with `tmux attach -r -t NAME`.

Output bytes are mirrored with `pipe-pane` into a raw log; its size is our
"has anything happened since" signal for settle detection, and the log doubles
as a local recording of the session.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import time
from pathlib import Path

from .screen import Screen, parse_capture

TMUX = os.environ.get("NH_TMUX", "tmux")
# A dedicated tmux server socket keeps our sessions isolated from any tmux
# the user runs, and makes cleanup safe.
TMUX_SOCKET = os.environ.get("NH_TMUX_SOCKET", "nh")


def _tmux(*args: str, check: bool = True, capture: bool = True) -> str:
    cmd = [TMUX, "-L", TMUX_SOCKET, *args]
    p = subprocess.run(cmd, capture_output=capture, text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"tmux {' '.join(args)} failed: {p.stderr.strip()}")
    return p.stdout if capture else ""


class TmuxTerminal:
    def __init__(self, session: str, raw_log: Path, width: int = 80, height: int = 24):
        self.session = session
        self.raw_log = Path(raw_log)
        self.width = width
        self.height = height

    # ---- lifecycle -------------------------------------------------------
    def exists(self) -> bool:
        p = subprocess.run([TMUX, "-L", TMUX_SOCKET, "has-session", "-t", f"={self.session}"],
                           capture_output=True, text=True)
        return p.returncode == 0

    def start(self, command: str, env: dict[str, str] | None = None, cwd: str | None = None) -> None:
        """Start `command` (a shell command string) in a new detached session."""
        if self.exists():
            raise RuntimeError(f"tmux session {self.session!r} already exists")
        self.raw_log.parent.mkdir(parents=True, exist_ok=True)
        args = ["new-session", "-d", "-s", self.session, "-x", str(self.width), "-y", str(self.height)]
        if cwd:
            args += ["-c", cwd]
        for k, v in (env or {}).items():
            args += ["-e", f"{k}={v}"]
        args.append(command)
        # server-wide options must exist before the first session: pass them
        # via a start-server chain.
        _tmux("start-server", check=False)
        _tmux(*args)
        self._configure()

    def _configure(self) -> None:
        s = self.session
        _tmux("set-option", "-t", s, "status", "off", check=False)
        _tmux("set-option", "-t", s, "remain-on-exit", "on", check=False)
        _tmux("set-option", "-t", s, "history-limit", "2000", check=False)
        _tmux("set-window-option", "-t", s, "window-size", "manual", check=False)
        _tmux("set-window-option", "-t", s, "aggressive-resize", "off", check=False)
        _tmux("resize-window", "-t", s, "-x", str(self.width), "-y", str(self.height), check=False)
        self.ensure_pipe()

    def ensure_pipe(self) -> None:
        """(Re)attach the raw-output mirror. -o: only if not already piping."""
        self.raw_log.parent.mkdir(parents=True, exist_ok=True)
        cmd = f"cat >> {shlex.quote(str(self.raw_log))}"
        _tmux("pipe-pane", "-o", "-t", self.session, cmd, check=False)

    def kill(self) -> None:
        if self.exists():
            _tmux("kill-session", "-t", f"={self.session}", check=False)

    # ---- io --------------------------------------------------------------
    def send(self, data: bytes) -> None:
        if not data:
            return
        # send-keys -H takes hex bytes; chunk to keep argv small.
        for i in range(0, len(data), 256):
            chunk = data[i:i + 256]
            _tmux("send-keys", "-t", self.session, "-H", *[f"{b:02x}" for b in chunk])

    def raw_size(self) -> int:
        try:
            return self.raw_log.stat().st_size
        except FileNotFoundError:
            return 0

    def capture(self) -> Screen:
        fmt = "#{cursor_x} #{cursor_y} #{pane_width} #{pane_height} #{pane_dead}"
        # one tmux invocation => screen and cursor are read atomically
        out = _tmux("capture-pane", "-p", "-e", "-N", "-t", self.session, ";",
                    "display-message", "-p", "-t", self.session, fmt)
        body, _, meta = out.rstrip("\n").rpartition("\n")
        try:
            cx, cy, w, h, dead = meta.split()
            cursor = (int(cx), int(cy))
            w, h = int(w), int(h)
        except ValueError:
            raise RuntimeError(f"unexpected tmux display output: {meta!r}")
        if (w, h) != (self.width, self.height):
            _tmux("resize-window", "-t", self.session, "-x", str(self.width), "-y", str(self.height),
                  check=False)
        return parse_capture(body, self.width, self.height, cursor, dead=(dead == "1"), t=time.time())

    def wait_quiet(self, since_size: int, first_timeout: float, quiet: float, max_wait: float,
                   poll: float = 0.01) -> tuple[bool, float]:
        """Wait for output to start (after since_size) and then go quiet.

        Returns (got_output, seconds_waited)."""
        t0 = time.monotonic()
        size = self.raw_size()
        while size == since_size:
            if time.monotonic() - t0 >= first_timeout:
                return False, time.monotonic() - t0
            time.sleep(poll)
            size = self.raw_size()
        last_change = time.monotonic()
        while True:
            time.sleep(poll)
            s = self.raw_size()
            now = time.monotonic()
            if s != size:
                size = s
                last_change = now
            elif now - last_change >= quiet:
                return True, now - t0
            if now - t0 >= max_wait:
                return True, now - t0
