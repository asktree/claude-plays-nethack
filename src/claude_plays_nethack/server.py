"""MCP server exposing NLE to Claude Code as the in-game harness."""

from __future__ import annotations

import builtins
import contextlib
import io
import json
import os
import sys
import time
import traceback
import uuid
from pathlib import Path
from typing import Any

import gymnasium as gym
import nle  # noqa: F401  (registers gym envs)
from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
from nle import nethack

REPO_ROOT = Path(__file__).resolve().parents[2]
GAME_DIR = REPO_ROOT / "game"
TRAJECTORY_DIR = Path(os.environ.get("NETHACK_TRAJECTORY_DIR", GAME_DIR / "trajectory"))
TRAJECTORY_DIR.mkdir(parents=True, exist_ok=True)
LIVE_STATE_PATH = Path(os.environ.get("NETHACK_LIVE_STATE", GAME_DIR / ".live_state.json"))
LIVE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

# Make `views/` (and future `tactics/`) importable inside game.exec()'d code.
if str(GAME_DIR) not in sys.path:
    sys.path.insert(0, str(GAME_DIR))

ENV_ID = os.environ.get("NETHACK_ENV", "NetHackChallenge-v0")

mcp = FastMCP("nethack")


class GameState:
    """Holds the persistent NLE env and a table of action names → indices."""

    def __init__(self) -> None:
        self.env: gym.Env | None = None
        self.last_obs: dict[str, Any] | None = None
        self.last_info: dict[str, Any] | None = None
        self.terminated: bool = False
        self.truncated: bool = False
        self.session_id: str = uuid.uuid4().hex[:8]
        self.trajectory_path: Path = TRAJECTORY_DIR / f"{int(time.time())}-{self.session_id}.jsonl"
        self.action_table: dict[str, int] = {}
        self.actions_tuple: tuple = ()

    def ensure_env(self) -> gym.Env:
        if self.env is None:
            obs_keys = (
                "tty_chars", "tty_colors", "tty_cursor",
                "blstats", "message",
                "inv_glyphs", "inv_strs", "inv_letters", "inv_oclasses",
                "screen_descriptions",
            )
            self.env = gym.make(ENV_ID, observation_keys=obs_keys)
            self.actions_tuple = tuple(self.env.unwrapped.actions)
            self._build_action_table()
        return self.env

    def _build_action_table(self) -> None:
        # Map several name forms to the gym action index.
        # e.g. "Command.READ", "READ", "north", "n" all resolvable.
        table: dict[str, int] = {}
        for idx, action_enum in enumerate(self.actions_tuple):
            cls_name = type(action_enum).__name__  # e.g. "Command"
            short = action_enum.name              # e.g. "READ"
            qualified = f"{cls_name}.{short}"     # e.g. "Command.READ"
            table[qualified] = idx
            table[qualified.lower()] = idx
            # Short name is unambiguous in most cases; on collision, first wins.
            table.setdefault(short, idx)
            table.setdefault(short.lower(), idx)
        # Movement aliases.
        movement_aliases = {
            "north": "CompassDirection.N", "south": "CompassDirection.S",
            "east": "CompassDirection.E", "west": "CompassDirection.W",
            "ne": "CompassDirection.NE", "nw": "CompassDirection.NW",
            "se": "CompassDirection.SE", "sw": "CompassDirection.SW",
            "up": "MiscDirection.UP", "down": "MiscDirection.DOWN",
        }
        for alias, qualified in movement_aliases.items():
            if qualified in table:
                table[alias] = table[qualified]
        self.action_table = table

    def resolve_action(self, action: int | str) -> int:
        if isinstance(action, int):
            if action < 0 or action >= len(self.actions_tuple):
                raise ValueError(f"action index {action} out of range [0, {len(self.actions_tuple)})")
            return action
        if isinstance(action, str):
            key = action.strip()
            if key in self.action_table:
                return self.action_table[key]
            if key.lower() in self.action_table:
                return self.action_table[key.lower()]
            raise ValueError(
                f"unknown action name {action!r}. "
                f"Try a Command/CompassDirection/MiscAction enum name "
                f"(e.g. 'Command.READ', 'north', 'MORE')."
            )
        raise TypeError(f"action must be int or str, got {type(action).__name__}")

    def log(self, record: dict[str, Any]) -> None:
        record = {"t": time.time(), "session": self.session_id, **record}
        with self.trajectory_path.open("a") as fh:
            fh.write(json.dumps(record, default=str) + "\n")


