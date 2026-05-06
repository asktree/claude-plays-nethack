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
# NetHack tty geometry. tty_chars is 24x80 total (NLE keeps the full VT100
# layout). Dungeon proper is at tty rows 1..21 cols 0..78 — row 0 is the
# message line, rows 22-23 are status, col 79 is unused padding.
#
# In our model-facing obs, all 2D arrays (chars, colors, glyphs, descriptions,
# seen, seenv) use a UNIFIED 21x79 dungeon-only shape — no message/status rows,
# no padding col. cursor is dungeon-relative ([row 0..20, col 0..78]) so it
# indexes into chars[r][c] directly. Views and tactics never need to add +1
# offsets. Internal STATE.last_obs still has full tty_chars for the renderer.
DUNGEON_ROWS = 21
DUNGEON_COLS = 79
# Char substituted for `' '` cells we've never had line-of-sight to.
# `°` (degree sign): Latin-1, guaranteed single-width in any monospace font,
# and NetHack uses NO `°` anywhere in its glyph set — zero collision.
# Considered: `?` (scroll collision), `]` (visually too close to `[` armor),
# emoji like ✦ (Unicode width neutral — renders 2-wide in CJK fonts/terminals
# and would break grid alignment). Override via env var.
UNSEEN_CHAR = os.environ.get("NETHACK_UNSEEN_CHAR", "°")

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
        # For inventory dedup in formatted text: track the last inventory we
        # actually rendered. `do()` skips the inventory section when unchanged
        # since last rendered, to keep tool_results small in long sessions.
        self.last_rendered_inventory: list[dict[str, str]] | None = None
        # Per-level "seen" boolean grid (24x80). Marks any cell that has ever
        # been rendered as a non-blank glyph OR was adjacent to @. The `screen`
        # render substitutes UNSEEN_CHAR for `' '` cells where seen is False,
        # so the gamer can distinguish unexplored frontier from known void.
        self.seen_per_level: dict[tuple[int, int], list[list[bool]]] = {}

    def ensure_env(self) -> gym.Env:
        if self.env is None:
            obs_keys = (
                "tty_chars", "tty_colors", "tty_cursor",
                "blstats", "message",
                "inv_glyphs", "inv_strs", "inv_letters", "inv_oclasses",
                "screen_descriptions",
                "glyphs",  # 21x79 NetHack glyph IDs — encode monster/item/terrain type
                "seenv",   # 21x79 NetHack seenv bitmask — ground truth for "seen this cell"
                           # (requires our forked NLE; see /Users/em/Coding/nle-fork)
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

    def resolve_action(self, action) -> int:
        # NLE action enums (CompassDirection.NW, Command.READ, etc) are
        # IntEnum members — `int(member) = keypress byte`, NOT the gym action
        # index. Map by .value to find the index.
        import enum
        if isinstance(action, enum.IntEnum):
            target = int(action.value)
            for idx, ae in enumerate(self.actions_tuple):
                if int(ae.value) == target:
                    return idx
            raise ValueError(f"enum {action!r} (value={target}) not in action set")
        if isinstance(action, int):
            if action < 0 or action >= len(self.actions_tuple):
                raise ValueError(f"action index {action} out of range [0, {len(self.actions_tuple)})")
            return action
        if isinstance(action, str):
            # No .strip() here — '\r' (MORE), ' ' (SPACE) and friends are
            # valid single-char keypresses and would be eaten by strip.
            key = action
            # Single-char strings → look up by KEYPRESS, not short-name.
            # do("y") = literal y key (= CompassDirection.NW for movement OR
            # "yes" in a prompt; NetHack interprets the byte in context).
            # do("n"), do("?"), etc. all work the same way. This sidesteps the
            # confusion where "n" could mean "north" alias or the n key (SE).
            if len(key) == 1:
                target = ord(key)
                for idx, action_enum in enumerate(self.actions_tuple):
                    if int(action_enum.value) == target:
                        return idx
                raise ValueError(
                    f"keypress {key!r} (byte {target}) is not in the action set"
                )
            if key in self.action_table:
                return self.action_table[key]
            if key.lower() in self.action_table:
                return self.action_table[key.lower()]
            raise ValueError(
                f"unknown action name {action!r}. "
                f"Try a Command/CompassDirection/MiscAction enum name "
                f"(e.g. 'Command.READ', 'north', 'MORE'), or a single key char."
            )
        raise TypeError(f"action must be int or str, got {type(action).__name__}")

    def _level_key(self, obs: dict[str, Any]) -> tuple[int, int] | None:
        if obs is None or "blstats" not in obs:
            return None
        bl = _decode_blstats(obs)
        return (bl.get("dungeon_number", 0), bl.get("level_number", 0))

    def update_seen(self, obs: dict[str, Any]) -> None:
        """Read NetHack's per-cell seenv bitmask into our 21x79 seen grid.

        seenv is a uint8 per dungeon cell tracking which directions the player
        has viewed the cell from. Any non-zero value = seen. Ground truth via
        our forked NLE (see /Users/em/Coding/nle-fork). seen grid uses the same
        dungeon-relative indexing as glyphs/descriptions — `seen[r][c]` aligns
        directly to `chars[r][c]` in the model-facing snapshot.
        """
        if obs is None or "seenv" not in obs:
            return
        key = self._level_key(obs)
        if key is None:
            return
        seen = self.seen_per_level.setdefault(key, [[False] * DUNGEON_COLS for _ in range(DUNGEON_ROWS)])
        seenv = obs["seenv"]
        for gr in range(min(len(seenv), DUNGEON_ROWS)):
            row = seenv[gr]
            for gc in range(min(len(row), DUNGEON_COLS)):
                if int(row[gc]) != 0:
                    seen[gr][gc] = True

    def current_seen(self, obs: dict[str, Any]) -> list[list[bool]] | None:
        key = self._level_key(obs)
        return self.seen_per_level.get(key) if key is not None else None

    def log(self, record: dict[str, Any]) -> None:
        record = {"t": time.time(), "session": self.session_id, **record}
        with self.trajectory_path.open("a") as fh:
            fh.write(json.dumps(record, default=str) + "\n")


STATE = GameState()


def _render_screen(obs: dict[str, Any]) -> str:
    """Render the dungeon map, with `' '` cells replaced by UNSEEN_CHAR when
    they've never been in line-of-sight on the current level.

    Reads from the raw 24×80 tty_chars (slicing rows 1..21, cols 0..78 — the
    dungeon area — and dropping col 79 padding). seen[r][c] is the
    dungeon-relative 21×79 grid, indexed directly.
    """
    chars = obs["tty_chars"]
    seen = STATE.current_seen(obs)
    decorative = " " + UNSEEN_CHAR
    map_rows: list[str] = []
    for gr in range(DUNGEON_ROWS):
        row_chars = chars[gr + 1]  # +1 because tty_chars row 0 is message line
        line = []
        for gc in range(DUNGEON_COLS):
            v = int(row_chars[gc])
            ch = chr(v) if v else " "
            if ch == " " and seen is not None and not seen[gr][gc]:
                ch = UNSEEN_CHAR
            line.append(ch)
        # rstrip ' ' and unseen marker — trailing run carries no info.
        map_rows.append("".join(line).rstrip(decorative))
    while map_rows and not map_rows[0]:
        map_rows.pop(0)
    while map_rows and not map_rows[-1]:
        map_rows.pop()
    return "\n".join(map_rows)


def _decode_message(obs: dict[str, Any]) -> str:
    return bytes(obs["message"]).rstrip(b"\x00").decode("latin-1", errors="replace")


def _chars_to_strings(obs: dict[str, Any]) -> list[str]:
    """Encode tty_chars as 24 strings of 80 chars each (full grid, no crop).

    Compact and human-readable in the trajectory log — replaying any turn is
    just `obs['chars']` from the line, parsed back to a 2D structure if needed.
    """
    if "tty_chars" not in obs:
        return []
    out: list[str] = []
    for row in obs["tty_chars"]:
        out.append("".join(chr(int(c)) if c else " " for c in row))
    return out


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


# NetHack hunger states from include/hack.h. The header was showing a raw int
# (e.g. "Hunger=2") which the gamer kept missing — labels are unmissable.
HUNGER_LABELS = {
    0: "Satiated", 1: "Normal", 2: "Hungry",
    3: "Weak", 4: "Fainting", 5: "Fainted", 6: "Starved",
}


def _format_for_text(snap: dict[str, Any], *, dedup_inventory: bool = False) -> str:
    """Render a snapshot as the text the model will actually read.

    `dedup_inventory=True` (used by `do()`): if inventory hasn't changed since
    last render, show "(unchanged from last turn — call observe() to see)"
    instead of the full list. Saves ~500 tokens/call across long sessions.
    `observe()` and `exec` always render full inventory (no dedup).
    """
    if not snap.get("started"):
        return snap.get("hint", "(no game started)")
    bl = snap.get("blstats", {})
    hunger_int = bl.get("hunger_state", "?")
    hunger = HUNGER_LABELS.get(hunger_int, str(hunger_int))
    lines = []
    lines.append(
        f"T={bl.get('time','?')}  "
        f"HP={bl.get('hitpoints','?')}/{bl.get('max_hitpoints','?')}  "
        f"Pw={bl.get('energy','?')}/{bl.get('max_energy','?')}  "
        f"Dlvl={bl.get('depth','?')}  "
        f"AC={bl.get('armor_class','?')}  "
        f"$={bl.get('gold','?')}  "
        f"XP={bl.get('experience_level','?')}/{bl.get('experience_points','?')}  "
        f"Hunger={hunger}"
    )
    msg = snap.get("message") or ""
    if msg:
        lines.append(f"msg: {msg}")
    lines.append("")
    lines.append(snap.get("screen", ""))
    inv = snap.get("inventory") or []
    if inv:
        lines.append("")
        unchanged = dedup_inventory and inv == STATE.last_rendered_inventory
        if unchanged:
            lines.append("Inventory: (unchanged from last turn — call observe() to see full list)")
        else:
            lines.append("Inventory:")
            for it in inv:
                lines.append(f"  {it['letter']} - {it['text']}")
            STATE.last_rendered_inventory = list(inv)
    if "reward" in snap:
        lines.append("")
        lines.append(f"reward: {snap['reward']}")
    if snap.get("terminated") or snap.get("truncated"):
        lines.append("")
        lines.append("** GAME OVER **")
    return "\n".join(lines)


def _tool_result(snap: dict[str, Any], *, dedup_inventory: bool = False) -> ToolResult:
    """Wrap a snapshot as a single TextContent block.

    We deliberately do NOT set `structured_content`: Claude Code's UI surfaces
    structured_content as JSON (with `\\n` escapes), which destroys the dungeon
    map for the human watching. The trajectory log already captures structured
    state for any post-hoc analysis; we don't need it on the wire.
    """
    return ToolResult(
        content=[TextContent(type="text", text=_format_for_text(snap, dedup_inventory=dedup_inventory))],
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
    # All 2D grids written here are 21x79 (dungeon-only) — view.py consumes
    # them with the same indexing. cursor is dungeon-relative (in snap already).
    tty_chars = obs["tty_chars"]
    tty_colors = obs["tty_colors"]
    chars_grid = [
        [int(tty_chars[gr + 1][gc]) for gc in range(DUNGEON_COLS)]
        for gr in range(DUNGEON_ROWS)
    ]
    colors_grid = [
        [int(tty_colors[gr + 1][gc]) for gc in range(DUNGEON_COLS)]
        for gr in range(DUNGEON_ROWS)
    ]
    descs_grid = _decode_screen_descriptions(obs)
    seen_grid = STATE.current_seen(obs)
    glyphs_grid = (
        [[int(g) for g in row] for row in obs["glyphs"]]
        if "glyphs" in obs else None
    )
    # NetHack's bottom-of-screen status rows (rows 22-23 of the 24-row tty).
    # We strip these from chars (since blstats has the structured info), but
    # view.sh wants to show them in the familiar "Agent the Footpad ..." form.
    tty_chars_full = obs["tty_chars"]
    status_rows = [
        "".join(chr(int(c)) if c else " " for c in tty_chars_full[r]).rstrip()
        for r in (22, 23)
        if r < len(tty_chars_full)
    ]
    state = {
        "session": snap.get("session"),
        "terminated": snap.get("terminated"),
        "truncated": snap.get("truncated"),
        "blstats": snap.get("blstats", {}),
        "message": snap.get("message", ""),
        "inventory": snap.get("inventory", []),
        "cursor": snap.get("cursor", [0, 0]),  # already dungeon-relative
        "chars": chars_grid,
        "colors": colors_grid,
        "descriptions": descs_grid,
        "glyphs": glyphs_grid,
        "seen": [list(row) for row in seen_grid] if seen_grid else None,
        "status_rows": status_rows,
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
    tty_cursor = obs["tty_cursor"]
    # Cursor in dungeon-relative coords: subtract 1 from row to skip the
    # message line. cursor[0] now indexes chars[r] directly (0..20).
    dungeon_cursor = [int(tty_cursor[0]) - 1, int(tty_cursor[1])]
    snap: dict[str, Any] = {
        "started": True,
        "terminated": STATE.terminated,
        "truncated": STATE.truncated,
        "screen": _render_screen(obs),
        "message": _decode_message(obs),
        "blstats": _decode_blstats(obs),
        "inventory": _decode_inventory(obs),
        "cursor": dungeon_cursor,
        "trajectory_log": str(STATE.trajectory_path),
        "session": STATE.session_id,
    }
    if include_grid:
        # All 2D grids are 21x79 dungeon-only — chars[r][c], colors[r][c],
        # descriptions[r][c], glyphs[r][c], seen[r][c] all use the same
        # indexing. r in 0..20 is the dungeon row; c in 0..78 is the col.
        tty_chars = obs["tty_chars"]
        tty_colors = obs["tty_colors"]
        snap["chars"] = [
            [int(tty_chars[gr + 1][gc]) for gc in range(DUNGEON_COLS)]
            for gr in range(DUNGEON_ROWS)
        ]
        snap["colors"] = [
            [int(tty_colors[gr + 1][gc]) for gc in range(DUNGEON_COLS)]
            for gr in range(DUNGEON_ROWS)
        ]
        snap["descriptions"] = _decode_screen_descriptions(obs)
        if "glyphs" in obs:
            snap["glyphs"] = [[int(g) for g in row] for row in obs["glyphs"]]
        seen = STATE.current_seen(obs)
        if seen is not None:
            snap["seen"] = [list(row) for row in seen]
    return snap


def _reset() -> dict[str, Any]:
    env = STATE.ensure_env()
    # Generate and log a known seed so the run is reproducible from the trajectory.
    import random
    seed = int(os.environ.get("NETHACK_SEED") or random.randint(0, 2**31 - 1))
    STATE.seen_per_level.clear()  # fresh game, fresh memory
    obs, info = env.reset(seed=seed)
    STATE.last_obs = obs
    STATE.last_info = info
    STATE.terminated = False
    STATE.truncated = False
    STATE.update_seen(obs)
    # Roll the trajectory file: every game gets its own <timestamp>-<seed>.jsonl
    # so post-hoc analysis splits naturally per game (vs per server-session).
    STATE.trajectory_path = TRAJECTORY_DIR / f"{int(time.time())}-{seed}.jsonl"
    # Reference where the corresponding Claude Code conversation lives; the
    # gamer-Claude session jsonl path is encoded from the gamer cwd.
    gamer_session_dir = Path.home() / ".claude" / "projects" / str(GAME_DIR).replace("/", "-")
    STATE.log({
        "event": "reset",
        "env": ENV_ID,
        "seed": seed,
        "claude_session_dir": str(gamer_session_dir),
        "chars": _chars_to_strings(obs),
        "cursor": [int(x) for x in obs["tty_cursor"]],
    })
    snap = _snapshot()
    _write_live_state(STATE.last_obs, snap)
    return snap


def _observe() -> dict[str, Any]:
    # Lazy auto-reset: the gamer can't call reset() (it isn't an MCP tool).
    # First observe() or do() in a fresh server starts the game transparently.
    if STATE.last_obs is None:
        _reset()
    return _snapshot()


def _do(action: int | str) -> dict[str, Any]:
    env = STATE.ensure_env()
    if STATE.last_obs is None:
        _reset()
    if STATE.terminated or STATE.truncated:
        raise RuntimeError(
            "game over — restart the harness (./run.sh) to start a new game"
        )

    idx = STATE.resolve_action(action)
    action_enum = STATE.actions_tuple[idx]
    obs, reward, terminated, truncated, info = env.step(idx)
    STATE.last_obs = obs
    STATE.last_info = info
    STATE.update_seen(obs)

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
            STATE.update_seen(obs)
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
        "chars": _chars_to_strings(obs),
        "cursor": [int(x) for x in obs["tty_cursor"]],
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
    # Pre-import NLE action enums so the gamer can write
    # `do(CompassDirection.NW)` or `do(Command.READ)` without bringing them in
    # explicitly. Single-char strings like `do("y")` go straight to keypress.
    if "Command" not in _KERNEL:
        from nle import nethack as _nh
        _KERNEL["Command"] = _nh.Command
        _KERNEL["CompassDirection"] = _nh.CompassDirection
        _KERNEL["CompassDirectionLonger"] = _nh.CompassDirectionLonger
        _KERNEL["MiscDirection"] = _nh.MiscDirection
        _KERNEL["MiscAction"] = _nh.MiscAction
        _KERNEL["TextCharacters"] = _nh.TextCharacters

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


# Note: reset() is intentionally NOT exposed as an MCP tool. The gamer should
# not be able to restart themselves mid-game (no escape hatch). _observe and
# _do auto-init a game on first call. For a fresh game, restart `./run.sh`
# (which spawns a new MCP server process).


@mcp.tool
def observe() -> ToolResult:
    """Return the current game observation without taking an action.

    Always shows full inventory (no dedup) — call this when you want a
    confirmed full view, e.g. after `do()` reported inventory unchanged
    but you want to double-check.
    """
    return _tool_result(_observe(), dedup_inventory=False)


@mcp.tool
def do(action: int | str) -> ToolResult:
    """Take one action and return the resulting observation.

    `action` may be an int (gym action index, 0..120 for NetHackChallenge-v0)
    or a string name like 'Command.READ', 'CompassDirection.N', 'north', 'MORE'.

    Inventory section is deduped: if it hasn't changed since last `do()`/render,
    you'll see "Inventory: (unchanged...)" instead of the full list. Call
    `observe()` to force a full render.
    """
    return _tool_result(_do(action), dedup_inventory=True)


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
