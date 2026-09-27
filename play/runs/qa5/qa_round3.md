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
