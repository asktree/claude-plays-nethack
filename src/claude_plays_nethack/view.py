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

import atexit
import json
import os
import re
import select
import sys
import termios
import threading
import time
import tty
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
    ts_str = rec.get("timestamp")
    try:
        ts = time.mktime(time.strptime(ts_str.split(".")[0], "%Y-%m-%dT%H:%M:%S")) if ts_str else 0
    except Exception:
        ts = 0
    out: list[SessionEvent] = []

    # User-type messages: pull tool_result content and extract NetHack
    # `msg: ...` lines so game messages flow into the activity log
    # alongside thinking/text/tool_use, all from the same session-jsonl
    # source so they share the same write-cadence.
    if rec.get("type") == "user":
        for b in rec.get("message", {}).get("content", []) or []:
            if not isinstance(b, dict) or b.get("type") != "tool_result":
                continue
            content = b.get("content", "")
            if isinstance(content, list):
                content = "".join(c.get("text", "") for c in content if isinstance(c, dict))
            for line in str(content).split("\n"):
                if line.startswith("msg: "):
                    msg = line[5:].strip()
                    if msg:
                        out.append(SessionEvent(t=ts, kind="msg", text=msg))
                    break  # only the first msg: line per tool result
        return out

    if rec.get("type") != "assistant":
        return []
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


UNSEEN_GLYPH = "░"  # light-shade block; single-width in mac monospace; "fog"
UNSEEN_STYLE = "grey50"  # rich's standard dim-grey; renders as 50% white


def _build_screen(state: dict[str, Any]) -> tuple[Text, int, int]:
    """Render the full colored dungeon map. Returns (text, width, height).

    Reads from `state["chars"]` and `state["seen"]` which are now both 21×79
    dungeon-relative grids (no message/status rows, no padding col). Cell
    indexing is direct: `chars[r][c]` and `seen[r][c]` align.

    Cells that have never been in line-of-sight are rendered as a dim-grey
    `░` (fog), matching the model's text overlay (`°`).
    """
    chars = state["chars"]
    colors = state["colors"]
    seen = state.get("seen")  # 21x79, may be None for older live states

    out = Text()
    for r in range(len(chars)):
        row_chars = chars[r]
        row_colors = colors[r] if r < len(colors) else []
        for c in range(len(row_chars)):
            ch_int = row_chars[c]
            char = chr(ch_int) if ch_int else " "
            is_unseen = (
                seen is not None
                and r < len(seen)
                and c < len(seen[r])
                and not seen[r][c]
            )
            if char == " " and is_unseen:
                out.append(UNSEEN_GLYPH, style=UNSEEN_STYLE)
            else:
                col_int = int(row_colors[c]) if c < len(row_colors) else 0
                color_name = NH_COLOR_TO_RICH.get(col_int & 0xF, "white")
                out.append(char, style=color_name)
        if r < len(chars) - 1:
            out.append("\n")
    width = len(chars[0]) if chars else 0
    height = len(chars)
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


