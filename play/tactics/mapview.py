"""Pure helpers over a snapshot's map (screen rows 1..21). No side effects."""

from __future__ import annotations

from nh.parse import MAP_BOTTOM, MAP_TOP, MONSTER_CHARS

DIRS8 = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
DIRS4 = [(0, -1), (-1, 0), (1, 0), (0, 1)]
DIR_KEY = {(-1, -1): "y", (0, -1): "k", (1, -1): "u", (-1, 0): "h", (1, 0): "l",
           (-1, 1): "b", (0, 1): "j", (1, 1): "n"}
KEY_DIR = {v: k for k, v in DIR_KEY.items()}

BROWN = 3
FLOORISH = set(".<>{_\\") | set(")[%?/=!\"(*$`")   # walkable when seen (items lie on floor)


def cell(s, x, y):
    return s.screen.at(x, y)


def color(s, x, y):
    return s.screen.color_at(x, y)


def in_map(x, y):
    return 0 <= x < 80 and MAP_TOP <= y <= MAP_BOTTOM


def is_door(s, x, y) -> bool:
    if (x, y) == s.hero and getattr(s, "under", None) == "D":
        return True          # you stand in a doorway with a door (the '@' hides it)
    if (getattr(s, "feature_mem", None) or {}).get((x, y)) == "D":
        return True          # a door seen before, now under an object pile or a monster
    if getattr(s, "rogue", False) and cell(s, x, y) == "+":
        from nh.mapscan import _door_like
        if _door_like(s.screen, x, y):
            return True      # a Rogue-level doorway: no door, but no diagonal moves either (doorless_door)
    return is_open_door(s, x, y) or is_closed_door(s, x, y)


def is_open_door(s, x, y) -> bool:
    return cell(s, x, y) in "|-" and color(s, x, y) == BROWN


def is_closed_door(s, x, y) -> bool:
    """A brown '+' in a wall line; a '+' lying on the floor is a spellbook."""
    from nh.mapscan import _door_like
    return cell(s, x, y) == "+" and color(s, x, y) == BROWN and (
        _door_like(s.screen, x, y) or (getattr(s, "feature_mem", None) or {}).get((x, y)) == "D")


def is_wall(s, x, y) -> bool:
    ch = cell(s, x, y)
    return ch in "|-" and color(s, x, y) != BROWN and not (ch == "|" and color(s, x, y) == 15)   # (15: a grave)


def is_walkable(s, x, y, allow_monsters=True) -> bool:
    """Known-walkable by appearance. Corridors '#' count; trees/sinks/iron bars
    also draw as '#' (green tree, gray sink in rooms, cyan bars) — we treat
    only gray '#' as corridor."""
    if not in_map(x, y):
        return False
    if (x, y) in getattr(s, "solid_mem", ()):
        return False          # a step there said "It's solid stone." (gold/gems embedded in rock)
    ch = cell(s, x, y)
    if ch == " ":
        # a cyan blank is open air (Planes of Air and Water); on the Rogue level a dark-room floor square
        # seen before shows blank again (the harness remembers it); any other blank is unknown
        return color(s, x, y) == 6 or (x, y) in getattr(s, "floor_mem", ())
    if ch == "#":
        return color(s, x, y) in (7, 8, 15)   # corridor (lit or not); not tree(green)/bars(cyan)
    if ch == "|" and color(s, x, y) == 15:
        return True                            # a grave (drawing.c: bright white '|'; walls are gray)
    if ch in FLOORISH:
        return True
    if is_open_door(s, x, y):
        return True
    if ch == "+":
        return not is_closed_door(s, x, y)   # a spellbook on the floor
    if ch == "^":
        return False  # traps: avoid by default
    if ch in MONSTER_CHARS:
        return allow_monsters
    return False


def is_solid(s, x, y) -> bool:
    """What NetHack's diagonal-squeeze rule counts (bad_rock): rock or
    unknown, walls (not doors), trees, boulders."""
    ch = cell(s, x, y)
    if ch in "|-":
        return color(s, x, y) not in (BROWN, 15)      # (brown: an open door; bright white '|': a grave)
    return ch in " 0" or (ch == "#" and color(s, x, y) == 2)


def squeeze_steps(s, path, start) -> list:
    """The diagonal steps of `path` (from `start`) that pass between two solid
    squares. NetHack refuses them while your inventory weighs more than 600
    ("You are carrying too much to get through"), and its travel then finds
    no route at all. Returns the squares the squeezes start from."""
    out, prev = [], start
    for c in path or []:
        dx, dy = c[0] - prev[0], c[1] - prev[1]
        if dx and dy and is_solid(s, prev[0] + dx, prev[1]) and is_solid(s, prev[0], prev[1] + dy):
            out.append(prev)
        prev = c
    return out


