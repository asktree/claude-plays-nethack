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
    return is_open_door(s, x, y) or is_closed_door(s, x, y)


def is_open_door(s, x, y) -> bool:
    return cell(s, x, y) in "|-" and color(s, x, y) == BROWN


def is_closed_door(s, x, y) -> bool:
    """A brown '+' in a wall line; a '+' lying on the floor is a spellbook."""
    from nh.mapscan import _door_like
    return cell(s, x, y) == "+" and color(s, x, y) == BROWN and _door_like(s.screen, x, y)


def is_wall(s, x, y) -> bool:
    ch = cell(s, x, y)
    return ch in "|-" and color(s, x, y) != BROWN


def is_walkable(s, x, y, allow_monsters=True) -> bool:
    """Known-walkable by appearance. Corridors '#' count; trees/sinks/iron bars
    also draw as '#' (green tree, gray sink in rooms, cyan bars) — we treat
    only gray '#' as corridor."""
    if not in_map(x, y):
        return False
    ch = cell(s, x, y)
    if ch == " ":
        return False
    if ch == "#":
        return color(s, x, y) in (7, 8, 15)   # corridor (lit or not); not tree(green)/bars(cyan)
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
        return color(s, x, y) != BROWN
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


def bfs_path(s, start, goal, avoid=frozenset(), allow_monsters=False, allow_traps=False, allow_water=False):
    """Shortest 8-connected path over known-walkable cells (doors: no diagonal
    moves into/out of doorways, per NetHack rules). Returns list of cells
    excluding start, or None. allow_traps=True also crosses '^' squares,
    allow_water=True water/lava '}' squares (to tell "the only way is over a
    trap / across water" from "no known way")."""
    from collections import deque
    if start == goal:
        return []
    prev = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        for nx, ny in neighbors(*cur):
            nxt = (nx, ny)
            if nxt in prev or nxt in avoid:
                continue
            if nxt != goal and not is_walkable(s, nx, ny, allow_monsters=allow_monsters) \
                    and not (allow_traps and cell(s, nx, ny) == "^") \
                    and not (allow_water and cell(s, nx, ny) == "}"):
                continue
            if nxt == goal and not (is_walkable(s, nx, ny, allow_monsters=True) or cell(s, nx, ny) == " "):
                continue
            diag = nx != cur[0] and ny != cur[1]
            if diag and (is_door(s, *cur) or is_door(s, nx, ny)):
                continue
            prev[nxt] = cur
            if nxt == goal:
                path = [nxt]
                while prev[path[-1]] != start:
                    path.append(prev[path[-1]])
                return list(reversed(path))
            q.append(nxt)
    return None
