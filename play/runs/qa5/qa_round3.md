# QA round 3: mid-game harness tour (wizard-mode game `qa5`)

Tester: QA agent (round 3), 2026-09-27. Game `qa5` (local 3.6.7 build, wizard mode, seed 3131), lawful female
dwarven Valkyrie. Earlier rounds: `play/runs/dev1/qa_late_game.md`, `play/runs/qa2/qa_round2.md`.
Scope: Medusa's level (levitation + blindfold, then reflection), the Castle (passtune / force bolt at the
drawbridge, moat, storerooms, the wand of wishing, a wish through the harness, the trap doors), the
Valkyrie Quest (portal, leader at XL<14 and XL14+, locate/goal levels, Surtur, the Orb of Fate), and the
climb with the Amulet ("mysterious force").
Method: wizard-mode setup (#levelchange, wishes, ^V), then play each task through the kernel helpers as a
player would. Step numbers are the obs header `#N`.

## Raw log

### Setup (Dlvl 1, #2-#21)
- `#levelchange` 13 and wishes via raw `do('<C-w>')` + `do('<wish><CR>')` fine; `inventory()` parses.
- (cosmetic) #2/#4: while a getlin prompt is open the hero's own square is listed as `up stairs (under a
  monster) (39,13)` (the `@` is taken for a monster while `obs.hero` is None).
- ^V menu #21: 3 pages, `f - Portal to The Quest: 14`, `h - medusa: 23`, `j - castle: 25 (tune EBCCD)`. Fine.

### Medusa's level (Dlvl 23, medusa-4 variant: trees, iron bars, a walled building in the west)
- #22 arrival (^V puts you at a random spot on the up-stairs side, here (70,15)): obs `where: The Dungeons
  of Doom / Level 23`, nothing says "Medusa's level". `info` shows `Level 23: [medusa]` only because the ^O
  overview is annotated in wizard mode — on the server that tag doesn't exist. See M1 below.
- M2 (MED-HIGH) #55-#61, #76 **auto-fight melees poisonous snakes although the hero has no poison
  resistance**: `auto-fight: snake at (63,6), garter snake at (64,8)` -> "The snake bites! | The snake's bite
  was poisoned!" (twice; HP 136 -> 101). A plain `snake` (AD_DRST bite) has no NOTES entry, so
  `threat_level()` rates it by difficulty only (6 <= XL13//2) = trivial -> auto_fightable. Without poison
  resistance every poisoned bite (1 hit in 8) has a 1-in-30 "The poison was deadly..." instadeath
  (mhitu.c AD_DRST -> poisoned(..., 30)). Killer bee / pit viper / cobra are covered by notes; `snake`,
  `water moccasin`(noted), `quasit` (DRDX), `rabid rat` (DRCO), `homunculus`... any AD_DRST/DRDX/DRCO
  melee should never be "trivial" unless `game.intrinsics` has poison. Medusa-4 spawns ~10 of them.
- (good) #40-#89 pauses on this snake level were sensible: new monsters with notes (`cobra !! poison +
  blinding spit`, `python !! crushes`, `giant eel !! can DROWN you`), the polymorph trap that turned the
  kitten into a `tame white unicorn` and a black naga into a `peaceful lich` was named in features
  (`polymorph trap (70,14)`), and a pit viper dropping through `trap door (66,7)` showed up as a named
  trap. `-a '.*'` + `--no-monsters` made the snake clean-up affordable.
- M3 (LOW) #107-#111 engulfed by an air elemental (HP 79 -> 27 in 4 turns): `fight()` paused
  `fight: engulfed and HP 51/136 is below 45% — pray if HP <= 1/7 max`; `cont` then just RETURNED (no
  blow; #108 unchanged) — you can't walk away from an engulfer, so the stop only costs a call; then every
  blow paused on HP loss (`fight(stop_hp=0.2)`: "HP 51->41 ... two more like that" x3). A raw
  `do('Fk')` loop with `--hp-pause 0.08` finished it. Suggest: engulfed = keep swinging down to the prayer
  line (prayer is the only other exit), one pause per big hit.
- M4 (LOW) #25 `go_down()` while levitating with no `>` known yet says only `NavError you are
  LEVITATING ...` — the "no '>' known" part (find the stairs first) comes after you land.
- M1 (HIGH) #104-#182 **nothing warns before Medusa's gaze can reach you.** After ^F the obs knew the level
  (down stairs (12,5) inside a walled building, statues everywhere) and `mon('Medusa')` has the right note
  (`GAZE = STONING. Need reflection or be blind`), but the note only appears once Medusa is IN VIEW — and
  the first turn she is in view and awake is the stoning. The naive player flow: `travel(11, 5)` (next to
  the `>`) -> `NavError travel: the door at (10, 5) is locked — ... kick_door(10, 5)` -> `kick_door(10,5)`
  (#182): "As you kick the door, it crashes open! | You meet Medusa's gaze. | You turn to stone..." ->
  `Die? [yn]` (wizard mode; on the server: dead). No reflection, not blind, Dlvl 23 of a water level with
  statues: nothing in obs, no guard in travel/kick_door/explore, no pause before. Suggest: a Medusa-level
  flag (Dlvl 21-24 + the level is mostly water, or ^O/overview, or the statue garden) that makes
  travel/explore/kick_door/open refuse to reveal new squares unless `Blind` or reflection is known worn
  (shield of reflection / SDSM / amulet of reflection in `inventory()` "(being worn)"), and an arrival
  line `!! MEDUSA'S LEVEL: be Blind (blindfold/towel) or wear reflection BEFORE she comes into view`.
