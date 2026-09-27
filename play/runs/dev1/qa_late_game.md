# QA: late-game tour of the harness (wizard-mode game `dev1`)

Tester: QA agent, 2026-09-27. Game `dev1` (local 3.6.7 build, wizard mode). Started at T:789, Dlvl 1, XL4, step #128.
Method: power up with wizard tools, then ^V to each late-game level; on each level check `obs`, `info`,
movement helpers (travel / explore / head_to / go_down / go_up), exec pauses, and crashes/stuck prompts.

Findings are logged per level as they happen (raw log), then ranked in the summary at the end.

## Raw log

### Setup (Dlvl 1, #128-#148)
- `#levelchange` 30, wishes via `do('<C-w>...<CR>')` all fine (#131-#140). `W`/`P` fine.
- `^I` in this build opens a "Debug Identify" menu (select items) rather than identifying everything; escaped.
- `^V` + `?<CR>` menu (#150-#153) parses fine over 3 pages; the unselectable `knox: 18` line is shown as a
  `[knox: 18]` header — correct (it has no letter on the raw screen). `<h` picked medusa and closed the menu.

### Medusa's level (Dlvl 28, arrived #154)
- M1 (obs, #154/#156): `features:` lists every water square individually, nearest first:
  `features: water (68,1); water (69,1); ... 1039 more` after `^F`. The up stairs `<` (75,9), down stairs
  `>` (6,9), fountains and the `^` traps are buried in "... N more" — the features line is useless on a water
  level. Expected: water/lava summarized (count or not listed; `}` is on the map anyway) and stairs/altars/
  fountains/portals listed first.
- M2 (travel, #157-#161): `travel(76, 9)` (I mis-read the column; (76,9) is water) walked the hero 3 squares
  toward it (70,3)->(73,6) and then raised `NavError ... did not move (no known path? ...)`. OK-ish; it could say
  "target is water/lava" up front instead of moving first.
- M3 (guard, #161): plain step into water without levitation: `PermissionError refusing to step into the
  water/lava at (74, 6)` — correct. With the ring of levitation on (#165) the same step was allowed — correct.
- M4 (auto-fight, #168-#173) **auto-fight kept fighting a dangerous monster that stepped into its dead
  target's square.** `go_down()` while levitating; `travel` -> `fight_trivial` printed `auto-fight: snake at
  (63,2)` (a snake: trivial at XL30, fine). #171 "You kill the snake!", then the python from (62,2) moved into
  (63,2) and `fight()` swung on: #172 `Fh` "You hit the python!", #173 `Fh` "... The python grabs you!".
  The python carries a `!! crushes.` note and would not have been auto-fightable. Cause: `fight_trivial()`
  checks `auto_fightable` once, then calls the general `fight()` loop, which attacks whatever hostile is
  adjacent until none is left. Expected: under auto-fight, re-check `auto_fightable` for every blow's
  target (or stop after the original targets die) and pause for a newcomer that isn't trivial. A real
  character auto-fighting a jackal while a known soldier ant / cockatrice approaches would melee it unasked.
- M5 (monster labels, #211-#224) **stale identity for same-looking monsters, not fixed even by an explicit
  farlook.** Medusa's snakes hide under water and resurface. `fight()` at #218: "You hit the pit viper!" while
  the list showed `S cobra at (46,2) d=1 <-- ADJACENT` (cobra and pit viper are both blue `S`).
  `farlook(46, 2)` -> `S a snake (pit viper)`, yet `look().monsters` right after still said `cobra at (46,2)`
  (#224). Expected: a farlook result (explicit or automatic) overwrites the label on that square, and a
  monster that was just "hidden under the water"/"hiding under" gets re-looked when it reappears. Here the
  labels are harmless (both dangerous), but the same mechanism can put a wrong danger note or a wrong
  `auto_fightable` verdict on a monster (see M4).
- M6 (fight, #217): `fight()` returned (no pause) while a cobra and a python were still adjacent (the pit
  viper it was hitting had gone under water). Then `go_down()` correctly raised `NavError ... hostile cobra at
  (46,2), python at (48,2) adjacent — travel never starts next to one`. Minor: fight() could say why it stopped.
- M7 (travel over water): with levitation, `travel()`/`go_down()` legs crossed open water fine
  ((74,6) -> (47,2)); the exec pauses were all sensible (snake bites, "It misses!" from an unseen eel, a
  landmine). Pause noise is high on this level simply because of ~15 snakes; no misparsed prompt.
- M8 (go_down while levitating, #232): `go_down()` travelled onto `>` (under Medusa's statue — found fine) and
  pressed `>`: "You are floating high above the stairs." The exec paused on the message; after `cont`,
  `go_down()` simply RETURNED the snap (no exception) and the hero is still on Dlvl 28. A script doing
  `go_down(); explore()` would carry on as if on the next level. Expected: check `Lev` before pressing `>`
  (say "remove the levitation ring/boots first"), and raise NavError whenever the level did not change.
- M9 (Medusa, #227): with the amulet of reflection, `^T` next to her: "Medusa's gaze is reflected by your
  medallion. | Medusa is turned to stone! | You kill Medusa!" — paused once, fine. Her statue then hides `>`;
  obs shows `statues: @ (6,9)` and the stairs were still found by `go_down()` (good).
- `info` records "The Dungeons of Doom / Level 28: fountain, down stairs, up stairs"; the level name comes
  only from the game's ^O (`Level 28: [medusa]` — wizard-mode annotation). OK.

### Castle (Dlvl 29, arrived #237)
- C1 (features, #239-#241) **no drawbridge in `features`, and trap types are dropped.** `^F`-mapped
  castle: features = water 179, trap 11, closed door 11, up stairs, fountain, throne. The raised drawbridge
  `#` at (14,12) (farlook: "raised drawbridge") is not listed at all; after zapping opening (#300) the
  lowered drawbridge at (13,12) shows as `.` and isn't listed either. All 11 traps print as plain `trap`
  although `farlook(48,12)` = "trap door" and (2,14) = "magic trap". The Castle's trap doors (the way to the
  Valley) are indistinguishable from the maze's magic/other traps in obs. Expected: `raised drawbridge`,
  `lowered drawbridge`, and `trap door`/`magic trap`/... (the harness already reads #terrain/farlook).
  Safety: a monster can raise the bridge again — standing on the lowered bridge or in its doorway then is
  death ("crushed"); the harness has no notion of it.
- C2 (travel, #268-#281) **misleading NavError when the only route crosses a known trap.** From the
  castle's west maze, `travel(12, 12)` -> `NavError travel to (12, 12) did not move (no known path? — the map
  you know doesn't connect to it: explore() to find the way, or head_to(...))`. The map is fully known
  (`^F`); the only connection is over the magic trap at (2,14) (NetHack's travel and the harness both avoid
  known traps). `explore()`/`head_to()` can't help. Expected: "the only known path crosses the trap at
  (2,14) (magic trap)". Also: the trap-step guard refuses while levitating even for trap types that
  levitation makes harmless (trap door, hole, pit, bear trap, land mine) — acceptable, but it forces
  `force=True` on every castle-maze trap square.
- C3 (danger notes, #252-#255) **no danger note for an incubus.** `& incubus at (2,12) (NEW)` had no `!!`
  line and `mon('incubus')` gives no note. In one turn it swapped my ring of levitation for a ring of
  adornment ("You float gently to the floor."), took off my gray dragon scale mail (AC -10 -> 2), stole
  800 gold and dulled Wisdom. Over water (Medusa's level, the moat) the levitation swap = drowning. The
  seduction prompt itself ("Shall I remove your boots, sweetheart?" [yn]) paused correctly inside
  `fight()` and `cont --reply n` answered it. Expected: a `!!` note for AD_SSEX/AD_SEDU monsters
  ("removes armor/rings — levitation!, steals"), like the nymph's.
- C4 (pauses, #308-#318) fight_until_clear at the drawbridge paused almost every turn on routine castle
  noise: "You hear a door open." / "You hear a door crash open." / "The soldier throws a spear! | The spear
  misses the lieutenant. | A spear misses you." / "The long sword welds itself to the lieutenant's hand!".
  With a garrison of ~15 soldiers this is one tool call per game turn. Suggest: missiles that miss, "You
  hear ..." and monster-vs-monster hits as routine inside fight/fight_until_clear (HP loss still pauses).
- C5 (go_down, #318): `go_down()` -> `NavError no '>' known on this level`. Correct, but on the Castle it
  could say "no stairs down here: the trap doors at the east end lead to the Valley".
- The "new monster" pause for the garrison had the right `!! may carry attack WANDS (even death)` notes.
  Minor: `out of view:` lists "soldier last at (14,12)" while a soldier is listed in view at (14,12).

### Valley of the Dead (Gehennom Dlvl 30, arrived #321)
- `^F` obs is compact and correct: traps, `up stairs (68,19)`, `altar (5,12)`, `down stairs (3,3)`. `info`:
  "Gehennom / Level 30: down stairs, altar, up stairs" + ^O "[valley]". The altar isn't marked as Moloch's
  (unaligned) — a player could try to #offer/pray there. Minor.
- V1 (auto-fight, #338-#344) **vampire bats are auto-fought as trivial, but in 3.6 a vampire bat can be a
  shapeshifted vampire.** `auto-fight: vampire bat at (5,9)` -> "You kill the vampire bat! | The seemingly
  dead vampire bat suddenly transforms and rises as a vampire! | The vampire hits!" (level drain). The
  new-monster pause did fire for the vampire. Expected: `auto_fightable()` false for vampire bats / fog
  clouds / wolves & bats that may be shifted vampires (at least in Gehennom and Vlad's), with a `!!` note.
- V2 (danger notes): umber hulks listed with no `!!` note (confusing gaze — matters next to water/lava/
  traps); `couatl`, `horned devil`, `Elvenking` also have none. Minor.
- V3 (pause, #333): "Monsters appear from nowhere!" + 8 adjacent monsters: one pause listing them, then
  `go_down()` raised `NavError ... hostile ochre jelly ..., ogre king ..., (8 names) adjacent`. Good.
- V4 (go_down, #362): after `^T` to (12,12), `go_down()` walked through the Moloch temple (the "Pilgrim, you
  enter a sacred place! | You have a forbidding feeling..." message paused once — fine) and stopped at (3,8):
  `NavError ... did not move (no known path? ...)`. Correct: the `>` room at (3,3) is walled off (secret
  passage). The hint "explore() to find the way" is OK-ish; "search for a secret door near (3..5,4)" would
  be better.

### Plain Gehennom maze (Dlvl 31, arrived #365; dark, 2-wide corridors)
- G1 (explore, #365-#687) **explore() quit early on a dark maze with a reachable frontier left.** 106 legs,
  no pauses, then `blocked: boulders [(65, 5)] ... no down stairs seen yet`. `frontiers()` returned `[]`
  while `screen_frontiers()` returned `[(65, 4)]` — a floor square with a `%` on it, next to never-seen
  space; `travel(65, 4)` reached it at once and the maze went on east (the `>` was at (72,17)). Expected:
  explore() also uses the screen frontiers (object-covered squares count). Also: the boulder advice "step
  into one to push it" was given while levitating (you can't push boulders while levitating).
- G2 (head_to, #703-#733): `head_to(75, 19)` worked well leg by leg with a nice status suffix
  (`[during: head_to(75, 19): leg 19 to frontier (73, 16)]`). The minotaur pause had the right note
  ("IGNORES Elbereth; hits very hard").
- G3 (travel/head_to/go_down) **movement helpers step INTO monsters ("You move right into ...").**
  #733: during `head_to`, "You move right into the dust vortex. | The dust vortex engulfs you! | You can't
  see in here!" (blinded). #749: `go_down()` with a vampire bat, owlbear and minotaur adjacent: "You move
  right into the vampire bat." — a wasted turn next to a minotaur (-20 HP) — and only THEN `NavError ...
  hostile vampire bat at (73,16), owlbear at (73,17), minotaur at (74,17) adjacent — travel never starts
  next to one`. So the "travel never starts next to a monster" premise is false when the first square of
  the route holds the monster: the travel command moves into it (with travel's nopick flag NetHack prints
  "You move right into X" instead of attacking, and an engulfer engulfs you). Expected: before any travel/
  leg/final step, if the next route square holds a monster (seen or `I`), raise NavError without sending
  keys. This is exactly the moment a player uses go_down()/travel to escape.
- G4 (engulfed): right after being engulfed, `head_to` raised `NavError ... did not move (no known path?)`
  and `explore()` returned `explored (no reachable frontier left) — search for hidden passages` (the
  "map" was the vortex interior `/-\ |@| \-/`). Expected: both refuse with "you are engulfed" (obs knows:
  `obs.engulfed`). `fight()` then got me out correctly ("You get expelled!").
- G5 (fight): `fight()` paused correctly at HP 95/224 (<45%, "adjacent hostiles can deal ~164/turn").
  After being expelled blind, `fight()` returned without pausing while "It hits! It hits! It butts!" came from
  the unseen minotaur (the `I` refusal while blind is by design) — OK since the message paused.

### Juiblex's swamp (Dlvl 36, arrived #753)
- `^F` obs: map fine, `info` = "Gehennom / Level 36: fountain (60,6), down stairs (3,17), up stairs (74,17)",
  ^O "[juiblex]". Features line again flooded by ~300 `water` entries (see M1).
- J1 (pauses, #758): "Juiblex suddenly appears! | Juiblex engulfs you! | You feel deathly sick." paused with
  `status: +TermIll` — correct and important.
- J2 (travel in the swamp, #772-#774) `go_down()` without levitation paused repeatedly on "You stop at the
  edge of the water." (NetHack's travel stopping in front of a pool). That is a routine travel stop; each
  one costs a pause/tool call in a swamp. Expected: treated as routine inside travel (re-plan the next leg).
- J3 (prompt, #779) "The vrock reads a scroll labeled FOOBIE BLETCH!" opened the game's naming prompt
  "Call a scroll labeled FOOBIE BLETCH:"; the harness paused with `naming prompt open: ... — type a name +
  <CR> or <Esc>` — good. But after `cont --reply '<Esc>'`, `go_down()` had already RETURNED that snap: no
  exception, hero still at (69,14) on Dlvl 36 with two vrocks adjacent. Same class as M8: go_down()/travel()
  return normally when interrupted, so callers must check `obs.status.dlvl`/position themselves; a
  `go_down(); explore()` script would explore the wrong level. Expected: raise NavError("interrupted:
  ...") or resume after the prompt.
- Minor: `F red mold`s and a `@ Woodland-elf` 49-63 squares away are listed (lit level) — fine.

### Orcus Town (Dlvl 41, arrived #784)
- `^F` obs fine; features compact; `info` = "up stairs (2,4), altar (56,11), down stairs (65,19)", ^O "[orcus]".
  The two vrocks that were adjacent on Juiblex's level came along through `^V` (game behavior) and paused.
- O1 (travel + boulders, #790-#805) **travel/go_down/head_to get stuck on a boulder with a misleading
  error.** `go_down()` from the west maze: `NavError travel to (65, 19) did not move (no known path? — the
  map you know doesn't connect to it: explore() ... or head_to(...)); messages: ['A boulder blocks your
  path.']`. `path_to(65, 19)` -> None; `head_to(65, 19)` -> `NavError ... no reachable frontier left (tried
  0) — search for hidden passages, dig, or pick another target`. The map was fully known (^F); the only way
  is along a corridor holding a boulder at (18,12) that NetHack's travel plans through but won't push. After
  one manual push ("With great effort you move the boulder.") the next `go_down()` failed the same way at
  (19,12). Expected: name the boulder ("route blocked by the boulder at (19,12): push it east by stepping
  l") — explore() already reports boulders; travel/go_down/head_to don't. Gehennom mazes are full of
  boulders, so this will come up often.

### Wizard's Tower, outside (wizard1 = Dlvl 42, arrived #808)
- `^F` obs fine. `info`: "Gehennom / Level 42: up stairs (47,4), down stairs [(30,11), (17,16)]" — the `>`
  at (30,11) is the Wizard's ladder INSIDE the sealed tower, recorded as a second "down stairs". The
  two-staircase (branch) logic could pick it; here `go_down()` took the reachable (17,16) and descended
  fine (#837). Suggest: record ladders as ladders (farlook says "ladder") and mark unreachable ones.
- "You hear a B note squeak in the distance." paused (#819) — routine noise (squeaky boards).

### Fake Wizard's Tower with the portal (fakewiz1 = Dlvl 48, arrived #842)
- W1 (features) the magic portal at (38,12) is listed as plain `trap` like the 4 squeaky boards around it;
  only `farlook` tells "magic portal". Same for the Castle trap doors (C1). On the Planes the portal is the
  whole point of the level. Expected: named trap types in `features`/`info` ("magic portal (38,12)").
- W2 `^T` into the fake tower centre: "Sorry..." and a random teleport — game rule, not a harness bug.
- W3 (dig, #869-#888) `dig('l')` from over the moat (levitating) worked through 4 interruptions by an
  arch-lich ("You stop digging." -> "You continue digging." ... "You make an opening in the wall.") — good.
- W4 (danger notes, #889-#903) **`v fog cloud ... !! engulf; mostly harmless.`** — then "You destroy the fog
  cloud! | The fog cloud suddenly reconstitutes and rises as a vampire lord!" and the vampire lord drained
  3 levels (XL 30 -> 27) in 4 turns. Same as V1: in Gehennom (and Vlad's) fog clouds, vampire bats and
  wolves may be shape-shifted vampires/vampire lords; the note "mostly harmless" is dangerously wrong
  there, and `auto_fightable()` may treat them as trivial. The arch-lich/wraith/gremlin notes were right.
- W5 (guard) a plain step onto the squeaky board next to the portal: `PermissionError refusing to step onto
  the known trap at (37, 12) ... force=True if you mean it (... entering a magic portal)` — correct.
- `fight()` paused at HP 88/220 (<45%) — correct.

### Wizard's Tower, inside (wizard3 = Dlvl 44, via the portal, #914)
- The forced step onto the portal: "You activated a magic portal! | You feel dizzy ..." -> `level: Dlvl:48 ->
  Dlvl:44` pause. Good. `info` = "Gehennom / Level 44: up stairs [(35,13), (63,20)], down stairs [(29,20)]":
  the ladder in the sealed central tower and the outer maze's `<` are both "up stairs" (see wizard1).
- W6 (go_up, #916-#934) `go_up()` chose the ladder (35,13) in the sealed centre (walls + moat; no path) and
  walked toward it anyway (49,17)->(44,13) before a hostile stopped it. An unreachable target should be
  rejected up front (path_to is None) instead of letting NetHack's travel "guess" its way closer.
- Pauses were sensible (poison-gas trap blast reflected, blindness, "An arch-lich suddenly appears! ...
  Suddenly you cannot see the arch-lich."). "You hear a C note squeak in the distance." again noise.

### Vlad's Tower, top (tower1 = Dlvl 37, arrived #938)
- `^F` obs and `info` fine ("Vlad's Tower / Level 37: down stairs (27,11)"; ^O "Vlad's Tower: levels 39 up to
  37"). Vlad got a strong note: `!! LEVEL DRAIN bite; strong.; stronger than you (difficulty 32); fast (speed
  26)`; `threat('Vlad the Impaler')` = dangerous; the throne shows up in features once seen.
- `go_down()` opened the door on the way ("The door opens." not paused — good), paused on "Vlad the Impaler
  drinks a dark green potion!", then raised `NavError ... hostile Vlad the Impaler at (22,9) adjacent` after
  "Vlad the Impaler suddenly appears! ... bites!". Correct behaviour.
- (tester note: one of my exec scripts produced no `--- stdout` block at all — probably a NameError in my own
  code; the harness error format just didn't match my filter. Not counted as a finding.)

### Vlad's Tower bottom (tower3 = Dlvl 39, #952)
- `^V` `49<CR>` from Vlad's Tower lands on Dlvl 39 (the game clamps to the branch) — expected. A `B vampire
  bat` there had no note (V1). Vlad followed through `^V` (adjacent follower). The vibrating-square level
  was NOT visited (budget); it is a plain maze, so G1/G3/O1 apply.

### Plane of Fire (endgame, #959)
- Arrival: "Endgame prerequisite: Q - the Amulet of Yendor. | ... The Wizard of Yendor suddenly appears!".
  Status shows `Fire` in the Dlvl slot and `where: The Elemental Planes / Plane of Fire` — parsed fine.
  `}` is correctly classified as `lava` here (204 squares; see M1 for the flood of the features line).
  The Wizard's note is good ("steals the Amulet ...; much stronger than you").
- P1 (monster labels, #959) **on a crowded level most monsters are labelled with a COLOUR word.** The
  arrival obs listed `& red at (63,10)`, `: orange at (69,9)`, `: orange at (73,8)`, `E yellow at (60,8)`
  ... with no danger notes; farlook says barbed devil / salamander / fire elemental. The monitor describes
  8 cells per step (`describe` events in events.jsonl), and until a monster's turn comes it shows a colour
  placeholder. On the Planes (40+ monsters in view) that is dozens of steps of wrong/absent labels.
  Expected: an explicit "unidentified" label (`& ? (not looked at yet)`) and prioritising the nearest/
  most dangerous glyphs; or describe all new cells in one go on arrival (farlook costs no game time).
- P2 (pauses, #966) the batched descriptions keep producing "new monster: fire elemental at (27,6), hell
  hound at (21,2), fire vortex at (21,5), barbed devil at (11,20)" pauses on later steps — even inside a
  `farlook()` call (its internal `do(".")` at nav.py:73 paused my info-only script). Expected: farlook()
  and other no-time helpers don't pause on monitor events; arrival monsters pause once.

### Astral Plane (#971)
- Arrival messages paused once; `tame guardian Angel of Tyr` labelled correctly. Colour placeholders again
  on arrival: `A white at (54,15)`, `A white at (57,17)`, `A white at (58,20)` (P1); they resolved to
  "Angel of Moloch" a step later. Angels of Moloch have no `!!` note.
- After `^F`: features = 3 altars + 9 closed doors; `info` = "Astral Plane: altar [[39,7],[9,11],[69,11]]".
  farlook gives "aligned high altar" for all three; neither obs nor info carries an altar ALIGNMENT, so
  the one thing that matters on this level (which altar is lawful) has to be found by hand.

State left behind: `dev1` is on the Astral Plane, T:1128, XL29, Vlad + a lich + a white dragon adjacent,
wizard mode. `^V` from the endgame only offers the Planes, so the game can't go back to the Dungeons.

## Summary: findings ranked by danger to a real character

| # | Level / step | Finding | Risk |
|---|---|---|---|
| 1 | Maze #733, #749 (G3) | travel/head_to/go_down step INTO a monster on the first route square ("You move right into the dust vortex" → engulfed + blinded; "... into the vampire bat" → a wasted turn next to a minotaur, -20 HP), THEN raise "hostile adjacent" | HIGH: happens when you use go_down/travel to escape |
| 2 | Medusa #168-#173 (M4) | `fight_trivial()` → `fight()` keeps swinging at whatever moves into the dead target's square (a python with `!! crushes` after a snake) | HIGH: auto-fight bypasses the danger gate |
| 3 | Valley #344, fakewiz #891 (V1, W4) | vampire bats / fog clouds treated as trivial / "mostly harmless" and auto-fought; they are shifted vampires: a vampire lord drained XL 30→27 in 4 turns | HIGH in Gehennom & Vlad's |
| 4 | Castle #252 (C3) | no danger note for incubus/succubus: swapped off the ring of levitation (drowning over water), removed GDSM (MR), took gold | MED-HIGH |
| 5 | Medusa #232, Juiblex #779 (M8, J3) | `go_down()` RETURNS normally without changing level (levitating: "floating high above the stairs"; interrupted by the naming prompt) — `go_down(); explore()` runs on the wrong level | MEDIUM |
| 6 | Medusa #218-#224, Fire #959, Astral #971 (M5, P1) | wrong monster labels: stale same-glyph label kept even after an explicit `farlook()` (cobra vs pit viper); colour-word placeholders (`& red`, `: orange`, `A white`) with no notes for monsters not yet described (8 per step) | MEDIUM |
| 7 | Gehennom maze #687 (G1) | `explore()` quits ("blocked: boulders ...") with a reachable frontier left: `frontiers()`=[] but `screen_frontiers()`=[(65,4)] (object on the square) | MEDIUM (slows; looks "done") |
| 8 | Medusa, Castle, fakewiz, Astral (M1, C1, W1) | `features` flooded by hundreds of water/lava squares (stairs buried in "... 1039 more"); raised/lowered drawbridge missing; trap types dropped (trap door, magic portal = "trap"); altar alignment missing | MEDIUM (slows; drawbridge crush risk invisible) |
| 9 | Orcus #802, Castle #281 (O1, C2) | NavError says "no known path? — explore()/head_to()" when the real blocker is a boulder ("A boulder blocks your path.") or the only route crosses a known trap; `path_to`/`head_to` also fail without naming it | MED-LOW (slows) |
| 10 | Wizard's Tower #916-#934, wizard1 (W6) | ladders in the sealed tower recorded as stairs (two `>`/`<` per level); `go_up()` walks toward the unreachable ladder before failing | LOW-MED |
| 11 | Maze #733 (G4) | engulfed: `head_to` says "no known path", `explore()` says "explored" instead of "you are engulfed" | LOW |
| 12 | Castle #308-#318, Juiblex #772, fakewiz #966, towers (C4, J2, P2) | pause noise: "You hear a door open", missiles missing, "You stop at the edge of the water.", "You hear a B note squeak", monitor batches pausing inside `farlook()` | LOW (1 tool call per game turn in fights) |
| 13 | various (M2, M6, C5, V2, V4) | minor: travel to a water target moves first then fails; fight() returns silently with hostiles adjacent after one hides; no hints for "Castle: use the trap doors"/"secret door"; umber hulk, Angels, couatl without notes; `out of view` duplicates a monster in view; Valley altar not marked as Moloch's | LOW |

Worked well: the water/lava step guard (refused on foot, allowed while levitating; `}` is classified as
lava on the Plane of Fire), the trap/portal guard (force=True needed), reflection vs Medusa, travel over
water while levitating, `head_to` in a dark maze, `dig()` resuming through interruptions, prompt
detection (seduction [yn], naming getlin, 3-page ^V menu, endgame menu), level-change / TermIll / HP-stop
pauses, danger notes for soldiers, minotaur, arch-lich, Vlad, the Wizard, and `info` naming the special
levels (via ^O).

Not covered (budget): the vibrating-square level (plain maze: G1/G3/O1 apply), falling through a Castle
trap door, Asmodeus/Baalzebub, the Sanctum, the Earth/Air/Water planes.
