"""Per-(dungeon, level, cell) memory of how many Command.SEARCH actions have
been spent at each standing position.

Populated by game/hooks/search_record.py (fires on every post_do where the
action is Command.SEARCH). Consumed by views/likely_secret_doors.py to drop
candidates that have been searched ~12 times already (the canonical NetHack
threshold — Luck=0 search has ~1/12 chance per turn, so ~64% find rate at 12).

State is module-level so views and tactics share the same map. Survives game
resets within a single server lifetime; a new run.sh starts fresh.
"""

from __future__ import annotations

# Threshold: the canonical NetHack "12s" idiom. After this many searches at a
# standing cell, the cell is treated as exhausted by likely_secret_doors.
EXHAUSTED_THRESHOLD = 12

_counts: dict[tuple[int, int, int, int], int] = {}


def record_search(dungeon: int, dlevel: int, row: int, col: int) -> int:
    """Bump the count for (dungeon, dlevel, row, col). Returns the new count."""
    key = (int(dungeon), int(dlevel), int(row), int(col))
    _counts[key] = _counts.get(key, 0) + 1
    return _counts[key]


def count_at(dungeon: int, dlevel: int, row: int, col: int) -> int:
    """Return how many searches we've recorded at that standing cell."""
    return _counts.get((int(dungeon), int(dlevel), int(row), int(col)), 0)


def is_exhausted(dungeon: int, dlevel: int, row: int, col: int,
                 threshold: int = EXHAUSTED_THRESHOLD) -> bool:
    return count_at(dungeon, dlevel, row, col) >= threshold


def all_counts_for_level(dungeon: int, dlevel: int) -> dict[tuple[int, int], int]:
    """Map (row, col) -> count for the given level. Useful for view rendering."""
    return {(r, c): n for (d, dl, r, c), n in _counts.items()
            if d == dungeon and dl == dlevel}
