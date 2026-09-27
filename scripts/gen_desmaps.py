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


def parse(path: Path) -> list[dict]:
    out: list[dict] = []
    level = None
    geometry = None
    init = False           # the level has INIT_MAP (sp_lev.c splev_init_present: LEFT maps start at x=1)
    count: dict = {}
    cur = None
    lines = path.read_text(errors="replace").splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i]
        m = _LEVEL.match(ln)
        if m:
            level, geometry, cur, init = m.group(1), None, None, False
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
                   "features": []}
            out.append(cur)
            geometry = None
            i += 1
            continue
        if cur is not None and not ln.lstrip().startswith("#"):
            for kind, rx in _FEATS:
                fm = rx.search(ln)
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
        i += 1
    return out


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
