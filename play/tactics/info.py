"""Knowledge lookups for the player (no game time, no side effects):
monster stats + danger notes, corpse safety, object facts, price
identification candidates, and wiki grep."""

from __future__ import annotations

import json
import re
import subprocess
from functools import lru_cache
from pathlib import Path

from nh.danger import base_name, monster_summary
from nh.data.corpses import corpse_verdict

REPO = Path(__file__).resolve().parents[2]


def mon(name: str) -> str:
    """Stats and danger note for a monster: mon('soldier ant')."""
    return monster_summary(name)


def corpse(name: str, age: int = 0, poison_res: bool = False, **kw) -> str:
    """Is it safe for us (dwarf Valkyrie) to eat this corpse? age = turns since
    it died (0 if you just killed it). Extra kwargs go to corpse_verdict
    (e.g. has_stoning_res=True, buc='cursed')."""
    v = corpse_verdict(base_name(name), hero_race="dwarf", hero_role="Valkyrie", age_turns=age,
                       has_poison_res=poison_res, **kw)
    verdict = getattr(v.verdict, "value", v.verdict)
    out = f"{name}: {verdict}"
    if v.reasons:
        out += " — " + "; ".join(v.reasons)
    if v.benefits:
        out += " | benefits: " + "; ".join(str(b) for b in v.benefits)
    if v.notes:
        out += " | notes: " + "; ".join(str(n) for n in v.notes)
    return out


@lru_cache(maxsize=1)
def _objects():
    data = json.loads((REPO / "src" / "nh" / "data" / "objects.json").read_text())
    return data["objects"]


def obj(name: str) -> str:
    """Facts about an object type by (partial) name: obj('speed boots')."""
    rx = re.compile(re.escape(name), re.I)
    hits = [o for o in _objects() if o.get("name") and rx.search(o["name"])]
    if not hits:
        return f"no object matching {name!r}"
    out = []
    for o in hits[:8]:
        if o.get("shuffle_group"):
            desc = f" (appearance RANDOMIZED per game, group '{o['shuffle_group']}')"
        else:
            desc = f" (unidentified: {o['appearance']})" if o.get("appearance") else ""
        out.append(f"{o['name']}{desc}: class {o.get('class')}, cost {o.get('cost')}, wt {o.get('weight')}")
    return "\n".join(out)


def price_candidates(klass: str, base_price: int) -> list[str]:
    """Object names of a class ('SCROLL_CLASS', 'POTION_CLASS', 'RING_CLASS',
    'WAND_CLASS', 'AMULET_CLASS', 'SPBOOK_CLASS', 'TOOL_CLASS'...) with this
    base price. Compute the base price from the shop's quote first (see
    knowledge/wiki/Price_identification.txt)."""
    return [o["name"] for o in _objects() if o.get("class") == klass and o.get("cost") == base_price
            and o.get("name")]


def wiki(pattern: str, max_lines: int = 40) -> str:
    """grep the offline wiki (knowledge/wiki) — returns matching lines with file names."""
    d = REPO / "knowledge" / "wiki"
    if not d.exists():
        return "(knowledge/wiki not fetched yet)"
    p = subprocess.run(["grep", "-r", "-i", "-n", "-m", "3", pattern, str(d)], capture_output=True, text=True)
    lines = p.stdout.splitlines()
    lines = [l.replace(str(d) + "/", "") for l in lines]
    return "\n".join(lines[:max_lines]) or "(no matches)"


def wiki_page(title: str, max_chars: int = 6000) -> str:
    """Read an offline wiki page by title ('Floating eye', 'Sokoban Level 1a')."""
    d = REPO / "knowledge" / "wiki"
    f = d / (title.replace(" ", "_") + ".txt")
    if not f.exists():
        cands = sorted(d.glob(f"*{title.replace(' ', '_')}*.txt"))[:10]
        return f"no page {title!r}; similar: {[c.stem for c in cands]}"
    t = f.read_text()
    return t[:max_chars] + ("\n...[truncated; read the file for more]" if len(t) > max_chars else "")


def threat(desc: str) -> str:
    """'trivial' | 'normal' | 'dangerous' for a monster vs you right now
    (difficulty vs XL, worst-case hit vs HP, danger notes, deadly passives):
    threat('newt') -> 'trivial'. Use it to decide what to ignore."""
    from nh.danger import threat_level
    from . import ctx
    st = ctx.last().status
    return threat_level(desc, st.xl if st.ok else None, st.hp if st.ok else None,
                        getattr(ctx.game, "intrinsics", ()))


def last_seen(name: str | None = None) -> list[dict]:
    """Monsters seen recently on this level that are out of view now, newest
    first: [{desc, x, y, turn, ago}]. last_seen('gas spore') filters by name."""
    from . import ctx
    tr = getattr(ctx.game, "tracker", None)
    if tr is None:
        return []
    turn = ctx.last().status.turn or 0
    out = []
    for r in tr.gone(turn):
        if name and name not in r.get("desc", ""):
            continue
        out.append({"desc": r.get("desc"), "x": r["x"], "y": r["y"], "turn": r.get("turn"),
                    "ago": turn - (r.get("turn") or turn)})
    return out


