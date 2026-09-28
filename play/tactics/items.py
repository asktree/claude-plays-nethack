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


def _wielded(text: str) -> bool:
    from nh.game import WIELDED_RE
    return bool(WIELDED_RE.search(text))


def _welded(inv) -> dict | None:
    """Your wielded weapon when it is known CURSED: welded to your hand (wield.c will_weld()), so NetHack
    refuses to wield anything else — #rub (a lamp) and applying a pick-axe included (apply.c wield_tool:
    "Since your weapon is welded to your hand, you cannot ...")."""
    from nh.game import is_weapon_text
    return next((i for i in inv if _wielded(i["text"]) and re.search(r"\bcursed\b", i["text"])
                 and (str(i.get("class") or "").startswith("Weapons") or is_weapon_text(i["text"]))), None)


def inventory():
    """Return the hero's inventory as a list of {letter, text, class, buc}."""
    ctx.require_command("inventory()")
    with ctx.no_monster_pauses():
        s = ctx.do("i", quiet=True)
        items = _parse_menu_pages(s)[0] if s.state.kind == "menu" else None
    if items is not None:
        ctx.game.inv_items = items          # (helpers that only need a name look here: zap() notes)
        w = next((it for it in items if _wielded(it["text"])), None)
        if hasattr(ctx.game, "set_wielded"):
            st = ctx.last().status
            ctx.game.set_wielded(w["text"] if w else "", w["class"] if w else "", w["letter"] if w else None,
                                 bool(w) and w["class"].startswith("Tools"), st.turn if st.ok else None)
        else:
            ctx.game.wielded = w["text"] if w else ""
            ctx.game.wielded_class = w["class"] if w else ""
        ctx.game.gloves = next((it["text"] for it in items if "(being worn)" in it["text"]
                                and re.search(r"\b(?:gloves|gauntlets)\b", it["text"])), "")
        ctx.game.reflecting = any("(being worn)" in it["text"] and _REFLECT.search(it["text"]) for it in items)
        ctx.game.magic_res = any(("(being worn)" in it["text"] and _MR_WORN.search(it["text"]))
                                 or (re.search(r"\bMagicbane\b", it["text"]) and _wielded(it["text"]))
                                 for it in items)
        empty = getattr(ctx.game, "empty_wands", None)
        if empty:           # a letter that isn't a wand any more (dropped, recharged: "(x:N)" with N > 0)
            wands = {it["letter"]: it["text"] for it in items if re.search(r"\bwand\b", it["text"])}
            empty.intersection_update({k for k, t in wands.items() if not re.search(r"\(\d+:[1-9]\d*\)", t)})
        ctx.game.helmet = next((it["text"] for it in items if "(being worn)" in it["text"]
                                and re.search(r"\b(?:helm|helmet|hat|cap|cornuthaum|fedora|kabuto)\b", it["text"])), "")
        ctx.game.cursed_worn = [it["text"] for it in items if re.search(r"\bcursed\b", it["text"])
                                and not re.search(r"\buncursed\b", it["text"])
                                and re.search(r"\((?:being worn|on (?:left|right) hand|weapon in \w+|"
                                              r"wielded)", it["text"])]
        # pray.c worst_cursed_item() also counts a cursed luckstone, and a cursed loadstone once Strained
        ctx.game.cursed_stones = [it["text"] for it in items if re.search(r"\bcursed (?:luck|load)stone", it["text"])]
        ctx.game.bags = [it["letter"] for it in items if re.search(r"\b(?:sack|bag)\b", it["text"])
                         and "tricks" not in it["text"]]
        # trap.c dofiretrap() -> destroy_item(): Gehennom's fire traps burn scrolls/books and boil potions in
        # the open pack (a bag protects them): the obs warns there
        ctx.game.loose_burnables = [it["letter"] for it in items
                                    if it["class"] in ("Scrolls", "Potions", "Spellbooks")
                                    and not _INVOCATION.search(it["text"])]   # (the Book never burns)
        ctx.game.blindfolded = any(re.search(r"\b(?:blindfold|towel)\b.*\(being worn\)", it["text"]) for it in items)
        ctx.game.punished = any("(chained to you)" in it["text"] for it in items)   # objnam.c: ball and chain
        # (our rc: !implicit_uncursed — a known B/U/C always shows): a curse spell can only have hit these
        ctx.game.unknown_buc = [f"{it['letter']} ({it['text'][:40]})" for it in items if it["class"] != "Coins"
                                and not re.search(r"\b(?:un)?cursed\b|\bblessed\b", it["text"])]
        _refresh_burn_note()
        return items
    # "Not carrying anything." or a tiny inventory shown on the message line
    return []


# worn magic resistance (extrinsic): gray dragon scales/scale mail, a cloak of magic resistance; Magicbane wielded
_MR_WORN = re.compile(r"\b(?:gray dragon scale mail|gray dragon scales|cloak of magic resistance)\b")

# worn reflection, by identified name (or the shield of reflection's own look): an unidentified amulet
# of reflection can't be told apart — the player passes medusa_ok=True then
_REFLECT = re.compile(r"\b(?:shield of reflection|polished silver shield|silver dragon scale mail|"
                      r"silver dragon scales|amulet of reflection)\b")


def piety(letter: str | None = None) -> str | None:
    """Your alignment record in words, from a stethoscope applied to
    yourself ('Status of Brunhild (piously lawful): ...'; the first use
    each turn is free): 'piously' = 20+, what the quest leader requires.
    Remembered as game.piety. Returns the word ('' = exactly 3), or None
    without a stethoscope (a wand of probing zapped at yourself or
    enlightenment also tell)."""
    s = ctx.require_command("piety()")
    it = next((i for i in inventory() if (letter and i["letter"] == letter)
               or (not letter and re.search(r"\bstethoscope\b", i["text"]))), None)
    if it is None:
        print("piety(): no stethoscope — a wand of probing zapped at yourself (.) or a potion/wand of "
              "enlightenment tells too ('You are piously aligned')")
        return None
    s = ctx.do("a", quiet=True)
    if s.state.kind != "object":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        raise RuntimeError(f"piety(): 'a' gave {s.state.kind}: {s.state.prompt!r}")
    s = ctx.do(it["letter"], quiet=True)
    if s.state.kind == "direction":
        s = ctx.do(".", quiet=True)
    text = " ".join(s.messages)
    m = re.search(r"Status of .+? \((?:(\w+) )?(lawful|neutral|chaotic)\)", text)
    if not m:
        print(f"piety(): no status line in {s.messages}")
        return None
    word = m.group(1) or ""
    ctx.game.piety = word
    print(f"piety(): {word or 'plainly'} {m.group(2)}" + (" — ready for the quest leader (record 20+)"
                                                          if word == "piously" else
                                                          " — NOT yet 'piously': the quest leader would count a "
                                                          "rejection (kill hostiles; no murders, no hypocrisy)"))
    return word


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


def here(force: bool = False):
    """What's on the floor here (':' look). Takes no game time — except while BLIND: then feeling the floor costs
    a turn (invent.c look_here() returns !!Blind; p2 shift 36 #12 lost a round to four attackers), so blind it
    answers from what the harness saw on this square before (tagged "(remembered)") unless force=True."""
    s0 = ctx.require_command("here()")
    if not force and s0 is not None and s0.status.ok and "Blind" in s0.status.conditions:
        txt = ctx.game._here_text(s0) if hasattr(ctx.game, "_here_text") else ""
        print("here(): Blind — feeling the floor costs a turn; " + ("the harness's memory of this square: "
              f"{txt!r}" if txt else "nothing remembered for this square") + " (here(force=True) feels it)")
        return (txt.replace("\n", " | ") + " (remembered)") if txt else ""
    with ctx.no_monster_pauses():
        s = ctx.do(":", quiet=True)
    return " | ".join(s.messages)


# ---- engrave-identification of wands ------------------------------------------

_ENGRAVE_ID = [
    (r"is a wand of ([\w ]+)!", None),   # auto-identified (digging/fire/lightning)
    # the game identified it on its own (zapnodir() for create monster, light, secret door detection,
    # enlightenment): "You write in the dust with a wand of create monster."
    (r"(?:write|engrave|burn|melt)\w* (?:in|into) the \w+ with an? (?:[\w+-]+ )*?wand of ([\w ]+?)(?: \(|\.)",
     None),
    (r"Gravel flies up|You hear drilling|Chips fly out|Ice chips fly up|Splinters fly up|You feel tremors",
     "digging"),
    (r"Flames fly from the wand|You feel the wand heat up", "fire"),
    (r"Lightning arcs from the wand|You hear crackling|Your hair stands up", "lightning"),
    (r"bugs on the .* stop moving", "sleep or death"),
    (r"bugs on the .* slow down", "slow monster"),
    (r"bugs on the .* speed up", "speed monster"),
    (r"is riddled by bullet holes", "magic missile"),
    (r"A few ice cubes drop from the wand", "cold"),
    (r"unsuccessfully fights your attempt to write", "striking"),
    (r"engraving on the .* vanishes", "cancellation, teleportation or make invisible (to tell: zap it at a "
                                      "boulder or an object pile — teleportation makes it vanish)"),
    (r"The engraving now reads", "polymorph"),
    (r"You feel self-knowledgeable", "enlightenment"),
    (r"A lit field surrounds you", "light"),
    (r"turns to dust", "(the wand was empty and crumbled)"),
    (r"too worn out to engrave", "(cancelled wand)"),
]
_NO_EFFECT = ("no effect: nothing, opening, locking, probing, undead turning, an EMPTY wand"
              " — or secret door detection / create monster with nothing to show")


def engrave_test(letter: str, text: str = "Elbereth", prep: bool = True, force: bool = False) -> dict:
    """Engrave-identify the wand in inventory slot `letter` in one call.

    - Refuses (unless force=True) on a square with a burned/engraved message:
      cancellation/teleport/make-invisible would erase it and polymorph would
      rewrite it (e.g. your burned Elbereth). Don't test in shops either.
    - prep=True: if nothing is engraved here, first writes "x" in the dust
      with your finger (1 turn), so the vanish/polymorph groups show up.
    - Answers "add to the current engraving?" with n, writes `text`.
    - A wish prompt (wand of wishing!) or anything unexpected pauses.
    Returns {"verdict", "messages", "autoidentified"}; also prints the verdict."""
    from .survival import engraving_here
    cur = engraving_here()
    permanent = re.search(r"burned into|melted into|is engraved here", cur or "")
    if permanent and not force:
        raise PermissionError(f"engrave_test: there is a permanent engraving here ({cur!r}); testing could "
                              "erase or change it. Move to a clean square (force=True to override).")
    msgs: list[str] = []
    if prep and not cur:
        s = ctx.do("E", quiet=True)
        if s.state.kind == "object":
            s = ctx.do("-", quiet=True)
            for _ in range(4):
                if s.state.kind == "yn" and "add to the current engraving" in s.state.prompt:
                    s = ctx.do("n", quiet=True)
                elif s.state.kind == "getlin":
                    s = ctx.do("x<CR>", quiet=True)
                    break
                else:
                    break
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
    s = ctx.do("E", quiet=True)
    if s.state.kind != "object":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        raise RuntimeError(f"engrave_test: expected 'What do you want to write with?', got {s.state.kind}")
    s = ctx.do(letter, quiet=True)
    msgs += s.messages
    wrote = False
    for _ in range(8):
        k, p = s.state.kind, s.state.prompt or ""
        if k == "getlin" and "wish" in p.lower():
            ctx.pause("engrave_test: WAND OF WISHING — the wish prompt is open. Follow PLAYBOOK §E for what to "
                      "wish for; answer with cont(reply='...<CR>') after deciding. Don't let it time out.")
            s = ctx.last()
            msgs += s.messages
            continue
        if k == "yn" and "add to the current engraving" in p:
            s = ctx.do("n", quiet=True)
        elif k == "getlin":
            s = ctx.do(f"{text}<CR>", quiet=True)
            wrote = True
        elif k == "command":
            break
        else:
            ctx.pause(f"engrave_test: unexpected {k} prompt {p!r}")
            s = ctx.last()
        msgs += s.messages
    joined = " | ".join(msgs)
    verdict, auto = None, False
    for pat, v in _ENGRAVE_ID:
        m = re.search(pat, joined)
        if m:
            verdict = v if v is not None else m.group(1).strip()
            auto = v is None
            break
    if verdict is None:
        verdict = _NO_EFFECT
    if not auto and " or " in verdict:
        verdict = _narrow_verdict(verdict)
    cur = ctx.last()
    if wrote and cur.hero is not None and cur.status.ok and hasattr(ctx.game, "engr_seen"):
        # the test left `text` engraved here: the harness must know (attacking from an Elbereth
        # square erases it and costs -5 alignment — "You feel like a hypocrite")
        ctx.game.engr_seen.setdefault(ctx.game.level_key(cur.status), {})[cur.hero] = text
        if text.strip().lower() == "elbereth":
            print(f"engrave_test: an Elbereth is under you now at {cur.hero} — step off before attacking "
                  "(melee, zap, throw or kick from it erases it and costs -5 alignment)")
    print(f"engrave_test({letter!r}): {verdict}" + (" (auto-identified)" if auto else ""))
    return {"verdict": verdict, "messages": msgs, "autoidentified": auto}


