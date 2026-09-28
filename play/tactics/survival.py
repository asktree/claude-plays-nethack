"""Survival tactics: Elbereth, prayer, searching, resting."""

from __future__ import annotations

import re

from . import ctx


def search(n: int = 10):
    """Search n times in place (count-prefixed 's'; interrupted by monsters).
    n counts your actions, not game turns: while Fast/Very fast (speed boots)
    15 searches take only ~9-11 turns of the T: counter.
    A monster fleeing from your Elbereth ("turns to flee") doesn't pause."""
    ctx.require_command("search()")
    return _counted(f"{int(n)}s", int(n), [r"turns to flee"])


def rest(n: int = 20):
    """Rest n turns in place (count-prefixed '.'; needs !rest_on_space off: '.').
    A monster fleeing from your Elbereth ("turns to flee") doesn't pause."""
    ctx.require_command("rest()")
    from .combat import warn_bounce
    warn_bounce("rest()")
    # ("You stop waiting.": a scared monster stepping into view ends the count — p1 shift 36 #589: every 2-7
    # turns of rest_on_elbereth() paused on it while fire giants hovered around the Elbereth square)
    return _counted(f"{int(n)}.", int(n), [r"turns to flee", r"^You stop searching", r"^You stop waiting"])


def _counted(keys: str, n: int, ok):
    """Run a count-prefixed command; if it ran a single turn with nothing to
    explain it (no message, no monster next to you) — NetHack sometimes drops
    the count right after a travel — run it once more."""
    t0 = ctx.last().status.turn or 0
    s = ctx.do(keys, ok=ok)
    t1 = s.status.turn or t0
    if n > 2 and s.state.kind == "command" and t1 - t0 <= 1 and not s.messages and not s.adjacent_hostiles():
        s = ctx.do(keys, ok=ok)
    return s


def _engrave_elbereth():
    ctx.require_command("elbereth()")
    s = ctx.do("E", quiet=True)
    for _ in range(8):
        k = s.state.kind
        p = s.state.prompt
        if k == "object" and "write with" in p:
            s = ctx.do("-", quiet=True)
        elif k == "yn" and "add to the current engraving" in p:
            s = ctx.do("n", quiet=True)
        elif k == "yn" and "Do you want to" in p:
            s = ctx.do("n", quiet=True)
        elif k == "getlin" and ("write" in p or "engrave" in p):
            # monsters attacking during the engrave turn are expected (that's why you
            # engrave); a hit that costs HP still pauses through the kernel's HP check
            from .combat import ROUTINE
            s = ctx.do("Elbereth<CR>", ok=ROUTINE + [r"(?:misses|just misses)[!.]$", r"turns to flee"])
            break
        else:
            break
    return s


def elbereth(retries: int = 3):
    """Engrave Elbereth in the dust where you stand, read it back and
    re-engrave (up to `retries` times) if a letter slipped — engrave.c turns
    each dust letter into a random one 1 time in 25, so 28% of tries come out
    garbled (two in a row 8%: the live game, shift 5 #1203). Returns the final
    snap and prints OK / UNVERIFIED; still GARBLED after every try PAUSES (it
    protects nothing).

    NetHack 3.6.7 rules (monmove.c onscary, hack.c, engrave.c):
    - It must read exactly "Elbereth" (any case) and protects only while you
      STAND on it. It does not scare @ (humans and elves), minotaurs,
      shopkeepers, vault guards, peacefuls, or blind monsters, and does
      nothing in Gehennom or on the Planes.
    - Every step smudges dust engravings on the square you leave AND the one
      you enter: engrave where you stand, when you need it (a pre-made one
      nearby is usually already broken when you step back onto it).
    - Attacking (melee, firing, applying, kicking) while standing on it
      smudges it, and a scared monster you then attack makes you "feel like a
      hypocrite" (alignment penalty). Dust also decays at random over time.
    - While Blind you can engrave, but dust can't be felt: unverifiable."""
    st = ctx.last().status
    bad = {"Hallu", "Stun"} & set(st.conditions if st.ok else ())
    if bad:
        # engrave.c: each letter is garbled 1 time in 2 while hallucinating, 1 in 4 while stunned
        ctx.pause(f"elbereth(): you are {'/'.join(sorted(bad))} — the engraving would come out garbled (Hallu 1/2, "
                  "Stun 1/4 per letter). Wait it out, retreat, or pray if it's an emergency.")
        return ctx.last()
    if st.ok and "Conf" in st.conditions:
        print("elbereth(): confused — each letter is garbled 1 time in 7; the read-back will tell")
    blind = "Blind" in ctx.last().status.conditions
    s = ctx.last()
    for attempt in range(retries + 1):
        s = _engrave_elbereth()
        if s.state.kind != "command":
            return s
        if blind:
            print("elbereth(): engraved while Blind — dust engravings can't be felt, so it is UNVERIFIED "
                  "(a slipped letter makes it useless)")
            return s
        txt = engraving_here()
        if _elbereth_ok(txt):
            print("elbereth(): OK (reads \"Elbereth\")")
            return ctx.last()
        print(f"elbereth(): GARBLED ({txt!r})" + (" — engraving again" if attempt < retries else ""))
    ctx.pause(f"elbereth(): still GARBLED after {retries + 1} tries ({txt!r}) — it does NOT scare anything. "
              "elbereth() again, or get away")
    return ctx.last()


def _elbereth_ok(txt: str) -> bool:
    m = re.search(r'You (?:read|feel the words): "(.*)"', txt or "")
    return bool(m) and m.group(1).strip().lower() == "elbereth"


_ENGR_KIND = re.compile(r"(is written here in the (dust|frost)|is engraved here on the|"
                        r"has been (burned|melted) into the|some graffiti on the|scrawled in blood here)")
_ENGR_TEXT = re.compile(r"^You (read|feel the words): ")


def engraving_here() -> str:
    """What's engraved here (via ':' look; no game time), e.g.
    'Some text has been burned into the floor here. You read: "Elbereth".'
    The first sentence tells the kind: written in the dust (smudges),
    engraved (semi-permanent), burned (permanent), graffiti, blood.
    Returns '' when nothing is engraved here."""
    ctx.require_command("engraving_here()")
    s = ctx.do(":", quiet=True)
    parts = [m for m in s.messages if _ENGR_KIND.search(m) or _ENGR_TEXT.search(m)]
    txt = " ".join(parts)
    m = re.search(r'You (?:read|feel the words): "(.*)"', txt)
    if m and not _elbereth_ok(txt) and re.search(r"[Ee].{0,2}b.{0,2}r.{0,2}th|lber|bere", m.group(1)):
        txt += " [BROKEN Elbereth: it no longer scares anything — engrave again]"
    if not txt and "Blind" in s.status.conditions:
        print("engraving_here(): Blind — dust engravings can't be felt; burned/engraved ones can")
    return txt


import json as _json
import random as _random
from pathlib import Path as _Path

_REPO = _Path(__file__).resolve().parents[2]


def _harness_state() -> dict:
    name = getattr(ctx, "game_name", None)
    if not name:
        return {}
    p = _REPO / "run" / name / "harness_state.json"
    try:
        return _json.loads(p.read_text())
    except Exception:
        return {}


