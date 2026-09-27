"""`nh` command-line client.

Game lifecycle:
  nh start-local NAME [--role Valkyrie --race dwarf --gender female --align lawful]
                      [--seed N] [--wizard]           local NetHack in tmux + daemon
  nh start-remote NAME --server hardfought            ssh session in tmux + daemon
  nh daemon [NAME]         (re)start the daemon for an existing tmux session
  nh use NAME              make NAME the current game (or set NH_GAME)
  nh list                  list games
  nh stop                  stop the daemon (game/tmux keeps running)
  nh kill [--force]        kill the tmux session (remote: hangup-saves the game)

Playing (current game unless --game NAME):
  nh obs [--crop|--brief]  observe (full map by default)
  nh do KEYS [--full]      send keys (e.g. 'k', 's', '20s', '#pray<CR>', '<Esc>')
  nh exec [-a REGEX]... [FILE|-]   run Python in the kernel (pauses on events)
  nh cont [--reply KEYS]   resume a paused exec
  nh drop                  abandon a paused exec
  nh screen                raw 80x24 terminal (via daemon)
  nh peek                  raw terminal straight from tmux (works while daemon busy)
  nh history [N]           last N messages
  nh reload                reload tactics/views modules in the kernel
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import socket
import subprocess
import sys
import time
from pathlib import Path

from .paths import REPO_ROOT, RUN_DIR, current_game, game_dir, load_meta, save_meta, set_current

LOCAL_NETHACK = os.environ.get("NH_LOCAL_NETHACK",
                               str(Path.home() / ".local" / "nethack-3.6.7" / "bin" / "nethack"))
PY = sys.executable


# --------------------------------------------------------------------- client
def request(name: str, req: dict, timeout: float = 900.0) -> dict:
    sock_path = game_dir(name) / "daemon.sock"
    if not sock_path.exists():
        raise SystemExit(f"daemon for {name!r} is not running (no {sock_path}). Try `nh daemon {name}`.")
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect(str(sock_path))
    except (ConnectionRefusedError, FileNotFoundError):
        raise SystemExit(f"daemon for {name!r} not answering. Try `nh daemon {name}`.")
    s.sendall((json.dumps(req) + "\n").encode())
    data = b""
    while True:
        chunk = s.recv(1 << 20)
        if not chunk:
            break
        data += chunk
        if data.endswith(b"\n"):
            break
    s.close()
    return json.loads(data.decode())


def _print(resp: dict) -> int:
    print(resp.get("text", ""))
    return 0 if resp.get("ok") else 1


# ------------------------------------------------------------------ lifecycle
def _tmux(*args, check=True):
    from .tmuxterm import TMUX, TMUX_SOCKET
    return subprocess.run([TMUX, "-L", TMUX_SOCKET, *args], capture_output=True, text=True, check=check)


def spawn_daemon(name: str, wait: float = 10.0) -> None:
    d = game_dir(name)
    sock = d / "daemon.sock"
    # stop an old daemon if any
    pidf = d / "daemon.pid"
    if pidf.exists():
        try:
            old = int(pidf.read_text().strip())
            os.kill(old, 15)
            t0 = time.time()
            while time.time() - t0 < 8:
                try:
                    os.kill(old, 0)
                except ProcessLookupError:
                    break
                time.sleep(0.05)
            else:
                os.kill(old, 9)
        except (ProcessLookupError, ValueError, PermissionError):
            pass
    if sock.exists():
        sock.unlink()
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    log = open(d / "daemon.log", "a")
    subprocess.Popen([PY, "-m", "nh.daemon", "--game", name], stdout=log, stderr=log,
                     stdin=subprocess.DEVNULL, env=env, start_new_session=True, cwd=str(REPO_ROOT))
    t0 = time.time()
    while time.time() - t0 < wait:
        if sock.exists():
            try:
                r = request(name, {"op": "ping"}, timeout=5)
                if r.get("ok"):
                    return
            except SystemExit:
                pass
        time.sleep(0.1)
    raise SystemExit(f"daemon for {name} did not come up; see {d / 'daemon.log'}")


def write_rc(name: str, extra: list[str], base_file: str | None = None) -> Path:
    d = game_dir(name)
    home = d / "home"
    home.mkdir(parents=True, exist_ok=True)
    base = Path(base_file).read_text() if base_file else (REPO_ROOT / "play" / "nethackrc").read_text()
    rc = base.rstrip() + "\n" + "\n".join(extra) + "\n"
    p = home / ".nethackrc"
    p.write_text(rc)
    return p


def _claim_current(name: str) -> None:
    """Make `name` the current game unless another game that is still
    running holds that slot (a concurrent player may rely on it). Scripts
    should pass --game anyway."""
    from .paths import CURRENT_FILE
    try:
        cur = CURRENT_FILE.read_text().strip()
    except FileNotFoundError:
        cur = ""
    if cur and cur != name:
        try:
            meta = load_meta(cur)
            alive = _tmux("has-session", "-t", f"={meta['tmux_session']}", check=False).returncode == 0
        except Exception:
            alive = False
        if alive:
            print(f"note: current game stays {cur!r} (still running); use --game {name} or `nh use {name}`")
            return
    set_current(name)


def _lock_name(meta_or_player, wizard: bool) -> str:
    # NetHack names wizard-mode (-D) games "wizard": all of them share one lock
    return "wizard" if wizard else meta_or_player


def cmd_start_local(a) -> int:
    name = a.name
    d = game_dir(name)
    if d.exists() and (d / "meta.json").exists() and not a.fresh:
        raise SystemExit(f"game {name!r} exists; use `nh daemon {name}` to reattach or --fresh to replace")
    mine = _lock_name(a.player or name.replace("-", "")[:10] or "agent", a.wizard)
    for other in sorted(RUN_DIR.glob("*/meta.json")):
        if other.parent.name == name:
            continue
        try:
            om = load_meta(other.parent.name)
        except Exception:
            continue
        if om.get("kind") != "local":
            continue
        alive = _tmux("has-session", "-t", f"={om['tmux_session']}", check=False).returncode == 0
        if alive and _lock_name(om.get("player", ""), bool(om.get("wizard"))) == mine:
            why = 'wizard-mode games all lock as "wizard"' if a.wizard else "same player"
            raise SystemExit(f"refusing: running game {other.parent.name!r} uses the same NetHack lock name "
                             f"{mine!r} ({why}); "
                             "starting would ask 'Destroy old game?' and answering y would wipe that game")
    if a.fresh:
        _tmux("kill-session", "-t", f"=nh-{name}", check=False)
        import shutil
        shutil.rmtree(d, ignore_errors=True)
        # also drop the local NetHack save/lock files for this player name (wizard-mode games all
        # save and lock as "wizard": that is the name to clear then)
        hackdir = Path(a.nethack).resolve().parent.parent / "lib" / "nethackdir"
        pname = mine
        for f in list(hackdir.glob(f"save/*{pname}*")) + list(hackdir.glob(f"[0-9]*{pname}.*")):
            try:
                f.unlink()
            except OSError:
                pass
    elif a.wizard:
        hackdir = Path(a.nethack).resolve().parent.parent / "lib" / "nethackdir"
        if list(hackdir.glob("save/*wizard*")):
            print("note: a wizard-mode save exists (every wizard-mode game saves as \"wizard\"): NetHack will "
                  "RESTORE it — pass --fresh for a new game")
    d.mkdir(parents=True, exist_ok=True)
    extra = [] if a.rc else [f"OPTIONS=role:{a.role},race:{a.race},gender:{a.gender},align:{a.align}"]
    rc = write_rc(name, extra, a.rc)
    session = f"nh-{name}"
    env = {"HOME": str(rc.parent), "TERM": "screen", "NETHACKOPTIONS": str(rc), "LANG": "C", "LC_ALL": "C"}
    if a.seed is not None:
        env["NETHACK_SEED"] = str(a.seed)
    player = a.player or name.replace("-", "")[:10] or "agent"
    flags = f"-u {shlex.quote(player)}" + (" -D" if a.wizard else "")
    command = f"{shlex.quote(a.nethack)} {flags}"
    meta = {"name": name, "kind": "local", "tmux_session": session, "width": 80, "height": 24,
            "command": command, "env": env, "player": player, "created": time.time(),
            "character": {"role": a.role, "race": a.race, "gender": a.gender, "align": a.align},
            "seed": a.seed, "wizard": a.wizard}
    save_meta(name, meta)
    from .tmuxterm import TmuxTerminal
    term = TmuxTerminal(session, d / "raw.log")
    term.start(command, env=env, cwd=str(d))
    _claim_current(name)
    spawn_daemon(name)
    print(f"started local game {name!r} (tmux -L nh attach -r -t {session} to watch)")
    return _print(request(name, {"op": "obs", "mode": "full"}))


def cmd_start_remote(a) -> int:
    name = a.name
    d = game_dir(name)
    if d.exists() and (d / "meta.json").exists():
        raise SystemExit(f"game {name!r} exists; use `nh daemon {name}` to reattach")
    d.mkdir(parents=True, exist_ok=True)
    script = REPO_ROOT / "scripts" / "nh-connect.sh"
    session = f"nh-{name}"
    command = f"{shlex.quote(str(script))} {shlex.quote(a.server)}"
    env = {"TERM": "screen", "LANG": "C", "LC_ALL": "C"}
    meta = {"name": name, "kind": "remote", "server": a.server, "tmux_session": session,
            "width": 80, "height": 24, "command": command, "env": env, "created": time.time()}
    save_meta(name, meta)
    from .tmuxterm import TmuxTerminal
    term = TmuxTerminal(session, d / "raw.log")
    term.start(command, env=env, cwd=str(d))
    _claim_current(name)
    spawn_daemon(name)
    return _print(request(name, {"op": "screen"}))


def cmd_restart(a) -> int:
    """Relaunch the game process for an existing game (after a crash, a hangup,
    or a container restart). Local: NetHack restores the save. Remote: opens a
    new ssh session to the server lobby."""
    name = current_game(a.name or a.game)
    meta = load_meta(name)
    d = game_dir(name)
    from .tmuxterm import TmuxTerminal
    term = TmuxTerminal(meta["tmux_session"], d / "raw.log", width=meta.get("width", 80),
                        height=meta.get("height", 24))
    if term.exists():
        scr = term.capture()
        if not scr.dead and not a.force:
            raise SystemExit(f"{meta['tmux_session']} is still running; use `nh daemon {name}` to reattach "
                             "(or --force to kill and relaunch)")
        term.kill()
    term.start(meta["command"], env=meta.get("env"), cwd=str(d))
    set_current(name)
    spawn_daemon(name)
    print(f"relaunched {name}")
    return _print(request(name, {"op": "obs", "mode": "full"}))


def cmd_daemon(a) -> int:
    name = current_game(a.name or a.game)
    meta = load_meta(name)
    r = _tmux("has-session", "-t", f"={meta['tmux_session']}", check=False)
    if r.returncode != 0:
        raise SystemExit(f"tmux session {meta['tmux_session']} is gone; the game process ended")
    spawn_daemon(name)
    print(f"daemon for {name} (re)started")
    return 0


def cmd_list(a) -> int:
    if not RUN_DIR.exists():
        print("(no games)")
        return 0
    cur = None
    try:
        cur = current_game(None)
    except SystemExit:
        pass
    for d in sorted(RUN_DIR.iterdir()):
        if not (d / "meta.json").exists():
            continue
        meta = json.loads((d / "meta.json").read_text())
        alive = _tmux("has-session", "-t", f"={meta['tmux_session']}", check=False).returncode == 0
        dm = (d / "daemon.sock").exists()
        mark = "*" if d.name == cur else " "
        print(f"{mark} {d.name:20s} {meta.get('kind'):6s} tmux={'up' if alive else 'DOWN'} "
              f"daemon={'up' if dm else 'down'}")
    return 0


def cmd_peek(a) -> int:
    name = current_game(a.game)
    meta = load_meta(name)
    r = _tmux("capture-pane", "-p", "-t", meta["tmux_session"], check=False)
    if r.returncode != 0:
        raise SystemExit(r.stderr)
    for y, line in enumerate(r.stdout.rstrip("\n").split("\n")):
        print(f"{y:>2}|{line.rstrip()}")
    return 0


def cmd_kill(a) -> int:
    name = current_game(a.game)
    meta = load_meta(name)
    if meta.get("kind") == "remote" and not a.force:
        raise SystemExit("remote game: killing tmux hangs up the ssh session (server saves the game). "
                         "Pass --force if that's what you want.")
    try:
        request(name, {"op": "shutdown"}, timeout=10)
    except SystemExit:
        pass
    _tmux("kill-session", "-t", f"={meta['tmux_session']}", check=False)
    print(f"killed {meta['tmux_session']}")
    return 0


# ------------------------------------------------------------------- playing
def _read_code(arg: str | None) -> str:
    if arg is None or arg == "-":
        return sys.stdin.read()
    try:
        # a script file; long or multi-line inline code isn't a path (and a
        # too-long "file name" would raise OSError)
        if "\n" not in arg and len(arg) < 1024 and Path(arg).is_file():
            return Path(arg).read_text()
    except OSError:
        pass
    return arg  # inline code


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="nh", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game", help="game name (default: $NH_GAME or run/CURRENT)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("start-local")
    p.add_argument("name")
    p.add_argument("--role", default="Valkyrie")
    p.add_argument("--race", default="dwarf")
    p.add_argument("--gender", default="female")
    p.add_argument("--align", default="lawful")
    p.add_argument("--seed", type=int)
    p.add_argument("--wizard", action="store_true")
    p.add_argument("--player", help="in-game player name (default derived from NAME)")
    p.add_argument("--nethack", default=LOCAL_NETHACK)
    p.add_argument("--fresh", action="store_true", help="replace an existing game of this name")
    p.add_argument("--rc", help="use this rc file verbatim instead of play/nethackrc + character options")

    p = sub.add_parser("start-remote")
    p.add_argument("name")
    p.add_argument("--server", default="hardfought")

    p = sub.add_parser("daemon")
    p.add_argument("name", nargs="?")

    p = sub.add_parser("restart", help="relaunch the game process (restores the save)")
    p.add_argument("name", nargs="?")
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("use")
    p.add_argument("name")

    sub.add_parser("list")
    sub.add_parser("stop")
    p = sub.add_parser("kill")
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("obs")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--crop", action="store_true")
    g.add_argument("--brief", action="store_true")

    p = sub.add_parser("do")
    p.add_argument("keys")
    p.add_argument("--full", action="store_true", help="show the full map")
    p.add_argument("--brief", action="store_true", help="no map")
    p.add_argument("--force", action="store_true", help="allow dangerous keys like #quit")
    p.add_argument("--multi", action="store_true",
                   help="allow several commands in one call (default: stop when a command completes)")

    p = sub.add_parser("exec")
    p.add_argument("code", nargs="?", help="file path, inline code, or - for stdin (default)")
    p.add_argument("-a", "--autocontinue", action="append", default=[],
                   help="regex; matching messages don't pause (repeatable)")
    p.add_argument("--no-monsters", action="store_true", help="don't pause on new monsters")
    p.add_argument("--hp-pause", type=float, default=None,
                   help="pause on HP loss only below this fraction of max HP (default 0.7; big hits always pause)")
    p.add_argument("--at-prompt", action="store_true",
                   help="start even though a prompt/menu is open (your script answers it first)")
    p.add_argument("--full", action="store_true")
    p.add_argument("--brief", action="store_true")

    p = sub.add_parser("cont")
    p.add_argument("--reply", help="keys to send first (answer the open prompt)")
    p.add_argument("-a", "--autocontinue", action="append", default=None)
    p.add_argument("--full", action="store_true")
    p.add_argument("--brief", action="store_true")

    sub.add_parser("drop")
    sub.add_parser("screen")
    sub.add_parser("peek")
    p = sub.add_parser("history")
    p.add_argument("n", nargs="?", type=int, default=30)
    sub.add_parser("reload")
    sub.add_parser("info", help="harness memory: current branch/level, prayer log, per-level features, overview")

    a = ap.parse_args(argv)

    if a.cmd == "start-local":
        return cmd_start_local(a)
    if a.cmd == "start-remote":
        return cmd_start_remote(a)
    if a.cmd == "daemon":
        return cmd_daemon(a)
    if a.cmd == "restart":
        return cmd_restart(a)
    if a.cmd == "use":
        load_meta(a.name)
        set_current(a.name)
        print(f"current game: {a.name}")
        return 0
    if a.cmd == "list":
        return cmd_list(a)
    if a.cmd == "peek":
        return cmd_peek(a)
    if a.cmd == "kill":
        return cmd_kill(a)

    name = current_game(a.game)

    def mode_of(ns, default="crop"):
        if getattr(ns, "full", False):
            return "full"
        if getattr(ns, "brief", False):
            return "brief"
        return default

    if a.cmd == "stop":
        return _print(request(name, {"op": "shutdown"}, timeout=10))
    if a.cmd == "obs":
        return _print(request(name, {"op": "obs", "mode": "crop" if a.crop else "brief" if a.brief else "full"}))
    if a.cmd == "do":
        return _print(request(name, {"op": "do", "keys": a.keys, "force": a.force, "multi": a.multi,
                                     "mode": mode_of(a)}))
    if a.cmd == "exec":
        code = _read_code(a.code)
        return _print(request(name, {"op": "exec", "code": code, "autocontinue": a.autocontinue,
                                     "monsters": not a.no_monsters, "hp_pause": a.hp_pause,
                                     "at_prompt": a.at_prompt, "mode": mode_of(a)}))
    if a.cmd == "cont":
        return _print(request(name, {"op": "cont", "reply": a.reply, "autocontinue": a.autocontinue,
                                     "mode": mode_of(a)}))
    if a.cmd == "drop":
        return _print(request(name, {"op": "drop"}))
    if a.cmd == "screen":
        return _print(request(name, {"op": "screen"}))
    if a.cmd == "history":
        return _print(request(name, {"op": "history", "n": a.n}))
    if a.cmd == "reload":
        return _print(request(name, {"op": "reload"}))
    if a.cmd == "info":
        return _print(request(name, {"op": "info"}))
    ap.error(f"unknown command {a.cmd}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
