# QA round 7: into the Wizard's Tower via the fakewiz1 portal (wizard-mode game `qa8`)

Tester: QA agent (round 7), 2026-09-27. Game `qa8` (local 3.6.7, wizard mode), lawful dwarven Valkyrie XL28, HP 270,
AC -15, Excalibur, GDSM (MR), shield of reflection, carrying the real Amulet (y), the papyrus spellbook (x = Book),
the Bell (z), two candelabra. Start: Baalzebub's lair (Dlvl 35), T:592. End: wizard3 (Dlvl 42) INSIDE the tower, T:812,
HP 142/270, in a fight with the invisible Wizard of Yendor (^G-created) and his summons. The exec was dropped (see the end).
`#N` = obs step number. At #0 I restarted qa8's daemon (`bin/nh --game qa8 daemon`): the obs said the daemon's core
was older than the disk, and round 6 had tested stale core code. Nothing else was touched. By the end (#352) the obs again said the core on disk was newer than the daemon: src/nh
changed during the session, so late core-side findings may already be addressed on disk.

Route: ^V 46 (fakewiz1) -> walk to the fake tower -> portal -> wizard3 portal room -> random secret door -> beehive
-> 3 more secret doors (a blessed wand of secret door detection, wished for) -> morgue/moat ring -> ladder (35,13).
go_up() hit the MYSTERIOUS FORCE twice (1 in 4 each, stays inside the tower). With about 25 calls left I stopped
climbing and ^G-created the Wizard of Yendor to test the fight handling. The character was clairvoyant (source
unknown, maybe an earlier round), and an earlier round had killed the original Wizard: the `intervene()` harassment
("You notice a black glow surrounding you", "Monsters appear from nowhere!") ran throughout.
Not reached: wizard2, wizard1, the Wizard's room, the Book on the floor.

## Findings (step, what I did, expected, what happened, severity)

### R7-1 [HIGH] go_up()/travel() cross a squeaky board next to kraken water without the eel-water check
- Step 2, wizard3 #280-#292. `go_up()` from (27,15) to the ladder (35,13). It printed only `travel: the only known way
  crosses the squeaky board(s) [(34, 13)] — harmless ... walking over`, then walked onto the ice (32,13) between two
  moat squares.
- `telepathy_scan()` (#119) had shown 2 krakens and a giant eel hiding in this moat, and the level is in Gehennom
  ("ALL water counts").
- Expected: PLAYER.md's eel-water rule. No detour exists, so warn (or refuse while one is in view).
- Happened: no warning. Then "The kraken hits! | The kraken hits! | The kraken brushes against your leg." (the
  DROWNING ATTEMPT pause, which worked).
- Cause (from the traceback): the path goes `_travel` -> `_walk_over(wide, boards)` (nav.py:625 -> :173), which
  steps along its own route without the eel-zone logic. A wrap there drowns you: instadeath.

### R7-2 [MED] The wizard3 portal room's exit is a RANDOM secret door; desmap knows nothing about it
- Step 2, #111-#146. yendor.des: `REGION:(20,06,26,11),unlit,"ordinary",unfilled { ROOMDOOR:true, closed,
  north|west, random }`. That is one secret door, at a random spot on the entry chamber's north or west wall (screen
  x=44..50/y=11 or x=43/y=12..17).
- Happened:
  - `show()` lists the 5 fixed secret doors but not this one.
  - `desmap.route(35, 13)` raised "no way to (35, 13) on the map either — ... or it is sealed".
  - `go_up()` raised a NavError about a stale `I` on the ladder (see R7-9) and never said the real problem.
- I found it by searching: it was at (43,15), after about 40 turns at 5 spots. It opens into the killer-bee hive.
- Expected: `show()`/`route()` say "the portal room has one random secret door in its N or W wall: search from
  (44,12), (47,12), (50,12), (44,15), (44,17)", and route() treats those wall squares as candidate secret doors.
- Check wizard2 and wizard1 for other `ROOMDOOR:true` regions.

### R7-3 [MED] desmap.walk() keeps walking with a non-trivial hostile adjacent
- Step 1, fakewiz1 #90-#92. After a pause I ran `cont`. walk() took 2 more steps with the COVETOUS master lich
  adjacent, and the lich followed and hit me.
- Code (desmap.py:392-395): `if fight and ... s.adjacent_hostiles(): if fight_trivial(s) is not None: continue`. With a
  non-trivial neighbour, fight_trivial returns None and the loop falls through to `walk_path(chunk)` (up to 8 steps).
- Expected: what the docstring and PLAYER.md say, "anything else stops the walk".

### R7-4 [MED] Clairvoyance's "You sense your surroundings." [getpos] browse stops scripts; during it the obs misplaces the hero
- Steps 1-2: #107 (fakewiz1), #145, #172 (wizard3), and once more in a loop that dismissed it itself.
- detect.c `do_vicinity_map()` (intrinsic clairvoyance, every 15 turns with 50%) opens a browse getpos when it
  reveals objects under water (`odetected`), so it keeps happening next to moats.
- Happened:
  - desmap.walk()/search() ended with the prompt open.
  - `obs.hero` was None, and `you @ (34,13)` was stale: the screen showed me on (35,12).
  - My own `@` was listed as `unidentified white @ ... !! could be aligned priest, high priest, shopkeeper` (#107).
  - Monsters the browse drew were all `unidentified ... (not looked at yet)`, and the `I`s it leaves were then
    called "old markers; maybe gone" although they were placed that turn.
- Expected: recognise the prompt, answer `<Esc>` (no game time), carry on, and mark those `I`s as "sensed by
  clairvoyance at T:n".
- A real Valkyrie gets 500-999 turns of clairvoyance from a 200-400 x XL temple donation ("I bestow upon thee a
  blessing"), and Medusa, the Castle and the Wizard's Tower all have moats with objects in them.

### R7-5 [MED] The SWALLOWED pause suggests prayer in Gehennom
- Step 2, #229: `SWALLOWED by a purple worm: ... a wand of digging zapped any direction tears you out; prayer works at
  low HP`. This was Dlvl 42 in Gehennom, where prayer fails (`prayer_check()` itself says "IN GEHENNOM: ... Do not pray").
- Expected: no prayer hint in Gehennom. Otherwise the pause was excellent, and fight() killed the worm from inside.

### R7-6 [MED] The CURSED ITEMS pause promises "inventory() shows which", but a curse doesn't reveal B/U/C
- Step 1, #16-#105: 5 curse pauses from the master lich ("You feel as if you need some help."). `inventory()` still
  showed only the ration that was already known cursed. Every other item's BUC stays unknown after a curse.
  The one visible clue was "The long sword named Excalibur resists!" (#105).
- Expected: "unknown items may now be cursed (not shown): don't swap/remove/put on untested gear; remove curse / holy
  water / an altar".
- Related: the Wizard's harassment curse ("You notice a black glow surrounding you. | You feel a malignant aura
  surround you.", from `intervene()`) paused only as a plain `message` (#54), not as CURSED ITEMS.

### R7-7 [MED-LOW] While held (STUCK), fight_until_clear() swings at other monsters; the STUCK text names a mimic
- Step 2, #243-#247. The owlbear grabbed me at the doorway. `fight_until_clear` sent `Fn` at the gremlin (checked in
  events.jsonl) and got "You cannot escape from the owlbear!", a wasted turn (hack.c: an attack on anything but the
  holder is an escape attempt).
- Expected: when u.ustuck, fight the holder first.
- The named pause says `STUCK — 'You cannot escape from the owlbear!': ... fight() it — a giant mimic hits 3d6 twice`.
  The mimic sentence is hard-coded.
- Two later `Fh` blows at the owlbear also went astray from confusion (1 in 5 each): bad luck, not a bug.

### R7-8 [MED-LOW] hunt() on a covetous monster that just teleported returns at once
- Step 1, #94: `hunt('master lich')` one turn after it teleported away returned `{'reason': "no hostile 'master
  lich' in view", 'turns': 0}`.
- Expected: for a COVETOUS target, say where it goes ("it heals on the up stairs (67,4) and comes back: hold with
  fight_until_clear(hold=...)"), or use `obs.gone`.
- fight() itself gives the right message: "gone — NOT killed (it teleported ...) (a covetous one teleports to heal
  and comes back)".

### R7-9 [LOW-MED] A stale `I` on the stairs blocks go_up() with a misleading reason
- Step 2, #149: `go_up()` -> `NavError travel target (35, 13) is occupied by remembered, unseen monster`. The `I` was
  a clairvoyance marker 20 squares away, behind 4 undiscovered secret doors.
- Expected: check the path first (no known path: secret doors, see R7-2), and treat a far, old `I` as "maybe gone".

### R7-10 [LOW-MED] The portal arrival doesn't say where you are
- Step 1, #111: the pause says `message; level: Dlvl:46 -> Dlvl:42`, and `where: Gehennom / Level 42`.
- Expected: "wizard3 — INSIDE the Wizard's Tower (portal room)". Run `desmap.identify()` automatically on arrival by
  portal, or on the levels where Gehennom special levels can be. Only the player's own identify() call told me.

### R7-11 [LOW] show() omits class-only monsters from the .des
- Step 2: wizard3's `MONSTER:'L',(10,07)` (a random lich at screen (34,13), next to the ladder) is not listed.
  `show()` prints only named ones (vampire lord, krakens, eels). The same probably holds for fakewiz1's `L` on its
  portal square. Expected: `monster (34,13) L (random lich)`.

### R7-12 [LOW] Trivial newcomers during desmap.walk() pause instead of being auto-fought
- Step 1, #63 and #84. `new monster: warg`, adjacent, and `threat('warg')` = trivial. walk() only calls
  fight_trivial() at the top of its loop, and the new-monster pause fires first inside walk_path.
- The second warg had been seen 10 turns earlier 6 squares away, but it paused as NEW again.

### R7-13 [LOW] Routine spell lines still pause inside fight()
- "The air crackles around the master lich." (a fumbled spell, #64), "Something casts a spell at you!" / "A field of
  force surrounds you!" (#162) and "You hear a mumbled curse." each paused as a plain `message`.
- PLAYER.md says monster spell lines are routine inside fight(). The real effects (curse, stun, HP) have their own
  pauses.

### R7-14 [LOW] fight_until_clear() says `clear` with a known crowd one wall away
- Step 2, #149: `clear` after 1 turn. 4 killer bees and the nalfeshnee were still in the dark hive behind the open
  door, as `I` markers. Same family as round 6 F15.

### R7-15 [LOW] A board crossing that travel announced still pauses as `trap`
- #294: `trap at (34, 13)` ("A board beneath you squeaks a D note loudly."), right after travel said "harmless ...
  walking over". The step_onto pause on the fakewiz1 board (#110, "You escape a squeaky board.") is fine: it was a
  step on purpose.

### R7-16 [LOW] Missing or odd danger notes
- A fire elemental has no note. It set me on fire, and "One of your scrolls of teleportation catches fire and burns!
  | The papyrus spellbook glows a strange dark red" (#337). Without fire resistance it burns scrolls, potions and
  spellbooks (the Book!).
- "The cockatrice touches you! | You hear the cockatrice's hissing!" (#225) is a plain `message` pause. In Gehennom
  (no prayer) a named `HISS` pause could say "watch for Stone; no lizard/acid carried".
- A reviving Olog-hai paused as `new monster: Olog-hai` twice (#280, #324). It could say "revived".
- The Wizard's note states covetousness twice ("covetous: steals ... COVETOUS: once it has noticed you ..."), as in
  round 6 F17.

### R7-17 [cosmetic] MYSTERIOUS FORCE pause text
- The pause says "moved on this level or sent down a few". The NavError right after is precise ("kept you on Dlvl 42,
  moved to (25, 7): go back to the '<' and climb again"), so the pause could say the same.
- Worth documenting: inside the Wizard's Tower the force never takes you out of the tower (do.c `was_in_W_tower`).
  From wizard3 it always leaves you on wizard3.

## Worked well
- `desmap.identify()`: fakewiz1 at (34,8), 70 good / 2 bad (the 2 are squares an earlier round dug and froze); wizard3
  at (24,6), 369 / 2.
- `show()` matches yendor.des:
  - fakewiz1: the portal (38,12) -> wizard3, its 4 boards, the vampire lord, the kraken.
  - wizard3: the ladder, the portal -> fakewiz1, the 4 moat monsters and the 5 fixed secret doors.
- `route()`: a 67-step path over the ice with `traps [(37,12),(38,12)]`. `farlook(35,12)` said "ice".
- `desmap.walk()`:
  - stopped cleanly before each undiscovered secret door ("next square (48, 8) is an undiscovered SECRET DOOR:
    search here"), before the board ("a trap on the only way: step_onto(x, y)") and before an `I`;
  - after the zaps it walked through 4 secret doors in one call chain;
  - opening a closed door no longer stops it (round 6 F10 is fixed).
- `step_onto()` for the board and the portal. The portal ("You activated a magic portal! | You feel dizzy ...")
  paused with the level change.
- `go_up()` from INSIDE the tower picks the ladder (35,13) ("stays in Gehennom (leads to Gehennom / Level 41)"), not
  the outer stairs (7,4). It announced the board crossing.
- MYSTERIOUS FORCE: named pause, a precise NavError, and a retry loop on it works (T:765 and T:781).
- `telepathy_scan()`: 24 monsters in 2 turns, including the hidden krakens and eel, the invisible demilich and bone
  devil, a vampire bat on the ladder, and the hive; species counts; "watching 22 noted monster(s)".
- fight() on a covetous monster that teleports: "is gone — NOT killed (it teleported ...) a covetous one teleports to
  heal and comes back" (master lich 4 times, the Wizard once).
- `fight_until_clear(unseen=True)`:
  - killed 3 invisible attackers, reported in `kills` as `'it (unseen)'`;
  - held a doorway against 8 summoned nasties (cockatrice, silver dragon, purple worm, umber hulk, gremlin, owlbear,
    Olog-hai, and a vampire bat that rose as a vampire lord, as its note had warned);
  - its HP pauses follow the fight rules ("-33: two more like that and you're below 50%").
- The new named pauses:
  - SWALLOWED, with the digestion timer (see R7-5 for the prayer slip);
  - "out of the engulfer (killed) — stopped; look around";
  - DROWNING ATTEMPT, which fired even under `-a '.'`;
  - STUCK;
  - `+Stun` and `+Conf`.
- The danger notes for the summons were accurate: purple worm, umber hulk ("fight it blindfolded"), cockatrice,
  gremlin, xan, arch-lich, and the Wizard ("much stronger than you (difficulty 34 vs XL 28)").
- Prompts:
  - ^W wish: `[getlin]`, then `blessed wand of secret door detection<CR>` gave "G - a zinc wand.";
  - ^G's "Creating doppelganger instead; force Wizard of Yendor? [yn]" was parsed with its default;
  - ^V's level prompt.
- `prayer_check()` in Gehennom: "IN GEHENNOM: prayer cannot help ... Do not pray", and it counts the 6 earlier wishes.
- `pickup('Book of the Dead')` also matches the unidentified "papyrus spellbook" (items.py:843-848). This was read in
  the code only; I didn't drop the Book next to a covetous arch-lich to test it live.
- Useful by-product: the Olog-hai zapped "a glass wand" of sleep, so the character's own `q` glass wand is sleep.

## Not tested (budget)
- wizard2, wizard1, the Wizard's sleeping room and the original Book on the floor.
- A THEFT of the Amulet: the ^G Wizard only hit, cursed, summoned and went invisible during the ~15 turns I fought.
- Wishing for the Amulet: the character already carried the real one, so the Amulet effects (mysterious force,
  "Destroy the thief, my pets!") were exercised with it.

## State left behind
qa8 at a command prompt on wizard3 (Dlvl 42) at (27,10), INSIDE the tower (the west strip beside the (27,10) door).
T:812, HP 142/270. Adjacent: a fire elemental and a cockatrice, 4 `I`s (the invisible Wizard of Yendor, the
arch-lich, the iron golem ...). The paused fight_until_clear exec was dropped.
- The ladder (35,13) is reachable via the found doors (30,16) and the ice (32,13); the kraken is at (32,14).
- New item: G = blessed wand of secret door detection (a few charges used).
- One scroll of teleportation burned.
- Excalibur resisted one curse. Other items may now be cursed (5 curse spells plus the harassment curse).
