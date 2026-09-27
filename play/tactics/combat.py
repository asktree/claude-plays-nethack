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
           # monster chatter in melee (wizard.c cuss(), demon/imp taunts, quoted speech)
           r"casts aspersions on your ancestry", r"laughs fiendishly", r'^"[^"]*"$',
           # hit side effects that the HP check already covers
           r"^You get zapped!$", r"^You are (?:stung|bitten|kicked|butted)",
           # weapon-wielding monsters announce each swing (mhitu.c); leg attacks (xan)
           r"^The .+ (?:swings|thrusts) (?:his|her|its) ", r" pricks your (?:left |right )?leg!$",
           # ranged/weapon flavour (the damage, if any, is caught by the HP checks); thefts still pause
           r"^The .+ wields (?:an? |the |\d+ )", r"^The .+ (?:throws|shoots|fires) ", r"^The .+ breathes ",
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
           r"^The [\w' -]+ misses[.!]$", r"^You are almost hit by "]
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
    if stops:
        return "; ".join(txt for _dt, txt in pas)
    pdmg, _pw = passive_max(desc, resists=getattr(ctx.game, "intrinsics", ()))
    if pdmg and st.ok and pdmg * 2 > st.hp:
        return f"passive up to {pdmg} HP"
    return ""


def _key_toward(hero, m):
    return DIR_KEY.get((m["x"] - hero[0], m["y"] - hero[1]))


