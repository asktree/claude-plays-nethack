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
    s = _snap({5: "        ..@.  "}, (10, 5), [troll])
    assert _greedy_step(s, (13, 5), set()) == (11, 5)          # known floor toward it (the rest is dark)
    s = _snap({5: "        ..@   "}, (10, 5), [troll])
    assert _greedy_step(s, (13, 5), set()) is None             # a blank NEXT to you is rock when you can see
    s.status.conditions = ["Blind"]
    assert _greedy_step(s, (13, 5), set()) == (11, 5)          # blind: you don't see the floor next to you
    assert _greedy_step(s, (13, 5), {(11, 5), (11, 4), (11, 6)}) is None
    # never diagonally out of a doorway (a Rogue-level '+' doorway too)
    s = _snap({3: "     ---+---", 4: "     |.....|"}, (8, 3), [dict(troll, x=10, y=6)])
    s.rogue = True
    assert _greedy_step(s, (10, 6), set()) == (8, 4)


def test_bounce_risk_breather_in_line_with_wall_behind(monkeypatch):
    from tactics import combat, ctx
    monkeypatch.setattr(ctx, "game", _G())
    naga = {"x": 20, "y": 5, "ch": "N", "desc": "red naga", "dist": 10}
    s = _snap({5: "         |@.........."}, (10, 5), [naga])
    assert [d for _m, d in combat.bounce_risk(s)] == [(1, 0)]
    s2 = _snap({5: "         .@.........."}, (10, 5), [naga])
    assert combat.bounce_risk(s2) == []                       # open floor behind: no bounce
    s3 = _snap({5: "         |@.........."}, (10, 5), [dict(naga, y=7, dist=10)])
    assert combat.bounce_risk(s3) == []                       # not lined up


def test_prayer_check_counts_cursed_worn_items_and_stones(monkeypatch):
    from tactics import ctx, survival
    g = _G()
    g.history = []
    monkeypatch.setattr(ctx, "game", g)
    monkeypatch.setattr(survival, "_harness_state", lambda: {})
    s = _snap({}, (10, 5), [])
    s.status.hp, s.status.hpmax, s.status.turn, s.status.xl = 90, 90, 5000, 10
    monkeypatch.setattr(ctx, "last", lambda: s)
    assert survival.prayer_check()["trouble"] == "none"
    g.cursed_worn = ["m - a cursed +0 elven mithril-coat (being worn)"]
    r = survival.prayer_check()
    assert r["trouble"] == "minor" and "mithril" in r["reasons"][0]
    g.cursed_worn, g.cursed_stones = [], ["k - a cursed loadstone"]
    assert survival.prayer_check()["trouble"] == "none"        # a loadstone counts only once Strained
    s.status.encumbrance = "Strained"
    assert survival.prayer_check()["trouble"] == "minor"


def test_gold_note_only_with_a_bag_and_real_gold():
    from nh.game import Game, Timing
    g = Game(term=None, timing=Timing.local())
    s = _snap({5: "     .@."}, (6, 5), [])
    s.status.ldesc, s.status.gold = "Dlvl:6", 1635
    g._annotate(s)
    assert s.gold_note == ""                    # no bag known: nothing to put it in
    g.bags = ["n"]
    g._annotate(s)
    assert "$1635" in s.gold_note and "bag_put('n', '$')" in s.gold_note
    s.status.gold = 40
    g._annotate(s)
    assert s.gold_note == ""


def test_descend_goes_down_several_levels_and_stops_short(monkeypatch):
    from tactics import ctx, nav
    levels = iter(["Dlvl:6", "Dlvl:7", "Dlvl:7"])
    cur = {"s": _snap({}, (10, 5), [])}
    cur["s"].status.ldesc = "Dlvl:5"
    calls = []

    def fake_go_down(wait_pet=6, to=None):
        calls.append(to)
        s = _snap({}, (10, 5), [])
        s.status.ldesc = next(levels)
        cur["s"] = s
        return s
    monkeypatch.setattr(nav, "go_down", fake_go_down)
    monkeypatch.setattr(ctx, "last", lambda: cur["s"])
    monkeypatch.setattr(ctx, "defer_far", None)
    s = nav.descend(5)
    assert len(calls) == 3 and s.status.ldesc == "Dlvl:7"      # the third go_down stayed on Dlvl:7: stop


