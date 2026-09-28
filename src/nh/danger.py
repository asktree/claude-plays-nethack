"""Monster danger notes: what kills players, keyed by monster name.

Used to annotate the auto-farlooked monster list so the player sees the
special threat next to the monster, e.g. "floating eye  !! NEVER melee".
Notes are short and actionable; details live in knowledge/wiki.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

NOTES = {
    "floating eye": "NEVER melee (paralysis -> death). Ranged only, or ignore. Corpse = telepathy.",
    "cockatrice": "touch/hiss -> stoning. Never touch or eat its corpse; fight with a weapon, never bare-handed.",
    "fire elemental": "its fire burns scrolls, potions and spellbooks in your open pack (fire resistance saves "
                      "you, not them: bag them) and your cloak.",
    "chickatrice": "touch/hiss -> stoning. Never touch or eat its corpse; fight with a weapon.",
    "gas spore": "EXPLODES when killed (4d6 to adjacent). Kill at range or walk away.",
    "green slime": "touch -> SLIMING. Kill at range; carry fire/polymorph cure.",
    "soldier ant": "fast, bite + poison sting; deadly early. Elbereth/fight at a chokepoint.",
    "fire ant": "fast, fire damage; burns scrolls/potions.",
    "killer bee": "poisonous swarm; poison can kill outright without poison resistance.",
    "leprechaun": "steals gold and teleports.",
    "water nymph": "steals an item and teleports. Kill fast or keep away.",
    "wood nymph": "steals an item and teleports. Kill fast or keep away.",
    "mountain nymph": "steals an item and teleports. Kill fast or keep away.",
    "werejackal": "bite -> LYCANTHROPY (pray / holy water / wolfsbane).",
    "wererat": "bite -> LYCANTHROPY (pray / holy water / wolfsbane).",
    "werewolf": "bite -> LYCANTHROPY (pray / holy water / wolfsbane).",
    "giant eel": "can DROWN you when you stand next to water: once it 'swings itself around you' its NEXT hit "
                 "drowns you (levitation does NOT help) — engrave Elbereth at once (it flees and lets go), kill "
                 "it, or teleport. Keep 2 squares from the water where eels are.",
    "electric eel": "shock bite; can DROWN you like a giant eel once it 'swings itself around you' (levitation "
                    "does NOT help) — Elbereth at once, kill it, or teleport. Keep away from the water's edge.",
    "kraken": "can DROWN you once it 'swings itself around you' (levitation does NOT help) — Elbereth at once, "
              "kill it, or teleport. Keep 2 squares from the water.",
    "shark": "hits hard from water; stay off the water edge.",
    "mind flayer": "EATS YOUR BRAIN: 3 tentacles a turn; each hit a worn helmet doesn't stop (it stops 7 in 8) "
                   "costs 1-2 Int and some memory, and with Int at 3 the next one KILLS you (life saving doesn't "
                   "help). Flies, fast. Kill it at range or flee; never melee it helmetless or with Int <= 6.",
    "master mind flayer": "EATS YOUR BRAIN: FIVE tentacles a turn; each hit a worn helmet doesn't stop (it stops "
                          "7 in 8) costs 1-2 Int, and with Int at 3 the next one KILLS you (life saving doesn't "
                          "help). Kill it at range or flee; never melee it helmetless or with Int <= 6.",
    "lich": "spellcaster (level 11+): curses items, destroys armor (MR stops that), weakens (Str), stuns; cold "
            "touch; regenerates. Kill fast.",
    "demilich": "spellcaster (level 14+): curses items, destroys armor (MR stops that), aggravates, stuns; "
                "cold touch. Kill fast.",
    "master lich": "powerful caster: SUMMONS NASTIES, curses items, destroys armor; a high-level one casts "
                   "TOUCH OF DEATH (MR stops it). Covetous: wants the Book of the Dead — follows you, teleports "
                   "off to heal.",
    "arch-lich": "deadliest caster: TOUCH OF DEATH without MR, summons nasties, curses, destroys armor, hastes "
                 "itself. Needs MR. Covetous: wants the Book of the Dead — follows you, teleports off to heal.",
    "disenchanter": "each hit drains +1 from a worn piece of POSITIVELY enchanted armor (or a ring); hitting it "
                    "drains your weapon's positive enchantment — but Excalibur (drain-resistant) and gear at +0 or "
                    "less can't be drained (zap.c drain_item). Kill it at range, or melee with Excalibur.",
    "rust monster": "no HP damage. Its touches rust iron armor (a worn cloak covers body armor; helmet, shield, "
                    "gloves, boots can rust); hitting it rusts an iron weapon unless rustproof (a fountain "
                    "Excalibur is). Eats metal off the floor.",
    "gremlin": "AT NIGHT (game clock 22:00-05:59, the server's local time) its claw can STEAL AN INTRINSIC "
               "(speed, poison/fire/cold res, telepathy...): kill it asleep or at range. Multiplies in water "
               "and fountains.",
    "gelatinous cube": "PARALYSING touch (2d4 turns) and passive PARALYSIS if you hit it in melee; eats "
                       "objects off the floor. Kill it at range (or with free action); never melee it with "
                       "hostiles around.",
    "blue jelly": "passive cold (you are cold resistant).",
    "spotted jelly": "passive acid corrodes weapon.",
    "ochre jelly": "passive/active acid.",
    "yellow light": "explodes -> long blindness. Kill at range.",
    "black light": "explodes -> hallucination. Kill at range.",
    "chameleon": "shapeshifts into random monsters.",
    "owlbear": "grabs and crushes.",
    "Medusa": "GAZE = STONING. Need reflection or be blind. Never look without protection.",
    "minotaur": "IGNORES Elbereth; hits very hard. Scare monster scroll works.",
    "soldier": "may carry attack WANDS (even death). Stay off straight lines.",
    "sergeant": "may carry attack WANDS (even death). Stay off straight lines.",
    "lieutenant": "may carry attack WANDS (even death). Stay off straight lines.",
    "captain": "may carry attack WANDS (even death). Stay off straight lines.",
    "vampire": "LEVEL DRAIN bite; regenerates; shape-shifts (fog cloud, vampire bat): killing that form makes it "
               "rise again as the vampire at full HP (mon.c pickvampshape).",
    "Nazgul": "LEVEL DRAIN weapon hit; SLEEP BREATH ray (without sleep resistance you fall asleep and everything "
              "gets free hits — reflection bounces it); carries a cursed ring of invisibility.",
    "vampire lord": "LEVEL DRAIN bite; regenerates; shape-shifts (fog cloud, vampire bat, WOLF): killing that "
                    "form raises the vampire lord at full HP next to you.",
    "Vlad the Impaler": "LEVEL DRAIN bite; strong, very fast (26). Carries the CANDELABRUM (needed to win); "
                        "covetous: teleports next to you, hits, teleports off to heal — hold your square: "
                        "fight_until_clear(radius=3, hold=30, unseen=True) fights him each time he comes back "
                        "(a light doesn't help). Shape-shifts only once he has lost "
                        "the Candelabrum. NO corpse: the Candelabrum drops on his square (pickup('Candelabrum')).",
    "wraith": "LEVEL DRAIN touch. Its corpse gives a level.",
    "barrow wight": "level drain weapon, spells.",
    "nurse": "harmless if you are unarmed & unarmored (heals you); otherwise just a nuisance.",
    "quantum mechanic": "hit teleports you.",
    "tengu": "teleports; bites.",
    "homunculus": "sleep bite (you lack sleep resistance).",
    "giant mimic": "sticks to you; hits hard.",
    "large mimic": "sticks to you.",
    "purple worm": "ENGULFS AND DIGESTS (instadeath). Kill at range / escape.",
    "trapper": "engulfs and digests. Don't stand still in unknown rooms.",
    "lurker above": "engulfs and digests.",
    "energy vortex": "engulf: shock, drains energy.",
    "steam vortex": "engulf: fire.",
    "fire vortex": "engulf: fire, burns items.",
    "ice vortex": "engulf: cold (you resist).",
    "dust vortex": "engulf: blindness.",
    "fog cloud": "engulf; harmless by itself — BUT a vampire can take this shape (3.6): killing it makes it "
                 "rise as a VAMPIRE (level drain). Around vampires / Vlad's / Gehennom treat it as one.",
    "vampire bat": "poisonous bite — and a vampire can take this shape (3.6): killing it makes it rise as a "
                   "VAMPIRE (level drain). Around vampires / Vlad's / Gehennom treat it as one.",
    "incubus": "SEDUCES: takes off your armor/cloak/rings — a ring of LEVITATION over water/lava = death — "
               "can take gold, drain levels/attributes. Kill it at range or before it reaches you; answer n "
               "to 'remove your ...?' prompts.",
    "succubus": "SEDUCES: takes off your armor/cloak/rings — a ring of LEVITATION over water/lava = death — "
                "can take gold, drain levels/attributes. Kill it at range or before it reaches you; answer n "
                "to 'remove your ...?' prompts.",
    "umber hulk": "CONFUSING gaze (you stumble at random — deadly next to water/lava/traps); digs through "
                  "walls. Fight it away from water/lava, or blindfolded.",
    "couatl": "grabs and crushes; poisonous bite; flies.",
    "horned devil": "hits hard (4 attacks).",
    "Elvenking": "fast elven lord, often with a strong weapon; sleep resistant; hits hard.",
    "nalfeshnee": "spellcaster; hits hard.",
    "pit fiend": "strong: two weapon hits (4d2 each) and a crushing hug that holds you; no spells.",
    "balrog": "very strong; bullwhip + broadsword; flies.",
    "ice devil": "cold (you resist) + slowing sting.",
    "barbed devil": "grabs; hits hard.",
    "cockatrice corpse": "never touch without gloves.",
    "Death": "RIDER. Touch of death. Avoid.",
    "Pestilence": "RIDER. Illness. Avoid.",
    "Famine": "RIDER. Hunger. Avoid.",
    "Wizard of Yendor": "covetous: steals the Amulet, the Bell, the Candelabrum, the Book or your quest "
                        "artifact, then teleports off to heal; casts touch of death (MR stops it), summon nasties, "
                        "curses, destroy armor, double trouble (clones himself). Comes back after being killed. "
                        "In his tower he WAITS until he SEES you or is hurt — waking him (a whistle, a squeaky "
                        "board) is not enough (mon.c: uniques keep waiting); open a sightline into his room, in "
                        "his row or column (no diagonal gaps). "
                        "Keep MR, reflection and uncursing ready; kill him fast.",
    "Lord Surtur": "QUEST NEMESIS (fire giant king): 2d10 weapon x2 and fire (you need fire resistance on his "
                   "lava level); his claw STEALS the Orb of Fate / the Amulet and he TELEPORTS away to heal (often "
                   "to the up stairs), then comes back; he carries the Bell of Opening (needed to ascend).",
    "Juiblex": "engulf -> illness, sliming risk. Fire kills slime.",
    "Orcus": "wand of death, spells. MR required.",
    "Asmodeus": "cold (you resist), spells.",
    "Baalzebub": "poison bite.",
    "Yeenoghu": "confusion, paralysis, magic missiles.",
    "Demogorgon": "extremely deadly: disease, drain. Avoid.",
    "black dragon": "DISINTEGRATION breath: need reflection or disint. resistance.",
    "silver dragon": "cold breath (you resist).",
    "red dragon": "fire breath.",
    "blue dragon": "lightning breath (blinds, destroys rings/wands).",
    "green dragon": "poison breath.",
    "yellow dragon": "acid breath.",
    "orange dragon": "sleep breath (you lack sleep resistance).",
    "white dragon": "cold breath (you resist).",
    "gray dragon": "magic missile breath.",
    "hill giant": "throws boulders.",
    "stone giant": "throws boulders.",
    "ettin": "hits very hard.",
    "troll": "revives after death; eat/tin its corpse or keep it off the floor.",
    "Olog-hai": "revives; hits hard.",
    "rock troll": "revives.",
    "ice troll": "revives.",
    "water troll": "revives.",
    "xorn": "phases through walls.",
    "Master of Thieves": "steals.",
    "dwarf": "hostile ones hit hard (mattock d12) early; as a dwarf most Mines dwarves are peaceful.",
    "dwarf lord": "hits hard with mattock early.",
    "hill orc": "comes in packs.",
    "Uruk-hai": "packs.",
    "giant beetle": "strong bite early.",
    "leocrotta": "fast, 3 attacks; dangerous mid-early.",
    "cobra": "poison + blinding spit.",
    "water moccasin": "poisonous.",
    "pit viper": "poisonous.",
    "python": "crushes.",
    "scorpion": "poison sting; corpse gives poison res.",
    "giant spider": "fast, strong poison. Dangerous below XL10.",
    "cave spider": "harmless nuisance.",
    "centipede": "poisonous.",
    "rotting corpse": "",
    "ghost": "slow but hard to hit; blocks corridors.",
    "shade": "only silver/blessed hurts; paralysis? touch can remove speed.",
    "Angel": "strong, spellcaster; don't anger peaceful ones.",
    "aligned priest": "temple priest: clerical spells (summons insects, paralysis without MR, lightning, fire "
                      "pillar, curses items) and a 4d10 weapon; hitting it while YOU stand in its temple (door "
                      "included) may call its god's lightning — reflection stops the damage, not the BLINDING "
                      "flash. Fight it from outside the temple (it won't leave it) or blindfolded with telepathy.",
    "high priest": "SANCTUM BOSS / Astral temple priest: clerical spells (summons insects, paralysis without MR, "
                   "lightning, fire pillar, curses items), 4d10 weapon + kick; hitting it while YOU stand in its "
                   "temple (door included) may call its god's lightning — reflection stops the damage, not the "
                   "BLINDING flash: fight from outside the temple (it stays inside), or blindfolded with "
                   "telepathy, unicorn horn ready. It carries the Amulet (Sanctum).",
    "jabberwock": "4 attacks up to 2d10 each (~80 a turn at worst), flies: fight it at full HP or at range.",
    "zruty": "hits hard (3 attacks, up to ~42 a turn) but slow (speed 8): you can walk away from it.",
    "baluchitherium": "hits hard (two 5d4 claws, ~40 a turn).",
    "xan": "leg sting: WOUNDED LEGS (can't kick; lower carrying capacity) — fast (18) and flies; kill it quickly.",
    "storm giant": "hits hard (2d12 weapon, level 16), throws boulders; shock resistant.",
    "shopkeeper": "NEVER anger (very strong).",
    "watchman": "Minetown Watch: don't anger (no fountain dipping/quaffing, no door breaking, no theft).",
    "watch captain": "Minetown Watch: don't anger.",
}

# notes that inform but don't by themselves make a monster 'dangerous' in threat_level() (packs,
# nuisances, thieves, slow hard hitters): its level and worst-case damage vs you decide
INFO_NOTES = {"hill orc", "Uruk-hai", "dwarf", "dwarf lord", "leprechaun", "chameleon", "tengu", "cave spider",
              "ghost", "xorn", "hill giant", "stone giant", "giant beetle", "owlbear", "leocrotta",
              "ettin", "troll", "rock troll", "ice troll", "water troll", "Olog-hai", "python", "rust monster",
              "blue jelly", "nurse", "rotting corpse", "Master of Thieves", "water moccasin", "centipede",
              "scorpion", "pit viper", "large mimic", "giant mimic", "ice vortex", "dust vortex",
              "zruty", "baluchitherium", "storm giant"}

# player-monsters ("wizard called Kevin the Sorcerer"): on the Astral Plane they are level 15-30 with a
# +4..+8 weapon, half the time an ARTIFACT, good armor and sometimes wands (mplayer.c mk_mplayer special)
PLAYER_MONSTERS = {"archeologist", "barbarian", "caveman", "cavewoman", "healer", "knight", "monk", "priest",
                   "priestess", "rogue", "ranger", "samurai", "tourist", "valkyrie", "wizard"}
PLAYER_MONSTER_NOTE = ("player-monster: on the Astral Plane level 15-30 with a +4..+8 weapon (half the time an "
                       "ARTIFACT), good armor, maybe wands; don't let several gang up on you.")
# role.c rank titles: do_name.c names a player monster OUTSIDE the endgame by its rank ("wayfarer", "enchanter"),
# and outside the endgame those are nearly always a DOPPELGANGER's shapes (mon.c select_newcham_form(): 4 in 7 of
# its changes pick a player-monster form) — p2 shift 33 met one as "enchanter" / "wayfarer" with no note
_RANKS = {
    "archeologist": "digger field worker investigator exhumer excavator spelunker speleologist collector curator",
    "barbarian": "plunderer plunderess pillager bandit brigand raider reaver slayer chieftainess "
                 "conqueror conqueress",
    "caveman": "troglodyte aborigine wanderer vagrant wayfarer roamer nomad rover pioneer",
    "healer": "rhizotomist empiric embalmer dresser medicus_ossium medica_ossium herbalist magister magistra "
              "physician chirurgeon",
    "knight": "gallant esquire bachelor banneret chevalier chevaliere seignieur dame paladin",
    "monk": "candidate novice initiate student_of_stones student_of_waters student_of_metals student_of_winds "
            "student_of_fire",
    "priest": "aspirant adept curate canon canoness lama patriarch matriarch",
    "rogue": "footpad cutpurse pilferer robber burglar filcher magsman magswoman thief",
    "ranger": "tenderfoot lookout trailblazer reconnoiterer reconnoiteress scout arbalester archer sharpshooter "
              "marksman markswoman",
    "samurai": "hatamoto ronin kunoichi joshu ryoshu kokushu daimyo kuge shogun",
    "tourist": "rambler sightseer excursionist peregrinator peregrinatrix traveler journeyer voyager explorer "
               "adventurer",
    "valkyrie": "stripling skirmisher fighter man-at-arms woman-at-arms swashbuckler hero heroine champion "
                "lord lady",
    "wizard": "evoker conjurer thaumaturge magician enchanter enchantress sorcerer sorceress necromancer mage",
}
# (left out: titles that are also monsters — the quest guardians chieftain, acolyte, warrior; sergeant, ninja,
# high priest — and the role names themselves, which PLAYER_MONSTERS covers)
RANK_TITLES = {t.replace("_", " "): role for role, ts in _RANKS.items() for t in ts.split()}
RANK_TITLE_NOTE = ("a player-monster form ({role}): outside the Astral Plane almost always a DOPPELGANGER in disguise "
                   "(it changes shape at random, often into something nastier — kill it quickly); on the Astral "
                   "Plane a real one: " + PLAYER_MONSTER_NOTE)
# damage types of poisonous active attacks (mhitu.c AD_DRST/DRDX/DRCO -> poisoned(): Str/Dex/Con loss, or
# death outright 1 time in 30 without poison resistance)
POISON_AD = ("AD_DRST", "AD_DRDX", "AD_DRCO")
POISON_NOTE = ("poisonous: without poison resistance each poisoned hit costs Str/Dex/Con — or kills outright "
               "(1 in 30); fight it at range or with poison resistance")
LEADER_NOTE = ("QUEST LEADER: never attack. Walking NEXT to it is your visit — go only at XL14+ and piously "
               "aligned (alignment record 20+: check with a stethoscope on yourself, piety()): each visit with a "
               "lower record counts, and after 7 you're expelled for good (no Bell = no ascension)")
LEADER_GIVEN_NOTE = ("QUEST LEADER: never attack. The quest is ASSIGNED already (its speech / ^O 'Given quest by'): "
                     "visits are harmless now — it only encourages you; come back with the quest artifact after "
                     "the nemesis if you want the quest completed")
NEMESIS_NOTE = ("QUEST NEMESIS: strong, carries the Bell of Opening (needed to ascend); covetous ones steal your "
                "quest artifact/Amulet and teleport away to heal")


def poison_melee(name: str) -> bool:
    """Does it have a poisonous active attack (bite/sting/weapon)?"""
    rec = monster_record(name)
    return bool(rec) and any(a.get("damage_type") in POISON_AD and a.get("type") not in ("AT_NONE", "AT_BOOM")
                             for a in rec.get("attacks", []))


def paralysing_melee(name: str) -> bool:
    rec = monster_record(name)
    return bool(rec) and any(a.get("damage_type") == "AD_PLYS" and a.get("type") not in ("AT_NONE", "AT_BOOM")
                             for a in rec.get("attacks", []))


def quest_role(name: str) -> str:
    """'leader' / 'nemesis' / '' from the monster's sound (MS_LEADER / MS_NEMESIS)."""
    rec = monster_record(name) or {}
    return {"MS_LEADER": "leader", "MS_NEMESIS": "nemesis"}.get(rec.get("sound", ""), "")


