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


def test_squeeze_steps():
    from tactics.mapview import bfs_path, squeeze_steps
    rows = {5: "   ##   ",
            6: "  #  ## ",
            7: "  #    #"}
    # (3,5)->(4,5) orthogonal; (2,6)->(3,5): between (3,6) rock and (2,5) rock = squeeze
    s = _snap(rows, (2, 7), [])
    path = bfs_path(s, (2, 7), (7, 7))
    assert path is not None
    assert squeeze_steps(s, path, (2, 7)) == [(2, 6), (4, 5), (6, 6)]


def test_auto_fightable():
    from tactics.combat import auto_fightable
    s = _snap({}, (10, 5), [])
    s.status.xl, s.status.hp, s.status.hpmax = 7, 70, 70

    def m(desc, **kw):
        return dict({"x": 11, "y": 5, "ch": "x", "desc": desc}, **kw)
    assert auto_fightable(m("jackal"), s) and auto_fightable(m("newt"), s) and auto_fightable(m("sewer rat"), s)
    for bad in ("floating eye", "gas spore", "yellow mold", "acid blob", "soldier ant", "cockatrice",
                "leprechaun", "werejackal", "hill orc"):
        assert not auto_fightable(m(bad), s), bad
    assert not auto_fightable(m("peaceful gnome", peaceful=True), s)
    assert not auto_fightable(m("jackal", hallu=True), s)
    assert not auto_fightable(m("", unseen=True), s)
    # at XL1 with 12 HP a hill orc or a jackal pack member is judged differently
    s.status.xl, s.status.hp, s.status.hpmax = 1, 12, 12
    assert not auto_fightable(m("gnome lord"), s)


def test_wait_for_pet_at_stairs(monkeypatch):
    from tactics import ctx, nav
    cat_far = {"x": 13, "y": 5, "ch": "f", "desc": "tame kitten", "tame": True, "pet": True, "dist": 3}
    cat_near = dict(cat_far, x=11, dist=1)
    frames = [_snap({}, (10, 5), [cat_far]), _snap({}, (10, 5), [dict(cat_far, x=12, dist=2)]),
              _snap({}, (10, 5), [cat_near])]
    sent = []

    def fake_do(keys, **kw):
        sent.append(keys)
        return frames[min(len(sent), len(frames) - 1)]
    monkeypatch.setattr(ctx, "do", fake_do)
    s = nav._wait_for_pet(frames[0], 6)
    assert sent == ["s", "s"] and any(m["dist"] == 1 for m in s.monsters)
    # no pet in view: no waiting at all
    sent.clear()
    nav._wait_for_pet(_snap({}, (10, 5), []), 6)
    assert sent == []
    # a hostile close by: don't wait
    sent.clear()
    jackal = {"x": 11, "y": 6, "ch": "d", "desc": "jackal", "dist": 1}
    nav._wait_for_pet(_snap({}, (10, 5), [cat_far, jackal]), 6)
    assert sent == []
