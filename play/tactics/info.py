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
    return threat_level(desc, st.xl if st.ok else None, st.hp if st.ok else None)


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
