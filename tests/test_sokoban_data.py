"""The generated Sokoban solutions (play/tactics/sokoban_data.py) replay
cleanly in the rules simulator of scripts/gen_sokoban.py."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "play"))
sys.path.insert(0, str(ROOT / "src"))

from gen_sokoban import DIRS, Board  # noqa: E402
from tactics.sokoban_data import LEVELS  # noqa: E402


def test_all_eight_levels_present():
    assert sorted(LEVELS) == ["soko1-1", "soko1-2", "soko2-1", "soko2-2", "soko3-1", "soko3-2",
                              "soko4-1", "soko4-2"]


def test_solutions_replay():
    for name, lv in LEVELS.items():
        b = Board({"rows": lv["rows"], "boulders": [tuple(x) for x in lv["boulders"]],
                   "traps": [tuple(x) for x in lv["traps"]], "start": tuple(lv["start"])})
        for i, st in enumerate(lv["steps"]):
            cur = tuple(st["at"])
            for d in st["moves"]:
                assert d in DIRS
                cur = b.push(cur, d)
                if cur is None:
                    break
            assert (cur is None) == st["fills"], (name, i)
            assert sorted(b.boulders) == [tuple(x) for x in st["after"]["boulders"]], (name, i)
            assert sorted(b.traps) == [tuple(x) for x in st["after"]["traps"]], (name, i)
        assert b.path(b.hero, tuple(lv["exit"])) is not None, name


def _screen_for(name, ox, oy, step=None, pet=None):
    from nh.game import Snap
    from nh.parse import State, Status
    from nh.screen import Screen
    lv = LEVELS[name]
    rows = [" " * 80 for _ in range(24)]
    src = lv if step is None else lv["steps"][step]["after"]
    boulders, traps = set(map(tuple, src["boulders"])), set(map(tuple, src["traps"]))
    for y, r in enumerate(lv["rows"]):
        line = list(rows[y + oy])
        for x, c in enumerate(r):
            ch = "0" if (x, y) in boulders else "^" if (x, y) in traps else c
            if ch != " ":
                line[x + ox] = ch
        rows[y + oy] = "".join(line)
    if pet:
        line = list(rows[pet[1] + oy])
        line[pet[0] + ox] = "f"
        rows[pet[1] + oy] = "".join(line)
    scr = Screen(width=80, height=24, chars=rows, fg=[[7] * 80 for _ in range(24)],
                 reverse=[[False] * 80 for _ in range(24)], bold=[[False] * 80 for _ in range(24)], cursor=(0, 0))
    return Snap(screen=scr, state=State("command"), status=Status(ok=True))


def test_identify_and_progress_on_synthetic_screens():
    from tactics import sokoban as S
    for name, lv in LEVELS.items():
        p = S.progress(_screen_for(name, 27, 4))
        assert (p["level"], p["ox"], p["oy"], p["done"]) == (name, 27, 4, 0)
        p = S.progress(_screen_for(name, 27, 4, step=5))
        assert p["done"] == 6
        # a pet standing on a boulder square doesn't break the match
        b = lv["steps"][5]["after"]["boulders"][0]
        p = S.progress(_screen_for(name, 27, 4, step=5, pet=tuple(b)))
        assert p["done"] == 6


def test_progress_resumes_mid_step():
    from tactics import sokoban as S
    for name, lv in LEVELS.items():
        # find a step with at least 3 moves; build the board after 2 of its pushes
        for i, st in enumerate(lv["steps"]):
            if len(st["moves"]) >= 3:
                break
        prev = lv if i == 0 else lv["steps"][i - 1]["after"]
        at = tuple(st["at"])
        pos = at
        for d in st["moves"][:2]:
            dx, dy = S._DXY[d]
            hero, pos = pos, (pos[0] + dx, pos[1] + dy)
        boulders = [b for b in map(tuple, prev["boulders"]) if b != at] + [pos]
        snap = _screen_for_state(name, 27, 4, boulders, [tuple(x) for x in prev["traps"]], hero=hero)
        p = S.progress(snap)
        assert p["done"] == i and p["partial"] == {"pushes_done": 2, "boulder_at": (pos[0] + 27, pos[1] + 4)}, name


def test_step_that_returns_its_boulder_is_told_apart_by_the_hero():
    """soko4-1 step 3 pushes D right, walks around, pushes it back left: after
    2 pushes the board is as before the step; only the hero's side differs
    (and from the right side, replaying the 'r' is impossible)."""
    from tactics import sokoban as S
    lv = LEVELS["soko4-1"]
    st = lv["steps"][2]
    assert st["moves"].startswith("rl") and tuple(st["at"]) == (9, 3)
    prev = lv["steps"][1]["after"]
    board = ([tuple(x) for x in prev["boulders"]], [tuple(x) for x in prev["traps"]])
    # before the step (hero where step 2 left it, left of D): replay the whole step
    p = S.progress(_screen_for_state("soko4-1", 27, 4, *board, hero=(2, 3)))
    assert p["done"] == 2 and p["partial"] is None
    # paused after 'rl' (hero right of D): resume with the remaining pushes
    p = S.progress(_screen_for_state("soko4-1", 27, 4, *board, hero=(10, 3)))
    assert p["done"] == 2 and p["partial"] == {"pushes_done": 2, "boulder_at": (9 + 27, 3 + 4)}


def _screen_for_state(name, ox, oy, boulders, traps, hero=None):
    from nh.game import Snap
    from nh.parse import State, Status
    from nh.screen import Screen
    lv = LEVELS[name]
    rows = [" " * 80 for _ in range(24)]
    for y, r in enumerate(lv["rows"]):
        line = list(rows[y + oy])
        for x, c in enumerate(r):
            ch = "0" if (x, y) in boulders else "^" if (x, y) in traps else c
            if (x, y) == hero:
                ch = "@"
            if ch != " ":
                line[x + ox] = ch
        rows[y + oy] = "".join(line)
    cursor = (hero[0] + ox, hero[1] + oy) if hero else (0, 0)
    scr = Screen(width=80, height=24, chars=rows, fg=[[7] * 80 for _ in range(24)],
                 reverse=[[False] * 80 for _ in range(24)], bold=[[False] * 80 for _ in range(24)], cursor=cursor)
    return Snap(screen=scr, state=State("command"), status=Status(ok=True))
