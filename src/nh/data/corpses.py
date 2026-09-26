"""Corpse-eating rules for NetHack 3.6.7, ported from src/eat.c.

    >>> from nh.data.corpses import corpse_info, corpse_verdict
    >>> v = corpse_verdict("floating eye", hero_race="human", hero_role="Valkyrie",
    ...                    age_turns=5, has_poison_res=True)
    >>> v.verdict
    <Verdict.SAFE: 'SAFE'>

Monster facts come from monsters.json (generated from monst.c); the rules
are hand-ported from eat.c (eatcorpse, cprefx, cpostfx, givit,
intrinsic_possible, maybe_cannibal, rottenfood), mon.c (make_corpse,
corpse_chance, undead_to_corpse, mondead's lycanthrope reversion) and
were.c (were_beastie).  Function references are to 3.6.7.

Order of events when a corpse is eaten, which the verdict mirrors:
  1. eatcorpse(): rot check.  rotted = age / (10 + rn2(20)), +2 if cursed,
     -2 if blessed (lizard, lichen and Rider corpses never rot).
     rotted > 5 -> "tainted": fatal food poisoning unless cured (skipped
     for acid blobs, for petrifying meat without stoning resistance and
     for green slime).  Otherwise acidic -> 1d15 damage without acid
     resistance; else poisonous -> 80%: -1d4 Str and 1d15 damage unless
     poison resistant; else rotted > 5 (or > 3, 80%) -> "you feel sick",
     1d8 damage.  If none of those fired, 1 in 7 "Blecch! Rotten food!"
     (confusion / blindness / 1-10 turns unconscious).
  2. cprefx() on the first bite: cannibalism, petrification, Riders,
     domestic dogs/cats, green slime, lizard/acid curing stoning.
  3. cpostfx() when finished: special cases (newt, wraith, lycanthropes,
     nurse, stalker, bats, yellow light, mimics, quantum mechanic, lizard,
     shapeshifters, disenchanter, mind flayers), then hallucination for
     AD_STUN/AD_HALU attackers and violet fungus, then at most one
     intrinsic chosen uniformly among the candidates and granted with
     probability level/chance (givit()).
Tins run cprefx/cpostfx but skip step 1 (pass tinned=True).
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

__all__ = ["Verdict", "CorpseVerdict", "corpse_info", "corpse_verdict",
           "taint_chance", "monster"]

_MONSTERS_JSON = Path(__file__).with_name("monsters.json")


class Verdict(str, Enum):
    SAFE = "SAFE"      # nothing bad beyond the ~1/7 "rotten food" chance
    RISKY = "RISKY"    # non-lethal harm possible/likely (HP, Str, stun, ...)
    DEADLY = "DEADLY"  # real chance of dying (tainted meat, choking)
    NEVER = "NEVER"    # certain death or lasting damage (stoning, Riders,
                       # sliming, lycanthropy, cannibalism, pet meat)

    @property
    def rank(self) -> int:
        return ("SAFE", "RISKY", "DEADLY", "NEVER").index(self.value)


# --- tables ported from the C sources -------------------------------------

# eat.c CANNIBAL_ALLOWED(): Role_if(PM_CAVEMAN) || Race_if(PM_ORC)
_RACE_SELFMASK = {"human": "M2_HUMAN", "elf": "M2_ELF", "dwarf": "M2_DWARF",
                  "gnome": "M2_GNOME", "orc": "M2_ORC"}
_RACE_ALIASES = {"hum": "human", "elf": "elf", "elv": "elf", "dwa": "dwarf",
                 "gno": "gnome", "orc": "orc"}  # first 3 letters
_ROLES = {"arc": "Archeologist", "bar": "Barbarian", "cav": "Caveman",
          "hea": "Healer", "kni": "Knight", "mon": "Monk", "pri": "Priest",
          "rog": "Rogue", "ran": "Ranger", "sam": "Samurai", "tou": "Tourist",
          "val": "Valkyrie", "wiz": "Wizard"}

# eat.c cprefx(): eating these without CANNIBAL_ALLOWED() gives permanent
# Aggravate monster
_DOMESTIC = {"PM_LITTLE_DOG", "PM_DOG", "PM_LARGE_DOG", "PM_KITTEN",
             "PM_HOUSECAT", "PM_LARGE_CAT"}
_RIDERS = {"PM_DEATH", "PM_PESTILENCE", "PM_FAMINE"}
# mondata.h touch_petrifies() + eat.c flesh_petrifies() adds Medusa
_PETRIFYING = {"PM_COCKATRICE", "PM_CHICKATRICE", "PM_MEDUSA"}
# eat.c nonrotting_corpse()
_NONROTTING = {"PM_LIZARD", "PM_LICHEN"} | _RIDERS
# eat.c cpostfx(): lycanthropy from the @ forms; mon.c mondead() turns the
# animal forms back into these before the corpse is made
_LYCANTHROPY = {"PM_HUMAN_WERERAT": "PM_WERERAT",
                "PM_HUMAN_WEREJACKAL": "PM_WEREJACKAL",
                "PM_HUMAN_WEREWOLF": "PM_WEREWOLF"}
_WERE_TO_HUMAN = {v: k for k, v in _LYCANTHROPY.items()}
# were.c were_beastie(): eating these is cannibalism for a lycanthrope
_WERE_BEASTIE = {
    "PM_WERERAT": {"PM_WERERAT", "PM_SEWER_RAT", "PM_GIANT_RAT", "PM_RABID_RAT"},
    "PM_WEREJACKAL": {"PM_WEREJACKAL", "PM_JACKAL", "PM_FOX", "PM_COYOTE"},
    "PM_WEREWOLF": {"PM_WEREWOLF", "PM_WOLF", "PM_WARG", "PM_WINTER_WOLF"},
}
# eat.c cpostfx(): stun (HStun += 30 per fallthrough step)
_STUN_TURNS = {"PM_BAT": 30, "PM_GIANT_BAT": 60, "PM_YELLOW_LIGHT": 60,
               "PM_STALKER": 60}
_MIMIC_TURNS = {"PM_SMALL_MIMIC": 20, "PM_LARGE_MIMIC": 40, "PM_GIANT_MIMIC": 50}
_POLYMORPH = {"PM_CHAMELEON", "PM_DOPPELGANGER", "PM_SANDESTIN"}
_MIND_FLAYERS = {"PM_MIND_FLAYER", "PM_MASTER_MIND_FLAYER"}
# cpostfx() cases that 'break' without setting check_intrinsics: no
# intrinsic and no hallucination roll after eating these
_NO_INTRINSIC_CHECK = ({"PM_NEWT", "PM_WRAITH", "PM_QUANTUM_MECHANIC",
                        "PM_LIZARD", "PM_DISENCHANTER"} | set(_LYCANTHROPY)
                       | set(_STUN_TURNS) | set(_MIMIC_TURNS) | _POLYMORPH
                       | _RIDERS)  # cprefx() kills you before cpostfx()
# mon.c undead_to_corpse(); make_corpse() also ages these corpses by 100
_UNDEAD_TO_CORPSE = {
    "PM_KOBOLD_ZOMBIE": "PM_KOBOLD", "PM_KOBOLD_MUMMY": "PM_KOBOLD",
    "PM_DWARF_ZOMBIE": "PM_DWARF", "PM_DWARF_MUMMY": "PM_DWARF",
    "PM_GNOME_ZOMBIE": "PM_GNOME", "PM_GNOME_MUMMY": "PM_GNOME",
    "PM_ORC_ZOMBIE": "PM_ORC", "PM_ORC_MUMMY": "PM_ORC",
    "PM_ELF_ZOMBIE": "PM_ELF", "PM_ELF_MUMMY": "PM_ELF",
    "PM_HUMAN_ZOMBIE": "PM_HUMAN", "PM_HUMAN_MUMMY": "PM_HUMAN",
    "PM_VAMPIRE": "PM_HUMAN", "PM_VAMPIRE_LORD": "PM_HUMAN",
    "PM_GIANT_ZOMBIE": "PM_GIANT", "PM_GIANT_MUMMY": "PM_GIANT",
    "PM_ETTIN_ZOMBIE": "PM_ETTIN", "PM_ETTIN_MUMMY": "PM_ETTIN",
}
# mon.c make_corpse(): what golems leave instead of a corpse
_GOLEM_REMAINS = {
    "PM_IRON_GOLEM": "iron chains", "PM_GLASS_GOLEM": "worthless glass",
    "PM_CLAY_GOLEM": "rocks", "PM_STONE_GOLEM": "a statue",
    "PM_WOOD_GOLEM": "quarterstaves", "PM_LEATHER_GOLEM": "leather armor",
    "PM_GOLD_GOLEM": "gold pieces", "PM_PAPER_GOLEM": "blank scrolls",
}
_PUDDINGS = {"PM_GRAY_OOZE", "PM_BROWN_PUDDING", "PM_GREEN_SLIME",
             "PM_BLACK_PUDDING"}  # leave "glob of ..." food instead
# eat.c intrinsic_possible(): resistances come from mconveys, in prop.h order
_CONVEYABLE = [("MR_FIRE", "fire resistance"), ("MR_COLD", "cold resistance"),
               ("MR_SLEEP", "sleep resistance"),
               ("MR_DISINT", "disintegration resistance"),
               ("MR_ELEC", "shock resistance"),
               ("MR_POISON", "poison resistance")]
_TELEPATHIC = {"PM_FLOATING_EYE", "PM_MIND_FLAYER", "PM_MASTER_MIND_FLAYER"}
_GIVIT_CHANCE = {"teleportitis": 10, "teleport control": 12, "telepathy": 1}

_MZ_SMALL, _MZ_LARGE = 1, 3
_ROT_DIVISORS = range(10, 30)  # 10 + rn2(20)


# --- monster lookup --------------------------------------------------------

@lru_cache(maxsize=1)
def _db() -> tuple[dict[str, dict], dict[str, list[dict]]]:
    data = json.loads(_MONSTERS_JSON.read_text(encoding="utf-8"))
    by_pm: dict[str, dict] = {}
    by_name: dict[str, list[dict]] = {}
    for m in data["monsters"]:
        by_pm[m["pm"]] = m
        by_name.setdefault(m["name"].lower(), []).append(m)
    return by_pm, by_name


_PREFIX_RE = re.compile(
    r"^(?:an?|the|\d+|blessed|uncursed|cursed|partly eaten|tins? of|"
    r"(?:(?:very )?large |small )?globs? of)\s+")


def _normalize(name: str) -> str:
    s = " ".join(name.strip().lower().split())
    prev = None
    while prev != s:
        prev = s
        s = _PREFIX_RE.sub("", s)
    s = re.sub(r"\s+(?:corpses?|meat)$", "", s)
    s = re.sub(r"'s?$", "", s)  # "Medusa's corpse", "Croesus' corpse"
    return s


def monster(name: str) -> dict:
    """monsters.json record for a monster name, PM_ constant, or item name
    such as "2 uncursed jackal corpses" / "Medusa's corpse" / "glob of gray
    ooze".  Were-creature names resolve to the @ form (what the corpse is)."""
    by_pm, by_name = _db()
    if name in by_pm:
        return by_pm[name]
    key = _normalize(name)
    cands = by_name.get(key)
    if not cands:
        raise KeyError(f"unknown monster {name!r}")
    for c in cands:
        if c["pm"] in _LYCANTHROPY:
            return c
    return cands[0]