def _narrow_verdict(verdict: str) -> str:
    """'cancellation, teleportation or make invisible' minus the wand types
    already identified (discoveries(); no game time)."""
    try:
        known = {name.lower() for name, _look in discoveries()}
    except Exception:  # noqa: BLE001
        return verdict
    head, _, tail = verdict.partition(" (")
    names = [n.strip() for n in re.split(r",\s*|\s+or\s+", head) if n.strip()]
    left = [n for n in names if f"wand of {n}".lower() not in known]
    if not left or len(left) == len(names):
        return verdict
    return (" or ".join(left) + (" (" + tail if tail else "")
            + f" [ruled out, already identified: {', '.join(n for n in names if n not in left)}]")


# ---- dipping (Excalibur) ------------------------------------------------------

_DIP_OUTCOMES = [
    (r"a hand reaches up to bless the sword", "EXCALIBUR"),
    (r"grants you a wish", "WISH"),
    (r"You unleash", "WATER DEMON (dangerous: flee or Elbereth; it may have granted a wish)"),
    (r"You attract", "WATER NYMPH (steals: kill it fast or keep away)"),
    (r"stream of snakes|Snakes!", "WATER MOCCASINS (poisonous: retreat, fight one at a time)"),
    (r"fountain dries up", "fountain dried up"),
    # fountain.c dryup() in a town: the first dry-up roll only WARNS — the fountain stays, and the next one
    # dries it AND angers the Watch (p3 shift 17 #1275/#1321: both lines were read as harmless)
    (r"reduces to a trickle|stop using that fountain|earnestly (?:shakes|waves)",
     "TOWN FOUNTAIN WARNING — STOP dipping/quaffing here: the next dry-up ANGERS THE WATCH (the fountain is "
     "still there)"),
    (r"freezing mist", "CURSED item (you are not lawful?!)"),
    (r"(rusts|rusty|corrode)", "item rusted"),
    (r"spot a gem", "gem"),
    (r"gushes forth", "water gushes"),
    (r"coins", "coins"),
]


def dip(letter: str, into_fountain: bool = True) -> dict:
    """Dip inventory item `letter` into the fountain/pool you stand on, one
    dip per call: answers the prompts and classifies the outcome.
    For Excalibur: lawful, XL5+, long sword, full HP, a planned escape, never
    in Minetown (the Watch). Each dip: 1/6 Excalibur; otherwise the sword may
    rust and the fountain dries up about 1 time in 3 — so expect to need 2-3
    fountains. Returns {"outcome", "messages", "before", "after"} (the item's
    inventory line before and after: a fountain can curse it silently, which
    shows only there when you know its BUC); prints the outcome."""
    ctx.require_command("dip()")
    before = next((it["text"] for it in inventory() if it["letter"] == letter), None)
    s = ctx.do("#dip<CR>", quiet=True)
    if s.state.kind != "object":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        raise RuntimeError(f"dip: expected 'What do you want to dip?', got {s.state.kind} {s.state.prompt!r}")
    s = ctx.do(letter, quiet=True)
    msgs = list(s.messages)
    p = s.state.prompt or ""
    if s.state.kind == "yn" and ("fountain" in p or "pool" in p or "moat" in p or "water" in p):
        if not into_fountain:
            ctx.do("n", quiet=True)
        else:
            s = ctx.do("y", quiet=True)
            msgs += s.messages
    elif s.state.kind != "command":
        ctx.do("<Esc>", quiet=True)
        raise RuntimeError(f"dip: not standing on a fountain/pool (got {s.state.kind}: {p!r})")
    msgs = [m for m in msgs if not re.search(r"\[yn\]|\? *$", m)]    # the "Dip ... into the fountain?" prompt
    joined = " | ".join(msgs)
    outcome = "; ".join(o for pat, o in _DIP_OUTCOMES if re.search(pat, joined)) or \
        ("nothing special" if msgs else "no message (a silent outcome: the fountain is still there)")
    if s.state.kind == "getlin" and "wish" in (s.state.prompt or "").lower():
        outcome = "WISH"
        ctx.pause("dip: WISH prompt open — follow PLAYBOOK §E (first wish: blessed +2 gray dragon scale mail); "
                  "answer with cont(reply='...<CR>') promptly.")
    after = None
    if s.state.kind == "command":
        after = next((it["text"] for it in inventory() if it["letter"] == letter), None)
        if before and after != before:
            outcome += f"; the item changed: {before!r} -> {after!r}"
            if after and re.search(r"\bcursed\b", after) and not re.search(r"\bcursed\b", before):
                outcome += " (CURSED by the fountain: holy water / remove curse / pray when in trouble)"
    print(f"dip({letter!r}): {outcome}")
    return {"outcome": outcome, "messages": msgs, "before": before, "after": after}


_GLOW = [
    (r"glows? amber", "now UNCURSED (it was cursed)"),
    (r"glows? with a light blue aura", "now BLESSED (it was uncursed)"),
    (r"glows? with a black aura", "now CURSED (it was uncursed)"),
    (r"glows? brown", "now UNCURSED (it was blessed)"),
    (r"^Interesting\.\.\.", "nothing happened (not water, or water that can't change it)"),
    (r"gets? wet|dilute", "got wet/diluted (plain water)"),
    (r"explode", "the potions EXPLODED"),
]


def dip_into(letter: str, potion: str, name: str | None = None) -> dict:
    """Dip inventory item `letter` into the potion `potion` with #dip (a
    fountain/pool here is declined). Holy water: a cursed item "glows amber"
    (now uncursed), an uncursed one "glows with a light blue aura" (now
    blessed); unholy water: "black aura" (cursed), a blessed item "glows
    brown" (uncursed). The potion is used up; the "Call a clear potion:"
    prompt that may follow is answered with `name` (or skipped with Esc —
    clear potions are always water). Returns {"outcome", "messages",
    "before", "after"} (the item's inventory text) and prints the outcome."""
    ctx.require_command("dip_into()")
    inv = inventory()
    before = next((it["text"] for it in inv if it["letter"] == letter), None)
    pot = next((it["text"] for it in inv if it["letter"] == potion), None)
    if before is None or pot is None:
        raise RuntimeError(f"dip_into: no item {letter!r} or no potion {potion!r} in the inventory")
    s = ctx.do("#dip<CR>", quiet=True)
    if s.state.kind != "object":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        raise RuntimeError(f"dip_into: expected 'What do you want to dip?', got {s.state.kind} {s.state.prompt!r}")
    s = ctx.do(letter, quiet=True)
    msgs = list(s.messages)
    if s.state.kind == "yn" and re.search(r"fountain|pool|moat|water|lava", s.state.prompt or ""):
        s = ctx.do("n", quiet=True)                 # not into the fountain/pool: into a potion
        msgs += s.messages
    if s.state.kind != "object" or "into" not in (s.state.prompt or ""):
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        raise RuntimeError(f"dip_into: expected 'What do you want to dip ... into?', got {s.state.kind} "
                           f"{s.state.prompt!r} ({msgs})")
    s = ctx.do(potion, ok=[p for p, _ in _GLOW] + [r"^Call "])
    msgs += s.messages
    if s.state.kind == "getlin" and (s.state.prompt or "").startswith("Call "):
        s = ctx.do(f"{name}<CR>" if name else "<Esc>", quiet=True)
        msgs += s.messages
    joined = " | ".join(msgs)
    outcome = "; ".join(o for pat, o in _GLOW if re.search(pat, joined)) or \
        ("no visible effect" if not msgs else "see messages")
    after = None
    if s.state.kind == "command":
        after = next((it["text"] for it in inventory() if it["letter"] == letter), None)
    print(f"dip_into({letter!r}, {potion!r}): {outcome}" + (f"; now {after!r}" if after else ""))
    return {"outcome": outcome, "messages": msgs, "before": before, "after": after}


_RUB = [
    (r"grant one wish", "WISH"),
    (r"Thank you for freeing me", "TAME djinni (no wish)"),
    (r"You freed me", "PEACEFUL djinni (no wish)"),
    (r"It is about time", "the djinni left (no wish)"),
    (r"You disturbed me, fool", "HOSTILE djinni: kill it (it hits hard) or get away"),
    (r"puff of smoke|You smell smoke", "a puff of smoke (magic lamp: nothing yet, rub again)"),
    (r"not particularly rewarding", "a brass lantern: nothing"),
    (r"Nothing happens", "nothing happens (an oil lamp never does anything)"),
]
_RUB_OK = [r"^You now wield", r"puff of smoke", r"^You smell smoke", r"^Nothing happens"]


