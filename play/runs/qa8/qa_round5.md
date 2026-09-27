# QA round 5: Vlad rematch, the Wizard's Tower, the Amulet climb (wizard-mode game `qa8`)

Tester: QA agent (round 5), 2026-09-27. Game `qa8` (local 3.6.7 build, wizard mode, seed 808), lawful female
dwarven Valkyrie. Setup at #14-#51: `#levelchange 28` (HP 270), wished +3 GDSM, +3 shield of reflection, +3 speed
boots, +3 gauntlets of power, amulet of life saving (all worn), blessed +3 Excalibur (wielded: note that it gives
drain resistance, so Vlad's bite never drained), wands of cold (o), digging (p), sleep (q), plus death (g) from
the start; brass lantern (r), unicorn horn (s), 3 blessed scrolls of teleportation (t), 7 blessed wax candles (u),
blindfold (e), pick-axe (f). AC -15.
Earlier round: `play/runs/qa7/qa_round4.md`. Method: wizard-mode moves (^V, ^F, ^T, ^G, ^W), then the kernel
helpers as a player would use them. `#N` = obs step number.

**Setup note (harness dev): qa8's kernel was running a stale `hunt()`.** The daemon started at 12:19:16. The
`hunt()` follow feature (commit bc154df) reached `play/tactics/combat.py` at 12:23:29 and was never loaded. At #143
and #146 `hunt('Vlad')` returned `lost: the Vlad the Impaler is out of view` with no follow step. The loaded code
object had no `chase` variable and still carried the old docstring. (`inspect.getsource` reads the file on disk,
so it is no proof of what is loaded.) I ran `bin/nh --game qa8 reload` at #146, and everything after that uses the
current code. p1, p2 and p3 are probably also on old tactics unless they were reloaded after 12:24, and nothing
tells a player so.

## Raw log

### Vlad's Tower, tower1 (Dlvl 34), lantern off (#57-#135)
- #57 ^V menu -> tower1, arriving at (29,9). #59 ^F: ladder `down stairs (27,11)`, throne (22,11), 7 doors. The
  niche secret doors are not shown (correct).
- #64 during `travel(20, 9)`: "The fog cloud flows under the door." A niche vampire in fog form, adjacent on the
  secret door (27,8). Its note ("a vampire can take this shape ... treat it as one") is right. #66 `fight(27, 8)`:
  "You destroy the fog cloud! | The fog cloud suddenly reconstitutes and rises as a vampire!" The paused fight
  stopped cleanly.
- #68 (PASS) `fight(28, 9)`: `fight: the vampire stepped away from (28,9) to (29,9) (d=2) — NOT killed; hunt((29,
  9)) goes after it`. #71 `hunt('vampire')` -> killed.
- #88-#109 `fight_until_clear(radius=3, hold=10, unseen=True)` in the throne-room doorway (19,10). A vampire bat
  came, turned into a fog cloud (#100) and then a vampire (#101), and was killed. A blue dragon was also killed.
  Result: `{'reason': 'held', 'turns': 14}`.
  - **O1** From #102 on, obs kept `out of view: fog cloud last at (19,9) ...; vampire bat last at (19,8) ...`.
    Both are shapes of the vampire that had just been destroyed. They look like two more vampires still around.
- #110 Vlad first seen, on the throne at (22,11), zapping a wand of striking ("Boing!").
  - (PASS) His note: `LEVEL DRAIN bite; strong, very fast (26). Carries the CANDELABRUM (needed to win); covetous:
    hits and runs, flees to heal — in the dark he vanishes between blows: fight from a lit spot / wait with `s` for
    him to come back. Shape-shifts only once he has lost the Candelabrum. NO corpse: the Candelabrum drops on his
    square (pickup('Candelabrum')).; much stronger than you ...`. The facts are right (makemon.c gives him the
    Candelabrum; mon.c pickvampshape keeps his shape while `mon_has_special`). The ".;" is cosmetic.
- #111-#113 `hunt('Vlad')` (the old code, see the setup note). Each wand zap paused (fine). At #113: "You hit
  Vlad the Impaler! | Vlad the Impaler suddenly appears!". This is covetous harassment: wizard.c `tactics()`
  makes him jump next to you (mnexto) 1 turn in 5.
  - **H1** fight() printed `the Vlad the Impaler stepped away from (22,11) to (20,11) (d=1) — NOT killed;
    hunt((20, 11)) goes after it`, and hunt() returned `fight() stopped with it still next to you (see its
    message)`. The same monster was still adjacent, one square over, yet both helpers stopped.
- #114 `fight(20, 11)`: one blow, then `is gone — NOT killed ... (a covetous one teleports to heal and comes
  back)`.
- **(PASS) #121-#129 `fight_until_clear(radius=3, hold=20, unseen=True)` in the dark room killed Vlad.** Pattern:
  he appears adjacent ("suddenly appears" or a wand zap), gets one Excalibur blow, and vanishes. It took 4
  exchanges, T:240-250, and HP never went below 244/270. Every exchange paused on his messages, so it needed 4
  `cont`s. At #129: "You destroy Vlad the Impaler! | Vlad the Impaler's body crumbles into dust."
- (PASS) #135 `pickup('Candelabrum')` took `v - a candelabrum (no candles attached)` and left the long sword and
  the wand of striking.

### Vlad #2 (^G), lantern lit (#136-#276)
- #136 lantern on (radius 3). #140 ^G "Vlad the Impaler" (forced). He appears adjacent, with the same note.
- #143, #146 `hunt('Vlad')`: 3 blows, then he vanished and hunt returned `lost` without following (stale code).
  Reload at #146.
- #150-#151 `hunt('Vlad')`, now on current code: one blow, and Vlad teleported away.
  - **H2** hunt followed him 1 step to his last square (20,11). That step put me next to a lieutenant (note
    "may carry attack WANDS (even death)"), who attacked. Result: `lost: ... (last seen at (20, 11); followed 1
    step(s))`. Following the last square of a monster that TELEPORTS is useless. The follow step does not check
    for other hostiles, unlike hunt()'s normal steps (`blocked:`).
- (PASS) #155 `fight_until_clear(radius=3)` with no hold: `clear — BUT Vlad the Impaler was at (19,10) 2 turn(s)
  ago and left view: a hit-and-run in the dark (Vlad, a covetous caster)? wait a turn (`s`) and look before
  moving on`.
- #156-#197 `hold=25`: `held`, and Vlad never came back. Wounded, he holes up to heal (wizard.c STRAT_HEAL: near
  the stairs; here he came out of the NW niche). He regenerates at 1 HP/turn.
- #206 he interrupted `travel(25, 11)` in the lit hall. #207 `fight(21, 9)`: one blow, then "Vlad zaps a wand of
  fire!" from out of view. **L1: the lit lantern made no difference.** He does not walk away into the dark: he
  teleports (mnearto to heal, mnexto to harass). Only `fight_until_clear(hold=N)` copes with that, lamp or no
  lamp. The note and PLAYBOOK F lead with "fight from a lit spot".
- #209-#233 `fight_until_clear(radius=3, hold=40, unseen=True)`:
  - #213 "The fog cloud flows under the door." A niche vampire lord sat ON the closed secret door (23,8).
  - #214 `Fu` "You destroy the fog cloud!". The vampire lord rose unseen and left an `I` on the door.
  - **U1 #215** the unseen branch swung at that `I`: "You harmlessly attack the closed door." A wasted turn.
  - #217 Vlad and the vampire lord were both adjacent. #233 "You destroy Vlad the Impaler!" The hold then killed
    a gray dragon: `held`, kills fog cloud, vampire lord, Vlad, gray dragon.
- (PASS) #276 `pickup('Candelabrum')` from the pile under a gray dragon corpse (obs showed only `% food (pile)`)
  -> `w - a candelabrum`. "already have candelabrum? | Program in disorder!" is the wizard-mode duplicate, not
  the harness.

### fakewiz1 (Dlvl 46): freeze, dig, portal (#280-#323)
- #282 ^F: `magic portal (38,12)` and the 4 squeaky boards named.
- #286 `travel(38, 12)`: auto-fight on an owlbear (trivial at XL28). "A master lich suddenly appears!": this is the
  chamber's `L`, a covetous harasser. Frost touch, "Your potion of full healing freezes and shatters!", psi bolt.
  #288 `fight()`: 2 blows, then it teleported off.
- **E1 #291 `travel(34, 12)` walked the route along the moat (row 16).** "A kraken was hidden under the water! |
  The kraken hits! | The kraken hits! | The kraken brushes against your leg. | The kraken bites!" ("brushes
  against your leg" is a wrap that failed.) `eel_zone()` was `{}`: the kraken had never been seen. yendor.des puts
  a kraken in every fake-tower moat, where it starts hidden (makemon.c: eels `hideunder()`).
  - #295-#297 killed it from the shore; each round paused on its wrap attempts.
- **D1 #297** `eel_zone()` raised NameError: it isn't in the kernel namespace, though PLAYER.md documents it.
  `from tactics.nav import eel_zone` works.
- #307 `zap('o', 'l')` from (34,12): "The moat is bridged with ice! | The bolt of cold bounces! | The bolt of cold
  whizzes by you!". It bounced off the chamber wall right behind the frozen square, with no bounce warning
  (harmless for a cold-resistant character with reflection).
- (PASS) #315 `dig('l')` from the ice: "You make an opening in the wall." It wielded Excalibur again.
- **F2 #320 `travel(38, 12)` stepped into the opening (36,12), then raised a misleading NavError:** `no known path
  — the known map doesn't connect to it and has no unexplored edge left: search() walls and dead ends for hidden
  doors/passages, dig through ..., or teleport/levitate; in Gehennom's mazes digging is often quickest`. The real
  blocker is the harmless squeaky board (37,12): by design all four neighbours of the portal are boards. That
  message sends a player off digging or searching.