# --- probabilities ----------------------------------------------------------

def _rotted(age: float, buc: str, divisor: int) -> float:
    r = age // divisor
    return r + 2 if buc == "cursed" else r - 2 if buc == "blessed" else r


def taint_chance(age_turns: float | None, buc: str = "uncursed") -> float:
    """P(rotted > 5) for a rotting corpse (eat.c eatcorpse()).  Uncursed:
    0 below 60 turns, 1 from 174.  age_turns=None means unknown -> 1.0."""
    if age_turns is None:
        return 1.0
    hits = sum(_rotted(age_turns, buc, d) > 5 for d in _ROT_DIVISORS)
    return hits / len(_ROT_DIVISORS)


def _mild_sick_chance(age: float | None, buc: str, taint_possible: bool) -> float:
    """P(no taint and "You feel sick" 1d8), before the acid/poison branch."""
    if age is None:
        return 0.0 if taint_possible else 1.0
    total = 0.0
    for d in _ROT_DIVISORS:
        r = _rotted(age, buc, d)
        if r > 5:
            total += 0.0 if taint_possible else 1.0
        elif r > 3:
            total += 0.8
    return total / len(_ROT_DIVISORS)


def _givit(m: dict, intrinsic: str) -> float:
    """P(givit() succeeds) = P(mlevel > rn2(chance))."""
    lvl = m["level"]
    if intrinsic == "poison resistance" and m["pm"] in ("PM_KILLER_BEE",
                                                         "PM_SCORPION"):
        return 0.25 * (lvl > 0) + 0.75 * min(max(lvl, 0), 15) / 15
    chance = _GIVIT_CHANCE.get(intrinsic, 15)
    return min(max(lvl, 0), chance) / chance