def _build_header(state: dict[str, Any]) -> Panel:
    """Compact header panel that lives in col 1 above the map.

    Renders 3 thematic status lines from structured blstats + character info
    (no longer parses NetHack's tty status_rows directly), then message and
    game-over flag.

    Line 1 — IDENTITY:    "Agent the Hatamoto (lawful human Samurai)"
    Line 2 — VITALS:      "HP:15(15)  Pw:2(2)  AC:4  Hunger:Normal"
    Line 3 — PROGRESSION: "Dlvl:1  T:98  $:0  Xp:1/4  ·  St:18/01 Dx:14 Co:14 In:8 Wi:11 Ch:7"
    """
    import re
    rows = state.get("status_rows") or []
    bl = state.get("blstats", {}) or {}
    msg = state.get("message", "") or ""
    char = state.get("character") or {}
    body = Text()

    # Line 1 — identity. Name+title comes from NetHack's row 22 (the rank
    # title like "Hatamoto" advances with experience; not in blstats), then
    # we append (alignment race role) from the parsed welcome message.
    row22 = rows[0] if rows else ""
    m = re.search(r"\s+St:", row22)
    name_part = row22[:m.start()].rstrip() if m else row22.rstrip()
    align = char.get("alignment") or ""
    race = char.get("race") or ""
    role = char.get("role") or ""
    inner_parts = [x for x in (align, race, role) if x]
    if inner_parts:
        body.append(f"{name_part} ({' '.join(inner_parts)})", style="bold")
    elif name_part:
        body.append(name_part, style="bold")
    body.append("\n")

    if bl:
        from .server import HUNGER_LABELS  # type: ignore
        hunger = HUNGER_LABELS.get(bl.get("hunger_state"), str(bl.get("hunger_state", "?")))

        # Line 2 — vitals + hunger. The "is the player about to die?" row.
        body.append(
            f"HP:{bl.get('hitpoints','?')}({bl.get('max_hitpoints','?')})  "
            f"Pw:{bl.get('energy','?')}({bl.get('max_energy','?')})  "
            f"AC:{bl.get('armor_class','?')}  "
            f"Hunger:{hunger}",
            style="bold",
        )
        body.append("\n")

        # Line 3 — progression + attributes. The "where am I and what am I
        # made of?" row. Strength formats as 18/NN when at the percentile tier.
        str_int = bl.get("strength")
        str_pct = bl.get("strength_pct") or 0
        if str_int == 18 and str_pct:
            str_str = f"18/{int(str_pct):02d}"
        elif str_int is not None:
            str_str = str(str_int)
        else:
            str_str = "?"
        body.append(
            f"Dlvl:{bl.get('depth','?')}  T:{bl.get('time','?')}  "
            f"$:{bl.get('gold','?')}  "
            f"Xp:{bl.get('experience_level','?')}/{bl.get('experience_points','?')}  "
            f"·  St:{str_str} Dx:{bl.get('dexterity','?')} Co:{bl.get('constitution','?')} "
            f"In:{bl.get('intelligence','?')} Wi:{bl.get('wisdom','?')} Ch:{bl.get('charisma','?')}",
            style="bold",
        )
        body.append("\n")

    if msg:
        body.append("msg: ", style="bold dark_orange")
        body.append(msg, style="dark_orange")
    if state.get("terminated") or state.get("truncated"):
        body.append("\n** GAME OVER **", style="bold red")
    if not body.plain:
        body = Text("(waiting for game state…)", style="dim")
    session = state.get("session") or "?"
    return Panel(body, title=f"session={session}", border_style="white", padding=(0, 1))


def _build_legend(state: dict[str, Any]) -> Panel:
    chars = state["chars"]
    descs = state.get("descriptions") or []
    # Post-unification both are 21×79 dungeon-relative — same indexing.
    seen: dict[str, str] = {}
    for r, row in enumerate(chars):
        for c, ch in enumerate(row):
            char = chr(ch) if ch else " "
            if char in LEGEND_SKIP or char in seen:
                continue
            desc = ""
            if r < len(descs) and c < len(descs[r]):
                desc = descs[r][c]
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


