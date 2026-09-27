"""Endgame helpers: the invocation on the vibrating square.

The rules (3.6.7 apply.c use_bell / use_candelabrum, spell.c deadbook):
- all on the vibrating square (not on stairs);
- the Candelabrum of Invocation holds 7 candles (attach them by applying the
  CANDLES) and is lit there ("... glows with a strange light!"); lit off the
  square the candles are "rapidly consumed";
- the Bell of Opening, rung there, "issues an unsettling shrill sound..."; it
  spends a charge each time ("But it makes no sound." = empty: charge it);
- the Book of the Dead, read within 5 turns of the ringing, with the lit
  7-candle candelabrum in your pack: "You are standing at the top of a
  stairwell leading down!". A cursed Bell/Book/Candelabrum makes it fail
  (a cursed Bell raises undead, a cursed Book scrambles its runes).
"""

from __future__ import annotations

import re

from . import ctx
from .nav import NavError

BELL = re.compile(r"\bBell of Opening\b|\bsilver bell\b", re.I)
CANDELABRUM = re.compile(r"\bCandelabrum of Invocation\b|\bcandelabrum\b", re.I)
BOOK = re.compile(r"\bBook of the Dead\b|\bpapyrus spellbook\b", re.I)
CANDLE = re.compile(r"\b(?:wax |tallow )?candles?\b", re.I)
_HOLDS = re.compile(r"\((no|\d+) candles?(?: attached|, lit)\)")

_ATTACH_Q = re.compile(r"^Attach .* to .*candelabrum\?", re.I)
_OK = [r"^You attach \d+ (?:more )?candles? to ", r"candles?'? (?:burn brightly|are lit|dimly)",
       r"glows? with a strange light!", r"radiates? a strange warmth!", r"^You ring ",
       r"issues? an unsettling shrill sound", r"^You begin to recite the runes\.",
       r"^You turn the pages of the Book of the Dead", r"^The floor shakes violently under you!",
       r"^The walls around you begin to bend and crumble!", r"stairwell leading down!",
       r"^The new candles? magically ignites?!", r"^(?:They go|It goes) out\."]


def _qty(text: str) -> int:
    m = re.match(r"^(\d+) ", text)
    return int(m.group(1)) if m else 1


def _held(text: str) -> tuple[int, bool]:
    """(candles attached, lit) from the candelabrum's inventory text."""
    m = _HOLDS.search(text)
    if not m:
        return 0, False
    n = 0 if m.group(1) == "no" else int(m.group(1))
    return n, ", lit)" in m.group(0)


def _apply(letter: str, what: str):
    s = ctx.do("a", quiet=True)
    if s.state.kind != "object":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        raise RuntimeError(f"invoke(): 'a' gave {s.state.kind}: {s.state.prompt!r} (applying {what})")
    return ctx.do(letter, ok=_OK)


def on_vibrating_square(s=None) -> bool:
    s = s or ctx.last()
    mem = getattr(ctx.game, "terrain_seen", {}).get(ctx.game.level_key(s.status), {})
    return s.hero is not None and (mem.get(s.hero) == "~" or getattr(s, "under", None) == "~")


