"""Combat helpers. One blow per step, checked every time; never batches.

fight() only ever attacks monsters the tracker identified as hostile (not
tame/peaceful/statue), and the harness guard refuses floating eyes, gas
spores and green slime anyway.
"""

from __future__ import annotations

import re

from . import ctx
from .mapview import DIR_KEY

try:
    from nh.kernel import INVISIBLE_MISS
except ImportError:        # (a daemon whose core predates it: `bin/nh reload` only loads new tactics)
    INVISIBLE_MISS = (r"^(?:The |An? )?.+? (?:(?:swings|snaps|kicks|lunges) wildly(?: and misses)?!|attacks a spot "
                      r"beside you\.|strikes at (?:thin air|empty water)!)$")

ROUTINE = [r"^You (hit|miss|kill|destroy) ", r"^You smite ", r"(bites|hits|misses|stings|butts|kicks|claws|touches)[!.]$",
           # an invisible fight's flavour (p1 shift 37 #470-#488, the Wizard and his clone): a monster going
           # invisible or zapping itself, MR shrugging off destroy armor, a quantum mechanic's teleport blocked
           # on a no-teleport level (a real teleport still pauses as TELEPORTED), hearing again, a unicorn horn
           # with nothing to fix
           r"^Suddenly you cannot see ", r" zaps (?:himself|herself|itself) with (?:an? |the )",
           r"^A field of force surrounds you!$", r"^Your position suddenly seems very uncertain!$",
           r"^A mysterious force prevents you from teleporting!$", r"^You can hear again\.$",
           r"^Nothing seems to happen\.$",
           # (p1 shift 40 #676/#679 in a hold loop) an intervention's flavour line; a spell of aggravation
           # (every monster on the level wakes and comes: what a hold is for)
           r"^You feel (?:vaguely nervous|that monsters are aware of your presence)\.$",
           r"^The .* (turns to flee|is killed|dies)", r"^You hear some noises", r"^Welcome to experience level",
           # the target stepped away before the blow (hack.c domove, F into an empty square); a monster
           # healing itself or reading itself away (muse.c) — fight() sees what's left and decides
           r"^You (?:harmlessly |futilely )?attack thin air\.$", r" looks (?:completely healed|much better|better)\.$",
           r" reads a scroll of teleportation!$",
           # monster chatter in melee (wizard.c cuss(), demon/imp taunts, quoted speech)
           r"casts aspersions on your ancestry", r"laughs fiendishly", r'^"[^"]*"$',
           # hit side effects that the HP check already covers
           r"^You get zapped!$", r"^You are (?:stung|bitten|kicked|butted)",
           # weapon-wielding monsters announce each swing (mhitu.c); leg attacks (xan)
           r"^The .+ (?:swings|thrusts) (?:his|her|its) (?!(?:cockatrice|chickatrice) corpse)",
           r" pricks your (?:left |right )?leg!$",
           # ranged/weapon flavour (the damage, if any, is caught by the HP checks); thefts still pause
           # (never "wields a cockatrice corpse": a gloved monster hitting you with one stones you)
           r"^The .+ wields (?:an? |the |\d+ )(?!.*\b(?:cockatrice|chickatrice) corpse)",
           r"^The .+ (?:throws|shoots|fires) ", r"^The .+ breathes ",
           r"^You are hit by ", r"^The .+ misses you[.!]$",
           # a monster that can't see you (invisible / displaced) swinging at the wrong square (mhitu.c wildmiss)
           INVISIBLE_MISS,
           r"^(?:The )?.+ (?:kicks|scratches|butts|stings|touches|bites) you[.!]$",   # also "Jay's ghost touches you!"
           # an engulfer's routine attack from inside (mhitu.c gulpmu()); the damage is the HP check's job
           r"^You feel your magical energy drain away", r"^You are pummeled with debris",
           r"^You are laden with moisture", r"^The air around you crackles with electricity",
           r"^You seem unhurt\.", r"^You feel mildly (?:chilly|hot)\.", r"^You are freezing to death",
           r"^You are burning to a crisp", r"^You are covered (?:with a seemingly harmless goo|in slime)",
           r"^You can't see in here", r"^You are jolted with electricity", r"^You are suddenly very (?:hot|cold)",
           # a passive you resist (uhitm.c passive(): Fire_resistance "mildly warm", ...)
           r"^You feel mildly (?:warm|chilly)\.", r"^You feel a mild (?:chill|tingle)\.",
           r"^You are (?:splashed|covered) by .* but it doesn't",
           # monster spellcasting (mcastu.c) whose damage the HP checks cover (curses, paralysis, lost
           # armor, summoned monsters still pause: their own messages / the new-monster check)
           r" casts a spell(?: at [\w' -]+)?!$", r"^Your skin itches", r"^You are hit by a shower of missiles",
           r"^The missiles bounce off", r"^You stiffen briefly", r"^A bolt of lightning strikes down at you",
           r"^It bounces off your ", r"^A pillar of fire strikes all around you", r"^You are uninjured\.",
           r"^A sudden geyser slams into you", r"^Your body is covered with (?:deadly|painful) wounds",
           r" looks better\.$",
           # a priest's spells (mcastu.c CLC_OPEN_WOUNDS / CLC_BLIND_YOU — the Blind status still pauses), a monster
           # reading/zapping aggravation at you (muse.c you_aggravate), a monster's cursed weapon welding (weapon.c)
           # — p2 shift 38 #229-#287 needed ~40 -a patterns for the Sanctum's priests
           r"^(?:Severe )?[Ww]ounds appear on your body!$", r"^Scales cover your [\w ]+!$",
           r"^For some reason, .+ presence is known to you\.$", r"^You feel aggravated at .+\.$",
           r" welds? (?:itself|themselves) to .+ hands?!$",
           r"^Your armor is covered with water", r"^You feel a malignant aura surround you\.$",
           # a temple priest hit in its temple: its god's lightning (the Blind status still pauses)
           r' roars in anger: +"Thou shalt suffer!"', r"^The bolt of lightning (?:hits you|whizzes by you)",
           r"^But it reflects from your ", r"^Your arms? tingles?\.",
           # missiles and potions flying at other monsters, monsters quaffing (the HP checks cover you)
           r"^The (?:\d+(?:st|nd|rd|th) )?[\w' -]+ (?:hits|misses) (?!you\b)(?:the |an? |it[.!]|[A-Z])",
           r" hurls (?:an? |the |\d+ )", r"^The [\w' -]+ crashes on your \w+ and breaks into shards\.",
           r"^The [\w' -]+ evaporates?\.$", r"^Crash!$", r" drinks (?:an? |the )[\w' -]+!$",
           r"^The [\w' -]+ misses[.!]$", r"^You are almost hit by ",
           # battles with armed crowds (the Castle): polearm thrusts from 2 squares (mthrowu.c thrwmu),
           # missiles named with an article, monsters dressing, cursed weapons, revivals, potions breaking
           # on others, create monster (the newcomers pause by themselves), rays that bounce or miss you
           r"^The .+ thrusts (?:an? |the )", r"^(?:An?|The) [\w' -]+ misses you[.!]$", r"^The .+ puts on ",
           r"^The .+ (?:is|are) welded to (?:his|her|its) hands?!$", r" rises from the dead!$",
           r"^The [\w' -]+ crashes on .+ and breaks into shards\.$", r"^The .+ reads a scroll of create monster!$",
           r"^The (?:magic missile|bolt of \w+|sleep ray|death ray|blast of [\w ]+|stream of \w+|ray of \w+|"
           r"fireball|cone of cold) (?:bounces|whizzes by you)!$",
           # other monsters' spells on themselves (mcastu.c: haste self, invisibility, cure self)
           r" is suddenly moving faster\.$", r" becomes transparent\.$", r"^The invisible .+ casts a spell"]
# a thrown/fired object hitting or missing ("The dagger misses the jackal.")
THROW_OK = ROUTINE + [r"^The .+ (hits|misses)( the .+| it)?[.!]$", r"^You (kill|destroy) "]
# a zapped ray/bolt doing its job ("The bolt of lightning hits the rope golem!"); hits on YOU still pause
_RAY = r"(?:magic missile|bolt of \w+|sleep ray|death ray|blast of [\w ]+|stream of \w+|ray of \w+|fireball|cone of cold)"
ZAP_OK = ROUTINE + [rf"^The {_RAY} (?:hits|misses|whizzes by) (?!you)", rf"^The {_RAY} bounces!",
                    r"^The wand (?:hits|misses) (?!you)", r"^Boing!$",
                    r"^The .+ (?:is killed|is destroyed|dies)", r"^You (?:kill|destroy) ",
                    r"^The .+ resists", r"^The .+ is not affected"]

_warned: set = set()
_warned_expl: set = set()


def _covetous(name) -> bool:
    """monst.c M3_COVETOUS (wants the Amulet/Bell/Book/Candelabrum/quest artifact): it teleports to you and
    away to heal — there is no point walking to where it was."""
    from nh.danger import monster_record
    rec = monster_record(name or "") or {}
    return any(f.startswith("M3_WANTS") for f in rec.get("flags3") or [])


_HOLD_RE = re.compile(r"^(?:You cannot escape from (?:the |an? )?(?P<a>.+?)!|(?:The |An? )?(?P<b>.+?) grabs you!)$")
_FREE_RE = re.compile(r" releases you\.$|^You (?:get|are) released|^You pull free|^You get expelled")


def _holder_from(messages) -> str | None:
    """The species holding you per the latest messages ("The owlbear grabs you!", "You cannot escape from
    the owlbear!"), or None (none, or released since)."""
    from nh.danger import base_name
    for msg in reversed(list(messages or [])):
        if _FREE_RE.search(msg):
            return None
        mm = _HOLD_RE.match(msg)
        if mm:
            return base_name(mm.group("a") or mm.group("b"))
    return None


def _ignores_elbereth(m) -> bool:
    try:
        from nh.game import ignores_elbereth
    except ImportError:          # (an older core)
        return m.get("ch") == "@"
    return ignores_elbereth(m)


def _elbereth_holds(s) -> bool:
    """You stand on an engraving last read as exactly 'Elbereth' where it works (monmove.c onscary(): not
    in Gehennom, not on the Planes). Monsters that can't see (blinded) ignore it all the same."""
    g = ctx.game
    if not hasattr(g, "on_elbereth") or not g.on_elbereth(s):
        return False
    key = g.level_key(s.status) if s.status.ok else ""
    return not (key or "").startswith(("Gehennom", "The Elemental Planes"))


def _ench_safe() -> bool:
    """zap.c drain_item(): a disenchanter's passive can't take enchantment from a weapon that defends
    against level drain (Excalibur, Stormbringer, the Staff of Aesculapius) or has none to lose (+0 or
    less); other artifacts resist it 9 times in 10."""
    w = getattr(ctx.game, "wielded", None) or ""
    if re.search(r"\b(?:Excalibur|Stormbringer|Staff of Aesculapius)\b", w):
        return True
    m = re.search(r"(?:^|\s)([+-]\d+) ", w)
    return m is not None and int(m.group(1)) <= 0


def _passive_refusal(desc: str, st) -> str:
    """Why fight() won't melee this monster without allow_passive (its
    passive paralyses/stones/slimes/disenchants, or can cost too much HP),
    or ''."""
    from nh.danger import STOP_PASSIVES, passive_attacks, passive_max
    if not desc:
        return ""
    pas = passive_attacks(desc)
    stops = [dt for dt, _txt in pas if dt in STOP_PASSIVES]
    if "AD_STON" in stops and getattr(ctx.game, "wielded", None):
        stops.remove("AD_STON")
    if "AD_ENCH" in stops and _ench_safe():
        stops.remove("AD_ENCH")
    if stops:
        return "; ".join(txt for _dt, txt in pas)
    pdmg, _pw = passive_max(desc, resists=getattr(ctx.game, "intrinsics", ()))
    if pdmg and st.ok and pdmg * 2 > st.hp:
        return f"passive up to {pdmg} HP"
    return ""


def _key_toward(hero, m):
    return DIR_KEY.get((m["x"] - hero[0], m["y"] - hero[1]))


def fight(x: int | None = None, y: int | None = None, stop_hp: float = 0.45, max_blows: int = 25,
          allow_passive: bool = False, only=None, force: bool = False, attack_peaceful: bool = False,
          near_water: bool = False):
    """Melee an adjacent hostile (the one at (x, y) if given) until it's gone,
    it moves out of reach, or HP falls below stop_hp * max (then pauses).
    Returns the final Snap.

    - Before the first blow at a monster type it prints the target's passive
      attacks (acid, rust, disenchant...); paralysing/stoning/sliming/
      disenchanting ones stop it unless allow_passive=True (fight those at
      range, or not at all).
    - Below stop_hp it keeps swinging only while the adjacent hostiles'
      worst-case damage per turn is under a third of your HP (a newt can't
      threaten 21 HP); otherwise it pauses.
    - fight(x, y) sticks to the monster that was there: if another species
      steps into the square after the kill, it stops and says so.
    - only=predicate: stop as soon as an adjacent hostile fails it (auto-fight
      uses auto_fightable, so a python joining a snake fight isn't meleed).
    - force=True: swing at an 'I' (unseen) square while blind — the guard
      refuses that by default (it may be a peaceful): e.g. blindfolded
      against Medusa, on the square telepathy/her last position shows; it
      also passes force to every blow (past the move guards: yours to judge).
      Hitting a monster that ignores Elbereth (@ humans/elves, minotaurs,
      shopkeepers, priests...) from your Elbereth square needs no force: no
      hypocrisy, but the blow smudges dust — re-engrave after.
    - HP pauses inside it follow the fight rules (kernel hp_rules): below
      stop_hp, a loss that would take you there in two more rounds, or a
      quarter of max HP in one step — not every blow below 70%.
    - An F blow NEVER asks "Really attack?" (uhitm.c attack_checks returns
      before the peaceful check), so before the first blow at each monster it
      looks at it (';', no game time) unless its label came from a look this
      turn; a peaceful/tame one pauses instead (a peaceful adult black naga
      labeled like the hostile hatchlings next to it). attack_peaceful=True
      hits it anyway (angering a peaceful costs alignment; killing one, more).
    - Next to water with a drowner (eel, kraken, an unseen monster) in it, it
      pauses before the first blow; near_water=True fights on there (a spot
      touching ONE water square, chosen on purpose: p1 shift 33 cleared the
      Wizard's moat one sea monster at a time) — force=True does too, but
      also passes every other guard."""
    import contextlib
    seen: list[str] = []
    rules = getattr(ctx, "hp_rules", None)
    try:
        with (rules(stop_hp) if rules is not None else contextlib.nullcontext()):
            return _fight(x, y, stop_hp, max_blows, allow_passive, seen, only, force, attack_peaceful, near_water)
    finally:
        last = ctx.last()
        if seen and last is not None:
            last.messages = seen + [m for m in last.messages if m not in seen]


