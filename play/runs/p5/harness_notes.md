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