PEACEFUL_PRIEST_NOTE = ("peaceful temple priest: never anger it (protection: donate at least 400*XL but under "
                        "600*XL gold — buy_protection()); on Astral its god must be yours before you #offer the "
                        "Amulet.")

# notes whose danger is the poison: with poison resistance the level/damage rating decides
POISON_NOTES = {"killer bee", "water moccasin", "pit viper", "centipede", "scorpion"}

_STRIP = re.compile(r"^(?:peaceful |tame |invisible |saddled |partly eaten )+")
# farlook suffixes (pager.c look_at_monster / mhidden_description) and the long worm's "tail of a"
_SUFFIX = re.compile(r",\s*(?:swallowing you|engulfing you|being held|holding you|leashed to you|trapped in\b|"
                     r"mimicking\b|masquerading as\b|hiding\b).*$")
_TAIL = re.compile(r"^(?:peaceful |tame )?tail of (?:a )?")
# priest.c priestname(): "the high priestess of Moloch", "priest of Tyr" (a temple priest: aligned priest),
# "high priestess" (an Astral high priest seen from afar); minions: "guardian Angel of Tyr", "Aleax of Tyr"
_PRIEST = re.compile(r"^(?:renegade )?(?P<high>high )?(?:priest|priestess|poohbah)(?: of (?P<god>.+))?$")
_MINION = re.compile(r"^(?:renegade )?(?:guardian )?(?P<sp>.+?) of (?P<god>[A-Z][\w' -]*)$")


