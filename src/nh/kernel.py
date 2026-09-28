"""Persistent Python kernel with pause-on-event execution.

`exec(code)` runs player code in a worker thread. Inside it, every `do(keys)`
performs one game step and then checks for events worth a human look:
messages, HP loss, new monsters, status conditions, level change, game over.
On such an event the worker parks inside `do()` and control returns to the
player with the reason. `cont()` resumes; any other request abandons the
parked code (the game state is consistent at the pause boundary).
"""

from __future__ import annotations

import builtins
import contextlib
import io
import linecache
import queue
import re
import sys
import threading
import time
import traceback
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable

from .game import Game, Snap
from .keys import parse_keys
from .parse import MAP_BOTTOM, MAP_TOP, MONSTER_CHARS, HUNGER, ENCUMBRANCE

_HUNGER_RANK = {"": 0, "Satiated": 0, "Hungry": 1, "Weak": 2, "Fainting": 3, "Fainted": 4}
_ENC_RANK = {"": 0, "Burdened": 1, "Stressed": 2, "Strained": 3, "Overtaxed": 4, "Overloaded": 5}
# engulfers with AD_DGST (monst.c): being swallowed by one is a race against total digestion
DIGESTERS = ("purple worm", "lurker above", "trapper")
# what cures the deadly conditions (3.6.7: potion.c healup(), eat.c, pray.c fix_worst_trouble())
COND_HINTS = {
    "TermIll": "deadly illness (dies in ~10-30 turns): apply a unicorn horn, eat a eucalyptus leaf, quaff blessed "
               "healing / non-cursed extra or full healing, or pray if prayer is safe. If an engulfer or attacker "
               "keeps re-infecting you (Juiblex, Demogorgon, Pestilence), kill it first when a few blows will do "
               "(from inside an engulfer every blow hits), then cure",
    "FoodPois": "deadly food poisoning: apply a unicorn horn, eat a eucalyptus leaf, quaff blessed healing / "
                "non-cursed extra or full healing, or pray if prayer is safe",
    "Stone": "TURNING TO STONE (5 turns): eat a lizard corpse or an acidic corpse, quaff acid, cast stone to "
             "flesh, or pray if prayer is safe",
    "Slime": "TURNING INTO SLIME (10 turns): burn it (zap fire at yourself, read fire, step into a fire trap), "
             "or pray if prayer is safe (a unicorn horn does NOT help)",
    "Strngl": "STRANGLED (dies in 6 turns): remove the amulet (R) at once, or pray if prayer is safe",
}


# Messages that never need a human look by themselves (pets, routine
# noises). They're still shown in the output; they just don't pause an exec.
INVISIBLE_MISS = (r"^(?:The |An? )?.+? (?:(?:swings|snaps|kicks|lunges) wildly(?: and misses)?!|attacks a spot beside "
                  r"you\.|strikes at (?:thin air|empty water)!|tries to touch you and misses!|strikes at your "
                  r"(?:invisible )?displaced image and misses you!|smiles (?:engagingly|seductively) at your "
                  r"(?:invisible )?displaced image\.\.\.|reaches towards your distorted image\.|is fooled by water "
                  r"reflections and misses!)$")
DEFAULT_BENIGN = [re.compile(p) for p in (
    r"^You feel full of energy\.$",            # allmain.c: Pw back to max (interrupts a rest)
    # (p2 shift 34: each paused a crowd fight) uhitm.c passive(): a fire elemental's fire, resisted — no damage;
    # mhitu.c AD_LEGS: a xan's prick stopped by your boots (dmg 0); zap.c zap_over_floor(): your cold ray froze
    # water out of your sight
    r"^You feel mildly warm\.$", r"^(?:The |It ).*scratches your (?:left |right )?boot!$",
    r"^You hear a crackling sound\.$",
    # invent.c look_here() while blind: stepping on objects (p1 shift 30: hunt() paused on every pile)
    r"^You feel here ", r"^You feel no objects here\.", r"^Things that you feel here:",
    r"^Suddenly, .+ disappears out of sight\.$",   # teleport.c: a monster took a level teleporter/trap door away
    # (not when a monster picks up a wand — it may zap you with it — or something you need to win)
    # (nor a cockatrice corpse: a gloved monster wields it and every hit stones you — p2 shift 38 #560)
    r"^(The |Your )?[\w' -]+ (picks up|drops|eats|is eating|finishes eating) (?!.*\b(?:wand|Amulet of Yendor|"
    r"Orb of Fate|Bell of Opening|Candelabrum|Book of the Dead|silver bell|candelabrum|papyrus spellbook|"
    r"(?:cockatrice|chickatrice) corpse)\b)",
    # worn.c m_dowear(): a monster changing armor (p4 shift 6: every soldier-fight call needed -a patterns);
    # shk.c: a shopkeeper repairing damage out of sight; monmove.c: a monster opening a door out of sight
    r"^(?:The |An? )?[\w' -]+ (?:removes .+ and )?puts on .+\.$",
    r"^The dungeon acoustics noticeably change\.$", r"^You hear a door (?:unlock and )?open\.$",
    r"^You swap places with ",
    # mhitu.c wildmiss(): a monster that can't see you (you are invisible / displaced / underwater) misses —
    # no damage (p4 shift 7 #57: "The orc mummy attacks a spot beside you." paused fight() while invisible)
    INVISIBLE_MISS,
    # monster-vs-monster melee (mhitm.c), usually your pet's fights; a death, stoning or
    # swallowing still pauses
    r"^(?:The |Your )?[\w' -]+? (?:misses|bites|stings|butts|touches|hits|squeezes) "
    r"(?:the [\w' -]+|it|itself|himself|herself)\.$",
    r"^(?:The |Your )[\w' -]+? (?:kills|destroys) (?!you\b)(?:the |an? )?[\w' -]+[.!]$",   # your pet's kills
    r"^You stop\. .* is in your way",
    r"^You stop\.$",                                   # "You stop.  Your kitten is in your way." is split
    r"^(Your|The) .* is in your way\.$",
    r"^(Your|The) .* is in the way!$",                 # uhitm.c: 1/7 of pet swaps fail (or in a shop)
    r"^(Your|The) .* doesn't seem to move!$",          # a frozen pet you tried to swap with
    r"^Pardon me, .+\.$",                               # travel's fallback step bumped a pet/peaceful
    # struggling out of a trap you already know you're in (the trap itself paused once)
    r"^You are still in a pit\.", r"^You crawl to the edge of the pit\.",
    r"^You are (?:stuck to the web|caught in a bear trap)\.", r"^You disentangle yourself\.",
    r"^You move .* out of your way",
    r"^You see here ",
    r"^Things that are here:",
    # level sounds (sounds.c dosounds): recorded per level by the tracker (`nh info`);
    # the beehive and barracks sounds still pause
    r"^You hear (bubbling water|water falling on coins|the splashing of a naiad|a soda fountain|a slow drip|"
    r"a gurgling noise|dishes being washed|the tones of courtly conversation|a sceptre pounded|"
    r"Queen Beruthiel's cats|mosquitoes|Donald Duck|someone counting money|the quarterback calling|"
    r"someone searching|the footsteps of a guard on patrol|Ebenezer Scrooge|a sound reminiscent of|"
    r"Doctor Dolittle|someone cursing shoplifters|the chime of a cash register|Neiman and Marcus|"
    r"someone praising|someone beseeching|an animal carcass being offered|a strident plea|"
    r"a strange wind|convulsive ravings|snoring snakes|someone say|a loud ZOT|crashing rock)",
    r"^You smell marsh gas",
    r"^You suddenly realize it is unnaturally quiet",
    r"on the back of your .* (stand|stands) up",
    r"^You see no objects here", r"^There are (?:several|many) objects here\.",
    r"^You try to feel what is lying here on the ",       # (blind: the pile's list follows)
    r"^There (is|are) (a|an|several|many|\d+) .* here\.?$",
    r"^You hear (some noises|a door open|the footsteps of a guard|bubbling water|water falling|the splashing|a gurgling|a slow drip|a chugging|someone counting money|the chime of a cash register|someone cursing shoplifters)",
    r"^You hear some noises in the distance",
    r"^\$ - (\d+|a) gold pieces?\.",
    r"^[a-zA-Z] - (?!.*\b(cursed|loadstone)\b).*\.$",   # pickup/inventory result "i - a scroll ..."
    r"^The door opens\.",
    r"^You stop in front of the door\.",
    r"^You are in full health\.",                      # a counted search/rest stops at full HP
    r"^You drop (?!.*\b(?:loadstone)\b).*\.$",          # result of your own drop command
    r"^Your (?!wielded ).*\b(corpse|corpses|egg|eggs)\b.* rots? away\.$",   # carried food rotting
    # the floor listing of a feature square with a pile ("There is an altar ... here." + the list window)
    r"^There (?:is|are) [^\n]* here\.\nThings that are here:",
    # siege noise (castle garrisons, archers): the HP and new-monster checks still pause
    r"^You hear a door crash open", r"^(?:An? |The )[\w' -]+ misses you[.!]$", r"^You are almost hit by ",
    r"^The [\w' -]+ (?:throws|shoots|fires) ", r" welds itself to the [\w' -]+'s hand!$",
    r"^You stop at the edge of the (?:water|lava)\.",
    r"^A board beneath (?:the |an? )[\w' -]+ squeaks",
    r"^You hear an? [A-G][\w ]* squeak (?:nearby|in the distance)\.",   # a monster on a squeaky board (trap.c)
    r"^The poison doesn't seem to affect you\.",       # poison resistance at work
    r"^A mysterious force prevents (?:the |an? )?[\w' -]+ from teleporting!$",   # a no-teleport level (Sokoban)
    # your own armor/accessory changes (a cursed one still pauses: "You can't. It is cursed.")
    r"^You were wearing (?!.*\bcursed\b)", r"^You are now wearing (?!.*\bcursed\b)",
    r"^You finish (?:taking off|your dressing maneuver)",
    r"^You can see again\.$",           # blindness over (the status line shows it)
    r"^You feel (?:a bit steadier|less wobbly|less confused|less trippy) now\.$",   # stun/confusion over
    # armed monsters around you (the effects on you — HP, status, burnt items — pause by themselves; a
    # monster picking up a WAND still pauses, and so does one wielding a cockatrice corpse)
    r"^Boing!$", r"^You hear a nearby zap\.$",
    # monsters using items in a melee: potions, create monster (the newcomers pause by themselves), weapons
    r"^(?!You )(?:The |An? )?[\w' -]+ drinks (?:an? |the )[\w' -]+!$", r" (?:seems|looks) more experienced\.$",
    r"^The .+ reads a scroll of create monster!$", r"^The .+ tries to wield ",
    r"^It is (?:hit|missed)[.!]$",
    r"^The (?:magic missile|bolt of \w+|sleep ray|death ray|blast of [\w ]+|stream of \w+|ray of \w+|"
    r"fireball|cone of cold) (?:whizzes by you|bounces)!$",
    r"^The .+ wields (?:an? |the |\d+ )(?!.*\b(?:cockatrice|chickatrice) corpse).*!$",
    r"^You stop searching\.$",          # a counted search cut short (its cause pauses by itself)
    # monmove.c m_move(): a mind flayer more than 8 squares away blasted — no effect at that range ("goto
    # toofar"); the obs keeps a MIND FLAYER line for the level instead of a pause (p2 shift 33: it stopped
    # dig() and paused head_to() right after telepathy_scan() had shown it)
    r"^You sense a faint wave of psychic energy\.$",
    # a monster stumbling into a trap (trap.c mintrap(): the trap is already on the map or now is)
    r"^(?!You )(?:The |An? |[A-Z][\w']*'s )?[\w' -]+ (?:falls into a pit|is caught in a bear trap|"
    r"is caught in a web|steps on a squeaky board|is hit by a (?:little dart|arrow))!$",
    r"^A gush of water hits (?!you\b|your\b)",        # a monster on a rust trap (yours still pauses)
    # a monster's spell that fumbled or wasn't aimed at you (mcastu.c cursetxt(), castmu() fumble)
    r"^.+ points (?:at you, then curses|all around, then curses|and curses in your general direction)\.$",
    r"^You hear a mumbled curse\.$", r"^The air crackles around .+\.$",
    # mcastu.c castmu(): an UNDIRECTED spell (no "at you": cure/haste self, disappear, aggravation, summoning)
    # — cast from afar too, even from behind a locked door (p1 shift 32); its effect has its own message
    # (new monsters, "monsters are aware of your presence") that pauses by itself
    r"^(?!You )(?:The |An? )?[\w' -]+ casts a spell!$",
    r"^You feel yourself slowing down a bit\.$",     # a temporary speed-up ended; intrinsic speed remains
    r"^You feel vaguely nervous\.$",   # wizard.c intervene() cases 0-1: flavour only (the other cases pause)
    # a light source burning down (timeout.c burn_object()); "has gone out" still pauses
    r"^Your .+ flickers(?: considerably)?\.$", r"^Your .+ seems? about to go out\.$",
    r"^Your .+ flames? flickers? low!$",
    # a lighter load (hack.c encumber_msg) is good news; a heavier one pauses on the status change
    r"^Your movements are (?:now unencumbered|only slowed slightly by your load)\.$",
    r"^You rebalance your load\.  ?Movement is still difficult\.$",
    r"^You \w+ under your load\.  ?Movement is still very hard\.$",      # (stagger/crawl/slither...)
    # exercise (attrib.c exerchk): gains are good news; the status line shows the attribute
    r"^You feel (?:very )?(?:strong|smart|wise|agile|tough|charismatic)!$",
    r"^You must have been (?:exercising diligently|very observant|working on your reflexes|leading a healthy)",
    # dropping things on an altar to learn their BUC (the flash/landing is the answer, not an event)
    r" lands? on the altar\.$", r"^There is an? (?:amber|black) flash as .* hits? the altar\.$",
    # a shopkeeper's greeting (shk.c u_entered_shop; the snapshot's `shop` names the shop) — "leave your
    # pick-axe outside" and "Invisible customers are not welcome!" still pause
    r'^"?[A-Z][\w ]*, [^!]+!\s+Welcome(?: again)? to [^!]+!"?$',
)]


