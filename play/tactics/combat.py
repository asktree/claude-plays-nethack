"""Combat helpers. One blow per step, checked every time; never batches.

fight() only ever attacks monsters the tracker identified as hostile (not
tame/peaceful/statue), and the harness guard refuses floating eyes, gas
spores and green slime anyway.
"""

from __future__ import annotations

import re

from . import ctx
from .mapview import DIR_KEY

ROUTINE = [r"^You (hit|miss|kill|destroy) ", r"^You smite ", r"(bites|hits|misses|stings|butts|kicks|claws|touches)[!.]$",
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
           r"^The .+ (?:swings|thrusts) (?:his|her|its) ", r" pricks your (?:left |right )?leg!$",
           # ranged/weapon flavour (the damage, if any, is caught by the HP checks); thefts still pause
           # (never "wields a cockatrice corpse": a gloved monster hitting you with one stones you)
           r"^The .+ wields (?:an? |the |\d+ )(?!.*\b(?:cockatrice|chickatrice) corpse)",
           r"^The .+ (?:throws|shoots|fires) ", r"^The .+ breathes ",
           r"^You are hit by ", r"^The .+ misses you[.!]$",
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
           r"^A sudden geyser slams into you", r"^Your body is covered with deadly wounds", r" looks better\.$",
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
          allow_passive: bool = False, only=None, force: bool = False, attack_peaceful: bool = False):
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
      hits it anyway (angering a peaceful costs alignment; killing one, more)."""
    import contextlib
    seen: list[str] = []
    rules = getattr(ctx, "hp_rules", None)
    try:
        with (rules(stop_hp) if rules is not None else contextlib.nullcontext()):
            return _fight(x, y, stop_hp, max_blows, allow_passive, seen, only, force, attack_peaceful)
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


def _wielding() -> bool:
    """Do you wield something? (cached by inventory(); asks once if unknown)"""
    w = getattr(ctx.game, "wielded", None)
    if w is None:
        from .items import inventory
        inventory()
        w = getattr(ctx.game, "wielded", None)
    return bool(w)


def _check_target(m) -> tuple:
    """Look at the monster about to get an F blow (no game time). Returns (snap, fresh monster dict at
    that square or None when nothing is there now)."""
    from .nav import farlook
    farlook(m["x"], m["y"])
    s = ctx.last()
    return s, next((t for t in s.monsters or [] if (t["x"], t["y"]) == (m["x"], m["y"])
                    and not t.get("statue")), None)


def _fight(x, y, stop_hp, max_blows, allow_passive, seen, only=None, force=False, attack_peaceful=False):
    """fight() body; `seen` collects every round's messages (so an early
    'You feel feverish' isn't lost behind later rounds)."""
    from nh.danger import STOP_PASSIVES, base_name, explodes_at_you, max_hit, passive_attacks, passive_max
    s = ctx.last()
    locked_on = None                 # fight(x, y): the species that was on (x, y) at the first blow
    checked: set = set()             # (id, x, y) of targets looked at before their first blow
    engulf_warned = False
    inside = False                   # swung from inside an engulfer during this call
    seen_notes: set = set()
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
        if drown and not force and "drown" not in seen_notes:
            seen_notes.add("drown")
            ctx.pause("fight: you stand next to WATER with " + ", ".join(
                f"{m.get('desc') or 'an unseen monster'} at ({m['x']},{m['y']})" for m in drown[:3])
                + " in it — one wrap holds you and the next DROWNS you (levitation doesn't help). Step to a square "
                  "with no water next to it first and fight what follows you there (or Elbereth / freeze the "
                  "water); fight(..., force=True) to fight on here")
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
            if not targets and s.screen.at(x, y) == "I" and max(abs(x - s.hero[0]), abs(y - s.hero[1])) == 1:
                # an unseen (invisible) monster you asked for by square: swing at it
                s = ctx.do("F" + DIR_KEY[(x - s.hero[0], y - s.hero[1])], ok=ROUTINE, force=force)
                seen.extend(s.messages)
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
                was_killed = any(re.search(r"^You (?:kill|destroy) ", m) for m in seen) \
                    or any(killed.search(m) for m in recent)
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
                        print(f"fight: the {locked_on} at ({x},{y}) is gone — NOT killed (it teleported, fled out "
                              "of view or hid): look around (a covetous one teleports to heal and comes back)")
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
                      near_water: bool = False) -> dict:
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
    unseen=True: also swing (F) at an adjacent remembered unseen monster 'I'
    (invisible attackers; never where a peaceful may be).
    Next to water with a sea monster (or an unseen 'I') in it, it returns
    "DROWNING RISK: ..." at once — step away from the water first
    (near_water=True fights on there)."""
    import contextlib
    from nh.danger import base_name, threat_level
    from nh.monitor import killed_names

    def dangerous(m):
        d = m.get("desc") or ""
        if d and base_name(d) in ignore:
            return False
        st = ctx.last().status
        return not d or threat_level(d, st.xl if st.ok else None, st.hp if st.ok else None,
                                     getattr(ctx.game, "intrinsics", ())) == "dangerous"

    ctx.require_command("fight_until_clear()")
    warn_bounce("fight_until_clear()")
    t0 = ctx.last().status.turn or 0
    kills: list = []
    best, idle = None, 0

    def out(reason):
        return {"reason": reason, "kills": kills, "turns": (ctx.last().status.turn or t0) - t0}

    guard = ctx.monster_filter(dangerous) if ctx.monster_filter else contextlib.nullcontext()
    rules = getattr(ctx, "hp_rules", None)
    with guard, (rules(stop_hp) if rules is not None else contextlib.nullcontext()):
        for _ in range(max(max_turns, hold)):
            s = ctx.last()
            if s.state.kind != "command" or s.hero is None:
                return out(f"not at the command prompt ({s.state.kind}: {s.state.prompt!r})")
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
            mobile_adj = [m for m in s.adjacent_hostiles() if not _stationary(m.get("desc") or "")]
            if mobile_adj:
                s = fight(stop_hp=stop_hp, allow_passive=allow_passive)
                kills += killed_names(s.messages, include_it=True)
                best, idle = None, 0
                if s.adjacent_hostiles() and s.status.ok and s.status.hp < stop_hp * max(1, s.status.hpmax):
                    return out(f"HP {s.status.hp}/{s.status.hpmax} below {stop_hp:.0%} with hostiles adjacent")
                continue
            if unseen:
                ivs = [m for m in s.monsters or [] if m.get("unseen") and m.get("dist") == 1]
                key = _key_toward(s.hero, ivs[0]) if ivs else None
                if key:
                    s = ctx.do("F" + key, ok=ROUTINE + [r"^You (?:harmlessly )?attack thin air",
                                                        r"^Wait!  There's (?:something|\w+) there"])
                    kills += killed_names(s.messages, include_it=True)
                    continue
            near = [m for m in s.hostiles(radius) if not _stationary(m.get("desc") or "")]
            if not near and hold and (s.status.turn or t0) - t0 < hold:
                s = ctx.do("s", ok=ROUTINE)          # keep the square: wait for the next one to come
                kills += killed_names(s.messages, include_it=True)
                continue
            if not near:
                if hold:
                    return out("held")
                beyond = [m for m in s.hostiles() if not _stationary(m.get("desc") or "")]
                recent = [g for g in getattr(s, "gone", None) or [] if (g.get("ago") or 0) <= 2]
                return out("clear" + (" (beyond the radius: " + ", ".join(
                    f"{m.get('desc') or m['ch']} at ({m['x']},{m['y']}) d={m['dist']}" for m in beyond[:3]) + ")"
                                      if beyond else "")
                           + (" — BUT " + ", ".join(f"{g['desc']} was at ({g['x']},{g['y']}) {g['ago']} turn(s) ago"
                                                     for g in recent[:2])
                              + " and left view: a hit-and-run in the dark (Vlad, a covetous caster)? wait a turn "
                                "(`s`) and look before moving on" if recent else ""))
            d = min(m["dist"] for m in near)
            if best is None or d < best:
                best, idle = d, 0
            else:
                idle += 1
            if idle >= patience:
                who = ", ".join(f"{m.get('desc') or m['ch']} at ({m['x']},{m['y']})" for m in near[:4])
                mim = any("mimic" in (m.get("desc") or "") for m in near)
                return out(f"{who} within {radius} but not coming for {idle} turns (trapped, slow or sessile?) "
                           "— go to it or leave it" + ("; a MIMIC re-hides as an object whenever you can't see "
                                                       "it — keep it in sight, or hunt() it" if mim else ""))
            s = ctx.do(".", ok=ROUTINE)
            kills += killed_names(s.messages, include_it=True)
    return out("max_turns")


def friendly_in_line(direction: str, ray: bool = False, s=None, maxlen: int = 13) -> list:
    """Tame/peaceful monsters in the straight line from you in `direction`.
    A thrown object stops at the first monster in its path, so only friends
    before the first hostile count; a ray (ray=True) passes through
    everything, so the whole line counts (bounces off walls aren't followed:
    mind them yourself)."""
    from .mapview import KEY_DIR
    s = s or ctx.last()
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
        if m.get("tame") or m.get("peaceful") or m.get("pet"):
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


def _refuse_friendly_fire(what: str, direction: str, ray: bool, force: bool) -> bool:
    if force:
        return False
    friends = friendly_in_line(direction, ray=ray)
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
    if _refuse_friendly_fire("throw", direction, ray=False, force=force):
        return ctx.last()
    target = _first_in_line(direction) if not force else None
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
    return ctx.do(direction, ok=THROW_OK, force=force)


def zap(wand: str, direction: str | None = None, force: bool = False):
    """Zap wand `wand` (a letter) in `direction` (or None for non-directional
    wands). Sends the direction only if the game actually asks for one (an
    empty wand says "Nothing happens" and asks nothing). Refuses (pauses)
    when your pet or a peaceful is anywhere on the straight line (rays and
    beams go through monsters; force=True to zap anyway)."""
    ctx.require_command("zap()")
    empty = getattr(ctx.game, "empty_wands", None)
    if empty and wand in empty and not force:
        ctx.pause(f"zap: wand {wand} said \"Nothing happens\" last time — it is EMPTY (0 charges): recharge it "
                  "(scroll of charging) or use another; zap(..., force=True) tries to wrest a last charge (1 in "
                  "121 per zap, a turn each)")
        return ctx.last()
    if direction and _refuse_friendly_fire("zap", direction, ray=True, force=force):
        return ctx.last()
    if direction:
        objs = _objects_in_line(direction)
        if objs:
            print(f"zap: objects on the line {objs[:4]} — a beam goes on past a monster: striking/force bolt "
                  "BREAKS potions and glass there, fire burns scrolls/potions, teleportation sends them away, "
                  "polymorph changes them, undead turning revives corpses")
    s = ctx.do("z", quiet=True, force=force)
    if s.state.kind != "object":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        ctx.pause(f"zap: expected an item prompt, got {s.state.kind}: {s.state.prompt!r}")
        return ctx.last()
    s = ctx.do(wand)
    if s.state.kind == "command" and any(m.startswith("Nothing happens") for m in s.messages):
        # zap.c zappable(): a wand with 0 charges does nothing (no direction asked)
        if getattr(ctx.game, "empty_wands", None) is None:
            ctx.game.empty_wands = set()
        ctx.game.empty_wands.add(wand)
        print(f"zap: wand {wand} is EMPTY (\"Nothing happens\": 0 charges) — recharge it (scroll of charging); "
              "zap() now refuses it unless force=True (wresting a last charge: 1 in 121 per zap)")
    if s.state.kind == "direction":
        if direction is None:
            ctx.do("<Esc>", quiet=True)
            ctx.pause("zap: the wand wants a direction but none was given")
            return ctx.last()
        return ctx.do(direction, ok=ZAP_OK, force=force)
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


def _greedy_step(s, goal, bad) -> tuple | None:
    """A square next to you, closer to `goal`, that is known floor (or, while you are BLIND, a blank:
    you don't see the squares next to you then; otherwise a blank next to you is rock) and not a known
    trap, water, wall or monster; never diagonally into or out of a doorway."""
    from .mapview import is_door, is_walkable, neighbors
    h = s.hero
    occupied = {(m["x"], m["y"]) for m in s.monsters or []}
    blind = s.status.ok and "Blind" in s.status.conditions
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
                hs = [m for m in s.hostiles() if not m.get("statue")]
                hs = [m for m in hs if (m["x"], m["y"]) == tuple(target)] if isinstance(target, tuple) else \
                    [m for m in hs if str(target).lower() in (m.get("desc") or "").lower()]
                if not hs and isinstance(target, tuple) and \
                        tuple(target) in (getattr(s, "mimic_mem", None) or {}):
                    return _hunt_hidden_mimic(tuple(target), stop_hp, out, kills)
                if not hs:
                    return out(f"no hostile {target!r} in view")
                m = min(hs, key=lambda e: e["dist"] if e["dist"] is not None else 99)
                want, species = m.get("id"), base_name(m.get("desc") or "")
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
                s = fight(m["x"], m["y"], stop_hp=stop_hp)
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
                nxt = _greedy_step(s, goal, bad_squares(s) | set(zone)) if m["dist"] is not None and m["dist"] <= 6 \
                    else None
                if nxt is None:
                    # far off, just past the edge of the map you know: go to the frontier nearest to it
                    from .explore import screen_frontiers
                    from .mapview import dist as _d
                    from .nav import travel
                    here_d = _d(s.hero, goal)
                    fr = sorted((c for c in screen_frontiers(s) if _d(c, goal) < here_d and c != s.hero
                                 and c not in tried and bfs_path(s, s.hero, c, allow_monsters=False,
                                                                 allow_pets=True) is not None),
                                key=lambda c: (_d(c, goal), _d(c, s.hero)))
                    moved = False
                    for c in fr[:4]:
                        tried.add(c)
                        try:
                            s = travel(*c)
                        except NavError as e:
                            print(f"hunt: couldn't get to the frontier {c} ({str(e)[:90]}) — trying another")
                            s = ctx.last()
                            continue
                        kills += killed_names(s.messages, include_it=True)
                        moved = True
                        break
                    if not moved:
                        return out(f"no route to the {species or target} at {goal} on the map you know (across "
                                   "water, behind a wall or other monsters): travel near it, head_to() it, or "
                                   "wait for it")
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
