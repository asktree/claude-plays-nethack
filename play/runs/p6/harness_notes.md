# p6 harness notes (the bug tracker: step numbers, what happened, what you expected)

## Shift 1

1. (#1199, T:737 onward) The obs keeps saying `!! harness code on disk is newer than this daemon's core (src/nh:
   only a daemon restart loads it — tell the orchestrator)`. `bin/nh reload` fixed the helpers part; the core part
   needs a daemon restart, which I was told not to do. Telling the orchestrator here. No visible misbehaviour so far.
2. (#7, T:3) explore() paused on the pet's kill ("The kitten bites the newt. | The newt is killed!"). Pet combat
   lines are routine; I had to add `-a` patterns to every exec/cont. Expected: pet-vs-monster lines (bites/misses/
   kills, "X is killed!" when the pet killed it) don't pause explore()/travel() — only damage to me or the pet dying.
3. **explore() blames an immovable boulder instead of pointing at the dead end I stand on** (#2266 T:1525, #2334
   T:1593, #2365 T:1604, DL4).
   - Verdict each time: `blocked: boulders (21, 13) [25 unseen square(s) around] in the way / next to unexplored
     space ... — no down stairs seen yet`. The boulder sits just north of a doorway with rock behind it
     (push_boulder: "You try to move the boulder, but in vain."), so it can never be the way.
   - The real way on was three HIDDEN passages/doors at corridor dead ends: (25,8), (36,10), (39,17). I found each
     with search() at the dead end the obs map showed. dead_ends() listed (25,9) correctly when I asked.
   - Expected: once a push has failed "in vain", drop that boulder from the verdict; when the only other leads are
     corridor dead ends, say `explored — search dead ends [...]` (as it did on DL3), nearest first.
4. (#2193, T:1482) The map kept showing a `)` pile at (9,18) after it was gone (the kitten had taken it). Stepping
   there: "You see no objects here." NetHack's own remembered glyph, so not really a harness bug. But `obs.objects`
   listed it as a real pile. A note like "remembered, not seen" would help (I spent a call walking there).
5. (#2030-#2119) throw() worked well (it refused nothing wrong). Missing piece: after a throw it doesn't say where
   the missile ended up. A hint "the dart lies under the floating eye at (9,18)" would have saved the 45-turn
   wait and the rock fetch.
6. (minor, #1575) force_box() with the quivered dagger worked perfectly (11 turns, sword wielded again at the end).
   pickup() correctly refused the 350-wt large box.

Worked well: fight_until_clear() at the hidden door (2 jackals, 0 damage); farlook() price scan of the whole shop
in one exec (no game time); pay(); the mimic note (`!! MIMIC`, and the pet-adjacent warning); pray() plus
prayer_check(); go_down() keeping the kitten both times; the Elbereth fallback pattern in a fight loop.

### Top issues (ranked)
1. The daemon runs OLDER core code (`!! harness code on disk is newer than this daemon's core`, from #1199 on).
   It needs an orchestrator restart. No misbehaviour seen, but safety fixes in src/nh may be missing live.