def _scale(tmp: int, mult: int, div: int) -> int:
    """shk.c rounding: ((tmp * mult * 10) / div + 5) / 10, never 0 from nonzero."""
    tmp *= mult
    if div > 1:
        tmp = (tmp * 10 // div + 5) // 10
    return max(tmp, 1) if tmp else tmp


def _buy_prices(base: int, cha: int, dunce: bool = False) -> set:
    """Possible 'For you, N zorkmids' unit prices for an UNidentified item of
    this base price (shk.c get_cost): 1 in 4 items carry a fixed +1/3."""
    out = set()
    for surcharge in (False, True):
        mult, div = 1, 1
        if surcharge:
            mult, div = mult * 4, div * 3
        if dunce:
            mult, div = mult * 4, div * 3
        if cha > 18:
            div *= 2
        elif cha == 18:
            mult, div = mult * 2, div * 3
        elif cha >= 16:
            mult, div = mult * 3, div * 4
        elif cha <= 5:
            mult *= 2
        elif cha <= 7:
            mult, div = mult * 3, div * 2
        elif cha <= 10:
            mult, div = mult * 4, div * 3
        out.add(_scale(base or 5, mult, div))
    return out


def _sell_offers(base: int, dunce: bool = False, rate: str | None = None) -> set:
    """Possible sell offers for one UNidentified item (shk.c set_cost): half
    the base price, or 3/8 of it at a shopkeeper who lowballs unidentified
    things (1 in 4 shopkeepers, m_id % 4 == 0 — always the same one).
    rate: "normal" / "low" once that shopkeeper's habit is known."""
    div = 3 if dunce else 2
    if base <= 1:
        return {base}
    normal, low = _scale(base, 1, div), _scale(base, 3, div * 4)
    return {normal} if rate == "normal" else {low} if rate == "low" else {normal, low}


def _shopkeeper(shk: str | None = None) -> str | None:
    """The shopkeeper whose shop you stand in ("Wonotobo's general store" -> "Wonotobo")."""
    from . import ctx
    if shk:
        return shk
    if ctx.game is None:
        return None              # no game attached (offline use): nothing to remember
    shop = getattr(ctx.last(), "shop", "") or ""
    return shop.split("'s ")[0] if "'s " in shop else None


def shk_rates() -> dict:
    """{shopkeeper: "normal" | "low"} learned from sell offers for unidentified items."""
    from . import ctx
    if ctx.game is None:
        return {}
    r = getattr(ctx.game, "shk_rates", None)
    if r is None:
        r = ctx.game.shk_rates = {}
    return r


def price_id(klass: str, buy: int | None = None, sell: int | None = None, cha: int | None = None,
             dunce: bool = False, exclude_known: bool = True, shk: str | None = None) -> list:
    """Which unidentified items of a class match a shop price? klass like
    'SCROLL_CLASS', 'POTION_CLASS', 'RING_CLASS', 'WAND_CLASS',
    'AMULET_CLASS', 'SPBOOK_CLASS'. buy = the unit price quoted to you
    ("For you, 133 zorkmids"), sell = the offer for ONE item. cha defaults
    to your Charisma from the status line. Returns [(name, base price)]
    consistent with every number given (formulas from shk.c). Types you have
    already identified (the discoveries list, read at the command prompt)
    are left out unless exclude_known=False. A sell offer also teaches the
    harness whether this shopkeeper lowballs unidentified items (3/8 instead
    of 1/2 of the base: fixed per shopkeeper) when only one rate fits; later
    offers from the same one then give one answer (shk= names the
    shopkeeper when you aren't standing in the shop)."""
    from . import ctx
    if cha is None:
        st = ctx.last().status
        cha = st.ch if st.ok else 10
    known: set = set()
    if exclude_known and ctx.game is not None:
        try:
            if ctx.last().state.kind == "command":
                from .items import discoveries
                known = {n for n, _look in discoveries() if " called " not in n}
        except Exception:  # noqa: BLE001 — the price list still works without it
            known = set()
    who = _shopkeeper(shk) if sell is not None else None
    rate = shk_rates().get(who) if who else None
    out, fits = [], {"normal": 0, "low": 0}
    for o in _objects():
        if o.get("class") != klass or not o.get("name"):
            continue
        if o.get("full_name") in known or o.get("name") in known:
            continue
        base = int(o.get("cost") or 0)
        if buy is not None and buy not in _buy_prices(base, cha, dunce):
            continue
        if sell is not None:
            if sell not in _sell_offers(base, dunce, rate):
                continue
            for r in ("normal", "low"):
                fits[r] += sell in _sell_offers(base, dunce, r)
        out.append((o["name"], base))
    if who and sell is not None and rate is None and out and (fits["normal"] == 0) != (fits["low"] == 0):
        learned = "low" if fits["low"] else "normal"
        shk_rates()[who] = learned
        print(f"price_id: {who} " + ("LOWBALLS unidentified items (offers 3/8 of the base, not 1/2)" if learned ==
                                     "low" else "pays the normal half of the base") + " — remembered for later offers")
    return sorted(out, key=lambda x: (x[1], x[0]))


def overview() -> str:
    """The dungeon overview (^O, no game time) as text: every level you have
    seen with its notes — branch stairs ("Stairs down to the Gnomish Mines"),
    shops, altars, fountains, "A primitive area." (the Rogue level)..."""
    from . import ctx
    ctx.require_command("overview()")
    with ctx.no_monster_pauses():
        s = ctx.do("<C-o>", quiet=True)
    text = "\n".join(s.messages)
    s.messages = []            # the text is the return value, not a message to show again
    return text
