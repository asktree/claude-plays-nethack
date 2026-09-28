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
    # p2 shift 37 #51: a bullwhip snatch doesn't teleport — the devil is still next to you, holding it
    g._note_theft(["The horned devil snatches Excalibur!"], 340)
    note = g.theft_note(341)
    assert note.startswith("DISARMED at T:340") and "still next to you" in note and "teleported" not in note

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
    # p3 shift 16 #528: sensed (telepathy) before a defer_far(3) block, deferred at the default 6: inside the
    # block it waits until it is within 3; an explicit watch_monsters() keeps its own distance
    snake = {"ch": "S", "x": 70, "y": 10, "desc": "snake [seen: telepathy]", "new": True, "dist": 25, "id": 11}
    assert step(40, [snake]) == ""
    with k.ns["defer_far"](3):
        assert step(41, [dict(snake, new=False, x=45, dist=5)]) == ""
        assert "approaching: snake" in step(42, [dict(snake, new=False, x=43, dist=3)])
    troll = {"ch": "T", "x": 60, "y": 10, "desc": "troll", "new": False, "dist": 20, "id": 12}
    k.game.last = snap({}, 42)                    # (watch_monsters files it under the current level)
    k.ns["watch_monsters"]([troll], near=6)
    with k.ns["defer_far"](3):
        assert "approaching: troll" in step(43, [dict(troll, x=45, dist=5)])


def test_kernel_defer_keepaway_pauses_for_a_unicorn_only_next_to_you():
    # p4 shift 7: dig('>') / explore() paused for gray unicorns 2+ squares away. A unicorn never steps onto your
    # row, column or diagonals (mon.c mfndpos NOTONL): inside defer_keepaway(1) it is news only next to you
    from nh.danger import keeps_away
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    assert keeps_away("gray unicorn") and keeps_away("black unicorn [seen: telepathy]") and not keeps_away("pony")
    k = Kernel(Game(term=None, timing=Timing.local()))
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)

    def step(turn, mons):
        s = snap({}, turn)
        s.monsters = mons
        reasons.clear()
        k._check_events(snap({}, turn - 1), s)
        return reasons[-1] if reasons else ""
    uni = {"ch": "u", "x": 43, "y": 8, "desc": "gray unicorn", "new": True, "dist": 3, "id": 5}
    with k.ns["defer_keepaway"](1):
        assert step(10, [uni]) == ""                                          # new, 3 squares off
        assert step(11, [dict(uni, new=False, x=42, y=8, dist=2)]) == ""      # 2 squares: nothing yet
        assert step(12, [dict(uni, new=False, x=46, y=13, dist=6)]) == ""
        assert "approaching: gray unicorn" in step(13, [dict(uni, new=False, x=41, y=9, dist=1)])
        assert step(14, [dict(uni, new=False, x=41, y=9, dist=1)]) == ""      # once
        # first seen next to you: new at once
        assert "new monster: gray unicorn" in step(20, [dict(uni, id=6, x=41, y=11, dist=1)])
        # one you WALK UP to (it didn't move) pauses too: it fights only then
        assert step(30, [dict(uni, id=7, x=50, y=10, dist=10)]) == ""
        assert "approaching: gray unicorn" in step(31, [dict(uni, id=7, new=False, x=50, y=10, dist=1)])
        # other monsters keep the usual rules
        assert "new monster: soldier ant" in step(40, [{"ch": "a", "x": 43, "y": 8, "desc": "soldier ant",
                                                         "new": True, "dist": 3, "id": 8}])
    # after the block a unicorn deferred inside it still waits until it is next to you...
    assert step(50, [dict(uni, id=9, x=45, y=10, dist=5)]) == "new monster: gray unicorn at (45,10)"
    with k.ns["defer_keepaway"](1):
        assert step(60, [dict(uni, id=10, x=45, y=10, dist=5)]) == ""
    assert step(61, [dict(uni, id=10, new=False, x=43, y=10, dist=3)]) == ""
    assert "approaching: gray unicorn" in step(62, [dict(uni, id=10, new=False, x=41, y=10, dist=1)])
    # ...and a telepathy-deferred one (6 squares outside the block) waits for 1 inside it
    tele = {"ch": "u", "x": 70, "y": 10, "desc": "white unicorn [seen: telepathy]", "new": True, "dist": 30, "id": 11}
    assert step(70, [tele]) == ""
    with k.ns["defer_keepaway"](1):
        assert step(71, [dict(tele, new=False, x=44, dist=4)]) == ""
        assert "approaching: white unicorn" in step(72, [dict(tele, new=False, x=41, dist=1)])
    assert k.keepaway_dist is None


def _water_beside_hero(s):
    row = s.screen.chars[HERO[1]]
    s.screen.chars[HERO[1]] = row[:HERO[0] + 1] + "}" + row[HERO[0] + 2:]


def test_kernel_held_move_attack_and_teleport_reasons():
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    k = Kernel(Game(term=None, timing=Timing.local()))
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    a, b = snap({}, 10), snap({}, 11)
    b.messages = ["The giant eel bites!", "The giant eel swings itself around you!"]
    _water_beside_hero(b)
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


def test_wanderer_back_in_view_far_away_is_looked_at_but_not_new():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(5, 3): "frost giant"}
    first = t.update(snap({(5, 3): "H"}, 100, color=15))
    t.update(snap({}, 101, color=15))
    g.truth = {(70, 18): "frost giant"}
    g.looked.clear()
    m = t.update(snap({(70, 18): "H"}, 300, color=15))    # 65 squares and 200 turns away: looked at...
    assert g.looked == [(70, 18)] and m[0]["desc"] == "frost giant"
    assert not m[0]["new"] and m[0]["id"] == first[0]["id"]  # ...but the same giant, not a newcomer
    # a SECOND one while the first is still in view is new
    g.truth = {(70, 18): "frost giant", (10, 3): "frost giant"}
    m = by_pos(t.update(snap({(70, 18): "H", (10, 3): "H"}, 301, color=15)))
    assert m[(10, 3)]["new"] and not m[(70, 18)]["new"]


