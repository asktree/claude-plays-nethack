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
    statues = [m for m in mons if m.get("statue")]
    mons = [m for m in mons if not m.get("statue")]
    unseen = [m for m in mons if m.get("unseen") and m["ch"] == "I" and m["dist"] != 1]
    if len(unseen) > 2:
        # remembered 'I' markers far off: one line (each carries the same note)
        mons = [m for m in mons if m not in unseen]
        unseen.sort(key=lambda m: m["dist"] if m["dist"] is not None else 99)
        parts.append(f"  I x{len(unseen)} remembered unseen monsters (old markers; maybe gone) at "
                     + ", ".join(f"({m['x']},{m['y']})" for m in unseen[:10])
                     + (f" +{len(unseen) - 10} more" if len(unseen) > 10 else ""))
    for m in mons:
        note_txt = m.get("note") or ""
        if m.get("desc"):
            who = m["desc"]
        else:
            tag = " PET?" if m["pet"] else ""
            who = f"unidentified {m['color']} {m['ch']}{tag} (not looked at yet)"
            if not note_txt and not m["pet"]:
                try:
                    from .danger import noted_lookalikes
                    risky = noted_lookalikes(m["ch"], m["color"])
                except Exception:  # noqa: BLE001
                    risky = []
                if risky:
                    note_txt = (f"could be {', '.join(risky[:4])}{' ...' if len(risky) > 4 else ''} — "
                                f"farlook({m['x']}, {m['y']}) before engaging")
        adj = "  <-- ADJACENT" if m["dist"] == 1 else ""
        if m.get("new"):
            adj += "  (NEW)"
        note = f"\n      !! {note_txt}" if note_txt else ""
        parts.append(f"  {m['ch']} {who} at ({m['x']},{m['y']}) d={m['dist']}{adj}{note}")
    if statues:
        # statues look like monsters but never move: one line for all of them
        parts.append("  statues: " + ", ".join(f"{m['ch']} ({m['x']},{m['y']})" for m in statues[:12])
                     + (f" +{len(statues) - 12} more" if len(statues) > 12 else ""))
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
    if getattr(snap, "wield_note", "") and snap.state.kind == "command":
        lines.append(f"!! {snap.wield_note}")
    if getattr(snap, "theft_note", ""):
        lines.append(f"!! {snap.theft_note}")
    gold_warn = getattr(snap, "gold_note", "")
    if gold_warn and snap.state.kind == "command":
        lines.append(f"!! {gold_warn}")
    burn_warn = getattr(snap, "burn_note", "")
    if burn_warn and snap.state.kind == "command":
        lines.append(f"!! {burn_warn}")
    k = snap.state.kind
    if k != "command":
        if snap.state.prompt:
            lines.append(f"PROMPT ({k}): {snap.state.prompt}")
        if k == "getpos":
            cx, cy = snap.screen.cursor
            lines.append(f"  cursor at ({cx},{cy}) — cursor_to(x, y) moves it; then '.' or ',' picks that square")
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
        lines.append(f"you @ ({h[0]},{h[1]})  [coords are (x=col, y=row)]"
                     + (f"  — in {snap.shop} (no throwing/firing/digging down here)" if getattr(snap, "shop", "")
                        else ""))
    if mons is None or (not mons and snap.state.kind != "command"):
        mons = monsters_in_view(snap, None, hero=h)
    ml = monsters_line(snap, radius=None if mode == "full" else 2 * radius, mons=mons)
    if ml:
        lines.append(ml)
    if getattr(snap, "gone", None):
        lines.append("out of view: " + "; ".join(f"{g['desc']} last at ({g['x']},{g['y']}) {g['ago']} turn(s) ago"
                                                  for g in snap.gone))
    mim = getattr(snap, "mimic_mem", None) or {}
    if mim and snap.state.kind == "command":
        shown = {(m["x"], m["y"]) for m in (mons or []) if "mimic" in (m.get("desc") or "")}
        hidden = sorted((c, n) for c, n in mim.items() if c not in shown)
        if hidden:
            lines.append("mimics remembered here (hiding as the object/boulder/stairs shown there — don't walk "
                         "or push into them): " + "; ".join(f"{n} ({x},{y})" for (x, y), n in hidden))
    lim = None if mode == "full" else 2 * radius
    allo = snap.objects
    objs = [o for o in allo if lim is None or o["dist"] is None or o["dist"] <= lim]   # (None: no hero seen)
    far = len(allo) - len(objs)
    if objs or far:
        lines.append("objects: " + "; ".join(
            f"{o['ch']} {o['kind']}{' (pile)' if o['pile'] else ''} ({o['x']},{o['y']})" for o in objs[:14])
            + (f"; ... {len(objs) - 14} more" if len(objs) > 14 else "")
            + (f"{'; ' if objs else ''}+{far} farther away (`bin/nh obs` lists all; obs.objects in exec)"
               if far else ""))
    allf = snap.features
    liquid = [f for f in allf if f["name"] in ("water", "lava", "poison gas cloud")]
    feats = [f for f in allf if f["name"] not in ("water", "lava", "poison gas cloud")
             and (lim is None or (f["dist"] is not None and f["dist"] <= lim)
                  or f["name"].startswith(("up stairs", "down stairs", "magic portal", "vibrating"))
                  or "altar" in f["name"])]
    # stairs, altars, portals first (a water level would otherwise bury them)
    key = {"up stairs": 0, "down stairs": 0, "magic portal": 0, "vibrating square": 0}
    feats.sort(key=lambda f: (key.get(f["name"].split(" (")[0], 1 if "altar" in f["name"] else 2),
                              f["dist"] if f["dist"] is not None else 99))
    bits = [f"{f['name']} ({f['x']},{f['y']})" for f in feats[:16]]
    if len(feats) > 16:
        bits.append(f"... {len(feats) - 16} more")
    for nm in ("water", "lava", "poison gas cloud"):
        sq = [f for f in liquid if f["name"] == nm]
        if sq:
            near = min(sq, key=lambda f: f["dist"] if f["dist"] is not None else 99)
            bits.append(f"{nm} x{len(sq)} (nearest ({near['x']},{near['y']}))")
    if bits:
        lines.append("features: " + "; ".join(bits))
    niches = getattr(snap, "niche_mem", None) or {}
    if niches:
        lines.append("trapped closet(s), avoided: " + "; ".join(
            f"({x},{y}) {'one-time teleporter (gold vault / level teleporter)' if k == 'teleport' else 'one-time trap door'}"
            for (x, y), k in sorted(niches.items())))
    rooms = getattr(snap, "room_mem", None) or {}
    if rooms:
        lines.append("special rooms (travel/explore keep out; forget_room() to go in): " + "; ".join(
            f"{r.get('kind')} entered at ({x},{y})" for (x, y), r in sorted(rooms.items())))
    plane = snap.status.ldesc if snap.status.ok else ""
    if getattr(snap, "medusa_risk", False):
        lines.append("!! " + ("MEDUSA IS ON THIS LEVEL" if "medusa" in getattr(snap, "flags", ()) else
                              "PROBABLY MEDUSA'S LEVEL (Dlvl 21+, water all around)")
                     + ": her gaze STONES you when you see each other (within ~8 squares). Before going on: be "
                       "Blind (apply a blindfold/towel; telepathy shows monsters) or WEAR reflection (shield of "
                       "reflection / silver dragon scale mail). She starts asleep: noise (kicking doors, fights) "
                       "wakes her. travel()/explore()/kick_door() refuse here until then (medusa_ok=True overrides; "
                       "going back up is always allowed)")
    flags = getattr(snap, "flags", None) or set()
    if not getattr(snap, "medusa_risk", False) and flags & {"medusa", "medusa?"} and "medusa_dead" not in flags:
        lines.append(("MEDUSA'S LEVEL" if "medusa" in flags else "PROBABLY MEDUSA'S LEVEL")
                     + " (you are Blind or wear reflection): reflection turns her gaze back on her — it kills her "
                       "only if she can see you (NOT while you are invisible)")
    if getattr(snap, "rogue", False):
        lines.append("ROGUE LEVEL (no colours): '%' = stairs (up or down: see features), '+' in a wall = doorway "
                     "(NO diagonal moves into or out of it), ':' = food or a lizard/newt, ']' armor, ',' amulet, '*' gold or gem, "
                     "'`' boulder")
    if plane == "Air":
        lines.append("Plane of Air: blank = open air, '#' = cloud (both passable, clouds block sight; without "
                     "levitation/flying most steps fail); no map is kept: the portal stays in features once seen")
    elif plane == "Water":
        lines.append("Plane of Water: blank = your air bubble (bubbles drift every turn), '}' = water (drowning "
                     "without magical breathing; things get wet): step() inside the bubble; no map is kept: the "
                     "portal stays in features once seen")
    return "\n".join(lines)


def render_screen(snap: Snap) -> str:
    """The raw 80x24 terminal, verbatim (for prompts/menus/odd states)."""
    return header(snap) + "\n" + "\n".join(f"{y:>2}|{r.rstrip()}" for y, r in enumerate(snap.screen.chars))