# level sounds worth ONE pause per level (the tracker records them in `nh info`); repeats are noise
ONCE_PER_LEVEL = [re.compile(p) for p in (
    r"^You hear an? [\w' -]+ howling at the moon\.",           # a were-creature changed form out of sight
    r"^You hear (?:a low buzzing|an angry drone)", r"^You suddenly realize it is unnaturally quiet",
    r"^You hear (?:blades being honed|loud snoring|dice being thrown|General MacArthur)",
    r"^You hear (?:the tones of courtly conversation|a sceptre pounded|Queen Beruthiel)",
    r"^You hear (?:a seal barking|an elephant stepping on a peanut)",
    r"^You hear (?:a|several) slurping sounds?\.",       # a gelatinous cube eating objects out of sight (mon.c)
    r"^You hear a crunching sound\.",                    # mon.c meatmetal(): a metal-eater (rust monster, xorn)
    r"^You feel that monsters are aware of your presence\.",   # mcastu.c aggravation: once per level is news
    # priest.c intemple(): each entry into a temple (p3 shift 15: every trip through Minetown's temple paused);
    # the Sanctum's own lines still pause every time
    r'^"?Pilgrim, you enter a (?:sacred|desecrated) place!"?$', r"^You have a(?: strange)? forbidding feeling\.\.\.$",
    r"^You experience (?:a|an unusual) sense of peace\.$", r"^You have an eerie feeling\.\.\.$",
    r"^You feel like you are being watched\.$", r"^A shiver runs down your [\w ]+\.$", r"^[\w' -]+ intones:$",
    # hack.c check_special_room(): said once per room (it turns into an ordinary room); the game records the
    # room (special_rooms) and the step's SPECIAL ROOM reason pauses for each new one
    r"^You enter an opulent throne room!", r"^You enter a leprechaun hall!", r"^You enter a giant beehive!",
    r"^You enter a disgusting nest!", r"^You enter an anthole!", r"^You enter a military barracks!",
    r"^Welcome to David's treasure zoo!", r"^You have an uncanny feeling\.\.\.", r"^Run away!  Run away!",
)]


def wand_danger(note: str, kind, game) -> str:
    """The pause for a monster's wand zapped at you (game._note_wand_zaps): SLEEP and DEATH rays you neither
    resist nor reflect are deadly (asleep 6d25 turns beside it; a death ray kills outright) — say so by name;
    an unknown wand might be either; others ('' for a ray you resist) get the plain message pause."""
    res = set(getattr(game, "intrinsics", None) or ())
    refl = bool(getattr(game, "reflecting", False))
    mr = bool(getattr(game, "magic_res", False))
    lines = ("get OUT of its lines (the same row, column or diagonal, up to 13 squares away — it zaps from next "
             "to you too, muse.c), kill it at range, or zap/teleport it away")
    if kind == "sleep" and "sleep" not in res and not refl:
        return (f"SLEEP RAY — {note}: you have NO sleep resistance or reflection: asleep for up to 150 turns "
                f"beside it = death — {lines}")
    if kind == "death" and not mr and not refl:
        return f"DEATH RAY — {note}: you have NO magic resistance or reflection: one hit KILLS you — {lines}"
    if kind is None and not refl:
        return (f"WAND ZAPPED AT YOU — {note}: it may be SLEEP or DEATH — {lines} until you know (the ray names "
                "itself when it comes: 'The sleep ray ...')")
    return ""