def fight(x: int | None = None, y: int | None = None, stop_hp: float = 0.45, max_blows: int = 25,
          allow_passive: bool = False, only=None, force: bool = False):
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
      against Medusa, on the square telepathy/her last position shows.
    - HP pauses inside it follow the fight rules (kernel hp_rules): below
      stop_hp, a loss that would take you there in two more rounds, or a
      quarter of max HP in one step — not every blow below 70%."""
    import contextlib
    seen: list[str] = []
    rules = getattr(ctx, "hp_rules", None)
    try:
        with (rules(stop_hp) if rules is not None else contextlib.nullcontext()):
            return _fight(x, y, stop_hp, max_blows, allow_passive, seen, only, force)
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


def _fight(x, y, stop_hp, max_blows, allow_passive, seen, only=None, force=False):
    """fight() body; `seen` collects every round's messages (so an early
    'You feel feverish' isn't lost behind later rounds)."""
    from nh.danger import STOP_PASSIVES, base_name, explodes_at_you, max_hit, passive_attacks, passive_max
    s = ctx.last()
    locked_on = None                 # fight(x, y): the species that was on (x, y) at the first blow
    engulf_warned = False
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
            continue
        if "Hallu" in st.conditions:
            ctx.pause("fight: hallucinating — can't tell hostile from peaceful (and NetHack won't ask). Attack "
                      "with do('F'+dir, force=True) only a monster that is attacking you, or retreat.")
            return ctx.last()
        targets = s.adjacent_hostiles()
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
            targets = [m for m in targets if (m["x"], m["y"]) == (x, y)]
            if not targets and s.screen.at(x, y) == "I" and max(abs(x - s.hero[0]), abs(y - s.hero[1])) == 1:
                # an unseen (invisible) monster you asked for by square: swing at it
                s = ctx.do("F" + DIR_KEY[(x - s.hero[0], y - s.hero[1])], ok=ROUTINE, force=force)
                seen.extend(s.messages)
                continue
            if not targets and locked_on:
                recent = [m for t, m in list(getattr(ctx.game, "history", []))[-40:] if t is None or t >= t_first]
                killed = re.compile(r"^You (?:kill|destroy) (?:it\b|(?:the |an? |poor )?" + re.escape(locked_on) + ")")
                if not any(re.search(r"^You (?:kill|destroy) ", m) for m in seen) \
                        and not any(killed.search(m) for m in recent):
                    print(f"fight: the {locked_on} at ({x},{y}) is gone — NOT killed (it teleported, fled out of "
                          "view or hid): look around (a covetous one teleports to heal and comes back)")
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
        worst = sum(max_hit(m.get("desc") or "") for m in s.adjacent_hostiles())
        if st.ok and st.hp < stop_hp * max(1, st.hpmax) and worst * 3 >= st.hp:
            ctx.pause(f"fight: HP {st.hp}/{st.hpmax} is below {stop_hp:.0%} and the adjacent hostiles can "
                      f"deal ~{worst}/turn — disengage? (Elbereth, retreat, pray if HP <= 1/7 max)")
            return ctx.last()
        # attack the most dangerous-looking adjacent target first (noted ones), else the first — but
        # never pick one the passive checks below refuse while another is there (a coyote beside a
        # floating eye gets the blow)
        targets.sort(key=lambda m: (bool(allow_passive is False and _passive_refusal(m.get("desc") or "", st)),
                                    _danger_rank(m.get("desc") or "")))
        m = targets[0]
        desc = m.get("desc") or ""
        pas = passive_attacks(desc) if desc else []
        pdmg, pwhat = passive_max(desc, resists=getattr(ctx.game, "intrinsics", ())) if desc else (0, "")
        if pas and desc not in _warned:
            _warned.add(desc)
            print(f"fight: {desc} — passive: " + "; ".join(txt for _dt, txt in pas)
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
        if not allow_passive and stops:
            ctx.pause(f"fight: not meleeing the {desc}: " + "; ".join(txt for _dt, txt in pas)
                      + ". Use ranged attacks or leave it (fight(..., allow_passive=True) to override).")
            return ctx.last()
        if not allow_passive and pdmg and st.ok and pdmg * 2 > st.hp:
            ctx.pause(f"fight: one hit on the {desc} can cost you up to {pdmg} HP from its passive ({pwhat}) and "
                      f"you have {st.hp}: rest first, fight it at range, or allow_passive=True.")
            return ctx.last()
        key = _key_toward(s.hero, m)
        if key is None:
            return s
        s = ctx.do("F" + key, ok=ROUTINE)
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
                      ignore=(), allow_passive: bool = False) -> dict:
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
    to fight() (a cockatrice at a doorway, with your weapon wielded)."""
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
        for _ in range(max_turns):
            s = ctx.last()
            if s.state.kind != "command" or s.hero is None:
                return out(f"not at the command prompt ({s.state.kind}: {s.state.prompt!r})")
            st = s.status
            if st.ok and st.hp < stop_hp * max(1, st.hpmax):
                return out(f"HP {st.hp}/{st.hpmax} below {stop_hp:.0%} — Elbereth / retreat / pray if HP <= 1/7")
            from nh.monitor import _stationary
            mobile_adj = [m for m in s.adjacent_hostiles() if not _stationary(m.get("desc") or "")]
            if mobile_adj:
                s = fight(stop_hp=stop_hp, allow_passive=allow_passive)
                kills += killed_names(s.messages)
                best, idle = None, 0
                if s.adjacent_hostiles() and s.status.ok and s.status.hp < stop_hp * max(1, s.status.hpmax):
                    return out(f"HP {s.status.hp}/{s.status.hpmax} below {stop_hp:.0%} with hostiles adjacent")
                continue
            near = [m for m in s.hostiles(radius) if not _stationary(m.get("desc") or "")]
            if not near:
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
            kills += killed_names(s.messages)
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


def throw(item: str, direction: str, count: bool = False, force: bool = False):
    """Throw inventory item `item` (a letter) in `direction` (y k u h l b j n
    < >), verifying each prompt. Refuses (pauses) when your pet or a
    peaceful stands between you and the first hostile in that direction
    (force=True to throw anyway). Returns the final Snap."""
    ctx.require_command("throw()")
    if _refuse_friendly_fire("throw", direction, ray=False, force=force):
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


def hunt(target, max_turns: int = 30, stop_hp: float = 0.45) -> dict:
    """Close in on one hostile and fight it: target = part of its label
    ('pyrolisk') or its square (x, y). Each turn: adjacent -> fight() it
    (all of fight()'s checks); otherwise ONE checked step along a known-map
    route toward it (never onto another monster; its fiery gaze, spit or
    missiles don't pause — HP pauses follow the fight rules, new monsters and
    statuses still pause). Trivial hostiles in the way are fought.
    Returns {"reason", "turns", "kills"}: reason "killed", "lost: ..." (out
    of view), "HP ...", "blocked: ..." (another non-trivial hostile next to
    you), "no route ..." or "max_turns"."""
    import contextlib
    from nh.danger import base_name
    from nh.monitor import killed_names
    from .benign import BENIGN
    from .mapview import DIR_KEY, bfs_path
    from .nav import _check_free, bad_squares
    s = ctx.require_command("hunt()")
    t0 = s.status.turn or 0
    kills: list = []
    want = species = None
    warned_others = False

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
                kills += killed_names(s.messages)
                if getattr(s, "engulfed", False):
                    return out("still ENGULFED (fight() stopped: HP) — pray at 1/7 HP")
                continue
            if want is None:
                hs = [m for m in s.hostiles() if not m.get("statue")]
                hs = [m for m in hs if (m["x"], m["y"]) == tuple(target)] if isinstance(target, tuple) else \
                    [m for m in hs if str(target).lower() in (m.get("desc") or "").lower()]
                if not hs:
                    return out(f"no hostile {target!r} in view")
                m = min(hs, key=lambda e: e["dist"] if e["dist"] is not None else 99)
                want, species = m.get("id"), base_name(m.get("desc") or "")
            else:
                m = next((e for e in s.monsters or [] if e.get("id") == want), None)
                if m is None:
                    return out("killed" if species and species in kills else
                               f"lost: the {species or target} is out of view")
            from nh.monitor import _stationary
            others = [e for e in s.adjacent_hostiles() if e is not m and not auto_fightable(e, s)
                      and not _stationary(e.get("desc") or "")]     # a mold can't follow: walk on past it
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
                kills += killed_names(s.messages)
                if s.state.kind == "command" and any(e.get("id") == want for e in s.adjacent_hostiles()) \
                        and not killed_names(s.messages):
                    return out("fight() stopped with it still next to you (see its message)")
                continue
            if s.adjacent_hostiles():
                fs = fight_trivial(s)
                if fs is not None:
                    kills += killed_names(fs.messages)
                    continue
            goal = (m["x"], m["y"])
            path = bfs_path(s, s.hero, goal, avoid=frozenset(bad_squares(s) - {goal}), allow_monsters=False,
                            allow_pets=True)
            if not path or len(path) < 2:
                nxt = _greedy_step(s, goal, bad_squares(s)) if m["dist"] is not None and m["dist"] <= 6 else None
                if nxt is None:
                    # far off, just past the edge of the map you know: go to the frontier nearest to it
                    from .explore import screen_frontiers
                    from .mapview import dist as _d
                    fr = [c for c in screen_frontiers(s) if _d(c, goal) <= 3 and c != s.hero
                          and bfs_path(s, s.hero, c, allow_monsters=False) is not None]
                    if not fr:
                        return out(f"no route to the {species or target} at {goal} on the map you know (across "
                                   "water, behind a wall or other monsters): travel near it, or wait for it")
                    from .nav import travel
                    best = min(fr, key=lambda c: _d(c, goal))
                    s = travel(*best)
                    kills += killed_names(s.messages)
                    continue
                path = [nxt, goal]           # a step into unexplored dark floor toward it
            _check_free(s, path[0], "hunt()")
            h0 = s.hero
            s = ctx.do(DIR_KEY[(path[0][0] - s.hero[0], path[0][1] - s.hero[1])],
                       ok=HUNT_OK + BENIGN + [r"^The door opens\.$"])
            kills += killed_names(s.messages)
            if s.hero == h0 and any(m.startswith("The door opens") for m in s.messages):
                continue                     # the step opened a door on the way (autoopen): go on through it
            if s.hero == h0 and s.state.kind == "command" and not kills:
                return out(f"no way toward the {species or target} at {goal}: the step to {path[0]} failed "
                           f"({s.messages or 'rock or a wall'})")
    return out("max_turns")
