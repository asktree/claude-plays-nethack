"""Sokoban helpers: a checked boulder-push executor.

You (the player) decide WHAT to push, using the level's known solution
(knowledge/wiki/Sokoban_Level_*.txt). This module handles HOW: walking to
the right side of the boulder without disturbing anything, pushing, and
verifying every result. It stops (pauses) on anything unexpected.

Sokoban rules that matter (3.6): boulders can only be pushed orthogonally;
you can't move diagonally between two boulders/walls; holes (^) swallow a
boulder and become floor; destroying boulders / reading earth costs Luck.
Symbols with our options: boulder '0', hole/trap '^'.
"""

from __future__ import annotations

from collections import deque

from . import ctx
from .mapview import DIR_KEY, KEY_DIR, MONSTER_CHARS

from .benign import BENIGN

PUSH_OK = [r"With great effort you move the boulder", r"You try to move the boulder",
           r"You hear a monster behind the boulder", r"Perhaps that's why you cannot move it",
           r"The boulder falls into and plugs a hole", r"plugs? a (hole|trap door)",
           r"The boulder fills a pit", r"fills a (pit|hole)",
           r"You hear the boulder", r"There is a boulder in your way",
           r"You swap places with", r"You stop\. .* is in your way"] + BENIGN   # + engravings read on the way

_ORTHO = {"h": (-1, 0), "l": (1, 0), "k": (0, -1), "j": (0, 1)}
_ALIASES = {"left": "h", "right": "l", "up": "k", "down": "j", "w": "h", "e": "l", "n": "k", "s": "j",
            "L": "h", "R": "l", "U": "k", "D": "j"}


def _norm(d: str) -> str:
    d = _ALIASES.get(d, d)
    if d not in _ORTHO:
        raise ValueError(f"push direction must be one of h/j/k/l (got {d!r})")
    return d


def _solid(s, x, y):
    """Rock, walls, boulders: what the no-diagonal-squeeze rule counts."""
    return s.screen.at(x, y) in " |-0#+}"


def _blocked(s, x, y, allow_goal=None):
    ch = s.screen.at(x, y)
    if (x, y) == allow_goal:
        return False
    if ch in " |-0^#+}":
        return True    # rock/walls/boulders/holes/corridor-looking bars/doors/water
    if ch in MONSTER_CHARS and (x, y) != s.hero and not s.screen.reverse_at(x, y):
        return True    # a monster that isn't our pet (pets just swap places)
    return False


def route(s, start, goal, ignore_monsters=False):
    """Shortest walk avoiding boulders/holes/monsters, honoring the Sokoban
    'no diagonal squeeze' rule. Returns a string of move keys, or None."""
    q = deque([start])
    prev = {start: None}
    while q:
        cur = q.popleft()
        if cur == goal:
            keys = []
            while prev[cur] is not None:
                p = prev[cur]
                keys.append(DIR_KEY[(cur[0] - p[0], cur[1] - p[1])])
                cur = p
            return "".join(reversed(keys))
        for (dx, dy), key in DIR_KEY.items():
            nx, ny = cur[0] + dx, cur[1] + dy
            if (nx, ny) in prev:
                continue
            if _blocked(s, nx, ny, allow_goal=goal) and not (ignore_monsters and _occupied(s, nx, ny)):
                continue
            if dx and dy and _solid(s, cur[0] + dx, cur[1]) and _solid(s, cur[0], cur[1] + dy):
                continue   # can't squeeze diagonally between boulders/walls in Sokoban
            prev[(nx, ny)] = cur
            q.append((nx, ny))
    return None


def _occupied(s, x, y):
    ch = s.screen.at(x, y)
    return ch in MONSTER_CHARS and (x, y) != s.hero and not s.screen.reverse_at(x, y)


def _hostiles_near(s) -> list:
    return [m for m in s.adjacent_hostiles() if not m.get("statue")]


