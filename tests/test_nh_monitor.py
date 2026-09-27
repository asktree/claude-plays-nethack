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
    g.truth = {(50, 10): "ogre"}
    first = t.update(snap({(50, 10): "O"}, 10))
    t.update(snap({}, 11))
    g.looked.clear()
    m = t.update(snap({(53, 12): "O"}, 13))
    assert g.looked == [] and m[0]["desc"] == "ogre" and not m[0]["new"]
    assert m[0]["id"] == first[0]["id"]
    # 100 turns later and 10 squares off it still counts as the same ogre (p1: looting ogres)
    t.update(snap({}, 14))
    g.looked.clear()
    m = t.update(snap({(63, 14): "O"}, 114))
    assert g.looked == [] and not m[0]["new"]


def test_reseen_lookalike_is_looked_at_again():
    """A brown 'd' back in view may be the werejackal, not the jackal seen before."""
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(50, 10): "jackal"}
    t.update(snap({(50, 10): "d"}, 10))
    t.update(snap({}, 11))
    g.truth = {(52, 10): "werejackal"}
    g.looked.clear()
    m = t.update(snap({(52, 10): "d"}, 13))
    assert g.looked == [(52, 10)] and m[0]["desc"] == "werejackal" and m[0]["new"]


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


def test_pet_grows_up_label_follows():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(42, 10): "tame kitten"}
    first = t.update(snap({(42, 10): "f"}, 10, color=7, pets={(42, 10)}))
    g.looked.clear()
    s = snap({(43, 10): "f"}, 11, color=7, pets={(43, 10)})
    s.messages = ["Your kitten grows up into a housecat."]
    m = t.update(s)
    assert g.looked == [] and m[0]["desc"] == "tame housecat" and m[0]["tame"] and not m[0]["new"]
    assert m[0]["id"] == first[0]["id"]


def test_hostile_grows_up_ambiguous_is_relooked():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(45, 10): "gnome", (47, 10): "gnome"}
    t.update(snap({(45, 10): "G", (47, 10): "G"}, 10))
    g.truth = {(45, 10): "gnome lord", (47, 10): "gnome"}
    g.looked.clear()
    s = snap({(45, 10): "G", (47, 10): "G"}, 11)
    s.messages = ["The gnome becomes a gnome lord."]
    m = by_pos(t.update(s))
    assert sorted(g.looked) == [(45, 10), (47, 10)]
    assert m[(45, 10)]["desc"] == "gnome lord" and m[(47, 10)]["desc"] == "gnome"


def test_grow_regex_ignores_other_becomes():
    from nh.monitor import _GROW_RE
    assert _GROW_RE.search("Your kitten grows up into a housecat.")
    assert _GROW_RE.search("The gnome changes into a male gnome lord.").group("new") == "gnome lord"
    assert not _GROW_RE.search("The water becomes murky.")
    assert not _GROW_RE.search("You feel that Tyr is displeased.")


def test_kernel_monster_filter_limits_new_monster_pauses():
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    g = Game(term=None, timing=Timing.local())
    k = Kernel(g)
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    before = snap({}, 10)
    after = snap({(41, 10): "d", (45, 12): "D"}, 11)
    after.monsters = [{"ch": "d", "x": 41, "y": 10, "desc": "jackal", "new": True},
                      {"ch": "D", "x": 45, "y": 12, "desc": "red dragon", "new": True}]
    k._check_events(before, after)
    assert reasons and "jackal" in reasons[-1] and "red dragon" in reasons[-1]
    reasons.clear()
    k._announced.clear()          # (the same newcomers again: not a swarm repeat for this test)
    with k.ns["monster_filter"](lambda m: m["desc"] != "jackal"):
        k._check_events(before, after)
    assert reasons and "jackal" not in reasons[-1] and "red dragon" in reasons[-1]
    reasons.clear()
    k._announced.clear()
    with k.ns["monster_filter"](lambda m: False):
        k._check_events(before, after)
    assert reasons == []
    assert k.new_monster_filter is None