- #321 `step('l', force=True)`: "A board beneath you squeaks a C note loudly." (pause `trap at (37, 12)`).
- (PASS) #323 `step_onto(38, 12)` -> "You activated a magic portal!" Arrived in wizard3's entry chamber. The pause
  listed a vampire bat, an orange dragon and a horned devil.
- #325-#344 `fight_until_clear(radius=4)`: "You feel that monsters are aware of your presence.", the bat rose as a
  vampire lord, "A horned devil appears in a cloud of smoke!", and "The arch-lich drinks a potion of gain level!
  | The arch-lich rises up, through the ceiling!". Result `clear`.

### wizard3 (Dlvl 42): stairs choice, moat, ladder (#345-#396)
- #345 ^F: `up stairs (35,13); up stairs (7,4)`. (35,13) is the tower's ladder, in the moat-ringed chamber.
- **S2 #354 `go_up()`**: `2 '<' here ((35, 13), (7, 4)) and where they lead is unknown — taking the nearest, (35,
  13); one of them is a branch`. Neither is a branch, and the ladder was not filtered out, although PLAYBOOK F
  says go_up() skips ladders.
  - Cause (#360): `farlook(35,13)` = `'< a staircase up or a ladder up (ladder up)'` and `farlook(7,4)` = `'< a
    staircase up or a ladder up (staircase up)'`. The test `"ladder" in farlook(...)` (nav.py ~l.969) is true for
    BOTH, because the symbol's generic description names both.
