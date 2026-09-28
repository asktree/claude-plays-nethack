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


def test_f_blow_guard_refuses_a_peaceful_label():
    # uhitm.c attack_checks(): an F blow never asks "Really attack?" (p2 shift 26)
    import pytest
    g = _guard_game()
    snap = _cmd_snap([{"x": 11, "y": 5, "desc": "peaceful black naga", "peaceful": True}])
    with pytest.raises(PermissionError, match="never asks"):
        g._guard(snap, b"Fl", force=False)
    g._guard(snap, b"Fl", force=True)
    g._guard(_cmd_snap([{"x": 11, "y": 5, "desc": "black naga hatchling"}]), b"Fl", force=False)


def test_corpse_guard():
    import pytest
    from nh.game import Snap
    from nh.parse import State, Status
    g = _guard_game()
    g.hero_pos = (10, 5)

    def yn(prompt):
        return Snap(screen=mk({0: prompt}, cursor=(len(prompt), 0)), state=State("yn", prompt=prompt, choices="ynq"),
                    status=Status(ok=True, turn=100))
    with pytest.raises(PermissionError):
        g._guard(yn("There is a cockatrice corpse here; eat it? [ynq] (n)"), b"y", force=False)
    with pytest.raises(PermissionError):
        g._guard(yn("There is a dwarf corpse here; eat it? [ynq] (n)"), b"y", force=False)
    g.record_kill("newt", (10, 5), 95)          # a newt you just killed here
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
    # a book in a room CORNER (walls on two adjacent sides) is no door (p1 shift 13)
    s2 = mk({4: "      |-----------|", 5: "      |+..........|", 6: "      |......@....|",
             22: STATUS1, 23: "Dlvl:1 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:5"}, cursor=(13, 6))
    s2.fg[5][7] = 3
    snap2 = Snap(screen=s2, state=State("command"), status=Status(ok=True))
    assert not [f for f in features_in_view(snap2) if f["name"] == "closed door"]
    assert [(o["x"], o["y"]) for o in objects_in_view(snap2) if o["ch"] == "+"] == [(7, 5)]


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
    # p3 shift 14 #551: a search found a land mine under a scroll — its square is re-read from #terrain
    from nh.tracker import FOUND_TRAP_RE
    for m in ["You find a land mine.", "You find a sleeping gas trap.", "You find an anti-magic field.",
              "You find a trap door."]:
        assert FOUND_TRAP_RE.search(m), m
    for m in ["You find a hidden door.", "You find a hidden passage.", "You find a lamp."]:
        assert not FOUND_TRAP_RE.search(m), m


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


def test_guard_blind_step_onto_a_cockatrice_kill_square():
    # p2 shift 35 #14: two cockatrices killed ON the zoo doorway (39,8) with Fj from (39,7) — never stood on, so no
    # "You see here" memory — then a blindfolded step onto it: stoned (life saving used up)
    import pytest
    g = _guard_game()
    blind = _cmd_snap([], hero=(9, 5), conditions=["Blind"])
    blind.status.turn = 22530
    key = g.level_key(blind.status)
    g.kills[key] = [("cockatrice", (10, 5), 22481), ("cockatrice", (10, 5), 22495), ("newt", (8, 5), 22500)]
    with pytest.raises(PermissionError, match=r"where a cockatrice was killed 35 turns ago"):
        g._guard(blind, b"l", force=False)
    g._guard(blind, b"h", force=False)                   # a newt died there: fine
    g._guard(blind, b"l", force=True)
    blind.status.turn = 22900                            # long rotted away
    g._guard(blind, b"l", force=False)
    seeing = _cmd_snap([], hero=(9, 5))
    seeing.status.turn = 22530
    g._guard(seeing, b"l", force=False)                  # sighted steps never touch what lies there
    blind.status.turn = 22530
    assert g.trice_squares(blind) == {(10, 5)}           # (travel/explore routes avoid it while blind)


def test_guard_water_lava_and_choking():
    import pytest
    from nh.game import Snap
    from nh.parse import State, Status
    g = _guard_game()
    scr = mk({5: " " * 10 + "@}", 22: STATUS1, 23: "Dlvl:1 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:5"}, cursor=(10, 5))
    s = Snap(screen=scr, state=State("command"), status=Status(ok=True))
    with pytest.raises(PermissionError):
        g._guard(s, b"l", force=False)
    with pytest.raises(PermissionError):
        g._guard(s, b"ml", force=False)
    g._guard(s, b"h", force=False)
    g._guard(s, b"l", force=True)
    lev = Snap(screen=scr, state=State("command"), status=Status(ok=True, conditions=["Lev"]))
    g._guard(lev, b"l", force=False)
    full = Snap(screen=scr, state=State("command"), status=Status(ok=True, hunger="Satiated"))
    with pytest.raises(PermissionError):
        g._guard(full, b"e", force=False)
    g._guard(s, b"e", force=False)
    stoned = Snap(screen=scr, state=State("command"), status=Status(ok=True, hunger="Satiated", conditions=["Stone"]))
    g._guard(stoned, b"e", force=False)     # a lizard corpse against stoning beats the choking risk
    p = "Continue eating? [yes/no] (no)"
    q = Snap(screen=mk({0: p}, cursor=(len(p), 0)), state=State("yn", prompt=p, choices="yes/no"),
             status=Status(ok=True))
    with pytest.raises(PermissionError):
        g._guard(q, b"y", force=False)
    g._guard(q, b"n", force=False)


def test_guard_deadly_tins_and_gray_stones():
    import pytest
    from nh.game import Snap
    from nh.parse import Menu, MenuItem, State, Status
    g = _guard_game()

    def yn(prompt, msgs=()):
        s = Snap(screen=mk({0: prompt}, cursor=(len(prompt), 0)), state=State("yn", prompt=prompt, choices="yn"),
                 status=Status(ok=True))
        s.messages = list(msgs)
        return s
    for smell in ("cockatrices", "dwarves", "little dogs", "werejackals", "the Medusa", "green slimes"):
        s = yn(f"It smells like {smell}.  Eat it? [yn] (n)")
        with pytest.raises(PermissionError):
            g._guard(s, b"y", force=False)
    g._guard(yn("It smells like newts.  Eat it? [yn] (n)"), b"y", force=False)
    with pytest.raises(PermissionError):
        g._guard(yn("It smells like chicken.  Eat it? [yn] (n)"), b"y", force=False)
    hallu = yn("It smells like newts.  Eat it? [yn] (n)")
    hallu.status.conditions = ["Hallu"]
    with pytest.raises(PermissionError):
        g._guard(hallu, b"y", force=False)
    g._guard(yn("It smells like gnomes.  Eat it? [yn] (n)"), b"y", force=False)
    # the smell line shown with --More-- first: only the prompt is left on screen
    with pytest.raises(PermissionError):
        g._guard(yn("Eat it? [yn] (n)", ["It smells like chickatrices."]), b"y", force=False)
    # gray stones: ',' on a lone one is refused; a pickup menu confirming one too
    s = _cmd_snap([])
    g._remember_here(s, ["You see here a gray stone."])
    with pytest.raises(PermissionError):
        g._guard(s, b",", force=False)
    g._remember_here(s, ["You see here 2 gray stones."])
    with pytest.raises(PermissionError):
        g._guard(s, b",", force=False)
    g._remember_here(s, ["You see here a luckstone."])
    g._guard(s, b",", force=False)
    menu = Menu(title="Pick up what?", items=[MenuItem("a", "a gray stone", selected=True)])
    ms = Snap(screen=mk({}), state=State("menu", menu=menu, prompt="Pick up what?"), status=Status(ok=True))
    with pytest.raises(PermissionError):
        g._guard(ms, b"\r", force=False)


def test_guard_corpse_age_from_kill_records():
    import pytest
    from nh.game import Snap
    from nh.parse import State, Status
    g = _guard_game()
    g.hero_pos = (10, 5)

    def q(name, turn):
        p = f"There is a {name} corpse here; eat it? [ynq] (n)"
        s = Snap(screen=mk({0: p}, cursor=(len(p), 0)), state=State("yn", prompt=p, choices="ynq"),
                 status=Status(ok=True, turn=turn))
        g.last_status = s.status
        return s
    # a jackal you didn't see die: age unknown -> refused
    with pytest.raises(PermissionError):
        g._guard(q("jackal", 500), b"y", force=False)
    # killed right here 10 turns ago: fine
    g.record_kill("jackal", (10, 5), 490)
    g._guard(q("jackal", 500), b"y", force=False)
    # 200 turns later it may be tainted
    with pytest.raises(PermissionError):
        g._guard(q("jackal", 700), b"y", force=False)
    # lichens never rot
    g._guard(q("lichen", 9000), b"y", force=False)
    g._guard(q("jackal", 700), b"y", force=True)


