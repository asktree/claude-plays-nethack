"""Pure parts of the tactics helpers (no game: snapshots are built by hand)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "play"))
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from nh.game import Snap  # noqa: E402
from nh.parse import State, Status  # noqa: E402
from nh.screen import Screen  # noqa: E402


from tactics import combat as _combat  # noqa: E402

_REAL_CHECK_TARGET = _combat._check_target


@pytest.fixture(autouse=True)
def _looks_confirm_labels(monkeypatch):
    """fight() looks at each target before its first blow; the fake games here draw no getpos cursor,
    so that look confirms the label (test_fight_looks_before_the_first_blow tests the look itself)."""
    from tactics import combat, ctx

    def confirm(m):
        s = ctx.last()
        return s, next((t for t in s.monsters or [] if (t["x"], t["y"]) == (m["x"], m["y"])), None)
    monkeypatch.setattr(combat, "_check_target", confirm)


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
    # standing on a corridor end: your own square ('@') counts too
    rows[8] = "               @"
    s = _snap(rows, (15, 8), [])
    assert sorted(dead_ends(s)) == [(15, 8), (18, 5)]
    # ...but not in a room
    rows[8] = "               #"
    rows[5] = "        |@..|     #"
    s = _snap(rows, (9, 5), [])
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
    # p2 shift 28: punishment is pray.c's first minor trouble (TROUBLE_PUNISHED)
    s.status.encumbrance = ""
    g.cursed_stones = []
    g.history = [(4000, "You are being punished for your misbehavior!")]
    r = survival.prayer_check()
    assert r["trouble"] == "minor" and "punished" in r["reasons"][0]
    g.history.append((4100, "Your chain disappears."))
    assert survival.prayer_check()["trouble"] == "none"
    g.history, g.punished = [], True                             # (only the last inventory() tells)
    assert survival.prayer_check()["trouble"] == "minor"
    g.punished = False
    s.status.conditions = ["Deaf"]
    assert survival.prayer_check()["trouble"] == "minor"          # timed deafness counts like blindness


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


def test_detour_passes_through_your_pet():
    from tactics.mapview import bfs_path
    rows = {17: "      #-|---", 18: "#######.F@.|", 19: "      #|d..|", 20: "      #-----"}
    rows = {y: r.rjust(len(r) + 36) for y, r in rows.items()}
    dog = {"x": 44, "y": 19, "ch": "d", "desc": "tame little dog", "tame": True, "pet": True}
    mold = {"x": 44, "y": 18, "ch": "F", "desc": "red mold"}
    s = _snap(rows, (45, 18), [dog, mold])
    assert bfs_path(s, (45, 18), (36, 18), avoid=frozenset({(44, 18)}), allow_monsters=False) is None
    p = bfs_path(s, (45, 18), (36, 18), avoid=frozenset({(44, 18)}), allow_monsters=False, allow_pets=True)
    assert p and p[0] == (44, 19) and p[1] == (43, 18)       # swap with the dog, then the doorless doorway


def test_price_id_learns_a_lowballing_shopkeeper(monkeypatch):
    from tactics import ctx, info
    g = _G()
    monkeypatch.setattr(ctx, "game", g)
    s = _snap({}, (10, 5), [])
    s.shop = "Wonotobo's general store"
    s.status.ch = 10
    monkeypatch.setattr(ctx, "last", lambda: s)
    ident = info.price_id("SCROLL_CLASS", sell=8, exclude_known=False)
    assert [b for _n, b in ident] == [20] and info.shk_rates()["Wonotobo"] == "low"
    both = {b for _n, b in info.price_id("SCROLL_CLASS", sell=30, exclude_known=False, shk="Someone else")}
    assert both == {60, 80}                                   # an unknown shopkeeper: either rate
    low = {b for _n, b in info.price_id("SCROLL_CLASS", sell=30, exclude_known=False)}
    assert low == {80}                                        # Wonotobo lowballs: base 80 only



def test_monster_rust_trap_is_not_your_trap_and_monitor_uses_the_snapshots_level():
    from nh.game import Game
    assert not Game._TRAP_MSG.search("A gush of water hits the rothe on the head!")
    assert Game._TRAP_MSG.search("A gush of water hits you on the head!")
    assert Game._TRAP_MSG.search("A gush of water hits your left arm!")


def test_hunt_steps_around_a_peaceful_in_the_way(monkeypatch):
    from tactics import combat, ctx
    g = _G()
    g.wielded = "a +2 long sword (weapon in hand)"
    monkeypatch.setattr(ctx, "game", g)
    monkeypatch.setattr(ctx, "hp_rules", None)
    rows = {4: "        ..........", 5: "        ..........", 6: "        .........."}
    gnome = {"x": 10, "y": 5, "ch": "G", "desc": "peaceful gnome lord", "peaceful": True, "dist": 1, "id": 9}
    troll = {"x": 13, "y": 5, "ch": "T", "desc": "troll", "dist": 4, "id": 3}
    s = _snap(rows, (9, 5), [gnome, troll])
    s.status.hp, s.status.hpmax, s.status.turn = 90, 90, 100
    sent = []

    def do(keys, **kw):
        sent.append(keys)
        raise RuntimeError("stop")          # one step is enough to see which way it went
    monkeypatch.setattr(ctx, "do", do)
    monkeypatch.setattr(ctx, "last", lambda: s)
    monkeypatch.setattr(ctx, "pause", lambda r: None)
    try:
        combat.hunt("troll")
    except RuntimeError:
        pass
    assert sent and sent[0] in ("u", "n")        # around the gnome lord (diagonally), not into it


def test_travel_detours_around_eel_water(monkeypatch):
    import pytest
    from tactics import ctx, nav
    monkeypatch.setattr(ctx, "game", _G())
    monkeypatch.setattr(ctx, "monster_filter", None)
    # a moat along row 7; the eel (visible) at (14,7); two ways east: along the moat (row 6) or row 4
    rows = {3: "        ...........",
            4: "        ...........",
            5: "        .---------.",
            6: "        ...........",
            7: "        }}}}}}}}}}}"}
    colors = {(x, 7): 4 for x in range(8, 19)}
    eel = {"x": 14, "y": 7, "ch": ";", "desc": "giant eel", "dist": 5}
    s = _snap(rows, (8, 6), [eel], colors=colors)
    z = nav.eel_zone(s)
    assert (14, 6) in z and (13, 6) in z and (15, 6) in z and (11, 6) not in z
    walked = {}
    monkeypatch.setattr(ctx, "last", lambda: s)
    monkeypatch.setattr(nav, "walk_path", lambda path, ok=None: walked.setdefault("p", path) and s)
    nav._travel(18, 6, 40, None, 3, None, False)
    assert walked["p"][-1] == (18, 6) and not any(c in z for c in walked["p"][:-1])
    # no other way (the wall row is closed): refused while the eel is in view
    rows[5] = "        -----------"
    s2 = _snap(rows, (8, 6), [eel], colors=colors)
    monkeypatch.setattr(ctx, "last", lambda: s2)
    sent = []
    monkeypatch.setattr(ctx, "do", lambda keys, **kw: sent.append(keys) or s2)
    with pytest.raises(nav.NavError, match="drowns you"):
        nav._travel(18, 6, 40, None, 3, None, False)
    assert sent == []
    # lava is no eel water
    s3 = _snap(rows, (8, 6), [eel], colors={(x, 7): 1 for x in range(8, 19)})
    assert set(nav.eel_zone(s3)) <= {(13, 6), (14, 6), (15, 6)}


def test_disenchanter_passive_vs_excalibur_and_battle_noise(monkeypatch):
    import re
    from tactics import combat, ctx
    g = _G()
    monkeypatch.setattr(ctx, "game", g)
    st = _snap({}, (10, 5), []).status
    st.hp, st.hpmax = 100, 100
    g.wielded = "a - a blessed rustproof +6 Excalibur (weapon in hand)"
    assert combat._ench_safe() and combat._passive_refusal("disenchanter", st) == ""
    g.wielded = "a - a +3 long sword (weapon in hand)"
    assert not combat._ench_safe() and "DISENCHANTS" in combat._passive_refusal("disenchanter", st)
    g.wielded = "a - a +0 long sword (weapon in hand)"
    assert combat._ench_safe()

    def routine(m):
        return any(re.search(p, m) for p in combat.ROUTINE)
    for m in ("The soldier thrusts a halberd.", "A halberd misses you.", "The lieutenant puts on a helmet.",
              "The soldier's short sword is welded to her hand!", "The ice troll rises from the dead!",
              "The sleep ray bounces!", "The soldier wields a dagger!",
              "The vial crashes on the soldier's head and breaks into shards."):
        assert routine(m), m
    assert not routine("The soldier wields a cockatrice corpse!")


def test_fight_until_clear_holds_the_square(monkeypatch):
    from tactics import combat, ctx
    monkeypatch.setattr(ctx, "game", _G())
    monkeypatch.setattr(ctx, "monster_filter", None)
    monkeypatch.setattr(combat, "warn_bounce", lambda who: None)
    turn = {"t": 100}

    def snap_now():
        s = _snap({5: "        ....."}, (10, 5), [])
        s.status.turn, s.status.hp, s.status.hpmax = turn["t"], 50, 50
        return s
    cur = {"s": snap_now()}
    sent = []

    def fake_do(keys, **kw):
        sent.append(keys)
        turn["t"] += 1
        cur["s"] = snap_now()
        return cur["s"]
    monkeypatch.setattr(ctx, "do", fake_do)
    monkeypatch.setattr(ctx, "last", lambda: cur["s"])
    r = combat.fight_until_clear(hold=5)
    assert r["reason"] == "held" and sent == ["s"] * 5
    sent.clear()
    assert combat.fight_until_clear()["reason"].startswith("clear") and sent == []


def test_read_identify_never_escapes_the_menu(monkeypatch):
    from nh.parse import Menu, MenuItem, State
    from tactics import ctx, items
    monkeypatch.setattr(ctx, "game", _G())
    base = _snap({}, (10, 5), [])
    obj = _snap({}, (10, 5), [])
    obj.state = State("object", prompt="What do you want to read?")
    menu = _snap({}, (10, 5), [])
    menu.state = State("menu", prompt="What would you like to identify first?",
                       menu=Menu(title="What would you like to identify first?",
                                 items=[MenuItem("", "Weapons", header=True), MenuItem("a", "a dagger"),
                                        MenuItem("", "Tools", header=True), MenuItem("b", "a bag")]))
    done = _snap({}, (10, 5), [])
    done.messages = ["b - a bag of holding."]
    frames = {"r": obj, "k": menu, "b": menu, "<CR>": done}
    sent = []
    cur = {"s": base}

    def fake_do(keys, **kw):
        sent.append(keys)
        cur["s"] = frames.get(keys, cur["s"])
        return cur["s"]
    monkeypatch.setattr(ctx, "do", fake_do)
    monkeypatch.setattr(ctx, "last", lambda: cur["s"])
    monkeypatch.setattr(ctx, "require_command", lambda who: base)
    items.read_identify("k", priority=(r"^Rings",))          # nothing matches: the default order picks
    assert "<Esc>" not in sent and sent[-2:] == ["b", "<CR>"]  # the bag (tools before weapons)


def test_hunt_follows_a_target_out_of_view(monkeypatch):
    from types import SimpleNamespace
    from tactics import combat, ctx
    g = _G()
    g.tracker = SimpleNamespace(recent={7: {"id": 7, "x": 14, "y": 5, "desc": "hill giant"}})
    monkeypatch.setattr(ctx, "game", g)
    row = {5: "        ..........."}
    giant = {"x": 14, "y": 5, "ch": "H", "desc": "hill giant", "dist": 4, "id": 7}
    pos = {"x": 10}

    def frame(with_giant):
        s = _snap(row, (pos["x"], 5), [dict(giant, dist=14 - pos["x"])] if with_giant else [])
        s.status.turn, s.status.hp, s.status.hpmax = 100 + pos["x"], 90, 90
        return s
    cur = {"s": frame(True)}
    sent = []

    def fake_do(keys, **kw):
        sent.append(keys)
        if keys == "l":
            pos["x"] += 1
        cur["s"] = frame(False)          # it went round a corner: out of view from now on
        return cur["s"]
    monkeypatch.setattr(ctx, "do", fake_do)
    monkeypatch.setattr(ctx, "last", lambda: cur["s"])
    monkeypatch.setattr(ctx, "require_command", lambda who: cur["s"])
    r = combat.hunt("hill giant")
    assert sent == ["l", "l", "l", "l"] and pos["x"] == 14       # one step while seen, then to its last square
    assert r["reason"].startswith("lost:") and "last seen at (14, 5)" in r["reason"]


def test_prayer_check_counts_wishes_and_demigod(monkeypatch):
    # zap.c makewish(): every wish adds 50-149 to the prayer timeout, which never drops below 0 before that
    from tactics import ctx, survival
    g = _G()
    g.history = []
    monkeypatch.setattr(ctx, "game", g)
    s = _snap({}, (10, 5), [])
    s.status.hp, s.status.hpmax, s.status.xl = 10, 145, 13        # low HP: major trouble
    monkeypatch.setattr(ctx, "last", lambda: s)
    hs = {"prayers": [{"turn": 18211, "outcome": "You are surrounded by a shimmering light."}],
          "wishes": [{"turn": t} for t in (20563, 20566, 20568, 20570, 20618)]}
    monkeypatch.setattr(survival, "_harness_state", lambda: hs)
    s.status.turn = 20706
    r = survival.prayer_check()
    assert r["trouble"] == "major" and r["p_safe"] < 0.05 and "5 wish(es)" in r["advice"]
    s.status.turn = 21400
    assert survival.prayer_check()["p_safe"] > 0.95
    # without the wishes the same prayer 2495 turns ago would be safe
    hs["wishes"] = []
    s.status.turn = 20706
    assert survival.prayer_check()["p_safe"] > 0.95
    # a demigod (the Wizard killed before that prayer): each prayer also adds rnz(1000)
    hs["demigod"] = {"turn": 18000}
    s.status.turn = 18211 + 800
    p_demi = survival.prayer_check()["p_safe"]
    del hs["demigod"]
    assert p_demi < survival.prayer_check()["p_safe"]


def test_dig_rewields_before_pausing(monkeypatch):
    # p2 #136: dig('>') fell into a temple and paused on its message with the pick-axe still in hand
    from nh.parse import State
    from tactics import ctx, items
    monkeypatch.setattr(ctx, "game", _G())
    monkeypatch.setattr(ctx, "monster_filter", None)
    monkeypatch.setattr(items, "inventory", lambda: [
        {"letter": "a", "text": "a blessed +6 long sword named Excalibur (weapon in hand)"},
        {"letter": "M", "text": "a pick-axe"}])

    def snap(ld, kind="command", msgs=()):
        s = _snap({}, (10, 5), [])
        s.status.ldesc, s.status.turn = ld, 100
        s.state = State(kind)
        s.messages = list(msgs)
        return s
    frames = {"a": snap("Dlvl:23", "object"), "M": snap("Dlvl:23", "direction"),
              ">": snap("Dlvl:24", msgs=["You dig a pit in the floor.", "You dig a hole through the floor.",
                                         "You fall through...", "You experience a strange sense of peace."]),
              "wa": snap("Dlvl:24", msgs=["a - a blessed +6 long sword named Excalibur (weapon in hand)."])}
    cur = {"s": snap("Dlvl:23")}
    sent, pauses = [], []

    def fake_do(keys, **kw):
        sent.append(keys)
        cur["s"] = frames[keys]
        return cur["s"]
    monkeypatch.setattr(ctx, "do", fake_do)
    monkeypatch.setattr(ctx, "last", lambda: cur["s"])
    monkeypatch.setattr(ctx, "require_command", lambda who: cur["s"])
    monkeypatch.setattr(ctx, "pause", lambda reason: pauses.append((reason, list(sent))))
    items.dig(">")
    assert sent == ["a", "M", ">", "wa"]
    assert len(pauses) == 1 and "sense of peace" in pauses[0][0] and pauses[0][1][-1] == "wa"


def test_travel_falls_back_to_head_to_without_a_known_path(monkeypatch):
    # p1 #155: NetHack's travel only guesses toward a target across never-seen dark floor
    from nh.parse import State
    from tactics import ctx, explore, nav
    monkeypatch.setattr(ctx, "game", _G())
    monkeypatch.setattr(ctx, "monster_filter", None)
    rows = {4: "        -----", 5: "        |...|", 6: "        |....", 7: "        -----"}
    s = _snap(rows, (10, 5), [])
    getpos = _snap(rows, (10, 5), [])
    getpos.state = State("getpos")
    cur = {"s": s}

    def fake_do(keys, **kw):
        cur["s"] = getpos if keys == "_" else s          # the travel command: the hero doesn't move
        return cur["s"]
    monkeypatch.setattr(ctx, "do", fake_do)
    monkeypatch.setattr(ctx, "last", lambda: cur["s"])
    monkeypatch.setattr(nav, "cursor_to", lambda x, y, rounds=5: getpos)
    called = []
    monkeypatch.setattr(explore, "head_to", lambda x, y, max_legs=30: called.append((x, y)) or s)
    assert nav._travel(40, 12, 40, None, 3, 0, False) is s
    assert called == [(40, 12)]
    assert nav._HEADING[0] is False


def test_hidden_drowners_eel_levels_and_fight_at_the_water(monkeypatch):
    # QA round 5: moats hold eels/krakens created hidden; an 'I' in the water is one of them
    from tactics import combat, ctx, nav
    g = _G()
    g.level_flags, g.water_seen = {}, {}
    monkeypatch.setattr(ctx, "game", g)
    monkeypatch.setattr(ctx, "monster_filter", None)
    rows = {5: "        ..........", 6: "        ..........", 7: "        }}}}}}}}}}", 8: "        }}}}}}}}}}"}
    colors = {(x, y): 4 for x in range(8, 18) for y in (7, 8)}
    s = _snap(rows, (10, 5), [], colors=colors)
    assert nav.eel_zone(s) == {}                       # an ordinary level, nothing seen
    g.level_flags["L"] = {"castle"}
    z = nav.eel_zone(s)
    assert (12, 6) in z and (12, 5) not in z and "may hide" in z[(12, 6)]
    # an unseen 'I' in the water next to you: a drowner
    g.level_flags["L"] = set()
    rows7 = "        }}}I}}}}}}"
    s2 = _snap({**rows, 7: rows7}, (11, 6), [{"x": 11, "y": 7, "ch": "I", "unseen": True, "dist": 1,
                                                    "desc": ""}], colors=colors)
    assert nav.drowners_adjacent(s2) and (12, 6) in nav.eel_zone(s2)
    paused = []
    monkeypatch.setattr(ctx, "last", lambda: s2)
    monkeypatch.setattr(ctx, "pause", lambda r: paused.append(r))
    monkeypatch.setattr(ctx, "do", lambda keys, **kw: (_ for _ in ()).throw(AssertionError("no blows")))
    combat.fight()
    assert paused and "WATER" in paused[0]
    s2.status.hp, s2.status.hpmax = 50, 50
    monkeypatch.setattr(combat, "warn_bounce", lambda who: None)
    r = combat.fight_until_clear()
    assert r["reason"].startswith("DROWNING RISK")


def test_squeaky_board_only_way_is_crossed(monkeypatch):
    from tactics import ctx, nav
    g = _G()
    monkeypatch.setattr(ctx, "game", g)
    monkeypatch.setattr(ctx, "monster_filter", None)
    rows = {4: "        -----", 5: "        |.^.|", 6: "        -----"}
    s = _snap(rows, (9, 5), [])
    s.feature_desc = {(10, 5): "squeaky board"}
    g.traps = {"L": {(10, 5)}}
    monkeypatch.setattr(ctx, "last", lambda: s)
    walked = []
    monkeypatch.setattr(nav, "_walk_over", lambda path, boards: walked.append((path, boards)) or s)
    nav._travel(11, 5, 40, None, 3, None, False)
    assert walked and walked[0][0][-1] == (11, 5) and (10, 5) in walked[0][1]


def test_fight_follows_a_teleporter_to_its_new_adjacent_square(monkeypatch):
    from tactics import combat, ctx
    monkeypatch.setattr(ctx, "game", _G())
    vlad1 = {"x": 11, "y": 5, "ch": "V", "desc": "Vlad the Impaler", "dist": 1, "id": 3}
    vlad2 = dict(vlad1, x=9, y=6)
    s1 = _snap({}, (10, 5), [vlad1])
    s2 = _snap({}, (10, 5), [vlad2])
    dead = _snap({}, (10, 5), [])
    dead.messages = ["You kill Vlad the Impaler!"]
    for s in (s1, s2, dead):
        s.status.hp, s.status.hpmax, s.status.xl = 200, 200, 25
    frames = iter([s2, dead])
    cur = {"s": s1}
    sent = []

    def fake_do(keys, **kw):
        sent.append(keys)
        cur["s"] = next(frames)
        return cur["s"]
    monkeypatch.setattr(ctx, "do", fake_do)
    monkeypatch.setattr(ctx, "last", lambda: cur["s"])
    monkeypatch.setattr(combat, "_wielding", lambda: True)
    combat.fight(11, 5)
    assert sent == ["Fl", "Fb"]                  # the second blow went to its new square


def test_ladder_check_reads_the_specific_description(monkeypatch):
    # QA round 5 S2: "< a staircase up or a ladder up (staircase up)" names both kinds; the part in
    # parentheses is this square's
    from tactics import ctx, nav
    g = _G()
    g.stair_links = {}
    monkeypatch.setattr(ctx, "game", g)
    s = _snap({}, (20, 10), [])
    looks = {(35, 13): "< a staircase up or a ladder up (ladder up)",
             (7, 4): "< a staircase up or a ladder up (staircase up)"}
    monkeypatch.setattr(nav, "farlook", lambda x, y: looks[(x, y)])
    cell, why = nav._pick_stairs("<", [(35, 13), (7, 4)], None, s)
    assert cell == (7, 4) and "ladder" in why


def test_mysterious_force_stops_the_script(monkeypatch):
    import pytest
    from tactics import ctx, nav
    monkeypatch.setattr(ctx, "game", _G())
    s0 = _snap({5: "        .<."}, (9, 5), [])
    s0.status.dlvl, s0.status.ldesc = 44, "Dlvl:44"
    s1 = _snap({5: "        ..."}, (30, 12), [])
    s1.status.dlvl, s1.status.ldesc = 47, "Dlvl:47"
    s1.messages = ["A mysterious force momentarily surrounds you..."]
    cur = {"s": s0}
    monkeypatch.setattr(nav, "known_cells", lambda ch, s=None, rescan=False: [(9, 5)])
    monkeypatch.setattr(ctx, "do", lambda keys, **kw: cur.__setitem__("s", s1) or s1)
    monkeypatch.setattr(ctx, "last", lambda: cur["s"])
    with pytest.raises(nav.NavError, match="MYSTERIOUS FORCE.*44 -> 47"):
        nav._use_stairs("<", wait_pet=0)


def test_eat_pattern_picks_one_corpse_and_zero_nutrition_while_satiated(monkeypatch):
    from nh.parse import State
    from tactics import ctx, items
    monkeypatch.setattr(ctx, "game", _G())
    assert items._zero_nutrition("a wraith corpse") and not items._zero_nutrition("a jackal corpse")

    def snap(kind="command", prompt=None, msgs=()):
        s = _snap({}, (10, 5), [])
        s.state = State(kind, prompt=prompt)
        s.status.hunger = "Satiated"
        s.messages = list(msgs)
        return s
    base = snap()
    frames = [snap("yn", "There is a human corpse here; eat it? [ynq] (n)"),
              snap("yn", "There is a wraith corpse here; eat it? [ynq] (n)"),
              snap("yn", "You're having a hard time getting all of it down. Continue eating? [yn] (n)"),
              snap(msgs=["You finish eating the wraith corpse.", "You feel that was a bad idea."])]
    it = iter(frames)
    sent = []
    cur = {"s": base}

    def fake_do(keys, **kw):
        sent.append((keys, kw.get("force", False)))
        cur["s"] = next(it)
        return cur["s"]
    monkeypatch.setattr(ctx, "do", fake_do)
    monkeypatch.setattr(ctx, "last", lambda: cur["s"])
    monkeypatch.setattr(ctx, "require_command", lambda who: base)
    monkeypatch.setattr(items, "here", lambda: "Things that are here:\na human corpse\na wraith corpse")
    items.eat(pattern="wraith corpse")
    assert sent == [("e", True), ("n", False), ("y", False), ("y", True)]


def test_desmap_identifies_and_routes_over_unseen_parts(monkeypatch):
    from tactics import ctx, desmap
    g = _G()
    g.traps, g.avoid = {}, {}
    monkeypatch.setattr(ctx, "game", g)
    fake = {"level": "testlev", "file": "test.des", "index": 0, "geometry": None, "features":
            [{"kind": "stair", "x": 8, "y": 2, "detail": "down"}, {"kind": "trap", "x": 5, "y": 2, "detail": "sleep gas"}],
            "rows": ["------------",
                     "|....|.....|",
                     "|....S.....|",
                     "|....|.....|",
                     "------------"]}
    monkeypatch.setattr(desmap, "_MAPS", None)
    monkeypatch.setattr(desmap, "_DATA", None)
    monkeypatch.setattr(desmap, "maps", lambda: _prep([fake]))

    def _prep(ms):
        for m in ms:
            m["_cells"] = [(x, y, desmap._MAP_CLS[ch]) for y, row in enumerate(m["rows"])
                           for x, ch in enumerate(row) if ch in desmap._MAP_CLS]
            m["w"], m["h"] = max(len(r) for r in m["rows"]), len(m["rows"])
        return ms
    # only the west room is seen (map offset (20,5)); the east room is dark / never seen
    rows = {5: "                    ------", 6: "                    |....|", 7: "                    |....|",
            8: "                    |....|", 9: "                    ------"}
    s = _snap(rows, (22, 7), [])
    monkeypatch.setattr(ctx, "last", lambda: s)
    r = desmap.identify(names="testlev", min_score=10)
    assert r and (r["ox"], r["oy"]) == (20, 5)
    feats = {f["kind"]: (f["x"], f["y"]) for f in desmap.features()}
    assert feats["stair"] == (28, 7)
    route = desmap.route(28, 7)
    assert route["path"][-1] == (28, 7) and route["secret"] == [(25, 7)]


def test_sokoban_remembers_a_hiding_mimic_on_the_route(monkeypatch):
    from tactics import ctx
    from tactics.sokoban import _sessile_on_route, _state, route
    g = _G()
    monkeypatch.setattr(ctx, "game", g)
    # a giant mimic was unmasked on the hole at (8,5); now it hides as '%' there (no monster in view)
    s = _snap({4: "   ------", 5: "   ..0..%.", 6: "   ------"}, (4, 5), [])
    s.mimic_mem = {(8, 5): "giant mimic"}
    m, sq = _sessile_on_route(s, (5, 5), ["l", "l", "l"])
    assert sq == (8, 5) and "remembered" in m["desc"]
    assert _sessile_on_route(s, (5, 5), ["l"]) is None
    # pushing the boulder left from the east side needs (6,5)... and a mimic on a stand square blocks too
    s2 = _snap({4: "   ------", 5: "   ..0%..", 6: "   ------"}, (9, 5), [])
    s2.mimic_mem = {(6, 5): "giant mimic"}
    assert _sessile_on_route(s2, (5, 5), ["h"])[1] == (6, 5)
    # the walk to a stand square never steps into it
    s3 = _snap({4: "   -------", 5: "   ...%...", 6: "   ...+...", 7: "   -------"}, (4, 5), [])
    s3.mimic_mem = {(7, 5): "giant mimic"}
    path = route(s3, (4, 5), (9, 5))
    assert path is not None
    x, y = 4, 5
    from tactics.mapview import KEY_DIR
    for k in path:
        x, y = x + KEY_DIR[k][0], y + KEY_DIR[k][1]
        assert (x, y) != (7, 5)
    # its square counts as covered when matching the board to the plan (the hole under it isn't seen)
    lv = {"rows": ["......"]}
    s4 = _snap({5: "   ..0..%."}, (4, 5), [])
    s4.mimic_mem = {(8, 5): "giant mimic"}
    boulders, traps, covered = _state(s4, lv, 3, 5)
    assert (5, 0) in covered


def test_throw_refuses_non_weapons_at_monsters(monkeypatch):
    from tactics import combat, ctx, items
    assert combat.throw_can_hit("a +0 dagger", "Weapons")
    assert combat.throw_can_hit("a gray stone", "Gems/Stones")
    assert combat.throw_can_hit("an uncursed pick-axe", "Tools")
    assert combat.throw_can_hit("2 cream pies", "Comestibles")
    assert combat.throw_can_hit("a potion of sleeping", "Potions")
    assert combat.throw_can_hit("a tripe ration", "Comestibles", "large dog")
    assert not combat.throw_can_hit("a tripe ration", "Comestibles", "soldier ant")
    assert not combat.throw_can_hit("a credit card", "Tools")
    assert not combat.throw_can_hit("a wand of striking (0:4)", "Wands")
    assert not combat.throw_can_hit("a scroll labeled FOO", "Scrolls")
    s = _snap({5: "    .....    "}, (4, 5), [{"x": 7, "y": 5, "ch": "D", "desc": "red dragon"}])
    monkeypatch.setattr(ctx, "last", lambda: s)
    monkeypatch.setattr(ctx, "require_command", lambda who: s)
    paused, sent = [], []
    monkeypatch.setattr(ctx, "pause", lambda msg: paused.append(msg))
    monkeypatch.setattr(ctx, "do", lambda keys, **kw: sent.append(keys) or s)
    monkeypatch.setattr(items, "inventory", lambda: [
        {"letter": "q", "text": "a credit card", "class": "Tools", "buc": ""},
        {"letter": "d", "text": "4 +0 daggers", "class": "Weapons", "buc": ""}])
    combat.throw("q", "l")
    assert paused and "ALWAYS miss" in paused[0] and sent == []
    paused.clear()
    combat.throw("q", "l", force=True)         # (the fake game never shows the item prompt)
    assert not any("ALWAYS miss" in p for p in paused) and sent[:1] == ["t"]
    paused.clear()
    sent.clear()
    combat.throw("d", "l")                      # daggers: thrown
    assert not any("ALWAYS miss" in p for p in paused) and sent[:1] == ["t"]


def test_desmap_walk_fights_trivial_neighbours(monkeypatch):
    from tactics import combat, ctx, desmap, nav
    g = _G()
    monkeypatch.setattr(ctx, "game", g)
    newt = {"x": 23, "y": 7, "ch": ":", "desc": "newt", "dist": 1}
    cur = {"s": _snap({}, (22, 7), [newt])}
    cur["s"].hostiles = lambda radius=None: [newt] if cur["s"].monsters else []
    monkeypatch.setattr(ctx, "last", lambda: cur["s"])
    fought, walked = [], []

    def fake_fight_trivial(s=None):
        fought.append(1)
        cur["s"] = _snap({}, (22, 7), [])
        cur["s"].hostiles = lambda radius=None: []
        return cur["s"]

    def fake_walk_path(cells):
        walked.append(list(cells))
        cur["s"] = _snap({}, tuple(cells[-1]), [])
        cur["s"].hostiles = lambda radius=None: []
        return cur["s"]
    monkeypatch.setattr(combat, "fight_trivial", fake_fight_trivial)
    monkeypatch.setattr(nav, "walk_path", fake_walk_path)
    monkeypatch.setattr(desmap, "route", lambda x, y, **kw: {"path": [(23, 7), (24, 7)], "secret": [], "traps": []})
    s = desmap.walk(24, 7)
    assert fought == [1] and walked == [[(23, 7), (24, 7)]] and s.hero == (24, 7)
    # fight=False: never fights — and never walks on beside a hostile either (QA round 7)
    fought.clear()
    walked.clear()
    cur["s"] = _snap({}, (22, 7), [newt])
    cur["s"].hostiles = lambda radius=None: [newt]
    desmap.walk(24, 7, fight=False)
    assert fought == [] and walked == []
    # a non-trivial neighbour: stops without fighting even with fight=True
    lich = {"x": 23, "y": 7, "ch": "L", "desc": "master lich", "dist": 1}
    cur["s"] = _snap({}, (22, 7), [lich])
    cur["s"].hostiles = lambda radius=None: [lich]
    monkeypatch.setattr(combat, "fight_trivial", lambda s=None: None)
    desmap.walk(24, 7)
    assert walked == []


def test_travel_pass_hostile_walks_past_a_sleeper(monkeypatch):
    import pytest
    from tactics import ctx, nav
    monkeypatch.setattr(ctx, "game", _G())
    monkeypatch.setattr(ctx, "monster_filter", None)
    rows = {4: "        ..........", 5: "        ..........", 6: "        .........."}
    nymph = {"x": 10, "y": 4, "ch": "n", "desc": "wood nymph", "dist": 1}
    s = _snap(rows, (10, 5), [nymph])
    getpos = _snap(rows, (10, 5), [nymph])
    getpos.state = State("getpos")
    cur = {"s": s}
    monkeypatch.setattr(ctx, "last", lambda: cur["s"])
    monkeypatch.setattr(ctx, "do", lambda keys, **kw: getpos if keys == "_" else s)   # lookaround(): no move
    monkeypatch.setattr(nav, "cursor_to", lambda x, y, rounds=5: getpos)
    with pytest.raises(nav.NavError, match="pass_hostile=True"):
        nav._travel(16, 5, 40, None, 3, 0, False)
    walked = []

    def fake_walk(path, ok=None):
        walked.append(list(path))
        cur["s"] = _snap(rows, (16, 5), [])
        return cur["s"]
    monkeypatch.setattr(nav, "walk_path", fake_walk)
    r = nav._travel(16, 5, 40, None, 3, 0, False, pass_hostile=True)
    assert walked and (10, 4) not in walked[0] and r.hero == (16, 5)


def test_fight_stops_once_out_of_the_engulfer(monkeypatch):
    from tactics import combat, ctx
    monkeypatch.setattr(ctx, "game", _G())
    monkeypatch.setattr(ctx, "hp_rules", None)
    inside = _snap({}, (10, 5), [])
    inside.engulfed = True
    hulk = {"x": 11, "y": 5, "ch": "U", "desc": "umber hulk", "dist": 1}
    out = _snap({5: "         ...."}, (10, 5), [hulk])
    out.messages = ["You kill the lurker above!"]
    for s in (inside, out):
        s.status.hp, s.status.hpmax, s.status.xl = 100, 139, 12
    cur = {"s": inside}
    sent = []

    def fake_do(keys, **kw):
        sent.append(keys)
        cur["s"] = out
        return out
    monkeypatch.setattr(ctx, "do", fake_do)
    monkeypatch.setattr(ctx, "last", lambda: cur["s"])
    monkeypatch.setattr(combat, "_wielding", lambda: True)
    combat.fight(max_blows=6)
    assert sent == ["Fk"]                        # one blow inside; the umber hulk outside is not attacked


def test_fight_worst_case_on_elbereth_counts_only_ignorers(monkeypatch):
    from tactics import combat, ctx
    g = _G()
    g.on_elbereth = lambda s, cell=None: True
    monkeypatch.setattr(ctx, "game", g)
    monkeypatch.setattr(ctx, "hp_rules", None)
    monkeypatch.setattr(combat, "_wielding", lambda: True)
    dragon = {"x": 11, "y": 5, "ch": "D", "desc": "green dragon", "dist": 1}
    giant = {"x": 9, "y": 5, "ch": "H", "desc": "storm giant", "dist": 1}
    soldier = {"x": 10, "y": 4, "ch": "@", "desc": "soldier", "dist": 1}
    s = _snap({}, (10, 5), [dragon, giant, soldier])
    s.status.hp, s.status.hpmax, s.status.xl = 40, 139, 12
    paused, sent = [], []
    monkeypatch.setattr(ctx, "last", lambda: s)
    monkeypatch.setattr(ctx, "pause", lambda r: paused.append(r))
    monkeypatch.setattr(ctx, "do", lambda keys, **kw: sent.append(keys) or s)
    combat.fight(10, 4, max_blows=1)             # the soldier ignores Elbereth; the dragon and giant are scared
    assert not any("disengage" in p for p in paused)
    g.on_elbereth = lambda s, cell=None: False    # no Elbereth: all three count
    paused.clear()
    combat.fight(10, 4, max_blows=1)
    assert any("disengage" in p for p in paused)


def test_burn_elbereth_skips_empty_wands_and_verifies(monkeypatch):
    from tactics import ctx, items, survival
    g = _G()
    monkeypatch.setattr(ctx, "game", g)
    base = _snap({}, (10, 5), [])
    obj = _snap({}, (10, 5), [])
    obj.state = State("object", prompt="What do you want to write with? [- gly or ?*]")
    worn = _snap({}, (10, 5), [])
    worn.messages = ["The wand is too worn out to engrave."]
    add = _snap({}, (10, 5), [])
    add.state = State("yn", prompt="Do you want to add to the current engraving? [ynq] (y)")
    getlin = _snap({}, (10, 5), [])
    getlin.state = State("getlin", prompt="What do you want to burn into the floor here?")
    done = _snap({}, (10, 5), [])
    done.messages = ["Flames fly from the wand."]
    flow = {("E", 0): obj, ("g", 0): worn, ("E", 1): obj, ("l", 1): add, ("n", 1): getlin,
            ("Elbereth<CR>", 1): done}
    cur = {"s": base, "try": 0}
    sent = []

    def fake_do(keys, **kw):
        sent.append(keys)
        nxt = flow[(keys, cur["try"])]
        if nxt is worn:
            cur["try"] = 1
        cur["s"] = nxt
        return nxt
    monkeypatch.setattr(ctx, "do", fake_do)
    monkeypatch.setattr(ctx, "last", lambda: cur["s"])
    monkeypatch.setattr(ctx, "require_command", lambda who: base)
    monkeypatch.setattr(items, "inventory", lambda: [
        {"letter": "g", "text": "a wand of fire", "class": "Wands", "buc": ""},
        {"letter": "l", "text": "a wand of fire", "class": "Wands", "buc": ""},
        {"letter": "m", "text": "a wand of fire (0:0)", "class": "Wands", "buc": ""},
        {"letter": "y", "text": "a wand of lightning (0:5)", "class": "Wands", "buc": ""}])
    monkeypatch.setattr(survival, "engraving_here",
                        lambda: 'Something is burned into the floor here. You read: "Elbereth".')
    r = survival.burn_elbereth(wands=["g", "l"])
    assert r["ok"] and r["wand"] == "l" and r["empty"] == ["g"] and "g" in g.empty_wands
    assert sent == ["E", "g", "E", "l", "n", "Elbereth<CR>"]
    # default choice: identified fire wands only (not lightning), skipping the ones known empty: 'g' (it
    # said so above) and 'm' ("(0:0)") -> just 'l'
    cur["s"], cur["try"] = base, 1
    sent.clear()
    r = survival.burn_elbereth()
    assert sent[:2] == ["E", "l"] and r["ok"]
    # blind: refused
    blind = _snap({}, (10, 5), [])
    blind.status.conditions = ["Blind"]
    monkeypatch.setattr(ctx, "require_command", lambda who: blind)
    paused = []
    monkeypatch.setattr(ctx, "pause", lambda m: paused.append(m))
    sent.clear()
    r = survival.burn_elbereth()
    assert not r["ok"] and paused and "garbled" in paused[0] and sent == []


def test_stairs_prefer_reachable_and_fall_back_when_unreachable(monkeypatch):
    # QA round 6 #133: outside the sealed Wizard's Tower, go_down() took the tower's ladder (its destination
    # was known, "stays in Gehennom") and never tried the level's real '>'
    import pytest
    from tactics import ctx, nav
    g = _G()
    monkeypatch.setattr(ctx, "game", g)
    g.level_key = lambda status=None: "Gehennom / Level 31"
    g.stair_links = {"Gehennom / Level 31": {(12, 3): "Gehennom / Level 32"}}
    # the ladder (12,3) sits inside walls; the real '>' (20,5) is on open floor
    rows = {2: "          -----        ", 3: "          |.>|        ", 4: "          -----        ",
            5: "     @..............>  "}
    s = _snap(rows, (5, 5), [])
    s.status.ldesc = "Dlvl:31"
    cur = {"s": s}
    monkeypatch.setattr(ctx, "last", lambda: cur["s"])
    monkeypatch.setattr(nav, "known_cells", lambda ch, s=None, rescan=False: [(12, 3), (20, 5)])
    tried = []

    def fake_travel(x, y, **kw):
        tried.append((x, y))
        raise nav.NavError("stop here")              # (the test only looks at which target it chose)
    monkeypatch.setattr(nav, "travel", fake_travel)
    with pytest.raises(nav.NavError):
        nav._use_stairs(">", wait_pet=0)
    assert tried == [(20, 5)]
    # nothing reachable on the known map: the known one first, then the other when it proves unreachable
    rows2 = {2: "          -----        ", 3: "          |.>|        ", 4: "          -----        ",
             5: "     @..    .......>   "}
    s2 = _snap(rows2, (5, 5), [])
    s2.status.ldesc = "Dlvl:31"
    cur["s"] = s2
    monkeypatch.setattr(nav, "known_cells", lambda ch, s=None, rescan=False: [(12, 3), (19, 5)])
    tried.clear()

    def fake_travel2(x, y, **kw):
        tried.append((x, y))
        if (x, y) == (12, 3):
            raise nav.NavError("head_to(12, 3): no reachable frontier left (tried 3)")
        raise nav.NavError("stop here")
    monkeypatch.setattr(nav, "travel", fake_travel2)
    with pytest.raises(nav.NavError, match="stop here"):
        nav._use_stairs(">", wait_pet=0)
    assert tried == [(12, 3), (19, 5)]


def test_desmap_route_unseen_secret_doors_and_filler_traps(monkeypatch):
    import pytest
    from tactics import ctx, desmap
    g = _G()
    g.traps, g.avoid = {}, {}
    monkeypatch.setattr(ctx, "game", g)
    fake = {"level": "testlev2", "file": "test.des", "index": 0, "geometry": None, "features": [],
            "rows": ["------------",
                     "|....|.....|",
                     "|....|.....S",
                     "|....|.....|",
                     "------------"]}

    def _prep(ms):
        for m in ms:
            m["_cells"] = [(x, y, desmap._MAP_CLS[ch]) for y, row in enumerate(m["rows"])
                           for x, ch in enumerate(row) if ch in desmap._MAP_CLS]
            m["w"], m["h"] = max(len(r) for r in m["rows"]), len(m["rows"])
        return ms
    monkeypatch.setattr(desmap, "_MAPS", None)
    monkeypatch.setattr(desmap, "_DATA", None)
    monkeypatch.setattr(desmap, "maps", lambda: _prep([fake]))
    # seen: the east room (map offset (20,5)), and a corridor with a trap outside the map to the east
    # (the east wall's secret door at (31,7) was never seen: blank)
    rows = {5: "                         -------       ", 6: "                         |.....|       ",
            7: "                         |..... ##^#.  ", 8: "                         |.....|       ",
            9: "                         -------       "}
    s = _snap(rows, (28, 7), [])
    monkeypatch.setattr(ctx, "last", lambda: s)
    monkeypatch.setattr(desmap, "_current", lambda s=None, names=None: (
        _prep([fake])[0], {"ox": 20, "oy": 5, "good": 30, "bad": 0}))
    r = desmap.route(36, 7)
    assert (31, 7) in r["path"] and r["secret"] == [(31, 7)] and (34, 7) in r["traps"]
    # a goal walled off with no water around: no water hint
    with pytest.raises(RuntimeError) as e:
        desmap.route(50, 15)
    assert "allow_water" not in str(e.value)


def test_render_groups_far_unseen_markers():
    from nh.render import monsters_line
    s = _snap({}, (10, 5), [])
    mons = [{"ch": "I", "x": 20 + i, "y": 8, "dist": 10 + i, "desc": "remembered, unseen monster", "unseen": True,
             "note": "an unseen monster was here", "pet": False, "color": 7} for i in range(5)]
    mons.append({"ch": "d", "x": 11, "y": 5, "dist": 1, "desc": "jackal", "pet": False, "color": 3})
    txt = monsters_line(s, mons=mons)
    assert "I x5 remembered unseen monsters" in txt and txt.count("an unseen monster was here") == 0
    assert "jackal" in txt


def test_desmap_identifies_a_dark_level_from_a_few_squares(monkeypatch):
    # p1 shift 26: Juiblex's swamp is dark; from a 3x3 view the free slide can't place it, but the level
    # generator puts every map at a fixed spot (sp_lev.c spo_map), here offset (14,4)
    from tactics import ctx, desmap
    g = _G()
    g.level_key = lambda status=None: "Gehennom / Level 30"
    monkeypatch.setattr(ctx, "game", g)
    monkeypatch.setattr(desmap, "_MAPS", None)
    m = next(mm for mm in desmap.maps() if mm["level"] == "juiblex" and mm["index"] == 2)
    assert desmap.fixed_offset(m) == (14, 4)
    castle = next(mm for mm in desmap.maps() if mm["level"] == "castle")
    assert desmap.fixed_offset(castle) == (8, 4)
    valley = next(mm for mm in desmap.maps() if mm["level"] == "valley")
    assert desmap.fixed_offset(valley) == (2, 2)
    # draw 4x4 squares of the swamp around a spot with water and floor, everything else unseen
    rows = {y: [" "] * 80 for y in range(24)}
    cx, cy = 30, 8
    colors = {}
    for y in range(cy - 2, cy + 2):
        for x in range(cx - 2, cx + 2):
            ch = m["rows"][y - 4][x - 14] if 0 <= y - 4 < len(m["rows"]) and 0 <= x - 14 < len(m["rows"][y - 4]) else " "
            rows[y][x] = {"}": "}", ".": ".", "-": "-", "|": "|"}.get(ch, " ")
            if ch == "}":
                colors[(x, y)] = 4
    s = _snap({y: "".join(r) for y, r in rows.items()}, (cx, cy), [], colors=colors)
    seen = desmap._screen_cls(s)
    assert 6 <= len(seen) <= 16
    r = desmap.identify(s=s, remember=False)
    assert r is not None and r["level"] == "juiblex" and r["index"] == 2 and (r["ox"], r["oy"]) == (14, 4)
    assert r.get("fixed") and not r.get("ambiguous")


def test_travel_names_the_known_trap_on_the_only_route(monkeypatch):
    import pytest
    from tactics import ctx, nav
    g = _G()
    g.traps = {"L": {(14, 5)}}
    monkeypatch.setattr(ctx, "game", g)
    monkeypatch.setattr(ctx, "monster_filter", None)
    rows = {4: "        ---------------", 5: "        |.....^.......|", 6: "        ---------------"}
    s = _snap(rows, (10, 5), [])
    s.feature_desc = {(14, 5): "sleeping gas trap"}
    monkeypatch.setattr(ctx, "last", lambda: s)
    sent = []
    monkeypatch.setattr(ctx, "do", lambda keys, **kw: sent.append(keys) or s)
    with pytest.raises(nav.NavError, match="sleeping gas trap"):
        nav._travel(20, 5, 40, None, 3, 0, False)
    assert sent == []


def test_desmap_skips_unique_levels_placed_elsewhere(monkeypatch):
    from tactics import ctx, desmap
    g = _G()
    g.level_key = lambda status=None: "Gehennom / Level 34"
    g.desmap_ids = {"Gehennom / Level 28": {"level": "asmodeus", "index": 0, "ox": 1, "oy": 1}}
    monkeypatch.setattr(ctx, "game", g)
    monkeypatch.setattr(desmap, "_MAPS", None)
    seen_levels = []
    real = desmap._identify_fixed

    def spy(cands, seen):
        seen_levels.extend(m["level"] for m in cands)
        return real(cands, seen)
    monkeypatch.setattr(desmap, "_identify_fixed", spy)
    s = _snap({}, (10, 5), [])
    desmap.identify(s=s, remember=False)
    assert seen_levels and "asmodeus" not in seen_levels and "juiblex" in seen_levels


def test_squeaky_board_crossing_next_to_eel_water_is_refused(monkeypatch):
    # QA round 7 R7-1: go_up() crossed a board next to a kraken moat — the board branch skipped the eel check
    import pytest
    from tactics import ctx, nav
    g = _G()
    monkeypatch.setattr(ctx, "game", g)
    monkeypatch.setattr(ctx, "monster_filter", None)
    rows = {4: "        -----", 5: "        |.^.|", 6: "        -}}}-"}
    kraken = {"x": 10, "y": 6, "ch": ";", "desc": "kraken", "dist": 1}
    s = _snap(rows, (9, 5), [kraken], colors={(x, 6): 4 for x in range(9, 12)})
    s.feature_desc = {(10, 5): "squeaky board"}
    g.traps = {"L": {(10, 5)}}
    monkeypatch.setattr(ctx, "last", lambda: s)
    walked = []
    monkeypatch.setattr(nav, "_walk_over", lambda path, boards: walked.append((path, boards)) or s)
    with pytest.raises(nav.NavError, match="kraken"):
        nav._travel(11, 5, 40, None, 3, None, False)
    assert walked == []
    nav._travel(11, 5, 40, None, 3, None, False, near_water=True)       # on purpose: crosses
    assert walked


def test_fight_hits_the_holder_first_even_with_an_old_label(monkeypatch):
    # QA round 7 R7-7: held by an owlbear (labelled before the grab), fight_until_clear swung at a gremlin
    from tactics import combat, ctx
    g = _G()
    g.history = [(100, "The owlbear grabs you!")]
    monkeypatch.setattr(ctx, "game", g)
    monkeypatch.setattr(ctx, "hp_rules", None)
    monkeypatch.setattr(combat, "_wielding", lambda: True)
    owl = {"x": 11, "y": 5, "ch": "Y", "desc": "owlbear", "dist": 1}
    grem = {"x": 9, "y": 5, "ch": "g", "desc": "gremlin", "dist": 1, "note": "steals intrinsics"}
    s = _snap({}, (10, 5), [grem, owl])
    s.status.hp, s.status.hpmax, s.status.xl = 100, 100, 20
    sent = []
    monkeypatch.setattr(ctx, "last", lambda: s)
    monkeypatch.setattr(ctx, "pause", lambda m: None)

    def fake_do(keys, **kw):
        sent.append(keys)
        raise RuntimeError("stop")
    monkeypatch.setattr(ctx, "do", fake_do)
    try:
        combat.fight(max_blows=1)
    except RuntimeError:
        pass
    assert sent and sent[0] == "Fl"             # the owlbear to the east, not the gremlin


def test_graves_are_walkable_not_walls():
    # p3 shift 9 #663: path_to() treated graves ('|', bright white) as walls
    from tactics.mapview import bfs_path, is_walkable, is_wall
    rows = {4: "        -------", 5: "        |.|.|.|", 6: "        |.....|", 7: "        -------"}
    s = _snap(rows, (9, 5), [], colors={(10, 5): 15, (12, 5): 15})
    assert is_walkable(s, 10, 5) and not is_wall(s, 10, 5)
    assert not is_walkable(s, 8, 5) and is_wall(s, 8, 5)
    p = bfs_path(s, (9, 5), (13, 5), allow_monsters=True)
    assert p is not None and len(p) == 4        # straight along row 5 over the graves


def test_hunt_keeps_away_from_eel_water(monkeypatch):
    # p2 shift 25 #131: hunt() walked beside the Castle moat with a giant eel adjacent
    from tactics import combat, ctx
    g = _G()
    monkeypatch.setattr(ctx, "game", g)
    monkeypatch.setattr(ctx, "hp_rules", None)
    # the only way east runs along the moat (row 6); the eel sits in it
    rows = {5: "        ---------------", 6: "        |.............|", 7: "        }}}}}}}}}}}}}}}"}
    colors = {(x, 7): 4 for x in range(8, 23)}
    eel = {"x": 14, "y": 7, "ch": ";", "desc": "giant eel", "dist": 5}
    troll = {"x": 20, "y": 6, "ch": "T", "desc": "troll", "dist": 11, "id": 5}
    s = _snap(rows, (9, 6), [eel, troll], colors=colors)
    s.status.hp, s.status.hpmax, s.status.xl, s.status.turn = 100, 100, 14, 500
    monkeypatch.setattr(ctx, "last", lambda: s)
    monkeypatch.setattr(ctx, "require_command", lambda who: s)
    sent = []
    monkeypatch.setattr(ctx, "do", lambda keys, **kw: sent.append(keys) or s)
    r = combat.hunt("troll", max_turns=2)
    assert r["reason"].startswith("blocked: the only way") and "giant eel" in r["reason"] and sent == []


def test_fight_looks_before_the_first_blow(monkeypatch):
    # p2 shift 26 #411: an F blow never asks "Really attack?" (uhitm.c attack_checks) — a peaceful black naga
    # labeled like the hostile hatchlings beside it was hit. fight() now looks first.
    from tactics import combat, ctx, nav
    monkeypatch.setattr(combat, "_check_target", _REAL_CHECK_TARGET)
    monkeypatch.setattr(ctx, "game", _G())
    monkeypatch.setattr(ctx, "hp_rules", None)
    monkeypatch.setattr(combat, "_wielding", lambda: True)
    naga = {"x": 11, "y": 5, "ch": "N", "desc": "black naga hatchling", "dist": 1, "id": 7}
    s = _snap({}, (10, 5), [naga])
    s.status.hp, s.status.hpmax, s.status.xl = 100, 100, 13
    cur = {"s": s}
    monkeypatch.setattr(ctx, "last", lambda: cur["s"])
    looks, sent, paused = [], [], []

    def look(x, y):
        looks.append((x, y))
        for m in cur["s"].monsters:
            if (m["x"], m["y"]) == (x, y):
                m.update(desc="peaceful black naga", peaceful=True, looked=True)
        return "N   a naga (peaceful black naga) [seen: normal vision]"
    monkeypatch.setattr(nav, "farlook", look)
    monkeypatch.setattr(ctx, "pause", lambda msg: paused.append(msg))

    def fake_do(keys, **kw):
        sent.append(keys)
        return cur["s"]
    monkeypatch.setattr(ctx, "do", fake_do)
    combat.fight(11, 5)
    assert looks == [(11, 5)] and sent == []
    assert paused and "NOT attacking" in paused[0] and "black naga hatchling" in paused[0]
    # a hostile confirmed by the look gets its blows; a label from this turn's look needs no second look
    looks.clear()
    paused.clear()
    naga2 = {"x": 11, "y": 5, "ch": "N", "desc": "black naga hatchling", "dist": 1, "id": 8}
    s2 = _snap({}, (10, 5), [naga2])
    s2.status.hp, s2.status.hpmax, s2.status.xl = 100, 100, 13
    dead = _snap({}, (10, 5), [])
    dead.messages = ["You kill the black naga hatchling!"]
    dead.status.hp, dead.status.hpmax, dead.status.xl = 100, 100, 13
    cur["s"] = s2
    monkeypatch.setattr(nav, "farlook", lambda x, y: looks.append((x, y)) or "N  (black naga hatchling)")

    def blow(keys, **kw):
        sent.append(keys)
        cur["s"] = dead
        return dead
    monkeypatch.setattr(ctx, "do", blow)
    combat.fight(11, 5)
    assert looks == [(11, 5)] and sent == ["Fl"] and not paused
    sent.clear()
    looks.clear()
    fresh = dict(naga2, looked=True)
    cur["s"] = _snap({}, (10, 5), [fresh])
    cur["s"].status.hp, cur["s"].status.hpmax, cur["s"].status.xl = 100, 100, 13
    combat.fight(11, 5)
    assert looks == [] and sent == ["Fl"]


def test_explore_verdict_names_a_trap_with_unseen_ground_beyond(monkeypatch):
    # p1 shift 28 #1445: the only way east crossed the known sleeping gas trap; explore() said "explored"
    from tactics import ctx, explore
    g = _G()
    g.visited = {}
    monkeypatch.setattr(ctx, "game", g)
    rows = {5: "        |......^   ",
            4: "        --------   ",
            6: "        --------   "}
    s = _snap(rows, (10, 5), [])
    assert explore._trap_frontiers(s, {(15, 5)}) == [(15, 5)]
    assert explore._trap_frontiers(s, {(12, 5)}) == []          # nothing unseen next to it
    g.visited = {g.level_key(s.status): {(16, 4)}}               # stood next to that blank: seen rock
    assert explore._trap_frontiers(s, {(15, 5)}) == []


def test_special_room_is_remembered_and_kept_out(monkeypatch):
    # p3 shift 10 #587: "You enter an anthole!" comes ONCE per room (hack.c makes it an ordinary room);
    # explore then walked in through its second doorway
    from nh.game import Game, Timing
    from tactics import ctx, nav
    rows = {10: "  ---------",
            11: "  |.......|",
            12: "  |.......|",
            13: "  |........##",
            14: "  |.......|",
            15: "  |........##",
            16: "  ---------"}
    g = Game(term=None, timing=Timing.local())
    s = _snap(rows, (10, 13), [])
    s.status = Status(ok=True, ldesc="Dlvl:18", dlvl=18, turn=500)
    g._note_special_room(s, ["You enter an anthole!"], prev_hero=(11, 13))
    assert "anthole" in s.room_note and "ONCE" in s.room_note
    key = g.level_key(s.status)
    assert g.special_rooms[key][(10, 13)]["kind"] == "anthole"
    s2 = _snap(rows, (11, 13), [])
    s2.status = s.status
    g._note_special_room(s2, ["You enter an anthole!"], prev_hero=(12, 13))   # the same doorway again
    assert list(g.special_rooms[key]) == [(10, 13)]
    cells = nav._room_cells(s, (10, 13), (11, 13))
    assert (5, 12) in cells and (9, 15) in cells and (10, 15) in cells        # the floor and the 2nd doorway
    assert (11, 15) not in cells and (12, 13) not in cells                    # the corridors outside
    g2 = _G()
    g2.special_rooms = {"L": {(10, 13): {"kind": "anthole", "prev": (11, 13), "turn": 500}}}
    monkeypatch.setattr(ctx, "game", g2)
    out = _snap(rows, (12, 15), [])
    out.room_mem = dict(g2.special_rooms["L"])
    zone = nav.special_room_zone(out)
    assert zone.get((10, 15)) == "anthole" and (5, 12) in nav.bad_squares(out)
    inside = _snap(rows, (5, 12), [])
    inside.room_mem = dict(g2.special_rooms["L"])
    assert nav.special_room_zone(inside) == {}                               # in it: free to walk out
    monkeypatch.setattr(ctx, "last", lambda: out)
    assert nav.forget_room() == [] and nav.special_room_zone(out) == {}


def test_levitation_route_crosses_water_and_unseen_squares(monkeypatch):
    # p2 shift 26 #366: NetHack's travel plans only over seen squares; levitating, water is a road
    import pytest
    from tactics import ctx, nav
    monkeypatch.setattr(ctx, "game", _G())
    rows = {4: "  ------------------",
            5: "  |....}}}}}}}}....|",
            6: "  |....}}}  }}}....|",
            7: "  |....}}}}}}}}....|",
            8: "  ------------------"}
    s = _snap(rows, (4, 6), [])
    s.status = Status(ok=True, ldesc="Dlvl:24", turn=100, conditions=["Lev"])
    path = nav._lev_path(s, (4, 6), (16, 6))
    assert path and path[-1] == (16, 6) and len(path) == 12
    assert nav._lev_path(s, (4, 6), (16, 6), avoid={(c, y) for c in range(7, 15) for y in (5, 6, 7)}) is None
    kraken = {"x": 11, "y": 5, "ch": ";", "desc": "kraken", "dist": 7}
    s.monsters = [kraken]
    zone = nav._lev_drowner_zone(s)
    assert (10, 6) in zone and (12, 4) in zone and (4, 6) not in zone
    s.status = Status(ok=True, ldesc="Dlvl:24", turn=100, conditions=[])
    monkeypatch.setattr(ctx, "last", lambda: s)
    with pytest.raises(nav.NavError, match="not levitating"):
        nav.levitate_to(16, 6)


def test_bag_of_holding_explosion_guard():
    # pickup.c mbag_explodes(): a bag of holding/tricks or a charged wand of cancellation destroys a bag of holding
    from tactics.items import _boh_risk
    assert "EXPLODE" in _boh_risk("a bag of holding", "a wand of cancellation (0:5)")
    assert _boh_risk("a bag of holding", "a wand of cancellation (0:0)") == ""       # an empty one is harmless
    assert "EXPLODE" in _boh_risk("a bag of holding", "a bag of tricks (0:10)")
    assert "EXPLODE" in _boh_risk("an uncursed bag", "a bag of holding")
    assert "unidentified bag" in _boh_risk("a bag of holding", "an uncursed bag")
    assert "CANCELLATION" in _boh_risk("a bag of holding", "an oak wand")
    assert _boh_risk("a bag of holding", "an oak wand called teleport") == ""
    assert "CANCELLATION" in _boh_risk("a bag of holding", "an oak wand called vanish")
    assert _boh_risk("a bag of holding", "a wand of digging (0:4)") == ""
    assert _boh_risk("an oilskin sack", "an oak wand") == ""                          # not a bag of holding
    assert _boh_risk("a sack", "a bag of holding") == ""
    assert _boh_risk("a bag of holding", "3 uncursed potions of healing") == ""


def test_trap_crossing_policy_and_trek(monkeypatch):
    # p1 shift 29: explore/travel never crossed known minor traps; trek() (p1's helper, built in) does
    from tactics import ctx, nav
    g = _G()
    g.intrinsics = {"cold"}
    g.magic_res = False
    g.feature_desc = {"L": {(12, 5): "dart trap", (14, 5): "magic trap"}}
    g.traps = {"L": {(12, 5), (14, 5)}}
    monkeypatch.setattr(ctx, "game", g)
    st = Status(ok=True, hp=100, hpmax=100)
    assert nav.trap_crossable("squeaky board", st) and nav.trap_crossable("arrow trap", st)
    assert not nav.trap_crossable("dart trap", st)                  # no poison resistance: 1/180 death per hit
    assert not nav.trap_crossable("level teleporter", st) and not nav.trap_crossable("magic trap", st)
    g.intrinsics.add("poison")
    g.magic_res = True
    assert nav.trap_crossable("dart trap", st) and nav.trap_crossable("level teleporter", st)
    assert not nav.trap_crossable("fire trap", st) and not nav.trap_crossable("land mine", st)
    assert not nav.trap_crossable("rolling boulder trap", Status(ok=True, hp=30, hpmax=100))
    rows = {4: "        ----------",
            5: "        |..^.^..|",
            6: "        ----------"}
    cur = {"s": _snap(rows, (10, 5), [])}
    cur["s"].status = Status(ok=True, hp=100, hpmax=100)
    monkeypatch.setattr(ctx, "last", lambda: cur["s"])
    monkeypatch.setattr(ctx, "require_command", lambda what: cur["s"])
    calls = []

    def move(x, y):
        s = _snap(rows, (x, y), [])
        s.status = cur["s"].status
        cur["s"] = s
        return s

    def fake_travel(x, y, **kw):
        calls.append(("travel", (x, y)))
        return move(x, y)

    def fake_step_onto(x, y, **kw):
        calls.append(("step_onto", (x, y)))
        return move(x, y)
    monkeypatch.setattr(nav, "travel", fake_travel)
    monkeypatch.setattr(nav, "step_onto", fake_step_onto)
    import pytest
    with pytest.raises(nav.NavError, match="magic trap"):
        nav.trek(15, 5)                                               # the magic trap is never crossed
    cur["s"] = _snap(rows, (10, 5), [])
    cur["s"].status = Status(ok=True, hp=100, hpmax=100)
    calls.clear()
    nav.trek(13, 5)
    assert calls == [("travel", (11, 5)), ("step_onto", (12, 5)), ("travel", (13, 5))]
    # p1 shift 31 #86: a stalker's remembered 'I' ON the dart trap of the only way — name it, not the traps
    rows[5] = "        |...I...|"
    cur["s"] = _snap(rows, (10, 5), [])
    cur["s"].status = Status(ok=True, hp=100, hpmax=100)
    with pytest.raises(nav.NavError, match=r"unseen monster 'I' at \(12, 5\) \(on the dart trap\) — clear_I"):
        nav.trek(13, 5)


def test_detection_browse_is_left_but_player_prompts_are_not():
    # p1 shift 31 #2095: object detection left the game in its getpos browse
    from nh.game import _detect_browse
    top = "You detect the presence of objects.  (For instructions type a '?')"
    assert _detect_browse([top], top)
    assert _detect_browse(["You sense your surroundings."], "(For instructions type a '?')")
    assert _detect_browse(["You feel very greedy, and sense gold!"], "")
    assert not _detect_browse(["You sense a faint wave of psychic energy."], "")
    # a travel/teleport prompt the player asked for is never escaped, whatever came before it
    assert not _detect_browse(["You sense your surroundings."], "Where do you want to travel to?  (For instructions")
    assert not _detect_browse(["You detect the presence of objects."], "Pick an object.")


def test_fall_through_trap_door_is_remembered_on_the_level_left():
    # p1 shift 31: the DL41 trap door fallen through wasn't in `nh info` nor a known trap
    from nh.game import Game, Timing
    g = Game(term=None, timing=Timing.local())

    class _M:
        state = {"levels": {"Gehennom / Level 41": {"features": {"up stairs": [[59, 5]]}}}}
    g.memory = _M()
    cur = _snap({5: "   ....@...."}, (7, 5), [])
    g._note_fall(cur, ["A trap door opens up under you!"], "Gehennom / Level 41")
    assert (7, 5) in g.traps["Gehennom / Level 41"]
    assert g.feature_desc["Gehennom / Level 41"][(7, 5)] == "trap door"
    lv = _M.state["levels"]["Gehennom / Level 41"]
    assert lv["features"]["trap door"] == [[7, 5]] and lv["traps"] == [[7, 5]]
    g._note_fall(cur, ["You climb up the stairs."], "Gehennom / Level 40")
    assert "Gehennom / Level 40" not in g.traps


def test_levitation_drowner_zone_stays_in_its_own_pool(monkeypatch):
    # p2 shift 28: a kraken walled into Medusa's inner pool blocked levitate_to over the outer water
    from tactics import ctx, nav
    g = _G()

    class _T:
        def gone(self, turn):
            return [{"x": 10, "y": 7, "desc": "kraken", "turn": turn - 10, "ch": ";"}]
    g.tracker = _T()
    monkeypatch.setattr(ctx, "game", g)
    rows = {4: "  ---------------------",
            5: "  |}}}}}}}}}}}}}}}}}}|",
            6: "  |}}}}}|---|}}}}}}}}|",
            7: "  |}}}}}|}}}|}}}}}}}}|",
            8: "  |}}}}}|---|}}}}}}}}|",
            9: "  |}}}}}}}}}}}}}}}}}}|",
            10: "  ---------------------"}
    s = _snap(rows, (4, 7), [])
    s.status = Status(ok=True, ldesc="Dlvl:24", turn=200, conditions=["Lev"])
    zone = nav._lev_drowner_zone(s)
    assert "kraken" in zone[(10, 7)] and (10, 5) not in zone and (6, 7) not in zone
    path = nav._lev_path(s, (4, 7), (18, 7), avoid=set(zone))
    assert path and path[-1] == (18, 7) and not set(path) & set(zone)


def test_covetous_ring_and_box_trap_check(monkeypatch):
    # p1 shift 30: fight a wounded covetous monster 6-8 squares from its heal stairs (wizard.c STRAT_HEAL:
    # it heals while you are more than 8 away; muse.c: it leaves by the stairs if you are within 5)
    from tactics import ctx, items, nav
    g = _G()
    g.terrain_seen = {}
    monkeypatch.setattr(ctx, "game", g)
    rows = {y: "  |" + "." * 30 + "|" for y in range(3, 20)}
    rows[10] = "  |" + "." * 10 + "<" + "." * 19 + "|"
    s = _snap(rows, (20, 10), [])
    ring = nav.covetous_ring(s)
    assert ring and all(25 < (x - 13) ** 2 + (y - 10) ** 2 <= 64 for x, y in ring)
    assert (19, 10) in ring and (20, 10) in ring and (17, 10) not in ring and (22, 10) not in ring
    # check_box: never disarms; a found trap -> 'trapped'
    from nh.parse import State
    script = [("direction", "", []), ("yn", "There is a large box here.  Check it for traps?", []),
              ("yn", "Disarm it?", ["You find a trap on the large box!"]), ("command", "", [])]
    sent, frames = [], iter(script)

    def fake_do(keys, **kw):
        sent.append(keys)
        k, p, msgs = next(frames)
        f = _snap({}, (5, 5), [])
        f.state = State(k, prompt=p)
        f.messages = msgs
        return f
    monkeypatch.setattr(ctx, "do", fake_do)
    monkeypatch.setattr(ctx, "require_command", lambda what: s)
    monkeypatch.setattr(ctx, "last", lambda: s)
    assert items.check_box(3) == "trapped" and sent == ["#untrap<CR>", ".", "y", "n"]


def test_sokoban_holes_filled_out_of_order():
    # p3 shift 12: a teleported boulder plugged a different hole; progress() said done=-1
    from tactics.sokoban import _out_of_order
    lv = {"boulders": [[1, 1], [1, 3]], "traps": [[5, 1], [6, 1]],
          "steps": [{"at": [1, 1], "moves": "rrrr", "after": {"boulders": [[1, 3]], "traps": [[6, 1]]}},
                    {"at": [1, 3], "moves": "uurrrrr", "after": {"boulders": [], "traps": []}}]}
    states = [({(1, 1), (1, 3)}, {(5, 1), (6, 1)}), ({(1, 3)}, {(6, 1)}), (set(), set())]
    cur = ({(1, 1)}, {(5, 1)}, set())               # boulder (1,3) is gone into hole (6,1)
    o = _out_of_order(lv, states, cur, 10, 2)
    assert o["from_step"] == 0 and o["gone"] == [(11, 5)] and o["filled"] == [(16, 3)]
    assert o["rest"] == ["push_wiki(11, 3, 'rrrr')"]
    assert _out_of_order(lv, states, ({(2, 2)}, {(5, 1)}, set()), 0, 0) is None


def test_no_squeeze_after_carrying_too_much():
    # p3 shift 12 #2005: hunt() planned a diagonal squeeze while the pack was over 600
    from nh.game import Game, Timing
    from tactics.mapview import bfs_path
    rows = {3: "    -----",
            4: "    |-.|",
            5: "    |.|-",
            6: "    -----"}
    s = _snap(rows, (5, 5), [])
    assert bfs_path(s, (5, 5), (6, 4)) == [(6, 4)]
    s.no_squeeze = True
    assert bfs_path(s, (5, 5), (6, 4)) is None
    g = Game(term=None, timing=Timing.local())
    g.no_squeeze = True
    s2 = _snap(rows, (5, 5), [])
    s2.status.ldesc = "Dlvl:6"
    g._annotate(s2)
    assert s2.no_squeeze is True


def test_explore_small_max_legs_notices_back_and_forth(monkeypatch):
    # p1 shift 31 #2002: explore(max_legs=3) x16 in a closed pocket only ever said "max_legs reached"
    from tactics import ctx, explore, nav
    g = _G()
    monkeypatch.setattr(ctx, "game", g)
    monkeypatch.setattr(ctx, "monster_filter", None)
    monkeypatch.setattr(explore, "_STALE", {})
    rows = {4: "        ----------------", 5: "        |..............|", 6: "        ----------------"}
    cur = {"s": _snap(rows, (11, 5), [])}
    cur["s"].status = Status(ok=True, hp=50, hpmax=50, turn=100)
    steps = {"seq": [(12, 5), (11, 5)], "i": 0}

    def fake_do(keys, **kw):
        if keys == ".":
            seq = steps["seq"]
            x, y = seq[steps["i"] % len(seq)]
            steps["i"] += 1
            s = _snap(rows, (x, y), [])
            s.status = Status(ok=True, hp=50, hpmax=50, turn=cur["s"].status.turn + 1)
            cur["s"] = s
        return cur["s"]
    monkeypatch.setattr(ctx, "do", fake_do)
    monkeypatch.setattr(ctx, "last", lambda: cur["s"])
    monkeypatch.setattr(explore, "_pick_target", lambda skip, bad, why: (22, 5))
    monkeypatch.setattr(nav, "waypoint", lambda s, t, cap: t)
    monkeypatch.setattr(nav, "leg_cap", lambda s=None: 8)
    monkeypatch.setattr(nav, "cursor_to", lambda x, y: None)
    monkeypatch.setattr(explore, "frontiers", lambda limit=12: [(22, 5)])
    monkeypatch.setattr(explore, "_boulder_leads", lambda s=None: [(15, 5)])
    monkeypatch.setattr(explore, "_hidden_stairs_hint", lambda: "")
    monkeypatch.setattr(explore, "dead_ends", lambda s=None, limit=8: [])
    assert explore._explore(3, set())["reason"] == "max_legs reached"
    r = explore._explore(3, set())
    assert r["reason"].startswith("blocked: boulders (15, 5)") and "back and forth over 2 squares" in r["reason"]
    # legs across known ground toward a far frontier end on new squares each time: never a verdict
    monkeypatch.setattr(explore, "_STALE", {})
    steps.update(seq=[(12, 5), (14, 5), (16, 5), (18, 5), (20, 5), (13, 5)], i=0)
    assert explore._explore(3, set())["reason"] == "max_legs reached"
    assert explore._explore(2, set())["reason"] == "max_legs reached"


def test_burn_note_drops_quaffed_letters_and_refreshes(monkeypatch):
    # p1 shift 31 / shift 29 #3333: the Gehennom burn warning named a quaffed potion / a bagged scroll
    from nh.game import Game, Timing
    from tactics import ctx, items
    g = Game(term=None, timing=Timing.local())
    g.level_name, g.level_name_ldesc = "Gehennom / Level 44", "Dlvl:44"
    g.loose_burnables, g.bags = ["m", "i"], ["D"]
    s = _snap({5: "   ..@.."}, (5, 5), [])
    s.status = Status(ok=True, hp=50, hpmax=50, ldesc="Dlvl:44")
    assert g.burn_note_for(s).startswith("2 scroll(s)/potion(s)/spellbook(s) in the open pack (per the last "
                                         "inventory(): mi)")
    g._note_used_up(s, b"qm")
    assert g.loose_burnables == ["i"]
    s.state = State("object", prompt="What do you want to read? [i or ?*]")
    g._note_used_up(s, b"i")
    assert g.loose_burnables == [] and g.burn_note_for(s) == ""
    g.loose_burnables = ["i"]
    s.burn_note = "stale"
    g.last = s
    monkeypatch.setattr(ctx, "game", g)
    items._stashed("i", ["You put a scroll labeled FOO into the bag."])
    assert g.loose_burnables == [] and s.burn_note == ""