def test_two_of_a_kind_wandering_in_and_out_of_view_are_not_new_again():
    # p4 shift 7 (DL11 T:9751-9816): two gray unicorns re-paused "new monster: gray unicorn" 4+ times. One came
    # back into view within the cluster radius of the other (still in view): the cluster had more members than
    # before, both were looked at, and the spare one was marked new without consulting the out-of-view records
    g = FakeGame()
    t = MonsterTracker(g)
    u = "gray unicorn"
    g.truth = {(43, 7): u, (40, 16): u}
    m = by_pos(t.update(snap({(43, 7): "u", (40, 16): "u"}, 100, color=7)))
    assert m[(43, 7)]["new"] and m[(40, 16)]["new"]                 # two at once: both are news
    a, b = m[(43, 7)]["id"], m[(40, 16)]["id"]
    g.truth = {(41, 15): u}
    m = by_pos(t.update(snap({(41, 15): "u"}, 101, color=7)))       # A leaves view, B stays
    assert m[(41, 15)]["id"] == b and not m[(41, 15)]["new"]
    g.truth = {(42, 14): u, (41, 12): u}                            # A back, 3 squares from B
    g.looked.clear()
    m = by_pos(t.update(snap({(42, 14): "u", (41, 12): "u"}, 103, color=7)))
    assert sorted(g.looked) == [(41, 12), (42, 14)]                  # (looked at: the cluster grew)
    assert not any(e["new"] for e in m.values()) and {e["id"] for e in m.values()} == {a, b}
    # on they wander, in and out of view: never new again
    g.truth = {(45, 13): u}
    assert not any(e["new"] for e in t.update(snap({(45, 13): "u"}, 106, color=7)))
    g.truth = {(44, 12): u, (46, 11): u}
    m = by_pos(t.update(snap({(44, 12): "u", (46, 11): "u"}, 110, color=7)))
    assert not any(e["new"] for e in m.values()) and {e["id"] for e in m.values()} == {a, b}
    # a genuinely new THIRD one (both known ones in view) still is new
    g.truth = {(44, 12): u, (46, 11): u, (45, 9): u}
    m = by_pos(t.update(snap({(44, 12): "u", (46, 11): "u", (45, 9): "u"}, 111, color=7)))
    assert m[(45, 9)]["new"] and not m[(44, 12)]["new"] and not m[(46, 11)]["new"]
    assert m[(45, 9)]["id"] not in (a, b)
    # ...and once it is known, the three come and go without new pauses
    g.truth = {(47, 10): u}
    t.update(snap({(47, 10): "u"}, 113, color=7))
    g.truth = {(47, 10): u, (46, 12): u, (48, 8): u}
    m = t.update(snap({(47, 10): "u", (46, 12): "u", (48, 8): "u"}, 115, color=7))
    assert not any(e["new"] for e in m) and len({e["id"] for e in m}) == 3


def test_kernel_encumbrance_and_gas_cloud_rules():
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    g = Game(term=None, timing=Timing.local())
    k = Kernel(g)
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)

    def check(before_enc, after_enc, msgs=(), conds=((), ()), expect=()):
        s0, s1 = snap({}, 10), snap({}, 11)
        s0.status.encumbrance, s1.status.encumbrance = before_enc, after_enc
        s0.status.conditions, s1.status.conditions = list(conds[0]), list(conds[1])
        s1.messages = list(msgs)
        reasons.clear()
        k._check_events(s0, s1, expect=expect)
        return " / ".join(reasons)
    assert "encumbrance: Burdened" in check("", "Burdened", ["Your movements are slowed slightly because of your load."])
    assert check("Burdened", "", ["Your movements are now unencumbered."]) == ""        # lighter: no news
    assert check("", "Burdened", expect=("encumbrance",)) == ""                         # an item helper's own pickup
    # a poison gas cloud: news once per level (again after 50 turns without one); the burns are the HP
    # rules' job and the 1-turn blindness in it is routine after that (p2 shift 24: a pause every turn)
    g.intrinsics = {"cold"}
    first = check("", "", ["Your eyes sting.", "Something is burning your lungs!", "You cough and spit blood!"],
                  conds=((), ("Blind",)))
    assert "POISON GAS CLOUD" in first and "BURNS YOUR LUNGS" in first
    again = check("", "", ["Your eyes sting.", "Something is burning your lungs!"], conds=((), ("Blind",)))
    assert "POISON GAS CLOUD" not in again and "status: +Blind" not in again
    # with poison resistance: the same, saying it's harmless
    g.intrinsics = {"cold", "poison"}
    k._heard.clear()
    k._cloud_turns.clear()
    once = check("", "", ["Your eyes sting.", "You cough!"], conds=((), ("Blind",)))
    assert "POISON GAS CLOUD" in once and "harmless" in once
    assert check("", "", ["You can see again.", "Your eyes sting.", "You cough!"], conds=((), ("Blind",))) == ""


def test_wolf_in_gehennom_may_be_a_vampire_and_is_not_auto_fought():
    g = FakeGame()
    g.level_key = lambda st=None: "Gehennom / Level 33"
    t = MonsterTracker(g)
    g.truth = {(44, 10): "wolf"}
    m = t.update(snap({(44, 10): "d"}, 50, color=3))
    assert "VAMPIRE" in m[0]["note"]
    g2 = FakeGame()
    g2.level_key = lambda st=None: "The Dungeons of Doom / Level 7"
    t2 = MonsterTracker(g2)
    g2.truth = {(44, 10): "wolf"}
    m2 = t2.update(snap({(44, 10): "d"}, 50, color=3))
    assert "VAMPIRE" not in (m2[0].get("note") or "")


def test_kernel_brain_eaten_pause_names_the_int_danger():
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    g = Game(term=None, timing=Timing.local())
    k = Kernel(g)
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    s0, s1 = snap({}, 10), snap({}, 11)
    s0.status.in_, s1.status.in_ = 6, 4
    s1.messages = ["The mind flayer's tentacles suck you!", "Your brain is eaten!"]
    k._check_events(s0, s1)
    assert reasons and reasons[-1].startswith("BRAIN EATEN") and "NEXT" in reasons[-1] and "Int 6->4" in reasons[-1]
    assert "LOW-Int:4" in s1.status.short()


def test_sleepers_you_walk_up_to_are_not_approaching():
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
    court = [{"ch": "o", "x": 50 + i, "y": 3, "desc": "bugbear", "new": True, "dist": 12 + i, "id": 100 + i}
             for i in range(10)]
    assert step(10, court) == ""                                   # a crowd far off: deferred
    walked = [dict(m, new=False, dist=m["dist"] - 8) for m in court]
    assert step(11, walked) == ""                                  # you came closer, they didn't move
    woke = [dict(walked[0], x=walked[0]["x"] - 1, dist=3)] + walked[1:]
    assert "approaching: bugbear" in step(12, woke)                # one woke up and moved toward you
    # defer_far(1): the approach line is 1 square, not 6; and monster_filter applies to it
    ape = {"ch": "Y", "x": 60, "y": 10, "desc": "ape", "new": True, "dist": 5, "id": 300}
    with k.ns["defer_far"](1):
        assert step(20, [ape]) == ""
        assert step(21, [dict(ape, new=False, x=59, dist=4)]) == ""
        with k.ns["monster_filter"](lambda m: False):
            assert step(22, [dict(ape, new=False, x=58, dist=1)]) == ""


def test_sleepers_with_swapped_ids_and_autocontinue_for_monster_pauses():
    # p3 shift 18 #448-#483: 29 sleeping killer bees after a telepathy scan; the tracker's ids swapped between
    # identical bees as you walked up, so still bees looked "moved" -> 5 'approaching' pauses. And -a
    # 'approaching: killer bee' couldn't silence them (it matched messages only).
    import re
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
    hive = [{"ch": "a", "x": 50 + i, "y": 3, "desc": "killer bee", "new": True, "dist": 12 + i, "id": 400 + i}
            for i in range(10)]
    assert step(10, hive) == ""
    # you walk up; nobody moves, but ids 400 and 401 swapped places in the tracker
    walked = [dict(m, new=False, dist=max(1, m["dist"] - 11)) for m in hive]
    walked[0]["id"], walked[1]["id"] = 401, 400
    assert step(11, walked) == ""
    woke = [dict(walked[2], x=walked[2]["x"], y=4, dist=2)] + walked[:2] + walked[3:]
    assert "approaching: killer bee" in step(12, woke)          # a real move still pauses
    k.autocontinue = [re.compile(r"approaching: killer bee")]
    woke2 = [dict(walked[3], y=4, dist=2)] + walked[4:]
    assert step(13, woke2) == ""                                  # -a names it: no pause
    k.autocontinue = [re.compile(r"new monster: soldier ant")]
    ant = {"ch": "a", "x": 45, "y": 10, "desc": "soldier ant", "new": True, "dist": 3, "id": 500}
    assert step(14, [ant]) == ""