def test_stationary_hostiles_are_avoided_and_not_waited_for(monkeypatch):
    from tactics import ctx, nav
    monkeypatch.setattr(ctx, "game", _G())
    mold = {"x": 12, "y": 5, "ch": "F", "desc": "brown mold", "dist": 2}
    lichen = {"x": 13, "y": 5, "ch": "F", "desc": "lichen", "dist": 3}
    tame = {"x": 11, "y": 6, "ch": "F", "desc": "tame brown mold", "tame": True, "dist": 1}
    s = _snap({5: "        ........"}, (10, 5), [mold, lichen, tame])
    bad = nav.bad_squares(s)
    assert (12, 5) in bad and (13, 5) not in bad and (11, 6) not in bad


def test_pickup_says_why_nothing_was_picked_up(monkeypatch, capsys):
    from nh.parse import Menu, MenuItem, State
    from tactics import ctx, items
    monkeypatch.setattr(ctx, "game", _G())
    s = _snap({}, (10, 5), [])
    monkeypatch.setattr(ctx, "last", lambda: s)
    monkeypatch.setattr(items, "here", lambda: "You see here a tripe ration.")
    sent = []
    monkeypatch.setattr(ctx, "do", lambda keys, **kw: sent.append(keys) or s)
    assert items.pickup("blindfold") == [] and sent == []
    assert "only a tripe ration" in capsys.readouterr().out
    monkeypatch.setattr(items, "here", lambda: "You see no objects here.")
    assert items.pickup("blindfold") == [] and "no objects here" in capsys.readouterr().out
    # a pile: the menu has no match -> Esc, and the floor is listed
    menu = _snap({}, (10, 5), [])
    menu.state = State("menu", prompt="Pick up what?",
                       menu=Menu(title="Pick up what?", items=[MenuItem("a", "a tripe ration"),
                                                               MenuItem("b", "2 daggers")]))
    monkeypatch.setattr(items, "here", lambda: "Things that are here: | a tripe ration | 2 daggers")
    monkeypatch.setattr(ctx, "do", lambda keys, **kw: sent.append(keys) or (menu if keys == "," else s))
    items.pickup("blindfold")
    assert sent == [",", "<Esc>"] and "2 daggers" in capsys.readouterr().out


def test_bag_take_gold_means_coins_not_golden_potions(monkeypatch):
    from nh.parse import Menu, MenuItem, State
    from tactics import ctx, items
    monkeypatch.setattr(ctx, "game", _G())
    what = _snap({}, (10, 5), [])
    what.state = State("menu", prompt="Take out what?",
                       menu=Menu(title="Take out what?", items=[MenuItem("a", "6044 gold pieces"),
                                                                MenuItem("b", "2 golden potions"),
                                                                MenuItem("c", "a gold ring")]))
    done = _snap({}, (10, 5), [])
    sent = []
    monkeypatch.setattr(ctx, "last", lambda: done)
    monkeypatch.setattr(items, "_apply_container", lambda bag, action: what)
    monkeypatch.setattr(items, "discoveries", lambda: [])
    monkeypatch.setattr(ctx, "do", lambda keys, **kw: sent.append(keys) or (done if keys == "<CR>" else what))
    items.bag_take("D", "gold")
    assert sent == ["a", "<CR>"]


def test_discoveries_leave_no_message_dump(monkeypatch):
    from tactics import ctx, items
    monkeypatch.setattr(ctx, "game", _G())
    s = _snap({}, (10, 5), [])
    monkeypatch.setattr(ctx, "last", lambda: s)
    monkeypatch.setattr(ctx, "monster_filter", None)
    shown = _snap({}, (10, 5), [])
    shown.messages = ["Discoveries\nPotions\n  potion of paralysis (white)"]
    monkeypatch.setattr(ctx, "do", lambda keys, **kw: shown)
    assert items.discoveries() == [("potion of paralysis", "white potion")]
    assert shown.messages == []


