"""List visible monsters with positions, names, and tame/hostile flags."""

from __future__ import annotations

from typing import Any

# Letters that are monsters in NetHack. Excludes player and a few non-monster
# alphabetic glyphs (none in standard nethack: . | - + < > etc are all symbols).
# Using isalpha() catches both case ranges.
PLAYER = "@"


def _bearing(pr: int, pc: int, r: int, c: int) -> str:
    dr, dc = r - pr, c - pc
    parts = []
    if dr < 0: parts.append(f"{-dr}N")
    elif dr > 0: parts.append(f"{dr}S")
    if dc < 0: parts.append(f"{-dc}W")
    elif dc > 0: parts.append(f"{dc}E")
    return "+".join(parts) if parts else "here"


def monsters(obs: dict[str, Any]) -> str:
    """Enumerate monster glyphs in view, sorted by distance from the player.

    Tame monsters (your pet, charmed creatures) are tagged. Hostile and
    peaceful are reported separately so you can see the threat at a glance.
    Naming uses NLE's per-cell screen_descriptions ("kobold", "tame little
    dog called Hachi", etc.) — it's the same text NetHack would show on `;`
    glance.
    """
    chars = obs.get("chars") or []
    descriptions = obs.get("descriptions") or []
    cursor = obs.get("cursor") or [0, 0]
    pr, pc = int(cursor[0]), int(cursor[1])

    if not chars:
        return "(monsters unavailable: obs has no `chars`; call from inside game.exec)"

    # screen_descriptions is 21x79 covering rows 1..21 of chars; offset by 1.
    def desc_at(r: int, c: int) -> str:
        dr = r - 1
        if 0 <= dr < len(descriptions) and 0 <= c < len(descriptions[dr]):
            return descriptions[dr][c]
        return ""

    sightings: list[tuple[int, int, int, str, str, bool]] = []  # (dist, r, c, glyph, desc, tame)
    # Only the dungeon area (rows 1..21). Row 0 is the message line, rows 22-23
    # are status — those contain alpha characters that aren't monsters.
    DUNGEON_ROW_START, DUNGEON_ROW_END = 1, 22  # half-open
    for r in range(DUNGEON_ROW_START, min(DUNGEON_ROW_END, len(chars))):
        row = chars[r]
        for c, ch_int in enumerate(row):
            ch = chr(ch_int) if ch_int else " "
            if not ch.isalpha() or ch == PLAYER:
                continue
            desc = desc_at(r, c)
            tame = desc.startswith("tame ")
            d = max(abs(r - pr), abs(c - pc))  # Chebyshev = NetHack moves
            sightings.append((d, r, c, ch, desc or f"unknown {ch!r}", tame))

    if not sightings:
        return "No monsters visible."

    sightings.sort()
    tame_list = [s for s in sightings if s[5]]
    foes = [s for s in sightings if not s[5]]

    out: list[str] = []
    if foes:
        out.append(f"Hostile/peaceful ({len(foes)}):")
        for d, r, c, ch, desc, _ in foes:
            out.append(f"  d={d:>2}  ({r:>2},{c:>2})  '{ch}'  {_bearing(pr, pc, r, c):<8}  {desc}")
    if tame_list:
        if foes:
            out.append("")
        out.append(f"Tame ({len(tame_list)}):")
        for d, r, c, ch, desc, _ in tame_list:
            out.append(f"  d={d:>2}  ({r:>2},{c:>2})  '{ch}'  {_bearing(pr, pc, r, c):<8}  {desc}")
    return "\n".join(out)
