"""Unit tests for the terminal harness parser (no game needed)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nh.keys import describe_bytes, parse_keys  # noqa: E402
from nh.parse import classify, parse_status  # noqa: E402
from nh.screen import Screen, parse_capture  # noqa: E402

W, H = 80, 24


def mk(rows: dict[int, str], cursor=(0, 0), reverse_cells=()) -> Screen:
    lines = [" " * W for _ in range(H)]
    for y, t in rows.items():
        lines[y] = t.ljust(W)[:W]
    rev = [[False] * W for _ in range(H)]
    for (x, y) in reverse_cells:
        rev[y][x] = True
    return Screen(width=W, height=H, chars=lines, fg=[[7] * W for _ in range(H)], reverse=rev,
                  bold=[[False] * W for _ in range(H)], cursor=cursor)


STATUS1 = "Agnes the Stripling           St:18/02 Dx:14 Co:15 In:7 Wi:12 Ch:7 Lawful"


def test_status_basic():
    s = mk({22: STATUS1, 23: "Dlvl:3 $:42 HP:17(21) Pw:1(1) AC:6 Xp:2/31 T:512 Hungry Burdened Conf"})
    st = parse_status(s)
    assert st.ok
    assert (st.dlvl, st.gold, st.hp, st.hpmax, st.ac, st.xl, st.exp, st.turn) == (3, 42, 17, 21, 6, 2, 31, 512)
    assert st.hunger == "Hungry" and st.encumbrance == "Burdened" and st.conditions == ["Conf"]
    assert st.st == "18/02" and st.align == "Lawful"


def test_status_special_levels():
    for ld in ("Home 1", "Fort Ludios", "Astral Plane", "End Game"):
        s = mk({22: STATUS1, 23: f"{ld} $:0 HP:100(120) Pw:20(30) AC:-5 Xp:15/400000 T:30000"})
        st = parse_status(s)
        assert st.ok and st.ldesc == ld and st.ac == -5 and st.hp == 100


def test_status_polymorphed():
    s = mk({22: STATUS1, 23: "Dlvl:12 $:0 HP:80(80) Pw:20(30) AC:-2 HD:15 T:20000 Stone"})
    st = parse_status(s)
    assert st.ok and st.hd == 15 and st.conditions == ["Stone"]


def test_more_on_message_line():
    s = mk({0: "You hit the jackal.--More--", 22: STATUS1, 23: "Dlvl:1 $:0 HP:1(1) Pw:1(1) AC:6 Xp:1/0 T:1"},
           cursor=(27, 0))
    st = classify(s)
    assert st.kind == "more" and st.more_text == "You hit the jackal."


def test_more_wrapped_message():
    s = mk({0: "x        a xan or other mythical/fantastic insect or a boulder or statue (a",
            1: "statue of a grid bug)--More--"}, cursor=(29, 1))
    st = classify(s)
    assert st.kind == "more"
    assert st.more_text.endswith("(a statue of a grid bug)")


def test_text_window_more():
    s = mk({1: "                                Things that are here:",
            2: "                                a dagger",
            3: "                                2 food rations",
            4: "                                --More--"}, cursor=(40, 4))
    st = classify(s)
    assert st.kind == "text"
    assert "Things that are here:" in st.more_text and "2 food rations" in st.more_text


def test_yn_prompt():
    s = mk({0: "There is a newt corpse here; eat it? [ynq] (n) "}, cursor=(47, 0))
    st = classify(s)
    assert st.kind == "yn" and st.choices == "ynq" and st.default == "n"


def test_object_prompt():
    s = mk({0: "What do you want to eat? [d or ?*] "}, cursor=(35, 0))
    st = classify(s)
    assert st.kind == "object" and st.choices == "d or ?*"


def test_direction_prompt():
    s = mk({0: "In what direction? "}, cursor=(19, 0))
    assert classify(s).kind == "direction"


def test_menu_parse():
    s = mk({0: "                     Weapons",
            1: "                     a - an uncursed +1 long sword (weapon in hand)",
            2: "                     b - an uncursed +0 dagger (alternate weapon; not wielded)",
            3: "                     Comestibles",
            4: "                     d + an uncursed food ration",
            5: "                     (end)"}, cursor=(26, 5),
           reverse_cells=[(x, 0) for x in range(21, 28)] + [(x, 3) for x in range(21, 32)])
    st = classify(s)
    assert st.kind == "menu"
    items = st.menu.selectable()
    assert [i.letter for i in items] == ["a", "b", "d"]
    assert items[2].selected and not items[0].selected
    heads = [i.text for i in st.menu.items if i.header]
    assert heads == ["Weapons", "Comestibles"]


def test_command_state():
    s = mk({5: "      |..@..|", 22: STATUS1, 23: "Dlvl:1 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:5"},
           cursor=(9, 5))
    assert classify(s).kind == "command"


def test_capture_colors():
    raw = "\x1b[1m\x1b[32mF\x1b[0m\x1b[34me\x1b[39m.\x1b[7m\x1b[33md\x1b[27m\n"
    s = parse_capture(raw, W, H, (0, 0))
    assert s.chars[0][:4] == "Fe.d"
    assert s.fg[0][0] == 10 and s.fg[0][1] == 4 and s.fg[0][2] == 7 and s.fg[0][3] == 3
    assert s.reverse[0][3] and not s.reverse[0][2]


def test_keys():
    assert parse_keys("#pray<CR>") == b"#pray\r"
    assert parse_keys("<") == b"<" and parse_keys(">") == b">"
    assert parse_keys("<Esc><C-d>") == b"\x1b\x04"
    assert parse_keys("20s") == b"20s"
    assert describe_bytes(b"\x1b\r") == "<Esc><CR>"


def _guard_game():
    from nh.game import Game, Timing
    return Game(term=None, timing=Timing.local())


def _cmd_snap(monsters, hero=(10, 5), conditions=()):
    from nh.game import Snap
    from nh.parse import State, Status
    scr = mk({5: " " * 10 + "@", 22: STATUS1, 23: "Dlvl:1 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:5"}, cursor=hero)
    st = Status(ok=True, conditions=list(conditions))
    return Snap(screen=scr, state=State("command"), status=st, monsters=monsters)


def test_melee_guard_blocks_floating_eye():
    import pytest
    g = _guard_game()
    snap = _cmd_snap([{"x": 11, "y": 5, "desc": "floating eye"}])
    with pytest.raises(PermissionError):
        g._guard(snap, b"l", force=False)
    with pytest.raises(PermissionError):
        g._guard(snap, b"Fl", force=False)
    g._guard(snap, b"h", force=False)            # other direction is fine
    g._guard(snap, b"l", force=True)             # explicit override
    blind = _cmd_snap([{"x": 11, "y": 5, "desc": "floating eye"}], conditions=["Blind"])
    g._guard(blind, b"l", force=False)           # blind: its gaze can't paralyze you
    g._guard(_cmd_snap([{"x": 11, "y": 5, "desc": "jackal"}]), b"l", force=False)


def test_corpse_guard():
    import pytest
    from nh.game import Snap
    from nh.parse import State, Status
    g = _guard_game()
    def yn(prompt):
        return Snap(screen=mk({0: prompt}, cursor=(len(prompt), 0)), state=State("yn", prompt=prompt, choices="ynq"),
                    status=Status(ok=True))
    with pytest.raises(PermissionError):
        g._guard(yn("There is a cockatrice corpse here; eat it? [ynq] (n)"), b"y", force=False)
    with pytest.raises(PermissionError):
        g._guard(yn("There is a dwarf corpse here; eat it? [ynq] (n)"), b"y", force=False)
    g._guard(yn("There is a newt corpse here; eat it? [ynq] (n)"), b"y", force=False)
    g._guard(yn("There is a dwarf corpse here; eat it? [ynq] (n)"), b"n", force=False)


def test_hard_wrapped_sell_prompt():
    # p1 shift 2 #629: terminal auto-wrap split "Sell" across rows 0/1
    full = "Annootok offers 100 gold pieces for your scroll labeled EIRIS SAZUN IDISI.   Sell it? [ynaq] (y) "
    row0, row1 = full[:80], full[80:]
    s = mk({0: row0, 1: row1, 5: "      |..@..|", 22: STATUS1,
            23: "Dlvl:3 $:19 HP:29(29) Pw:1(1) AC:3 Xp:2/30 T:863"}, cursor=(len(row1), 1))
    st = classify(s)
    assert st.kind == "yn" and st.choices == "ynaq" and st.default == "y"
    assert "Sell it?" in st.prompt and st.msg_rows == 1


def test_explosion_frame_detected():
    from nh.game import _explosion_frame
    rows = {9: "      |....../-\\...|", 10: "      |......| |...|", 11: "      |......\\-/...|",
            22: STATUS1, 23: "Dlvl:3 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:5"}
    s = mk(rows, cursor=(9, 5))
    for (x, y) in ((13, 9), (15, 9), (13, 11), (15, 11), (14, 9), (14, 11), (13, 10), (15, 10)):
        s.fg[y][x] = 2      # one blast colour
    assert _explosion_frame(s)
    # a closet made of walls is not an explosion, nor a lone wand and throne
    walls = mk({9: "      |---|", 10: "      |.@.|", 11: "      |---|"}, cursor=(8, 10))
    assert not _explosion_frame(walls)
    items = mk({9: "   /  \\", 11: "   \\"}, cursor=(0, 5))
    items.fg[9][3], items.fg[9][6], items.fg[11][3] = 5, 3, 3
    assert not _explosion_frame(items)


def test_polymorphed_status_keeps_real_xl():
    from nh.game import Game, Timing

    class Term:
        def __init__(self, scr):
            self.scr = scr

        def capture(self):
            return self.scr

    normal = mk({5: "      |..@..|", 22: STATUS1, 23: "Dlvl:3 $:0 HP:30(49) Pw:1(1) AC:6 Xp:4/100 T:900"},
                cursor=(9, 5))
    poly = mk({5: "      |..d..|", 22: STATUS1, 23: "Dlvl:3 $:0 HP:10(10) Pw:1(1) AC:7 HD:2 T:901"},
              cursor=(9, 5))
    menu = mk({0: "                     Weapons", 1: "                     a - a long sword (weapon in hand)",
               2: "                     (end)"}, cursor=(26, 2), reverse_cells=[(x, 0) for x in range(21, 28)])
    g = Game(term=Term(normal), timing=Timing.local())
    assert g.capture().status.xl == 4
    g.term.scr = poly
    st = g.capture().status
    assert st.polymorphed and st.hd == 2 and st.xl == 4
    g.term.scr = menu
    s = g.capture()
    assert s.state.kind == "menu" and s.status.ok and s.status.stale and s.status.hp == 10


def test_level_key_and_rekey():
    from nh.game import Game, Timing
    g = Game(term=None, timing=Timing.local())
    from nh.parse import Status
    st = Status(ok=True, ldesc="Dlvl:3")
    assert g.level_key(st) == "Dlvl:3"
    g.traps["Dlvl:3"] = {(5, 5)}
    g.level_name, g.level_name_ldesc = "The Gnomish Mines / Level 3", "Dlvl:3"
    g.rekey_level("Dlvl:3", g.level_name)
    assert g.level_key(st) == "The Gnomish Mines / Level 3"
    assert g.traps == {"The Gnomish Mines / Level 3": {(5, 5)}}
    assert g.level_key(Status(ok=True, ldesc="Dlvl:4")) == "Dlvl:4"


def test_trap_message_regex():
    from nh.game import Game
    r = Game._TRAP_MSG
    for m in ("There is a bear trap here.", "You escape a bear trap.", "An arrow shoots out at you!",
              "You fall into a pit!", "A board beneath you squeaks loudly.", "You stumble into a spider web!",
              "KAABLAMM!!!  You triggered a land mine!", "There is a spiked pit here."):
        assert r.search(m), m
    for m in ("You can't set a trap on the stairs!", "You find a trap door.", "A trap door opens up under you!",
              "You set the bear trap.", "There is a staircase down here.", "You disarm the trap."):
        assert not r.search(m), m


def test_step_onto_known_trap_guard():
    import pytest
    g = _guard_game()
    snap = _cmd_snap([])
    g.traps[g.level_key(snap.status)] = {(11, 5)}
    with pytest.raises(PermissionError):
        g._guard(snap, b"l", force=False)
    with pytest.raises(PermissionError):
        g._guard(snap, b"ml", force=False)
    g._guard(snap, b"Fl", force=False)        # attacking that square is fine
    g._guard(snap, b"h", force=False)
    g._guard(snap, b"l", force=True)


def test_engulfed_is_not_an_explosion():
    from nh.game import _explosion_frame
    s = mk({9: "      /-\\", 10: "      |@|", 11: "      \\-/"}, cursor=(7, 10))
    for (x, y) in ((6, 9), (7, 9), (8, 9), (6, 10), (8, 10), (6, 11), (7, 11), (8, 11)):
        s.fg[y][x] = 6
    assert not _explosion_frame(s)


def test_really_attack_guard():
    import pytest
    from nh.game import Snap
    from nh.parse import State, Status
    g = _guard_game()
    p = "Really attack the peaceful gnome? (yes) [no]"
    snap = Snap(screen=mk({0: p}, cursor=(len(p), 0)), state=State("yn", prompt=p, choices="yes/no"),
                status=Status(ok=True))
    with pytest.raises(PermissionError):
        g._guard(snap, b"y", force=False)
    g._guard(snap, b"\x1b", force=False)
    g._guard(snap, b"y", force=True)


def test_feature_under_hero_remembered():
    from nh.game import Game, Snap, Timing
    from nh.mapscan import features_in_view
    from nh.parse import State, parse_status
    g = Game(term=None, timing=Timing.local())
    before = mk({5: "      |..{@.|", 22: STATUS1, 23: "Dlvl:5 $:0 HP:10(10) Pw:1(1) AC:6 Xp:5/200 T:900"},
                cursor=(10, 5))
    s0 = Snap(screen=before, state=State("command"), status=parse_status(before))
    g._remember_terrain(s0, [])
    on = mk({5: "      |..@..|", 22: STATUS1, 23: "Dlvl:5 $:0 HP:10(10) Pw:1(1) AC:6 Xp:5/200 T:901"},
            cursor=(9, 5))
    s1 = Snap(screen=on, state=State("command"), status=parse_status(on))
    g._remember_terrain(s1, [])
    assert s1.under == "{"
    assert any(f["name"] == "fountain (under you)" for f in features_in_view(s1))
    s2 = Snap(screen=on, state=State("command"), status=parse_status(on))
    g._remember_terrain(s2, ["The fountain dries up!"])
    assert s2.under is None


def test_feature_under_object_remembered_from_look_message():
    """Stairs/altar/throne under an object or statue don't show on the map;
    look_here()'s "There is ... here." (also first line of a pile window) does."""
    from nh.game import Game, Snap, Timing
    from nh.parse import State, parse_status
    g = Game(term=None, timing=Timing.local())
    on = mk({5: "      |..@..|", 22: STATUS1, 23: "Dlvl:5 $:0 HP:10(10) Pw:1(1) AC:6 Xp:5/200 T:901"},
            cursor=(9, 5))
    for msg, ch in [("There is a staircase down here.", ">"), ("There is a ladder up here.", "<"),
                    ("There is an opulent throne here.", "\\"),
                    ("There is an altar to Tyr (lawful) here.", "_"),
                    ("There is a high altar to Moloch (unaligned) here.", "_"),
                    ("There is a staircase up here.\nThings that are here:\na statue of a newt", "<")]:
        g.terrain_seen.clear()
        s = Snap(screen=on, state=State("command"), status=parse_status(on))
        g._remember_terrain(s, [msg])
        assert s.under == ch, msg
    g.terrain_seen.clear()
    s = Snap(screen=on, state=State("command"), status=parse_status(on))
    g._remember_terrain(s, ["There is a doorway here.", "There is a sink here."])
    assert s.under is None