def test_known_mold_is_not_new_when_you_come_back_to_its_level():
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(48, 8): "yellow mold"}
    m = t.update(snap({(48, 8): "F"}, 100, color=11))
    assert m[0]["new"]
    other = snap({}, 150)
    other.status.ldesc = "Dlvl:4"
    t.update(other)                                        # down to D4 and back
    g.looked.clear()
    m = t.update(snap({(48, 8): "F"}, 400, color=11))
    assert not m[0]["new"] and m[0]["desc"] == "yellow mold" and g.looked == []
    # killed: standing next to its square with nothing there forgets it
    s = snap({}, 410)
    s.screen.cursor = (47, 8)
    t.update(s)
    assert (48, 8) not in t.sessile.get("Dlvl:3", {})


def test_kernel_reflected_ray_and_closet_and_guard_notes():
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    g = Game(term=None, timing=Timing.local())
    k = Kernel(g)
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    s = snap({}, 11)
    s.messages = ["The soldier zaps a wand of sleep!", "The sleep ray hits you!", "But it reflects from your shield!"]
    k._check_events(snap({}, 10), s)
    assert reasons == []                         # reflected: nothing to decide
    s.messages = ["The soldier zaps a wand of sleep!", "The sleep ray hits you!"]
    k._check_events(snap({}, 10), s)
    assert reasons and "message" in reasons[-1]  # not reflected: news
    reasons.clear()
    s = snap({}, 12)
    s.niche_note = "the engraving 'ad aerarium' here marks a closet"
    k._check_events(snap({}, 11), s)
    assert reasons and "TRAPPED CLOSET" in reasons[-1]
    reasons.clear()
    s = snap({}, 13)
    s.messages = ["Suddenly, the guard disappears."]
    k._check_events(snap({}, 12), s)
    assert reasons and "VAULT GUARD gone" in reasons[-1]


def test_kernel_bashing_warning_and_battle_noise():
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    g = Game(term=None, timing=Timing.local())
    k = Kernel(g)
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    s = snap({}, 11)
    s.messages = ["You begin bashing monsters with your pick-axe."]
    k._check_events(snap({}, 10), s)
    assert reasons and reasons[-1].startswith("NOT YOUR WEAPON")
    reasons.clear()
    s.messages = ["The soldier zaps a wand of striking!", "Boing!"]
    k._check_events(snap({}, 10), s)
    assert reasons and "message" in reasons[-1]           # the zap itself is still news...
    reasons.clear()
    s.messages = ["Boing!", "You hear a nearby zap.", "The magic missile whizzes by you!",
                  "The soldier wields a spear!"]
    k._check_events(snap({}, 10), s)
    assert reasons == []                                  # ...its harmless echoes are not
    s.messages = ["The soldier wields a cockatrice corpse!"]
    k._check_events(snap({}, 10), s)
    assert reasons and "message" in reasons[-1]


def test_kernel_wrap_attempt_curse_and_filter_validation():
    import pytest
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    from nh.monitor import killed_names
    g = Game(term=None, timing=Timing.local())
    k = Kernel(g)
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    s = snap({}, 11)
    # p2 shift 26: only a holder standing in water drowns you — no water next to you, no drowning attempt
    s.messages = ["The python brushes against your leg."]
    k._check_events(snap({}, 10), s)
    assert not any(r.startswith("DROWNING ATTEMPT") for r in reasons)
    reasons.clear()
    s.messages = ["It bites!", "It brushes against your leg."]
    _water_beside_hero(s)
    k._check_events(snap({}, 10), s)
    assert reasons and reasons[-1].startswith("DROWNING ATTEMPT")
    reasons.clear()
    s = snap({}, 11)
    s.messages = ["The Wizard of Yendor casts a spell!", "You feel as if you need some help."]
    k._check_events(snap({}, 10), s)
    assert reasons and reasons[-1].startswith("CURSED ITEMS") and "Run inventory()" in reasons[-1]
    # p2 shift 32 #1127: name the suspects — only items whose B/U/C wasn't known can have been hit
    reasons.clear()
    g.unknown_buc = ["w (a ring of levitation)", "t (a candelabrum (no candles attached))"]
    k._check_events(snap({}, 10), s)
    assert "Suspects" in reasons[-1] and "w (a ring of levitation)" in reasons[-1]
    with pytest.raises(TypeError, match="predicate"):
        with k.ns["monster_filter"]("killer bee"):
            pass
    assert killed_names(["The vampire lord is destroyed by the blast of fire!"]) == ["vampire lord"]
    from nh.danger import note_for
    assert ".;" not in note_for("Vlad the Impaler", 5)


def test_kernel_blocked_teleport_resisted_poison_and_more_newcomers():
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    g = Game(term=None, timing=Timing.local())
    k = Kernel(g)
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    s = snap({}, 11)
    s.messages = ["Your position suddenly seems very uncertain!", "A mysterious force prevents you from teleporting!"]
    k._check_events(snap({}, 10), s)
    assert not any("TELEPORTED" in r for r in reasons)
    reasons.clear()
    s.messages = ["The quasit's sting was poisoned!", "The poison doesn't seem to affect you."]
    k._check_events(snap({}, 10), s)
    assert reasons == []
    s.messages = ["The bone devil drinks a potion of gain level!", "The bone devil seems more experienced.",
                  "The Grey-elf tries to wield an elven bow.", "It is missed."]
    k._check_events(snap({}, 10), s)
    assert reasons == []
    after = snap({}, 12)
    after.monsters = [{"ch": "Z", "x": 40 + i, "y": 10, "desc": f"zombie{i}", "new": True} for i in range(7)]
    k._check_events(snap({}, 11), after)
    assert reasons and "+3 more" in reasons[-1]


def test_unmasked_mimic_is_remembered_while_hiding_until_seen_gone():
    g = FakeGame()
    g.mimics = {}
    t = MonsterTracker(g)
    g.truth = {(41, 10): "giant mimic", (45, 12): "large mimic"}
    t.update(snap({(41, 10): "m", (45, 12): "m"}, 100))
    (key, mem), = g.mimics.items()
    assert mem == {(41, 10): "giant mimic", (45, 12): "large mimic"}
    # the large mimic crawls one square: remembered where it is now, not where it was
    g.truth = {(41, 10): "giant mimic", (46, 12): "large mimic"}
    t.update(snap({(41, 10): "m", (46, 12): "m"}, 104))
    assert mem == {(41, 10): "giant mimic", (46, 12): "large mimic"}
    # out of sight both hide again as objects ('%', ']' is still a disguise): remembered
    t.update(snap({(41, 10): "%", (46, 12): "0"}, 150))
    assert g.mimics[key] == {(41, 10): "giant mimic", (46, 12): "large mimic"}
    # next to you, the square shows floor: nothing hides there any more
    t.update(snap({(41, 10): ".", (46, 12): "0"}, 160))
    assert g.mimics[key] == {(46, 12): "large mimic"}
    # unmasked again and killed: forgotten
    g.truth = {(46, 12): "large mimic"}
    t.update(snap({(46, 12): "m"}, 170))
    s = snap({(46, 12): "%"}, 171)
    s.messages = ["You kill the large mimic!"]
    t.update(s)
    assert key not in g.mimics


