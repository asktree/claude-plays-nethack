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

7. **travel()'s last step went diagonally out of a KNOWN doorway** (#2821, T:1874, Minetown). `travel(44,13)` from the
   hardware store's door (43,14) (listed as "open door (43,14)" in features before): NavError "the last step from (43,14)
   failed; messages: ["You can't move diagonally out of an intact doorway."]". A peaceful gnomish wizard stood on
   (43,13), the orthogonal exit — so the plain-step fallback chose the diagonal. Expected: never plan a diagonal
   step into/out of a known door square; wait for the peaceful (as it does elsewhere) or say so.

8. **altar_test() re-picks unknown scrolls: a scare monster scroll picked up from the floor before turns to dust on
   the second pickup** (#2689, T:1845). Three of my four scrolls (i, m, n) were floor pickups; all survived, so no
   harm this time. Suggest: before dropping an unknown scroll that the harness saw come off the floor, warn (or skip
   it unless `scrolls=True`), and report the survivors as "not scare monster" (useful information).

9. (minor) `pickup('dagger')` right after `travel()`/`step()` onto my thrown daggers said "there are no objects here"
   (#2474, #2844, #2851): the final step had already auto-picked them up (pickup_thrown). The step's own messages
   ("b - a dagger") weren't shown in my script. A hint like "(travel's last step already picked up: b, p)" would save
   a confused look.

10. (minor) After I sold 2 spellbooks in a 3x3 general store, sell_offer() refused every square (#2612): the free
    squares held the books I had just sold. It refused correctly (it must not take shop goods); just note in
    PLAYER.md that price-ID offers should come before real sales in small shops.

11. (info) explore() paused for giant rats/geckos/newts as "new monster" at XL2 (threat 'normal' for a giant rat at
    XL2, so no auto-fight). Fine, but it cost ~4 calls on Mines 1-2. Maybe rate a giant rat trivial at 25+ HP / AC <= 0.

Worked well this shift: go_down() raising PetLost instead of silently leaving the housecat (#2099/#2110) — the p4
top-2 issue is fixed; force_box() with the spare dagger and re-wield (twice); loot_all(check_traps=3); altar_test();
trek() across the anti-magic field; gas spore / floating eye / mimic danger notes; shop tags now appear INSIDE the
shops ("in Wonotobo's general store" at (35,16)/(35,17), "in Ymla's hardware store" at the door and inside) — the p4
wrong-side-of-the-door bug looks fixed; throw() refusing through peacefuls; the SPECIAL/temple entry pause.

### Top 5 (ranked)
1. **travel()'s own plain steps ignore NetHack's movement rules** — diagonal out of a known doorway (#2821), diagonal
   squeeze with a >600 pack (#2033), bumping a wall next to a doorway (#1485). Three NavErrors in one shift; in a fight
   or a flight this strands a script at the worst moment.
2. **altar_test() can destroy a scare monster scroll** by re-picking unknown floor scrolls (#2689).
3. **force_box() returns 'stopped' when a trivial monster interrupts the #force** instead of resuming it (#694).
4. **Trap-victim corpse piles (3.6.7 mklev.c) aren't flagged**: a trap is under each and every item there is cursed
   (4 piles on DL1-3 this game; I avoid()ed them by hand).
5. **The daemon's CORE is older than the code on disk** (obs line since #695): `reload` fixed the helpers only.
   Orchestrator: restart p5's daemon between shifts.
