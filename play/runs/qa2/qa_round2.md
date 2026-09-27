# QA round 2: late-game harness tour (wizard-mode game `qa2`)

Tester: QA agent (round 2), 2026-09-27. Game `qa2` (local 3.6.7 build, wizard mode, seed 77). Started at T:1,
Dlvl 1, XL1, step #2. Round 1 report: `play/runs/dev1/qa_late_game.md`.
Scope: regression checks of round-1 fixes; Castle trap door -> Valley; the vibrating-square level and the
invocation; the Sanctum; the Elemental Planes and the Astral Plane.

## Raw log

### Setup (Dlvl 1, #2-#26)
- `#levelchange` 30 + wishes fine. Every wish/wear message pauses unless `ok=['.*']` is passed (expected).
- The real Bell/Book/Candelabrum were granted (unidentified: "silver bell", "papyrus spellbook",
  "candelabrum (no candles attached)"). `^F` on Dlvl 1: trap types named in `features` (`squeaky board`,
  `bear trap`) — the round-1 C1/W1 fix is visible even on ordinary levels.
- (minor, S1) #29: the scroll that turned up on the up stairs at (4,4) hid them: `features` stopped listing
  `up stairs` while the map showed `?` there. travel_to('<') remembers hidden stairs, but the obs line drops them.

### Regression checks (Dlvl 1, #29-#59)
- R1 PASS (round-1 G3): boxed in a corridor at (8,10) by three red molds (^G), the route's first square
  (9,10) held one. `travel(5,14)`, `go_down()`, `travel_to('>')` all raised
  `NavError travel to (5, 14) did not move: hostile red mold at (7,9), red mold at (7,10), red mold at (9,10)
  adjacent — travel never starts next to one. Fight it (fight()) or step away by hand.` with no key sent
  (T:17 unchanged, no "You move right into"). `step('l',1)`: `NavError step(): red mold at (9,10) is on
  (9, 10) — a plain step there would attack it`.
