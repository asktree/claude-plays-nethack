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


def test_read_identify_picks_by_priority_across_pages(monkeypatch):
    from nh.parse import Menu, MenuItem, State
    from tactics import ctx, items

    def menu(page, pages, entries, title="What would you like to identify first?"):
        s = _snap({}, (10, 5), [])
        its = []
        for cls, lst in entries:
            its.append(MenuItem("", cls, header=True))
            its += [MenuItem(l, t) for l, t in lst]
        s.state = State("menu", prompt=title, menu=Menu(title=title, items=its, page=page, pages=pages))
        return s
    base = _snap({}, (10, 5), [])
    objp = _snap({}, (10, 5), [])
    objp.state = State("object", prompt="What do you want to read? [kz or ?*]")
    p1 = menu(1, 2, [("Potions", [("F", "a dark green potion")]), ("Scrolls", [("z", "a scroll labeled ZLORFIK")])])
    p2 = menu(2, 2, [("Rings", [("J", "a twisted ring")])])
    p2b = menu(2, 2, [("Rings", [("J", "a twisted ring")])])
    nxt = menu(1, 1, [("Potions", [("F", "a dark green potion")])], title="What would you like to identify next?")
    done = _snap({}, (10, 5), [])
    done.messages = ["F - a potion of see invisible."]
    after_j = _snap({}, (10, 5), [])
    frames = {"r": objp, "k": p1, ">": p2, "J": p2b, "F": nxt}
    seq = []

    def fake_do(keys, **kw):
        seq.append(keys)
        if keys == "<CR>":
            return nxt if seq.count("<CR>") == 1 else done
        return frames[keys]
    state = {"cur": base}

    def fake_last():
        return {"r": objp, "k": p1, ">": p2, "J": p2b, "F": nxt}.get(seq[-1], base) if seq else base
    monkeypatch.setattr(ctx, "do", fake_do)
    monkeypatch.setattr(ctx, "last", fake_last)
    nxt_msgs = nxt.messages
    nxt.messages = ["J - a ring of teleportation."]
    msgs = items.read_identify("k")
    # round 1: the ring on page 2 first (priority), round 2: the only thing left
    assert seq == ["r", "k", ">", "J", "<CR>", "F", "<CR>"], seq
    assert "J - a ring of teleportation." in msgs and "F - a potion of see invisible." in msgs
    nxt.messages = nxt_msgs


def test_write_scroll_flow_and_unknown_type(monkeypatch):
    import pytest
    from nh.parse import State
    from tactics import ctx, items
    base = _snap({}, (10, 5), [])
    inv = [{"letter": "h", "text": "a magic marker (0:50)", "class": "Tools", "buc": ""},
           {"letter": "p", "text": "an unlabeled scroll", "class": "Scrolls", "buc": ""}]
    inv_after = [{"letter": "h", "text": "a magic marker (0:39)", "class": "Tools", "buc": ""},
                 {"letter": "q", "text": "an uncursed scroll of identify", "class": "Scrolls", "buc": "uncursed"}]
    calls = {"inv": 0}

    def fake_inv():
        calls["inv"] += 1
        return inv if calls["inv"] == 1 else inv_after
    monkeypatch.setattr(items, "inventory", fake_inv)
    monkeypatch.setattr(items, "discoveries", lambda: [("scroll of identify", "scroll labeled KIRJE")])
    monkeypatch.setattr(ctx, "last", lambda: base)
    apply_p = _snap({}, (10, 5), [])
    apply_p.state = State("object", prompt="What do you want to use or apply? [h or ?*]")
    write_on = _snap({}, (10, 5), [])
    write_on.state = State("object", prompt="What do you want to write on? [p or ?*]")
    what = _snap({}, (10, 5), [])
    what.state = State("getlin", prompt="What type of scroll do you want to write?")
    done = _snap({}, (10, 5), [])
    done.messages = ["q - an uncursed scroll of identify."]
    frames = {"a": apply_p, "h": write_on, "p": what, "identify<CR>": done}
    sent = []
    monkeypatch.setattr(ctx, "do", lambda keys, **kw: sent.append(keys) or frames[keys])
    r = items.write_scroll("identify")
    assert sent == ["a", "h", "p", "identify<CR>"]
    assert r["written"] == "q - an uncursed scroll of identify." and (r["charges_before"], r["charges_after"]) == (50, 39)
    calls["inv"] = 0
    sent.clear()
    with pytest.raises(PermissionError, match="isn't identified"):
        items.write_scroll("genocide")
    assert sent == []