- #362 ^T into the moat ring at (31,13), skipping the secret-door maze. #365 a cold zap froze (32,13).
- **E1 again, #367-#370.** ^G "giant eel": it is created hidden (makemon hideunder). `eel_zone()` = `{}`, and
  `travel(31, 9)` went straight along the moat: "The giant eel bites! | The giant eel brushes against your leg."
- (PASS) #370 with the eel now in view, `travel(31, 9)` refused: `the only known way passes (31, 10), next to the
  water with the giant eel at (32,12) — its wrap drowns you (levitation doesn't help). Kill it or freeze the water
  (cold ray) first, wait for it to leave, or travel(..., near_water=True)`.
- #373 `zap('o', 'n')` at the eel: "The moat is bridged with ice! | The bolt of cold hits the giant eel!". It is now
  stranded on ice and can't drown anyone (drowning needs the eel in water), but `eel_zone()` still counts it
  (minor). #374 one blow killed it, and `eel_zone()` went back to `{}`.
- (PASS) #384 `dig('l')` from the ice: `dig(): stopped — vampire bat at (34,13) in view; your weapon (n) is
  wielded again. dig() again to go on`. This is the re-wield-before-pause spot check.
- **E2 #385 `fight_until_clear(radius=3)` returned `clear — BUT vampire bat was at (34,13) ...`** while "It misses!
  | It misses!" came from an `I` at (32,14), in the WATER next to me. The `I` note: `an unseen monster was here
  (blind/invisible): could be anything, even a peaceful`. `eel_zone()` was `{}`. #386 `fight(32, 14)`: "You kill
  the giant eel!" An `I` on a water square that attacks you is a hidden eel, kraken or piranha, and nothing in
  the harness connects that to drowning.
- **F2 again, #387** `hunt('vampire bat')`: `no route to the vampire bat at (36, 13) on the map you know (across
  water, behind a wall or other monsters)`. The real blocker is the squeaky board (34,13).
- **S2 inverted, #396** `go_up()` from the board: `stairs: [(7, 4)] is a ladder (a tower's) — not taking it unless
  nothing else is left` / `using the < at (35, 13): the only staircase (the other is a ladder)`, then "You climb up
  the ladder." It got things backwards:
  - The real stairs (7,4) were flagged as a ladder (see #360).
  - The ladder was taken for stairs because an object lay on it, so farlook described the object. wizard3 always
    has one: yendor.des puts its amulet (`OBJECT:'"',(11,07)`) on the ladder square `LADDER:(11,07)`.
  - It was right by luck here. For a character outside the tower (the Amulet climb from Dlvl 43) go_up() will
    pick the sealed tower's ladder.

### wizard2 -> wizard1 (Dlvl 41-40): the Wizard, the Book (#398-#442)
- #402 ^T onto wizard2's up ladder (the ring of secret doors skipped for budget): the arch-lich attacked. #404
  `go_up()`: "You climb up the ladder." Now on wizard1, at (30,11).
- #406 ^F: squeaky boards (39,11), (40,10), (40,12), (41,11) round the Wizard's square (40,11).
- #408 ^T to (36,11), the ring square west of the chamber. The moat squares next to me were (37,10), (37,11) and
  (37,12).
- #411 `zap('p', 'l')` (digging) opened (38,11) and showed the Wizard of Yendor (40,11) and a vampire bat.
  - (PASS) The Wizard's note: `covetous: steals the Amulet, the Bell, the Candelabrum, the Book or your quest
    artifact, then teleports off to heal; casts touch of death (MR stops it), summon nasties, curses, destroy armor,
    double trouble (clones himself). Comes back after being killed. Keep MR, reflection and uncursing ready; kill him
    fast.`
- #414 `zap('o', 'l')`: "The moat is bridged with ice! | The bolt of cold hits the vampire bat! | The bolt of cold
  misses the Wizard of Yendor. | The Wizard of Yendor drinks a potion of gain level!"
- **W1 #416-#426 `fight_until_clear(radius=5, hold=8, unseen=True)`.** The Wizard came to me.
  - A hidden giant eel (37,12) and a hidden kraken (37,10) attacked me every turn from the water beside me. Their
    wraps failed 5 times ("brushes against your leg").
  - "The hell hound breathes fire! | The ice crackles and melts.": the frozen path melted back into moat.
  - The Wizard: "casts a spell at you! | A field of force surrounds you!", then "You feel as if you need some help.
    | You feel a malignant aura surround you." (items cursed), aggravate, and "Oh no, he's using the touch of
    death! | Lucky for you, it didn't work!" (MR).
  - The helper always struck the Wizard (danger rank = note + difficulty), while two drowners were each one wrap
    away from killing me. Every pause was a plain `message`. The eel note says "Keep 2 squares from the water",
    but no helper said so here.
  - #426 "You kill the Wizard of Yendor!" (T:389, 4 blows). No double trouble happened in this short fight.
- #428-#438 killed the eel and two krakens ("A kraken was hidden under the water!" again). A piranha was left.
- (PASS, B1 from round 4 fixed) #442 `pickup('Book of the Dead')` -> `x - a papyrus spellbook.`. The Wizard had
  picked it up and dropped it where he died (36,12).
- **O1 again** at #442: `out of view: vampire lord last at (37,11) 12 turn(s) ago`. It had been "destroyed by the
  blast of fire!" (the hell hound's breath), which is not "You kill", so the tracker never dropped it.

### The Amulet climb and the invocation check (#445-#470)
- #445-#447 ^W: `y - the Amulet of Yendor`, `z - a silver bell`. #448 ^V 44 (a maze filler, Gehennom dunlev 17,
  inside the force's range) and ^F.
- #455 `go_up()`: 17 turns of NetHack's travel guessing, then a trap NavError (round 4's M1, unchanged).
- #459 ^T onto the up stairs. "You faint from lack of food." (my fault: I skipped eating while Hungry, and the
  wizard-mode ^T calls seem to have cost nutrition).
- **(PASS, first live test) #460, first climb:** "A mysterious force momentarily surrounds you...": Dlvl 44 -> 47.
  - Pause: `MYSTERIOUS FORCE (you carry the Amulet): the climb failed — you were moved on this level or sent down a
    few; climb again (1 in 4 climbs deep in the dungeon); message`. It is clear, but it doesn't say which of the
    two happened ("sent down 3 levels, Dlvl 44 -> 47"). go_up() suppresses the level-change reason.
  - After `cont`, go_up() printed `stairs: the MYSTERIOUS FORCE (you carry the Amulet) sent you DOWN to Dlvl:47,
    somewhere random on it: find this level's '<' (known_cells('<') / explore()) and climb again`.
  - **MF3** It then RETURNED normally. My loop's next line, `go_down()`, ran on Dlvl 47 and got a NavError (no
    `>`). A scripted climb (`for ...: go_up()`) goes on after being thrown 3 levels down.
- #463 `eat('d')`: "Blecch! Rotten food!". The ration had been cursed by the Wizard, the first visible sign of his
  curse; no pause or obs line ever said which items were cursed.
- #464 ^F on Dlvl 47: `vibrating square (64,14)`. #467 ^T onto it: "You feel a strange vibration under your feet."
- (PASS) #470 `invoke()`: `RuntimeError invoke(): BUC unknown — a silver bell; a candelabrum (no candles attached);
  a papyrus spellbook: a cursed one makes it fail ...`. The BUC check sees the Book (and the Bell and the
  Candelabrum). The invocation was not done.

## Summary: findings ranked by danger to a real character

| # | Where / step | Finding | Risk |
|---|---|---|---|
| 1 | fakewiz1 #291; wizard3 #367-#370, #385; wizard1 #416-#438 (E1, E2) | **Hidden drowners are invisible to `eel_zone()`.** The fake-tower, wizard1 and wizard3 moats always hold krakens and eels (yendor.des), created hidden under water. travel() walked the moat edge twice and was attacked by wrapping drowners. `fight_until_clear` returned `clear` while an `I` in the water (a giant eel) was attacking. The `I` note says "could be anything, even a peaceful". Expected: treat the water of those levels (and Medusa's, the Castle's, Juiblex's) as eel water from arrival; treat an `I` or an "It bites/hits" from a water square as a drowner (eel_zone, travel refusal, a pause naming it); a pause on the first "brushes against your leg" | HIGH |
| 2 | wizard1 #416-#426 (W1) | **Fighting at the moat edge with drowners adjacent**: `fight_until_clear`/`fight()` rank targets by difficulty and struck the Wizard 4 times, while a kraken and a giant eel tried to wrap me every turn (5 failed wraps, all plain `message` pauses). No helper said "step back from the water"; the hell hound's fire melted the frozen path ("The ice crackles and melts.") unmentioned. Life saving would be the only thing between one lucky wrap and death. Expected: drowners adjacent while you stand next to their water rank first, or the helper pauses with "step away from the water / Elbereth" | HIGH |
| 3 | wizard3 #354, #360, #396 (S2) | **The ladder check in go_up()/go_down() is broken**: every farlook of `<` reads "a staircase up or a ladder up (…)", so `"ladder" in text` flags real stairs as ladders, and a ladder with an object on it (always on wizard3: the level's amulet lies on the ladder) is taken for stairs. #396 picked the ladder as "the only staircase (the other is a ladder)", backwards. On the Amulet climb from outside the tower, go_up() heads for the sealed tower's ladder (and #354 still says "one of them is a branch"). Expected: test the parenthesised part ("(ladder up)"), look at the square's terrain rather than its top object, never call a tower ladder a branch; PLAYBOOK F's "skips the ladders" is false until then | MEDIUM (ascension run) |
| 4 | setup, #143-#146 | **The qa8 kernel ran stale tactics**: `hunt()` without the follow feature (bc154df reached the disk 4 min after the daemon started). Players on p1-p3 may be on old helpers without knowing. Expected: the kernel records the git commit / file mtimes it loaded and says so in `obs`/`info` when the tree is newer (or auto-reloads tactics between execs) | MEDIUM (process) |
| 5 | fakewiz1 #320, wizard3 #387 (F2) | **Squeaky boards block routes, with a misleading reason.** travel() to the portal said "no known path … search walls, dig through, teleport/levitate"; hunt() said "across water, behind a wall or other monsters". The real blocker is a harmless board; all four neighbours of the fakewiz1 portal and the wizard3/wizard1 centres are boards by design. Expected: route over known squeaky boards (they only wake monsters) or name them ("passes the squeaky board at (37,12), harmless: step('l', force=True)") | MEDIUM-LOW |
| 6 | Dlvl 44->47 #460 (MF3) | The force pause is clear but vague ("moved on this level or sent down a few"), and **go_up() returns normally after being sent down**. Its print is good ("sent you DOWN to Dlvl:47 ... climb again"), but a script loop carries on: my next `go_down()` ran on Dlvl 47. Expected: raise NavError (or return a flagged result) when the climb didn't go up; put "Dlvl 44 -> 47" in the pause | MEDIUM-LOW |
| 7 | tower1 #113, #150 (H1, H2) | Covetous hit-and-run vs hunt()/fight(): a teleport to ANOTHER adjacent square ends both. fight() says "stepped away ... (d=1) ... hunt((20, 11)) goes after it", and hunt returns "fight() stopped with it still next to you". hunt()'s new follow step walks to a teleporter's last square (pointless) and steps next to other hostiles without its usual `blocked:` check (a lieutenant). Expected: keep attacking the same monster id at its new adjacent square; don't follow covetous teleporters; check neighbours before the follow step | LOW-MED |
| 8 | tower1 #136-#233 (L1) | The lantern made no difference: Vlad teleports (mnexto 1 turn in 5 at full HP; wounded, he heals near the stairs or in a niche), he doesn't walk off into the dark. `fight_until_clear(radius=3, hold=N, unseen=True)` killed both Vlads (T:240-250 in the dark, and with the lamp). The note and PLAYBOOK F lead with "fight from a lit spot" | LOW |
| 9 | tower1 #102-#110, wizard1 #442 (O1) | Stale out-of-view lines: a shape-shifted vampire leaves `fog cloud`/`vampire bat` entries after it is destroyed; a vampire lord "destroyed by the blast of fire" (a monster's breath) is never dropped. They look like more vampires at large | LOW |
| 10 | tower1 #215 (U1) | `fight_until_clear(unseen=True)` swung at a stale `I` on a closed door ("You harmlessly attack the closed door.") | LOW |
| 11 | #297 (D1), #307, #373 | `eel_zone()` isn't in the kernel namespace (NameError) though PLAYER.md documents it; an eel frozen onto ice (it can't drown you) still counts; a cold zap at moat-then-wall bounced back ("whizzes by you") with no warning | LOW |
| 12 | wizard1 #419, #463 | The Wizard's curse ("You feel as if you need some help. / malignant aura") pauses as a plain `message`, and nothing says which items were cursed (the first sign was "Rotten food!" at #463). Expected: suggest `inventory()` after a curse message | LOW |
| 13 | notes | Cosmetic ".;" at the end of Vlad's and the Wizard's notes (the note joined to the "much stronger than you" suffix) | cosmetic |

Worked well:
- Hold and strike: `fight_until_clear(hold=N, unseen=True)` beat Vlad's hit-and-run twice, and without a hold it
  warned "clear — BUT Vlad ... left view: a hit-and-run". fight() now says where a monster stepped to.
- Vlad's note: the Candelabrum, no shape-shifting while he holds it, no corpse. `pickup('Candelabrum')` worked
  twice, once from under a dragon corpse.
- The fakewiz1 way in, once past the board: freezing with `zap()` ("The moat is bridged with ice!"), `dig()` from
  the ice (it re-wields the weapon, and before a newcomer pause too), `step_onto()` onto the portal.
- travel() refused the moat edge with the eel in view, with a good recipe.
- The Wizard's note is complete. Fog-cloud and bat notes are right.
- `pickup('Book of the Dead')` now matches the papyrus spellbook. invoke() on the square sees all three items and
  refuses unknown BUC.
- The mysterious force is recognised (pause plus go_up()'s "sent you DOWN to Dlvl:47" line). go_up() climbs
  ladders inside the tower. Level-change and arrival pauses are fine.

Not covered: the Plane of Earth (budget); the trapped-closet engraving and the stunned-F-next-to-a-pet spot checks;
the Wizard's return, "double trouble" and summon nasties (he died in 4 blows); the force's "moved on this level"
case; wizard2's secret-door route and wizard1's random secret door into the moat ring (skipped with wizard-mode ^T
at #362, #402, #408); the fakewiz1 vampire lord (it had left the chamber).

State left behind: `qa8` (tmux nh-qa8 and its daemon running, tactics reloaded at #146, so current code) at a
command prompt on Gehennom Dlvl 47, the vibrating-square level, standing ON the square (64,14). T:431, XL28, HP
261/270, AC -15, not hungry. No exec is paused.
- Worn: +3 GDSM, +3 shield of reflection ("polished silver shield"), +3 speed boots, +3 gauntlets of power, amulet
  of life saving ("oval amulet").
- Wielded: Excalibur (n). Brass lantern (r) LIT.
- Carrying the invocation items: the Amulet of Yendor (y), the Bell (z, "silver bell"), two candelabra (v, w; the
  second is a wizard-mode duplicate from a ^G Vlad, and picking it up printed "Program in disorder"), the Book (x,
  "papyrus spellbook"), 7 blessed wax candles (u).
- Carrying tools and wands: wands of cold (o, 4 zaps used), digging (p, 1 used), sleep (q), death (g); 3 blessed
  scrolls of teleportation (t, "TEMOV"); unicorn horn (s); blindfold (e); pick-axe (f); 1 food ration (d, possibly
  cursed).
- Some items were cursed by the Wizard; which ones is unknown.
- The Wizard of Yendor was killed at T:389 and will come back. Both Vlads are dead.
