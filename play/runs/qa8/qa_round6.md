# QA round 6: desmap on the Gehennom special levels, ladders, telepathy_scan, covetous notes, mimics, throw (wizard-mode game `qa8`)

Tester: QA agent (round 6), 2026-09-27. Game `qa8` (local 3.6.7, wizard mode), lawful dwarven Valkyrie XL28, HP 270,
AC -15, Excalibur (auto-search!), GDSM, shield of reflection, carrying the Amulet (y), the Book (x), the Bell (z),
two candelabra. Start: the Valley, T:463. End: tower3 (Dlvl 36), T:592, HP 270/270, no exec paused.
`#N` = obs step number. Tactics were being edited during the session: I ran `bin/nh reload` three times (#9, #20,
#68); from #20 on the obs said the daemon's CORE (src/nh) was older than the disk (not restarted: orchestrator's
call), so core-side behaviour may lag the tree.

Levels visited: Valley (28), Vlad's Tower tower3/tower2/tower1 (36/35/34), wizard1 (40, outside the tower only),
Orcus Town (39), Juiblex's swamp (31). Not reached: the Wizard's Tower interior (wizard-mode ^T into the sealed tower
answers "Sorry..." and teleports you at random, #147; the fakewiz1 portal route was too long for the budget),
Asmodeus, Baalzebub, the Sanctum.

## Findings (step, what I did, expected, what happened, severity)

### F1 [MED-HIGH] go_down()/go_up() pick the sealed Wizard's Tower ladder from outside (round 5 S2, still open)
- Steps 1-2, wizard1 #133-#144. Standing in the maze outside the tower, `go_down()`.
- Expected: take the real stairs (64,16); the ladder (30,11) is inside the sealed tower.
- Happened: `stairs: using the > at (30, 11): stays in Gehennom (leads to Gehennom / Level 41)`, then `travel: no
  known path ... (head_to)` -> `NavError head_to(30, 11): no reachable frontier left`. Same after ^F (#144).
- Cause (nav.py `_pick_stairs`): the ladder's link was learned in round 5 (`stair_links` = `{(30, 11): 'Gehennom /
  Level 41'}`), the real stairs' link is unknown. The `same`-branch shortcut returns the known-link cell BEFORE the
  ladder check (which only runs when `len(unknown) > 1`) and regardless of the reachability order made in
  `_use_stairs`. A Wizard's Tower ladder always links to a Gehennom level, so it always wins once used.
- Why it matters: on the Amulet climb, wizard2 and wizard3 each have a `<` ladder whose link round 5 learned, so
  `go_up()` there heads for the unreachable ladder and raises, while the Wizard harasses you.
- Fix idea: drop ladders (the farlook's parenthesised part, or the desmap feature `ladder`) and unreachable cells
  before the `same`/`known` logic whenever another staircase exists.

### F2 [MED] desmap.route() doesn't list secret doors in UNSEEN parts of the map
- Step 1, Valley #19: `desmap.route(3, 3)` (the Valley's down stairs).
- Expected: `secret` lists (6,3), the (locked) secret door that `show()` lists and the path goes through.
- Happened: `secret []`; the path is `... (7,3), (6,3), (5,3), (4,3), (3,3)`.
- Cause: `secret` and the +20 cost both require the square to be drawn as a wall now (`s.screen.at(c) in "-|"`).
  An unseen `S` (blank) counts as plain floor, so routes through unseen secret doors look free and aren't flagged.
  `walk()` only stops once the wall has been drawn. Expected: treat an unseen `S` the same way.

### F3 [MED] desmap.route() treats known traps outside the fixed map block as walls; misleading hint
- Step 1, Orcus Town #159: `desmap.route(65, 19)` from the arrival square (2,11), next to a known trap door (2,10),
  in the maze filler west of the town map.
- Happened: `RuntimeError: desmap.route: no way to (65, 19) on the map either (allow_water=True if you can cross
  water)`. `is_walkable()` is False on a `^`. Outside the map block `lay.get()` is None, so the fallback in
  `passable()` rejects it. The intended `trap_cost` detour never applies there, and the hint about water is wrong.
  Gehennom's filler mazes are full of traps.
- The same `allow_water` hint came for the sealed wizard1 tower (#133), where the correct answer is "sealed: enter
  by the ladder/portal".

### F4 [MED] Nazgul has no danger note
- Step 3, Orcus Town #158 scan: `W Nazgul at (6,6) d=5` with no `!!`. `mon('Nazgul')`: `WEAP DRLI 1d4, BREA SLEE
  2d25`, and `note_for('Nazgul', 28)` is empty. Expected: level drain (weapon hit) and SLEEP breath (sleep
  resistance or reflection), stalks. The wraith gets "LEVEL DRAIN touch".

### F5 [MED] telepathy_scan() can leave the level's boss out of its printout
- Step 3, Orcus Town #158: 44 monsters. The print shows the nearest 30 only, and Orcus (COVETOUS, wand of death, at
  distance 63) was in `... 14 more`. The returned list has him with the right note.
- Expected: print covetous, unique and `!!`-noted monsters first (or a `bosses:` line), then the nearest others.

### F6 [MED-LOW] `I` markers flood the monster list; after a scan their note contradicts what was just seen
- tower3 #23 -> #27: the arrival screen showed a 3x7 area. After the arrival `#terrain` read (the event at #24;
  its known-map option doesn't write map memory) the redraw showed a 12x10 remembered area with 8 `I`s. Each got the
  same 3-line note: 24 lines of monster list.
- After scans, `I`s appear or persist: Valley #18, a new `I` at (72,14), where the scan had just shown Jiro's
  ghost. tower3 #249: (19,9), (17,12).
- The note says "if your telepathy doesn't show it, it's MINDLESS: black light / stalker". Yet the scan at #243
  showed a troll at the `I` (25,15) and a leocrotta at the `I` (31,9).
- Expected: one line for several identical `I` notes. After `telepathy_scan()`, label an `I` with what the scan
  saw on that square, or drop it.

### F7 [MED-LOW] A killed covetous monster stays "out of view"
- Step 4, tower3 #217-#262: `^G arch-lich`. It went invisible, `fight_until_clear(unseen=True)` hit the `I`: "You
  destroy it! | Its body crumbles into dust." (#227).
- Happened: `fight_until_clear` reported `kills: ['frost giant']` (arch-lich missing), and the obs kept `out of view:
  arch-lich last at (25,11) N turn(s) ago` for 17+ turns. A dead covetous caster looks alive. This is the round 5 O1
  family: "You destroy it!" doesn't name the monster.

### F8 [LOW-MED] No helper attacks a known hidden mimic
- Step 5, tower3 #271-#275: the mimic at (26,13) (a "boulder") was in `known_mimics()`.
  - `hunt((26, 13))` -> `no hostile (26, 13) in view`.
  - From the adjacent square, `fight(26, 13)` returned `[]` silently, with no turn used and no message.
  - `do('Fb')` worked: "You hit the giant mimic!". Then `fight()` killed it, and `known_mimics()` went to `{}`.
- Expected: `fight(x, y)`/`hunt((x, y))` on a `known_mimics()` square F-attacks it, or at least says why not.

### F9 [LOW-MED] `bin/nh obs` seems to drop a paused exec
- #254: an exec paused on a new monster (mountain centaur). I ran `bin/nh obs` (read-only, to grep a line). The next
  `bin/nh cont` said `[exec ERROR] nothing is paused`, so the rest of the script was lost.
- A player naturally looks with `obs` before deciding. Expected: obs/screen/history leave a paused exec alone, or
  the pause text says that obs drops it.

### F10 [LOW] desmap.walk() gives up after its step opens a door
- Step 1, tower3 #40: after `unlock(30, 11)`, `desmap.walk(21, 13)` -> `desmap.walk: no progress at (31, 11) (['The
  door opens.'])`. It needed a second call. Expected: "The door opens." counts as progress, and the walk goes on.

### F11 [LOW] travel()/go_up() ignore the desmap's locked doors
- tower2 #86: `show()` listed `door (26,10) locked`, but `go_up()` walked the long way round to it and then got
  "This door is locked" (NavError, clear message). Every Vlad's Tower door is locked (tower.des). Expected: when a
  desmap is identified, warn up front ("the only way to the ladder passes the locked door (26,10): unlock first").

### F12 [LOW] Known traps covered by an object or an `I` vanish from the obs `features` line
- tower3 #68: after ^F revealed the spiked pit (31,9), the falling rock trap (29,15) and the bear trap (21,7), they
  dropped out of `features` once an object or `I` was drawn on them. `bad_squares()` still has them, so routes are
  fine. Expected: `spiked pit (31,9) (under an object)`, like the stairs.

### F13 [LOW] auto_fightable() never checks the danger note
- Orcus Town #169: `travel(65, 19)` auto-fought a zruty (note "hits hard (3 attacks, up to ~42 a turn)").
- The docstring and PLAYER.md say auto-fight needs "no danger note", but the code only checks the vampire note and
  `threat_level() == 'trivial'`. Harmless at XL28, but the doc and the code disagree.
- Same call: NetHack's travel wandered 13 turns (T:533-546) into a dead end, and only then did `travel()` report
  `no known path ... head_to ... no reachable frontier left` (path_to was None from the start).

### F14 [LOW] Deadly "stuck" states pause only as a plain `message`
- tower3 #48: engulfed by a lurker above. "The lurker above engulfs you! | Your brass lantern goes out! | The lurker
  above digests you!" was a plain `message` pause. The obs says "you are ENGULFED by it: attack with F + any
  direction", but not that a DIGESTER kills on a timer (total digestion). fight_until_clear() then killed it from
  inside (fine).
- tower3 #249: "You cannot escape from the giant mimic!" (stuck) was also a plain `message` inside travel().

### F15 [LOW] fight_until_clear() says `clear` with a non-trivial hostile just out of sight
- tower3 #55: `clear`, while the second yellow dragon was last seen 2 squares away in the dark room (it came back
  at #56). For Vlad it says "clear — BUT ... left view"; the same caveat would help for any breather or noted monster
  that left view inside the radius.

### F16 [LOW] Round 5's U1 again: a swing at a closed door
- Orcus Town #193: "You harmlessly attack the closed door." A fog cloud had flowed under it
  (`fight_until_clear(unseen=True)`).

### F17 [cosmetic]
- The arch-lich note states covetousness twice ("Covetous: wants the Book ... teleports off to heal; COVETOUS: once
  it has noticed you ...").
- After "You find a giant mimic." the list still says `giant mimic, mimicking a statue` (#246). `[seen: telepathy]`
  leaks into the desc and the out-of-view line (#262).
- telepathy_scan counts "a statue of a bone devil" as a hostile monster (#286, Juiblex).
- The plain `vampire` note lacks shape-shifting (3.6 vampires also become fog clouds and bats; it rose from a fog
  cloud at #186).
- `show()` prints `branch (68,19)` with no detail (Valley: the up stairs to the Castle; tower3: the stairs down to
  Gehennom).
- A `@ wayfarer` ("a human or elf (wayfarer)") had no note and then "disappears!" (#41-#52). I don't know what it
  was.

## Worked well
- `desmap.identify()` found the right map and offset every time: Valley (2,2) 119/0; tower3 (16,6) 210/0; tower2
  (16,6) 136/0; wizard1 (24,6) 376/1; Orcus (32,4) 762/3; Juiblex map 2 (14,4) 871/0. On tower3 a 3x7 arrival view
  gave `ambiguous: True` (correct caution).
- `show()` was right against the .des files: Valley down stairs, branch, 3 locked secret doors, the shrine and the
  fixed traps. Vlad's ladders, the branch, the locked doors and the 10 niche secret doors. wizard1's ladder, the four
  squeaky boards and the moat monsters. Orcus's sanctum altar and 15 doors.
- `route()` correctly finds no way into the sealed wizard1 tower. `walk()` stopped at the locked door with a clear
  message, reached the tower3 ladder, paused on new non-trivial monsters, and Excalibur's auto-search found a secret
  door on the way.
- Ladders: `go_up()` tower3 -> tower2 -> tower1 and `go_down()` tower1 -> tower2 -> tower3 all worked ("You climb
  up/down the ladder."). `unlock()` with the credit card worked twice. travel's NavErrors (locked door, adjacent
  hostile) are clear.
- `telepathy_scan()`: 2 turns, no unexpected pauses, species counts. It shows mimics as "mimicking a
  statue/boulder/fountain/staircase down" and hiding snakes and jellyfish. It seeds the mimic memory: all 6 of
  Juiblex's mimics, including the fake `>` at (40,16), went straight into "mimics remembered here".
- Mimic memory: obs line, `known_mimics()`, `bad_squares()`; `path_to()` and `desmap.route()` route around it;
  killing it clears it (twice).
- COVETOUS notes: `note_for()` gives them for master lich, Juiblex, Vlad, the Wizard, Asmodeus, Baalzebub,
  Demogorgon, Yeenoghu, Dispater, Geryon and the quest nemeses; not for lich or demilich (correct). The live notes
  for Orcus, the arch-lich and Juiblex are right ("much stronger than you (difficulty 36 vs XL 28)").
- `throw('e', 'l')` (blindfold at a troll) refused with the dothrow.c reason, and after `cont` returned `[]`
  without throwing. `throw('b', 'l')` threw the dagger: "The dagger hits the troll!".
- fight_until_clear():
  - handled a lurker above from inside and a vampire-lord shape-shift chain;
  - warned "you stand in line with the yellow dragon ... which BREATHES, with a wall right behind you";
  - reported "clear (beyond the radius: vampire lord at (71,16) d=4)";
  - killed an invisible arch-lich via `unseen=True`.

## State left behind
qa8 at a command prompt on tower3 (Dlvl 36), T:592, HP 270/270, no exec paused. A troll and a mountain centaur
are on the level. The brass lantern went out when I was engulfed (not relit). The +0 dagger (b) lies near the troll
(east of the tower3 central room). New: `E` - 2 blessed food rations.