def test_shop_greeting_and_stair_climbs_are_routine():
    import re
    from nh.kernel import DEFAULT_BENIGN
    from tactics.nav import _STAIRS_OK

    def benign(m):
        return any(p.search(m) for p in DEFAULT_BENIGN)
    assert benign('"Velkommen, p1!  Welcome to Asidonhopo\'s general store!"')
    assert benign('"Hello, Agent!  Welcome again to Izchak\'s lighting store!"')
    assert not benign('"Will you please leave your pick-axe outside?"')
    assert not benign('"Invisible customers are not welcome!"')
    stairs = [re.compile(p) for p in _STAIRS_OK]
    for m in ("You climb up the stairs.", "You descend the stairs.", "You fly down the stairs.",
              "With great effort, you climb up the stairs.", "You climb down the ladder."):
        assert any(p.search(m) for p in stairs), m
    assert not any(p.search("You have a sad feeling for a moment, then it passes.") for p in stairs)


def test_arrival_snapshot_is_reannotated_once_the_level_is_named():
    from nh.game import Game, Timing
    g = Game(term=None, timing=Timing.local())
    name = "The Dungeons of Doom / Level 18"
    g.level_flags[name] = {"rogue"}
    s = _snap({5: "     +.@.]"}, (7, 5), [{"x": 9, "y": 5, "ch": "]", "mimic": True, "desc": "mimic"}])
    s.status.ldesc = "Dlvl:18"
    g._annotate(s)                    # the arrival: filed under the provisional "Dlvl:18"
    assert not s.rogue
    g.level_name, g.level_name_ldesc = name, "Dlvl:18"      # the tracker's ^O named it
    g.reannotate(s)
    assert s.rogue and "rogue" in s.flags and s.monsters == []     # ']' is armor on the Rogue level


def test_travel_waits_for_a_peaceful_on_the_next_square(monkeypatch):
    import pytest
    from tactics import ctx, nav
    monkeypatch.setattr(ctx, "game", _G())
    monkeypatch.setattr(ctx, "monster_filter", None)
    row = {5: "        ........."}
    gnome = {"x": 11, "y": 5, "ch": "G", "desc": "peaceful gnomish wizard", "peaceful": True, "dist": 1}
    s = _snap(row, (10, 5), [gnome])
    monkeypatch.setattr(ctx, "last", lambda: s)
    sent = []
    monkeypatch.setattr(ctx, "do", lambda keys, **kw: sent.append(keys) or s)
    with pytest.raises(nav.NavError, match="stays on"):
        nav._travel(12, 5, 5, None, 3, 0, False)
    assert sent == [".", ".", "."]              # waited, never stepped into it


def test_arrival_next_to_the_stairs_moves_the_memory(monkeypatch):
    from nh.game import Game, Timing
    g = Game(term=None, timing=Timing.local())
    key = "Dlvl:17"
    s = _snap({16: "     |...@..|", 17: "     |..8...|"}, (9, 16), [])
    s.status.ldesc = key
    g.terrain_seen[key] = {(9, 16): ">"}          # recorded on arrival: you stand on the other end
    g.stair_links[key] = {(9, 16): "Dlvl:18"}
    s.under = ">"
    monkeypatch.setattr(g, "_quiet_look", lambda: "You see no objects here.")
    g._verify_arrival(s, {"n": s.n, "hero": (9, 16), "ch": ">", "old_key": "Dlvl:18"})
    assert g.terrain_seen[key] == {(8, 17): ">"} and g.stair_links[key] == {(8, 17): "Dlvl:18"}
    assert s.under is None
    # on the stairs after all: nothing changes
    g.terrain_seen[key] = {(9, 16): ">"}
    monkeypatch.setattr(g, "_quiet_look", lambda: "There is a staircase down here. You see here a dagger.")
    g._verify_arrival(s, {"n": s.n, "hero": (9, 16), "ch": ">", "old_key": "Dlvl:18"})
    assert g.terrain_seen[key] == {(9, 16): ">"}
    # two monsters next to you: #terrain decides
    s2 = _snap({16: "     |..d@..|", 17: "     |..8...|"}, (9, 16), [])
    s2.status.ldesc = key
    monkeypatch.setattr(g, "_quiet_look", lambda: "You see no objects here.")
    monkeypatch.setattr(g, "terrain_scan", lambda: {"traps": set(), "features": {(8, 17): ">", (20, 3): "<"}})
    g._verify_arrival(s2, {"n": s2.n, "hero": (9, 16), "ch": ">", "old_key": "Dlvl:18"})
    assert g.terrain_seen[key] == {(8, 17): ">"}