def rub(letter: str, max_rubs: int = 1, rewield: bool = True) -> dict:
    """#rub the lamp `letter` up to `max_rubs` times, stopping at the first
    djinni. #rub WIELDS the lamp; afterwards (rewield=True) your weapon is
    wielded again (one more turn). A magic lamp: each rub 1/3 djinni; a
    BLESSED one then grants a wish 80% (uncursed 20%, cursed 5% — cursed:
    80% hostile). The wish prompt pauses the exec: answer it only with
    `cont --reply '...<CR>'` (PLAYBOOK §E). Returns {"outcome", "messages",
    "rubs"} and prints the outcome."""
    ctx.require_command("rub()")
    inv = inventory()
    lamp = next((it["text"] for it in inv if it["letter"] == letter), None)
    if lamp is None:
        raise RuntimeError(f"rub(): no item {letter!r} in the inventory")
    welded = _welded(inv)
    if welded is not None and welded["letter"] != letter:
        raise RuntimeError(f"rub(): your weapon {welded['letter']} - {welded['text']} is CURSED, so it is welded to "
                           "your hand, and #rub has to WIELD the lamp: NetHack refuses. Uncurse the weapon first "
                           "(holy water: dip it; a scroll of remove curse; a prayer that fixes it), then rub.")
    weapon = next((i["letter"] for i in inv if _wielded(i["text"]) and i["letter"] != letter), None)
    msgs: list = []
    outcome, n = "", 0
    for n in range(1, max_rubs + 1):
        s = ctx.do("#rub<CR>", quiet=True)
        if s.state.kind != "object":
            if s.state.kind != "command":
                ctx.do("<Esc>", quiet=True)
            raise RuntimeError(f"rub(): expected 'What do you want to rub?', got {s.state.kind} {s.state.prompt!r}")
        s = ctx.do(letter, ok=_RUB_OK)
        msgs += s.messages
        cur = ctx.last()
        if cur is not s:                    # the wish prompt paused and was answered with cont --reply
            msgs += [m for m in cur.messages if m not in msgs]
        joined = " | ".join(msgs)
        outcome = next((o for pat, o in _RUB if re.search(pat, joined)), "")
        if cur.state.kind != "command" or not re.search(r"smoke|^nothing happens", outcome):
            break
    if rewield and weapon and ctx.last().state.kind == "command":
        s = ctx.do("w" + weapon, quiet=True, ok=[r"^[a-zA-Z] - "])
        msgs += s.messages
    print(f"rub({letter!r}): {outcome or 'see messages'} after {n} rub(s)"
          + (f"; re-wielded {weapon!r}" if rewield and weapon else ""))
    return {"outcome": outcome, "messages": msgs, "rubs": n}


ID_PRIORITY = (r"^Rings", r"^Amulets", r"^Wands", r"^Potions", r"^Scrolls", r"^Spellbooks", r"^Armor",
               r"^Tools", r".")


def _menu_entries(s):
    """All selectable entries of the open menu, every page: [(page, letter,
    'Class header: item text')]; leaves the menu on its last page."""
    out = []
    for _page in range(10):
        m = s.state.menu
        if m is None:
            break
        cls = ""
        for it in m.items:
            if it.header:
                cls = it.text
            elif it.letter:
                out.append((m.page, it.letter, f"{cls}: {it.text}"))
        if m.page < m.pages:
            s = ctx.do(">", quiet=True)
        else:
            break
    return out


def read_identify(letter: str, priority=ID_PRIORITY) -> list:
    """Read the scroll of identify `letter` and answer its menus: each round
    picks the ONE item ranked first by `priority` (regexes tried in order on
    'Class: item text' — default rings, amulets, wands, potions, scrolls,
    spellbooks, armor, tools, anything), so a scroll that identifies several
    items takes them in your order (NetHack would otherwise take them in
    inventory order). Returns the messages (the identified items' lines)."""
    ctx.require_command("read_identify()")
    s = ctx.do("r", quiet=True)
    if s.state.kind != "object":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        raise RuntimeError(f"read_identify(): expected 'What do you want to read?', got {s.state.kind}")
    s = ctx.do(letter, quiet=True)
    msgs = list(s.messages)
    rxs = [re.compile(p, re.I) for p in priority]
    for _round in range(20):
        title = (s.state.prompt or "") + " " + (s.state.menu.title if s.state.menu is not None else "")
        if s.state.kind != "menu" or "identify" not in title:
            break
        entries = _menu_entries(s)
        pick = next((e for rx in rxs for e in entries if rx.search(e[2])), None)
        if pick is None:
            # (Esc here throws the scroll's remaining identifications away: invent.c menu_identify)
            dflt = [re.compile(p, re.I) for p in ID_PRIORITY]
            pick = next((e for rx in dflt for e in entries if rx.search(e[2])), entries[0] if entries else None)
            if pick is not None:
                print(f"read_identify(): none of your priorities matched — taking {pick[2]!r}")
        if pick is None:
            s = ctx.do("<Esc>", quiet=True)
            break
        s = ctx.last()
        while s.state.menu is not None and s.state.menu.page > pick[0]:
            s = ctx.do("<", quiet=True)
        s = ctx.do(pick[1], quiet=True)
        s = ctx.do("<CR>", quiet=True)
        msgs += s.messages
    print("read_identify(): " + (" | ".join(m for m in msgs if re.match(r"^[a-zA-Z$] - ", m)) or
                                 " | ".join(msgs[-3:])))
    return msgs


_CHARGES = re.compile(r"\((?:\d+|-\d+):(-?\d+)\)")


def write_scroll(name: str, paper: str | None = None, marker: str | None = None, force: bool = False) -> dict:
    """Write a scroll (or spellbook, on blank spellbook paper) of `name`
    ('enchant armor', 'identify', 'remove curse'...) with your magic marker
    on a blank one (found in the inventory unless given). Refuses a type you
    haven't identified (NetHack then usually fails — "You don't know how to
    write that!" — and the blank is lost) unless force=True. Ink cost is
    random between half and all of the type's base cost (identify 14,
    enchant armor 16, remove curse 16, enchant weapon 16, charging 16,
    genocide 30); a marker "too dry" keeps the blank. Returns {"messages",
    "charges_before", "charges_after", "written"}."""
    ctx.require_command("write_scroll()")
    inv = inventory()
    if marker is None:
        m = next((i for i in inv if "magic marker" in i["text"]), None)
        if m is None:
            raise RuntimeError("write_scroll(): no magic marker in the inventory")
        marker = m["letter"]
    if paper is None:
        p = next((i for i in inv if re.search(r"unlabeled scroll|scrolls? of blank paper|plain spellbook|"
                                               r"spellbooks? of blank paper|unlabeled", i["text"])), None)
        if p is None:
            raise RuntimeError("write_scroll(): no blank scroll (unlabeled) in the inventory — blank some by "
                               "dipping scrolls into a fountain/water")
        paper = p["letter"]
    book = "spellbook" in next((i["text"] for i in inv if i["letter"] == paper), "")
    if not force:
        full = f"{'spellbook' if book else 'scroll'} of {name}"
        known = {n for n, _look in discoveries()}
        if full not in known:
            raise PermissionError(f"write_scroll(): {full!r} isn't identified yet — writing an unknown type usually "
                                  "fails and uses up the blank. force=True to gamble.")
    mtext = next((i["text"] for i in inv if i["letter"] == marker), "")
    cm = _CHARGES.search(mtext)
    before = int(cm.group(1)) if cm else None
    s = ctx.do("a", quiet=True)
    if s.state.kind != "object":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        raise RuntimeError(f"write_scroll(): expected the apply prompt, got {s.state.kind}")
    s = ctx.do(marker, quiet=True)
    if s.state.kind != "object" or "write on" not in (s.state.prompt or ""):
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        raise RuntimeError(f"write_scroll(): expected 'What do you want to write on?', got {s.state.kind} "
                           f"{s.state.prompt!r} ({s.messages})")
    s = ctx.do(paper, quiet=True)
    msgs = list(s.messages)
    if s.state.kind != "getlin":
        raise RuntimeError(f"write_scroll(): no 'What type of scroll' prompt ({s.state.kind} {s.state.prompt!r}; "
                           f"{msgs})")
    s = ctx.do(f"{name}<CR>", quiet=True)
    msgs += s.messages
    after = None
    written = None
    if s.state.kind == "command":
        inv2 = inventory()
        cm = _CHARGES.search(next((i["text"] for i in inv2 if i["letter"] == marker), ""))
        after = int(cm.group(1)) if cm else None
        written = next((m for m in msgs if re.match(r"^[a-zA-Z] - ", m)), None)
    print(f"write_scroll({name!r}): " + (written or " | ".join(msgs[-2:]))
          + (f"; marker {before} -> {after} charges" if before is not None else ""))
    return {"messages": msgs, "charges_before": before, "charges_after": after, "written": written}


def _menu_pick(s, pattern: str):
    """Select (by text, on any page) the first item of the open menu matching
    `pattern`; returns the snap after the key, or None if there is none."""
    rx = re.compile(pattern, re.I)
    for _page in range(8):
        items = [it for it in s.state.menu.selectable() if rx.search(it.text)] if s.state.menu else []
        if items:
            return ctx.do(items[0].letter, quiet=True)
        if s.state.menu and s.state.menu.page < s.state.menu.pages:
            s = ctx.do(">", quiet=True)
        else:
            return None
    return None


def _apply_container(bag: str, action: str):
    """'a' + bag, then pick `action` ('take something out' / 'stash one item')
    in the pick-one "Do what with ...?" menu. Returns the snap."""
    ctx.require_command("bag helper")
    s = ctx.do("a", quiet=True)
    if s.state.kind != "object":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        raise RuntimeError(f"bag: expected 'What do you want to use or apply?', got {s.state.kind} {s.state.prompt!r}")
    s = ctx.do(bag, quiet=True)
    if s.state.kind != "menu" or "Do what with" not in (s.state.prompt or ""):
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        raise RuntimeError(f"bag: {bag!r} didn't open as a container (got {s.state.kind} {s.state.prompt!r}; "
                           f"messages {s.messages}) — a bag of tricks bites; check what it is first")
    nxt = _menu_pick(s, action)
    if nxt is None:
        ctx.do("<Esc>", quiet=True)
        raise RuntimeError(f"bag: no {action!r} choice (empty bag?) in {[i.text for i in s.state.menu.selectable()]}")
    return nxt


def _warn_full(msgs, who: str) -> None:
    """pickup.c lift_object(): a full pack (52 letters) silently stops a pickup."""
    if any("cannot accommodate any more items" in m for m in msgs):
        print(f"!! {who}: your pack is FULL (52 inventory letters) — the rest stayed where it was. Drop or bag "
              "something (bag_put) and try again.")


_ENC = ("", "Burdened", "Stressed", "Strained", "Overtaxed", "Overloaded")
_TAKE = ("encumbrance",)     # a heavier load from a helper's own pickup is no news: _enc_note says it once


def _enc_note(who: str, enc0: str) -> None:
    st = ctx.last().status
    e1 = (st.encumbrance or "") if st.ok else ""
    if e1 in _ENC and (enc0 or "") in _ENC and _ENC.index(e1) > _ENC.index(enc0 or ""):
        print(f"{who}: you are now {e1}" + ("" if e1 == "Burdened" else
                                              " — !! slow and clumsy in a fight: drop or bag something heavy"))


def _boh_risk(bag_text: str, item_text: str) -> str:
    """Why putting the item into this container could blow up a bag of holding ('' when it can't):
    pickup.c mbag_explodes() — a bag of holding or of tricks, or a charged wand of cancellation (also
    inside another container), destroys the bag of holding and everything in it."""
    b, it = (bag_text or "").lower(), (item_text or "").lower()
    if re.search(r"\b(?:oilskin )?sacks?\b", b) or "bag of tricks" in b or not re.search(r"\bbag\b", b):
        return ""                      # an identified sack/oilskin sack, or not a bag at all
    what = "this bag of holding" if "bag of holding" in b else "this bag (unidentified: maybe a bag of holding)"
    if re.search(r"\bbags? of (?:holding|tricks)\b", it):
        return f"a bag of holding/tricks put into {what} makes it EXPLODE (everything inside is lost)"
    if re.search(r"\bwands? of cancellation\b", it) and not re.search(r"\(\d+:0\)", it):
        return f"a wand of cancellation put into {what} makes it EXPLODE (everything inside is lost)"
    if re.search(r"\bbags?\b", it) and not re.search(r"\bsacks?\b", it):
        return f"an unidentified bag may be a bag of holding or tricks: into {what} it may EXPLODE"
    if re.search(r"\bwands?\b", it) and not re.search(r"\bwands? of\b", it) \
            and (not re.search(r"\bcalled\b", it) or re.search(r"cancel|vanish", it)):
        return (f"an unidentified wand may be CANCELLATION: into {what} it may EXPLODE (engrave-test it: "
                "'vanishes' = cancellation/teleport/make invisible)")
    return ""


