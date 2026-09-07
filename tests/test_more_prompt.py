"""_has_more_prompt must catch a --More-- marker that NetHack's tty wrapped
onto rows 1-2 (bare '\\n' before the marker keeps the column), not only the
whole marker on row 0. Two gamer runs got stuck on this: every keypress was
eaten until MORE was sent by hand (harness notes at Dlvl 7 T=3753 and
Dlvl 13 T=11542)."""

from __future__ import annotations

import numpy as np

from claude_plays_nethack import server

BLANK = " " * 80
MORE = "--More--"

# Captured from a replay of trajectory 1787672699-1753613894-9549c9a5 to
# step 5193: message on row 0, marker split "--M" / "ore--" across rows 1-2.
CAPTURED = [
    "You have a little trouble lifting c - 4 blessed +2 orcish arrows (in quiver).   ",
    "                                                                             --M",
    "ore--                                                                           ",
]


def _obs(rows: list[str]) -> dict:
    arr = np.full((24, 80), ord(" "), dtype=np.uint8)
    for i, row in enumerate(rows):
        for j, ch in enumerate(row[:80]):
            arr[i, j] = ord(ch)
    return {"tty_chars": arr}


def test_captured_wrapped_marker_rows_1_2():
    assert server._has_more_prompt(_obs(CAPTURED))


def test_whole_marker_on_row_0():
    assert server._has_more_prompt(_obs(["You see here a dagger." + MORE, BLANK, BLANK]))


def test_every_split_point_across_rows_0_1_and_1_2():
    for k in range(1, len(MORE)):
        head, tail = MORE[:k], MORE[k:]
        rows01 = ["x" * (80 - k) + head, tail + " " * (80 - len(tail)), BLANK]
        rows12 = ["msg", " " * (80 - k) + head, tail + " " * (80 - len(tail))]
        assert server._has_more_prompt(_obs(rows01)), f"rows 0/1 split at {k}"
        assert server._has_more_prompt(_obs(rows12)), f"rows 1/2 split at {k}"


def test_whole_marker_on_row_1_flush_right():
    # curx == 72 exactly: the bare newline drops to row 1 and the marker
    # fits in cols 72-79 without wrapping.
    assert server._has_more_prompt(_obs(["x" * 72, " " * 72 + MORE, BLANK]))


def test_no_false_positive_on_map_walls_or_popups():
    assert not server._has_more_prompt(_obs(["You hit the newt.", BLANK, "  -----   " + " " * 70]))
    # A message ending in '-' above a wall row must not pair up (row 1 is
    # the never-drawn map row 0, so adjacent-row splits never straddle it).
    assert not server._has_more_prompt(_obs(["You are hit by a boomerang -", BLANK, "-----" + " " * 75]))
    # Popup windows put their --More-- at the window's left edge; those are
    # dismissed by the gamer (content must stay readable), not auto-pumped.
    assert not server._has_more_prompt(_obs(["Things that are here:", "a dagger", MORE + " " * 72]))


def test_missing_tty_chars():
    assert not server._has_more_prompt({})