def test_hiding_mimic_next_to_you_stays_remembered():
    g = FakeGame()
    g.mimics = {}
    t = MonsterTracker(g)
    g.truth = {(41, 11): "giant mimic"}
    t.update(snap({(41, 11): "m"}, 100))
    for ch in "%0]>+":         # objects, a boulder, a strange object, stairs, a door: all disguises
        t.update(snap({(41, 11): ch}, 200))
        assert list(g.mimics.values()) == [{(41, 11): "giant mimic"}], ch
    g.truth = {(41, 11): "jackal"}
    t.update(snap({(41, 11): "d"}, 210))          # another monster stands there: the mimic is gone
    assert g.mimics == {}


def test_kernel_blind_on_purpose_and_deadly_condition_hints():
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    g = Game(term=None, timing=Timing.local())
    k = Kernel(g)
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    a, b = snap({}, 10), snap({}, 11)
    b.status.conditions = ["Blind"]
    k._check_events(a, b, expect=("blind",))
    assert reasons == []
    k._check_events(a, b)
    assert reasons and "status: +Blind" in reasons[-1]
    reasons.clear()
    c = snap({}, 12)
    c.status.conditions = ["TermIll"]
    k._check_events(a, c, expect=("blind",))      # "blind" never hides a deadly condition
    assert reasons and "+TermIll" in reasons[-1] and "unicorn horn" in reasons[-1] and "kill it first" in reasons[-1]


def test_covetous_monsters_get_a_note():
    from nh.danger import covetous, note_for
    assert covetous("Juiblex") and covetous("master lich") and covetous("Vlad the Impaler")
    assert not covetous("jackal") and not covetous("minotaur")
    assert "COVETOUS" in note_for("Asmodeus", 14)
    assert "COVETOUS" not in note_for("peaceful Asmodeus", 14)


def test_kernel_watch_monsters_pauses_when_one_comes_near():
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    g = Game(term=None, timing=Timing.local())
    k = Kernel(g)
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    before = snap({}, 10)
    g.last = before
    mino = {"ch": "H", "x": 60, "y": 10, "desc": "minotaur", "id": 7, "dist": 20, "new": False,
            "note": "hits very hard"}
    assert k.ns["watch_monsters"]([mino]) == 1
    far = snap({(55, 10): "H"}, 11)
    far.monsters = [dict(mino, x=55, dist=15)]
    k._check_events(before, far)
    assert not any("approaching" in r for r in reasons)
    near = snap({(44, 10): "H"}, 14)
    near.monsters = [dict(mino, x=44, dist=4)]
    k._check_events(far, near)
    assert reasons and "approaching" in reasons[-1] and "minotaur" in reasons[-1]


def test_unnamed_kill_forgets_the_nearby_record():
    # QA round 6: an invisible arch-lich died with "You destroy it!" and stayed "out of view" for 17 turns
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(41, 10): "arch-lich"}
    t.update(snap({(41, 10): "L"}, 100))
    assert any(r["desc"] == "arch-lich" for r in t.recent.values())
    s = snap({}, 104)                                # it turned invisible: gone from view
    t.update(s)
    s = snap({}, 105)
    s.messages = ["You destroy it!"]
    t.update(s)
    assert not any(r["desc"] == "arch-lich" for r in t.recent.values())
    from nh.monitor import killed_names
    assert killed_names(["You destroy it!"], include_it=True) == ["it (unseen)"]
    assert killed_names(["You destroy it!"]) == []


def test_kernel_named_pauses_for_digestion_and_mimic_sticking():
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    g = Game(term=None, timing=Timing.local())
    k = Kernel(g)
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    a, b = snap({}, 10), snap({}, 11)
    b.messages = ["The purple worm engulfs you!"]
    k._check_events(a, b)
    assert reasons and "SWALLOWED" in reasons[-1] and "digging" in reasons[-1]
    reasons.clear()
    b.messages = ["The fog cloud engulfs you!"]
    k._check_events(a, b)
    assert not any("SWALLOWED" in r for r in reasons)
    reasons.clear()
    # p1 shift 28: with slow digestion the same turn spits you out again
    b.messages = ["The trapper engulfs you!", "You get expelled!", "Obviously the trapper doesn't like your taste."]
    k._check_events(a, b)
    assert not any("SWALLOWED" in r for r in reasons)
    reasons.clear()
    b.messages = ["You get regurgitated!", "The purple worm engulfs you!"]    # out, then swallowed again
    k._check_events(a, b)
    assert reasons and "SWALLOWED" in reasons[-1]
    reasons.clear()
    b.messages = ["The purple worm utterly digests you!"]
    k._check_events(a, b)
    assert reasons and "BEING DIGESTED" in reasons[-1] and "NEXT turn" in reasons[-1]
    reasons.clear()
    b.messages = ["Wait!  That's a giant mimic!"]
    k._check_events(a, b)
    assert reasons and "STUCK" in reasons[-1]
    reasons.clear()
    k._check_events(a, b, expect=("stuck",))
    assert not any("STUCK" in r for r in reasons)


def test_gold_warning_with_a_leprechaun_on_the_level_even_without_a_bag():
    from nh.game import Game, Timing

    class Tr:
        recent = {1: {"desc": "leprechaun", "turn": 90, "x": 1, "y": 1}}
    g = Game(term=None, timing=Timing.local())
    g.tracker = Tr()
    s = snap({}, 100)
    s.status.gold = 1932
    g._annotate(s)
    assert "LEPRECHAUN" in s.gold_note and "$1932" in s.gold_note
    Tr.recent = {1: {"desc": "leprechaun", "turn": 10, "x": 1, "y": 1}}      # long ago: no warning
    s = snap({}, 900)
    s.status.gold = 1932
    g._annotate(s)
    assert s.gold_note == ""


def test_kernel_blind_defers_far_noted_monsters():
    # p1 shift 27: blind with telepathy, far noted monsters (vampire lords 50 squares off) paused every blow
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    g = Game(term=None, timing=Timing.local())
    k = Kernel(g)
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    before = snap({}, 10)
    far = snap({(70, 10): "V"}, 11)
    far.status.conditions = ["Blind"]
    lord = {"ch": "V", "x": 70, "y": 10, "desc": "vampire lord", "id": 3, "dist": 30, "new": True,
            "note": "LEVEL DRAIN bite"}
    far.monsters = [lord]
    k._check_events(before, far)
    assert not any("new monster" in r for r in reasons)
    near = snap({(44, 10): "V"}, 15)
    near.status.conditions = ["Blind"]
    near.monsters = [dict(lord, x=44, dist=4, new=False)]
    k._check_events(far, near)
    assert reasons and "approaching" in reasons[-1]
    # not blind: a noted newcomer pauses at once, far or not
    reasons.clear()
    k2 = Kernel(g)
    k2._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    seen = snap({(70, 10): "V"}, 11)
    seen.monsters = [dict(lord, id=9)]
    k2._check_events(before, seen)
    assert reasons and "new monster" in reasons[-1]


