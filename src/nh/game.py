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

    def hostiles(self, radius: int | None = None) -> list:
        """Monsters that are not tame/peaceful/statues, optionally within
        radius. Excludes what can't be judged: 'I' markers (unseen, maybe a
        peaceful) and anything seen while hallucinating."""
        out = []
        for m in self.monsters:
            d = m.get("desc", "")
            if m.get("statue") or m.get("pet") or d.startswith("tame ") or d.startswith("peaceful "):
                continue
            if m.get("unseen") or m.get("hallu"):
                continue
            if radius is not None and (m.get("dist") is None or m["dist"] > radius):
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


def _engulfed(scr: Screen, hero) -> bool:
    """The swallow display: a ring of / - \\ | around the hero (corners are
    the tell, as for explosions, but the centre is '@')."""
    if hero is None:
        return False
    x, y = hero
    want = ((-1, -1, "/"), (1, -1, "\\"), (-1, 1, "\\"), (1, 1, "/"))
    return sum(1 for dx, dy, ch in want if scr.at(x + dx, y + dy) == ch) >= 3


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
        self.tracker = None   # MonsterTracker, attached by the daemon
        self.visited: dict[str, set] = {}   # level (ldesc) -> hero positions seen in command state
        self.traps: dict[str, set] = {}     # level (ldesc) -> squares known to hold traps
        self.avoid: dict[str, set] = {}     # level (ldesc) -> squares the player asked to avoid
        self.terrain_seen: dict[str, dict] = {}   # level key -> {(x, y): feature char} (stairs, fountains...)
        self.here_seen: dict[str, dict] = {}      # level key -> {(x, y): last "You see here"/pile text}
        self.kills: dict[str, list] = {}          # level key -> [(name, (x, y), turn)]: corpse ages
        self.engr_seen: dict[str, dict] = {}      # level key -> {(x, y): engraving text last read there}
        self.wielded: str | None = None           # what inventory() last showed "(weapon in hand)"; None = unknown
        self.gloves: str | None = None            # worn gloves/gauntlets per inventory(); "" none; None = unknown
        self.wielded_class: str | None = None     # inventory() class header of the wielded item ("Weapons")
        self.shops: dict[str, list] = {}          # level key -> [[x1, y1, x2, y2, "Name's shop type"]] interiors
        self.locked_doors: dict[str, set] = {}    # level key -> doors found locked (travel walks around them)
        self.feature_desc: dict[str, dict] = {}   # level key -> {(x, y): "trap door" / "lawful altar"} (farlook)
        self.intrinsics: set = {"cold", "stealth"}   # Valkyrie start; more learned from messages (_note_intrinsics)
        self.stair_links: dict[str, dict] = {}    # level key -> {(x, y) of a staircase: key of the level it leads to}
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
        for d in (self.traps, self.avoid, self.visited, self.locked_doors):
            if old in d:
                d.setdefault(new, set()).update(d.pop(old))
        for d in (self.terrain_seen, self.here_seen, self.engr_seen, self.stair_links, self.feature_desc):
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
    # look_here(): "There is %s here." with dfeature_at() (invent.c) — "an opulent throne",
    # "an altar to Tyr (lawful)", "a high altar to ..." on Astral/Sanctum
    _HERE_FEATURE = re.compile(r"^There is an? (?:high )?(staircase up|staircase down|ladder up|ladder down|"
                               r"fountain|altar|opulent throne)\b.* here\.")
    _HERE_CH = {"staircase up": "<", "staircase down": ">", "ladder up": "<", "ladder down": ">",
                "fountain": "{", "altar": "_", "opulent throne": "\\"}

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
        for m in messages:
            mm = self._ENGR_READ.search(m)
            if mm:
                engr[snap.hero] = mm.group(1)
                read = True
            elif self._ENGR_GONE.search(m):
                engr.pop(snap.hero, None)
        if not read and prev_hero is not None and prev_hero != snap.hero \
                and "Blind" not in snap.status.conditions:
            # arriving on a square shows its engraving; none shown = none left (smudged away)
            engr.pop(snap.hero, None)

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

    def corpse_age(self, name: str, cell, turn: int | None):
        """Turns since the oldest recorded kill of `name` on `cell` of this level
        (a corpse lies where its monster died), or None if unknown."""
        if cell is None or turn is None:
            return None
        ages = [turn - t for n, c, t in self.kills.get(self.level_key(), []) if n == name and c == tuple(cell)]
        return max(ages) if ages else None

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
            if turn - r.get("turn", 0) <= 20 and d and not d.startswith(("tame ", "peaceful ")) \
                    and not r.get("statue") and note_for(d):
                out.append({"desc": d, "x": r["x"], "y": r["y"], "ago": turn - r.get("turn", 0)})
        return out[:4]

    _WIELD_NOW = re.compile(r"^You now wield (.+?)\.$")          # wield_tool(): #rub, apply a pick-axe
    _WIELD_INV = re.compile(r"^[a-zA-Z] - (.+?)\.?$")          # 'w'/'x' echo the inventory line

    def _note_wield(self, messages: list[str]) -> None:
        """Keep self.wielded current from the messages: "You now wield a
        blessed lamp." (#rub / applying a pick-axe wields the tool),
        "a - ... (weapon in hand)." ('w'), "You are empty handed."; anything
        else about wielding makes it unknown (re-checked by inventory())."""
        for m in messages:
            mm = self._WIELD_NOW.search(m)
            if mm:
                self.wielded, self.wielded_class = mm.group(1), None
                continue
            mm = self._WIELD_INV.search(m)
            if mm and WIELDED_RE.search(m):
                self.wielded, self.wielded_class = mm.group(1), None
                continue
            if re.search(r"^You are (?:now |already )?empty.handed", m):
                self.wielded, self.wielded_class = "", None
            elif re.search(r"wield|slips from your|welded|disarm|wrested|snatches|You are now empty", m):
                self.wielded, self.wielded_class = None, None     # re-check the weapon next time it matters
            if re.search(r"\b(?:gloves|gauntlets)\b", m):
                self.gloves = None      # put on / taken off / stolen / destroyed: re-check

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

    def wield_note(self) -> str:
        """A warning when you are known to wield something that isn't a
        weapon (a lamp after #rub, nothing at all), else ''."""
        w = self.wielded
        if w is None:
            return ""
        if w == "":
            return "you are EMPTY-HANDED (w + letter to wield your weapon)"
        if (self.wielded_class or "").startswith("Weapons"):
            return ""
        if not is_weapon_text(w):
            return f"you WIELD {w} — not a weapon (w + letter to wield your weapon again)"
        return ""

    # shk.c u_entered_shop(): "Velkommen, p2!  Welcome to Carignan's antique weapons outlet!"
    # ("Welcome again to ..." on later visits); printed on the first square inside the door
    _SHOP_WELCOME = re.compile(r"^[^!]+!\s+Welcome(?: again)? to (?P<name>[^!]+?(?:'s|s') [^!]+)!")
    _ROOM_EDGE = set("|-+# ")

    def _room_rect(self, snap: Snap, start) -> tuple | None:
        """The interior (x1, y1, x2, y2) of the lit room around `start`,
        scanning to the walls along its row and column."""
        x, y = start
        scr = snap.screen
        # on the shop door (in_rooms() counts it, so the welcome can come there): start one step inside
        if scr.at(x, y - 1) in "|-" and scr.at(x, y + 1) in "|-":       # a door in a left/right wall
            x += next((d for d in (1, -1) if scr.at(x + d, y) not in self._ROOM_EDGE), 0)
        elif scr.at(x - 1, y) in "|-" and scr.at(x + 1, y) in "|-":     # a door in a top/bottom wall
            y += next((d for d in (1, -1) if scr.at(x, y + d) not in self._ROOM_EDGE), 0)
        door = start if (x, y) != tuple(start) else None               # (the '@' there is part of the wall)

        def run(dx, dy):
            cx, cy = x, y
            for _ in range(80):
                nx, ny = cx + dx, cy + dy
                if not (0 <= nx < 80 and MAP_TOP < ny <= MAP_BOTTOM) or scr.at(nx, ny) in self._ROOM_EDGE \
                        or (nx, ny) == door:
                    return cx if dx else cy
                cx, cy = nx, ny
            return None
        x1, x2, y1, y2 = run(-1, 0), run(1, 0), run(0, -1), run(0, 1)
        if None in (x1, x2, y1, y2) or x2 - x1 > 40 or y2 - y1 > 15:
            return None
        return (x1, y1, x2, y2)

    def _note_shop(self, snap: Snap, messages: list[str]) -> None:
        if snap.hero is None or not snap.status.ok:
            return
        for m in messages:
            mm = self._SHOP_WELCOME.search(m)
            if not mm:
                continue
            rect = self._room_rect(snap, snap.hero)
            if rect is None:
                continue
            lst = self.shops.setdefault(self.level_key(snap.status), [])
            x1, y1, x2, y2 = rect
            lst[:] = [e for e in lst if e[2] < x1 or e[0] > x2 or e[3] < y1 or e[1] > y2]
            lst.append([x1, y1, x2, y2, mm.group("name")])

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
        feats = self.terrain_seen.setdefault(self.level_key(snap.status), {})
        for y in range(MAP_TOP + snap.state.msg_rows, MAP_BOTTOM + 1):
            row = snap.screen.row(y)
            for x, ch in enumerate(row):
                if ch in self.FEATURE_CHARS and feature_at(snap.screen, x, y):
                    feats[(x, y)] = ch
        for c in list(feats):
            if c != snap.hero and snap.screen.at(*c) in ".#" and c[1] > snap.state.msg_rows:
                del feats[c]           # e.g. a fountain that dried up
        if any("dries up" in m or "fountain disappears" in m for m in messages):
            feats.pop(snap.hero, None)
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
                if (tx, ty) in self.traps.get(self.level_key(snap.status), ()):
                    raise PermissionError(
                        f"refusing to step onto the known trap at {(tx, ty)} (NetHack doesn't ask). Go around "
                        "(travel() avoids traps), or force=True if you mean it (jumping into a hole/trap "
                        "door on purpose, entering a magic portal).")
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
            if snap.hero is not None and self.on_elbereth(snap):
                # throws/zaps/kicks are checked at their direction prompt (only hitting a monster counts)
                attack = unit[:1] == b"F" or unit.startswith(b"#force")
                if key in self._MOVE and unit[:1] != b"m":
                    dx, dy = self._MOVE[key]
                    tgt = (snap.hero[0] + dx, snap.hero[1] + dy)
                    attack = attack or any((m["x"], m["y"]) == tgt and not m.get("tame") and not m.get("pet")
                                           and not m.get("statue") for m in snap.monsters or [])
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
                        "with levitation/water walking you're sure of.")
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
                if self.COCKATRICE_CORPSE.search(txt) and "Things that" not in txt:
                    raise PermissionError(
                        "refusing to pick up here: the only object on this square is a cockatrice/chickatrice "
                        "corpse, and ',' takes it without a menu — touching it bare-handed is instant stoning. "
                        "force=True only if you wear gloves.")
                if self.GRAY_STONE.search(txt) and "Things that" not in txt:
                    raise PermissionError(
                        "refusing to pick up the gray stone: it may be a LOADSTONE (cursed ones can't be dropped; "
                        "500 weight). Step off and kick it first: a loadstone doesn't budge ('Thump!'), a "
                        "luckstone/touchstone/flint slides. force=True once you know.")
            if step in self._MOVE and snap.hero is not None and "Blind" in conds:
                dx, dy = self._MOVE[step]
                if self.COCKATRICE_CORPSE.search(self._here_text(snap, (snap.hero[0] + dx, snap.hero[1] + dy))):
                    raise PermissionError(
                        "refusing to step blind onto the square with the cockatrice corpse: while blind you feel "
                        "the objects you step on, and feeling it bare-handed is instant stoning. Wait until you "
                        "can see, go around, or force=True if you wear gloves.")
            if step in self._MOVE and snap.hero is not None and conds & {"Conf", "Stun"}:
                from .danger import base_name
                near = [m for m in snap.monsters or [] if m.get("dist") == 1 and not m.get("tame")
                        and (m.get("peaceful") or base_name(m.get("desc") or "") in self.NEVER_MELEE)]
                if near:
                    raise PermissionError(
                        "refusing to move while " + "/".join(sorted(conds & {"Conf", "Stun"})) + " next to "
                        + ", ".join(f"the {m.get('desc')} at ({m['x']},{m['y']})" for m in near)
                        + ": your step can go astray into it, and NetHack attacks without asking while you "
                        "are confused/stunned. Wait ('.') until it wears off, or force=True.")
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
            if bad:
                raise PermissionError(
                    f"refusing to confirm the pickup of {bad[0]!r}: touching a cockatrice corpse bare-handed is "
                    "instant stoning. Unselect it (its letter again), or force=True if you wear gloves.")
            stones = [i.text for i in snap.state.menu.selectable() if i.selected and self.GRAY_STONE.search(i.text)]
            if stones:
                raise PermissionError(
                    f"refusing to confirm the pickup of {stones[0]!r}: it may be a LOADSTONE (cursed: can't be "
                    "dropped). Unselect it and kick it first (a loadstone doesn't budge), or force=True.")
        elif k == "menu" and snap.state.menu is not None and "of what?" in (snap.state.prompt or "") \
                and unit[:1].isalpha():
            hit = [i.text for i in snap.state.menu.selectable()
                   if i.letter == unit[:1].decode() and self.COCKATRICE_CORPSE.search(i.text)]
            if hit:
                raise PermissionError(f"refusing to pick up {hit[0]!r} (instant stoning bare-handed); "
                                      "force=True if you wear gloves.")
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
                while auto_more and snap.state.kind in ("more", "text") and pages < max_more:
                    txt = snap.state.more_text
                    if snap.state.kind == "more":
                        messages.extend(_split_top(txt))
                    elif txt:
                        messages.append(txt)
                    snap = self.send_bytes(snap.state.dismiss.encode())
                    pages += 1
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
                    self._note_traps(snap, messages, moved_level=moved)
                    self._remember_terrain(snap, messages)
                    self._remember_here(snap, messages, prev_hero=cur.hero if cur is not None else None)
                    self._note_shop(snap, messages)
                    if (cur.state.kind == "direction" or b"z" in data[:2]) and data[-1:] == b">":
                        # zapped/applied downward: a wand of teleportation/cancellation/make invisible
                        # moves or erases the engraving here without a word (zap.c)
                        self.engr_seen.get(self.level_key(snap.status), {}).pop(snap.hero, None)
                    self._note_wield(messages)
                    self._note_intrinsics(messages)
                    arrive = {b">": "<", b"<": ">"}.get(bytes(data[-1:])) if (moved and data) else None
                    if arrive:
                        # only a real staircase: not a hole you dug ('>' answered the dig
                        # direction), a trap door, a level teleport or a fall
                        stood = self.terrain_seen.get(old_key, {}).get(cur.hero) if old_key else None
                        fell = any(re.search(r"\bfall|\bhole\b|trap door|\bdig\b|dug|teleport|You float down",
                                             m, re.I) for m in messages)
                        if fell or (stood is not None and stood != chr(data[-1])) or cur.state.kind != "command":
                            arrive = None
                    if arrive and snap.under is None:
                        # took the stairs: you stand on the other end (the '@' hides it)
                        self.terrain_seen.setdefault(self.level_key(snap.status), {})[snap.hero] = arrive
                        snap.under = arrive
                    if arrive and cur.hero is not None and old_key:
                        # where each staircase leads: the one you took, and the one you arrived on
                        new_key = self.level_key(snap.status)
                        self.stair_links.setdefault(old_key, {})[cur.hero] = new_key
                        self.stair_links.setdefault(new_key, {})[snap.hero] = old_key
            if snap.hero is not None:
                snap.engulfed = _engulfed(snap.screen, snap.hero)
            snap.wield_note = self.wield_note()
            snap.shop = self.shop_at(snap.hero, snap.status) if snap.status.ok else ""
            snap.last_pos = snap.hero or self.hero_pos
            snap.feature_desc = self.feature_desc.setdefault(self.level_key(snap.status), {}) \
                if snap.status.ok else {}
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
            for m in messages:
                self.history.append((snap.status.turn, m))
            if len(self.history) > self.max_history:
                del self.history[: len(self.history) - self.max_history]
            self.last = snap
            self._log(snap)
            for cb in list(self.on_step):
                try:
                    cb(snap)
                except Exception:
                    pass
            return snap

    # Messages meaning the hero is standing on a trap *now* (teleporters, trap
    # doors, holes and portals move you away, so they're not listed; their '^'
    # is picked up from the map or the per-level #terrain scan instead).
    _TRAP_MSG = re.compile(
        r"(^There is an? .*\b(trap|pit|web)\b.* here\.|^You escape an? |An arrow shoots out at you|"
        r"A little dart shoots out at you|bear trap closes on your|your magical energy drain away|"
        r"^You (fall|step|tumble|jump|land) into an? pit|on a set of sharp iron spikes|A board beneath you|"
        r"loose board below you|crease in the linoleum|spider web!|A cloud of gas puts you to sleep|"
        r"You are enveloped in a cloud of gas|A gush of water hits|tower of flame|momentarily lethargic|"
        r"momentarily blinded by a flash of light|You trigger a rolling boulder trap|triggered an? land mine|"
        r"You (step onto|float over|fly over|feel) an? polymorph trap|^You (float|fly) over an? )")

    def _note_traps(self, snap: Snap, messages: list[str], moved_level: bool = False) -> None:
        """Remember trap squares per level: every displayed '^', and the hero's
        square when a trap message fires there (objects can hide a trap)."""
        if snap.hero is not None and _engulfed(snap.screen, snap.hero):
            return
        lv = self.level_key(snap.status)
        known = self.traps.setdefault(lv, set())
        # a seen trap stays drawn as '^' unless something stands/lies on it:
        # plain floor/corridor there means it's gone (disarmed, used up, filled)
        for c in list(known):
            if c != snap.hero and snap.screen.at(*c) in ".#" and c[1] > snap.state.msg_rows:
                known.discard(c)
        for y in range(1 + snap.state.msg_rows, 22):
            row = snap.screen.row(y)
            x = row.find("^")
            while x >= 0:
                known.add((x, y))
                x = row.find("^", x + 1)
        if not moved_level and snap.hero is not None and any(self._TRAP_MSG.search(m) for m in messages):
            known.add(snap.hero)

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
            self.terrain_seen.setdefault(key, {}).update(r["features"])
        return r

    def terrain_scan(self) -> dict | None:
        """What the hero knows of this level's terrain, from NetHack's own
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
                    found = {"traps": set(), "features": {}}
                    for y in range(MAP_TOP + 1, MAP_BOTTOM + 1):
                        row = s.screen.row(y)
                        for x, ch in enumerate(row):
                            if ch == "^" or ch == '"':
                                found["traps"].add((x, y))
                            elif ch in self.FEATURE_CHARS and feature_at(s.screen, x, y):
                                found["features"][(x, y)] = ch
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
            snap.wield_note = self.wield_note()
            snap.shop = self.shop_at(snap.hero, snap.status) if snap.status.ok else ""
            snap.last_pos = snap.hero or self.hero_pos
            snap.feature_desc = self.feature_desc.setdefault(self.level_key(snap.status), {}) \
                if snap.status.ok else {}
            if self.tracker is not None and snap.state.kind == "command":
                try:
                    snap.monsters = self.tracker.update(snap)
                except Exception as e:  # noqa: BLE001
                    self.log_event({"ev": "tracker_error", "err": repr(e)})
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

    def log_event(self, rec: dict) -> None:
        if not self.log_path:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a") as f:
            f.write(json.dumps(rec) + "\n")
