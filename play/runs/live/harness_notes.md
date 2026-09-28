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

## Shift 6 (T:5109-)
- #512: pickup('mithril') paused on "You have a little trouble lifting ... Continue? [ynq]" (fine, but maybe pickup could take
  a `burden_ok=True` arg to answer y itself).
- explore() stop message "An ape blocks your path." — the ape was hostile; the wording made me farlook it first. Fine.
- #1878: Sokoban solver refused to push because of a stale remembered `I` at (29,14) (a xan's, killed elsewhere);
  forget_mimic(29,14) did NOT clear it (it's the game's own `I` glyph, not a harness mimic). One manual push fixed it.
  The pause text could suggest the manual push / a clear_I-like fix for `I` markers the player can't get adjacent to.
- #1651: step('k', force=True) into a Sokoban pit to recover daggers worked ("Air currents pull you down").

## Shift 7 (T:6445-)
- #536 T:6822: go_up() on solved Soko2 from (31,12) raised NavError "TELEPORTED during the leg ((31,12) -> (51,16); leg aimed at
  (47,10), at most 8 squares)". No teleport happened: NetHack's `_` travel just ran the whole corridor to the closed door
  (51,15) in one go ("You stop in front of the door."). False positive of the new silent-teleport check (a walked
  distance > leg cap along a real path should not count as a teleport; compare with the path length instead).
- #1025 T:7135: same false TELEPORTED NavError on Soko3 go_up() ((37,7)->(48,17), travel ran to the door). Reproducible.
- #2320 T:8023: fight_until_clear() raised PermissionError "refusing to attack from your Elbereth square" but my previous blow
  (fight(force=True) at a Mordor orc) had already smudged it: engraving_here() read "Elb??c h". The guard should forget the
  engraving after any melee/throw from the square (or re-read it) instead of blocking the next fight.
- rest_on_elbereth() stops for an Elbereth-ignoring Grey-elf — correct; worked well otherwise. elbereth() retries worked (3 garbles seen).
- The giant-mimic-as-boulder check in sokoban.solve() ("unexpected boulders ... often a MIMIC") was spot on (#1096).

## Shift 8 (T:8141-8968)
- No harness problems. rest_on_elbereth, fight/fight_until_clear (puddings split, mimic, water demons, vrock), descend(), buy_protection(),
  dip() loop, pickup(pattern) after an altar drop all worked. fight_until_clear's "attacked from OUT OF VIEW (blast of frost)" after the
  winter wolf was already killed was a harmless false alarm (#272).
- Minor: the pickup of '$' zoo gold at the Soko door opened a 'little trouble lifting ... Continue?' prompt from a plain step (#43) — fine.
- exec budget pause "47 steps / 113s" inside a go_down loop (#1110) — fine, just cont.

## Shift 9 (T:8968-)
- No harness bugs so far. Obs output for a 55-leprechaun hall lists every monster with a note: ~3k tokens per call (a compact
  "N x leprechaun (same note)" grouping would help). The sweep loop + `@` autopickup off worked well.
- #1022/#985 dip() into a fountain for a cursed LAMP works ('The water glows for a moment.' -> uncursed) — worth a PLAYBOOK line:
  fountain dips uncurse ANY item 4/30, not only Excalibur.
- #2698: rest_on_elbereth() stopped correctly for an unseen attacker ("It hits!"); telepathy_scan() then showed an invisible stalker. Fine.
- #2653: fight_until_clear() in the Big Room paused on each new monster (8 pauses in ~10 turns); expected, but a crowd mode ("pause only for
  danger-noted newcomers") inside fight_until_clear would save calls.

## Shift 10 (T:10388-)
- #574-#679 T:10716: explore() walked onto the (undiscovered) quest MAGIC PORTAL at DL13 (70,10) -> Quest Home 1 at XL11 (fire ants around).
  Stepped off and back at once (#682), no leader contact. Not really avoidable once hidden, but on a level flagged "QUEST PORTAL is hidden
  somewhere" explore() could warn/pause before entering each new room's squares? (low priority). Fine otherwise.
- #1-#410: Big Room fights, fight_until_clear/hunt/throw/zap all fine. zap() WandEmpty detection worked (y).
- #406: pickup('dagger') after travel() hit "You have a little trouble lifting ... Continue?" — the travel's final step triggered the pickup
  prompt? (actually the pickup prompt came from pickup('wand') loop? the exec raised RuntimeError in the NEXT pickup since the prompt was open).
- #1661-#1669: after a thief (water nymph) came back into view, EVERY exec paused at once with "THIEF BACK in view" — even inside throw()'s
  inventory() <Esc>, and `-a 'THIEF BACK'` did not suppress it. Two execs wasted; I had to throw with raw `do t / B / l`. The pause should fire
  once per return (not on every snapshot while it stays in view) and honour -a.
- #1685: travel() to the thrown-dagger square picked the daggers up by itself (fine), then pickup('dagger|ring') found only the ring — fine.

## Shift 11 (T:11258-11316)
- #37-#40: offer() on a CROSS-aligned altar paused (exec PAUSED "message") on the successful conversion lines ("You sense a conflict between
  Tyr and Odin. | You feel the power of Tyr increase. | The altar glows white.") instead of classifying them as an outcome (converted /
  "Unluckily ... decrease" = Luck -1). Harmless; had to `drop` the exec.
- Everything else (pray(force=True) holy water detection, dip_into, rub + wish-prompt pause, altar_test) worked cleanly.