def test_burnables_warning_in_gehennom():
    from nh.game import Game, Timing
    g = Game(term=None, timing=Timing.local())
    g.bags, g.loose_burnables = ["D"], ["a", "b"]
    g.level_key = lambda status=None: "Gehennom / Level 34"
    s = snap({}, 100)
    g._annotate(s)
    assert "FIRE TRAPS" in s.burn_note and "bag_put('D'" in s.burn_note
    g.level_key = lambda status=None: "The Dungeons of Doom / Level 5"
    s = snap({}, 100)
    g._annotate(s)
    assert s.burn_note == ""


def test_telepathy_only_sightings_raise_no_left_view_alarm():
    # p1 shift 31 #2322: monsters seen only through a blindfold scan "left view" when it came off, and
    # fight_until_clear() called that a hit-and-run in the dark
    from nh.game import Game, Timing
    g = FakeGame()
    g.truth = {(50, 10): "vampire lord"}
    t = MonsterTracker(g)
    s = snap({(50, 10): "V"}, 10, color=1)
    s.screen.chars[23] = (s.screen.chars[23].rstrip() + " Blind").ljust(W)
    s.status = parse_status(s.screen)
    assert "Blind" in s.status.conditions
    t.update(s)
    t.update(snap({}, 12, color=1))
    assert t.gone(12)[0]["blind"] is True
    game = Game(term=None, timing=Timing.local())
    game.tracker = t
    assert game._recently_gone(snap({}, 12)) == []
    t2 = MonsterTracker(g)                       # seen with your own eyes: it counts
    t2.update(snap({(50, 10): "V"}, 10, color=1))
    t2.update(snap({}, 12, color=1))
    game.tracker = t2
    assert [r["desc"] for r in game._recently_gone(snap({}, 12))] == ["vampire lord"]


def test_autopickup_of_a_cursed_item_pauses():
    # p3 shift 12 #1560: pickup_thrown took 4 cursed daggers during a Sokoban push, unnoticed
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    k = Kernel(Game(term=None, timing=Timing.local()))
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    before = snap({}, 20)
    after = snap({}, 21)
    after.screen.cursor = (41, 10)
    after.messages = ["i - 4 cursed -1 daggers."]
    k._last_keys = b"l"
    k._check_events(before, after)
    assert reasons and reasons[-1].startswith("AUTOPICKUP took a CURSED item: 'i - 4 cursed -1 daggers.'")
    reasons.clear()
    after.messages = ["i - 4 uncursed daggers."]
    k._check_events(before, after)
    assert not any("AUTOPICKUP" in r for r in reasons)
    reasons.clear()
    same = snap({}, 21)                                 # wielded in place: no move
    same.messages = ["a - a cursed long sword (weapon in hand)."]
    k._last_keys = b"wa"
    k._check_events(before, same)
    assert not any("AUTOPICKUP" in r for r in reasons)


def test_trap_pause_respects_the_exec_autocontinue_patterns():
    # p2 shift 30: "trap at (x, y)" paused for arrow traps the exec's -a list already covered
    import re as _re
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    k = Kernel(Game(term=None, timing=Timing.local()))
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    before, after = snap({}, 20), snap({}, 21)
    after.messages = ["An arrow shoots out at you!", "You are hit by an arrow."]
    k._check_events(before, after)
    assert any("trap at" in r for r in reasons)
    reasons.clear()
    k.autocontinue = [_re.compile(r"arrow shoots out|hit by an arrow")]
    k._check_events(before, after)
    assert not any("trap at" in r for r in reasons)


def test_monster_wand_of_sleep_is_named_and_remembered():
    # p3 shift 13 #627: "The ogre king zaps a curved wand! | The sleep ray bounces!" only paused as "message"
    from nh.game import Game, Timing
    from nh.kernel import Kernel, wand_danger
    g = Game(term=None, timing=Timing.local())
    s = snap({(42, 10): "O"}, 30)
    g._note_wand_zaps(s, ["The ogre king zaps a curved wand!", "The sleep ray bounces!",
                          "The sleep ray whizzes by you!"])
    assert s.wand_kind == "sleep" and "ogre king" in s.wand_note
    key = g.level_key(s.status)
    assert g.wand_users[key]["ogre king"]["kind"] == "sleep"
    assert wand_danger(s.wand_note, s.wand_kind, g).startswith("SLEEP RAY")
    g.intrinsics.add("sleep")
    assert wand_danger(s.wand_note, s.wand_kind, g) == ""               # resisted: no named pause
    g.intrinsics.discard("sleep")
    g.reflecting = True
    assert wand_danger(s.wand_note, s.wand_kind, g) == ""               # reflected
    g.reflecting = False
    assert wand_danger("the soldier zapped a wand", None, g).startswith("WAND ZAPPED AT YOU")
    assert wand_danger("x", "death", g).startswith("DEATH RAY")
    g.magic_res = True
    assert wand_danger("x", "death", g) == ""
    # a later zap without a ray message keeps the known kind
    s2 = snap({(42, 10): "O"}, 31)
    g._note_wand_zaps(s2, ["The ogre king zaps a curved wand!"])
    assert s2.wand_kind == "sleep"
    # self-zaps (teleport/digging away) are no attack
    s3 = snap({}, 32)
    g._note_wand_zaps(s3, ["The gnome lord zaps itself with a wand of digging!"])
    assert not s3.wand_note
    # the monster list keeps a note on the zapper
    fg = FakeGame()
    fg.truth = {(42, 10): "ogre king"}
    t = MonsterTracker(fg)
    s4 = snap({(42, 10): "O"}, 33)
    s4.wand_users = dict(g.wand_users[key])
    m = by_pos(t.update(s4))[(42, 10)]
    assert m["note"].startswith("ZAPPED A WAND OF SLEEP AT YOU")
    # the kernel pause
    k = Kernel(g)
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    g.magic_res = False
    s5 = snap({(42, 10): "O"}, 34)
    s5.messages = ["The ogre king zaps a curved wand!", "The sleep ray whizzes by you!"]
    s5.wand_note, s5.wand_kind = "the ogre king zapped a curved wand — a WAND OF SLEEP", "sleep"
    k._check_events(snap({(42, 10): "O"}, 33), s5)
    assert reasons and reasons[-1].startswith("SLEEP RAY")


def test_undirected_spells_from_afar_pause_once():
    # p1 shift 32 #418/#419: a caster sealed behind a locked door paused every rest loop
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    k = Kernel(Game(term=None, timing=Timing.local()))
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    for turn in (40, 41, 42):
        b, a = snap({}, turn - 1), snap({}, turn)
        a.messages = ["The invisible nalfeshnee casts a spell!", "You feel that monsters are aware of your presence."]
        k._check_events(b, a)
    assert len(reasons) == 1                 # the aggravation once on this level; the cast itself is routine
    reasons.clear()
    b, a = snap({}, 50), snap({}, 51)
    a.messages = ["The nalfeshnee casts a spell at you!"]
    k._check_events(b, a)
    assert reasons                           # a spell AT you is news