def test_hostiles_exclude_unseen_and_hallucinated():
    from nh.game import Snap
    from nh.parse import State, Status
    s = Snap(screen=mk({}), state=State("command"), status=Status(ok=True),
             monsters=[{"x": 1, "y": 1, "dist": 1, "desc": "remembered, unseen monster", "unseen": True},
                       {"x": 2, "y": 1, "dist": 1, "desc": "", "hallu": True},
                       {"x": 3, "y": 1, "dist": 1, "desc": "jackal"}])
    assert [m["desc"] for m in s.hostiles()] == ["jackal"]


def test_engulfed_detection():
    from nh.game import _engulfed
    s = mk({9: "      /-\\", 10: "      |@|", 11: "      \\-/"}, cursor=(7, 10))
    assert _engulfed(s, (7, 10))
    assert not _engulfed(mk({10: "      .@."}, cursor=(7, 10)), (7, 10))


def test_condition_guards():
    import pytest
    g = _guard_game()
    hallu = _cmd_snap([], conditions=["Hallu"])
    hallu.screen.chars[5] = hallu.screen.chars[5][:11] + "D" + hallu.screen.chars[5][12:]
    with pytest.raises(PermissionError):
        g._guard(hallu, b"Fl", force=False)
    g._guard(hallu, b"h", force=False)
    blind = _cmd_snap([], conditions=["Blind"])
    blind.screen.chars[5] = blind.screen.chars[5][:11] + "I" + blind.screen.chars[5][12:]
    with pytest.raises(PermissionError):
        g._guard(blind, b"l", force=False)
    conf = _cmd_snap([{"x": 11, "y": 5, "dist": 1, "desc": "peaceful watchman", "peaceful": True}],
                     conditions=["Conf"])
    with pytest.raises(PermissionError):
        g._guard(conf, b"h", force=False)
    g._guard(conf, b"s", force=False)