def _danger_rank(desc: str) -> tuple:
    """Sort key, most dangerous first: a real danger note (not an info note like a ghost's), then the
    monster's difficulty."""
    from nh.danger import INFO_NOTES, NOTES, base_name, monster_record
    bn = base_name(desc)
    rec = monster_record(bn) or {}
    return (0 if bn in NOTES and bn not in INFO_NOTES else 1, -(rec.get("difficulty") or 0))


def rewield_main(who: str = "fight()"):
    """A tool a helper applied into your hands (a dig's pick-axe, a #rubbed lamp: "You now wield ...") is
    still there and your usual weapon is known and in the pack: wield the weapon again (one turn). p3 shift
    17 #231: after a paused tunnel(), fight() bashed a long worm with the pick-axe. Returns the snap after
    the swap, or None when nothing was done."""
    g = ctx.game
    mw = getattr(g, "main_weapon", None)
    s = ctx.last()
    if not mw or not getattr(g, "wield_tool", False) or not getattr(g, "wielded", None) \
            or s is None or s.state.kind != "command":
        return None
    from .items import inventory
    it = next((i for i in inventory() if i["letter"] == mw["letter"]), None)
    if it is None or not it["class"].startswith("Weapons") or not getattr(g, "wield_tool", False):
        return None
    tool = g.wielded
    s = ctx.do("w" + mw["letter"], ok=[r"^[a-zA-Z] - ", r"welded to your"] + ROUTINE)   # (p4 shift 3 #180)
    if any("welded" in m for m in s.messages):
        print(f"{who}: {tool} is WELDED to your hand (cursed) — fighting with it")
    else:
        print(f"{who}: wielded your weapon ({mw['letter']} - {it['text']}) again first — {tool} was in hand")
    return ctx.last()


def _wielding() -> bool:
    """Do you wield something? (cached by inventory(); asks once if unknown)"""
    w = getattr(ctx.game, "wielded", None)
    if w is None:
        from .items import inventory
        inventory()
        w = getattr(ctx.game, "wielded", None)
    return bool(w)


_WAND_WARNED: set = set()        # (level, monster name) already warned about by _wand_user_check


def _wand_user_check(m, who: str) -> None:
    """Pause ONCE per monster kind and level before closing in on / meleeing one that zapped a sleep or death
    wand at you that you don't resist (p3 shift 13: muse.c zaps offensive wands from next to you too — melee
    doesn't get you out of its line). cont() goes on."""
    from nh.danger import base_name
    s = ctx.last()
    name = base_name(m.get("desc") or "")
    rec = (getattr(s, "wand_users", None) or {}).get(name)
    if not rec or (rec.get("ids") and m.get("id") not in rec["ids"]):
        return          # (another monster of that name zapped: p2 shift 33 #1103)
    from nh.kernel import wand_danger
    reason = wand_danger(f"the {name} zapped {rec.get('wand') or 'a wand'}", rec.get("kind"), ctx.game)
    key = (ctx.game.level_key(s.status) if s.status.ok else None, name)
    if not reason or key in _WAND_WARNED:
        return
    _WAND_WARNED.add(key)
    ctx.pause(f"{who}: {reason}. Meleeing it keeps you in its line. cont() closes in anyway")


def _check_target(m) -> tuple:
    """Look at the monster about to get an F blow (no game time). Returns (snap, fresh monster dict at
    that square or None when nothing is there now)."""
    from .nav import farlook
    farlook(m["x"], m["y"])
    s = ctx.last()
    return s, next((t for t in s.monsters or [] if (t["x"], t["y"]) == (m["x"], m["y"])
                    and not t.get("statue")), None)