def base_name(desc: str) -> str:
    """'peaceful dwarf called Bob' -> 'dwarf'; 'tame kitten' -> 'kitten';
    'jackal, trapped in a pit' -> 'jackal'; 'tail of a long worm' -> 'long worm'."""
    d = desc.strip()
    d = re.sub(r"\s*\[seen:.*\]$", "", d)
    d = _SUFFIX.sub("", d)
    d = _TAIL.sub("", d)
    d = re.sub(r",? called .*$", "", d)
    d = re.sub(r"\s+named .*$", "", d)
    d = re.sub(r"\b(coyote) - .+$", r"\1", d)       # pager.c coyotename(): "coyote - Eatius-Slobbius"
    d = re.sub(r"^.+'s? ghost$", "ghost", d)           # a bones ghost: "Jay's ghost", "Andries' ghost"
    d = _STRIP.sub("", d)
    d = re.sub(r"^(?:a|an|the) ", "", d)
    d = _STRIP.sub("", d.strip())          # "the invisible high priest ..."
    m = _PRIEST.match(d)
    if m and (m.group("high") or m.group("god")):
        return "high priest" if m.group("high") else "aligned priest"
    m = _MINION.match(d)
    if m and d not in _monsters() and m.group("sp") in _monsters():
        return m.group("sp")
    return d.strip()