def walk(keys: str):
    """Walk a key path one step at a time, verifying each step moved us.
    Never steps into a (non-pet) monster: waits for a peaceful to move, but
    pauses at once when a hostile is next to you (waiting beside it only
    gives it free hits)."""
    s = ctx.last()
    for k in keys:
        before = s.hero
        if before is None:
            ctx.pause(f"walk: not at the command prompt ({s.state.kind}: {s.state.prompt!r})")
            return ctx.last()
        dx, dy = KEY_DIR[k]
        dest = (before[0] + dx, before[1] + dy)
        waited = 0
        while _occupied(s, *dest) and waited < 4:
            hostile = _hostiles_near(s)
            if hostile:
                ctx.pause("walk: hostile " + ", ".join(f"{m.get('desc') or m['ch']} at ({m['x']},{m['y']})"
                                                     for m in hostile) + " next to you — fight() it, then solve() "
                          "again (it resumes)")
                return ctx.last()
            s = ctx.do(".", ok=PUSH_OK)
            waited += 1
        if _occupied(s, *dest):
            ctx.pause(f"walk: {s.screen.at(*dest)!r} at {dest} is in the way (not attacking it)")
            return ctx.last()
        s = ctx.do(k, ok=PUSH_OK)
        if s.hero != dest:
            if s.state.kind != "command":
                ctx.do("<Esc>", quiet=True)   # e.g. an attack confirmation: decline
            ctx.pause(f"walk: step {k!r} from {before} didn't arrive (now at {ctx.last().hero})")
            return ctx.last()
    return s


def push(bx: int, by: int, dirs: str):
    """Push the boulder at (bx, by) along `dirs` (e.g. 'hhk' = left, left, up).
    Walks to the correct side before each push. Returns (final_snap, boulder_pos
    or None if it plugged a hole)."""
    b = (bx, by)
    s = ctx.last()
    if s.screen.at(bx, by) != "0":
        raise ValueError(f"no boulder '0' at {b} (found {s.screen.at(bx, by)!r})")
    for d in dirs:
        d = _norm(d)
        dx, dy = _ORTHO[d]
        stand = (b[0] - dx, b[1] - dy)
        s = ctx.last()
        if s.hero is None:
            ctx.pause(f"push: not at the command prompt ({s.state.kind}: {s.state.prompt!r})")
            return ctx.last(), b
        if s.hero != stand:
            path = route(s, s.hero, stand)
            waited = 0
            while path is None and waited < 8 and route(s, s.hero, stand, ignore_monsters=True):
                if _hostiles_near(s):
                    ctx.pause("push: hostile " + ", ".join(f"{m.get('desc') or m['ch']} at ({m['x']},{m['y']})"
                                                         for m in _hostiles_near(s))
                              + " next to you blocks the way — fight() it, then solve() again")
                    return ctx.last(), b
                s = ctx.do(".", ok=PUSH_OK)      # a monster blocks the way: give it time to move
                waited += 1
                path = route(s, s.hero, stand)
            if path is None:
                ctx.pause(f"push: no safe route from {s.hero} to {stand} (to push {b} {d})")
                return ctx.last(), b
            s = walk(path)
            if s.hero != stand:
                return s, b
        s = ctx.do(d, ok=PUSH_OK)
        text = " ".join(s.messages)
        waits = 0
        while "behind the boulder" in text and waits < 6:
            # something (often the pet) is on the far side: wait and retry
            ctx.do(".", ok=PUSH_OK)
            waits += 1
            s = ctx.do(d, ok=PUSH_OK)
            text = " ".join(s.messages)
        nb = (b[0] + dx, b[1] + dy)
        if "plug" in text or "fills" in text:
            return s, None
        if s.screen.at(*nb) == "0" and s.hero == b:
            b = nb
            continue
        ctx.pause(f"push: boulder {b} did not move {d} as expected (messages: {text!r})")
        return ctx.last(), b
    return ctx.last(), b


