"""MCP server exposing NLE to Claude Code as the in-game harness."""

from __future__ import annotations

import builtins
import contextlib
import io
import json
import linecache
import os
import queue as _queue
import re
import sys
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field
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
        # Role/race/gender/alignment parsed from the welcome message at reset.
        # NLE doesn't expose these in `obs` directly (only alignment via blstats),
        # so we recover them from the "You are a <align> <gender> <race> <role>."
        # text printed on game start. None until first reset.
        self.character: dict[str, str] | None = None
        # Currently-paused safe exec, if any. The threaded gamer code is parked
        # inside its do() call awaiting `continue_exec`; any other MCP tool
        # call drops it via _drop_paused().
        self.paused_exec: "PausedExec | None" = None

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

    Output invariant: always exactly 21 lines (one per dungeon row), so
    `screen.split('\\n')[r]` is `chars[r]`. No leading/trailing rows are
    stripped — that would silently shift the gamer's mental row counts.
    Trailing whitespace within a row is still rstrip'd (no info loss).
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
        map_rows.append("".join(line).rstrip(decorative))
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


def _parse_welcome_message(msg: str) -> dict[str, str] | None:
    """Pull role/race/gender/alignment from NetHack's welcome line.

    Format examples:
      "Hello Agent, welcome to NetHack!  You are a chaotic male orcish Wizard."
      "Konnichi wa Agent, welcome to NetHack!  You are a lawful female human Samurai."
      "Salutations Agent, welcome to NetHack!  You are a neutral human Priestess."  (no gender word for some)
    """
    import re
    # 4-word form: align + gender + race + role
    m = re.search(r"You are an? (\w+) (\w+) (\w+) (\w+)\.", msg)
    if m:
        return {"alignment": m.group(1), "gender": m.group(2),
                "race": m.group(3), "role": m.group(4)}
    # 3-word fallback: align + race + role (no gender; rare)
    m = re.search(r"You are an? (\w+) (\w+) (\w+)\.", msg)
    if m:
        return {"alignment": m.group(1), "gender": "",
                "race": m.group(2), "role": m.group(3)}
    return None


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
        "character": STATE.character,
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
    # Capture role/race/gender/alignment from the welcome message before any
    # subsequent action overwrites it. obs["message"] right after reset holds
    # NetHack's "You are a <align> <gender> <race> <role>." greeting.
    STATE.character = _parse_welcome_message(_decode_message(obs))
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
    _fire_hook("post_reset", {
        "seed": seed,
        "obs": _snapshot(include_grid=True) if _has_hooks("post_reset") else None,
        "character": STATE.character,
    })
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

    _load_hooks()  # idempotent; covers direct MCP do() calls before any exec
    idx = STATE.resolve_action(action)
    action_enum = STATE.actions_tuple[idx]
    # Snapshot pre-step state if any post_do hook is registered (cost: one
    # extra grid build per step, ~10KB; skipped when no hooks need it).
    fire_post_do = _has_hooks("post_do")
    pre_snap = _snapshot(include_grid=True) if fire_post_do else None
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
    if fire_post_do:
        post_snap = _snapshot(include_grid=True)
        _fire_hook("post_do", {
            "action": action,
            "action_name": f"{type(action_enum).__name__}.{action_enum.name}",
            "pre_obs": pre_snap,
            "post_obs": post_snap,
            "reward": float(reward),
            "terminated": STATE.terminated,
            "auto_more_count": auto_more_count,
        })
    return snap


# Persistent Python kernel for game.exec(). Imports, variable bindings, and
# definitions persist across exec() calls within a session. NOT cleared on
# reset(); the gamer can keep their helpers across game restarts.
_KERNEL: dict[str, Any] = {"__name__": "__nethack_kernel__"}


# Hooks system: gamer-side files at game/hooks/*.py register callbacks that
# fire on lifecycle events (post_do, post_reset, ...). This is how we encode
# rules deterministically — e.g. record every Command.SEARCH into a per-level
# memory map so the AI doesn't have to remember to do it manually.
HOOKS: dict[str, list[Any]] = {"post_do": [], "post_reset": [], "post_observe": []}
_HOOKS_LOADED: bool = False


