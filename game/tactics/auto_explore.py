"""auto_explore(): repeatedly travel toward the nearest unexplored frontier
until the level is fully explored or pathfinding gets stuck.

Stops on:
  - no remaining frontier cells reachable from `@`
  - max_iters reached (safety cap to prevent runaway)
  - no progress in last iteration (cursor didn't change after travel_to)

Game events (hostile arriving, hunger transition, item underfoot, …) are
intentionally NOT checked here — they all produce NetHack messages, which
safe_exec pauses on, putting the gamer in control. Defending against them
inside the loop would be redundant.

Returns a summary dict with `reason`, `iters`, `targets` (list of (r,c) tried).
"""

from __future__ import annotations

import sys
from typing import Any

from .travel_to import travel_to

# Opportunistic search burst: when @ stands on/adjacent to a likely-secret-door
# candidate, do this many SEARCHes before continuing. Two such bursts add up to
# the canonical 12-search threshold, so a candidate naturally exits the view's
# fresh list after two visits — no per-call dedup math needed beyond a set of
# "already burst at this cell during this auto_explore call".
SEARCH_BURST = 6


def _resolve_kernel():
    frame = sys._getframe(2).f_globals
    do = frame.get("do")
    observe = frame.get("observe")
    if do is None or observe is None:
        raise RuntimeError("auto_explore must be called inside game.exec()")
    return do, observe


def _best_frontier(obs: dict[str, Any]) -> tuple[int, int, str] | None:
    """Return (row, col, glyph) of the best frontier to head toward, or None.

    Sort key: (is_door, distance). All non-door walkable frontiers come first
    by distance, then closed doors. Doors are blind risk surfaces — only try
    them when the safe (non-door) frontier is exhausted.
    """
    chars = obs.get("chars") or []
    seen = obs.get("seen") or []
    if not chars or not seen:
        return None
    cursor = obs.get("cursor") or [0, 0]
    py, px = int(cursor[0]), int(cursor[1])
    h = len(chars)
    w = len(chars[0]) if chars else 0
    walkable = set(".#+<>")
    candidates: list[tuple[int, int, int, int, str]] = []  # (is_door, distance, r, c, glyph)
    for r in range(h):
        for c in range(w):
            ch_int = chars[r][c]
            ch = chr(ch_int) if ch_int else " "
            if ch not in walkable:
                continue
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and nr < len(seen) and 0 <= nc < len(seen[nr]):
                    if not seen[nr][nc]:
                        d = max(abs(r - py), abs(c - px))
                        candidates.append((1 if ch == "+" else 0, d, r, c, ch))
                        break
    if not candidates:
        return None
    candidates.sort()  # non-doors (0) first by distance, then doors (1)
    _, _, r, c, ch = candidates[0]
    return (r, c, ch)


def _open_adjacent_door(do, observe) -> str | None:
    """If a closed `+` is adjacent to @, walk into it (auto-opens or attempts).

    Returns the direction we tried, or None if no `+` was adjacent.
    """
    obs = observe()
    chars = obs.get("chars") or []
    cursor = obs.get("cursor") or [0, 0]
    cy, cx = int(cursor[0]), int(cursor[1])
    h, w = len(chars), len(chars[0]) if chars else 0
    for dr, dc, dname in (
        (-1, 0, "north"), (1, 0, "south"),
        (0, -1, "west"), (0, 1, "east"),
    ):
        nr, nc = cy + dr, cx + dc
        if 0 <= nr < h and 0 <= nc < w:
            ch_int = chars[nr][nc]
            ch = chr(ch_int) if ch_int else " "
            if ch == "+":
                do(dname)  # NetHack auto-opens (or asks for unlock if locked)
                return dname
    return None


