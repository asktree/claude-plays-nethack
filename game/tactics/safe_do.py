"""safe_do(action): step + abort on watched conditions.

Wraps a single `do()` call with checks that raise `Interrupted` if anything
unexpected happens — designed for use in exec loops that would otherwise
chain blindly past new threats.

Usage inside game.exec():
    from tactics import safe_do
    for d in ["east"] * 5:
        safe_do(d)
    # If a kobold appears mid-loop, this exec returns early with an error
    # naming the threat. Gamer reads, picks next action.

Default interrupts (override with `interrupts=[...]` kwarg):
  - new monster in view (compared to a baseline taken before the step)
  - HP dropped > 25% in this step
  - game terminated/truncated

Each interrupt is a callable `(pre_obs, post_obs) -> str | None`. Return a
non-empty string to fire (the string is the abort reason); return None or
empty to pass.
"""

from __future__ import annotations

import sys
from typing import Any, Callable

Interrupt = Callable[[dict, dict], str | None]


class Interrupted(Exception):
    """Raised by safe_do when a watched condition fires."""

    def __init__(self, reason: str, snap: dict[str, Any]) -> None:
        self.reason = reason
        self.snap = snap
        super().__init__(reason)


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
    out: set[tuple[str, tuple[int, int]]] = set()
    if glyphs:
        try:
            from nle import nethack as _nh
            for gr in range(len(glyphs)):
                row = glyphs[gr]
                for gc in range(len(row)):
                    g = int(row[gc])
                    if not _nh.glyph_is_normal_monster(g):
                        continue
                    if _nh.glyph_is_pet(g):
                        continue
                    # glyphs[gr] aligns to chars[gr+1] (chars row 0 is the
                    # message line; glyphs starts at the first dungeon row).
                    cr = gr + 1
                    ch_int = chars[cr][gc] if cr < len(chars) and gc < len(chars[cr]) else 0
                    ch = chr(ch_int) if ch_int else "?"
                    out.add((ch, (cr, gc)))
            return out
        except ImportError:
            pass
    # Fallback: chars+descriptions heuristic (trips on statues but better
    # than nothing if glyphs aren't in scope).
    descs = obs.get("descriptions") or []
    for r in range(1, min(22, len(chars))):
        row = chars[r]
        for c, ch_int in enumerate(row):
            ch = chr(ch_int) if ch_int else " "
            if not ch.isalpha() or ch == "@":
                continue
            dr = r - 1
            desc = descs[dr][c] if 0 <= dr < len(descs) and 0 <= c < len(descs[dr]) else ""
            if desc.startswith("tame ") or desc.startswith("statue"):
                continue
            out.add((ch, (r, c)))
    return out


def _new_monster(pre: dict, post: dict) -> str | None:
    new_threats = _hostile_set(post) - _hostile_set(pre)
    if not new_threats:
        return None
    parts = [f"'{ch}' at ({r},{c})" for ch, (r, c) in sorted(new_threats)[:3]]
    return "new monster in view: " + ", ".join(parts)


def _hostile_in_view(pre: dict, post: dict) -> str | None:
    """Fire on ANY hostile visible after the step, regardless of distance or
    whether it was already in baseline.

    Rationale: safe_do is for scripted sequences. If any hostile is visible,
    the gamer should stop scripting and decide consciously. Most of the time
    there are no enemies visible, so safe_do is a no-op; when there are, you
    need to handle them. The previous distance-1 rule missed cases like the
    bat-vs-Valkyrie post-mortem where a known hostile kept attacking through
    a long search loop. This also matches NetHack's Travel behavior, which
    auto-stops on any hostile in view.
    """
    cursor = post.get("cursor") or [0, 0]
    pr, pc = int(cursor[0]), int(cursor[1])
    threats = _hostile_set(post)
    if not threats:
        return None
    sorted_threats = sorted(threats, key=lambda t: max(abs(t[1][0] - pr), abs(t[1][1] - pc)))
    parts = [f"'{ch}' at ({r},{c})" for ch, (r, c) in sorted_threats[:3]]
    suffix = "" if len(threats) <= 3 else f" (+{len(threats)-3} more)"
    return f"hostile in view — bare do() to engage/flee: {', '.join(parts)}{suffix}"


def _hp_drop(pre: dict, post: dict, frac: float = 0.25) -> str | None:
    pre_hp = pre.get("blstats", {}).get("hitpoints", 0)
    post_hp = post.get("blstats", {}).get("hitpoints", 0)
    if pre_hp <= 0:
        return None
    if (pre_hp - post_hp) / pre_hp > frac:
        return f"HP dropped {pre_hp}→{post_hp}"
    return None


def _terminated(_pre: dict, post: dict) -> str | None:
    if post.get("terminated"):
        return "game terminated"
    if post.get("truncated"):
        return "game truncated (step limit)"
    return None


# Hunger thresholds in NetHack's hunger_state int:
#   0=Satiated, 1=Normal, 2=Hungry, 3=Weak, 4=Fainting, 5=Fainted, 6=Starved
# Weak means -1 to hit/damage and you might collapse soon. Fire here so the
# gamer can't burn turns scripting through to starvation (the actual cause of
# the recent Valkyrie post-mortem death — food crisis from over-searching).
def _hunger_critical(pre: dict, post: dict) -> str | None:
    pre_h = pre.get("blstats", {}).get("hunger_state", 1)
    post_h = post.get("blstats", {}).get("hunger_state", 1)
    if post_h >= 3 and post_h > pre_h:
        labels = {3: "Weak", 4: "Fainting", 5: "Fainted", 6: "Starved"}
        return f"hunger crossed into {labels.get(post_h, str(post_h))} — eat before continuing"
    return None


DEFAULT_INTERRUPTS: list[Interrupt] = [
    _hostile_in_view,
    _hp_drop,
    _hunger_critical,
    _terminated,
]
# _new_monster removed — _hostile_in_view subsumes it (any hostile visible is
# a stop, not just newly-appeared ones).


def safe_do(
    action: int | str,
    *,
    interrupts: list[Interrupt] | None = None,
    do=None,
    observe=None,
) -> dict[str, Any]:
    """Take one action; raise Interrupted if any interrupt fires after the step."""
    if do is None or observe is None:
        frame = sys._getframe(1).f_globals
        do = do or frame.get("do")
        observe = observe or frame.get("observe")
        if do is None or observe is None:
            raise RuntimeError("safe_do must be called inside game.exec(); needs `do` and `observe` in scope")

    checks = interrupts if interrupts is not None else DEFAULT_INTERRUPTS

    pre = observe()
    do(action)
    post = observe()

    for check in checks:
        reason = check(pre, post)
        if reason:
            raise Interrupted(reason, post)
    return post
