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


def pray():
    """Pray. Confirms the prompt (paranoid 'yes' or 'y'). Returns final snap.
    Only pray when in real trouble (HP<1/7 max or <6, weak from hunger,
    stoning, sliming, strangling, lycanthropy, food poisoning...) and the
    prayer timeout has likely expired (~1000 turns since last prayer; the
    first prayer is safe from about turn 300)."""
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