def test_stairs_retry_after_a_wrong_memory(monkeypatch):
    from tactics import ctx, nav

    class G(_G):
        def __init__(self):
            super().__init__()
            self.terrain_seen = {"L": {(10, 5): ">", (12, 6): ">"}}
            self.stair_links = {"L": {(10, 5): "Dlvl:6"}}

        def terrain_scan(self):
            return {"traps": set(), "features": {(12, 6): ">", (10, 5): ">"}}
    g = G()
    monkeypatch.setattr(ctx, "game", g)
    s = _snap({5: "        ..@..", 6: "        ....>"}, (10, 5), [])
    s.status.ldesc = "Dlvl:5"
    cur = {"s": s}
    monkeypatch.setattr(ctx, "last", lambda: cur["s"])
    monkeypatch.setattr(nav, "known_cells", lambda ch, s=None, rescan=False:
                        sorted((c for c, v in g.terrain_seen["L"].items() if v == ch),
                               key=lambda c: abs(c[0] - 10) + abs(c[1] - 5)))
    monkeypatch.setattr(nav, "_pick_stairs", lambda ch, cells, to, s: (cells[0], ""))
    moved = _snap({6: "        ....@"}, (12, 6), [])
    moved.status.ldesc = "Dlvl:5"
    down = _snap({}, (40, 10), [])
    down.status.ldesc = "Dlvl:6"
    sent = []

    def fake_do(keys, **kw):
        sent.append(keys)
        if keys == ">":
            if cur["s"].hero == (10, 5):
                r = _snap({5: "        ..@..", 6: "        ....>"}, (10, 5), [])
                r.status.ldesc = "Dlvl:5"
                r.messages = ["You can't go down here."]
                cur["s"] = r
                return r
            cur["s"] = down
            return down
        return cur["s"]
    monkeypatch.setattr(ctx, "do", fake_do)
    monkeypatch.setattr(nav, "travel", lambda x, y, **kw: cur.__setitem__("s", moved) or moved)
    s = nav._use_stairs(">", wait_pet=0)
    assert s.status.ldesc == "Dlvl:6" and sent == [">", ">"]
    assert (10, 5) not in g.terrain_seen["L"] and (10, 5) not in g.stair_links["L"]


def test_travel_stops_short_on_a_free_square(monkeypatch):
    from tactics import ctx, nav
    monkeypatch.setattr(ctx, "game", _G())
    monkeypatch.setattr(ctx, "monster_filter", None)
    rows = {4: "        |.....|", 5: "        |..8@.|", 6: "        |.....|"}
    ghost = {"x": 11, "y": 5, "ch": "8", "desc": "ghost", "dist": 1}
    s = _snap(rows, (12, 5), [ghost])
    cur = {"s": s}
    monkeypatch.setattr(ctx, "last", lambda: cur["s"])
    steps = []

    def fake_do(keys, **kw):
        steps.append(keys)
        return cur["s"]
    monkeypatch.setattr(ctx, "do", fake_do)
    monkeypatch.setattr(nav, "_final_step", lambda s, c: steps.append(("step", c)) or s)
    try:
        nav._travel(10, 6, 5, None, 0, 0, False)
    except nav.NavError:
        pass
    assert ("step", (11, 5)) not in steps and ("step", (11, 6)) in steps