# the Amulet of Yendor, the Candelabrum, the Bell of Opening and the Book of the Dead, named or not (their looks:
# "candelabrum", "silver bell", "papyrus spellbook"); a bag refuses the real ones
_INVOCATION = re.compile(r"\b(?:Amulet of Yendor|Candelabrum of Invocation|candelabrum|Bell of Opening|silver bell|"
                         r"Book of the Dead|papyrus spellbook)\b")


def bag_put(bag: str, letters: str, one_move: bool = True, force: bool = False) -> list:
    """Put the inventory items `letters` (e.g. 'mq') into the carried
    container `bag`. one_move=True (default): the container's "put something
    in" menu takes them all in ONE move (an ambush leaves no time for one
    move per item); one_move=False: one "stash one item" per item. Refuses
    anything that can make a bag of holding explode (a bag of holding/tricks,
    a wand of cancellation, or an unidentified bag/wand while the bag may be
    one) unless force=True. Returns the messages."""
    ctx.require_command("bag_put()")
    letters = "".join(dict.fromkeys(letters))
    if bag in letters:
        raise ValueError(f"bag_put: {bag!r} is the bag itself")
    inv = {it["letter"]: it["text"] for it in inventory()}
    if bag not in inv:
        raise LookupError(f"bag_put: no item {bag!r} in your inventory")
    missing = [c for c in letters if c not in inv]
    if missing:
        raise LookupError(f"bag_put: no inventory item(s) {missing}")
    held = [c for c in letters if _INVOCATION.search(inv[c])]
    if held:
        # pickup.c in_container(): "cannot be confined in such trappings" (p1 shift 34 #295: the Book of the Dead)
        print("bag_put: the invocation items stay in your pack — the game refuses to bag them: "
              + ", ".join(f"{c} ({inv[c]})" for c in held))
        letters = "".join(c for c in letters if c not in held)
        if not letters:
            return []
    risky = [(c, _boh_risk(inv[bag], inv[c])) for c in letters]
    risky = [(c, why) for c, why in risky if why]
    if risky and not force:
        raise PermissionError("bag_put: refusing — " + "; ".join(f"{c} ({inv[c]}): {why}" for c, why in risky)
                              + ". force=True if you know it is safe.")
    enc0 = ctx.last().status.encumbrance or ""
    if not one_move or len(letters) == 1:
        msgs = []
        for letter in letters:
            s = _apply_container(bag, r"stash one item")
            msgs += s.messages
            if s.state.kind != "object":
                if s.state.kind != "command":
                    ctx.do("<Esc>", quiet=True)
                raise RuntimeError(f"bag_put: expected the stash prompt, got {s.state.kind} {s.state.prompt!r}")
            s = ctx.do(letter, quiet=True)
            msgs += s.messages
            if s.state.kind != "command":
                ctx.pause(f"bag_put({letter!r}): unexpected {s.state.kind} {s.state.prompt!r}")
        _stashed(letters, msgs)
        return msgs
    # pickup.c menu_loot(put_in): a class menu ("Put in what type of objects?": never 'A', which puts in
    # EVERYTHING), then "Put in what?" listing your items under their own inventory letters (invlet_constant)
    s = _apply_container(bag, r"^put .* in$")
    msgs = list(s.messages)
    chosen: set = set()
    for _ in range(6):
        k, p = s.state.kind, s.state.prompt or ""
        if k == "command":
            break
        if k == "menu" and "what type of objects" in p:
            nxt = _menu_pick(s, r"^All types")
            if nxt is None:
                ctx.do("<Esc>", quiet=True)
                raise RuntimeError(f"bag_put: no 'All types' in {[i.text for i in s.state.menu.selectable()]}")
            s = ctx.do("<CR>", quiet=True)
        elif k == "menu" and "Put in what" in p:
            for _page in range(8):
                for it in s.state.menu.selectable():
                    if it.letter in letters and it.letter not in chosen and not it.selected:
                        s = ctx.do(it.letter, quiet=True)
                        chosen.add(it.letter)
                if s.state.menu and s.state.menu.page < s.state.menu.pages:
                    s = ctx.do(">", quiet=True)
                else:
                    break
            if not chosen:
                ctx.do("<Esc>", quiet=True)
                raise RuntimeError(f"bag_put: none of {letters!r} is offered in the 'Put in what?' menu")
            s = ctx.do("<CR>", quiet=True, expect=_TAKE)
        else:
            ctx.pause(f"bag_put(): unexpected {k} {p!r}")
            s = ctx.last()
        msgs += s.messages
    left = [c for c in letters if c not in chosen]
    if left:
        print(f"bag_put: {left} not offered by the menu (worn/wielded items can't go in) — still in your pack")
    _stashed("".join(chosen), msgs)
    _enc_note("bag_put", enc0)
    return msgs


def _stashed(letters: str, msgs) -> None:
    """Items put into a bag leave the open pack: the Gehennom burn warning (per the last inventory())
    must not keep naming them (p1 shift 29)."""
    if not any(re.search(r"^You put .* into ", m) for m in msgs or []):
        return
    lb = getattr(ctx.game, "loose_burnables", None)
    if lb:
        ctx.game.loose_burnables = [c for c in lb if c not in letters]
        _refresh_burn_note()


def _refresh_burn_note() -> None:
    """The snap the obs shows was annotated before the list changed (p1 shift 29 #3333: the warning named an
    item right after bag_put() and inventory()): recompute its burn note now."""
    f = getattr(ctx.game, "burn_note_for", None)
    s = getattr(ctx.game, "last", None)
    if f is not None and s is not None and hasattr(s, "burn_note"):
        try:
            s.burn_note = f(s)
        except Exception:  # noqa: BLE001  (a note must never break the helper)
            pass


_DISCO_LINE = re.compile(r"^\*?\s*(?P<name>\S.*?) \((?P<app>[^()]+)\)$")
_DISCO_CLASS = {"potion": "{} potion", "scroll": "scroll labeled {}", "wand": "{} wand", "ring": "{} ring",
                "amulet": "{} amulet", "spellbook": "{} spellbook"}


def discoveries() -> list:
    """What you have identified or named (the '\\' list; no game time):
    [(name, unidentified look)], e.g. ('potion of paralysis', 'white potion'),
    ('potion called water', 'clear potion'), ('scroll of identify',
    'scroll labeled KIRJE'), ('magic lamp', 'lamp'). Identified and named
    types are shown by that name everywhere (inventory, bags, the floor)."""
    ctx.require_command("discoveries()")
    with ctx.no_monster_pauses():
        s = ctx.do("\\", quiet=True)
    out = parse_discoveries(s.messages)
    s.messages = []            # the whole list would otherwise show as the exec's last `msgs:` line
    return out


def parse_discoveries(blocks) -> list:
    out, heading = [], ""
    for block in blocks:
        for line in block.split("\n"):
            m = _DISCO_LINE.match(line.strip())
            if not m:
                if line.strip() and not line.startswith((" ", "*")):
                    heading = line.strip()            # "Potions", "Gems/Stones", ...
                continue
            name, app = m.group("name"), m.group("app")
            word = name.split()[0]
            if word in _DISCO_CLASS:
                look = _DISCO_CLASS[word].format(app)
            elif heading.startswith("Gems"):
                look = f"{app} stone" if re.search(r"stone$|^flint", name) else f"{app} gem"
            else:
                look = app                            # tools/armor: 'lamp', 'ornamental cope'
            out.append((name, look))
    return out


def _name_rx(name: str):
    """'potion of paralysis' -> matches 'potions of paralysis' too."""
    words = name.split(" ", 1)
    if words[0] in _DISCO_CLASS and len(words) > 1:
        rest = re.escape(words[1])
        if words[1] == "of water":
            rest = r"of (?:holy |unholy )?water"          # "potions of holy water" (blessed, known)
        return re.compile(re.escape(words[0]) + r"s? " + rest, re.I)
    return re.compile(re.escape(name) + r"(?:e?s)?\b", re.I)


def with_looks(text: str, disco: list) -> str:
    """An item text plus the unidentified look of its (identified/named)
    type: 'a potion of paralysis' -> 'a potion of paralysis [white potion]'."""
    looks = [look for name, look in disco if _name_rx(name).search(text)]
    return text + "".join(f" [{lk}]" for lk in looks)


def bag_contents(bag: str) -> list:
    """What the carried container `bag` holds, taking nothing out: apply it and "Look inside" (pickup.c: no game
    time once its contents are known — the first look into a bag you never opened costs a turn). Returns the
    item texts ([] for an empty bag) and prints them. p1 shift 35 #83: bag_take() with a pattern that matched
    nothing was the only way to list a bag."""
    ctx.require_command("bag_contents()")
    s = ctx.do("a", quiet=True)
    if s.state.kind != "object":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        raise RuntimeError(f"bag_contents: expected the apply prompt, got {s.state.kind} {s.state.prompt!r}")
    s = ctx.do(bag, quiet=True)
    menu = s.state.menu
    if s.state.kind != "menu" or "Do what with" not in (s.state.prompt or "") or menu is None:
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        if any(re.search(r" is empty\.", m) for m in s.messages):
            print(f"bag_contents({bag!r}): empty")
            return []
        raise RuntimeError(f"bag_contents: {bag!r} didn't open as a container ({s.state.kind} "
                           f"{s.state.prompt!r}; {s.messages})")
    # (its selector is ':', which the menu parser keeps as a header line: ": - Look inside the bag")
    if not any(re.match(r"^(?:: - )?Look inside", i.text) for i in menu.items):
        ctx.do("<Esc>", quiet=True)
        raise RuntimeError(f"bag_contents: no 'Look inside' in {[i.text for i in menu.items]}")
    s = ctx.do(":", quiet=True)
    # (the step reads the "Contents of the bag:" window into the messages and closes it; the container menu
    # comes back after a look)
    text = "\n".join(s.messages)
    mm = re.search(r"Contents of [^\n]*:\n(.*)", text, re.S)
    items: list = [ln.strip() for ln in mm.group(1).split("\n") if ln.strip()] if mm else []
    empty = bool(re.search(r" is empty\.", text))
    for _ in range(4):
        if s.state.kind == "command":
            break
        s = ctx.do("<Esc>", quiet=True)
    items = [t for t in items if not re.search(r" is empty\.$", t)]
    print(f"bag_contents({bag!r}): " + ("empty" if empty and not items else
                                        f"{len(items)} item(s): " + "; ".join(items)))
    return items


