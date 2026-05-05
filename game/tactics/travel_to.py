"""travel_to(row, col): use NetHack's Command.TRAVEL to auto-path to a cell."""

from __future__ import annotations

from typing import Any


def travel_to(row: int, col: int, *, observe=None, do=None) -> dict[str, Any]:
    """Auto-path to the given tty (row, col) via NetHack's Travel command.

    Travel is NetHack's built-in pathfinder: it routes through known terrain
    and stops automatically on monsters, item pickup, level boundaries, or
    when blocked. Strictly better than a python `for d in [...]: do(d)` loop
    for navigating known map.

    Usage inside game.exec():
        from tactics import travel_to
        from views import unexplored
        # frontier returns rows like "  d= 5  (12,34)  '.'  3N+5E"
        # parse the (row, col), then:
        result = travel_to(12, 34)
        # result is the post-travel snapshot

    Mechanics: presses `_` (TRAVEL), moves the cursor to (row, col) using
    cardinal direction keys, then sends `.` to confirm and start moving.
    NetHack handles the actual stepping.

    Returns the post-travel observation snapshot.
    """
    # `do` and `observe` are injected by the kernel (game.exec sets them as
    # globals). Allow them to be passed in for testability/explicitness.
    if do is None or observe is None:
        # Resolve from caller's exec frame globals
        import builtins
        frame_globals = _caller_kernel_globals()
        do = do or frame_globals.get("do")
        observe = observe or frame_globals.get("observe")
        if do is None or observe is None:
            raise RuntimeError("travel_to must be called inside game.exec(); needs `do` and `observe` in scope")

    obs = observe()
    cursor = obs.get("cursor") or [0, 0]
    cy, cx = int(cursor[0]), int(cursor[1])

    if (cy, cx) == (row, col):
        return obs  # already there

    # Step 1: enter Travel mode. The cursor in travel mode starts at @.
    do("Command.TRAVEL")

    # Step 2: move the in-game cursor to (row, col).
    dy = row - cy
    dx = col - cx
    for _ in range(abs(dy)):
        do("south" if dy > 0 else "north")
    for _ in range(abs(dx)):
        do("east" if dx > 0 else "west")

    # Step 3: confirm with `.` (period — the MiscDirection.WAIT keypress is the
    # same byte). NetHack interprets `.` in travel-cursor mode as "confirm
    # destination" and starts auto-stepping. Outside travel mode, `.` is rest.
    return do("MiscDirection.WAIT")


def _caller_kernel_globals() -> dict:
    """Walk up the stack to find the game.exec() kernel's globals."""
    import sys
    frame = sys._getframe(2)  # caller of travel_to
    return frame.f_globals