_RAYS = (r"(?:magic missile|bolt of \w+|sleep ray|death ray|blast of [\w ]+|stream of \w+|ray of \w+|"
         r"fireball|cone of cold)")
_REFLECTED = re.compile(rf"^The {_RAYS} hits you!$|^The .+ zaps an? wand of (?:sleep|fire|cold|lightning|"
                        rf"magic missile|death)!$|^But it reflects from your ")

# a monster buffing itself (muse.c potions/wands, mcastu.c cure self, worn.c mon_adjust_speed): routine when
# every monster of that name in view is PEACEFUL (p3 shift 14: Minetown gnomes quaffing speed and invisibility
# paused travel); a hostile's still pauses
_SELF_BUFF = re.compile(r"^(?:The |An? )?(?P<n>[\w' -]+?)(?:'s? body takes on an? [\w ]+ transparency\.|"
                        r" drinks [^!]+!| is suddenly moving (?:much )?faster\.| looks (?:better|completely healed)\.|"
                        r" seems more experienced\.)$")


def peaceful_self_buff(m: str, *snaps) -> bool:
    mm = _SELF_BUFF.search(m)
    if not mm:
        return False
    from .danger import base_name
    name = mm.group("n").strip().lower()
    seen = [x for s in snaps if s is not None for x in (s.monsters or [])
            if base_name(x.get("desc") or "").lower() == name]
    return bool(seen) and all(x.get("peaceful") and not x.get("tame") for x in seen)


# mon.c monkilled(): "The newt is killed!" / "The zombie is destroyed by the blast of fire!" — a monster in view
# killed by your pet, a trap, another monster: no news for you (p6 shift 1 #7: every explore() with a kitten
# paused on its kills) — unless it may be your pet: a kind among the tame monsters in view, or a name that is no
# monster's (a named pet)
_KILLED_BY_OTHER = re.compile(r"^(?:The |An? )?(?P<n>[\w' -]+?) is (?:killed|destroyed)(?: by [^!]+)?!$")


def other_monster_killed(m: str, *snaps) -> bool:
    mm = _KILLED_BY_OTHER.match(m)
    if not mm:
        return False
    from .danger import base_name, monster_record
    name = (base_name(mm.group("n")) or "").lower()
    if not name or not monster_record(name):
        return False
    tame = {(base_name(re.sub(r"^tame ", "", x.get("desc") or "")) or "").lower()
            for s in snaps if s is not None for x in (s.monsters or []) if x.get("tame") or x.get("pet")}
    return name not in tame


# a poison gas cloud (region.c inside_gas_cloud; a green dragon's breath leaves them, so do stinking cloud
# scrolls and Gehennom's fumaroles): with poison resistance only a 1-turn blindness and a cough each turn
# you stand in it — news once per level; without it "Something is burning your lungs!" costs HP
_CLOUD = re.compile(r"^Your eyes sting\.$|^You cough!$")

# mhitu.c AD_FIRE/AD_COLD/AD_ELEC: a resisted elemental hit ("You're on fire! | The fire doesn't feel hot!"):
# no damage (burnt/frozen/shocked items have their own messages, which still pause)
_RESISTED_HIT = {
    re.compile(r"^The fire doesn't feel hot!$"):
        re.compile(r"^You're (?:on fire|already on fire|burning|boiling|melting|heating up|being roasted)!$"),
    re.compile(r"^The frost doesn't seem cold!$"): re.compile(r"^You're covered in frost!$"),
    re.compile(r"^The zap doesn't shock you!$"): re.compile(r"^You get zapped!$"),
}

# engrave.c read_engr_at(): the lead-in line and the text; the same text read again on the same square is no
# news (p1 shift 35 #14: an old dust engraving paused on every step onto it)
_ENGR_LINES = re.compile(r"^Something is (?:written here in the (?:dust|frost)|engraved here on the )|"
                         r"^Some text has been (?:burned|melted) into the |^There's some graffiti on the |"
                         r"^You see a message scrawled in blood here\.$|^You (?:read|feel the words): \"")


def _moves_at_most_one(keys: bytes) -> bool:
    """A command that moves you at most one square: a single step, F/m + direction, search or rest
    (with a count too)."""
    return bool(re.fullmatch(rb"[hjklyubn.s]|[Fm][hjklyubn]|n?\d{1,4}[s.]", keys or b""))


class Abandon(BaseException):
    """Raised inside a parked worker to unwind it."""


class PauseRequested(Exception):
    pass


class _ThreadStdout(io.TextIOBase):
    """sys.stdout proxy: writes from registered threads go to their buffers."""

    def __init__(self, real):
        self.real = real
        self.buffers: dict[int, io.StringIO] = {}

    def write(self, s):
        buf = self.buffers.get(threading.get_ident())
        if buf is not None:
            return buf.write(s)
        return self.real.write(s)

    def flush(self):
        try:
            self.real.flush()
        except Exception:
            pass


_STDOUT = None


def _install_stdout():
    global _STDOUT
    if _STDOUT is None:
        _STDOUT = _ThreadStdout(sys.stdout)
        sys.stdout = _STDOUT
    return _STDOUT


def monster_counts(snap: Snap) -> Counter:
    c: Counter = Counter()
    scr = snap.screen
    hero = snap.hero
    for y in range(MAP_TOP, MAP_BOTTOM + 1):
        row = scr.row(y)
        for x, ch in enumerate(row):
            if ch in MONSTER_CHARS and (hero is None or (x, y) != hero):
                c[(ch, scr.color_at(x, y), scr.reverse_at(x, y))] += 1
    return c


@dataclass
class PauseInfo:
    reason: str
    snap: Snap
    where: list[dict] = field(default_factory=list)


