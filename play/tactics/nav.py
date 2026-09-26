"""Navigation tactics: cursor positioning, travel, farlook, stepping."""

from __future__ import annotations

from . import ctx
from .benign import BENIGN
from .mapview import DIR_KEY, bfs_path, dist, find, nearest


class NavError(Exception):
    pass


def _cursor_keys(cx, cy, tx, ty) -> str:
    """Keys that move the getpos cursor from (cx,cy) to (tx,ty).
    Capital letters move 8 cells (truncated at map edges, so we verify)."""
    keys = []
    dx, dy = tx - cx, ty - cy
    while abs(dx) >= 8 and abs(dy) >= 8:
        k = DIR_KEY[((dx > 0) - (dx < 0), (dy > 0) - (dy < 0))].upper()
        keys.append(k)
        dx -= 8 * ((dx > 0) - (dx < 0))
        dy -= 8 * ((dy > 0) - (dy < 0))
    while abs(dx) >= 8:
        keys.append("L" if dx > 0 else "H")
        dx -= 8 if dx > 0 else -8
    while abs(dy) >= 8:
        keys.append("J" if dy > 0 else "K")
        dy -= 8 if dy > 0 else -8
    while dx and dy:
        keys.append(DIR_KEY[((dx > 0) - (dx < 0), (dy > 0) - (dy < 0))])
        dx -= (dx > 0) - (dx < 0)
        dy -= (dy > 0) - (dy < 0)
    while dx:
        keys.append("l" if dx > 0 else "h")
        dx -= (dx > 0) - (dx < 0)
    while dy:
        keys.append("j" if dy > 0 else "k")
        dy -= (dy > 0) - (dy < 0)
    return "".join(keys)


def cursor_to(tx, ty, rounds=5):
    """In a getpos prompt, move the cursor to (tx, ty). Returns final snap."""
    s = ctx.last()
    for _ in range(rounds):
        if s.state.kind != "getpos":
            if s.state.kind != "command":
                ctx.do("<Esc>", quiet=True)
            raise NavError(f"not in a position prompt (state={s.state.kind}: {s.state.prompt!r})")
        cx, cy = s.screen.cursor
        if (cx, cy) == (tx, ty):
            return s
        s = ctx.do(_cursor_keys(cx, cy, tx, ty), quiet=True)
    if s.screen.cursor != (tx, ty):
        ctx.do("<Esc>", quiet=True)
        raise NavError(f"could not place cursor at {(tx, ty)} (at {s.screen.cursor})")
    return s


def farlook(x, y) -> str:
    """Describe what's displayed at (x, y) using ';' (takes no game time)."""
    s = ctx.do(";", quiet=True)
    if s.state.kind != "getpos":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        raise NavError(f"';' did not open a position prompt: {s.state.kind} {s.state.prompt!r}")
    cursor_to(x, y)
    s = ctx.do(".", quiet=True)
    txt = " ".join(s.messages).strip()
    if s.state.kind not in ("command",):
        # e.g. a lingering prompt; get back to the map
        ctx.do("<Esc>", quiet=True)
    return txt


def travel(x, y, max_legs=6, max_dist=None):
    """Travel to (x, y) with NetHack's `_` command (auto-pathing over known
    map; stops when something interesting happens). Re-issues while making
    progress. Returns the final Snap (check .hero, .messages).
    max_dist: refuse (NavError) if the known-map path is longer than this —
    a guard against burning many turns on a far-away target."""
    s = ctx.last()
    if max_dist is not None and s.hero is not None:
        path = bfs_path(s, s.hero, (x, y), allow_monsters=True)
        if path is None or len(path) > max_dist:
            raise NavError(f"travel to {(x, y)}: path length {None if path is None else len(path)} > max_dist {max_dist}")
    for _ in range(max_legs):
        h0 = s.hero
        if h0 == (x, y):
            return s
        s = ctx.do("_", quiet=True)
        if s.state.kind != "getpos":
            return s
        cursor_to(x, y)
        s = ctx.do(".", ok=BENIGN)
        if s.state.kind != "command":
            return s
        h1 = s.hero
        if h1 == (x, y) or h1 is None or h1 == h0:
            return s
        if s.messages:
            return s   # something happened en route; let the caller look
    return s


def travel_to(ch: str, index: int = 0, color_num: int | None = None):
    """Travel to the index-th nearest cell showing `ch` (e.g. '>', '<', '{')."""
    s = ctx.last()
    cells = find(s, ch, color_num)
    h = s.hero
    if not cells or h is None:
        raise NavError(f"no {ch!r} on the map")
    cells.sort(key=lambda c: dist(c, h))
    if index >= len(cells):
        raise NavError(f"only {len(cells)} {ch!r} on the map")
    return travel(*cells[index])


def step(direction: str, n: int = 1):
    """Move one square n times (direction: y k u h l b j n). Stops on messages
    (inside exec) like any do()."""
    s = ctx.last()
    for _ in range(n):
        s = ctx.do(direction)
    return s


def go_down():
    """Travel to the nearest '>' and descend."""
    s = travel_to(">")
    if s.hero is not None and ctx.last().screen.at(*s.hero) in "@":
        pass
    return ctx.do(">")


def go_up():
    s = travel_to("<")
    return ctx.do("<")


def kick_door(x, y, tries: int = 8):
    """Kick the (adjacent) door at (x, y) until it opens/breaks. Never do this
    to shop doors (angers the shopkeeper) or in Minetown (angers the Watch)."""
    s = ctx.last()
    h = s.hero
    if h is None or max(abs(x - h[0]), abs(y - h[1])) != 1:
        raise NavError(f"kick_door: {(x, y)} is not adjacent to you at {h}")
    key = DIR_KEY[(x - h[0], y - h[1])]
    for _ in range(tries):
        s = ctx.do("<C-d>", quiet=True)
        if s.state.kind != "direction":
            return s
        s = ctx.do(key, ok=[r"^WHAMM", r"crashes open", r"^As you kick the door, it (crashes|shatters)"])
        text = " ".join(s.messages)
        if "crashes open" in text or "shatters" in text or "breaks" in text or ctx.last().screen.at(x, y) != "+":
            return s
    return s