def test_peaceful_self_buffs_are_routine():
    # p3 shift 14 #653/#3083/#3134: Minetown gnomes hasting themselves / turning invisible paused travel
    from nh.game import Game, Timing
    from nh.kernel import Kernel, peaceful_self_buff
    gnome = {"x": 12, "y": 5, "ch": "G", "desc": "peaceful gnome", "peaceful": True}
    wiz = {"x": 14, "y": 5, "ch": "G", "desc": "peaceful gnomish wizard", "peaceful": True}
    b, a = snap({}, 40), snap({}, 41)
    b.monsters, a.monsters = [gnome, wiz], [wiz]          # the gnome is invisible now
    assert peaceful_self_buff("The gnome's body takes on a strange transparency.", b, a)
    assert peaceful_self_buff("The gnomish wizard is suddenly moving faster.", b, a)
    assert not peaceful_self_buff("The gnome lord is suddenly moving faster.", b, a)    # none in view: news
    b.monsters = [gnome, dict(gnome, x=10, desc="gnome", peaceful=False)]
    assert not peaceful_self_buff("The gnome is suddenly moving faster.", b, a)         # a hostile one too
    k = Kernel(Game(term=None, timing=Timing.local()))
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    b.monsters = [gnome, wiz]
    a.messages = ["The gnome drinks a potion of invisibility!", "The gnome's body takes on a strange transparency."]
    k._check_events(b, a)
    assert reasons == []
    b.monsters = [dict(gnome, desc="gnome", peaceful=False)]
    k._check_events(b, a)
    assert reasons                                        # a hostile turning invisible is news


def test_temple_entry_pauses_once_per_level_and_far_psychic_wave_never():
    # p3 shift 15 #759/#1153: every entry into Minetown's temple paused travel; p2 shift 33 #97/#281: a far mind
    # flayer's wave (no effect beyond 8 squares) paused head_to() and stopped dig(): now a level flag + obs line
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    from nh.render import render
    g = Game(term=None, timing=Timing.local())
    k = Kernel(g)
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    for msgs, n in ((['"Pilgrim, you enter a sacred place!"', "You have a strange forbidding feeling..."], 1),
                    (["You sense a faint wave of psychic energy."], 0)):
        for turn in (40, 90):
            b, a = snap({}, turn - 1), snap({}, turn)
            a.messages = list(msgs)
            k._check_events(b, a)
        assert len(reasons) == n, (msgs, reasons)
        reasons.clear()
    a = snap({}, 91)
    g._remember_terrain(a, ["You sense a faint wave of psychic energy."])
    g._annotate(a)
    assert "mind_flayer" in a.flags and "MIND FLAYER on this level" in render(a)
    g._remember_terrain(a, ["You kill the mind flayer!"])
    g._annotate(a)
    assert "mind_flayer" not in a.flags


def test_resisted_elemental_hits_and_repeated_engraving_reads_do_not_pause():
    # p1 shift 35 #959: "You're on fire! | The fire doesn't feel hot!" paused every fire-ant bite; #14: an old
    # dust engraving paused on every step onto it
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    g = Game(term=None, timing=Timing.local())
    k = Kernel(g)
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)

    def check(msgs, repeat=False):
        reasons.clear()
        b, a = snap({}, 40), snap({}, 41)
        a.messages = list(msgs)
        a.engr_repeat = repeat
        k._check_events(b, a)
        return reasons
    assert not check(["You're on fire!", "The fire doesn't feel hot!"])
    assert not check(["You're covered in frost!", "The frost doesn't seem cold!"])
    assert not check(["You get zapped!", "The zap doesn't shock you!"])
    assert check(["You're on fire!"])                                         # not resisted: news
    assert check(["You're on fire!", "The fire doesn't feel hot!", "Your scroll of light catches fire and burns!"])
    read = ["Something is written here in the dust.", 'You read: "ad aerarium".']
    assert check(read)                                                        # the first read is news
    assert not check(read, repeat=True)
    # a grave's epitaph is flavour (p3 shift 18 #75)
    assert not check(["There is a grave here.", "Something is engraved here on the headstone.",
                      'You read: "This gravestone is shareware..."'])
    # the game marks a re-read of the same text on the same square
    from nh.parse import State
    s1 = snap({}, 50)
    s1.state = State("command")
    g._remember_here(s1, read, prev_hero=None)
    assert not s1.engr_repeat
    s2 = snap({}, 51)
    s2.state = State("command")
    g._remember_here(s2, read, prev_hero=None)
    assert s2.engr_repeat


def test_wand_zaps_are_pinned_on_the_right_monster():
    # p1 shift 34 #142/#149: the hero's own bouncing fire ray made the storm giant (it zapped STRIKING) a fire
    # zapper, and an Olog-hai's magic missile was pinned on the storm giant too
    from nh.game import Game, Timing
    from nh.parse import State
    g = Game(term=None, timing=Timing.local())
    before = snap({}, 40)
    before.state = State("direction", prompt="In what direction?")      # the hero answered a zap
    s = snap({}, 41)
    g._note_wand_zaps(s, ["The bolt of fire hits the green dragon!", "The bolt of fire bounces!",
                          "The bolt of fire hits you!", "But it reflects from your shield!",
                          "The storm giant zaps a wand of striking!", "Boing!"], before)
    key = g.level_key(s.status)
    assert g.wand_users[key]["storm giant"]["kind"] == "striking" and s.wand_kind == "striking"
    s2 = snap({}, 42)
    g._note_wand_zaps(s2, ["The storm giant zaps a wand of striking!", "The wand misses you.",
                           "The Olog-hai zaps a wand of magic missile!", "The magic missile hits you!"], snap({}, 41))
    assert g.wand_users[key]["storm giant"]["kind"] == "striking"
    assert g.wand_users[key]["Olog-hai"]["kind"] == "magic missile"
    # a sleep ray from an unseen zapper (no zap line) while you didn't zap: still named
    s3 = snap({}, 43)
    g._note_wand_zaps(s3, ["You hear a nearby zap.", "The sleep ray hits you!"], snap({}, 42))
    assert s3.wand_kind == "sleep" and s3.wand_note.startswith("a wand ray came at you")


def test_you_find_a_monster_relabels_the_one_beside_you():
    # p2 shift 35 #295: "You find a piranha." — the ';' next to you had inherited a stale "kraken, hiding" label
    g = FakeGame()
    g.truth = {(41, 10): "kraken, hiding"}
    t = MonsterTracker(g)
    s1 = snap({(41, 10): ";"}, 100, color=1)
    by_pos(t.update(s1))
    g.truth = {}                                  # no look needed: the message says what it is
    s2 = snap({(41, 11): ";"}, 101, color=1)
    s2.messages = ["You find a piranha."]
    m = by_pos(t.update(s2))[(41, 11)]
    assert m["desc"] == "piranha"
    # "You find a hidden passage." is not a monster
    s3 = snap({(41, 11): ";"}, 102, color=1)
    s3.messages = ["You find a hidden passage."]
    assert by_pos(t.update(s3))[(41, 11)]["desc"] == "piranha"


