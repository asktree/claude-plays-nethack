# p5 harness notes (the bug tracker: step numbers, what happened, what you expected)

## Shift 1

1. **(info) The obs said "harness code on disk is newer than this daemon's core ... helpers"** at #695 (T:418).
   `bin/nh --game p5 reload` fixed the helpers part; the CORE part still shows ("only a daemon restart loads it —
   tell the orchestrator"). Not restarting it myself, as instructed. Orchestrator: please restart p5's daemon
   between shifts.

2. **force_box() gives up when interrupted** (#694-#695, T:417). A newt bit me during the #force occupation ("You
   stop forcing the lock."); force_box returned `stopped` after 13 turns instead of continuing. lock.c keeps the
   progress (xlock) when you #force the same box again ("You resume your attempt..."), so it could simply
   re-issue #force while only trivial monsters are around (it re-wielded the sword correctly — good). Cost: 2 calls.

3. **Suggestion: trap-victim corpse piles.** mklev.c mktrap() (3.6.7) puts a human/elf/dwarf/orc/gnome corpse
   (aged 51+ turns) plus 1+ ALWAYS-CURSED items (weapon/tool/food/gem) ON a trap on DL1-4 (arrow, dart, rock, bear
   trap, sleeping gas, rolling boulder...). DL1 here had two: human corpse pile (2,5), dwarf corpse pile (48,6).
   The harness doesn't flag them: an obs note like `!! probable trap-victim pile (trap under it, items cursed)`
   plus an automatic avoid() would stop explore()/travel() from stepping there and pickup() from taking cursed
   items. I used avoid() by hand.

4. **travel()'s last step bumped a wall** (#1485, T:1023, DL2). `travel(39,6)` (a doorway in the bottom wall of the
   room holding '>' (39,5)) from (38,7) paused with "It's a wall." Expected: reach the doorway (orthogonally, from
   (39,7)) or say why not. go_down() from there worked.

5. **travel() tried a diagonal squeeze while the pack weighed > 600** (#2033, T:1330, Mines 1). `travel(6,10)` from
   (7,12): NavError "the step to (6,11) failed; messages: ['You are carrying too much to get through.']" (I carried
   ~810 with a 400-wt splint mail). explore() knows this rule (p4 note); travel()'s own route/last steps should too
   (skip squeezes between two rock/wall orthogonals when inv weight > 600), or at least name the fix.

6. (ok, documented) travel() refused a route over the anti-magic field (36,12) with a clear NavError; trek() crossed
   it. Fine — maybe travel() could auto-cross traps that are harmless to you right now (anti-magic field without
   spellcasting; squeaky board already is).

