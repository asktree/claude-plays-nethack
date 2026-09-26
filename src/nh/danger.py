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
    "rust monster": "rusts/eats iron armor and weapons.",
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
    "fog cloud": "engulf; mostly harmless.",
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

_STRIP = re.compile(r"^(?:peaceful |tame |invisible |saddled )+")


def base_name(desc: str) -> str:
    """'peaceful dwarf called Bob' -> 'dwarf'; 'tame kitten' -> 'kitten'."""
    d = desc.strip()
    d = re.sub(r"\s*\[seen:.*\]$", "", d)
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
    return (f"{rec['name']} ({rec['symbol']} {rec['color']}): lvl {rec['level']} diff {rec['difficulty']} "
            f"spd {rec['speed']} AC {rec['ac']} MR {rec['mr']} | attacks: {atk or '-'} | resists: {res} | "
            f"corpse conveys: {conv} | {' '.join(f[3:].lower() for f in flags)}"
            + (f"\n  NOTE: {note}" if note else ""))
