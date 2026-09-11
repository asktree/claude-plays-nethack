"""travel_to(row, col): use NetHack's Command.TRAVEL to auto-path to a cell."""

from __future__ import annotations

from typing import Any


class TravelStalled(RuntimeError):
    """Travel ran but made no progress toward the destination — typically
    because NetHack's Travel halted silently on a visible monster (peaceful
    or hostile) via lookaround()→nomul(0), or hit a doorway/diagonal rule.
    Caller should re-evaluate before retrying instead of racing the next
    `do(d)` into the same blockage."""


def travel_to(row: int, col: int, *, assert_progress: bool = True,
              observe=None, do=None) -> dict[str, Any]:
    """Auto-path to the given dungeon (row, col) via NetHack's Travel command.

    Travel is NetHack's built-in pathfinder: it routes through known terrain
    and stops automatically on monsters, item pickup, level boundaries, or
    when blocked. Strictly better than a python `for d in [...]: do(d)` loop
    for navigating known map.

    Usage inside game.exec():
        from tactics import travel_to
        from views import unexplored
        result = travel_to(12, 34)

    Mechanics: presses `_` (TRAVEL), moves the cursor to (row, col) using
    cardinal direction keys, then sends `.` to confirm and start moving.
    NetHack handles the actual stepping.

    `assert_progress` (default True): raise TravelStalled if Travel made
    ZERO movement when at least one cell was requested. NetHack's Travel
    halts SILENTLY on visible monsters (lookaround → nomul(0)) and certain
    terrain rules; without this check, a stalled Travel returns an empty
    message and your outer loop blindly issues the next `do(d)` into the
    same situation. Pass False if you genuinely expect zero progress (e.g.
    chained Travels where the first might land exactly on target).

    Returns the post-travel observation snapshot.
    """
    # `do` and `observe` are injected by the kernel (game.exec sets them as
    # globals). Allow them to be passed in for testability/explicitness.
    if do is None or observe is None:
        frame_globals = _caller_kernel_globals()
        do = do or frame_globals.get("do")
        observe = observe or frame_globals.get("observe")
        if do is None or observe is None:
            raise RuntimeError("travel_to must be called inside game.exec(); needs `do` and `observe` in scope")

    obs = observe()
    cursor = obs.get("cursor") or [0, 0]
    cy, cx = int(cursor[0]), int(cursor[1])
    start = (cy, cx)

    if start == (row, col):
        return obs  # already there

    # Step 1: enter Travel mode. The cursor in travel mode starts at @.
    do("Command.TRAVEL")
    # NetHack caches the previous travel destination (iflags.travelcc) when a
    # travel was interrupted, and starts the getpos cursor THERE, not at @.
    # `@` in getpos moves the cursor to the player, so relative moves below
    # are always anchored correctly.
    do("@")

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
    snap = do("MiscDirection.WAIT")

    if assert_progress:
        end_cursor = snap.get("cursor") or [cy, cx]
        end = (int(end_cursor[0]), int(end_cursor[1]))
        moved = max(abs(end[0] - start[0]), abs(end[1] - start[1]))
        intended = max(abs(row - start[0]), abs(col - start[1]))
        msg = (snap.get("message") or "").strip()
        # Stall = under-progress + silent halt. If a message fired (real
        # NetHack msg or our synth hostile-LoS msg), safe_exec already paused
        # on it; the gamer is in the loop. The dangerous case is the SILENT
        # halt — empty message, cursor barely moved, gamer's outer loop
        # races on without realizing. NetHack's lookaround → nomul(0) on
        # visible monsters frequently triggers this.
        if moved < intended and not msg:
            raise TravelStalled(
                f"travel_to({row},{col}): silent halt at {end} after {moved}/"
                f"{intended} cells (start={start}). NetHack Travel stopped "
                f"without printing — likely a visible monster (lookaround "
                f"halts on any monster in LoS, peaceful or hostile) or a "
                f"terrain rule. Re-evaluate (clear/displace the monster, or "
                f"pick a closer target) before retrying. Pass "
                f"assert_progress=False to opt out."
            )
    return snap


def _caller_kernel_globals() -> dict:
    """Walk up the stack to find the game.exec() kernel's globals."""
    import sys
    frame = sys._getframe(2)  # caller of travel_to
    return frame.f_globals


def travel_to_nearest(symbol: str, index: int = 0, *,
                      assert_progress: bool = True,
                      observe=None, do=None) -> dict[str, Any]:
    """Find the nth-nearest occurrence of `symbol` in view, then travel_to it.

    `index=0` (default) is the nearest. Distance is Chebyshev (NetHack moves).
    Searches the dungeon area only (rows 1..21).

    Useful for grabbing items: travel_to_nearest('$') walks toward the nearest
    gold pile; travel_to_nearest('!') toward a potion; travel_to_nearest('?')
    toward a scroll. Travel will auto-stop on hostiles or item pickup.

    Raises ValueError if there are fewer than index+1 matches.
    """
    if do is None or observe is None:
        frame = _caller_kernel_globals()
        do = do or frame.get("do")
        observe = observe or frame.get("observe")
        if do is None or observe is None:
            raise RuntimeError("must be called inside game.exec()")
    obs = observe()
    chars = obs.get("chars") or []
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
            f"only {len(matches)} occurrence(s) of {symbol!r} in view; requested index {index}"
        )
    _, r, c = matches[index]
    return travel_to(r, c, assert_progress=assert_progress, do=do, observe=observe)