@lru_cache(maxsize=1)
def _monsters() -> dict:
    p = Path(__file__).parent / "data" / "monsters.json"
    try:
        data = json.loads(p.read_text())
        return {m["name"]: m for m in data.get("monsters", [])}
    except Exception:
        return {}


def monster_record(name: str) -> dict | None:
    return _monsters().get(name)


@lru_cache(maxsize=1)
def _lookalikes() -> dict:
    """(glyph, screen colour name) -> species drawn that way."""
    out: dict = {}
    try:   # the raw list: both forms of a were-creature share a name, so _monsters() keeps only one
        raw = json.loads((Path(__file__).parent / "data" / "monsters.json").read_text()).get("monsters", [])
    except Exception:
        raw = list(_monsters().values())
    for m in raw:
        col = (m.get("color") or "").replace("_", " ")
        sym = "8" if m.get("symbol") == " " else m.get("symbol")      # ghosts/shades: SYMBOLS=S_ghost:8
        for c in ([col, "dark gray", "blue"] if col == "black" else [col]):
            out.setdefault((sym, c), set()).add(m["name"])
    return out


def glyph_species(ch: str, color: str) -> list[str]:
    """Every species drawn as this glyph in this screen colour ('D', 'red' -> baby red dragon, red dragon):
    what a monster nobody has looked at yet can be."""
    return sorted(_lookalikes().get((ch, color), ()))