def test_kernel_swarm_pauses_once_per_species_group():
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    g = Game(term=None, timing=Timing.local())
    k = Kernel(g)
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)

    def step(turn, cells_new, cells_old=(), desc="killer bee"):
        s = snap({}, turn)
        s.monsters = ([{"ch": "a", "x": x, "y": y, "desc": desc, "new": True} for x, y in cells_new]
                      + [{"ch": "a", "x": x, "y": y, "desc": desc, "new": False} for x, y in cells_old])
        reasons.clear()
        k._check_events(snap({}, turn - 1), s)
        return reasons[-1] if reasons else ""

    assert "killer bee" in step(11, [(41, 10)])
    assert step(12, [(42, 11)], [(41, 10)]) == ""                  # the next bee of the swarm: no pause
    assert step(13, [(43, 12), (44, 12)], [(41, 10), (42, 11)]) == ""
    assert "killer bee" in step(14, [(70, 3)], [(41, 10)])           # a bee from elsewhere still pauses
    assert "soldier ant" in step(14, [(42, 12)], desc="soldier ant")  # another species pauses
    assert "killer bee" in step(30, [(42, 12)], [(41, 10)])          # long after: pauses again


def test_were_change_is_relooked_not_renamed():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(41, 10): "werejackal", (45, 10): "jackal"}
    t.update(snap({(41, 10): "@", (45, 10): "d"}, 10))
    # "The werejackal changes into a jackal.": the '@' becomes a 'd' next to a real jackal
    g.truth = {(41, 10): "werejackal", (45, 10): "jackal"}
    g.looked.clear()
    s = snap({(41, 10): "d", (45, 10): "d"}, 11)
    s.messages = ["The werejackal changes into a jackal."]
    m = by_pos(t.update(s))
    assert m[(41, 10)]["desc"] == "werejackal"
    assert (41, 10) in g.looked
    # the grow-up rename must not have touched it
    assert all(k.get("desc") != "jackal" or (k["x"], k["y"]) == (45, 10) for k in t.known)


def test_mimic_next_to_pet_gets_a_warning():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(46, 12): "tame kitten"}
    m = by_pos(t.update(snap({(45, 12): "]", (46, 12): "f"}, 10, pets={(46, 12)})))
    assert "PET IS NEXT TO IT" in m[(45, 12)]["note"]
    m = by_pos(t.update(snap({(45, 12): "]", (48, 14): "f"}, 11, pets={(48, 14)})))
    assert "PET" not in m[(45, 12)]["note"]


def test_same_monster_seen_by_telepathy_is_not_new():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(50, 10): "leprechaun"}
    t.update(snap({(50, 10): "l"}, 10, color=2))
    t.update(snap({}, 11, color=2))
    # back in view via telepathy: the look (if any) says "[seen: telepathy]"
    g.truth = {(52, 11): "leprechaun [seen: telepathy]"}
    g.looked.clear()
    m = t.update(snap({(52, 11): "l"}, 14, color=2))
    assert not m[0]["new"]


def test_monster_back_on_its_square_much_later_is_not_new():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(33, 16): "kobold shaman"}
    t.update(snap({(33, 16): "k"}, 100, color=12))
    t.update(snap({}, 101, color=12))
    g.looked.clear()
    m = t.update(snap({(33, 16): "k"}, 900, color=12))     # 800 turns later, same closet square
    assert g.looked == [] and not m[0]["new"] and m[0]["desc"] == "kobold shaman"


def test_kernel_expected_level_change_does_not_pause():
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    g = Game(term=None, timing=Timing.local())
    k = Kernel(g)
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    a, b = snap({}, 10), snap({}, 11)
    a.status.ldesc, b.status.ldesc = "Dlvl:10", "Dlvl:11"
    k._check_events(a, b, expect=("level",))
    assert reasons == []
    k._check_events(a, b)
    assert reasons and "level: Dlvl:10 -> Dlvl:11" in reasons[-1]


def test_explicit_farlook_relabels_a_lookalike():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(46, 2): "cobra"}
    t.update(snap({(46, 2): "S"}, 10))
    assert t.relabel(46, 2, "S       a snake (pit viper)") == "pit viper"
    g.truth = {(46, 2): "cobra"}          # the automatic look would say cobra again...
    g.looked.clear()
    m = by_pos(t.update(snap({(46, 2): "S"}, 11)))
    assert m[(46, 2)]["desc"] == "pit viper"   # ...but the unambiguous re-sighting keeps the explicit label
    assert t.relabel(50, 5, "a doorway") is None