def _intrinsics(m: dict) -> tuple[dict[str, float], float]:
    """{intrinsic: P(gained)} and P(+Str) for one corpse eaten completely,
    per cpostfx(): one candidate chosen uniformly, then givit()."""
    if m["pm"] in _NO_INTRINSIC_CHECK:
        return {}, 0.0
    cands = [label for flag, label in _CONVEYABLE if flag in m["conveys"]]
    if "M1_TPORT" in m["flags1"]:
        cands.append("teleportitis")
    if "M1_TPORT_CNTRL" in m["flags1"]:
        cands.append("teleport control")
    if m["pm"] in _TELEPATHIC:
        cands.append("telepathy")
    giant = "M2_GIANT" in m["flags2"]
    count = len(cands) + giant
    if not count:
        return {}, 0.0
    scale = 0.5 if m["pm"] in _MIND_FLAYERS else 1.0  # 50%: +1 Int instead
    probs = {c: scale * _givit(m, c) / count for c in cands}
    strength = (0.5 if count == 1 else 1 / count) if giant else 0.0
    return probs, strength


def _corpse_chance(m: dict) -> tuple[float, str]:
    """mon.c corpse_chance() + make_corpse() for a monster killed normally."""
    pm, flags = m["pm"], m["geno"]["flags"]
    if pm == "PM_VLAD_THE_IMPALER" or m["class"] == "S_LICH":
        return 0.0, "body crumbles to dust"
    if any(a["type"] == "AT_BOOM" for a in m["attacks"]):
        return 0.0, "explodes when killed"
    if pm in _GOLEM_REMAINS:
        return 0.0, f"leaves {_GOLEM_REMAINS[pm]} instead of a corpse"
    if "G_NOCORPSE" in flags and pm not in _UNDEAD_TO_CORPSE \
            and pm not in _PUDDINGS:
        return 0.0, "never leaves a corpse (G_NOCORPSE)"
    what = "a glob (eaten like a corpse)" if pm in _PUDDINGS else "a corpse"
    extra = ("; on graveyard levels undead leave nothing 2 times in 3"
             if "M2_UNDEAD" in m["flags2"] else "")
    idx = m["index"]
    by_pm = _db()[0]
    mplayer = by_pm["PM_ARCHEOLOGIST"]["index"] <= idx <= by_pm["PM_WIZARD"]["index"]
    if (m["size_value"] >= _MZ_LARGE or pm == "PM_LIZARD" or m["class"] == "S_GOLEM"
            or mplayer or pm in _RIDERS or pm == "PM_SHOPKEEPER"):
        return 1.0, f"always leaves {what} (unless it was a clone){extra}"
    n = 2 + (m["geno"]["frequency"] < 2) + (m["size_value"] < _MZ_SMALL)
    return 1.0 / n, f"leaves {what} 1 time in {n}{extra}"


