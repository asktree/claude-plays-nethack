"""Read and toggle boolean game options through the in-game `O` menu (no
game time). Useful to verify the rc file took effect on a server."""

from __future__ import annotations

import re

from . import ctx

_BOOL = re.compile(r"^(\w+)\s+\[(true|false)\]$")


def _walk(on_item):
    """Open O, call on_item(page, item) for every item (stop when it returns
    True: the O menu then stays open on that page). Returns the snap."""
    s = ctx.do("O", quiet=True)
    for page in range(15):
        if s.state.kind != "menu":
            return s, None
        for it in s.state.menu:
            if on_item(page, it):
                return s, it
        if s.state.menu.page < s.state.menu.pages:
            s = ctx.do(">", quiet=True)
        else:
            break
    return s, None


def bool_options() -> dict:
    """{name: True/False} for every boolean option in the O menu."""
    out = {}

    def grab(_page, it):
        m = _BOOL.match(it.text.strip())
        if m:
            out[m.group(1)] = m.group(2) == "true"
        return False

    s, _ = _walk(grab)
    if s.state.kind == "menu":
        ctx.do("<Esc>", quiet=True)
    return out


def set_bool(name: str, value: bool) -> bool:
    """Set boolean option `name` (e.g. set_bool('timed_delay', False)).
    Returns the value read back afterwards."""
    def hit(_page, it):
        m = _BOOL.match(it.text.strip())
        return bool(m and m.group(1) == name)

    s, it = _walk(hit)
    if it is None:
        if s.state.kind == "menu":
            ctx.do("<Esc>", quiet=True)
        raise KeyError(f"no boolean option {name!r} in the O menu")
    current = _BOOL.match(it.text.strip()).group(2) == "true"
    if current == value:
        ctx.do("<Esc>", quiet=True)
        return current
    ctx.do(it.letter, quiet=True)
    s = ctx.do("<CR>", quiet=True)
    for _ in range(3):
        if s.state.kind == "command":
            break
        s = ctx.do("<Esc>", quiet=True)
    return bool_options().get(name, current)