def test_rogue_doorways_forbid_diagonal_moves():
    from tactics.mapview import bfs_path, is_door
    rows = {4: "     ---+---",
            5: "     |.....|",
            3: "        #   "}
    s = _snap(rows, (7, 5), [])
    s.rogue = True
    assert is_door(s, 8, 4)
    path = bfs_path(s, (7, 5), (8, 3))
    assert path is not None and path[0] == (8, 5) and path[1] == (8, 4)     # straight in, straight out
    s.rogue = False                                   # elsewhere a gray '+' in a wall is a doorless doorway
    assert not is_door(s, 8, 4)


def test_mysterious_force_arrival_is_not_a_staircase():
    from nh.game import Game, Timing
    g = Game(term=None, timing=Timing.local())
    cur = _snap({5: "     .@."}, (6, 5), [])
    cur.status.ldesc = "Dlvl:30"
    g.terrain_seen["Dlvl:30"] = {(6, 5): "<"}
    arr = _snap({12: "   ..@.."}, (5, 12), [])
    arr.status.ldesc = "Dlvl:32"
    g._note_arrival(cur, arr, b"<", ["A mysterious force momentarily surrounds you..."], "Dlvl:30", True)
    assert (5, 12) not in g.terrain_seen.get("Dlvl:32", {}) and not g.stair_links.get("Dlvl:30")
    g._note_arrival(cur, arr, b"<", ["You climb up the stairs."], "Dlvl:30", True)      # a real climb
    assert g.terrain_seen["Dlvl:32"][(5, 12)] == ">" and g.stair_links["Dlvl:30"][(6, 5)] == "Dlvl:32"


def test_fight_refuses_a_mind_flayer_without_a_helmet_and_skips_auto_fight_next_to_an_I(monkeypatch):
    from tactics import combat, ctx
    g = _G()
    g.helmet = ""
    monkeypatch.setattr(ctx, "game", g)
    flayer = {"x": 11, "y": 5, "ch": "h", "desc": "mind flayer", "dist": 1}
    s = _snap({5: "        ..@..."}, (10, 5), [flayer])
    s.status.xl, s.status.hp, s.status.hpmax, s.status.in_ = 14, 120, 120, 16
    monkeypatch.setattr(ctx, "last", lambda: s)
    paused, sent = [], []
    monkeypatch.setattr(ctx, "pause", lambda why: paused.append(why))
    monkeypatch.setattr(ctx, "do", lambda keys, **kw: sent.append(keys) or s)
    monkeypatch.setattr(ctx, "hp_rules", None)
    combat.fight(11, 5)
    assert paused and "NO helmet" in paused[0] and not any(k.startswith("F") for k in sent)
    # a trivial newt next to an unseen 'I': auto-fight leaves it to you
    newt = {"x": 11, "y": 5, "ch": ":", "desc": "newt", "dist": 1}
    unseen = {"x": 9, "y": 5, "ch": "I", "desc": "remembered, unseen monster", "unseen": True, "dist": 1}
    s2 = _snap({5: "        .I@:.."}, (10, 5), [newt, unseen])
    s2.status.xl, s2.status.hp, s2.status.hpmax = 14, 120, 120
    assert combat.fight_trivial(s2) is None


def test_fight_targets_the_most_dangerous_neighbour_first():
    from tactics.combat import _danger_rank
    ranked = sorted(["ghost", "lich", "newt"], key=_danger_rank)
    assert ranked[0] == "lich" and ranked[-1] == "newt"


def test_step_onto_refuses_when_not_adjacent(monkeypatch):
    import pytest
    from tactics import ctx, nav
    monkeypatch.setattr(ctx, "game", _G())
    s = _snap({5: "        ..@..^"}, (10, 5), [])
    monkeypatch.setattr(ctx, "last", lambda: s)
    with pytest.raises(nav.NavError, match="not next to it"):
        nav.step_onto(13, 5)
    steps = []
    monkeypatch.setattr(nav, "step", lambda d, **kw: steps.append((d, kw.get("force"))) or s)
    nav.step_onto(11, 5)
    assert steps == [("l", True)]