- M5 (LOW-MED) #167-#169 the locked-door NavError suggests `kick_door(10, 5)` while LEVITATING; the kick
  fails ("You have nothing to brace yourself against.", a paused message). Mention it (or #force/unlock/
  force bolt) when `Lev` is on.
- M6 (MEDIUM) #185-#188 **blindfolded melee (the no-reflection way to fight Medusa) is blocked by
  contradictory advice**: `fight()` blind says `fight: you are Blind — ... cure it (apply a unicorn horn)
  or fight(x, y) on an 'I' square you know is hostile`; `fight(8, 5)` then raises `PermissionError
  refusing to attack the remembered unseen monster 'I' at (8, 5) while blind ... force=True if it is
  attacking you.` — but `fight()` has no `force` parameter (signature `x, y, stop_hp, max_blows,
  allow_passive, only`). Only raw `do('Fh', force=True)` works (used for Medusa at #189-#197: "You hit it."
  x3, then she left). And "cure it (apply a unicorn horn)" is the wrong advice when the blindness is a
  worn blindfold on Medusa's level — taking it off is death; the harness doesn't tell self-blinding
  (blindfold/towel worn) from a blinding attack.
- (good) #185-#207 while blind: `out of view: Medusa last at (11,5) N turn(s) ago` kept her last position;
  `step('l')` into her unseen square gave NetHack's "Wait! There's something there you can't see!" (no
  attack) and the `I` got the right `!!` note. After eating a floating eye (wished corpse: `eat('m')` was
  NOT refused although the harness never saw it die — fine for a wish; `corpse()` warned about the 1-in-7
  "Rotten food" roll, which then happened: 2 turns unconscious) telepathy labelled everything while blind,
  incl. `kraken, hiding in murky water` and the statues (`a statue of a stone giant`).
- (info) Medusa, hurt, left the level (with telepathy she is nowhere on it; she stood next to the `>` —
  fleeing monsters use stairs). `hunt('Medusa')` -> `no hostile 'Medusa' in view` (expected).
