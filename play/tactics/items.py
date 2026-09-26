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
    s = ctx.do(":", quiet=True)
    return " | ".join(s.messages)
