"""Screen model: a captured terminal frame (chars + colors + attributes + cursor).

Colors use NetHack's numbering, which matches ANSI order:
  0 black  1 red  2 green  3 brown  4 blue  5 magenta  6 cyan  7 gray
  8 no-color/dark gray  9 orange  10 bright green  11 yellow  12 bright blue
  13 bright magenta  14 bright cyan  15 white
tty NetHack draws bright colors as bold + base color, so nh_color = base + 8*bold.
Default foreground (no SGR color) is reported as 7 (gray).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

COLOR_NAMES = [
    "black", "red", "green", "brown", "blue", "magenta", "cyan", "gray",
    "dark gray", "orange", "bright green", "yellow", "bright blue",
    "bright magenta", "bright cyan", "white",
]

_CSI = re.compile(r"\x1b\[([0-9;:?]*)([A-Za-z])")
_OSC = re.compile(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")


@dataclass
class Screen:
    width: int
    height: int
    chars: list[str]                 # height strings of exactly `width` chars
    fg: list[list[int]]              # NetHack color per cell (0..15)
    reverse: list[list[bool]]        # inverse video (pets, piles with hilite_*)
    bold: list[list[bool]]
    cursor: tuple[int, int]          # (x, y) = (col, row)
    dead: bool = False               # the pane's process exited
    t: float = 0.0                   # capture time (time.time())

    def __repr__(self) -> str:
        return f"<Screen {self.width}x{self.height} cursor={self.cursor}{' DEAD' if self.dead else ''}>"

    def dump(self) -> str:
        """The screen as text with row numbers (for printing)."""
        return "\n".join(f"{y:>2}|{r.rstrip()}" for y, r in enumerate(self.chars))

    # ---- basic accessors -------------------------------------------------
    def row(self, y: int) -> str:
        return self.chars[y] if 0 <= y < self.height else ""

    def at(self, x: int, y: int) -> str:
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.chars[y][x]
        return " "

    def color_at(self, x: int, y: int) -> int:
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.fg[y][x]
        return 7

    def reverse_at(self, x: int, y: int) -> bool:
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.reverse[y][x]
        return False

    @property
    def text(self) -> str:
        return "\n".join(r.rstrip() for r in self.chars)

    def same_as(self, other: "Screen | None") -> bool:
        return (other is not None and self.chars == other.chars
                and self.cursor == other.cursor and self.fg == other.fg)

    def find(self, needle: str) -> list[tuple[int, int]]:
        hits = []
        for y, r in enumerate(self.chars):
            start = 0
            while True:
                i = r.find(needle, start)
                if i < 0:
                    break
                hits.append((i, y))
                start = i + 1
        return hits


def _new_grid(w: int, h: int, v):
    return [[v] * w for _ in range(h)]


def parse_capture(raw: str, width: int, height: int, cursor: tuple[int, int],
                  dead: bool = False, t: float = 0.0) -> Screen:
    """Parse `tmux capture-pane -p -e` output (SGR-annotated lines)."""
    raw = _OSC.sub("", raw)
    lines = raw.split("\n")
    chars = [[" "] * width for _ in range(height)]
    fg = _new_grid(width, height, 7)
    rev = _new_grid(width, height, False)
    bold = _new_grid(width, height, False)
    # tmux carries SGR state across lines in capture output only if it emits
    # it again; we reset at each line start (tmux re-emits attributes per line).
    cur_fg = None
    cur_bold = False
    cur_rev = False
    for y in range(min(height, len(lines))):
        line = lines[y]
        x = 0
        i = 0
        n = len(line)
        while i < n and x < width:
            c = line[i]
            if c == "\x1b":
                m = _CSI.match(line, i)
                if m:
                    params, final = m.group(1), m.group(2)
                    if final == "m":
                        cur_fg, cur_bold, cur_rev = _apply_sgr(params, cur_fg, cur_bold, cur_rev)
                    i = m.end()
                    continue
                i += 1
                continue
            if c in "\r":
                i += 1
                continue
            if c == "\t":
                nx = min(width, (x // 8 + 1) * 8)
                x = nx
                i += 1
                continue
            chars[y][x] = c if c.isprintable() else " "
            base = 7 if cur_fg is None else cur_fg
            if base < 8 and cur_bold and cur_fg is not None:
                base += 8
            elif base == 0 and cur_bold:
                base = 8
            fg[y][x] = base
            bold[y][x] = cur_bold
            rev[y][x] = cur_rev
            x += 1
            i += 1
    return Screen(width=width, height=height, chars=["".join(r) for r in chars],
                  fg=fg, reverse=rev, bold=bold, cursor=cursor, dead=dead, t=t)


def _apply_sgr(params: str, fgc, bold, rev):
    if params == "":
        return None, False, False
    parts = [p for p in re.split(r"[;:]", params)]
    i = 0
    while i < len(parts):
        p = parts[i]
        try:
            v = int(p) if p != "" else 0
        except ValueError:
            i += 1
            continue
        if v == 0:
            fgc, bold, rev = None, False, False
        elif v == 1:
            bold = True
        elif v in (2, 22):
            bold = False
        elif v == 7:
            rev = True
        elif v == 27:
            rev = False
        elif 30 <= v <= 37:
            fgc = v - 30
        elif v == 39:
            fgc = None
        elif 90 <= v <= 97:
            fgc = v - 90 + 8
        elif v == 38:
            # 38;5;N or 38;2;r;g;b
            if i + 1 < len(parts) and parts[i + 1] == "5" and i + 2 < len(parts):
                try:
                    n = int(parts[i + 2])
                except ValueError:
                    n = 7
                fgc = n if n < 16 else 7
                i += 2
            elif i + 1 < len(parts) and parts[i + 1] == "2":
                i += 4
                fgc = 7
        elif v == 48:
            if i + 1 < len(parts) and parts[i + 1] == "5":
                i += 2
            elif i + 1 < len(parts) and parts[i + 1] == "2":
                i += 4
        # ignore other attributes (underline, blink, bg colors)
        i += 1
    return fgc, bold, rev