def test_no_keys_after_death_or_in_lobby():
    import pytest
    from nh.game import Snap
    from nh.parse import State, Status
    g = _guard_game()
    g.last = Snap(screen=mk({0: "Do you want your possessions identified? [ynq] (n)"}),
                  state=State("gameover", prompt="Do you want your possessions identified?"), status=Status())
    with pytest.raises(PermissionError):
        g.step("p")
    g.last = Snap(screen=mk({}), state=State("dgl", prompt="p) Play last game"), status=Status())
    with pytest.raises(PermissionError):
        g.step("p")


def test_quoted_speech_stays_whole():
    from nh.game import _split_top
    assert _split_top('"Velkommen, wizard!  Welcome to Izchak\'s lighting store!"  You see here a lamp.') == [
        '"Velkommen, wizard!  Welcome to Izchak\'s lighting store!"', "You see here a lamp."]


def test_direction_and_name_prompts():
    from nh.parse import _classify_prompt
    assert _classify_prompt("Talk to whom? (in what direction)").kind == "direction"
    assert _classify_prompt("What monster do you want to genocide? [type the name]").kind == "getlin"


def test_genocide_guard():
    import pytest
    from nh.game import Snap
    from nh.parse import State, Status
    g = _guard_game()
    p = "What class of monsters do you wish to genocide?"
    snap = Snap(screen=mk({0: p}), state=State("getlin", prompt=p), status=Status(ok=True))
    with pytest.raises(PermissionError):
        g._guard(snap, b"master mind flayer\r", force=False)
    with pytest.raises(PermissionError):
        g._guard(snap, b"h\r", force=False)
    g._guard(snap, b"L\r", force=False)


