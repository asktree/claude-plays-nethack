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
    assert sent == [".", "."] and any(m["dist"] == 1 for m in s.monsters)
    # no pet in view: no waiting at all
    sent.clear()
    nav._wait_for_pet(_snap({}, (10, 5), []), 6)
    assert sent == []
    # a hostile close by: don't wait
    sent.clear()
    jackal = {"x": 11, "y": 6, "ch": "d", "desc": "jackal", "dist": 1}
    nav._wait_for_pet(_snap({}, (10, 5), [cat_far, jackal]), 6)
    assert sent == []


def test_pay_flow(monkeypatch):
    from nh.parse import State
    from tactics import ctx, town
    bill = _snap({}, (10, 5), [])
    bill.state = State("yn", prompt="Itemized billing? [ynq] (q)")
    done = _snap({}, (10, 5), [])
    done.messages = ["You bought a food ration for 60 gold pieces."]
    script = {"p": bill, "n": done}
    sent = []

    def fake_do(keys, **kw):
        sent.append(keys)
        return script[keys]
    monkeypatch.setattr(ctx, "do", fake_do)
    monkeypatch.setattr(ctx, "last", lambda: _snap({}, (10, 5), []))
    msgs = town.pay()
    assert sent == ["p", "n"] and msgs == ["You bought a food ration for 60 gold pieces."]


def test_routine_flavour_messages():
    import re
    from tactics.combat import ROUTINE

    def routine(m):
        return any(re.search(p, m) for p in ROUTINE)
    for m in ["The hill orc wields a dagger!", "The Grey-elf shoots 2 elven arrows!", "The winter wolf breathes frost!",
              "You are hit by an elven arrow.", "The elven arrow misses you.", "The ogre swings her club."]:
        assert routine(m), m
    for m in ["The monkey stole a ring of fire resistance.", "You feel feverish."]:
        assert not routine(m), m


def test_pick_stairs_by_branch(monkeypatch):
    import pytest
    from tactics import ctx, nav

    class G:
        stair_links = {"The Dungeons of Doom / Level 2": {(21, 14): "The Gnomish Mines / Level 3"}}

        def level_key(self, status=None):
            return "The Dungeons of Doom / Level 2"
    monkeypatch.setattr(ctx, "game", G())
    s = _snap({}, (21, 14), [])
    cells = [(21, 14), (74, 17)]
    # the Mines staircase under you is known: go_down() takes the other one
    assert nav._pick_stairs(">", cells, None, s)[0] == (74, 17)
    # on purpose: to='Mines'
    assert nav._pick_stairs(">", cells, "Mines", s)[0] == (21, 14)
    # the main one isn't known yet, but by elimination
    assert nav._pick_stairs(">", cells, "Dungeons", s)[0] == (74, 17)
    G.stair_links["The Dungeons of Doom / Level 2"][(74, 17)] = "The Dungeons of Doom / Level 3"
    assert nav._pick_stairs(">", cells, None, s)[0] == (74, 17)
    with pytest.raises(nav.NavError):
        nav._pick_stairs(">", cells, "Sokoban", s)


def test_movement_helpers_never_step_onto_monsters(monkeypatch):
    import pytest
    from tactics import ctx, nav
    sent = []
    monkeypatch.setattr(ctx, "do", lambda keys, **kw: sent.append(keys) or _snap({}, (11, 5), []))
    row = {5: "        ......"}
    cock = {"x": 11, "y": 5, "ch": "c", "desc": "cockatrice", "dist": 1}
    s = _snap(row, (10, 5), [cock])
    monkeypatch.setattr(ctx, "last", lambda: s)
    with pytest.raises(nav.NavError, match="cockatrice"):
        nav._final_step(s, (11, 5))                 # travel's last step: the cockatrice moved onto the target
    with pytest.raises(nav.NavError):
        nav.walk_path([(11, 5)])
    with pytest.raises(nav.NavError):
        nav.step("l")
    unseen = {"x": 11, "y": 5, "ch": "I", "desc": "remembered, unseen monster", "unseen": True, "dist": 1}
    with pytest.raises(nav.NavError, match="unseen"):
        nav._final_step(_snap(row, (10, 5), [unseen]), (11, 5))
    assert sent == []
    # your pet just swaps places
    cat = {"x": 11, "y": 5, "ch": "f", "desc": "tame kitten", "tame": True, "pet": True, "dist": 1}
    nav._final_step(_snap(row, (10, 5), [cat]), (11, 5))
    assert sent == ["l"]


