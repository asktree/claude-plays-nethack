"""dgamelaunch lobby automation for Hardfought (run inside `bin/nh exec`).

Everything here checks the screen before each keystroke and stops (raises)
rather than guessing. Parts of the lobby we have never seen verbatim (the
"1) NetHack (various versions)" submenu, "j) Manage settings") are NOT
automated: the helpers return the screen for you to read and decide.

Credentials live in play/secrets/hardfought.json (gitignored):
    {"user": "ClaudeAscends", "password": "<alnum, <=20 chars, no ':'>", "email": "..."}
Keystrokes carrying the password are sent with secret=True (not logged).

Hard rules (from docs/research/servers.md):
- Never press `t` (TNNT tournament bans bots). Never answer `y` to
  "Destroy old game?" (the harness refuses anyway).
- During a stale-process countdown ("will recover in N seconds ... Press a
  key NOW if you don't want this"), send NOTHING (the harness refuses).
- Idle 30 min without game output = hangup-save (the daemon sends ^R
  keepalives at the command prompt; never idle at a prompt).
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from . import ctx

REPO = Path(__file__).resolve().parents[2]
SECRETS = REPO / "play" / "secrets" / "hardfought.json"


class LobbyError(Exception):
    pass


def creds() -> dict:
    if not SECRETS.exists():
        raise LobbyError(f"missing {SECRETS} (see play/ORCHESTRATOR.md)")
    return json.loads(SECRETS.read_text())


def text() -> str:
    return ctx.look().screen.text


def wait_for(pattern: str, timeout: float = 25.0, poll: float = 0.5) -> str:
    """Poll the screen (no keys sent) until `pattern` (regex) appears."""
    rx = re.compile(pattern, re.I | re.S)
    t0 = time.time()
    while time.time() - t0 < timeout:
        t = text()
        if rx.search(t):
            return t
        time.sleep(poll)
    raise LobbyError(f"timed out waiting for /{pattern}/; screen:\n{text()}")


def lobby_state(t: str | None = None) -> str:
    """'stale' | 'logged_in' | 'logged_out' | 'username' | 'password' | 'game' | 'unknown'."""
    t = t if t is not None else text()
    low = t.lower()
    if "stale" in low and "will recover in" in low:
        return "stale"
    if "logged in as:" in low:
        return "logged_in"
    if "enter your username" in low or "please enter a username" in low:
        return "username"
    if "enter your password" in low or "enter a password" in low:
        return "password"
    if "l) login" in low or "r) register" in low:
        return "logged_out"
    s = ctx.look()
    if s.status.ok:
        return "game"
    return "unknown"


def login() -> str:
    """Log in from the logged-out menu. Returns the lobby screen text."""
    c = creds()
    st = lobby_state()
    if st == "logged_in":
        return text()
    if st != "logged_out":
        raise LobbyError(f"not at the logged-out menu (state={st}):\n{text()}")
    ctx.do("l", quiet=True, force=True)
    wait_for(r"enter your username")
    ctx.do(c["user"] + "<CR>", quiet=True, force=True)
    wait_for(r"enter your password")
    ctx.do(c["password"] + "<CR>", quiet=True, secret=True, force=True)
    t = wait_for(r"Logged in as:|l\) Login")
    if "Logged in as:" not in t:
        raise LobbyError("login failed (back at the logged-out menu): wrong password?")
    return t


def register() -> str:
    """Register the account in play/secrets/hardfought.json (first time only)."""
    c = creds()
    if not re.fullmatch(r"[A-Za-z0-9]{2,16}", c["user"]):
        raise LobbyError("username must be 2-16 letters/digits")
    if not re.fullmatch(r"[A-Za-z0-9]{8,20}", c["password"]):
        raise LobbyError("password must be 8-20 letters/digits (no ':')")
    if lobby_state() != "logged_out":
        raise LobbyError(f"not at the logged-out menu:\n{text()}")
    ctx.do("r", quiet=True, force=True)
    wait_for(r"Please enter a username")
    ctx.do(c["user"] + "<CR>", quiet=True, force=True)
    t = wait_for(r"enter a password|problem with your last entry|already|taken")
    if "enter a password" not in t:
        raise LobbyError(f"username rejected:\n{t}")
    ctx.do(c["password"] + "<CR>", quiet=True, secret=True, force=True)
    wait_for(r"And again")
    ctx.do(c["password"] + "<CR>", quiet=True, secret=True, force=True)
    t = wait_for(r"email address|don't match")
    if "email" not in t.lower():
        raise LobbyError(f"password step failed:\n{t}")
    ctx.do(c["email"] + "<CR>", quiet=True, force=True)
    return wait_for(r"Logged in as:|problem|abort", timeout=120)


def play_last_game() -> str:
    """From the logged-in lobby, press `p` only if it launches nh367-hdf.
    Returns the screen after launch (restore, new game, or countdown)."""
    t = text()
    if lobby_state(t) != "logged_in":
        raise LobbyError(f"not in the logged-in lobby:\n{t}")
    line = next((l for l in t.splitlines() if "p) Play last game" in l), "")
    if "[nh367-hdf]" not in line:
        raise LobbyError(f"'p' would not launch nh367-hdf ({line.strip()!r}); use the versions menu "
                         "(1) by hand and pick NetHack 3.6.7 after reading it")
    ctx.do("p", quiet=True, force=True)
    time.sleep(3)
    return text()


def resume_last_save() -> str:
    t = text()
    line = next((l for l in t.splitlines() if "r) Resume last save" in l), "")
    if "[nh367-hdf]" not in line:
        raise LobbyError(f"no nh367-hdf save to resume ({line.strip()!r})")
    ctx.do("r", quiet=True, force=True)
    time.sleep(3)
    return text()


def wait_out_stale(timeout: float = 60) -> str:
    """Wait (sending nothing) until a stale-process countdown is over."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        if lobby_state() != "stale":
            return text()
        time.sleep(2)
    raise LobbyError("stale-process countdown did not finish")


def vi_replace_buffer(content: str) -> None:
    """Inside dgamelaunch's `virus` editor (a small vi clone): replace the
    whole file with `content` and save. Verify afterwards via the public rc
    URL (https://www.hardfought.org/userdata/<F>/<Name>/nethack/<Name>.nh36rc)."""
    g = ctx.game
    g.send_bytes(b"\x1b\x1b")
    g.send_bytes(b":1,$d\r")
    g.send_bytes(b"i")
    body = content.rstrip("\n").replace("\r", "") + "\n"
    if any(ord(ch) > 126 or (ord(ch) < 32 and ch != "\n") for ch in body):
        raise LobbyError("rc content must be plain printable ASCII")
    g.send_bytes(body.replace("\n", "\r").encode())
    g.send_bytes(b"\x1b")
    g.send_bytes(b":wq\r")