def test_tracker_records_kills():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_nh_monitor import FakeGame, snap  # noqa: E402
    from nh.monitor import MonsterTracker
    g = FakeGame()
    kills = []
    g.record_kill = lambda name, cell, turn: kills.append((name, cell, turn))
    t = MonsterTracker(g)
    g.truth = {(41, 10): "jackal"}
    t.update(snap({(41, 10): "d"}, 100))
    s = snap({}, 101)
    s.messages = ["You kill the jackal!"]
    t.update(s)
    assert kills == [("jackal", (41, 10), 101)]


def test_guard_elbereth_attack_and_peaceful_step():
    import pytest
    g = _guard_game()
    s = _cmd_snap([{"x": 11, "y": 5, "desc": "jackal"}, {"x": 9, "y": 5, "desc": "peaceful gnome", "peaceful": True}])
    g._remember_here(s, ["Something is written here in the dust.", 'You read: "Elbereth".'])
    assert g.on_elbereth(s)
    for keys in (b"Fl", b"l"):
        with pytest.raises(PermissionError):
            g._guard(s, keys, force=False)
    for keys in (b"t", b"f", b"z", b"\x04"):       # checked at their direction prompt instead
        g._guard(s, keys, force=False)
    g._guard(s, b"Fl", force=True)
    # at the direction prompt: toward the jackal (east) is refused, down/west/up are fine
    from nh.game import Snap
    from nh.parse import State
    g.hero_pos = (10, 5)
    d = Snap(screen=s.screen, state=State("direction", prompt="In what direction?"), status=s.status,
             monsters=s.monsters)
    with pytest.raises(PermissionError):
        g._guard(d, b"l", force=False)
    g._guard(d, b">", force=False)
    g._guard(d, b"k", force=False)
    g._guard(s, b"k", force=False)            # stepping away is fine
    # a plain step into the peaceful gnome is refused (NetHack would ask 'Really attack?')
    with pytest.raises(PermissionError):
        g._guard(s, b"h", force=False)
    # the engraving fades after a hypocritical attack: no longer on Elbereth
    g._remember_here(s, ["You feel like a hypocrite.", "The engraving beneath you fades."])
    assert not g.on_elbereth(s)
    g._guard(s, b"Fl", force=False)
    # arriving on a square without a read message forgets an engraving remembered there
    g._remember_here(s, ['You read: "Elbereth".'])
    assert g.on_elbereth(s)
    g._remember_here(s, [], prev_hero=(10, 6))
    assert not g.on_elbereth(s)


def test_door_at_corridor_end_is_a_door():
    from nh.mapscan import _door_like
    scr = mk({5: "   ###+   ", 6: "          "})
    assert _door_like(scr, 6, 5)                      # corridor end, walls not seen yet
    scr = mk({4: "  |.....|", 5: "  |..+..|", 6: "  |.....|"})
    assert not _door_like(scr, 5, 5)                  # a book lying in the room
    scr = mk({4: "  ---+---", 5: "  |.....|"})
    assert _door_like(scr, 5, 4)                      # in a wall line


def test_default_benign_pet_kills_and_traps():
    from nh.kernel import DEFAULT_BENIGN

    def benign(m):
        return any(p.search(m) for p in DEFAULT_BENIGN)
    for m in ["The large cat kills the gnome!", "The kitten kills the newt.", "You are still in a pit.",
              "You crawl to the edge of the pit.", "Pardon me, large cat.", "You are caught in a bear trap."]:
        assert benign(m), m
    for m in ["The soldier ant kills you!", "The large cat is killed!", "You feel feverish."]:
        assert not benign(m), m


def test_guard_bare_prefix_key():
    import pytest
    g = _guard_game()
    s = _cmd_snap([])
    for k in (b"F", b"m", b"M", b"g", b"G"):
        with pytest.raises(PermissionError):
            g._guard(s, k, force=False)
    g._guard(s, b"Fh", force=False)
    g._guard(s, b"m<", force=False)


def test_stair_links_follow_level_renames():
    from nh.game import Game, Timing
    g = Game(term=None, timing=Timing.local())
    g.stair_links = {"The Dungeons of Doom / Level 2": {(21, 14): "Dlvl:3"}, "Dlvl:3": {(77, 13): "The Dungeons of Doom / Level 2"}}
    g.rekey_level("Dlvl:3", "The Gnomish Mines / Level 3")
    assert g.stair_links["The Dungeons of Doom / Level 2"][(21, 14)] == "The Gnomish Mines / Level 3"
    assert g.stair_links["The Gnomish Mines / Level 3"] == {(77, 13): "The Dungeons of Doom / Level 2"}


def test_long_message_wrapped_onto_row1_is_not_map():
    # tty split a long quest message: row 1 holds one leftover word at column 0
    top = "You receive a faint telepathic message from the Norn: Look for a ...ic"
    s = mk({0: top.ljust(79)[:79].rstrip(), 1: "transporter.", 5: "     |..@..|", 22: STATUS1,
            23: "Dlvl:11 $:0 HP:98(104) Pw:11(11) AC:-3 Xp:8/1869 T:5817"}, cursor=(8, 5))
    st = classify(s)
    assert st.kind == "command" and st.msg_rows == 1


def test_fullwidth_text_window_keeps_first_column():
    # ^O overview as a full-width NHW_MENU text window: --More-- at column 1
    rows = {0: "The Dungeons of Doom: levels 1 to 11", 1: "   Level 1:", 2: "      Some fountains.",
            3: " --More--"}
    s = mk(rows, cursor=(9, 3))
    st = classify(s)
    assert st.kind == "text" and st.more_text.startswith("The Dungeons of Doom")


def test_travel_cursor_over_blank_square_is_getpos():
    top = "Where do you want to travel to?  (For instructions type a '?')"
    s = mk({0: top, 1: "  ----          ---------", 2: "  |<..--   ------.......--", 3: "  |.....---|......",
            4: "  --..|....|.-----    |..|    ", 22: STATUS1, 23: "Dlvl:1 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:5"},
           cursor=(52, 4))
    assert classify(s).kind == "getpos"


def test_guard_wish_prompt():
    import pytest
    from nh.game import Snap
    from nh.parse import State, Status
    g = _guard_game()
    p = "For what do you wish?"
    s = Snap(screen=mk({0: p}, cursor=(len(p) + 1, 0)), state=State("getlin", prompt=p), status=Status(ok=True))
    for bad in (b"\x1b", b"\r", b"#rub\r", b"h\r"):
        with pytest.raises(PermissionError):
            g._guard(s, bad, force=False)
    g._guard(s, b"blessed +2 gray dragon scale mail\r", force=False)


def test_feature_colours_throne_vs_ray_and_engulf_ring(tmp_path):
    from nh.game import Game, Snap, Timing, feature_at
    from nh.parse import State
    from nh.tracker import Tracker
    scr = mk({7: "      \\  \\   _  _", 22: STATUS1, 23: "Dlvl:11 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:5"},
             cursor=(20, 7))
    scr.fg[7][6] = 11          # a gold '\': a throne
    scr.fg[7][9] = 12          # a bright blue '\': a sleep ray passing by
    scr.fg[7][16] = 6          # a cyan '_': an iron chain
    assert feature_at(scr, 6, 7) == "\\" and feature_at(scr, 9, 7) is None
    assert feature_at(scr, 13, 7) == "_" and feature_at(scr, 16, 7) is None
    g = Game(term=None, timing=Timing.local())
    s = Snap(screen=scr, state=State("command"), status=parse_status(scr))
    g._remember_terrain(s, [])
    assert g.terrain_seen[g.level_key(s.status)] == {(6, 7): "\\", (13, 7): "_"}
    # engulfed by a dust vortex: the ring's corners are no thrones, for the game or the tracker
    ring = mk({8: " " * 48 + "/-\\", 9: " " * 48 + "|@|", 10: " " * 48 + "\\-/", 22: STATUS1,
               23: "Dlvl:11 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:6 Blind"}, cursor=(49, 9))
    for x, y in ((50, 8), (48, 10)):
        ring.fg[y][x] = 11
    r = Snap(screen=ring, state=State("command"), status=parse_status(ring))
    r.engulfed = True
    g._remember_terrain(r, [])
    t = Tracker(g, tmp_path / "hs.json")
    t.need_overview = False
    t.on_step(r)
    t.on_step(s)
    feats = t.state["levels"][g.level_key(s.status)]["features"]
    assert feats == {"throne": [[6, 7]], "altar": [[13, 7]]}