def bag_take(bag: str, pattern: str | None = None) -> list:
    """Take items out of the carried container `bag`: those whose menu text
    matches `pattern` (regex, case-insensitive), or everything if None.
    The menu lists identified/named types by name ("potion of paralysis",
    "potions called water"), so the pattern is also tried against their
    unidentified look from discoveries() ('white' finds the paralysis
    potion). Raises LookupError listing the contents if nothing matches.
    Returns the messages. 'gold' or '$' means the coins only (not golden
    potions or gold rings)."""
    if pattern is not None and pattern.strip().lower() in ("gold", "$", "coins", "gold pieces", "zorkmids"):
        pattern = r"\bgold pieces?\b"
    disco = discoveries() if pattern else []
    enc0 = ctx.last().status.encumbrance or ""
    s = _apply_container(bag, r"take something out")
    msgs = list(s.messages)
    for _ in range(6):
        k, p = s.state.kind, s.state.prompt or ""
        if k == "command":
            break
        if k == "menu" and "what type of objects" in p:
            nxt = _menu_pick(s, r"^All types")
            if nxt is None:
                ctx.do("<Esc>", quiet=True)
                raise RuntimeError(f"bag_take: no 'All types' in {[i.text for i in s.state.menu.selectable()]}")
            s = ctx.do("<CR>", quiet=True)
        elif k == "menu":
            rx = re.compile(pattern, re.I) if pattern else None
            chosen, seen = 0, []
            for _page in range(8):
                for it in s.state.menu.selectable():
                    seen.append(it.text)
                    if not it.selected and (rx is None or rx.search(with_looks(it.text, disco))):
                        s = ctx.do(it.letter, quiet=True)
                        chosen += 1
                if s.state.menu and s.state.menu.page < s.state.menu.pages:
                    s = ctx.do(">", quiet=True)
                else:
                    break
            if rx is not None and not chosen:
                ctx.do("<Esc>", quiet=True)
                raise LookupError(f"bag_take: nothing in {bag!r} matches {pattern!r}; it holds: "
                                  + "; ".join(with_looks(t, disco) for t in seen))
            s = ctx.do("<CR>", quiet=True, expect=_TAKE)
        else:
            ctx.pause(f"bag_take(): unexpected {k} {p!r}")
            s = ctx.last()
        msgs += s.messages
    _warn_full(msgs, "bag_take")
    _enc_note("bag_take", enc0)
    return msgs


def _zero_nutrition(item: str) -> bool:
    """A corpse with 0 nutrition (wraith, vortices, lights, elementals, paper/straw golems...): eating it
    can't choke you, Satiated or not (eat.c lesshungry(0) adds nothing)."""
    from nh.danger import monster_record
    m = re.search(r"(?:^|\b)(?:an? |\d+ |the )?(?:partly eaten )?([a-z][\w' -]*?) corpses?\b", item or "")
    rec = monster_record(m.group(1)) if m else None
    return bool(rec) and rec.get("nutrition") == 0


def eat(letter: str | None = None, pattern: str | None = None) -> list:
    """Eat inventory item `letter`, or (letter=None) the food on the floor
    here. NetHack first offers each floor corpse ("There is a jackal corpse
    here; eat it?"): with a letter those are declined; with `pattern` (a
    regex, e.g. eat(pattern='wraith corpse')) only a matching one is eaten
    (the others are declined). The harness guards still apply (deadly/old
    corpses, tins, Satiated) — except that a corpse with 0 nutrition (a
    wraith's) can't choke you, so it is eaten while Satiated too. Returns
    the messages — [] when nothing (matching) was on the floor to eat."""
    ctx.require_command("eat()")
    rx = re.compile(pattern, re.I) if pattern else None
    zero_ok = False
    if rx is not None and ctx.last().status.hunger == "Satiated":
        floor = here()
        hits = [t for t in re.split(r"\n|\s*\|\s*|(?<=\.)\s+", floor) if rx.search(t)]
        zero_ok = bool(hits) and all(_zero_nutrition(t) for t in hits)
    s = ctx.do("e", quiet=True, force=zero_ok)
    msgs = list(s.messages)
    current = ""
    for _ in range(12):
        k, p = s.state.kind, s.state.prompt or ""
        if k == "command":
            break
        if k == "yn" and "here; eat" in p:
            mm = re.search(r"There (?:is|are) (.+?) here; eat", p)
            item = mm.group(1) if mm else p
            take = letter is None and (rx is None or bool(rx.search(item)))
            if take:
                current = item
            s = ctx.do("y" if take else "n", quiet=True)
        elif k == "object":
            if letter is None:
                # (p3 shift 13: the kill left no corpse — raising aborted the rest of the exec)
                ctx.do("<Esc>", quiet=True)
                print("eat(): nothing eaten — no " + (f"floor food matching {pattern!r}" if pattern else
                                                      "food on the floor") + " here (pass an inventory letter "
                      "to eat from your pack)")
                return []
            s = ctx.do(letter, quiet=True)
        elif k in ("yn", "getlin") and "Continue eating" in p:
            if _zero_nutrition(current):
                s = ctx.do("y", quiet=True, force=True)   # 0 nutrition: nothing to choke on (a wraith: its level)
            else:
                s = ctx.do("n", quiet=True)          # starting Satiated: stop before choking
        else:
            ctx.pause(f"eat(): unexpected {k} {p!r}")
            s = ctx.last()
        msgs += s.messages
    text = " | ".join(msgs)
    if re.search(r"rises from the dead", text):
        print("eat(): the troll REVIVED mid-meal — kill it, then eat the new corpse at once (or tin it / keep "
              "it off the floor)")
    if "Rotten" in text:
        # eat.c rottenfood(): passing out stops the meal and flags the corpse rotten (every new try
        # rolls again); the confusion/blindness branches finish it for a quarter of its nutrition
        if re.search(r"world spins|conscious again", text):
            print("eat(): ROTTEN — you passed out; the corpse is now flagged rotten (each new try rolls "
                  "again): leave it")
        else:
            print("eat(): rotten food — you ate it anyway, but for only a quarter of its nutrition")
    return msgs


def kick_test(x: int, y: int) -> dict:
    """Is the gray stone on the ADJACENT square (x, y) a loadstone? Kick it (dokick.c really_kick_object(): the
    range is Str/2 - weight/40, so a loadstone (500) never moves — "Thump!" — while a luckstone, touchstone or
    flint (10) slides away). The square beyond it must be open floor (a wall, rock or closed door there makes
    any stone go "Thump!"), and the stone must be the top object there (a kick moves the top one). Returns
    {'verdict', 'to': where it landed or None, 'messages'}; a stone that slid into view is marked, so pickup()
    takes it on that square without force (game.kicked_stones). Not in a shop, not while levitating."""
    from .mapview import DIR_KEY, is_walkable
    from .nav import NavError
    s = ctx.require_command("kick_test()")
    h = s.hero
    if h is None or max(abs(x - h[0]), abs(y - h[1])) != 1:
        raise NavError(f"kick_test: {(x, y)} is not next to you at {h} — stand next to the stone")
    dx, dy = x - h[0], y - h[1]
    beyond = (x + dx, y + dy)
    if not is_walkable(s, *beyond, allow_monsters=False):
        raise NavError(f"kick_test: the square beyond the stone, {beyond}, isn't open floor — any stone goes "
                       "'Thump!' against it; kick from the opposite side")
    if s.status.ok and "Lev" in s.status.conditions:
        raise NavError("kick_test: you are levitating — no floor to brace a kick on")
    shop = ctx.game.shop_at(h, s.status) if hasattr(ctx.game, "shop_at") and s.status.ok else None
    if shop:
        raise NavError(f"kick_test: you are in {shop} — kicking things around a shop angers the shopkeeper")
    line = [(x + dx * k, y + dy * k) for k in range(0, 13)]     # the stone square first
    was = {c: s.screen.at(*c) for c in line}
    s = ctx.do("<C-d>", quiet=True)
    if s.state.kind != "direction":
        return {"verdict": "unclear: no kick (" + (" ".join(s.messages) or s.state.kind) + ")", "to": None,
                "messages": list(s.messages)}
    s = ctx.do(DIR_KEY[(dx, dy)], ok=[r"^Thump!$"])
    msgs = list(s.messages)
    if any(m.startswith("Thump!") for m in msgs):
        return {"verdict": "THUMP: it didn't move — a LOADSTONE (leave it be)", "to": None, "messages": msgs}
    if s.screen.at(x, y) == was[(x, y)] == "*":
        return {"verdict": "unclear: it is still there without a 'Thump!' (was it the top object?)", "to": None,
                "messages": msgs}
    to = next((c for c in line[1:] if s.screen.at(*c) == "*" and was[c] != "*"), None)
    if to is not None and s.status.ok:
        store = getattr(ctx.game, "kicked_stones", None)
        if store is not None:
            store.setdefault(ctx.game.level_key(s.status), set()).add(to)
    return {"verdict": "slid: NOT a loadstone" + (f" — it lies at {to} (pickup() takes it there)" if to else
                                                  " — it landed out of sight along that line"),
            "to": to, "messages": msgs}


_HEAVY_NAMES: list | None = None


def heavy_weight(text: str) -> int | None:
    """The base weight of a heavy thing named in an object text (200 or more: a large box/chest/ice box, heavy
    armor, a statue, an iron ball, a big corpse — a gnome lord's is 700), or None."""
    global _HEAVY_NAMES
    if _HEAVY_NAMES is None:
        import json
        from pathlib import Path
        import nh
        try:
            objs = json.loads((Path(nh.__file__).parent / "data" / "objects.json").read_text())["objects"]
        except Exception:  # noqa: BLE001
            objs = []
        _HEAVY_NAMES = sorted(((o["name"], o["weight"]) for o in objs if o.get("name") and (o.get("weight") or 0) >= 200),
                              key=lambda p: -len(p[0]))
    t = (text or "").lower()
    m = re.search(r"\b(?:an? |\d+ |the )?(?:partly eaten )?(.+?) corpses?\b", t)
    if m:
        from nh.danger import monster_record
        rec = monster_record(re.sub(r"^(?:an?|the|\d+|uncursed|blessed|cursed) ", "", m.group(1))) or {}
        w = rec.get("weight") or 0
        return w if w >= 200 else None
    for name, w in _HEAVY_NAMES:
        if re.search(rf"\b{re.escape(name)}(?:e?s)?\b", t):
            return w
    return None


