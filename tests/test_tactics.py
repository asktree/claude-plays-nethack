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
