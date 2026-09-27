#!/usr/bin/env python3
"""Build machine-checked Sokoban solutions for NetHack 3.6.7.

Sources:
- the exact level maps, boulders and traps from NetHack's dat/sokoban.des
  (default: /root/src/nethack-3.6.7/dat/sokoban.des or $NH_SRC/dat/...)
- the move lists from the offline wiki pages knowledge/wiki/Sokoban_Level_*.txt
  (boulders named by letters on the wiki's first lettered diagram).

Every solution is replayed in a simulator of the 3.6 Sokoban rules
(orthogonal pushes only; a boulder pushed into a pit/hole fills it; the hero
can't enter pits/holes or squeeze diagonally between two boulders/walls) and
must end with a trap-free path from the arrival stairs to the exit stairs.
Output: play/tactics/sokoban_data.py (plain Python literals).

Usage: scripts/gen_sokoban.py [--des PATH] [--check-only]
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import deque
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WIKI = REPO / "knowledge" / "wiki"
DIRS = {"u": (0, -1), "d": (0, 1), "l": (-1, 0), "r": (1, 0)}

# Wiki typos found by the simulator: (page, step index) -> corrected moves.
CORRECTIONS = {
    # 2a: "L lllr rrrr rruu rdrr rrrr*" is one 'r' short: P just filled the hole at
    # x=16 along the same path, L must fill x=17 (and the next step, I, fills x=18).
    ("Sokoban_Level_2a", 17): "lllrrrrrrruurdrrrrrrr*",
}
# Pages whose move list ends with alternatives: keep only the first N steps.
# 2a: after the main solution, "If you start from < or @: A r" (kept: the
# solution ends next to the holes) / "If you start from >: C d, F l" (dropped).
KEEP_STEPS = {"Sokoban_Level_2a": 29}


def load_des(path: Path) -> dict:
    src = path.read_text()
    out = {}
    for lv in re.split(r"\nMAZE:", src)[1:]:
        name = re.match(r'"([^"]+)"', lv).group(1)
        rows = re.search(r"\nMAP\n(.*?)\nENDMAP", lv, re.S).group(1).split("\n")
        w = max(len(r) for r in rows)
        rows = [r.ljust(w) for r in rows]
        boulders = [(int(x), int(y)) for x, y in re.findall(r'OBJECT:\(\'`\',"boulder"\),\((\d+),(\d+)\)', lv)]
        traps = [(int(x), int(y)) for _t, x, y in re.findall(r'TRAP:"(pit|hole)",\((\d+),(\d+)\)', lv)]
        stairs = {d: (int(x), int(y)) for x, y, d in re.findall(r'STAIR:\((\d+),(\d+)\),(up|down)', lv)}
        br = re.findall(r'BRANCH:\((\d+),(\d+)', lv)
        start = (int(br[0][0]), int(br[0][1])) if br else stairs["down"]
        if "up" in stairs:
            exit_ = stairs["up"]
        else:   # top level: the goal is the treasure zoo's door beyond the holes (the rightmost door)
            doors = [(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c == "+"]
            exit_ = max(doors)
        out[name] = {"rows": rows, "boulders": boulders, "traps": traps, "start": start, "exit": exit_}
    return out


# ---------------------------------------------------------------- simulator

class Board:
    def __init__(self, lv: dict):
        self.rows = lv["rows"]
        self.boulders = set(lv["boulders"])
        self.traps = set(lv["traps"])
        self.hero = lv["start"]

    def wall(self, x, y) -> bool:
        if not (0 <= y < len(self.rows) and 0 <= x < len(self.rows[y])):
            return True
        return self.rows[y][x] in " |-+"          # doors never matter for the puzzle part

    def solid(self, x, y) -> bool:
        return self.wall(x, y) or (x, y) in self.boulders

    def walkable(self, x, y) -> bool:
        if 0 <= y < len(self.rows) and 0 <= x < len(self.rows[y]) and self.rows[y][x] == "+":
            return True        # doors (closed, but the hero can open them) — only used as goals
        return not self.solid(x, y) and (x, y) not in self.traps

    def path(self, a, b):
        if a == b:
            return []
        prev = {a: None}
        q = deque([a])
        while q:
            cx, cy = q.popleft()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if not (dx or dy):
                        continue
                    nx, ny = cx + dx, cy + dy
                    if (nx, ny) in prev or not self.walkable(nx, ny):
                        continue
                    if dx and dy and self.solid(cx + dx, cy) and self.solid(cx, cy + dy):
                        continue       # no diagonal squeeze in Sokoban
                    prev[(nx, ny)] = (cx, cy)
                    if (nx, ny) == b:
                        p = [(nx, ny)]
                        while prev[p[-1]] != a:
                            p.append(prev[p[-1]])
                        return list(reversed(p))
                    q.append((nx, ny))
        return None

    def push(self, b, d) -> tuple:
        """Push boulder b one step in direction d. Returns the new position
        (None if it filled a trap). Raises ValueError if illegal."""
        if b not in self.boulders:
            raise ValueError(f"no boulder at {b}")
        dx, dy = DIRS[d]
        behind = (b[0] - dx, b[1] - dy)
        dest = (b[0] + dx, b[1] + dy)
        if self.path(self.hero, behind) is None:
            raise ValueError(f"hero at {self.hero} can't reach {behind} to push {b} {d}")
        if self.solid(*dest):
            raise ValueError(f"{b} can't move {d}: {dest} is blocked")
        self.boulders.discard(b)
        self.hero = b
        if dest in self.traps:
            self.traps.discard(dest)
            return None
        self.boulders.add(dest)
        return dest


# ---------------------------------------------------------------- wiki parsing

def _diagrams(text: str, h: int) -> list[list[str]]:
    """Blocks of >= h consecutive lines that look like map rows."""
    lines = text.split("\n")
    out, i = [], 0
    looks = re.compile(r"^\s*[-|]")
    while i < len(lines):
        if looks.match(lines[i]):
            j = i
            while j < len(lines) and looks.match(lines[j]):
                j += 1
            if j - i >= h - 2:
                out.append(lines[i:j])
            i = j
        else:
            i += 1
    return out


def _align(diag: list[str], lv: dict):
    """Map each diagram row onto the .des map. Returns {letter: (x, y)} for
    letters standing on .des boulder squares, or None if it doesn't fit."""
    rows = lv["rows"]
    boulders = set(lv["boulders"])
    letters = {}
    if len(diag) < len(rows) - 1:
        return None
    for y, want in enumerate(rows):
        if y >= len(diag):
            break
        line = diag[y]
        best = None
        for shift in range(-2, 3):
            ok = 0
            bad = 0
            for x, wc in enumerate(want):
                i = x + shift
                c = line[i] if 0 <= i < len(line) else " "
                if wc in "|-":
                    ok, bad = (ok + 1, bad) if c in "|-" else (ok, bad + 1)
            if best is None or bad < best[1] or (bad == best[1] and ok > best[0]):
                best = (ok, bad, shift)
        ok, bad, shift = best
        if bad > 1:
            return None
        for x, wc in enumerate(want):
            i = x + shift
            c = line[i] if 0 <= i < len(line) else " "
            if c.isalpha() and c.isupper() and (x, y) in boulders:
                letters[c] = (x, y)
    return letters