def test_keep_pet_waits_then_reports_lost(monkeypatch):
    import pytest
    from tactics import ctx, nav
    cat = {"x": 14, "y": 5, "ch": "f", "desc": "tame kitten", "tame": True, "pet": True, "dist": 4}
    frames = [_snap({}, (10, 5), [dict(cat, x=13, dist=3)]), _snap({}, (10, 5), [dict(cat, x=12, dist=2)])]
    sent = []

    def fake_do(keys, **kw):
        sent.append(keys)
        return frames[min(len(sent), len(frames)) - 1]
    monkeypatch.setattr(ctx, "do", fake_do)
    s = nav._keep_pet(_snap({}, (10, 5), [cat]), [12])
    assert sent == [".", "."] and s.monsters[0]["dist"] == 2
    # the pet never shows up again: waits out the budget, then PetLost
    sent.clear()
    frames[:] = [_snap({}, (10, 5), [])]
    with pytest.raises(nav.PetLost):
        nav._keep_pet(_snap({}, (10, 5), []), [3])
    assert sent == [".", ".", "."]
    # a hostile within 3: no waiting
    sent.clear()
    jackal = {"x": 12, "y": 6, "ch": "d", "desc": "jackal", "dist": 2}
    nav._keep_pet(_snap({}, (10, 5), [cat, jackal]), [12])
    assert sent == []


def test_discoveries_and_looks():
    from tactics.items import parse_discoveries, with_looks
    text = ("Discoveries\n\nPotions\n* potion of water (clear)\n  potion of paralysis (white)\n"
            "  potion called fruit (pink)\nScrolls\n  scroll of identify (KIRJE)\nWands\n  wand of digging (iron)\n"
            "Tools\n  magic lamp (lamp)\nGems/Stones\n  luckstone (gray)\n  emerald (green)\n"
            "Amulets\n  amulet of life saving (circular)")
    d = parse_discoveries([text])
    for pair in (("potion of paralysis", "white potion"), ("potion of water", "clear potion"),
                 ("potion called fruit", "pink potion"), ("scroll of identify", "scroll labeled KIRJE"),
                 ("wand of digging", "iron wand"), ("magic lamp", "lamp"), ("luckstone", "gray stone"),
                 ("emerald", "green gem"), ("amulet of life saving", "circular amulet")):
        assert pair in d, pair
    assert with_looks("2 uncursed potions of paralysis", d).endswith("[white potion]")
    assert "[clear potion]" in with_looks("2 blessed potions of holy water", d)
    assert "[pink potion]" in with_looks("a potion called fruit", d)
    assert with_looks("a food ration", d) == "a food ration"


def test_prayer_verdict_and_quiet_patterns():
    import re
    from tactics.survival import _PRAYER_OK, prayer_verdict
    good = ["You begin praying to Tyr.", "You are surrounded by a shimmering light.", "You finish your prayer.",
            "The potions on the altar glow light blue for a moment.", "You feel that Tyr is well-pleased."]
    v = prayer_verdict(good)
    assert v.startswith("SUCCESS: Tyr is well-pleased") and "HOLY water" in v, v
    assert all(any(re.search(p, m) for p in _PRAYER_OK) for m in good)
    assert prayer_verdict(["You begin praying to Tyr.", "You feel that Tyr is displeased."]).startswith("FAILED")
    v = prayer_verdict(["You begin praying to Tyr.", "You finish your prayer.", "You feel much better.",
                        "You feel that Tyr is pleased."])
    assert "HP restored" in v
    bad = ["You feel that Tyr is displeased.", "Thou durst call upon me?"]
    assert not any(any(re.search(p, m) for p in _PRAYER_OK) for m in bad)