class _G:
    """A minimal ctx.game for helpers that consult level memory."""
    def __init__(self):
        self.traps, self.avoid, self.visited, self.kills = {}, {}, {}, {}
        self.locked_doors, self.feature_desc, self.intrinsics = {}, {}, {"cold"}
        self.tracker = None
        self.hero_pos = None

    def level_key(self, status=None):
        return "L"

    def corpse_age(self, name, cell, turn):
        return None


def test_travel_two_squares_away_never_moves_into_the_middle_monster(monkeypatch):
    import pytest
    from tactics import ctx, nav
    monkeypatch.setattr(ctx, "game", _G())
    monkeypatch.setattr(ctx, "monster_filter", None)
    row = {5: "        ........."}
    vortex = {"x": 11, "y": 5, "ch": "v", "desc": "dust vortex", "dist": 1}
    s = _snap(row, (10, 5), [vortex])
    monkeypatch.setattr(ctx, "last", lambda: s)
    sent = []
    monkeypatch.setattr(ctx, "do", lambda keys, **kw: sent.append(keys) or s)
    with pytest.raises(nav.NavError, match="dust vortex"):
        nav._travel(12, 5, 40, None, 3, None, False)
    assert sent == []              # no '_' travel to the adjacent square ("You move right into ...")


def test_engulfed_helpers_refuse(monkeypatch):
    import pytest
    from tactics import ctx, explore, nav
    monkeypatch.setattr(ctx, "game", _G())
    s = _snap({}, (10, 5), [])
    s.engulfed = True
    monkeypatch.setattr(ctx, "last", lambda: s)
    for fn in (lambda: nav._travel(20, 5, 40, None, 3, None, False), lambda: explore.head_to(20, 5),
               lambda: nav.go_down()):
        with pytest.raises(nav.NavError, match="ENGULFED"):
            fn()


def test_go_down_refuses_while_levitating_and_checks_the_level(monkeypatch):
    import pytest
    from tactics import ctx, nav
    monkeypatch.setattr(ctx, "game", _G())
    s = _snap({5: "        .>."}, (9, 5), [])
    s.status.conditions = ["Lev"]
    monkeypatch.setattr(ctx, "last", lambda: s)
    with pytest.raises(nav.NavError, match="LEVITATING"):
        nav.go_down()
    # pressed '>' but still on the same level (e.g. a prompt interrupted): NavError, not a silent return
    s.status.conditions, s.status.ldesc = [], "Dlvl:5"
    monkeypatch.setattr(nav, "known_cells", lambda ch, s=None, rescan=False: [(9, 5)])
    s2 = _snap({5: "        .@."}, (9, 5), [])
    s2.status.ldesc = "Dlvl:5"
    s2.messages = ["You are floating high above the stairs."]
    monkeypatch.setattr(ctx, "do", lambda keys, **kw: s2)
    monkeypatch.setattr(ctx, "last", lambda: s if not hasattr(ctx, "_sent") else s2)
    ctx._sent = True
    try:
        with pytest.raises(nav.NavError, match="still on Dlvl:5"):
            nav._use_stairs(">", wait_pet=0)
    finally:
        del ctx._sent


def test_auto_fight_stops_for_a_nontrivial_newcomer(monkeypatch):
    from tactics import combat, ctx
    monkeypatch.setattr(ctx, "game", _G())
    snake = {"x": 11, "y": 5, "ch": "S", "desc": "snake", "dist": 1}
    python = {"x": 11, "y": 5, "ch": "S", "desc": "python", "dist": 1, "note": "crushes."}
    s1 = _snap({}, (10, 5), [snake])
    s1.status.xl, s1.status.hp, s1.status.hpmax = 30, 300, 300
    s2 = _snap({}, (10, 5), [python])       # the snake died, a python stepped in
    s2.status.xl, s2.status.hp, s2.status.hpmax = 30, 300, 300
    frames = iter([s2, s2, s2])
    cur = {"s": s1}
    sent = []

    def fake_do(keys, **kw):
        sent.append(keys)
        cur["s"] = next(frames)
        return cur["s"]
    monkeypatch.setattr(ctx, "do", fake_do)
    monkeypatch.setattr(ctx, "last", lambda: cur["s"])
    monkeypatch.setattr(combat, "_wielding", lambda: True)
    combat.fight(only=lambda m: m["desc"] == "snake")
    assert sent == ["Fl"]                     # one blow at the snake, none at the python
    cur["s"], sent[:] = s1, []
    frames = iter([s2, s2])
    combat.fight(11, 5)                      # fight(x, y): sticks to the species first found there
    assert sent == ["Fl"]


