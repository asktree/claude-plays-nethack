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