def test_wielded_labels_and_weapon_names():
    from nh.game import WIELDED_RE, is_weapon_text
    for t in ("a - a +1 long sword (weapon in hand)", "a - a dwarvish mattock (weapon in hands)",
              "a - 4 +0 daggers (wielded)", "a - an elven dagger named Sting (weapon in hand, glowing light blue)",
              "a - an aklys (tethered weapon in hand)"):
        assert WIELDED_RE.search(t), t
    for t in ("b - a blessed +0 dagger (alternate weapon; not wielded)", "b - a dagger (wielded in other hand)",
              "c - an uncursed +3 small shield (being worn)"):
        assert not WIELDED_RE.search(t), t
    for t in ("a blessed rustproof +6 long sword named Excalibur", "the blessed rustproof +6 Excalibur",
              "the uncursed +2 Sting (weapon in hand, glowing light blue)", "a +0 pick-axe", "2 daggers",
              "an uncursed unicorn horn", "a broad pick", "a runed dagger"):
        assert is_weapon_text(t), t
    for t in ("a blessed lamp", "a blessed magic lamp", "an oil lamp (lit)", "a cockatrice corpse", "a sack",
              "a white potion", "a gray stone", "a red gem"):
        assert not is_weapon_text(t), t


def test_wield_tracking_from_messages():
    g = _guard_game()
    g.wielded = "a +1 long sword (weapon in hand)"
    g._note_wield(["You now wield a blessed lamp."])
    assert g.wielded == "a blessed lamp" and "not a weapon" in g.wield_note()
    g._note_wield(["a - a blessed rustproof +6 long sword named Excalibur (weapon in hand)."])
    assert g.wielded.startswith("a blessed rustproof +6 long sword") and g.wield_note() == ""
    g._note_wield(["a - the blessed rustproof +6 Excalibur (weapon in hand)."])    # fully identified artifact
    assert g.wield_note() == ""
    g.wielded, g.wielded_class = "a strange thing (weapon in hand)", "Weapons"   # inventory() says Weapons
    assert g.wield_note() == ""
    g._note_wield(["You are empty handed."])
    assert g.wielded == "" and "EMPTY-HANDED" in g.wield_note()
    g._note_wield(["Your long sword slips from your hands."])
    assert g.wielded is None and g.wield_note() == ""
    g.gloves = "d - leather gloves (being worn)"
    g._note_wield(["You finish taking off your gloves."])
    assert g.gloves is None


def test_guard_cockatrice_bare_handed():
    import pytest
    g = _guard_game()
    s = _cmd_snap([{"x": 11, "y": 5, "desc": "cockatrice"}])
    g.wielded, g.gloves = "", ""
    for keys in (b"l", b"Fl"):
        with pytest.raises(PermissionError, match="EMPTY-HANDED"):
            g._guard(s, keys, force=False)
    g._guard(s, b"ml", force=False)                  # 'm' never attacks ("You move right into it")
    g.wielded = None                                  # unknown: look first
    with pytest.raises(PermissionError, match="inventory"):
        g._guard(s, b"Fl", force=False)
    g.wielded = "a +1 long sword (weapon in hand)"
    g._guard(s, b"Fl", force=False)                   # a wielded weapon protects your hands
    g.wielded, g.gloves = "", "e - leather gloves (being worn)"
    g._guard(s, b"Fl", force=False)
    g.gloves = ""
    g._guard(s, b"Fl", force=True)


def test_shop_tracking_and_guards():
    import pytest
    from nh.game import Snap
    from nh.parse import State
    g = _guard_game()
    rows = {3: "  ------------",
            4: "  |.)).[[....|",
            5: "  |@.........|",
            6: "  |..........|",
            7: "  -----|------",
            22: STATUS1, 23: "Dlvl:12 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:5"}
    # the welcome comes on the door square (7,7): the shop is the room above it
    door = mk({**rows, 7: "  -----@------"}, cursor=(7, 7))
    s = Snap(screen=door, state=State("command"), status=parse_status(door))
    g._note_shop(s, ["Velkommen, p2!  Welcome to Carignan's antique weapons outlet!"])
    assert g.shops[g.level_key(s.status)] == [[3, 4, 12, 6, "Carignan's antique weapons outlet"]]
    assert g.shop_at((5, 5), s.status) and g.shop_at((7, 7), s.status) and not g.shop_at((7, 9), s.status)
    inside = Snap(screen=mk(rows, cursor=(3, 5)), state=State("command"), status=s.status, monsters=[])
    for keys in (b"t", b"f"):
        with pytest.raises(PermissionError, match="SOLD"):
            g._guard(inside, keys, force=False)
    g._guard(inside, b"t", force=True)
    g.hero_pos = (3, 5)
    dig = Snap(screen=inside.screen, state=State("direction", prompt="In what direction do you want to dig? [yu>]"),
               status=s.status)
    with pytest.raises(PermissionError, match="backpack"):
        g._guard(dig, b">", force=False)
    g._guard(dig, b"l", force=False)                   # sideways is the shopkeeper's wall... not our guard
    # outside the shop: no refusal
    g.hero_pos = (7, 9)
    out = Snap(screen=mk(rows, cursor=(7, 9)), state=State("command"), status=s.status, monsters=[])
    g._guard(out, b"t", force=False)


def test_trap_colours_drawbridge_vibrating_square_and_feature_summary():
    from nh.game import Snap
    from nh.mapscan import features_in_view, monsters_in_view
    from nh.parse import State
    from nh.render import render
    s = mk({5: "  .^.^.^.#.~..}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}>", 22: STATUS1,
            23: "Dlvl:30 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:5"}, cursor=(2, 5))
    s.fg[5][3] = 13     # bright magenta ^: magic portal
    s.fg[5][5] = 3      # brown ^: squeaky board / hole / trap door
    s.fg[5][7] = 10     # bright green ^: polymorph trap
    s.fg[5][9] = 3      # brown #: raised drawbridge
    s.fg[5][11] = 5     # magenta ~: the vibrating square (a worm tail is brown)
    for x in range(14, 50):
        s.fg[5][x] = 4
    snap = Snap(screen=s, state=State("command"), status=parse_status(s))
    names = {(f["x"], f["y"]): f["name"] for f in features_in_view(snap)}
    assert names[(3, 5)] == "magic portal" and names[(7, 5)] == "polymorph trap"
    assert names[(5, 5)] == "trap: squeaky board/hole/trap door" and names[(9, 5)] == "raised drawbridge"
    assert names[(11, 5)] == "vibrating square"
    assert not [m for m in monsters_in_view(snap) if (m["x"], m["y"]) == (11, 5)]
    snap.feature_desc = {(5, 5): "trap door"}
    assert {(f["x"], f["y"]): f["name"] for f in features_in_view(snap)}[(5, 5)] == "trap door"
    out = render(snap, mode="full")
    line = next(l for l in out.splitlines() if l.startswith("features:"))
    assert line.index("down stairs") < line.index("water x")      # stairs first, water summarized
    assert "water x35" in line


def test_intrinsics_from_messages_and_resisted_passives():
    from nh.danger import passive_max
    g = _guard_game()
    assert "cold" in g.intrinsics and "fire" not in g.intrinsics
    g._note_intrinsics(["You feel a momentary chill."])
    assert "fire" in g.intrinsics
    assert passive_max("fire vortex")[0] > 0 and passive_max("fire vortex", resists=g.intrinsics)[0] == 0
    g._note_intrinsics(["You feel warmer."])            # a gremlin stole it
    assert "fire" not in g.intrinsics


def test_default_benign_siege_noise_and_altar_pile():
    from nh.kernel import DEFAULT_BENIGN

    def benign(m):
        return any(p.search(m) for p in DEFAULT_BENIGN)
    for m in ["You hear a door crash open.", "A spear misses you.", "The soldier throws a spear!",
              "You stop at the edge of the water.", "A board beneath the gnome squeaks a B note loudly.",
              "There is an altar to Tyr (lawful) here.\nThings that are here:\na jaguar corpse"]:
        assert benign(m), m
    for m in ["The soldier ant bites!", "You are hit by an arrow.", "A board beneath you squeaks loudly."]:
        assert not benign(m), m


def test_kernel_refuses_exec_at_an_open_prompt():
    from nh.game import Game, Snap, Timing
    from nh.kernel import Kernel
    from nh.parse import State
    g = Game(term=None, timing=Timing.local())
    k = Kernel(g)
    g.last = Snap(screen=mk({}), state=State("object", prompt="What do you want to drop? [a-z or ?*]"),
                  status=parse_status(mk({22: STATUS1, 23: "Dlvl:1 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:5"})))
    out = k.start_exec("print('hi')")
    assert out["status"] == "error" and "prompt" in out["error"] and "drop" in out["error"]