def _vegan(m: dict) -> bool:
    cls = m["class"]
    return (cls in ("S_BLOB", "S_JELLY", "S_FUNGUS", "S_VORTEX", "S_LIGHT", "S_GHOST")
            or (cls == "S_ELEMENTAL" and m["pm"] != "PM_STALKER")
            or (cls == "S_GOLEM" and m["pm"] not in ("PM_FLESH_GOLEM",
                                                     "PM_LEATHER_GOLEM")))


def _vegetarian(m: dict) -> bool:
    return _vegan(m) or (m["class"] == "S_PUDDING" and m["pm"] != "PM_BLACK_PUDDING")


# --- public API --------------------------------------------------------------

def corpse_info(name: str) -> dict[str, Any]:
    """Static facts about eating `name`'s corpse (independent of the hero)."""
    src = monster(name)
    notes: list[str] = []
    m, age_offset = src, 0
    if src["pm"] in _WERE_TO_HUMAN:
        m = _db()[0][_WERE_TO_HUMAN[src["pm"]]]
        notes.append("an animal-form lycanthrope reverts to its @ form when "
                     "it dies; the corpse carries lycanthropy")
    if src["pm"] in _UNDEAD_TO_CORPSE:
        m = _db()[0][_UNDEAD_TO_CORPSE[src["pm"]]]
        age_offset = 100
        notes.append(f"a {src['name']} leaves a {m['name']} corpse that is "
                     f"already 100 turns old (ages it by -100 at death)")
    # mondead() reverts lycanthropes before corpse_chance() looks at them
    chance, chance_note = _corpse_chance(m if src["pm"] in _WERE_TO_HUMAN else src)
    pm = m["pm"]
    intrinsics, strength = _intrinsics(m)
    hallu = 0
    if pm not in _NO_INTRINSIC_CHECK and (
            pm == "PM_VIOLET_FUNGUS"
            or any(a["damage_type"] in ("AD_STUN", "AD_HALU") for a in m["attacks"])):
        hallu = 200
    races = [r for r, flag in _RACE_SELFMASK.items()
             if flag in m["flags2"] and r != "orc"]
    if pm in _MIND_FLAYERS:
        notes.append("if Int is below maximum: 50% '+1 Int' instead of the "
                     "intrinsic roll (probabilities above include this)")
    return {
        "name": m["name"],
        "pm": pm,
        "source": src["name"],
        "source_pm": src["pm"],
        "corpse_age_offset": age_offset,
        "corpse_chance": chance,
        "corpse_chance_note": chance_note,
        "weight": m["weight"],
        "nutrition": m["nutrition"],
        "eat_turns": 3 + (m["weight"] >> 6),
        "vegan": _vegan(m),
        "vegetarian": _vegetarian(m),
        "never_rots": pm in _NONROTTING,
        "acidic": "M1_ACID" in m["flags1"],
        "poisonous": "M1_POIS" in m["flags1"],
        "petrifies": pm in _PETRIFYING,
        "slimes": pm == "PM_GREEN_SLIME",
        "fatal": pm in _RIDERS,
        "lycanthropy": _db()[0][_LYCANTHROPY[pm]]["name"] if pm in _LYCANTHROPY else None,
        "cannibalism_for": races,
        "domestic_animal": pm in _DOMESTIC,
        "cures_stoning": pm == "PM_LIZARD" or "M1_ACID" in m["flags1"],
        "polymorph": pm in _POLYMORPH,
        "stun_turns": _STUN_TURNS.get(pm, 0),
        "hallucination_turns": hallu,
        "mimic_turns": _MIMIC_TURNS.get(pm, 0),
        "invisibility": pm == "PM_STALKER",
        "toggles_speed": pm == "PM_QUANTUM_MECHANIC",
        "gain_level": pm == "PM_WRAITH",
        "energy_boost": pm == "PM_NEWT",
        "full_heal": pm == "PM_NURSE",
        "int_gain_chance": 0.5 if pm in _MIND_FLAYERS else 0.0,
        "strips_intrinsic": pm == "PM_DISENCHANTER",
        "cures_stun_confusion": pm == "PM_LIZARD",
        "intrinsics": intrinsics,
        "strength_chance": strength,
        "tinnable": m["nutrition"] > 0 and pm not in _RIDERS,
        "notes": notes,
    }