class Kernel:
    def __init__(self, game: Game):
        self.game = game
        self.ns: dict[str, Any] = {"__name__": "__nhkernel__", "__builtins__": builtins}
        self.worker: threading.Thread | None = None
        self.events: queue.Queue = queue.Queue()
        self.resume = threading.Event()
        self.abandon_flag = False
        self.autocontinue: list[re.Pattern] = []
        self.pause_on_monsters = True
        self.new_monster_filter: Callable | None = None   # set by monster_filter(): which newcomers pause
        self._announced: dict[str, dict] = {}   # species -> {turn, level, cells} of its last new-monster pause
        self._heard: set = set()     # (level, ONCE_PER_LEVEL index) already paused for
        self._cloud_turns: dict = {}  # level -> turn of the last poison-gas-cloud message there
        self.defer_dist: int | None = None   # defer_far(): newcomers farther than this wait until they come near
        self._deferred: dict = {}    # monster id -> {level, pos, near}: seen far off, pauses once it MOVES within near
        self.activity = ""         # set_activity(): what a long helper is doing (shown with pauses)
        self._reply_sent: bytes | None = None   # the `cont --reply` keys just sent for the script
        self.parked = False        # True while an exec worker waits at a pause point
        self.hp_pause = 0.7        # pause on HP loss when HP < this fraction of max...
        self.hp_hit_pause = 0.15   # ...or when one step costs >= this fraction of max
        self.fight_floor: float | None = None   # hp_rules(): inside a fight, the HP floor instead of the above
        self.budget_steps = 400
        self.budget_seconds = 110.0
        self._steps = 0
        self._t0 = 0.0
        self._prev: Snap | None = None
        self._pending_reply: str | None = None
        self.code_counter = 0
        self._stdout = _install_stdout()
        self._install_api()

    # ------------------------------------------------------------------ api
    def _install_api(self) -> None:
        k = self

        def do(keys: str, *, force: bool = False, quiet: bool = False, ok=None, multi: bool = False,
               secret: bool = False, expect=()) -> Snap:
            """Send keys (see nh.keys notation); returns the settled snapshot.

            quiet=True: messages from this step don't pause an exec (HP loss,
            new monsters, status changes and game over still do). For
            information-only keystrokes like farlook or inventory display.
            ok=[regex,...]: messages matching any of these don't pause (this
            step only), on top of the exec's autocontinue list.
            expect=("level",): this step is meant to change level (no
            level-change pause; everything else still pauses); "blind": it
            puts on a blindfold on purpose (no pause for +Blind)."""
            return k._do(keys, force=force, quiet=quiet, ok=ok, multi=multi, secret=secret, expect=expect)

        def look() -> Snap:
            """Re-capture the screen without sending anything."""
            s = k.game.look()
            k.ns["obs"] = s
            return s

        def pause(reason: str = "script pause") -> None:
            """Hand control back to the player (inside exec)."""
            k._maybe_pause(reason, k.game.last or k.game.look(), force=True)

        def note(text: str) -> None:
            k.game.log_event({"ev": "note", "ts": round(time.time(), 3), "text": text})

        @contextlib.contextmanager
        def long_task(steps: int = 1200, seconds: float = 330.0):
            """Inside this block the exec's step/time budget pause comes later (a long helper the player
            trusts, like sokoban.solve(), shouldn't stop mid-way just for the budget); restored after."""
            old = (k.budget_steps, k.budget_seconds)
            k.budget_steps, k.budget_seconds = max(old[0], steps), max(old[1], seconds)
            try:
                yield
            finally:
                k.budget_steps, k.budget_seconds = old

        @contextlib.contextmanager
        def monster_filter(fn):
            """Inside this block a newly seen hostile pauses the exec only if
            fn(monster_dict) is true (e.g. only dangerous ones during a fight
            at a chokepoint). Everything else still pauses as usual."""
            if not callable(fn):
                raise TypeError(f"monster_filter() takes a predicate on the monster dict, not {fn!r}: e.g. "
                                "monster_filter(lambda m: 'bee' not in (m.get('desc') or '')) — only newcomers "
                                "it returns True for pause")
            old = k.new_monster_filter
            # nested blocks combine: a newcomer pauses only if every active filter says so (a helper's
            # own filter must not undo the player's: fight_until_clear inside a "no bees" block)
            k.new_monster_filter = fn if old is None else (lambda m, _o=old, _f=fn: _o(m) and _f(m))
            try:
                yield
            finally:
                k.new_monster_filter = old

        @contextlib.contextmanager
        def hp_rules(floor: float):
            """Inside this block (fight(), fight_until_clear()) HP loss pauses
            only when HP falls below floor * max, when two more steps losing
            what this one lost would take it there, or when one step costs a
            quarter of max HP — not after every blow below 70% (the helper
            checks HP before each blow itself). Nested blocks keep the higher floor."""
            old = k.fight_floor
            k.fight_floor = floor if old is None else max(old, floor)
            try:
                yield
            finally:
                k.fight_floor = old

        @contextlib.contextmanager
        def defer_far(dist: int = 6):
            """Inside this block a new hostile farther than `dist` squares
            (and without a danger note) doesn't pause yet — it pauses once
            as 'approaching' when it comes within DEFER_NEAR squares (a Sokoban
            solve with monsters behind walls). Nested blocks keep the smaller."""
            old = k.defer_dist
            k.defer_dist = dist if old is None else min(old, dist)
            try:
                yield
            finally:
                k.defer_dist = old

        def set_activity(text: str = "") -> None:
            """What a long helper is doing right now (e.g. 'sokoban step 25/26, 12 pushes done'):
            shown after the reason of any pause until changed or cleared."""
            k.activity = text or ""

        def watch_monsters(mons, near: int | None = None) -> int:
            """Pause once ('approaching: ...') when one of these monsters (dicts with the tracker's id, from
            obs.monsters or a telepathy scan) MOVES to within `near` squares (default 6). For dangerous
            monsters you have already seen: coming back into view they are not 'new' and would not pause.
            Returns how many are watched (this level only)."""
            snap = k.game.last
            level = snap.status.ldesc if snap is not None and snap.status.ok else ""
            n = 0
            for m in mons or []:
                if m.get("id") is None or m.get("tame") or m.get("peaceful") or m.get("pet"):
                    continue
                k._deferred[m["id"]] = {"level": level, "pos": (m["x"], m["y"]), "near": near or k.DEFER_NEAR,
                                        "watch": True, "ch": m.get("ch")}
                n += 1
            return n

        def unwatch_monsters(ids) -> None:
            """No more 'approaching' pause for these monster ids (the one hunt()/fight() goes after)."""
            for i in ids or ():
                k._deferred.pop(i, None)

        def quiet_messages(messages) -> list:
            """Which of these messages would NOT pause an exec now: the exec's autocontinue (-a) patterns,
            the default benign list, level sounds already paused for on this level. No side effects."""
            snap = k.game.last
            level = snap.status.ldesc if snap is not None and snap.status.ok else ""
            return [m for m in messages or []
                    if any(p.search(m) for p in k.autocontinue) or any(p.search(m) for p in DEFAULT_BENIGN)
                    or any(p.search(m) and (level, i) in k._heard for i, p in enumerate(ONCE_PER_LEVEL))]

        self.ns.update(do=do, look=look, pause=pause, note=note, game=self.game, monster_filter=monster_filter,
                       set_activity=set_activity, hp_rules=hp_rules, defer_far=defer_far, long_task=long_task,
                       watch_monsters=watch_monsters, quiet_messages=quiet_messages,
                       unwatch_monsters=unwatch_monsters)
        self.ns["obs"] = self.game.last

    # --------------------------------------------------------- stepping
    def in_worker(self) -> bool:
        return self.worker is not None and threading.current_thread() is self.worker

    def _do(self, keys: str, force: bool = False, quiet: bool = False, ok=None, multi: bool = False,
            secret: bool = False, expect=()) -> Snap:
        data = parse_keys(keys) if isinstance(keys, str) else keys
        if self.in_worker() and self._reply_sent is not None:
            sent, self._reply_sent = self._reply_sent, None
            if data == sent:
                # the player already answered the prompt with `cont --reply`; this is the script's
                # own answer to the same prompt — sending it now would type it as commands
                print(f"(skipped do({keys!r}): already answered by cont --reply)")
                return self.game.last or self.game.look()
        _guard_dangerous(data, force)
        cur = self.game.last or self.game.look()
        if self.in_worker():
            if self.abandon_flag:
                raise Abandon()
            # prompt-swallow check: a [yn]-style prompt ignores other keys
            if cur.state.kind == "yn" and data:
                if cur.state.choices == "yes/no":       # typed answer: "yes<CR>" / "no<CR>" / <Esc>
                    allowed = set("yYnN\x1b\r\n")
                else:
                    allowed = set(cur.state.choices.replace(" ", "")) | {"\x1b", "\r", "\n"}
                if chr(data[0]) not in allowed:
                    self._maybe_pause(
                        f"prompt open: {cur.state.prompt!r} accepts [{cur.state.choices}] "
                        f"but code sent {keys!r} (not sent). Answer with cont(reply=...)", cur, force=True,
                        sent=False)
                    cur = self.game.last or cur
            self._steps += 1
        before = self.game.last
        snap = self.game.step(data, multi=multi, secret=secret, force=force)
        self.ns["obs"] = snap
        if self.in_worker():
            self._last_keys = data
            self._check_events(before, snap, quiet=quiet, ok=ok, expect=expect)
            if self._reply_sent is not None and self.game.last is not None and self.game.last is not snap:
                # the player answered the prompt this step opened (`cont --reply`): the caller gets the state
                # AFTER the answer (p4 shift 5 #156/#157: fight() saw the stale "Call an emerald potion:" getlin
                # and stopped with its target alive)
                after = self.game.last
                after.messages = list(snap.messages) + [m for m in after.messages if m not in snap.messages]
                snap = after                # (keeping this step's own messages: "You kill the hill orc!")
                self.ns["obs"] = snap
            if snap.state.kind == "command" and (self._steps >= self.budget_steps or
                                                 time.monotonic() - self._t0 >= self.budget_seconds):
                # (only at the command prompt: never park a script inside a menu/cursor prompt)
                self._maybe_pause(
                    f"budget: {self._steps} steps / {time.monotonic() - self._t0:.0f}s in this exec "
                    f"— cont() to keep going", snap, force=True)
        return snap

    def _check_events(self, before: Snap | None, snap: Snap, quiet: bool = False, ok=None, expect=()) -> None:
        """expect: pause reasons the calling helper handles itself ("level": it meant to change
        level, e.g. dig() falling through its hole — it re-wields first; new monsters still pause)."""
        reasons = []
        if snap.state.kind in ("gameover", "dead"):
            reasons.append("GAME OVER" if snap.state.kind == "gameover" else "TERMINAL DEAD")
        extra = [re.compile(p) if isinstance(p, str) else p for p in (ok or [])]
        in_cloud = any(_CLOUD.search(m) for m in snap.messages)
        cloud_key = (snap.status.ldesc if snap.status.ok else "", "cloud")
        turn = snap.status.turn if snap.status.ok and snap.status.turn is not None else 0
        last_cloud = self._cloud_turns.get(cloud_key[0])
        # once per level (again after 50 turns without cloud messages); the HP checks cover the damage
        cloud_news = in_cloud and (last_cloud is None or turn - last_cloud > 50)
        if in_cloud:
            self._cloud_turns[cloud_key[0]] = turn
        # a ray you reflected (zap.c buzz(): "The sleep ray hits you!" + "But it reflects from your
        # shield!"): the hit and the monster's zap before it are news only without the reflection
        reflected = any(m.startswith("But it reflects from your ") for m in snap.messages)
        # a poisoned bite/sting you resisted ("The quasit's sting was poisoned! | The poison doesn't seem to
        # affect you.") is no news either
        resisted = any(m.startswith("The poison doesn't seem to affect you") for m in snap.messages)
        elemental = [lead for tail, lead in _RESISTED_HIT.items() if any(tail.search(m) for m in snap.messages)]
        engr_repeat = bool(getattr(snap, "engr_repeat", False))
        # a grave's epitaph ("Something is engraved here on the headstone. | You read: ...") is flavour text,
        # not news (p3 shift 18 #75: stepping onto a grave paused the exec)
        engr_repeat = engr_repeat or any(m.startswith("Something is engraved here on the headstone")
                                         for m in snap.messages)
        msgs = [m for m in snap.messages
                if not any(p.search(m) for p in self.autocontinue)
                and not any(p.search(m) for p in extra)
                and not any(p.search(m) for p in DEFAULT_BENIGN)
                and not (reflected and _REFLECTED.search(m))
                and not (resisted and re.search(r" was poisoned!$", m))
                and not any(t.search(m) for t in _RESISTED_HIT)
                and not any(lead.search(m) for lead in elemental)
                and not (engr_repeat and _ENGR_LINES.search(m))
                and not peaceful_self_buff(m, before, snap)
                and not other_monster_killed(m, before, snap)
                and not self._heard_before(m, snap)]
        if msgs and not quiet:
            reasons.append("message")
        if cloud_news:
            reasons.insert(0, "POISON GAS CLOUD (bright green '#'): each turn in it blinds you for a turn"
                              + (" — harmless otherwise with your poison resistance; step out of it (it also "
                                 "hides monsters)" if self._poison_res() else
                                 " and BURNS YOUR LUNGS (rnd(dmg)+5 HP a turn without poison resistance) — "
                                 "get out now"))
        trapmsg = [m for m in snap.messages if self.game._TRAP_MSG.search(m)
                   and not m.startswith("There is")
                   # (the exec's own -a / ok patterns cover it: p2 shift 30's arrow traps in a trap-rich maze;
                   # the square is remembered all the same, and HP loss pauses on its own)
                   and not any(p.search(m) for p in self.autocontinue) and not any(p.search(m) for p in extra)]
        lt = getattr(self.game, "last_theft", None)
        back = self._thief_back(lt, snap, turn) if lt and getattr(snap, "theft_note", "") else None
        if lt and lt.get("msg") in snap.messages and getattr(snap, "theft_note", ""):
            reasons.insert(0, "THEFT — " + snap.theft_note)
        elif back and not any(p.search(back) for p in self.autocontinue) and not any(p.search(back) for p in extra):
            reasons.insert(0, back)
        if getattr(snap, "niche_note", ""):
            reasons.insert(0, "TRAPPED CLOSET — " + snap.niche_note)
        if getattr(snap, "room_note", ""):
            reasons.insert(0, "SPECIAL ROOM — " + snap.room_note)
        keys = getattr(self, "_last_keys", b"") or b""
        if len(keys) == 1 and chr(keys[0]) in "hjklyubn" and before is not None and before.state.kind == "command" \
                and any(re.match(r"^You (?:hit|miss|smite|kill|destroy) ", m) for m in snap.messages):
            # a plain move became an attack: something you couldn't see was there (an invisible monster,
            # a ghost/shade drawn as a blank, a hider) — the movement helpers never attack on purpose
            reasons.insert(0, "YOUR MOVE ATTACKED something you didn't see there (invisible? a hider? a ghost?) "
                              "— look before the next step (it may be peaceful)")
        if _moves_at_most_one(keys) and before is not None and before.hero is not None and snap.hero is not None \
                and before.state.kind == "command" and before.status.ok and snap.status.ok \
                and before.status.ldesc == snap.status.ldesc \
                and max(abs(snap.hero[0] - before.hero[0]), abs(snap.hero[1] - before.hero[1])) > 1 \
                and not getattr(snap, "engulfed", False) \
                and not any("position suddenly seems very uncertain" in m for m in snap.messages):
            # a step, a search or a rest that left you 2+ squares away: teleported WITHOUT A WORD — teleportitis
            # (eating a tengu/leprechaun/the Wizard) or an unseen teleport trap (p1 shift 37 #135/#263: go_down()
            # and tunnel() carried on from the new spot)
            reasons.insert(0, f"TELEPORTED without a word: {before.hero} -> {snap.hero} (teleportitis? a teleport "
                              "trap?) — any plan made before this is stale: look around first")
        if before is not None and before.hero is not None and snap.hero is not None and before.hero != snap.hero \
                and not keys.startswith(b","):
            # a step that auto-picked up something CURSED (pickup_thrown takes back what you threw, cursed or
            # not: p3 shift 12's 4 cursed daggers put the pack over the 600 squeeze limit)
            cursed = [m for m in snap.messages if re.match(r"^[a-zA-Z] - .*\bcursed\b", m)
                      and not re.search(r"\buncursed\b", m)]
            if cursed:
                reasons.insert(0, f"AUTOPICKUP took a CURSED item: {cursed[0]!r} — dead weight? drop it "
                                  f"(`d{cursed[0][0]}`) unless you want it")
        wn = getattr(snap, "wand_note", "")
        if wn:
            reason = wand_danger(wn, getattr(snap, "wand_kind", None), self.game)
            if reason:
                reasons.insert(0, reason)
        if any("position suddenly seems very uncertain" in m for m in snap.messages) \
                and not any("prevents you from teleporting" in m for m in snap.messages):
            reasons.insert(0, f"TELEPORTED by a monster's hit (quantum mechanic) — you are now at {snap.hero}")
        brush = next((m for m in snap.messages if re.search(r"brushes against your (?:left |right )?\w+\.$", m)), None)
        # mhitu.c AD_WRAP drowns only when the holder stands in water (is_pool at ITS square): with no water next
        # to you, a python's wrap only crushes (p2 shift 26: a python on land paused as a drowning attempt)
        wet = snap.hero is None or any(snap.screen.at(snap.hero[0] + dx, snap.hero[1] + dy) == "}"
                                       for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)
        if brush and wet and not any(re.search(r" swings itself around you!$", m) for m in snap.messages):
            # mhitu.c AD_WRAP: a failed wrap — the next one can hold you, and a hold in water drowns you
            reasons.insert(0, f"DROWNING ATTEMPT — {brush!r}: a sea monster (eel/kraken, maybe hidden under the "
                              "water) tried to wrap you. Step AWAY from the water now (to a square with no water "
                              "next to it); fight it only from there or at range")
        grab = next((m for m in snap.messages if re.search(r" swings itself around you!$", m)), None)
        if grab and wet:
            # mhitu.c AD_WRAP: held by an eel/kraken in water, its next wrap hit drowns you outright
            reasons.insert(0, f"HELD — {grab!r}: if it is in water, its NEXT hit DROWNS you (levitation does NOT "
                              "help). This turn: engrave Elbereth (E - Elbereth: it flees and lets go; impossible "
                              "while levitating), or kill it, or teleport away (not on the Castle)")
        gulps = [(i, re.match(r"^(?:The |An? )?(.+?) engulfs you!$", m)) for i, m in enumerate(snap.messages)]
        gulp_i, gulp = next(((i, g) for i, g in reversed(gulps) if g), (None, None))
        # mhitu.c gulpmu(): with slow digestion (or a huge form) the same turn ends "You get regurgitated!"
        # (/expelled) — out again, nothing to do (p1 shift 28: a trapper vs a ring of slow digestion)
        spat_out = gulp is not None and any(
            re.match(r"^You get (?:regurgitated|expelled)", m) or re.search(r" very hurriedly (?:regurgitates|"
                                                                            r"expels) you!$", m)
            for m in snap.messages[gulp_i + 1:])
        if gulp and not spat_out \
                and re.sub(r"^(?:invisible |tame |peaceful )+", "", gulp.group(1).lower()) in DIGESTERS:
            # mhitu.c gulpmu() AD_DGST: total digestion when u.uswldtim runs out (~25 - its level, halved,
            # + 10 - your AC turns); a wand of digging zapped from inside tears it open (zap.c zap_dig)
            hell = (self.game.level_key(snap.status) if snap.status.ok else "").startswith("Gehennom")
            reasons.insert(0, f"SWALLOWED by a {gulp.group(1)}: it DIGESTS you — death when its timer runs "
                              "out (roughly 10-30 turns, fewer with worse AC; 'thoroughly'/'utterly digests "
                              "you' = nearly done). From inside every blow hits: fight() now; a wand of digging "
                              "zapped any direction tears you out; "
                              + ("NO prayer in Gehennom" if hell else "prayer works at low HP if it's safe"))
        dig = next((m for m in snap.messages if re.search(r"(?:thoroughly |utterly )digests you!$", m)), None)
        if dig:
            reasons.insert(0, f"BEING DIGESTED — {dig!r}: " + ("the NEXT turn digests you totally (death): pray / "
                                                              "zap digging / kill it NOW" if "utterly" in dig
                                                              else "only a few turns left: kill it or zap digging"))
        stuck = next((m for m in snap.messages if re.match(r"^Wait!\s+That's (?:an? )?.*mimic!$", m)
                      or re.match(r"^You cannot escape from ", m)), None)
        if stuck and "stuck" not in expect:
            # uhitm.c stumble_onto_mimic() / hack.c domove(): a mimic's AD_STCK holds you (u.ustuck)
            reasons.insert(0, f"STUCK — {stuck!r}: you can't walk away while it holds you (teleporting works); "
                              "fight() it — fight() hits the holder first"
                              + (" (a giant mimic hits 3d6 twice)" if "mimic" in stuck else ""))
        hiss = next((m for m in snap.messages if re.match(r"^You hear (?:the |an? )?.+'s? hissing!$", m)), None)
        if hiss:
            # mhitu.c AD_STON: after the hiss, 1 in 10 (always at new moon without a lizard) starts stoning
            reasons.insert(0, f"COCKATRICE HISS — {hiss!r}: each hiss can start STONING (then 'You are slowing "
                              "down': eat a lizard/acidic corpse or pray at once). Kill it now or step away")
        if any(m.startswith("Your brain is eaten!") for m in snap.messages):
            # mhitu.c AD_DRIN / eat.c eat_brains(): with Int (base) at 3 a brain-eating hit KILLS, life
            # saving or not; each one costs 1-2 Int; a worn helmet stops 7 in 8
            iq = snap.status.in_ if snap.status.ok else 0
            reasons.insert(0, f"BRAIN EATEN (mind flayer) — Int now {iq or '?'}: "
                              + ("the NEXT brain-eating hit can KILL you" if iq and iq <= 4 else
                                 "at Int 3 the next one kills you")
                              + " (life saving doesn't help). Kill it at range, Elbereth, or get away NOW; a worn "
                                "helmet stops 7 in 8")
        if any(m.startswith(("You feel as if you need some help.", "You notice a black glow surrounding you",
                             "You feel a malignant aura surround you")) for m in snap.messages):
            # sit.c rndcurse() (mcastu.c MGC_CURSE_ITEMS; wizard.c intervene() after the Wizard's death): some
            # items are cursed now (fewer with MR: "malignant aura")
            sus = list(getattr(self.game, "unknown_buc", None) or [])
            reasons.insert(0, "CURSED ITEMS — a curse hit you: inventory() marks 'cursed' only on items whose "
                              "B/U/C you knew; the others may be cursed too (test on an altar, or watch for a "
                              "welded weapon / armor that won't come off; a cursed bag of holding loses items "
                              "when opened)" + (
                                  ". Suspects (B/U/C unknown at the last inventory()): " + ", ".join(sus[:14])
                                  + (f" (+{len(sus) - 14} more)" if len(sus) > 14 else "") if sus else
                                  ". Run inventory(): only the items without a B/U/C shown can have been hit"))
        if getattr(snap, "left_note", ""):
            reasons.insert(0, snap.left_note)
        if any(m.startswith("Your medallion ") or m.startswith("The medallion crumbles") for m in snap.messages):
            # end.c done(): you died and the amulet of life saving brought you back at full HP (Con -1)
            reasons.insert(0, "LIFE SAVED — you DIED and your amulet of life saving is used up (full HP now, Con -1): "
                              "put on a spare at once if you have one, and get away from what killed you")
        bash = next((m for m in snap.messages if m.startswith("You begin bashing monsters with ")), None)
        if bash:
            # uhitm.c: the first blow with something that isn't a proper weapon (a pick-axe applied to dig,
            # a lamp after #rub, a wand...)
            reasons.insert(0, f"NOT YOUR WEAPON — {bash!r}: wield your weapon again (w + its letter)")
        if any(re.match(r"^Suddenly, the .*guard disappears\.", m) for m in snap.messages):
            reasons.insert(0, "VAULT GUARD gone — his temporary corridor turns back into rock behind you as you "
                              "walk: keep walking out to the real corridor/room now (don't wait or go back in it)")
        if any(m.startswith("A mysterious force momentarily surrounds you") for m in snap.messages):
            reasons.insert(0, "MYSTERIOUS FORCE (you carry the Amulet): the climb failed — you were moved on this "
                              "level or sent down a few; climb again (1 in 4 climbs deep in the dungeon)")
        if trapmsg and snap.hero is not None and not quiet and not getattr(snap, "engulfed", False) \
                and "trap" not in expect:
            # (inside an energy vortex "your magical energy drain away" is its attack, not a magic trap)
            reasons.append(f"trap at {snap.hero}")
        if snap.state.kind == "getlin" and (snap.state.prompt or "").startswith("Call ") \
                and not (before is not None and before.state.kind == "getlin") \
                and not any(p.search(snap.state.prompt) for p in extra):      # a helper that answers it
            # e.g. a scroll of scare monster crumbled on pickup: the game asks you to name
            # the type; the script's next keys would be typed into this prompt
            reasons.append(f"naming prompt open: {snap.state.prompt!r} — type a name + <CR> or <Esc>")
        if snap.state.kind == "getlin" and "For what do you wish" in (snap.state.prompt or "") \
                and not (before is not None and before.state.kind == "getlin"):
            # never let a script type its next command into a wish; Esc/empty = a random object
            reasons.append("WISH PROMPT OPEN: answer ONLY with `cont --reply '<wish><CR>'` (PLAYBOOK §E, e.g. "
                           "'blessed +2 gray dragon scale mail<CR>'); Esc or an empty line gives a RANDOM object")
        if before is not None and before.status.ok and snap.status.ok:
            b, a = before.status, snap.status
            if a.hp < b.hp:
                loss, mx = b.hp - a.hp, max(1, a.hpmax)
                if self.fight_floor is not None:
                    floor = self.fight_floor * mx
                    if a.hp < floor or a.hp - 2 * loss < floor or loss >= 0.25 * mx:
                        reasons.append(f"HP {b.hp}->{a.hp}/{a.hpmax}" + (
                            f" (-{loss}: two more like that and you're below {self.fight_floor:.0%})"
                            if a.hp >= floor and loss < 0.25 * mx else ""))
                else:
                    big_hit = loss >= max(4, self.hp_hit_pause * mx)
                    low = a.hp < self.hp_pause * mx
                    if big_hit or low:
                        reasons.append(f"HP {b.hp}->{a.hp}/{a.hpmax}")
            new_conds = [c for c in a.conditions if c not in b.conditions
                         and not (c == "Blind" and in_cloud and not cloud_news)
                         and not (c == "Blind" and "blind" in expect)]
            if new_conds:
                reasons.append("status: +" + ",".join(new_conds)
                               + "".join(f" — {COND_HINTS[c]}" for c in new_conds if c in COND_HINTS))
            if a.cut and a.cut != b.cut:
                reasons.append(f"status line full: its last word '{a.cut}' may be cut short and a condition after "
                               f"it hidden (Stone/Slime/Strngl come first, so they show) — `do '^X'` lists them all")
            if _HUNGER_RANK.get(a.hunger, 0) > _HUNGER_RANK.get(b.hunger, 0):
                reasons.append(f"hunger: {a.hunger}")
            if _ENC_RANK.get(a.encumbrance or "", 0) > _ENC_RANK.get(b.encumbrance or "", 0) \
                    and "encumbrance" not in expect:
                # (a lighter load is never news; the item helpers take heavier loads themselves and say so)
                reasons.append(f"encumbrance: {a.encumbrance}")
            if a.ldesc != b.ldesc and "level" not in expect:
                reasons.append(f"level: {b.ldesc} -> {a.ldesc}")
            if a.xl != b.xl:
                reasons.append(f"XL {b.xl}->{a.xl}")
            if a.in_ and b.in_ and a.in_ < b.in_:
                reasons.append(f"Int {b.in_}->{a.in_}")
            if a.polymorphed != b.polymorphed or (a.polymorphed and a.hd != b.hd):
                reasons.append(f"polymorphed (HD:{a.hd}; own XL {a.xl})" if a.polymorphed
                               else "back in your own form")
        if self.pause_on_monsters and snap.state.kind == "command":
            if snap.monsters:
                new = [m for m in snap.monsters if m.get("new") and not m.get("statue")
                       and not m.get("tame") and not m.get("peaceful")]
                burst = [m for m in new if m.get("dist") is not None and m["dist"] <= 2 and m["ch"] != "~"]
                # (not when this step changed what you perceive: p1 shift 40 #248 — putting on a blindfold made
                # the invisible Wizard and a long worm's tail 'appear' through telepathy)
                sight = before is not None and before.status.ok and snap.status.ok \
                    and ("Blind" in snap.status.conditions) != ("Blind" in before.status.conditions)
                if len(burst) >= 3 and not sight:
                    # wizard.c nasty() / a demon gate / create monster: several monsters appear around you at once
                    # with no message (p2 shift 36 #389: a storm giant, umber hulk, silver dragon and Aleax)
                    how = next((m for m in snap.messages if re.search(
                        r"(?:zaps|reads) (?:a |an )?(?:wand|scroll) of create monster|zaps a .*wand!|"
                        r"reads a scroll|opens a gate|summons help|nasty", m, re.I)), None)
                    # (p2 shift 37 #185: an umber hulk's wand of create monster — name the source when it showed)
                    reasons.insert(0, f"SUMMONED: {len(burst)} monsters appeared right around you at once ("
                                      + ", ".join(m.get("desc") or m["ch"] for m in burst[:5])
                                      + (f") — {how!r}" if how else
                                         ") — the Wizard's summon nasties, a gate or a create monster")
                                      + ": get out (teleport, levelport, stairs; Elbereth doesn't stop @ or "
                                        "minotaurs) or fight from a corridor")
                if new and self.new_monster_filter is not None:
                    try:
                        new = [m for m in new if self.new_monster_filter(m)]
                    except Exception as e:  # noqa: BLE001 — a broken filter must not hide monsters
                        reasons.append(f"monster_filter error: {e!r}")
                new = self._not_yet_announced(new, snap)
                crowd = [m for m in snap.monsters if not m.get("statue") and not m.get("tame")
                         and not m.get("peaceful")]
                level = snap.status.ldesc if snap.status.ok else ""

                blind = snap.status.ok and "Blind" in snap.status.conditions

                def far(m):
                    d = m.get("dist")
                    # (a sea monster ';' can't leave its water: far off it waits like any other, note or not;
                    # while you are BLIND telepathy shows the whole level: a noted monster far off waits too,
                    # pausing as 'approaching' when it comes near — p1 shift 27: Orcus Town's vampire lords
                    # 50 squares off paused every blow)
                    if d is None or (m.get("note") and m.get("ch") != ";"
                                     and not (blind and d > self.DEFER_NEAR)):
                        return False
                    # a big lit room reveals a crowd a few at a time; telepathy senses a whole level
                    # (a sleeping court 30 squares off): those are news only when they come near
                    return (d > self.DEFER_NEAR and (len(crowd) > 8 or blind
                                                     or "[seen: telepathy" in (m.get("desc") or "")
                                                     or "[seen: warned" in (m.get("desc") or ""))) \
                        or (self.defer_dist is not None and d > self.defer_dist)
                later = [m for m in new if far(m)]
                near_at = self.defer_dist if self.defer_dist is not None else self.DEFER_NEAR
                for m in later:
                    if m.get("id") is not None:
                        self._deferred[m["id"]] = {"level": level, "pos": (m["x"], m["y"]), "near": near_at,
                                                   "ch": m.get("ch")}
                new = [m for m in new if m not in later]
                # the exec's -a patterns may name monster pauses too (p3 shift 18: -a 'approaching: killer bee')
                new = [m for m in new if not self._autocontinued(f"new monster: {m.get('desc') or m['ch']}")]
                if new:
                    reasons.append("new monster: " + ", ".join(
                        f"{m.get('desc') or m['ch']} at ({m['x']},{m['y']})" for m in new[:4])
                        + (f" +{len(new) - 4} more (`bin/nh obs` lists all)" if len(new) > 4 else ""))
                if self._deferred:
                    for i in [i for i, v in self._deferred.items() if v["level"] != level]:
                        del self._deferred[i]
                    near = []
                    # every square a watched monster stood on at the last look: in a crowd of one glyph (29
                    # sleeping killer bees, p3 shift 18 #448-#483) the tracker's ids can swap between them, so
                    # "moved" is judged by squares — a monster on a watched square of its glyph didn't move
                    was_at = {(v["pos"], v.get("ch")) for v in self._deferred.values() if v["level"] == level}
                    for m in snap.monsters:
                        v = self._deferred.get(m.get("id"))
                        if v is None or m.get("new") or m.get("dist") is None or m.get("tame") \
                                or m.get("peaceful"):
                            continue
                        pos, v["pos"] = v["pos"], (m["x"], m["y"])
                        # inside a defer_far(n) block a monster deferred before it (the telepathy/crowd default,
                        # 6) waits until it is within n too (p3 shift 16 #528: pauses at d=5-6 under defer_far(3));
                        # an explicit watch_monsters() keeps its own distance
                        lim = v["near"] if self.defer_dist is None or v.get("watch") else min(v["near"],
                                                                                              self.defer_dist)
                        if m["dist"] > lim or (m["x"], m["y"]) == pos or ((m["x"], m["y"]), m.get("ch")) in was_at \
                                or ((m["x"], m["y"]), None) in was_at:
                            continue         # still far, or it didn't move: only you came closer (a sleeper)
                        if self._autocontinued(f"approaching: {m.get('desc') or m['ch']}"):
                            del self._deferred[m["id"]]
                            continue
                        del self._deferred[m["id"]]
                        if self.new_monster_filter is not None:
                            try:
                                if not self.new_monster_filter(m):
                                    continue
                            except Exception:  # noqa: BLE001 — a broken filter must not hide monsters
                                pass
                        near.append(m)
                    if near:
                        reasons.append("approaching: " + ", ".join(
                            f"{m.get('desc') or m['ch']} at ({m['x']},{m['y']}) d={m['dist']}" for m in near[:4]))
            elif before is not None and before.state.kind == "command" and self.game.tracker is None:
                prev = monster_counts(before)
                now = monster_counts(snap)
                new = [f"{ch}" for (ch, col, rev), n in now.items() if n > prev.get((ch, col, rev), 0) and not rev]
                if new:
                    reasons.append("new monster in view: " + ",".join(sorted(set(new))))
        if reasons:
            self._maybe_pause("; ".join(reasons), snap)

    def _thief_back(self, lt: dict, snap: Snap, turn: int) -> str | None:
        """The thief coming back into view (p4 shift 3 #1386: the nymph returned at d=9, not "new", no pause):
        once per return. Only map snapshots count (live shift 10 #1661-#1669: a menu covering the map made the
        thief "come back" after every inventory() — each exec paused at once), and a thief out of sight for a
        turn or two (a corner, a doorway) hasn't left."""
        if snap.state.kind != "command" or snap.monsters is None:
            return None
        from .danger import base_name
        thief = base_name(re.sub(r"^(?:The|the) ", "", lt.get("who") or ""))
        if not thief or thief.lower() in ("she", "he", "it", "someone"):
            return None
        now = [m for m in snap.monsters if base_name(m.get("desc") or "") == thief
               and not m.get("tame") and not m.get("peaceful") and not m.get("statue")]
        key = (lt.get("turn"), lt.get("msg"))
        view = getattr(self, "_thief_view", None)
        if view is None or view["key"] != key:
            view = self._thief_view = {"key": key, "in_view": False, "last": lt.get("turn") or turn}
        if lt.get("msg") in snap.messages:          # the theft itself (its own pause)
            view.update(in_view=bool(now), last=turn)
            return None
        if not now:
            view["in_view"] = False
            return None
        returned = not view["in_view"] and turn - (view["last"] or 0) > 2
        view.update(in_view=True, last=turn)
        if not returned:
            return None
        return (f"THIEF BACK in view: the {thief} at ({now[0]['x']},{now[0]['y']}) — it stole {lt.get('what')} at "
                f"T:{lt.get('turn')}: kill it to get it back (at range if you can: it steals again and teleports "
                "off), or keep away")

    def _heard_before(self, m: str, snap: Snap) -> bool:
        """A ONCE_PER_LEVEL noise already paused for on this level (and, with poison resistance, the
        gas-cloud cough)."""
        for i, p in enumerate(ONCE_PER_LEVEL):
            if p.search(m):
                key = (snap.status.ldesc if snap.status.ok else "", i)
                if key in self._heard:
                    return True
                self._heard.add(key)
                return False
        if _CLOUD.search(m) and self._poison_res():
            key = (snap.status.ldesc if snap.status.ok else "", "cloud")
            if key in self._heard:
                return True
            self._heard.add(key)
        return False

    def _poison_res(self) -> bool:
        return "poison" in (getattr(self.game, "intrinsics", None) or ())

    DEFER_NEAR = 6       # a deferred far newcomer pauses when it comes this close

    SWARM_TURNS = 5      # another member of a species announced this recently...
    SWARM_DIST = 4       # ...and this close to its group doesn't pause again (bee swarms, orc packs)

    def _not_yet_announced(self, new: list, snap: Snap) -> list:
        """Drop newcomers of a species that paused within SWARM_TURNS turns
        and that turn up within SWARM_DIST squares of that group (as then
        announced or now in view): a swarm pauses once, not once per bee."""
        from .danger import base_name
        turn = snap.status.turn if snap.status.ok else None
        level = snap.status.ldesc if snap.status.ok else ""

        def species(m):
            return base_name(m.get("desc") or "") or f"{m['ch']}/{m.get('color')}"
        fresh = []
        for m in new:
            rec = self._announced.get(species(m))
            if rec and turn is not None and rec["level"] == level and 0 <= turn - rec["turn"] <= self.SWARM_TURNS:
                group = rec["cells"] + [(o["x"], o["y"]) for o in snap.monsters or []
                                        if o is not m and species(o) == species(m)]
                if any(max(abs(m["x"] - x), abs(m["y"] - y)) <= self.SWARM_DIST for x, y in group):
                    continue
            fresh.append(m)
        if turn is not None:
            for m in fresh:
                cells = [(o["x"], o["y"]) for o in snap.monsters or [] if species(o) == species(m)]
                self._announced[species(m)] = {"turn": turn, "level": level, "cells": cells}
        return fresh

    def _autocontinued(self, reason: str) -> bool:
        """Does one of the exec's -a patterns match this monster pause reason ('new monster: X' /
        'approaching: X')? Only monster reasons: HP, status and prompt pauses always stop."""
        return any(p.search(reason) for p in self.autocontinue)

    def _maybe_pause(self, reason: str, snap: Snap, force: bool = False, sent: bool = True) -> None:
        if not self.in_worker():
            return
        try:
            snap.paused = reason       # helpers: the player has seen this step (don't stop again for it)
        except Exception:  # noqa: BLE001
            pass
        if self.activity:
            reason = f"{reason}  [during: {self.activity}]"
        where = _user_frames()
        self.events.put(("paused", PauseInfo(reason=reason, snap=snap, where=where)))
        self.resume.clear()
        self.parked = True
        try:
            self.resume.wait()
        finally:
            self.parked = False
        if self.abandon_flag:
            raise Abandon()
        # reset budget on every resume
        self._steps = 0
        self._t0 = time.monotonic()
        if self._pending_reply is not None:
            r, self._pending_reply = self._pending_reply, None
            try:
                snap2 = self.game.step(parse_keys(r))
            except PermissionError as e:
                # a guard refused the reply (Esc at a wish): the prompt is still open — stay paused
                # there so the right answer can still go through `cont --reply`
                self._maybe_pause(f"your reply {r!r} was REFUSED: {e} — the prompt is still open; answer again "
                                  "with cont --reply", self.game.last or snap, force=True)
                return
            self.ns["obs"] = snap2
            self._reply_sent = parse_keys(r)

    # ---------------------------------------------------------- exec api
    def busy(self) -> bool:
        return self.worker is not None and self.worker.is_alive()

    def start_exec(self, code: str, autocontinue: list[str] | None = None,
                   monsters: bool = True, hp_pause: float | None = None, at_prompt: bool = False) -> dict:
        cur = self.game.last
        if cur is not None and cur.state.kind not in ("command", "gameover", "dgl", "unknown") and not at_prompt:
            # a script's first command key would be typed into the open prompt ("What do you want to
            # drop?" + 's' drops item s); a paused exec there stays paused
            where = " — an exec is PAUSED there: answer with `nh cont --reply KEYS`" if self.busy() else \
                " — answer or <Esc> it with `nh do KEYS`"
            return {"status": "error", "stdout": "",
                    "error": f"the game is at a {cur.state.kind} prompt ({cur.state.prompt!r}){where}, then "
                             "exec again (or `exec --at-prompt` if your script answers it first)"}
        dropped = self.drop()
        self.autocontinue = [re.compile(p) for p in (autocontinue or [])]
        self.pause_on_monsters = monsters
        self.new_monster_filter = None
        self.activity = ""
        self._reply_sent = None
        if self.game.last is None:
            try:
                self.game.look()           # after a daemon restart: `obs` must not be None
            except Exception:  # noqa: BLE001
                pass
        self.ns["obs"] = self.game.last
        self.hp_pause = 0.7 if hp_pause is None else float(hp_pause)
        self.code_counter += 1
        fname = f"<exec-{self.code_counter}>"
        linecache.cache[fname] = (len(code), None, code.splitlines(True), fname)
        try:
            compiled = compile(code, fname, "exec")
        except SyntaxError as e:
            return {"status": "error", "error": f"SyntaxError: {e}", "stdout": ""}
        self.abandon_flag = False
        self.events = queue.Queue()
        self._steps = 0
        self._t0 = time.monotonic()
        buf = io.StringIO()
        if dropped:
            buf.write("(note: the paused exec was dropped — whatever it had left to do, e.g. a helper's "
                      "re-wield, won't happen)\n")

        def run():
            self._stdout.buffers[threading.get_ident()] = buf
            try:
                result = None
                exec(compiled, self.ns)
                result = self.ns.pop("_result", None)
                self.events.put(("done", {"result": result}))
            except Abandon:
                self.events.put(("abandoned", {}))
            except BaseException as e:  # noqa: BLE001
                tb = traceback.format_exc(limit=8)
                self.events.put(("error", {"error": f"{type(e).__name__}: {e}", "traceback": tb}))
            finally:
                self._stdout.buffers.pop(threading.get_ident(), None)

        self._buf = buf
        self.worker = threading.Thread(target=run, name="nh-exec", daemon=True)
        self.worker.start()
        return self._wait()

    def cont(self, reply: str | None = None, autocontinue: list[str] | None = None) -> dict:
        if not self.busy():
            return {"status": "error", "error": "nothing is paused", "stdout": ""}
        if autocontinue is not None:
            self.autocontinue = [re.compile(p) for p in autocontinue]
        self._pending_reply = reply
        self.resume.set()
        return self._wait()

    def _wait(self) -> dict:
        while True:
            try:
                kind, info = self.events.get(timeout=0.5)
            except queue.Empty:
                if not self.worker.is_alive():
                    kind, info = "error", {"error": "worker died"}
                else:
                    continue
            out = self._buf.getvalue()
            self._buf.seek(0)
            self._buf.truncate()
            if kind == "paused":
                return {"status": "paused", "reason": info.reason, "snap": info.snap,
                        "where": info.where, "stdout": out}
            if kind == "done":
                self.worker = None
                return {"status": "done", "result": info.get("result"), "stdout": out,
                        "snap": self.game.last}
            if kind == "abandoned":
                self.worker = None
                return {"status": "abandoned", "stdout": out, "snap": self.game.last}
            self.worker = None
            return {"status": "error", "error": info.get("error"), "traceback": info.get("traceback", ""),
                    "stdout": out, "snap": self.game.last}

    def drop(self) -> str:
        """Abandon a paused exec, if any."""
        if not self.busy():
            self.worker = None
            return ""
        self.abandon_flag = True
        self.resume.set()
        self.worker.join(timeout=10)
        self.worker = None
        # drain
        while not self.events.empty():
            try:
                self.events.get_nowait()
            except queue.Empty:
                break
        return "dropped paused exec"

    # direct (non-exec) step used by `nh do`
    def direct_do(self, keys: str, force: bool = False, multi: bool = False) -> Snap:
        self.drop()
        data = parse_keys(keys)
        _guard_dangerous(data, force)
        snap = self.game.step(data, multi=multi, force=force)
        self.ns["obs"] = snap
        return snap