STATE = GameState()


def _render_screen(obs: dict[str, Any]) -> str:
    """Render the dungeon map, stripping NLE's top message row and bottom status rows.

    NLE's tty_chars is 24×80: row 0 is the message line, rows 22-23 are the status
    lines. Both are already surfaced in our snapshot (`message`, `blstats`), so
    keeping them in the screen string would just duplicate info and bloat tokens.
    """
    rows = ["".join(chr(int(c)) for c in row).rstrip() for row in obs["tty_chars"]]
    map_rows = rows[1:-2]
    # trim leading/trailing fully-blank rows
    while map_rows and not map_rows[0]:
        map_rows.pop(0)
    while map_rows and not map_rows[-1]:
        map_rows.pop()
    return "\n".join(map_rows)


def _decode_message(obs: dict[str, Any]) -> str:
    return bytes(obs["message"]).rstrip(b"\x00").decode("latin-1", errors="replace")


def _has_more_prompt(obs: dict[str, Any]) -> bool:
    """True if the top tty row shows --More-- (a flush-the-message-buffer prompt).

    NetHack shows --More-- when there are too many messages to fit on one line.
    The only useful response is to advance, so we auto-handle it in _do() and
    accumulate the messages.
    """
    if "tty_chars" not in obs:
        return False
    row0 = obs["tty_chars"][0]
    text = bytes(row0).rstrip(b"\x00").decode("latin-1", errors="replace")
    return "--More--" in text