@dataclass(frozen=True)
class CorpseVerdict:
    verdict: Verdict
    reasons: tuple[str, ...]   # hazards, most severe first, "LEVEL: text"
    benefits: tuple[str, ...]
    notes: tuple[str, ...]
    taint_chance: float
    monster: str               # whose meat it actually is

    def __str__(self) -> str:
        head = self.verdict.value + ": "
        parts = [r[len(head):] if r.startswith(head) else r for r in self.reasons]
        return head + ("; ".join(parts) or "no hazards")

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        return d


def _pct(p: float) -> str:
    return f"{100 * p:.0f}%" if p not in (0.0, 1.0) else ("certain" if p else "never")


def corpse_verdict(
    name: str,
    *,
    hero_race: str,
    hero_role: str,
    age_turns: float | None,
    has_poison_res: bool,
    has_stoning_res: bool = False,
    is_hungry: bool = True,
    buc: str = "uncursed",
    has_acid_res: bool = False,
    has_sick_res: bool = False,
    is_satiated: bool = False,
    is_stoned: bool = False,
    hero_lycanthropy: str | None = None,
    has_intrinsic_speed: bool | None = None,
    unchanging: bool = False,
    tinned: bool = False,
) -> CorpseVerdict:
    """Is it safe to eat this corpse now?

    name        monster or corpse name ("jackal", "3 jackal corpses",
                "kobold zombie" -> old kobold corpse, PM_ constant)
    hero_race   human/elf/dwarf/gnome/orc (3-letter abbreviations ok)
    hero_role   role name or abbreviation (Caveman and Monk matter)
    age_turns   turns since the monster died (None = unknown -> worst case)
    buc         "blessed" / "uncursed" / "cursed" ("unknown" treated as cursed)
    is_hungry   False adds a note (no nutrition need); choking only happens
                if you *start* eating while Satiated: pass is_satiated=True
    tinned      the meat is in a tin: no rot, acid or poison checks
    Not modelled: being polymorphed (same-race cannibalism, poly_when_stoned,
    slimeproof forms), ice-box aging, blindness during rottenfood().
    """
    info = corpse_info(name)
    by_pm = _db()[0]
    m = by_pm[info["pm"]]
    pm = m["pm"]
    race = _RACE_ALIASES.get(hero_race.strip().lower()[:3])
    if race is None:
        raise ValueError(f"unknown race {hero_race!r}")
    role_key = hero_role.strip().lower()[:3]
    if role_key not in _ROLES:
        raise ValueError(f"unknown role {hero_role!r}")
    role = _ROLES[role_key]
    age = None if age_turns is None else age_turns + info["corpse_age_offset"]

    hazards: list[tuple[Verdict, str]] = []
    benefits: list[str] = []
    notes: list[str] = list(info["notes"])
    if buc not in ("blessed", "uncursed", "cursed"):
        notes.append(f"BUC {buc!r} unknown: assumed cursed (rots fastest)")
        buc = "cursed"

    def hazard(level: Verdict, text: str) -> None:
        hazards.append((level, text))

    cannibal_ok = role == "Caveman" or race == "orc"
    stoneable = info["petrifies"] and not has_stoning_res
    slimeable = info["slimes"] and not unchanging

    # 1. eatcorpse(): rot, acid, poison, mild sickness, rotten food
    p_taint = 0.0
    if not tinned:
        rots = pm not in _NONROTTING
        taint_possible = rots and pm != "PM_ACID_BLOB" and not stoneable \
            and not slimeable
        if taint_possible:
            p_taint = taint_chance(age, buc)
        if p_taint > 0 and not has_sick_res:
            when = "age unknown" if age is None else f"{age:g} turns old"
            hazard(Verdict.DEADLY,
                   f"{_pct(p_taint)} chance it is tainted ({when}, {buc}): fatal "
                   "food poisoning unless cured (pray, unicorn horn, "
                   "uncursed extra/full healing, eucalyptus leaf)")
        elif p_taint > 0:
            notes.append(f"{_pct(p_taint)} tainted, harmless with sickness resistance")
        not_tainted = 1.0 - p_taint
        acid_branch = info["acidic"] and not has_acid_res
        if acid_branch and not_tainted > 0:
            hazard(Verdict.RISKY, "acidic: 1d15 damage (no acid resistance)")
        elif info["poisonous"] and not_tainted > 0:
            if has_poison_res:
                notes.append("poisonous, but your poison resistance blocks it")
            else:
                hazard(Verdict.RISKY, "poisonous: 80% chance of -1d4 Str and "
                                      "1d15 damage (no poison resistance)")
        if rots and not acid_branch and not has_sick_res:
            p = _mild_sick_chance(age, buc, taint_possible)
            if info["poisonous"]:
                p *= 0.2
            if p > 0:
                hazard(Verdict.RISKY, f"{_pct(p)} chance of 'you feel sick' "
                                      "(1d8 damage) from age")
        if rots:
            notes.append("1 in 7 'Blecch! Rotten food!' roll (confusion, "
                         "blindness or up to 10 turns unconscious) if nothing "
                         "else went wrong")

    # 2. cprefx()
    if info["fatal"]:
        hazard(Verdict.NEVER, f"{m['name']}: eating a Rider is instantly fatal "
                              "(and the corpse revives)")
    if not cannibal_ok and (race in info["cannibalism_for"] or (
            hero_lycanthropy and pm in _WERE_BEASTIE.get(
                monster(hero_lycanthropy)["pm"].replace("PM_HUMAN_", "PM_"), ()))):
        hazard(Verdict.NEVER, "cannibalism: Luck -2..-5 and permanent "
                              "Aggravate monster")
    if info["petrifies"]:
        if stoneable:
            hazard(Verdict.NEVER, f"{m['name']} meat petrifies: you turn to "
                                  "stone (no stoning resistance)")
        else:
            notes.append("petrifying meat is safe with stoning resistance "
                         "('tastes just like chicken')")
    if info["domestic_animal"] and not cannibal_ok:
        hazard(Verdict.NEVER, "domestic dog/cat: permanent Aggravate monster "
                              "(only Cavemen and orcs may eat pets)")
    if info["slimes"]:
        if slimeable:
            hazard(Verdict.NEVER, "green slime: you start turning into green "
                                  "slime (cure: fire, prayer, polymorph)")
    if is_stoned:
        if info["cures_stoning"]:
            benefits.append("cures your petrification")
        else:
            notes.append("does NOT cure stoning (need lizard or acidic meat)")

    # 3. cpostfx()
    if info["lycanthropy"]:
        hazard(Verdict.NEVER, f"lycanthropy: you become a {info['lycanthropy']} "
                              "(cure: prayer, holy water, wolfsbane)")
    if info["stun_turns"]:
        hazard(Verdict.RISKY, f"stuns you for {info['stun_turns']}+ turns")
    if info["mimic_turns"] and not unchanging:
        hazard(Verdict.RISKY, f"helpless for {info['mimic_turns']} turns "
                              "mimicking a pile of gold")
    if info["polymorph"] and not unchanging:
        hazard(Verdict.RISKY, "polymorphs you into a random monster (armor may "
                              "break, no control without polymorph control)")
    if info["strips_intrinsic"]:
        hazard(Verdict.RISKY, "removes one random intrinsic (attrcurse)")
    if info["hallucination_turns"]:
        hazard(Verdict.RISKY, f"hallucination for {info['hallucination_turns']} turns")
    if info["toggles_speed"]:
        if has_intrinsic_speed:
            hazard(Verdict.RISKY, "toggles speed: you LOSE intrinsic speed")
        elif has_intrinsic_speed is None:
            hazard(Verdict.RISKY, "toggles intrinsic speed (gain if you lack it, "
                                  "lose it if you have it)")
        else:
            benefits.append("grants intrinsic speed")
    if info["invisibility"]:
        benefits.append("invisibility (temporary; permanent + see invisible if "
                        "already invisible)")
    if info["gain_level"]:
        benefits.append("gain one experience level")
    if info["energy_boost"]:
        benefits.append("restores 1-3 energy (may raise max energy)")
    if info["full_heal"]:
        benefits.append("fully heals HP and cures blindness")
    if info["int_gain_chance"]:
        benefits.append("50% +1 Int (if below maximum)")
    if info["cures_stun_confusion"]:
        benefits.append("cuts stun/confusion to 2 turns")
    for what, p in info["intrinsics"].items():
        benefits.append(f"{what}: {_pct(p)}")
    if info["strength_chance"]:
        benefits.append(f"+Str (giant): {_pct(info['strength_chance'])}")

    # role / hunger
    if role == "Monk" and not info["vegetarian"]:
        notes.append("Monk eating meat: 'You feel guilty.' (-1 alignment)")
    if is_satiated:
        hazard(Verdict.DEADLY, "you are Satiated: reaching 2000 nutrition while "
                               "eating chokes you to death (95%; Breathless is safe)")
    elif not is_hungry:
        notes.append("not hungry: only worth it for the benefits"
                     + ("" if benefits else " (there are none)")
                     + f"; {info['nutrition']} nutrition")

    level = max((h[0] for h in hazards), key=lambda v: v.rank, default=Verdict.SAFE)
    hazards.sort(key=lambda h: -h[0].rank)
    return CorpseVerdict(
        verdict=level,
        reasons=tuple(f"{lv.value}: {text}" for lv, text in hazards),
        benefits=tuple(benefits),
        notes=tuple(notes),
        taint_chance=p_taint,
        monster=m["name"],
    )
