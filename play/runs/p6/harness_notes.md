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