def test_sacrifice_evidence_recorded(tmp_path):
    from nh.game import Snap
    from nh.parse import State
    from nh.tracker import Tracker
    g = _guard_game()
    t = Tracker(g, tmp_path / "hs.json")
    t.need_overview = False
    scr = mk({22: STATUS1, 23: "Dlvl:13 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:7100"}, cursor=(10, 5))
    s = Snap(screen=scr, state=State("command"), status=parse_status(scr),
             messages=["Your sacrifice is consumed in a flash of light!", "You glimpse a four-leaf clover at your feet."])
    t.on_step(s)
    assert t.state["prayer_evidence"] == [{"turn": 7100, "kind": "zero"}]


def test_shop_rect_on_east_and_south_doors_in_minetown():
    """p4 shift 2: in Minetown the square outside a shop door is lit street floor; the door scan tried east/south
    first and recorded the street as the shop (guards on in the street, off inside). Screens from p4's run."""
    from nh.game import Snap
    from nh.parse import State
    status = {22: STATUS1, 23: "Dlvl:8 $:107 HP:69(78) Pw:10(10) AC:3 Xp:7 T:4131"}
    bojolali = {    # door (45,16) in the shop's EAST wall; the street and a gnome lord 'h' outside
        11: '                                   -----',
        12: '                        +           ....',
        13: '                        |.         -...   --+----------',
        14: '                       --...--+-   |..-    ........G..',
        15: '                        ........   |..|  -----....--------',
        16: '                          #.....----..|  |%%.@(.h.|......|',
        17: '                        -....{........|  |%!@|....-...@).|',
        18: '                        -  |....#.....--------....|......|',
        19: '                           --.....................|-------',
        20: '                            --------..-------.-...|',
    }
    izchak = {      # door (30,14) in the SOUTH wall; your dropped pick-axe '(' lies outside it
        10: '                            -----',
        11: '                            |(((|  -----',
        12: '                        +   |@((|   ....',
        13: '                        |.  |..G|  -...   --+----------',
        14: '                       --...--@--  |..-    ...........',
        15: '                       |......(.|  |..|  -----....--------',
        16: '                       |  #.....----..|  |%..-....|......|',
        17: '                        -....{........|  |%!.|....-....).|',
        18: '                        -..|....#.....--------....|......|',
        19: '                        .. --.....................|-------',
        20: '                      -..-  --------..-------.-...|',
    }
    chibougamau = {  # door (44,8) in the SOUTH wall of a shop in the town's NE corner
        2: '                                  ---',
        3: '                                   ..------',
        4: '                                    ......|----',
        5: '                                     .....|)//|',
        6: '                                       ...|!@?|',
        7: '                                       -..|G..|',
        8: '                                       |.%--@--- -',
        9: '                                       +.............-',
        10: '                            -----      |......--+-   |',
        11: '                            |(((|+------..{%..|',
        12: '                        +   |(((|......)......|',
        13: '                        |.  |...|-+-.....---|----------',
        14: '                       --...--|-|  |.%-%-- ...........',
        15: '                       |......(.|  |..|..-----....--------',
    }
    cases = [(bojolali, (45, 16), (46, 16), "Bojolali's delicatessen", [42, 16, 44, 17]),
             (izchak, (30, 14), (30, 15), "Izchak's lighting store", [29, 11, 31, 13]),
             (chibougamau, (44, 8), (44, 9), "Chibougamau's general store", [43, 5, 45, 7])]
    for rows, door, outside, name, rect in cases:
        for prev in (outside, None, (door[0] * 2 - outside[0], door[1] * 2 - outside[1])):
            # the walls decide, whatever the previous square says (even a wrong one)
            g = _guard_game()
            scr = mk({**rows, **status}, cursor=door)
            s = Snap(screen=scr, state=State("command"), status=parse_status(scr))
            g._note_shop(s, [f'"Velkommen, p4!  Welcome to {name}!"'], prev_hero=prev)
            assert g.shops[g.level_key(s.status)] == [rect + [name]], (name, prev)
            inside = (rect[0], rect[1])
            assert g.shop_at(inside, s.status) == name and g.shop_at(door, s.status) == name
            assert not g.shop_at((outside[0] + (outside[0] - door[0]), outside[1] + (outside[1] - door[1])),
                                 s.status)
    # a wrong old record of the same shop (the street, from an older harness) is replaced on the next welcome
    g = _guard_game()
    scr = mk({**izchak, **status}, cursor=(30, 14))
    s = Snap(screen=scr, state=State("command"), status=parse_status(scr))
    g.shops[g.level_key(s.status)] = [[24, 15, 31, 19, "Izchak's lighting store"],
                                      [46, 14, 49, 19, "Bojolali's delicatessen"]]
    g._note_shop(s, ['"Velkommen, p4!  Welcome again to Izchak\'s lighting store!"'], prev_hero=(30, 15))
    assert g.shops[g.level_key(s.status)] == [[46, 14, 49, 19, "Bojolali's delicatessen"],
                                              [29, 11, 31, 13, "Izchak's lighting store"]]


def test_shop_rect_spellbook_and_dark_street():
    """A spellbook '+' in the scan line doesn't end the shop scan; when the walls can't tell (a dark street), the
    side you came from is the outside."""
    from nh.game import Snap
    from nh.parse import State
    status = {22: STATUS1, 23: "Dlvl:6 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:5"}
    rows = {3: "          -------",
            4: "          |?+?.?|",
            5: "          |.@...|",
            6: "          |?.+..|",
            7: "          ---@---",
            8: "            ...."}                     # lit bits of a street outside, the rest unseen
    for prev in ((13, 8), (12, 8), None):
        g = _guard_game()
        scr = mk({**rows, **status}, cursor=(13, 7))
        s = Snap(screen=scr, state=State("command"), status=parse_status(scr))
        g._note_shop(s, ['"Hello, p3!  Welcome to Asidonhopo\'s rare books!"'], prev_hero=prev)
        assert g.shops[g.level_key(s.status)] == [[11, 4, 15, 6, "Asidonhopo's rare books"]]


def test_zoo_welcome_is_not_a_shop_and_extcmd_guard():
    import pytest
    from nh.game import Snap
    from nh.parse import State
    g = _guard_game()
    rows = {3: "  ------------", 4: "  |.)).[[....|", 5: "  |@.........|", 6: "  |..........|", 7: "  ------------",
            22: STATUS1, 23: "Dlvl:15 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:5"}
    scr = mk(rows, cursor=(3, 5))
    s = Snap(screen=scr, state=State("command"), status=parse_status(scr))
    g._note_shop(s, ["Welcome to David's treasure zoo!"])
    assert not g.shops
    g._note_shop(s, ["Velkommen, p1!  Welcome to Asidonhopo's hardware store!"])
    assert g.shops
    ext = Snap(screen=scr, state=State("extcmd", prompt="# force"), status=s.status)
    with pytest.raises(PermissionError, match="extended-command"):
        g._guard(ext, b"s", force=False)
    g._guard(ext, b"pray\r", force=False)
    g._guard(ext, b"\x1b", force=False)


def test_resistance_aware_ratings_and_notes():
    from nh.danger import note_for, threat_level
    assert threat_level("killer bee", 10, 120) == "dangerous"
    assert threat_level("killer bee", 10, 120, resists={"poison"}) != "dangerous"
    assert "you resist" in note_for("killer bee", 10, {"poison"})
    assert threat_level("soldier ant", 10, 120, resists={"poison"}) == "dangerous"   # fast and strong anyway


def test_nested_monster_filters_combine():
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    g = Game(term=None, timing=Timing.local())
    k = Kernel(g)
    with k.ns["monster_filter"](lambda m: m["desc"] != "killer bee"):
        with k.ns["monster_filter"](lambda m: True):          # a helper's own filter inside
            f = k.new_monster_filter
            assert not f({"desc": "killer bee"}) and f({"desc": "soldier ant"})
        assert not k.new_monster_filter({"desc": "killer bee"})
    assert k.new_monster_filter is None


def test_crowded_level_far_newcomers_do_not_pause():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_nh_monitor import snap as msnap  # noqa: E402
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    g = Game(term=None, timing=Timing.local())
    k = Kernel(g)
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    s = msnap({}, 11)
    s.monsters = [{"ch": "d", "x": 10 + i, "y": 3, "desc": "jackal", "new": False, "dist": 20} for i in range(9)]
    s.monsters += [{"ch": "r", "x": 60, "y": 3, "desc": "sewer rat", "new": True, "dist": 25},
                   {"ch": "a", "x": 61, "y": 3, "desc": "soldier ant", "new": True, "dist": 25, "note": "fast"}]
    k._check_events(msnap({}, 10), s)
    assert reasons and "soldier ant" in reasons[-1] and "sewer rat" not in reasons[-1]