def test_more_wrapped_to_column_zero():
    msg = "Velkommen wizard, welcome to NetHack!  You are a lawful dwarven Valkyrie.xx"
    s = mk({0: msg, 1: "--More--", 5: "      |..@..|", 22: STATUS1,
            23: "Dlvl:1 $:0 HP:18(18) Pw:1(1) AC:6 Xp:1/0 T:1"}, cursor=(8, 1))
    st = classify(s)
    assert st.kind == "more" and "You are a lawful dwarven Valkyrie" in st.more_text


def test_prompt_hard_wrapped_at_79():
    # p2 #1082: tty wraps the message line at column 79 (CO-1), mid-token
    row0 = "Kittamagh offers 30 gold pieces for your scroll labeled YUM YUM.  Sell it? [yna"
    assert len(row0) == 79
    s = mk({0: row0, 1: "q] (y)", 5: "      |..@..|", 22: STATUS1,
            23: "Dlvl:2 $:7 HP:20(20) Pw:1(1) AC:6 Xp:2/30 T:1000"}, cursor=(7, 1))
    st = classify(s)
    assert st.kind == "yn" and st.choices == "ynaq" and st.default == "y"
    assert "Sell it? [ynaq]" in st.prompt


def test_pick_one_menu_stops_extra_keys():
    from nh.game import Game, Snap, Timing
    from nh.parse import State, Status, classify
    menu1 = mk({0: "                     Do what with the large box?",
                1: "                     o - take something out",
                2: "                     i - put something in",
                3: "                     (end)"}, cursor=(26, 3))
    menu2 = mk({0: "                     Take out what?",
                1: "                     a - a scroll labeled FOO",
                2: "                     (end)"}, cursor=(26, 2))
    g = Game(term=None, timing=Timing.local())
    first = Snap(screen=menu1, state=classify(menu1), status=Status())
    assert first.state.kind == "menu"
    g.last = first
    sent = []

    def fake_send(data):
        sent.append(data)
        return Snap(screen=menu2, state=classify(menu2), status=Status())
    g.send_bytes = fake_send
    s = g.step("o<CR>")
    assert sent == [b"o"]
    assert s.unsent == "<CR>" and "pick-one" in s.stop_reason


