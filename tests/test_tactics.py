"""Pure parts of the tactics helpers (no game: snapshots are built by hand)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "play"))
sys.path.insert(0, str(ROOT / "src"))

from nh.game import Snap  # noqa: E402
from nh.parse import State, Status  # noqa: E402
from nh.screen import Screen  # noqa: E402


def _snap(rows: dict, hero, monsters, colors=None):
    chars = [" " * 80 for _ in range(24)]
    for y, r in rows.items():
        chars[y] = r.ljust(80)
    fg = [[7] * 80 for _ in range(24)]
    for (x, y), c in (colors or {}).items():
        fg[y][x] = c
    scr = Screen(width=80, height=24, chars=chars, fg=fg, reverse=[[False] * 80 for _ in range(24)],
                 bold=[[False] * 80 for _ in range(24)], cursor=hero)
    return Snap(screen=scr, state=State("command"), status=Status(ok=True), monsters=monsters)


def test_friendly_in_line_thrown_and_ray():
    from tactics.combat import friendly_in_line
    row = "        |....@f....i...|"
    cat = {"x": 14, "y": 5, "ch": "f", "desc": "tame housecat", "tame": True, "pet": True}
    imp = {"x": 19, "y": 5, "ch": "i", "desc": "homunculus"}
    s = _snap({5: row}, (13, 5), [cat, imp])
    assert friendly_in_line("l", s=s) == [cat]            # the cat is between you and the target
    assert friendly_in_line("h", s=s) == []
    # the target first, the pet behind it: a thrown dagger stops at the target, a ray doesn't
    row2 = "        |....@i...f....|"
    imp2 = {"x": 14, "y": 5, "ch": "i", "desc": "homunculus"}
    cat2 = dict(cat, x=18)
    s = _snap({5: row2}, (13, 5), [imp2, cat2])
    assert friendly_in_line("l", s=s) == []
    assert friendly_in_line("l", ray=True, s=s) == [cat2]
    # a wall stops the scan; a peaceful beyond it is safe
    row3 = "        |.@|..@..."
    dwarf = {"x": 14, "y": 5, "ch": "h", "desc": "peaceful dwarf", "peaceful": True}
    s = _snap({5: row3}, (10, 5), [dwarf])
    assert friendly_in_line("l", ray=True, s=s) == []
    # ...but an open door (brown '|') doesn't
    s = _snap({5: row3}, (10, 5), [dwarf], colors={(11, 5): 3})
    assert friendly_in_line("l", ray=True, s=s) == [dwarf]


def test_spellbook_on_floor_is_walkable_door_is_not():
    from tactics.mapview import bfs_path, is_closed_door, is_walkable
    rows = {4: "        ---------",
            5: "        |...+...|",
            6: "        |.......+",
            7: "        ---------"}
    s = _snap(rows, (9, 5), [], colors={(12, 5): 3, (16, 6): 3})   # both brown
    assert is_walkable(s, 12, 5) and not is_closed_door(s, 12, 5)
    assert is_closed_door(s, 16, 6) and not is_walkable(s, 16, 6)
    assert bfs_path(s, (9, 5), (12, 5)) == [(10, 5), (11, 5), (12, 5)]


def test_dead_ends():
    from tactics.explore import dead_ends
    rows = {4: "        -----",
            5: "        |...|     #",
            6: "        |....#####",
            7: "        -----  #",
            8: "               #"}
    s = _snap(rows, (10, 5), [])
    # (18,5) is the end of the corridor going NE, (15,8) the end of the branch S
    assert sorted(dead_ends(s)) == [(15, 8), (18, 5)]