def board(s=None) -> str:
    """The Sokoban board region of the map with coordinates (boulders 0, holes ^)."""
    s = s or ctx.last()
    rows = [(y, s.screen.row(y)) for y in range(1, 22)]
    rows = [(y, r) for y, r in rows if r.strip()]
    if not rows:
        return "(empty map)"
    x0 = min(len(r) - len(r.lstrip()) for _, r in rows)
    x1 = max(len(r.rstrip()) for _, r in rows)
    tens = "".join(str((x // 10) % 10) if x % 10 == 0 else " " for x in range(x0, x1))
    ones = "".join(str(x % 10) for x in range(x0, x1))
    out = ["    " + tens, "    " + ones]
    out += [f"{y:>2}  {r[x0:x1]}" for y, r in rows]
    return "\n".join(out)


_WIKI = {"r": "l", "l": "h", "u": "k", "d": "j"}


def push_wiki(bx: int, by: int, moves: str):
    """Push using the wiki's solution notation: r/l/u/d (right/left/up/down),
    spaces ignored, a trailing '*' (fills a pit) ignored. Example: the wiki's
    'D rlll llll' for the boulder you identified as D at (41,9) is
    push_wiki(41, 9, 'rlll llll'). NOTE: wiki 'l' = LEFT (vi-key 'h')."""
    keys = "".join(_WIKI[c] for c in moves.lower() if c in _WIKI)
    return push(bx, by, keys)


# ---- full-level solutions (scripts/gen_sokoban.py; verified in a simulator) ----

_UDLR = {"u": "k", "d": "j", "l": "h", "r": "l"}


def _levels():
    from .sokoban_data import LEVELS
    return LEVELS


def identify(s=None):
    """Which Sokoban level is on screen, and where: returns
    {"level", "wiki", "ox", "oy", "score"} or None. Matches the level's wall
    shape (NetHack draws some '|' of the .des as '-', so only wall/non-wall
    counts); Sokoban levels are premapped, so all walls are visible."""
    s = s or ctx.last()
    walls = {(x, y) for y in range(1, 22) for x, c in enumerate(s.screen.row(y)) if c in "|-"}
    if not walls:
        return None
    best = None
    for name, lv in _levels().items():
        lw = [(x, y) for y, r in enumerate(lv["rows"]) for x, c in enumerate(r) if c in "|-"]
        x0, y0 = min(lw, key=lambda c: (c[1], c[0]))
        for (sx, sy) in walls:
            ox, oy = sx - x0, sy - y0
            hit = sum(1 for (x, y) in lw if (x + ox, y + oy) in walls)
            score = hit / len(lw)
            if best is None or score > best["score"]:
                best = {"level": name, "wiki": lv["wiki"], "ox": ox, "oy": oy, "score": round(score, 3)}
    return best if best and best["score"] >= 0.9 else None


_ITEM_GLYPHS = set(")[%?/=!\"(*$`+")


def _state(s, lv, ox, oy):
    """(boulders, traps, covered) in level coordinates; covered = squares a
    monster or the hero hides (they match anything)."""
    h, w = len(lv["rows"]), max(len(r) for r in lv["rows"])
    boulders, traps, covered = set(), set(), set()
    for y in range(h):
        row = s.screen.row(y + oy)
        for x in range(w):
            c = row[x + ox] if 0 <= x + ox < len(row) else " "
            if c == "0":
                boulders.add((x, y))
            elif c == "^":
                traps.add((x, y))
            elif c in MONSTER_CHARS or c in _ITEM_GLYPHS:
                covered.add((x, y))       # a monster or an item lying there hides what's under it
    return boulders, traps, covered


def _diff(state, want, ox, oy) -> str:
    """Human-readable difference between the board and the plan (screen coords)."""
    boulders, traps, covered = state
    wb, wt = want
    def scr(cells):
        return sorted((x + ox, y + oy) for x, y in cells)
    bits = []
    extra = (boulders - covered) - wb
    missing = (wb - covered) - boulders
    if extra:
        bits.append(f"unexpected boulders {scr(extra)} (a boulder that appeared from nowhere is often a MIMIC: "
                    "farlook/search before touching it)")
    if missing:
        bits.append(f"boulders missing at {scr(missing)}")
    tm = (wt - covered) - traps
    if tm:
        bits.append(f"holes filled that shouldn't be {scr(tm)}")
    te = (traps - covered) - wt
    if te:
        bits.append(f"holes still open {scr(te)}")
    return "; ".join(bits) or "no visible difference"


def _matches(state, want) -> bool:
    boulders, traps, covered = state
    wb, wt = want
    return (boulders - covered == wb - covered) and (traps - covered == wt - covered)


_DXY = {"u": (0, -1), "d": (0, 1), "l": (-1, 0), "r": (1, 0)}


def _partials(lv, cur, only=None):
    """Points part-way through a step (a pause between two pushes of the same
    boulder) whose board matches `cur`: yields (i, j, pos, stand) = step
    index, pushes already done, the boulder's position now, and the square to
    stand on for its next push (level coordinates)."""
    prev_b = set(map(tuple, lv["boulders"]))
    prev_t = set(map(tuple, lv["traps"]))
    for i, st in enumerate(lv["steps"]):
        if only is None or i == only:
            at = tuple(st["at"])
            pos = at
            for j in range(1, len(st["moves"])):
                dx, dy = _DXY[st["moves"][j - 1]]
                pos = (pos[0] + dx, pos[1] + dy)
                if _matches(cur, ((prev_b - {at}) | {pos}, prev_t)):
                    nx, ny = _DXY[st["moves"][j]]
                    yield i, j, pos, (pos[0] - nx, pos[1] - ny)
        prev_b = set(map(tuple, st["after"]["boulders"]))
        prev_t = set(map(tuple, st["after"]["traps"]))


def progress(s=None) -> dict:
    """Where are we in this level's solution? Returns {"level", "wiki", "ox",
    "oy", "done": k (steps already done), "total", "next": step or None,
    "partial": None or {"pushes_done", "boulder_at"} when step k+1 was
    interrupted between two of its pushes (solve() resumes it)}.
    done is -1 if the board matches no point of the solution (boulders were
    moved differently: solve by hand from `board()` and the wiki page)."""
    s = s or ctx.last()
    ident = identify(s)
    if ident is None:
        raise ValueError("this doesn't look like a Sokoban level (no known wall layout on screen)")
    lv = _levels()[ident["level"]]
    cur = _state(s, lv, ident["ox"], ident["oy"])
    states = [(set(map(tuple, lv["boulders"])), set(map(tuple, lv["traps"])))]
    states += [(set(map(tuple, st["after"]["boulders"])), set(map(tuple, st["after"]["traps"]))) for st in lv["steps"]]
    done = -1
    for k in range(len(states) - 1, -1, -1):
        if _matches(cur, states[k]):
            done = k
            break
    ox, oy = ident["ox"], ident["oy"]

    def reachable(p):
        return s.hero is not None and route(s, s.hero, (p[3][0] + ox, p[3][1] + oy)) is not None

    partial = None
    if done < 0:
        cands = list(_partials(lv, cur))
        partial = next((p for p in cands if reachable(p)), cands[0] if cands else None)
        if partial:
            done = partial[0]
    elif done < len(lv["steps"]):
        # a step that brings its boulder back to its start part-way ('rl...': push it aside,
        # walk around, push it back) leaves the board as it was before the step. If the hero
        # can reach the next push from here, resume: replaying the whole step is often
        # impossible by then (the first push's side is cut off).
        partial = next((p for p in _partials(lv, cur, only=done) if reachable(p)), None)
    nxt = lv["steps"][done] if 0 <= done < len(lv["steps"]) else None
    return dict(ident, done=done, total=len(lv["steps"]), next=nxt,
                partial=({"pushes_done": partial[1], "boulder_at": (partial[2][0] + ident["ox"],
                                                                    partial[2][1] + ident["oy"])}
                         if partial else None))


def solve(max_steps: int | None = None, defer: int = 6):
    """Run this Sokoban level's verified solution from wherever the board is,
    one boulder at a time, checking the board after every step. Pauses (and
    stops) on anything unexpected. Returns progress() at the end.
    New monsters farther than `defer` squares without a danger note (behind
    the level's walls) don't pause until they come that close (defer=None:
    every newcomer pauses).
    When it finishes: the up stairs are reachable (top level: the door to the
    treasure zoo — prepare for that fight before going in)."""
    import contextlib
    far = getattr(ctx, "defer_far", None)
    with (far(defer) if far is not None and defer else contextlib.nullcontext()):
        return _solve(max_steps)


def _solve(max_steps):
    p = progress()
    if p["done"] < 0:
        lv = _levels()[p["level"]]
        cur = _state(ctx.last(), lv, p["ox"], p["oy"])
        start = (set(map(tuple, lv["boulders"])), set(map(tuple, lv["traps"])))
        ctx.pause(f"sokoban: the board of {p['wiki']} matches no point of the solution (vs the start: "
                  f"{_diff(cur, start, p['ox'], p['oy'])}) — solve the rest by hand (board(), push_wiki()) "
                  "or ask for help")
        return p
    lv = _levels()[p["level"]]
    ox, oy = p["ox"], p["oy"]
    print(f"sokoban: {p['wiki']} ({p['level']}), offset ({ox},{oy}), step {p['done']}/{p['total']}")
    n = 0
    part = p.get("partial")
    for i in range(p["done"], len(lv["steps"])):
        if max_steps is not None and n >= max_steps:
            break
        st = lv["steps"][i]
        bx, by = st["at"][0] + ox, st["at"][1] + oy
        keys = "".join(_UDLR[c] for c in st["moves"])
        if part and i == p["done"]:
            # resume a step that was interrupted between two pushes
            bx, by = part["boulder_at"]
            keys = keys[part["pushes_done"]:]
            print(f"  (resuming step {i + 1} after {part['pushes_done']} of its pushes)")
        print(f"  step {i + 1}/{len(lv['steps'])}: boulder {st['boulder']} at ({bx},{by}) {st['moves']}"
              + (" (fills a hole)" if st["fills"] else ""))
        ctx.activity(f"sokoban.solve() step {i + 1}/{len(lv['steps'])}: boulder {st['boulder']} from ({bx},{by}) "
                     f"moves {''.join(k for k in keys)} — call solve() again after dealing with it (it resumes)")
        s, pos = push(bx, by, keys)
        want = None if st["fills"] else (st["to"][0] + ox, st["to"][1] + oy)
        if pos != want:
            ctx.pause(f"sokoban: step {i + 1} ended with the boulder at {pos}, expected {want}")
            return progress()
        want = (set(map(tuple, st["after"]["boulders"])), set(map(tuple, st["after"]["traps"])))
        cur = _state(ctx.last(), lv, ox, oy)
        if not _matches(cur, want):
            ctx.pause(f"sokoban: after step {i + 1} the board differs from the plan: {_diff(cur, want, ox, oy)}")
            return progress()
        n += 1
    ctx.activity("")
    p = progress()
    if p.get("done") == p.get("total"):
        try:
            from .nav import known_cells
            s = ctx.last()
            ups = known_cells("<", s)
            hs = s.hostiles()
            print(f"sokoban: level solved — up stairs {ups[:2] or 'not in view yet'}; hostiles in view: "
                  + (", ".join(f"{m.get('desc') or m['ch']} at ({m['x']},{m['y']})" for m in hs[:5]) or "none")
                  + " (the stair room's door may be locked: unlock() / kick; the top level's prize room is a zoo)")
        except Exception:  # noqa: BLE001
            pass
    return p