def test_prompt_filling_the_row_cursor_on_next_row():
    # p2 #556: 79-char prompt + trailing space wrapped; cursor at (1,1)
    row0 = "Upernavik offers 50 gold pieces for your vellum spellbook.  Sell it? [ynaq] (y)"
    assert len(row0) == 79
    s = mk({0: row0, 5: "      |..@..|", 22: STATUS1,
            23: "Dlvl:4 $:6 HP:40(40) Pw:4(4) AC:2 Xp:3/69 T:1800"}, cursor=(1, 1))
    st = classify(s)
    assert st.kind == "yn" and st.choices == "ynaq" and "Sell it?" in st.prompt


def test_brown_plus_door_vs_spellbook():
    from nh.game import Snap
    from nh.mapscan import features_in_view, objects_in_view
    from nh.parse import State, Status
    s = mk({4: "      |-----+-----|", 5: "      |...........|", 6: "      |.....+.@...|", 7: "      |...........|",
            22: STATUS1, 23: "Dlvl:1 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:5"}, cursor=(14, 6))
    s.fg[4][12] = 3          # brown '+' in the top wall: a door
    s.fg[6][12] = 3          # brown '+' on the floor: a spellbook
    snap = Snap(screen=s, state=State("command"), status=Status(ok=True))
    doors = [(f["x"], f["y"]) for f in features_in_view(snap) if f["name"] == "closed door"]
    books = [(o["x"], o["y"]) for o in objects_in_view(snap) if o["ch"] == "+"]
    assert doors == [(12, 4)] and books == [(12, 6)]


