"""Inventory and item-selection helpers."""

from __future__ import annotations

import re

from . import ctx

_BUC = re.compile(r"\b(blessed|uncursed|cursed)\b")


def _parse_menu_pages(first):
    """Collect all items of a (possibly multi-page) menu, then close it."""
    s = first
    items = []
    cls = ""
    seen_pages = 0
    while s.state.kind == "menu" and seen_pages < 20:
        m = s.state.menu
        for it in m.items:
            if it.header:
                cls = it.text
                continue
            if it.letter:
                items.append({"letter": it.letter, "text": it.text, "class": cls,
                              "buc": (_BUC.search(it.text).group(1) if _BUC.search(it.text) else "")})
        seen_pages += 1
        if m.page < m.pages:
            s = ctx.do(">", quiet=True)
        else:
            break
    if s.state.kind == "menu":
        s = ctx.do("<Esc>", quiet=True)
    return items, s


def inventory():
    """Return the hero's inventory as a list of {letter, text, class, buc}."""
    ctx.require_command("inventory()")
    s = ctx.do("i", quiet=True)
    if s.state.kind == "menu":
        items, _ = _parse_menu_pages(s)
        return items
    # "Not carrying anything." or a tiny inventory shown on the message line
    return []


def inventory_text():
    inv = inventory()
    out, cls = [], None
    for it in inv:
        if it["class"] != cls:
            cls = it["class"]
            out.append(f"[{cls}]")
        out.append(f"  {it['letter']} - {it['text']}")
    return "\n".join(out) if out else "(empty)"


def find_item(pattern: str, inv=None):
    rx = re.compile(pattern, re.I)
    for it in inv or inventory():
        if rx.search(it["text"]):
            return it
    return None


def here():
    """What's on the floor here (':' look). Takes no game time."""
    ctx.require_command("here()")
    s = ctx.do(":", quiet=True)
    return " | ".join(s.messages)


# ---- engrave-identification of wands ------------------------------------------

_ENGRAVE_ID = [
    (r"is a wand of ([\w ]+)!", None),   # auto-identified (digging/fire/lightning)
    (r"Gravel flies up|You hear drilling|Chips fly out|Ice chips fly up|Splinters fly up|You feel tremors",
     "digging"),
    (r"Flames fly from the wand|You feel the wand heat up", "fire"),
    (r"Lightning arcs from the wand|You hear crackling|Your hair stands up", "lightning"),
    (r"bugs on the .* stop moving", "sleep or death"),
    (r"bugs on the .* slow down", "slow monster"),
    (r"bugs on the .* speed up", "speed monster"),
    (r"is riddled by bullet holes", "magic missile"),
    (r"A few ice cubes drop from the wand", "cold"),
    (r"unsuccessfully fights your attempt to write", "striking"),
    (r"engraving on the .* vanishes", "cancellation, teleportation or make invisible"),
    (r"The engraving now reads", "polymorph"),
    (r"You feel self-knowledgeable", "enlightenment"),
    (r"A lit field surrounds you", "light"),
    (r"turns to dust", "(the wand was empty and crumbled)"),
    (r"too worn out to engrave", "(cancelled wand)"),
]
_NO_EFFECT = ("no effect: nothing, opening, locking, probing, undead turning, an EMPTY wand"
              " — or secret door detection / create monster with nothing to show")