def test_silent_teleport_pauses():
    # p1 shift 37 #135/#263: teleportitis moved the hero without a word; go_down()/tunnel() went on from the new spot
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    k = Kernel(Game(term=None, timing=Timing.local()))
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)

    def check(keys, frm, to):
        reasons.clear()
        b, a = snap({}, 40), snap({}, 41)
        b.screen.cursor, a.screen.cursor = frm, to
        k._last_keys = keys
        k._check_events(b, a)
        return reasons[-1] if reasons else ""
    assert "TELEPORTED without a word" in check(b"s", (10, 5), (60, 15))
    assert "TELEPORTED without a word" in check(b"l", (10, 5), (60, 15))
    assert "TELEPORTED" in check(b"20s", (10, 5), (60, 15))
    assert check(b"l", (10, 5), (11, 5)) == ""                    # a plain step
    assert check(b"_", (10, 5), (60, 15)) == ""                   # travel moves far on purpose


def test_sokoban_no_teleport_suffix_only_for_thieves():
    # p4 shift 3 #3447 (SAFETY): the floating eye's note ("... Corpse = telepathy.") got "BUT teleporting is
    # blocked in Sokoban: corner it and kill it" appended — meleeing a floating eye paralyses you
    class SokoGame(FakeGame):
        def level_key(self, status=None):
            return "Sokoban / Level 2"
    g = SokoGame()
    g.truth = {(42, 10): "floating eye", (44, 12): "water nymph"}
    t = MonsterTracker(g)
    ms = by_pos(t.update(snap({(42, 10): "e", (44, 12): "n"}, 100, color=4)))
    assert "corner it" not in ms[(42, 10)]["note"] and "NEVER melee" in ms[(42, 10)]["note"]
    assert "corner it and kill it" in ms[(44, 12)]["note"]



def test_thief_back_in_view_pauses():
    # p4 shift 3 #1386: the nymph that had just robbed you came back into view at d=9 with no pause
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    g = Game(term=None, timing=Timing.local())
    k = Kernel(g)
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    g.last_theft = {"turn": 100, "msg": "The mountain nymph stole a +0 orcish helm.", "what": "a +0 orcish helm",
                    "who": "The mountain nymph"}
    b, a = snap({}, 120), snap({}, 121)
    b.monsters = []
    a.monsters = [{"ch": "n", "x": 49, "y": 10, "desc": "mountain nymph", "dist": 9, "id": 7}]
    a.theft_note = g.theft_note(121)
    k._check_events(b, a)
    assert reasons and reasons[-1].startswith("THIEF BACK in view: the mountain nymph at (49,10)")


def test_summoned_burst_is_named():
    # p2 shift 36 #389: the Wizard's summon nasties put 4 monsters round the hero with no message
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    k = Kernel(Game(term=None, timing=Timing.local()))
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    b, a = snap({}, 200), snap({}, 201)
    a.monsters = [{"ch": c, "x": 40 + dx, "y": 10 + dy, "desc": d, "new": True, "dist": 1, "id": 900 + i}
                  for i, (c, dx, dy, d) in enumerate([("H", 1, 0, "storm giant"), ("U", -1, 0, "umber hulk"),
                                                      ("D", 0, 1, "silver dragon"), ("A", 0, -1, "Aleax")])]
    k._check_events(b, a)
    assert reasons and reasons[-1].startswith("SUMMONED: 4 monsters appeared right around you")
    # p1 shift 40 #248: a blindfold just went on — telepathy shows what was there all along
    reasons.clear()
    b.status.conditions, a.status.conditions = [], ["Blind"]
    k._check_events(b, a)
    assert not any(r.startswith("SUMMONED") for r in reasons)


def test_melee_kill_of_one_twin_is_filed_on_the_square_hit():
    # p3 shift 20 #257: two fire giants; the one at (46,13) dies, the other steps next to where it stood
    # and inherits its record — the vanished record is the survivor's old square (45,12)
    g = FakeGame()
    kills = []
    g.record_kill = lambda name, cell, turn: kills.append((name, cell, turn))
    t = MonsterTracker(g)
    g.truth = {(45, 12): "fire giant", (46, 13): "fire giant"}
    t.update(snap({(45, 12): "H", (46, 13): "H"}, 100))
    g.truth = {(47, 13): "fire giant"}
    s = snap({(47, 13): "H"}, 101)
    s.messages = ["You kill the fire giant!"]
    s.melee_kill = ("fire giant", (46, 13))
    t.update(s)
    assert kills == [("fire giant", (46, 13), 101)]


def test_cockatrice_corpse_wielder_gets_a_lethal_note():
    # p2 shift 38 #560-#577: a priestess of Moloch picked up the cockatrice corpse and stoned the hero twice
    from nh.game import Game, Timing
    g0 = Game(term=None, timing=Timing.local())
    for msg in ("The priestess of Moloch wields a cockatrice corpse!", "The priestess of Moloch swings her "
                "cockatrice corpse.", "The priestess of Moloch hits you with the cockatrice corpse."):
        mm = g0._TRICE_WIELD.match(msg)
        assert mm and mm.group("who") == "priestess of Moloch"
    assert not g0._TRICE_WIELD.match("The priestess of Moloch wields a mace!")
    g = FakeGame()
    t = MonsterTracker(g)
    g.truth = {(41, 10): "priestess of Moloch"}
    s = snap({(41, 10): "@"}, 100)
    from nh.danger import base_name
    s.trice_wielders = {base_name("priestess of Moloch"): 99}      # (as game._note_trice_wielders files it)
    m = t.update(s)[0]
    assert m["note"].startswith("!! WIELDS A COCKATRICE CORPSE (T:99)")


def test_killed_names_counts_exploders_only_when_they_are_monsters():
    # p4 shift 7 #773: an exploded flaming sphere stayed a LURKER "last seen 7 turns ago"
    from nh.monitor import killed_names
    assert killed_names(["The flaming sphere explodes!"]) == ["flaming sphere"]
    assert killed_names(["The yellow light explodes at a spot in thin air!"]) == ["yellow light"]
    for m in ("A potion explodes!", "Your wand of digging vibrates violently and explodes!",
              "The wand suddenly explodes!", "It explodes at a spot in thin air!"):
        assert killed_names([m], include_it=True) == [], m


def test_invisible_hero_misses_are_benign():
    from nh.kernel import DEFAULT_BENIGN
    for m in ("The orc mummy attacks a spot beside you.", "The soldier ant snaps wildly and misses!",
              "The Uruk-hai strikes at thin air!", "The kraken strikes at empty water!",
              "The succubus smiles seductively at your invisible displaced image...",
              "The shark is fooled by water reflections and misses!", "The troll swings wildly!"):
        assert any(p.search(m) for p in DEFAULT_BENIGN), m
    assert not any(p.search("The soldier ant bites!") for p in DEFAULT_BENIGN)


