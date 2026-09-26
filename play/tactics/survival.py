"""Survival tactics: Elbereth, prayer, searching, resting."""

from __future__ import annotations

import re

from . import ctx


def search(n: int = 10):
    """Search n turns in place (count-prefixed 's'; interrupted by monsters)."""
    return ctx.do(f"{int(n)}s")


def rest(n: int = 20):
    """Rest n turns in place (count-prefixed '.'; needs !rest_on_space off: '.')."""
    return ctx.do(f"{int(n)}.")


def elbereth():
    """Engrave Elbereth in the dust with a finger. Returns the final snap.

    3.6 rules: most monsters won't melee you while you stand on it (not @
    humans, minotaurs, shopkeepers/guards/priests, the Riders). Attacking
    while standing on it usually erases it; so does fighting/firing. Dust
    engravings can smudge when monsters flee over... re-engrave as needed."""
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
        elif k == "command":
            break
        else:
            break
    return s


def engraving_here() -> str:
    """Read what's engraved here (via ':' look). No game time."""
    s = ctx.do(":", quiet=True)
    txt = " | ".join(s.messages)
    m = re.search(r"(?:Something is written here in the dust|You read): ?\"?([^\"]*)\"?", txt)
    return txt if not m else m.group(0)


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