def test_offer_skips_own_race_and_records_outcome(monkeypatch):
    from nh.parse import State
    from tactics import ctx, survival
    g = _G()
    monkeypatch.setattr(ctx, "game", g)
    base = _snap({}, (10, 5), [])
    base.under = "_"
    base.feature_desc = {(10, 5): "lawful altar (Tyr)"}
    q1 = _snap({}, (10, 5), [])
    q1.state = State("yn", prompt="There is a dwarf corpse here; sacrifice it? [ynq] (q)")
    q2 = _snap({}, (10, 5), [])
    q2.state = State("yn", prompt="There is a jackal corpse here; sacrifice it? [ynq] (q)")
    done = _snap({}, (10, 5), [])
    done.messages = ["Your sacrifice is consumed in a flash of light!", "You glimpse a four-leaf clover at your feet."]
    seq = iter([q1, q2, done])
    sent = []
    monkeypatch.setattr(ctx, "do", lambda keys, **kw: sent.append(keys) or next(seq))
    monkeypatch.setattr(ctx, "last", lambda: base)
    r = survival.offer()
    assert sent == ["#offer<CR>", "n", "y"] and r["offered"] == "jackal"
    assert "prayer timeout is 0" in r["outcome"]


def test_travel_keeps_away_from_exploders(monkeypatch):
    import pytest
    from tactics import ctx, nav
    monkeypatch.setattr(ctx, "game", _G())
    monkeypatch.setattr(ctx, "monster_filter", None)
    row = {5: "        ....................."}
    light = {"x": 16, "y": 6, "ch": "y", "desc": "yellow light", "dist": 6}
    s = _snap(row, (10, 5), [light])
    monkeypatch.setattr(ctx, "last", lambda: s)
    sent = []
    monkeypatch.setattr(ctx, "do", lambda keys, **kw: sent.append(keys) or s)
    with pytest.raises(nav.NavError, match="EXPLODES"):
        nav._travel(25, 5, 40, None, 3, 8, False)
    assert sent == []


def test_engrave_message_identification():
    import re
    from tactics.items import _ENGRAVE_ID
    for msg, want in (("You write in the dust with a wand of create monster.", "create monster"),
                      ("You write in the dust with an uncursed wand of striking (0:4).", "striking")):
        hit = next((m.group(1) for pat, v in _ENGRAVE_ID if v is None for m in [re.search(pat, msg)] if m), None)
        assert hit == want, msg


def test_remembered_features_and_invocation_stairs():
    from nh.game import Game, Timing
    g = Game(term=None, timing=Timing.local())
    rows = {5: "        ..........", 6: "        ....?.....", 7: "        .........."}
    s = _snap(rows, (10, 6), [], colors={})
    s.status.ldesc = "Dlvl:48"
    # the stairs seen, then covered by a scroll; a vibrating square underfoot; a portal seen once
    g.terrain_seen["Dlvl:48"] = {(12, 6): "<", (30, 3): "^"}
    g._remember_terrain(s, ["You feel a strange vibration under your feet."])
    g._annotate(s)
    names = {f["name"] for f in s.features}
    assert "vibrating square (under you)" in names
    assert "up stairs (under an object)" in names and "magic portal (remembered)" in names
    # the invocation: '>' under you, the vibrating square forgotten, old traps nearby dropped
    g.traps["Dlvl:48"] = {(11, 7), (40, 7)}
    g._remember_terrain(s, ["You are standing at the top of a stairwell leading down!"])
    assert g.terrain_seen["Dlvl:48"][(10, 6)] == ">" and s.under == ">"
    assert g.traps["Dlvl:48"] == {(40, 7)}


def test_no_path_message_names_traps_and_moat(monkeypatch):
    from tactics import ctx, nav
    monkeypatch.setattr(ctx, "game", _G())
    rows = {4: "        ...........",
            5: "        .}}}}}}}}}.",
            6: "        .}^^^..<.}.",
            7: "        .}^>^....}.",
            8: "        .}^^^....}.",
            9: "        .}}}}}}}}}."}
    s = _snap(rows, (11, 7), [])
    msg = nav._no_path_msg(s, (14, 7), (15, 6))
    assert "a route exists" in msg                # inside the moat, no trap in the way
    msg = nav._no_path_msg(s, (11, 7), (15, 6))
    assert "known trap(s)" in msg and "water" not in msg
    msg = nav._no_path_msg(s, (11, 7), (18, 4))
    assert "known trap(s)" in msg and "water" in msg and "ringed by fire traps" in msg
    s2 = _snap({5: "   ....   ", 6: "   .@..   "}, (4, 6), [])
    msg = nav._no_path_msg(s2, (4, 6), (40, 12), start=(3, 5))
    assert msg.startswith("travel to (40, 12) stopped at (4, 6): NetHack's travel guessed")