def find(s, ch: str, color_num: int | None = None) -> list[tuple[int, int]]:
    out = []
    for y in range(MAP_TOP, MAP_BOTTOM + 1):
        row = s.screen.row(y)
        for x, c in enumerate(row):
            if c == ch and (color_num is None or s.screen.color_at(x, y) == color_num):
                out.append((x, y))
    return out


def dist(a, b) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def nearest(s, cells):
    h = s.hero
    if not cells or h is None:
        return None
    return min(cells, key=lambda c: dist(c, h))


def direction_key(frm, to) -> str | None:
    dx, dy = to[0] - frm[0], to[1] - frm[1]
    if max(abs(dx), abs(dy)) != 1:
        return None
    return DIR_KEY[(dx, dy)]


def neighbors(x, y, diag=True):
    for dx, dy in (DIRS8 if diag else DIRS4):
        nx, ny = x + dx, y + dy
        if in_map(nx, ny):
            yield nx, ny


def _bfs_dist(s, start, passable) -> dict:
    """{cell: steps} from start over 8-connected cells passable(c) says yes to (no diagonal moves into or out of
    doorways)."""
    from collections import deque
    d = {start: 0}
    q = deque([start])
    while q:
        cur = q.popleft()
        for nx, ny in neighbors(*cur):
            nxt = (nx, ny)
            if nxt in d or not passable(nxt):
                continue
            if nx != cur[0] and ny != cur[1] and (is_door(s, *cur) or is_door(s, nx, ny)):
                continue
            d[nxt] = d[cur] + 1
            q.append(nxt)
    return d


def on_short_routes(s, start, goal, cells, slack: int = 1) -> list:
    """The squares of `cells` that lie on SOME route from start to goal at most `slack` steps longer than the
    shortest one — where NetHack's own travel may walk (it knows nothing of a disguised mimic, a mold out of
    view or an avoid() square: p2 shift 30 walked into a remembered giant mimic). [] when none."""
    cells = set(cells) - {start, goal}
    if not cells or start is None or goal is None:
        return []

    def passable(c):
        return c in cells or c == goal or is_walkable(s, *c, allow_monsters=True)
    ds = _bfs_dist(s, start, passable)
    if goal not in ds:
        return []
    dg = _bfs_dist(s, goal, passable)
    limit = ds[goal] + slack
    return sorted(c for c in cells if c in ds and c in dg and ds[c] + dg[c] <= limit)


def bfs_path(s, start, goal, avoid=frozenset(), allow_monsters=False, allow_traps=False, allow_water=False,
             allow_boulders=False, allow_pets=False):
    """Shortest 8-connected path over known-walkable cells (doors: no diagonal
    moves into/out of doorways, per NetHack rules). Returns list of cells
    excluding start, or None. allow_traps=True also crosses '^' squares,
    allow_water=True water/lava '}' squares (to tell "the only way is over a
    trap / across water" from "no known way")."""
    from collections import deque
    if start == goal:
        return []
    # allow_pets: your pet's square is passable even when other monsters aren't (a step there swaps places)
    pets = {(m["x"], m["y"]) for m in (s.monsters or []) if m.get("tame") or m.get("pet")} if allow_pets else set()
    prev = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        for nx, ny in neighbors(*cur):
            nxt = (nx, ny)
            if nxt in prev or nxt in avoid:
                continue
            if nxt != goal and nxt not in pets and not is_walkable(s, nx, ny, allow_monsters=allow_monsters) \
                    and not (allow_traps and cell(s, nx, ny) == "^") \
                    and not (allow_water and cell(s, nx, ny) == "}") \
                    and not (allow_boulders and cell(s, nx, ny) in "0`"):
                continue
            if nxt == goal and not (is_walkable(s, nx, ny, allow_monsters=True) or cell(s, nx, ny) == " "
                                    or (allow_traps and cell(s, nx, ny) == "^")):
                continue
            diag = nx != cur[0] and ny != cur[1]
            if diag and (is_door(s, *cur) or is_door(s, nx, ny)):
                continue
            if diag and getattr(s, "no_squeeze", False) and is_solid(s, nx, cur[1]) and is_solid(s, cur[0], ny):
                continue              # "You are carrying too much to get through" was seen: no squeezes
            prev[nxt] = cur
            if nxt == goal:
                path = [nxt]
                while prev[path[-1]] != start:
                    path.append(prev[path[-1]])
                return list(reversed(path))
            q.append(nxt)
    return None
