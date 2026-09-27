"""MonsterTracker identity rules (no game needed: a fake game answers looks)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nh.game import Snap  # noqa: E402
from nh.monitor import MonsterTracker  # noqa: E402
from nh.parse import State, parse_status  # noqa: E402
from nh.screen import Screen  # noqa: E402

W, H = 80, 24
STATUS1 = "Agnes the Stripling           St:18/02 Dx:14 Co:15 In:7 Wi:12 Ch:7 Lawful"
HERO = (40, 10)


class FakeGame:
    """Answers looks from a {(x, y): desc} table; counts them."""

    def __init__(self):
        self.truth: dict = {}
        self.looked: list = []

    def describe_cells(self, cells):
        self.looked.extend(cells)
        return {c: self.truth[c] for c in cells if c in self.truth}

    def farlook(self, x, y):
        return self.describe_cells([(x, y)]).get((x, y), "")


def snap(mons, turn, color=3, pets=()):
    """mons: {(x, y): ch}; all in one colour (brown, like jackals/werejackals)."""
    rows = [" " * W for _ in range(H)]
    fg = [[7] * W for _ in range(H)]
    rev = [[False] * W for _ in range(H)]

    def put(x, y, ch, col=7):
        rows[y] = rows[y][:x] + ch + rows[y][x + 1:]
        fg[y][x] = col

    put(*HERO, "@")
    for (x, y), ch in mons.items():
        put(x, y, ch, color)
        if (x, y) in pets:
            rev[y][x] = True
    rows[22] = STATUS1.ljust(W)
    rows[23] = f"Dlvl:3 $:0 HP:20(20) Pw:1(1) AC:6 Xp:3/40 T:{turn}".ljust(W)
    scr = Screen(width=W, height=H, chars=rows, fg=fg, reverse=rev,
                 bold=[[False] * W for _ in range(H)], cursor=HERO)
    return Snap(screen=scr, state=State("command"), status=parse_status(scr))


def by_pos(mons):
    return {(m["x"], m["y"]): m for m in mons}


def test_summoned_jackals_are_not_werejackals():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(41, 10): "werejackal"}
    m = by_pos(t.update(snap({(41, 10): "d"}, 100)))
    assert m[(41, 10)]["desc"] == "werejackal" and m[(41, 10)]["new"]
    wid = m[(41, 10)]["id"]
    # "The werejackal summons help!": two jackals appear next to the hero
    g.truth = {(41, 10): "werejackal", (39, 9): "jackal", (39, 11): "jackal"}
    g.looked.clear()
    m = by_pos(t.update(snap({(41, 10): "d", (39, 9): "d", (39, 11): "d"}, 101)))
    assert m[(41, 10)]["desc"] == "werejackal" and not m[(41, 10)]["new"] and m[(41, 10)]["id"] == wid
    assert m[(39, 9)]["desc"] == "jackal" and m[(39, 9)]["new"]
    assert m[(39, 11)]["desc"] == "jackal" and m[(39, 11)]["new"]
    # they all move: the mixed cluster is looked at again, labels stay right
    g.truth = {(40, 11): "werejackal", (39, 10): "jackal", (41, 9): "jackal"}
    g.looked.clear()
    m = by_pos(t.update(snap({(40, 11): "d", (39, 10): "d", (41, 9): "d"}, 102)))
    assert m[(40, 11)]["desc"] == "werejackal" and m[(40, 11)]["id"] == wid
    assert {m[(39, 10)]["desc"], m[(41, 9)]["desc"]} == {"jackal"}
    assert not any(e["new"] for e in m.values())
    assert len(g.looked) == 3


def test_homogeneous_pack_moves_without_looks():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(45, 10): "jackal", (46, 11): "jackal"}
    t.update(snap({(45, 10): "d", (46, 11): "d"}, 50))
    g.looked.clear()
    m = t.update(snap({(44, 10): "d", (45, 11): "d"}, 51))
    assert g.looked == []
    assert all(e["desc"] == "jackal" and not e["new"] for e in m)


def test_hostile_never_inherits_peaceful_label():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(50, 10): "peaceful dwarf"}
    m = t.update(snap({(50, 10): "h"}, 10, color=1))
    assert m[0]["peaceful"]
    t.update(snap({}, 12, color=1))                 # it walks out of view
    g.truth = {(52, 11): "dwarf"}                   # a hostile dwarf shows up nearby
    g.looked.clear()
    m = t.update(snap({(52, 11): "h"}, 14, color=1))
    assert g.looked == [(52, 11)]
    assert m[0]["desc"] == "dwarf" and m[0]["new"] and not m[0]["peaceful"]


def test_reseen_peaceful_is_rechecked_but_not_new():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(50, 10): "peaceful gnome"}
    t.update(snap({(50, 10): "G"}, 10))
    t.update(snap({}, 11))
    g.truth = {(51, 10): "peaceful gnome"}
    m = t.update(snap({(51, 10): "G"}, 12))
    assert m[0]["peaceful"] and not m[0]["new"]


def test_reseen_hostile_keeps_label_without_look():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(50, 10): "jackal"}
    first = t.update(snap({(50, 10): "d"}, 10))
    t.update(snap({}, 11))
    g.looked.clear()
    m = t.update(snap({(53, 12): "d"}, 13))
    assert g.looked == [] and m[0]["desc"] == "jackal" and not m[0]["new"]
    assert m[0]["id"] == first[0]["id"]


def test_pet_reseen_keeps_tame_label():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(42, 10): "tame kitten"}
    t.update(snap({(42, 10): "f"}, 10, color=7, pets={(42, 10)}))
    t.update(snap({}, 11, color=7))
    g.looked.clear()
    m = t.update(snap({(44, 12): "f"}, 12, color=7, pets={(44, 12)}))
    assert g.looked == [] and m[0]["tame"] and not m[0]["new"]


def test_mixed_peaceful_and_hostile_gnomes_are_relooked():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(50, 10): "peaceful gnome", (52, 10): "gnome"}
    t.update(snap({(50, 10): "G", (52, 10): "G"}, 10))
    # they swap sides: nearest-position matching alone would swap the labels
    g.truth = {(51, 10): "gnome", (51, 11): "peaceful gnome"}
    g.looked.clear()
    m = by_pos(t.update(snap({(51, 10): "G", (51, 11): "G"}, 11)))
    assert sorted(g.looked) == [(51, 10), (51, 11)]
    assert m[(51, 10)]["desc"] == "gnome" and not m[(51, 10)]["peaceful"]
    assert m[(51, 11)]["peaceful"]
    assert not any(e["new"] for e in m.values())


def test_newcomer_beside_peacefuls_is_found():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(50, 10): "peaceful gnome", (53, 10): "peaceful gnome"}
    t.update(snap({(50, 10): "G", (53, 10): "G"}, 10))
    g.truth = {(50, 10): "peaceful gnome", (52, 10): "gnome", (53, 11): "peaceful gnome"}
    m = by_pos(t.update(snap({(50, 10): "G", (52, 10): "G", (53, 11): "G"}, 11)))
    assert m[(52, 10)]["desc"] == "gnome" and m[(52, 10)]["new"]
    assert m[(50, 10)]["peaceful"] and m[(53, 11)]["peaceful"]


def test_gone_reports_last_sighting():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(50, 10): "gas spore"}
    t.update(snap({(50, 10): "e"}, 10, color=8))
    t.update(snap({}, 12, color=8))
    gone = t.gone(12)
    assert gone and gone[0]["desc"] == "gas spore" and (gone[0]["x"], gone[0]["y"]) == (50, 10)


def test_reseen_hostile_rechecked_when_glyph_is_mixed():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(50, 10): "gnome", (60, 12): "peaceful gnome"}
    t.update(snap({(50, 10): "G", (60, 12): "G"}, 10))
    t.update(snap({}, 11))
    g.truth = {(51, 10): "peaceful gnome"}      # a peaceful one shows up where the hostile was
    g.looked.clear()
    m = t.update(snap({(51, 10): "G"}, 12))
    assert g.looked == [(51, 10)] and m[0]["peaceful"]


def test_second_monster_after_a_kill_is_new():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(41, 10): "dwarf zombie"}
    t.update(snap({(41, 10): "Z"}, 100, color=1))
    s = snap({}, 101, color=1)
    s.messages = ["You destroy the dwarf zombie!"]
    t.update(s)
    assert not t.gone(101)
    g.truth = {(45, 12): "dwarf zombie"}
    g.looked.clear()
    m = t.update(snap({(45, 12): "Z"}, 110, color=1))
    assert g.looked == [(45, 12)] and m[0]["new"]


def test_killed_names():
    from nh.monitor import killed_names
    assert killed_names(["You kill the jackal!", "The kitten kills the newt.", "The gnome lord is killed!",
                         "You kill it!", "You destroy the dwarf zombie!"]) == ["jackal", "newt", "gnome lord",
                                                                                 "dwarf zombie"]


def _with_conditions(s, conds):
    s.status.conditions = list(conds)
    return s


def test_hallucination_freezes_labels_then_relooks():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(50, 10): "peaceful gnome"}
    t.update(snap({(50, 10): "G"}, 10))
    g.looked.clear()
    m = t.update(_with_conditions(snap({(51, 10): "D"}, 11), ["Hallu"]))
    assert g.looked == [] and m[0]["hallu"] and not m[0]["new"] and not m[0]["peaceful"]
    m = t.update(_with_conditions(snap({(52, 10): "q"}, 12), ["Hallu"]))
    assert g.looked == []
    g.truth = {(52, 10): "peaceful gnome"}
    m = t.update(snap({(52, 10): "G"}, 13))
    assert g.looked == [(52, 10)] and m[0]["peaceful"]


def test_unseen_and_mimic_markers():
    g = FakeGame()
    t = MonsterTracker(g)
    m = by_pos(t.update(snap({(41, 10): "I", (45, 12): "]"}, 10)))
    assert g.looked == []
    assert m[(41, 10)]["unseen"] and not m[(41, 10)]["new"]
    assert m[(45, 12)]["mimic"] and m[(45, 12)]["new"]
    m = by_pos(t.update(snap({(41, 10): "I", (45, 12): "]"}, 11)))
    assert not m[(45, 12)]["new"]


def test_stationary_monster_remembered_long():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(50, 10): "yellow mold"}
    t.update(snap({(50, 10): "F"}, 100, color=11))
    t.update(snap({}, 101, color=11))
    g.looked.clear()
    m = t.update(snap({(50, 10): "F"}, 400, color=11))     # 300 turns later, same square
    assert g.looked == [] and not m[0]["new"] and m[0]["desc"] == "yellow mold"