def invoke(force: bool = False) -> dict:
    """Perform the invocation. Checks first (and changes nothing if a check
    fails): you stand on the vibrating square; the Bell, the Candelabrum and
    the Book are in your pack and not cursed (unknown BUC is refused unless
    force=True); 7 candles are attached or carried. Then attaches candles,
    lights the candelabrum, rings the Bell and reads the Book back to back,
    requiring each step's confirming message (monster/HP pauses still come).
    Returns {"ok", "step", "messages"}: ok=True with the new '>' under you."""
    from .items import inventory
    s = ctx.require_command("invoke()")
    if not on_vibrating_square(s):
        mem = getattr(ctx.game, "terrain_seen", {}).get(ctx.game.level_key(s.status), {})
        where = [c for c, v in mem.items() if v == "~"]
        raise NavError("invoke(): you are not on the vibrating square" + (
            f" — it is at {where[0]}: travel there first" if where else
            " (walk Gehennom's bottom level until 'You feel a strange vibration under your feet')"))
    inv = inventory()
    cand = next((it for it in inv if CANDELABRUM.search(it["text"])), None)
    bell = next((it for it in inv if BELL.search(it["text"])), None)
    book = next((it for it in inv if BOOK.search(it["text"])), None)
    missing = [n for n, it in (("the Bell of Opening", bell), ("the Candelabrum", cand), ("the Book of the Dead",
                                                                                          book)) if it is None]
    if missing:
        raise RuntimeError(f"invoke(): not in your pack: {', '.join(missing)}")
    cursed = [it["text"] for it in (bell, cand, book) if it.get("buc") == "cursed"]
    if cursed:
        raise RuntimeError(f"invoke(): CURSED — {'; '.join(cursed)}: uncurse first (holy water, remove curse, "
                           "or pray in trouble); a cursed item makes the invocation fail")
    unknown = [it["text"] for it in (bell, cand, book) if not it.get("buc")]
    if unknown and not force:
        raise RuntimeError(f"invoke(): BUC unknown — {'; '.join(unknown)}: a cursed one makes it fail (test on an "
                           "altar, or dip in holy water); force=True to go ahead anyway")
    held, lit = _held(cand["text"])
    candles = [it for it in inv if CANDLE.search(it["text"]) and not CANDELABRUM.search(it["text"])]
    if held + sum(_qty(it["text"]) for it in candles) < 7:
        raise RuntimeError(f"invoke(): the candelabrum holds {held} and you carry "
                           f"{sum(_qty(it['text']) for it in candles)} candles: 7 are needed")
    msgs: list = []

    def fail(step, why):
        return {"ok": False, "step": step, "why": why, "messages": msgs}

    # 1. candles
    for it in candles:
        if held >= 7:
            break
        s = _apply(it["letter"], "the candles")
        msgs.extend(s.messages)
        if s.state.kind != "yn" or not _ATTACH_Q.search(s.state.prompt or ""):
            if s.state.kind != "command":
                ctx.do("<Esc>", quiet=True)
            return fail("attach", f"expected 'Attach ... to the candelabrum?', got {s.state.kind}: "
                                  f"{s.state.prompt!r} {s.messages}")
        s = ctx.do("y", ok=_OK)
        msgs.extend(s.messages)
        m = re.search(r"You attach (\d+)", " ".join(s.messages))
        if not m:
            return fail("attach", f"no 'You attach' message: {s.messages}")
        held += int(m.group(1))
    if held < 7:
        return fail("attach", f"only {held} candles attached")
    # 2. light it (applying a lit candelabrum would snuff it)
    if not lit:
        s = _apply(cand["letter"], "the candelabrum")
        msgs.extend(s.messages)
        text = " ".join(s.messages)
        if "strange light" not in text and "strange warmth" not in text:
            return fail("light", "no 'glows with a strange light' — " + (
                "not the vibrating square? the candles are burning fast now" if "rapidly consumed" in text
                else "cursed? it flickered out" if "flicker" in text else f"messages: {s.messages}"))
    # 3. ring the Bell, 4. read the Book at once (the ringing counts for 5 turns)
    s = _apply(bell["letter"], "the Bell")
    msgs.extend(s.messages)
    text = " ".join(s.messages)
    if "unsettling shrill sound" not in text:
        return fail("ring", "the Bell is out of charges (read charging on it)" if "makes no sound" in text
                    else f"no 'unsettling shrill sound': {s.messages}")
    s = ctx.do("r", quiet=True)
    if s.state.kind != "object":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        return fail("read", f"'r' gave {s.state.kind}: {s.state.prompt!r} — read the Book NOW (the Bell's ringing "
                            "counts for 5 turns)")
    s = ctx.do(book["letter"], ok=_OK, expect=("level",))
    msgs.extend(s.messages)
    text = " ".join(msgs)
    if "stairwell leading down" in text:
        return {"ok": True, "step": "done", "messages": msgs,
                "next": "the stairs down are under you; around them a ring of fire traps and a moat — "
                        "the way back up needs levitation (PLAYBOOK F)"}
    why = ("not primed (the Bell rung too long ago, or the candelabrum not lit with 7): it raised the dead"
           if "amiss" in text else "a cursed item" if "invocation fails" in text
           else "the Book is cursed" if "scrambled" in text else f"messages: {s.messages}")
    return fail("read", why)
