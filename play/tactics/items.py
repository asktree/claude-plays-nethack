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


def inventory():
    """Return the hero's inventory as a list of {letter, text, class, buc}."""
    ctx.require_command("inventory()")
    with ctx.no_monster_pauses():
        s = ctx.do("i", quiet=True)
        items = _parse_menu_pages(s)[0] if s.state.kind == "menu" else None
    if items is not None:
        ctx.game.wielded = next((it["text"] for it in items if _wielded(it["text"])), "")
        ctx.game.wielded_class = next((it["class"] for it in items if _wielded(it["text"])), "")
        ctx.game.gloves = next((it["text"] for it in items if "(being worn)" in it["text"]
                                and re.search(r"\b(?:gloves|gauntlets)\b", it["text"])), "")
        ctx.game.reflecting = any("(being worn)" in it["text"] and _REFLECT.search(it["text"]) for it in items)
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
        ctx.game.blindfolded = any(re.search(r"\b(?:blindfold|towel)\b.*\(being worn\)", it["text"]) for it in items)
        return items
    # "Not carrying anything." or a tiny inventory shown on the message line
    return []


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


def here():
    """What's on the floor here (':' look). Takes no game time."""
    ctx.require_command("here()")
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
    (r"dries up|reduces to a trickle", "fountain dried up"),
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


def bag_put(bag: str, letters: str) -> list:
    """Put the inventory items `letters` (e.g. 'mq') into the carried
    container `bag`, one "stash one item" at a time. Returns the messages."""
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
    return msgs


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


def eat(letter: str | None = None) -> list:
    """Eat inventory item `letter`, or (letter=None) the food on the floor
    here. NetHack first offers each floor corpse ("There is a jackal corpse
    here; eat it?"): with a letter those are declined. The harness guards
    still apply (deadly/old corpses, tins, Satiated). Returns the messages."""
    ctx.require_command("eat()")
    s = ctx.do("e", quiet=True)
    msgs = list(s.messages)
    for _ in range(8):
        k, p = s.state.kind, s.state.prompt or ""
        if k == "command":
            break
        if k == "yn" and "here; eat" in p:
            s = ctx.do("y" if letter is None else "n", quiet=True)
        elif k == "object":
            if letter is None:
                ctx.do("<Esc>", quiet=True)
                raise RuntimeError("eat(): no food on the floor here — pass an inventory letter")
            s = ctx.do(letter, quiet=True)
        elif k in ("yn", "getlin") and "Continue eating" in p:
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


def pickup(pattern: str | None = None) -> list:
    """Pick up the objects here whose text matches `pattern` (regex,
    case-insensitive), or everything if None. Looks first (no game time), so
    a lone object that doesn't match is left alone. Returns the messages."""
    ctx.require_command("pickup()")
    look = here()
    if "You see no objects here" in look or not look:
        print(f"pickup({pattern!r}): there are no objects here" + (f" ({look})" if look else ""))
        return []
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
    enc0 = ctx.last().status.encumbrance or ""
    s = ctx.do(",", quiet=True, expect=_TAKE)
    msgs = list(s.messages)
    if s.state.kind == "menu":
        chosen, seen = 0, []
        for _page in range(8):
            for it in s.state.menu.selectable():
                seen.append(it.text)
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
    if s.state.kind != "command":
        ctx.pause(f"pickup(): unexpected {s.state.kind} {s.state.prompt!r}")
    _warn_full(msgs, "pickup")
    _enc_note("pickup", enc0)
    return msgs


_DIG_OK = [r"^You (?:are )?now wield", r"^You (?:start|continue) digging", r"^You dig a pit in the ",
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
    messages. A monster interrupting pauses as usual; call dig() again."""
    ctx.require_command("dig()")
    inv = inventory()
    if tool is None:
        t = next((i for i in inv if re.search(r"pick-axe|mattock", i["text"])), None)
        if t is None:
            raise RuntimeError("dig(): no pick-axe or mattock in the inventory")
        tool = t["letter"]
    weapon = next((i["letter"] for i in inv if _wielded(i["text"]) and i["letter"] != tool), None)
    ldesc0 = ctx.last().status.ldesc
    msgs: list = []
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
            ctx.pause(f"dig(): no dig-direction prompt after applying {tool!r} ({s.state.kind} {s.state.prompt!r}; "
                      f"messages {s.messages})")
            break
        # falling through the hole is the point: no level-change pause before the re-wield below
        # (new monsters there still pause)
        s = ctx.do(direction, ok=_DIG_OK, expect=("level",) if direction == ">" else ())
        msgs += s.messages
        text = " ".join(s.messages)
        if s.status.ok and s.status.ldesc != ldesc0:
            break                                   # fell through the hole
        if re.search(r"dig a hole through|make an opening|succeed in cutting away|too hard to dig|"
                     r"cannot|can't|here is too hard|The .* here is too hard|boulder falls apart|"
                     r"statue shatters", text):
            break
        if s.state.kind != "command":
            break
    if weapon and ctx.last().state.kind == "command":
        s = ctx.do("w" + weapon, quiet=True, ok=[r"^[a-zA-Z] - "])
        msgs += s.messages
    return msgs


_KEYS = re.compile(r"skeleton key|\bkey\b|lock pick|credit card|Master Key of Thievery", re.I)
_UNLOCK_OK = [r"^You succeed in (?:unlocking|picking)", r"^You stop (?:unlocking|picking)",
              r"^Hmmm, it turns out to be locked", r"^It is locked", r"^There is .* here; (?:un)?lock"]


def unlock(x: int | None = None, y: int | None = None, tool: str | None = None, tries: int = 4) -> list:
    """Unlock the locked box/chest under you (no x, y) or the locked door
    at the adjacent (x, y) with your skeleton key / lock pick / credit card
    (found in the inventory unless `tool` is given): applies it, answers the
    direction ('.' = here), says y to "unlock it?" and never to "lock it?".
    It takes a few turns and a monster can interrupt it ("You stop
    unlocking"): retried up to `tries` times. A trapped box can go off.
    Never on a shop door. Returns the messages."""
    ctx.require_command("unlock()")
    if tool is None:
        t = next((i for i in inventory() if _KEYS.search(i["text"])), None)
        if t is None:
            raise RuntimeError("unlock(): no key, lock pick or credit card in the inventory — kick or #force")
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
        print("unlock(): note — a booby-trapped door can still explode when you OPEN it (stunned, woken "
              "neighbours): open it at full HP")
    return msgs


def loot_all(unlock_with_key: bool = True, take_gray_stones: bool = False) -> list:
    """Take everything out of the (single) container on your square with
    #loot: confirms, picks "take something out" in the pick-one "Do what?"
    menu, then every item — EXCEPT unknown gray stones (a chest's loadstone
    is generated cursed: once in your pack it can't be dropped): those stay
    inside and it says how to test them (#tip the box, kick the stone;
    take_gray_stones=True to take them anyway). Returns the messages. A
    locked box: unlocked with your key/lock pick/credit card first when you
    carry one (unlock(); unlock_with_key=False to skip), else it says so
    (kick it or #force with a blade). Pauses on anything else."""
    s = ctx.require_command("loot_all()")
    if s.status.ok and "Lev" in s.status.conditions:
        raise RuntimeError("loot_all(): you are levitating — you can't reach the floor; remove the levitation "
                           "first (and mind water/traps where you land)")
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
        if k == "yn" and "loot it?" in p:
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