def test_trapped_closet_engraving_marks_the_niche():
    # mklev.c makeniche(): "ad aerarium" in the dust just inside a (secret) door of the room's top or
    # bottom wall marks a one-time teleporter in the closet beyond the door
    from nh.game import Snap, engraving_is
    from nh.parse import State, Status
    assert engraving_is("ad ae?ar?um", "ad aerarium") and engraving_is("d aerariun", "ad aerarium")
    assert engraving_is("V|ad was ?ere", "Vlad was here")
    assert not engraving_is("Elbereth", "ad aerarium") and not engraving_is("ad aerarium", "Vlad was here")
    g = _guard_game()
    rows = {4: "          -------", 5: "          |.@...|", 6: "          |.....|", 7: "          -------",
            22: STATUS1, 23: "Dlvl:8 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:5"}
    s = Snap(screen=mk(rows, cursor=(12, 5)), state=State("command"), status=Status(ok=True, ldesc="Dlvl:8", dlvl=8))
    # random graffiti with the same words is not a closet marker
    g._remember_here(s, ["There's some graffiti on the floor here.", 'You read: "ad aerarium".'])
    assert not g.niches and not getattr(s, "niche_note", "")
    g._remember_here(s, ["Something is written here in the dust.", 'You read: "ad ae?arium".'])
    assert g.niches["Dlvl:8"] == {(12, 3): "teleport"}          # the top wall is above: closet at y-2
    assert (12, 3) in g.avoid["Dlvl:8"]
    assert "GOLD VAULT" in s.niche_note and "LEVEL TELEPORTER" not in s.niche_note
    # reading it again doesn't raise a new note
    s2 = Snap(screen=s.screen, state=State("command"), status=s.status)
    g._remember_here(s2, ["Something is written here in the dust.", 'You read: "ad aerarium".'])
    assert not s2.niche_note
    # a trap door marker on the bottom row (the wall is below)
    rows[5], rows[6] = "          |.....|", "          |...@.|"
    s3 = Snap(screen=mk(rows, cursor=(14, 6)), state=State("command"), status=Status(ok=True, ldesc="Dlvl:8", dlvl=8))
    g._remember_here(s3, ["Something is written here in the dust.", 'You read: "Vlad was here".'])
    assert g.niches["Dlvl:8"][(14, 8)] == "trapdoor" and "TRAP DOOR" in s3.niche_note
    g._annotate(s3)
    from nh.render import render
    assert "trapped closet(s), avoided: (12,3) one-time teleporter" in render(s3)


def test_guard_stunned_blows_near_pet_or_peaceful():
    import pytest
    g = _guard_game()
    jackal = {"x": 11, "y": 5, "desc": "jackal", "dist": 1}
    kitten = {"x": 9, "y": 5, "desc": "tame kitten", "tame": True, "dist": 1}
    s = _cmd_snap([jackal, kitten], conditions=["Stun"])
    with pytest.raises(PermissionError):
        g._guard(s, b"Fl", force=False)          # the blow can go astray into the kitten
    g._guard(s, b"Fl", force=True)
    g._guard(s, b"l", force=False)               # a plain stunned step into a pet just swaps places
    g._guard(_cmd_snap([jackal], conditions=["Stun"]), b"Fl", force=False)   # only the hostile: fine
    shk = {"x": 10, "y": 4, "desc": "peaceful shopkeeper", "peaceful": True, "dist": 1}
    with pytest.raises(PermissionError):
        g._guard(_cmd_snap([jackal, shk], conditions=["Conf"]), b"Fl", force=False)
    g._guard(_cmd_snap([jackal, kitten]), b"Fl", force=False)                # not stunned: fine


def test_diagonal_doorway_refusal_teaches_the_door():
    # a door the harness never saw (a sleeping monster on it, then its loot pile): NetHack's refusal says
    # where it is, so routes stop trying the diagonal step
    from nh.game import Game, Snap, Timing
    from nh.parse import classify, parse_status
    g = Game(term=None, timing=Timing.local())
    base = {5: "          @[", 22: STATUS1, 23: "Dlvl:1 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:5"}
    scr = mk(base, cursor=(10, 5))
    g.last = Snap(screen=scr, state=classify(scr), status=parse_status(scr))

    def fake_send(data):
        rows = dict(base)
        rows[0] = "You can't move diagonally into an intact doorway."
        s2 = mk(rows, cursor=(10, 5))
        return Snap(screen=s2, state=classify(s2), status=parse_status(s2))
    g.send_bytes = fake_send
    g.step("u")
    assert g.terrain_seen[g.level_key()][(11, 4)] == "D"

    def fake_send2(data):
        rows = dict(base)
        rows[0] = "You can't move diagonally out of an intact doorway."
        s2 = mk(rows, cursor=(10, 5))
        return Snap(screen=s2, state=classify(s2), status=parse_status(s2))
    g.send_bytes = fake_send2
    g.step("n")
    assert g.terrain_seen[g.level_key()][(10, 5)] == "D"


def test_it_kill_dates_the_corpse_and_pickaxe_wield_note():
    g = _guard_game()
    g.last = _cmd_snap([])
    g.record_kill("it", (11, 5), 100)
    assert g.corpse_age("troll", (11, 5), 120) == 20        # the invisible troll killed there
    assert g.corpse_age("troll", (11, 5), 200) is None      # too long ago to be sure
    assert g.corpse_age("troll", (12, 5), 120) is None
    g.wielded, g.wielded_class = "a pick-axe", None
    assert "digging tool" in g.wield_note()
    g.wielded = "a blessed +6 long sword named Excalibur"
    assert g.wield_note() == ""


def test_elbereth_guard_lets_you_hit_monsters_that_ignore_it():
    # mon.c setmangry(): hitting a monster that ignores Elbereth (onscary() false: @ humans, minotaurs...)
    # from your Elbereth square is no hypocrisy
    import pytest
    g = _guard_game()
    soldier = {"x": 11, "y": 5, "ch": "@", "desc": "soldier", "dist": 1}
    s = _cmd_snap([soldier])
    g._remember_here(s, ["Something is written here in the dust.", 'You read: "Elbereth".'])
    g._guard(s, b"Fl", force=False)                              # a soldier: allowed
    jackal = {"x": 11, "y": 5, "ch": "d", "desc": "jackal", "dist": 1}
    with pytest.raises(PermissionError):
        g._guard(_cmd_snap([jackal]), b"Fl", force=False)       # a jackal respects it: hypocrisy
    peaceful = {"x": 11, "y": 5, "ch": "@", "desc": "peaceful watchman", "peaceful": True, "dist": 1}
    with pytest.raises(PermissionError):
        g._guard(_cmd_snap([peaceful]), b"Fl", force=False)
    mino = {"x": 11, "y": 5, "ch": "H", "desc": "minotaur", "dist": 1}
    g._guard(_cmd_snap([mino]), b"Fl", force=False)


def test_clairvoyance_browse_cursor_is_left_by_the_step():
    # QA round 7 R7-4: "You sense your surroundings." opens a getpos map browse by itself (detect.c
    # do_vicinity_map); the step leaves it with Esc so a script's next keys don't move that cursor
    from nh.game import Game, Snap, Timing
    from nh.parse import GETPOS_HINTS, classify, parse_status
    g = Game(term=None, timing=Timing.local())
    base = {5: "          @.", 22: STATUS1, 23: "Dlvl:42 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:5"}
    scr = mk(base, cursor=(10, 5))
    g.last = Snap(screen=scr, state=classify(scr), status=parse_status(scr))
    sent = []

    def snap_of(rows, cursor):
        s2 = mk(rows, cursor=cursor)
        return Snap(screen=s2, state=classify(s2), status=parse_status(s2))

    def fake_send(data):
        sent.append(data)
        if data == b"s":
            rows = dict(base)
            rows[0] = "You sense your surroundings.--More--"
            return snap_of(rows, (36, 0))
        if data in (b"\r", b" "):                      # the --More-- dismissed: the browse cursor on the map
            rows = dict(base)
            rows[0] = "(For instructions type a '?')"      # do_name.c getpos() with flags.verbose
            assert any(h in rows[0] for h in GETPOS_HINTS)
            return snap_of(rows, (15, 8))
        return snap_of(base, (10, 5))                  # Esc: back at the command prompt
    g.send_bytes = fake_send
    s = g.step("s")
    assert s.state.kind == "command" and sent[-1] == b"\x1b"
    assert any("sense your surroundings" in m for m in s.messages)