def test_screen_frontiers_and_head_to(monkeypatch):
    from tactics import ctx, explore

    class G:
        visited = {"L": {(10, 5)}}
        hero_pos = (10, 5)

        def level_key(self, status=None):
            return "L"
    monkeypatch.setattr(ctx, "game", G())
    # a maze corridor going east into the unknown; (9,5)'s blank west side was seen from (10,5)
    rows = {4: "        ---------",
            5: "         @......",
            6: "        ---------"}
    s = _snap(rows, (9, 5), [])
    G.visited["L"] = {(9, 5)}
    assert explore.screen_frontiers(s) == [(15, 5)]
    # head_to: no known path to (30,5) -> travel to the frontier nearest to it, then (path known) to the target
    trips = []
    wall = "        " + "-" * 24
    s2 = _snap({4: wall, 5: "         .............", 6: wall}, (15, 5), [])            # corridor seen to x=21
    s3 = _snap({4: wall, 5: "         ......................", 6: wall}, (21, 5), [])   # ... and on to x=30
    s4 = _snap({4: wall, 5: "         ......................", 6: wall}, (30, 5), [])
    frames = iter([s2, s3, s4])
    snaps = {"cur": s}

    def fake_travel(x, y, **kw):
        trips.append((x, y))
        snaps["cur"] = next(frames)
        G.visited["L"].add(snaps["cur"].hero)      # the harness records every square you stand on
        return snaps["cur"]
    monkeypatch.setattr(ctx, "last", lambda: snaps["cur"])
    monkeypatch.setattr(ctx, "activity", lambda text="": None)
    import tactics.nav as nav
    monkeypatch.setattr(nav, "travel", fake_travel)
    out = explore.head_to(30, 5)
    assert trips == [(15, 5), (21, 5), (30, 5)] and out.hero == (30, 5)


def test_refuge_steps_back_out_of_a_corridor_mouth():
    from tactics import ctx, nav

    class G:
        traps, avoid = {}, {}

        def level_key(self, status=None):
            return "L"
    import pytest
    mp = pytest.MonkeyPatch()
    mp.setattr(ctx, "game", G())
    try:
        # a room (x 2-9) opening east into a 1-wide corridor; you in the doorway, a gnome in the corridor
        rows = {3: " --------",
                4: " |.......",
                5: " |.......@G####",
                6: " |.......",
                7: " --------"}
        gnome = {"x": 10, "y": 5, "ch": "G", "desc": "peaceful gnome", "peaceful": True, "dist": 1}
        s = _snap(rows, (9, 5), [gnome])
        ref = nav._refuge(s, [gnome], (14, 5))
        assert ref is not None and ref[0] == 8           # back into the room, away from the gnome
        assert nav._refuge(_snap({5: "       #@G###"}, (8, 5), [gnome]), [gnome], (12, 5)) == (7, 5)
    finally:
        mp.undo()


def test_unlock_box_prompt_flow(monkeypatch):
    from nh.parse import State
    from tactics import ctx, items
    base = _snap({}, (10, 5), [])
    obj = _snap({}, (10, 5), [])
    obj.state = State("object", prompt="What do you want to use or apply? [k or ?*]")
    dirp = _snap({}, (10, 5), [])
    dirp.state = State("direction", prompt="In what direction?")
    lockq = _snap({}, (10, 5), [])
    lockq.state = State("yn", prompt="There is a large box here; lock it? [ynq] (q)")
    unlockq = _snap({}, (10, 5), [])
    unlockq.state = State("yn", prompt="There is a chest here; unlock it? [ynq] (q)")
    done = _snap({}, (10, 5), [])
    done.messages = ["You succeed in unlocking the chest."]
    script = iter([obj, dirp, lockq, unlockq, done])
    sent = []

    def fake_do(keys, **kw):
        sent.append(keys)
        return next(script)
    monkeypatch.setattr(ctx, "do", fake_do)
    monkeypatch.setattr(ctx, "last", lambda: base)
    msgs = items.unlock(tool="k")
    # the unlocked large box is left alone ('n' to "lock it?"), the locked chest gets 'y'
    assert sent == ["a", "k", ".", "n", "y"] and msgs[-1] == "You succeed in unlocking the chest."