def _build_log(
    _traj: list[TrajectoryEvent],
    sess: list[SessionEvent],
    expanded: bool = False,
    scroll: int = 0,
) -> Panel:
    """Render the gamer's session activity, newest-first.

    `expanded`: when True (toggled by Ctrl+O in the TUI), say/thinking events
    keep their original line breaks and don't truncate, and exec blocks show
    every line of code instead of the first 6.

    Newest-first ordering means rich's bottom-cropping (when the panel is
    shorter than content) drops the OLDEST events — latest is always visible.

    Thinking-block text is empty in saved transcripts (Claude Code strips
    plaintext post-v2.1.89) so empty thinking events are dropped.
    """
    KIND_STYLE = {
        "think": ("yellow", "💭"),
        "say":   ("cyan", "💬"),
        "call":  ("bright_blue", "🛠"),
        "msg":   ("dark_orange", "📜"),
    }
    COLLAPSED_CODE_LINES = 6
    COLLAPSED_TEXT_CHARS = 240
    LINE_CAP = 200  # always cap individual code/text lines so one giant line
                    # can't blow up panel layout
    # Apply scroll: skip the first `scroll` newest events, then render up to 40.
    chrono = sess[-300:]
    reverse_chrono = list(reversed(chrono))
    max_scroll = max(0, len(reverse_chrono) - 1)
    scroll = min(scroll, max_scroll)
    visible = reverse_chrono[scroll:scroll + 60]
    body = Text()
    rendered = 0
    for e in visible:
        if e.kind == "thinking" and not e.text:
            continue
        kind = {"thinking": "think", "text": "say", "tool_use": "call", "msg": "msg"}.get(e.kind)
        if kind is None:
            continue
        color, icon = KIND_STYLE[kind]
        body.append(f"{icon} ", style=color)
        if kind in ("think", "say"):
            text = e.text
            if expanded:
                # Preserve newlines; let rich wrap long lines naturally.
                lines = text.splitlines() or [""]
                body.append(f"{lines[0]}\n", style=color)
                for ln in lines[1:]:
                    body.append(f"   {ln}\n", style=color)  # hanging indent under icon
            else:
                flat = text.replace("\n", " ")
                if len(flat) > COLLAPSED_TEXT_CHARS:
                    flat = flat[:COLLAPSED_TEXT_CHARS - 1] + "…"
                body.append(f"{flat}\n", style=color)
        else:  # call
            body.append(f"{e.text}\n", style=color)
            if e.code:
                code_lines = e.code.splitlines()
                shown = code_lines if expanded else code_lines[:COLLAPSED_CODE_LINES]
                for ln in shown:
                    if len(ln) > LINE_CAP:
                        ln = ln[:LINE_CAP - 1] + "…"
                    body.append(f"     │ {ln}\n", style="dim cyan")
                if not expanded and len(code_lines) > COLLAPSED_CODE_LINES:
                    body.append(f"     └ (+{len(code_lines)-COLLAPSED_CODE_LINES} more lines)\n", style="dim")
        rendered += 1
        if rendered >= 40:
            break
    if rendered == 0:
        body = Text("(no activity yet — start a gamer session)", style="dim")
    base = "Recent activity"
    if scroll > 0:
        # Show "scrolled back N of total" with a different border color so it's
        # obvious we're not live anymore.
        title = f"{base} — scrolled back {scroll}/{len(reverse_chrono)} — [↑↓ PgUpDn  g=live G=oldest] [Ctrl+O] {'collapse' if expanded else 'expand'}"
        border = "yellow"
    else:
        title = f"{base} (newest ↑) — [↑↓ PgUpDn] [Ctrl+O] {'collapse' if expanded else 'expand'} — q quit"
        border = "green"
    return Panel(body, title=title, border_style=border, padding=(0, 1))


def _build_layout(state: dict[str, Any] | None,
                  traj: list[TrajectoryEvent],
                  sess: list[SessionEvent],
                  expanded: bool = False,
                  scroll: int = 0) -> Layout:
    layout = Layout(name="root")
    if state is None:
        layout.split_row(
            Layout(_build_log(traj, sess, expanded=expanded, scroll=scroll), name="left"),
            Layout(
                Panel(Text(
                    "Waiting for live state... start a game with ./run.sh in another terminal.",
                    style="dim",
                ), border_style="white"),
                name="right", size=40,
            ),
        )
        return layout

    map_text, map_w, map_h = _build_screen(state)
    map_panel_width = map_w + 4   # +2 borders, +2 padding
    map_panel_height = map_h + 2  # +2 borders

    # Mouse hover → dungeon (row, col), shown in the map panel title.
    # Layout offsets within col 1: header takes 6 rows, then map panel; map
    # content starts at term_row=7 (6 header + 1 top border) and term_col=2
    # (panel left border + 1-col padding). SGR mouse coords are 1-indexed.
    map_title = "NetHack"
    mouse = _UI_STATE.get("mouse_term")
    if mouse:
        mr, mc = mouse
        # 1-indexed terminal coords. Map content occupies term rows 7..7+map_h-1
        # and term cols 2..2+map_w-1 (using 0-indexed internally; mouse is 1-indexed).
        dr = mr - 1 - 7      # to 0-indexed dungeon row
        dc = mc - 1 - 2      # to 0-indexed dungeon col
        if 0 <= dr < map_h and 0 <= dc < map_w:
            map_title = f"NetHack — hover ({dr},{dc})"

    map_panel = Panel(map_text, title=map_title, border_style="white", padding=(0, 1), width=map_panel_width)

    # Three-column layout (no full-width header — header is INSIDE col 1):
    #   col 1: header/stats (top) + map + legend (rest)
    #   col 2: activity log (widest, full height)
    #   col 3: inventory (33 wide)
    layout.split_row(
        Layout(name="col1", size=map_panel_width),
        Layout(name="col2"),  # widest, remaining
        Layout(name="col3", size=33),
    )

    col1 = Layout(name="col1_inner")
    # Header panel = NetHack's 2-row status + msg + game-over flag.
    # Status rows are 2; with title bar + bottom border + msg line that's
    # ~5-6 rows. Size 6 covers it without crowding the map.
    col1.split_column(
        Layout(_build_header(state), name="header", size=7),
        Layout(map_panel, name="map", size=map_panel_height),
        Layout(_build_legend(state), name="legend"),
    )
    layout["col1"].update(col1)

    layout["col2"].update(_build_log(traj, sess, expanded=expanded, scroll=scroll))
    layout["col3"].update(_build_inventory(state))

    return layout


