# Valley of the Dead helpers (shift 24). Load in the kernel: exec(open('play/runs/p1/valley_helpers.py').read())
import os, heapq
_src = open(os.path.expanduser('~/src/nethack-3.6.7/dat/gehennom.des')).read()
_i = _src.index('MAZE: "valley"'); _j = _src.index('MAP', _i); _k = _src.index('ENDMAP', _j)
VMAP = [list(r) for r in _src[_j+4:_k].rstrip('\n').split('\n')]
VOX, VOY = 2, 2          # screen = des map + (2,2)  (verified: `<` map (66,17) = screen (68,19))
VTRAPS = {(16,7):'spiked pit', (7,4):'spiked pit', (5,3):'sleep gas', (23,14):'board', (62,3):'dart', (28,19):'dart'}
def vcell(x, y):
    mx, my = x - VOX, y - VOY
    if 0 <= my < len(VMAP) and 0 <= mx < len(VMAP[my]): return VMAP[my][mx]
    return ' '
def vpassable(x, y, s):
    ch = s.screen.at(x, y) if s else ' '
    if ch in '-|' and vcell(x, y) not in 'S+': return False     # a wall seen on screen wins (random variants)
    return vcell(x, y) in '.BS'                                   # 'B' = invisible boundary = floor
def vroute(dst, src=None, avoid=(), trap_cost=30):
    s = look(); src = src or s.hero
    avoid = set(avoid) | set(tuple(b) for b in (bad_squares() or []))
    dist = {src: 0}; prev = {src: None}; pq = [(0, src)]
    while pq:
        d, p = heapq.heappop(pq)
        if p == dst: break
        if d > dist[p]: continue
        x, y = p
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
            n = (x+dx, y+dy)
            if not vpassable(*n, s): continue
            if dx and dy and (vcell(x, y) == 'S' or vcell(*n) == 'S' or s.screen.at(x,y) == '+' or s.screen.at(*n) == '+'): continue
            c = 1 + (trap_cost if (n in VTRAPS or n in avoid) and n != dst else 0)
            if d + c < dist.get(n, 1e9):
                dist[n] = d + c; prev[n] = p; heapq.heappush(pq, (d + c, n))
    if dst not in prev: return None
    path = []; p = dst
    while p: path.append(p); p = prev[p]
    return path[::-1]
def vwalk(dst, maxsteps=60):
    p = vroute(dst)
    if not p: print('vwalk: no route'); return None
    p = p[1:][:maxsteps]
    s = walk_path(p)
    print('vwalk: at', s.hero, 'target', dst); return s
def adj_hostiles(s=None):
    s = s or look()
    return [m for m in (s.monsters or []) if m.get('dist') == 1 and not m.get('peaceful') and not m.get('tame')
            and not m.get('statue') and not m.get('pet')]
def eat_wraith():
    s = do('e', quiet=True, force=True)       # Satiated guard: a wraith corpse has 0 nutrition, cannot choke
    msgs = list(s.messages)
    for _ in range(10):
        k, p = s.kind, s.prompt or ''
        if k == 'command': break
        if 'here; eat' in p: s = do('y' if 'wraith corpse' in p else 'n', quiet=True)
        elif 'Continue eating' in p: s = do('y', quiet=True, force=True)
        elif k == 'object': s = do('<Esc>', quiet=True); msgs += s.messages; break
        else: pause('eat_wraith: unexpected ' + k + ' ' + p); s = look(); break
        msgs += s.messages
    print('eat_wraith:', ' | '.join(msgs)); return msgs
def _pri(m):
    d = (m.get('desc') or '')
    return -1 if 'ghoul' in d else 0 if 'wraith' in d else 1 if 'vampire' in d else 3 if 'ghost' in d else 2
UNDEAD_OK = lambda m: not (m.get('ch') in 'ZMVW8B' and 'unidentified' not in (m.get('desc') or ''))
def sweep(targets, max_iter=40, hp_floor=0.6):
    """Kill sleeping graveyard monsters one at a time, eat wraith corpses. Pauses on an adjacent & or L."""
    targets = list(targets)
    for it in range(max_iter):
        s = look()
        if s.kind != 'command': pause('sweep: prompt open'); return 'prompt'
        if s.status.hp < hp_floor * s.status.hpmax: print('sweep: HP low', s.status.hp); return 'hp'
        adj = adj_hostiles(s)
        if adj:
            m = sorted(adj, key=_pri)[0]; d = m.get('desc') or m['ch']
            if m['ch'] in '&L': pause('sweep: DEMON/L adjacent: ' + d); return 'demon'
            fight(m['x'], m['y'])
            s2 = look()
            if not any(mm['x'] == m['x'] and mm['y'] == m['y'] and mm.get('desc') == m.get('desc') for mm in (s2.monsters or [])):
                targets = [t for t in targets if t != (m['x'], m['y'])]
                if 'wraith' in d:
                    fl = farlook(m['x'], m['y']); print('killed wraith; square shows:', fl)
                    if 'wraith corpse' in str(fl):
                        walk_path([(m['x'], m['y'])])
                        if look().hero == (m['x'], m['y']): eat_wraith()
            continue
        h = s.hero
        targets = [t for t in targets if max(abs(t[0]-h[0]), abs(t[1]-h[1])) > 1]
        if not targets: print('sweep: all targets done'); return 'done'
        targets.sort(key=lambda t: max(abs(t[0]-h[0]), abs(t[1]-h[1])))
        p = vroute(targets[0])
        if not p or len(p) < 2: print('sweep: no route to', targets[0]); targets.pop(0); continue
        try: walk_path(p[1:2])
        except NavError as e: print('sweep: step blocked:', e)
    return 'max_iter'
def hold_front(front, turns=20, stop_at=80):
    """Chokepoint hold: fight only what stands on `front` (skip statues), search otherwise."""
    t0 = look().status.turn
    for i in range(turns):
        s = look()
        if s.kind != 'command': pause('prompt'); return 'prompt'
        if 'Stone' in (s.status.conditions or []): pause('STONING'); return 'stone'
        if s.status.hp < stop_at: return f'HP {s.status.hp}'
        m = [m for m in s.monsters if (m['x'], m['y']) == front and not m.get('peaceful') and not m.get('statue')]
        if m: fight(front[0], front[1], max_blows=2, stop_hp=0.3, allow_passive=('cockatrice' in (m[0].get('desc') or '')))
        else: do('s', ok=[r'.*'])
    return f'held {look().status.turn - t0} turns'
print('valley helpers loaded')
