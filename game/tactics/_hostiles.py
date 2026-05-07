"""Hostile-detection helper used by tactics like `auto_explore` to bail when
any wild/peaceful monster is in line of sight.

Complementary to the message-based pauses in `exec`: NetHack does not always
emit a message when a monster comes into LoS (just appearing on screen as the
player walks past produces no `message`), so a glyph-level scan is the only
reliable way to halt before stepping further into trouble.
"""

from __future__ import annotations

from typing import Any


def _hostile_set(obs: dict[str, Any]) -> set[tuple[str, tuple[int, int]]]:
    """Set of (glyph_char, (chars_row, col)) for actual hostile/peaceful monsters.

    Uses NLE's `glyph_is_normal_monster()` which returns False for statues,
    pets, objects, terrain, invisible-markers, swallow effects, etc. — only
    True for real wild/peaceful monsters that can hurt you. Char-based
    detection (alpha glyphs in dungeon area) trips on statues, which render
    as their monster letter (e.g. `H` for a giant statue).
    """
    glyphs = obs.get("glyphs") or []
    chars = obs.get("chars") or []
    cursor = obs.get("cursor") or [0, 0]
    player_pos = (int(cursor[0]), int(cursor[1]))
    out: set[tuple[str, tuple[int, int]]] = set()
    if glyphs:
        try:
            from nle import nethack as _nh
            for r in range(len(glyphs)):
                row = glyphs[r]
                for c in range(len(row)):
                    g = int(row[c])
                    if not _nh.glyph_is_normal_monster(g):
                        continue
                    if _nh.glyph_is_pet(g):
                        continue
                    # NetHack renders the player as their race's monster glyph,
                    # which IS in the normal_monster range. Filter via cursor.
                    if (r, c) == player_pos:
                        continue
                    ch_int = chars[r][c] if r < len(chars) and c < len(chars[r]) else 0
                    ch = chr(ch_int) if ch_int else "?"
                    out.add((ch, (r, c)))
            return out
        except ImportError:
            pass
    # Fallback: chars+descriptions heuristic (trips on statues but better
    # than nothing if glyphs aren't in scope).
    descs = obs.get("descriptions") or []
    for r in range(len(chars)):
        row = chars[r]
        for c, ch_int in enumerate(row):
            ch = chr(ch_int) if ch_int else " "
            if not ch.isalpha() or ch == "@":
                continue
            desc = descs[r][c] if 0 <= r < len(descs) and 0 <= c < len(descs[r]) else ""
            if desc.startswith("tame ") or desc.startswith("statue"):
                continue
            out.add((ch, (r, c)))
    return out