- R2 PASS (round-1 M4, partial): newt (trivial) + homunculus (`!! sleep bite (you lack sleep resistance)`)
  adjacent: `travel()` did not auto-fight, NavError naming both (#48). After `fight(10,9)` killed the
  homunculus, `travel()` printed `auto-fight: newt at (10,11)` and killed it (T:20); a second wild newt that
  attacked mid-leg was auto-fought too (T:23). The exact "non-trivial monster steps into the dead target's
  square" timing could not be staged with ^G (it always places adjacent).
- R3 PASS (round-1 M8): on `>` with the ring of levitation on, `go_down()` -> `NavError you are LEVITATING:
  you can't reach the stairs ("You are floating high above the stairs") — remove the ring/boots of
  levitation or wait for it to wear off`; no key sent (#59).
- (minor, S2) `auto_fightable(m)` is named in PLAYER.md (explore() row) but is not in the kernel namespace
  (`NameError`, #45); it lives in `tactics/combat.py`.
- (noise, S3) #29: "You hear a E note squeak in the distance." paused inside `travel()` (round-1 #12 noise
  item still open: squeaky-board noise is not in BENIGN).

### Medusa (Dlvl 25, #61-#63) — regression
- R4 PASS (round-1 M1): after `^F` the features line is `up stairs (6,11); down stairs (70,12); magic trap (5,14);
  spiked pit (19,11); sleeping gas trap (21,10); closed door (73,9); water x877 (nearest (7,15))` — stairs
  first, water as a count, trap types named. The gremlin's night-time intrinsic-theft note is good.
- ^V menu (#60, #81): 3 pages parse fine, the castle tune is shown, `[knox: 21]` header kept.

### Castle (Dlvl 29, #65-#77)
- R5 PASS (round-1 C1): `features: ... raised drawbridge (14,12); ... throne (44,12); trap door (48,12);
  trap door (52,12); ... 6 more; water x179`; `obs.features` holds all five trap doors (48/52/56/60/63,12).
- C1 (low, round-1 C5 still open) #68: `go_down()` -> `NavError no '>' known on this level` — no hint that
  the Castle's way down is the trap doors (they are listed in features, so a hint is cheap).
- C2 (low) `info` for the Castle records `fountain, throne, up stairs` only: no trap doors, no drawbridge.
- C3 (minor, API) #76: the known-trap guard says `force=True if you mean it (jumping into a hole/trap door on
  purpose...)` but the helper that raised it, `step('l', 1)`, has no `force` parameter
  (`TypeError: step() got an unexpected keyword argument 'force'`). `do('l', force=True)` works. Either give
  step()/walk_path() a force flag or say "do('<dir>', force=True)" in the message.
- Trap-door fall (#77-#78) PASS: `do('l', force=True)` onto (60,12): one pause `message; level: Dlvl:29 ->
  Dlvl:30` with `A trap door opens up under you! | You arrive at the Valley of the Dead... | The odor of burnt
  flesh ... | You hear groans and moans everywhere.`; obs `where: Gehennom / Level 30`; `^O` `[valley]`.
  `info` listed `Gehennom / Level 30: T32-32` with no features until the next steps (fine).
- ^T (wizard teleport) getpos was driven fine with `cursor_to()`.

### Valley (Dlvl 30, #78-#80)
- After `^F`: `up stairs (68,19); down stairs (3,3); altar (5,12); squeaky board (69,13); dart trap (62,3);
  magic trap ...; trap: squeaky board/hole/trap door (23,14); trap: pit/spiked pit (16,7) ...` — far traps
  keep colour-class guesses until looked at (as documented); the altar shows as plain `altar` (not yet
  looked at; round-1 "Moloch's altar not marked" still applies from afar).

### Vibrating-square level (Dlvl 48, #83-#111)
- `^F` (wiz_map also marks every trap seen) showed the magenta `~` at (24,9): `features: vibrating square
  (24,9); up stairs (53,12); ...` — listed FIRST, not in the monster list (no worm-tail misparse). PASS.
- `travel(24, 9)` walked there (auto-fought a tiger on the way) and the final plain step onto the square was
  NOT refused as a "known trap" (good). "You feel a strange vibration under your feet." paused once (#100).
- V1 (low-med) standing on the square, obs says nothing: `obs.under` None, no `vibrating square (under you)`
  in features (#100-#111). The one-time message is the only clue; an invocation helper can't check "am I on
  the square?" from obs (it would need `^`-look or the tracker to remember (24,9)). `info` doesn't record it
  either.
- Invocation prompts, step by step (all parsed correctly, nothing refused):
  - `a` -> `kind=object 'What do you want to use or apply? [elmoprs or ?*]'`.
  - `a` + `r` (candelabrum, no candles) -> "This candelabrum has no candles." (paused). NB: the task/PLAYBOOK
    wording "attach candles by applying the candelabrum" is wrong — you apply the CANDLES.
  - `a` + `s` (candles) -> `kind=yn 'Attach your candles to your candelabrum? [yn] (n)'`; `y` -> "You attach 7
    candles to the candelabrum." (paused).
  - `a` + `r` -> "The candelabrum's candles burn brightly! | The candelabrum glows with a strange light!"
    (T:50; paused). The "glows with a strange light" line is the confirmation that you are on the square with
    7 candles.
  - `a` + `p` -> "You ring the silver bell. | The silver bell issues an unsettling shrill sound..." (T:51,
    paused). The "unsettling shrill sound" line confirms the Bell was rung on the square.
  - `r` -> `kind=object 'What do you want to read? [q or ?*]'`; `q` -> one pause at T:53: "You begin to recite
    the runes. | You turn the pages of the Book of the Dead... | The floor shakes violently under you! | The
    walls around you begin to bend and crumble! | You are standing at the top of a stairwell leading down! |
    The demilich casts a spell! | The demilich suddenly disappears!" + new monster ettin. The in-game
    `display_nhwindow` --More-- during the crumbling animation was dismissed fine.
  - Pauses: every step paused on its message (5 tool calls with `cont`). Pauses cost no game time, but the
    Book must be read < 5 turns after the Bell — safe here; a helper should do bell+book back to back.
- V2 (medium) after the invocation the harness doesn't know the new `>` under the hero: `obs.under` None,
  `look().under` None, not in features or `info` ("You are standing at the top of a stairwell leading
  down!" is not learned like "There is a staircase down here."). `go_down()` still worked here (#112) because
  it pressed `>` anyway, but `travel_to('>')`/the level record would miss the Sanctum stairs when you come
  back up (you arrive on them).
- V3 (low-med) trap memory is stale after the level changed: `bad_squares()` holds 7 of the 8 new fire traps
  around the stairs; the one under the `%` at (23,10) is missing (the per-level `#terrain` read is not redone
  when the invocation rewrites the map). `path_to(53,12)` (up stairs) and `path_to(24,5)` are None — the
  stairs are ringed by fire traps and a 2-wide moat (`water x63`). See the climb back (below) for how the
  helpers cope.
- Invocation helper needs (for automation): check BUC of Bell/Book/Candelabrum/candles (cursed = fails; the
  harness has `inventory()` buc); verify "on the square" (V1); attach candles by applying the candles (yn
  'Attach ... to your candelabrum?' -> y), accept "N candles" < 7 as a hard stop; light it and require
  "glows with a strange light"; ring the Bell and require "unsettling shrill sound"; read the Book within 4
  turns and require "stairwell leading down"; suppress the per-message pauses for these expected lines but
  keep monster/HP pauses; afterwards record `>` under the hero and re-read #terrain.

### Sanctum (Dlvl 49, #112-#172)
- Arrival via `go_down()` fine; `^O` says `[sanctum]`. After `^F`: `features: up stairs (under you) (65,17);
  unaligned high altar (20,10); closed door ...; fire trap ... 30 more` — the altar is labelled correctly
  (farlook) and sorted right after the stairs. PASS.
- S1 (low-med) #117-#122 `travel(21,11)` -> `NavError travel to (21, 11) did not move (no known path? ...)` —
  but the hero HAD moved (65,17)->(63,17) and 3 turns passed (round-1 M2/W6: unreachable targets are tried
  with NetHack's "guess" travel instead of being rejected up front; the "did not move" text is then false).
  `head_to(21,11)` -> `no reachable frontier left (tried 0) — search for hidden passages, dig, or pick another
  target` (correct: the Sanctum's doors are secret and its walls undiggable; a Sanctum-specific hint would
  help). `travel_to('_')` picked the altar (20,10) and failed the same way.
- ^T into the temple onto (22,11) = a spiked pit: "Sorry..." and a random teleport (game rule).
- Temple entry (#128), one pause with everything: `The high priestess intones: | "Infidel, you have entered
  Moloch's Sanctum!" | "Be gone!" | ... hurls an effervescent potion! ... You feel rather tired. ... summons
  insects! ... You can move again.` + 10 new monsters + HP 254->215. Correct and readable.
- S2 (MEDIUM) **the high priest(ess) of Moloch has no `!!` note** (#125-#143), nor do the ordinary `priest of
  Moloch`s, although `mon('high priest')` shows `MAGC CLRC 2d8, MAGC CLRC 2d8` and `threat()` = dangerous.
  The lich/nalfeshnee get "spellcaster" notes; clerical casters (AD_CLRC) apparently don't. The high priest
  is THE Sanctum boss: summons insects, lightning, fire pillars, geysers, paralysis; plus Moloch's own
  lightning when you hurt it ("Moloch roars in anger: "Thou shalt suffer!"" — reflected, but "You are blinded
  by the flash!" twice, #129/#136). Expected: `!! clerical spellcaster (summons insects, lightning/fire
  pillar, paralysis); attacking it in its temple brings Moloch's lightning — blindness`.
- S3 (medium, round-1 C4 still open) #129-#132: `fight(18,11)` paused after almost every blow (monster
  misses/bites, "You hear a door open.", the priestess's spell lines), with -25..-50 HP per turn: one tool call
  per game turn in the most dangerous fight of the game. I switched to a death wand to stay in budget.
- S4 (low) while blind the adjacent crowd turned into `I` markers and `fight()` refused (by design), so the
  cure (unicorn horn) has to be manual each time; a hint "Blind: apply your unicorn horn (l)" in that refusal
  would help. Worked fine after `a`+`l` ("You can see again.").
- S5 (low) when a monster stands on the altar (barbed devil on (20,10), #128) the altar drops out of the
  features line (same as the stairs covered by a scroll on Dlvl 1).
- S6 (low) the dead priestess's pile at (18,11) was shown only as `% food (pile)`; `here()` listed it fine:
  `... a high priest corpse, a circular amulet, a cursed mace, ... the Amulet of Yendor, 4 spellbooks`.
  `pickup('Amulet')` -> `u - the Amulet of Yendor. | v - a circular amulet.` — the pattern is
  case-insensitive, so it also took the unknown amulet (harmless, but `pickup('Amulet of Yendor')` is the
  safe spelling; worth a line in PLAYER.md).

### Climbing back with the Amulet (Sanctum -> Dlvl 48, #172-#190)
- `go_up()` from inside the sealed temple (#173-#177) walked NetHack's "guess" route to the temple wall, paused
  on "You feel that monsters are aware of your presence." and then raised the generic `no known path?` error
  (same as S1). ^T with the Amulet did not trigger "You feel disoriented"/"Override?" this time (1-in-3).
- `go_up()` from (64,17) PASS: "You climb up the stairs." -> Dlvl 48, arriving on the invocation stairs, now
  recorded as `down stairs (under you) (24,9)` (and in `info`). No "mysterious force" (bottom levels exempt).
- E1 (MEDIUM) **the way back up from the vibrating-square level is always blocked for the helpers.** The new
  `>` is ringed by 8 fire traps and, further out, a 2-wide moat (`water x63`). `go_up()` on foot (#183):
  `NavError travel to (53, 12) did not move (no known path? — the map you know doesn't connect to it:
  explore() to find the way, or head_to(53, 12) ...)` although the whole map is known — the advice is wrong
  (explore/head_to can't help). With the levitation ring on: `go_up()` -> `NavError you are LEVITATING ...`
  (correct), `travel(53,12)` -> the same generic "no known path" (T+1). The real recipe is: levitate (or
  water-walk), step onto a fire trap on purpose (`do('l', force=True)`), travel across the moat, remove the
  ring, go_up(). Expected: NavError naming the blockers ("the only exits cross the known fire traps at ...
  and water: levitate + force=True"), and a PLAYBOOK F/G line about the post-invocation fire ring and moat.
- The forced fire-trap step (#190): "A tower of flame erupts from the floor! | The Book of the Dead glows a
  strange dark red, but remains intact. | Monsters appear from nowhere!" — the post-invocation harassment
  started (zruty, yellow dragon, baluchitherium, jabberwock, carnivorous ape, xan, horned devil adjacent),
  one pause, good. No `!!` notes for jabberwock (4x 2d10), zruty, baluchitherium, xan (leg wounds).
- (low) on the return visit (#182) several named traps fell back to colour-class guesses
  (`trap: falling rock/rolling boulder/statue trap (31,8)`); they were named again a step later (#187).

### Plane of Earth (#192-#206)
- Arrival PASS: status `Earth`, `where: The Elemental Planes / Plane of Earth`, one pause with "Well done,
  mortal! | But now thou must face the final Test... | ... "So thou thought thou couldst kill me, fool."";
  the Wizard (arrived adjacent) has a strong note; after ^F `features: magic portal (46,8)` (named, first).
- The Wizard's "Destroy the thief, my pets!" summons paused as new monsters. With 4 hostiles adjacent every
  movement helper refused; I left via ^V (dig()/tunnelling toward the portal NOT tested — budget).
- (minor) ^V from the endgame shows a 1-page menu with NEW letters (a astral .. e earth); a script that
  reuses letters from the dungeon menu (`M`) silently leaves the menu open.

### Plane of Air (#207-#219)
- Arrival PASS ("What a strange feeling! | You notice that there is no gravity here."); the Wizard and the
  horned devil followed (game rule).
- A1 (MEDIUM) `^F` on Air (and Water) is NetHack's `do_mapping()` on a level without hero memory: it shows a
  temporary map inside `browse_map()` = a getpos "(For instructions type a '?')" (#209). The harness
  reported `[getpos]` correctly and parsed `features: magic portal (60,18)` from that view, but after
  `<Esc>` the portal is gone from `features` and from `info` (#210: `features []`) — the harness only reads
  the screen, and the game forgets. The same holds for a crystal ball / Orb of Fate on these planes.
  Expected: remember portal squares seen on Air/Water (and on every plane in `info`) and let
  `travel()`/`head_to()` aim at them.
- A2 (medium) the map vocabulary breaks the planner on Air: open air is drawn as blank (= "unexplored") and
  clouds as `#` (= corridor): `path_to(60,18)` None; `frontiers()`/`screen_frontiers()` meaningless.
  NetHack's own travel still moves (it walked 2 squares east through the fog before "It hits!" from the
  invisible Wizard paused, #219).
- ^T to (58,18): "Sorry..." + random placement (#216).

### Plane of Fire (#221-#226)
- Arrival PASS: real names for 13 arrivals on the first obs (round-1 P1 fixed); one
  `unidentified yellow H (not looked at yet)` placeholder as documented; `lava x305` summarized; after ^F
  `features: magic portal (27,3); fire trap ...; lava x327`.
- F1 (MEDIUM-HIGH) **Amulet theft is not flagged.** #226, one step into `travel(27,3)`: `[exec PAUSED]
  message; trap at (69, 16); new monster: ...` with msgs "It hits! | It steals the Amulet of Yendor! | A tower
  of flame erupts from the floor under the steam vortex! | ..." — the single event that stops an ascension
  is one line in a flood, with a generic `message` reason. Expected: a dedicated pause reason and obs line
  (`!! the AMULET OF YENDOR was STOLEN — the Wizard teleports to the stairs up/away`) from the message or
  an inventory diff; also a note that the invisible Wizard followed through the level teleport (`I`).
- (low) no notes for fire elemental / salamander / hell hound (possibly suppressed because the harness learned
  fire resistance from "The fire doesn't feel hot!" — fine) and none for the ordinary player-monster
  `wizard called Kevin the Sorcerer` on Astral.

### Plane of Water (#230-#238)
- Arrival PASS: "You find yourself suspended in an air bubble surrounded by water."; `water x1651`
  summarized; ^F again opens the browse getpos (`features: magic portal (60,17)` only while it is open).
- W1 (medium) the bubble interior is blank (= "unexplored" to the harness) — the player can't tell bubble
  from unknown in obs; `path_to(60,17)` None. `travel(60,17)` (#236-#238) moved the hero into open water as
  the bubble drifted: "You can't levitate in here. | You plunge into the water. | Your dagger rusts! | Steam
  rises from the Book of the Dead. | Your candelabrum's candles' flames are extinguished. | But you aren't
  drowning." then "Water turbulence affects your movements. | ... Your pick-axe rusts! | ... Your potion of
  full healing dilutes." — each leg damages inventory; without magical breathing this would be drowning
  territory. The water-step guard only covers plain steps, and `Lev` vanished from the status ("You can't
  levitate in here") while the ring stayed on. Expected: on the Plane of Water, travel/head_to refuse (or
  take single checked steps only inside the bubble) and obs marks the bubble squares.

### Astral Plane (#240-#252)
- Arrival PASS: "You arrive on the Astral Plane! | Here the High Temple of Tyr is located. | You sense alarm,
  hostility, and excitement in the air! ..."; `tame guardian Angel of Tyr` labelled. After ^F:
  `features: aligned high altar (39,7); aligned high altar (9,11); aligned high altar (69,11); closed door ...`.
- A master lich teleported in and cursed items ("You feel as if you need some help." — paused, has a note).
- Altar alignment PASS with caveats (#248-#252): ^T to (39,8) under the altar: "The high priestess intones: |
  "Pilgrim, you enter a sacred place!"". While the `peaceful high priestess of Tyr` stood ON the altar, the
  altar vanished from `features` (S5). A turn later, visible and adjacent: `features: lawful high altar
  (39,7); aligned high altar (9,11); aligned high altar (69,11)`; `farlook(39,7)` = "an iron chain or an altar
  (lawful high altar)". 
- AS1 (low-med) the priest's label LOST the god on re-description: `peaceful high priestess of Tyr` (#248)
  -> `peaceful high priestess` (#252). PLAYBOOK G says to confirm the priest's god by its label/farlook
  before #offer; keep "of <god>" in the label.
- AS2 (low) `info` for the Astral Plane lists `altar [[39, 7], [9, 11], [69, 11]]` without alignments (the
  one learned, lawful at (39,7), isn't stored); no plane records its magic portal.