def engrave_test(letter: str, text: str = "Elbereth", prep: bool = True, force: bool = False) -> dict:
    """Engrave-identify the wand in inventory slot `letter` in one call.

    - Refuses (unless force=True) on a square with a burned/engraved message:
      cancellation/teleport/make-invisible would erase it and polymorph would
      rewrite it (e.g. your burned Elbereth). Don't test in shops either.
    - prep=True: if nothing is engraved here, first writes "x" in the dust
      with your finger (1 turn), so the vanish/polymorph groups show up.
    - Answers "add to the current engraving?" with n, writes `text`.
    - A wish prompt (wand of wishing!) or anything unexpected pauses.
    Returns {"verdict", "messages", "autoidentified"}; also prints the verdict."""
    from .survival import engraving_here
    cur = engraving_here()
    permanent = re.search(r"burned into|melted into|is engraved here", cur or "")
    if permanent and not force:
        raise PermissionError(f"engrave_test: there is a permanent engraving here ({cur!r}); testing could "
                              "erase or change it. Move to a clean square (force=True to override).")
    msgs: list[str] = []
    if prep and not cur:
        s = ctx.do("E", quiet=True)
        if s.state.kind == "object":
            s = ctx.do("-", quiet=True)
            for _ in range(4):
                if s.state.kind == "yn" and "add to the current engraving" in s.state.prompt:
                    s = ctx.do("n", quiet=True)
                elif s.state.kind == "getlin":
                    s = ctx.do("x<CR>", quiet=True)
                    break
                else:
                    break
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
    s = ctx.do("E", quiet=True)
    if s.state.kind != "object":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        raise RuntimeError(f"engrave_test: expected 'What do you want to write with?', got {s.state.kind}")
    s = ctx.do(letter, quiet=True)
    msgs += s.messages
    for _ in range(8):
        k, p = s.state.kind, s.state.prompt or ""
        if k == "getlin" and "wish" in p.lower():
            ctx.pause("engrave_test: WAND OF WISHING — the wish prompt is open. Follow PLAYBOOK §E for what to "
                      "wish for; answer with cont(reply='...<CR>') after deciding. Don't let it time out.")
            s = ctx.last()
            msgs += s.messages
            continue
        if k == "yn" and "add to the current engraving" in p:
            s = ctx.do("n", quiet=True)
        elif k == "getlin":
            s = ctx.do(f"{text}<CR>", quiet=True)
        elif k == "command":
            break
        else:
            ctx.pause(f"engrave_test: unexpected {k} prompt {p!r}")
            s = ctx.last()
        msgs += s.messages
    joined = " | ".join(msgs)
    verdict, auto = None, False
    for pat, v in _ENGRAVE_ID:
        m = re.search(pat, joined)
        if m:
            verdict = v if v is not None else m.group(1).strip()
            auto = v is None
            break
    if verdict is None:
        verdict = _NO_EFFECT
    print(f"engrave_test({letter!r}): {verdict}" + (" (auto-identified)" if auto else ""))
    return {"verdict": verdict, "messages": msgs, "autoidentified": auto}


# ---- dipping (Excalibur) ------------------------------------------------------

_DIP_OUTCOMES = [
    (r"a hand reaches up to bless the sword", "EXCALIBUR"),
    (r"grants you a wish", "WISH"),
    (r"You unleash", "WATER DEMON (dangerous: flee or Elbereth; it may have granted a wish)"),
    (r"You attract", "WATER NYMPH (steals: kill it fast or keep away)"),
    (r"stream of snakes|Snakes!", "WATER MOCCASINS (poisonous: retreat, fight one at a time)"),
    (r"dries up|reduces to a trickle", "fountain dried up"),
    (r"freezing mist", "CURSED sword (you are not lawful?!)"),
    (r"(rusts|rusty|corrode)", "sword rusted"),
    (r"spot a gem", "gem"),
    (r"gushes forth", "water gushes"),
    (r"coins", "coins"),
]


def dip(letter: str, into_fountain: bool = True) -> dict:
    """Dip inventory item `letter` into the fountain/pool you stand on, one
    dip per call: answers the prompts and classifies the outcome.
    For Excalibur: lawful, XL5+, long sword, full HP, a planned escape, never
    in Minetown (the Watch). Each dip: 1/6 Excalibur; otherwise the sword may
    rust and the fountain dries up about 1 time in 3 — so expect to need 2-3
    fountains. Returns {"outcome", "messages"}; prints the outcome."""
    ctx.require_command("dip()")
    s = ctx.do("#dip<CR>", quiet=True)
    if s.state.kind != "object":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        raise RuntimeError(f"dip: expected 'What do you want to dip?', got {s.state.kind} {s.state.prompt!r}")
    s = ctx.do(letter, quiet=True)
    msgs = list(s.messages)
    p = s.state.prompt or ""
    if s.state.kind == "yn" and ("fountain" in p or "pool" in p or "moat" in p or "water" in p):
        if not into_fountain:
            ctx.do("n", quiet=True)
        else:
            s = ctx.do("y", quiet=True)
            msgs += s.messages
    elif s.state.kind != "command":
        ctx.do("<Esc>", quiet=True)
        raise RuntimeError(f"dip: not standing on a fountain/pool (got {s.state.kind}: {p!r})")
    joined = " | ".join(msgs)
    outcome = "; ".join(o for pat, o in _DIP_OUTCOMES if re.search(pat, joined)) or "nothing special"
    if s.state.kind == "getlin" and "wish" in (s.state.prompt or "").lower():
        outcome = "WISH"
        ctx.pause("dip: WISH prompt open — follow PLAYBOOK §E (first wish: blessed +2 gray dragon scale mail); "
                  "answer with cont(reply='...<CR>') promptly.")
    print(f"dip({letter!r}): {outcome}")
    return {"outcome": outcome, "messages": msgs}