def register_hook(event: str, fn: Any) -> None:
    """Register a callback for a lifecycle event. Called by game/hooks/*.py."""
    HOOKS.setdefault(event, []).append(fn)


def _fire_hook(event: str, payload: dict[str, Any]) -> None:
    """Dispatch all registered callbacks for `event`. Buggy hooks are caught
    and logged but never break the game step."""
    # Snapshot the list so hooks can safely register new hooks without mutation issues.
    for fn in list(HOOKS.get(event, [])):
        try:
            fn(payload)
        except Exception as e:
            # Log to trajectory so post-hoc analysis catches it; never raise.
            STATE.log({"event": "hook_error", "hook_event": event,
                       "hook": getattr(fn, "__name__", repr(fn)), "error": str(e)})


def _has_hooks(event: str) -> bool:
    return bool(HOOKS.get(event))


def _load_hooks() -> None:
    """One-time discovery: import every game/hooks/*.py so they can call
    register_hook() at module load. Idempotent — guarded by _HOOKS_LOADED.
    """
    global _HOOKS_LOADED
    if _HOOKS_LOADED:
        return
    _HOOKS_LOADED = True
    hooks_dir = GAME_DIR / "hooks"
    if not hooks_dir.is_dir():
        return
    import importlib.util
    for path in sorted(hooks_dir.glob("*.py")):
        if path.name.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location(f"hooks.{path.stem}", path)
        if not spec or not spec.loader:
            continue
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception as e:
            STATE.log({"event": "hook_load_error", "file": path.name, "error": str(e)})


def _kernel_do(action: int | str) -> dict[str, Any]:
    """Wrap _do so the kernel's `obs` global stays fresh after each step.
    (post_do hooks fire inside _do itself, so all do() paths trigger them.)
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
    _load_hooks()  # idempotent; first exec or first do() loads game/hooks/*.py
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


# ----------------------------------------------------------------------
# safe_exec: pause-on-message exec, with continue_exec to resume.
#
# The gamer's code runs in a daemon thread. Each `do()` call blocks on a
# queue; the main thread pumps actions to NLE. If the resulting snap has
# any non-empty `message`, we PAUSE the parked thread and return to the
# MCP caller with the message + line/stack info. The gamer either:
#   - calls `continue_exec()` to wake the thread (do() returns the snap)
#   - calls any other tool, which drops the parked thread (it dies, NLE
#     state is fine because the pause boundary is between completed do()s)
# autocontinue: list of regexes; messages matching any pattern auto-resume
# without bothering the gamer.
# ----------------------------------------------------------------------


class _Abandon(BaseException):
    """Injected into a parked safe_exec thread when the gamer moves on.
    Inherits BaseException (not Exception) so plain `except:` clauses in
    gamer code don't accidentally swallow it."""


@dataclass
class PausedExec:
    code: str
    autocontinue: list[str] = field(default_factory=list)
    thread: threading.Thread | None = None
    action_q: _queue.Queue = field(default_factory=lambda: _queue.Queue(maxsize=1))
    response_q: _queue.Queue = field(default_factory=lambda: _queue.Queue(maxsize=1))
    last_snap: dict[str, Any] = field(default_factory=dict)
    last_msg: str = ""
    error: str | None = None


def _drop_paused() -> None:
    """If a safe_exec is parked, signal it to die and clear the slot.
    Called by every other MCP tool entry point."""
    pe = STATE.paused_exec
    if pe is None:
        return
    STATE.paused_exec = None
    try:
        pe.response_q.put_nowait(_Abandon())
    except _queue.Full:
        pass  # thread already moving; it'll see the next put or just exit