def test_priest_label_keeps_its_god_from_afar():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(41, 9): "peaceful high priestess of Tyr"}
    t.update(snap({(41, 9): "@", (47, 9): "A"}, 10, color=15))
    # a step later another '@' shows up next to it (an ambiguous cluster: everyone is looked at again)
    # and from 2+ squares away the game names no god
    g.truth = {(42, 9): "peaceful high priestess", (43, 10): "wizard called Kevin the Sorcerer"}
    g.looked.clear()
    m = by_pos(t.update(snap({(42, 9): "@", (43, 10): "@"}, 11, color=15)))
    assert m[(42, 9)]["desc"] == "peaceful high priestess of Tyr"
    assert "player-monster" in m[(43, 10)]["note"]
    assert t.relabel(42, 9, "@  a human (peaceful high priestess)") == "peaceful high priestess of Tyr"


def test_kernel_theft_and_fight_hp_rules():
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    g = Game(term=None, timing=Timing.local())
    k = Kernel(g)
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    a, b = snap({}, 225), snap({}, 226)
    b.messages = ["It hits!", "It steals the Amulet of Yendor!"]
    g._note_theft(b.messages, 226)
    g._annotate(b)
    k._check_events(a, b)
    assert reasons and reasons[-1].startswith("THEFT — STOLEN at T:226") and "NEED it" in reasons[-1]
    later = snap({}, 300)
    g._annotate(later)
    assert "Amulet of Yendor" in later.theft_note
    g._note_theft(["u - the Amulet of Yendor."], 310)       # picked it back up
    g._annotate(later)
    assert later.theft_note == ""
    g._note_theft(["The gnome lord stole a +0 dagger."], 320)
    assert g.last_theft["what"] == "a +0 dagger"
    g.last_theft = None
    g._note_theft(["The nymph steals a gem from the gnome!", "You stole 30 zorkmids worth of merchandise."], 330)
    assert g.last_theft is None                              # monster vs monster; your own shoplifting

    def hp(h0, h1, mx=262):
        s0, s1 = snap({}, 10), snap({}, 11)
        s0.status.hp, s0.status.hpmax, s1.status.hp, s1.status.hpmax = h0, mx, h1, mx
        reasons.clear()
        k._check_events(s0, s1)
        return reasons[-1] if reasons else ""
    assert hp(180, 170) != ""                 # outside a fight: any loss below 70% pauses
    with k.ns["hp_rules"](0.45):
        assert hp(180, 170) == ""             # in a fight: a scratch well above the floor doesn't
        assert "two more like that" in hp(190, 150)    # 150 - 2*40 < 118
        assert hp(262, 220) == ""
        assert hp(262, 190) != ""             # a quarter of max HP in one step
        assert hp(120, 110) != ""             # below the floor
    assert k.fight_floor is None


def test_were_form_change_is_not_a_new_monster_and_howls_pause_once():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(44, 10): "werejackal"}
    t.update(snap({(44, 10): "@"}, 10))
    g.truth = {(45, 10): "werejackal"}
    s = snap({(45, 10): "d"}, 11)
    s.messages = ["The werejackal changes into a jackal."]
    m = by_pos(t.update(s))
    assert m[(45, 10)]["desc"] == "werejackal" and not m[(45, 10)]["new"]
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    k = Kernel(Game(term=None, timing=Timing.local()))
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    for i in range(3):
        b = snap({}, 20 + i)
        b.messages = ["You hear a jackal howling at the moon."]
        k._check_events(snap({}, 19 + i), b)
    assert len(reasons) == 1


def test_coyote_alias_kill_is_recorded():
    from nh.monitor import killed_names
    g = FakeGame()
    kills = []
    g.record_kill = lambda name, cell, turn: kills.append((name, cell, turn))
    t = MonsterTracker(g)
    g.truth = {(41, 10): "coyote - Eatius-Slobbius"}
    t.update(snap({(41, 10): "d"}, 10))
    s = snap({}, 11)
    s.messages = ["You kill the coyote!"]
    t.update(s)
    assert killed_names(s.messages) == ["coyote"] and kills == [("coyote", (41, 10), 11)]


