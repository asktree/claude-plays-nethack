# live — harness notes (bug tracker for the live game)

- setup: `scripts/nh-connect.sh` lacked the executable bit -> `start-remote` died with 'permission denied' (fixed, committed).
- setup: lobby username/password/email prompts parsed as `unknown`, so each keystroke waited the full recheck budget
  (30-70 s per step); `register()` then timed out at 30 s although registration had succeeded. Fixed: any screen with the
  Hardfought banner is `dgl`; register() waits 120 s. Registration on Hardfought returns to the logged-out-looking screen
  briefly, then shows the logged-in lobby.
- the virus editor screen parses as `[extcmd]` (lines starting with `#`): use `exec --at-prompt` for vi_replace_buffer().
- shift 1b #~240: hunt('newt') printed "fight: the newt at (37,5) is gone — NOT killed" and then returned
  {'reason': 'killed', 'kills': ['newt']} — contradictory; unclear whether the newt died.
- shift 1b: dead_ends() returned [] on DL1 while standing at an obvious corridor dead end (58,13) (a spur off the start
  room's east doorway). Harmless, but the explore verdict then didn't list it.
- shift 3 #~1383: pickup('dagger') printed "B - a dagger." when the item actually merged into B (inventory then showed
  "B 7 daggers"); the game message itself says that, but it looked like a new single item. Cosmetic.
- shift 3: the monster list briefly labelled my grown pet "tame little dog" after it had grown to "dog" (#1154); a farlook
  fixed it. Harmless.

## Shift 4 (T:3008-3837)
- #146 / #186 / #778: in the DARK Minetown the hostile mumak reached melee without a pause first (travel()/desmap.walk()
  finished with it ADJACENT at #146; explore() only paused after "The mumak butts! The mumak bites!" at #778, HP 54->28).
  It was a known dangerous monster seen earlier on the level; maybe travel/explore legs should shorten or stop when a
  remembered dangerous hostile (last_seen within N turns) is out of view in the dark nearby.
- #138: desmap.walk() "no progress" on "You stop. Your dog is in the way!" — a retry worked; could retry itself.
- #775-ish: explore() walked me out of the general store and into the mumak; fine otherwise.
- pickup(r'^(?!.*arrow)') worked as an "everything but" pattern — worth documenting.

## Shift 5 (T:3837-5109)
- #1023: the mumak (known, dangerous, last seen 12 turns earlier 3 squares away) was ADJACENT when travel() refused to
  start; no pause had fired when it came into view in the dark. Same issue as shift 4. The engrave turn cost 15 HP.
- #1203: elbereth() garbled twice in a row ("El~ereth" then "E}bereth") and returned after the 2nd garble with a BROKEN
  engraving while the mumak was adjacent; had to call it again. Maybe retry up to 3 times when a hostile is adjacent.
- explore(max_legs=20) covered very little on DL5 (legs are short); max_legs=60-80 works better.
- trek(5,6) on Mines DL5 raised "the way is blocked by fox at (28,17)" although the fox was nowhere near the route (asleep?).
- loot_all() on a floor bag that here() identified as a BAG OF TRICKS went ahead and #looted it (bitten, -10 HP). It could
  refuse a known bag of tricks.
