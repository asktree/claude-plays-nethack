"""Live-watch TUI for the NetHack gamer.

Reads three live streams:
  - game/.live_state.json      (the MCP server writes this each turn)
  - game/trajectory/<latest>.jsonl  (per-action game log)
  - ~/.claude/projects/-Users-em-Coding-claude-plays-nethack-game/<latest>.jsonl
    (gamer-Claude's session transcript: tool calls + reasoning + thinking)

Renders with rich.Live: colored map + inventory + auto-derived legend +
unified action/reasoning log.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

REPO_ROOT = Path(__file__).resolve().parents[2]
LIVE_STATE_PATH = Path(
    os.environ.get("NETHACK_LIVE_STATE", REPO_ROOT / "game" / ".live_state.json")
)
TRAJECTORY_DIR = Path(
    os.environ.get("NETHACK_TRAJECTORY_DIR", REPO_ROOT / "game" / "trajectory")
)
GAMER_SESSION_DIR = Path(os.path.expanduser(
    "~/.claude/projects/-Users-em-Coding-claude-plays-nethack-game"
))

# NetHack 0..15 color palette → rich color names.
NH_COLOR_TO_RICH: dict[int, str] = {
    0: "black",
    1: "red",
    2: "green",
    3: "yellow",       # CLR_BROWN
    4: "blue",
    5: "magenta",
    6: "cyan",
    7: "bright_black", # CLR_GRAY
    8: "bright_black",
    9: "bright_red",   # CLR_ORANGE-ish
    10: "bright_green",
    11: "bright_yellow",
    12: "bright_blue",
    13: "bright_magenta",
    14: "bright_cyan",
    15: "white",
}

# Glyphs whose meaning is obvious; skip in legend.
LEGEND_SKIP = set(" .#-|+@<>")


@dataclass
class TrajectoryEvent:
    t: float
    turn: int | None
    action_name: str | None
    reward: float | None
    message: str
    raw: dict[str, Any]


@dataclass
class SessionEvent:
    t: float
    kind: str  # "thinking" | "text" | "tool_use"
    text: str
    code: str | None = None  # python source for exec() tool_use, None otherwise


EVENT_RETENTION = 500  # cap per reader so old events drop off


@dataclass
class TailReader:
    """Tails a jsonl file and incrementally parses each new line.

    Why incremental: the previous design re-walked ALL accumulated lines on every
    refresh tick, json-decoding the whole file repeatedly. With ~1000+ lines per
    session and a 200ms tick, this gradually fell behind real time. Now we parse
    each line exactly once as it's first read, then keep a bounded ring of
    parsed events.
    """
    directory: Path | None = None
    parse_record: Callable[[dict[str, Any]], list[Any]] | None = None
    path: Path | None = None
    offset: int = 0
    pending: str = ""  # last partial line (no trailing newline yet)
    events: list[Any] = field(default_factory=list)

    def refresh(self) -> None:
        latest = _latest_jsonl(self.directory)
        if latest != self.path:
            self.path = latest
            self.offset = 0
            self.pending = ""
            self.events = []
        if self.path is None:
            return
        try:
            with self.path.open("rb") as fh:
                fh.seek(self.offset)
                chunk = fh.read()
                self.offset = fh.tell()
        except FileNotFoundError:
            self.path = None
            return
        if not chunk:
            return
        combined = self.pending + chunk.decode("utf-8", errors="replace")
        parts = combined.split("\n")
        self.pending = parts.pop()  # "" if combined ended with \n, else partial
        for line in parts:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if self.parse_record is not None:
                new = self.parse_record(rec)
                if new:
                    self.events.extend(new)
        if len(self.events) > EVENT_RETENTION:
            self.events = self.events[-EVENT_RETENTION:]


def _latest_jsonl(directory: Path | None) -> Path | None:
    if directory is None or not directory.exists():
        return None
    candidates = sorted(directory.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def _trajectory_record(rec: dict[str, Any]) -> list[TrajectoryEvent]:
    if rec.get("event") == "do":
        return [TrajectoryEvent(
            t=float(rec.get("t", 0)),
            turn=rec.get("blstats", {}).get("time"),
            action_name=rec.get("action_name"),
            reward=rec.get("reward"),
            message=rec.get("message", "") or "",
            raw=rec,
        )]
    if rec.get("event") == "reset":
        return [TrajectoryEvent(
            t=float(rec.get("t", 0)),
            turn=None,
            action_name="<reset>",
            reward=None,
            message="",
            raw=rec,
        )]
    return []


def _session_record(rec: dict[str, Any]) -> list[SessionEvent]:
    if rec.get("type") != "assistant":
        return []
    ts_str = rec.get("timestamp")
    try:
        ts = time.mktime(time.strptime(ts_str.split(".")[0], "%Y-%m-%dT%H:%M:%S")) if ts_str else 0
    except Exception:
        ts = 0
    out: list[SessionEvent] = []
    msg = rec.get("message", {})
    for block in msg.get("content", []):
        if not isinstance(block, dict):
            continue
        btype = block.get("type")
        if btype == "thinking":
            txt = (block.get("thinking") or "").strip()
            if txt:
                out.append(SessionEvent(t=ts, kind="thinking", text=txt))
        elif btype == "text":
            txt = (block.get("text") or "").strip()
            if txt:
                out.append(SessionEvent(t=ts, kind="text", text=txt))
        elif btype == "tool_use":
            name = block.get("name", "")
            inp = block.get("input", {})
            if "nethack" in name:
                short = name.replace("mcp__nethack__", "")
                if short == "exec" and isinstance(inp, dict):
                    code = (inp.get("python_code") or "").rstrip()
                    n_lines = len(code.splitlines()) if code else 0
                    out.append(SessionEvent(
                        t=ts,
                        kind="tool_use",
                        text=f"exec [{n_lines} line{'' if n_lines == 1 else 's'}]",
                        code=code,
                    ))
                else:
                    arg = inp.get("action") if isinstance(inp, dict) else inp
                    out.append(SessionEvent(
                        t=ts,
                        kind="tool_use",
                        text=f"{short}({arg!r})" if arg is not None else f"{short}()",
                    ))
    return out


def _trajectory_reader() -> TailReader:
    return TailReader(directory=TRAJECTORY_DIR, parse_record=_trajectory_record)


def _session_reader() -> TailReader:
    return TailReader(directory=GAMER_SESSION_DIR, parse_record=_session_record)


def _read_state() -> dict[str, Any] | None:
    try:
        return json.loads(LIVE_STATE_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _build_screen(state: dict[str, Any]) -> tuple[Text, int, int]:
    """Render the full colored dungeon map. Returns (text, width, height).

    NetHack's dungeon area is fixed at 21 rows x 80 cols (rows 1..21 of the
    24-row tty; rows 0 and 22-23 are message and status). We drop those four
    rows but keep the full 21x80 grid even when mostly blank — position
    consistency matters for spatial reasoning, and frame-to-frame layout
    shouldn't shift around as the player explores.
    """
    chars = state["chars"]
    colors = state["colors"]
    rows_chars = chars[1:-2]
    rows_colors = colors[1:-2]

    out = Text()
    for i, (row_chars, row_colors) in enumerate(zip(rows_chars, rows_colors, strict=True)):
        for ch, col in zip(row_chars, row_colors, strict=True):
            char = chr(ch) if ch else " "
            color_name = NH_COLOR_TO_RICH.get(int(col) & 0xF, "white")
            out.append(char, style=color_name)
        if i < len(rows_chars) - 1:
            out.append("\n")
    width = len(rows_chars[0]) if rows_chars else 0
    height = len(rows_chars)
    return out, width, height


def _build_inventory(state: dict[str, Any]) -> Panel:
    inv = state.get("inventory", []) or []
    if not inv:
        body = Text("(empty)", style="dim")
    else:
        body = Text()
        for it in inv:
            body.append(f" {it.get('letter','?')} ", style="bold yellow")
            body.append(f"{it.get('text','')}\n")
    return Panel(body, title="Inventory", border_style="blue", padding=(0, 1))


def _build_legend(state: dict[str, Any]) -> Panel:
    chars = state["chars"]
    descs = state.get("descriptions") or []
    # NLE's screen_descriptions is 21x79 and starts at chars row 1 (top message
    # line is not in descriptions); align by offset.
    seen: dict[str, str] = {}
    for r, row in enumerate(chars):
        for c, ch in enumerate(row):
            char = chr(ch) if ch else " "
            if char in LEGEND_SKIP or char in seen:
                continue
            dr, dc = r - 1, c
            desc = ""
            if 0 <= dr < len(descs) and 0 <= dc < len(descs[dr]):
                desc = descs[dr][dc]
            if desc:
                seen[char] = desc
    if not seen:
        body = Text("(only obvious glyphs visible)", style="dim")
    else:
        body = Text()
        for char in sorted(seen.keys()):
            body.append(f" {char} ", style="bold")
            body.append(f"— {seen[char]}\n")
    return Panel(body, title="Legend (visible)", border_style="magenta", padding=(0, 1))


def _build_log(_traj: list[TrajectoryEvent], sess: list[SessionEvent]) -> Panel:
    """Render the gamer's session activity, newest-first.

    Rendering top-down with newest at top means rich's natural bottom-cropping
    behavior (when the panel is shorter than the content) drops the OLDEST
    events. The latest activity is always visible at the top regardless of
    terminal size — same convention as Slack, Discord, htop, twitter feeds.

    Thinking-block text is empty in saved transcripts (Claude Code strips
    plaintext post-v2.1.89) so empty thinking events are dropped.
    """
    KIND_STYLE = {
        "think": ("yellow", "💭"),
        "say":   ("cyan", "💬"),
        "call":  ("bright_blue", "🛠"),
    }
    CODE_PREVIEW_LINES = 6  # for exec tool_use, show first N lines of python_code
    body = Text()
    rendered = 0
    # Walk newest -> oldest, append top-to-bottom of the panel.
    for e in reversed(sess[-60:]):
        if e.kind == "thinking" and not e.text:
            continue
        kind = {"thinking": "think", "text": "say", "tool_use": "call"}.get(e.kind)
        if kind is None:
            continue
        color, icon = KIND_STYLE[kind]
        text = e.text
        if kind in ("think", "say"):
            text = text.replace("\n", " ")
            if len(text) > 240:
                text = text[:237] + "…"
        body.append(f"{icon} ", style=color)
        body.append(f"{text}\n", style=color)
        # exec calls: show the python code, indented and dim.
        if kind == "call" and e.code:
            code_lines = e.code.splitlines()
            for i, ln in enumerate(code_lines[:CODE_PREVIEW_LINES]):
                if len(ln) > 100:
                    ln = ln[:97] + "…"
                body.append(f"     │ {ln}\n", style="dim cyan")
            if len(code_lines) > CODE_PREVIEW_LINES:
                body.append(f"     └ (+{len(code_lines)-CODE_PREVIEW_LINES} more lines)\n", style="dim")
        rendered += 1
        if rendered >= 40:
            break
    if rendered == 0:
        body = Text("(no activity yet — start a gamer session)", style="dim")
    return Panel(body, title="Recent activity (newest ↑)", border_style="green", padding=(0, 1))


def _build_header(state: dict[str, Any]) -> Panel:
    bl = state.get("blstats", {}) or {}
    msg = state.get("message", "") or ""
    session = state.get("session") or "?"
    hunger = bl.get("hunger_state", "?")
    line1 = (
        f"session={session}  T={bl.get('time','?')}  "
        f"HP={bl.get('hitpoints','?')}/{bl.get('max_hitpoints','?')}  "
        f"Pw={bl.get('energy','?')}/{bl.get('max_energy','?')}  "
        f"Dlvl={bl.get('depth','?')}  "
        f"AC={bl.get('armor_class','?')}  "
        f"$={bl.get('gold','?')}  "
        f"XP={bl.get('experience_level','?')}/{bl.get('experience_points','?')}  "
        f"Score={bl.get('score','?')}  "
        f"Hunger={hunger}"
    )
    body = Text(line1, style="bold")
    if msg:
        body.append("\n")
        body.append(f"msg: {msg}", style="italic yellow")
    if state.get("terminated") or state.get("truncated"):
        body.append("\n** GAME OVER **", style="bold red")
    return Panel(body, border_style="white", padding=(0, 1))


def _build_layout(state: dict[str, Any] | None,
                  traj: list[TrajectoryEvent],
                  sess: list[SessionEvent]) -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=4),
        Layout(name="body", ratio=1),
    )
    if state is None:
        layout["header"].update(Panel(Text(
            "Waiting for live state... start a game with ./run.sh in another terminal.",
            style="dim",
        ), border_style="white"))
        body = Layout(name="body")
        body.split_row(
            Layout(_build_log(traj, sess), name="left"),
            Layout(Panel(Text("(no map yet)", style="dim")), name="right", size=40),
        )
        layout["body"].update(body)
        return layout

    layout["header"].update(_build_header(state))

    map_text, map_w, map_h = _build_screen(state)
    # Panel adds 2 chars horizontal (borders), 2 vertical, plus our padding=(0,1) → +2 horizontal.
    map_panel_width = map_w + 4
    map_panel_height = map_h + 2
    map_panel = Panel(map_text, title="NetHack", border_style="white", padding=(0, 1), width=map_panel_width)

    body = Layout(name="body")
    body.split_row(
        Layout(name="left"),
        Layout(name="right", size=44),
    )

    left = Layout(name="left_inner")
    left.split_column(
        Layout(map_panel, name="map", size=map_panel_height),
        Layout(_build_log(traj, sess), name="activity"),
    )
    body["left"].update(left)

    right = Layout(name="right_inner")
    right.split_column(
        Layout(_build_inventory(state), name="inv"),
        Layout(_build_legend(state), name="legend"),
    )
    body["right"].update(right)

    layout["body"].update(body)
    return layout


def main() -> None:
    console = Console()
    traj_reader = _trajectory_reader()
    sess_reader = _session_reader()
    with Live(console=console, screen=True, refresh_per_second=5) as live:
        while True:
            traj_reader.refresh()
            sess_reader.refresh()
            state = _read_state()
            live.update(_build_layout(state, traj_reader.events, sess_reader.events))
            time.sleep(0.2)


if __name__ == "__main__":
    main()
