# p1 deep-Gehennom kernel helpers (shift 29). Load in the kernel with:
#   bin/nh --game p1 exec <<'EOF'
#   exec(open('/home/user/claude-plays-nethack/play/runs/p1/deep_helpers.py').read())
#   EOF
# Then e.g.:  with monster_filter(pause_filter): print(gexplore5())
#             with monster_filter(pause_filter): print(trek((8, 20)))
import re
from tactics.mapview import bfs_path

DIRS = {(0, -1): 'k', (0, 1): 'j', (-1, 0): 'h', (1, 0): 'l',
        (-1, -1): 'y', (1, -1): 'u', (-1, 1): 'b', (1, 1): 'n'}


def sgn(v):
    return (v > 0) - (v < 0)


def inline(dx, dy):
    return dx == 0 or dy == 0 or abs(dx) == abs(dy)


# species that stop the explore loop when within `radius`
WATCH = ('minotaur', 'dragon', 'storm giant', 'trapper', 'lurker', 'cockatrice', 'soldier', 'Wizard',
         'vampire lord', 'owlbear', 'devil', 'vrock')
# never auto-melee these when adjacent
DANGER_ADJ = ('cockatrice', 'chickatrice', 'floating eye', 'gas spore', 'Wizard', 'green slime', 'mind flayer',
              'disenchanter', 'nymph', 'succubus', 'incubus')
# newcomers that still pause under monster_filter(pause_filter)
SAFE_PAUSE = WATCH + DANGER_ADJ + ('lich', 'titan', 'vampire', 'gelatinous', 'energy vortex', 'black light',
                                   'yellow light', 'Nazgul', 'nalfeshnee', 'pit fiend', 'balrog', 'Angel',
                                   'jabberwock', 'purple worm', 'master', 'arch', 'umber hulk', 'unidentified',
                                   'Juiblex', 'Orcus', 'Demogorgon', 'Yeenoghu', 'Asmodeus', 'Baalzebub',
                                   'Dispater', 'Geryon', 'Vlad')
FIRE_WANDS = ['Q', 'z', 'P', 'o']
# traps the trek never crosses (magic traps summon monsters; the fire trap burns scroll i)
AVOID_TRAPS = frozenset()


def pause_filter(m):
    return any(w in (m.get('desc') or '') for w in SAFE_PAUSE) or m.get('ch') == 'I'


def watched_near(radius=7):
    o = look()
    return [m for m in o.monsters if not m.get('tame') and not m.get('peaceful')
            and any(w in (m.get('desc') or '') for w in WATCH) and m['dist'] <= radius]


def mino_handler():
    """minotaur in view: melee if adjacent, fire ray if in line within 8, else 'wait'."""
    o = look()
    ms = [m for m in o.monsters if 'minotaur' in (m.get('desc') or '')]
    if not ms:
        return None
    m = ms[0]
    hx, hy = o.hero
    dx, dy = m['x'] - hx, m['y'] - hy
    if max(abs(dx), abs(dy)) == 1:
        return fight(m['x'], m['y'], stop_hp=0.25)
    if inline(dx, dy) and max(abs(dx), abs(dy)) <= 8 and FIRE_WANDS:
        r = zap(FIRE_WANDS[0], DIRS[(sgn(dx), sgn(dy))])
        if any('Nothing happens' in x for x in (getattr(r, 'messages', []) or [])):
            FIRE_WANDS.pop(0)
        return r
    return 'wait'


def fight_adjacent_ordinary():
    adj = [m for m in look().adjacent_hostiles() if not any(d in (m.get('desc') or '') for d in DANGER_ADJ)]
    for m in adj:
        print('fighting adjacent', m['desc'])
        fight(m['x'], m['y'], stop_hp=0.45)
    return bool(adj)


def clear_I(x, y):
    """travel next to a stale remembered-unseen 'I' and swing once ('You attack thin air' clears it)."""
    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        try:
            travel(nx, ny)
        except NavError as ex:
            print('travel', (nx, ny), ex)
            continue
        if look().hero == (nx, ny):
            return fight(x, y, force=True)
    return None


def gexplore5(n=40, radius=7, legs=3):
    """explore() in short chunks: minotaur handler, stop for watched species, fight ordinary blockers,
    clear stale 'I' targets."""
    for i in range(n):
        r = mino_handler()
        if r is not None and r != 'wait':
            continue
        near = [m for m in watched_near(radius) if 'minotaur' not in m['desc']]
        if near or r == 'wait':
            print('WATCH:', [(m['desc'], m['x'], m['y'], m['dist']) for m in near], r)
            return 'watch'
        if fight_adjacent_ordinary():
            continue
        try:
            e = explore(max_legs=legs)
        except NavError as ex:
            s = str(ex)
            mm = re.search(r"target \((\d+), (\d+)\) holds an 'I'", s)
            if mm:
                print('clearing stale I', mm.groups(), clear_I(int(mm.group(1)), int(mm.group(2))))
                continue
            print('NavError:', s)
            if fight_adjacent_ordinary():
                continue
            return s
        reason = e.get('reason', '') if isinstance(e, dict) else str(e)
        if 'legs' in reason and not reason.startswith('blocked'):
            continue
        if reason.startswith('blocked: hostile') and fight_adjacent_ordinary():
            continue
        print('explore:', e)
        return e
    return 'n'


def trek(goal, maxit=25):
    """go to goal crossing known harmless traps with step_onto() (never the AVOID_TRAPS squares)."""
    for it in range(maxit):
        s = look()
        if s.hero == goal:
            return 'arrived'
        if fight_adjacent_ordinary():
            continue
        p = bfs_path(s, s.hero, goal, avoid=AVOID_TRAPS, allow_traps=True)
        if p is None:
            return 'no path'
        trapset = set(bad_squares(s)) - {goal}
        idx = next((i for i, c in enumerate(p) if c in trapset), None)
        try:
            if idx is None:
                travel(*goal)
            elif idx == 0:
                print('stepping onto trap', p[0])
                step_onto(*p[0])
            else:
                travel(*p[idx - 1])
        except NavError as ex:
            print('NavError', ex)
            if not fight_adjacent_ordinary():
                return 'navfail: ' + str(ex)
    return 'maxit'
