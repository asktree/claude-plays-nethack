"""Game driver: send keys to the tmux terminal, wait for the game to settle,
auto-dismiss --More--, collect messages, and produce snapshots.

Safety rule: we never send a key until the previous one has settled into a
recognized waiting state (or a generous timeout expires), so a keystroke
can't land in a prompt we haven't seen yet.
"""

from __future__ import annotations

import copy
import json
import os
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from .keys import describe_bytes, parse_keys
from .parse import (MAP_BOTTOM, MAP_TOP, MONSTER_CHARS, MORE, State, Status, classify, parse_status)
from .screen import Screen
from .tmuxterm import TmuxTerminal


@dataclass
class Timing:
    first: float = 0.5     # max wait for the first output byte after a send
    quiet: float = 0.04    # output must be silent this long to count as settled
    max_wait: float = 8.0  # hard cap for one settle
    recheck: int = 10      # extra settle rounds when the screen looks mid-draw

    @classmethod
    def local(cls) -> "Timing":
        return cls(first=0.5, quiet=0.04, max_wait=8.0)

    @classmethod
    def remote(cls) -> "Timing":
        return cls(first=2.5, quiet=0.18, max_wait=20.0, recheck=8)


@dataclass
class Snap:
    screen: Screen
    state: State
    status: Status
    messages: list[str] = field(default_factory=list)   # messages seen during this step
    keys: str = ""
    elapsed: float = 0.0
    n: int = 0              # global step counter
    unsent: str = ""        # keys NOT sent because the game state made them unsafe
    stop_reason: str = ""
    monsters: list = field(default_factory=list)   # set by the MonsterTracker (command state)
    under: str | None = None   # remembered map feature under the hero ('<', '>', '{', '_', '\\')
    engulfed: bool = False     # the hero is inside a monster (the /-\\ ring is drawn around '@')
    paused: str = ""           # set when the exec paused on this step and the player resumed it
    gone: list = field(default_factory=list)   # dangerous monsters that left view in the last ~20 turns
    wield_note: str = ""       # set when you are known to wield a non-weapon / nothing (Game.wield_note)
    shop: str = ""             # the shop you stand in ("Carignan's antique weapons outlet"), if known
    last_pos: tuple | None = None   # the hero's last known square (set while a prompt hides the cursor)
    feature_desc: dict = field(default_factory=dict)   # {(x, y): "trap door"} looked up on this level
    feature_mem: dict = field(default_factory=dict)    # {(x, y): '<'/'>'/'{'/'_'/'\\'/'^' portal/'~' vib. square}
    theft_note: str = ""       # set for a while after a monster stole something from you
    charm_note: str = ""       # armor a nymph's charm took off and nobody put on again
    rogue: bool = False        # the Rogue level: no colours, '%' stairs, '+' doorways, ':' food, ']' armor...
    floor_mem: set = field(default_factory=set)   # Rogue level: floor seen before (dark rooms forget it)
    flags: set = field(default_factory=set)       # this level's flags ("rogue", "castle", "medusa?", "medusa"...)
    medusa_risk: bool = False  # probably Medusa's level and you are neither blind nor known to reflect
    gold_note: str = ""        # loose gold while you carry a bag (leprechauns take the purse, not the bag)
    burn_note: str = ""        # in Gehennom: scrolls/potions outside the bag (fire traps destroy them)
    wand_note: str = ""        # set on the step a monster zapped a wand / a wand ray came at you
    wand_kind: str | None = None   # ... and what that wand does ("sleep", "death", "striking"...), if known
    held_trap: str = ""        # "bear trap" while it holds you (hack.c trapmove: pull diagonally — escape_trap())
    wand_users: dict = field(default_factory=dict)  # {monster name: {"kind", "wand", "turn"}} zappers here
    trice_wielders: dict = field(default_factory=dict)  # {monster name: turn} seen wielding a cockatrice corpse here
    trice_note: str = ""       # a fresh cockatrice corpse you killed lies on this level (a gloved monster can wield it)
    left_note: str = ""        # on arriving: covetous monsters you left on this level are still here (_note_departure)
    solid_mem: set = field(default_factory=set)   # squares found to be solid rock (an object shown embedded in it)
    niche_note: str = ""       # set on the step that read a trapped closet's engraving ('ad aerarium')
    pet_note: str = ""         # for a while after the stairs: your pet didn't come along (Game.pet_left_note)
    niche_mem: dict = field(default_factory=dict)   # {(x, y): 'teleport'/'trapdoor'} trapped closets here
    no_squeeze: bool = False   # a diagonal squeeze between rock failed (pack over 600): planners avoid them
    sokoban: bool = False      # a Sokoban level: never a diagonal squeeze between boulders/rock (hack.c)
    room_note: str = ""        # set on the step that entered a special room (zoo, anthole, beehive...)
    room_mem: dict = field(default_factory=dict)    # {(x, y) entry: {"kind", "prev", "turn"}} special rooms here
    mimic_mem: dict = field(default_factory=dict)   # {(x, y): 'giant mimic'} mimics unmasked on this level
    melee_kill: tuple | None = None   # (name, (x, y)): the monster your blow killed this step, on the square hit
    engr_repeat: bool = False  # this step read the same engraving text as last time on this square

    def __repr__(self) -> str:
        st = self.status.short() if self.status.ok else "?"
        return (f"<Snap #{self.n} {self.state.kind} {st} hero={self.hero} "
                f"msgs={self.messages!r}{' PROMPT=' + repr(self.state.prompt) if self.state.kind != 'command' else ''}>")

    @property
    def objects(self) -> list:
        """Object glyphs on the map: [{ch, x, y, kind, pile, color, dist}]."""
        from .mapscan import objects_in_view
        return objects_in_view(self)

    @property
    def features(self) -> list:
        """Stairs, fountains, altars, doors, traps, water... [{ch, x, y, name, dist}]."""
        from .mapscan import features_in_view
        return features_in_view(self)

    @property
    def menu(self):
        """Parsed menu/text window (items with letter/text/selected/header) or None."""
        return self.state.menu

    def hostiles(self, radius: int | None = None, mobile: bool = False) -> list:
        """Monsters that are not tame/peaceful/statues, optionally within
        radius. Excludes what can't be judged: 'I' markers (unseen, maybe a
        peaceful) and anything seen while hallucinating. mobile=True leaves
        out the ones that never move (molds, lichens' kin...: a script's "while
        hostiles near: fight" loop spun 35 times on a brown mold — p4 shift 3)."""
        out = []
        for m in self.monsters:
            d = m.get("desc", "")
            if m.get("statue") or m.get("pet") or d.startswith("tame ") or d.startswith("peaceful "):
                continue
            if m.get("unseen") or m.get("hallu"):
                continue
            if radius is not None and (m.get("dist") is None or m["dist"] > radius):
                continue
            if mobile:
                from .monitor import _stationary
                if _stationary(d):
                    continue
            out.append(m)
        return out

    def adjacent_hostiles(self) -> list:
        return self.hostiles(radius=1)

    @property
    def kind(self) -> str:
        return self.state.kind

    @property
    def hero(self) -> tuple[int, int] | None:
        if self.state.kind in ("command",):
            cx, cy = self.screen.cursor
            if MAP_TOP <= cy <= MAP_BOTTOM:
                return (cx, cy)
        return None

    @property
    def pos(self) -> tuple[int, int] | None:
        """Where you are: .hero at the command prompt, else your last known
        square (.hero is None while a prompt/menu hides the cursor)."""
        return self.hero or self.last_pos

    @property
    def message(self) -> str:
        return " | ".join(self.messages)

    @property
    def msgs(self) -> list:
        """Alias of .messages (the repr prints msgs=...)."""
        return self.messages

    @property
    def turn(self):
        """Alias of .status.turn."""
        return self.status.turn

    @property
    def prompt(self) -> str:
        return self.state.prompt if self.state.kind not in ("command",) else ""


_DIRS = {(-1, -1): "y", (0, -1): "k", (1, -1): "u", (-1, 0): "h", (1, 0): "l",
         (-1, 1): "b", (0, 1): "j", (1, 1): "n"}


def _sgn(v: int) -> int:
    return (v > 0) - (v < 0)


def _cursor_keys(cx: int, cy: int, tx: int, ty: int) -> str:
    """getpos cursor keys from (cx,cy) to (tx,ty); capitals move 8."""
    keys = []
    dx, dy = tx - cx, ty - cy
    while abs(dx) >= 8 and abs(dy) >= 8:
        keys.append(_DIRS[(_sgn(dx), _sgn(dy))].upper())
        dx -= 8 * _sgn(dx)
        dy -= 8 * _sgn(dy)
    while abs(dx) >= 8:
        keys.append("L" if dx > 0 else "H")
        dx -= 8 * _sgn(dx)
    while abs(dy) >= 8:
        keys.append("J" if dy > 0 else "K")
        dy -= 8 * _sgn(dy)
    while dx and dy:
        keys.append(_DIRS[(_sgn(dx), _sgn(dy))])
        dx -= _sgn(dx)
        dy -= _sgn(dy)
    while dx:
        keys.append("l" if dx > 0 else "h")
        dx -= _sgn(dx)
    while dy:
        keys.append("j" if dy > 0 else "k")
        dy -= _sgn(dy)
    return "".join(keys)


def _explosion_frame(scr: Screen) -> bool:
    """True if an explosion animation (explode.c: a 3x3 ring of / - \\ |
    glyphs around a blank centre) is on the map. The corners are the tell:
    '/' top-left and bottom-right, '\\' top-right and bottom-left, all in one
    colour; at least three must match (part of a blast can be out of sight)."""
    rows = [scr.row(y) for y in range(scr.height)]
    want = ((-1, -1, "/"), (1, -1, "\\"), (-1, 1, "\\"), (1, 1, "/"))
    for y in range(MAP_TOP + 1, MAP_BOTTOM):
        if "/" not in rows[y - 1] + rows[y + 1] and "\\" not in rows[y - 1] + rows[y + 1]:
            continue
        for x in range(1, scr.width - 1):
            if rows[y][x] == "@":
                continue      # engulfed: the same ring drawn around the hero is the engulfer
            hits = [scr.fg[y + dy][x + dx] for dx, dy, ch in want if rows[y + dy][x + dx] == ch]
            if len(hits) >= 3 and len(set(hits)) == 1:
                return True
    return False


HERO_RACE, HERO_ROLE = "dwarf", "valkyrie"
# genociding your own race's base monster or your role's player-monster kills
# you (read.c: i == urace.malenum || i == urole.malenum); class genocide of
# their classes (h, @) includes them
_SELF_CLASSES = {"h", "@"}
_SELF_NAMES = {HERO_RACE, HERO_RACE + "s", "dwarves", HERO_ROLE, HERO_ROLE + "s"}


def _genocide_danger(prompt: str, answer: str) -> str:
    a = answer.replace("\r", "").replace("\n", "").strip().lower()
    if not a or a.startswith("\x1b"):
        return ""
    if "class" in prompt.lower():
        cls = a if len(a) == 1 else None
        if cls is None:
            from .danger import monster_record
            name = a[:-1] if a.endswith("s") and monster_record(a[:-1]) else a
            rec = monster_record(name) or monster_record(a.replace("ves", "f"))
            cls = rec.get("symbol") if rec else None
            if cls is None and name in _SELF_NAMES:
                cls = "h"
        if cls in _SELF_CLASSES:
            return (f"refusing genocide answer {answer.strip()!r}: it resolves to class {cls!r}, which contains "
                    f"your own race ({HERO_RACE}) or role ({HERO_ROLE}) — you would die. Blessed genocide: "
                    "answer 'L' (liches) or ';' (sea monsters).")
        return ""
    if a in _SELF_NAMES:
        return (f"refusing to genocide {a!r}: that is your own race/role — you would die. Uncursed genocide: "
                "'master mind flayer' or 'mind flayer'.")
    return ""


def _menu_sig(snap: "Snap"):
    m = snap.state.menu if snap.state.kind == "menu" else None
    if not m:
        return ("-", snap.state.kind)
    return (m.title, tuple(it.text for it in m.items[:4]), m.page)


def _squeeze_rock(scr: Screen, x: int, y: int) -> bool:
    """hack.c bad_rock() as seen on the screen: rock/unknown, a wall (not an open door), a tree, a boulder."""
    ch, col = scr.at(x, y), scr.color_at(x, y)
    return ch in " 0" or (ch in "|-" and col not in (3, 15)) or (ch == "#" and col == 2)


def _engulfed(scr: Screen, hero) -> bool:
    """The swallow display: a ring of / - \\ | around the hero (corners are
    the tell, as for explosions, but the centre is '@')."""
    if hero is None:
        return False
    x, y = hero
    want = ((-1, -1, "/"), (1, -1, "\\"), (-1, 1, "\\"), (1, 1, "/"))
    return sum(1 for dx, dy, ch in want if scr.at(x + dx, y + dy) == ch) >= 3