def test_thief_back_pauses_once_per_return_and_honours_autocontinue():
    # live shift 10 #1661-#1669: every exec paused at once with "THIEF BACK in view" (a menu covering the map made
    # the thief "come back" after each inventory()), and -a 'THIEF BACK' did not suppress it
    import re as _re
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    from nh.parse import State
    g = Game(term=None, timing=Timing.local())
    k = Kernel(g)
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    g.last_theft = {"turn": 100, "msg": "The water nymph stole a blindfold.", "what": "a blindfold",
                    "who": "The water nymph"}
    nymph = {"ch": "n", "x": 49, "y": 10, "desc": "water nymph", "dist": 9, "id": 7}

    def step(turn, seen, kind="command"):
        a = snap({}, turn)
        a.state = State(kind)
        a.monsters = [dict(nymph)] if seen else []
        a.theft_note = g.theft_note(turn)
        b = snap({}, turn - 1)
        b.monsters = []
        reasons.clear()
        k._check_events(b, a)
        return [r for r in reasons if r.startswith("THIEF BACK")]
    assert step(120, True)                       # back in view: one pause
    assert not step(121, True)                   # still in view: no more
    assert not step(121, False, kind="menu")     # a menu over the map (inventory()) isn't "gone"
    assert not step(121, True)                   # ...so closing it isn't a return
    assert not step(122, False) and not step(123, True)     # a turn round a corner: not a return
    assert not step(124, False)
    assert step(130, True)                       # gone for turns, back: pause again
    step(131, False)
    k.autocontinue = [_re.compile("THIEF BACK")]
    assert not step(140, True)                   # -a 'THIEF BACK'


def test_wand_note_names_one_unknown_zapper_among_several():
    # p2 shift 39 #94: one bone devil zapped lightning; the note went onto all 4 bone devils
    fg = FakeGame()
    t = MonsterTracker(fg)
    cells = {(44, 10): "&", (43, 12): "&", (37, 12): "&"}
    fg.truth = {c: "bone devil" for c in cells}
    s = snap(cells, 60)
    s.wand_users = {"bone devil": {"kind": "lightning", "wand": "a wand of lightning", "turn": 50, "ids": set()}}
    ms = by_pos(t.update(s))
    assert all(m["note"].startswith("one of the 3 bone devils here (which one is unknown) ZAPPED A WAND OF "
                                    "LIGHTNING") for m in ms.values())
    # a zap THIS turn: the one lined up with you now is the zapper (it stepped into line and zapped)
    rec = {"kind": "lightning", "wand": "a wand of lightning", "turn": 61, "ids": set()}
    s2 = snap(cells, 61)
    s2.wand_users = {"bone devil": rec}
    ms = by_pos(t.update(s2))
    assert ms[(44, 10)]["note"].startswith("ZAPPED A WAND OF LIGHTNING")
    assert not ms[(43, 12)]["note"].startswith(("ZAPPED", "one of")) and rec["ids"] == {ms[(44, 10)]["id"]}


def test_cockatrice_corpse_picked_up_drops_its_kill_record():
    # p2 shift 39 #588: after pickup('cockatrice corpse') the "cockatrice corpse at (48,13) (your kill)" note stayed
    # all shift (other food on the square still showed '%')
    from nh.game import Game, Timing
    g = Game(term=None, timing=Timing.local())
    s = snap({}, 150)
    key = g.level_key(s.status)
    g.kills[key] = [("cockatrice", HERO, 100), ("jackal", HERO, 101), ("cockatrice", (41, 10), 120)]
    g._note_trice_taken(s, ["J - a cockatrice corpse (weapon in hand)."])       # wielding it: no pickup
    assert len(g.kills[key]) == 3
    g._note_trice_taken(s, ["J - a cockatrice corpse."])
    assert g.kills[key] == [("jackal", HERO, 101), ("cockatrice", (41, 10), 120)]
    assert g._trice_killed_on(s, HERO) is None and g._trice_killed_on(s, (41, 10))


def test_a_monster_killed_by_the_pet_is_no_news_but_the_pet_dying_is():
    # p6 shift 1 #7: explore() paused on "The kitten bites the newt. | The newt is killed!"
    from nh.kernel import other_monster_killed
    s = snap({}, 50)
    s.monsters = [{"ch": "f", "x": 41, "y": 10, "desc": "tame kitten", "tame": True, "pet": True}]
    assert other_monster_killed("The newt is killed!", s)
    assert other_monster_killed("The gnome zombie is destroyed by the blast of fire!", s)
    assert not other_monster_killed("The kitten is killed!", s)           # the pet (its kind is tame here)
    assert not other_monster_killed("Sparky is killed!", s)               # a named pet: not a monster name
    assert not other_monster_killed("You kill the newt!", s)


def test_your_alignments_unicorn_gets_a_note():
    fg = FakeGame()
    fg.truth = {(44, 10): "white unicorn"}
    t = MonsterTracker(fg)
    s = snap({(44, 10): "u"}, 70)          # the status line says Lawful
    m = t.update(s)[0]
    assert m["note"].startswith("YOUR ALIGNMENT'S UNICORN: never kill it")


def test_trice_pickup_lines_burdened_and_unpaid():
    from nh.game import Game, Timing
    g = Game(term=None, timing=Timing.local())
    for m in ("You have a little trouble lifting J - a cockatrice corpse.",
              "J - a cockatrice corpse (unpaid, 8 zorkmids).", "J - 2 chickatrice corpses."):
        assert g._TRICE_TAKEN.match(m), m
    assert not g._TRICE_TAKEN.match("J - a cockatrice corpse (weapon in hand).")


def test_wand_zapper_fill_needs_exactly_one_lined_up_and_a_visible_hero():
    fg = FakeGame()
    fg.history = []
    t = MonsterTracker(fg)
    cells = {(44, 10): "&", (40, 14): "&"}            # both lined up with the hero at (40,10)
    fg.truth = {c: "bone devil" for c in cells}
    rec = {"kind": "lightning", "wand": "a wand of lightning", "turn": 61, "ids": set()}
    s = snap(cells, 61)
    s.wand_users = {"bone devil": rec}
    t.update(s)
    assert rec["ids"] == set()                         # two candidates: unknown
    fg2 = FakeGame()
    fg2.history = [(50, "Gee!  All of a sudden, you can't see yourself.")]
    t2 = MonsterTracker(fg2)
    fg2.truth = {(44, 10): "bone devil"}
    rec2 = {"kind": "lightning", "wand": "a wand of lightning", "turn": 61, "ids": set()}
    s2 = snap({(44, 10): "&"}, 61)
    s2.wand_users = {"bone devil": rec2}
    t2.update(s2)
    assert rec2["ids"] == set()                        # invisible: it aimed where it guessed you are


def test_thief_back_the_turn_after_the_theft_pauses():
    from nh.game import Game, Timing
    from nh.kernel import Kernel
    g = Game(term=None, timing=Timing.local())
    k = Kernel(g)
    reasons = []
    k._maybe_pause = lambda reason, snap, **kw: reasons.append(reason)
    g.last_theft = {"turn": 100, "msg": "The water nymph stole a blindfold.", "what": "a blindfold",
                    "who": "The water nymph"}
    a = snap({}, 100)
    a.messages = ["The water nymph stole a blindfold."]
    a.monsters = []
    a.theft_note = g.theft_note(100)
    k._check_events(snap({}, 99), a)
    b = snap({}, 101)
    b.monsters = [{"ch": "n", "x": 49, "y": 10, "desc": "water nymph", "dist": 9, "id": 7}]
    b.theft_note = g.theft_note(101)
    reasons.clear()
    k._check_events(snap({}, 100), b)
    assert any(r.startswith("THIEF BACK") for r in reasons)