def _gamer_pause_location(pe: PausedExec) -> list[dict[str, Any]]:
    """Walk the parked thread's frames to surface a code-snippet stack.
    Topmost entry is the deepest frame (closest to the do() that paused).
    Filters to gamer-authored code only — server internals are hidden."""
    frames_map = sys._current_frames()
    if pe.thread is None:
        return []
    f = frames_map.get(pe.thread.ident)
    stack: list[dict[str, Any]] = []
    while f is not None:
        fname = f.f_code.co_filename
        if fname == "<safe_exec>":
            lines = pe.code.split("\n")
            text = lines[f.f_lineno - 1].rstrip() if 0 < f.f_lineno <= len(lines) else ""
            stack.append({"file": "<safe_exec>", "line": f.f_lineno, "code": text})
        elif str(GAME_DIR) in fname:
            text = linecache.getline(fname, f.f_lineno).rstrip()
            display = fname[len(str(GAME_DIR)) + 1:] if fname.startswith(str(GAME_DIR)) else fname
            stack.append({"file": display, "line": f.f_lineno, "code": text})
        f = f.f_back
    return stack


def _create_paused_exec(code: str, autocontinue: list[str]) -> PausedExec:
    pe = PausedExec(code=code, autocontinue=list(autocontinue))

    def _do_blocking(action: int | str) -> dict[str, Any]:
        pe.action_q.put(("do", action))
        resp = pe.response_q.get()
        if isinstance(resp, BaseException):
            raise resp
        return resp

    def _observe_passthrough() -> dict[str, Any]:
        # observe() is read-only on STATE.last_obs; doesn't advance the game,
        # so it doesn't need to round-trip through the queue. Just snapshot.
        snap = _snapshot(include_grid=True)
        _KERNEL["obs"] = snap
        return snap

    def _run() -> None:
        try:
            _load_hooks()
            _KERNEL["obs"] = _snapshot(include_grid=True)
            _KERNEL["do"] = _do_blocking
            _KERNEL["observe"] = _observe_passthrough
            # Pre-import enums (idempotent — _exec_python does the same).
            if "Command" not in _KERNEL:
                from nle import nethack as _nh
                _KERNEL["Command"] = _nh.Command
                _KERNEL["CompassDirection"] = _nh.CompassDirection
                _KERNEL["CompassDirectionLonger"] = _nh.CompassDirectionLonger
                _KERNEL["MiscDirection"] = _nh.MiscDirection
                _KERNEL["MiscAction"] = _nh.MiscAction
                _KERNEL["TextCharacters"] = _nh.TextCharacters
            builtins.exec(compile(code, "<safe_exec>", "exec"), _KERNEL)
        except _Abandon:
            pass  # gamer dropped us; clean exit
        except BaseException:
            pe.error = traceback.format_exc()
        finally:
            try:
                pe.action_q.put_nowait(("done", None))
            except _queue.Full:
                pass

    pe.thread = threading.Thread(target=_run, daemon=True, name="safe_exec")
    return pe


def _drive_paused(pe: PausedExec) -> dict[str, Any]:
    """Run the main-thread loop: receive actions, step NLE, decide pause/resume.
    Returns when the thread completes, errors, or pauses for the gamer."""
    while True:
        try:
            kind, payload = pe.action_q.get(timeout=30.0)
        except _queue.Empty:
            STATE.paused_exec = None
            return {"status": "error", "error": "safe_exec thread stalled (no action in 30s)"}
        if kind == "done":
            STATE.paused_exec = None
            if pe.error:
                return {"status": "error", "error": pe.error}
            return {"status": "complete"}
        # Step NLE; on exception, propagate back into the thread.
        try:
            snap = _do(payload)
        except BaseException as e:
            pe.response_q.put(e)
            continue
        msg = snap.get("message", "").strip()
        if msg:
            matched = False
            for pat in pe.autocontinue:
                try:
                    if re.search(pat, msg):
                        matched = True
                        break
                except re.error:
                    continue
            if matched:
                pe.response_q.put(snap)
                continue
            # No autocontinue match — pause for the gamer.
            pe.last_snap = snap
            pe.last_msg = msg
            STATE.paused_exec = pe
            return {
                "status": "paused",
                "message": msg,
                "post_obs": snap,
                "stack": _gamer_pause_location(pe),
                "autocontinue": list(pe.autocontinue),
            }
        # Silent step — let the thread proceed.
        pe.response_q.put(snap)