def pickup(pattern: str | None = None, force: bool = False) -> list:
    """Pick up the objects here whose text matches `pattern` (regex,
    case-insensitive), or everything if None — except, with no pattern,
    heavy things (a large box/chest/ice box, heavy armor, statues, big
    corpses: heavy_weight() 200+), which it leaves and names (p4 shift 1: a
    350-weight large box came along). Looks first (no game time), so a lone
    object that doesn't match is left alone. NetHack's "You have much
    trouble / extreme difficulty lifting X. Continue?" (the lift would make
    you Stressed or worse) is answered no — the item stays and is named;
    force=True takes it ("a little trouble" = Burdened is taken). Returns the
    messages."""
    s0 = ctx.require_command("pickup()")
    blind = s0 is not None and s0.status.ok and "Blind" in s0.status.conditions
    look = here()
    if ("You see no objects here" in look or not look) and not blind:
        print(f"pickup({pattern!r}): there are no objects here" + (f" ({look})" if look else ""))
        return []
    if blind:
        look = ""          # (a remembered look may be stale: the ',' menu itself tells what you feel)
    if pattern and pattern.strip().lower() in ("ring", "rings"):
        pattern = r"\brings?\b(?!\s+mail)"          # a ring, not a ring mail (250 weight)
    if pattern:
        # the invocation items look different until identified: "papyrus spellbook", "silver bell",
        # "candelabrum" (and a fake "Amulet of Yendor" is identical to the real one)
        for real, look_as in (("Book of the Dead", "papyrus spellbook"), ("Bell of Opening", "silver bell"),
                              ("Candelabrum of Invocation", "candelabrum")):
            if re.search(pattern, real, re.I) and not re.search(pattern, look_as, re.I):
                pattern = f"(?:{pattern})|{look_as}"
    rx = re.compile(pattern, re.I) if pattern else None
    single = re.search(r"You (?:see|feel) here (.+?)\.(?: \||$)", look)
    if single and "Things that" not in look and rx is not None and not rx.search(single.group(1)):
        print(f"pickup({pattern!r}): nothing matching here — the floor has only {single.group(1)} "
              "(a pet or a monster may have moved it: obs.objects)")
        return []
    if single and "Things that" not in look and rx is None and heavy_weight(single.group(1)):
        print(f"pickup(): left {single.group(1)} (about {heavy_weight(single.group(1))} weight) — name it in a "
              "pattern to take it anyway (loot a box/chest where it stands: loot_all())")
        return []
    skipped: list = []
    enc0 = ctx.last().status.encumbrance or ""
    s = ctx.do(",", quiet=True, expect=_TAKE)
    msgs = list(s.messages)
    if s.state.kind == "menu":
        chosen, seen = 0, []
        for _page in range(8):
            for it in s.state.menu.selectable():
                seen.append(it.text)
                if rx is None and heavy_weight(it.text):
                    skipped.append(it.text)
                    continue
                if not it.selected and (rx is None or rx.search(it.text)):
                    s = ctx.do(it.letter, quiet=True)
                    chosen += 1
            if s.state.menu and s.state.menu.page < s.state.menu.pages:
                s = ctx.do(">", quiet=True)
            else:
                break
        if not chosen:
            ctx.do("<Esc>", quiet=True)
            print(f"pickup({pattern!r}): nothing matching here — the floor has: " + "; ".join(seen))
            return msgs
        try:
            s = ctx.do("<CR>", quiet=True, expect=_TAKE)
        except PermissionError:
            ctx.do("<Esc>", quiet=True)          # a guard refused (loadstone? cockatrice?): don't leave the menu open
            raise
        msgs += s.messages
    too_heavy = []
    for _ in range(30):
        # pickup.c lift_object(): "You have a little trouble / much trouble / extreme difficulty lifting X.
        # Continue?" — 'n' leaves that one and goes on with the rest (p3 shift 18 #933: a warhorse corpse)
        pr = s.state.prompt or ""
        if s.state.kind != "yn" or not re.search(r"(?:trouble|difficulty) lifting", pr):
            break
        if re.search(r"much trouble|extreme difficulty", pr) and not force:
            what = re.search(r"lifting (.+?)\.\s+Continue", pr)
            too_heavy.append(what.group(1) if what else pr)
            s = ctx.do("n", quiet=True)
        else:
            s = ctx.do("y", quiet=True, expect=_TAKE)
        msgs += s.messages
    if too_heavy:
        print("pickup(): left " + "; ".join(too_heavy[:4]) + " — lifting it would make you Stressed or worse "
              "(pickup(..., force=True) takes it anyway)")
    if skipped:
        print("pickup(): left the heavy " + "; ".join(skipped[:4]) + " — name them in a pattern to take them")
    if s.state.kind != "command":
        ctx.pause(f"pickup(): unexpected {s.state.kind} {s.state.prompt!r}")
    _warn_full(msgs, "pickup")
    _enc_note("pickup", enc0)
    return msgs


_DIG_OK = [r"^You (?:are )?now wield", r"^You (?:start|continue) (?:digging|chipping the statue)",
           r"^You dig a pit in the ",
           r"^You dig a hole through", r"^You make an opening", r"^You succeed in cutting away",
           r"^You dig (?:upward|downward)", r"^There's a hole", r"^You fall through", r"^You hit the ",
           r"^The boulder falls apart\.$", r"^The statue shatters\.$"]


def dig(direction: str = ">", tool: str | None = None, max_applies: int = 6) -> list:
    """Dig with your pick-axe/mattock (found in the inventory unless `tool`
    is given) in `direction` ('>' down, or a direction key through rock/a
    wall), applying again past the "You dig a pit" stage until the hole is
    through (you fall to the level below) or the passage opens; then wields
    your previous weapon again. Can't dig on stairs, altars, fountains, in
    Sokoban or through undiggable walls (the messages say so). Returns the
    messages. "You stop digging." (something came into view) with nothing
    but trivial monsters around just digs on; otherwise it wields your
    weapon again first and then pauses (call dig() again to go on)."""
    ctx.require_command("dig()")
    import contextlib
    from .combat import auto_fightable
    guard = ctx.monster_filter(lambda m: False) if ctx.monster_filter else contextlib.nullcontext()
    with guard:            # newcomers are judged below, after the weapon is back in hand
        return _dig(direction, tool, max_applies, auto_fightable)


def _dig(direction, tool, max_applies, auto_fightable):
    from nh.kernel import DEFAULT_BENIGN
    from .benign import BENIGN
    inv = inventory()
    if tool is None:
        t = next((i for i in inv if re.search(r"pick-axe|mattock", i["text"])), None)
        if t is None:
            raise RuntimeError("dig(): no pick-axe or mattock in the inventory")
        tool = t["letter"]
    weapon = next((i["letter"] for i in inv if _wielded(i["text"]) and i["letter"] != tool), None)
    welded = _welded(inv)
    if welded is not None and welded["letter"] != tool:
        raise RuntimeError(f"dig(): your weapon {welded['letter']} - {welded['text']} is CURSED, so it is welded to "
                           "your hand, and applying a pick-axe has to wield it: NetHack refuses. Dig with a wand "
                           "of digging instead (zap it: '>' down, or a direction), or uncurse the weapon first.")
    ldesc0 = ctx.last().status.ldesc
    ids0 = {m.get("id") for m in ctx.last().hostiles(7) if m.get("id") is not None}   # already known when you began
    routine = [re.compile(p) for p in _DIG_OK + [r"^You stop digging\.$"] + list(BENIGN)] + list(DEFAULT_BENIGN)
    msgs: list = []
    why = ""                       # something dig() must show you AFTER your weapon is back in hand
    for _ in range(max_applies):
        s = ctx.do("a", quiet=True)
        if s.state.kind != "object":
            if s.state.kind != "command":
                ctx.do("<Esc>", quiet=True)
            raise RuntimeError(f"dig(): expected the apply prompt, got {s.state.kind} {s.state.prompt!r}")
        s = ctx.do(tool, ok=_DIG_OK)
        msgs += s.messages
        if s.state.kind != "direction":
            if s.state.kind != "command":
                ctx.do("<Esc>", quiet=True)
            why = (f"no dig-direction prompt after applying {tool!r} ({s.state.kind} {s.state.prompt!r}; "
                   f"messages {s.messages})")
            break
        # quiet: the messages of the dig itself (and of the level you fall into) are looked at below, after
        # the weapon is back in hand (falling through the hole is the point: no level-change pause either)
        s = ctx.do(direction, ok=_DIG_OK + [r"^You stop digging\.$"], quiet=True,
                   expect=("level",) if direction == ">" else ())
        msgs += s.messages
        text = " ".join(s.messages)
        fell = s.status.ok and s.status.ldesc != ldesc0
        news = [m for m in s.messages if not any(p.search(m) for p in routine)]
        threats = ([m for m in s.hostiles(7) if not auto_fightable(m, s)
                    and (fell or m.get("id") not in ids0 or m.get("dist") == 1)] if s.state.kind == "command" else [])
        adjacent = s.adjacent_hostiles() if s.state.kind == "command" else []
        if threats or adjacent:
            why = ", ".join(f"{m.get('desc') or m['ch']} at ({m['x']},{m['y']})" for m in (threats or adjacent)[:3]) \
                  + " in view"
        if news:
            why = (why + "; " if why else "") + "messages: " + " | ".join(news[:4])
        if fell:
            if why:
                why = f"fell to {s.status.ldesc} — {why}"
            break                                   # fell through the hole
        if why:
            break
        if "You stop digging" in text:
            continue                                # something came and went: dig on
        if re.search(r"dig a hole through|make an opening|succeed in cutting away|too hard to dig|"
                     r"cannot|can't|here is too hard|The .* here is too hard|boulder falls apart|"
                     r"statue shatters", text):
            break
        if s.state.kind != "command":
            break
    if weapon and ctx.last().state.kind == "command":
        s = ctx.do("w" + weapon, quiet=True, ok=[r"^[a-zA-Z] - "])
        msgs += s.messages
    if why:
        done = next((m for m in msgs if re.search(r"^You dig a hole through|^You make an opening|^You succeed in "
                                                  r"cutting away|^The boulder falls apart|^The statue shatters", m)),
                    None)
        ctx.pause("dig(): " + why + (f" — your weapon ({weapon}) is wielded again" if weapon else "")
                  + (f"; the dig is DONE ({done})" if done else "; dig() again to go on digging"))
    return msgs


def tunnel(x: int, y: int, max_steps: int = 80, tool: str | None = None) -> dict:
    """Go to (x, y) in straight lines (across first, then up/down), digging through whatever rock, wall,
    boulder or statue is in the way with your pick-axe/mattock — kept in hand between digs (dig() re-wields
    your weapon after every wall: p2 shift 33 #120 crossed a maze 18-28 columns at a time with its own loop
    of step-or-dig). Your weapon is wielded again at the end. Stops at: the goal; a hostile next to you that
    auto_fightable() wouldn't fight; water, lava, a known trap or a monster on the next square; an undiggable
    wall ("too hard to dig in"); a level change; `max_steps` moves/digs. Returns {"reason", "at", "digs",
    "steps"}."""
    from .combat import auto_fightable
    from .mapview import DIR_KEY, is_walkable
    s = ctx.require_command("tunnel()")
    inv = inventory()
    if tool is None:
        t = next((i for i in inv if re.search(r"pick-axe|mattock", i["text"])), None)
        if t is None:
            raise RuntimeError("tunnel(): no pick-axe or mattock in the inventory")
        tool = t["letter"]
    weapon = next((i["letter"] for i in inv if _wielded(i["text"]) and i["letter"] != tool), None)
    ldesc0 = s.status.ldesc
    goal = (x, y)
    digs = steps = 0
    reason = "max_steps"
    ok = _DIG_OK + [r"^You stop digging\.$", r"^You swap places with ", r"^The door opens\.$",
                    r"^This (?:wall|drawbridge) is too hard to dig into\.$"]
    prev = s.hero
    try:
        for _ in range(max_steps):
            s = ctx.last()
            if s.state.kind != "command" or s.hero is None:
                reason = f"not at the command prompt ({s.state.kind}: {s.state.prompt!r})"
                break
            if s.status.ok and s.status.ldesc != ldesc0:
                reason = f"level changed: {ldesc0} -> {s.status.ldesc}"
                break
            if prev is not None and max(abs(s.hero[0] - prev[0]), abs(s.hero[1] - prev[1])) > 1:
                # one step or one dig can't move you 2+ squares: teleported (p1 shift 37 #263: moved from ~(74,12)
                # to (11,12) mid-tunnel — it would have dug ~50 squares from the wrong place)
                reason = f"TELEPORTED from {prev} to {s.hero} (teleportitis? a teleport trap?) — stopped"
                break
            prev = s.hero
            if s.hero == goal:
                reason = "arrived"
                break
            near = [m for m in s.adjacent_hostiles() if not auto_fightable(m, s)]
            if near:
                reason = "hostile next to you: " + ", ".join(f"{m.get('desc') or m['ch']} at ({m['x']},{m['y']})"
                                                             for m in near[:3])
                break
            hx, hy = s.hero
            dx = (x > hx) - (x < hx)
            dy = 0 if dx else (y > hy) - (y < hy)
            nxt = (hx + dx, hy + dy)
            ch = s.screen.at(*nxt)
            mon = next((m for m in s.monsters or [] if (m["x"], m["y"]) == nxt and not m.get("statue")), None)
            if mon is not None:
                if not mon.get("tame") and auto_fightable(mon, s):
                    from .combat import fight
                    fight(*nxt)
                    continue
                reason = f"{mon.get('desc') or mon['ch']} on the next square {nxt}"
                break
            if ch in "}^" or (ch == "#" and s.screen.color_at(*nxt) == 10):
                reason = f"{'water/lava' if ch == '}' else 'a trap' if ch == '^' else 'a gas cloud'} at {nxt}"
                break
            shops = (getattr(ctx.game, "shops", None) or {}).get(ctx.game.level_key(s.status), []) \
                if s.status.ok else []
            if getattr(s, "shop", "") or any(x1 - 1 <= nxt[0] <= x2 + 1 and y1 - 1 <= nxt[1] <= y2 + 1
                                             for x1, y1, x2, y2, *_ in shops):
                reason = f"a shop at {nxt}: digging its walls or floor angers the shopkeeper — go round it"
                break
            if is_walkable(s, *nxt, allow_monsters=False) or ch == "+":
                s = ctx.do(DIR_KEY[(dx, dy)], ok=ok)
                steps += 1
                if s.hero != (hx, hy) or any(m.startswith("The door opens") for m in s.messages):
                    continue
                if any(re.search(r"This door is locked|door is closed", m) for m in s.messages):
                    reason = f"a locked door at {nxt}: unlock(), kick it, or dig('{DIR_KEY[(dx, dy)]}') through it"
                    break
                if not any(m in ("It's solid stone.", "It's a wall.") for m in s.messages):
                    reason = f"the step {DIR_KEY[(dx, dy)]!r} to {nxt} didn't move you ({s.messages or 'no message'})"
                    break
            # rock, a wall, a boulder or a statue: dig (the pick stays in hand between digs)
            s = ctx.do("a", quiet=True)
            if s.state.kind != "object":
                if s.state.kind != "command":
                    ctx.do("<Esc>", quiet=True)
                reason = f"no apply prompt ({s.state.kind} {s.state.prompt!r})"
                break
            s = ctx.do(tool, ok=ok)
            if s.state.kind != "direction":
                if s.state.kind != "command":
                    ctx.do("<Esc>", quiet=True)
                reason = f"no dig direction prompt ({s.state.kind} {s.state.prompt!r}; {s.messages})"
                break
            s = ctx.do(DIR_KEY[(dx, dy)], ok=ok)
            digs += 1
            text = " ".join(s.messages)
            if re.search(r"too hard to dig|cannot|can't", text):
                reason = f"can't dig toward {nxt}: {text}"
                break
    finally:
        if weapon and digs and ctx.last().state.kind == "command":
            ctx.do("w" + weapon, quiet=True, ok=[r"^[a-zA-Z] - "])
    s = ctx.last()
    print(f"tunnel{goal}: {reason} at {s.hero} ({steps} step(s), {digs} dig(s))"
          + (f"; weapon {weapon} wielded again" if weapon else ""))
    return {"reason": reason, "at": s.hero, "digs": digs, "steps": steps}