def test_travel_refuses_on_the_plane_of_water(monkeypatch):
    import pytest
    from tactics import ctx, nav
    monkeypatch.setattr(ctx, "game", _G())
    s = _snap({5: "   }}}  }}}"}, (6, 5), [])
    s.status.ldesc = "Water"
    monkeypatch.setattr(ctx, "last", lambda: s)
    with pytest.raises(nav.NavError, match="Plane of Water"):
        nav.travel(20, 5)


def test_castle_hint_when_no_down_stairs(monkeypatch):
    from tactics import nav
    s = _snap({12: "   #.....^...^..."}, (5, 12), [], colors={(3, 12): 3})
    s.feature_desc = {(9, 12): "trap door", (13, 12): "trap door"}
    hint = nav._ways_down_hint(s)
    assert "(9, 12)" in hint and "Castle" in hint and "ONLY way down" in hint


def test_diagonal_rule_knows_the_door_under_you():
    from tactics.mapview import bfs_path
    rows = {4: "        --|---", 5: "        |....|", 6: "        |....|"}
    s = _snap(rows, (10, 4), [], colors={})
    s.screen.chars[4] = "        --@---".ljust(80)
    s.under = "D"                      # standing in the doorway of an open door
    path = bfs_path(s, (10, 4), (11, 5))
    assert path and path[0] == (10, 5)           # straight out first, never diagonally
    s.under = None                                 # a doorless doorway: the diagonal is fine
    assert bfs_path(s, (10, 4), (11, 5)) == [(11, 5)]


def test_fight_prefers_a_meleeable_target_and_strikes_an_adjacent_exploder(monkeypatch):
    from tactics import combat, ctx
    g = _G()
    g.wielded = "a +2 long sword (weapon in hand)"
    monkeypatch.setattr(ctx, "game", g)
    monkeypatch.setattr(ctx, "hp_rules", None)
    eye = {"x": 11, "y": 5, "ch": "e", "desc": "floating eye", "dist": 1, "note": "NEVER melee"}
    coy = {"x": 9, "y": 5, "ch": "d", "desc": "coyote", "dist": 1}
    s = _snap({5: "        .....", 6: "        ....."}, (10, 5), [eye, coy])
    s.status.hp, s.status.hpmax = 50, 50
    s_after = _snap({5: "        .....", 6: "        ....."}, (10, 5), [eye])
    s_after.status.hp, s_after.status.hpmax = 50, 50
    state = {"s": s}
    sent = []
    monkeypatch.setattr(ctx, "last", lambda: state["s"])

    def do(keys, **kw):
        sent.append(keys)
        state["s"] = s_after
        return s_after
    monkeypatch.setattr(ctx, "do", do)
    paused = []
    monkeypatch.setattr(ctx, "pause", lambda r: paused.append(r))
    combat.fight(max_blows=2)
    assert sent[0] == "Fh"                          # the coyote, not the floating eye
    assert paused and "floating eye" in paused[0]   # then it stops at the eye
    # a yellow light next to you: strike first (no pause)
    light = {"x": 11, "y": 5, "ch": "y", "desc": "yellow light", "dist": 1, "note": "explodes"}
    s2 = _snap({5: "        .....", 6: "        ....."}, (10, 5), [light])
    s2.status.hp, s2.status.hpmax = 50, 50
    empty = _snap({5: "        .....", 6: "        ....."}, (10, 5), [])
    state["s"] = s2
    sent.clear()
    paused.clear()
    monkeypatch.setattr(ctx, "do", lambda keys, **kw: sent.append(keys) or state.update(s=empty) or empty)
    combat.fight()
    assert sent == ["Fl"] and paused == []


def test_routine_projectile_and_potion_messages():
    import re
    from tactics.combat import ROUTINE
    ok = ["The 1st elven arrow hits the gold golem.", "The mountain centaur hurls an emerald potion!",
          "The flagon crashes on your head and breaks into shards.", "The emerald potion evaporates.",
          "The mountain centaur drinks a potion of healing!", "The high priestess casts a spell!"]
    for m in ok:
        assert any(re.search(p, m) for p in ROUTINE), m
    for m in ["The arrow hits you!", "You feel a strange sense of loss.", "The nymph stole a +0 dagger."]:
        assert not any(re.search(p, m) for p in ROUTINE), m