_UI_STATE = {
    "expanded": False,
    "quit": False,
    "scroll": 0,        # how many events scrolled back from newest
    "last_count": 0,    # session event count at last render (for scroll-pinning)
    "mouse_term": None, # (term_row, term_col) of latest mouse position, or None
}

# SGR mouse tracking enable/disable sequences.
# 1003 = report any motion (not just clicks); 1006 = SGR (extended) coord encoding.
_MOUSE_ENABLE = "\x1b[?1003h\x1b[?1006h"
_MOUSE_DISABLE = "\x1b[?1003l\x1b[?1006l"
_DEBUG_LOG = os.environ.get("NETHACK_VIEW_DEBUG")  # path to write key events to


def _dbg(msg: str) -> None:
    if not _DEBUG_LOG:
        return
    try:
        with open(_DEBUG_LOG, "a") as fh:
            fh.write(f"{time.time():.3f}  {msg}\n")
    except OSError:
        pass


def _try_read(fd: int, timeout_s: float = 0.05) -> bytes:
    """Read up to 1 byte with a short timeout (for ESC-sequence assembly)."""
    rlist, _, _ = select.select([fd], [], [], timeout_s)
    if rlist:
        try:
            return os.read(fd, 1)
        except OSError:
            return b""
    return b""


def _key_listener(fd: int) -> None:
    """Background thread: blocking-read keypresses, mutate _UI_STATE.

    Handles single-byte keys (q, Ctrl+O, Ctrl+C, g/G) and CSI escape
    sequences for arrows/PageUp/PageDown/Home/End:
        ESC [ A   = up
        ESC [ B   = down
        ESC [ 5 ~ = PageUp
        ESC [ 6 ~ = PageDown
        ESC [ H   = Home
        ESC [ F   = End
    """
    _dbg(f"key_listener thread started, fd={fd}, isatty={os.isatty(fd)}")
    while not _UI_STATE["quit"]:
        try:
            ch = os.read(fd, 1)
        except OSError as e:
            _dbg(f"OSError on read: {e}")
            return
        if not ch:
            _dbg("got empty bytes (EOF) — thread exiting")
            return
        _dbg(f"got byte: {ch!r}")
        if ch == b"\x1b":
            second = _try_read(fd)
            if second not in (b"[", b"O"):
                continue  # bare ESC or unknown sequence
            third = _try_read(fd)
            # SGR mouse:  ESC [ < button ; col ; row (M|m)
            if second == b"[" and third == b"<":
                buf = b""
                while True:
                    b2 = _try_read(fd, 0.05)
                    if not b2:
                        break
                    buf += b2
                    if b2 in (b"M", b"m"):
                        break
                _dbg(f"  mouse SGR raw: {buf!r}")
                try:
                    parts = buf[:-1].decode("ascii", errors="replace").split(";")
                    if len(parts) == 3:
                        _UI_STATE["mouse_term"] = (int(parts[2]), int(parts[1]))
                        _dbg(f"  → mouse_term={_UI_STATE['mouse_term']}")
                except (ValueError, IndexError) as e:
                    _dbg(f"  mouse parse failed: {e}")
                continue
            if third == b"A":
                _UI_STATE["scroll"] += 1
            elif third == b"B":
                _UI_STATE["scroll"] = max(0, _UI_STATE["scroll"] - 1)
            elif third in (b"5", b"6"):
                _try_read(fd)  # consume trailing '~'
                if third == b"5":
                    _UI_STATE["scroll"] += 10
                else:
                    _UI_STATE["scroll"] = max(0, _UI_STATE["scroll"] - 10)
            elif third == b"H":
                _UI_STATE["scroll"] = 99999  # clamp on render
            elif third == b"F":
                _UI_STATE["scroll"] = 0
            continue
        if ch == b"\x0f":      # Ctrl+O
            _UI_STATE["expanded"] = not _UI_STATE["expanded"]
            _dbg(f"  → toggled expanded to {_UI_STATE['expanded']}")
        elif ch in (b"q", b"\x03"):  # q or Ctrl+C
            _UI_STATE["quit"] = True
            _dbg("  → quit")
            return
        elif ch == b"g":   # less/vim-style: jump to TOP of the visible list
            # Newest is at top in our log (reverse-chrono), so g → live (newest).
            _UI_STATE["scroll"] = 0
        elif ch == b"G":   # less/vim-style: jump to BOTTOM of the visible list
            # Bottom of reverse-chrono = oldest event.
            _UI_STATE["scroll"] = 99999


