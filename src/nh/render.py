"""Text renderings of snapshots for the LLM player (token-conscious)."""

from __future__ import annotations

from .game import Snap
from .parse import MAP_BOTTOM, MAP_TOP, MONSTER_CHARS
from .screen import COLOR_NAMES

try:  # optional: glyph -> monster name candidates, generated from NetHack source
    from .data import glyphs as _glyphs  # type: ignore
except Exception:  # pragma: no cover
    _glyphs = None


def header(snap: Snap) -> str:
    st = snap.status
    bits = [f"#{snap.n}"]
    bits.append(st.short() if st.ok else "(status unreadable)")
    bits.append(f"[{snap.state.kind}]")
    return " ".join(bits)


def ruler(x0: int, x1: int, indent: int = 4) -> str:
    """Two-row column ruler: tens digit and ones digit for EVERY column, so a
    column number can be read directly above any cell (e.g. 4/7 -> x=47)."""
    tens = "".join(str((x // 10) % 10) for x in range(x0, x1))
    ones = "".join(str(x % 10) for x in range(x0, x1))
    pad = " " * indent
    return f"{pad}{tens}\n{pad}{ones}"


def map_block(snap: Snap, x0: int = 0, x1: int = 80, y0: int = MAP_TOP, y1: int = MAP_BOTTOM,
              mark_hero: bool = False) -> str:
    scr = snap.screen
    out = [ruler(x0, x1)]
    for y in range(y0, y1 + 1):
        row = scr.row(y)[x0:x1]
        out.append(f"{y:>2} |{row.rstrip()}")
    return "\n".join(out)


def monsters_in_view(snap: Snap, radius: int | None = None, hero=None) -> list[dict]:
    from .mapscan import monsters_in_view as _miv
    return _miv(snap, radius, hero)


def monsters_line(snap: Snap, radius: int | None = None, mons: list[dict] | None = None) -> str:
    if mons is None:
        mons = monsters_in_view(snap, radius)
    elif radius is not None:
        mons = [m for m in mons if m["dist"] is None or m["dist"] <= radius]
    if not mons:
        return ""
    parts = []
    for m in mons:
        if m.get("desc"):
            who = m["desc"]
        else:
            tag = " PET?" if m["pet"] else ""
            maybe = f" ~{'/'.join(m['maybe'])}" if m.get("maybe") else ""
            who = f"{m['color']}{tag}{maybe}"
        adj = "  <-- ADJACENT" if m["dist"] == 1 else ""
        if m.get("new"):
            adj += "  (NEW)"
        note = f"\n      !! {m['note']}" if m.get("note") else ""
        parts.append(f"  {m['ch']} {who} at ({m['x']},{m['y']}) d={m['dist']}{adj}{note}")
    return "monsters:\n" + "\n".join(parts)


def render(snap: Snap, mode: str = "crop", radius: int = 6, mons: list[dict] | None = None,
           hero: tuple[int, int] | None = None) -> str:
    """mode: 'full' (whole map + ruler), 'crop' (window around @), 'brief' (no map).
    `hero` = last known hero position, used when the cursor is off the map
    (prompt states)."""
    lines = [header(snap)]
    if snap.messages:
        lines.append("msgs: " + " | ".join(snap.messages))
    if getattr(snap, "unsent", ""):
        lines.append(f"!! NOT SENT: {snap.unsent!r} — {snap.stop_reason}")
    k = snap.state.kind
    if k != "command":
        if snap.state.prompt:
            lines.append(f"PROMPT ({k}): {snap.state.prompt}")
        if k == "yn" and snap.state.choices:
            lines.append(f"  answer with one of [{snap.state.choices}]"
                         + (f", default {snap.state.default!r}" if snap.state.default else ""))
    if snap.state.menu is not None and k in ("menu", "text"):
        m = snap.state.menu
        lines.append(f"{'MENU' if k == 'menu' else 'TEXT'}: {m.title!r} page {m.page}/{m.pages}")
        for it in m.items:
            if it.header or not it.letter:
                lines.append(f"   [{it.text}]" if k == "menu" else f"   {it.text}")
            else:
                sel = "+" if it.selected else "-"
                lines.append(f"   {it.letter} {sel} {it.text}")
        if k == "menu":
            lines.append("  (select letters, then <CR>; '>' next page; <Esc> cancel)")
        return "\n".join(lines)
    if k in ("dgl", "unknown", "gameover"):
        lines.append("\n".join(f"{y:>2}|{r.rstrip()}" for y, r in enumerate(snap.screen.chars)))
        return "\n".join(lines)
    h = snap.hero or hero
    if mode == "full" or (mode == "crop" and h is None):
        lines.append(map_block(snap))
    elif mode == "crop" and h is not None:
        hx, hy = h
        x0, x1 = max(0, hx - 2 * radius), min(80, hx + 2 * radius + 1)
        y0, y1 = max(MAP_TOP, hy - radius), min(MAP_BOTTOM, hy + radius)
        lines.append(map_block(snap, x0, x1, y0, y1))
    if h is not None:
        lines.append(f"you @ ({h[0]},{h[1]})  [coords are (x=col, y=row)]")
    if mons is None or (not mons and snap.state.kind != "command"):
        mons = monsters_in_view(snap, None, hero=h)
    ml = monsters_line(snap, radius=None if mode == "full" else 2 * radius, mons=mons)
    if ml:
        lines.append(ml)
    lim = None if mode == "full" else 2 * radius
    objs = [o for o in snap.objects if lim is None or (o["dist"] is not None and o["dist"] <= lim)]
    if objs:
        lines.append("objects: " + "; ".join(
            f"{o['ch']} {o['kind']}{' (pile)' if o['pile'] else ''} ({o['x']},{o['y']})" for o in objs[:14])
            + (f"; ... {len(objs) - 14} more" if len(objs) > 14 else ""))
    feats = [f for f in snap.features if lim is None or (f["dist"] is not None and f["dist"] <= lim)
             or f["name"] in ("up stairs", "down stairs")]
    if feats:
        lines.append("features: " + "; ".join(f"{f['name']} ({f['x']},{f['y']})" for f in feats[:16])
                     + (f"; ... {len(feats) - 16} more" if len(feats) > 16 else ""))
    return "\n".join(lines)


def render_screen(snap: Snap) -> str:
    """The raw 80x24 terminal, verbatim (for prompts/menus/odd states)."""
    return header(snap) + "\n" + "\n".join(f"{y:>2}|{r.rstrip()}" for y, r in enumerate(snap.screen.chars))
