#!/usr/bin/env python3
"""Extract the fixed special-level maps from NetHack 3.6.7's dat/*.des files.

Writes src/nh/data/desmaps.json:
  {"maps": [{"level", "file", "index", "geometry", "rows", "features": [...]}]}
One entry per MAP ... ENDMAP block (a level can have several: small pieces
placed on a maze, or a variant per file entry). "features" are the statements
after the block that place something at explicit map coordinates (stairs,
ladders, traps, doors, altars, portals, branches, drawbridges, named
monsters); coordinates are relative to the block's top-left corner.
Statements with random or level-absolute coordinates (levregion) are skipped.
Features inside IF/ELSE/SWITCH blocks or behind a "[N%]:" chance carry "cond": true.

"variants": the squares that random TERRAIN statements may change, in groups
that change together (sp_lev.c: one IF branch, one "[N%]:" line; a
REPLACE_TERRAIN below 100% changes each square on its own):
  [{"p": 50, "pair": index-or-null, "cells": [[x, y, "alt char"], ...]}]
"pair" links an IF branch to its ELSE branch (exactly one of them happens).
A REPLACE_TERRAIN below 100% is one entry {"p", "pair": null, "replace":
[x1, y1, x2, y2, from, to]}: each square showing `from` may be `to`.
Unconditional TERRAIN / 100% REPLACE_TERRAIN at explicit coordinates is
applied to "rows" directly. Selections with random parts (randline, grow,
$variables) are skipped.

Usage: scripts/gen_desmaps.py [path/to/nethack-3.6.7/dat]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src" / "nh" / "data" / "desmaps.json"
DEFAULT_DAT = [Path.home() / "src" / "nethack-3.6.7" / "dat",
               Path.home() / ".cache" / "nethack-build" / "NetHack-3.6.7" / "dat"]

_LEVEL = re.compile(r'^\s*(?:MAZE|LEVEL)\s*:\s*"([^"]+)"')
_XY = r"\(\s*(\d+)\s*,\s*(\d+)\s*\)"
_BOX = r"\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)"
_FEATS = [
    ("stair", re.compile(rf"^\s*STAIR\s*:\s*{_XY}\s*,\s*(up|down)")),
    ("ladder", re.compile(rf"^\s*LADDER\s*:\s*{_XY}\s*,\s*(up|down)")),
    ("trap", re.compile(rf'^\s*TRAP\s*:\s*"([^"]+)"\s*,\s*{_XY}')),
    ("door", re.compile(rf"^\s*DOOR\s*:\s*(\w+)\s*,\s*{_XY}")),
    ("altar", re.compile(rf"^\s*ALTAR\s*:\s*{_XY}\s*,\s*(\w+)\s*,\s*(\w+)")),
    ("fountain", re.compile(rf"^\s*FOUNTAIN\s*:\s*{_XY}")),
    ("throne", re.compile(rf"^\s*THRONE\s*:\s*{_XY}")),
    ("sink", re.compile(rf"^\s*SINK\s*:\s*{_XY}")),
    ("drawbridge", re.compile(rf"^\s*DRAWBRIDGE\s*:\s*{_XY}\s*,\s*(\w+)\s*,\s*(\w+)")),
    ("portal", re.compile(rf'^\s*PORTAL\s*:\s*{_BOX}\s*,\s*\([^)]*\)\s*,\s*"([^"]+)"')),
    ("branch", re.compile(rf"^\s*BRANCH\s*:\s*{_BOX}")),
    ("monster", re.compile(rf"^\s*MONSTER\s*:\s*\(\s*'.'\s*,\s*\"([^\"]+)\"\s*\)\s*,\s*{_XY}")),
    ("monster", re.compile(rf"^\s*MONSTER\s*:\s*'(.)'\s*,\s*{_XY}")),        # a random one of that class
]


_PCT = re.compile(r"^\s*\[\s*(\d+)\s*%\s*\]\s*:\s*")
_IF = re.compile(r"^\s*IF\s*\[\s*(\d+)\s*%\s*\]\s*\{\s*$")
_ELSE = re.compile(r"^\s*\}\s*ELSE\s*\{\s*$")
_CH = r"'(.)'"
_TER_PT = re.compile(rf"^\s*TERRAIN\s*:\s*{_XY}\s*,\s*{_CH}\s*$")
_TER_LINE = re.compile(rf"^\s*TERRAIN\s*:\s*line\s*{_XY}\s*,\s*{_XY}\s*,\s*{_CH}\s*$")
_TER_RECT = re.compile(rf"^\s*TERRAIN\s*:\s*(fillrect|rect)\s*{_BOX}\s*,\s*{_CH}\s*$")
_REPLACE = re.compile(rf"^\s*REPLACE_TERRAIN\s*:\s*{_BOX}\s*,\s*{_CH}\s*,\s*{_CH}\s*,\s*(\d+)\s*%\s*$")


def _line_cells(x1, y1, x2, y2) -> list:
    """sp_lev.c selection_do_line(): Bresenham from (x1,y1) to (x2,y2)."""
    cells = []
    dx, dy = abs(x2 - x1), -abs(y2 - y1)
    sx, sy = (1 if x1 < x2 else -1), (1 if y1 < y2 else -1)
    err = dx + dy
    x, y = x1, y1
    while True:
        cells.append((x, y))
        if (x, y) == (x2, y2):
            return cells
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def terrain_cells(stmt: str):
    """(cells, char) of a TERRAIN statement at explicit coordinates, or None (random selection)."""
    m = _TER_PT.match(stmt)
    if m:
        return [(int(m.group(1)), int(m.group(2)))], m.group(3)
    m = _TER_LINE.match(stmt)
    if m:
        return _line_cells(*(int(g) for g in m.groups()[:4])), m.group(5)
    m = _TER_RECT.match(stmt)
    if m:
        x1, y1, x2, y2 = (int(g) for g in m.groups()[1:5])
        cells = [(x, y) for x in range(min(x1, x2), max(x1, x2) + 1) for y in range(min(y1, y2), max(y1, y2) + 1)
                 if m.group(1) == "fillrect" or x in (x1, x2) or y in (y1, y2)]
        return cells, m.group(6)
    return None


def _set_char(rows: list, x: int, y: int, ch: str) -> None:
    if 0 <= y < len(rows) and 0 <= x < len(rows[y]):
        rows[y] = rows[y][:x] + ch + rows[y][x + 1:]


def parse(path: Path) -> list[dict]:
    out: list[dict] = []
    level = None
    geometry = None
    init = False           # the level has INIT_MAP (sp_lev.c splev_init_present: LEFT maps start at x=1)
    count: dict = {}
    cur = None
    blocks: list = []      # open { } blocks: [conditional?, group of this branch, IF chance]
    lines = path.read_text(errors="replace").splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i]
        m = _LEVEL.match(ln)
        if m:
            level, geometry, cur, init, blocks = m.group(1), None, None, False, []
            i += 1
            continue
        code = "" if ln.lstrip().startswith("#") else ln       # (no .des file has inline comments)
        if _ELSE.match(code):
            prev = blocks.pop() if blocks else [True, None, 50]
            blocks.append([True, {"else_of": prev[1]}, 100 - prev[2]])
            i += 1
            continue
        if "{" in code and "}" not in code:
            mi = _IF.match(code)
            kind = code.strip().split()[0].upper() if code.strip() else ""
            cond = bool(mi) or kind.startswith(("IF", "SWITCH")) or bool(_PCT.match(code))
            blocks.append([cond, {} if cond else None, int(mi.group(1)) if mi else 50])
            i += 1
            continue
        if code.strip() == "}" or (code.strip().startswith("}") and "{" not in code):
            if blocks:
                blocks.pop()
            i += 1
            continue
        if code.strip().upper().startswith("CASE"):
            if blocks:
                blocks[-1][1] = {}          # each CASE of a SWITCH is its own branch
            i += 1
            continue
        if ln.strip().startswith("INIT_MAP"):
            init = True
        if ln.strip().startswith("GEOMETRY:"):
            geometry = ln.split(":", 1)[1].strip()
        if ln.strip() == "MAP" and level is not None:
            rows = []
            i += 1
            while i < len(lines) and lines[i].strip() != "ENDMAP":
                rows.append(lines[i].rstrip("\n"))
                i += 1
            k = count.get(level, 0)
            count[level] = k + 1
            cur = {"level": level, "file": path.name, "index": k, "geometry": geometry, "init": init, "rows": rows,
                   "features": [], "variants": []}
            out.append(cur)
            geometry = None
            i += 1
            continue
        if cur is not None and not ln.lstrip().startswith("#"):
            pm = _PCT.match(code)
            stmt = code[pm.end():] if pm else code
            cond_blk = next((b for b in reversed(blocks) if b[0]), None)
            cond = pm is not None or cond_blk is not None
            _terrain(cur, stmt, cond, pm, cond_blk)
            n_feat = len(cur["features"])
            for kind, rx in _FEATS:
                fm = rx.search(stmt)
                if not fm:
                    continue
                g = fm.groups()
                if kind in ("stair", "ladder"):
                    cur["features"].append({"kind": kind, "x": int(g[0]), "y": int(g[1]), "detail": g[2]})
                elif kind == "trap":
                    cur["features"].append({"kind": kind, "x": int(g[1]), "y": int(g[2]), "detail": g[0]})
                elif kind == "door":
                    cur["features"].append({"kind": kind, "x": int(g[1]), "y": int(g[2]), "detail": g[0]})
                elif kind == "altar":
                    cur["features"].append({"kind": kind, "x": int(g[0]), "y": int(g[1]),
                                            "detail": f"{g[2]} {g[3]}"})
                elif kind in ("fountain", "throne", "sink"):
                    cur["features"].append({"kind": kind, "x": int(g[0]), "y": int(g[1]), "detail": ""})
                elif kind == "drawbridge":
                    cur["features"].append({"kind": kind, "x": int(g[0]), "y": int(g[1]),
                                            "detail": f"{g[2]} {g[3]}"})
                elif kind == "portal":
                    cur["features"].append({"kind": kind, "x": int(g[0]), "y": int(g[1]), "detail": g[4]})
                elif kind == "branch":
                    cur["features"].append({"kind": kind, "x": int(g[0]), "y": int(g[1]), "detail": ""})
                elif kind == "monster":
                    detail = g[0] if len(g[0]) > 1 else f"a random '{g[0]}' (class)"
                    cur["features"].append({"kind": kind, "x": int(g[1]), "y": int(g[2]), "detail": detail})
                break
            if cond:
                for ft in cur["features"][n_feat:]:
                    ft["cond"] = True
        i += 1
    for m in out:
        for k, g in enumerate(m["variants"]):
            g.pop("_id", None)
        if not m["variants"]:
            m.pop("variants")
    return out


def _group(cur: dict, blk, p: int) -> dict:
    """The variant group of this IF/ELSE/CASE branch (made on its first TERRAIN), linked to its pair."""
    ref = blk[1]
    if ref.get("_group") is None:
        g = {"p": p, "pair": None, "cells": [], "_id": len(cur["variants"])}
        cur["variants"].append(g)
        ref["_group"] = g
        other = (ref.get("else_of") or {}).get("_group")
        if other is not None and other in cur["variants"]:
            g["pair"] = cur["variants"].index(other)
            other["pair"] = g["_id"]
    return ref["_group"]


def _terrain(cur: dict, stmt: str, cond: bool, pm, blk) -> None:
    """Apply an unconditional TERRAIN/REPLACE_TERRAIN at explicit coordinates to the rows, or record a
    conditional one as a variant group."""
    tc = terrain_cells(stmt)
    rm = _REPLACE.match(stmt)
    if tc is None and rm is None:
        return
    rows = cur["rows"]
    if tc is not None:
        cells, ch = tc
        if not cond:
            for x, y in cells:
                _set_char(rows, x, y, ch)
            return
        if pm is not None:
            g = {"p": int(pm.group(1)), "pair": None, "cells": []}
            cur["variants"].append(g)
        else:
            g = _group(cur, blk, blk[2])
        g["cells"].extend([x, y, ch] for x, y in cells if 0 <= y < len(rows) and 0 <= x < len(rows[y]))
        return
    x1, y1, x2, y2 = (int(v) for v in rm.groups()[:4])
    src, dst, pct = rm.group(5), rm.group(6), int(rm.group(7))
    cells = [(x, y) for y in range(min(y1, y2), max(y1, y2) + 1) for x in range(min(x1, x2), max(x1, x2) + 1)
             if 0 <= y < len(rows) and 0 <= x < len(rows[y]) and rows[y][x] == src]
    if pct >= 100 and not cond:
        for x, y in cells:
            _set_char(rows, x, y, dst)
        return
    if cells:
        # each square on its own (sp_lev.c spo_replace_terrain: rn2(100) per square): one compact entry,
        # expanded by desmap.maps() into a group per square
        cur["variants"].append({"p": pct, "pair": None, "replace": [x1, y1, x2, y2, src, dst]})


def main() -> None:
    dat = Path(sys.argv[1]) if len(sys.argv) > 1 else next((d for d in DEFAULT_DAT if d.is_dir()), None)
    if dat is None or not dat.is_dir():
        sys.exit("gen_desmaps: give the path to nethack-3.6.7/dat")
    maps = []
    for f in sorted(dat.glob("*.des")):
        maps += parse(f)
    OUT.write_text(json.dumps({"source": "NetHack 3.6.7 dat/*.des", "maps": maps}, indent=0))
    print(f"wrote {OUT} ({len(maps)} maps from {len(list(dat.glob('*.des')))} files)")


if __name__ == "__main__":
    main()