_DANGEROUS = [
    (re.compile(rb"#\s*quit", re.I), "#quit ends the game"),
    (re.compile(rb"\x1bq"), "M-q is #quit"),
    (re.compile(rb"^\xf1"), "M-q is #quit"),
]


def _guard_dangerous(data: bytes, force: bool) -> None:
    if force:
        return
    for rx, why in _DANGEROUS:
        if rx.search(data):
            raise PermissionError(f"refusing to send {data!r}: {why}. Pass force=True if you really mean it.")


_SRC: dict[str, list[str]] = {}    # helper sources as loaded (realpath -> lines)


def snapshot_sources() -> None:
    """Remember the tactics sources as they are when (re)loaded, so pause
    traces quote the code that is running, not a file edited since."""
    import glob
    import os
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "play", "tactics")
    for p in glob.glob(os.path.join(root, "*.py")):
        try:
            with open(p) as f:
                _SRC[os.path.realpath(p)] = f.read().splitlines()
        except OSError:
            pass


def _user_frames() -> list[dict]:
    import os
    frames = []
    for fs in traceback.extract_stack()[:-2]:
        if fs.filename.startswith("<exec-") or "/tactics/" in fs.filename:
            lines = _SRC.get(os.path.realpath(fs.filename)) if not fs.filename.startswith("<") else None
            code = lines[fs.lineno - 1] if lines and 0 < fs.lineno <= len(lines) else (fs.line or "")
            frames.append({"file": fs.filename, "line": fs.lineno, "code": code.strip()})
    return frames[-6:]