def _moves(text: str) -> list[tuple[str, str]]:
    """'X ddrr uu*' steps anywhere in the text (own lines or legends at the
    right of diagram rows), in reading order."""
    steps = []
    rx = re.compile(r"(?:^|\s)([A-Z]) ((?:[udlr]+\*?)(?: [udlr]+\*?)*)\s*$")
    for line in text.split("\n"):
        m = rx.search(line)
        if m:
            steps.append((m.group(1), m.group(2).replace(" ", "")))
    return steps


def build(lv_name: str, lv: dict, page: Path) -> dict:
    text = page.read_text()
    strat = text.split("All boulders are replaced by letters", 1)
    if len(strat) < 2:
        raise ValueError(f"{page.name}: no lettered solution")
    body = strat[1].split("## Next level")[0]
    diags = _diagrams(body, len(lv["rows"]))
    letters = None
    for d in diags:
        letters = _align(d, lv)
        if letters and len(letters) >= len(lv["boulders"]) - 2:
            break
    if not letters:
        raise ValueError(f"{page.name}: couldn't align the lettered diagram")
    steps = _moves(body)
    steps = [(l, CORRECTIONS.get((page.stem, n), mv)) for n, (l, mv) in enumerate(steps)]
    if page.stem in KEEP_STEPS:
        steps = steps[:KEEP_STEPS[page.stem]]
    board = Board(lv)
    pos = dict(letters)
    out_steps = []
    for n, (letter, mv) in enumerate(steps):
        if letter not in pos or pos[letter] is None:
            raise ValueError(f"{page.name} step {n} {letter} {mv}: boulder {letter} unknown/gone")
        start = pos[letter]
        seq = mv.rstrip("*")
        cur = start
        for d in seq:
            try:
                cur = board.push(cur, d)
            except ValueError as e:
                raise ValueError(f"{page.name} step {n} ({letter} {mv}): {e}") from None
            if cur is None:
                break
        if mv.endswith("*") and cur is not None:
            raise ValueError(f"{page.name} step {n} ({letter} {mv}): expected to fill a trap, boulder at {cur}")
        pos[letter] = cur
        out_steps.append({"boulder": letter, "at": start, "moves": seq, "fills": cur is None, "to": cur,
                          "after": {"boulders": sorted(board.boulders), "traps": sorted(board.traps)}})
    if board.path(board.hero, lv["exit"]) is None:
        raise ValueError(f"{page.name}: after the solution the exit {lv['exit']} is still unreachable; "
                         f"traps left {sorted(board.traps)}")
    return {"level": lv_name, "wiki": page.stem, "rows": lv["rows"], "start": lv["start"], "exit": lv["exit"],
            "boulders": lv["boulders"], "traps": lv["traps"], "letters": letters, "steps": out_steps}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--des", default=os.path.join(os.environ.get("NH_SRC", "/root/src/nethack-3.6.7"),
                                                  "dat", "sokoban.des"))
    ap.add_argument("--check-only", action="store_true")
    a = ap.parse_args()
    levels = load_des(Path(a.des))
    pages = sorted(WIKI.glob("Sokoban_Level_*.txt"))
    results, failures = {}, []
    for lv_name, lv in levels.items():
        matched = None
        for page in pages:
            head = page.read_text().split("## Strategy")[0]
            # the page's first map must contain every .des wall row (ignoring alignment)
            if all(r.strip().replace("0", ".").replace("^", ".") and
                   _stripped(r) in _stripped_page(head) for r in lv["rows"] if r.strip()):
                matched = page
                break
        if matched is None:
            failures.append(f"{lv_name}: no wiki page matches")
            continue
        try:
            results[lv_name] = build(lv_name, lv, matched)
            print(f"{lv_name} = {matched.stem}: {len(results[lv_name]['steps'])} steps OK")
        except ValueError as e:
            failures.append(str(e))
            print(f"{lv_name} = {matched.stem}: FAILED: {e}")
    if failures:
        print("\n".join(["", "FAILURES:"] + failures))
    if not a.check_only and results:
        out = REPO / "play" / "tactics" / "sokoban_data.py"
        with open(out, "w") as f:
            f.write('"""Generated by scripts/gen_sokoban.py from NetHack 3.6.7 dat/sokoban.des and the\n'
                    'NetHackWiki solutions (CC BY-SA). Map coordinates are (x, y) within each level map;\n'
                    'every solution was replayed in a simulator of the Sokoban rules. Do not edit."""\n\n')
            f.write(f"LEVELS = {results!r}\n")
        print(f"wrote {out}")
    return 1 if failures else 0


def _walls(s: str) -> str:
    """Wall/non-wall shape: NetHack draws wall junctions from the .des '|'
    as '-' (and vice versa), so only 'is it a wall' is comparable."""
    return re.sub(r"[^#]", ".", re.sub(r"[|\-]", "#", s))


def _stripped(row: str) -> str:
    return _walls(row.strip())


def _stripped_page(text: str) -> str:
    return "\n".join(_walls(l.strip()) for l in text.split("\n"))


if __name__ == "__main__":
    sys.exit(main())