def _fight(x, y, stop_hp, max_blows, allow_passive, seen, only=None, force=False, attack_peaceful=False,
           near_water=False):
    """fight() body; `seen` collects every round's messages (so an early
    'You feel feverish' isn't lost behind later rounds)."""
    from nh.danger import STOP_PASSIVES, base_name, explodes_at_you, max_hit, passive_attacks, passive_max
    s = ctx.last()
    locked_on = None                 # fight(x, y): the species that was on (x, y) at the first blow
    unseen_hits = 0                  # blows at an unseen/warning-digit square in this fight
    checked: set = set()             # (id, x, y) of targets looked at before their first blow
    engulf_warned = False
    inside = False                   # swung from inside an engulfer during this call
    seen_notes: set = set()
    if s.state.kind == "command" and not getattr(s, "engulfed", False):
        s = rewield_main("fight()") or s
    t_first = s.status.turn if s.status.ok and s.status.turn is not None else 0
    for _ in range(max_blows):
        if s.state.kind != "command" or s.hero is None:
            return s
        st = s.status
        if getattr(s, "engulfed", False):
            # inside a monster: any direction hits it; walking away is impossible, so after one warning
            # keep swinging down to the prayer line (prayer is the only other way out)
            if st.ok and st.hp <= max(1, st.hpmax) // 7:
                ctx.pause(f"fight: engulfed and HP {st.hp}/{st.hpmax} is at the prayer line (1/7) — PRAY now "
                          "(pray()), or a teleport/escape item")
                return ctx.last()
            if st.ok and st.hp < stop_hp * max(1, st.hpmax) and not engulf_warned:
                engulf_warned = True
                ctx.pause(f"fight: engulfed and HP {st.hp}/{st.hpmax} is below {stop_hp:.0%} — cont() keeps "
                          "swinging (you can't walk out) down to 1/7, then pray")
            s = ctx.do("Fk", ok=ROUTINE + [r"^You (hit|miss) the ", r"^You get (expelled|regurgitated)"])
            seen.extend(s.messages)
            inside = True
            continue
        if inside:
            # the engulfer died or spat you out: you are back on the map, maybe beside other monsters and
            # off the square you had prepared (Elbereth) — a new situation, not more of the same fight
            print("fight: out of the engulfer (" + ("killed" if any(re.search(r"^You (?:kill|destroy) ", m)
                                                                    for m in seen) else "expelled")
                  + ") — stopped; look around before fighting on")
            return s
        if "Hallu" in st.conditions:
            ctx.pause("fight: hallucinating — can't tell hostile from peaceful (and NetHack won't ask). Attack "
                      "with do('F'+dir, force=True) only a monster that is attacking you, or retreat.")
            return ctx.last()
        targets = s.adjacent_hostiles()
        dizzy = {"Stun", "Conf"} & set(st.conditions)
        if dizzy and targets:
            # hack.c domove(): stunned, every blow goes in a random open direction (confused, 1 in 5), and
            # NetHack doesn't ask "Really attack?" then — never with a peaceful, your pet or a floating eye near
            near = [m for m in s.monsters or [] if m.get("dist") == 1 and not m.get("statue")
                    and (m.get("peaceful") or m.get("tame") or m.get("pet")
                         or base_name(m.get("desc") or "") in ("floating eye", "gas spore", "green slime"))]
            if near and not force:
                ctx.pause("fight: you are " + " and ".join({"Stun": "Stunned", "Conf": "Confused"}[c]
                                                          for c in sorted(dizzy)) + " — blows go astray "
                          + ("in a random direction" if "Stun" in dizzy else "1 time in 5")
                          + " and NetHack attacks WITHOUT asking: "
                          + ", ".join(f"{m.get('desc') or m['ch']} at ({m['x']},{m['y']})" for m in near)
                          + " next to you. Wait it out (do('s')) or step away once it wears off; force=True "
                            "swings anyway")
                return ctx.last()
            if "Stun" in dizzy and "stun" not in seen_notes:
                seen_notes.add("stun")
                hx, hy = s.hero
                n = sum(1 for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx or dy)
                        and s.screen.at(hx + dx, hy + dy) not in " -|")
                print(f"fight: Stunned — each blow goes in a random open direction (about 1 in {max(1, n)} "
                      "lands on the target; the others hit thin air); no peaceful/pet is next to you, so swinging")
        from .nav import drowners_adjacent
        drown = drowners_adjacent(s) if targets or any(m.get("unseen") and m.get("dist") == 1
                                                       for m in s.monsters or []) else []
        if drown and not force and not near_water and "drown" not in seen_notes:
            seen_notes.add("drown")
            ctx.pause("fight: you stand next to WATER with " + ", ".join(
                f"{m.get('desc') or 'an unseen monster'} at ({m['x']},{m['y']})" for m in drown[:3])
                + " in it — one wrap holds you and the next DROWNS you (levitation doesn't help). Step to a square "
                  "with no water next to it first and fight what follows you there (or Elbereth / freeze the "
                  "water); fight(..., near_water=True) to fight on here")
            return ctx.last()
        if x is None:
            from nh.monitor import _stationary
            sessile = [m for m in targets if _stationary(m.get("desc") or "")]
            if sessile and len(sessile) < len(targets):
                targets = [m for m in targets if m not in sessile]   # never waste blows on a mold/jelly
            elif sessile:
                print("fight: only sessile monsters next to you (" + ", ".join(m.get("desc") or m["ch"]
                                                                       for m in sessile)
                      + ") — they never move: step away instead (fight(x, y) to hit one on purpose)")
                return s
        if x is not None:
            if locked_on is None and any((m["x"], m["y"]) == (x, y) and m.get("statue") for m in s.monsters or []) \
                    and not any((m["x"], m["y"]) == (x, y) and not m.get("statue") for m in s.monsters or []):
                print(f"fight: ({x},{y}) holds a STATUE, not a monster — nothing to fight there")
                return s
            targets = [m for m in targets if (m["x"], m["y"]) == (x, y)]
            if not targets and unseen_hits and s.hero is not None and s.screen.at(x, y) not in "12345":
                # the unseen monster moved: its WARNING digit shows where it is now, while the square you hit may
                # keep a stale 'I' (p1 shift 38 #121/#136: an invisible Wizard jumping square to square; fight(x, y)
                # swung at thin air) — follow the one digit next to you
                digits = [(s.hero[0] + dx, s.hero[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                          if (dx or dy) and s.screen.at(s.hero[0] + dx, s.hero[1] + dy) in "12345"]
                if len(digits) == 1:
                    print(f"fight: the warning digit moved from ({x},{y}) to {digits[0]} — following it")
                    x, y = digits[0]
            if not targets and (s.screen.at(x, y) == "I" or s.screen.at(x, y) in "12345") \
                    and max(abs(x - s.hero[0]), abs(y - s.hero[1])) == 1:
                # an unseen (invisible) monster you asked for by square: swing at it — or a WARNING digit
                # (display.c display_warning(): only ever a hostile; p2 shift 34 #172: fight(49, 16) on a '5',
                # an iron golem next to a blindfolded hero, did nothing six times)
                s = ctx.do("F" + DIR_KEY[(x - s.hero[0], y - s.hero[1])], ok=ROUTINE, force=force)
                seen.extend(s.messages)
                unseen_hits += 1
                continue
            hidden = (getattr(s, "mimic_mem", None) or {}).get((x, y))
            if not targets and hidden and max(abs(x - s.hero[0]), abs(y - s.hero[1])) == 1 \
                    and "hidden" not in seen_notes:
                # a remembered mimic hiding as the object/boulder shown there: F attacks the square (it
                # unmasks: "Wait! That's a giant mimic!") and the next round fights it in the open
                seen_notes.add("hidden")
                print(f"fight: attacking the {hidden} hiding at ({x},{y}) (shown as {s.screen.at(x, y)!r})")
                s = ctx.do("F" + DIR_KEY[(x - s.hero[0], y - s.hero[1])],
                           ok=ROUTINE + [r"^Wait!\s+That's an? .*mimic!", r"^You (?:hit|miss) "], force=force,
                           expect=("stuck",))
                seen.extend(s.messages)
                continue
            if not targets and locked_on:
                recent = [m for t, m in list(getattr(ctx.game, "history", []))[-40:] if t is None or t >= t_first]
                killed = re.compile(r"^You (?:kill|destroy) (?:it\b|(?:the |an? |poor )?" + re.escape(locked_on) + ")")
                from nh.monitor import killed_names
                # (live shift 1b: the dog finished the newt — "The newt is killed!" — and fight() said "NOT
                # killed" while hunt() counted the kill)
                was_killed = any(re.search(r"^You (?:kill|destroy) ", m) for m in seen) \
                    or any(killed.search(m) for m in recent) or locked_on in killed_names(seen + recent)
                again = [m for m in s.adjacent_hostiles() if base_name(m.get("desc") or "") == locked_on] \
                    if not was_killed else []
                if again:
                    # it stepped to another square next to you, or a covetous one teleported back next to you
                    # (monmove.c: mnexto): same fight. (Not after the kill: another of its kind next to you —
                    # a sleeping soldier ant you meant to leave alone — is not this fight; p3 shift 10)
                    x, y = again[0]["x"], again[0]["y"]
                    print(f"fight: the {locked_on} is next to you again at ({x},{y}) — fighting it there")
                    continue
                if not was_killed:
                    moved = [m for m in s.monsters or [] if base_name(m.get("desc") or "") == locked_on
                             and not m.get("tame") and not m.get("statue")]
                    if moved:
                        m2 = min(moved, key=lambda m: m.get("dist") or 99)
                        print(f"fight: the {locked_on} stepped away from ({x},{y}) to ({m2['x']},{m2['y']}) "
                              f"(d={m2.get('dist')}) — NOT killed; hunt(({m2['x']}, {m2['y']})) goes after it")
                    else:
                        stair = (getattr(s, "feature_mem", None) or {}).get((x, y))
                        if stair in ("<", ">"):
                            # (p2 shift 34 #483: the hurt demilich on wizard3's up ladder fled up it)
                            print(f"fight: the {locked_on} at ({x},{y}) is gone — NOT killed: it stood on the "
                                  f"{'up' if stair == '<' else 'down'} stairs/ladder and probably took them (it "
                                  "waits at the arrival point on that level)")
                        else:
                            print(f"fight: the {locked_on} at ({x},{y}) is gone — NOT killed (it teleported, fled "
                                  "out of view or hid): look around (a covetous one teleports to heal and comes "
                                  "back)")
                return s
        if not targets:
            if "Blind" in st.conditions and any(m.get("unseen") and m.get("dist") == 1 for m in s.monsters or []):
                if getattr(ctx.game, "blindfolded", None):
                    print("fight: you are blindfolded — the monsters next to you show as 'I': fight(x, y, "
                          "force=True) on the 'I' you know is hostile (keep the blindfold on near Medusa)")
                else:
                    print("fight: you are Blind — the monsters next to you show as 'I' (unseen, maybe peaceful): "
                          "cure it (apply a unicorn horn) or fight(x, y, force=True) on an 'I' you know is hostile")
            return s
        if only is not None:
            bad = [t for t in s.adjacent_hostiles() if not t.get("statue") and not only(t)]
            if bad:
                print("fight: stopped — " + ", ".join(f"{t.get('desc') or t['ch']} at ({t['x']},{t['y']})"
                                                      for t in bad)
                      + " is next to you now and isn't a trivial target; your call")
                return s
        if x is not None:
            nm = base_name(targets[0].get("desc") or "")
            if locked_on is None:
                locked_on = nm
            elif nm and locked_on and nm != locked_on:
                print(f"fight: the {locked_on} at ({x},{y}) is gone — a {nm} is there now; stopped (fight({x}, "
                      f"{y}) again to attack it)")
                return s
        threats = s.adjacent_hostiles()
        if _elbereth_holds(s):
            # monmove.c onscary(): on a working Elbereth only the monsters that ignore it can attack you
            threats = [m for m in threats if _ignores_elbereth(m)]
        worst = sum(max_hit(m.get("desc") or "") for m in threats)
        if st.ok and st.hp < stop_hp * max(1, st.hpmax) and worst * 3 >= st.hp:
            ctx.pause(f"fight: HP {st.hp}/{st.hpmax} is below {stop_hp:.0%} and the adjacent hostiles can "
                      f"deal ~{worst}/turn — disengage? (Elbereth, retreat, pray if HP <= 1/7 max)")
            return ctx.last()
        # attack the most dangerous-looking adjacent target first (noted ones), else the first — but
        # never pick one the passive checks below refuse while another is there (a coyote beside a
        # floating eye gets the blow)
        # a monster HOLDING you comes first: while held, a blow at anything else only says "You cannot
        # escape from ..." (hack.c domove u.ustuck). Its label may predate the grab: the messages tell too
        holder = _holder_from([m for _t, m in list(getattr(ctx.game, "history", []))[-12:]] + list(seen))
        targets.sort(key=lambda m: ("holding you" not in (m.get("desc") or "")
                                    and not (holder and base_name(m.get("desc") or "") == holder),
                                    bool(allow_passive is False and _passive_refusal(m.get("desc") or "", st)),
                                    _danger_rank(m.get("desc") or "")))
        m = targets[0]
        desc = m.get("desc") or ""
        pas = passive_attacks(desc) if desc else []
        pdmg, pwhat = passive_max(desc, resists=getattr(ctx.game, "intrinsics", ())) if desc else (0, "")
        if pas and desc not in _warned:
            _warned.add(desc)
            print(f"fight: {desc} — passive: " + "; ".join(
                txt + (" — not your wielded weapon: it resists (drain resistance) or has no enchantment to "
                       "lose" if dt == "AD_ENCH" and _ench_safe() else "") for dt, txt in pas)
                  + (f" | worst case {pdmg} HP per hit ({pwhat})" if pdmg else ""))
        expl = explodes_at_you(desc) if desc else ""
        if expl and desc not in _warned_expl:
            # its explosion IS its attack (AT_EXPL): next to you it goes off on its own turn anyway, and a
            # killing blow never sets it off — so strike first (kill it at range before it gets here)
            _warned_expl.add(desc)
            print(f"fight: the {desc} is next to you and EXPLODES as its attack ({expl[3:].lower()}) — striking "
                  "first: a kill doesn't set it off; if it survives, it may go off on its turn")
        if base_name(desc) in ("mind flayer", "master mind flayer") and not force:
            helm = getattr(ctx.game, "helmet", None)
            iq = st.in_ if st.ok else 0
            if (iq and iq <= 6) or helm == "":
                ctx.pause(f"fight: not meleeing the {desc}: " + (f"your Int is {iq} — its brain-eating tentacles "
                          "kill you once Int is 3 (life saving doesn't help)" if iq and iq <= 6 else
                          "you wear NO helmet (inventory()) — every tentacle hit eats your brain (a helmet stops "
                          "7 in 8)") + ". Zap/throw at it, Elbereth, or leave; fight(..., force=True) to melee "
                          "anyway.")
                return ctx.last()
        from nh.danger import coaligned_unicorn
        if coaligned_unicorn(desc, st.align if st.ok else "") and not force:
            ctx.pause(f"fight: not attacking the {desc}: it is the unicorn of YOUR alignment — killing it costs 5 Luck "
                      "('You feel guilty...', mon.c xkilled(); your luckstone would keep the bad luck, and prayer "
                      "fails while Luck is negative). Walk away (it never closes in on you) or throw it a gem "
                      "(Luck +); fight(..., force=True) only if it is killing you")
            return ctx.last()
        if "WIELDS A COCKATRICE CORPSE" in (m.get("note") or "") and not force:
            ctx.pause(f"fight: not meleeing the {desc}: it WIELDS A COCKATRICE CORPSE — each of its hits starts "
                      "stoning you, and a melee keeps you next to it. Zap it away (teleport), kill it at range, or "
                      "leave; fight(..., force=True) to melee anyway (a lizard corpse ready)")
            return ctx.last()
        stops = [dt for dt, _txt in pas if dt in STOP_PASSIVES]
        if "AD_STON" in stops and _wielding():
            stops.remove("AD_STON")     # uhitm.c: only a bare-handed (no weapon, no gloves) hit petrifies you
        if "AD_ENCH" in stops and _ench_safe():
            stops.remove("AD_ENCH")     # drain-resistant (Excalibur) or unenchanted weapon: nothing to lose
        if not allow_passive and stops:
            ctx.pause(f"fight: not meleeing the {desc}: " + "; ".join(txt for _dt, txt in pas)
                      + ". Use ranged attacks or leave it (fight(..., allow_passive=True) to override).")
            return ctx.last()
        if not allow_passive and pdmg and st.ok and pdmg * 2 > st.hp:
            ctx.pause(f"fight: one hit on the {desc} can cost you up to {pdmg} HP from its passive ({pwhat}) and "
                      f"you have {st.hp}: rest first, fight it at range, or allow_passive=True.")
            return ctx.last()
        mk = (m.get("id"), m["x"], m["y"])
        if mk not in checked and not m.get("looked") and not m.get("unseen") and m["ch"] != "I":
            # uhitm.c attack_checks(): `if (context.forcefight) return FALSE;` comes BEFORE the "Really attack?"
            # question, so an F blow hits a peaceful without asking — and a label inherited from a look-alike
            # can be wrong (p2 shift 26: a peaceful black naga labeled as the hostile hatchlings beside it)
            checked.add(mk)
            old = desc
            from .nav import NavError
            try:
                s, m2 = _check_target(m)
            except NavError as e:
                ctx.pause(f"fight: couldn't look at the {old or m['ch']} at ({m['x']},{m['y']}) before hitting it "
                          f"({e}) — an F blow never asks 'Really attack?': check it with farlook() first")
                return ctx.last()
            if m2 is None or s.state.kind != "command" or s.hero is None:
                continue                          # it moved off (or a prompt came up): look again next round
            if (m2.get("peaceful") or m2.get("tame")) and not attack_peaceful:
                ctx.pause(f"fight: a look at ({m['x']},{m['y']}) shows a {m2.get('desc')}"
                          + (f" (its label said '{old}')" if old and old != m2.get("desc") else "")
                          + " — NOT attacking: an F blow never asks 'Really attack?'. Leave it be (or "
                            "fight(x, y, attack_peaceful=True) to anger it on purpose: -alignment, and "
                            "killing a peaceful costs more)")
                return ctx.last()
            checked.add((m2.get("id"), m2["x"], m2["y"]))
            if (m2.get("desc") or "") != old:
                print(f"fight: a look at ({m['x']},{m['y']}) shows a {m2.get('desc')} (was labeled '{old}')")
                continue                          # re-pick with the corrected label (passive/danger checks)
            m = m2
        _wand_user_check(m, "fight")
        key = _key_toward(s.hero, m)
        if key is None:
            return s
        if ctx.unwatch_monsters is not None and m.get("id") is not None:
            ctx.unwatch_monsters([m["id"]])           # (you are fighting it: its moves aren't news)
        s = ctx.do("F" + key, ok=ROUTINE, force=force or (attack_peaceful and bool(m.get("peaceful"))))
        seen.extend(s.messages)
    return s


def auto_fightable(m, s=None) -> bool:
    """A hostile the movement helpers may fight without asking: threat()
    'trivial' for you now, not sessile (molds: walk away instead), no passive
    attack, no danger note, seen clearly (not 'I', not while hallucinating)."""
    from nh.danger import base_name, passive_attacks, threat_level
    from nh.monitor import _stationary
    d = m.get("desc") or ""
    if not d or m.get("peaceful") or m.get("tame") or m.get("pet") or m.get("statue") or m.get("unseen") \
            or m.get("hallu") or m.get("mimic") or m.get("engulfer"):
        return False
    if "shape-shifted VAMPIRE" in (m.get("note") or ""):
        return False
    st = (s or ctx.last()).status
    from nh.danger import coaligned_unicorn
    if coaligned_unicorn(d, st.align if st.ok else ""):
        return False                    # -5 Luck (mon.c xkilled)
    if threat_level(d, st.xl if st.ok else None, st.hp if st.ok else None,
                    getattr(ctx.game, "intrinsics", ())) != "trivial":
        return False
    return not passive_attacks(base_name(d)) and not _stationary(d)


def not_auto_fightable(m) -> bool:
    """monster_filter predicate: pause only for newcomers the helpers won't fight."""
    return not auto_fightable(m)


def fight_trivial(s=None):
    """If hostiles are adjacent and every one of them is auto_fightable(),
    fight them (fight(): one checked blow at a time) and return the Snap;
    otherwise return None and do nothing."""
    s = s or ctx.last()
    adj = s.adjacent_hostiles()
    if not adj or not all(auto_fightable(m, s) for m in adj):
        return None
    if any(m.get("unseen") and m.get("dist") == 1 for m in s.monsters or []):
        return None          # an unseen 'I' next to you (an invisible attacker?): not a trivial situation
    if hasattr(ctx.game, "on_elbereth") and ctx.game.on_elbereth(s):
        return None          # attacking from Elbereth erases it and costs alignment: leave that to the player
    print("auto-fight: " + ", ".join(f"{m.get('desc')} at ({m['x']},{m['y']})" for m in adj))
    return fight(only=lambda m: auto_fightable(m))


def fight_until_clear(radius: int = 2, stop_hp: float = 0.5, max_turns: int = 60, patience: int = 6,
                      ignore=(), allow_passive: bool = False, hold: int = 0, unseen: bool = False,
                      near_water: bool = False, pause_new: str = "dangerous") -> dict:
    """Hold your square and fight a crowd (a zoo from its doorway, a pack in a
    corridor): melee whatever hostile comes adjacent (fight(): passive checks,
    worst-case HP rule), wait a turn while hostiles within `radius` aren't
    adjacent yet, and return when none is left within it.
    Newly seen monsters pause only when threat() rates them 'dangerous' (or
    they can't be rated); messages and status changes still pause as usual,
    HP loss by the fight rules (see fight()).
    Returns {"reason", "kills", "turns"}: reason "clear"; "HP ..." (below
    stop_hp: Elbereth / retreat / pray); "... not coming" (a hostile in range
    didn't approach for `patience` turns: trapped, slow or sessile — go to
    it or leave it); or "max_turns". ignore=('killer bee',): newcomers of
    these species never pause (a swarm you decided to fight); an outer
    monster_filter() block still applies too. allow_passive=True is passed
    to fight() (a cockatrice at a doorway, with your weapon wielded).
    hold=N: keep the square for N turns even while nothing is within the
    radius (search 's' each turn; whatever comes next to you is fought) —
    holding a chokepoint for a garrison that trickles in; reason "held".
    unseen=True: also swing (F) at an adjacent remembered unseen monster 'I' or warning digit 1-5
    (invisible attackers; never where a peaceful may be).
    Next to water with a sea monster (or an unseen 'I') in it, it returns
    "DROWNING RISK: ..." at once — step away from the water first
    (near_water=True fights on there).
    pause_new: which newcomers pause — "dangerous" (default: rated
    dangerous, or not looked at yet), "rated" (only looked-at ones rated
    dangerous: a crowd whose far members the harness hasn't looked at yet —
    the live game's Big Room paused 8 times in 10 turns), "never" (a crowd
    you chose to fight; fight() still refuses passive/NEVER-melee targets and
    the HP rules still pause)."""
    import contextlib
    from nh.danger import base_name, threat_level
    from nh.monitor import killed_names

    if pause_new not in ("dangerous", "rated", "never"):
        raise ValueError(f"fight_until_clear(pause_new={pause_new!r}): 'dangerous', 'rated' or 'never'")

    def dangerous(m):
        d = m.get("desc") or ""
        if pause_new == "never" or (d and base_name(d) in ignore):
            return False
        if not d:
            return pause_new == "dangerous"
        st = ctx.last().status
        return threat_level(d, st.xl if st.ok else None, st.hp if st.ok else None,
                            getattr(ctx.game, "intrinsics", ())) == "dangerous"

    ctx.require_command("fight_until_clear()")
    warn_bounce("fight_until_clear()")
    t0 = ctx.last().status.turn or 0
    kills: list = []
    best, idle = None, 0
    felt: set = set()          # 'I' squares a blind search already felt (unseen=True)
    search_marked: set = set()  # 'I' squares that appeared because OUR search felt a monster there (pet, peaceful)
    passed: set = set()        # 'I' squares left alone: couldn't tell it was the attacker

    def out(reason):
        return {"reason": reason, "kills": kills, "turns": (ctx.last().status.turn or t0) - t0}

    def adjacent_I(s1) -> set:
        h = s1.hero
        return {(x, y) for x in range(h[0] - 1, h[0] + 2) for y in range(h[1] - 1, h[1] + 2)
                if (x, y) != h and s1.screen.at(x, y) == "I"} if h is not None else set()

    def search_step():
        """One search: a blind search maps an 'I' on each monster it feels (detect.c mfind0(): "You feel an
        unseen monster!") — pets and peacefuls too: remember those squares, they are no attacker's mark."""
        before = adjacent_I(ctx.last())
        s1 = ctx.do("s", ok=ROUTINE + [r"^You feel an unseen monster", r"^You find "])
        after = adjacent_I(s1)
        felt.update(before | after)
        if any(m.startswith("You feel an unseen monster") for m in s1.messages):
            search_marked.update(after - before)
        return s1

    guard = ctx.monster_filter(dangerous) if ctx.monster_filter else contextlib.nullcontext()
    rules = getattr(ctx, "hp_rules", None)
    with guard, (rules(stop_hp) if rules is not None else contextlib.nullcontext()):
        # (a very fast hero acts ~2 times a turn: hold=40 ran out of loop steps at 33-35 turns — p3 shift 23 #359)
        for _ in range(max(max_turns, 3 * hold)):
            s = ctx.last()
            if s.state.kind != "command" or s.hero is None:
                return out(f"not at the command prompt ({s.state.kind}: {s.state.prompt!r})")
            if ctx.unwatch_monsters is not None:
                # holding a square to fight what comes: monsters closing in are the plan, not an 'approaching'
                # surprise (p2 shift 28: fire ants from the census watch list; shift 31: a gray dragon, a
                # demilich and Vlad reached the doorway in one step, before a radius+3 unwatch saw them) —
                # everything within max(radius + 8, 12), in view or just out of it (a teleporter)
                far = max(radius + 8, 12)
                near_ids = [m["id"] for m in s.monsters or [] if m.get("id") is not None
                            and m.get("dist") is not None and m["dist"] <= far]
                tr = getattr(ctx.game, "tracker", None)
                if tr is not None and hasattr(tr, "gone") and s.hero is not None:
                    near_ids += [r["id"] for r in tr.gone(s.status.turn) if r.get("id") is not None
                                 and max(abs(r["x"] - s.hero[0]), abs(r["y"] - s.hero[1])) <= far]
                ctx.unwatch_monsters(near_ids)
            st = s.status
            if st.ok and st.hp < stop_hp * max(1, st.hpmax):
                return out(f"HP {st.hp}/{st.hpmax} below {stop_hp:.0%} — Elbereth / retreat / pray if HP <= 1/7")
            from .nav import drowners_adjacent
            drown = drowners_adjacent(s)
            if drown and not near_water:
                return out("DROWNING RISK: " + ", ".join(f"{m.get('desc') or 'an unseen monster'} at ({m['x']},{m['y']})"
                                                         for m in drown[:3])
                           + " in the water next to you — step to a square with no water next to it and hold "
                             "there")
            from nh.monitor import _stationary
            # (a HIDDEN trapper/lurker above next to you acts only once found: a blow would un-hide it — leave it)
            from nh.danger import coaligned_unicorn
            align = s.status.align if s.status.ok else ""
            mobile_adj = [m for m in s.adjacent_hostiles() if not _stationary(m.get("desc") or "")
                          and "hiding" not in (m.get("desc") or "")
                          and not coaligned_unicorn(m.get("desc") or "", align)]
            if mobile_adj:
                s = fight(stop_hp=stop_hp, allow_passive=allow_passive, near_water=near_water)
                kills += killed_names(s.messages, include_it=True)
                best, idle = None, 0
                if s.adjacent_hostiles() and s.status.ok and s.status.hp < stop_hp * max(1, s.status.hpmax):
                    return out(f"HP {s.status.hp}/{s.status.hpmax} below {stop_hp:.0%} with hostiles adjacent")
                continue
            if unseen:
                blind = "Blind" in (s.status.conditions if s.status.ok else ())
                # (a passed 'I' stays a candidate while blind: it may start hitting you later)
                ivs = [m for m in s.monsters or [] if m.get("unseen") and m.get("dist") == 1
                       and (blind or (m["x"], m["y"]) not in passed)]
                if not ivs and s.hero is not None:
                    # a WARNING digit next to you (display.c display_warning(): only ever a hostile you can't
                    # see — p1 shift 37: the invisible Wizard showed as a '4')
                    ivs = [{"x": s.hero[0] + dx, "y": s.hero[1] + dy} for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                           if (dx or dy) and s.screen.at(s.hero[0] + dx, s.hero[1] + dy) in "12345"]
                adj_I = sorted((m["x"], m["y"]) for m in ivs if s.screen.at(m["x"], m["y"]) == "I") if blind else []
                key = _key_toward(s.hero, ivs[0]) if ivs and not adj_I else None
                if adj_I:
                    # BLIND, next to remembered unseen monsters 'I': an F blow never asks (uhitm.c attack_checks():
                    # context.forcefight) and the harness guard refuses it — a peaceful may stand there. A blind
                    # search feels every square round you (detect.c dosearch0() -> feel_location()): a stale 'I'
                    # goes; but it also MAPS an 'I' on every monster it feels (mfind0() -> map_invisible(): your
                    # pet, a shopkeeper...) — never swing at one of those. (p2 shift 39 #302 / p1 shift 41 #128:
                    # the PermissionError ended the fight; review of 4c3f55f: the forced blow hit the wrong 'I')
                    hider = any("hiding" in (m.get("desc") or "") and m.get("dist") == 1 for m in s.monsters or [])
                    if any(c not in felt for c in adj_I) and not hider:
                        s = search_step()
                        kills += killed_names(s.messages, include_it=True)
                        continue
                    cands = [c for c in adj_I if c not in search_marked]
                    if len(cands) == 1 and _unseen_melee(s):
                        # exactly one candidate, and something unseen MELEEd you ("It hits!" / "It misses!" — not a
                        # missile's "It misses."): that one is the attacker — lift only the blind-'I' guard for it
                        tgt = cands[0]
                        passed.discard(tgt)
                        ctx.game.blind_I_ok = tgt
                        try:
                            s = ctx.do("F" + _key_toward(s.hero, {"x": tgt[0], "y": tgt[1]}),
                                       ok=ROUTINE + [r"^You (?:harmlessly )?attack thin air",
                                                     r"^Wait!  There's (?:something|\w+) there"])
                        except PermissionError as e:
                            # (a daemon whose core predates game.blind_I_ok)
                            return out(f"blind: the guard refused the blow at the attacking 'I' {tgt} ({e}) — "
                                       f"fight({tgt[0]}, {tgt[1]}, force=True) if it is attacking you")
                        finally:
                            ctx.game.blind_I_ok = None
                        kills += killed_names(s.messages, include_it=True)
                        continue
                    new_pass = [c for c in adj_I if c not in passed]
                    passed.update(adj_I)
                    if new_pass:
                        print("fight_until_clear(): blind, unseen monster(s) at " + ", ".join(map(str, adj_I))
                              + (" — which one attacked can't be told" if len(cands) > 1 else
                                 " — felt by your own search, or no melee attack from it") + ": left alone "
                              "(fight(x, y, force=True) at the one hitting you)")
                if key:
                    s = ctx.do("F" + key, ok=ROUTINE + [r"^You (?:harmlessly )?attack thin air",
                                                        r"^Wait!  There's (?:something|\w+) there"])
                    kills += killed_names(s.messages, include_it=True)
                    continue
            # (p2 shift 38 #526/#532/#623: the ignored species and HIDDEN trappers/lurkers above — they never come —
            # ended holds as "not coming")
            near = [m for m in s.hostiles(radius) if not _stationary(m.get("desc") or "")
                    and base_name(m.get("desc") or "") not in ignore and "hiding" not in (m.get("desc") or "")
                    and not coaligned_unicorn(m.get("desc") or "", align)]
            if not near and hold and (s.status.turn or t0) - t0 < hold:
                # keep the square: wait for the next one to come — searching, unless a HIDDEN hider is next to you
                # (an explicit search un-hides it: detect.c mfind0 — and it engulfs)
                hider = any("hiding" in (m.get("desc") or "") and m.get("dist") == 1 for m in s.monsters or [])
                s = ctx.do(".", ok=ROUTINE) if hider else search_step()
                kills += killed_names(s.messages, include_it=True)
                continue
            if not near:
                if hold:
                    return out("held")
                t_now = s.status.turn or t0
                hist = [m for t, m in list(getattr(ctx.game, "history", []))[-30:]
                        if t is not None and t >= t_now - 2]
                ranged = [m for m in hist if re.search(
                    r"\bbreathes\b|^The (?:blast|bolt|ray|stream|cone|spray|sleep ray|death ray) .*hits you|"
                    r"^You are hit by |^It (?:breathes|spits|throws|shoots|zaps|casts)|^Something (?:breathes|hits)", m)]
                if ranged and not s.hostiles(radius):
                    # the attacker in view beyond the radius: named in the message, else a hostile lined up with
                    # you (p2 shift 39 #58: "The hell hound pup breathes fire!" from d=4 at radius=2 was reported
                    # as "out of view")
                    from nh.game import _lined_up
                    said = [base_name(mm.group(1)) for mm in (re.match(
                        r"^The (.+?) (?:breathes|spits|throws|shoots|zaps|casts)\b", r) for r in ranged) if mm]
                    far = [m for m in s.hostiles() if base_name(m.get("desc") or "") in said] or \
                          [m for m in s.hostiles() if s.hero is not None and _lined_up(s.hero, (m["x"], m["y"]))]
                    if far:
                        return out(f"attacked from BEYOND THE RADIUS ({ranged[-1]!r}) by " + ", ".join(
                            f"{m.get('desc') or m['ch']} at ({m['x']},{m['y']}) d={m.get('dist')}" for m in far[:3])
                                   + f" — nothing hostile within {radius}: go for it (hunt()/zap()/throw) or step "
                                     "out of its line; not 'clear'")
                    # (p1 shift 30: winter wolf cubs breathing frost down a dark corridor — nothing in view)
                    return out(f"attacked from OUT OF VIEW ({ranged[-1]!r}) — nothing hostile shows within {radius}: "
                               "telepathy_scan() / step out of that line; not 'clear'")
                beyond = [m for m in s.hostiles() if not _stationary(m.get("desc") or "")]
                recent = [g for g in getattr(s, "gone", None) or [] if (g.get("ago") or 0) <= 2]
                return out("clear" + (" (beyond the radius: " + ", ".join(
                    f"{m.get('desc') or m['ch']} at ({m['x']},{m['y']}) d={m['dist']}" for m in beyond[:3]) + ")"
                                      if beyond else "")
                           + (" — BUT " + ", ".join(f"{g['desc']} was at ({g['x']},{g['y']}) {g['ago']} turn(s) ago"
                                                     for g in recent[:2])
                              + " and left view: a hit-and-run in the dark (Vlad, a covetous caster)? wait a turn "
                                "(`s`) and look before moving on" if recent else "")
                           + (" — an unseen monster stays at " + ", ".join(map(str, sorted(passed)))
                              + " (it never attacked: left alone — a peaceful? fight(x, y, force=True) if not)"
                              if passed else ""))
            d = min(m["dist"] for m in near)
            if best is None or d < best:
                best, idle = d, 0
            else:
                idle += 1
            if idle >= patience and not (hold and (s.status.turn or t0) - t0 < hold):
                # (with hold=N the square is kept N turns whatever stays put in range — p3 shift 21 #313: a
                # hold=12 ended after 5 turns on a minotaur that took its time)
                who = ", ".join(f"{m.get('desc') or m['ch']} at ({m['x']},{m['y']})" for m in near[:4])
                mim = any("mimic" in (m.get("desc") or "") for m in near)
                return out((f"held {hold} turns — " if hold else "")
                           + f"{who} within {radius} but not coming for {idle} turns (trapped, slow or sessile?) "
                           "— go to it or leave it" + ("; a MIMIC re-hides as an object whenever you can't see "
                                                       "it — keep it in sight, or hunt() it" if mim else ""))
            s = ctx.do(".", ok=ROUTINE)
            kills += killed_names(s.messages, include_it=True)
    return out("max_turns")


def friendly_in_line(direction: str, ray: bool = False, s=None, maxlen: int = 13, gems: bool = False) -> list:
    """Tame/peaceful monsters in the straight line from you in `direction`.
    A thrown object stops at the first monster in its path, so only friends
    before the first hostile count; a ray (ray=True) passes through
    everything, so the whole line counts (bounces off walls aren't followed:
    mind them yourself). The unicorn of your alignment counts as a friend
    too (killing it costs 5 Luck) — except for a thrown gem (gems=True: it
    catches gems, and a gem it likes raises your Luck)."""
    from nh.danger import coaligned_unicorn
    from .mapview import KEY_DIR
    s = s or ctx.last()
    align = s.status.align if s.status.ok else ""
    d = KEY_DIR.get(direction)
    if d is None or s.hero is None:
        return []
    mons = {(m["x"], m["y"]): m for m in (s.monsters or [])}
    out = []
    x, y = s.hero
    for _ in range(maxlen):
        x, y = x + d[0], y + d[1]
        m = mons.get((x, y))
        if m is None:
            if s.screen.at(x, y) in " |-" and s.screen.color_at(x, y) != 3:
                break                       # rock or wall (a brown '|'/'-' is an open door)
            continue
        if m.get("tame") or m.get("peaceful") or m.get("pet") \
                or (not gems and coaligned_unicorn(m.get("desc") or "", align)):
            out.append(m)
        elif not ray and not m.get("unseen"):
            break                           # the first hostile stops a thrown object
    return out


def bounce_risk(s=None) -> list:
    """Hostiles with a breath weapon in a straight line from you (within 13
    squares) while a wall or rock is right behind you on that line: their ray
    hits you, bounces off the wall and hits you again. Returns
    [(monster, direction)]."""
    from nh.danger import base_name, monster_record
    s = s or ctx.last()
    if s.hero is None:
        return []
    hx, hy = s.hero
    out = []
    for m in s.hostiles():
        rec = monster_record(base_name(m.get("desc") or "")) or {}
        if not any(a.get("type") == "AT_BREA" for a in rec.get("attacks", [])):
            continue
        dx, dy = m["x"] - hx, m["y"] - hy
        if not (dx == 0 or dy == 0 or abs(dx) == abs(dy)) or max(abs(dx), abs(dy)) > 13:
            continue
        sx, sy = (dx > 0) - (dx < 0), (dy > 0) - (dy < 0)
        if s.screen.at(hx - sx, hy - sy) in " |-" and s.screen.color_at(hx - sx, hy - sy) != 3:
            out.append((m, (sx, sy)))
    return out


def warn_bounce(who: str, s=None) -> None:
    for m, _d in bounce_risk(s):
        print(f"{who}: !! you stand in line with the {m.get('desc')} at ({m['x']},{m['y']}), which BREATHES, with "
              "a wall right behind you: its ray hits you, bounces and hits you again — step off the line")


def _objects_in_line(direction: str, maxlen: int = 13, s=None) -> list:
    """Object squares on the straight line from you (up to a wall or rock)."""
    from .mapview import KEY_DIR
    s = s or ctx.last()
    d = KEY_DIR.get(direction)
    if d is None or s.hero is None:
        return []
    objs = {(o["x"], o["y"]) for o in s.objects if o["ch"] not in "0`"}
    out, (x, y) = [], s.hero
    for _ in range(maxlen):
        x, y = x + d[0], y + d[1]
        if s.screen.at(x, y) in " |-" and s.screen.color_at(x, y) != 3:
            break
        if (x, y) in objs:
            out.append((x, y))
    return out


# zap.c bhitm() WAN_PROBING: mstatusline() ("Status of the demilich (chaotic): Level 20 HP ...") and
# display_minventory() — "<Monnam>'s possessions:" in a menu, or "... is not carrying anything."
# (the status line splits at its double spaces: "Status of the hill orc (chaotic):", "Level 3", "HP 8(8)",
# "AC 10, peaceful.")
_PROBE_OK = [r"^Status of ", r"^Level \d+$", r"^HP \d+\(\d+\)$", r"^AC -?\d+(?:,.*)?\.$",
             r"^.+ is not carrying anything\.$", r"'s? possessions:$", r"^You probe towards "]


def _close_probe(s):
    """Probing opens an info-only menu of the monster's possessions (p2 shift 33 #268: the exec paused inside
    zap() with it open, and the next exec was refused): print it and close it (Esc, no game time)."""
    for _ in range(4):
        if s.state.kind not in ("menu", "text", "more"):
            break
        menu = getattr(s.state, "menu", None)
        if menu is not None and getattr(menu, "items", None):
            text = ([menu.title] if menu.title else []) + [
                (f"{i.letter} - " if i.letter else "") + i.text for i in menu.items if i.text.strip()]
        elif s.state.kind == "more" and s.state.more_text:
            text = [s.state.more_text]
        else:
            x0 = getattr(menu, "x0", 0) if menu is not None else 0
            text = [r for r in (s.screen.row(y)[x0:].strip() for y in range(0, 22)) if r]
        print("zap: " + " | ".join(text[:30])[:1500])
        s = ctx.do(s.state.dismiss if s.state.kind == "more" and getattr(s.state, "dismiss", None) else "<Esc>",
                   quiet=True)
    return s


def _tele_region_note(wand: str, before: list, s0) -> None:
    """A wand of teleportation at monsters inside a teleport-restricted area (desmap.TELE_BOXES: the Wizard's
    Tower, the fake towers, the Castle): teleport.c tele_jump_ok() keeps them inside it — say so."""
    item = next((i for i in getattr(ctx.game, "inv_items", None) or [] if i.get("letter") == wand), None)
    if not before or item is None or not re.search(r"\bteleportation\b", item.get("text") or ""):
        return
    from .desmap import in_box, tele_box
    box = tele_box(s0)
    if box is None:
        return
    inside = [m for m in before if in_box(box, (m["x"], m["y"]))]
    if inside:
        print("zap: " + ", ".join(f"the {m.get('desc') or m['ch']} at ({m['x']},{m['y']})" for m in inside[:3])
              + f" is inside this level's teleport-restricted area {box} (teleport.c tele_jump_ok): a teleport "
              "only moves it somewhere ELSE INSIDE that area — it can't be sent out of it")


_RAY_AT_MON = re.compile(rf"^The {_RAY} (?:hits|misses) (?!you\b)")
_RAY_BACK = re.compile(rf"^The {_RAY} (?:hits you|whizzes by you)|^But it reflects from your ")


def _reflected_note(before: list, s, s0=None) -> None:
    """zap.c dobuzz(): YOUR ray names every monster it passes ("The bolt of fire hits it.", "... misses the
    demilich."), except one that REFLECTS it out of your sight (mon_reflects() prints only if cansee()) — the
    ray just turns around. A monster in the line, no hit/miss line for any monster, and the ray coming back at
    you: it reflected (p2 shift 33 #247-#256: 4 fire charges at a demilich wearing an amulet of reflection)."""
    msgs = s.messages or []
    if not before or not any(re.match(rf"^The {_RAY} ", m) for m in msgs):
        return
    if any(_RAY_AT_MON.search(m) for m in msgs) or not any(_RAY_BACK.search(m) for m in msgs):
        return
    if any(re.match(r"^You (?:kill|destroy) ", m) for m in msgs):
        # dobuzz(): a ray that KILLS prints only xkilled()'s "You kill the Wizard of Yendor!" — then it
        # bounced off the wall behind and came back (p1 shift 36 #940/#999: a false REFLECTS note on the Wizard)
        return
    m = before[0]
    h = s0.hero if s0 is not None else None
    if h is not None:
        # a closed door between you and it bounces the ray back just the same (zap.c buzz(): closed_door())
        sx, sy = (m["x"] > h[0]) - (m["x"] < h[0]), (m["y"] > h[1]) - (m["y"] < h[1])
        c = (h[0] + sx, h[1] + sy)
        while c != (m["x"], m["y"]) and max(abs(c[0] - h[0]), abs(c[1] - h[1])) < 14:
            if s0.screen.at(*c) == "+" and s0.screen.color_at(*c) == 3:
                return
            c = (c[0] + sx, c[1] + sy)
    print(f"!! zap: the ray came back with NO hit/miss message for the {m.get('desc') or m['ch']} at "
          f"({m['x']},{m['y']}) — it probably REFLECTS rays (amulet of reflection / shield of reflection / silver "
          "dragon scales): stop zapping rays at it (melee, or a non-ray wand)")
    key = ctx.game.level_key(s.status) if s.status.ok else None
    if key is not None and m.get("id") is not None:
        if getattr(ctx.game, "reflectors", None) is None:
            ctx.game.reflectors = {}
        ctx.game.reflectors.setdefault(key, {})[m["id"]] = s.status.turn


def _freeze_note(direction: str, s0, s) -> None:
    """A cold ray over water: which squares froze (zap.c zap_over_floor(): each frozen square costs the ray 3 of
    its range, and Norep() prints "The moat is bridged with ice!" once — p2 shift 34 #351/#418: 2-3 squares per
    zap on wizard3's moat, blindfolded only "You hear a crackling sound."). Prints the frozen squares and the
    water still ahead on that line."""
    from .mapview import KEY_DIR
    d = KEY_DIR.get(direction)
    if d is None or s0 is None or s0.hero is None or s.state.kind != "command":
        return
    x, y = s0.hero
    froze, left = [], []
    for _ in range(20):
        x, y = x + d[0], y + d[1]
        if not (0 <= x < 80 and 1 <= y <= 21):
            break
        was, now = s0.screen.at(x, y), s.screen.at(x, y)
        if was == "}" and now != "}":
            froze.append((x, y))
        elif was == "}" and now == "}":
            left.append((x, y))
        elif was in "|- " and s0.screen.color_at(x, y) != 3:
            break
    if froze:
        print(f"zap: the ray FROZE {len(froze)} water square(s) {froze[:6]}"
              + (f"; water still ahead on that line at {left[:4]} — each frozen square shortens a ray by 3: zap "
                 "again from the new ice edge" if left else "")
              + " (ice melts again after a while)")


def _monsters_in_line(direction: str, maxlen: int = 13, s=None) -> list:
    """Monsters in view on the straight line from you (up to a wall or rock), nearest first."""
    from .mapview import KEY_DIR
    s = s or ctx.last()
    d = KEY_DIR.get(direction)
    if d is None or s.hero is None:
        return []
    mons = {(m["x"], m["y"]): m for m in s.monsters or [] if not m.get("statue") and m.get("ch") != "I"}
    out, (x, y) = [], s.hero
    for _ in range(maxlen):
        x, y = x + d[0], y + d[1]
        if s.screen.at(x, y) in " |-" and s.screen.color_at(x, y) != 3:
            break
        if (x, y) in mons:
            out.append(mons[(x, y)])
    return out


# mhitu.c hitmsg()/missmu(): a monster you can't see MELEEing you — "It hits!", "It bites!", "It misses!" /
# "It just misses!" (mthrowu.c thitu()'s missile miss while blind is "It misses." with a period: not melee)
_UNSEEN_MELEE = re.compile(r"^It (?:hits|bites|kicks|stings|butts)!$|^It touches you!$|^Its tentacles suck you!$|"
                           r"^It (?:just )?misses!$")


def _unseen_melee(s, turns: int = 3) -> bool:
    """Did something you can't see MELEE you in the last `turns` turns?"""
    now = s.status.turn if s.status.ok else None
    if now is None:
        return False
    return any(t is not None and t >= now - turns and _UNSEEN_MELEE.search(m)
               for t, m in list(getattr(ctx.game, "history", []))[-60:])


# mhitu.c: a monster you can't see attacking you is "It" ("It hits!", "It bites!", "It misses.")
_UNSEEN_ATTACK = re.compile(r"^It (?:hits|bites|stings|butts|kicks|claws|scratches|touches|misses|thrusts|swings|"
                            r"lashes|squeezes|grabs|smites|strikes|punches|whips|tickles|engulfs|gazes|breathes|"
                            r"spits|casts)\b|^You are (?:hit|stung|bitten|kicked|butted) by it\b")


def _unseen_attacked(s, turns: int = 3) -> bool:
    """Did something you can't see attack you in the last `turns` turns (the game's message history)?"""
    now = s.status.turn if s.status.ok else None
    if now is None:
        return False
    return any(t is not None and t >= now - turns and _UNSEEN_ATTACK.search(m)
               for t, m in list(getattr(ctx.game, "history", []))[-60:])


def _vanished(before: list, s, s0=None) -> list:
    """Monsters from `before` whose square no longer shows them and no kill message names them: a wand of
    teleportation / make invisible / polymorph leaves no message (p3 shift 12: a minotaur zapped away).
    s0: the snapshot before the zap (every monster then: a square one of them stood on isn't a new one's)."""
    from nh.danger import base_name
    from nh.monitor import killed_names
    shown = {(m["x"], m["y"]): m for m in s.monsters or []}
    killed = set(killed_names(s.messages, include_it=True))
    taken = {(o["x"], o["y"]) for o in ((s0.monsters if s0 is not None else None) or before)}
    out = []
    for m in before:
        now = shown.get((m["x"], m["y"]))
        if now is not None and now.get("ch") == m.get("ch"):
            continue
        name = (m.get("desc") or "").split(" [")[0]
        if name and any(k and k in name for k in killed):
            continue
        bn = base_name(name) if name else ""
        if bn and any(re.search(rf"\b{re.escape(bn)}\b", msg, re.I) for msg in s.messages or []):
            continue        # the zap named it ("The bolt of fire misses the warg."): it just moved (p1 shift 33)
        # one of its kind now on a free square near its old one: it stepped (p2 shift 39 #493: "the priestess
        # of Moloch is gone" — she had moved from (48,14) to (48,15))
        if any(max(abs(o["x"] - m["x"]), abs(o["y"] - m["y"])) <= 2 and (o["x"], o["y"]) not in taken
               and (base_name((o.get("desc") or "").split(" [")[0]) == bn if bn else o.get("ch") == m.get("ch"))
               for o in s.monsters or []):
            continue
        out.append(m)
    return out


def _refuse_friendly_fire(what: str, direction: str, ray: bool, force: bool, gems: bool = False) -> bool:
    if force:
        return False
    friends = friendly_in_line(direction, ray=ray, gems=gems)
    if not friends:
        return False
    who = ", ".join(f"{m.get('desc') or m['ch']} at ({m['x']},{m['y']})" for m in friends)
    ctx.pause(f"{what}: not firing {direction!r} — {who} is in the line of fire (the game won't ask). "
              f"Step aside / wait for it to move, or pass force=True.")
    return True


# dothrow.c thitmonst(): what can hit a monster when thrown — weapons (ammo, missiles, daggers...),
# weapon-tools, gems/rocks/gray stones, iron balls, boulders, eggs, cream pies, venom; a potion shatters
# on it (a Dex roll); food thrown at a dog, cat or horse can tame or pacify it. ANYTHING ELSE ALWAYS
# MISSES (tmiss()) and just lands there.
_THROW_CLASSES = ("Weapons", "Gems/Stones", "Potions", "Iron balls", "Boulders/Statues", "Venoms", "Coins")
_WEPTOOL = re.compile(r"\b(?:pick-axe|dwarvish mattock|broad pick|unicorn horns?|grappling hook|iron hook)\b")
_HIT_FOOD = re.compile(r"\b(?:eggs?|cream pies?)\b")
_DOMESTIC = re.compile(r"\b(?:little dog|dog|large dog|kitten|housecat|large cat|pony|horse|warhorse)\b")


def throw_can_hit(text: str, cls: str, target: str = "") -> bool:
    """Can this inventory item (its text and class header) hit a monster when thrown (thitmonst)?"""
    if cls in _THROW_CLASSES or _WEPTOOL.search(text or ""):
        return True
    if cls == "Comestibles":
        return bool(_HIT_FOOD.search(text or "")) or bool(_DOMESTIC.search(target or ""))
    return False


def _first_in_line(direction: str, s=None, maxlen: int = 13):
    """The first monster (not an unseen 'I') a thrown object would meet in `direction`, or None."""
    from .mapview import KEY_DIR
    s = s or ctx.last()
    d = KEY_DIR.get(direction)
    if d is None or s.hero is None:
        return None
    mons = {(m["x"], m["y"]): m for m in (s.monsters or [])}
    x, y = s.hero
    for _ in range(maxlen):
        x, y = x + d[0], y + d[1]
        m = mons.get((x, y))
        if m is not None and not m.get("unseen"):
            return m
        if m is None and s.screen.at(x, y) in " |-" and s.screen.color_at(x, y) != 3:
            return None
    return None


def throw(item: str, direction: str, count: bool = False, force: bool = False):
    """Throw inventory item `item` (a letter) in `direction` (y k u h l b j n
    < >), verifying each prompt. Refuses (pauses) when your pet or a
    peaceful stands between you and the first hostile in that direction,
    and when a monster is in that line but the item can't hit anything
    (not a weapon, weapon-tool, gem/rock, potion, egg or cream pie: such a
    throw ALWAYS misses; food at a dog/cat/horse is fine) — force=True
    throws anyway. Returns the final Snap."""
    ctx.require_command("throw()")
    gem = next((it for it in getattr(ctx.game, "inv_items", None) or [] if it.get("letter") == item
                and (it.get("class") or "").startswith("Gems")), None) is not None
    if _refuse_friendly_fire("throw", direction, ray=False, force=force, gems=gem):
        return ctx.last()
    first = _first_in_line(direction)
    target = first if not force else None
    if target is not None and not (target.get("tame") or target.get("pet")):
        from .items import inventory
        it = next((i for i in inventory() if i["letter"] == item), None)
        if it is not None and not throw_can_hit(it["text"], it["class"], target.get("desc") or ""):
            ctx.pause(f"throw: {item} - {it['text']} ({it['class']}) can't hit the "
                      f"{target.get('desc') or target['ch']} at ({target['x']},{target['y']}): thrown non-weapons "
                      "ALWAYS miss (dothrow.c thitmonst) and are lost on the floor. Throw weapons/daggers, "
                      "gems/rocks, potions or eggs/cream pies instead (force=True throws it anyway)")
            return ctx.last()
    s = ctx.do("t", quiet=True, force=force)
    if s.state.kind != "object":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        ctx.pause(f"throw: expected an item prompt, got {s.state.kind}: {s.state.prompt!r}")
        return ctx.last()
    s = ctx.do(item, quiet=True)
    if s.state.kind != "direction":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        ctx.pause(f"throw: expected 'In what direction?', got {s.state.kind}: {s.state.prompt!r}")
        return ctx.last()
    s = ctx.do(direction, ok=THROW_OK, force=force)
    if first is not None and first.get("peaceful") and not first.get("tame") and s.state.kind == "command":
        # a treat thrown at a peaceful domestic animal can tame it without a word (p3 shift 15 #1163: a candy bar
        # in the dark; the label stayed "peaceful"): look at it again, wherever it moved
        now = next((m for m in s.monsters or [] if first.get("id") is not None and m.get("id") == first["id"]),
                   None) or next((m for m in s.monsters or [] if (m["x"], m["y"]) == (first["x"], first["y"])), None)
        if now is not None:
            from .nav import farlook
            try:
                d = farlook(now["x"], now["y"])
            except Exception:  # noqa: BLE001  (a look is a courtesy)
                d = ""
            if d:
                print(f"throw: the monster at ({now['x']},{now['y']}) now looks like: {d}")
            s = ctx.last()
    return s


class WandEmpty(RuntimeError):
    """zap() of a wand that said "Nothing happens" last time (0 charges): catch it to try another wand."""


def zap(wand: str, direction: str | None = None, force: bool = False):
    """Zap wand `wand` (a letter) in `direction` (or None for non-directional
    wands). Sends the direction only if the game actually asks for one (an
    empty wand says "Nothing happens" and asks nothing). Refuses (pauses)
    when your pet or a peaceful is anywhere on the straight line (rays and
    beams go through monsters; force=True to zap anyway). A wand known to be
    EMPTY raises WandEmpty (no game time) — `except WandEmpty:` tries the next
    one; force=True wrests at it. A zap that finds the wand empty ("Nothing
    happens": a turn, no charge) raises WandEmpty right away too."""
    ctx.require_command("zap()")
    empty = getattr(ctx.game, "empty_wands", None)
    if empty and wand in empty and not force:
        # (p1 shift 32: a pause here broke the script's fallback loop over several wands)
        raise WandEmpty(f"zap: wand {wand} said \"Nothing happens\" last time — it is EMPTY (0 charges): recharge "
                        "it (scroll of charging) or use another; zap(..., force=True) tries to wrest a last charge "
                        "(1 in 121 per zap, a turn each)")
    if direction and _refuse_friendly_fire("zap", direction, ray=True, force=force):
        return ctx.last()
    if direction == ">":
        from .nav import castle_below, castle_pause
        if castle_below():
            from .items import inventory
            if any(i["letter"] == wand and re.search(r"\bdigging\b", i["text"]) for i in inventory()):
                castle_pause("zap(digging, '>')")
    if direction:
        objs = _objects_in_line(direction)
        if objs:
            print(f"zap: objects on the line {objs[:4]} — a beam goes on past a monster: striking/force bolt "
                  "BREAKS potions and glass there, fire burns scrolls/potions, teleportation sends them away, "
                  "polymorph changes them, undead turning revives corpses")
    s0 = ctx.last()
    s = ctx.do("z", quiet=True, force=force)
    if s.state.kind != "object":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        ctx.pause(f"zap: expected an item prompt, got {s.state.kind}: {s.state.prompt!r}")
        return ctx.last()
    # quiet: the empty-wand verdict must come before any pause on what else happened this turn (p1 shift 37
    # #468: "Nothing happens. | The Wizard of Yendor zaps himself with a hexagonal wand! | ..." paused as a
    # message, and the script's `except WandEmpty:` melee fallback never ran with the Wizard adjacent)
    s = ctx.do(wand, quiet=True)
    others = [m for m in s.messages if not m.startswith("Nothing happens")]
    if s.state.kind == "command" and any(m.startswith("Nothing happens") for m in s.messages):
        # zap.c dozap(): !zappable() — a wand with 0 charges (or cancelled) does nothing, asks no direction and
        # spends no charge
        if getattr(ctx.game, "empty_wands", None) is None:
            ctx.game.empty_wands = set()
        ctx.game.empty_wands.add(wand)
        print(f"zap: wand {wand} is EMPTY (\"Nothing happens\": 0 charges) — recharge it (scroll of charging); "
              "zap() now refuses it unless force=True (wresting a last charge: 1 in 121 per zap)")
        if not force:
            # (p1 shift 34 #206: returning normally skipped the script's `except WandEmpty:` fallback this turn)
            raise WandEmpty(f"zap: wand {wand} is EMPTY — \"Nothing happens\" (0 charges; the turn is spent)"
                            + (f"; also this turn: {' | '.join(others[:4])}" if others else ""))
    elif s.state.kind == "command" and others:
        news = [m for m in others if m not in (ctx.quiet_messages(others) if ctx.quiet_messages else [])]
        if news and direction is None:
            print(f"zap: {' | '.join(news[:4])}")        # (a NODIR wand's effect: said below)
        elif news:
            ctx.pause(f"zap: {' | '.join(news[:4])}")
    if s.state.kind == "direction":
        if direction is None:
            ctx.do("<Esc>", quiet=True)
            ctx.pause("zap: the wand wants a direction but none was given")
            return ctx.last()
        before = _monsters_in_line(direction, s=s0)        # (the snap before 'z': the hero was on the map)
        _tele_region_note(wand, before, s0)
        s = ctx.do(direction, ok=ZAP_OK + _PROBE_OK, force=force)
        s = _close_probe(s)
        gone = _vanished(before, s, s0) if s.state.kind == "command" else []
        if gone:
            print("zap: " + ", ".join(f"the {m.get('desc') or m['ch']} at ({m['x']},{m['y']})" for m in gone[:3])
                  + " is gone from that square — no message (teleported, turned invisible, or changed shape?)")
        _reflected_note(before, s, s0)
        _freeze_note(direction, s0, s)
        return s
    if direction and not any(m.startswith("Nothing happens") for m in s.messages):
        # zap.c zapnodir(): no direction asked = a NODIR wand (light, secret door detection, create monster,
        # enlightenment, wishing); an unknown one says which by what happened
        print(f"zap: wand {wand} asked NO direction — a non-directional wand (light / secret door detection / "
              f"create monster / enlightenment / wishing): {s.messages or 'no message'}")
    return s


# closing in on a monster: its ranged attacks' flavour (the HP/status checks cover the effects; a
# confusing or sleep gaze still pauses — "gaze confuses you", "gaze makes you very sleepy")
HUNT_OK = ROUTINE + [r" attacks you with a fiery gaze!$", r" spits venom!$", r"^The venom (?:hits|misses) you",
                     r"^You are hit by ", r"^The .+ (?:whizzes by|misses) you[.!]$",
                     r"^It's (?:solid stone|a wall)\.$"]


def _greedy_step(s, goal, bad, blank_ok: bool = False) -> tuple | None:
    """A square next to you, closer to `goal`, that is known floor (or, while you are BLIND or `blank_ok` —
    walking into a dark room toward a sensed monster — a blank: you don't see the squares next to you then;
    otherwise a blank next to you is rock) and not a known trap, water, wall or monster; never diagonally
    into or out of a doorway."""
    from .mapview import is_door, is_walkable, neighbors
    h = s.hero
    occupied = {(m["x"], m["y"]) for m in s.monsters or []}
    blind = blank_ok or (s.status.ok and "Blind" in s.status.conditions)
    best = None
    for c in neighbors(*h):
        if c in bad or c in occupied or c == goal:
            continue
        ch = s.screen.at(*c)
        if not (is_walkable(s, *c, allow_monsters=False) or (ch == " " and blind)):
            continue
        if c[0] != h[0] and c[1] != h[1] and (is_door(s, *h) or is_door(s, *c)):
            continue
        d = (max(abs(c[0] - goal[0]), abs(c[1] - goal[1])), abs(c[0] - goal[0]) + abs(c[1] - goal[1]))
        if d[0] < max(abs(h[0] - goal[0]), abs(h[1] - goal[1])) and (best is None or d < best[0]):
            best = (d, c)
    return best[1] if best else None


def _sensed_at(s, target) -> dict | None:
    """A non-tame, non-peaceful monster that telepathy_scan() sensed at `target` on this level within the last
    30 turns (game.last_scan), else None."""
    scan = getattr(ctx.game, "last_scan", None)
    if not scan or not s.status.ok or scan.get("level") != ctx.game.level_key(s.status) \
            or (s.status.turn or 0) - (scan.get("turn") or 0) > 30:
        return None
    return next((m for m in scan.get("mons") or [] if (m["x"], m["y"]) == tuple(target)
                 and not (m.get("desc") or "").startswith(("tame ", "peaceful "))), None)


def _ignored(m, ignore) -> bool:
    """hunt(ignore=...): a species name / names (matched against the label) or a predicate."""
    if not ignore:
        return False
    if callable(ignore):
        try:
            return bool(ignore(m))
        except Exception:  # noqa: BLE001
            return False
    names = (ignore,) if isinstance(ignore, str) else tuple(ignore)
    d = (m.get("desc") or "").lower()
    return any(str(n).lower() in d for n in names)


def _hunt_hidden_mimic(target, stop_hp, out, kills) -> dict:
    """hunt((x, y)) on a remembered mimic hiding as an object: walk next to it (never onto it), then
    fight(x, y) — the first blow unmasks it."""
    from nh.monitor import killed_names
    from .mapview import bfs_path
    from .nav import NavError, bad_squares, walk_path
    s = ctx.last()
    tx, ty = target
    name = (getattr(s, "mimic_mem", None) or {}).get(target, "mimic")
    if max(abs(tx - s.hero[0]), abs(ty - s.hero[1])) > 1:
        bad = frozenset(bad_squares(s))
        best = None
        for g in [(tx + dx, ty + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]:
            p = bfs_path(s, s.hero, g, avoid=bad - {g}, allow_monsters=False, allow_pets=True)
            if p is not None and (best is None or len(p) < len(best)):
                best = p
        if best is None:
            return out(f"no route next to the {name} hiding at {target}")
        try:
            s = walk_path(best)
        except NavError as e:
            return out(f"blocked: {e}")
        if s.hero is None or max(abs(tx - s.hero[0]), abs(ty - s.hero[1])) > 1:
            return out(f"stopped on the way to the {name} hiding at {target} (at {s.hero})")
    s = fight(tx, ty, stop_hp=stop_hp)
    kills += killed_names(s.messages, include_it=True)
    gone = target not in (getattr(ctx.last(), "mimic_mem", None) or {})
    return out("killed" if gone else f"fought the {name} at {target} (not dead yet: fight({tx}, {ty}) again)")


def _desmap_step(s, goal, avoid=frozenset()):
    """The first step of desmap.route() toward goal when this level's fixed map is identified: a walkable
    square next to you, not a trap, an undiscovered secret door, a water-edge square to avoid or a monster.
    None otherwise."""
    ids = (getattr(ctx.game, "desmap_ids", None) or {}).get(ctx.game.level_key(s.status)) if s.status.ok else None
    if not ids or ids.get("ambiguous") or s.hero is None:
        return None
    try:
        from . import desmap
        r = desmap.route(goal[0], goal[1], s=s)
    except Exception:  # noqa: BLE001  (no route on the map either)
        return None
    from nh.parse import MONSTER_CHARS
    path = r.get("path") or []
    if len(path) < 2:
        return None
    c = path[0]
    if c in (r.get("secret") or ()) or c in (r.get("traps") or ()) or c in avoid \
            or s.screen.at(*c) in MONSTER_CHARS or max(abs(c[0] - s.hero[0]), abs(c[1] - s.hero[1])) != 1:
        return None
    return c


def hunt(target, max_turns: int = 30, stop_hp: float = 0.45, ignore=None, near_water: bool = False) -> dict:
    """Close in on one hostile and fight it: target = part of its label
    ('pyrolisk') or its square (x, y). Each turn: adjacent -> fight() it
    (all of fight()'s checks); otherwise ONE checked step along a known-map
    route toward it (never onto another monster; its fiery gaze, spit or
    missiles don't pause — HP pauses follow the fight rules, new monsters and
    statuses still pause). Trivial hostiles in the way are fought.
    Returns {"reason", "turns", "kills"}: reason "killed", "lost: ..." (out
    of view: it first follows it up to 6 steps toward where it was last seen,
    and hunts on if it shows up again), "HP ...", "blocked: ..." (another
    non-trivial hostile next to you), "no route ..." or "max_turns".
    ignore: monsters next to you that don't block the hunt — species names
    (ignore=('ghost',) in a morgue of sleepers) or a predicate on the monster.
    near_water=True: walk beside water with a drowner in it anyway (like
    travel(..., near_water=True)): you levitate/wear a greased or oilskin
    cloak, or accept the wrap risk."""
    import contextlib
    from nh.danger import base_name
    from nh.monitor import killed_names
    from .benign import BENIGN
    from .mapview import DIR_KEY, bfs_path
    from .nav import NavError, _check_free, bad_squares
    s = ctx.require_command("hunt()")
    t0 = s.status.turn or 0
    kills: list = []
    want = species = None
    warned_others = False
    tried: set = set()                 # frontier squares already tried on the way to a far target
    chase = 0                          # steps taken toward where the target was last seen

    def out(reason):
        return {"reason": reason, "turns": (ctx.last().status.turn or t0) - t0, "kills": kills}

    rules = getattr(ctx, "hp_rules", None)
    with (rules(stop_hp) if rules is not None else contextlib.nullcontext()):
        for _ in range(max_turns):
            s = ctx.last()
            if s.state.kind != "command" or s.hero is None:
                return out(f"not at the command prompt ({s.state.kind}: {s.state.prompt!r})")
            st = s.status
            if st.ok and st.hp < stop_hp * max(1, st.hpmax):
                return out(f"HP {st.hp}/{st.hpmax} below {stop_hp:.0%}")
            if getattr(s, "engulfed", False):
                s = fight(stop_hp=stop_hp)             # inside it: any direction hits the engulfer
                kills += killed_names(s.messages, include_it=True)
                if getattr(s, "engulfed", False):
                    return out("still ENGULFED (fight() stopped: HP) — pray at 1/7 HP")
                continue
            if want is None:
                hs0 = [m for m in s.hostiles() if not m.get("statue")]
                hs = [m for m in hs0 if (m["x"], m["y"]) == tuple(target)] if isinstance(target, tuple) else \
                    [m for m in hs0 if str(target).lower() in (m.get("desc") or "").lower()]
                sensed = _sensed_at(s, tuple(target)) if isinstance(target, tuple) else None
                if not hs and sensed is not None:
                    # moved since the scan: the same kind shown near where it was sensed
                    bn = base_name(sensed.get("desc") or "")
                    hs = [m for m in hs0 if bn and base_name(m.get("desc") or "") == bn
                          and max(abs(m["x"] - target[0]), abs(m["y"] - target[1])) <= 3]
                if not hs and isinstance(target, tuple) and \
                        tuple(target) in (getattr(s, "mimic_mem", None) or {}):
                    return _hunt_hidden_mimic(tuple(target), stop_hp, out, kills)
                if not hs and isinstance(target, tuple) and sensed is None:
                    # (p1 shift 36 #284: the stone giant meant had just stepped from (23,11) to (22,12)) — ONE
                    # hostile within 2 squares of the given square is the one that moved
                    near = [m for m in hs0 if max(abs(m["x"] - target[0]), abs(m["y"] - target[1])) <= 2]
                    if len(near) == 1:
                        print(f"hunt: nothing at {tuple(target)} now — the {near[0].get('desc') or near[0]['ch']} "
                              f"at ({near[0]['x']},{near[0]['y']}) beside it is taken for the one that moved")
                        hs = near
                if not hs and sensed is not None:
                    # p1 shift 35 #173: sensed by telepathy_scan() in the dark, gone from view with the blindfold
                    # off — walk toward that square until it shows (a monster next to you is seen, dark or not)
                    what = f"the {sensed.get('desc') or 'monster'} telepathy_scan() sensed at {tuple(target)}"
                    digit = min(((x, y) for x in range(target[0] - 2, target[0] + 3)
                                 for y in range(target[1] - 2, target[1] + 3) if s.screen.at(x, y) in "12345"),
                                key=lambda c: max(abs(c[0] - target[0]), abs(c[1] - target[1])), default=None)
                    if digit is not None and max(abs(s.hero[0] - digit[0]), abs(s.hero[1] - digit[1])) == 1:
                        # p1 shift 39 #12: the sensed zruty showed only as warning digit '3' — the digit IS it
                        print(f"hunt: {what} shows as warning digit {s.screen.at(*digit)!r} at {digit}: fighting it")
                        s = fight(digit[0], digit[1], stop_hp=stop_hp, near_water=near_water)
                        kills += killed_names(s.messages, include_it=True)
                        if s.state.kind != "command":
                            return out("fight() stopped at a prompt")
                        if s.screen.at(*digit) in "12345" and ctx.last().status.ok:
                            return out(f"fight() stopped with the warning digit still at {digit} (see its message)")
                        return out("killed" if kills else f"the monster at {digit} is gone (no kill seen)")
                    if max(abs(s.hero[0] - target[0]), abs(s.hero[1] - target[1])) <= 1 or chase >= 12:
                        return out(f"no hostile {target!r} in view: {what} isn't there now (moved away, or "
                                   "invisible: F-attack the square or search) — telepathy_scan() again")
                    chase += 1
                    bad = frozenset(bad_squares(s) - {tuple(target)})
                    path = bfs_path(s, s.hero, tuple(target), avoid=bad, allow_monsters=False, allow_pets=True)
                    nxt = path[0] if path and len(path) > 1 else _greedy_step(s, tuple(target), bad, blank_ok=True)
                    if nxt is None:
                        return out(f"no route toward {what}")
                    try:
                        _check_free(s, nxt, "hunt()")
                    except NavError as e:
                        return out(f"blocked on the way toward {what}: {e}")
                    s = ctx.do(DIR_KEY[(nxt[0] - s.hero[0], nxt[1] - s.hero[1])],
                               ok=HUNT_OK + BENIGN + [r"^The door opens\.$"])
                    kills += killed_names(s.messages, include_it=True)
                    continue
                if not hs:
                    return out(f"no hostile {target!r} in view")
                m = min(hs, key=lambda e: e["dist"] if e["dist"] is not None else 99)
                want, species = m.get("id"), base_name(m.get("desc") or "")
                _wand_user_check(m, "hunt")
                if ctx.unwatch_monsters is not None and want is not None:
                    ctx.unwatch_monsters([want])      # (p2 shift 27: 'approaching:' for the very target)
            else:
                m = next((e for e in s.monsters or [] if e.get("id") == want), None)
                if m is None:
                    if species and species in kills:
                        return out("killed")
                    # out of view (round a corner, past telepathy's reach): follow it to where it was last
                    # seen for a few steps — it keeps its id if it shows up again
                    tr = getattr(ctx.game, "tracker", None)
                    rec = (getattr(tr, "recent", None) or {}).get(want) if tr is not None else None
                    last = (rec["x"], rec["y"]) if rec else None
                    near = [e for e in s.adjacent_hostiles() if not auto_fightable(e, s)]
                    if near:
                        return out(f"lost: the {species or target} is out of view, and "
                                   + ", ".join(f"{e.get('desc') or e['ch']} at ({e['x']},{e['y']})" for e in near[:3])
                                   + " is next to you — your call")
                    if last and chase < 6 and s.hero != last and not _covetous(species):
                        chase += 1
                        path = bfs_path(s, s.hero, last, avoid=frozenset(bad_squares(s) - {last}),
                                        allow_monsters=False, allow_pets=True)
                        if path:
                            try:
                                _check_free(s, path[0], "hunt()")
                            except NavError:
                                path = None
                        if path:
                            s = ctx.do(DIR_KEY[(path[0][0] - s.hero[0], path[0][1] - s.hero[1])],
                                       ok=HUNT_OK + BENIGN + [r"^The door opens\.$"])
                            kills += killed_names(s.messages, include_it=True)
                            continue
                    if _covetous(species):
                        return out(f"lost: the {species} teleported away — COVETOUS: it heals (usually on the "
                                   "up stairs) and comes back next to you; telepathy_scan() shows where it is. Stay "
                                   "ready at full HP; walking after it is pointless")
                    return out(f"lost: the {species or target} is out of view"
                               + (f" (last seen at {last}; followed {chase} step(s))" if last else ""))
                chase = 0
            from nh.monitor import _stationary
            others = [e for e in s.adjacent_hostiles() if e is not m and not auto_fightable(e, s)
                      and not _stationary(e.get("desc") or "")      # a mold can't follow: walk on past it
                      and not _ignored(e, ignore)]
            if others and m["dist"] != 1:
                return out("blocked: " + ", ".join(f"{e.get('desc') or e['ch']} at ({e['x']},{e['y']})"
                                                   for e in others) + " is next to you — your call")
            if m["dist"] == 1:
                if others and not warned_others:
                    warned_others = True
                    print("hunt: " + ", ".join(f"{e.get('desc') or e['ch']} at ({e['x']},{e['y']})" for e in others)
                          + f" is next to you too — fighting the {species or target} first (fight()'s HP checks "
                          "count every adjacent hostile)")
                s = fight(m["x"], m["y"], stop_hp=stop_hp, near_water=near_water)
                kills += killed_names(s.messages, include_it=True)
                if s.state.kind == "command" and any(e.get("id") == want for e in s.adjacent_hostiles()) \
                        and not killed_names(s.messages):
                    return out("fight() stopped with it still next to you (see its message)")
                continue
            if s.adjacent_hostiles():
                fs = fight_trivial(s)
                if fs is not None:
                    kills += killed_names(fs.messages, include_it=True)
                    continue
            goal = (m["x"], m["y"])
            from .nav import _eel_zone, squeaky_boards
            boards = squeaky_boards(s)      # (they only squeak: a hunt crosses them)
            # squares next to water where a drowning monster may be (p2 shift 25: hunt walked beside the
            # Castle moat with a giant eel adjacent — travel() avoided it, hunt() didn't)
            zone = {} if near_water else {c: w for c, w in _eel_zone(s).items() if c not in (s.hero, goal)}
            path = bfs_path(s, s.hero, goal, avoid=frozenset((bad_squares(s) | set(zone)) - {goal} - boards),
                            allow_monsters=False, allow_pets=True)
            if not path and zone:
                wet = bfs_path(s, s.hero, goal, avoid=frozenset(bad_squares(s) - {goal} - boards),
                               allow_monsters=False, allow_pets=True)
                hit = [c for c in wet or [] if c in zone]
                if hit:
                    return out(f"blocked: the only way to the {species or target} at {goal} passes {hit[0]}, next "
                               f"to water — {zone[hit[0]][0]} (its wrap drowns you). Wait for it to come to you "
                               "away from the water, fight it at range, or hunt(..., near_water=True) if you "
                               "levitate / wear a greased or oilskin cloak / accept that")
            if not path or len(path) < 2:
                # an identified special level: its fixed map knows the dark, never-seen floor between you and it
                # (p2 shift 29 #221: sleepers deep in the Valley's dark graveyard)
                nxt = _desmap_step(s, goal, set(zone))
                if nxt is None:
                    nxt = _greedy_step(s, goal, bad_squares(s) | set(zone)) \
                        if m["dist"] is not None and m["dist"] <= 6 else None
                if nxt is None:
                    # far off, just past the edge of the map you know: go to the frontier nearest to it
                    from .explore import screen_frontiers
                    from .mapview import dist as _d
                    from .nav import travel
                    here_d = _d(s.hero, goal)
                    cands = [c for c in screen_frontiers(s) if _d(c, goal) < here_d and c != s.hero
                             and c not in tried]
                    # (never along the water where a drowner may be: p1 shift 33 #869 — the frontier trip warned
                    # and walked 2 squares beside the Wizard's moat, then the next turn said 'blocked')
                    fr = sorted((c for c in cands if bfs_path(s, s.hero, c, avoid=frozenset(set(zone) - {c}),
                                                              allow_monsters=False, allow_pets=True) is not None),
                                key=lambda c: (_d(c, goal), _d(c, s.hero)))
                    if not fr and zone:
                        wet = [p for p in (bfs_path(s, s.hero, c, allow_monsters=False, allow_pets=True)
                                           for c in cands) if p]
                        hit = [c for c in (wet[0] if wet else []) if c in zone]
                        if hit:
                            return out(f"blocked: the only way toward the {species or target} at {goal} passes "
                                       f"{hit[0]}, next to water — {zone[hit[0]][0]} (its wrap drowns you). Wait "
                                       "for it away from the water, fight it at range, or hunt(..., "
                                       "near_water=True) if you levitate / wear a greased or oilskin cloak / "
                                       "accept that")
                    moved = False
                    for c in fr[:4]:
                        tried.add(c)
                        try:
                            s = travel(*c, near_water=near_water)
                        except NavError as e:
                            print(f"hunt: couldn't get to the frontier {c} ({str(e)[:90]}) — trying another")
                            s = ctx.last()
                            continue
                        kills += killed_names(s.messages, include_it=True)
                        moved = True
                        break
                    if not moved:
                        manual = ctx.game.avoid.get(ctx.game.level_key(s.status), set()) \
                            if hasattr(ctx.game, "avoid") and s.status.ok else set()
                        # (p3 shift 18 #605: 74 old avoid() squares round a beehive were the real cause)
                        return out(f"no route to the {species or target} at {goal} on the map you know (across "
                                   "water, behind a wall or other monsters): travel near it, head_to() it, or "
                                   "wait for it"
                                   + (f"; {len(manual)} manual avoid() squares on this level count as walls for "
                                      "the routes — avoid(clear=True) forgets them" if manual else ""))
                    continue
                path = [nxt, goal]           # a step into unexplored dark floor toward it
            try:
                _check_free(s, path[0], "hunt()")
            except NavError as e:
                # a peaceful (or another monster) on the next square: a way around it, else say so
                alt = bfs_path(s, s.hero, goal, avoid=frozenset((bad_squares(s) | {path[0]}) - {goal}),
                               allow_monsters=False, allow_pets=True)
                if not alt or len(alt) < 2:
                    return out(f"blocked: {e}")
                path = alt
            h0 = s.hero
            s = ctx.do(DIR_KEY[(path[0][0] - s.hero[0], path[0][1] - s.hero[1])],
                       ok=HUNT_OK + BENIGN + [r"^The door opens\.$", r"^A board beneath you squeaks"],
                       force=path[0] in boards)
            kills += killed_names(s.messages, include_it=True)
            if s.hero == h0 and any(m.startswith("The door opens") for m in s.messages):
                continue                     # the step opened a door on the way (autoopen): go on through it
            if s.hero == h0 and s.state.kind == "command" and not kills:
                return out(f"no way toward the {species or target} at {goal}: the step to {path[0]} failed "
                           f"({s.messages or 'rock or a wall'})")
    return out("max_turns")


# zap.c: a RAY (dobuzz: magic missile, fire, cold, sleep, death, lightning) goes on through every monster on its
# line and bounces off walls; a BEAM (bhit: striking, teleportation, polymorph, cancellation, slow/speed monster,
# make invisible, undead turning, probing, opening, locking, nothing) stops at the FIRST monster it meets
_WAND_KIND = re.compile(r"\bwands? (?:of|called) (magic missile|fire|cold|sleep|death|lightning|striking|"
                        r"teleportation|polymorph|cancellation|make invisible|slow monster|speed monster|"
                        r"undead turning|probing|opening|locking|nothing|digging|light|secret door detection|"
                        r"create monster|enlightenment|wishing)\b")
_RAY_KINDS = ("magic missile", "fire", "cold", "sleep", "death", "lightning")
# wands zap_when_lined() never zaps at a monster: no effect on it (digging, opening, locking, probing, nothing),
# no direction at all (light ... wishing), or a HELP to it (speed monster, make invisible: an invisible cockatrice)
_NOT_AT_MONSTERS = ("digging", "opening", "locking", "probing", "nothing", "light", "secret door detection",
                    "create monster", "enlightenment", "wishing", "speed monster", "make invisible")


def _wand_kind(text: str) -> str | None:
    m = _WAND_KIND.search(text or "")
    return m.group(1) if m else None


def _ray_stopper(s, x, y, sighted: bool) -> bool:
    """Does this square stop a ray (zap.c dobuzz(): !ZAP_POS or a closed door)? A wall (a brown '|'/'-' is an
    open door, a bright white '|' a grave), a closed door (brown '+'), a tree (green '#'); a blank square too
    unless the line is in your sight (then it is dark floor)."""
    ch, col = s.screen.at(x, y), s.screen.color_at(x, y)
    return (ch in "|-" and col not in (3, 15)) or (ch == "+" and col == 3) or (ch == "#" and col == 2) \
        or (ch == " " and not sighted)


def _lined(s, m, within: int, frm=None):
    """The direction key from you (or from square `frm`) toward monster m when it stands in a straight line
    from there — row, column or diagonal — within `within` squares, with nothing between that stops a ray (a
    wall, a closed door, a tree; rock or ground you haven't seen, unless you SEE m from your own square: then
    the line between is clear). Else None."""
    h = tuple(frm) if frm is not None else s.hero
    if h is None:
        return None
    dx, dy = m["x"] - h[0], m["y"] - h[1]
    n = max(abs(dx), abs(dy))
    if n == 0 or n > within or not (dx == 0 or dy == 0 or abs(dx) == abs(dy)):
        return None
    seen = re.search(r"\[seen: ([^\]]*)\]", m.get("desc") or "")
    sighted = frm is None and (seen is None or "vision" in seen.group(1))    # (not telepathy/warning only)
    sx, sy = (dx > 0) - (dx < 0), (dy > 0) - (dy < 0)
    x, y = h
    for _ in range(n - 1):
        x, y = x + sx, y + sy
        if _ray_stopper(s, x, y, sighted):
            return None
    return DIR_KEY[(sx, sy)]


def _bounce_back(s, key: str) -> tuple | None:
    """The first square on the line from you in direction `key` that bounces a ray (a wall, a closed door, rock
    — or a blank you can't see past), if it lies within 6 squares: a ray (range 7-13, 1 more for the bounce, 2
    per monster hit) can come straight back across your square from there. None when it is farther."""
    from .mapview import KEY_DIR
    d = KEY_DIR.get(key)
    if d is None or s.hero is None:
        return None
    x, y = s.hero
    for _ in range(6):
        x, y = x + d[0], y + d[1]
        if not (0 <= x < 80 and 1 <= y <= 21) or _ray_stopper(s, x, y, False):
            return (x, y)
    return None


def _self_hit_risk(kind: str | None) -> str:
    """What your own ray of this kind does to YOU when it bounces back ('' when you resist or reflect it, or it
    only costs HP): sleep beside what you are zapping is death, a death ray kills, lightning blinds you for
    up to 300 turns even when reflected (zap.c dobuzz(): flashburn() whenever the bolt crosses your square)."""
    g = ctx.game
    res = set(getattr(g, "intrinsics", None) or ())
    refl = bool(getattr(g, "reflecting", False))
    if kind == "sleep" and "sleep" not in res and not refl:
        return "it would put YOU to sleep (no sleep resistance or reflection)"
    if kind == "death" and not getattr(g, "magic_res", False) and not refl:
        return "it would KILL you (no magic resistance or reflection)"
    if kind == "lightning":
        st = ctx.last().status
        if not (st.ok and "Blind" in st.conditions):
            return "its flash BLINDS you for up to 300 turns (even when reflected)"
    return ""


def _line_up_steps(s, m, within: int) -> list:
    """Squares next to you, on known floor with no monster, trap or avoided square, from which monster m is
    lined up (zap_when_lined's rules) 2+ squares away: one step and it can be zapped."""
    from .mapview import is_door, is_walkable, neighbors
    h = s.hero
    if h is None:
        return []
    try:
        from .nav import bad_squares
        bad = bad_squares(s)
    except Exception:  # noqa: BLE001  (a hint only)
        bad = set()
    occupied = {(o["x"], o["y"]) for o in s.monsters or []}
    out = []
    for c in neighbors(*h):
        if c in occupied or c in bad or not is_walkable(s, *c, allow_monsters=False):
            continue
        if c[0] != h[0] and c[1] != h[1] and (is_door(s, *h) or is_door(s, *c)):
            continue
        if max(abs(m["x"] - c[0]), abs(m["y"] - c[1])) >= 2 and _lined(s, m, within, frm=c):
            out.append(c)
    return out


def zap_when_lined(name: str, wands, within: int = 8, max_turns: int = 20, stop_hp: float = 0.45,
                   patience: int = 5, fight_others: bool = True, bounce_ok: bool = False) -> dict:
    """Kill a monster you must never melee (a cockatrice, a floating eye...) with your wands, from where you
    stand. name = part of its label ('cockatrice'); wands = your wand letters in order of preference ('RlMm').
    Each turn:
    - it (any hostile whose label contains `name`) stands in a straight line from you — row, column or
      diagonal — within `within` squares, no wall/closed door between and NO pet or peaceful anywhere on that
      line (friendly_in_line(ray=True)): zap the first listed wand that still has charges at it (zap(): a
      WandEmpty goes on to the next wand; one known empty — "(x:0)", or "Nothing happens" before — is skipped);
    - else fight() ONE blow at another adjacent hostile (never the target; molds and hidden hiders are left
      alone; one fight() refuses twice is left alone too) — fight_others=False: never;
    - else search one turn ('s').
    It never moves you and never melees the target. A BEAM wand (striking, teleportation, polymorph, slow
    monster...: known from its name) is used only when the target is the first monster on the line (a beam
    stops at the first one; a ray passes through them all). A known SLEEP/DEATH/LIGHTNING ray is skipped while a
    wall is within 6 squares on that line (it can bounce straight back across you) unless you resist/reflect it
    — bounce_ok=True zaps anyway. Wands that do nothing to a monster or help it (digging, opening, locking,
    probing, nothing, speed monster, make invisible, the non-directional ones) are left out; an unidentified
    wand is zapped as given (your call). Rays reach 7-13 squares, beams 6-13: at 7-8 a zap can fall short.
    Newcomers of the target's kind don't pause (they are the plan: it zaps them too), and no 'approaching'
    pause for them; other newcomers, messages and HP pause as usual (HP by the fight rules: stop_hp).
    Returns {"reason", "zaps": [{"wand", "dir", "at", "d", "turn"}], "kills", "turns", "empty"}; reason:
    "killed: ..." / "gone: ..." (out of view, no kill seen — last seen where) / "no hostile ... in view" /
    "no usable wand ..." / "no wands left: ... EMPTY" / "adjacent: ..." (next to you and not zappable: a pet
    behind it) / "blocked: ..." (lined up and standing still, but no zap may go: a pet in the line, a bounce) /
    "not coming into line: ..." (it stood still `patience` turns out of line: asleep, slow or stuck — with the
    squares one step away that line you up) / "HP ..." / "STONING ..." / "max_turns: ..." (p2 shift 39: a
    cockatrice killed at d=3 with 2 cold rays before it ever reached you)."""
    import contextlib
    from nh.danger import base_name
    from nh.monitor import _stationary, killed_names
    s = ctx.require_command("zap_when_lined()")
    want = str(name or "").strip().lower()
    if not want:
        raise ValueError("zap_when_lined(name, wands): name = part of the monster's label, e.g. 'cockatrice'")
    letters = list(dict.fromkeys(c for c in (wands if isinstance(wands, (list, tuple)) else str(wands or ""))
                                 if str(c).strip()))
    t0 = s.status.turn or 0
    kills: list = []
    zaps: list = []
    empty: list = []
    names: set = set()                 # base names of the targets seen
    last_seen = None                   # (desc, x, y, turn) of the nearest target, last time in view
    still, still_at = 0, None          # turns the targets stood still out of line
    tries: dict = {}                   # adjacent others: fight() calls that landed no blow

    def out(reason):
        return {"reason": reason, "zaps": zaps, "kills": kills, "empty": empty,
                "turns": (ctx.last().status.turn or t0) - t0}

    def is_target(m) -> bool:
        return want in (m.get("desc") or "").lower()

    if not any(is_target(m) for m in s.hostiles()):
        return out(f"no hostile {name!r} in view")
    from .items import inventory
    inv = {i["letter"]: i for i in inventory()}
    known_empty = getattr(ctx.game, "empty_wands", None) or set()
    kinds: dict = {}
    for w in letters:
        it = inv.get(w)
        if it is None or not re.search(r"\bwands?\b", it["text"]):
            print(f"zap_when_lined: {w!r} is not a wand in your pack" + (f" ({it['text']})" if it else "")
                  + " — skipped")
        elif w in known_empty or re.search(r"\(\d+:(?:0|-1)\)", it["text"]):
            empty.append(w)
            print(f"zap_when_lined: {w} - {it['text']} is EMPTY — skipped")
        elif _wand_kind(it["text"]) in _NOT_AT_MONSTERS:
            print(f"zap_when_lined: {w} - {it['text']} does nothing to a monster (or helps it) — skipped")
        else:
            kinds[w] = _wand_kind(it["text"])
    if not kinds:
        return out(f"no usable wand among {''.join(letters)!r}" + (f" (EMPTY: {', '.join(empty)})" if empty else ""))
    if _elbereth_holds(s):
        print("zap_when_lined: you stand on Elbereth — a zap at a monster that respects it ERASES it (mon.c "
              "setmangry: 'You feel like a hypocrite', -5 alignment); searching and waiting keep it")

    guard =ctx.monster_filter(lambda m: not is_target(m)) if ctx.monster_filter else contextlib.nullcontext()
    rules = getattr(ctx, "hp_rules", None)
    with guard, (rules(stop_hp) if rules is not None else contextlib.nullcontext()):
        for _ in range(max_turns):
            s = ctx.last()
            if s.state.kind != "command" or s.hero is None:
                return out(f"not at the command prompt ({s.state.kind}: {s.state.prompt!r})")
            st = s.status
            if st.ok and "Stone" in st.conditions:
                return out("STONING — eat a lizard corpse or an acidic corpse, or pray, NOW")
            if st.ok and st.hp < stop_hp * max(1, st.hpmax):
                return out(f"HP {st.hp}/{st.hpmax} below {stop_hp:.0%} — get away (Elbereth, retreat, pray at 1/7)")
            if getattr(s, "engulfed", False):
                return out("ENGULFED — fight() hits the engulfer from inside")
            if st.ok and "Hallu" in st.conditions:
                return out("hallucinating — every label is random: the target can't be told apart")
            live = [w for w in kinds if w not in empty]
            if not live:
                return out(f"no wands left: {', '.join(empty)} EMPTY — recharge them or kill it another way "
                           "(throw daggers; never melee it)")
            ts = sorted((m for m in s.hostiles() if is_target(m)),
                        key=lambda m: m["dist"] if m.get("dist") is not None else 99)
            if not ts:
                got = [k for k in kills if k in names]
                if got:
                    return out("killed: " + ", ".join(got))
                if not names:
                    return out(f"no hostile {name!r} in view")
                if "it (unseen)" in kills:
                    return out(f"killed (probably): 'You kill it!' and no {'/'.join(sorted(names))} is in view now")
                return out(f"gone: the {last_seen[0]} is out of view (last seen at ({last_seen[1]},{last_seen[2]}) "
                           f"T:{last_seen[3]}), no kill seen — it moved out of sight, teleported or turned invisible")
            names.update(base_name(m.get("desc") or "") for m in ts)
            last_seen = (ts[0].get("desc") or ts[0]["ch"], ts[0]["x"], ts[0]["y"], st.turn)
            if ctx.unwatch_monsters is not None:
                ctx.unwatch_monsters([m["id"] for m in ts if m.get("id") is not None])
            # 1. a zap, when one is lined up
            acted, blocked, lined = False, [], []
            for m in ts:
                key = _lined(s, m, within)
                if key is None:
                    continue
                lined.append(m)
                friends = friendly_in_line(key, ray=True, s=s)
                if friends:
                    f = friends[0]
                    blocked.append(f"the {f.get('desc') or f['ch']} at ({f['x']},{f['y']}) is in the line of fire")
                    continue
                first = _first_in_line(key, s=s)
                wall = _bounce_back(s, key)
                for w in live:
                    kind = kinds[w]                 # (None: an unidentified wand — your call, zapped like a ray)
                    if kind is not None and kind not in _RAY_KINDS \
                            and (first is None or (first["x"], first["y"]) != (m["x"], m["y"])):
                        blocked.append(f"{w} (wand of {kind}: a beam) would stop at the "
                                       f"{(first or {}).get('desc') or 'monster'} in front of it")
                        continue
                    risk = _self_hit_risk(kind) if wall and not bounce_ok else ""
                    if risk:
                        blocked.append(f"{w} (wand of {kind}): {wall} bounces the ray straight back — {risk}")
                        continue
                    try:
                        s2 = zap(w, key)
                    except WandEmpty:
                        empty.append(w)             # ("Nothing happens": the turn is spent — look again)
                        print(f"zap_when_lined: wand {w} is EMPTY — the next one from now on")
                        kills += killed_names(ctx.last().messages, include_it=True)
                        acted = True
                        break
                    zaps.append({"wand": w, "dir": key, "at": (m["x"], m["y"]), "d": m.get("dist"), "turn": st.turn})
                    kills += killed_names(s2.messages, include_it=True)
                    print(f"zap_when_lined: zapped {w} ({'wand of ' + kind if kind else 'unknown wand'}) '{key}' at "
                          f"the {m.get('desc') or m['ch']} at ({m['x']},{m['y']}) d={m.get('dist')}")
                    acted = True
                    break
                if acted:
                    break
            if acted:
                still, still_at = 0, None
                continue
            near = [m for m in ts if m.get("dist") == 1]
            if near:
                m = near[0]
                return out(f"adjacent: the {m.get('desc') or m['ch']} at ({m['x']},{m['y']}) is NEXT TO YOU and "
                           f"can't be zapped ({'; '.join(blocked) or 'no wand can reach it'}) — step away / "
                           "Elbereth / your call (never melee it)")
            # 2. another hostile next to you: one checked blow at it (not a mold, a hidden hider, or one whose
            # passive fight() refuses — a floating eye beside the cockatrice)
            if fight_others:
                others = [o for o in s.adjacent_hostiles() if not is_target(o) and not _stationary(o.get("desc") or "")
                          and "hiding" not in (o.get("desc") or "") and not _passive_refusal(o.get("desc") or "", st)
                          and tries.get((o.get("id"), o["x"], o["y"]), 0) < 2]
                if others:
                    o = sorted(others, key=lambda o: _danger_rank(o.get("desc") or ""))[0]
                    s2 = fight(o["x"], o["y"], stop_hp=stop_hp, max_blows=1)
                    kills += killed_names(s2.messages, include_it=True)
                    if not any(re.match(r"^You (?:hit|miss|kill|destroy|smite)\b", x) for x in s2.messages):
                        k = (o.get("id"), o["x"], o["y"])
                        tries[k] = tries.get(k, 0) + 1         # (a refusal/pause: after 2, leave it be)
                    continue
            # 3. wait for it to come into line
            pos = tuple(sorted((m["x"], m["y"]) for m in ts))
            still = still + 1 if pos == still_at else 0
            still_at = pos
            if patience and still >= patience:
                m = ts[0]
                if lined:
                    m = lined[0]
                    return out(f"blocked: the {m.get('desc') or m['ch']} at ({m['x']},{m['y']}) d={m.get('dist')} is "
                               f"lined up but stood still {still} turns and no zap may go: " + "; ".join(blocked)
                               + " — wait for the line to clear, move, or bounce_ok=True for a bounce you accept")
                steps = _line_up_steps(s, m, within)
                return out(f"not coming into line: the {m.get('desc') or m['ch']} at ({m['x']},{m['y']}) "
                           f"d={m.get('dist')} stood still for {still} turns (asleep, slow or stuck)"
                           + (f" — step to {' or '.join(str(c) for c in steps[:3])} to line up" if steps else
                              f" — step onto its row, column or diagonal within {within} yourself"))
            hider = any("hiding" in (o.get("desc") or "") and o.get("dist") == 1 for o in s.monsters or [])
            s2 = ctx.do("." if hider else "s", ok=ROUTINE)
            kills += killed_names(s2.messages, include_it=True)
    s = ctx.last()
    ts = sorted((m for m in s.hostiles() if is_target(m)), key=lambda m: m["dist"] if m.get("dist") is not None else 99)
    if not ts:
        got = [k for k in kills if k in names]
        return out("killed: " + ", ".join(got) if got else f"max_turns: no {name!r} in view now")
    m = ts[0]
    steps = _line_up_steps(s, m, within) if s.hero is not None else []
    return out(f"max_turns: the {m.get('desc') or m['ch']} at ({m['x']},{m['y']}) d={m.get('dist')} is still there "
               f"({len(zaps)} zap(s))" + (f" — step to {' or '.join(str(c) for c in steps[:3])} to line up" if steps
                                          and not _lined(s, m, within) else ""))