def test_default_benign_monster_vs_monster_melee():
    from nh.kernel import DEFAULT_BENIGN

    def benign(m):
        return any(p.search(m) for p in DEFAULT_BENIGN)
    for m in ["The kitten misses the rock mole.", "The kitten bites the newt.", "It hits the jackal.",
              "The gnome lord hits the little dog.", "The soldier ant stings the kitten."]:
        assert benign(m), m
    for m in ["The jackal bites!", "The kitten turns to stone.", "The purple worm swallows the kitten.",
              "The mind flayer's tentacles suck the kitten.", "The imp hits!", "You hit the rock mole."]:
        assert not benign(m), m


def test_monster_trap_messages():
    from nh.tracker import MON_TRAP_RE
    for m in ["The leprechaun falls into a pit!", "The jackal is caught in a bear trap!",
              "The gnome is caught in a spider web.", "A board beneath the newt squeaks loudly.",
              "Click!  The dwarf triggers a rolling boulder trap.", "The hill orc triggers a land mine!",
              "The leprechaun doesn't fall into the pit.", "A gush of water hits the gnome's left arm!"]:
        assert MON_TRAP_RE.search(m), m
    for m in ["You fall into a pit!", "A gush of water hits you!", "There is a pit here.",
              "The kitten misses the rock mole."]:
        assert not MON_TRAP_RE.search(m), m