def _safe_exec_python(code: str, autocontinue: list[str] | None = None) -> dict[str, Any]:
    _drop_paused()
    pe = _create_paused_exec(code, autocontinue or [])
    pe.thread.start()
    return _drive_paused(pe)


def _continue_exec(autocontinue: list[str] | None = None) -> dict[str, Any]:
    pe = STATE.paused_exec
    if pe is None:
        return {"status": "error", "error": "no execution paused"}
    if autocontinue is not None:
        pe.autocontinue = list(autocontinue)
    pe.response_q.put(pe.last_snap)
    return _drive_paused(pe)


def _format_safe_exec_result(out: dict[str, Any]) -> str:
    """Render a safe_exec/continue_exec result for the model."""
    status = out.get("status", "?")
    parts: list[str] = [f"=== status: {status} ==="]
    if status == "paused":
        parts.append("=== message ===\n" + str(out.get("message", "")))
        stack = out.get("stack") or []
        if stack:
            lines = []
            for frame in stack:
                fp = frame.get("file", "?")
                ln = frame.get("line", "?")
                code = frame.get("code", "")
                lines.append(f"  {fp}:{ln}    {code}")
            parts.append("=== paused at ===\n" + "\n".join(lines))
        autoc = out.get("autocontinue") or []
        if autoc:
            parts.append("=== autocontinue patterns ===\n" + "\n".join(f"  {p}" for p in autoc))
        parts.append("=== post-step state ===\n" + _format_for_text(out.get("post_obs") or {}))
    elif status == "error":
        parts.append("=== error ===\n" + str(out.get("error", "")).rstrip())
        parts.append("=== post-state ===\n" + _format_for_text(_snapshot()))
    elif status == "complete":
        parts.append("=== post-state ===\n" + _format_for_text(_snapshot()))
    return "\n\n".join(parts)


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
    _drop_paused()
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
    _drop_paused()
    return _tool_result(_do(action), dedup_inventory=True)


@mcp.tool
def exec(python_code: str, autocontinue: list[str] | None = None) -> ToolResult:
    """Run Python in a persistent kernel; PAUSE on any NetHack message.

    Same persistent kernel as `exec_raw`, but every `do()` whose result
    carries a non-empty `message` parks the thread right there and returns
    {"status": "paused", "message", "post_obs", "stack"}. Call
    `continue_exec()` to wake it up; call any other tool to drop it.

    `autocontinue`: list of regex patterns; messages matching any pattern
    auto-resume without bothering you. Useful for routine chatter like
    "You hear ...", "You see here ...". Patterns persist for this exec
    until you replace them via `continue_exec(autocontinue=[...])`.

    Use this for any multi-step plan; `exec_raw` only when you need full
    control and don't want pauses (e.g., scripted item interactions).
    """
    return ToolResult(
        content=[TextContent(type="text",
                             text=_format_safe_exec_result(_safe_exec_python(python_code, autocontinue)))],
    )


@mcp.tool
def continue_exec(autocontinue: list[str] | None = None) -> ToolResult:
    """Resume a paused `exec`. The paused do() returns its snap; gamer code
    continues to the next line. If the next do() also produces a message,
    pauses again — call this repeatedly.

    `autocontinue`: if provided, REPLACES the pattern list for the rest of
    this exec. Omit to keep using the existing list.

    Errors if no exec is currently paused.
    """
    return ToolResult(
        content=[TextContent(type="text",
                             text=_format_safe_exec_result(_continue_exec(autocontinue)))],
    )


@mcp.tool
def exec_raw(python_code: str) -> ToolResult:
    """Run Python in the persistent kernel WITHOUT message-pausing.

    Same kernel as `exec`, but `do()` never pauses on messages — you get
    the snap back regardless. Use only when you genuinely want full
    control over message handling, or for one-shot scripted sequences.

    Returns: stdout + final expression value + traceback (if any) +
    post-exec state.
    """
    _drop_paused()
    return ToolResult(
        content=[TextContent(type="text", text=_format_exec_result(_exec_python(python_code)))],
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