- (b) with reflection (#208-#231): the WISH PROMPT pause inside exec worked (`[exec PAUSED] WISH PROMPT
  OPEN: answer ONLY with cont --reply ...`; `cont --reply 'blessed +2 shield of reflection<CR>'` -> "n - a
  smooth shield."). A ^G'd second Medusa adjacent: `fight(10, 5)` -> one pause "You hit Medusa! | Medusa's
  gaze is reflected by your shield. | Medusa is turned to stone! | You kill Medusa!"; her statue listed as
  `statues: @ (10,5)`. `travel(12, 5)` walked over both statues onto `down stairs (under you)`.
  The Medusa note never changes with reflection worn (the shield is unidentified "smooth shield", so the
  harness can't know) — fine, but M1's guard would need the player to tell it (or check worn SoR/SDSM/
  amulet by name once identified).
- (PASS, round-2 R3) #227 `go_down()` levitating on the `>` -> `NavError you are LEVITATING: you can't reach
  the stairs ... remove the ring/boots of levitation`, no key sent; after `R f` it went down.
- (good) #229 the first Medusa had fled down to Dlvl 24 and stood 6 squares from the up stairs: the arrival
  paused with `new monster: Medusa at (3,7)` + her note BEFORE her move — a blindfold-carrying player gets
  exactly one action to put it on. With the shield she was stoned by her own reflected gaze on the next
  turn (#231).

### Castle (Dlvl 25, arrival by ^V at (8,13) on the drawbridge side)
- (good) #233 arrival: `features: raised drawbridge (14,12); water x19`. Flute: `do('ao')` ->
  `[yn] Improvise? [ynq] (q)`; `n` -> the tune prompt; `EBCCD<CR>` -> "You extract a strange sound from the
  flute! | You see a drawbridge coming down!" and `features: lowered drawbridge (never stand on it or in its
  gate when it may be raised) (13,12)` (#241). The three soldiers pouring out got their `!! may carry attack
  WANDS ... Stay off straight lines` notes (they were in a straight line with me: correct and useful).
- C1 (LOW-MED) #240 the tune prompt "What tune are you playing? [5 notes, A-G]" is classified `[object]`
  (an inventory-letter prompt) instead of `[getlin]` — the `[...]` suffix fools the classifier.
  `do('EBCCD<CR>')` still worked, but any logic keyed on `kind == 'object'` (unit-wise sending that
  stops when a letter "closes" the prompt, helpers that answer object prompts) treats a free-text line as
  an item choice. Same risk for other `[...]`-suffixed getlins.
- (good) #244 `zap('p', 'l')` (striking) at the lowered bridge: "The drawbridge collapses into the moat!"
  plus the debris/force-bolt lines, one pause.
- C2 (HIGH) #244-#254 **grabbed by a giant eel, then drowned while levitating.** In the same zap pause:
  "... It misses! | The giant eel swings itself around you! | The soldier throws a spear! ..." — the grab is
  one line in 15; the pause reason is the generic `message; new monster: giant eel, holding you at
  (13,11)` and the note stays `!! can DROWN you if you're next to water. Step away from water.` — which
  is impossible while held ("You cannot escape"). I put the levitation ring on (#246: the eel did NOT let
  go — `farlook` still "giant eel, holding you"), then `fight(13, 11)` swung once and the eel's next hit
  was "The giant eel drowns you..." -> `Die?` (#254). Levitation does not protect in 3.6.7 (mhitu.c AD_WRAP
  checks only Swimming/Amphibious/sticks). Expected: a dedicated pause `!! HELD by a giant eel next to
  water: its next hit can DROWN you — zap sleep/cold/teleport at it, or kill it this turn; levitation does
  NOT help` (the hero had a wand of sleep), and the eel notes should drop "step away" when held and say
  levitation/flying doesn't protect. A player reading the current note would do what I did.
- C3 (LOW-MED) #255 after "The giant eel releases you." the label stayed `giant eel, holding you` (stale:
  the label is from the first farlook) — the inverse mistake is as bad (a player may think it still holds).
- C4 (LOW-MED) #244-#291 **an iron chain `_` is listed as `altar`** in features (`altar (14,12)`, then
  `altar (15,12)` when the debris moved): `farlook(15,12)` says "an iron chain or an altar (an iron chain)"
  but the feature line keeps "altar" for the rest of the visit. The drawbridge debris always drops chains.
- (good) #257 ^T + `cursor_to()` + `.` teleported fine; `^F` named every trap in the castle (trap doors,
  rust/dart/falling rock). The chest was in the SW tower (12,18) this game (not NE), with the 3.6 burned
  "Elbereth" and a scroll on it; `here()` read it all.
