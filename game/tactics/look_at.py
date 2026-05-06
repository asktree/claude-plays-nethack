"""look_at(row, col) and look_at_nearest(symbol, index): use NetHack's
Command.GLANCE (`;`) to identify what's at a cell.

GLANCE prints a description in the message, e.g. "kobold; a small humanoid"
or "(a fountain)". Useful when a glyph is ambiguous from chars alone.

Same multi-keystroke pattern as travel_to: press `;`, move the cursor to
the target with cardinal directions, press `.` to confirm.
"""

from __future__ import annotations

import sys
from typing import Any


def _resolve_kernel():
    frame = sys._getframe(2).f_globals
    do = frame.get("do")
    observe = frame.get("observe")
    if do is None or observe is None:
        raise RuntimeError("must be called inside game.exec(); needs `do` and `observe`")
    return do, observe


def _move_cursor_to(do, dy: int, dx: int) -> None:
    for _ in range(abs(dy)):
        do("south" if dy > 0 else "north")
    for _ in range(abs(dx)):
        do("east" if dx > 0 else "west")


def look_at(row: int, col: int, *, do=None, observe=None) -> dict[str, Any]:
    """Glance at a cell — returns the post-glance snapshot whose `message`
    is NetHack's description of what's there.

    Inside game.exec():
        from tactics import look_at
        snap = look_at(12, 34)
        print(snap["message"])   # e.g. "(a fountain)" or "kobold; ..."
    """
    if do is None or observe is None:
        do, observe = _resolve_kernel()
    obs = observe()
    cursor = obs.get("cursor") or [0, 0]
    cy, cx = int(cursor[0]), int(cursor[1])

    do("Command.GLANCE")
    _move_cursor_to(do, row - cy, col - cx)
    return do("MiscDirection.WAIT")  # `.` confirms the glance target


def look_at_nearest(symbol: str, index: int = 0, *, do=None, observe=None) -> dict[str, Any]:
    """Find the nth-nearest occurrence of `symbol` in view, then look_at it.

    `index=0` (default) is the nearest, 1 is the 2nd-nearest, etc. Distance
    is Chebyshev (the NetHack movement cost). Searches the dungeon area
    only (rows 1..21).

    Raises ValueError if there are fewer than index+1 matches.
    """
    if do is None or observe is None:
        do, observe = _resolve_kernel()
    obs = observe()
    chars = obs.get("chars") or []
    if not chars:
        raise RuntimeError("no chars in obs; ensure called inside game.exec()")
    cursor = obs.get("cursor") or [0, 0]
    py, px = int(cursor[0]), int(cursor[1])

    matches: list[tuple[int, int, int]] = []
    for r in range(len(chars)):
        for c, ch_int in enumerate(chars[r]):
            ch = chr(ch_int) if ch_int else " "
            if ch == symbol:
                d = max(abs(r - py), abs(c - px))
                matches.append((d, r, c))
    matches.sort()
    if index >= len(matches):
        raise ValueError(
            f"only {len(matches)} occurrence(s) of {symbol!r} in view; "
            f"requested index {index}"
        )
    _, r, c = matches[index]
    return look_at(r, c, do=do, observe=observe)