def test_status_short_forms_from_a_long_line():
    # wintty.c make_things_fit: a long bottom line shows short condition/encumbrance words and "Dl:"
    s = mk({22: STATUS1, 23: "Dlvl:36 $:0 HP:165(165) Pw:41(41) AC:-8 Xp:15/43210 T:24189 Hungry Bl Df"})
    st = parse_status(s)
    assert st.ok and st.conditions == ["Blind", "Deaf"] and st.hunger == "Hungry" and not st.cut
    s = mk({22: STATUS1, 23: "Dl:36 $:1234 HP:165(165) Pw:41(41) AC:-8 Xp:15 T:24189 Weak Ovld Sto Slm Str"})
    st = parse_status(s)
    assert st.ok and (st.ldesc, st.dlvl, st.gold) == ("Dlvl:36", 36, 1234) and not st.cut
    assert st.encumbrance == "Overloaded" and st.conditions == ["Stone", "Slime", "Strngl"]
    for words, conds in (("Ston Slim Stngl Fpois Ill Blnd Def", ["Stone", "Slime", "Strngl", "FoodPois",
                                                                  "TermIll", "Blind", "Deaf"]),
                         ("Poi Ill St Cf Hl Lv Fl Rd", ["FoodPois", "TermIll", "Stun", "Conf", "Hallu", "Lev", "Fly",
                                                        "Ride"]),
                         ("Burden Stun Cnf Hal Lev Fly Rid", ["Stun", "Conf", "Hallu", "Lev", "Fly", "Ride"])):
        st = parse_status(mk({22: STATUS1, 23: f"Dlvl:3 $:0 HP:17(21) Pw:1(1) AC:6 Xp:2 T:512 {words}"}))
        assert st.ok and st.conditions == conds, words
    st = parse_status(mk({22: STATUS1, 23: "Dlvl:3 $:0 HP:17(21) Pw:1(1) AC:6 Xp:2 T:512 Strs"}))
    assert st.encumbrance == "Stressed" and st.conditions == []
    st = parse_status(mk({22: STATUS1, 23: "Dlvl:3 $:0 HP:17(21) Pw:1(1) AC:6 Xp:2 T:512 Strain Str"}))
    assert st.encumbrance == "Strained" and st.conditions == ["Strngl"]


def test_status_line_full_flags_a_possibly_cut_word():
    line = "Dl:48 $:12345 HP:250(250) Pw:120(120) AC:-25 Xp:25/9876543 T:55000 Satiated Brd Sto St"
    line = line[:79]
    st = parse_status(mk({22: STATUS1, 23: line}))
    assert st.ok and st.cut == line.split()[-1] and "STATUS LINE FULL" in st.short()
    st = parse_status(mk({22: STATUS1, 23: "Dlvl:3 $:0 HP:17(21) Pw:1(1) AC:6 Xp:2 T:512 Blind"}))
    assert not st.cut and "STATUS LINE FULL" not in st.short()


def test_hole_plunge_records_no_stairs_and_rescan_drops_stale_ones():
    # p3 shift 11 #1151: '>' on a known hole plunges you through with no message (trap.c fall_through,
    # TOOKPLUNGE, one level): the landing square was recorded as up stairs
    from nh.game import Game, Snap, Timing
    from nh.parse import State
    g = Game(term=None, timing=Timing.local())

    def snap_at(hero, dl):
        scr = mk({22: STATUS1, 23: f"Dlvl:{dl} $:0 HP:10(10) Pw:1(1) AC:6 Xp:1 T:5"}, cursor=hero)
        return Snap(screen=scr, state=State("command"), status=parse_status(scr))     # (hero = the cursor)
    cur, new = snap_at((71, 15), 22), snap_at((5, 16), 23)
    old_key, new_key = g.level_key(cur.status), g.level_key(new.status)
    g.traps[old_key] = {(71, 15)}
    g._note_arrival(cur, new, b">", ["You see here a worthless piece of red glass."], old_key, True)
    assert (5, 16) not in g.terrain_seen.get(new_key, {})
    g.traps[old_key] = set()                                  # (no trap known: the look without stairs tells)
    g._note_arrival(cur, new, b">", ["You see here a worthless piece of red glass."], old_key, True)
    assert (5, 16) not in g.terrain_seen.get(new_key, {})
    g._note_arrival(cur, new, b">", [], old_key, True)        # a plain staircase trip still records it
    assert g.terrain_seen[new_key][(5, 16)] == "<"
    g.terrain_seen[new_key][(8, 8)] = "<"
    g.merge_terrain(new_key, {"features": {(8, 8): "<"}, "plain": {(5, 16)}, "traps": set()}, hero=(9, 9))
    assert g.terrain_seen[new_key] == {(8, 8): "<"}


def test_remembered_door_under_a_gas_cloud_stays_a_feature():
    # p1 shift 32 #646: a closed door vanished from features under a poison gas cloud
    from nh.game import Snap
    from nh.mapscan import features_in_view
    from nh.parse import classify, parse_status
    scr = mk({5: "          |.@.#.|", 22: STATUS1, 23: "Dlvl:38 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:5"},
             cursor=(12, 5))
    scr.fg[5][14] = 10                               # bright green '#': a poison gas cloud
    s = Snap(screen=scr, state=classify(scr), status=parse_status(scr))
    s.feature_mem = {(14, 5): "D"}
    feats = features_in_view(s)
    assert any((f["x"], f["y"]) == (14, 5) and f["name"].startswith("door (remembered") for f in feats)
    s.feature_mem = {}
    assert not any(f["name"].startswith("door (remembered") for f in features_in_view(s))


def test_bare_y_or_n_at_a_paranoid_prompt_types_the_word():
    # p2 shift 32 #118-#129: "Continue eating? (yes) [no]" is a text prompt (paranoid_confirmation:eat); a bare
    # 'n' was typed into it ("nnnnnnnnn") and the prompt stayed open
    import pytest
    from nh.game import Game, Snap, Timing
    from nh.parse import classify, parse_status
    g = Game(term=None, timing=Timing.local())
    base = {5: " " * 10 + "@", 22: STATUS1, 23: "Dlvl:1 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:5"}
    q = "Continue eating? (yes) [no] "

    def at_prompt(typed=""):
        rows = dict(base)
        rows[0] = q + typed
        scr = mk(rows, cursor=(len(q + typed), 0))
        return Snap(screen=scr, state=classify(scr), status=parse_status(scr))
    g.last = at_prompt()
    assert g.last.state.kind == "yn" and g.last.state.choices == "yes/no"
    sent, typed = [], {"t": ""}

    def fake_send(data):
        sent.append(data)
        if data.endswith(b"\r") or typed.get("done"):
            typed["done"] = True
            rows = dict(base)
            rows[0] = "You stop eating."
            scr = mk(rows, cursor=(10, 5))
            return Snap(screen=scr, state=classify(scr), status=parse_status(scr))
        typed["t"] += data.decode()
        return at_prompt(typed["t"])
    g.send_bytes = fake_send
    s = g.step("n")
    assert b"".join(sent).startswith(b"no\r") and s.state.kind == "command"
    # 'y' at "Continue eating?" is still refused by the choking guard (the word's first letter is checked)
    g.last = at_prompt()
    sent.clear()
    typed.update(t="", done=False)
    with pytest.raises(PermissionError, match="continue eating"):
        g.step("y")
    assert sent == []


def test_life_saving_is_not_game_over():
    # p1 shift 34 #146/#196: "You die...  But wait...  Your medallion begins to glow!--More--" paused as GAME OVER
    from nh.game import Game, Snap, Timing
    from nh.parse import classify, parse_status
    base = {5: " " * 10 + "@", 22: STATUS1, 23: "Dlvl:37 $:0 HP:0(165) Pw:1(1) AC:-8 Xp:15/1 T:27383"}

    def page(text, hp="0"):
        rows = dict(base)
        rows[0] = text
        rows[23] = rows[23].replace("HP:0(", f"HP:{hp}(")
        cur = (len(text), 0) if text.endswith("--More--") else (10, 5)
        scr = mk(rows, cursor=cur)
        return Snap(screen=scr, state=classify(scr), status=parse_status(scr))
    saved = page("You die...  But wait...  Your medallion begins to glow!--More--")
    assert saved.state.kind == "more"
    lone = page("You die...--More--")
    assert lone.state.kind == "gameover"
    # a lone death page is stepped past (nothing to decide there): life saving speaks on the next page
    g = Game(term=None, timing=Timing.local())
    g.last = page("", hp="12")
    g.last = Snap(screen=mk({**base, 23: base[23].replace("HP:0(", "HP:12(")}, cursor=(10, 5)),
                  state=classify(mk(base, cursor=(10, 5))), status=parse_status(mk(base, cursor=(10, 5))))
    pages = iter([lone, page("But wait...  Your medallion begins to glow!--More--"),
                  page("You feel much better!  The medallion crumbles to dust!--More--", hp="165"),
                  page("", hp="165")])
    g.send_bytes = lambda data: next(pages)
    s = g.step("s")
    assert s.state.kind == "command" and "Your medallion begins to glow!" in s.messages
    # a real death still stops at the end-of-game question
    dywypi = page("Do you want your possessions identified? [ynq] (n) ")
    dywypi.screen.cursor = (len("Do you want your possessions identified? [ynq] (n) "), 0)
    pages = iter([lone, Snap(screen=dywypi.screen, state=classify(dywypi.screen), status=dywypi.status)])
    g.last = page("", hp="12")
    g.send_bytes = lambda data: next(pages)
    s = g.step("s")
    assert s.state.kind == "gameover"