- C5 (LOW) #279 `loot_all()` while levitating: `loot_all(): You can't reach the floor.` — returned the
  message, no hint that levitation is the reason (it worked after `R f`, #287: "q - an iron wand").
- (good) #289 `zap('q')` on the unknown wand: `[exec PAUSED] message; WISH PROMPT OPEN: answer ONLY with
  cont --reply ...`.
- C6 (MEDIUM) #290 **a refused reply kills the paused exec**: `cont --reply '<Esc>'` -> `[exec ERROR]
  PermissionError: refusing Esc/an empty answer at the WISH prompt ...` (good refusal) — but the exec is now
  gone: the correct `cont --reply '2 blessed scrolls of charging<CR>'` answers `[exec ERROR] nothing is
  paused`. The prompt was still open; `do('2 blessed scrolls of charging<CR>')` worked ("r - 2 scrolls
  labeled NR 9"). A refused `--reply` should leave the pause in place (or say "answer with nh do").
- C7 (LOW) #291 `go_down()` on the Castle after the drawbridge was destroyed: `NavError no '>' known on this
  level — but trap door(s)/hole(s) are known at [(48,12), ..., (63,12)]: they lead down (step in on purpose
  with step(dir, force=True)); you land somewhere random below` — the Castle-specific text ("the ONLY way
  down, into the Valley of the Dead (Gehennom) — ready for it?") is keyed on a drawbridge being in
  features, so it disappears once the bridge is destroyed (or before it is seen).
- (PASS, round-2 C3 fixed) #292-#296 plain `step('l')` onto a trap door -> `PermissionError refusing to step
  onto the known trap ... step('l', force=True) if you mean it`; `step('l', 1, force=True)` -> one pause
  `message; level: Dlvl:25 -> Dlvl:26` "A trap door opens up under you! | You arrive at the Valley of the
  Dead..."; `where: Gehennom / Level 26`; the vampire bat there got its shape-shifter note.

### The Quest (portal on Dlvl 14; home "Home 1", locate "Home 3", goal "Home 6")
- (good) #300 the portal level's "faint telepathic message from the Norn" paused; after ^F `features:
  magic portal (70,14)` and `info` records it; ^O "Portal to The Quest." Status `Home 1` parsed, `where:
  The Quest / Level 1`; the multi-line arrival/leader texts arrive complete in `msgs`.
- Q1 (LOW-MED) #312-#320 `travel(70, 14)` (the portal) -> `NavError ... NetHack's travel guessed its way
  ... explore() to find the way, or head_to(70, 14)` and `travel(69, 14)` -> `no known path ... explore()`:
  the map was complete (^F); the portal room's only entrance is a secret door (the corridor dead-ends at
  (64,13)). The advice (explore/head_to) can't help; "search at dead ends (64,13)" would. Also travel to a
  trap square (the portal itself) can never succeed — say "travel next to it, then step(dir, force=True)".
- Q2 (MEDIUM) #340-#347 **walking next to the quest leader IS the visit**: `travel(38, 12)` toward the
  Norn at XL13 — as soon as I was near her she spoke (no #chat needed: STRAT_CLOSE quest_talk) "... you are
  not prepared and shall die at Lord Surtur's hand ... grow more experienced ..." and the game expelled me
  to Dlvl 14 (pause `message; level: Home 1 -> Dlvl:14`). The XL rejection is harmless, but at XL14 the
  next check is ALIGNMENT (wizard mode showed it: `You are currently 10 and require 20. adjust?`, #369):
  on the server a record < 20 is a rejection that counts toward the 7 tries before PERMANENT banishment
  (quest.c MAX_QUEST_TRIES) — no Bell of Opening, no ascension. Nothing in the harness or PLAYBOOK E
  mentions it ("The quest needs XL14" only). Suggest: PLAYBOOK E — check ^X says "piously aligned"
  (record >= 20) before going near the leader; a guard/warning in travel/step when approaching a `peaceful
  <quest leader>` (Norn) below XL14 or without a recent "piously" reading. The leader's label also carries
  `!! much stronger than you (difficulty 23 vs XL 13)` — misleading for a peaceful quest leader (never
  attack her: the note should say "QUEST LEADER — talk, never attack").
- Q3 (MED-HIGH) #347-#353 **travel() keeps going after the level changes under it**: after the
  expulsion pause (`level: Home 1 -> Dlvl:14`), `cont` resumed `travel(38, 12)` ON THE NEW LEVEL: it walked
  (70,14) -> (68,13) (2 turns) and then raised `NavError travel to (38, 12) stopped at (68, 13): NetHack's
  travel guessed its way from (42, 12) ...` (the "from" square is from the old level). Same for any trap
  door / level teleporter / hole / expulsion mid-travel: the target coordinates belong to another level.
  travel()/explore()/hunt() should end (NavError "level changed") when Dlvl/branch changes.
- (wizard only) #369 the alignment prompt "adjust?" came as `[getlin]` (it is a yn_function without
  choices); `y` then the full assignment text ("... Defeat him and return the Orb of Fate to me.").
- (cosmetic) `cont` rejects `--no-monsters` (only `exec` has it); ^V menu page 2 shows `MENU: ''` (no title).
- Q4 (MEDIUM) Lord Surtur (#381-#394): `mon('Lord Surtur')` = WEAP 2d10 x2, CLAW **SAMU** 2d6, resists
  fire, "stalk nasty" — no NOTE at all; at XL14 the label says only `much stronger than you (difficulty 19)`,
  at XL22 nothing. Expected: `!! QUEST NEMESIS: carries the Bell of Opening (needed to ascend); covetous —
  steals the Orb/Amulet (SAMU claw) and TELEPORTS away to heal (usually to the up stairs), comes back`.
  In the fight: #391 "Lord Surtur picks up a glass orb named The Orb of Fate." (the pause reason was
  `hunger: Hungry`), then one `fight(39, 12)` blow ("You hit Lord Surtur!") and he was gone — fight()
  returned silently, `hunt('Lord Surtur')` -> `no hostile 'Lord Surtur' in view`. Nothing says he
  teleported with the Orb. The goal level's features were fine (`raised drawbridge (39,7)`, squeaky boards,
  fire traps, `lava x936`); `mon()` lists "resists: fire ... conveys: fire" but no fire-resistance advice
  for the lava/fire-trap level (the harness knows `game.intrinsics` lacks fire).
- Q5 (LOW) naming: the Orb is "a glass orb named The Orb of Fate" (unidentified crystal ball look) —
  `pickup('crystal ball')` would not match it; `pickup('Orb of Fate')` would. Worth a PLAYBOOK line.

### Climbing with the Amulet (Asmodeus' level, Gehennom Dlvl 27, #396-#425)
- `^W` "Amulet of Yendor" -> "s - the Amulet of Yendor."; ^V menu `l` (asmodeus: 27); `^F`.
- #413 first `go_up()`: normal climb, one pause `message; level: Dlvl:27 -> Dlvl:26` "You climb up the stairs."
- A1 (good, LOW) #420 second climb (after ^V back): **"A mysterious force momentarily surrounds you..."**
  paused as a plain `message`; `go_up()` then raised `NavError pressed '<' at (2, 4) but you are still on
  Dlvl:27: ['A mysterious force momentarily surrounds you...'] — look at why before going on` (so a
  `go_up(); go_up()` script can't run on as if it had climbed — good). The force had teleported me across
  the level to (75,10) (diff = 0 case; it can also drop you 1-3 levels). Suggest: name it ("the Amulet's
  mysterious force: 1 in 4 climbs in Gehennom; you were moved on this level / sent down to Dlvl N — climb
  again") and give it its own pause reason.
- A2 (LOW-MED) #425 the retry `go_up()` from (75,10) -> `NavError travel to (2, 4) stopped at (74, 6): ... the
  only known route crosses the known trap(s) at [(52, 4), (38, 6), (28, 4)]: farlook() the trap(s) and step
  onto one on purpose with ... force=True` — the round-2 wording fix works, but it again walked NetHack's
  "guess" route first (2 squares) and the advice to jump into unknown traps on Asmodeus' level (after ^F
  the far traps are still colour guesses) is risky; "farlook first" is there, good.

## Summary: findings ranked by danger to a real character

| # | Where / step | Finding | Risk |
|---|---|---|---|
| 1 | Medusa #104-#182 (M1) | Nothing warns before Medusa's gaze: no Medusa-level flag, no reflection/blindness check; `travel()`/`kick_door()` opened her door unprotected -> "You meet Medusa's gaze. You turn to stone..." (`Die?`). Her note exists but only once she is in view = too late | HIGH |
| 2 | Castle #244-#254 (C2) | Giant eel grab buried in a 15-line zap pause; note says "Step away from water" (impossible when held); levitation does NOT free you or stop drowning in 3.6.7 -> "The giant eel drowns you..." (`Die?`) while levitating. No "HELD — next hit drowns: zap sleep/cold/tele or kill it now" pause | HIGH |
| 3 | Medusa #55-#76 (M2) | auto-fight/`threat()` treat poisonous `snake` (AD_DRST) as trivial without poison resistance ("The snake's bite was poisoned!" x3); each poisoned bite = 1/30 instadeath. Only NOTES-listed poisoners count | MED-HIGH |
| 4 | Quest #347-#353 (Q3) | `travel()` resumed after a level change (expelled Home 1 -> Dlvl 14) and walked 2 squares on the NEW level toward the old target; same for trap doors/level teleporters mid-travel | MED-HIGH |
| 5 | Quest #340-#369 (Q2) | walking next to the quest leader is the visit (no #chat): at XL14 an alignment record < 20 is one of 7 rejections before permanent banishment (no Bell = no ascension); neither harness nor PLAYBOOK E mentions the alignment requirement; the Norn is labelled `!! much stronger than you` | MEDIUM (run-ender over time) |
| 6 | Medusa #185-#197 (M6) | blindfolded melee: fight() says "fight(x, y) on an 'I' square", fight(x, y) raises "force=True", fight() has no force param -> only raw `do('Fh', force=True)`; blind advice "apply a unicorn horn" is wrong when the blindness is a worn blindfold on Medusa's level | MEDIUM |
| 7 | Quest #381-#394 (Q4) | Lord Surtur has no note (nemesis, Bell of Opening, SAMU claw steals the Orb/Amulet, teleports away to heal); he picked up the Orb (pause reason was "Hungry") and vanished after one blow, fight() returned silently | MEDIUM |
| 8 | Castle #290 (C6) | a refused `cont --reply '<Esc>'` at the wish prompt KILLS the paused exec: the correct `cont --reply '<wish><CR>'` then says "nothing is paused" (the prompt is still open: `nh do` works) | MEDIUM |
| 9 | Castle #240 (C1) | the passtune getlin "What tune are you playing? [5 notes, A-G]" is classified `[object]` | LOW-MED |
| 10 | Castle #244-#291 (C3, C4) | stale eel label ("holding you" after it released); iron chain `_` listed as `altar` all visit although farlook says iron chain | LOW-MED |
| 11 | Quest #312-#320, Amulet #425 (Q1, A2) | travel to the portal: "explore()/head_to()" advice on a fully mapped level (secret door; a trap target can't be travelled to); guess-walk before failing | LOW-MED |
| 12 | Medusa #167-#169, Castle #279 (M5, C5) | levitation-blind advice: locked-door NavError suggests kick_door while levitating ("nothing to brace yourself against"); `loot_all()` "You can't reach the floor." without naming levitation | LOW-MED |
| 13 | Medusa #108, Castle #291 (M3, C7, M4, A1) | engulfed: fight() stops at 45% and cont just returns; Castle trap-door hint lost once the drawbridge is destroyed; go_down levitating hides "no > known"; mysterious force pauses as a plain message | LOW |

Correction to M2's list: homunculus is a SLEEP biter, not poison (it belongs with sleep resistance); the
poison list is AD_DRST/AD_DRDX/AD_DRCO melee (snake, water moccasin, quasit, rabid rat, soldier ant sting...).

Worked well: arrival/level-change pauses everywhere (Medusa, Dlvl 24 with the fled Medusa in view — one
action to blindfold, the Castle, the trap-door fall to the Valley, the portal both ways, the quest texts in
full); reflection vs Medusa (both kills in one clean pause each); `go_down()` levitation refusal; ^F named
every trap (trap doors, portal, polymorph trap, squeaky boards) and summarized water/lava; the drawbridge
states (`raised` / `lowered (never stand on it ...)`); the flute prompts (`Improvise?` as yn) and the
passtune opening the bridge; `zap()` refusing a peaceful in line and destroying the drawbridge;
`loot_all()` on the castle chest; the WISH PROMPT pause for both ^W-style and wand wishes and the Esc
refusal; `step(dir, force=True)` (round-2 C3 fixed); telepathy labels while blind (hiding eels/krakens,
statues named); danger notes for cobra/python/eel/kraken/soldiers/minotaur/fire ant/vampire bat;
`info`/^O recording the portal and "Given quest by the Norn."; go_up() raising NavError after the
mysterious force instead of returning normally.

Not covered (budget): killing Surtur and taking the Orb from him (he teleported off with it; `pickup()`
naming untested beyond the message "a glass orb named The Orb of Fate"); the Castle storerooms and
fighting through the garrison (^T used); the wand of wishing's charge count/recharge; the "sent down N
levels" variant of the mysterious force; the locate level beyond arrival.

State left behind: `qa5` at a command prompt on Gehennom Dlvl 27 (Asmodeus' level) at (74,6), T:214, XL22,
HP 224/224, Hungry, wearing GDSM + shield of reflection + speed boots, ring of levitation (f) off, blindfold
(g) off, carrying the Amulet of Yendor (s), the wand of wishing (q, 1 wish used), wands of sleep (l) and
striking (p), 2 scrolls of charging (r), unicorn horn (h), wooden flute (o). Wizard mode.