def noted_lookalikes(ch: str, color: str) -> list[str]:
    """Species drawn as this glyph/colour that carry a danger note (for a
    monster not looked at yet)."""
    return sorted(n for n in _lookalikes().get((ch, color), ()) if NOTES.get(n) and n not in INFO_NOTES)


def risky_lookalike(ch: str, color: str, desc: str) -> bool:
    """Does another species with a danger note look exactly like this one
    (same glyph and colour: a werejackal's 'd' next to jackals)? Then a
    monster re-entering view must be looked at again, not given the label
    of the one seen there before."""
    name = base_name(desc or "")
    return any(n != name and NOTES.get(n) for n in _lookalikes().get((ch, color), ()))


# monst.h M3_COVETOUS: wizard.c tactics() — with nothing to go for it "harasses": 1 turn in 5 it teleports next to
# you (mnexto(): even where teleporting is blocked); badly hurt it teleports to the up stairs to heal
COVETOUS_FLAGS = ("M3_WANTSAMUL", "M3_WANTSBELL", "M3_WANTSBOOK", "M3_WANTSCAND", "M3_WANTSARTI")
COVETOUS_NOTE = ("COVETOUS: once it has noticed you it keeps teleporting next to you (about 1 turn in 5, even on "
                 "no-teleport levels). Wounded, it jumps onto the level's UP stairs (the DOWN ladder in Vlad's "
                 "Tower; in the Wizard's Tower he teleports at random instead) and heals 1d8 a turn while you are "
                 "more than 8 squares away; low on HP it leaves by those stairs if you are within 5 of them. "
                 "Fight it from 6-8 squares away from those stairs: covetous_ring() lists the squares")


