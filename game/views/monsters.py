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

    # All grids (chars, descriptions, glyphs) use the same dungeon-relative
    # 21x79 indexing. desc_at(r, c) is just descriptions[r][c].
    def desc_at(r: int, c: int) -> str:
        if 0 <= r < len(descriptions) and 0 <= c < len(descriptions[r]):
            return descriptions[r][c]
        return ""

    sightings: list[tuple[int, int, int, str, str, bool]] = []  # (dist, r, c, glyph, desc, tame)
    # Use NLE's glyph predicates so we don't false-positive on statues
    # (they render as their monster letter, e.g. `H` for a giant statue).
    glyphs = obs.get("glyphs") or []
    use_glyphs = False
    _nh = None
    if glyphs:
        try:
            from nle import nethack as _nh  # type: ignore
            use_glyphs = True
        except ImportError:
            _nh = None

    if use_glyphs:
        for r in range(len(glyphs)):
            row = glyphs[r]
            for c in range(len(row)):
                g = int(row[c])
                if not _nh.glyph_is_normal_monster(g):
                    continue
                tame = bool(_nh.glyph_is_pet(g))
                # Player is in the normal_monster glyph range too. Filter via
                # cursor (more robust than ch=='@' check, which would miss a
                # polymorphed player rendered as a different char).
                if (r, c) == (pr, pc):
                    continue
                ch_int = chars[r][c] if r < len(chars) and c < len(chars[r]) else 0
                ch = chr(ch_int) if ch_int else "?"
                desc = desc_at(r, c)
                d = max(abs(r - pr), abs(c - pc))
                sightings.append((d, r, c, ch, desc or f"unknown {ch!r}", tame))
    else:
        # Fallback: chars+descriptions heuristic. Filters statues by description
        # ("statue of ...") since glyphs aren't available.
        for r in range(len(chars)):
            row = chars[r]
            for c, ch_int in enumerate(row):
                ch = chr(ch_int) if ch_int else " "
                if not ch.isalpha() or ch == PLAYER:
                    continue
                desc = desc_at(r, c)
                if desc.startswith("statue"):
                    continue
                tame = desc.startswith("tame ")
                d = max(abs(r - pr), abs(c - pc))
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
