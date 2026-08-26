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
    """List explored walkable cells worth exploring further.

    Frontiers come in two flavors:
      1. Walkable cells with at least one unseen 4-neighbor — the boundary
         between known and unknown.
      2. Closed `+` doors regardless of neighbor seen-status — even if the
         door cell itself is "seen", what's beyond is gated until you walk
         through. Always worth a visit.

    Sorted by Chebyshev distance (NetHack movement cost), closest first.
    """
    chars = obs.get("chars") or []
    if not chars:
        return "(unexplored unavailable: obs has no `chars`; call from inside game.exec)"

    cursor = obs.get("cursor") or [0, 0]
    pr, pc = int(cursor[0]), int(cursor[1])
    h = len(chars)
    w = len(chars[0]) if chars else 0

    seen = obs.get("seen") or []
    desc = obs.get("descriptions")
    frontiers: list[tuple[int, int, int, str]] = []
    for r in range(h):
        for c in range(w):
            ch_int = chars[r][c]
            ch = chr(ch_int) if ch_int else " "
            if ch not in WALKABLE:
                # open doors render as | or - (same as walls); trust the
                # per-cell description so the corridor beyond a door counts
                d = (desc[r][c] if desc and r < len(desc) and c < len(desc[r]) else "") or ""
                if "door" not in d.lower() or "closed" in d.lower():
                    continue
            is_frontier = False
            # Rule 2: closed doors are always frontiers.
            if ch == "+":
                is_frontier = True
            # Rule 1: walkable cells adjacent to unseen.
            else:
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < h and 0 <= nc < w):
                        continue
                    if seen and 0 <= nr < len(seen) and 0 <= nc < len(seen[nr]):
                        if not seen[nr][nc]:
                            is_frontier = True
                            break
                    else:
                        if _is_blank(_at(chars, nr, nc)):
                            is_frontier = True
                            break
            if is_frontier:
                d = max(abs(r - pr), abs(c - pc))  # Chebyshev = NetHack moves
                frontiers.append((d, r, c, ch))

    if not frontiers:
        return "No frontier cells visible — current view is fully explored."

    frontiers.sort()
    out = [f"Frontier cells: {len(frontiers)} total ({frontiers[0][0]} steps to nearest). Showing top {min(max_results, len(frontiers))}:"]
    for d, r, c, ch in frontiers[:max_results]:
        out.append(f"  d={d:>2}  ({r:>2},{c:>2})  '{ch}'  {_bearing(pr, pc, r, c)}")
    return "\n".join(out)