def call_type(letter: str, name: str) -> list:
    """Name an object TYPE (#name -> "the type of an object in inventory"): call_type('x', 'polymorph') makes
    every marble wand show as "a wand called polymorph" — the way to remember an engrave-test verdict that
    didn't identify the wand (p4 shift 1 #2554: the "Call a marble wand:" prompt paused the script). No game
    time. Returns the messages."""
    ctx.require_command("call_type()")
    s = ctx.do("#name<CR>", quiet=True)
    if s.state.kind == "menu":
        s = ctx.do("o", quiet=True)            # "the type of an object in inventory"
    if s.state.kind != "object":
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        raise RuntimeError(f"call_type(): expected 'What do you want to call?', got {s.state.kind} "
                           f"{s.state.prompt!r}")
    s = ctx.do(letter, quiet=True, ok=[r"^Call "])
    if s.state.kind != "getlin":
        msgs = list(s.messages)
        if s.state.kind != "command":
            ctx.do("<Esc>", quiet=True)
        raise RuntimeError(f"call_type({letter!r}): no naming prompt ({s.state.kind} {s.state.prompt!r}; {msgs}) "
                           "— an identified type or one that can't be named")
    s = ctx.do(name + "<CR>", quiet=True)
    print(f"call_type({letter!r}, {name!r}): done")
    return s.messages


_BLADES: list | None = None
# artifacts show by their own name once identified ("the blessed +6 Excalibur"): their base weapon
_ARTI_BASE = {"Excalibur": "long sword", "Stormbringer": "runesword", "Cleaver": "battle-axe",
              "Grimtooth": "orcish dagger", "Orcrist": "elven broadsword", "Sting": "elven dagger",
              "Magicbane": "athame", "Frost Brand": "long sword", "Fire Brand": "long sword",
              "Dragonbane": "broadsword", "Demonbane": "long sword", "Werebane": "silver saber",
              "Grayswandir": "silver saber", "Giantslayer": "long sword", "Vorpal Blade": "long sword",
              "Snickersnee": "katana", "Sunsword": "long sword", "Tsurugi of Muramasa": "tsurugi"}


_ARTIFACT_BLADE = re.compile(r"\b(?:" + "|".join(_ARTI_BASE) + r")\b")


def blade_chance(text: str) -> int | None:
    """#force with this weapon: its chance per turn, in percent, to pry a box's lock open — lock.c doforce():
    twice the weapon's large-monster damage (dagger 6%, long sword 24%) — when it is a BLADE (the dagger..saber
    skills, axes included, not a pick-axe/mattock); None for anything else (blunt weapons bash, and can smash
    the box and its potions)."""
    global _BLADES
    if _BLADES is None:
        import json
        from pathlib import Path
        import nh
        try:
            objs = json.loads((Path(nh.__file__).parent / "data" / "objects.json").read_text())["objects"]
        except Exception:  # noqa: BLE001
            objs = []
        found = {}
        for o in objs:
            r = o.get("raw") or {}
            if r.get("oc_class") == 2 and 1 <= (r.get("oc_subtyp") or 0) <= 10 and r.get("oc_subtyp") != 4:
                for n in (o.get("name"), o.get("appearance")):
                    if n:
                        found[n.lower()] = r.get("oc_wldam") or 0
        _BLADES = sorted(found.items(), key=lambda p: -len(p[0]))
    t = text or ""
    if re.search(r"\bpick-axe|\bmattock|\bbroad pick\b", t, re.I):
        return None                    # lock.c is_pick(): digging tools bash, they don't pry
    for arti, base in _ARTI_BASE.items():
        if re.search(rf"\b{arti}\b", t):
            t = base
            break
    t = t.lower()
    for name, ldam in _BLADES:
        if re.search(rf"\b{re.escape(name)}(?:e?s)?\b", t):
            return 2 * ldam
    return None


_FORCE_OK = [r"^You force .* into a crack and pry", r"^You succeed in forcing the lock", r"broke!$",
             r"^You give up your attempt to force the lock", r"^You resume your attempt to force the lock",
             r"^There is .* here, but its lock is already", r"^You decide not to force the issue",
             r"^[a-zA-Z] - "]


def force_box(blade: str | None = None, allow_main: bool = False, tries: int = 3) -> dict:
    """#force open the locked box/chest you stand on with a BLADE, prying (lock.c: each turn succeeds with
    twice the blade's large-monster damage in percent — a dagger 6%, a long sword 24%; the attempt gives up
    after 50 turns and is retried up to `tries` times). A +0 blade breaks 0.7% of the prying turns, less
    when enchanted; an ARTIFACT only 1% as often (obj_resists: Excalibur +6 about once in 100,000 turns), and
    a cursed one never. Which blade: `blade` (a letter) if given; else your wielded weapon when it is an
    artifact blade; else a spare blade whose BUC you know is uncursed/blessed (a cursed one would WELD to
    your hand), the fastest first — wielded for the job, and your weapon wielded again at the end (in a
    finally: also when it stops early); else your own non-artifact blade only with allow_main=True (about 3%
    per box to lose it). Blunt weapons are never used (bashing can destroy the box and its potions). A
    trapped box doesn't go off from forcing, only when opened (check_box() first). Returns {"reason", "blade",
    "turns", "messages"}; reason: "forced", "not locked", "broke", "gave up", "stopped" or "no box"."""
    s = ctx.require_command("force_box()")
    inv = inventory()
    wield = next((i for i in inv if _wielded(i["text"])), None)
    pick = None
    if blade is not None:
        pick = next((i for i in inv if i["letter"] == blade), None)
        if pick is None or not blade_chance(pick["text"]):
            raise RuntimeError(f"force_box(): {blade!r} is not a blade in your pack "
                               f"({pick['text'] if pick else 'no such letter'})")
    elif wield is not None and _ARTIFACT_BLADE.search(wield["text"]) and blade_chance(wield["text"]):
        pick = wield
    else:
        spares = [i for i in inv if i is not wield and i["class"].startswith("Weapons") and blade_chance(i["text"])
                  and re.search(r"\b(?:uncursed|blessed)\b", i["text"]) and not re.search(r"\btwo-handed\b|"
                                                                                           r"\btsurugi\b", i["text"])]
        if spares:
            pick = max(spares, key=lambda i: blade_chance(i["text"]))
        elif wield is not None and blade_chance(wield["text"]) and allow_main:
            pick = wield
        else:
            unknown = [f"{i['letter']} - {i['text']}" for i in inv if i is not wield
                       and i["class"].startswith("Weapons") and blade_chance(i["text"])
                       and not re.search(r"\b(?:un)?cursed\b|\bblessed\b", i["text"])]
            raise RuntimeError(
                "force_box(): no blade to pry with — " + (
                    f"the spare blades {unknown[:3]} have UNKNOWN BUC (a cursed one welds to your hand: altar-test "
                    "first, or force_box(blade=letter) to take the risk)" if unknown else
                    "no spare dagger/knife/short sword known uncursed")
                + (f"; your own {wield['text']} works with allow_main=True (about 3% per box to break it)"
                   if wield is not None and blade_chance(wield["text"]) else "")
                + "; or kick it (dokick: 1 in 5 kicks breaks the lock, and each kick may shatter potions inside)")
    t0 = s.status.turn if s.status.ok else None
    swapped = wield is None or pick["letter"] != wield["letter"]
    msgs: list = []
    reason = "stopped"
    try:
        if swapped:
            s = ctx.do("w" + pick["letter"], ok=[r"^[a-zA-Z] - "])
            msgs += s.messages
            if not any(m.startswith(f"{pick['letter']} - ") for m in s.messages):
                raise RuntimeError(f"force_box(): couldn't wield {pick['text']}: {s.messages}")
        for _ in range(tries):
            s = ctx.do("#force<CR>", quiet=True, ok=_FORCE_OK)
            msgs += s.messages
            for _q in range(6):
                p = s.state.prompt or ""
                if s.state.kind in ("yn", "ynq") and "force its lock" in p:
                    s = ctx.do("y", ok=_FORCE_OK)
                    msgs += s.messages
                elif s.state.kind != "command":
                    ctx.do("<Esc>", quiet=True)
                    s = ctx.last()
                    break
                else:
                    break
            text = " | ".join(msgs)
            if "You succeed in forcing the lock" in text:
                reason = "forced"
            elif re.search(r"but its lock is already", text):
                reason = "not locked"
            elif re.search(r"decide not to force the issue", text):
                reason = "no box"
            elif re.search(r"broke!", text):
                reason = "broke"
            elif "give up your attempt" in text and s.state.kind == "command":
                msgs.append("(gave up after 50 turns: trying again)")
                reason = "gave up"
                continue
            break
    finally:
        if swapped and wield is not None and ctx.last().state.kind == "command":
            ctx.do("w" + wield["letter"], quiet=True, ok=[r"^[a-zA-Z] - "])
    now = ctx.last()
    turns = (now.status.turn - t0) if t0 is not None and now.status.ok and now.status.turn is not None else None
    name = re.sub(r"\s*\((?:weapon in \w+|alternate weapon; not wielded|in quiver[^)]*)\)", "", pick["text"])
    print(f"force_box(): {reason} with {name}" + (f" in {turns} turns" if turns is not None else "")
          + (f"; your weapon ({wield['letter']}) is wielded again" if swapped and wield is not None else "")
          + (" — loot_all() opens it now" if reason in ("forced", "not locked") else ""))
    return {"reason": reason, "blade": name, "turns": turns, "messages": msgs}


