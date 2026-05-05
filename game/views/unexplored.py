"""Frontier cells: walkable squares adjacent to unseen space."""

from __future__ import annotations

from typing import Any

WALKABLE = set(".#+<>")  # floor, corridor, door, stairs
BLANK_CHARS = {0, 0x20}  # NUL or space → unseen


def _at(chars: list[list[int]], r: int, c: int) -> int | None:
    if 0 <= r < len(chars) and 0 <= c < len(chars[r]):
        return chars[r][c]
    return None


def _is_blank(ch_int: int | None) -> bool:
    return ch_int is None or ch_int in BLANK_CHARS


def _bearing(pr: int, pc: int, r: int, c: int) -> str:
    dr, dc = r - pr, c - pc
    parts = []
    if dr < 0: parts.append(f"{-dr}N")
    elif dr > 0: parts.append(f"{dr}S")
    if dc < 0: parts.append(f"{-dc}W")
    elif dc > 0: parts.append(f"{dc}E")
    return "+".join(parts) if parts else "here"


def unexplored(obs: dict[str, Any], max_results: int = 12) -> str:
    """List explored walkable cells with at least one unseen 4-neighbor.

    These are the boundary between known map and the dark — walking onto a
    frontier and stepping further reveals new territory. Sorted by Chebyshev
    distance from the player (i.e. NetHack movement cost), closest first.
    """
    chars = obs.get("chars") or []
    if not chars:
        return "(unexplored unavailable: obs has no `chars`; call from inside game.exec)"

    cursor = obs.get("cursor") or [0, 0]
    pr, pc = int(cursor[0]), int(cursor[1])
    h = len(chars)
    w = len(chars[0]) if chars else 0

    frontiers: list[tuple[int, int, int, str]] = []
    for r in range(h):
        for c in range(w):
            ch_int = chars[r][c]
            ch = chr(ch_int) if ch_int else " "
            if ch not in WALKABLE:
                continue
            if any(_is_blank(_at(chars, r + dr, c + dc))
                   for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))):
                d = max(abs(r - pr), abs(c - pc))  # Chebyshev = NetHack moves
                frontiers.append((d, r, c, ch))

    if not frontiers:
        return "No frontier cells visible — current view is fully explored."

    frontiers.sort()
    out = [f"Frontier cells: {len(frontiers)} total ({frontiers[0][0]} steps to nearest). Showing top {min(max_results, len(frontiers))}:"]
    for d, r, c, ch in frontiers[:max_results]:
        out.append(f"  d={d:>2}  ({r:>2},{c:>2})  '{ch}'  {_bearing(pr, pc, r, c)}")
    return "\n".join(out)
