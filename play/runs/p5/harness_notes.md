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

## Shift 2

1. **travel()'s last step diagonal out of a known shop doorway — again** (#205, T:1979). `travel(35,15)` ended on
   Wonotobo's door (34,16) and raised NavError "You can't move diagonally out of an intact doorway." The shopkeeper stood
   on (35,16), the only orthogonal exit. Same bug as shift 1 #7 (#2821). Expected: wait for the peaceful to move (as
   travel does elsewhere) and step orthogonally, never plan a diagonal step out of a door square.

2. (info) **"harness code on disk is newer than this daemon's core"** from #154 (T:1943) on, although the daemon was
   restarted right before this shift — the core on disk changed mid-shift. Helpers reloaded at #4, #154, #292 as told.

3. **A pause inside sell_offer() loses the offer** (#290, T:2000). The exec paused on "You are beginning to feel hungry"
   during sell_offer('A')'s pickup step; the offer text never reached my output, and `bin/nh history` does not keep the
   "Wonotobo offers 50 gold pieces for your cyan potion." part (only "Sell it? [ynaq] (y)"). I had to redo the offer
   (#302: 1 call, 2 turns). Expected: history keeps the full prompt text; and/or Hungry (not Weak) shouldn't pause in
   the middle of a helper's drop/pickup pair.

4. (minor) `bin/nh history` contains the whole Discoveries menu text (T:1998) — noise from a helper reading `\`.

5. **SEVERE: `bin/nh reload` loaded helpers that need a newer CORE -> ImportError in fight()/travel()** (#342, #405,
   #414; T:2024-2077). After the reloads the obs asked for (#154, #292, #378, #402), play/tactics/combat.py does
   `from nh.danger import coaligned_unicorn`, which the daemon's in-memory core (older) lacks:
   - `fight(36,17)` vs a small mimic: ImportError before the first blow (#342) — fought by hand with `F j`.
   - travel(): "monster_filter error: ImportError(...)" pause on a new bat (#405), then travel() CRASHED in
     fight_trivial() -> auto_fightable() with the bat adjacent (#414) — killed it with `F l` by hand.
   Workaround: manual F blows, `travel(..., auto_fight=False)`. Expected: `reload` should refuse (or warn loudly) when
   the new helpers import core names the running core doesn't have — or the kernel could reload the core modules the
   helpers depend on. Orchestrator: please restart p5's daemon before the next shift.

6. **travel()'s NetHack `_` leg "guessed" me back INTO a shop next to a disguised mimic** (#341, T:2023). From the street
   (33,16), `go_up()` -> travel(64,6): no known path (the town's east door square was never seen), but the first `_`
   travel moved me from (33,16) into Wonotobo's shop to (37,15) (NetHack's travel falls back to "closest reachable
   square" when there's no path), then head_to() stopped at (36,16) next to the small mimic at (36,17). Expected: when
   the harness's own path_to() finds no path, never send `_` (go straight to head_to), and never route through a shop
   next to a remembered mimic.

7. **travel()'s "step back to let a peaceful pass" chose a diagonal step INTO a doorway** (#318, T:2010): from (35,15)
   inside the shop to the door (34,16) -> "You can't move diagonally into an intact doorway." Same family as #1.

8. (info, player lesson) Waiting with `s` next to a disguised mimic unmasks it ("You find a small mimic.", #342). Wait
   with `.` there. Also: a shopkeeper standing on his post (the square inside the door) only steps aside at random and
   walks straight back while you stand IN LINE with him (shk.c shk_move: satdoor -> random step; next move back if
   onlineu). From (36,16)/(35,15)... it took 9 turns at (35,15) before he stepped to (36,17) (off-line) and stayed.
   travel()'s peaceful-waiting could pick a waiting square that leaves the shk an off-line square.

9. (info) With auto_fight=False, `travel()`/`explore()`/`trek()` kept working for the rest of the shift; every newcomer
   still paused with "monster_filter error: ImportError(...)" (#405, #545, #607) — safe, just extra calls. throw() worked.
   I killed a giant bat, dwarf zombie, 2 giant rats, bats and the mimic with a hand-written `mfight()` loop of `F<dir>`.

10. (minor) A step that bumps a displayed, sessile hostile (green mold #545, acid blob #720) printed "X blocks your path."
    and did not attack — good (no acid) — but travel/explore should never try to step into a known passive-acid square.

Worked well: sell_offer()/price_id() (8 offers, lowballing detection), pay(), altar_test(), call_type(), trek() over the
anti-magic field, go_up()/go_down() with PetLost when the cat lagged (it came along both times after a short wait),
explore()'s dead-end/stairs-under-objects hints, pickup() patterns, throw() at an adjacent acid blob.

### Shift 2 — top issues (ranked)
1. **Helpers newer than the running core -> ImportError (`coaligned_unicorn`) in fight(), auto_fightable(), travel()'s
   monster filter** (#342, #405, #414). The reload the obs asks for makes things worse when the core is older. Fix:
   reload must refuse/warn on a core mismatch, or reload the core modules too. Restart p5's daemon before shift 3.
2. **travel() steps diagonally into/out of known shop doors** (#205 out of, #318 into) — still open from shift 1 (#7).
3. **travel() with no known path sends NetHack's `_` anyway**: it "guessed" me back into a shop next to a disguised
   mimic (#341). Go straight to head_to() when path_to() is None; keep mimic squares out of every leg.
4. **A pause inside sell_offer() (Hungry) loses the offer text; `history` drops the "X offers N gold" line** (#290).
5. (minor) Discoveries menu text dumped into `history` (T:1998).