def test_arrival_prunes_memory_the_game_map_contradicts():
    # p1 shift 35 #306: after a level teleport to DL2 the obs listed DL3's two '>' (and an up staircase on
    # a blank square) from stale memory filed under DL2: the first settled map of a level drops remembered
    # features where the game's own map shows nothing, plain floor, or a wall
    from nh.game import Game, Snap, Timing
    from nh.parse import classify, parse_status
    g = Game(term=None, timing=Timing.local())
    old = mk({5: "   @", 22: STATUS1, 23: "Dlvl:44 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:5"}, cursor=(3, 5))
    g.last = Snap(screen=old, state=classify(old), status=parse_status(old))
    rows = {4: " " * 20 + "|...|", 7: " " * 44 + "|...>..|", 16: " " * 44 + "|.@....|",
            18: " " * 44 + "|......|", 22: STATUS1, 23: "Dlvl:2 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:6"}

    def fake_send(data):
        s2 = mk(rows, cursor=(46, 16))
        return Snap(screen=s2, state=classify(s2), status=parse_status(s2))
    g.send_bytes = fake_send
    g.terrain_seen["Dlvl:2"] = {(46, 18): ">", (29, 16): ">", (76, 4): "<", (20, 4): "\\", (48, 7): ">",
                                (60, 12): "^"}
    g.stair_links["Dlvl:2"] = {(76, 4): "Dlvl:1", (48, 7): "Dlvl:3"}
    s = g.step("p")
    assert g.terrain_seen["Dlvl:2"] == {(48, 7): ">", (60, 12): "^"}          # (a portal never goes)
    assert g.stair_links["Dlvl:2"] == {(48, 7): "Dlvl:3"}
    assert s.feature_mem == {(48, 7): ">", (60, 12): "^"}
    # a level the game may have forgotten (amnesia): its blank squares keep the harness memory
    g.last = Snap(screen=old, state=classify(old), status=parse_status(old))
    g.terrain_seen["Dlvl:2"][(76, 4)] = "<"
    g.level_flags["Dlvl:2"] = {"forgotten"}
    g.step("p")
    assert g.terrain_seen["Dlvl:2"][(76, 4)] == "<"
    # amnesia marks every known level; a deja-vu arrival marks that one
    g2 = Game(term=None, timing=Timing.local())
    g2.terrain_seen = {"Dlvl:3": {(1, 2): ">"}, "Dlvl:4": {}}
    g2._note_forgetting(Snap(screen=old, state=classify(old), status=parse_status(old)),
                        ["Who was that Maud person anyway?"])
    assert all("forgotten" in g2.level_flags[k] for k in ("Dlvl:3", "Dlvl:4", "Dlvl:44"))
    g3 = Game(term=None, timing=Timing.local())
    g3._note_forgetting(Snap(screen=old, state=classify(old), status=parse_status(old)),
                        ["You have a sense of deja vu."])
    assert g3.level_flags["Dlvl:44"] == {"forgotten"}


def test_no_new_throne_from_engulf_corners_or_unsettled_frames():
    # p1's Sokoban memory held throne pairs 2 apart diagonally: a fire vortex's (yellow) engulf-ring corners
    # NE/SW of the hero, or a yellow acid ray left on screen by a --More--
    from nh.game import Game, Snap, Timing
    from nh.parse import State
    g = Game(term=None, timing=Timing.local())
    scr = mk({7: "     \\@   \\", 6: "       \\", 22: STATUS1, 23: "Dlvl:11 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:5"},
             cursor=(6, 7))
    for x, y in ((5, 7), (7, 6), (10, 7)):
        scr.fg[y][x] = 11
    s = Snap(screen=scr, state=State("more"), status=parse_status(scr))
    g._remember_terrain(s, [])
    assert not g.terrain_seen.get(g.level_key(s.status))             # nothing new from a --More-- frame
    s = Snap(screen=scr, state=State("command"), status=parse_status(scr))
    g._remember_terrain(s, [])
    assert g.terrain_seen[g.level_key(s.status)] == {(5, 7): "\\", (10, 7): "\\"}   # not the NE corner (7,6)
    g.terrain_seen[g.level_key(s.status)][(7, 6)] = "\\"                               # a known one stays
    g._remember_terrain(s, [])
    assert (7, 6) in g.terrain_seen[g.level_key(s.status)]
    # the ring captured with the cursor elsewhere (not on its '@'): its yellow corners still aren't thrones
    ring = mk({13: " " * 49 + "/-\\", 14: " " * 49 + "|@|", 15: " " * 49 + "\\-/", 5: "          @",
               22: STATUS1, 23: "Dlvl:12 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:6"}, cursor=(10, 5))
    for y in (13, 14, 15):
        for x in (49, 50, 51):
            ring.fg[y][x] = 11
    r = Snap(screen=ring, state=State("command"), status=parse_status(ring))
    g._remember_terrain(r, [])
    assert not g.terrain_seen.get(g.level_key(r.status))


def test_quest_assignment_learned_from_speech_and_overview(tmp_path):
    # p1 shift 35 #882/#896: after the Norn assigned the quest, travel()/step() still refused every square
    # next to her ("one of 7 tries"): the assignment (quest.txt QT_ASSIGNQUEST) sets got_quest for good
    from nh.game import Game, Snap, Timing
    from nh.parse import classify
    from nh.tracker import Tracker
    g = Game(term=None, timing=Timing.local())
    g._note_quest(['"Let me read your fate..."'])
    assert not g.quest_given
    g._note_quest(['"It is not clear, Brunhild, for my sight is limited without our relic.\n'
                   'But it is now likely that you can defeat Lord Surtur, and recover\nthe Orb of Fate.'])
    assert g.quest_given
    g2 = Game(term=None, timing=Timing.local())
    g2._note_quest(['"Domo Hiro-san, indeed you are ready.  I can now tell you what it is that I require of you.'])
    assert g2.quest_given
    # ^O: "Home. / Given quest by the Norn." (dungeon.c print_mapseen) — and the flag survives a restart
    g3 = Game(term=None, timing=Timing.local())
    t = Tracker(g3, tmp_path / "hs.json")
    scr = mk({22: STATUS1, 23: "Home 1 $:0 HP:10(10) Pw:1(1) AC:6 Xp:14/0 T:5"}, cursor=(10, 5))
    snap = Snap(screen=scr, state=classify(scr), status=parse_status(scr))
    t._parse_overview("The Quest:\nLevel 1: <- You are here.\nA fountain.\nHome.\nGiven quest by the Norn.",
                      snap, "Home 1")
    assert g3.quest_given
    t.save()
    g4 = Game(term=None, timing=Timing.local())
    Tracker(g4, tmp_path / "hs.json")
    assert g4.quest_given


def test_history_reloads_from_the_event_log(tmp_path):
    # p3 shift 16 #1: `bin/nh history` printed "(no messages yet)" after a daemon restart
    import json as _json
    from nh.game import Game, Timing
    log = tmp_path / "events.jsonl"
    with open(log, "w") as f:
        f.write(_json.dumps({"ev": "step", "n": 1, "keys": "h", "turn": 10, "messages": ["You hit the newt!"]}) + "\n")
        f.write(_json.dumps({"ev": "describe", "cells": {}}) + "\n")
        f.write(_json.dumps({"ev": "step", "n": 2, "keys": "<C-o>", "turn": 10, "messages": ["The Dungeons"]}) + "\n")
        f.write(_json.dumps({"ev": "step", "n": 3, "keys": "h", "turn": 11, "messages": ["You kill the newt!"]}) + "\n")
    g = Game(term=None, timing=Timing.local(), log_path=log)
    assert g.load_history() == 2
    assert g.history == [(10, "You hit the newt!"), (11, "You kill the newt!")]
    assert g.load_history(max_bytes=60) <= 1                         # (a partial first line is skipped)


