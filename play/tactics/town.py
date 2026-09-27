"""Town helpers: temple donations (protection).

priest.c: #chat with a peaceful temple priest -> "... asks you for a
contribution" -> "How much will you offer?". An offer of 400*XL up to (not
including) 600*XL buys protection: the first time you get -2..-4 AC, later +1
each while your protection is below 20 (and only rarely once it is 9+).
Offering 0 / escaping that prompt angers a co-aligned priest (-1 alignment).
"""

from __future__ import annotations

import re

from . import ctx
from .mapview import DIR_KEY

_PRIEST = re.compile(r"\bpriest(?:ess)?\b")


def buy_protection() -> dict:
    """Donate exactly 400 x XL gold to the adjacent peaceful temple priest.
    Checks gold and the priest first; answers every prompt (never leaves the
    offer prompt empty). Returns {"outcome", "offered", "messages", "ac_before",
    "ac_after"}."""
    s = ctx.last()
    st = s.status
    if not st.ok or s.hero is None:
        raise RuntimeError("buy_protection: not at the command prompt")
    amount = 400 * st.xl
    if st.gold < amount:
        raise ValueError(f"buy_protection: need {amount} gold (400 x XL{st.xl}), you have {st.gold}")
    pri = [m for m in s.monsters if m.get("dist") == 1 and _PRIEST.search(m.get("desc") or "")]
    if not pri:
        raise ValueError("buy_protection: no priest next to you (stand next to the temple priest)")
    p = pri[0]
    if not p.get("peaceful"):
        raise ValueError(f"buy_protection: the {p.get('desc')} is not peaceful")
    key = DIR_KEY[(p["x"] - s.hero[0], p["y"] - s.hero[1])]
    ac0 = st.ac
    s = ctx.do("#chat<CR>", quiet=True)
    if s.state.kind != "direction":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        raise RuntimeError(f"buy_protection: #chat gave {s.state.kind} {s.state.prompt!r}")
    s = ctx.do(key, quiet=True)
    msgs = list(s.messages)
    if not (s.state.kind == "getlin" and "offer" in (s.state.prompt or "")):
        ctx.pause(f"buy_protection: expected 'How much will you offer?', got {s.state.kind} {s.state.prompt!r}")
        return {"outcome": "unexpected", "offered": 0, "messages": msgs, "ac_before": ac0, "ac_after": ac0}
    s = ctx.do(f"{amount}<CR>", quiet=True)
    msgs += s.messages
    text = " ".join(msgs)
    outcome = ("PROTECTION" if "rewarded for thy devotion" in text
               else "no protection (already well protected)" if "selfless generosity" in text
               else "pious (offer below 400 x XL?)" if "pious individual" in text
               else "unknown")
    ac1 = ctx.last().status.ac
    print(f"buy_protection: offered {amount}: {outcome}; AC {ac0} -> {ac1}")
    return {"outcome": outcome, "offered": amount, "messages": msgs, "ac_before": ac0, "ac_after": ac1}


def pay(x: int | None = None, y: int | None = None) -> list:
    """Pay the shopkeeper for everything you picked up ('p', "Itemized
    billing?" -> n). With several shopkeepers in range the game asks "Pay
    whom?" with a cursor: pass the shopkeeper's square (x, y). Returns the
    messages."""
    from .nav import cursor_to
    ctx.require_command("pay()")
    s = ctx.do("p", quiet=True)
    msgs = list(s.messages)
    for _ in range(6):
        k, p = s.state.kind, s.state.prompt or ""
        if k == "command":
            break
        if k == "getpos":
            if x is None:
                ctx.do("<Esc>", quiet=True)
                raise RuntimeError("pay(): 'Pay whom?' — several shopkeepers in range: call pay(x, y) with the "
                                   "square of the one you owe")
            cursor_to(x, y)
            s = ctx.do(".", quiet=True)
        elif k == "yn" and "Itemized billing" in p:
            s = ctx.do("n", quiet=True)
        elif k == "yn" and re.search(r"\bPay\?", p):
            s = ctx.do("y", quiet=True)
        else:
            ctx.pause(f"pay(): unexpected {k} {p!r}")
            s = ctx.last()
        msgs += s.messages
    return msgs
