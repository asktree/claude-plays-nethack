"""Combat helpers. One blow per step, checked every time; never batches.

fight() only ever attacks monsters the tracker identified as hostile (not
tame/peaceful/statue), and the harness guard refuses floating eyes, gas
spores and green slime anyway.
"""

from __future__ import annotations

from . import ctx
from .mapview import DIR_KEY

ROUTINE = [r"^You (hit|miss|kill|destroy) ", r"^You smite ", r"(bites|hits|misses|stings|butts|kicks|claws|touches)[!.]$",
           r"^The .* (turns to flee|is killed|dies)", r"^You hear some noises", r"^Welcome to experience level",
           # monster chatter in melee (wizard.c cuss(), demon/imp taunts, quoted speech)
           r"casts aspersions on your ancestry", r"laughs fiendishly", r'^"[^"]*"$',
           # hit side effects that the HP check already covers
           r"^You get zapped!$", r"^You are (?:stung|bitten|kicked|butted)"]
# a thrown/fired object hitting or missing ("The dagger misses the jackal.")
THROW_OK = ROUTINE + [r"^The .+ (hits|misses)( the .+| it)?[.!]$", r"^You (kill|destroy) "]
# a zapped ray/bolt doing its job ("The bolt of lightning hits the rope golem!"); hits on YOU still pause
_RAY = r"(?:magic missile|bolt of \w+|sleep ray|death ray|blast of [\w ]+|stream of \w+|ray of \w+|fireball|cone of cold)"
ZAP_OK = ROUTINE + [rf"^The {_RAY} (?:hits|misses|whizzes by) (?!you)", rf"^The {_RAY} bounces!",
                    r"^The .+ (?:is killed|is destroyed|dies)", r"^You (?:kill|destroy) ",
                    r"^The .+ resists", r"^The .+ is not affected"]

_warned: set = set()


def _key_toward(hero, m):
    return DIR_KEY.get((m["x"] - hero[0], m["y"] - hero[1]))


def fight(x: int | None = None, y: int | None = None, stop_hp: float = 0.45, max_blows: int = 25,
          allow_passive: bool = False):
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
    - Exec tip: run fights with `bin/nh exec --hp-pause 0.4` so ordinary
      bites below 70% HP don't pause every round."""
    seen: list[str] = []
    try:
        return _fight(x, y, stop_hp, max_blows, allow_passive, seen)
    finally:
        last = ctx.last()
        if seen and last is not None:
            last.messages = seen + [m for m in last.messages if m not in seen]


def _fight(x, y, stop_hp, max_blows, allow_passive, seen):
    """fight() body; `seen` collects every round's messages (so an early
    'You feel feverish' isn't lost behind later rounds)."""
    from nh.danger import STOP_PASSIVES, max_hit, passive_attacks
    s = ctx.last()
    for _ in range(max_blows):
        if s.state.kind != "command" or s.hero is None:
            return s
        st = s.status
        if getattr(s, "engulfed", False):
            # inside a monster: any direction hits it
            if st.ok and st.hp < stop_hp * max(1, st.hpmax):
                ctx.pause(f"fight: engulfed and HP {st.hp}/{st.hpmax} is below {stop_hp:.0%} — pray if HP <= 1/7 max")
                return ctx.last()
            s = ctx.do("Fk", ok=ROUTINE + [r"^You (hit|miss) the ", r"^You get (expelled|regurgitated)"])
            seen.extend(s.messages)
            continue
        if "Hallu" in st.conditions:
            ctx.pause("fight: hallucinating — can't tell hostile from peaceful (and NetHack won't ask). Attack "
                      "with do('F'+dir, force=True) only a monster that is attacking you, or retreat.")
            return ctx.last()
        targets = s.adjacent_hostiles()
        if x is not None:
            targets = [m for m in targets if (m["x"], m["y"]) == (x, y)]
        if not targets:
            return s
        worst = sum(max_hit(m.get("desc") or "") for m in s.adjacent_hostiles())
        if st.ok and st.hp < stop_hp * max(1, st.hpmax) and worst * 3 >= st.hp:
            ctx.pause(f"fight: HP {st.hp}/{st.hpmax} is below {stop_hp:.0%} and the adjacent hostiles can "
                      f"deal ~{worst}/turn — disengage? (Elbereth, retreat, pray if HP <= 1/7 max)")
            return ctx.last()
        # attack the most dangerous-looking adjacent target first (noted ones), else the first
        targets.sort(key=lambda m: (0 if m.get("note") else 1))
        m = targets[0]
        desc = m.get("desc") or ""
        pas = passive_attacks(desc) if desc else []
        if pas and desc not in _warned:
            _warned.add(desc)
            print(f"fight: {desc} — passive: " + "; ".join(txt for _dt, txt in pas))
        if not allow_passive and any(dt in STOP_PASSIVES for dt, _txt in pas):
            ctx.pause(f"fight: not meleeing the {desc}: " + "; ".join(txt for _dt, txt in pas)
                      + ". Use ranged attacks or leave it (fight(..., allow_passive=True) to override).")
            return ctx.last()
        key = _key_toward(s.hero, m)
        if key is None:
            return s
        s = ctx.do("F" + key, ok=ROUTINE)
        seen.extend(s.messages)
    return s


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
    s = ctx.do("t", quiet=True)
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
    return ctx.do(direction, ok=THROW_OK)


def zap(wand: str, direction: str | None, force: bool = False):
    """Zap wand `wand` (a letter) in `direction` (or None for non-directional
    wands). Sends the direction only if the game actually asks for one (an
    empty wand says "Nothing happens" and asks nothing). Refuses (pauses)
    when your pet or a peaceful is anywhere on the straight line (rays and
    beams go through monsters; force=True to zap anyway)."""
    ctx.require_command("zap()")
    if direction and _refuse_friendly_fire("zap", direction, ray=True, force=force):
        return ctx.last()
    s = ctx.do("z", quiet=True)
    if s.state.kind != "object":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        ctx.pause(f"zap: expected an item prompt, got {s.state.kind}: {s.state.prompt!r}")
        return ctx.last()
    s = ctx.do(wand)
    if s.state.kind == "direction":
        if direction is None:
            ctx.do("<Esc>", quiet=True)
            ctx.pause("zap: the wand wants a direction but none was given")
            return ctx.last()
        return ctx.do(direction, ok=ZAP_OK)
    return s
