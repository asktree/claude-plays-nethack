# live — notes from the coach (dev session)

The coach watches the public ttyrec (`scripts/watch_ttyrec.py ClaudeAscends --history 3`) and practises the
same character in local games. Read this before each shift; append "ack T<turn>: ..." under an item you acted on.

## 2026-09-27 23:45 UTC — harness update on main (pull + restart the live daemon before the next shift)

`git pull --rebase`, then `bin/nh --game live daemon` (core files changed: game.py, kernel.py, mapscan.py,
render.py, tracker.py). What changes for the live game:

- **Your pet**: `go_down()`/`go_up()` no longer leave the little dog behind on their own. When it was around (in view
  within 7 squares at the start, in view now, or seen on this level in the last 60 turns) but isn't next to you at
  the stairs, they raise `PetLost` and press nothing. Fetch it, wait (`hold(n)`), or `go_down(with_pet=False)` to
  leave it. A pet that stays behind (so, or "still eating") gets a `PET: ... did NOT come along` line in the obs.
- **Weapons**: the harness knows your usual weapon (the long sword, a). The obs warns
  `!! you wield b - ..., not your usual weapon (a - ...)`. `fight()` wields the sword again first if a pick-axe
  from a dig is still in hand.
- **Locked boxes**: `force_box()` pries one open with your known-uncursed spare dagger (b), then wields the sword
  again; never kick boxes with potions in them. Locked doors: `kick_door(x, y)` (never a shop door, nothing in
  Minetown).
- `pickup()` with no pattern leaves heavy things (boxes, heavy armor, big corpses): name them in a pattern.
- `explore()` walks around boulders that NetHack's travel stops at, instead of calling that part "unreachable".
- `dip()`: in MINETOWN, "The flow reduces to a trickle." / "Hey, stop using that fountain!" now read
  `TOWN FOUNTAIN WARNING — STOP`. The next dry-up angers the Watch. Dip for Excalibur outside Minetown.
- Confused or Stunned next to water/lava: moves are refused (a random step into lava burns the bag).
- `call_type(letter, name)` names an unidentified type, e.g. after an engrave-test.

## Observations at T:1014 (from the ttyrec)

- "The little dog steps **reluctantly** over a pair of high boots." dogmove.c prints that only when the square holds
  a CURSED object (the message names the top one): those boots in the DL2 armor shop are cursed if they lie alone
  there, so never buy or wear them. Watch the dog near the other armor too (PLAYBOOK pet-testing).
- **Still XL1 at T:1014.** A Valkyrie is strong enough to fight nearly everything on DL1-4 (let `explore()`
  auto-fight trivial ones; `hunt()` the rest), and XP matters for HP. XL5+ is the Excalibur gate (lawful, dip a long
  sword in a fountain; DL1-2 fountains are fine, not Minetown's). Don't dawdle, but don't avoid fights either.
- Budget: the armor shop is a good pet-theft or price-identify spot later, but $25 buys nothing now. Move on.

ack T1777 (orchestrator): pulled and restarted the live daemon before shift 3. Shift 2 already pet-tested the DL2 boots
(both pairs cursed, not worn); XL2 at T:1777 — shift 3 told to fight more for XP.

## 2026-09-28 00:10 UTC — your shift-1b harness notes are fixed on main (pull; restart the daemon)

- hunt('newt') "gone — NOT killed" vs kills=['newt']: the dog made the kill ("The newt is killed!"). fight() now counts a
  kill by anyone, so no false "NOT killed".
- dead_ends() missed the spur end (58,13): an end square touching the last corridor square and its diagonal (two
  neighbours, both on one side) now counts; an L-bend's corner doesn't.
- (the coach doesn't edit your harness_notes.md — mark those two items done there yourself)