def test_rogue_overview_marks_the_level():
    from nh.game import Game, Timing
    from nh.tracker import Tracker
    import tempfile
    from pathlib import Path
    g = Game(term=None, timing=Timing.local())
    t = Tracker(g, Path(tempfile.mkdtemp()) / "h.json")
    text = ("The Dungeons of Doom: levels 1 to 18\nLevel 17:\nA fountain.\nLevel 18: <- You are here.\n"
            "A primitive area.\n")
    t._parse_overview(text, snap({}, 5), "Dlvl:18")
    assert "rogue" in g.level_flags["The Dungeons of Doom / Level 18"]
    t2 = Tracker(Game(term=None, timing=Timing.local()), Path(tempfile.mkdtemp()) / "h.json")
    t2._parse_overview("The Dungeons of Doom: levels 1 to 5\nLevel 5: <- You are here.\nA fountain.\n",
                       snap({}, 5), "Dlvl:5")
    assert not t2.game.level_flags


def test_far_telepathic_and_deferred_newcomers_pause_when_they_approach():
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    k = Kernel(Game(term=None, timing=Timing.local()))
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)

    def step(turn, mons):
        s = snap({}, turn)
        s.monsters = mons
        reasons.clear()
        k._check_events(snap({}, turn - 1), s)
        return reasons[-1] if reasons else ""
    ogre = {"ch": "O", "x": 70, "y": 10, "desc": "ogre king [seen: telepathy]", "new": True, "dist": 30, "id": 7}
    dragon = {"ch": "D", "x": 72, "y": 10, "desc": "yellow dragon [seen: telepathy]", "new": True, "dist": 32,
              "id": 8, "note": "acid breath"}
    r = step(10, [ogre, dragon])
    assert "yellow dragon" in r and "ogre king" not in r        # a noted one still pauses
    assert step(11, [dict(ogre, new=False, x=60, dist=20)]) == ""
    assert "approaching: ogre king" in step(12, [dict(ogre, new=False, x=45, dist=5)])
    assert step(13, [dict(ogre, new=False, x=44, dist=4)]) == ""     # once
    # inside defer_far(6): an ordinary far newcomer (seen normally) waits too
    ape = {"ch": "Y", "x": 60, "y": 10, "desc": "ape", "new": True, "dist": 20, "id": 9}
    with k.ns["defer_far"](6):
        assert step(20, [ape]) == ""
        assert "approaching: ape" in step(21, [dict(ape, new=False, x=46, dist=6)])
    assert "ape" in step(30, [dict(ape, id=10)])                    # outside the block it pauses at once


def test_kernel_held_move_attack_and_teleport_reasons():
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    k = Kernel(Game(term=None, timing=Timing.local()))
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    a, b = snap({}, 10), snap({}, 11)
    b.messages = ["The giant eel bites!", "The giant eel swings itself around you!"]
    k._check_events(a, b)
    assert reasons[-1].startswith("HELD") and "Elbereth" in reasons[-1]
    k._last_keys = b"h"
    b.messages = ["You hit it."]
    k._check_events(a, b)
    assert "YOUR MOVE ATTACKED" in reasons[-1]
    k._last_keys = b"Fh"
    k._check_events(a, b)
    assert "YOUR MOVE ATTACKED" not in reasons[-1]            # an F-attack is on purpose
    b.messages = ["Your position suddenly seems very uncertain!"]
    k._check_events(a, b)
    assert reasons[-1].startswith("TELEPORTED")
    b.messages = ["The gnome lord picks up a wand."]
    reasons.clear()
    k._check_events(a, b)
    assert reasons and "message" in reasons[-1]               # a monster picking up a wand is news


def test_poison_paralysis_and_quest_notes():
    from nh.danger import note_for, threat_level
    assert threat_level("snake", 13, 136) == "dangerous" and threat_level("snake", 13, 136, ("poison",)) == "trivial"
    assert "PARALYSE" in note_for("ghoul", 12)
    assert "QUEST LEADER" in note_for("peaceful Norn", 13) and "stronger" not in note_for("peaceful Norn", 13)
    assert "Bell of Opening" in note_for("Lord Surtur", 14)
    assert "DROWNS" in note_for("giant eel, holding you", 14)