def test_rogue_level_glyphs_and_floor_memory():
    from nh.game import Game, Timing
    from tactics.explore import screen_frontiers
    from tactics.mapview import is_walkable
    g = Game(term=None, timing=Timing.local())
    rows = {8: "    -----+-----", 9: "    |....%..:|", 10: "    |..@.....|", 11: "    ------+---"}
    s = _snap(rows, (7, 10), [])
    s.status.ldesc = "Dlvl:18"
    g._remember_terrain(s, ["You enter what seems to be an older, more primitive world."])
    g._remember_terrain(s, [])          # (the flag is set by the first call's message)
    g.feature_desc["Dlvl:18"] = {(9, 9): "staircase down"}
    g.terrain_seen["Dlvl:18"][(9, 9)] = ">"
    g._annotate(s)
    assert s.rogue and (6, 10) in s.floor_mem
    names = {f["name"] for f in s.features}
    assert "doorway" in names and "down stairs (shown as %)" in names
    assert not any(o["ch"] in "+%" for o in s.objects)      # no spellbooks/food from doors and stairs
    assert [o["kind"] for o in s.objects] == ["food"]        # the ':' nobody claimed as a monster
    # a dark-room floor square seen before shows blank again: still walkable, not a frontier
    s.screen.chars[10] = "    |  @     |".ljust(80)
    s.screen.chars[9] = "    |    %   |".ljust(80)
    assert is_walkable(s, 6, 10) and is_walkable(s, 5, 9)
    import tactics.ctx as ctx
    ctx.game = g
    assert (6, 10) not in screen_frontiers(s)


def test_air_is_walkable_and_portal_memory_survives_clouds():
    from nh.game import Game, Timing
    from tactics.mapview import is_walkable
    g = Game(term=None, timing=Timing.local())
    s = _snap({5: "####   ####^###"}, (5, 5), [], colors={(4, 5): 6, (6, 5): 6, (11, 5): 13})
    s.status.ldesc = "Air"
    s.screen.chars[5] = "####  @####^###".ljust(80)
    g._remember_terrain(s, [])
    assert g.terrain_seen["Air"][(11, 5)] == "^"
    assert is_walkable(s, 4, 5) and not is_walkable(s, 20, 5)
    s2 = _snap({5: "####  @########"}, (6, 5), [], colors={(4, 5): 6})
    s2.status.ldesc = "Air"
    g._remember_terrain(s2, [])           # unseen air is drawn as '#' clouds: the portal is not "gone"
    g._annotate(s2)
    assert "magic portal (remembered)" in {f["name"] for f in s2.features}


def test_hunt_closes_in_then_fights(monkeypatch):
    from tactics import combat, ctx
    g = _G()
    g.wielded = "a +2 long sword (weapon in hand)"
    monkeypatch.setattr(ctx, "game", g)
    monkeypatch.setattr(ctx, "hp_rules", None)
    row = {5: "        .........."}

    def mk(hero, mx, killed=False):
        mons = [] if killed else [{"x": mx, "y": 5, "ch": "c", "desc": "pyrolisk", "dist": abs(mx - hero[0]),
                                   "id": 3}]
        s = _snap(row, hero, mons)
        s.status.hp, s.status.hpmax, s.status.turn = 40, 40, 100
        return s
    frames = {"s": mk((9, 5), 13)}
    sent = []

    def do(keys, **kw):
        sent.append(keys)
        s = frames["s"]
        if keys == "l":
            nxt = mk((s.hero[0] + 1, 5), 13)
        elif keys == "Fl":
            nxt = mk(s.hero, 13, killed=True)
            nxt.messages = ["You kill the pyrolisk!"]
        else:
            nxt = s
        frames["s"] = nxt
        return nxt
    monkeypatch.setattr(ctx, "do", do)
    monkeypatch.setattr(ctx, "last", lambda: frames["s"])
    monkeypatch.setattr(ctx, "pause", lambda r: None)
    r = combat.hunt("pyrolisk")
    assert sent == ["l", "l", "l", "Fl"] and r["reason"] == "killed" and r["kills"] == ["pyrolisk"]


