"""Heuristic spots to search for hidden doors/passages.

Standard NetHack player wisdom — no level-generator knowledge needed:
  1. Dead-end corridors — `#` cells with only one walkable neighbor. Almost
     always have a hidden continuation behind the dead wall.
  2. Sealed rooms — `.` floor regions where every visible border cell is a
     wall (`-` or `|`) and no `+` door is anywhere on the border. The door
     is hidden somewhere on the perimeter.

Both heuristics avoid false positives by only flagging when the surrounding
area is *fully revealed* — partial visibility is skipped, not flagged.
"""

from __future__ import annotations

from typing import Any

WALKABLE = set(".#+<>")
WALL = set("-|")


def _ch(chars: list[list[int]], r: int, c: int) -> str:
    if 0 <= r < len(chars) and 0 <= c < len(chars[r]):
        ch_int = chars[r][c]
        return chr(ch_int) if ch_int else " "
    return " "


def _dead_ends(chars: list[list[int]]) -> list[tuple[int, int, str]]:
    """Corridor cells `#` with exactly one walkable neighbor (cardinals)."""
    h = len(chars)
    w = len(chars[0]) if chars else 0
    out: list[tuple[int, int, str]] = []
    # Dungeon rows only — row 0 is message, 22-23 are status.
    for r in range(1, min(22, h)):
        for c in range(w):
            if _ch(chars, r, c) != "#":
                continue
            neighbors = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
            walk_count = sum(1 for nr, nc in neighbors if _ch(chars, nr, nc) in WALKABLE)
            if walk_count == 1:
                # The wall side is the most likely place to search.
                walls = [(nr, nc) for nr, nc in neighbors if _ch(chars, nr, nc) in WALL]
                blanks = [(nr, nc) for nr, nc in neighbors if _ch(chars, nr, nc) == " "]
                hint = ""
                if blanks:
                    hint = f" (extends toward {len(blanks)} blank cell{'s' if len(blanks)>1 else ''})"
                elif walls:
                    hint = " (search the wall side)"
                out.append((r, c, hint))
    return out


def _sealed_rooms(chars: list[list[int]]) -> list[tuple[int, int, int, int, int]]:
    """Connected `.` regions with fully-revealed wall borders and no visible door.

    Returns a list of (r_min, c_min, r_max, c_max, floor_count) for each
    suspect room. Only emitted when every border cell is a wall — partial
    visibility is skipped to avoid noise.
    """
    h = len(chars)
    w = len(chars[0]) if chars else 0
    visited: set[tuple[int, int]] = set()
    rooms: list[tuple[int, int, int, int, int]] = []
    # Dungeon rows only.
    for r in range(1, min(22, h)):
        for c in range(w):
            if (r, c) in visited or _ch(chars, r, c) != ".":
                continue
            region: set[tuple[int, int]] = set()
            border: set[tuple[int, int]] = set()
            stack = [(r, c)]
            while stack:
                pr, pc = stack.pop()
                if (pr, pc) in region:
                    continue
                if _ch(chars, pr, pc) != ".":
                    continue
                region.add((pr, pc))
                visited.add((pr, pc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = pr + dr, pc + dc
                    if not (0 <= nr < h and 0 <= nc < w):
                        continue
                    if _ch(chars, nr, nc) == ".":
                        stack.append((nr, nc))
                    else:
                        border.add((nr, nc))
            if len(region) < 4:
                continue
            border_chars = {_ch(chars, br, bc) for br, bc in border}
            if "+" in border_chars:
                continue  # has a visible door — not sealed
            if border_chars - WALL:
                continue  # any non-wall border (e.g. blank space) means not fully revealed
            rs = [r for r, _ in region]
            cs = [c for _, c in region]
            rooms.append((min(rs), min(cs), max(rs), max(cs), len(region)))
    return rooms


def likely_secret_doors(obs: dict[str, Any]) -> str:
    chars = obs.get("chars") or []
    if not chars:
        return "(likely_secret_doors unavailable: obs has no `chars`; call from inside game.exec)"

    dead_ends = _dead_ends(chars)
    sealed = _sealed_rooms(chars)

    out: list[str] = []
    if dead_ends:
        out.append(f"Dead-end corridors ({len(dead_ends)}) — search at the wall side:")
        for r, c, hint in dead_ends[:8]:
            out.append(f"  ({r:>2},{c:>2}){hint}")
    if sealed:
        out.append("")
        out.append(f"Sealed rooms (fully-walled, no visible door, {len(sealed)}) — search the walls:")
        for r1, c1, r2, c2, area in sealed[:5]:
            out.append(f"  rows {r1}–{r2}, cols {c1}–{c2}, {area} floor cells")
    if not out:
        return "No obvious secret-door candidates visible. Reveal more map first, then re-check."
    return "\n".join(out)
