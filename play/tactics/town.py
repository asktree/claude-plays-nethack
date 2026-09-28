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
    s0 = ctx.require_command("pay()")
    s = ctx.do("p", quiet=True)
    msgs = list(s.messages)
    for _ in range(6):
        k, p = s.state.kind, s.state.prompt or ""
        if k == "command":
            break
        if k == "getpos":
            if x is None:
                # inside a shop the harness knows: its keeper (p4 shift 6 #1641: "Pay whom?" in Bojolali's shop)
                owner = (getattr(s0, "shop", "") or "").split("'")[0].strip() if "'" in (getattr(s0, "shop", "")
                                                                                         or "") else ""
                keep = [m for m in (s0.monsters or []) if owner and m["ch"] == "@"
                        and re.search(rf"\b{re.escape(owner)}\b", m.get("desc") or "")]
                if len(keep) == 1:
                    x, y = keep[0]["x"], keep[0]["y"]
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


_OFFER = re.compile(r"^(?P<shk>.+?) offers(?: only)? (?P<n>\d+) gold pieces? for ")
_CLASS_OF = (("scroll", "SCROLL_CLASS"), ("potion", "POTION_CLASS"), ("ring", "RING_CLASS"),
             ("wand", "WAND_CLASS"), ("amulet", "AMULET_CLASS"), ("spellbook", "SPBOOK_CLASS"))


def sell_offer(letter: str) -> dict:
    """In a shop, on an EMPTY floor square: drop item `letter`, read the
    shopkeeper's offer, DECLINE it ('n' — the item stays yours) and pick the
    item up again (2 turns). Returns {"offer", "per_item", "shk", "item",
    "candidates"}: candidates = price_id(<its class>, sell=per_item) for an
    unidentified scroll/potion/ring/wand/amulet/spellbook (the shopkeeper's
    lowballing habit is learned along the way). offer None: "seems
    uninterested" (not this shop's kind of item) or "cannot pay"."""
    from .info import price_id
    from .items import here, inventory, pickup
    s = ctx.require_command("sell_offer()")
    if not getattr(s, "shop", ""):
        raise RuntimeError("sell_offer(): you are not inside a shop")
    look = here()
    if look and "You see no objects here" not in look:
        raise RuntimeError(f"sell_offer(): step onto an empty floor square first (here: {look[:80]}) — picking "
                           "your item up again must not take the shop's goods")
    it = next((i for i in inventory() if i["letter"] == letter), None)
    if it is None:
        raise RuntimeError(f"sell_offer(): no item {letter!r} in your inventory")
    s = ctx.do("d", quiet=True)
    if s.state.kind != "object":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        raise RuntimeError(f"sell_offer(): 'd' gave {s.state.kind}: {s.state.prompt!r}")
    s = ctx.do(letter, quiet=True)
    offer, shk = None, None
    texts = list(s.messages) + ([s.state.prompt] if s.state.prompt else [])
    for t in texts:
        m = _OFFER.search(t or "")
        if m:
            offer, shk = int(m.group("n")), m.group("shk")
    if s.state.kind == "yn":
        s = ctx.do("n", quiet=True)          # decline: the item stays yours ("no charge")
    msgs = pickup()                           # the square was empty: everything here is yours
    qty = re.match(r"^(\d+) ", re.sub(r"^[a-zA-Z$] - ", "", it["text"]))
    n = int(qty.group(1)) if qty else 1
    per = (offer // n if offer % n == 0 else round(offer / n, 1)) if offer is not None else None
    klass = next((k for w, k in _CLASS_OF if re.search(rf"\b{w}s?\b", it["text"])), None)
    # (the shopkeeper prices the whole stack: p3 shift 15 #998 got "75 for 2 ... (None each)")
    cands = price_id(klass, sell=offer, shk=shk, qty=n) if (klass and offer and not re.search(r"\bof\b", it["text"])) \
        else []
    print(f"sell_offer({letter}): " + (f"{shk} offers {offer} for {it['text']}" + (f" ({per} each)" if n > 1 else "")
                                       + (f" — base price candidates: {cands}" if cands else "")
                                       if offer is not None else f"no offer ({' | '.join(texts)[:120]})")
          + ("" if any("You have a little trouble" in m or "- " in m for m in msgs) else ""))
    return {"offer": offer, "per_item": per, "shk": shk, "item": it["text"], "candidates": cands}
