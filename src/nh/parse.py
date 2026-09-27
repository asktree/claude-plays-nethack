"""Interpret a tty NetHack 3.6 screen: state, prompts, menus, status lines, map.

Layout (80x24 tty): row 0 = message line, rows 1..21 = map, rows 22..23 =
status lines. Coordinates everywhere are screen (x=col, y=row). NetHack's
internal map coordinates are (x+1, y-1) of these.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .screen import Screen

MAP_TOP = 1
MAP_BOTTOM = 21          # inclusive
MAP_WIDTH = 80

MORE = "--More--"

# ---------------------------------------------------------------------------
# status lines


HUNGER = ("Satiated", "Hungry", "Weak", "Fainting", "Fainted")
ENCUMBRANCE = ("Burdened", "Stressed", "Strained", "Overtaxed", "Overloaded")
CONDITIONS = ("Stone", "Slime", "Strngl", "FoodPois", "TermIll", "Blind", "Deaf",
              "Stun", "Conf", "Hallu", "Lev", "Fly", "Ride")
DEADLY_CONDITIONS = ("Stone", "Slime", "Strngl", "FoodPois", "TermIll")

_ST1 = re.compile(
    r"^(?P<title>.*?)\s+St:(?P<st>[0-9/*]+)\s+Dx:(?P<dx>\d+)\s+Co:(?P<co>\d+)\s+"
    r"In:(?P<in>\d+)\s+Wi:(?P<wi>\d+)\s+Ch:(?P<ch>\d+)\s*(?P<align>Lawful|Neutral|Chaotic|Unaligned)?"
    r"(?:\s+S:(?P<score>\d+))?")
_LDESC = re.compile(r"^(?P<ldesc>Dlvl:\s*(?P<dlvl>-?\d+)|Home\s+(?P<home>\d+)|Fort Ludios|"
                    r"Astral Plane|End Game|Plane of \w+|[A-Z][A-Za-z' ]+?)\s+")
_GOLD = re.compile(r"(?:^|\s)\S:(?P<gold>\d+)")
_HP = re.compile(r"HP:(?P<hp>-?\d+)\((?P<hpmax>\d+)\)")
_PW = re.compile(r"Pw:(?P<pw>-?\d+)\((?P<pwmax>\d+)\)")
_AC = re.compile(r"AC:(?P<ac>-?\d+)")
_XP = re.compile(r"(?:Xp|Exp):(?P<xl>\d+)(?:/(?P<exp>\d+))?")
_HD = re.compile(r"HD:(?P<hd>\d+)")
_T = re.compile(r"T:(?P<t>\d+)")


@dataclass
class Status:
    title: str = ""
    st: str = ""
    dx: int = 0
    co: int = 0
    in_: int = 0
    wi: int = 0
    ch: int = 0
    align: str = ""
    score: int | None = None
    ldesc: str = ""          # "Dlvl:5", "Home 2", "Fort Ludios", "Astral Plane", "End Game"
    dlvl: int | None = None  # depth for Dlvl:N; quest home level for Home N
    gold: int = 0
    hp: int = 0
    hpmax: int = 0
    pw: int = 0
    pwmax: int = 0
    ac: int = 0
    xl: int = 0
    exp: int | None = None
    hd: int | None = None    # set when polymorphed (the status line shows HD instead of Xp)
    polymorphed: bool = False  # set by the Game when HD is shown (xl then keeps the last real XL)
    stale: bool = False      # copied from the last readable status (a window covers the status lines)
    turn: int | None = None
    hunger: str = ""
    encumbrance: str = ""
    conditions: list[str] = field(default_factory=list)
    ok: bool = False         # both lines parsed

    def as_dict(self) -> dict:
        d = dict(self.__dict__)
        d["int"] = d.pop("in_")
        return d

    def short(self) -> str:
        bits = [f"T:{self.turn}", self.ldesc or "?", f"HP:{self.hp}/{self.hpmax}",
                f"Pw:{self.pw}/{self.pwmax}", f"AC:{self.ac}"]
        bits.append(f"HD:{self.hd}" if self.hd is not None else f"XL:{self.xl}")
        if self.exp is not None:
            bits.append(f"Exp:{self.exp}")
        bits.append(f"${self.gold}")
        extra = [s for s in (self.hunger, self.encumbrance) if s] + self.conditions
        if extra:
            bits.append(" ".join(extra))
        return " ".join(bits)


def parse_status(scr: Screen) -> Status:
    s = Status()
    l1 = scr.row(scr.height - 2).rstrip()
    l2 = scr.row(scr.height - 1).rstrip()
    m = _ST1.search(l1)
    ok1 = False
    if m:
        ok1 = True
        s.title = m.group("title").strip()
        s.st = m.group("st")
        s.dx, s.co = int(m.group("dx")), int(m.group("co"))
        s.in_, s.wi, s.ch = int(m.group("in")), int(m.group("wi")), int(m.group("ch"))
        s.align = m.group("align") or ""
        if m.group("score"):
            s.score = int(m.group("score"))
    ok2 = False
    mh = _HP.search(l2)
    if mh:
        ok2 = True
        s.hp, s.hpmax = int(mh.group("hp")), int(mh.group("hpmax"))
        head = l2[: mh.start()]
        ml = _LDESC.match(l2)
        if ml:
            s.ldesc = ml.group("ldesc").replace("Dlvl: ", "Dlvl:").strip()
            if ml.group("dlvl"):
                s.dlvl = int(ml.group("dlvl"))
            elif ml.group("home"):
                s.dlvl = int(ml.group("home"))
        mg = _GOLD.search(head[len(s.ldesc):] if s.ldesc else head)
        if mg:
            s.gold = int(mg.group("gold"))
        mp = _PW.search(l2)
        if mp:
            s.pw, s.pwmax = int(mp.group("pw")), int(mp.group("pwmax"))
        ma = _AC.search(l2)
        if ma:
            s.ac = int(ma.group("ac"))
        mx = _XP.search(l2)
        if mx:
            s.xl = int(mx.group("xl"))
            if mx.group("exp") is not None:
                s.exp = int(mx.group("exp"))
        md = _HD.search(l2)
        if md:
            s.hd = int(md.group("hd"))
        mt = _T.search(l2)
        if mt:
            s.turn = int(mt.group("t"))
        tail = l2[mt.end():] if mt else l2[mh.end():]
        words = tail.split()
        for w in words:
            if w in HUNGER:
                s.hunger = w
            elif w in ENCUMBRANCE:
                s.encumbrance = w
            elif w in CONDITIONS:
                s.conditions.append(w)
    s.ok = ok1 and ok2
    return s


# ---------------------------------------------------------------------------
# screen state


@dataclass
class MenuItem:
    letter: str          # selector ('a', 'A', '$', '#', ...) or '' for headers
    text: str
    selected: bool = False
    header: bool = False
    y: int = 0


@dataclass
class Menu:
    title: str
    items: list[MenuItem]
    page: int = 1
    pages: int = 1
    x0: int = 0          # left column of the menu window
    kind: str = "menu"   # "menu" (selectable) or "text" (--More-- text window)

    def __iter__(self):
        """Iterate over selectable items (not headers)."""
        return iter(self.selectable())

    def __len__(self):
        return len(self.selectable())

    def selectable(self) -> list[MenuItem]:
        return [i for i in self.items if i.letter and not i.header]

    def find(self, pattern: str) -> list[MenuItem]:
        rx = re.compile(pattern, re.I)
        return [i for i in self.selectable() if rx.search(i.text)]


@dataclass
class State:
    kind: str            # command | more | menu | text | yn | direction | object |
                         # getlin | extcmd | count | getpos | gameover | dgl | unknown
    prompt: str = ""     # prompt text (row 0) for prompt kinds
    choices: str = ""    # for yn: allowed chars; for object: the bracket content
    default: str = ""    # for yn: default answer
    menu: Menu | None = None
    more_text: str = ""  # message text shown with --More--
    msg_rows: int = 0    # extra screen rows (1..n) covered by a wrapped message/prompt
    dismiss: str = "\r" # key that dismisses a "more" state (Hardfought MSGTYPE=alert wants TAB)


_YN = re.compile(r"\[(?P<choices>[A-Za-z0-9\-#$ ]+)\](?:\s*\((?P<default>.)\))?\s*$")
_OBJ = re.compile(r"\[(?P<choices>[^\]]*)\]\s*$")
_MENU_END = re.compile(r"\((?:end|(?P<page>\d+) of (?P<pages>\d+))\)\s*$")
_ITEM = re.compile(r"^(?P<letter>[A-Za-z$#*]) (?P<sel>[-+#]) (?P<text>.*)$")

GETPOS_HINTS = ("Where do you want to travel", "Pick an object", "(For instructions type a",
                "Showing known terrain", "Showing underlying terrain",
                "Pick a monster", "Where do you want to", "Select an object",
                "Pick a location")

GAMEOVER_HINTS = ("Do you want your possessions identified?", "DYWYPI", "You die...",
                  "REST IN PEACE", "Goodbye ", "You are dead", "Farewell ",
                  "Do you want to see your attributes", "Do you want an account of creatures vanquished",
                  "Do you want to see your conduct", "Do you want to see the dungeon overview",
                  "Do you want to see your achievements")


def _cursor_after(scr: Screen, needle: str) -> tuple[int, int] | None:
    """Return (x, y) of `needle` if the cursor sits right after it (same row)."""
    cx, cy = scr.cursor
    r = scr.row(cy)
    i = r.rfind(needle, 0, cx + 1)
    if i >= 0 and i + len(needle) <= cx + 1 and r[i + len(needle):cx].strip() == "":
        return (i, cy)
    return None


def classify(scr: Screen) -> State:
    cx, cy = scr.cursor
    top = scr.row(0).rstrip()
    if scr.dead:
        return State("dead", prompt="the game process in the terminal has exited (connection lost or game ended)")

    # dgamelaunch / pre-game menus are recognizable by their banners.
    full = scr.text
    if "stale" in full and "will recover in" in full:
        return State("dgl", prompt="STALE-PROCESS COUNTDOWN: send NOTHING until it finishes")
    if _looks_dgl(full):
        return State("dgl", prompt=top)

    # config-file errors / other startup notices: "Hit return to continue:"
    hr = _cursor_after(scr, "Hit return to continue:")
    if hr is not None:
        txt = "\n".join(scr.row(r).rstrip() for r in range(0, hr[1]) if scr.row(r).strip())
        return State("more", more_text=txt or "Hit return to continue")

    # Hardfought MSGTYPE=alert: "<message> <TAB>" waits for a TAB keypress only
    # (used for eel/kraken/couatl wrap attacks -- a drowning threat!)
    tabpos = _cursor_after(scr, "<TAB>")
    if tabpos is not None and tabpos[1] <= 3:
        y = tabpos[1]
        txt = " ".join(scr.row(r).rstrip() if r < y else scr.row(r)[:tabpos[0]].rstrip()
                       for r in range(0, y + 1)).strip()
        return State("more", more_text=txt, dismiss="\t", msg_rows=y)

    # --More-- (message line, or at the end of a text window)
    pos = _cursor_after(scr, MORE)
    if pos is None:
        # cursor sometimes lands one row below / at col 0 of next row with some
        # terminals; fall back to any --More-- that ends a row.
        for (x, y) in scr.find(MORE):
            if scr.row(y)[x + len(MORE):].strip() == "":
                pos = (x, y)
                break
    if pos is not None:
        x, y = pos
        before = scr.row(y)[x - 1] if x > 0 else " "
        if before != " ":
            # message-line --More--: text runs from row 0 to row y (long
            # messages wrap onto following rows)
            txt = " ".join(scr.row(r).rstrip() if r < y else scr.row(r)[:x].rstrip()
                           for r in range(0, y + 1)).strip()
            st = State("more", more_text=txt)
        else:
            # a text window (e.g. "Things that are here:"), left edge at x
            menu = _parse_window(scr, pos, kind="text")
            txt = "\n".join(i.text for i in menu.items)
            st = State("text", more_text=txt, menu=menu)
        if "REST IN PEACE" in full or any(h in txt for h in GAMEOVER_HINTS):
            if st.kind == "more":
                st.kind = "gameover"
                st.prompt = txt
        return st

    # menus: "(end)" or "(n of m)" with the cursor right after it
    for (x, y) in _menu_end_positions(scr):
        menu = _parse_window(scr, (x, y), kind="menu")
        m = _MENU_END.search(scr.row(y))
        if m and m.group("page"):
            menu.page, menu.pages = int(m.group("page")), int(m.group("pages"))
        return State("menu", menu=menu, prompt=menu.title)

    # prompts on the message line. Long prompts/messages word-wrap onto rows
    # 1..n (tty update_topl), and the cursor then sits after the text on the
    # last of those rows -- NOT on the hero. A blank cell under a cursor that
    # is near the top of the map means we're looking at such a wrapped prompt.
    prompt_text = None
    msg_rows = 0
    if cy == 0:
        prompt_text = top
    elif 1 <= cy <= 4 and scr.at(cx, cy) == " " and scr.row(cy)[:cx].strip() and top \
            and (len(top) >= 60 or _PROMPT_END.search(scr.row(cy)[:cx]) or _texty(scr.row(cy)[:cx])):
        # rows 0..cy are one message/prompt: word-wrapped by tty (join with a
        # space) or hard-wrapped by the terminal at column 80 (join directly)
        parts = [scr.row(r) for r in range(0, cy)] + [scr.row(cy)[:cx]]
        prompt_text = ""
        for i, part in enumerate(parts):
            if i == 0:
                prompt_text = part.rstrip()
            elif len(parts[i - 1].rstrip()) >= scr.width:
                prompt_text += part.rstrip()          # hard wrap mid-word ("Sel" + "l it?")
            else:
                prompt_text += " " + part.strip()
        msg_rows = cy
    if prompt_text is not None:
        st = _classify_prompt(prompt_text)
        st.msg_rows = msg_rows
        return st

    if MAP_TOP <= cy <= MAP_BOTTOM:
        if any(h in top for h in GETPOS_HINTS):
            return State("getpos", prompt=top)
        if scr.at(cx, cy) == " ":
            # in command state the cursor always sits on the hero glyph
            return State("unknown", prompt=top)
        st = State("command", prompt=top)
        # a long final message can stay wrapped over the top map rows
        if len(top) >= 50:
            r = 1
            while r <= 3 and r != cy and _texty(scr.row(r)):
                r += 1
            st.msg_rows = r - 1
        return st

    if "Do you want your possessions identified?" in full or "REST IN PEACE" in full:
        return State("gameover", prompt=top)
    return State("unknown", prompt=top)


_WORDS = re.compile(r"[A-Za-z']{3,} [A-Za-z']{2,}")
_PROMPT_END = re.compile(r"(\[[^\]]*\](\s*\([^)]*\))?|\?|:)\s*$")


def _texty(row: str) -> bool:
    """Does this screen row look like English text (a wrapped message) rather
    than map? Maps have walls/corridors and rarely two adjacent words."""
    t = row.strip()
    if not t or "|" in t or "--" in t or "##" in t:
        return False
    if not _WORDS.search(t):
        return False
    good = sum(1 for c in t if c.isalpha() or c in " ,.'!?()[]-:;\"")
    return good / len(t) > 0.85


def _classify_prompt(text: str) -> State:
    t = text.rstrip()
    if any(h in t for h in GAMEOVER_HINTS):
        m = _YN.search(t)
        return State("gameover", prompt=t, choices=m.group("choices") if m else "",
                     default=(m.group("default") or "") if m else "")
    if t.startswith("#"):
        return State("extcmd", prompt=t)
    if t.startswith("Count:"):
        return State("count", prompt=t)
    if "In what direction?" in t or t.endswith("in what direction?"):
        return State("direction", prompt=t)
    if "[yes/no]" in t or re.search(r"\(yes\) \[no\]\s*$", t):
        # paranoid_confirmation prompts: type "yes<CR>" to confirm; anything else (or <Esc>) = no
        return State("yn", prompt=t, choices="yes/no", default="no")
    m = _YN.search(t)
    if m and re.fullmatch(r"[yYnNaAq\-#0-9 ]+|[a-zA-Z]{1,6}", m.group("choices").replace(" ", "")) \
            and not t.startswith("What do you want") and "or ?*" not in t:
        return State("yn", prompt=t, choices=m.group("choices"), default=m.group("default") or "")
    m = _OBJ.search(t)
    if m:
        return State("object", prompt=t, choices=m.group("choices"))
    return State("getlin", prompt=t)


def _menu_end_positions(scr: Screen):
    cx, cy = scr.cursor
    r = scr.row(cy)
    m = _MENU_END.search(r[: cx + 1].rstrip() + " ") if r else None
    hits = []
    if m:
        hits.append((m.start(), cy))
    else:
        # cursor may already be placed elsewhere; accept a menu end marker that
        # is the last text on its row, lowest one first.
        for y in range(scr.height - 1, 0, -1):
            rr = scr.row(y).rstrip()
            mm = _MENU_END.search(rr)
            if mm and mm.end() == len(rr):
                hits.append((mm.start(), y))
                break
    return hits


def _parse_window(scr: Screen, end_pos: tuple[int, int], kind: str) -> Menu:
    """Parse a tty menu/text window whose last line holds the end marker at end_pos."""
    x0, yend = end_pos
    # tty menus are left-aligned at the window's offx; the end marker is at offx
    # too, so x0 is the window's left edge. Full-screen windows have x0 == 0.
    rows = []
    for y in range(0, yend):
        seg = scr.row(y)[x0:].rstrip()
        rows.append((y, seg))
    # the window starts at the first row where its content begins; for
    # right-side windows, map debris to the left of x0 is ignored by slicing.
    # Drop leading blank rows.
    while rows and not rows[0][1]:
        rows.pop(0)
    title = ""
    items: list[MenuItem] = []
    for y, seg in rows:
        if not seg:
            continue
        m = _ITEM.match(seg)
        if m and kind == "menu":
            items.append(MenuItem(letter=m.group("letter"), text=m.group("text").strip(),
                                  selected=m.group("sel") in "+#", y=y))
            continue
        is_header = any(scr.reverse_at(x, y) for x in range(x0, min(scr.width, x0 + len(seg))))
        if not items and not title and not is_header and kind == "menu":
            title = seg.strip()
            continue
        items.append(MenuItem(letter="", text=seg.strip(), header=is_header or kind == "menu", y=y))
    return Menu(title=title, items=items, x0=x0, kind=kind)


def _looks_dgl(full: str) -> bool:
    low = full.lower()
    if "dgamelaunch" in low:
        return True
    markers = ("l) login", "r) register", "w) watch", "q) quit", "logged in as")
    return sum(1 for m in markers if m in low) >= 2


# ---------------------------------------------------------------------------
# map helpers


def map_rows(scr: Screen) -> list[str]:
    return [scr.row(y) for y in range(MAP_TOP, MAP_BOTTOM + 1)]


MONSTER_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ@&';:~")
# ':' is also a dog/lizard class and ';' sea monsters; '~' long worm tail; 'I'
# remembered unseen monster. Items/terrain use other symbols.
OBJECT_CHARS = set(")[%?/=!\"(*+$`0")
TERRAIN_CHARS = set(".#<>_{}|-+^\\")


def hero_pos(scr: Screen, state: State | None = None) -> tuple[int, int] | None:
    """In command state the cursor sits on the hero."""
    cx, cy = scr.cursor
    if MAP_TOP <= cy <= MAP_BOTTOM:
        return (cx, cy)
    return None