def _decode_inventory(obs: dict[str, Any]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for letter_byte, str_arr in zip(obs["inv_letters"], obs["inv_strs"], strict=True):
        letter = chr(int(letter_byte)) if letter_byte else ""
        text = bytes(str_arr).rstrip(b"\x00").decode("latin-1", errors="replace")
        if text:
            items.append({"letter": letter, "text": text})
    return items


def _decode_blstats(obs: dict[str, Any]) -> dict[str, int]:
    bl = obs["blstats"]
    keys = [
        "x", "y", "strength_pct", "strength", "dexterity", "constitution",
        "intelligence", "wisdom", "charisma", "score", "hitpoints", "max_hitpoints",
        "depth", "gold", "energy", "max_energy", "armor_class", "monster_level",
        "experience_level", "experience_points", "time", "hunger_state",
        "carrying_capacity", "dungeon_number", "level_number", "condition",
        "alignment",
    ]
    return {k: int(bl[i]) for i, k in enumerate(keys) if i < len(bl)}


def _format_for_text(snap: dict[str, Any]) -> str:
    """Render a snapshot as the text the model will actually read.

    Key point: this string contains real newlines. JSON-serializing the
    snapshot dict would escape them to '\\n' inside the tool result, which
    destroys spatial reasoning over the dungeon map.
    """
    if not snap.get("started"):
        return snap.get("hint", "(no game started)")
    bl = snap.get("blstats", {})
    lines = []
    lines.append(
        f"T={bl.get('time','?')}  "
        f"HP={bl.get('hitpoints','?')}/{bl.get('max_hitpoints','?')}  "
        f"Pw={bl.get('energy','?')}/{bl.get('max_energy','?')}  "
        f"Dlvl={bl.get('depth','?')}  "
        f"AC={bl.get('armor_class','?')}  "
        f"$={bl.get('gold','?')}  "
        f"XP={bl.get('experience_level','?')}/{bl.get('experience_points','?')}  "
        f"Hunger={bl.get('hunger_state','?')}"
    )
    msg = snap.get("message") or ""
    if msg:
        lines.append(f"msg: {msg}")
    lines.append("")
    lines.append(snap.get("screen", ""))
    inv = snap.get("inventory") or []
    if inv:
        lines.append("")
        lines.append("Inventory:")
        for it in inv:
            lines.append(f"  {it['letter']} - {it['text']}")
    if "reward" in snap:
        lines.append("")
        lines.append(f"reward: {snap['reward']}")
    if snap.get("terminated") or snap.get("truncated"):
        lines.append("")
        lines.append("** GAME OVER **")
    return "\n".join(lines)


def _tool_result(snap: dict[str, Any]) -> ToolResult:
    """Wrap a snapshot as a single TextContent block.

    We deliberately do NOT set `structured_content`: Claude Code's UI surfaces
    structured_content as JSON (with `\\n` escapes), which destroys the dungeon
    map for the human watching. The trajectory log already captures structured
    state for any post-hoc analysis; we don't need it on the wire.
    """
    return ToolResult(
        content=[TextContent(type="text", text=_format_for_text(snap))],
    )


def _decode_screen_descriptions(obs: dict[str, Any]) -> list[list[str]]:
    """Decode NLE's per-cell descriptions into a 2D string grid (rows x cols)."""
    sd = obs.get("screen_descriptions")
    if sd is None:
        return []
    out: list[list[str]] = []
    for row in sd:
        row_out: list[str] = []
        for cell in row:
            text = bytes(cell).rstrip(b"\x00").decode("latin-1", errors="replace").strip()
            row_out.append(text)
        out.append(row_out)
    return out


def _write_live_state(obs: dict[str, Any] | None, snap: dict[str, Any]) -> None:
    """Atomically dump the full live state for view.py to render.

    Includes the raw 24x80 chars + colors + per-cell descriptions so the
    viewer can apply ANSI colors and build a legend, plus the structured
    snapshot fields the model also sees.
    """
    if not snap.get("started") or obs is None:
        return
    chars_grid = [[int(c) for c in row] for row in obs["tty_chars"]]
    colors_grid = [[int(c) for c in row] for row in obs["tty_colors"]]
    descs_grid = _decode_screen_descriptions(obs)
    state = {
        "session": snap.get("session"),
        "terminated": snap.get("terminated"),
        "truncated": snap.get("truncated"),
        "blstats": snap.get("blstats", {}),
        "message": snap.get("message", ""),
        "inventory": snap.get("inventory", []),
        "cursor": snap.get("cursor", [0, 0]),
        "chars": chars_grid,
        "colors": colors_grid,
        "descriptions": descs_grid,
        "trajectory_log": snap.get("trajectory_log"),
    }
    tmp = LIVE_STATE_PATH.with_suffix(LIVE_STATE_PATH.suffix + ".tmp")
    tmp.write_text(json.dumps(state))
    tmp.replace(LIVE_STATE_PATH)


def _snapshot(include_grid: bool = False) -> dict[str, Any]:
    """Build the model-facing snapshot.

    `include_grid=True` adds the raw 24x80 chars/colors arrays for use by
    view/tactic functions inside game.exec(). Default is False because the
    grid is large and the rendered `screen` string already covers what the
    model needs to read.
    """
    if STATE.last_obs is None:
        return {
            "started": False,
            "hint": "Call reset() to start a new game.",
        }
    obs = STATE.last_obs
    snap: dict[str, Any] = {
        "started": True,
        "terminated": STATE.terminated,
        "truncated": STATE.truncated,
        "screen": _render_screen(obs),
        "message": _decode_message(obs),
        "blstats": _decode_blstats(obs),
        "inventory": _decode_inventory(obs),
        "cursor": [int(x) for x in obs["tty_cursor"]],
        "trajectory_log": str(STATE.trajectory_path),
        "session": STATE.session_id,
    }
    if include_grid:
        snap["chars"] = [[int(c) for c in row] for row in obs["tty_chars"]]
        snap["colors"] = [[int(c) for c in row] for row in obs["tty_colors"]]
        snap["descriptions"] = _decode_screen_descriptions(obs)
    return snap


def _reset() -> dict[str, Any]:
    env = STATE.ensure_env()
    obs, info = env.reset()
    STATE.last_obs = obs
    STATE.last_info = info
    STATE.terminated = False
    STATE.truncated = False
    STATE.log({"event": "reset", "env": ENV_ID})
    snap = _snapshot()
    _write_live_state(STATE.last_obs, snap)
    return snap


def _observe() -> dict[str, Any]:
    if STATE.last_obs is None:
        STATE.ensure_env()
    return _snapshot()


def _do(action: int | str) -> dict[str, Any]:
    env = STATE.ensure_env()
    if STATE.last_obs is None:
        raise RuntimeError("game not started; call reset() first")
    if STATE.terminated or STATE.truncated:
        raise RuntimeError("game over; call reset() to start a new game")

    idx = STATE.resolve_action(action)
    action_enum = STATE.actions_tuple[idx]
    obs, reward, terminated, truncated, info = env.step(idx)
    STATE.last_obs = obs
    STATE.last_info = info

    # Auto-MORE: when NetHack shows --More-- on the top line, the only useful
    # input is to advance. Loop press MORE until the prompt clears, accumulating
    # the messages so the gamer sees them all.
    messages: list[str] = []
    initial_msg = _decode_message(obs).strip()
    if initial_msg:
        messages.append(initial_msg)
    more_idx = STATE.action_table.get("MORE")
    SAFETY = 50  # absolute cap to prevent infinite loop on weird states
    auto_more_count = 0
    if more_idx is not None:
        while (
            not terminated
            and not truncated
            and _has_more_prompt(obs)
            and auto_more_count < SAFETY
        ):
            obs, more_reward, terminated, truncated, info = env.step(more_idx)
            STATE.last_obs = obs
            STATE.last_info = info
            new_msg = _decode_message(obs).strip()
            if new_msg:
                messages.append(new_msg)
            reward += more_reward
            auto_more_count += 1

    combined = " | ".join(messages)
    STATE.terminated = bool(terminated)
    STATE.truncated = bool(truncated)
    STATE.log({
        "event": "do",
        "action_index": int(idx),
        "action_name": f"{type(action_enum).__name__}.{action_enum.name}",
        "action_keycode": int(action_enum.value),
        "reward": float(reward),
        "terminated": STATE.terminated,
        "truncated": STATE.truncated,
        "blstats": _decode_blstats(obs),
        "message": combined,
        "auto_more_count": auto_more_count,
    })
    snap = _snapshot()
    snap["reward"] = float(reward)
    snap["message"] = combined  # override with full accumulated text
    _write_live_state(STATE.last_obs, snap)
    return snap


# Persistent Python kernel for game.exec(). Imports, variable bindings, and
# definitions persist across exec() calls within a session. NOT cleared on
# reset(); the gamer can keep their helpers across game restarts.
_KERNEL: dict[str, Any] = {"__name__": "__nethack_kernel__"}


def _kernel_do(action: int | str) -> dict[str, Any]:
    """Wrap _do so the kernel's `obs` global stays fresh after each step.

    Without this wrapper, the loop pattern
        while obs['blstats']['x'] > target: do(...)
    becomes infinite — `obs` is captured at exec entry and never updates,
    so the predicate is fixed and the loop bumps the same wall forever
    until NLE truncates the episode. Real bug, hit by the first gamer run.
    """
    slim = _do(action)
    _KERNEL["obs"] = _snapshot(include_grid=True)
    return slim


def _kernel_observe() -> dict[str, Any]:
    snap = _snapshot(include_grid=True)
    _KERNEL["obs"] = snap
    return snap


def _exec_python(python_code: str) -> dict[str, Any]:
    """Run python_code in the persistent kernel; capture stdout/result/error.

    Kernel globals: `obs` (latest snapshot with raw chars/colors/descriptions —
    AUTO-REFRESHED after every kernel do() call), `do(action)`, `observe()`.
    Imports persist across calls (e.g. `from views import crop`).
    """
    _KERNEL["obs"] = _snapshot(include_grid=True)
    _KERNEL["do"] = _kernel_do
    _KERNEL["observe"] = _kernel_observe

    # Snapshot the trajectory file position so we can read out the steps
    # taken during this exec call afterward.
    pos_before = STATE.trajectory_path.stat().st_size if STATE.trajectory_path.exists() else 0

    stdout = io.StringIO()
    err: str | None = None
    result_repr: str | None = None
    try:
        with contextlib.redirect_stdout(stdout):
            try:
                value = builtins.eval(compile(python_code, "<exec>", "eval"), _KERNEL)
                if value is not None:
                    result_repr = value if isinstance(value, str) else repr(value)
            except SyntaxError:
                builtins.exec(compile(python_code, "<exec>", "exec"), _KERNEL)
    except Exception:
        err = traceback.format_exc()

    # Read the trajectory delta — every do()/reset() that happened during exec.
    steps: list[dict[str, Any]] = []
    if STATE.trajectory_path.exists():
        with STATE.trajectory_path.open() as fh:
            fh.seek(pos_before)
            for line in fh.read().splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    steps.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    return {
        "stdout": stdout.getvalue(),
        "result": result_repr,
        "error": err,
        "steps": steps,
        "post_state": _snapshot(),
    }


def _format_exec_result(out: dict[str, Any]) -> str:
    parts: list[str] = []
    if out.get("stdout"):
        parts.append("=== stdout ===\n" + out["stdout"].rstrip())
    if out.get("result") is not None:
        parts.append("=== result ===\n" + str(out["result"]))
    if out.get("error"):
        parts.append("=== error ===\n" + out["error"].rstrip())
    steps = out.get("steps") or []
    if steps:
        lines: list[str] = []
        for s in steps:
            ev = s.get("event")
            if ev == "reset":
                lines.append("       <reset>")
            elif ev == "do":
                turn = s.get("blstats", {}).get("time", "?")
                action = s.get("action_name", "?")
                msg = s.get("message", "") or ""
                rew = s.get("reward")
                rew_part = f"  r={rew}" if rew not in (None, 0.0) else ""
                msg_part = f'  msg="{msg}"' if msg else ""
                lines.append(f"  T={turn:<4}  {action:<32}{rew_part}{msg_part}")
        parts.append(f"=== steps during exec ({len(steps)}) ===\n" + "\n".join(lines))
    parts.append("=== post-exec state ===\n" + _format_for_text(out["post_state"]))
    return "\n\n".join(parts)


@mcp.tool
def reset() -> ToolResult:
    """Start a new NetHack game. Returns the initial observation."""
    return _tool_result(_reset())


@mcp.tool
def observe() -> ToolResult:
    """Return the current game observation without taking an action."""
    return _tool_result(_observe())


@mcp.tool
def do(action: int | str) -> ToolResult:
    """Take one action and return the resulting observation.

    `action` may be an int (gym action index, 0..120 for NetHackChallenge-v0)
    or a string name like 'Command.READ', 'CompassDirection.N', 'north', 'MORE'.
    """
    return _tool_result(_do(action))


@mcp.tool
def exec(python_code: str) -> ToolResult:
    """Run Python in a persistent kernel. State, imports, defs persist across calls.

    In scope each call: `obs` (current observation with raw `chars`/`colors` grids),
    `do(action)` (take an action, returns new snapshot), `observe()` (re-read state).
    `game/views/` and `game/tactics/` are on sys.path — `from views import crop`.

    Returns: stdout + final expression value + traceback (if any) + post-exec state.

    Use this when you'd otherwise call do() many times in a row, or when a view
    function would render the dungeon better than the default screen.
    """
    return ToolResult(
        content=[TextContent(type="text", text=_format_exec_result(_exec_python(python_code)))],
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