def covetous(name: str) -> bool:
    rec = monster_record(base_name(name or ""))
    return bool(rec) and any(f in COVETOUS_FLAGS for f in rec.get("flags3", []))


# mon.c mfndpos() / monmove.c m_move(): a unicorn that sees you never moves onto a square in line with you (NOTONL:
# your row, column or diagonals — every square next to you among them), and one that can't move teleports away
# half the time. It never closes in: it fights only when YOU step next to it (or on a no-teleport level, where
# NOTONL is off and it may be cornered). p4 shift 7: dig('>') paused for a gray unicorn 2 squares away.
KEEPS_AWAY = ("white unicorn", "gray unicorn", "black unicorn")

# mon.c xkilled(): killing a unicorn of YOUR alignment — hostile or not — costs 5 Luck ("You feel guilty...");
# a carried luckstone keeps bad Luck from timing out, and prayer fails while Luck is negative
COALIGNED_UNICORN = {"Lawful": "white unicorn", "Neutral": "gray unicorn", "Chaotic": "black unicorn"}


def coaligned_unicorn(desc: str, align: str) -> bool:
    """Is this the unicorn of your alignment (status-line 'Lawful'/'Neutral'/'Chaotic')?"""
    return bool(align) and bool(desc) and base_name(desc) == COALIGNED_UNICORN.get(align)


def keeps_away(desc: str) -> bool:
    """A species that never closes in on you by itself (the unicorns): no threat until it is next to you."""
    return base_name(desc or "") in KEEPS_AWAY


HERO_GENDER: str | None = None      # "female"/"male" (the daemon sets it from the game's meta.json)


def harmless_seducer(name: str) -> bool:
    """mhitu.c could_seduce(): an incubus/succubus of YOUR gender can't seduce you — its AD_SSEX bite does
    nothing then (SYSOPT_SEDUCE), only the claws hurt (p1 shift 32: a succubus vs a female Valkyrie)."""
    return (name == "succubus" and HERO_GENDER == "female") or (name == "incubus" and HERO_GENDER == "male")


def note_for(desc: str, hero_xl: int | None = None, resists=()) -> str:
    """Short danger note for a farlook description ('' if nothing notable).
    resists: your resistances — a poison note shrinks when you resist it."""
    if not desc or "statue of" in desc or desc.startswith("tame "):
        return ""
    name = base_name(desc)
    bits = []
    n = NOTES.get(name)
    if n and harmless_seducer(name):
        n = ("claws only: it can't seduce you (the same gender as you — mhitu.c could_seduce), so no armor "
             "comes off; an ordinary demon fight")
    if n and name in POISON_NOTES and "poison" in resists:
        n = "poisonous (you resist the poison)"
    if name in ("aligned priest", "high priest") and desc.startswith("peaceful "):
        n = PEACEFUL_PRIEST_NOTE
    elif name in PLAYER_MONSTERS and not desc.startswith("peaceful "):
        n = PLAYER_MONSTER_NOTE
    elif not n and name in RANK_TITLES and not desc.startswith("peaceful "):
        n = RANK_TITLE_NOTE.format(role=RANK_TITLES[name])
    elif not n and quest_role(name) == "leader":
        n = LEADER_NOTE
    elif not n and quest_role(name) == "nemesis":
        n = NEMESIS_NOTE
    if not n and "poison" not in resists and poison_melee(name):
        n = POISON_NOTE
    if not n and "free action" not in resists and paralysing_melee(name):
        n = ("its hit can PARALYSE you (up to 10 turns, 1 in 3 hits; free action prevents it) — deadly with "
             "other monsters around: fight it alone, or at range")
    if n and "holding you" in desc and name in ("giant eel", "electric eel", "kraken"):
        n = ("IT IS HOLDING YOU next to water: its next hit DROWNS you (levitation does NOT help) — engrave "
             "Elbereth NOW (it flees and lets go; not possible while levitating), kill it this turn, or teleport")
    if n:
        bits.append(n.rstrip(". ") if len(n) > 1 else n)     # (joined with "; " below: no ".;")
    rec = monster_record(name)
    if rec and not desc.startswith("peaceful ") and any(f in COVETOUS_FLAGS for f in rec.get("flags3", [])):
        if n and re.search(r"\bcovetous:", n, re.I):
            bits[-1] = re.sub(r"\b[Cc]ovetous:", "COVETOUS (it teleports next to you, even on no-teleport "
                              "levels):", bits[-1], count=1)
        else:
            bits.append(COVETOUS_NOTE)
    if rec and hero_xl is not None and not desc.startswith("peaceful "):
        diff = rec.get("difficulty", 0)
        if diff >= hero_xl + 4:
            bits.append(f"much stronger than you (difficulty {diff} vs XL {hero_xl})")
        elif diff >= hero_xl + 2:
            bits.append(f"stronger than you (difficulty {diff})")
        spd = rec.get("speed", 0)
        if spd >= 15 and diff >= hero_xl:
            bits.append(f"fast (speed {spd})")
    return "; ".join(bits)