def _setup_input_thread() -> None:
    """Put stdin in cbreak (plus IEXTEN/IXON cleared) so all keys reach us.

    Plain tty.setcbreak only clears ECHO and ICANON. The terminal driver
    still processes IEXTEN special chars including DISCARD (^O on macOS) —
    that's why Ctrl+O was being silently swallowed before reaching our
    read(). We also clear IXON so ^S/^Q can't accidentally freeze the TUI.
    ISIG stays on so Ctrl+C still raises SIGINT.
    """
    if not sys.stdin.isatty():
        _dbg("stdin not a tty — keyboard disabled")
        return
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    new = termios.tcgetattr(fd)
    new[0] &= ~termios.IXON                                            # iflag
    new[3] &= ~(termios.ECHO | termios.ICANON | termios.IEXTEN)        # lflag
    new[6][termios.VMIN] = 1
    new[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, new)
    atexit.register(lambda: termios.tcsetattr(fd, termios.TCSADRAIN, old))
    _dbg(f"cbreak+IEXTEN/IXON cleared on fd={fd}, spawning thread")
    threading.Thread(target=_key_listener, args=(fd,), daemon=True).start()


def main() -> None:
    console = Console()
    traj_reader = _trajectory_reader()
    sess_reader = _session_reader()
    _setup_input_thread()
    # Belt-and-suspenders for mouse-mode cleanup: atexit covers abrupt
    # exits, the finally covers normal Live shutdown.
    def _disable_mouse() -> None:
        os.write(1, _MOUSE_DISABLE.encode("ascii"))
    atexit.register(_disable_mouse)
    with Live(console=console, screen=True, refresh_per_second=5) as live:
        # Enable SGR mouse-motion reporting *inside* the alt screen so the
        # mode is set on the screen we're actually drawing to. Use os.write
        # against fd 1 directly to avoid any Python stdio buffering or rich
        # console interaction. Mode 1003 = report any-event mouse motion;
        # 1006 = SGR encoding (`ESC [ < button ; col ; row M|m`).
        os.write(1, _MOUSE_ENABLE.encode("ascii"))
        _dbg(f"mouse-enable bytes written: {_MOUSE_ENABLE!r}")
        try:
            while not _UI_STATE["quit"]:
                traj_reader.refresh()
                sess_reader.refresh()
                state = _read_state()
                # Auto-pin: if user is scrolled back and new events arrive,
                # bump scroll so the visible window stays anchored to the same
                # absolute events. Without this, new events would shift their
                # view and "annoy" the user mid-read.
                count = len(sess_reader.events)
                if _UI_STATE["scroll"] > 0 and count > _UI_STATE["last_count"]:
                    _UI_STATE["scroll"] += count - _UI_STATE["last_count"]
                _UI_STATE["last_count"] = count
                live.update(_build_layout(
                    state, traj_reader.events, sess_reader.events,
                    expanded=_UI_STATE["expanded"],
                    scroll=_UI_STATE["scroll"],
                ))
                time.sleep(0.2)
        finally:
            os.write(1, _MOUSE_DISABLE.encode("ascii"))


if __name__ == "__main__":
    main()