def _lined_up(a, b, reach: int = 13) -> bool:
    """Same row, column or diagonal, within `reach` squares (a monster's zap/breath line to you)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    return (dx or dy) and (dx == 0 or dy == 0 or abs(dx) == abs(dy)) and max(abs(dx), abs(dy)) <= reach


def _ring_corner(scr: Screen, x: int, y: int) -> bool:
    """A '\\' at (x, y) that is the NE or SW corner of an engulf ring drawn in its colour ('-' beside it and
    '|' below/above it, all one colour: a fire vortex's ring is yellow like a throne)."""
    col = scr.color_at(x, y)

    def is_(dx, dy, ch):
        return scr.at(x + dx, y + dy) == ch and scr.color_at(x + dx, y + dy) == col
    return (is_(-1, 0, "-") and is_(0, 1, "|")) or (is_(1, 0, "-") and is_(0, -1, "|"))


def feature_at(scr: Screen, x: int, y: int) -> str | None:
    """The map feature ('<', '>', '{', '_', '\\') drawn at (x, y), or None.
    A '\\' counts as a throne only in its gold colour (drawing.c HI_GOLD):
    ray animations and the corners of the engulf ring also draw '\\'. A cyan
    '_' is an iron chain, not an altar."""
    ch = scr.at(x, y)
    if ch not in "<>{_\\":
        return None
    col = scr.color_at(x, y)
    if ch == "\\" and col != 11:
        return None
    if ch == "_" and col == 6:
        return None
    return ch


_WEAPON_NAMES: list | None = None
# artilist.h (3.6.7): the artifacts whose base object is a weapon (or weapon-tool)
_ARTIFACT_WEAPONS = re.compile(
    r"\b(?:Excalibur|Stormbringer|Mjollnir|Cleaver|Grimtooth|Orcrist|Sting|Magicbane|Frost Brand|Fire Brand|"
    r"Dragonbane|Demonbane|Werebane|Grayswandir|Giantslayer|Ogresmasher|Trollsbane|Vorpal Blade|Snickersnee|"
    r"Sunsword|Sceptre of Might|Staff of Aesculapius|Longbow of Diana|Tsurugi of Muramasa)\b")


_ELBERETH_IGNORERS = re.compile(r"\b(?:minotaur|shopkeeper|watchman|watch captain|guard|priest(?:ess)?|"
                                r"Wizard of Yendor|Angel|Aleax|ki-rin|Archon|Death|Famine|Pestilence)\b")


def ignores_elbereth(m: dict) -> bool:
    """monmove.c onscary(): @ humans and elves, minotaurs, shopkeepers, guards, priests, the Wizard, lawful
    minions (Angels...) and the Riders pay Elbereth no heed — hitting one from your Elbereth square is no
    hypocrisy (mon.c setmangry), though a blow still smudges a dust engraving (uhitm.c u_wipe_engr)."""
    desc = m.get("desc") or ""
    if desc.startswith("peaceful "):
        return False              # attacking a peaceful from Elbereth is hypocrisy whatever it is
    return m.get("ch") == "@" or bool(_ELBERETH_IGNORERS.search(desc))


def _item_core(text: str) -> str:
    """An inventory text without its state suffixes: 'a blessed +6 Excalibur (weapon in hand)' ->
    'a blessed +6 Excalibur'."""
    return re.sub(r"\s*\((?:weapon in \w+|wielded|alternate weapon; not wielded|in quiver[^)]*|"
                  r"tethered weapon in \w+)\)", "", text or "").strip()


def is_weapon_text(text: str) -> bool:
    """Does an inventory/wield text name a weapon or weapon-tool (pick-axe,
    unicorn horn...)? 'a blessed +6 long sword named Excalibur' -> True,
    'a blessed lamp' -> False. Names and unidentified appearances come from
    the object data."""
    global _WEAPON_NAMES
    if _ARTIFACT_WEAPONS.search(text or ""):
        return True                    # an identified artifact shows by its own name: "the +6 Excalibur"
    if _WEAPON_NAMES is None:
        import json
        from pathlib import Path
        try:
            objs = json.loads((Path(__file__).parent / "data" / "objects.json").read_text())["objects"]
            names = {n for o in objs if o.get("weapon") and o.get("class") != "GEM_CLASS"   # (sling ammo)
                     for n in (o.get("name"), o.get("appearance")) if n}
        except Exception:  # noqa: BLE001
            names = set()
        _WEAPON_NAMES = [re.compile(r"\b" + re.escape(n) + r"(?:e?s)?\b", re.I)
                         for n in sorted(names, key=len, reverse=True)]
    core = re.sub(r"\s+(?:named|called)\s.*$", "", text or "")
    core = re.sub(r"\s*\([^)]*\)", "", core)
    return any(rx.search(core) for rx in _WEAPON_NAMES)


# "(weapon in hand)", "(weapon in hands)" (two-handed), "(tethered weapon in hand)" (aklys),
# "(weapon in hand, glowing light blue)" (Sting), "(wielded)" for a wielded stack
# (objnam.c doname_base); not "(wielded in other hand)" / "(alternate weapon; not wielded)"
WIELDED_RE = re.compile(r"\((?:tethered )?weapon in \w+|\(wielded\)")


# engrave.c wipeout_text(): a rubbed-out letter becomes '?' (or ' ' for '?' and small punctuation) or a
# look-alike from this table; leading/trailing blanks are then dropped
_RUBOUTS = {"A": "^", "B": "Pb[", "C": "(", "D": "|)[", "E": "|FL[_", "F": "|-", "G": "C(", "H": "|-", "I": "|",
            "K": "|<", "L": "|_", "M": "|", "N": "|\\", "O": "C(", "P": "F", "Q": "C(", "R": "PF", "T": "|",
            "U": "J", "V": "/\\", "W": "V/\\", "Z": "/", "b": "|", "d": "c|", "e": "c", "g": "c", "h": "n",
            "j": "i", "k": "|", "l": "|", "m": "nr", "n": "r", "o": "c", "q": "c", "w": "v", "y": "v"}


def _rubbed_forms(ch: str) -> set:
    seen, todo = {ch}, [ch]
    while todo:
        for r in _RUBOUTS.get(todo.pop(), ""):
            if r not in seen:
                seen.add(r)
                todo.append(r)
    return seen | {"?", " "}


def engraving_is(text: str, orig: str) -> bool:
    """`text` reads like `orig` worn down by wipeout_text(): some letters rubbed out to '?'/' ' or to a
    look-alike ('m' -> 'n'/'r', 'd' -> 'c'/'|'...), blanks at the ends dropped; at least half of the
    letters must still be intact."""
    t = text.strip()
    if not t or len(t) > len(orig):
        return False
    need = max(3, (len(orig.replace(" ", "")) + 1) // 2)
    for off in range(len(orig) - len(t) + 1):
        exact = 0
        for c, o in zip(t, orig[off:off + len(t)]):
            if c == o:
                exact += o != " "
            elif o == " " or c not in _rubbed_forms(o):
                break
        else:
            if exact >= need:
                return True
    return False


# detect.c: the messages right before browse_map()'s cursor (the game opens it by itself, it asks nothing)
_DETECT_BROWSE = re.compile(r"You sense your surroundings\.|You detect the presence of |You sense the presence of "
                            r"monsters\.|You feel very greedy(?:, and sense gold!|\.)|You feel entrapped\.|"
                            r"and you smell (?:food|something)\.|You sense (?:food|something)\.")
_NOT_BROWSE = ("Where do you want", "Pick ", "Select ", "Showing ")


def _detect_browse(lines, top: str = "") -> bool:
    """A detection map-browse cursor follows these messages — and the top line isn't a position the player
    asked for (travel, farlook, a teleport/jump/spell target)."""
    return not any(n in top for n in _NOT_BROWSE) and any(_DETECT_BROWSE.search(ln) for ln in lines)


_PARANOID = re.compile(r"\(yes\) \[no\]|\[yes/no\]")     # a paranoid_confirmation prompt (typed answer)


def _death_page(snap) -> bool:
    """A lone "You die...--More--" page: nothing to decide there, and an amulet of life saving may speak on the
    next page ("But wait..."): step on to see (the end-of-game questions still stop everything)."""
    return snap.state.kind == "gameover" and (snap.state.more_text or "").rstrip().endswith("You die...")


def _split_top(text: str) -> list[str]:
    """tty packs several short messages on one line separated by 2+ spaces."""
    parts = [p.strip() for p in re.split(r"\s{2,}", text.strip()) if p.strip()]
    out: list[str] = []
    for p in parts:
        # re-join quoted speech that contains a double space ("Hello!  Welcome...")
        if out and out[-1].count('"') % 2 == 1:
            out[-1] += "  " + p
        else:
            out.append(p)
    return out


class Game:
    """Owns the terminal; every key goes through here (single-threaded use)."""

    def __init__(self, term: TmuxTerminal, timing: Timing, log_path: Path | None = None):
        self.term = term
        self.timing = timing
        self.log_path = Path(log_path) if log_path else None
        self.lock = threading.RLock()
        self.n = 0
        self.last: Snap | None = None
        self.history: list[tuple[int | None, str]] = []   # (turn, message)
        self.max_history = 2000
        self.on_step = []   # callbacks(snap) after every settled step
        self.hero_pos: tuple[int, int] | None = None   # last known hero position
        # getpos (cursor-selection) mode can't always be read off the screen
        # (autodescribe rewrites the top line), so we track it: set when a
        # position prompt appears, cleared by a pick key or ESC.
        self.getpos_active = False
        self._arrival_check: dict | None = None   # a stairs arrival with a monster next to you (see step())
        self._arrival_prune: str | None = None    # ldesc of a level just entered: prune its memory (step())
        self.tracker = None   # MonsterTracker, attached by the daemon
        self.visited: dict[str, set] = {}   # level (ldesc) -> hero positions seen in command state
        self.traps: dict[str, set] = {}     # level (ldesc) -> squares known to hold traps
        self.avoid: dict[str, set] = {}     # level (ldesc) -> squares the player asked to avoid
        self.terrain_seen: dict[str, dict] = {}   # level key -> {(x, y): feature char} (stairs, fountains...)
        self.here_seen: dict[str, dict] = {}      # level key -> {(x, y): last "You see here"/pile text}
        self.kills: dict[str, list] = {}          # level key -> [(name, (x, y), turn)]: corpse ages
        self.engr_seen: dict[str, dict] = {}      # level key -> {(x, y): engraving text last read there}
        self.engr_burned: dict[str, set] = {}     # level key -> squares whose engraving was read as BURNED
        self.niches: dict[str, dict] = {}         # level key -> {(x, y) of a trapped closet: 'teleport'/'trapdoor'}
        self.special_rooms: dict[str, dict] = {}  # level key -> {(x, y) where you entered: {"kind", "prev", "turn"}}
        self.mimics: dict[str, dict] = {}         # level key -> {(x, y): 'giant mimic'}: mimics seen unmasked,
                                                  # hiding again as objects there (MonsterTracker._note_mimics)
        self.desmap_ids: dict[str, dict] = {}     # level key -> the fixed special-level map placed there (desmap)
        self.wielded: str | None = None           # what inventory() last showed "(weapon in hand)"; None = unknown
        self.gloves: str | None = None            # worn gloves/gauntlets per inventory(); "" none; None = unknown
        self.wielded_class: str | None = None     # inventory() class header of the wielded item ("Weapons")
        self.wielded_letter: str | None = None    # its inventory letter (None: unknown, or nothing wielded)
        self.wield_since: int | None = None       # the turn it was wielded (main_weapon promotion)
        self.wield_tool: bool = False             # a tool applied into your hands ("You now wield ...": a dig)
        self.main_weapon: dict | None = None      # {"letter", "text"}: the weapon you usually fight with
        self.shops: dict[str, list] = {}          # level key -> [[x1, y1, x2, y2, "Name's shop type"]] interiors
        self.locked_doors: dict[str, set] = {}    # level key -> doors found locked (travel walks around them)
        self.feature_desc: dict[str, dict] = {}   # level key -> {(x, y): "trap door" / "lawful altar"} (farlook)
        self.intrinsics: set = {"cold", "stealth"}   # Valkyrie start; more learned from messages (_note_intrinsics)
        self.stair_links: dict[str, dict] = {}    # level key -> {(x, y) of a staircase: key of the level it leads to}
        self.last_theft: dict | None = None       # {"turn", "msg", "what"}: the latest theft from you
        self.pet_seen: dict | None = None         # {"key", "ldesc", "turn", "desc", "at"}: your pet, last in view
        self.pet_left: dict | None = None         # {"ldesc", "turn", "desc", "at"}: a pet that didn't follow you
        self.level_flags: dict[str, set] = {}     # level key -> {"rogue"}: levels drawn differently
        self.floor_seen: dict[str, set] = {}      # Rogue level: squares once shown as floor/corridor/doorway
        self.water_seen: dict[str, set] = {}      # level key -> squares last shown as water ('}' not red): an 'I'
                                                  # or a sea monster drawn there is IN the water
        self.solid: dict[str, set] = {}           # level key -> squares a step into said "It's solid stone."
                                                  # (gold/gems embedded in the Mines' rock look walkable)
        self.reflecting: bool | None = None       # inventory(): wearing a known reflection item (None = unknown)
        self.wand_users: dict[str, dict] = {}    # level -> {monster name: {"kind", "wand", "turn"}} (_note_wand_zaps)
        self.trice_wielders: dict[str, dict] = {}   # level -> {monster name: turn} (_note_trice_wielders)
        # level -> {covetous monster name: {"x", "y", "seen", "left", "ldesc"}} left behind there (_note_departure)
        self.left_behind: dict[str, dict] = {}
        self.held_trap = ""                       # "bear trap" while it holds you (_note_held)
        self.kicked_stones: dict[str, set] = {}   # level -> squares where a gray stone kick_test() slid landed
        self.unknown_buc: list[str] = []          # inventory(): items whose B/U/C isn't known ("w (a ring ...)")
        self.blindfolded: bool | None = None      # inventory(): wearing a blindfold/towel on purpose
        self.quest_given = False                  # the quest leader assigned the quest (its speech, or ^O's
                                                  # "Given quest by ..."): visits to it are harmless from then on
        self.real_xl: int | None = None    # last XL read while not polymorphed
        self.last_status: Status | None = None
        # Level identity for per-level memory: "Dlvl:3" is ambiguous (main
        # dungeon vs Gnomish Mines), so the memory tracker sets the ^O
        # overview name ("The Gnomish Mines / Level 3") for the ldesc it saw.
        self.level_name: str | None = None
        self.level_name_ldesc: str | None = None
        self._settled_raw = -1            # raw-log size at the last settled capture

    def level_key(self, status: Status | None = None) -> str:
        """Key for per-level memory (traps, avoid, visited): the overview
        name of the current level when known, else the status ldesc."""
        st = status if status is not None else (self.last.status if self.last is not None else None)
        ld = st.ldesc if st is not None else ""
        if self.level_name and self.level_name_ldesc == ld:
            return self.level_name
        return ld

    def rekey_level(self, old: str, new: str) -> None:
        """Merge per-level memory recorded under a provisional key."""
        if old == new:
            return
        for d in (self.traps, self.avoid, self.visited, self.locked_doors, self.level_flags, self.floor_seen,
                  self.solid, self.water_seen, self.kicked_stones, self.engr_burned):
            if old in d:
                d.setdefault(new, set()).update(d.pop(old))
        for d in (self.terrain_seen, self.here_seen, self.engr_seen, self.stair_links, self.feature_desc,
                  self.niches, self.mimics, self.desmap_ids, self.special_rooms, self.wand_users,
                  self.trice_wielders, self.left_behind):
            if old in d:
                d.setdefault(new, {}).update(d.pop(old))
        for links in self.stair_links.values():       # destinations recorded under the provisional key
            for c, dest in list(links.items()):
                if dest == old:
                    links[c] = new
        if old in self.kills:
            self.kills.setdefault(new, []).extend(self.kills.pop(old))
        if old in self.shops:
            lst = self.shops.setdefault(new, [])
            lst.extend(e for e in self.shops.pop(old) if e not in lst)

    FEATURE_CHARS = "<>{_\\"
    # remembered per level beside FEATURE_CHARS (terrain_seen): a magic portal ('^', bright magenta; on the
    # Planes of Air/Water the game itself keeps no map, so this is the only memory of it) and the vibrating
    # square ('~', magenta)
    PORTAL_COLOR, VIBRATING_COLOR = 13, 5
    ENDGAME = ("Earth", "Air", "Fire", "Water", "Astral Plane")
    # the invocation (mkinvokearea): the stairs appear under you; the area around is rebuilt (x +-6, y +-5)
    _INVOKED = re.compile(r"^You are standing at the top of a stairwell leading down!")
    # steal.c: "The nymph stole a +0 dagger." / "She stole ..." / "It steals the Amulet of Yendor!"
    # (stealamulet(), stealarm()); muse.c: "The ... snatches your long sword!" (a bullwhip);
    # "Your purse feels lighter." (a leprechaun took gold). Not monster-vs-monster ("... from the gnome!")
    THEFT_RE = re.compile(r"^(?!You )(?P<who>.+?) (?:steals|stole|removed your chain and stole|snatches) "
                          r"(?P<what>.+?)[.!]$|^Your purse feels lighter")
    THEFT_TURNS = 300      # how long the obs keeps saying so (unless you get it back)
    # look_here(): "There is %s here." with dfeature_at() (invent.c) — "an opulent throne",
    # "an altar to Tyr (lawful)", "a high altar to ..." on Astral/Sanctum
    _HERE_FEATURE = re.compile(r"^There is an? (?:high )?(staircase up|staircase down|ladder up|ladder down|"
                               r"fountain|altar|opulent throne)\b.* here\.")
    _HERE_CH = {"staircase up": "<", "staircase down": ">", "ladder up": "<", "ladder down": ">",
                "fountain": "{", "altar": "_", "opulent throne": "\\"}

    _MELEE_KILL = re.compile(r"^You (?:kill|destroy) (?:the |an? |poor )?(.+?)!$")
    _HERE_OBJS = re.compile(r"(?:^|\n)(?:You (?:see|feel) here |Things that (?:are|you feel) here:)")
    _NO_OBJS = re.compile(r"^You (?:see|feel) no objects here")
    COCKATRICE_CORPSE = re.compile(r"\b(?:cockatrice|chickatrice) corpses?\b")

    _ENGR_READ = re.compile(r'You (?:read|feel the words): "(.*)"\.?$')
    _ENGR_GONE = re.compile(r"engraving beneath you fades|You wipe out the message|engraving now reads|"
                            r"^You disturb the engraving|is riddled by bullet holes|gets? smudged|"
                            r"engraving on the .* vanishes")

    def _remember_here(self, snap: Snap, messages: list[str], prev_hero=None) -> None:
        """Remember what the look messages said lies on the hero's square
        (the guards use it: cockatrice corpses) and the engraving read there
        (the Elbereth guard)."""
        if snap.hero is None or not snap.status.ok:
            return
        key = self.level_key(snap.status)
        here = self.here_seen.setdefault(key, {})
        texts = [m for m in messages if self._HERE_OBJS.search(m)]
        if texts:
            here[snap.hero] = "\n".join(texts)
        elif any(self._NO_OBJS.search(m) for m in messages):
            here.pop(snap.hero, None)
        engr = self.engr_seen.setdefault(key, {})
        read = False
        dust = any(m.startswith("Something is written here in the dust.") for m in messages)
        burned = any(re.match(r"^Some text has been (?:burned|melted) into the ", m) for m in messages)
        for m in messages:
            mm = self._ENGR_READ.search(m)
            if mm:
                if engr.get(snap.hero) == mm.group(1):
                    snap.engr_repeat = True       # nothing new: the kernel doesn't pause on it again
                engr[snap.hero] = mm.group(1)
                read = True
                if burned:
                    self.engr_burned.setdefault(key, set()).add(snap.hero)
                else:
                    self.engr_burned.get(key, set()).discard(snap.hero)
                if dust:
                    self._note_niche(snap, key, mm.group(1))
            elif self._ENGR_GONE.search(m):
                engr.pop(snap.hero, None)
                self.engr_burned.get(key, set()).discard(snap.hero)
        if not read and prev_hero is not None and prev_hero != snap.hero \
                and "Blind" not in snap.status.conditions:
            # arriving on a square shows its engraving; none shown = none left (smudged away)
            engr.pop(snap.hero, None)

    # engrave.c u_wipe_engr(): every melee blow (uhitm.c attack(): 3 letters), kick or throw (2) from your square
    # rubs letters out of a DUST engraving there — after one blow "Elbereth" is gone; a burned one stays
    _WIPE_MSG = re.compile(r"^You (?:hit|miss|smite|kill|destroy|kick|begin bashing|throw|shoot)\b|^WHAMM|"
                           r"^You (?:kill|destroy) it\b")

    def _note_engraving_wiped(self, cur: Snap, snap: Snap, messages: list[str]) -> None:
        """Forget the (dust) engraving under you after an attack from your square: the guard kept refusing
        the next fight after a forced blow had already smudged the Elbereth (live shift 7 #2320)."""
        if snap.hero is None or cur is None or cur.hero != snap.hero or not snap.status.ok:
            return
        key = self.level_key(snap.status)
        engr = self.engr_seen.get(key, {})
        if snap.hero not in engr or snap.hero in self.engr_burned.get(key, ()):
            return
        if any(self._WIPE_MSG.search(m) for m in messages):
            engr.pop(snap.hero, None)

    # hack.c check_special_room(): said ONCE per room (it becomes an ordinary room right after), so the
    # harness must remember the room itself — another doorway of it says nothing (p3 shift 10: explore walked
    # into an anthole through its second doorway)
    SPECIAL_ROOMS = ((re.compile(r"^Welcome to David's treasure zoo!"), "treasure zoo"),
                     (re.compile(r"^You enter an opulent throne room!"), "throne room"),
                     (re.compile(r"^You enter a leprechaun hall!"), "leprechaun hall"),
                     (re.compile(r"^You have an uncanny feeling\.\.\.|^(?:Run|Fly|Slither|Crawl|Swim|Float|Walk)"
                                 r" away!  (?:Run|Fly|Slither|Crawl|Swim|Float|Walk) away!"), "graveyard"),
                     (re.compile(r"^You enter a giant beehive!"), "beehive"),
                     (re.compile(r"^You enter a disgusting nest!"), "cockatrice nest"),
                     (re.compile(r"^You enter an anthole!"), "anthole"),
                     (re.compile(r"^You enter a military barracks!"), "barracks"))

    def _note_special_room(self, snap: Snap, messages: list[str], prev_hero=None) -> None:
        kind = next((k for p, k in self.SPECIAL_ROOMS for m in messages if p.search(m)), None)
        if kind is None or snap.hero is None or not snap.status.ok:
            return
        key = self.level_key(snap.status)
        ident = (getattr(self, "desmap_ids", None) or {}).get(key) or {}
        if kind == "graveyard" and ident.get("level") in ("wizard1", "wizard3") and not ident.get("ambiguous"):
            return      # yendor.des: an UNFILLED 'morgue' region that only marks the tower (no undead: p1 shift 33)
        rooms = self.special_rooms.setdefault(key, {})
        if any(max(abs(c[0] - snap.hero[0]), abs(c[1] - snap.hero[1])) <= 1 and r.get("kind") == kind
               for c, r in rooms.items()):
            return
        rooms[snap.hero] = {"kind": kind, "prev": prev_hero if prev_hero != snap.hero else None,
                            "turn": snap.status.turn}
        what = {"treasure zoo": "a room full of SLEEPING monsters on gold",
                "throne room": "a throne room: a sleeping court (often a ruler) and a throne",
                "leprechaun hall": "sleeping leprechauns (they steal gold and teleport)",
                "graveyard": "a graveyard: undead (wraiths, ghosts, zombies, mummies, vampires at depth)",
                "beehive": "killer bees (poison: Str loss, rarely instadeath) and a queen bee; royal jelly",
                "cockatrice nest": "COCKATRICES (touch/hiss = stoning) among statues",
                "anthole": "sleeping ants (soldier ants are deadly early; poison)",
                "barracks": "sleeping soldiers (armed, many)"}.get(kind, kind)
        snap.room_note = (f"you entered a {kind} at {snap.hero} ({what}). NetHack says so only ONCE per room: "
                          "travel/explore now keep out of it (all its known squares and doorways count as avoided "
                          "while you are outside; special_rooms() lists them, forget_room() lets you in again)")

    # mklev.c makeniche(): a closet (one hidden corridor square) behind a SECRET door in a room's top or
    # bottom wall that holds a ONE-TIME trap is marked by a dust engraving on the room square just inside
    # that door (trap_engravings[]; aged by wipe_engr_at(5)): "ad aerarium" = a teleporter INTO THE CLOSED
    # GOLD VAULT (makevtele; below DL15 it can be a level teleporter instead), "Vlad was here" = a trap door
    # (DL6-24). The same words also turn up as random graffiti, which is never dust.
    NICHE_ENGR = (("ad aerarium", "teleport"), ("Vlad was here", "trapdoor"))

    def _note_niche(self, snap: Snap, key: str, text: str) -> None:
        kind = next((k for words, k in self.NICHE_ENGR if engraving_is(text, words)), None)
        if kind is None or snap.hero is None:
            return
        ex, ey = snap.hero
        cells = []
        for d in (-1, 1):
            between = snap.screen.at(ex, ey + d)      # the (secret) door in the wall row, or room floor
            if between in "-|+" or (between == "." and snap.screen.at(ex - 1, ey + d) == "-"
                                    and snap.screen.at(ex + 1, ey + d) == "-"):
                cells.append((ex, ey + 2 * d))
        if not cells:                                 # can't tell which wall: both
            cells = [(ex, ey - 2), (ex, ey + 2)]
        cells = [c for c in cells if 1 <= c[1] <= 21 and 0 <= c[0] < 80]
        known = self.niches.setdefault(key, {})
        new = [c for c in cells if c not in known]
        for c in cells:
            known[c] = kind
            self.avoid.setdefault(key, set()).add(c)
        if new:
            where = " or ".join(str(c) for c in new)
            depth = snap.status.dlvl or 0
            what = ("a ONE-TIME TELEPORTER INTO THE CLOSED GOLD VAULT (the guard then makes you drop ALL your "
                    "gold, bagged gold included, before he leads you out)"
                    + (" — or, this deep, a LEVEL TELEPORTER to a random level (up to 3 deeper)" if depth > 15
                       else "") + "; with magic resistance it does nothing"
                    if kind == "teleport" else "a ONE-TIME TRAP DOOR (drops you to a deeper level)")
            snap.niche_note = (f"the engraving {text!r} here marks a closet behind the (secret) door beside you: "
                               f"its square {where} holds {what}. Marked avoided (travel/explore keep out); to "
                               f"use it on purpose, step_onto() it" + (" with no gold on you and a way to dig "
                                                                     "out within ~30 turns (the vault holds 4 "
                                                                     "piles of gold)" if kind == "teleport"
                                                                     else "")
                               + " — while the door or the closet square is still hidden a step there says "
                                 "\"It's solid stone.\": search from the door square first (\"You find a "
                                 "hidden door/passage\", p3 shift 16)")

    def on_elbereth(self, snap: Snap, cell=None) -> bool:
        """The hero (or `cell`) stands on an engraving last read as exactly 'Elbereth'."""
        cell = cell or snap.hero
        if cell is None or not snap.status.ok:
            return False
        txt = self.engr_seen.get(self.level_key(snap.status), {}).get(cell, "")
        return txt.strip().lower() == "elbereth"

    def record_kill(self, name: str, cell, turn: int | None) -> None:
        """Called by the monster tracker when a monster it tracked was killed."""
        if not name or cell is None or turn is None:
            return
        lst = self.kills.setdefault(self.level_key(), [])
        lst.append((name, tuple(cell), int(turn)))
        del lst[:-40]
        lb = self.left_behind.get(self.level_key())
        if lb and lb.pop(name, None) is not None:
            if not lb:
                self.left_behind.pop(self.level_key(), None)
            self._save_left_behind()

    def corpse_age(self, name: str, cell, turn: int | None):
        """Turns since the oldest recorded kill of `name` on `cell` of this level
        (a corpse lies where its monster died), or None if unknown."""
        if cell is None or turn is None:
            return None
        recs = self.kills.get(self.level_key(), [])
        ages = [turn - t for n, c, t in recs if n == name and c == tuple(cell)]
        if not ages:
            # "You kill it!" (an invisible or unseen monster) on this square lately: the corpse there is its
            ages = [turn - t for n, c, t in recs if n == "it" and c == tuple(cell) and 0 <= turn - t <= 50]
        return max(ages) if ages else None

    def _trice_killed_on(self, snap: Snap, cell, within: int = 300):
        """(name, turns ago) of a cockatrice/chickatrice killed on `cell` of this level in the last `within`
        turns (a corpse lies where its monster died and rots away after ~250 turns), else None."""
        turn = snap.status.turn if snap.status.ok else None
        hits = [(n, turn - t if turn is not None else 0) for n, c, t in self.kills.get(self.level_key(snap.status), [])
                if n in ("cockatrice", "chickatrice") and tuple(c) == tuple(cell)
                and (turn is None or 0 <= turn - t <= within)]
        return min(hits, key=lambda h: h[1]) if hits else None

    def trice_squares(self, snap: Snap) -> set:
        """Squares of this level where a cockatrice/chickatrice corpse probably lies: seen there ("You see
        here ...") or killed there in the last 300 turns. Blind, stepping onto one is instant stoning."""
        if not snap.status.ok:
            return set()
        key = self.level_key(snap.status)
        out = {c for c, txt in self.here_seen.get(key, {}).items() if self.COCKATRICE_CORPSE.search(txt or "")}
        out |= {tuple(c) for n, c, t in self.kills.get(key, []) if self._trice_killed_on(snap, c)}
        return out

    def _recently_gone(self, snap: Snap) -> list:
        """Monsters with a danger note that left view within ~20 turns (a gas
        spore in a dark corridor is invisible to telepathy: mind where it was)."""
        from .danger import note_for
        turn = snap.status.turn if snap.status.ok else None
        if turn is None or self.tracker is None or not hasattr(self.tracker, "gone"):
            return []
        out = []
        for r in self.tracker.gone(turn):
            d = r.get("desc") or ""
            # (last seen while Blind = through telepathy — a telepathy_scan() census: it didn't "leave view",
            # your sight came back; p1 shift 31: sealed fake-tower monsters raised a hit-and-run alarm)
            if turn - r.get("turn", 0) <= 20 and d and not d.startswith(("tame ", "peaceful ")) \
                    and not r.get("statue") and not r.get("blind") and note_for(d):
                out.append({"desc": d, "x": r["x"], "y": r["y"], "ago": turn - r.get("turn", 0)})
        return out[:4]

    _WIELD_NOW = re.compile(r"^You now wield (.+?)\.$")          # wield_tool(): #rub, apply a pick-axe
    _WIELD_INV = re.compile(r"^[a-zA-Z] - (.+?)\.?$")          # 'w'/'x' echo the inventory line

    def burn_note_for(self, snap: Snap) -> str:
        """The Gehennom fire-trap warning for scrolls/potions/books outside the bag (per the last inventory();
        items.inventory()/bag_put() refresh it on the current snap, quaffing/reading drops the letter)."""
        burn = getattr(self, "loose_burnables", None) or []
        bags = getattr(self, "bags", None) or []
        key0 = self.level_key(snap.status) if snap.status.ok else ""
        return (f"{len(burn)} scroll(s)/potion(s)/spellbook(s) in the open pack (per the last inventory(): "
                f"{''.join(burn[:12])}) — Gehennom's FIRE TRAPS burn scrolls and boil potions: "
                f"bag_put('{bags[0]}', ...) them" if burn and bags and key0.startswith("Gehennom") else "")

    _USE_UP = re.compile(r"^What do you want to (?:drink|read|drop)\?")

    def _note_used_up(self, cur: Snap, data: bytes) -> None:
        """q/r + letter: that potion/scroll may be gone — drop it from the burn warning's list (a stack that is
        left shows again at the next inventory()). p1 shift 31: the warning kept naming a quaffed potion."""
        lb = getattr(self, "loose_burnables", None)
        if not lb:
            return
        letter = None
        if len(data) >= 2 and data[:1] in (b"q", b"r", b"d") and chr(data[1]).isalpha():
            letter = chr(data[1])           # (d + letter drops the whole stack: p1 shift 35 #111)
        elif len(data) == 1 and chr(data[0]).isalpha() and cur.state.kind == "object" \
                and self._USE_UP.search(cur.state.prompt or ""):
            letter = chr(data[0])
        if letter and letter in lb:
            self.loose_burnables = [c for c in lb if c != letter]

    # muse.c mzapmsg(): "The ogre king zaps a curved wand!" (a wand of sleep, unidentified); zap.c buzz(): the ray
    # names what it is ("The sleep ray whizzes by you!"); mbhitm(): striking says "The wand hits you!"
    _ZAP_RE = re.compile(r"^(?:The |An? )?(?P<mon>.+?) zaps (?:an? |the )(?P<wand>[\w' -]*wand(?: of [\w ]+)?)!$")
    _RAY_RE = re.compile(r"^The (?P<ray>sleep ray|death ray|bolt of fire|bolt of cold|bolt of lightning|"
                         r"magic missile) (?:hits you|whizzes by you|bounces|misses)")
    _RAY_KIND = {"sleep ray": "sleep", "death ray": "death", "bolt of fire": "fire", "bolt of cold": "cold",
                 "bolt of lightning": "lightning", "magic missile": "magic missile"}

    _DANGER_ORDER = {"death": 0, "sleep": 1, None: 2}

    def _note_wand_zaps(self, snap: Snap, messages: list[str], cur: Snap | None = None) -> None:
        """Remember monsters that zap attack wands at you (per level, by name) and what the wand does: the
        kernel pauses on a SLEEP / DEATH ray you don't resist, the monster list keeps a note on the zapper, and
        fight()/hunt() warn before closing in on one (p3 shift 13: an ogre king's wand of sleep, twice).
        Messages are read in order: a zap owns the ray (or "Boing!") that follows it, not one from before it —
        p1 shift 34: the hero's own bouncing fire ray and an Olog-hai's magic missile were pinned on a storm
        giant that zapped striking. Rays answering YOUR zap/spell (the step answered a direction prompt) that
        no monster's zap precedes are yours."""
        own = cur is not None and cur.state.kind == "direction"
        events: list[list] = []            # [name or None, wand text or None, kind or None]
        pending = None
        for m in messages:
            z = self._ZAP_RE.match(m)
            if z is not None:
                name = z.group("mon")
                if " itself" in name or name.startswith("You"):
                    pending = None
                    continue
                wm = re.search(r"wand of ([\w ]+)$", z.group("wand"))
                pending = [name, z.group("wand"), wm.group(1) if wm else None, False]
                events.append(pending)
                continue
            r = self._RAY_RE.match(m)
            if r is not None:
                kind = self._RAY_KIND.get(r.group("ray"))
                if pending is not None and not pending[3]:
                    pending[2], pending[3] = kind or pending[2], True
                elif pending is None and not own:
                    events.append([None, None, kind, True])     # a ray at you from someone unseen
                continue
            if m in ("The wand hits you!", "The wand misses you.", "Boing!"):
                if pending is not None:
                    pending[2] = pending[2] or "striking"
                    pending[3] = True
                elif not own:
                    events.append([None, None, "striking", True])   # striking from someone unseen
        if not events:
            return
        key = self.level_key(snap.status) if snap.status.ok else None
        store = self.wand_users.setdefault(key, {}) if key else {}
        from .danger import base_name
        heroes = [h for h in (snap.hero, cur.hero if cur is not None else None) if h is not None]
        prev = (cur.monsters if cur is not None else None) or []
        notes = []
        for name, wand, kind, _ray in events:
            if name:
                name = base_name(name) or name
                rec = store.get(name) or {}
                # which one zapped: the monsters of that name lined up with you (muse.c: it zaps only in line,
                # within BOLT_LIM) — the note stays on them, not on every monster of the name (p2 shift 33 #1103:
                # a dead sergeant's wand note moved to another sergeant)
                ids = set(rec.get("ids") or ())
                ids.update(x["id"] for x in prev if x.get("id") is not None
                           and (base_name(x.get("desc") or "") or "").lower() == name.lower()
                           and any(_lined_up(h, (x["x"], x["y"])) for h in heroes))
                store[name] = {"kind": kind or rec.get("kind"), "wand": wand or rec.get("wand"),
                               "turn": snap.status.turn if snap.status.ok else None, "ids": ids}
                kind = store[name]["kind"]
            notes.append((self._DANGER_ORDER.get(kind, 3), name, wand, kind))
        _o, name, wand, kind = min(notes, key=lambda n: n[0])      # the most dangerous one this step
        snap.wand_note = (f"the {name} zapped {wand or 'a wand'}" if name else
                          "a wand ray came at you") + (f" — a WAND OF {kind.upper()}" if kind else
                                                       " (what it does isn't known yet)")
        snap.wand_kind = kind

    # muse.c MUSE_WAN_DIGGING: a fleeing monster digs a hole under itself and falls through
    _MON_HOLE = re.compile(r"^(?:The |An? )?(?P<n>[\w' -]+?) has made a hole in the [\w ]+\.$")

    def _note_monster_hole(self, cur: Snap, snap: Snap, messages: list[str]) -> None:
        """Remember the hole a monster just dug where it stood (p2 shift 32 #1080: a food pile hid its '^'):
        a known trap (a way down, a square to avoid) on this level."""
        if cur is None or not snap.status.ok:
            return
        from .danger import base_name
        for m in messages:
            mm = self._MON_HOLE.search(m)
            if not mm:
                continue
            name = mm.group("n").strip().lower()
            was = [x for x in cur.monsters or [] if base_name(x.get("desc") or "").lower() == name]
            gone = [x for x in was if not any((y["x"], y["y"]) == (x["x"], x["y"]) for y in snap.monsters or [])]
            pick = gone if len(gone) == 1 else was if len(was) == 1 else []
            if pick:
                key = self.level_key(snap.status)
                c = (pick[0]["x"], pick[0]["y"])
                self.traps.setdefault(key, set()).add(c)
                self.feature_desc.setdefault(key, {})[c] = "hole"

    _HELD_RE = re.compile(r"^(?:A|Your) bear trap closes on your |^You are caught in a bear trap")

    def _note_held(self, cur: Snap, snap: Snap, messages: list[str]) -> None:
        """Held in a bear trap: from "A bear trap closes on your foot!" / "You are caught in a bear trap." until
        "You finally wriggle free." or a move off the square (p2 shift 31: 12 orthogonal pulls did nothing)."""
        if any(self._HELD_RE.search(m) for m in messages):
            self.held_trap = "bear trap"
        elif self.held_trap and (any(m.startswith("You finally wriggle free") for m in messages)
                                 or (cur.hero is not None and snap.hero is not None and cur.hero != snap.hero)):
            self.held_trap = ""

    MAIN_WEAPON_TURNS = 50        # a weapon wielded this long becomes your usual one (a dagger for #force doesn't)

    def set_wielded(self, text, cls, letter, tool: bool, turn=None) -> None:
        """Record what you wield (from a message or inventory()); the first
        weapon seen in hand is your usual one (main_weapon) until another
        has been wielded MAIN_WEAPON_TURNS turns."""
        if letter is None or letter != self.wielded_letter:
            self.wield_since = turn
        self.wielded, self.wielded_class, self.wielded_letter, self.wield_tool = text, cls, letter, tool
        weapon = letter and text and not tool and (
            (cls or "").startswith("Weapons") or (cls is None and is_weapon_text(text)))
        if weapon and (self.main_weapon is None or re.search(r"\bcursed\b", text)):
            # (a CURSED weapon in hand is welded there — wield.c will_weld(): it is your weapon until it is
            # uncursed, so no "wield your usual weapon again" advice NetHack would refuse; the live game's
            # bones Excalibur, T:3838)
            self.main_weapon = {"letter": letter, "text": _item_core(text)}

    def _promote_weapon(self, turn) -> None:
        """The weapon in hand for MAIN_WEAPON_TURNS turns is your usual one now."""
        if turn is None or not self.wielded or not self.wielded_letter or self.wield_tool:
            return
        if self.wield_since is None:
            self.wield_since = turn
            return
        mw = self.main_weapon
        if turn - self.wield_since < self.MAIN_WEAPON_TURNS or (mw and mw["letter"] == self.wielded_letter
                                                                 and mw["text"] == _item_core(self.wielded)):
            return
        if (self.wielded_class or "").startswith("Weapons") or (self.wielded_class is None
                                                                and is_weapon_text(self.wielded)):
            self.main_weapon = {"letter": self.wielded_letter, "text": _item_core(self.wielded)}

    def _note_wield(self, messages: list[str], turn=None) -> None:
        """Keep self.wielded current from the messages: "You now wield a
        blessed lamp." (#rub / applying a pick-axe wields the tool),
        "a - ... (weapon in hand)." ('w'), "You are empty handed."; anything
        else about wielding makes it unknown (re-checked by inventory())."""
        for m in messages:
            mm = self._WIELD_NOW.search(m)
            if mm:
                self.set_wielded(mm.group(1), None, None, True, turn)
                continue
            mm = self._WIELD_INV.search(m)
            if mm and WIELDED_RE.search(m):
                self.set_wielded(mm.group(1), None, m[0], False, turn)
                continue
            if mm:
                continue     # another inventory line ('w' with pushweapon: "a - ... (alternate weapon; not wielded).")
            if re.search(r"^You are (?:now |already )?empty.handed", m):
                self.set_wielded("", None, None, False, turn)
            elif re.search(r"wield|slips from your|\bwelds? (?:itself|themselves)\b|welded|disarm|wrested|snatches|"
                           r"You are now empty", m):
                # ("The long sword named Excalibur welds itself to your hand!" comes instead of the inventory line)
                self.wielded, self.wielded_class = None, None     # re-check the weapon next time it matters
                self.wielded_letter, self.wield_tool = None, False
            if re.search(r"\b(?:gloves|gauntlets)\b|^You finish your dressing maneuver", m):
                # put on / taken off / stolen / destroyed: re-check (gloves take a turn to put on, and then the
                # only message is "You finish your dressing maneuver." — the guard kept "no gloves")
                self.gloves = None

    # eat.c givit() / attrib.c attrcurse() / level-up messages -> (intrinsic, gained?)
    _INTRINSIC_MSGS = [
        (r"^You feel a momentary chill\.|^You be chillin'", "fire", True),
        (r"^You feel full of hot air\.", "cold", True),
        (r"^You feel wide awake\.", "sleep", True),
        (r"^You feel very firm\.|^You feel totally together", "disintegration", True),
        (r"^Your health currently feels amplified!|^You feel grounded in reality", "shock", True),
        (r"^You feel (?:especially )?healthy\.", "poison", True),
        (r"^You feel very jumpy\.|^You feel diffuse", "teleportitis", True),
        (r"^You feel in control of yourself\.|^You feel centered in your personal space", "teleport control", True),
        (r"^You feel a strange mental acuity\.|^You feel in touch with the cosmos", "telepathy", True),
        (r"^You feel quick!", "speed", True),
        (r"^You feel warmer\.", "fire", False), (r"^You feel cooler\.", "cold", False),
        (r"^You feel a little sick!", "poison", False), (r"^You feel less jumpy\.", "teleportitis", False),
        (r"^Your senses fail!", "telepathy", False), (r"^You feel slower\.", "speed", False),
        (r"^You feel clumsy\.", "stealth", False),
    ]

    def _note_intrinsics(self, messages: list[str]) -> None:
        for m in messages:
            for pat, name, gained in self._INTRINSIC_MSGS:
                if re.search(pat, m):
                    (self.intrinsics.add if gained else self.intrinsics.discard)(name)

    # quest.txt QT_ASSIGNQUEST (00021), one fragment per role (after quest.c's %-substitutions): the leader
    # sets got_quest — from then on each visit only says an encouragement (quest.c chat_with_leader Rule 1)
    _QUEST_ASSIGNED = re.compile(
        r"Grave times have befallen the college|The world is in great need of your assistance|"
        r"I shall tell you a tale of great suffering among your people|"
        r"For the first time, you sense a smile on|Thou art truly ready, as no |"
        r"During one of the Great Meditations a short time ago|At one of the Great Festivals a short time ago|"
        r"why we so desperately need your help|Will everyone not going to retrieve |"
        r"indeed you are ready\.  I can now tell you what it is that I require of you|"
        r"You have indeed proven yourself a worthy |But it is now likely that you can defeat |"
        r"you truly are ready for this dire task")

    def _note_quest(self, messages: list[str]) -> None:
        if self.quest_given:
            return
        if any(self._QUEST_ASSIGNED.search(" ".join(m.split()).replace(". ", ".  ")) for m in messages):
            self.quest_given = True
            mem = getattr(self, "memory", None)
            if mem is not None and isinstance(getattr(mem, "state", None), dict):
                mem.state["quest_given"] = True

    _CHARMED_OFF = re.compile(r"^You gladly (?:start removing|continue removing|hand over|let (?:her|him) take) "
                              r"your (?P<what>.+?)\.$")

    def _note_theft(self, messages: list[str], turn) -> None:
        for m in messages:
            cm = self._CHARMED_OFF.search(m)
            if cm:
                # steal.c: a nymph's/foocubus's charm takes armor OFF first; a second charm can replace the
                # steal target and leave the first piece unworn in your pack (p4 shift 3 #1346: the gray dragon
                # scale mail — no MR, AC 4 — and only the AC number said so)
                self.charmed_off = [c for c in (getattr(self, "charmed_off", None) or [])
                                    if c["what"] != cm.group("what")] + [{"turn": turn, "what": cm.group("what")}]
                continue
            co = getattr(self, "charmed_off", None)
            if co and (re.search(r"^You finish your dressing maneuver|^You are now wearing ", m)
                       or re.match(r"^[a-zA-Z] - .*\(being worn\)", m)):
                word = m.lower()
                self.charmed_off = [c for c in co if c["what"].split()[-1].lower() not in word]
            mm = self.THEFT_RE.search(m)
            if mm and " from " not in (mm.group("what") or "") and "some gold from" not in m:
                self.last_theft = {"turn": turn, "msg": m, "what": (mm.group("what") or "gold").strip(),
                                   "who": (mm.group("who") or "").strip()}
                if co:
                    stolen = (mm.group("what") or "").lower()
                    self.charmed_off = [c for c in co if c["what"].split()[-1].lower() not in stolen]
                continue
            lt = self.last_theft
            if lt and re.match(r"^[a-zA-Z$] - ", m):
                core = re.sub(r"^(?:the|an?|your|\d+) ", "", lt["what"]).split(" (")[0]
                if core and core.lower() in m.lower():
                    self.last_theft = None        # picked it back up
        self._note_gone_items(messages)

    _GONE_ITEM = re.compile(r"^You drop (?P<a>.+?)\.$|^You put (?P<b>.+?) into |^(?!You ).+? (?:steals|stole) "
                            r"(?P<c>.+?)[.!]$")

    def _note_gone_items(self, messages: list[str]) -> None:
        """Items you dropped, bagged or lost to a thief are no longer curse SUSPECTS (a curse hits only what you
        carry: sit.c rndcurse() — p1 shift 39 #192: the Bell lying under you was listed)."""
        sus = getattr(self, "unknown_buc", None)
        if not sus:
            return
        for m in messages:
            mm = self._GONE_ITEM.search(m)
            if not mm:
                continue
            what = (mm.group("a") or mm.group("b") or mm.group("c") or "").lower()
            core = re.sub(r"^(?:the|an?|your|\d+) ", "", what).split(" (")[0].strip()
            if core:
                self.unknown_buc = [e for e in self.unknown_buc if core not in e.lower()]

    PET_NOTE_TURNS = 30       # the arrival obs says the pet stayed behind this long (it survives a pause)

    def _note_pet(self, snap: Snap, messages: list) -> None:
        """Where your pet was last in view (the stairs helpers must not leave it without a word: p4 shift 1
        #739/#1700)."""
        if any(m.startswith("You have a sad feeling for a moment") for m in messages):
            self.pet_seen = None                  # mon.c monkilled(): your pet died out of your sight
            return
        seen = self.pet_seen
        if seen and messages:
            kind = re.sub(r"^(?:tame|peaceful) ", "", seen.get("desc") or "").strip()
            if kind and any(re.search(rf"\b{re.escape(kind)}\b.*\b(?:is killed|is destroyed|dies)\b|"
                                      rf"^You (?:kill|destroy) (?:poor |your )?.*\b{re.escape(kind)}\b", m)
                            for m in messages):
                self.pet_seen = None              # killed in view ("The little dog is killed!"): nothing to wait for
                return
        if snap.state.kind != "command" or not snap.status.ok:
            return
        pets = [m for m in snap.monsters or [] if (m.get("tame") or m.get("pet")) and not m.get("statue")]
        if pets:
            p = min(pets, key=lambda m: m.get("dist") if m.get("dist") is not None else 99)
            self.pet_seen = {"key": self.level_key(snap.status), "ldesc": snap.status.ldesc,
                             "turn": snap.status.turn, "desc": p.get("desc") or p.get("ch"), "at": (p["x"], p["y"])}
            pl = self.pet_left
            if pl and snap.status.ldesc == pl.get("ldesc"):
                self.pet_left = None              # back with it

    _PET_STAYS = re.compile(r"^(?P<who>.+?) is still (?P<why>eating|trapped)\.$")

    def _note_pet_stays(self, cur: Snap, snap: Snap, messages: list, moved: bool) -> None:
        """dog.c keepdogs(): a pet next to you that is eating or trapped stays behind ("The kitten is still
        eating."): the arrival obs says so."""
        if not moved or cur is None or not cur.status.ok:
            return
        for m in messages:
            mm = self._PET_STAYS.match(m)
            if mm:
                who = re.sub(r"^The ", "", mm.group("who"))
                seen = self.pet_seen or {}
                self.pet_left = {"ldesc": cur.status.ldesc, "turn": snap.status.turn, "desc": who,
                                 "at": seen.get("at") if seen.get("ldesc") == cur.status.ldesc else None,
                                 "why": f"it was still {mm.group('why')}"}

    def pet_left_note(self, snap: Snap) -> str:
        pl = self.pet_left
        if not pl or not snap.status.ok or snap.status.turn is None or pl.get("turn") is None:
            return ""
        if snap.status.ldesc == pl["ldesc"] or not 0 <= snap.status.turn - pl["turn"] <= self.PET_NOTE_TURNS:
            return ""
        return (f"your pet ({pl['desc']}) did NOT come along — it stayed on {pl['ldesc']}"
                + (f" at {pl['at']}" if pl.get("at") else "") + (f" ({pl['why']})" if pl.get("why") else "")
                + f", T:{pl['turn']}: go back for it (a pet follows only from a square next to you), or go on "
                  "without it")

    def charm_note(self, turn) -> str:
        """Armor a charm took off that isn't known to be worn again (or stolen), else ''."""
        co = [c for c in (getattr(self, "charmed_off", None) or [])
              if turn is not None and c.get("turn") is not None and 0 <= turn - c["turn"] <= 500]
        if not co:
            return ""
        return ("a charm took OFF your " + ", ".join(f"{c['what']} (T:{c['turn']})" for c in co)
                + " — NOT WORN now: W to wear it again (its AC — and magic resistance/reflection, if it gave them — "
                  "are gone meanwhile)")

    def theft_note(self, turn) -> str:
        lt = self.last_theft
        if not lt or turn is None or lt.get("turn") is None or not 0 <= turn - lt["turn"] <= self.THEFT_TURNS:
            return ""
        big = re.search(r"Amulet of Yendor|Bell of Opening|Candelabrum|Book of the Dead|silver bell|"
                        r"papyrus spellbook|candelabrum", lt["what"], re.I)
        if re.search(r"\bsnatches\b", lt.get("msg", "")):
            # muse.c MUSE_BULLWHIP: the whip yanks your weapon into ITS inventory — no teleport (p2 shift 37 #51:
            # a horned devil stayed adjacent holding Excalibur)
            return (f"DISARMED at T:{lt['turn']} ({turn - lt['turn']} turns ago): {lt['msg']} — the bullwhip "
                    "wielder HOLDS it and is still next to you: wield a spare weapon (blessed/silver against "
                    "demons) and kill it to get it back — or it snatches again")
        return (f"STOLEN at T:{lt['turn']} ({turn - lt['turn']} turns ago): {lt['msg']}"
                + (" — you NEED it to win: kill the thief to get it back (the Wizard teleports off and "
                   "comes back to harass you; nymphs/monkeys drop loot when killed)" if big else
                   " — the thief teleported off with it; kill it to get it back"))

    def wield_note(self) -> str:
        """A warning when you are known to wield something that isn't a
        weapon (a lamp after #rub, nothing at all), else ''."""
        w = self.wielded
        if w is None:
            return ""
        if w == "":
            return "you are EMPTY-HANDED (w + letter to wield your weapon)"
        if re.search(r"\bpick-axe\b", w):
            # applying it to dig wields it (apply.c wield_tool); dig() wields your weapon again, but a
            # paused/abandoned dig or a pick-axe applied by hand leaves it in your hands
            return f"you WIELD {w} (a digging tool) — w + letter to wield your weapon again"
        if not (self.wielded_class or "").startswith("Weapons") and not is_weapon_text(w):
            return f"you WIELD {w} — not a weapon (w + letter to wield your weapon again)"
        mw = self.main_weapon
        if mw and self.wielded_letter and self.wielded_letter != mw["letter"]:
            # (p4 shift 1 #2208: a pause between "w + spare dagger, #force" and the re-wield left the dagger in
            # hand with no word about it)
            return (f"you wield {self.wielded_letter} - {_item_core(w)}, not your usual weapon ({mw['letter']} - "
                    f"{mw['text']}): "
                    f"w{mw['letter']} to wield it again (after {self.MAIN_WEAPON_TURNS} turns in hand this one "
                    "counts as your usual weapon)")
        return ""

    # shk.c u_entered_shop(): "Velkommen, p2!  Welcome to Carignan's antique weapons outlet!"
    # ("Welcome again to ..." on later visits); printed on the first square inside the door
    _SHOP_WELCOME = re.compile(r"^[^!]+!\s+Welcome(?: again)? to (?P<name>[^!]+?(?:'s|s') [^!]+)!")

    def _room_rect(self, snap: Snap, start, prev=None) -> tuple | None:
        """The interior (x1, y1, x2, y2) of the lit room around `start`,
        scanning to the walls along its row and column. On a door (in_rooms()
        counts it as the shop, so the welcome comes there) the room is the
        side whose scan is closed by walls — in Minetown the street outside a
        shop door is lit floor too, and trying east/south first recorded the
        street as the shop (p4 shift 2) — else the side you didn't come from
        (`prev`: your square before this step)."""
        from .mapscan import _door_like
        x, y = start
        scr = snap.screen

        def edge(cx, cy):
            ch = scr.at(cx, cy)
            # a '+' is a door only in a wall line: a spellbook on the shop floor doesn't end the scan
            return ch in "|-# " or (ch == "+" and _door_like(scr, cx, cy))

        def scan(ix, iy, door):
            def run(dx, dy):
                cx, cy = ix, iy
                for _ in range(80):
                    nx, ny = cx + dx, cy + dy
                    if not (0 <= nx < 80 and MAP_TOP < ny <= MAP_BOTTOM) or edge(nx, ny) or (nx, ny) == door:
                        return cx if dx else cy
                    cx, cy = nx, ny
                return None
            x1, x2, y1, y2 = run(-1, 0), run(1, 0), run(0, -1), run(0, 1)
            if None in (x1, x2, y1, y2) or x2 - x1 > 40 or y2 - y1 > 15:
                return None
            return (x1, y1, x2, y2)

        def gaps(rect, door):
            """Squares of the ring around `rect` that aren't wall (or unseen): a street or corridor leads on."""
            x1, y1, x2, y2 = rect
            ring = [(cx, cy) for cx in range(x1 - 1, x2 + 2) for cy in (y1 - 1, y2 + 1)] + \
                   [(cx, cy) for cy in range(y1, y2 + 1) for cx in (x1 - 1, x2 + 1)]
            return sum(1 for c in ring if c != door and scr.at(*c) not in "|- ")

        if scr.at(x, y - 1) in "|-" and scr.at(x, y + 1) in "|-":       # a door in a left/right wall
            sides = [(d, 0) for d in (1, -1) if not edge(x + d, y)]
        elif scr.at(x - 1, y) in "|-" and scr.at(x + 1, y) in "|-":     # a door in a top/bottom wall
            sides = [(0, d) for d in (1, -1) if not edge(x, y + d)]
        else:
            return scan(x, y, None)
        if not sides:
            return scan(x, y, None)
        door = tuple(start)                                              # (the '@' there is part of the wall)
        best = None
        for dx, dy in sides:
            rect = scan(x + dx, y + dy, door)
            if rect is None:
                continue
            came = prev is not None and tuple(prev) != door and (
                (prev[0] - x) * dx > 0 if dx else (prev[1] - y) * dy > 0)
            n = gaps(rect, door)
            key = (n > 0, came, n, -(rect[2] - rect[0] + 1) * (rect[3] - rect[1] + 1))   # (then the bigger room)
            if best is None or key < best[0]:
                best = (key, rect)
        return best[1] if best else None

    def _note_shop(self, snap: Snap, messages: list[str], prev_hero=None) -> None:
        if snap.hero is None or not snap.status.ok:
            return
        for m in messages:
            mm = self._SHOP_WELCOME.search(m)
            if not mm:
                continue
            rect = self._room_rect(snap, snap.hero, prev_hero)
            if rect is None:
                continue
            lst = self.shops.setdefault(self.level_key(snap.status), [])
            x1, y1, x2, y2 = rect
            name = mm.group("name")
            # one shop per shopkeeper: a new welcome replaces a wrong old record of the same shop
            lst[:] = [e for e in lst if (e[2] < x1 or e[0] > x2 or e[3] < y1 or e[1] > y2) and e[4] != name]
            lst.append([x1, y1, x2, y2, name])

    def _validate_shops(self, snap: Snap) -> None:
        """Drop a recorded shop room whose ring (the walls round it) shows open floor in 2+ places on the screen:
        an older harness recorded the street outside east/south doors as the shop (p4 shift 3 #24: the stale
        records survived the fix); a real shop's ring is wall but for its one door."""
        if not snap.status.ok or snap.hero is None:
            return
        lst = self.shops.get(self.level_key(snap.status))
        if not lst:
            return
        scr = snap.screen
        keep = []
        for e in lst:
            x1, y1, x2, y2 = e[:4]
            ring = [(cx, cy) for cx in range(x1 - 1, x2 + 2) for cy in (y1 - 1, y2 + 1)] + \
                   [(cx, cy) for cy in range(y1, y2 + 1) for cx in (x1 - 1, x2 + 1)]
            open_ = sum(1 for c in ring if scr.at(*c) in ".#" and c != snap.hero)
            if open_ < 2:
                keep.append(e)
        if len(keep) != len(lst):
            lst[:] = keep

    def shop_at(self, cell, status: Status | None = None) -> str:
        """The name of the known shop that `cell` is in — its interior or its
        door (NetHack's in_rooms() counts the door as the shop) — or ''."""
        if cell is None:
            return ""
        for x1, y1, x2, y2, name in self.shops.get(self.level_key(status), []):
            if x1 - 1 <= cell[0] <= x2 + 1 and y1 - 1 <= cell[1] <= y2 + 1:
                return name
        return ""

    def _here_text(self, snap: Snap, cell=None) -> str:
        cell = cell or snap.hero
        if cell is None or not snap.status.ok:
            return ""
        return self.here_seen.get(self.level_key(snap.status), {}).get(cell, "")

    def _remember_terrain(self, snap: Snap, messages: list[str]) -> None:
        """Remember stairs/fountains/altars/thrones per level so the one under
        the hero (hidden by the '@') is still known: sets snap.under."""
        if snap.hero is None or not snap.status.ok or _engulfed(snap.screen, snap.hero):
            return
        key = self.level_key(snap.status)
        feats = self.terrain_seen.setdefault(key, {})
        from .mapscan import _door_like
        hx, hy = snap.hero
        for y in range(MAP_TOP + snap.state.msg_rows, MAP_BOTTOM + 1):
            row = snap.screen.row(y)
            for x, ch in enumerate(row):
                if ch in self.FEATURE_CHARS and feature_at(snap.screen, x, y):
                    if ch == "\\" and feats.get((x, y)) != "\\" and (
                            snap.state.kind != "command" or (x - hx, y - hy) in ((1, -1), (-1, 1))
                            or _ring_corner(snap.screen, x, y)):
                        # a NEW throne only from a settled map: a yellow '\' is also an acid ray left on
                        # screen by a --More--, and the NE/SW corners of a fire vortex's engulf ring (p1's
                        # memory held throne pairs 2 apart diagonally in Sokoban); a real one stays drawn
                        # and is recorded once you step away
                        continue
                    feats[(x, y)] = ch
                elif snap.screen.color_at(x, y) == 3 and (ch in "|-" or (ch == "+" and _door_like(snap.screen, x, y))):
                    feats[(x, y)] = "D"         # a door (open or closed): no diagonal moves in or out of it
        self._remember_portals(snap, feats)
        water = self.water_seen.setdefault(key, set())
        for y in range(MAP_TOP + snap.state.msg_rows, MAP_BOTTOM + 1):
            row = snap.screen.row(y)
            for x, ch in enumerate(row):
                if ch == "}" and snap.screen.color_at(x, y) != 1:
                    water.add((x, y))
                elif ch in ".#" and (x, y) in water:
                    water.discard((x, y))          # frozen, filled or drained
        if any(re.search(r"brushes against your (?:left |right )?\w+\.$|swings itself around you!$|"
                         r"was hidden under the water|^You are being crushed", m) for m in messages):
            # (mhitu.c AD_WRAP: a sea monster's wrap attempt; "A kraken was hidden under the water!")
            self.level_flags.setdefault(key, set()).add("eels")
        if any(m.startswith(("You sense a faint wave of psychic energy", "A wave of psychic energy pours over you"))
               for m in messages):
            self.level_flags.setdefault(key, set()).add("mind_flayer")      # (monmove.c: one is on this level)
        elif any(re.match(r"^You (?:kill|destroy) the (?:master )?mind flayer\b", m) for m in messages):
            self.level_flags.get(key, set()).discard("mind_flayer")
        if "rogue" in self.level_flags.get(key, ()):
            # the Rogue level turns dark-room floor you can't see back into blank stone (display.c): keep
            # it, or neither the frontier finder nor the route planner knows the room you walked through
            floor = self.floor_seen.setdefault(key, set())
            for y in range(MAP_TOP + snap.state.msg_rows, MAP_BOTTOM + 1):
                row = snap.screen.row(y)
                for x, ch in enumerate(row):
                    if ch in ".#%" or (ch == "+" and _door_like(snap.screen, x, y)):
                        floor.add((x, y))
                    if ch == "+" and _door_like(snap.screen, x, y):
                        # hack.c doorless_door(): Rogue-level doorways have no door but still forbid
                        # diagonal moves into and out of them
                        feats[(x, y)] = "D"
            floor.add(snap.hero)
        self._prune_features(snap, key)
        if any("dries up" in m or "fountain disappears" in m or "throne vanishes" in m for m in messages):
            feats.pop(snap.hero, None)
        for m in messages:
            if m.startswith("You enter what seems to be an older, more primitive world."):
                self.level_flags.setdefault(key, set()).add("rogue")
            if re.match(r"You receive a faint telepathic message from |You again sense .+ (?:pleading for help|"
                        r"demanding your attendance)", m):
                # quest.txt (%Cp 00002-00004): said on arriving at the level that holds the quest portal
                self.level_flags.setdefault(key, set()).add("quest_portal")
            if m.startswith("You feel a strange vibration under your "):
                feats[snap.hero] = "~"          # (only on the vibrating square itself)
            elif m.startswith("You activated a magic portal!") and snap.status.ldesc not in self.ENDGAME:
                feats[snap.hero] = "^"          # you arrive on the other end (not so on the Planes)
                if any(snap.screen.at(snap.hero[0] + dx, snap.hero[1] + dy) in MONSTER_CHARS
                       for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy):
                    # do.c u_collide_m(): a monster on the portal puts you NEXT TO it half the time (p2 shift 34
                    # #83: a squeaky board filed as the portal) — look once the step is done (_verify_arrival)
                    self._arrival_check = {"n": snap.n, "hero": snap.hero, "ch": "^", "old_key": None}
            elif self._INVOKED.search(m):
                # mkinvokearea(): the square becomes the down stairs, the area around is rebuilt (a ring
                # of fire traps, a moat): old traps there are gone, the tracker re-reads #terrain
                for c, v in list(feats.items()):
                    if v == "~" or (abs(c[0] - snap.hero[0]) <= 6 and abs(c[1] - snap.hero[1]) <= 5):
                        del feats[c]
                feats[snap.hero] = ">"
                tr = self.traps.get(key)
                if tr:
                    tr.difference_update({c for c in tr if abs(c[0] - snap.hero[0]) <= 6
                                          and abs(c[1] - snap.hero[1]) <= 5})
        # "There is a staircase up here." etc. (':' look, or stepping onto a pile):
        # the feature under the hero even when an object/statue covers it
        for m in messages:
            mm = self._HERE_FEATURE.search(m)
            if mm:
                feats[snap.hero] = self._HERE_CH[mm.group(1)]
            ma = re.search(r"^There is an? (?:high )?altar to (.+?) \((\w+)\) here", m)
            if ma:
                self.feature_desc.setdefault(self.level_key(snap.status), {})[snap.hero] = \
                    f"{ma.group(2)} altar ({ma.group(1)})"
        snap.under = feats.get(snap.hero)

    def _prune_features(self, snap: Snap, key, arrival: bool = False) -> bool:
        """Drop remembered features (stairs, fountains, altars, thrones, doors) the map now contradicts:
        plain floor or a corridor there (a fountain dried up, a door broken; not a green gas cloud over it),
        and on a settled map a wall. arrival=True — the first settled map after a level change, once the ^O
        name merged this level's old memory in: also where the map shows NOTHING. The game redraws all it
        remembers of a level you come back to, so a remembered '>' on a blank square is another level's
        (p1 shift 35 #306: DL3's two '>' listed on DL2 after a level teleport). Not on a level the game may
        have forgotten (amnesia, a mind flayer, "You have a sense of deja vu."), the Rogue level (dark floor
        fades to blank) or the Planes. Returns True when something went."""
        feats = self.terrain_seen.get(key) if key is not None else None
        if not feats or snap.hero is None:
            return False
        scr = snap.screen
        top = MAP_TOP + snap.state.msg_rows
        settled = snap.state.kind == "command"
        blank_ok = (arrival and settled and snap.status.ok and snap.status.ldesc not in self.ENDGAME
                    and not ({"rogue", "forgotten"} & self.level_flags.get(key, set())))
        hx, hy = snap.hero
        gone = []
        fd = self.feature_desc.get(key) or {}
        for c, v in feats.items():
            if v == "^" and fd.get(c) and "portal" not in fd[c]:
                gone.append(c)    # a look found another trap there (p2 shift 34: a squeaky board as the portal)
                continue
            if v in "^~" or c == snap.hero or not top <= c[1] <= MAP_BOTTOM:
                continue      # (portals never go away; on the Plane of Air unseen squares are '#' clouds)
            now, col = scr.at(*c), scr.color_at(*c)
            if now == "." or (now == "#" and col != 10) \
                    or (settled and now in "|-" and col != 3 and max(abs(c[0] - hx), abs(c[1] - hy)) > 1) \
                    or (blank_ok and now == " "):
                gone.append(c)
        links = self.stair_links.get(key, {})
        for c in gone:
            if feats.pop(c) in "<>":
                links.pop(c, None)
        if gone and arrival:
            self.log_event({"ev": "memory_pruned", "level": key, "cells": {f"{x},{y}": "" for x, y in gone}})
            mem = getattr(self, "memory", None)
            if mem is not None and hasattr(mem, "drop_cells"):
                try:
                    mem.drop_cells(key, gone)
                except Exception as e:  # noqa: BLE001
                    self.log_event({"ev": "drop_cells_error", "err": repr(e)})
        return bool(gone)

    # the game forgot levels' maps (read.c forget_levels(): a mind flayer's tentacles, a scroll of amnesia)
    # or you come back to one it forgot (do.c goto_level() "familiar"; 1 in 4 of those arrivals says nothing)
    _AMNESIA = re.compile(r"^(?:Your brain is eaten!|Who was that Maud person anyway\?|"
                          r"Thinking of Maud you forget everything else\.|"
                          r"As your mind turns inward on itself, you forget everything else\.|"
                          r"Your mind releases itself from mundane concerns\.)")
    _DEJA_VU = re.compile(r"^(?:You have a sense of deja vu\.|You feel like you've been here before\.|"
                          r"This place (?:looks|seems) familiar\.\.\.|Whoa!  Everything (?:looks|seems) different\.|"
                          r"You are surrounded by twisty little passages, all alike\.|"
                          r"Gee, this (?:looks|seems) like uncle Conan's place\.\.\.)")

    def _note_forgetting(self, snap: Snap, messages: list) -> None:
        """Levels whose map the game may have lost: flagged "forgotten", their harness memory then knows
        more than the map shows, and the arrival prune keeps it (see _prune_features)."""
        if any(self._AMNESIA.search(m) for m in messages):
            mem = getattr(self, "memory", None)
            keys = set(self.terrain_seen) | set(((getattr(mem, "state", None) or {}).get("levels") or {}))
            keys.add(self.level_key(snap.status))
            for k in keys:
                self.level_flags.setdefault(k, set()).add("forgotten")
                lv = ((getattr(mem, "state", None) or {}).get("levels") or {}).get(k)
                if lv is not None and "forgotten" not in lv.get("flags", []):
                    lv["flags"] = sorted(set(lv.get("flags", [])) | {"forgotten"})
        elif any(self._DEJA_VU.search(m) for m in messages):
            self.level_flags.setdefault(self.level_key(snap.status), set()).add("forgotten")

    def _remember_portals(self, snap: Snap, feats: dict | None = None) -> None:
        """Magic portals (bright magenta '^') and the vibrating square (magenta
        '~') on the map, also inside a ^F / crystal-ball browse view (the
        Planes of Air and Water keep no map of their own)."""
        if not snap.status.ok or "Hallu" in snap.status.conditions or snap.state.kind not in ("command", "getpos") \
                or getattr(snap, "engulfed", False):
            return
        if feats is None:
            feats = self.terrain_seen.setdefault(self.level_key(snap.status), {})
        for y in range(MAP_TOP + snap.state.msg_rows, MAP_BOTTOM + 1):
            row = snap.screen.row(y)
            for x, ch in enumerate(row):
                if ch == "^" and snap.screen.color_at(x, y) == self.PORTAL_COLOR:
                    feats[(x, y)] = "^"
                elif ch == "~" and snap.screen.color_at(x, y) == self.VIBRATING_COLOR:
                    feats[(x, y)] = "~"

    # ---- low level ---------------------------------------------------------
    def capture(self) -> Snap:
        scr = self.term.capture()
        st = classify(scr)
        if st.kind == "getpos":
            self.getpos_active = True
        elif st.kind == "command" and self.getpos_active:
            st.kind = "getpos"
        elif st.kind not in ("command", "getpos"):
            self.getpos_active = False
        status = parse_status(scr)
        if status.ok:
            if status.hd is None:
                self.real_xl = status.xl
            else:
                # polymorphed: the status line shows HD instead of Xp; keep the
                # hero's own level in .xl so scripts keyed on it stay sane
                status.polymorphed = True
                status.xl = self.real_xl or 0
            self.last_status = status
        elif st.kind not in ("command", "unknown") and self.last_status is not None:
            # a menu/text window covers the status lines: report the last
            # readable status, flagged stale
            status = copy.copy(self.last_status)
            status.conditions = list(status.conditions)
            status.stale = True
        snap = Snap(screen=scr, state=st, status=status, n=self.n)
        return snap

    def _plausible(self, snap: Snap) -> bool:
        k = snap.state.kind
        if k == "unknown":
            return False
        if k == "command":
            cx, cy = snap.screen.cursor
            ch = snap.screen.at(cx, cy)
            if ch == " ":
                return False
            if not snap.status.ok:
                return False
            # At the command prompt the cursor sits on the hero, drawn as '@'
            # unless polymorphed (status shows HD) or hallucinating. Anything
            # else means the final redraw/cursor placement hasn't arrived yet
            # (seen after a --More-- interrupted a travel).
            st = snap.status
            if ch != "@" and st.hd is None and "Hallu" not in st.conditions:
                return False
            if cy == 1:
                return False   # the hero never stands on map row 1 (level edge): likely wrapped text
            if _explosion_frame(snap.screen):
                return False   # an explosion animation is still on screen (explode() puts the cursor on @)
        return True

    def _settle(self, size0: int, expect_output: bool = True) -> Snap:
        t = self.timing
        first = t.first if expect_output else min(t.first, t.quiet * 4)
        self.term.wait_quiet(size0, first, t.quiet, t.max_wait)
        snap = self.capture()
        self._settled_raw = self.term.raw_size()
        stable = 0
        for _ in range(t.recheck):
            if self._plausible(snap):
                break
            size1 = self.term.raw_size()
            self.term.wait_quiet(size1, t.quiet * 3, t.quiet, t.max_wait)
            prev, snap = snap, self.capture()
            self._settled_raw = self.term.raw_size()
            # an implausible screen that no longer changes is the real one
            # (invisible hero with no '@' drawn, odd displays): stop waiting
            if snap.screen.chars == prev.screen.chars and snap.screen.cursor == prev.screen.cursor \
                    and self.term.raw_size() == size1:
                stable += 1
                if stable >= 3:
                    break
            else:
                stable = 0
        return snap

    def send_bytes(self, data: bytes) -> Snap:
        """Send raw bytes, settle, capture. No --More-- handling."""
        with self.lock:
            if self.getpos_active and any(b in b".,;:\x1b" for b in data):
                self.getpos_active = False
            size0 = self.term.raw_size()
            self.term.send(data)
            return self._settle(size0)

    # ---- the main entry point ---------------------------------------------
    # ---- safety guards (refuse keystrokes that are classic instant deaths) ----
    NEVER_MELEE = ("floating eye", "gas spore", "green slime")
    _MOVE = {ord("h"): (-1, 0), ord("j"): (0, 1), ord("k"): (0, -1), ord("l"): (1, 0),
             ord("y"): (-1, -1), ord("u"): (1, -1), ord("b"): (-1, 1), ord("n"): (1, 1)}
    _CORPSE_Q = re.compile(r"There (?:is|are) (?:an? |\d+ )?(.+?) corpses? here; eat (?:it|one)\?")
    _TIN_SMELL = re.compile(r"It smells like (?:the )?(.+?)\.")
    GRAY_STONE = re.compile(r"\bgr[ae]y stones?\b")
    _KNOWN_SAFE_BUC = re.compile(r"\b(?:uncursed|blessed)\b")    # only a CURSED loadstone can't be dropped

    def _gloves_hint(self) -> str:
        """The end of a cockatrice-corpse refusal: what the harness knows about your gloves."""
        if self.gloves is None:
            return ("The harness doesn't know whether you wear gloves: inventory() tells it (worn gloves lift "
                    "this guard), or force=True if you are sure.")
        return "You wear no gloves (per inventory()): put some on first."

    @staticmethod
    def _singulars(plural: str) -> list[str]:
        """'cockatrices' -> candidates ['cockatrices', 'cockatrice', ...]; 'dwarves' -> 'dwarf'."""
        p = plural.strip()
        out = [p]
        if p.endswith("ves"):
            out.append(p[:-3] + "f")
        if p.endswith("es"):
            out.append(p[:-2])
        if p.endswith("s"):
            out.append(p[:-1])
        if p.endswith("men"):
            out.append(p[:-3] + "man")
        return out

    def _tin_verdict(self, text: str):
        """(name, reasons) if the tin that smells like this is never to be eaten."""
        m = self._TIN_SMELL.search(text)
        if not m:
            return None
        if m.group(1).strip() == "chicken":
            # eat.c: a cockatrice/chickatrice tin smells like "chicken" while you hallucinate
            # (or resist stoning — which a Valkyrie doesn't)
            return "cockatrice", ["NEVER: 'chicken' is how a cockatrice tin smells while hallucinating: stoning"]
        from .danger import monster_record
        from .data.corpses import corpse_verdict
        for name in self._singulars(m.group(1)):
            if monster_record(name) is None:
                continue
            v = corpse_verdict(name, hero_race=HERO_RACE, hero_role=HERO_ROLE, age_turns=0, has_poison_res=False)
            if getattr(v.verdict, "value", v.verdict) == "NEVER":
                return name, v.reasons
            return None
        return None

    def _guard(self, snap: "Snap", unit: bytes, force: bool) -> None:
        if force or not unit:
            return
        k = snap.state.kind
        if k == "extcmd" and unit[:1] != b"\x1b" and not unit.endswith((b"\r", b"\n")):
            # stray keys typed into '# ' autocomplete into an extended command ("s" -> #sit)
            raise PermissionError(f"refusing {unit!r}: an extended-command prompt ('#') is open — finish it "
                                  "with the whole command and <CR> (e.g. 'pray<CR>') or <Esc> it first")
        if k == "command" and unit in (b"F", b"m", b"M", b"g", b"G"):
            # cmd.c parse(): a prefix reads the next key silently (no prompt on screen) — the
            # next thing you send would be taken as its direction
            raise PermissionError(f"refusing to send the prefix {unit.decode()!r} on its own: NetHack silently "
                                  f"waits for its direction key. Send both at once, e.g. do('{unit.decode()}h').")
        if k == "command":
            key = unit[1] if unit[:1] == b"F" and len(unit) > 1 else unit[0] if len(unit) == 1 else None
            step = unit[1] if unit[:1] == b"m" and len(unit) == 2 else unit[0] if len(unit) == 1 else None
            if step in self._MOVE and snap.hero is not None and snap.status.ok:
                dx, dy = self._MOVE[step]
                tx, ty = snap.hero[0] + dx, snap.hero[1] + dy
                if (tx, ty) in self.traps.get(self.level_key(snap.status), ()) \
                        and snap.screen.at(tx, ty) not in ".#" \
                        and (self.feature_desc.get(self.level_key(snap.status)) or {}).get((tx, ty)) \
                        != "squeaky board":
                    # (a squeaky board only squeaks — wakes monsters nearby: p2 shift 36 asked to step on them)
                    # (plain floor/corridor there: NetHack knows no trap on it — our memory is stale, the step is
                    # fine; _note_traps forgets it: p3 shift 18 #312, p1 shift 37 #633)
                    raise PermissionError(
                        f"refusing to step onto the known trap at {(tx, ty)} (NetHack doesn't ask). Go around "
                        f"(travel() avoids traps), or do('{chr(step)}', force=True) / step('{chr(step)}', "
                        "force=True) if you mean it (jumping into a hole/trap door on purpose, entering a magic "
                        "portal, crossing the invocation's fire traps).")
            conds = set(snap.status.conditions) if snap.status.ok else set()
            if key in self._MOVE and snap.hero is not None:
                dx, dy = self._MOVE[key]
                tx, ty = snap.hero[0] + dx, snap.hero[1] + dy
                target = snap.screen.at(tx, ty)
                if "Hallu" in conds and target in MONSTER_CHARS:
                    raise PermissionError(
                        f"refusing to attack/move into the monster at {(tx, ty)} while hallucinating: you can't "
                        "tell what it is (a peaceful? a floating eye?) and NetHack does NOT ask 'Really attack?' "
                        "while you hallucinate. Wait it out, cure it (unicorn horn), or force=True if it is "
                        "certainly hostile (it attacked you).")
                if "Blind" in conds and target == "I":
                    raise PermissionError(
                        f"refusing to attack the remembered unseen monster 'I' at {(tx, ty)} while blind: it may be "
                        "a peaceful (shopkeeper, priest, watchman) and NetHack does not ask when it can't see "
                        "it. force=True if it is attacking you.")
                peace = [m for m in snap.monsters or [] if (m["x"], m["y"]) == (tx, ty) and m.get("peaceful")
                         and not m.get("tame") and not m.get("statue")] if unit[:1] == b"F" else []
                if peace:
                    # uhitm.c attack_checks(): context.forcefight returns before the "Really attack?" question
                    raise PermissionError(
                        f"refusing to F-attack the {peace[0].get('desc')} at {(tx, ty)}: it is PEACEFUL and an F blow "
                        "never asks 'Really attack?' (angering it costs alignment; killing it, more). force=True "
                        "if you mean it.")
            if snap.hero is not None and self.on_elbereth(snap):
                # throws/zaps/kicks are checked at their direction prompt (only hitting a monster counts)
                attack = unit[:1] == b"F" or unit.startswith(b"#force")
                if key in self._MOVE and unit[:1] != b"m":
                    dx, dy = self._MOVE[key]
                    tgt = (snap.hero[0] + dx, snap.hero[1] + dy)
                    there = [m for m in snap.monsters or [] if (m["x"], m["y"]) == tgt and not m.get("tame")
                             and not m.get("pet") and not m.get("statue")]
                    attack = attack or bool(there)
                    if there and all(ignores_elbereth(m) for m in there):
                        attack = False       # (no hypocrisy; the blow smudges the dust: re-engrave after)
                if attack:
                    raise PermissionError(
                        "refusing to attack from your Elbereth square: melee, throwing/firing, zapping or kicking "
                        "while standing on it erases it and costs -5 alignment ('You feel like a hypocrite') "
                        "unless the target ignores Elbereth (@ humans/elves, minotaurs, shopkeepers). Step off "
                        "first, or force=True.")
            if len(unit) == 1 and unit[0] in self._MOVE and snap.hero is not None:
                dx, dy = self._MOVE[unit[0]]
                tgt = (snap.hero[0] + dx, snap.hero[1] + dy)
                peace = [m for m in snap.monsters or [] if (m["x"], m["y"]) == tgt and m.get("peaceful")
                         and not m.get("tame") and not m.get("pet")]
                if peace:
                    raise PermissionError(
                        f"refusing to walk into the {peace[0].get('desc')} at {tgt}: you can't swap places with "
                        "peacefuls, so NetHack would ask 'Really attack?'. Wait a turn ('.') or go around. "
                        "(If it turned hostile and is attacking you, force=True.)")
            if step in self._MOVE and snap.hero is not None and not conds & {"Lev", "Fly"}:
                dx, dy = self._MOVE[step]
                if snap.screen.at(snap.hero[0] + dx, snap.hero[1] + dy) == "}":
                    raise PermissionError(
                        f"refusing to step into the water/lava at {(snap.hero[0] + dx, snap.hero[1] + dy)}: NetHack "
                        "doesn't stop a single step (only running/travel avoid it). Lava is death without fire "
                        "resistance; water soaks your scrolls/potions and can drown you. Go around; force=True only "
                        "with levitation/water walking you're sure of"
                        + (" (Plane of Water: levitation and water walking don't work here — only magical "
                           "breathing makes water safe, and your things still get wet)."
                           if snap.status.ldesc == "Water" else ".")
                        + (" You are BLIND: that '}' is only REMEMBERED — if you froze it ('You hear a crackling "
                           "sound.') it may be ice now; take the blindfold off and look before forcing a step "
                           "(p1 shift 34)." if "Blind" in conds else ""))
            if unit in (b"t", b"f") and snap.hero is not None and snap.status.ok \
                    and self.shop_at(snap.hero, snap.status):
                raise PermissionError(
                    f"refusing to {'throw' if unit == b't' else 'fire'} inside {self.shop_at(snap.hero, snap.status)}: "
                    "whatever you throw that lands on the shop floor is SOLD to the shopkeeper (you'd buy it back "
                    "dearer), and an unpaid item thrown out of the shop is THEFT (an angry shopkeeper). Fight "
                    "in melee or step outside first; force=True overrides.")
            if unit == b"e" and snap.status.ok and snap.status.hunger == "Satiated" and "Stone" not in conds:
                raise PermissionError(
                    "refusing to eat while Satiated: eating past 2000 nutrition chokes you to death (19 times in "
                    "20), and a one-bite food gives no 'Continue eating?' warning. Wait until 'Not hungry'. "
                    "force=True only for an emergency cure (lizard/acidic corpse against stoning).")
            if unit == b"," and snap.hero is not None:
                txt = self._here_text(snap)
                if self.COCKATRICE_CORPSE.search(txt) and "Things that" not in txt and not self.gloves:
                    # (gloves known from inventory(): p3 shift 19 #503 had to force a gloved pickup)
                    raise PermissionError(
                        "refusing to pick up here: the only object on this square is a cockatrice/chickatrice "
                        "corpse, and ',' takes it without a menu — touching it bare-handed is instant stoning. "
                        + self._gloves_hint())
                kicked = (getattr(self, "kicked_stones", None) or {}).get(self.level_key(snap.status), ())
                if self.GRAY_STONE.search(txt) and "Things that" not in txt and not self._KNOWN_SAFE_BUC.search(txt) \
                        and snap.hero not in kicked:        # (kick_test() saw this one slide: not a loadstone)
                    raise PermissionError(
                        "refusing to pick up the gray stone: it may be a LOADSTONE (cursed ones can't be dropped; "
                        "500 weight). Step off and kick it first: a loadstone doesn't budge ('Thump!'), a "
                        "luckstone/touchstone/flint slides — kick_test(x, y) does that. force=True once you know.")
            if step in self._MOVE and snap.hero is not None and "Blind" in conds:
                dx, dy = self._MOVE[step]
                tgt = (snap.hero[0] + dx, snap.hero[1] + dy)
                killed = self._trice_killed_on(snap, tgt)
                if (self.COCKATRICE_CORPSE.search(self._here_text(snap, tgt)) or killed) and not self.gloves:
                    # (the kill memory too: p2 shift 35 killed two cockatrices ON a doorway with F from beside
                    # it, never stood there, then stepped onto it blindfolded — stoned, life saving used up)
                    raise PermissionError(
                        "refusing to step blind onto "
                        + (f"{tgt}, where a {killed[0]} was killed {killed[1]} turns ago (its corpse is probably "
                           "still there)" if killed and not self.COCKATRICE_CORPSE.search(self._here_text(snap, tgt))
                           else "the square with the cockatrice corpse")
                        + ": while blind you feel the objects you step on, and feeling it bare-handed is instant "
                        "stoning. Wait until you can see (take the blindfold off) or go around. "
                        + self._gloves_hint())
            fkey = key if unit[:1] == b"F" else None
            if (step in self._MOVE or fkey in self._MOVE) and snap.hero is not None and conds & {"Conf", "Stun"}:
                # hack.c domove(): stunned, every move/F-blow goes in a random direction (confused, 1 in 5),
                # and uhitm.c attack_checks() skips "Really attack?" while confused/stunned; a blow (not
                # a plain step, which swaps places) can also land on your pet
                from .danger import base_name
                near = [m for m in snap.monsters or [] if m.get("dist") == 1 and not m.get("statue")
                        and (not m.get("tame") or fkey in self._MOVE)
                        and (m.get("peaceful") or m.get("tame") or m.get("pet")
                             or base_name(m.get("desc") or "") in self.NEVER_MELEE)]
                if near:
                    raise PermissionError(
                        "refusing to " + ("swing" if fkey in self._MOVE else "move") + " while "
                        + "/".join(sorted(conds & {"Conf", "Stun"})) + " next to "
                        + ", ".join(f"the {m.get('desc')} at ({m['x']},{m['y']})" for m in near)
                        + ": it can go astray into it, and NetHack attacks without asking while you "
                        "are confused/stunned. Wait ('s') until it wears off, or force=True.")
            run = len(unit) == 1 and chr(unit[0]).lower().encode()[0] in self._MOVE and chr(unit[0]).isupper()
            if (step in self._MOVE or unit[:1] == b"_" or run) and snap.hero is not None \
                    and conds & {"Conf", "Stun"} and not conds & {"Lev", "Fly"}:
                # hack.c domove() -> confdir(): stunned, EVERY step goes in a random direction (confused, 1 in 5),
                # with no lava/water check — a lava fall burns the bag of holding and all in it even with fire
                # resistance; water blanks scrolls and can drown you (p1 shift 36: fire giants' potions of
                # confusion next to Surtur's lava)
                hx, hy = snap.hero
                wet = sorted((hx + dx, hy + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                             if (dx or dy) and snap.screen.at(hx + dx, hy + dy) == "}")
                if wet:
                    what = "lava" if all(snap.screen.color_at(*c) == 1 for c in wet) else \
                        "water" if not any(snap.screen.color_at(*c) == 1 for c in wet) else "lava/water"
                    raise PermissionError(
                        "refusing to move while " + "/".join(sorted(conds & {"Conf", "Stun"})) + f" next to {what} "
                        f"at {wet[:4]}: a step goes astray (stunned: always; confused: 1 in 5) with no check — "
                        "lava burns your bag and everything in it, water blanks scrolls and can drown you. Don't "
                        "move: fight()/F and searching are fine; apply a unicorn horn or wait it out (do('s')), "
                        "then go. force=True if you must.")
            if key in self._MOVE and snap.hero is not None and "Blind" not in conds:
                dx, dy = self._MOVE[key]
                tx, ty = snap.hero[0] + dx, snap.hero[1] + dy
                for m in snap.monsters or []:
                    if (m["x"], m["y"]) == (tx, ty):
                        from .danger import base_name
                        name = base_name(m.get("desc") or "")
                        if name in self.NEVER_MELEE:
                            raise PermissionError(
                                f"refusing to attack/move into the {name} at {(tx, ty)}: meleeing it is a "
                                f"classic death ({'paralysis' if name == 'floating eye' else 'explosion' if name == 'gas spore' else 'sliming'}). "
                                "Use ranged attacks or go around. force=True overrides.")
                        if name in ("cockatrice", "chickatrice") and not m.get("tame") \
                                and not self.gloves and not self.wielded:
                            # uhitm.c passive(): AD_STON stones you when you hit it with no weapon
                            # wielded and no gloves (attk_protection -> W_ARMG)
                            raise PermissionError(
                                f"refusing to attack/move into the {name} at {(tx, ty)}: "
                                + ("you are EMPTY-HANDED without gloves — hitting it bare-handed is instant "
                                   "stoning. Wield your weapon first." if self.wielded == "" else
                                   "the harness doesn't know whether you wield a weapon (bare-handed = instant "
                                   "stoning): run inventory() first, then attack again.")
                                + " force=True overrides.")
        elif k == "yn" and unit[:1] in (b"y", b"Y") and "Eat it?" in (snap.state.prompt or "") \
                and "Hallu" in (snap.status.conditions if snap.status.ok else ()) \
                and self._TIN_SMELL.search((snap.state.prompt or "") + "  " + "  ".join(snap.messages or [])):
            raise PermissionError("refusing to eat a tin while hallucinating: its smell is made up (a cockatrice "
                                  "tin smells like 'chicken'). Answer n. force=True overrides.")
        elif k == "yn" and unit[:1] in (b"y", b"Y") and "Eat it?" in (snap.state.prompt or "") \
                and self._tin_verdict((snap.state.prompt or "") + "  " + "  ".join(snap.messages or [])):
            name, reasons = self._tin_verdict((snap.state.prompt or "") + "  " + "  ".join(snap.messages or []))
            raise PermissionError(f"refusing to eat the tin of {name}: " + "; ".join(reasons)
                                  + " — answer n (the tin is discarded). force=True overrides.")
        elif k == "direction" and len(unit) == 1 and unit[0] in self._MOVE and self.hero_pos is not None \
                and self.on_elbereth(snap, self.hero_pos):
            # setmangry(via_attack): throwing, firing, zapping or kicking AT a monster from an
            # Elbereth square makes you a hypocrite; down/up/self or an empty line doesn't
            dx, dy = self._MOVE[unit[0]]
            hx, hy = self.hero_pos
            mons = {(m["x"], m["y"]): m for m in snap.monsters or []
                    if not m.get("tame") and not m.get("pet") and not m.get("statue")}
            for i in range(1, 14):
                c = (hx + dx * i, hy + dy * i)
                if c in mons and ignores_elbereth(mons[c]):
                    break                    # the first monster in line ignores Elbereth: no hypocrisy
                if c in mons:
                    raise PermissionError(
                        f"refusing to throw/zap/kick at the {mons[c].get('desc') or 'monster'} at {c} from your "
                        "Elbereth square: it erases the engraving and costs -5 alignment ('You feel like a "
                        "hypocrite') unless the target ignores Elbereth (@ humans/elves, minotaurs, "
                        "shopkeepers). Step off first, or force=True.")
                ch = snap.screen.at(*c)
                if ch == " " or (ch in "|-" and snap.screen.color_at(*c) != 3):
                    break
        elif k == "direction" and unit == b">" and "dig" in (snap.state.prompt or "") and snap.status.ok \
                and self.shop_at(self.hero_pos, snap.status):
            raise PermissionError(
                f"refusing to dig down inside {self.shop_at(self.hero_pos, snap.status)}: the shopkeeper grabs your "
                "backpack as you fall through the hole. Dig outside the shop. force=True overrides.")
        elif k in ("yn", "getlin") and unit[:1] in (b"y", b"Y") and "Continue eating?" in (snap.state.prompt or ""):
            raise PermissionError(
                "refusing to continue eating: you started while Satiated and are nearly full — going on chokes you "
                "to death (19 times in 20). Answer no. force=True overrides.")
        elif k == "yn" and unit[:1] in (b"y", b"Y") and "Still climb?" in (snap.state.prompt or ""):
            raise PermissionError(
                "refusing 'y' to 'Beware, there will be no return! Still climb?': going up from dungeon level 1 "
                "LEAVES THE DUNGEON and ends the game, unless you carry the real Amulet of Yendor (then it "
                "takes you to the Planes). Answer n. force=True only with the Amulet.")
        elif k == "menu" and snap.state.menu is not None and "Pick up what?" in (snap.state.prompt or "") \
                and unit in (b"\r", b"\n"):
            bad = [i.text for i in snap.state.menu.selectable() if i.selected and self.COCKATRICE_CORPSE.search(i.text)]
            if bad and not self.gloves:
                raise PermissionError(
                    f"refusing to confirm the pickup of {bad[0]!r}: touching a cockatrice corpse bare-handed is "
                    "instant stoning. Unselect it (its letter again). " + self._gloves_hint())
            stones = [i.text for i in snap.state.menu.selectable() if i.selected and self.GRAY_STONE.search(i.text)
                      and not self._KNOWN_SAFE_BUC.search(i.text)]
            if stones:
                raise PermissionError(
                    f"refusing to confirm the pickup of {stones[0]!r}: it may be a LOADSTONE (cursed: can't be "
                    "dropped). Unselect it and kick it first (a loadstone doesn't budge), or force=True.")
        elif k == "menu" and snap.state.menu is not None and "of what?" in (snap.state.prompt or "") \
                and unit[:1].isalpha():
            hit = [i.text for i in snap.state.menu.selectable()
                   if i.letter == unit[:1].decode() and self.COCKATRICE_CORPSE.search(i.text)]
            if hit and not self.gloves:
                raise PermissionError(f"refusing to pick up {hit[0]!r} (instant stoning bare-handed). "
                                      + self._gloves_hint())
        elif k == "getlin" and "For what do you wish" in (snap.state.prompt or ""):
            text = unit.rstrip(b"\r\n").strip()
            if unit[:1] == b"\x1b" or not text:
                raise PermissionError(
                    "refusing Esc/an empty answer at the WISH prompt: NetHack turns an empty wish into a RANDOM "
                    "object (objnam.c readobjnam). Type the wish from PLAYBOOK §E and <CR>, e.g. "
                    "'blessed +2 gray dragon scale mail<CR>'. force=True overrides.")
            if text.startswith(b"#") or len(text) < 4:
                raise PermissionError(
                    f"refusing {text.decode(errors='replace')!r} at the WISH prompt: it looks like a command typed "
                    "by a script, not a wish. Answer with the wish text + <CR>. force=True overrides.")
        elif k in ("getlin", "object") and "genocide" in (snap.state.prompt or "").lower():
            why = _genocide_danger(snap.state.prompt, unit.decode(errors="replace"))
            if why:
                raise PermissionError(why + " force=True overrides.")
        elif k in ("yn", "getlin") and unit[:1] in (b"y", b"Y") and "Really attack" in (snap.state.prompt or ""):
            # NetHack only asks this about peaceful monsters
            raise PermissionError(
                "refusing to confirm 'Really attack ...?': the target is PEACEFUL. Killing peacefuls costs "
                "alignment and Luck, angers your god, and in Minetown the Watch; a shopkeeper or priest "
                "will kill you. Answer no (<Esc>). force=True overrides.")
        elif k == "yn" and unit[:1] in (b"y", b"Y"):
            m = self._CORPSE_Q.search(snap.state.prompt or "")
            if m:
                try:
                    from .data.corpses import corpse_verdict
                    from .danger import base_name
                    name = base_name(m.group(1))
                    turn = (self.last_status.turn if self.last_status is not None else None) or snap.status.turn
                    age = self.corpse_age(name, self.hero_pos, turn)
                    v = corpse_verdict(name, hero_race="dwarf", hero_role="Valkyrie", age_turns=age,
                                       has_poison_res=False)
                    verdict = getattr(v.verdict, "value", v.verdict)
                except Exception:
                    return
                if verdict == "NEVER":
                    raise PermissionError(f"refusing to eat the {name} corpse: " + "; ".join(v.reasons)
                                          + " — force=True overrides.")
                if verdict == "DEADLY":
                    when = ("you didn't see it die here (age unknown)" if age is None
                            else f"it died {age} turns ago")
                    raise PermissionError(
                        f"refusing to eat the {name} corpse: {when} — " + "; ".join(v.reasons)
                        + ". Eat corpses you killed in the last ~50 turns (lichens/lizards never rot), or a "
                        "food item. force=True if you know better.")

    def _next_unit(self, data: bytes, i: int, kind: str) -> int:
        """End index of the next input unit starting at data[i], given the
        state the game is in right now."""
        n = len(data)
        c = data[i]
        if kind in ("getlin", "extcmd", "count", "dgl"):
            j = data.find(b"\r", i)
            return n if j < 0 else j + 1
        if kind == "menu":
            return i + 1          # one key at a time: a pick-one menu closes on the letter itself
        if kind == "getpos":
            j = i
            while j < n and data[j] not in b".,;:\x1b":
                j += 1
            return min(n, j + 1)
        if kind == "command":
            if c == ord("#"):
                j = data.find(b"\r", i)
                return n if j < 0 else j + 1
            if 48 <= c <= 57:           # count prefix + command
                j = i
                while j < n and 48 <= data[j] <= 57:
                    j += 1
                return min(n, j + 1)
            if c in b"FmMgG" and i + 1 < n:   # prefixes that take a direction
                return i + 2
        return i + 1

    def step(self, keys: str | bytes, auto_more: bool = True, max_more: int = 60,
             multi: bool = False, secret: bool = False, force: bool = False) -> Snap:
        """Send keys; follow --More-- pages (collecting their text) until the
        game waits for real input. Returns the final snapshot, whose
        .messages lists every message shown during the step.

        Keys are sent one logical unit at a time (a command, a prompt answer,
        a line of text). If the game comes back to the command prompt while
        keys remain (i.e. a command finished earlier than the caller
        expected), or a [yn] prompt is open that the next key can't answer,
        the rest is NOT sent (snap.unsent / snap.stop_reason explain).
        multi=True allows several commands in one call (e.g. 'hhhh')."""
        with self.lock:
            data = keys if isinstance(keys, bytes) else parse_keys(keys)
            t0 = time.monotonic()
            self.n += 1
            messages: list[str] = []
            cur = self.last
            if cur is None or (self.term is not None and self.term.raw_size() != self._settled_raw):
                cur = self.capture()      # output arrived since we last looked: decide on the real screen
            kind = cur.state.kind
            if data in (b"y", b"Y", b"n", b"N") and kind in ("yn", "getlin") and _PARANOID.search(cur.state.prompt or ""):
                # paranoid_confirmation (our rc: quit attack wand-break eat pray Remove Were-change) makes these a
                # TEXT prompt "... (yes) [no]": a bare y/n is typed into it and leaves it open (p2 shift 32 #118-#129:
                # "Continue eating?" collected "nnnnnnnnn"). Type the word; the guards still see its 'y'.
                data = b"yes\r" if data in (b"y", b"Y") else b"no\r"
            if not force and data:
                if kind == "dead":
                    raise PermissionError("the game process has exited (terminal dead): nothing to send. "
                                          "Look at `nh screen`; reconnect/restart per the runbook.")
                if kind == "gameover" and any(b not in b"ynqYNQ \r\n\x1b" for b in data):
                    raise PermissionError("the game is over: only y/n/q, space, Enter or Esc answer the end-of-game "
                                          "questions. Never start a new game without the human's go-ahead. "
                                          "force=True to send other keys.")
                if kind == "dgl":
                    raise PermissionError("this is the server lobby (dgamelaunch), not the game: a key here can "
                                          "start a game, enter a tournament or change settings. Use the "
                                          "tactics.server helpers, or force=True after reading the screen.")
            i = 0
            snap = cur
            unsent = b""
            stop_reason = ""
            sent_any = False
            answered: list[str] = []     # prompts answered in this step (their text can linger on row 0)
            if "Destroy old game?" in (cur.state.prompt or "") and data[:1] in (b"y", b"Y"):
                raise PermissionError("refusing to answer 'y' to 'Destroy old game?' -- that erases the "
                                      "game in progress. Answer 'n' and investigate.")
            if cur.state.kind == "dgl" and "STALE-PROCESS" in (cur.state.prompt or ""):
                raise PermissionError("stale-process countdown on screen: any key aborts the recovery. "
                                      "Wait ~20s (use `nh screen` to watch), then continue.")
            while i < len(data):
                if sent_any:
                    if kind == "command" and not multi:
                        unsent = data[i:]
                        stop_reason = "the game returned to the command prompt before these keys were sent"
                        break
                    if kind == "yn":
                        allowed = set(snap.state.choices.replace(" ", "")) | {"\x1b", "\r"}
                        if chr(data[i]) not in allowed and "yes" not in snap.state.choices:
                            unsent = data[i:]
                            stop_reason = f"a [yn] prompt is open ({snap.state.prompt!r}) and {chr(data[i])!r} doesn't answer it"
                            break
                    if kind in ("gameover", "dead"):
                        unsent = data[i:]
                        stop_reason = f"state is {kind}"
                        break
                j = self._next_unit(data, i, kind)
                unit = data[i:j]
                try:
                    self._guard(snap, unit, force)
                except PermissionError as e:
                    if not sent_any:
                        raise
                    unsent = data[i:]
                    stop_reason = str(e)
                    break
                i = j
                if snap.state.kind in ("yn", "getlin", "object", "direction", "count") and snap.state.prompt:
                    answered.append(snap.state.prompt.strip()[:40])
                menu_before = _menu_sig(snap) if snap.state.kind == "menu" else None
                snap = self.send_bytes(unit)
                sent_any = True
                pages = 0
                while auto_more and (snap.state.kind in ("more", "text") or _death_page(snap)) and pages < max_more:
                    txt = snap.state.more_text
                    if snap.state.kind == "more":
                        messages.extend(_split_top(txt))
                    elif txt:
                        messages.append(txt)
                    snap = self.send_bytes(snap.state.dismiss.encode())
                    pages += 1
                    if snap.state.kind in ("getpos", "unknown") and _detect_browse(messages[-3:],
                                                                                    snap.screen.row(0)):
                        # detect.c do_vicinity_map(): clairvoyance opens a map-browse cursor by itself
                        # between turns; leave it (Esc, no game time) — the next keys would move that
                        # cursor instead of playing (QA round 7)
                        snap = self.send_bytes(b"\x1b")
                if snap.state.kind == "getpos" and _detect_browse([snap.screen.row(0)], snap.screen.row(0)):
                    # detect.c browse_map(): object/monster/gold/food/trap detection (potion, scroll, spell,
                    # crystal ball) opens the same browse cursor with its message on the same line (p1 shift
                    # 31: "You detect the presence of objects. (For instructions type a '?')"). The detected
                    # things stay on the map; leave the browse (Esc, no game time).
                    messages.extend(m for m in _split_top(snap.screen.row(0)) if not m.startswith("(For instr"))
                    snap = self.send_bytes(b"\x1b")
                kind = snap.state.kind
                if menu_before is not None and unit.isalpha() and i < len(data) and not multi \
                        and _menu_sig(snap) != menu_before:
                    # the letter closed the menu (pick-one) or opened another one: the
                    # rest of the keys were meant for the old menu
                    unsent = data[i:]
                    stop_reason = (f"the menu closed on {unit.decode()!r} (a pick-one menu) — the remaining "
                                   "keys were not sent; look at the new state first")
                    break
            if snap.state.kind == "gameover" and snap.state.prompt:
                messages.append(snap.state.prompt)
            elif snap.state.kind == "command":
                top = snap.screen.row(0).strip()
                if top:
                    messages.extend(m for m in _split_top(top)
                                    if not any(a and m.startswith(a) for a in answered))
            snap.messages = messages
            snap.keys = "<secret>" if secret else describe_bytes(data[: len(data) - len(unsent)])
            snap.unsent = describe_bytes(unsent)
            snap.stop_reason = stop_reason
            snap.elapsed = time.monotonic() - t0
            snap.n = self.n
            if snap.hero is not None:
                prev_pos = self.hero_pos        # (before this step: a prompt's snapshot shows no hero)
                self.hero_pos = snap.hero
                if snap.status.ok:
                    self.visited.setdefault(self.level_key(snap.status), set()).add(snap.hero)
                    moved = cur.status.ok and cur.status.ldesc != snap.status.ldesc
                    old_key = self.level_key(cur.status) if cur.status.ok else None
                    if moved:
                        # the ^O name belongs to the level we left; until the tracker names the new
                        # one, file things under its provisional ldesc (main-dungeon and Mines/Sokoban
                        # levels share "Dlvl:N", so a stale name would mix their memories)
                        self.level_name = None
                        self.level_name_ldesc = None
                        self._arrival_prune = snap.status.ldesc
                    self._note_traps(snap, messages, moved_level=moved)
                    self._remember_terrain(snap, messages)
                    self._remember_here(snap, messages, prev_hero=cur.hero if cur is not None else None)
                    self._note_engraving_wiped(cur, snap, messages)
                    self._note_special_room(snap, messages, prev_hero=cur.hero if cur is not None else None)
                    self._note_shop(snap, messages, prev_hero=cur.hero if cur is not None and not moved else None)
                    self._validate_shops(snap)
                    if (cur.state.kind == "direction" or b"z" in data[:2]) and data[-1:] == b">":
                        # zapped/applied downward: a wand of teleportation/cancellation/make invisible
                        # moves or erases the engraving here without a word (zap.c)
                        self.engr_seen.get(self.level_key(snap.status), {}).pop(snap.hero, None)
                    if any(m.startswith("You are carrying too much to get through") for m in messages):
                        self.no_squeeze = True     # hack.c test_move(): inventory weight over 600
                    elif len(data) == 1 and data[0] in self._MOVE and cur.hero is not None and snap.hero is not None \
                            and abs(snap.hero[0] - cur.hero[0]) == 1 and abs(snap.hero[1] - cur.hero[1]) == 1 \
                            and _squeeze_rock(cur.screen, snap.hero[0], cur.hero[1]) \
                            and _squeeze_rock(cur.screen, cur.hero[0], snap.hero[1]):
                        self.no_squeeze = False    # a squeeze went through: light enough again
                    if len(data) == 1 and data[0] in self._MOVE and cur.hero is not None and snap.hero == cur.hero \
                            and any(m in ("It's solid stone.", "It's a wall.") for m in messages):
                        dx, dy = self._MOVE[data[0]]
                        self.solid.setdefault(self.level_key(snap.status), set()).add(
                            (cur.hero[0] + dx, cur.hero[1] + dy))
                    mv = data[-1] if data[:1] in (b"F", b"m") and len(data) == 2 else data[0] if len(data) == 1 else None
                    if mv in self._MOVE and cur.hero is not None and snap.hero == cur.hero:
                        # hack.c test_move(): a door the harness never saw (a monster or a pile on it) —
                        # remember it, so routes stop trying the diagonal step
                        dx, dy = self._MOVE[mv]
                        door = (cur.hero if any(m.startswith("You can't move diagonally out of an intact doorway")
                                                for m in messages) else
                                (cur.hero[0] + dx, cur.hero[1] + dy)
                                if any(m.startswith("You can't move diagonally into an intact doorway")
                                       for m in messages) else None)
                        if door is not None:
                            self.terrain_seen.setdefault(self.level_key(snap.status), {})[door] = "D"
                    if mv in self._MOVE and cur.hero is not None and snap.status.ok \
                            and any(re.match(r"^You (?:kill|destroy) it[.!]", m) for m in messages):
                        # an unseen monster killed: its corpse (if any) lies on the square you hit — date it,
                        # or the corpse guard can't tell it's fresh (corpse_age() matches any corpse there)
                        dx, dy = self._MOVE[mv]
                        self.record_kill("it", (cur.hero[0] + dx, cur.hero[1] + dy), snap.status.turn)
                    if mv in self._MOVE and cur.hero is not None and snap.hero == cur.hero and snap.status.ok:
                        # a melee kill: the corpse lies on the square you hit. The monster tracker files kills by
                        # its records, which can swap between two of a kind (p3 shift 20 #257: the fire giant
                        # killed at (46,13) was filed at the other giant's (45,12); the eat guard then called
                        # the fresh corpse "age unknown — DEADLY")
                        from .danger import base_name
                        named = [mm.group(1) for mm in (self._MELEE_KILL.match(m) for m in messages) if mm]
                        if len(named) == 1 and named[0] not in ("it", "them"):
                            dx, dy = self._MOVE[mv]
                            snap.melee_kill = (base_name(named[0]), (cur.hero[0] + dx, cur.hero[1] + dy))
                    self._note_wield(messages, snap.status.turn)
                    self._note_wand_zaps(snap, messages, cur)
                    self._note_trice_wielders(snap, messages)
                    self._note_held(cur, snap, messages)
                    self._note_monster_hole(cur, snap, messages)
                    self._note_used_up(cur, data)
                    self._note_intrinsics(messages)
                    self._note_theft(messages, snap.status.turn)
                    self._note_forgetting(snap, messages)
                    self._note_quest(messages)
                    self._note_arrival(cur, snap, data, messages, old_key, moved)
                    if moved:
                        self._note_departure(cur, snap, data, old_key)
                    self._note_pet_stays(cur, snap, messages, moved)
                    if moved:
                        self._note_fall(cur, messages, old_key, data, prev_pos=prev_pos)
            if (snap.hero is None or not snap.status.ok) and messages:
                # a prompt holds the cursor: the notes that only read messages still run (applying a pick-axe
                # prints "You now wield ..." together with the dig-direction prompt — p3 shift 17 #196: the
                # pick-axe warning never showed, and fight() bashed a long worm with it)
                self._note_wield(messages, snap.status.turn if snap.status.ok else None)
                self._note_intrinsics(messages)
                self._note_theft(messages, snap.status.turn if snap.status.ok else None)
                self._note_quest(messages)
            if snap.hero is not None:
                snap.engulfed = _engulfed(snap.screen, snap.hero)
            elif snap.state.kind == "getpos" and snap.status.ok:
                self._remember_portals(snap)       # a ^F / crystal-ball view on the Planes of Air/Water
            self._annotate(snap)
            if self.tracker is not None and snap.state.kind == "command":
                try:
                    snap.monsters = self.tracker.update(snap)
                    snap.gone = self._recently_gone(snap)
                except Exception as e:  # noqa: BLE001
                    self.log_event({"ev": "tracker_error", "err": repr(e)})
            elif snap.state.kind in ("yn", "direction", "object", "getlin", "count", "getpos"):
                # a prompt takes no time: the last labels still apply (a re-captured `cur`
                # has none, so fall back to the last labelled snapshot)
                prev = cur.monsters if cur is not None and cur.monsters else \
                    (self.last.monsters if self.last is not None else [])
                if prev:
                    snap.monsters = prev
            self._note_pet(snap, messages)
            if snap.status.ok:
                snap.mimic_mem = dict(self.mimics.get(self.level_key(snap.status), {}))
            for m in messages:
                self.history.append((snap.status.turn, m))
            if len(self.history) > self.max_history:
                del self.history[: len(self.history) - self.max_history]
            self.last = snap
            self._log(snap)
            key0 = self.level_key(snap.status) if snap.status.ok else None
            # (taken before the callbacks: the tracker's ^O runs nested steps of its own)
            chk, self._arrival_check = self._arrival_check, None
            for cb in list(self.on_step):
                try:
                    cb(snap)
                except Exception:
                    pass
            pruned = False
            if self._arrival_prune is not None and snap.status.ok and snap.status.ldesc == self._arrival_prune \
                    and snap.state.kind == "command" and snap.hero is not None \
                    and (self.level_name_ldesc == snap.status.ldesc or getattr(self, "memory", None) is None):
                # the first settled map of a level just entered, under its ^O name (the old memory merged
                # in): drop what the game's own map contradicts (_prune_features)
                self._arrival_prune = None
                key1 = self.level_key(snap.status)
                pruned = self._prune_features(snap, key1, arrival=True)
                if snap.under is None and self.terrain_seen.get(key1, {}).get(snap.hero):
                    snap.under = self.terrain_seen[key1][snap.hero]
            if key0 is not None and (self.level_key(snap.status) != key0 or pruned):
                self.reannotate(snap)
            if chk is not None and chk["n"] == snap.n and snap.state.kind == "command" and snap.hero == chk["hero"]:
                self._verify_arrival(snap, chk)
            return snap

    # Messages meaning the hero is standing on a trap *now* (teleporters, trap
    # doors, holes and portals move you away, so they're not listed; their '^'
    # is picked up from the map or the per-level #terrain scan instead).
    _TRAP_MSG = re.compile(
        r"(^There is an? .*\b(trap|pit|web)\b.* here\.|^You escape an? |An arrow shoots out at you|"
        r"A little dart shoots out at you|bear trap closes on your|your magical energy drain away|"
        r"^You (fall|step|tumble|jump|land) into an? pit|on a set of sharp iron spikes|A board beneath you|"
        r"loose board below you|crease in the linoleum|spider web!|A cloud of gas puts you to sleep|"
        r"You are enveloped in a cloud of gas|A gush of water hits (?:you|your)\b|"
        # trap.c dofiretrap(): yours is "A tower of flame erupts from the floor!"; a monster's has
        # "... under <it>!" and an invisible one's "You see a tower of flame erupt ..." (p1 shift 27)
        r"^A tower of flame (?:erupts|bursts) from (?!.*\bunder\b)|momentarily lethargic|"
        r"momentarily blinded by a flash of light|You trigger a rolling boulder trap|triggered an? land mine|"
        # trap.c ROCKTRAP: the rocks it drops lie on the trap and hide its '^' (p3 shift 14)
        r"^A trap door in .+? opens(?: and .+ falls on your|, but nothing falls out)|"
        r"You (step onto|float over|fly over|feel) an? polymorph trap|^You (float|fly) over an? )")

    _TRAP_NAMES = [
        (re.compile(r"^There is an? (.*?\b(?:trap|pit|web|board|mine)\b.*?) here\."), None),
        (re.compile(r"An arrow shoots out at you"), "arrow trap"),
        (re.compile(r"A little dart shoots out at you"), "dart trap"),
        (re.compile(r"bear trap closes on your"), "bear trap"),
        (re.compile(r"your magical energy drain away"), "anti-magic field"),
        (re.compile(r"on a set of sharp iron spikes"), "spiked pit"),
        (re.compile(r"^You (?:fall|step|tumble|jump|land) into an? pit"), "pit"),
        (re.compile(r"A board beneath you|loose board below you|crease in the linoleum"), "squeaky board"),
        (re.compile(r"spider web!"), "web"),
        (re.compile(r"A cloud of gas puts you to sleep|You are enveloped in a cloud of gas"), "sleeping gas trap"),
        (re.compile(r"A gush of water hits (?:you|your)\b"), "rust trap"),
        (re.compile(r"^A tower of flame (?:erupts|bursts) from (?!.*\bunder\b)"), "fire trap"),
        (re.compile(r"momentarily lethargic|momentarily blinded by a flash of light"), "magic trap"),
        (re.compile(r"You trigger a rolling boulder trap"), "rolling boulder trap"),
        (re.compile(r"triggered an? land mine"), "land mine"),
        (re.compile(r"^A trap door in .+? opens"), "falling rock trap"),
        (re.compile(r"an? polymorph trap"), "polymorph trap"),
    ]

    def _trap_name_from(self, messages: list[str]) -> str:
        """The trap type a trap message names ("There is a dart trap here.", "A little dart shoots out at you!"),
        or ''."""
        for m in messages:
            for rx, name in self._TRAP_NAMES:
                mm = rx.search(m)
                if mm:
                    return name or mm.group(1)
        return ""

    def _note_traps(self, snap: Snap, messages: list[str], moved_level: bool = False) -> None:
        """Remember trap squares per level: every displayed '^', and the hero's
        square when a trap message fires there (objects can hide a trap)."""
        if snap.hero is not None and _engulfed(snap.screen, snap.hero):
            return
        lv = self.level_key(snap.status)
        known = self.traps.setdefault(lv, set())
        # a seen trap stays drawn as '^' unless something stands/lies on it:
        # plain floor/corridor there means it's gone (disarmed, used up, filled) — or was never there (a stale
        # memory: p3 shift 18 #312); forget its name and the saved copy too, or the next load brings it back
        stale = [c for c in known if c != snap.hero and snap.screen.at(*c) in ".#" and c[1] > snap.state.msg_rows]
        if stale:
            known.difference_update(stale)
            fd = self.feature_desc.get(lv) or {}
            for c in stale:
                if re.search(r"trap|pit|hole|web|board|mine|teleporter|portal", fd.get(c, "")):
                    fd.pop(c, None)
            mem = getattr(self, "memory", None)
            if mem is not None and hasattr(mem, "drop_traps"):
                try:
                    mem.drop_traps(lv, stale)
                except Exception as e:  # noqa: BLE001
                    self.log_event({"ev": "drop_traps_error", "err": repr(e)})
        for y in range(1 + snap.state.msg_rows, 22):
            row = snap.screen.row(y)
            x = row.find("^")
            while x >= 0:
                known.add((x, y))
                x = row.find("^", x + 1)
        if not moved_level and snap.hero is not None and any(self._TRAP_MSG.search(m) for m in messages):
            known.add(snap.hero)
            # and its type (p1 shift 37 #722: trek() called a dart trap "a known trap of unknown type" although
            # "There is a dart trap here." had been said on it twice)
            name = self._trap_name_from(messages)
            if name:
                self.feature_desc.setdefault(lv, {})[snap.hero] = name
        elif not moved_level and snap.hero in known and snap.status.ok \
                and not {"Lev", "Fly"} & set(snap.status.conditions) \
                and re.search(r"\b(?:hole|trap door)\b", (self.feature_desc.get(lv) or {}).get(snap.hero, "")):
            # standing on a remembered hole/trap door without falling: there is none (p1 shift 37 #633: a stale
            # DL23 hole at (6,16) blocked steps; step_onto() walked onto plain floor)
            known.discard(snap.hero)
            self.feature_desc[lv].pop(snap.hero, None)
            mem = getattr(self, "memory", None)
            if mem is not None and hasattr(mem, "drop_traps"):
                try:
                    mem.drop_traps(lv, [snap.hero])
                except Exception as e:  # noqa: BLE001
                    self.log_event({"ev": "drop_traps_error", "err": repr(e)})
        # mklev.c/trap.c never put a trap on stairs, a ladder, an altar, a fountain or a throne (p1 shift 36: the
        # Castle's up stairs sat in the trap memory and trek() refused them)
        known.difference_update(c for c, v in self.terrain_seen.get(lv, {}).items() if v in "<>{_\\")

    def farlook(self, x: int, y: int) -> str:
        """Describe screen cell (x, y) via ';' without disturbing self.last.
        Takes no game time. Only valid in command state."""
        with self.lock:
            saved = self.last
            try:
                s = self.send_bytes(b";")
                if s.state.kind != "getpos":
                    if s.state.kind != "command":
                        self.send_bytes(b"\x1b")
                    return ""
                for _ in range(4):
                    cx, cy = s.screen.cursor
                    if (cx, cy) == (x, y):
                        break
                    s = self.send_bytes(_cursor_keys(cx, cy, x, y).encode())
                if s.screen.cursor != (x, y):
                    self.send_bytes(b"\x1b")
                    return ""
                s = self.send_bytes(b".")
                texts = []
                n = 0
                while s.state.kind in ("more", "text") and n < 10:
                    texts.append(s.state.more_text)
                    s = self.send_bytes(b"\r")
                    n += 1
                if s.state.kind == "command":
                    top = s.screen.row(0).strip()
                    if top:
                        texts.append(top)
                else:
                    self.send_bytes(b"\x1b")
                desc = " ".join(t for t in texts if t).strip()
                self.log_event({"ev": "farlook", "ts": round(time.time(), 3), "x": x, "y": y, "desc": desc})
                return desc
            finally:
                self.last = saved

    def terrain_traps(self) -> set | None:
        """The trap squares of terrain_scan() (or None)."""
        r = self.terrain_scan()
        return None if r is None else r["traps"]

    def rescan_terrain(self) -> dict | None:
        """terrain_scan() now, merged into this level's trap and feature
        memory (no game time). Returns the scan or None."""
        cur = self.last if self.last is not None else self.look()
        if not cur.status.ok or cur.state.kind != "command" \
                or {"Hallu", "Conf", "Stun"} & set(cur.status.conditions):
            return None
        r = self.terrain_scan()
        if r is not None:
            key = self.level_key(cur.status)
            self.traps.setdefault(key, set()).update(r["traps"])
            self.merge_terrain(key, r, cur.hero)
        return r

    def merge_terrain(self, key: str, found: dict, hero=None) -> None:
        """A #terrain scan into the level's feature memory: new features, and stairs remembered where the
        game's own map now shows plain floor dropped (p3 shift 11: a hole landing recorded as '<')."""
        mem = self.terrain_seen.setdefault(key, {})
        mem.update(found.get("features") or {})
        plain = found.get("plain") or set()
        for c in [c for c, v in mem.items() if v in "<>" and c in plain and c != hero]:
            del mem[c]
            self.stair_links.get(key, {}).pop(c, None)
            self.log_event({"ev": "stale_stairs_dropped", "level": key, "cell": list(c)})

    def terrain_scan(self) -> dict | None:
        """What the hero knows of this level's terrain (and doors), from NetHack's own
        memory: #terrain -> "known map without monsters and objects" shows
        remembered traps even under objects (webs as '"'), and the stairs,
        altars, fountains and thrones under objects too (the game keeps the
        last seen terrain type of every mapped square). No game time.
        Returns {"traps": set of squares, "features": {(x, y): glyph}}, or
        None if the view couldn't be read (e.g. hallucinating/confused:
        "You are too disoriented for this.")."""
        with self.lock:
            saved = self.last
            try:
                s = self.send_bytes(b"#terrain\r")
                if s.state.kind != "menu" or not s.state.menu:
                    self._leave_getpos(s)
                    return None
                letter = None
                for it in s.state.menu.selectable():
                    if "without monsters and objects" in it.text:
                        letter = it.letter
                if letter is None:
                    self.send_bytes(b"\x1b")
                    return None
                s = self.send_bytes(letter.encode())
                for _ in range(3):
                    if s.state.kind not in ("more", "text"):
                        break
                    s = self.send_bytes(s.state.dismiss.encode())
                found = None
                browsing = "Showing known terrain" in s.screen.row(0) or s.state.kind == "getpos"
                if browsing:
                    from .mapscan import _door_like
                    found = {"traps": set(), "features": {}, "plain": set()}
                    for y in range(MAP_TOP + 1, MAP_BOTTOM + 1):
                        row = s.screen.row(y)
                        for x, ch in enumerate(row):
                            if ch in ".#" and s.screen.color_at(x, y) in (7, 8, 15):
                                found["plain"].add((x, y))          # plain floor/corridor: no stairs here
                            if ch == "^" or ch == '"':
                                found["traps"].add((x, y))
                            elif ch in self.FEATURE_CHARS and feature_at(s.screen, x, y):
                                found["features"][(x, y)] = ch
                            elif s.screen.color_at(x, y) == 3 and (ch in "|-" or (ch == "+" and _door_like(s.screen, x, y))):
                                found["features"][(x, y)] = "D"     # a door, even one under a pile now
                self._leave_getpos(s, in_getpos=browsing)
                self.log_event({"ev": "terrain_traps", "ts": round(time.time(), 3),
                                "traps": sorted(found["traps"]) if found is not None else None,
                                "features": sorted((x, y, c) for (x, y), c in found["features"].items())
                                if found is not None else None})
                return found
            finally:
                self.last = saved

    def describe_cells(self, cells: list[tuple[int, int]]) -> dict:
        """Describe several map cells in one ';' session: turn on getpos
        autodescribe ('#'), move the cursor to each cell and read NetHack's
        own description off the top line ("peaceful dwarf", "jackal"), then
        turn autodescribe off again and leave with ESC. No game time. Costs
        about one keystroke per cell instead of ~4 for separate farlooks.
        Returns {(x, y): raw description}; cells it couldn't read are
        missing. A single cell uses farlook() (cheaper for one)."""
        cells = list(dict.fromkeys(cells))
        if len(cells) <= 1:
            return {c: self.farlook(*c) for c in cells}
        out: dict = {}
        with self.lock:
            saved = self.last
            try:
                s = self.send_bytes(b";")
                if s.state.kind != "getpos":
                    # (p3 shift 19 #419: a Castle scan came back with nothing and no trace of why)
                    self.log_event({"ev": "describe_short", "ts": round(time.time(), 3), "n": len(cells),
                                    "why": f"';' gave {s.state.kind}", "top": s.screen.row(0).strip()[:100]})
                    if s.state.kind != "command":
                        self.send_bytes(b"\x1b")
                    return out
                on = False
                for _ in range(2):
                    s = self.send_bytes(b"#")
                    top = s.screen.row(0)
                    if "Automatic description" not in top:
                        break
                    if " is on" in top:
                        on = True
                        break
                if not on:
                    self.log_event({"ev": "describe_short", "ts": round(time.time(), 3), "n": len(cells),
                                    "why": "autodescribe toggle", "top": s.screen.row(0).strip()[:100]})
                    self._leave_getpos(s, in_getpos=True)
                    return {c: self.farlook(*c) for c in cells}
                for (x, y) in cells:
                    for _ in range(3):
                        cx, cy = s.screen.cursor
                        if (cx, cy) == (x, y):
                            break
                        s = self.send_bytes(_cursor_keys(cx, cy, x, y).encode())
                    if s.screen.cursor == (x, y) and s.state.kind == "getpos":
                        out[(x, y)] = s.screen.row(0).strip()
                    elif s.state.kind != "getpos":
                        self.log_event({"ev": "describe_short", "ts": round(time.time(), 3), "n": len(cells),
                                        "done": len(out), "why": f"left getpos ({s.state.kind}) at {(x, y)}",
                                        "top": s.screen.row(0).strip()[:100]})
                        break
                # autodescribe off again (prints its message plus the goal
                # prompt, usually with a --More-- between them), then leave
                if s.state.kind == "getpos":
                    s = self.send_bytes(b"#")
                    for _ in range(3):
                        if s.state.kind not in ("more", "text"):
                            break
                        s = self.send_bytes(s.state.dismiss.encode())
                    if "is on" in s.screen.row(0):   # we toggled the wrong way: once more
                        s = self.send_bytes(b"#")
                self._leave_getpos(s, in_getpos=True)
                self.log_event({"ev": "describe", "ts": round(time.time(), 3),
                                "cells": {f"{x},{y}": d for (x, y), d in out.items()}})
                return out
            finally:
                self.last = saved

    def _leave_getpos(self, s: Snap, in_getpos: bool = False) -> Snap:
        """Back to the command prompt from a position prompt (or a --More--
        on the way out). in_getpos=True: we know a position prompt is open,
        so send ESC even if the screen reads like the command state."""
        for i in range(4):
            if in_getpos and i == 0 and s.state.kind not in ("more", "text"):
                s = self.send_bytes(b"\x1b")
                continue
            if s.state.kind == "command" and not self.getpos_active and self._plausible(s):
                break
            if s.state.kind in ("more", "text"):
                s = self.send_bytes(s.state.dismiss.encode())
            else:
                s = self.send_bytes(b"\x1b")
        return s

    def _annotate(self, snap: Snap) -> None:
        """Harness memory the obs shows with a snapshot."""
        self._promote_weapon(snap.status.turn if snap.status.ok else None)
        snap.wield_note = self.wield_note()
        snap.shop = self.shop_at(snap.hero, snap.status) if snap.status.ok else ""
        snap.last_pos = snap.hero or self.hero_pos
        key = self.level_key(snap.status) if snap.status.ok else None
        snap.feature_desc = self.feature_desc.setdefault(key, {}) if key is not None else {}
        snap.feature_mem = dict(self.terrain_seen.get(key, {})) if key is not None else {}
        snap.theft_note = self.theft_note(snap.status.turn if snap.status.ok else None)
        snap.charm_note = self.charm_note(snap.status.turn if snap.status.ok else None)
        snap.pet_note = self.pet_left_note(snap)
        snap.rogue = key is not None and "rogue" in self.level_flags.get(key, ())
        snap.medusa_risk = self._medusa_risk(snap, key)
        bags = getattr(self, "bags", None) or []
        gold = (snap.status.gold or 0) if snap.status.ok else 0
        lep = False
        if gold >= 100 and self.tracker is not None:
            # a hostile leprechaun seen on this level lately (the tracker's memory is per level)
            turn = snap.status.turn or 0
            lep = any("leprechaun" in (r.get("desc") or "")
                      and not (r.get("desc") or "").startswith(("tame ", "peaceful "))
                      and turn - r.get("turn", 0) <= 500
                      for r in (getattr(self.tracker, "recent", None) or {}).values())
        snap.burn_note = self.burn_note_for(snap)
        if bags and gold >= 200:
            snap.gold_note = (f"${gold} loose in your purse — a leprechaun takes it all: bag_put('{bags[0]}', '$')"
                              + (" — and a LEPRECHAUN is on this level" if lep else ""))
        elif lep:
            snap.gold_note = (f"${gold} in your purse and a LEPRECHAUN on this level: its hit takes ALL of it and it "
                              "teleports away — drop the gold somewhere safe first (d$), or kill it before it "
                              "reaches you")
        else:
            snap.gold_note = ""
        snap.flags = set(self.level_flags.get(key, ())) if key is not None else set()
        snap.floor_mem = (self.floor_seen.get(key, set()) | self.visited.get(key, set())) if snap.rogue else set()
        solid = self.solid.get(key) if key is not None else None
        if solid:
            for c in [c for c in solid if c == snap.hero or snap.screen.at(*c) in ".#"]:
                solid.discard(c)            # dug out since (or you stand there)
        snap.solid_mem = set(solid or ())
        snap.niche_mem = dict(self.niches.get(key, {})) if key is not None else {}
        snap.no_squeeze = bool(getattr(self, "no_squeeze", False))
        # hack.c cant_squeeze_thru(): in Sokoban the hero NEVER squeezes diagonally between boulders/rock (p4 shift 4
        # #550: hunt() planned one between two boulders)
        snap.sokoban = bool(key and str(key).startswith("Sokoban"))
        snap.wand_users = dict(self.wand_users.get(key, {})) if key is not None else {}
        tw = self.trice_wielders.get(key, {}) if key is not None else {}
        now = snap.status.turn if snap.status.ok else None
        snap.trice_wielders = {n: t for n, t in tw.items() if now is None or now - t <= self.TRICE_WIELD_TURNS}
        # a cockatrice you killed here in the last ~260 turns whose square still shows a '%' (mkobj.c: the corpse
        # rots away ~250 turns after death): a gloved monster can pick it up and hit you with it (p2 shift 38 #560)
        fresh = sorted({tuple(c) for n, c, t in self.kills.get(key, []) if n in ("cockatrice", "chickatrice")
                        and now is not None and 0 <= now - t <= 260 and snap.screen.at(*c) == "%"
                        and tuple(c) != snap.hero}) if key is not None else []
        snap.trice_note = (f"cockatrice corpse{'s' if len(fresh) > 1 else ''} at {', '.join(map(str, fresh[:3]))} "
                           "(your kill): a gloved monster can pick it up and hit you with it — every hit stones you. "
                           "Take it (gloves on: pickup) or keep monsters away from it" if fresh else "")
        snap.held_trap = getattr(self, "held_trap", "") or ""
        snap.room_mem = dict(self.special_rooms.get(key, {})) if key is not None else {}

    # not a staircase trip: a hole you dug ('>' answered the dig direction), a trap door, a level teleport,
    # a fall, or the Amulet's mysterious force (1 in 4 climbs in Gehennom: you land somewhere on a DEEPER level)
    _NOT_STAIRS = re.compile(r"\bfall|\bhole\b|trap door|\bdig\b|dug|teleport|You float down|mysterious force", re.I)

    # weapon.c/mhitu.c: a (gloved) monster that picked up a cockatrice corpse wields it — "The priestess of Moloch
    # wields a cockatrice corpse!", "... swings her cockatrice corpse", "... hits you with the cockatrice corpse."
    # Each hit starts STONING you (p2 shift 38 #560-#577: twice in 5 turns, both lizards used). The corpse rots
    # away within ~250 turns of the cockatrice's death, in its hands too (timeout.c rot_corpse)
    _TRICE_WIELD = re.compile(r"^(?:The |An? )?(?P<who>.+?) (?:wields (?:an? |the |\d+ )?(?:partly eaten )?|swings "
                              r"(?:his|her|its) |hits you with (?:the|an?) )(?:cockatrice|chickatrice) corpses?\b")
    TRICE_WIELD_TURNS = 300

    def _note_trice_wielders(self, snap: Snap, messages: list) -> None:
        if not snap.status.ok:
            return
        from .danger import base_name
        for m in messages:
            mm = self._TRICE_WIELD.match(m)
            if mm and not mm.group("who").startswith(("You", "you")):
                who = base_name(mm.group("who")) or mm.group("who")
                self.trice_wielders.setdefault(self.level_key(snap.status), {})[who] = snap.status.turn

    LEFT_BEHIND_TURNS = 3000

    def _note_departure(self, cur: Snap, snap: Snap, data: bytes, old_key) -> None:
        """Covetous monsters (the Wizard, liches, Vlad, quest nemeses, demon princes) seen on the level you just left
        stay there — a wounded one heals on the up stairs (wizard.c tactics() STRAT_HEAL) — unless it was next to you
        (dog.c levl_follower(): the Wizard always follows then). Filed per level; arriving on a level that holds one
        sets snap.left_note, which pauses (p1 shift 40 #414/#634: twice the Wizard stood by the arrival stairs; the
        second time he stole the Bell)."""
        from .danger import base_name, covetous
        if not old_key or not snap.status.ok or not cur.status.ok:
            return
        now, then = snap.status.turn, cur.status.turn or 0
        recs = list((getattr(self.tracker, "recent", None) or {}).values()) if self.tracker is not None else []
        recs += [dict(m, turn=then) for m in (cur.monsters or []) if m.get("desc")]
        seen: dict = {}
        for r in recs:
            d = r.get("desc") or ""
            if not d or d.startswith(("tame ", "peaceful ")) or r.get("statue"):
                continue
            name = base_name(d) or d
            t = r.get("turn") or 0
            if covetous(name) and then - t <= 300 and (name not in seen or t >= seen[name]["seen"]):
                seen[name] = {"x": r["x"], "y": r["y"], "seen": t, "left": now, "ldesc": cur.status.ldesc}
        store = self.left_behind.setdefault(old_key, {})
        for name, e in seen.items():
            if cur.hero is not None and e["seen"] >= then - 1 \
                    and max(abs(e["x"] - cur.hero[0]), abs(e["y"] - cur.hero[1])) <= 1:
                store.pop(name, None)            # next to you as you left: it came along
            else:
                store[name] = e
        if not store:
            self.left_behind.pop(old_key, None)
        if seen:
            self._save_left_behind()
        # arriving: the stairs' known destination, else any level filed under this status line (Dlvl:N)
        dest = (self.stair_links.get(old_key, {}).get(cur.hero) if cur.hero is not None else None)
        waiting = {}
        for key, ents in self.left_behind.items():
            if key == old_key:
                continue
            for name, e in ents.items():
                if (key == dest or e.get("ldesc") == snap.status.ldesc) and now is not None \
                        and now - (e.get("left") or 0) <= self.LEFT_BEHIND_TURNS:
                    waiting[name] = e
        pre = getattr(self, "left_prewarned", None) or {}
        if waiting and dest is not None and pre.get("dest") == dest and now is not None \
                and 0 <= now - (pre.get("turn") or 0) <= 5:
            waiting = {}                         # (go_up()/go_down() paused about it before the stairs)
        if waiting:
            snap.left_note = ("WAITING HERE: " + "; ".join(
                f"the {n} you left on this level at T:{e['left']} (last seen at ({e['x']},{e['y']}), T:{e['seen']})"
                for n, e in waiting.items())
                + " — covetous monsters stay where they were (a wounded one heals on the up stairs) and come straight "
                  "at you: full HP, blindfold for telepathy, fight from 6-8 squares off its stairs (covetous_ring()); "
                  "leaving at once is an option")

    def _save_left_behind(self) -> None:
        mem = getattr(self, "memory", None)
        st = getattr(mem, "state", None)
        if isinstance(st, dict):
            st["left_behind"] = {k: dict(v) for k, v in self.left_behind.items() if v}
            try:
                mem.save()
            except Exception:  # noqa: BLE001
                pass

    def _note_arrival(self, cur: Snap, snap: Snap, data: bytes, messages: list, old_key, moved: bool) -> None:
        """After '<'/'>' took you to another level: the staircase you arrived on is under you (the '@' hides
        it), and the two ends lead to each other (stair_links). With a monster next to you, checked by a look
        once the step is done (_verify_arrival)."""
        arrive = {b">": "<", b"<": ">"}.get(bytes(data[-1:])) if (moved and data) else None
        if not arrive:
            return
        stood = self.terrain_seen.get(old_key, {}).get(cur.hero) if old_key else None
        if any(self._NOT_STAIRS.search(m) for m in messages) or (stood is not None and stood != chr(data[-1])) \
                or cur.state.kind != "command":
            return
        if old_key and cur.hero in self.traps.get(old_key, ()):
            # '>' on a known hole/trap door plunges you through it (trap.c fall_through with TOOKPLUNGE says
            # NOTHING for a one-level drop): you land on a random square, not on stairs (p3 shift 11)
            return
        if any(self._HERE_OBJS.search(m) for m in messages) and not any(self._ON_STAIRS.search(m) for m in messages):
            return      # the arrival look listed what lies here without "There is a staircase ... here"
        if snap.under is None:
            self.terrain_seen.setdefault(self.level_key(snap.status), {})[snap.hero] = arrive
            snap.under = arrive
        if cur.hero is not None and old_key:
            new_key = self.level_key(snap.status)
            self.stair_links.setdefault(old_key, {})[cur.hero] = new_key
            self.stair_links.setdefault(new_key, {})[snap.hero] = old_key
        if any(snap.screen.at(snap.hero[0] + dx, snap.hero[1] + dy) in MONSTER_CHARS
               for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy):
            # a monster came along (or stood there): you may be NEXT TO the stairs
            self._arrival_check = {"n": snap.n, "hero": snap.hero, "ch": arrive, "old_key": old_key}

    _ON_STAIRS = re.compile(r"There is an? (?:staircase|ladder) (?:up|down) here")
    _ON_PORTAL = re.compile(r"There is a magic portal here")

    def _note_fall(self, cur: Snap, messages: list, old_key, data: bytes = b"", prev_pos=None) -> None:
        """trap.c fall_through(): "A trap door opens up under you!" / "There's a gaping hole under you!" — the
        trap is on the level you LEFT: remember it there (a known way down, and a square for routes to avoid) — in
        the harness memory too, as `nh info` shows it (p1 shift 31). On the square you stepped ONTO when the fall
        came with a move (p3 shift 18 #312, p1 shift 37 #633: the square you came from was filed as a hole, and
        the step guard then refused plain floor); on your own square for '>' / a dug hole; unknown (not filed)
        when a travel crossed it."""
        # dig.c digactualhole(): "You dig a hole through the floor." + "You fall through..." (a pick-axe or a
        # wand of digging zapped down) — your own hole, on the square you stood on (p3 shift 19: two dug holes
        # on D23/D24 were never filed)
        dug = any(m.startswith("You dig a hole through the ") for m in messages) \
            and any(m.startswith("You fall through") for m in messages)
        kind = ("trap door" if any(m.startswith("A trap door opens up under you") for m in messages) else
                "hole" if dug or any(m.startswith("There's a gaping hole under you") for m in messages) else None)
        here = cur.hero if cur.hero is not None else prev_pos    # (dig's '>' answers a prompt: no hero on it)
        if kind is None or not old_key or here is None:
            return
        data = bytes(data or b"")
        key = data[-1] if data[:1] in (b"m", b"F") and len(data) == 2 else data[0] if len(data) == 1 else None
        if key is not None and key in self._MOVE:
            dx, dy = self._MOVE[key]
            x, y = here[0] + dx, here[1] + dy
        elif not data or data[:1] in (b">", b"<", b"s", b"."):
            x, y = here                   # '>' into a hole you stand on, waiting on it, digging down
        else:
            return                        # a travel or a rush: the trap was somewhere on the way — not filed
        self.traps.setdefault(old_key, set()).add((x, y))
        self.feature_desc.setdefault(old_key, {})[(x, y)] = kind
        mem = getattr(self, "memory", None)
        lv = (getattr(mem, "state", None) or {}).get("levels", {}).get(old_key)
        if lv is not None:
            lst = lv.setdefault("features", {}).setdefault(kind, [])
            if [x, y] not in lst:
                lst.append([x, y])
            tr = lv.setdefault("traps", [])
            if [x, y] not in tr:
                tr.append([x, y])
                tr.sort()
            lv.setdefault("feature_desc", {})[f"{x},{y}"] = kind

    def _quiet_look(self) -> str:
        """':' (no game time) read straight off the screen, outside the step machinery (no history, no
        pauses); the next command clears the message line."""
        s = self.send_bytes(b":")
        texts = []
        for _ in range(6):
            if s.state.kind not in ("more", "text"):
                break
            if s.state.more_text:
                texts.append(s.state.more_text)
            s = self.send_bytes(s.state.dismiss.encode())
        if s.state.kind == "command":
            top = s.screen.row(0).strip()
            if top:
                texts.append(top)
        else:
            self.send_bytes(b"\x1b")
        return " ".join(texts)

    def _verify_arrival(self, snap: Snap, chk: dict) -> None:
        """do.c goto_level()/u_collide_m(): when a monster holds the arrival square (a pet or a follower
        that came along, or one standing there) NetHack puts you on a square NEXT TO the stairs half the
        time, and the monster stays on them. With a monster next to you after taking the stairs, look
        (':', no game time); if the stairs aren't under you, move their memory (and where they lead) to
        the square under that monster (#terrain decides when several monsters could be on them)."""
        try:
            text = self._quiet_look()
        except Exception as e:  # noqa: BLE001
            self.log_event({"ev": "arrival_look_error", "err": repr(e)})
            return
        finally:
            self.last = snap
        hero, ch = chk["hero"], chk["ch"]
        if (self._ON_STAIRS if ch in "<>" else self._ON_PORTAL).search(text):
            return
        key = self.level_key(snap.status)
        mem = self.terrain_seen.setdefault(key, {})
        if mem.get(hero) == ch:
            del mem[hero]
        links = self.stair_links.setdefault(key, {})
        dest = links.pop(hero, None) or chk.get("old_key")
        if snap.under == ch:
            snap.under = None
        cands = [(hero[0] + dx, hero[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                 if (dx or dy) and snap.screen.at(hero[0] + dx, hero[1] + dy) in MONSTER_CHARS]
        spot = cands[0] if len(cands) == 1 else None
        if spot is None:
            found = self.terrain_scan()
            self.last = snap
            if ch == "^":                           # (#terrain draws the portal as a trap '^')
                near = [c for c in (found or {}).get("traps") or () if max(abs(c[0] - hero[0]),
                                                                            abs(c[1] - hero[1])) == 1
                        and "portal" in (self.feature_desc.get(key, {}).get(c) or "portal")]
                spot = near[0] if len(near) == 1 else None
            else:
                spot = next((c for c, v in ((found or {}).get("features") or {}).items()
                             if v == ch and max(abs(c[0] - hero[0]), abs(c[1] - hero[1])) == 1), None)
        if spot is not None:
            mem[spot] = ch
            if dest:
                links[spot] = dest
        self.log_event({"ev": "arrival_next_to_stairs", "hero": list(hero), "stairs": list(spot) if spot else None,
                        "look": text[:200]})
        self._annotate(snap)

    def reannotate(self, snap: Snap) -> None:
        """The tracker named the level (^O) after `snap` was annotated — the arrival step on a new
        level, filed under its provisional ldesc until then: read that level's memory again (the Rogue
        level's symbols, Medusa, remembered features and traps) so the arrival obs is already right."""
        self._annotate(snap)
        if snap.rogue and snap.monsters:
            # ']' is armor on the Rogue level, not a mimic's "strange object" (random monsters there
            # are upper-case letters only: no mimics); a ':' looked at and found to be food is an object
            from .monitor import _monster_desc
            food = [m for m in snap.monsters if m["ch"] == ":" and m.get("desc") and not _monster_desc(m["desc"])]
            if food and self.tracker is not None and hasattr(self.tracker, "rogue_objects"):
                self.tracker.rogue_objects.update((snap.status.ldesc, m["x"], m["y"]) for m in food)
            snap.monsters = [m for m in snap.monsters if not (m["ch"] == "]" and m.get("mimic")) and m not in food]

    def _medusa_risk(self, snap: Snap, key) -> bool:
        """Probably Medusa's level (Dungeons of Doom, Dlvl 21+, water all around — or Medusa seen here)
        while you are neither blind nor known to wear reflection: her gaze stones you on sight."""
        if key is None or not snap.status.ok or snap.state.kind not in ("command", "getpos"):
            return False
        flags = self.level_flags.setdefault(key, set())
        if "medusa_dead" in flags:
            return False
        if key.startswith("The Dungeons of Doom /") and "medusa" not in flags:
            m = re.search(r"Level (\d+)$", key)
            if m and int(m.group(1)) >= 21:
                scr = snap.screen
                water = bridge = 0
                for y in range(MAP_TOP + snap.state.msg_rows, MAP_BOTTOM + 1):
                    row = scr.row(y)
                    for x, ch in enumerate(row):
                        if ch == "}" and scr.color_at(x, y) == 4:
                            water += 1
                        elif ch in "#." and scr.color_at(x, y) == 3:
                            bridge += 1            # a drawbridge: the Castle, not Medusa
                if bridge:
                    flags.add("castle")
                    flags.discard("medusa?")
                elif water >= 40 and "castle" not in flags:
                    flags.add("medusa?")
        if not flags & {"medusa", "medusa?"}:
            return False
        return "Blind" not in snap.status.conditions and not self.reflecting

    def look(self) -> Snap:
        """Capture without sending anything."""
        with self.lock:
            snap = self.capture()
            if self.last is not None:
                snap.messages = []
            if snap.hero is not None:
                self.hero_pos = snap.hero
                snap.engulfed = _engulfed(snap.screen, snap.hero)
                self._remember_terrain(snap, [])
            self._annotate(snap)
            if self.tracker is not None and snap.state.kind == "command":
                try:
                    snap.monsters = self.tracker.update(snap)
                except Exception as e:  # noqa: BLE001
                    self.log_event({"ev": "tracker_error", "err": repr(e)})
            if snap.status.ok:
                snap.mimic_mem = dict(self.mimics.get(self.level_key(snap.status), {}))
            self.last = snap
            return snap

    # ---- logging -----------------------------------------------------------
    def _log(self, snap: Snap) -> None:
        if not self.log_path:
            return
        rec = {
            "ev": "step", "n": snap.n, "ts": round(time.time(), 3), "keys": snap.keys,
            "kind": snap.state.kind, "prompt": snap.state.prompt if snap.state.kind != "command" else "",
            "messages": snap.messages, "status": snap.status.short() if snap.status.ok else None,
            "turn": snap.status.turn, "cursor": list(snap.screen.cursor),
            "elapsed": round(snap.elapsed, 3),
            "screen": snap.screen.text,
        }
        self.log_event(rec)

    def load_history(self, max_bytes: int = 8_000_000) -> int:
        """The recent messages from events.jsonl into self.history (a daemon restart left `bin/nh history` empty:
        p3 shift 16). Not the tracker's own ^O overview steps. Returns how many were loaded."""
        if not self.log_path or not Path(self.log_path).exists():
            return 0
        with open(self.log_path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - max_bytes))
            data = f.read()
        lines = data.split(b"\n")
        if size > max_bytes:
            lines = lines[1:]                   # (a partial first line)
        out = []
        for ln in lines:
            if not ln.startswith(b'{"ev": "step"'):
                continue
            try:
                rec = json.loads(ln)
            except ValueError:
                continue
            if rec.get("keys") == "<C-o>":
                continue
            out.extend((rec.get("turn"), m) for m in rec.get("messages") or [])
        self.history = out[-self.max_history:]
        return len(self.history)

    def log_event(self, rec: dict) -> None:
        if not self.log_path:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a") as f:
            f.write(json.dumps(rec) + "\n")
