"""The generated Sokoban solutions (play/tactics/sokoban_data.py) replay
cleanly in the rules simulator of scripts/gen_sokoban.py."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "play"))

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
