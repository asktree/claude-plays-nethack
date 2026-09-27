"""Survival tactics: Elbereth, prayer, searching, resting."""

from __future__ import annotations

import re

from . import ctx


def search(n: int = 10):
    """Search n turns in place (count-prefixed 's'; interrupted by monsters).
    A monster fleeing from your Elbereth ("turns to flee") doesn't pause."""
    ctx.require_command("search()")
    return ctx.do(f"{int(n)}s", ok=[r"turns to flee"])


def rest(n: int = 20):
    """Rest n turns in place (count-prefixed '.'; needs !rest_on_space off: '.').
    A monster fleeing from your Elbereth ("turns to flee") doesn't pause."""
    ctx.require_command("rest()")
    return ctx.do(f"{int(n)}.", ok=[r"turns to flee", r"^You stop searching"])


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
            s = ctx.do("Elbereth<CR>")
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
    trouble = "major" if reasons_major else "minor" if reasons_minor else "none"
    limit = {"major": 200, "minor": 100, "none": 0}[trouble]
    hs = _harness_state()
    prayers = hs.get("prayers", [])
    turn = st.turn or 0
    wishes = hs.get("wishes", [])
    if not prayers:
        timeout = 300 - turn + sum(99 for w in wishes)      # 50-149 per wish, take the mean
        p_safe = 1.0 if timeout <= limit else 0.0
        since = None
    else:
        last = prayers[-1]
        since = turn - (last.get("turn") or 0)
        bad = any(k in (last.get("outcome") or "") for k in ("displeased", "You feel guilty"))
        wish_after = sum(99 for w in wishes if (w.get("turn") or 0) >= (last.get("turn") or 0))
        p_safe = _p_timeout_below(limit - wish_after, since, st.xl) if not bad else 0.0
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
                  + ". Luck must also be >= 0 and your god not angry.")
    return {"trouble": trouble, "reasons": reasons_major or reasons_minor, "since_last": since,
            "p_safe": round(p_safe, 3), "advice": " ".join(advice)}


def pray(force: bool = False):
    """Pray, if prayer_check() says it's sensible (major trouble, timeout very
    likely OK, not in Gehennom); force=True overrides. Confirms the prompt.
    Returns the final snap."""
    chk = prayer_check()
    if not force and (chk["trouble"] != "major" or chk["p_safe"] < 0.8):
        raise PermissionError("pray() refused: " + chk["advice"] + " (pray(force=True) to override)")
    s = ctx.do("#pray<CR>", quiet=True)
    for _ in range(4):
        p = s.state.prompt
        if s.state.kind == "yn" and "pray" in p:
            s = ctx.do("y")
        elif s.state.kind in ("getlin", "yn", "object") and "yes" in p.lower() and "pray" in p:
            s = ctx.do("yes<CR>")
        else:
            break
    return s


def rest_on_elbereth(turns: int = 100, until_hp: int | None = None, burst: int = 10):
    """Rest on a verified dust Elbereth to heal: engraves one if missing or
    broken, rests in bursts of `burst` turns, re-checks the engraving between
    bursts (scared monsters smudge it; it decays), and stops at full HP (or
    until_hp), after `turns` turns, or when something Elbereth doesn't scare
    comes within 3 squares (@ humans/elves, minotaurs, shopkeepers, guards,
    blind monsters — it pauses). Returns the last snap."""
    s = ctx.require_command("rest_on_elbereth()")
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