_KEYS = re.compile(r"skeleton key|\bkey\b|lock pick|credit card|Master Key of Thievery", re.I)
_UNLOCK_OK = [r"^You succeed in (?:unlocking|picking)", r"^You stop (?:unlocking|picking)",
              r"^Hmmm, it turns out to be locked", r"^It is locked", r"^There is .* here; (?:un)?lock"]


def unlock(x: int | None = None, y: int | None = None, tool: str | None = None, tries: int = 4) -> list:
    """Unlock the locked box/chest under you (no x, y) or the locked door
    at the adjacent (x, y) with your skeleton key / lock pick / credit card
    (found in the inventory unless `tool` is given): applies it, answers the
    direction ('.' = here), says y to "unlock it?" and never to "lock it?".
    It takes a few turns and a monster can interrupt it ("You stop
    unlocking"): retried up to `tries` times. A trapped box can go off, and
    a BOOBY-TRAPPED DOOR EXPLODES the moment its lock gives (lock.c
    picklock: stunned, some HP, everything near wakes; the door is gone) —
    unlock doors at full HP. Never on a shop door. Returns the messages."""
    ctx.require_command("unlock()")
    if tool is None:
        t = next((i for i in inventory() if _KEYS.search(i["text"])), None)
        if t is None:
            raise RuntimeError("unlock(): no key, lock pick or credit card in the inventory — force_box() (a box "
                               "under you) or kick_door(x, y)")
        tool = t["letter"]
    s = ctx.last()
    if x is None:
        dkey = "."
    else:
        from .mapview import DIR_KEY
        dkey = DIR_KEY.get((x - s.hero[0], y - s.hero[1])) if s.hero else None
        if dkey is None:
            raise RuntimeError(f"unlock(): {(x, y)} is not next to you at {s.hero}")
    msgs: list = []
    for _ in range(tries):
        s = ctx.do("a", quiet=True)
        if s.state.kind != "object":
            if s.state.kind != "command":
                ctx.do("<Esc>", quiet=True)
            raise RuntimeError(f"unlock(): expected the apply prompt, got {s.state.kind} {s.state.prompt!r}")
        s = ctx.do(tool, quiet=True)
        if s.state.kind != "direction":
            if s.state.kind != "command":
                ctx.do("<Esc>", quiet=True)
            raise RuntimeError(f"unlock(): no direction prompt after applying {tool!r} ({s.state.kind} "
                               f"{s.state.prompt!r}; {s.messages})")
        s = ctx.do(dkey, ok=_UNLOCK_OK)
        msgs += s.messages
        answered = False
        for _q in range(6):
            p = s.state.prompt or ""
            if s.state.kind != "yn":
                break
            if re.search(r"\bunlock (?:it|its lock)\?|^Unlock it\?|pick its lock\?", p):
                s = ctx.do("y", ok=_UNLOCK_OK)
                answered = True
            elif re.search(r"\block (?:it|its lock)\?|^Lock it\?|fix", p):
                s = ctx.do("n", ok=_UNLOCK_OK)         # not locked (or broken): next box / done
            else:
                ctx.do("<Esc>", quiet=True)
                raise RuntimeError(f"unlock(): unexpected question {p!r}")
            msgs += s.messages
        text = " ".join(msgs)
        if re.search(r"You succeed in (?:unlocking|picking)", text) and x is not None:
            ctx.game.locked_doors.get(ctx.game.level_key(ctx.last().status), set()).discard((x, y))
        if re.search(r"You succeed in (?:unlocking|picking)", text) or not answered:
            break
    print("unlock(): " + (" | ".join(msgs[-3:]) or "nothing to unlock here"))
    if any("KABOOM" in m for m in msgs):
        print("!! unlock(): the door was booby-trapped — the explosion WOKE everything within ~15 squares "
              "(a zoo/throne room next door is now awake)")
    elif x is not None and any(re.search(r"You succeed in (?:unlocking|picking)", m) for m in msgs):
        # lock.c picklock(): a trapped door goes off the moment its lock gives (p3 shift 16 #930) — this one
        # didn't, so it isn't trapped
        print("unlock(): the door wasn't booby-trapped (a trapped door explodes as its lock gives) — opening it "
              "is safe")
    return msgs


def check_box(times: int = 3) -> str:
    """Check the container on your square for traps with #untrap (1 turn per check; trap.c untrap(): each
    check finds a real trap with rn2(31 - XL) < 10 — 62% at XL15, so 3 checks ~95%). NEVER disarms (a
    failed disarm sets it off: explosion, poison needle, gas, shock, paralysis): answers no. Returns
    'trapped' (leave it shut — or #force/kick it open from a safe spot, knowing the risk), 'clear' (no trap
    found in `times` checks), or 'no box' (no container here)."""
    ctx.require_command("check_box()")
    ok = [r"^You find no traps on ", r"^You find a trap on ", r"^You know of no traps here",
          r"^You find no other traps here", r"^You cannot disable"]
    for i in range(times):
        s = ctx.do("#untrap<CR>", quiet=True)
        if s.state.kind == "direction":
            s = ctx.do(".", quiet=True, ok=ok)
        seen = list(s.messages)
        for _ in range(4):
            p = s.state.prompt or ""
            if s.state.kind in ("yn", "ynq") and "Check it for traps" in p:
                s = ctx.do("y", quiet=True, ok=ok)
            elif s.state.kind in ("yn", "ynq") and "Disarm it" in p:
                s = ctx.do("n", quiet=True, ok=ok)
            elif s.state.kind != "command":
                ctx.do("<Esc>", quiet=True)
                s = ctx.last()
                break
            else:
                break
            seen += s.messages
        text = " ".join(seen)
        if "You find a trap on" in text:
            print(f"check_box: TRAPPED ({text.strip()}) — left shut (a disarm attempt fails often and sets it off)")
            return "trapped"
        if "You find no traps on" not in text:
            print(f"check_box: no container here? ({text.strip() or s.state.kind})")
            return "no box"
    print(f"check_box: no trap found in {times} check(s)")
    return "clear"


def loot_all(unlock_with_key: bool = True, take_gray_stones: bool = False, check_traps: int = 0) -> list:
    """Take everything out of the (single) container on your square with
    #loot: confirms, picks "take something out" in the pick-one "Do what?"
    menu, then every item — EXCEPT unknown gray stones (a chest's loadstone
    is generated cursed: once in your pack it can't be dropped): those stay
    inside and it says how to test them (#tip the box, kick the stone;
    take_gray_stones=True to take them anyway). Returns the messages. A
    locked box: unlocked with your key/lock pick/credit card first when you
    carry one (unlock(); unlock_with_key=False to skip), else it says so
    (force_box() pries it open with a blade). Pauses on anything else."""
    s = ctx.require_command("loot_all()")
    if s.status.ok and "Lev" in s.status.conditions:
        raise RuntimeError("loot_all(): you are levitating — you can't reach the floor; remove the levitation "
                           "first (and mind water/traps where you land)")
    if check_traps and check_box(check_traps) == "trapped":
        return ["loot_all: the container here is TRAPPED — not opened (check_box)"]
    msgs = _loot_all_once(take_gray_stones)
    if unlock_with_key and any(re.search(r"turns out to be locked|^It is locked", m) for m in msgs) \
            and any(_KEYS.search(i["text"]) for i in inventory()):
        msgs += unlock()
        if ctx.last().state.kind == "command":
            msgs += _loot_all_once(take_gray_stones)
    return msgs


_GRAY_STONE = re.compile(r"\bgr[ae]y stones?\b")


def _loot_all_once(take_gray_stones: bool = False) -> list:
    enc0 = ctx.last().status.encumbrance or ""
    s = ctx.do("#loot<CR>", quiet=True)
    msgs = list(s.messages)
    left: list = []
    for _ in range(10):
        k, p = s.state.kind, (s.state.prompt or "")
        if k == "command":
            break
        if k == "yn" and "loot it?" in p and "bag of tricks" in p:
            # (live shift 5: #loot of a floor bag of tricks bites — pickup.c: it isn't a container; -10 HP)
            s = ctx.do("n", quiet=True)
            msgs.append("(left the bag of tricks alone: #loot makes it bite you; apply it only to make a monster)")
        elif k == "yn" and "loot it?" in p:
            s = ctx.do("y", quiet=True)
        elif k == "menu" and "Do what" in p:
            opt = [it for it in s.state.menu.selectable() if "take something out" in it.text]
            if not opt:
                ctx.do("<Esc>", quiet=True)
                msgs.append("(nothing to take out)")
                break
            s = ctx.do(opt[0].letter, quiet=True)
        elif k == "menu":
            items = s.state.menu.selectable()
            auto = [it for it in items if "Auto-select every item" in it.text]
            if auto:
                # the class menu: "All types" (or the one class there is) -> the item list, where unknown
                # gray stones can be left out ("Auto-select every item" would take them unseen)
                kinds = [it for it in items if it.text.startswith("All types")] or \
                        [it for it in items if "Auto-select" not in it.text and not
                         re.match(r"^(?:Unpaid|Items known|Items of unknown|Unknown)", it.text)][:1]
                if not kinds:
                    ctx.do("<Esc>", quiet=True)
                    msgs.append("(loot_all: no item class to pick)")
                    break
                s = ctx.do(kinds[0].letter, quiet=True)
                s = ctx.do("<CR>", quiet=True)
            else:                                   # an item list: select every item on every page
                for _page in range(8):
                    for it in s.state.menu.selectable():
                        if it.selected:
                            continue
                        if _GRAY_STONE.search(it.text) and not take_gray_stones:
                            left.append(it.text)
                            continue
                        s = ctx.do(it.letter, quiet=True)
                    if s.state.menu and s.state.menu.page < s.state.menu.pages:
                        s = ctx.do(">", quiet=True)
                    else:
                        break
                s = ctx.do("<CR>", quiet=True, expect=_TAKE)
        else:
            ctx.pause(f"loot_all(): unexpected {k} {p!r}")
            s = ctx.last()
        msgs += s.messages
    print("loot_all(): " + " | ".join(msgs[-6:]))
    if left:
        print(f"!! loot_all(): left inside: {'; '.join(left)} — an unknown gray stone may be a LOADSTONE (a "
              "chest's is generated cursed: in your pack it can't be dropped, 500 weight). To test: #tip the "
              "container (its contents spill on the floor), step aside and kick the stone — a loadstone doesn't "
              "budge ('Thump!'); a luckstone/touchstone/flint slides. loot_all(take_gray_stones=True) takes them.")
    _warn_full(msgs, "loot_all")
    _enc_note("loot_all", enc0)
    return msgs