def monster_summary(name: str) -> str:
    rec = monster_record(base_name(name))
    if not rec:
        return f"unknown monster {name!r}"
    atk = ", ".join(f"{a['type'][3:]} {a['damage_type'][3:]} {a['dice']}" for a in rec.get("attacks", []))
    res = ",".join(r[3:].lower() for r in rec.get("resistances", [])) or "-"
    conv = ",".join(r[3:].lower() for r in rec.get("conveys", [])) or "-"
    flags = [f for f in rec.get("flags1", []) + rec.get("flags2", []) + rec.get("flags3", [])
             if f in ("M1_FLY", "M1_SWIM", "M1_AMPHIBIOUS", "M1_REGEN", "M1_SEE_INVIS", "M1_TPORT",
                      "M1_POIS", "M1_ACID", "M2_UNDEAD", "M2_DEMON", "M2_HOSTILE", "M2_PEACEFUL",
                      "M2_STRONG", "M2_NASTY", "M1_TPORT_CNTRL", "M3_INFRAVISIBLE", "M2_WERE",
                      "M1_UNSOLID", "M2_STALK")]
    note = NOTES.get(rec["name"], "")
    if "G_NOCORPSE" in (rec.get("geno") or {}).get("flags", []):
        body = "leaves NO corpse"
    else:
        w = rec.get("weight") or 0
        body = (f"corpse wt {w}" + (" (heavy: carrying capacity is 25*(St+Con)+50, at most 1000)" if w >= 600 else "")
                + f", nutrition {rec.get('nutrition')}, conveys: {conv}")
    return (f"{rec['name']} ({rec['symbol']} {rec['color']}): lvl {rec['level']} diff {rec['difficulty']} "
            f"spd {rec['speed']} AC {rec['ac']} MR {rec['mr']} align {rec.get('alignment')} | attacks: "
            f"{atk or '-'} | resists: {res} | {body} | {' '.join(f[3:].lower() for f in flags)}"
            + (f"\n  NOTE: {note}" if note else ""))


# ---- melee risk helpers (used by fight()) ------------------------------------

_PASSIVE_TEXT = {
    "AD_ACID": "acid: splashes you and can corrode your weapon",
    "AD_CORR": "corrodes your weapon",
    "AD_RUST": "rusts your weapon",
    "AD_ENCH": "DISENCHANTS your weapon when you hit it (not Excalibur, nor a weapon at +0 or less)",
    "AD_PLYS": "PARALYSES you when you hit it (deadly without free action)",
    "AD_STON": "touching it STONES you (never barehanded/without gloves)",
    "AD_COLD": "cold (you resist it as a Valkyrie)",
    "AD_FIRE": "burns you",
    "AD_ELEC": "shocks you",
    "AD_STUN": "stuns you",
    "AD_POIS": "poisons you",
    "AD_SLIM": "SLIMES you",
    "AD_DISE": "gives you disease",
    "AD_HALU": "makes you hallucinate",
    "AD_MAGM": "magic damage",
}
# passive effects that should stop fight() before the first blow
STOP_PASSIVES = ("AD_PLYS", "AD_STON", "AD_SLIM", "AD_ENCH")


def explodes_at_you(desc: str) -> str:
    """The damage type of an AT_EXPL attack (it explodes on you when it
    attacks: yellow light blinds, black light hallucinates, spheres burn/
    freeze/shock), or '' if none."""
    rec = monster_record(base_name(desc))
    for a in (rec or {}).get("attacks", []):
        if a.get("type") == "AT_EXPL":
            return a.get("damage_type", "AD_?")
    return ""