def test_guard_still_climb():
    import pytest
    from nh.game import Snap
    from nh.parse import State, Status
    g = _guard_game()
    p = "Beware, there will be no return!  Still climb? [yn] (n)"
    snap = Snap(screen=mk({0: p}, cursor=(len(p), 0)), state=State("yn", prompt=p, choices="yn"),
                status=Status(ok=True))
    with pytest.raises(PermissionError):
        g._guard(snap, b"y", force=False)
    g._guard(snap, b"n", force=False)
    g._guard(snap, b"y", force=True)


def test_guard_cockatrice_corpse_pickup_and_blind_step():
    import pytest
    from nh.game import Snap
    from nh.parse import Menu, MenuItem, State, Status
    g = _guard_game()
    s = _cmd_snap([])
    g._remember_here(s, ["You see here a cockatrice corpse."])
    with pytest.raises(PermissionError):
        g._guard(s, b",", force=False)
    g._guard(s, b",", force=True)
    # a pile: ',' opens a menu, so it's allowed; confirming with the corpse selected is not
    g._remember_here(s, ["Things that are here:\na cockatrice corpse\na dagger"])
    g._guard(s, b",", force=False)
    menu = Menu(title="Pick up what?", items=[MenuItem("a", "a cockatrice corpse", selected=True),
                                             MenuItem("b", "a dagger", selected=True)])
    ms = Snap(screen=mk({}), state=State("menu", menu=menu, prompt="Pick up what?"), status=Status(ok=True))
    with pytest.raises(PermissionError):
        g._guard(ms, b"\r", force=False)
    menu.items[0].selected = False
    g._guard(ms, b"\r", force=False)
    # blind: stepping onto the corpse square is refused, other squares are fine
    blind = _cmd_snap([], hero=(9, 5), conditions=["Blind"])
    with pytest.raises(PermissionError):
        g._guard(blind, b"l", force=False)        # (10,5) holds the corpse
    g._guard(blind, b"h", force=False)
    # "You see no objects here." forgets it
    g._remember_here(s, ["You see no objects here."])
    g._guard(s, b",", force=False)