def auto_explore(
    *,
    max_iters: int = 100,
    open_doors: bool = True,
    do=None,
    observe=None,
) -> dict[str, Any]:
    """Explore until done, hostile in view, or stuck.

    Frontier preference: non-door walkable cells first by distance, then closed
    doors. Doors are blind risk surfaces — handled only when safe frontier is
    exhausted, so we don't poke our head into a `+` while there's a corridor
    we could be exploring instead.

    `open_doors=True`: when a travel attempt makes no progress AND there's a
    closed door adjacent, walks into it (NetHack auto-opens, or attempts to
    unlock). On the next iteration, the newly-revealed cells become frontiers.
    """
    if do is None or observe is None:
        do, observe = _resolve_kernel()

    targets: list[tuple[int, int, str]] = []  # (r, c, glyph)
    searches: list[tuple[int, int, int]] = []  # (r, c, count_done) for telemetry
    last_pos: tuple[int, int] | None = None
    just_opened_door = False
    burst_done_at: set[tuple[int, int]] = set()  # in-call dedup of search bursts

    for i in range(max_iters):
        obs = observe()

        # Opportunistic search: if @ touches a likely-secret-door candidate AND
        # we haven't burst here this call, search SEARCH_BURST times before
        # moving on. Reveal-detection lives in the post_do hook (search_record)
        # and the view's filter; here we just spend the turns.
        cursor = obs.get("cursor") or [0, 0]
        cy, cx = int(cursor[0]), int(cursor[1])
        if (cy, cx) not in burst_done_at and _near_likely_secret(obs, cy, cx):
            for _ in range(SEARCH_BURST):
                do("Command.SEARCH")
            searches.append((cy, cx, SEARCH_BURST))
            burst_done_at.add((cy, cx))
            continue  # re-observe; new walkable cells (if any) will appear as frontiers

        frontier = _best_frontier(obs)
        if frontier is None:
            return {"reason": "level fully explored from current position",
                    "iters": i, "targets": targets, "searches": searches}
        tr, tc, glyph = frontier

        # No-progress check. If we didn't move since last iter AND we didn't
        # *just* open a door (that doesn't change cursor pos), we're stuck —
        # try opening an adjacent door. If even that fails, bail.
        cur_pos = (cy, cx)
        if last_pos is not None and cur_pos == last_pos and not just_opened_door:
            if open_doors:
                opened = _open_adjacent_door(do, observe)
                if opened:
                    just_opened_door = True
                    targets.append((cur_pos[0], cur_pos[1], f"door-{opened}"))
                    continue
            return {"reason": f"no progress (stuck at {cur_pos}, target was unreachable)",
                    "iters": i, "targets": targets, "searches": searches}
        last_pos = cur_pos
        just_opened_door = False

        targets.append((tr, tc, glyph))
        # assert_progress=False: auto_explore has its own no-progress branch
        # below (cur_pos==last_pos opens an adjacent door or returns
        # "no progress"), so a stalled Travel here doesn't need to also
        # raise TravelStalled — it'd just be redundant noise inside the loop.
        travel_to(tr, tc, assert_progress=False, do=do, observe=observe)

    return {"reason": f"max_iters={max_iters} reached",
            "iters": max_iters, "targets": targets, "searches": searches}


def _near_likely_secret(obs: dict[str, Any], cy: int, cx: int) -> bool:
    """True if any unexhausted likely-secret-door candidate sits in the 3×3
    around (cy, cx) — i.e. within a single Command.SEARCH's reveal radius.
    Reuses views.likely_secret_doors's internal dead-end and sealed-room
    detectors so the criterion is identical.
    """
    try:
        from views.likely_secret_doors import _dead_ends, _sealed_rooms
    except ImportError:
        return False
    try:
        from search_memory import count_at, EXHAUSTED_THRESHOLD
    except ImportError:
        count_at = lambda *a, **kw: 0  # type: ignore
        EXHAUSTED_THRESHOLD = 12

    chars = obs.get("chars") or []
    if not chars:
        return False
    bl = obs.get("blstats") or {}
    dnum = int(bl.get("dungeon_number", 0))
    dlevel = int(bl.get("level_number", 0))

    def in_3x3(r: int, c: int) -> bool:
        return abs(r - cy) <= 1 and abs(c - cx) <= 1

    for r, c, _hint in _dead_ends(chars, obs.get("seen"), obs.get("descriptions")):
        if in_3x3(r, c) and count_at(dnum, dlevel, r, c) < EXHAUSTED_THRESHOLD:
            return True
    for r1, c1, r2, c2, _area in _sealed_rooms(chars):
        # @ is "near" a sealed room if any of its perimeter wall cells are in
        # the 3×3. The room's bounding box gives an OK approximation.
        if cy >= r1 - 1 and cy <= r2 + 1 and cx >= c1 - 1 and cx <= c2 + 1:
            return True
    return False