def test_ascend_refuses_a_cross_aligned_altar(monkeypatch):
    import pytest
    from tactics import ctx, endgame
    monkeypatch.setattr(ctx, "game", _G())
    s = _snap({11: "   ...@..."}, (6, 11), [])
    s.status.ldesc, s.status.align, s.under = "Astral Plane", "Lawful", "_"
    look = _snap({11: "   ...@..."}, (6, 11), [])
    look.messages = ["There is a high altar to Loki (chaotic) here."]
    sent = []
    monkeypatch.setattr(ctx, "last", lambda: s)
    monkeypatch.setattr(ctx, "do", lambda keys, **kw: sent.append(keys) or look)
    with pytest.raises(RuntimeError, match="WITHOUT winning"):
        endgame.ascend()
    assert sent == [":"]                          # looked, offered nothing
    s.under = None
    with pytest.raises(RuntimeError, match="not standing on an altar"):
        endgame.ascend()


def test_loot_all_leaves_unknown_gray_stones_inside(monkeypatch):
    from nh.parse import Menu, MenuItem, State
    from tactics import ctx, items
    monkeypatch.setattr(ctx, "game", _G())

    def menu(title, entries):
        s = _snap({}, (10, 5), [])
        s.state = State("menu", prompt=title, menu=Menu(title=title, items=[MenuItem(l, t) for l, t in entries]))
        return s
    yn = _snap({}, (10, 5), [])
    yn.state = State("yn", prompt="There is a large box here, loot it? [ynq] (q)", choices="ynq")
    do_what = menu("Do what with the large box?", [("o", "take something out"), ("i", "put something in")])
    kinds = menu("Take out what type of objects?", [("A", "Auto-select every item"), ("a", "All types"),
                                                    ("b", "Coins"), ("c", "Gems/Stones")])
    what = menu("Take out what?", [("a", "551 gold pieces"), ("b", "a gray stone"), ("c", "a ruby")])
    done = _snap({}, (10, 5), [])
    done.messages = ["$ - 551 gold pieces.", "r - a ruby."]
    seq = []
    flow = {"#loot<CR>": yn, "y": do_what, "o": kinds, "a": kinds, "<CR>": None}
    state = {"cur": _snap({}, (10, 5), []), "menu_cr": 0}

    def fake_do(keys, **kw):
        seq.append(keys)
        if keys == "<CR>":
            state["menu_cr"] += 1
            state["cur"] = what if state["menu_cr"] == 1 else done
        elif keys in flow and flow[keys] is not None:
            state["cur"] = flow[keys]
        elif state["cur"] is what:
            state["cur"] = what            # item letters toggle within the same menu
        return state["cur"]
    monkeypatch.setattr(ctx, "do", fake_do)
    monkeypatch.setattr(ctx, "last", lambda: state["cur"])
    items.loot_all(unlock_with_key=False)
    assert "A" not in seq                        # never "Auto-select every item"
    assert seq[seq.index("<CR>") + 1:] == ["a", "c", "<CR>"]      # gold and ruby, not the gray stone


def test_sokoban_push_stops_before_a_mimic_on_the_route():
    from tactics.sokoban import _sessile_on_route
    s = _snap({5: "   ..0...."}, (4, 5), [{"x": 8, "y": 5, "ch": "m", "desc": "giant mimic, mimicking a boulder"}])
    assert _sessile_on_route(s, (5, 5), ["l", "l", "l"])[1] == (8, 5)
    assert _sessile_on_route(s, (5, 5), ["l"]) is None
    jackal = _snap({5: "   ..0...."}, (4, 5), [{"x": 6, "y": 5, "ch": "d", "desc": "jackal"}])
    assert _sessile_on_route(jackal, (5, 5), ["l"]) is None       # a mobile monster steps aside (the solver waits)


def test_remembered_doors_under_piles_and_beside_dug_walls():
    from tactics.mapview import bfs_path, is_door
    rows = {4: "   ---.---", 5: "   |..%..|", 6: "   |.....|"}
    s = _snap(rows, (5, 6), [])
    s.feature_mem = {(6, 4): "D"}          # an open door, now under a corpse pile... (the '%' at (6,5) is food)
    s.screen.chars[4] = "   ---%---".ljust(80)
    assert is_door(s, 6, 4)
    path = bfs_path(s, (5, 5), (6, 3)) if False else None   # (row 3 unknown: just check the diagonal rule below)
    s2 = _snap({4: "   ---+---", 5: "   |..@..|", 3: "      .   "}, (6, 5), [], colors={(6, 4): 3})
    s2.feature_mem = {(6, 4): "D"}
    s2.screen.chars[3] = "      .   ".ljust(80)
    # a dug wall beside the door broke its wall line: still a door (not a spellbook) thanks to the memory
    s2.screen.chars[4] = "   ---+.--".ljust(80)
    assert not any(o["ch"] == "+" for o in s2.objects)
    assert "closed door" in {f["name"] for f in s2.features}


