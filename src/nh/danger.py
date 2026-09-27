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
    "giant eel": "can DROWN you if you're next to water. Step away from water.",
    "electric eel": "can DROWN you; shock. Step away from water.",
    "kraken": "can DROWN you. Step away from water.",
    "shark": "hits hard from water; stay off the water edge.",
    "mind flayer": "tentacles eat your brain (Int loss, amnesia). Kill fast / flee; telepathic.",
    "master mind flayer": "tentacles eat your brain (Int loss, amnesia). Very dangerous; flee or burst it down.",
    "lich": "spellcaster (curses items, summons). Kill fast.",
    "demilich": "spellcaster: curses, destroys armor, paralysis? Kill fast.",
    "master lich": "powerful caster: touch of death possible without MR, summons nasties.",
    "arch-lich": "deadliest caster: touch of death without MR, haste self. Needs MR.",
    "disenchanter": "disenchants your weapon/armor on hit. Don't melee with good gear.",
    "rust monster": "no HP damage. Its touches rust iron armor (a worn cloak covers body armor; helmet, shield, "
                    "gloves, boots can rust); hitting it rusts an iron weapon unless rustproof (a fountain "
                    "Excalibur is). Eats metal off the floor.",
    "gremlin": "AT NIGHT (game clock 22:00-05:59, the server's local time) its claw can STEAL AN INTRINSIC "
               "(speed, poison/fire/cold res, telepathy...): kill it asleep or at range. Multiplies in water "
               "and fountains.",
    "gelatinous cube": "passive PARALYSIS if you hit it; engulfs. Don't melee without free action.",
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
    "vampire": "LEVEL DRAIN bite; regenerates.",
    "vampire lord": "LEVEL DRAIN bite; regenerates.",
    "Vlad the Impaler": "LEVEL DRAIN bite; strong.",
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
    "pit fiend": "strong: grabs; spellcaster.",
    "balrog": "very strong; bullwhip + broadsword; flies.",
    "ice devil": "cold (you resist) + slowing sting.",
    "barbed devil": "grabs; hits hard.",
    "cockatrice corpse": "never touch without gloves.",
    "Death": "RIDER. Touch of death. Avoid.",
    "Pestilence": "RIDER. Illness. Avoid.",
    "Famine": "RIDER. Hunger. Avoid.",
    "Wizard of Yendor": "steals the Amulet/quest artifact; curses; double trouble. Keep uncursing ready.",
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
    "master of thieves": "steals.",
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
    "aligned priest": "don't anger temple priests.",
    "shopkeeper": "NEVER anger (very strong).",
    "watchman": "Minetown Watch: don't anger (no fountain dipping/quaffing, no door breaking, no theft).",
    "watch captain": "Minetown Watch: don't anger.",
}

# notes that inform but don't by themselves make a monster 'dangerous' in threat_level() (packs,
# nuisances, thieves, slow hard hitters): its level and worst-case damage vs you decide
INFO_NOTES = {"hill orc", "Uruk-hai", "dwarf", "dwarf lord", "leprechaun", "chameleon", "tengu", "cave spider",
              "ghost", "xorn", "hill giant", "stone giant", "giant beetle", "owlbear", "leocrotta",
              "ettin", "troll", "rock troll", "ice troll", "water troll", "Olog-hai", "python", "rust monster",
              "blue jelly", "nurse", "rotting corpse", "master of thieves", "water moccasin", "centipede",
              "scorpion", "pit viper", "large mimic", "giant mimic", "ice vortex", "dust vortex"}

_STRIP = re.compile(r"^(?:peaceful |tame |invisible |saddled |partly eaten )+")
# farlook suffixes (pager.c look_at_monster / mhidden_description) and the long worm's "tail of a"
_SUFFIX = re.compile(r",\s*(?:swallowing you|engulfing you|being held|holding you|leashed to you|trapped in\b|"
                     r"mimicking\b|masquerading as\b|hiding\b).*$")
_TAIL = re.compile(r"^(?:peaceful |tame )?tail of (?:a )?")


def base_name(desc: str) -> str:
    """'peaceful dwarf called Bob' -> 'dwarf'; 'tame kitten' -> 'kitten';
    'jackal, trapped in a pit' -> 'jackal'; 'tail of a long worm' -> 'long worm'."""
    d = desc.strip()
    d = re.sub(r"\s*\[seen:.*\]$", "", d)
    d = _SUFFIX.sub("", d)
    d = _TAIL.sub("", d)
    d = re.sub(r",? called .*$", "", d)
    d = re.sub(r"\s+named .*$", "", d)
    d = _STRIP.sub("", d)
    d = re.sub(r"^(?:a|an|the) ", "", d)
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
        for c in ([col, "dark gray", "blue"] if col == "black" else [col]):
            out.setdefault((m.get("symbol"), c), set()).add(m["name"])
    return out


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


def note_for(desc: str, hero_xl: int | None = None) -> str:
    """Short danger note for a farlook description ('' if nothing notable)."""
    if not desc or "statue of" in desc or desc.startswith("tame "):
        return ""
    name = base_name(desc)
    bits = []
    n = NOTES.get(name)
    if n:
        bits.append(n)
    rec = monster_record(name)
    if rec and hero_xl is not None:
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
    "AD_ENCH": "DISENCHANTS your weapon (Excalibur loses its enchantment)",
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


def threat_level(desc: str, hero_xl: int | None = None, hp: int | None = None) -> str:
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
    if (NOTES.get(name) and name not in INFO_NOTES) or \
            any(dt in STOP_PASSIVES or dt == "AT_BOOM" for dt, _ in passive_attacks(name)):
        return "dangerous"
    if diff >= xl + 3 or (hp is not None and mh * 4 >= hp * 3):
        return "dangerous"      # much stronger, or one worst-case round takes 3/4 of your HP
    if diff <= max(1, xl // 2) and (mh <= 4 or (hp is not None and mh * 5 < hp)):
        return "trivial"
    return "normal"