def passive_attacks(desc: str) -> list[tuple[str, str]]:
    """[(damage_type, text)] for a monster's passive (AT_NONE) and death
    (AT_BOOM: explodes when killed) attacks."""
    rec = monster_record(base_name(desc))
    out = []
    for a in (rec or {}).get("attacks", []):
        if a.get("type") == "AT_BOOM":
            out.append(("AT_BOOM", f"EXPLODES when killed ({a.get('damage_type', '')[3:].lower()} {a.get('dice')})"))
        elif a.get("type") == "AT_NONE":
            dt = a.get("damage_type", "")
            out.append((dt, _PASSIVE_TEXT.get(dt, dt[3:].lower() + " (passive)")))
    return out


# passives a dwarven Valkyrie shrugs off (intrinsic cold resistance)
RESISTED_PASSIVES = ("AD_COLD",)
_DAMAGING_PASSIVES = ("AD_ACID", "AD_ELEC", "AD_FIRE", "AD_COLD", "AD_PHYS", "AD_DRST")


# intrinsic name (Game.intrinsics) -> the passive damage type it makes harmless
RESIST_AD = {"fire": "AD_FIRE", "cold": "AD_COLD", "shock": "AD_ELEC", "poison": "AD_DRST", "acid": "AD_ACID"}


def passive_max(desc: str, extra_levels: int = 2, resists=()) -> tuple[int, str]:
    """Worst-case HP one of your hits can cost from the target's damaging
    passive (uhitm.c passive(): damn d damd, or (monster level + 1) d damd
    when damn is 0 — the level can be a few above the base, hence
    extra_levels). resists: your resistances ('fire', 'shock', ...) — those
    passives do no HP damage. Returns (max damage, what) or (0, '')."""
    rec = monster_record(base_name(desc))
    best = (0, "")
    immune = {RESIST_AD[r] for r in resists if r in RESIST_AD}
    for a in (rec or {}).get("attacks", []):
        if a.get("type") != "AT_NONE":
            continue
        dt = a.get("damage_type", "")
        if dt not in _DAMAGING_PASSIVES or dt in RESISTED_PASSIVES or dt in immune:
            continue
        n, d = int(a.get("n") or 0), int(a.get("d") or 0)
        if not d:
            continue
        dice = n if n else int(rec.get("level", 0)) + 1 + extra_levels
        dmg = dice * d
        if dmg > best[0]:
            best = (dmg, f"{dt[3:].lower()} {dice}d{d}")
    return best


def max_hit(desc: str) -> int:
    """Rough worst-case damage this monster can do to you in one of your
    turns: sum of its active attacks' maxima (weapon attacks at least 12),
    times its moves per turn at your speed 12."""
    name = base_name(desc)
    rec = monster_record(name)
    if not rec:
        return 20
    total = 0
    for a in rec.get("attacks", []):
        t = a.get("type")
        if t in ("AT_NONE", "AT_BOOM"):
            continue
        n, d = int(a.get("n") or 0), int(a.get("d") or 0)
        dmg = n * d
        if t == "AT_WEAP":
            # the wielded weapon's damage replaces the listed dice: small
            # monsters carry d4-d8 weapons; dwarves carry mattocks (d12)
            dmg = max(dmg, 12 if (rec.get("level", 0) >= 4 or "dwarf" in name) else 8)
        if t == "AT_MAGC" and dmg == 0:
            dmg = 12
        total += dmg
    moves = max(1, -(-int(rec.get("speed", 12)) // 12))
    return total * moves


def threat_level(desc: str, hero_xl: int | None = None, hp: int | None = None, resists=()) -> str:
    """'trivial' | 'normal' | 'dangerous' for a monster description vs you.
    dangerous: has a danger note, deadly passive, or difficulty >= XL+3, or
    its worst-case round is >= 3/4 of your HP; trivial: difficulty <= XL/2
    and worst-case round < a fifth of your HP (or <= 4)."""
    name = base_name(desc or "")
    rec = monster_record(name)
    if not rec:
        return "normal"
    xl = hero_xl or 1
    diff = rec.get("difficulty", 0)
    mh = max_hit(name)
    noted = (NOTES.get(name) or name in PLAYER_MONSTERS or name in RANK_TITLES or quest_role(name)) \
        and name not in INFO_NOTES \
        and not (name in POISON_NOTES and "poison" in resists) and not harmless_seducer(name)
    if noted or any(dt in STOP_PASSIVES or dt == "AT_BOOM" for dt, _ in passive_attacks(name)):
        return "dangerous"
    if "poison" not in resists and poison_melee(name):
        return "dangerous"      # a snake's poisoned bite can kill outright without poison resistance
    if "free action" not in resists and paralysing_melee(name):
        return "dangerous"      # a ghoul's claw freezes you for up to 10 turns
    if diff >= xl + 3 or (hp is not None and mh * 4 >= hp * 3):
        return "dangerous"      # much stronger, or one worst-case round takes 3/4 of your HP
    if diff <= max(1, xl // 2) and (mh <= 4 or (hp is not None and mh * 5 < hp)):
        return "trivial"
    return "normal"