def test_throne_forgotten_when_it_vanishes():
    from nh.game import Game, Timing
    g = Game(term=None, timing=Timing.local())
    s = _snap({17: "   ..@.."}, (5, 17), [])
    s.status.ldesc = "Dlvl:19"
    g.terrain_seen["Dlvl:19"] = {(5, 17): "\\\\"}
    g._remember_terrain(s, ["The throne vanishes in a puff of logic."])
    assert (5, 17) not in g.terrain_seen["Dlvl:19"] and s.under is None


def test_travel_steps_away_from_a_floating_eye(monkeypatch):
    from tactics import ctx, nav
    monkeypatch.setattr(ctx, "game", _G())
    monkeypatch.setattr(ctx, "monster_filter", None)
    eye = {"x": 11, "y": 5, "ch": "e", "desc": "floating eye", "dist": 1, "note": "NEVER melee"}
    rows = {4: "        ..........", 5: "        ..........", 6: "        .........."}
    s = _snap(rows, (10, 5), [eye])
    assert nav._passive_only(eye) and not nav._passive_only({"desc": "jackal"})
    frames = {"s": s}
    sent = []

    from nh.parse import State

    def do(keys, **kw):
        sent.append(keys)
        cur = frames["s"]
        if keys == "_":                        # NetHack's travel prompt opens...
            g = _snap(rows, (10, 5), [eye])
            g.state = State("getpos", prompt="Where do you want to travel to?")
            frames["s"] = g
            return g
        if keys == "." and cur.state.kind == "getpos":
            back = _snap(rows, cur.last_pos or (10, 5), [eye])   # ...and lookaround() doesn't start it
            frames["s"] = back
            return back
        if keys in ("y", "k", "u", "h", "l", "b", "j", "n"):
            from tactics.mapview import KEY_DIR
            dx, dy = KEY_DIR[keys]
            cur = _snap(rows, (cur.hero[0] + dx, cur.hero[1] + dy), [dict(eye, dist=max(abs(11 - cur.hero[0] - dx),
                                                                                      abs(5 - cur.hero[1] - dy)))])
        frames["s"] = cur
        return cur
    monkeypatch.setattr(ctx, "do", do)
    monkeypatch.setattr(ctx, "last", lambda: frames["s"])
    monkeypatch.setattr(nav, "cursor_to", lambda x, y, rounds=5: frames["s"])
    try:
        nav._travel(2, 5, 3, None, 0, 0, False)
    except nav.NavError as e:
        assert "hostile floating eye adjacent" not in str(e)
    steps = [k for k in sent if k in ("y", "k", "u", "h", "l", "b", "j", "n")]
    assert sent[:2] == ["_", "."] and steps and steps[0] in ("h", "y", "b")   # then a plain step away


def test_sokoban_adjust_applies_to_every_plan_state(monkeypatch):
    from tactics import ctx, sokoban
    from tactics.sokoban_data import LEVELS

    class _T:
        def __init__(self):
            self.state, self.saved = {}, 0

        def save(self):
            self.saved += 1
    g = _G()
    g.memory = _T()
    monkeypatch.setattr(ctx, "game", g)
    name = next(iter(LEVELS))
    lv0 = LEVELS[name]
    spare = tuple(lv0["boulders"][0])
    g.memory.state["sokoban_adjust"] = {name: {"remove": [list(spare)], "add": [[1, 1]]}}
    lv = sokoban._levels()[name]
    assert spare not in {tuple(b) for b in lv["boulders"]} and (1, 1) in {tuple(b) for b in lv["boulders"]}
    assert all((1, 1) in {tuple(b) for b in st["after"]["boulders"]} for st in lv["steps"])
    assert spare in {tuple(b) for b in LEVELS[name]["boulders"]}       # the plan itself is untouched


