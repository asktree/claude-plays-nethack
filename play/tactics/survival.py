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
    return _counted(f"{int(n)}.", int(n), [r"turns to flee", r"^You stop searching"])


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


def elbereth(retries: int = 1):
    """Engrave Elbereth in the dust where you stand, read it back and
    re-engrave (up to `retries` times) if a letter slipped. Returns the
    final snap and prints OK / GARBLED / UNVERIFIED.

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
    it at 0 ("four-leaf clover") or reset it with a gift (rnz(300 + 50 * gifts))."""
    prayers = hs.get("prayers", [])
    t0 = (prayers[-1].get("turn") or 0) if prayers else 0
    kick = sum(1 for k in ("demigod", "crowned") if (hs.get(k) or {}).get("turn") is not None
               and hs[k]["turn"] <= t0) if prayers else 0
    evs = [(w.get("turn") or 0, "wish") for w in hs.get("wishes", [])]
    evs += [(e.get("turn") or 0, e.get("kind")) for e in hs.get("prayer_evidence", [])
            if e.get("kind") in ("zero", "reset")]
    evs = sorted(e for e in evs if e[0] >= t0)
    rng = _random.Random(12345)
    ok = 0
    for _ in range(n):
        tmo = _rnz(350, xl, rng) + sum(_rnz(1000, xl, rng) for _k in range(kick)) if prayers else 300
        t = t0
        for te, kind in evs:
            tmo, t = max(0, tmo - (te - t)), te
            if kind == "wish":
                tmo += 50 + rng.randrange(100)
            elif kind == "zero":
                tmo = 0
            elif kind == "reset":
                tmo = _rnz(300, xl, rng)
        tmo = max(0, tmo - (now - t))
        ok += tmo <= limit
    return ok / n


def _low_hp(st) -> bool:
    """pray.c critically_low_hp(): HP <= 5, or HP <= max/div with max capped
    at 15*XL and div 5 (XL1-5), 6 (6-13), 7 (14-21), 8 (22-29), 9 (30)."""
    xl = st.hd if st.hd is not None else st.xl
    mx = min(st.hpmax, 15 * max(1, xl))
    div = 5 if xl <= 5 else 6 if xl <= 13 else 7 if xl <= 21 else 8 if xl <= 29 else 9
    return st.hp <= 5 or st.hp * div <= mx


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
        elif c in ("Blind", "Stun", "Conf", "Hallu"):
            reasons_minor.append(c)
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
    cw = getattr(ctx.game, "cursed_worn", None) or []
    if cw:
        # pray.c worst_cursed_item(): cursed worn armor/rings/amulet/blindfold or a welded weapon (known
        # from the last inventory() — inventory() refreshes it)
        reasons_minor.append("cursed worn: " + "; ".join(cw[:3]))
    stones = [t for t in getattr(ctx.game, "cursed_stones", None) or []
              if "luckstone" in t or st.encumbrance in ("Strained", "Overtaxed", "Overloaded")]
    if stones and not cw:
        reasons_minor.append("cursed stone: " + stones[0])
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
    if trouble == "none":
        advice.append("No trouble: prayer only helps if the timeout is exactly 0; don't pray.")
    elif trouble == "minor":
        advice.append("Only MINOR trouble (" + ", ".join(reasons_minor) + "): cursed items, a welded weapon with "
                      "a free off-hand, blindness, hunger(Hungry) are minor — rarely worth a prayer.")
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
    (r"insult to|infamous offense|repay loyalty|You feel guilty", "BAD: an offense (-alignment/-Luck)"),
    (r"^Nothing happens", "nothing: the corpse was too old (more than 50 turns) or worthless"),
    (r"is consumed in a (?:flash of light|burst of flame)", "accepted, no visible effect (Luck already high?)"),
]
_OWN_RACE = ("dwarf", "dwarf lord", "dwarf king", "dwarf mummy", "dwarf zombie")    # M2_DWARF: our race
_UNICORN_ALIGN = {"white unicorn": "lawful", "gray unicorn": "neutral", "black unicorn": "chaotic"}


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
            s = ctx.do("y", ok=[p for p, _ in _OFFER_OUTCOMES])
        msgs += s.messages
    if s.state.kind != "command":
        ctx.do("<Esc>", quiet=True)
    joined = " | ".join(msgs)
    outcome = next((o for pat, o in _OFFER_OUTCOMES if re.search(pat, joined)), "")
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
              r"^You can see again\.", r"^You still cannot see\.", r"^You can see!"]


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
            need = [(m["x"], m["y"]) for m in mons if not m.get("desc") and m["ch"] not in "I"]
            if need:
                try:
                    got = ctx.game.describe_cells(need[:150])
                except Exception:  # noqa: BLE001
                    got = {}
                for m in mons:
                    if not m.get("desc") and (m["x"], m["y"]) in got:
                        m["desc"] = got[(m["x"], m["y"])]
        h = s.hero
        from nh.danger import note_for
        xl = s.status.xl if s.status.ok else None
        watched = [m for m in mons if m.get("id") is not None and not m.get("tame") and not m.get("peaceful")
                   and (m.get("note") or (m.get("desc") and note_for(m["desc"], xl,
                                                                     getattr(ctx.game, "intrinsics", ()))))]
        for m in mons:
            d = m.get("dist")
            if d is None and h is not None:
                d = max(abs(m["x"] - h[0]), abs(m["y"] - h[1]))
            note = m.get("note") or (note_for(m.get("desc") or "", xl, getattr(ctx.game, "intrinsics", ()))
                                     if m.get("desc") else "")
            out.append({"desc": m.get("desc") or "", "ch": m["ch"], "x": m["x"], "y": m["y"], "dist": d,
                        "note": note})
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
    print(f"telepathy_scan: {len(out)} monster(s), {len(hostile)} not tame/peaceful — "
          + ", ".join(f"{n} {k}" for k, n in sorted(kinds.items(), key=lambda kv: -kv[1]))
          + ("".join(f"\n  {m['ch']} {m['desc'] or '?'} at ({m['x']},{m['y']}) d={m['dist']}"
                     + (f"  !! {m['note']}" if m['note'] else "") for m in shown))
          + (f"\n  ... {len(out) - len(shown)} more, none with a serious note (the return value lists all)"
             if len(out) > len(shown) else ""))
    return out


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