2. explore()'s "blocked: boulders" verdict hides the real next step (search the dead ends): 3 times on DL4
   (#2266, #2334, #2365), about 4 calls lost.
3. Pet-combat lines pause explore()/travel() (#7): every exec needed `-a 'The kitten ...'` patterns.
4. Stale remembered object piles in obs.objects (#2193) and no "where did my missile land" info after throw().

## Shift 2

1. (#6, T:1811, first obs of the shift) `!! harness code on disk is newer than this daemon's core` is back although
   the orchestrator restarted the daemon before the shift. Cause: src/nh/kernel.py mtime 19:47:23, daemon (pid 9360)
   started 19:46:00 — a core edit landed a minute after the restart. `bin/nh reload` doesn't clear it (core, not
   tactics). Also: the PREVIOUS p6 daemon (pid 1236, started 19:17:42, PPID 1) is still alive next to the current
   one (daemon.pid = 9360). Expected: a daemon restart kills the old process. Not killed by me (not my role).
2. (#715, T:2417, DL6 stairs) go_down()'s PetLost message says "wait for it (hold(n))", but `hold` is NOT defined
   in the kernel (NameError). Waited with search(3) in a loop instead. Expected: the helper named by the error exists
   (or the message names one that does: search()/rest()).
3. **(#738, T:2437, DL7) SAFETY: `bin/nh reload` (as instructed for the "helpers newer" notice) loaded tactics that need
   core functions the running daemon lacks.** fight_until_clear() died with `ImportError: cannot import name
   'coaligned_unicorn' from 'nh.danger'` with a hostile housecat 2 squares away. danger.py/combat.py on disk are
   from 19:58 (commit d52396b), the daemon from 19:46. The same import sits in fight() (combat.py:544),
   auto_fightable() (:621 — travel/explore auto-fight) and friendly_in_line() (:868 — throw/zap): every combat
   helper was broken. A scan of all `from nh.* import` names in play/tactics against the loaded modules found only
   two missing: nh.danger.coaligned_unicorn and nh.danger.keeps_away (items.py). Workaround: exec'd the exact
   on-disk lines 394-408 of src/nh/danger.py into the loaded nh.danger module (in memory only, no file changed);
   fight_until_clear() then worked. Expected: `reload` refuses (or warns and keeps the old tactics) when the new
   tactics import core names the daemon doesn't have — e.g. run that same import scan before swapping modules in.
4. **(#1470-#1472, T:3244, Sokoban 1a step 12/16) STALE TRAP blocks the solver.** sokoban.solve() raised
   `PermissionError: refusing to step onto the known trap at (33, 13)` although boulder J had filled that pit (step 10,
   whose last push ran right after a pause/resume) and boulder B was visibly resting ON (33,13). `game.rescan_terrain()`
   returned traps {(33,8)..(33,12)} and listed (33,13) as 'plain', yet the step guard still refused afterwards (its trap
   store isn't the one the rescan refreshes). Earlier fills in the same exec (row 14 holes) were forgotten correctly.
   Workaround: after verifying with rescan_terrain() that the game has no trap there, `do('k', force=True)` (the push
   went through: "The boulder fills a pit."). Expected: "The boulder fills a pit/plugs a hole" (and a boulder standing
   on the square) clears the trap from every store; rescan_terrain() overrides the guard's memory.
   RECURRED 5 more times (#1539, #1625, #1665, #1726, #1741): every walk up/down the filled column (33,8)-(33,13) —
   including (33,8), filled by the level's LAST push — was refused as "known trap"; each time rescan_terrain()
   said the game has no trap there (at the end `traps: set()` for the whole level). I wrapped solve() in a loop:
   on that PermissionError, verify with rescan_terrain(), then `do(<dir>, force=True)`. sokoban.solve() then resumed
   correctly every time ("resuming step N after K of its pushes") — the solver itself is solid.
5. (#1063, T:2930, DL7) go_down(with_pet=False) printed "a 3-step detour round (59,6) (the giant spider was last seen
   at (60,6) 1 turn ago, out of view now)" and then walked me to (57,7), next to the stairs the spider was standing on
   (NavError: "giant spider at (58,6) is on (58,6)"). The lurker detour avoided the squares next to the last-seen
   spot, but the stairs themselves were within its reach. My own loop started it (I took "out of view" for "gone"),
   so this is mostly my error; suggestion: when a DANGEROUS hostile was last seen within 2 squares of the go_down()
   target in the last few turns, pause before the final leg instead of walking into its reach.
6. (info) The "helpers newer — bin/nh reload" notice came back 4-5 times during the shift (live edits of
   play/tactics). After the #738 breakage I reloaded only once more (#1350), followed by the same import scan
   (0 missing) — worth building into `reload` itself.

Worked well: elbereth() re-engraving garbled text (up to 3 in a row) and rest_on_elbereth() — ~400 turns on Elbereth
vs ants/spider/dog/dingo/bat/piercer with no melee hit taken; pray()/prayer_check() (94% estimate, success);
sokoban.solve() resuming after every monster pause; fight() on acid blob refused nothing wrong (I kicked it instead);
throw() + autopickup of thrown missiles; the TRAPPED CLOSET pause on DL8; go_up(to='Sokoban') by elimination.

### Shift 2 top issues (ranked)
1. **`bin/nh reload` can load tactics that need core names the running daemon lacks** (#738): fight(),
   fight_until_clear(), auto_fightable() (travel/explore auto-fight) and friendly_in_line() (throw/zap) all raised
   ImportError (nh.danger.coaligned_unicorn) with a hostile 2 squares away. Fix: reload should check every
   `from nh.* import` name against the loaded modules and refuse/warn; restart the daemon when core changes.
2. **Stale trap records at filled Sokoban pits block the step guard** (#1470 and 5 more): "The boulder fills a pit"
   and rescan_terrain() don't clear the guard's trap memory; every pass through the filled column needed force=True.
3. Old p6 daemon (pid 1236) still running after the restart, and core edited 1 minute after the restart (#6).
4. PetLost's advice names `hold(n)`, which doesn't exist in the kernel (#715).
5. go_down() walked me into a dangerous monster's reach at the stairs right after a lurker detour (#1063, suggestion).