def _rnz(i: int, xl: int, rng) -> int:
    """NetHack 3.6 rnz() (hacklib/rnd.c): the log-normal-ish timeout roll."""
    x = i
    tmp = 1000 + rng.randrange(1000)
    # rne(4): geometric, capped at max(xl/3, 5)
    cap = max(xl // 3, 5)
    n = 1
    while n < cap and rng.randrange(4) == 0:
        n += 1
    tmp *= n
    if rng.randrange(2):
        x = x * tmp // 1000
    else:
        x = x * 1000 // tmp
    return x


def _p_timeout_below(limit: int, elapsed: int, xl: int, n: int = 20000) -> float:
    rng = _random.Random(12345)
    ok = sum(1 for _ in range(n) if _rnz(350, xl, rng) - elapsed <= limit)
    return ok / n


def _p_timeout_ok(limit: int, hs: dict, now: int, xl: int, n: int = 20000) -> float:
    """Chance that the prayer timeout (u.ublesscnt) is <= limit now, replaying what the harness saw: it
    starts at 300 (u_init.c) or at rnz(350) after the last prayer (pray.c pleased(); + rnz(1000) each for
    being a demigod — the Wizard killed or the invocation done — and for being crowned), drops by 1 a
    turn but never below 0 (allmain.c), gains 50-149 per wish (zap.c makewish), and a sacrifice showed
    it at 0 ("four-leaf clover") or reset it with a gift (rnz(300 + 50 * gifts)). A "hopeful feeling"
    sacrifice (pray.c dosacrifice) cut it by value*300/24 (500 for chaotics) and proves it was MORE than
    that: histories that contradict it are dropped (p3 shift 21: three such cuts, 324 turns, were ignored —
    "31%" where ~88% was right)."""
    prayers = hs.get("prayers", [])
    t0 = (prayers[-1].get("turn") or 0) if prayers else 0
    kick = sum(1 for k in ("demigod", "crowned") if (hs.get(k) or {}).get("turn") is not None
               and hs[k]["turn"] <= t0) if prayers else 0
    evs = [(w.get("turn") or 0, "wish", 0) for w in hs.get("wishes", [])]
    evs += [(e.get("turn") or 0, e.get("kind"), int(e.get("amount") or 0)) for e in hs.get("prayer_evidence", [])
            if e.get("kind") in ("zero", "reset") or (e.get("kind") == "reduced" and e.get("amount"))]
    evs = sorted(e for e in evs if e[0] >= t0)
    rng = _random.Random(12345)
    ok = kept = 0
    for _ in range(n):
        tmo = _rnz(350, xl, rng) + sum(_rnz(1000, xl, rng) for _k in range(kick)) if prayers else 300
        t = t0
        consistent = True
        for te, kind, amount in evs:
            tmo, t = max(0, tmo - (te - t)), te
            if kind == "wish":
                tmo += 50 + rng.randrange(100)
            elif kind == "zero":
                tmo = 0
            elif kind == "reset":
                tmo = _rnz(300, xl, rng)
            elif kind == "reduced":
                if tmo <= amount:          # it would have said "reconciliation" (0) or nothing
                    consistent = False
                    break
                tmo -= amount
        if not consistent:
            continue
        kept += 1
        tmo = max(0, tmo - (now - t))
        ok += tmo <= limit
    if not kept:
        # (records that no sampled history explains — e.g. an amount from a partly eaten corpse: ignore the cuts)
        return _p_timeout_ok(limit, dict(hs, prayer_evidence=[e for e in hs.get("prayer_evidence", [])
                                                              if e.get("kind") != "reduced"]), now, xl, n)
    return ok / kept


def _low_hp(st) -> bool:
    """pray.c critically_low_hp(): HP <= 5, or HP <= max/div with max capped
    at 15*XL and div 5 (XL1-5), 6 (6-13), 7 (14-21), 8 (22-29), 9 (30)."""
    xl = st.hd if st.hd is not None else st.xl
    mx = min(st.hpmax, 15 * max(1, xl))
    div = 5 if xl <= 5 else 6 if xl <= 13 else 7 if xl <= 21 else 8 if xl <= 29 else 9
    return st.hp <= 5 or st.hp * div <= mx


# pray.c in_trouble(): any attribute below its maximum (ABASE < AMAX) is TROUBLE_POISONED, a MINOR trouble —
# and every loss lowers only ABASE (attrib.c adjattrib()): poison, a potion of sickness, the weaken spell, a
# mind flayer, a foocubus, even exercise abuse. What says so:
_DRAIN_MSG = re.compile(
    r"^You feel (?:very )?(?:weak|stupid|foolish|clumsy|fragile|repulsive)!$"          # adjattrib() loss
    r"|^You feel (?:weaker|very sick|innately weaker|sick inside)[!.]$"                 # poisontell()
    r"|^Your (?:brain is on fire|judgement is impaired|muscles won't obey you)[!.]$"
    r"|^You break out in hives[!.]$|^You suddenly feel weaker!$"                        # (+ mcastu weaken)
    r"|^Ecch - that must have been poisonous!$|^You are down in the dumps\.$|^Your senses are dulled\.$")
# ... and what restores them all: a unicorn horn that fixed every trouble, blessed restore ability, the prayer fix
_RESTORED_MSG = re.compile(r"^This makes you feel great!$|^Wow!  ?This makes you feel great!$"
                           r"|^You feel in good health again\.$|^There's a tiger in your tank\.$")


_HORN_CONDS = {"conf": "Conf", "confusion": "Conf", "stun": "Stun", "blind": "Blind", "blindness": "Blind",
               "hallu": "Hallu", "hallucination": "Hallu", "foodpois": "FoodPois", "termill": "TermIll",
               "sick": ("FoodPois", "TermIll"), "illness": ("FoodPois", "TermIll")}


def unihorn(until: str | None = None, max_applies: int = 12, letter: str | None = None) -> dict:
    """Apply your unicorn horn until the trouble is gone (apply.c use_unicorn_horn(); a turn each).
    until: 'conf', 'stun', 'blind', 'hallu', 'sick' (FoodPois/TermIll) — stops once that condition is off the
    status line; 'nausea' (vomiting has no status flag) — stops at "You feel much less nauseated now.";
    'attributes' — stops at "This makes you feel great!"; None — until nothing is left: "Nothing happens."
    (no trouble at all) or "... feel great!". The messages mislead (p4 shift 4 #1133): "Nothing seems to
    happen." = troubles left but this try fixed none (apply again); "This makes you feel better!" = an
    ATTRIBUTE point came back — not a cure of anything else. Refuses a CURSED horn (it CAUSES troubles).
    Returns {"applies", "done", "messages"}."""
    from .items import inventory
    ctx.require_command("unihorn()")
    horn = next((i for i in inventory() if (letter and i["letter"] == letter)
                 or (not letter and re.search(r"\bunicorn horns?\b", i["text"]))), None)
    if horn is None:
        raise ValueError("unihorn(): no unicorn horn in the inventory" + (f" (letter {letter!r})" if letter else ""))
    if re.search(r"\bcursed\b", horn["text"]) and not re.search(r"\buncursed\b", horn["text"]):
        raise PermissionError(f"unihorn(): {horn['letter']} - {horn['text']} is CURSED: applying it makes you sick, "
                              "blind, confused, stunned, hallucinating or drains an attribute. Uncurse it first.")
    key = (until or "").strip().lower()
    conds = _HORN_CONDS.get(key)
    conds = (conds,) if isinstance(conds, str) else conds
    if key and conds is None and key not in ("nausea", "vomiting", "attributes", "attribute"):
        raise ValueError(f"unihorn(until={until!r}): use conf/stun/blind/hallu/sick/nausea/attributes or None")
    msgs: list = []
    n, done = 0, False
    for n in range(1, max_applies + 1):
        s = ctx.last()
        if conds and not set(conds) & set(s.status.conditions):
            n -= 1
            done = True
            break
        s = ctx.do("a", quiet=True)
        if s.state.kind != "object":
            if s.state.kind != "command":
                ctx.do("<Esc>", quiet=True)
            raise RuntimeError(f"unihorn(): 'a' gave {s.state.kind} {s.state.prompt!r}")
        s = ctx.do(horn["letter"], ok=[r"^Nothing (?:seems to )?happens?", r"^This makes you feel (?:great|better)!",
                                        r"^You feel much less nauseated now", r"^You can see again",
                                        r"^You feel less confused now", r"^You feel a bit steadier now",
                                        r"^Everything looks SO boring now", r"^You feel cured"])
        msgs += s.messages
        text = " | ".join(s.messages)
        if "Nothing happens" in text or "feel great" in text:
            done = True
            break
        if key in ("nausea", "vomiting") and "less nauseated" in text:
            done = True
            break
        if conds and not set(conds) & set(ctx.last().status.conditions):
            done = True
            break
        if s.state.kind != "command":
            break
    print(f"unihorn({until!r}): {n} apply(s) — " + ("done" if done else "NOT done yet (apply again or wait it out)")
          + (f"; last: {msgs[-1]!r}" if msgs else ""))
    return {"applies": n, "done": done, "messages": msgs}


def drained_attributes(hist: list | None = None) -> list:
    """Messages since the last full restore that lowered an attribute (TROUBLE_POISONED: minor trouble, and
    with it a prayer's 'pat on the head' is no longer certain — p3 shift 19 #27). [] when none (or all fixed)."""
    if hist is None:
        hist = [m for (_t, m) in getattr(ctx.game, "history", [])]
    last_fix = max((i for i, m in enumerate(hist) if _RESTORED_MSG.search(m)), default=-1)
    out = []
    for i, m in enumerate(hist):
        if i > last_fix and _DRAIN_MSG.search(m):
            if m.startswith("Ecch") and any("seem unaffected by the poison" in n for n in hist[i + 1:i + 3]):
                continue
            out.append(m)
    return out


def _major_cursed(cw: list) -> list:
    """The cursed worn/wielded items (inventory texts) that pray.c in_trouble() counts as MAJOR trouble: a
    cursed blindfold or towel over your eyes (TROUBLE_CURSED_BLINDFOLD), cursed levitation boots / ring of
    levitation (TROUBLE_CURSED_LEVITATION), a welded weapon leaving no free hand — two-handed, or beside a
    cursed shield (TROUBLE_UNUSEABLE_HANDS). Other cursed worn items are minor (worst_cursed_item())."""
    welded = getattr(ctx.game, "welded_weapon", None)
    if welded is None:                      # (no inventory() since the daemon started: judge by the text)
        from nh.game import is_weapon_text
        welds = lambda t: is_weapon_text(t)     # noqa: E731
    else:
        welds = lambda t: bool(welded) and t == welded    # noqa: E731
    # (pray.c: only weapons/weapon-tools weld (wield.c will_weld()) — a cursed wielded corpse, wand or lamp
    # doesn't, and beside a cursed shield it is minor trouble: review of 4c3f55f)
    out = [t for t in cw if (re.search(r"\b(?:blindfold|towel)\b", t) and "(being worn)" in t)
           or re.search(r"\blevitation\b", t) or ("(weapon in hands)" in t and welds(t))]
    wep = [t for t in cw if "(weapon in hand)" in t and welds(t)]
    shield = [t for t in cw if re.search(r"shield\b", t) and "(being worn)" in t]
    return out + (wep + shield if wep and shield else [])


def prayer_check() -> dict:
    """What would prayer do right now? Returns {trouble, reasons, since_last,
    p_safe, advice}. Mirrors pray.c can_pray(): the prayer timeout must be
    <= 200 with major trouble, <= 100 with minor, 0 with none; Luck < 0 or an
    angry god also fails. Praying too soon: -3 Luck, god anger, divine wrath."""
    s = ctx.last()
    st = s.status
    hist = [m for (_t, m) in getattr(ctx.game, "history", [])]
    reasons_major, reasons_minor = [], []
    for c in st.conditions:
        if c in ("Stone", "Slime", "Strngl", "FoodPois", "TermIll"):
            reasons_major.append(c)
        elif c == "Blind" and getattr(ctx.game, "blindfolded", None):
            # pray.c in_trouble(): TROUBLE_BLIND is timed blindness only (Blinded > 1), never a blindfold you wear
            # (p3 shift 23 #6) — while it is on, the status line can't show whether you are also timed-blind
            continue
        elif c in ("Blind", "Deaf", "Stun", "Conf", "Hallu"):
            reasons_minor.append(c)      # (pray.c: timed deafness counts as TROUBLE_BLIND)
    if st.hunger in ("Weak", "Fainting", "Fainted"):
        reasons_major.append(st.hunger)
    elif st.hunger == "Hungry":
        reasons_minor.append("Hungry")
    if st.ok and _low_hp(st):
        reasons_major.append(f"low HP {st.hp}/{st.hpmax}")
    fever = max((i for i, m in enumerate(hist) if "You feel feverish" in m), default=-1)
    cured = max((i for i, m in enumerate(hist) if "You feel purified" in m), default=-1)
    if fever > cured:
        reasons_major.append("lycanthropy")
    # pray.c in_trouble(): TROUBLE_PUNISHED is the first minor trouble (read.c punish: "You are being
    # punished for your misbehavior!"; a prayer: "Your chain disappears."; a nymph can steal it)
    pun = max((i for i, m in enumerate(hist) if "You are being punished for your misbehavior" in m), default=-1)
    freed = max((i for i, m in enumerate(hist) if re.search(r"Your chain disappears|removed your chain|"
                                                            r"You slip free of the buried ball", m)), default=-1)
    punished = getattr(ctx.game, "punished", None)
    if (pun > freed and punished is not False) or (punished and freed < 0):
        reasons_minor.insert(0, "punished (ball and chain)")
    cw = getattr(ctx.game, "cursed_worn", None) or []
    cw_major = _major_cursed(cw)
    if cw_major:
        # (p1 shift 41: a cursed blindfold stuck on — prayer_check() called it minor; pray() needed force)
        reasons_major.append("cursed: " + "; ".join(cw_major[:2]))
    if [t for t in cw if t not in cw_major]:
        # pray.c worst_cursed_item(): cursed worn armor/rings/amulet/blindfold or a welded weapon (known
        # from the last inventory() — inventory() refreshes it)
        reasons_minor.append("cursed worn: " + "; ".join([t for t in cw if t not in cw_major][:3]))
    stones = [t for t in getattr(ctx.game, "cursed_stones", None) or []
              if "luckstone" in t or st.encumbrance in ("Strained", "Overtaxed", "Overloaded")]
    if stones and not cw:
        reasons_minor.append("cursed stone: " + stones[0])
    drained = drained_attributes(hist)
    if drained:
        reasons_minor.append(f"drained attribute ({drained[-1]!r}" + (f" +{len(drained) - 1} more" if len(drained) > 1
                                                                        else "")
                             + ") — apply a unicorn horn until 'This makes you feel great!' ('Nothing seems to "
                               "happen' only means that try fixed nothing; 'Nothing happens.' = nothing to fix)")
    trouble = "major" if reasons_major else "minor" if reasons_minor else "none"
    limit = {"major": 200, "minor": 100, "none": 0}[trouble]
    hs = _harness_state()
    prayers = hs.get("prayers", [])
    turn = st.turn or 0
    wishes = hs.get("wishes", [])
    since = turn - (prayers[-1].get("turn") or 0) if prayers else None
    bad = bool(prayers) and any(k in (prayers[-1].get("outcome") or "")
                                for k in ("displeased", "You feel guilty"))
    p_safe = 0.0 if bad else _p_timeout_ok(limit, hs, turn, st.xl)
    evid = [e for e in hs.get("prayer_evidence", []) if e.get("kind") == "zero"]
    last_raise = max([p.get("turn") or 0 for p in prayers] + [w.get("turn") or 0 for w in wishes]
                     + [e["turn"] for e in hs.get("prayer_evidence", []) if e.get("kind") == "reset"] + [-1])
    zero = [e for e in evid if (e.get("turn") or 0) > last_raise]
    proven = (f" (proven: a sacrifice at T:{zero[-1]['turn']} showed the timeout at 0, nothing raised it since)"
              if zero and not bad else "")
    recent_w = [w for w in wishes if (w.get("turn") or 0) >= (prayers[-1].get("turn") or 0 if prayers else 0)]
    if recent_w:
        proven += (f" ({len(recent_w)} wish(es) since the last prayer: each added 50-149 turns to the timeout, "
                   "which then counts down 1 per turn)")
    where = hs.get("current_branch") or ""
    advice = []
    if where == "Gehennom":
        advice.append("IN GEHENNOM: prayer cannot help and may anger your god. Do not pray.")
        p_safe = 0.0
    if trouble == "none" and zero and not bad:
        advice.append("No trouble and the timeout is PROVEN 0: a prayer now is safe. On a co-aligned altar (or "
                      "anywhere) with alignment >= 14 it is a certain 'pat on the head' (pray.c pleased()): "
                      "rn2((Luck+6)/2) — 0 nothing, 1 fix/bless your weapon, 2 golden glow (+5 max HP, restore), "
                      "3 the castle tune hint, 4 uncurse your pack, 5 an intrinsic (telepathy/speed/stealth, else AC), "
                      "6 a spellbook, 7-8 CROWNING if piously aligned (20+): 2/9 at Luck 12-13, 1/8 at Luck 10-11, "
                      "none below. The timeout then resets to ~350 (crowned: + ~1000 on every later prayer). Any "
                      "minor trouble (a drained attribute, Hungry...) makes the pat a 1+rn2(Luck+3) >= 5 roll: fix "
                      "it first.")
    elif trouble == "none":
        advice.append("No trouble: prayer only helps if the timeout is exactly 0; don't pray.")
    elif trouble == "minor":
        advice.append("Only MINOR trouble (" + ", ".join(reasons_minor) + "): punishment, cursed items, a welded "
                      "weapon with a free off-hand, blindness/deafness, hunger(Hungry) are minor — fixed by a "
                      "prayer with the timeout under 100 and Luck > 0 (e.g. while carrying a luck item).")
    else:
        advice.append("MAJOR trouble: " + ", ".join(reasons_major) + ".")
    advice.append(f"Estimated chance the prayer timeout is low enough: {p_safe:.0%}"
                  + (f" ({since} turns since the last prayer)" if since is not None else " (no prayer yet)")
                  + proven + ". Luck must also be >= 0 and your god not angry.")
    return {"trouble": trouble, "reasons": reasons_major or reasons_minor, "since_last": since,
            "p_safe": round(p_safe, 3), "advice": " ".join(advice)}


# pray.c: what a successful prayer says (pleased(), fix_worst_trouble(), water_prayer())
_PRAYER_OK = [r"^You begin praying to ", r"^You are surrounded by a shimmering light", r"^You finish your prayer",
              r"^You feel that \w+ is (?:well-pleased|pleased|satisfied|pleased as punch|ticklish|full)\.",
              r"potions? on the altar glows? light blue", r"^You feel (?:much )?better\.",
              r"^Your \w+ feels content\.", r"^You can breathe again\.", r"^You feel in good health again",
              r"^You feel more limber", r"^The slime disappears", r"^Your surroundings change",
              r"^You feel purified", r"^You are back on solid ground", r"^Your .* softly glows? amber",
              r"^You feel a hopeful feeling", r"^You feel (?:much )?(?:stronger|slimmer)", r"^Looks like you are back",
              r"^Your amulet vanishes", r"^Your chain disappears", r"^There's a tiger in your tank",
              r"^Your .* no longer slippery", r"^You are surrounded by a golden glow"]
_PRAYER_VERDICT = [
    (r"is (?:displeased|bummed)\.", "FAILED: your god is displeased (prayed too soon / Luck < 0) — no help; "
                                     "don't pray again for ~1000 turns"),
    (r"relearn thy lessons", "FAILED: god ANGRY — you lost a level and Wisdom"),
    (r"black glow surrounds you", "FAILED: god ANGRY — some of your items were CURSED"),
    (r"Thou durst", "FAILED: god ANGRY — a hostile minion was sent: fight or flee"),
    (r"bolt of lightning|disintegration beam", "FAILED: divine WRATH"),
    (r"Since you are in Gehennom", "no help in Gehennom (and your god may be angry)"),
]


def pray(force: bool = False):
    """Pray, if prayer_check() says it's sensible (major trouble, timeout very
    likely OK, not in Gehennom); force=True overrides. Confirms the prompt;
    the prayer's own good messages don't pause. Prints a one-line verdict
    (success/failure, holy water made, troubles fixed). Returns the final
    snap."""
    chk = prayer_check()
    if not force and (chk["trouble"] != "major" or chk["p_safe"] < 0.8):
        raise PermissionError("pray() refused: " + chk["advice"] + " (pray(force=True) to override)")
    s = ctx.do("#pray<CR>", quiet=True)
    msgs = list(s.messages)
    for _ in range(4):
        p = s.state.prompt
        if s.state.kind == "yn" and "pray" in p:
            s = ctx.do("y", ok=_PRAYER_OK)
        elif s.state.kind in ("getlin", "yn", "object") and "yes" in p.lower() and "pray" in p:
            s = ctx.do("yes<CR>", ok=_PRAYER_OK)
        elif s.state.kind == "yn" and "Force the gods to be pleased" in p:
            s = ctx.do("y", ok=_PRAYER_OK)          # wizard-mode test games only
        else:
            break
        msgs += s.messages
    print("pray(): " + prayer_verdict(msgs))
    return s


def prayer_verdict(msgs) -> str:
    """One line from a prayer's messages."""
    joined = " | ".join(msgs)
    bits = []
    m = re.search(r"You feel that (\w+) is (well-pleased|pleased|satisfied|pleased as punch|ticklish|full)\.",
                  joined)
    if m:
        bits.append(f"SUCCESS: {m.group(1)} is {m.group(2)} (prayer timeout reset to ~50-1000: prayer_check() "
                    "before the next)")
    else:
        for pat, v in _PRAYER_VERDICT:
            if v and re.search(pat, joined):
                bits.append(v)
                break
    w = re.search(r"(Some of the|One of the|The) potions? on the altar glows? (light blue|black)", joined)
    if w:
        bits.append(("HOLY" if w.group(2) == "light blue" else "UNHOLY") + " water made from the water on the "
                    "altar (" + ("some of the potions" if w.group(1) == "Some of the" else
                                 "one potion" if w.group(1) == "One of the" else "all of it") + ")")
    fixed = [f for pat, f in ((r"You feel much better", "HP restored"),
                              (r"feels content", "hunger fixed"),
                              (r"You can breathe again", "strangulation fixed"),
                              (r"You feel in good health again|You feel purified", "illness/lycanthropy cured"),
                              (r"You feel more limber", "stoning cured"),
                              (r"The slime disappears", "sliming cured"),
                              (r"You are back on solid ground", "out of the lava"),
                              (r"softly glows? amber", "an item uncursed"),
                              (r"golden glow", "golden glow (HP/level restored)"))
             if re.search(pat, joined)]
    if fixed:
        bits.append("fixed: " + ", ".join(fixed))
    gift = re.search(r"grant thee the gift of ([\w ]+)|I crown thee|appears at your feet", joined)
    if gift:
        bits.append("GIFT: " + gift.group(0))
    return "; ".join(bits) or ("no verdict message seen: " + joined[-200:])


_OFFER_OUTCOMES = [
    (r"An object appears at your feet|Use my gift wisely", "GIFT: an artifact at your feet (pick it up, check it; "
                                                           "the prayer timeout was reset by the gift)"),
    (r"four-leaf clover|brushed your (?:foot|feet)", "Luck +1 or more — and your prayer timeout is 0 (prayer is "
                                                     "safe if Luck >= 0 and your god isn't angry)"),
    (r"feeling of reconciliation", "the prayer timeout is now 0"),
    (r"hopeful feeling", "the prayer timeout went down (not yet 0) — or your god's anger lessened"),
    (r"partially absolved", "your alignment improved (it was negative)"),
    (r"seems (?:slightly )?mollified", "your god's ANGER lessened"),
    (r"feeling of inadequacy", "your god is still ANGRY (that sacrifice wasn't enough)"),
    (r"insult to|infamous offense|repay loyalty|You feel guilty", "BAD: an offense (-alignment/-Luck)"),
    (r"power of .+ increase", "a CROSS-ALIGNED altar: it is now your god's (Luck +1; a temple priest there "
                              "turns hostile)"),
    (r"power of .+ decrease", "BAD: a CROSS-ALIGNED altar resisted (Luck -1)"),
    (r"sense a conflict", "a CROSS-ALIGNED altar"),
    (r"^Nothing happens", "nothing: the corpse was too old (more than 50 turns) or worthless"),
]
# pray.c dosacrifice() on a co-aligned altar with your god not angry: a nonzero prayer timeout ALWAYS prints
# "hopeful feeling" / "reconciliation" (every corpse takes >= 12 off it), so a sacrifice that only says it
# was consumed means the timeout was already 0 — and Luck didn't move (at its maximum, or a weak corpse)
_SILENT_OFFER = re.compile(r"is consumed in a (?:flash of light|burst of flame)|^Your sacrifice disappears")
_SILENT_OUTCOME = ("the prayer timeout is 0 (proven: a sacrifice that prints nothing but 'consumed' only happens "
                   "at timeout 0 — recorded for prayer_check())")
# the lines around an outcome (pray.c dosacrifice()): a converted altar's glow (live shift 11 #37-#40: the
# conversion paused the exec on "The altar glows white."), the hallucinated versions of the outcomes
_OFFER_FLAVOUR = [r"^The altar glows [\w -]+\.$", r"^The gods seem tall\.$",
                  r"^You realize that the gods are not like you and I\.$",
                  r"^Overall, there is a smell of fried onions\.$", r"^You see crabgrass at your feet"]
_OWN_RACE = ("dwarf", "dwarf lord", "dwarf king", "dwarf mummy", "dwarf zombie")    # M2_DWARF: our race
_UNICORN_ALIGN = {"white unicorn": "lawful", "gray unicorn": "neutral", "black unicorn": "chaotic"}


def _note_hopeful_cut(name: str, msgs: list) -> None:
    """A "You have a hopeful feeling." sacrifice: pray.c dosacrifice() cut the prayer timeout by
    value*300/24 (500 for chaotics), value = the monster's difficulty + 1 (+1 undead unless you are chaotic)
    — file that amount on the tracker's "reduced" record so prayer_check() can replay it. Not for a partly
    eaten corpse (less value: unknown)."""
    from nh.danger import monster_record
    rec = monster_record(name) or {}
    if not rec.get("difficulty") or any(re.search(r"\bpartly eaten\b", m) for m in msgs):
        return
    st = ctx.last().status
    chaotic = (st.align or "").lower().startswith("chaotic")
    value = int(rec["difficulty"]) + 1 + (1 if "M2_UNDEAD" in rec.get("flags2", []) and not chaotic else 0)
    amount = value * (500 if chaotic else 300) // 24
    mem = getattr(getattr(ctx, "game", None), "memory", None)
    state = getattr(mem, "state", None)
    if not isinstance(state, dict) or st.turn is None:
        return
    ev = state.setdefault("prayer_evidence", [])
    rec_ev = next((e for e in reversed(ev) if e.get("turn") == st.turn and e.get("kind") == "reduced"), None)
    if rec_ev is None:
        ev.append({"turn": st.turn, "kind": "reduced", "amount": amount})
    else:
        rec_ev["amount"] = amount
    try:
        mem.save()
    except Exception:  # noqa: BLE001
        pass
    print(f"offer(): the {name} (value {value}) cut the prayer timeout by {amount} turns (recorded for prayer_check())")


def _note_prayer_evidence(turn, kind: str) -> None:
    """Add {"turn", "kind"} to the harness memory's prayer_evidence (tracker.py fills it from messages;
    this is for what only a helper can tell, e.g. a silent sacrifice)."""
    mem = getattr(getattr(ctx, "game", None), "memory", None)
    st = getattr(mem, "state", None)
    if not isinstance(st, dict) or turn is None:
        return
    ev = st.setdefault("prayer_evidence", [])
    if not ev or ev[-1] != {"turn": turn, "kind": kind}:
        ev.append({"turn": turn, "kind": kind})
        try:
            mem.save()
        except Exception:  # noqa: BLE001
            pass


def offer(pattern: str | None = None, max_age: int = 50, letter: str | None = None) -> dict:
    """#offer a corpse lying here, on the altar you stand on: the first one
    (or the first matching `pattern`) that is safe to offer. Refuses corpses
    of your own race (dwarves: -5 Luck, the altar is desecrated) and a
    unicorn of the altar's alignment (an insult); skips corpses the harness
    knows died more than `max_age` turns ago (worthless after 50). Prints and
    returns the outcome: Luck up / prayer timeout 0 (recorded for
    prayer_check()), gift, or nothing. Kill on or next to the altar, or carry
    light fresh corpses there: offer(letter='h') drops your corpse h on the
    altar first (the drop also shows its BUC) and offers that one."""
    ctx.require_command("offer()")
    from nh.danger import base_name
    s = ctx.last()
    if s.under != "_":
        raise RuntimeError("offer(): you are not standing on an altar")
    if letter:
        s = ctx.do("d" + letter, ok=[r" lands? on the altar", r"flash as .* hits? the altar"])
        for msg in s.messages:
            t = re.sub(r"^There is an? (?:amber|black) flash as ", "", msg)
            m = re.search(r"^(?:[Aa]n? |[Tt]he |\d+ )?(?:(?:blessed|uncursed|cursed|partly eaten) )*(.+?) "
                          r"corpses? (?:lands?|hits?) ", t)
            if m and pattern is None:
                pattern = re.escape(base_name(m.group(1)))
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
            raise RuntimeError(f"offer(): dropping {letter!r} opened {s.state.kind} {s.state.prompt!r}")
    altar = (getattr(s, "feature_desc", None) or {}).get(s.hero, "")
    rx = re.compile(pattern, re.I) if pattern else None
    s = ctx.do("#offer<CR>", quiet=True)
    msgs = list(s.messages)
    offered = None
    for _ in range(12):
        p = s.state.prompt or ""
        if s.state.kind != "yn":
            break
        mm = re.search(r"There (?:is|are) (?:an? |\d+ )?(.+?) corpses? here; sacrifice", p)
        if not mm:
            s = ctx.do("n", quiet=True)
            msgs += s.messages
            continue
        name = base_name(mm.group(1).replace("partly eaten ", ""))
        age = ctx.game.corpse_age(name, s.last_pos, s.status.turn if s.status.ok else None) \
            if hasattr(ctx.game, "corpse_age") else None
        why = ("your own race (a dwarf)" if name in _OWN_RACE else
               "a unicorn of the altar's alignment (an insult)" if name in _UNICORN_ALIGN
               and (not altar or _UNICORN_ALIGN[name] in altar) else
               f"{age} turns old (worthless after {max_age})" if age is not None and age > max_age else
               "not the one asked for" if rx is not None and not rx.search(mm.group(1)) else "")
        if why or offered:
            if why and not offered:
                print(f"offer(): skipping the {name} corpse: {why}")
            s = ctx.do("n", quiet=True)
        else:
            offered = name
            s = ctx.do("y", ok=[p for p, _ in _OFFER_OUTCOMES] + [_SILENT_OFFER.pattern] + _OFFER_FLAVOUR)
        msgs += s.messages
    if s.state.kind != "command":
        ctx.do("<Esc>", quiet=True)
    joined = " | ".join(msgs)
    outcome = next((o for pat, o in _OFFER_OUTCOMES if any(re.search(pat, m) for m in msgs)), "")
    if offered and outcome.startswith("the prayer timeout went down"):
        _note_hopeful_cut(offered, msgs)
    if offered and not outcome and any(_SILENT_OFFER.search(m) for m in msgs):
        st = ctx.last().status
        if "Hallu" in " ".join(st.conditions or []):
            outcome = "accepted (hallucinating: the messages can't be trusted)"
        else:
            outcome = _SILENT_OUTCOME
            _note_prayer_evidence(st.turn, "zero")
    if not offered:
        outcome = "nothing offered" + (f" ({msgs[-1]})" if msgs else "")
    print(f"offer(): {offered or '-'}: {outcome}")
    return {"offered": offered, "outcome": outcome, "messages": msgs}


def rest_on_elbereth(turns: int = 100, until_hp: int | None = None, burst: int = 10):
    """Rest on a verified dust Elbereth to heal: engraves one if missing or
    broken, rests in bursts of `burst` turns, re-checks the engraving between
    bursts (scared monsters smudge it; it decays), and stops at full HP (or
    until_hp), after `turns` turns, or when something Elbereth doesn't scare
    comes within 3 squares (@ humans/elves, minotaurs, shopkeepers, guards,
    blind monsters — it pauses). Returns the last snap."""
    s = ctx.require_command("rest_on_elbereth()")
    from .combat import warn_bounce
    warn_bounce("rest_on_elbereth()")
    if "Blind" in s.status.conditions:
        ctx.pause("rest_on_elbereth(): you are Blind — a dust Elbereth can't be verified; rest elsewhere or cure it")
        return ctx.last()
    target = until_hp if until_hp is not None else s.status.hpmax
    done = 0
    while done < turns:
        s = ctx.last()
        if s.status.ok and s.status.hp >= target:
            break
        threats = [m for m in s.hostiles(3) if m["ch"] == "@" or "minotaur" in (m.get("desc") or "")]
        if threats:
            ctx.pause("rest_on_elbereth(): " + ", ".join(f"{m.get('desc') or m['ch']} at ({m['x']},{m['y']})"
                                                          for m in threats) + " ignores Elbereth")
            return ctx.last()
        if not _elbereth_ok(engraving_here()):
            elbereth()
            if not _elbereth_ok(engraving_here()):
                ctx.pause("rest_on_elbereth(): couldn't get a clean Elbereth here")
                return ctx.last()
        s = rest(burst)
        done += burst
    return ctx.last()


# do_wear.c Blindf_on()/Blindf_off(), on_msg()/off_msg()
_BLINDF_OK = [r"^You are now wearing ", r"^You can't see any more\.", r"^You were wearing ",
              r"^You can see again\.", r"^You still cannot see\.", r"^You can see!",
              # monmove.c: a mind flayer's blast from more than 13 squares off does nothing (p2 shift 32: the
              # scan stopped at its put-on step); the census lists the flayer anyway
              r"^You sense a faint wave of psychic energy\.$",
              # Excalibur / an intrinsic's auto-search during the scan's turns (p1 shift 34 #231): the found trap
              # is recorded anyway (the #terrain re-read), the scan still prints its census
              r"^You find an? "]


def _scan_watch_list(mons: list, s) -> list:
    """The census's monsters to watch ('approaching' pauses once they move within 6 squares): hostiles that are
    DANGEROUS for you now (threat_level) — p2 shift 30: a watch on every monster with any note paused for hill
    giants and Green-elves. On the Wizard's Tower levels, not those on the other side of its sealed walls
    (p2 shift 32 #606: a white dragon inside while the hero was outside) — covetous ones teleport, so they stay."""
    from nh.danger import covetous, threat_level
    xl = s.status.xl if s.status.ok else None
    hp = s.status.hp if s.status.ok else None
    res = getattr(ctx.game, "intrinsics", ()) or ()
    from .desmap import in_box, tower_interior
    box = tower_interior(s)

    def inside(c):
        return in_box(box, c)
    return [m for m in mons if m.get("id") is not None and not m.get("tame") and not m.get("peaceful")
            and m.get("desc") and threat_level(m["desc"], xl, hp, res) == "dangerous"
            and (box is None or s.hero is None or inside((m["x"], m["y"])) == inside(s.hero)
                 or covetous(m["desc"]))]


def telepathy_scan(letter: str | None = None, describe: bool = True) -> list:
    """One call: put on your blindfold/towel (P), read every monster your telepathy shows on the level,
    take it off again (R): 2 turns. No pause for the Blind you asked for or for the monsters it reveals;
    anything else (HP loss, an attack) still pauses. Needs intrinsic telepathy (a floating eye corpse).
    letter: which blindfold/towel (default: the first one). Returns [{"desc", "ch", "x", "y", "dist",
    "note"}] nearest first (pets and peacefuls included, marked in desc) and prints them."""
    from .items import inventory
    s = ctx.require_command("telepathy_scan()")
    if "telepathy" not in (getattr(ctx.game, "intrinsics", None) or ()):
        print("telepathy_scan: no intrinsic telepathy known (eat a floating eye corpse) — blind you may see "
              "nothing")
    already = s.status.ok and "Blind" in s.status.conditions
    put_on = None
    if not already:
        cands = [i for i in inventory() if re.search(r"\b(?:blindfold|towel)\b", i["text"])
                 and "(being worn)" not in i["text"] and (letter is None or i["letter"] == letter)]
        if not cands:
            raise ValueError("telepathy_scan(): no blindfold or towel to put on" + (f" (letter {letter!r})"
                                                                                    if letter else ""))
        put_on = cands[0]["letter"]
    out: list = []
    with ctx.no_monster_pauses():
        if put_on:
            s = ctx.do("P", quiet=True)
            if s.state.kind != "object":
                if s.state.kind != "command":
                    ctx.do("<Esc>", quiet=True)
                ctx.pause(f"telepathy_scan: 'P' didn't ask what to put on ({s.state.kind}: {s.state.prompt!r})")
                return out
            s = ctx.do(put_on, ok=_BLINDF_OK, expect=("blind",))
            if not (s.status.ok and "Blind" in s.status.conditions):
                ctx.pause(f"telepathy_scan: putting on {put_on} didn't blind you ({s.messages or s.state.kind})")
                return out
        s = ctx.last()
        mons = [m for m in s.monsters or [] if not m.get("engulfer") and m["ch"] != "I"   # (I: old markers)
                and not m.get("statue")]
        if describe:
            got = _describe_all([m for m in mons if not m.get("desc") and m["ch"] not in "I"])
            tr = getattr(ctx.game, "tracker", None)
            for m in mons:
                if not m.get("desc") and (m["x"], m["y"]) in got:
                    m["desc"] = got[(m["x"], m["y"])]
                    if tr is not None and hasattr(tr, "note_label"):
                        tr.note_label(m)      # (a peaceful among look-alikes: labels need a look)
        h = s.hero
        from nh.danger import note_for, glyph_species
        xl = s.status.xl if s.status.ok else None
        watched = _scan_watch_list(mons, s)
        for m in mons:
            d = m.get("dist")
            if d is None and h is not None:
                d = max(abs(m["x"] - h[0]), abs(m["y"] - h[1]))
            note = m.get("note") or (note_for(m.get("desc") or "", xl, getattr(ctx.game, "intrinsics", ()))
                                     if m.get("desc") else "")
            rec = {"desc": m.get("desc") or "", "ch": m["ch"], "x": m["x"], "y": m["y"], "dist": d, "note": note}
            if not rec["desc"]:
                # never looked at (p3 shift 19 #419: 84 of 96 Castle monsters): what the glyph can be
                rec["color"] = m.get("color") or ""
                rec["could_be"] = glyph_species(m["ch"], rec["color"])
            out.append(rec)
        if put_on:
            s = ctx.do("R", quiet=True)
            if s.state.kind == "object":
                s = ctx.do(put_on, ok=_BLINDF_OK)
            elif s.state.kind != "command":
                ctx.do("<Esc>", quiet=True)
            s = ctx.last()
            if s.status.ok and "Blind" in s.status.conditions:
                print(f"telepathy_scan: !! still Blind after taking {put_on} off ({s.messages}) — check inventory()")
    out.sort(key=lambda m: (m["dist"] if m["dist"] is not None else 999))
    s = ctx.last()
    if s.status.ok:
        # hunt((x, y)) closes in on a monster sensed here although it isn't in view afterwards (the dark)
        ctx.game.last_scan = {"turn": s.status.turn, "level": ctx.game.level_key(s.status), "mons": list(out)}
    hostile = [m for m in out if not m["desc"].startswith(("tame ", "peaceful "))]
    w = getattr(ctx, "watch_monsters", None)
    if w is not None and watched:
        # seen now, they won't count as NEW when they come into view later: pause when one moves while within
        # 6 squares (a minotaur 3 squares off behind a wall too: its first move in view pauses)
        n = w(watched)
        if n:
            print(f"telepathy_scan: watching {n} noted monster(s) — any of them moving within 6 squares of you "
                  "pauses ('approaching')")
    from nh.danger import base_name
    kinds: dict = {}
    for m in out:
        k = base_name(m["desc"]) or "?"
        kinds[k] = kinds.get(k, 0) + 1
    # every hostile with a SERIOUS danger note (a demon lord 40 squares off matters more than a newt next
    # door: COVETOUS, much stronger than you, an all-caps warning), then the nearest of the rest
    def serious(m):
        n = m["note"]
        return bool(n) and bool(re.search(r"COVETOUS|stronger than you|\b[A-Z]{4,}\b", n))
    noted = [m for m in hostile if serious(m)]
    others = [m for m in out if m not in noted][:max(8, 30 - len(noted))]
    shown = sorted(noted + others, key=lambda m: (m not in noted, m["dist"] if m["dist"] is not None else 999))
    rest = [m for m in out if m not in shown]
    unseen = [m for m in out if not m["desc"]]
    print(f"telepathy_scan: {len(out)} monster(s), {len(hostile)} not tame/peaceful — "
          + ", ".join(f"{n} {k}" for k, n in sorted(kinds.items(), key=lambda kv: -kv[1]))
          + ("".join(f"\n  {m['ch']} {m['desc'] or _unseen_label(m)} at ({m['x']},{m['y']}) d={m['dist']}"
                     + (f"  !! {m['note']}" if m['note'] else "") for m in shown))
          + (f"\n  ... {len(rest)} more, none with a serious note (the return value lists all)"
             if rest and not any(not m["desc"] for m in rest) else
             f"\n  ... {len(rest)} more ({sum(1 for m in rest if not m['desc'])} of them NOT looked at)" if rest
             else "")
          + (_unseen_summary(unseen) if unseen else "")
          + "\n  (telepathy never shows MINDLESS monsters: zombies Z, mummies M, golems ', elementals E, blobs b, "
            "jellies j, puddings P, F, lights y, vortices v, spheres e — a square the scan shows empty can still hold "
            "one: p4 shift 5 planned a zoo route over 'empty' squares that held mummies and jellies)")
    return out


def _describe_all(mons: list) -> dict:
    """{(x, y): description} for these sensed monsters: one batch look (describe_cells, no game time), the cells
    it missed once more, then single farlooks for what is still missing (the most dangerous-looking glyphs and
    the nearest first, up to 60). A batch that comes back short says so (p3 shift 19 #419/#441: 84 of 96
    Castle monsters stayed '?', and the scan still said "none with a serious note")."""
    from nh.danger import noted_lookalikes
    cells = list(dict.fromkeys((m["x"], m["y"]) for m in mons))
    got: dict = {}
    if not cells:
        return got
    for _ in range(2):
        missing = [c for c in cells if c not in got]
        if not missing:
            break
        try:
            got.update({c: d for c, d in ctx.game.describe_cells(missing[:150]).items() if d})
        except Exception as e:  # noqa: BLE001
            print(f"telepathy_scan: the batch look failed ({type(e).__name__}: {e})")
    missing = [c for c in cells if c not in got]
    if missing:
        at = {(m["x"], m["y"]): m for m in mons}

        def order(c):
            m = at.get(c) or {}
            return (not noted_lookalikes(m.get("ch", ""), m.get("color", "")), m.get("dist") or 99)
        n = 0
        for c in sorted(missing, key=order)[:60]:
            try:
                d = ctx.game.farlook(*c)
            except Exception:  # noqa: BLE001
                d = ""
            d = _farlook_name(d)
            if d:
                got[c] = d
                n += 1
        print(f"telepathy_scan: the batch look missed {len(missing)} of {len(cells)} monster(s); single farlooks "
              f"named {n} of them")
    return got


def _farlook_name(text: str) -> str:
    """farlook()'s raw text ("D  a dragon (red dragon) [seen: telepathy]") -> the monster part ("red dragon",
    "peaceful gnome lord"), as describe_cells() gives it."""
    m = re.search(r"\(([^()]*)\)\s*(?:\[[^\]]*\])?\s*$", text or "")
    if m:
        return m.group(1).strip()
    return (text or "").strip()


def _unseen_label(m: dict) -> str:
    cands = m.get("could_be") or []
    return ("? NOT LOOKED AT" + (f" ({m.get('color')}: {' / '.join(cands[:4])}"
                                 + (" ..." if len(cands) > 4 else "") + ")" if cands else ""))


def _unseen_summary(unseen: list) -> str:
    """One line per glyph class of the monsters nobody could look at."""
    from nh.danger import noted_lookalikes
    groups: dict = {}
    for m in unseen:
        groups.setdefault((m["ch"], m.get("color") or ""), []).append(m)
    parts = []
    for (ch, col), ms in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        cands = ms[0].get("could_be") or []
        risky = noted_lookalikes(ch, col)
        parts.append(f"{len(ms)}x {ch} {col or '?'}" + (f" ({' / '.join(cands[:4])})" if cands else "")
                     + (f" — may be {', '.join(risky[:3])} (danger note)" if risky else ""))
    return (f"\n  !! {len(unseen)} monster(s) could NOT be looked at — don't treat them as harmless: "
            + "; ".join(parts[:12]) + (" ..." if len(parts) > 12 else "")
            + ". farlook(x, y) the ones that matter before you move.")


# engrave.c doengrave(): what burning with a wand says
_BURN_OK = [r"^Flames fly from the wand", r"^Lightning arcs from the wand", r"^You are blinded by the flash",
            r"^You (?:burn|melt) into the", r"^You will overwrite the current message", r"^You wipe out the message",
            r"^This .+ is a wand of (?:fire|lightning)!", r"^You feel the wand heat up", r"^You hear crackling",
            r"^Your hair stands up", r"^You add to the text", r"^The engraving now reads"]
_BURN_WAND = re.compile(r"\bwands? of (fire|lightning)\b")


def burn_elbereth(wands=None, lightning: bool = False, force: bool = False) -> dict:
    """Burn a PERMANENT Elbereth where you stand with a wand of fire (a wand of lightning only with
    lightning=True: its flash blinds you for up to 50 turns). Tries the wands in turn: one that is "too
    worn out to engrave" (empty) is remembered as EMPTY (zap() refuses it too) and the next is tried.
    Refuses while Blind, Hallucinating, Stunned or Confused (letters come out garbled: blind 1 in 11 each)
    unless force=True. Reads it back (burned text can be felt even blind).
    wands: letters to try, in order (default: your identified wands of fire, then lightning if allowed).
    Returns {"ok", "wand", "text", "empty"}.
    A burned Elbereth never smudges: fighting monsters that ignore it (@ humans/elves, minotaurs,
    shopkeepers, guards, priests) from it costs nothing; attacking one that RESPECTS it is hypocrisy
    (-5 alignment) and deletes it. It does nothing in Gehennom or on the Planes."""
    from .combat import ROUTINE
    from .items import inventory
    s = ctx.require_command("burn_elbereth()")
    out = {"ok": False, "wand": None, "text": "", "empty": []}
    bad = {"Blind", "Hallu", "Stun", "Conf"} & set(s.status.conditions if s.status.ok else ())
    if bad and not force:
        ctx.pause(f"burn_elbereth(): you are {'/'.join(sorted(bad))} — the letters would come out garbled (a "
                  "burned engraving can't be fixed, only burned over): wait it out or cure it (unicorn horn); "
                  "force=True burns anyway")
        return out
    inv = inventory()
    empty = getattr(ctx.game, "empty_wands", None)
    if empty is None:
        ctx.game.empty_wands = empty = set()
    if wands is None:
        kinds = ("fire", "lightning") if lightning else ("fire",)
        cands = []
        for kind in kinds:
            cands += [i["letter"] for i in inv if (_BURN_WAND.search(i["text"]) or [None, None])[1] == kind]
    else:
        cands = list(wands)
    texts = {i["letter"]: i["text"] for i in inv}
    cands = [c for c in cands if force or (c not in empty and not re.search(r"\(\d+:0\)", texts.get(c, "")))]
    if not cands:
        ctx.pause("burn_elbereth(): no wand to try (identified wands of fire" + (" / lightning" if lightning else "")
                  + " that aren't known EMPTY) — pass wands=['x'] to try an unidentified one, or elbereth() "
                    "for dust")
        return out
    for w in cands:
        s = ctx.do("E", quiet=True)
        if s.state.kind != "object":
            if s.state.kind != "command":
                ctx.do("<Esc>", quiet=True)
            ctx.pause(f"burn_elbereth(): 'E' didn't ask what to write with ({s.state.kind}: {s.state.prompt!r})")
            return out
        s = ctx.do(w, quiet=True, ok=_BURN_OK)
        wrote = False
        for _ in range(6):
            k, p = s.state.kind, s.state.prompt or ""
            if k == "yn" and "add to the current engraving" in p:
                s = ctx.do("n", quiet=True, ok=_BURN_OK)
            elif k == "getlin":
                s = ctx.do("Elbereth<CR>", ok=ROUTINE + _BURN_OK + [r"(?:misses|just misses)[!.]$",
                                                                     r"turns to flee"])
                wrote = True
                break
            elif k == "yn" and "Do you want to" in p:
                s = ctx.do("n", quiet=True)
            else:
                break
        msgs = " ".join(ctx.last().messages or []) + " " + " ".join(s.messages or [])
        if "too worn out to engrave" in msgs or (not wrote and re.search(r"You wrest|glows and fades", msgs)):
            empty.add(w)
            out["empty"].append(w)
            print(f"burn_elbereth(): wand {w} is EMPTY (\"too worn out to engrave\") — trying the next one")
            continue
        if ctx.last().state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        if not wrote:
            print(f"burn_elbereth(): wand {w} didn't burn anything ({msgs.strip() or 'no message'})")
            continue
        out["wand"] = w
        if not re.search(r"Flames fly|Lightning arcs|heat up|crackling|hair stands up|burn into|melt into",
                         msgs):
            print(f"burn_elbereth(): wand {w} wrote, but not by burning? ({msgs.strip()}) — the read-back tells")
        txt = engraving_here()
        out["text"] = txt
        out["ok"] = _elbereth_ok(txt) and bool(re.search(r"burned into|melted into", txt))
        if out["ok"]:
            print(f"burn_elbereth(): OK — burned with wand {w}: {txt}")
        else:
            print(f"burn_elbereth(): NOT a clean burned Elbereth ({txt!r}) — burn again over it (it asks to "
                  "add: the helper answers n = overwrite)")
        return out
    ctx.pause(f"burn_elbereth(): every wand tried was EMPTY ({out['empty']}) — engrave in the dust (elbereth()) "
              "or recharge one")
    return out