def test_wield_message_at_a_direction_prompt_is_noted():
    # p3 shift 17 #196: applying a pick-axe prints "You now wield ..." with the dig-direction prompt (the cursor
    # on the prompt, no hero on the map) — the wield note must still learn it (fight() then bashed with it)
    from nh.game import Game, Snap, Timing
    from nh.parse import classify, parse_status
    g = Game(term=None, timing=Timing.local())
    base = {5: "          @", 22: STATUS1, 23: "Dlvl:1 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:5"}
    scr = mk(base, cursor=(10, 5))
    g.last = Snap(screen=scr, state=classify(scr), status=parse_status(scr))
    g._note_wield(["a - a +1 long sword (weapon in hand)."], 5)
    assert g.main_weapon == {"letter": "a", "text": "a +1 long sword"}     # the first weapon seen in hand
    rows1 = dict(base)
    rows1[0] = "You now wield an uncursed pick-axe.--More--"
    rows2 = dict(base)
    rows2[0] = "In what direction do you want to dig? [ln>]"
    screens = [mk(rows1, cursor=(43, 0)), mk(rows2, cursor=(44, 0))]

    def fake_send(data):
        s2 = screens.pop(0) if len(screens) > 1 else screens[0]
        return Snap(screen=s2, state=classify(s2), status=parse_status(s2))
    g.send_bytes = fake_send
    s = g.step("e")
    assert s.state.kind == "direction" and "You now wield an uncursed pick-axe." in s.messages
    assert g.wielded == "an uncursed pick-axe" and g.wield_tool
    assert "digging tool" in s.wield_note or "digging tool" in g.wield_note()


def test_usual_weapon_note_and_promotion():
    # p4 shift 1 #2208: a pause between "w + spare dagger, #force" and the re-wield left the dagger in hand, and
    # the obs said nothing
    g = _guard_game()
    g._note_wield(["a - a +1 long sword (weapon in hand)."], 100)
    assert g.main_weapon["letter"] == "a" and g.wield_note() == ""
    # (the live 'w' echo with pushweapon: the old weapon's "alternate weapon; not wielded" line comes after)
    g._note_wield(["b - an orcish dagger (weapon in hand).", "a - a +1 long sword (alternate weapon; not wielded)."],
                  200)
    assert "not your usual weapon (a - a +1 long sword)" in g.wield_note() and "wa" in g.wield_note()
    g._promote_weapon(230)
    assert g.main_weapon["letter"] == "a"                     # 30 turns: still a temporary weapon
    g._promote_weapon(250)
    assert g.main_weapon == {"letter": "b", "text": "an orcish dagger"} and g.wield_note() == ""
    g._note_wield(["You now wield a pick-axe."], 260)        # applied to dig: a tool, never the usual weapon
    assert g.wield_tool and "digging tool" in g.wield_note()
    g._promote_weapon(400)
    assert g.main_weapon["letter"] == "b"
    g._note_wield(["You are empty handed."], 401)
    assert "EMPTY-HANDED" in g.wield_note()


def test_welded_cursed_weapon_is_the_usual_weapon():
    # the live game T:3838: "The long sword named Excalibur welds itself to your hand!" (no inventory line comes):
    # the old weapon is no longer in hand; once inventory() shows the cursed weapon in hand, it IS the usual
    # weapon (welded) — no "wa to wield it again" that NetHack would refuse
    g = _guard_game()
    g._note_wield(["a - an uncursed +1 long sword (weapon in hand)."], 3000)
    assert g.main_weapon["letter"] == "a"
    g._note_wield(["The long sword named Excalibur welds itself to your hand!"], 3838)
    assert g.wielded is None and g.wielded_letter is None           # unknown until the next inventory()
    g.set_wielded("a cursed long sword named Excalibur (weapon in hand)", "Weapons", "L", False, 3840)
    assert g.main_weapon == {"letter": "L", "text": "a cursed long sword named Excalibur"} and g.wield_note() == ""


def test_guard_confused_steps_next_to_lava_or_water():
    import pytest
    g = _guard_game()
    s = _cmd_snap([], conditions=["Stun"])
    s.screen.chars[6] = (" " * 11 + "}").ljust(80)
    s.screen.fg[6][11] = 1                                           # red: lava
    with pytest.raises(PermissionError, match="Stun next to lava"):
        g._guard(s, b"h", force=False)                               # ANY step can go astray while stunned
    with pytest.raises(PermissionError):
        g._guard(s, b"_", force=False)                               # travel too
    with pytest.raises(PermissionError):
        g._guard(s, b"H", force=False)                               # and a rush
    g._guard(s, b"Fh", force=False)                                  # a blow never moves you
    g._guard(s, b"s", force=False)
    g._guard(s, b"h", force=True)
    g._guard(_cmd_snap([], conditions=["Stun", "Lev"]), b"h", force=False)
    s2 = _cmd_snap([], conditions=["Conf"])
    g._guard(s2, b"h", force=False)                                  # no water/lava next to you


def test_grave_is_a_feature_not_a_wall():
    # p3 shift 17 #438: a bright white '|' inside a room is a grave (walkable), not a wall
    from nh.game import Snap
    from nh.mapscan import features_in_view
    from nh.parse import State, parse_status
    scr = mk({4: "      -------", 5: "      |.@.|.|", 6: "      -------", 22: STATUS1,
              23: "Dlvl:13 $:0 HP:10(10) Pw:1(1) AC:6 Xp:5/200 T:900"}, cursor=(8, 5))
    scr.fg[5][10] = 15                                    # the '|' at (10,5): bright white
    s = Snap(screen=scr, state=State("command"), status=parse_status(scr))
    graves = [f for f in features_in_view(s) if f["name"].startswith("grave")]
    assert [(f["x"], f["y"]) for f in graves] == [(10, 5)]


def test_hero_next_to_a_stale_position_is_not_a_monster():
    # p3 shift 17 #53: stepping onto a level teleporter opened "To what level do you want to teleport?" with the
    # last known square one behind — the hero's own '@' was listed as an adjacent unidentified @
    from nh.game import Snap
    from nh.mapscan import monsters_in_view
    from nh.parse import State, parse_status
    scr = mk({0: "To what level do you want to teleport?", 20: "      |.....|", 21: "      |..@..|",
              22: STATUS1, 23: "Dlvl:19 $:0 HP:10(10) Pw:1(1) AC:6 Xp:5/200 T:900"}, cursor=(39, 0))
    scr.fg[21][9] = 15
    s = Snap(screen=scr, state=State("getlin", prompt="To what level do you want to teleport?"),
             status=parse_status(scr))
    assert monsters_in_view(s, hero=(9, 20)) == []
    scr.fg[21][9] = 7                                    # a gray '@' (a human monster): listed
    assert [m["ch"] for m in monsters_in_view(s, hero=(9, 20))] == ["@"]


def test_stale_trap_memory_on_plain_floor_is_forgotten(tmp_path):
    """p3 shift 18 #312 / p1 shift 37 #633: a hole filed on the square the hero came FROM; the step guard then
    refused plain floor, and the saved level brought it back after a restart. Floor there = no trap NetHack knows."""
    import json
    import pytest
    from nh.game import Snap
    from nh.parse import State, parse_status
    from nh.tracker import Tracker
    g = _guard_game()
    rows = {5: "         .@^", 22: STATUS1, 23: "Dlvl:18 $:0 HP:10(10) Pw:1(1) AC:6 Xp:1/0 T:5"}
    scr = mk(rows, cursor=(10, 5))
    s = Snap(screen=scr, state=State("command"), status=parse_status(scr), monsters=[])
    key = g.level_key(s.status)
    path = tmp_path / "harness_state.json"
    path.write_text(json.dumps({"levels": {key: {"traps": [[9, 5], [11, 5]],
                                                 "features": {"hole": [[9, 5]], "trap door": [[11, 5]]},
                                                 "feature_desc": {"9,5": "hole", "11,5": "trap door"}}}}))
    g.memory = Tracker(g, path)
    g.feature_desc[key] = {(9, 5): "hole", (11, 5): "trap door"}
    assert g.traps[key] == {(9, 5), (11, 5)}
    g._guard(s, b"h", force=False)                 # '.' at (9,5): no trap there as far as NetHack knows
    with pytest.raises(PermissionError, match="known trap"):
        g._guard(s, b"l", force=False)             # the '^' is real
    g._note_traps(s, [])
    assert g.traps[key] == {(11, 5)} and g.feature_desc[key] == {(11, 5): "trap door"}
    lv = json.loads(path.read_text())["levels"][key]
    assert lv["traps"] == [[11, 5]] and lv["features"] == {"trap door": [[11, 5]]}
    assert lv["feature_desc"] == {"11,5": "trap door"}


def test_stairs_never_in_the_trap_memory():
    # p1 shift 36 #1229: the Castle's up stairs (2,20) sat in DL25's trap memory; trek() refused it
    g = _guard_game()
    s = _cmd_snap([])
    key = g.level_key(s.status)
    g.terrain_seen[key] = {(10, 5): "<", (12, 7): "_"}
    g.traps[key] = {(10, 5), (12, 7), (30, 9)}
    g._note_traps(s, ["There is a bear trap here."])
    assert g.traps[key] == {(30, 9)}