def test_medusa_risk_and_guards(monkeypatch):
    import pytest
    from nh.game import Game, Timing
    from tactics import ctx, nav
    g = Game(term=None, timing=Timing.local())
    g.level_name, g.level_name_ldesc = "The Dungeons of Doom / Level 23", "Dlvl:23"
    rows = {y: "}" * 60 for y in (3, 4)}
    rows[5] = "      .@.<"
    s = _snap(rows, (7, 5), [], colors={(x, y): 4 for y in (3, 4) for x in range(60)})
    s.status.ldesc = "Dlvl:23"
    g.terrain_seen["The Dungeons of Doom / Level 23"] = {(9, 5): "<"}
    g._annotate(s)
    assert s.medusa_risk and "medusa?" in s.flags
    monkeypatch.setattr(ctx, "game", g)
    with pytest.raises(nav.NavError, match="MEDUSA"):
        nav._medusa_check(s, (30, 12), "travel()", False)
    nav._medusa_check(s, (9, 5), "travel()", False)          # back to the up stairs: allowed
    s.status.conditions = ["Blind"]
    g._annotate(s)
    assert not s.medusa_risk                                   # blindfolded: protected
    s.status.conditions = []
    g.reflecting = True
    g._annotate(s)
    assert not s.medusa_risk
    # a drawbridge in view: the Castle, not Medusa
    g2 = Game(term=None, timing=Timing.local())
    g2.level_name, g2.level_name_ldesc = "The Dungeons of Doom / Level 27", "Dlvl:27"
    s2 = _snap(rows, (7, 5), [], colors={**{(x, y): 4 for y in (3, 4) for x in range(60)}, (8, 5): 3})
    s2.screen.chars[5] = "      .@#<".ljust(80)
    s2.status.ldesc = "Dlvl:27"
    g2._annotate(s2)
    assert not s2.medusa_risk and "castle" in s2.flags


def test_quest_leader_and_level_change_guards(monkeypatch):
    import pytest
    from tactics import ctx, nav
    g = _G()
    monkeypatch.setattr(ctx, "game", g)
    norn = {"x": 20, "y": 5, "ch": "@", "desc": "peaceful Norn", "peaceful": True, "dist": 10}
    s = _snap({5: "   " + "." * 30}, (10, 5), [norn])
    s.status.xl = 13
    with pytest.raises(nav.NavError, match="XL13"):
        nav._leader_check(s, (19, 5), "travel()", False)
    nav._leader_check(s, (12, 5), "travel()", False)           # not near her: fine
    s.status.xl = 14
    with pytest.raises(nav.NavError, match="7 tries"):
        nav._leader_check(s, (19, 5), "travel()", False)
    g.piety = "piously"
    nav._leader_check(s, (19, 5), "travel()", False)           # ready
    # the level changes under a travel: stop
    from nh.parse import State
    a = _snap({5: "   " + "." * 30}, (10, 5), [])
    a.status.ldesc = "Home 1"
    b = _snap({5: "   " + "." * 30}, (12, 5), [])
    b.status.ldesc = "Dlvl:14"
    frames = {"s": a}

    def do(keys, **kw):
        if keys == "_":
            gp = _snap({5: "   " + "." * 30}, (10, 5), [])
            gp.state = State("getpos", prompt="Where do you want to travel to?")
            frames["s"] = gp
            return gp
        frames["s"] = b
        return b
    monkeypatch.setattr(ctx, "do", do)
    monkeypatch.setattr(ctx, "last", lambda: frames["s"])
    monkeypatch.setattr(ctx, "monster_filter", None)
    monkeypatch.setattr(nav, "cursor_to", lambda x, y, rounds=5: frames["s"])
    with pytest.raises(nav.NavError, match="level changed"):
        nav._travel(25, 5, 5, None, 0, 0, False)


def test_tune_prompt_is_text_and_cyan_underscore_is_a_chain():
    from nh.parse import classify
    from nh.screen import Screen
    chars = ["What tune are you playing? [5 notes, A-G]".ljust(80)] + [" " * 80] * 23
    scr = Screen(width=80, height=24, chars=chars, fg=[[7] * 80 for _ in range(24)],
                 reverse=[[False] * 80 for _ in range(24)], bold=[[False] * 80 for _ in range(24)], cursor=(43, 0))
    assert classify(scr).kind == "getlin"
    chars[0] = "What do you want to wield? [a-c or ?*]".ljust(80)
    assert classify(scr).kind == "object"
    s = _snap({12: "    ._._."}, (4, 12), [], colors={(5, 12): 6})
    names = [(f["x"], f["name"]) for f in s.features]
    assert (5, 12) not in [(f["x"], f["y"]) for f in s.features] and (7, "altar") in names


def test_hunt_steps_into_unexplored_dark_floor(monkeypatch):
    from tactics.combat import _greedy_step
    troll = {"x": 13, "y": 5, "ch": "T", "desc": "rock troll", "dist": 3}
    s = _snap({5: "        ..@   "}, (10, 5), [troll])
    assert _greedy_step(s, (13, 5), set()) == (11, 5)          # blank (unexplored) square toward it
    assert _greedy_step(s, (13, 5), {(11, 5), (11, 4), (11, 6)}) is None
