"""Centered ASCII crop around the player @."""

from __future__ import annotations

from typing import Any


def crop(obs: dict[str, Any], radius: int = 4) -> str:
    """Return a (2r+1) x (2r+1) ASCII window centered on the player.

    Uses `obs["cursor"]` (the rendered tty cursor, **[row, col]** — NLE order)
    for centering and `obs["chars"]` (24x80 grid) for cell glyphs. The grid
    lives in the observation when game.exec() built it with include_grid=True
    (always true inside exec).

    Cells outside the grid are rendered as spaces, so the result is always a
    perfect square — easy to reason about distances and adjacency.
    """
    cursor = obs.get("cursor") or [0, 0]
    cy, cx = int(cursor[0]), int(cursor[1])  # NLE returns [row, col]
    chars: list[list[int]] = obs.get("chars") or []
    if not chars:
        return "(crop unavailable: obs has no `chars`; call from inside game.exec)"

    h = len(chars)
    w = len(chars[0]) if chars else 0
    rows: list[str] = []
    for dy in range(-radius, radius + 1):
        y = cy + dy
        line = []
        for dx in range(-radius, radius + 1):
            x = cx + dx
            if 0 <= y < h and 0 <= x < w:
                ch = chars[y][x]
                line.append(chr(ch) if ch else " ")
            else:
                line.append(" ")
        rows.append("".join(line))
    return "\n".join(rows)
