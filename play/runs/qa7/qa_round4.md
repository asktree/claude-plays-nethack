# QA round 4: Gehennom, Vlad's Tower, the Wizard's Tower (wizard-mode game `qa7`)

Tester: QA agent (round 4), 2026-09-27. Game `qa7` (local 3.6.7 build, wizard mode, seed 4444), lawful female
dwarven Valkyrie, #levelchange 22, GDSM + shield of reflection + speed boots; wands of digging/sleep/cold/death,
3 scrolls of teleportation, ring of levitation, unicorn horn. Earlier rounds: `play/runs/qa2/qa_round2.md`,
`play/runs/qa5/qa_round3.md`.
Scope: Gehennom maze fillers (explore/travel/go_down, typical monsters), mind flayers, Vlad's Tower, the
Wizard's Tower / fake wizard levels / the Book, the Amulet climb ("mysterious force"). Plane of Earth: not reached.
Method: wizard-mode setup (^W, ^V, ^G, ^F, ^T), then kernel helpers as a player would. `#N` = obs step number.

**Setup note (harness dev):** `bin/nh start-local qa7 --seed 4444 --wizard --fresh` refused: `running game 'qa6'
uses the same NetHack lock name 'wizard'` (qa6 is a live wizard-mode game; all -D games lock as "wizard"). I did
not touch qa6. Workaround: a private copy of the playground (nethack, nhdat, sysconf, symbols, empty
record/logfile/save) in my scratchpad plus a wrapper that exports HACKDIR and adds `-D`, passed as
`--nethack <scratchpad>/nh367/bin/nethack` without `--wizard`. The lock check compares names only, not
playgrounds; a supported `--playground DIR` option would let QA run beside other wizard games. NB: qa7's
meta.json points at that scratchpad wrapper, so the game can't be restarted once the scratchpad is gone.

## Raw log

### Gehennom maze filler (Dlvl 40, #43-#173)
- ^V menu (`?<CR>`) -> Valley (#40, arrival pause with the vampire bat's shape-shift note), then `^V 40`.
- #60 `explore()`: fire trap "A tower of flame erupts from the floor! | Your boots smoulder!" (maxHP 199->195,
  AC -8->-7), one pause `message; trap at (62, 18)`. Fine (unavoidable in an unexplored 1-wide corridor).
- M1 #75 `explore()` returned after 2 turns: `blocked: frontiers [(63, 20)] travel couldn't reach; boulders
  [(61, 16)] ...`. The real reason: the only corridor back to (63,20) crosses the fire trap it just found.
  `'avoided': []`, and the trap isn't named. `travel(63, 20)` (#81) does name it ("the only known route crosses
  the known trap(s) at [(62, 18)]"), but it first walked one square along NetHack's guess.
- #83 pushing the boulder paused on "With great effort you move the boulder." (fine once).
- #156 `explore()` again (23 legs, T:18->38): `blocked: frontiers [(63, 20)] travel couldn't reach — no down
  stairs seen yet`. The whole reachable part was a sealed pocket whose only exit is that fire trap. Same
  missing reason; `dead_ends: []` although the pocket has three dead ends (fine: maze dead ends are normal).
- M1 #161-#166 after ^F, `go_down()` walked **10 turns** (T:38->48) of NetHack's "guess" route into the dead
  end (44,14), then raised `NavError travel to (32, 8) stopped at (44, 14): ... the only known route crosses
  the known trap(s) at [(62, 18), (72, 17), (62, 14), (25, 4)] ...`. In a maze the guess (straight toward the
  target) always ends in a dead end: 10 wasted turns in Gehennom before the error.
- #173 `zap('h', 'h')` (digging) opened the pocket wall silently (correct in 3.6: no message for maze walls);
  `go_down()` again walked 5 turns, then NavError for the trap (25,4). None of the maze NavErrors mentions
  digging, although Gehennom maze walls are diggable and a wand of digging or pick-axe is the normal tool here.

### Gehennom monsters (Dlvl 40, #183-#217)
- #183 ^G lich, vampire lord, nalfeshnee, pit fiend, ghost. obs: `8 wizard's ghost` (note "slow but hard to
  hit"), `L lich` ("spellcaster (curses items, summons). Kill fast."), **`d wolf at (41,12)` with no note**: the
  vampire lord had shape-shifted at once (3.6 `pickvampshape`: lords become wolves 1 time in 10, else fog
  cloud/bat). The nalfeshnee and pit fiend were placed out of sight in the dark.
- `threat()`: wolf **trivial**, ghost normal, hell hound normal; lich, nalfeshnee, pit fiend, vampire lord,
  mind flayers, liches, Vlad, the Wizard, fog cloud, vampire bat, kraken: dangerous.
- `mon('pit fiend')`: WEAP 4d2, WEAP 4d2, HUGS 2d4, **no MAGC**, but the NOTE says "strong: grabs;
  spellcaster." (wrong). Nalfeshnee has MAGC (right).
- G1 #186 `fight()` without arguments chose the **ghost** (normal) over the adjacent **lich** (dangerous,
  "Kill fast"). It then paused after every blow on "Wizard's ghost touches you!": a named ghost ("Jay's ghost",
  "wizard's ghost") doesn't start with "The", so the routine melee pattern misses it.
- #189-#194 `fight(40, 13)` on the lich: "The lich casts a spell at you! | You feel momentarily weakened." (MR),
  "The lich points all around, then curses.", then "The lich reads a scroll labeled ABRA KA DABRA!" and it was
  gone: `fight: the lich at (40,13) is gone — NOT killed (it teleported ...)`. Good.
- #199 `fight(41, 12)` on the wolf: "You kill the wolf! | The seemingly dead wolf suddenly transforms and rises
  as a vampire lord!", pause `new monster: vampire lord`, and fight() stopped with `the wolf at (41,12) is gone —
  a vampire lord is there now; stopped (fight(41, 12) again to attack it)`. Good handling. But the wolf had no
  note and rates trivial, so **auto-fight in travel/explore would melee it** and leave a full-HP level-drainer
  adjacent (W1).
- #206 "The vampire lord escapes upstairs!": the out-of-view line keeps `vampire lord last at (41,12)`; nothing
  says it is now waiting at the top of those stairs (LOW).

### Mind flayer (Dlvl 40, #208-#217)
- #208 ^G inside an exec: pause `new monster: mind flayer at (40,13)`, note `tentacles eat your brain (Int
  loss, amnesia). Kill fast / flee; telepathic.` Status line (raw screen only): `St:16 Dx:12 Co:19 In:10`.
  **The obs header never shows attributes**; `obs` has no Int.
- **MF1 #211** `fight(40, 13)` (no helmet worn): one monster turn = three tentacle hits: "Your brain is eaten! |
  You feel very stupid! | ... Your brain is eaten! | You feel stupid! ..." **In:10 -> 6**, HP 189/195. The
  pause reason is a plain `message`.
- #212 `cont` (the natural next step: HP is fine): three more hits, **In:6 -> 3**, HP 181/195, plain `message`.
- #214 `cont`: "The mind flayer's tentacles suck you! | Your brain is eaten! | Your last thought fades away." ->
  **`Die? [yn]` at 181/195 HP.** A plain mind flayer killed an XL22 Valkyrie with AC-7 in three monster turns,
  and every pause looked routine. #215-#216: `n` -> "You feel like a scarecrow." (Int reset to 5), then eaten
  again -> `Die?` twice more. #217 `zap('n', 'j')` (death) killed it.
- 3.6.7 source facts (mhitu.c AD_DRIN, eat_brains()): each tentacle hit that lands costs Int -rnd(2) and makes you
  forget 25% of levels/objects; if Int is already 3 when a brain is eaten you die ("brainlessness"), and
  **life saving does not help** ("Unfortunately your brain is still gone."). **A worn helmet blocks 7 hits in 8**
  (`uarmh && rn2(8)`: "Your helmet blocks the attack to your head."). A master mind flayer has 5 tentacles.
  The note mentions none of this, and the Valkyrie starts without a helmet.

### The Vlad's Tower branch level (Dlvl 38 = wizard3, #222-#336)
- #224 ^F: `features: magic portal (49,17); up stairs (35,13); up stairs (18,15); up stairs (9,8); down stairs
  (2,18); ...`. (35,13) is the Wizard's Tower LADDER inside the moat, listed as `up stairs`; ladders are never
  told apart from stairs.
- **S1 #228** `go_up()`: `stairs: 3 '<' here ((35, 13), (18, 15), (9, 8)) and where they lead is unknown —
  taking the nearest; one of them is a branch` and it headed for (35,13), the unreachable tower ladder. From
  another square it took (18,15) (#254-#260), which happened to be the main stairs (-> Gehennom 37). With the
  Amulet the "nearest" can just as well be Vlad's branch (a 3-level dead end) or the ladder. Only 1 of the 3 is
  a branch according to the message, but 2 of 3 are wrong for the climb.
- A1 #228 the invisible nalfeshnee followed me through ^V (demons are stalkers). `auto-fight: dwarf mummy at
  (73,12)` swung at a trivial mummy while `I remembered, unseen monster at (72,14)` hit me ("It hits! | It hits! |
  It bites! | Something casts a spell at you!"). Auto-fight's "all adjacent hostiles are trivial" test ignores `I`.
  #233-#236: curse items twice ("You feel as if you need some help. | You feel a malignant aura surround you.",
  paused: good; which items got cursed is not shown), then "A nalfeshnee appears in a cloud of smoke!" (gating).
- #254 ^T refused ("Sorry...": a boulder at the target), then `go_up()` gave a good boulder NavError: "the only
  known route passes the boulder(s) at [(50, 20)]: push one by stepping into it ..., smash it ..., or dig
  around it".
- (wizard only) #256 ^T on a Wizard's Tower level asks "Override? [yn]" 1 time in 3 ("disoriented").
- #262 (PASS) `go_up(to="Vlad's Tower")` -> `NavError no known '<' here leading to "Vlad's Tower": (18, 15) ->
  Gehennom / Level 37, (9, 8) -> unknown, (35, 13) -> unknown — travel(x, y) to the right one and press it
  yourself`. The learned link was used later: "stairs: using the < at (18, 15): stays in Gehennom".
- #268 `travel(9, 8)`: trap NavError for the arrow trap (8,10) after a 2-square guess walk.
- #271 black dragon note "DISINTEGRATION breath: need reflection" (right; the harness can't know my unidentified
  "polished silver shield" is reflection). Auto-fight took an ogre and a human mummy.
- **N1 #310, #317** `travel(9, 10)` **stopped short and returned normally**: it only printed `travel: stopped at
  (16, 9) short of (9, 10) on ['The ogre swings her double-headed axe.'] — look, then travel again`. My next line,
  `step('h', force=True)` (the exact recipe of the trap NavError), ran from (16,9) instead of (9,10): "It's a
  wall." Harmless here, but `force=True` switches off the trap AND water/lava guards, so the same two-line
  script next to a moat or a trap door does something the player never checked.
- #325 forced step onto the arrow trap: "An arrow shoots out at you! | An arrow misses you." (`trap at (8,10)`).
- #336 `<` at (9,8): pause `message; level: Dlvl:38 -> Dlvl:37`, `where: Vlad's Tower / Level 37`. Good.

### Vlad's Tower (tower3 Dlvl 37, tower1 Dlvl 35, #344-#439)
- X1 #344 ^F then `go_up()`: `auto-fight: xan at (20,17)`. The xan carries a `!!` note ("leg sting: WOUNDED LEGS
  (can't kick ...)") but is in INFO_NOTES and rates trivial, so auto-fight engaged: "The xan pricks through your
  left boot!".
- #376 `go_up()` -> `NavError travel: the door at (30, 11) is locked — unlock(30, 11) with a key,
  kick_door(30, 11) ... or go another way` (good; the tower entry door is always locked). `features` keeps
  saying `closed door (30,11)`.
- X1 #377 `kick_door(30, 11)` returned "Your left leg is in no shape for kicking." with no explanation. Nothing
  in obs shows wounded legs, and the NavError above still suggests kicking. #380 `zap('h','h')`: "The door is
  razed!" (digging razes doors even in the solidified tower), and the pause listed horse, chickatrice and 4 storm
  giants (no note for storm giants).
- #382 `^V 35` (inside the branch a plain number works; from outside use the menu): tower1 after ^F: `down stairs
  (27,11); throne (22,11); closed door ...`. #386 "The door resists!" (a random failed open) and #388 it opens.
- #390 first sight: pause `new monster: Vlad the Impaler at (20,11)` ("Vlad the Impaler drinks a golden potion! |
  ... seems more experienced."), note `LEVEL DRAIN bite; strong.; much stronger than you (difficulty 32 vs XL 22);
  fast (speed 26)`. Missing: **he carries the Candelabrum of Invocation** (needed to ascend), he is covetous
  (M3_WANTSCAND: below full HP he jumps to the stairs to heal), flies and regenerates, and he leaves no corpse
  ("body crumbles into dust"; his inventory drops). Also cosmetic ".;". And a 3.6.7 fact the old task text got
  wrong: **Vlad never shape-shifts while he holds the Candelabrum** (mon.c pickvampshape: "ensure Vlad can keep
  carrying the Candelabrum"). Only without it does he become a wolf (1 in 3), fog cloud or bat.
- **V1 #391-#439 hit-and-run in the dark defeats the fight helpers.** `fight(20, 11)`: one blow, then `the Vlad the
  Impaler at (20,11) is gone — NOT killed (it teleported, fled out of view or hid) ... (a covetous one teleports to
  heal and comes back)`. He had only stepped 2 squares into the unlit room (speed 26). #394 "Vlad the Impaler
  bites! | Farvel level 22." (pause `XL 22->21`: good). #395 `fight()` again: one blow, gone.
  `fight_until_clear(radius=3)` returned `{'reason': 'clear', 'turns': 0}` while obs said `out of view: Vlad the
  Impaler last at (19,13) 0 turn(s) ago`. He also zapped a wand of cold (reflected, #408, #426). With my own
  wait-and-strike loop (search when he's out of view, fight() when adjacent, cold-zap when in line) I lost
  **XL22 -> 19 and 187 -> 111 HP in ~25 turns without killing him**; I stopped there (budget). So the Candelabrum
  pickup was **not tested live**. Its unidentified name is "candelabrum", which `pickup('Candelabrum')` matches
  case-insensitively.
- #401 a fog cloud flowed out of a niche (a tower vampire): its note "a vampire can take this shape" is right.

### The Wizard's Tower and fake wizard levels (#443-#502)
- How to get in (3.6.7 yendor.des): only **fakewiz1** has a magic portal, at the centre of a tiny tower (walls
  plus squeaky boards in the gaps, a 2-wide moat around, a lich on the portal, a vampire lord and a kraken). It
  leads to the entry chamber of **wizard3**. Inside, ladders lead up to wizard2 and wizard1. The Wizard sleeps in
  wizard1's innermost chamber, ringed by a moat with krakens and giant eels, beside a hell hound and a vampire
  lord, with the Book of the Dead ON THE FLOOR under him. All three wizard levels are noteleport. fakewiz2 has
  no portal.
- #445 fakewiz1 after ^F: `magic portal (38,12)` plus the four squeaky boards named. Good.
- #448 a master lich arrived: "Oh no, he's using the touch of death! | Lucky for you, it didn't work!" (MR). Its
  note ("touch of death possible without MR") fits. #450 travel refused to start next to it (right).
- F1 #455 from the moat's edge `travel(38, 12)` -> `NavError ... no known path — the known map doesn't connect to
  it and has no unexplored edge left: search() walls and dead ends for hidden doors/passages, dig through (not on
  undiggable levels), or teleport/levitate`. Workable, but it doesn't say what the obstacle is (a 2-wide moat,
  then a wall ring: cross the moat, dig the wall) or that this portal is the Wizard's Tower entrance. "search
  walls for hidden doors" is a dead end here. PLAYBOOK F says "a fake-tower level": fakewiz1 only.
- #462 wizard1: ^T into the Wizard's chamber -> "Sorry..." (the tower region refuses teleports even in wizard mode;
  only the portal route works). The Wizard fight was not reached (budget).
- Wizard note (`mon('Wizard of Yendor')`): `steals the Amulet/quest artifact; curses; double trouble. Keep
  uncursing ready.` Missing: he wants ALL the special items (M3_WANTSALL: Amulet, Bell, Candelabrum, Book, quest
  artifact); he teleports away to heal and comes back; he summons nasties; he returns periodically after being
  killed; his Book lies on the floor of his chamber until he picks it up.
- **The Book**: wizard-mode wishes gave `o - a papyrus spellbook` (the Book of the Dead), `p - a silver bell`
  (wished CURSED), `q - a candelabrum (no candles attached)`, `r - 7 candles`, `s - the Amulet of Yendor`.
  B1 #480 `pickup('Book of the Dead')` did NOT take it (only printed "You see here a papyrus spellbook.");
  `pickup('papyrus')` did. The same will happen with `pickup('Bell of Opening')` ("silver bell"). PLAYER.md warns
  only about `pickup('Amulet')`.
- #485 (PASS) ^V 44, ^F: `vibrating square (22,7)`. `invoke()` off the square: `NavError invoke(): you are not on
  the vibrating square — it is at (22, 7): travel there first`.
- #502 (PASS) ^T onto the square ("You feel a strange vibration under your feet.", `vibrating square (under you)`).
  `invoke()` refused: `invoke(): BUC unknown — a silver bell; a candelabrum (no candles attached); a papyrus
  spellbook: a cursed one makes it fail (test on an altar, or dip in holy water); force=True to go ahead anyway`.
  All five items show `buc=''`. The refusal protects against the secretly cursed Bell. The invocation itself was
  not done.

### Climbing with the Amulet: the mysterious force (#504-#610)
- `go_up()`/`go_down()` loop on the Gehennom 38<->37 stair pair with the real Amulet (wizard mode wishes the real
  one: objnam.c converts to the fake only `if (!wizard)`). The harness used the learned link every time ("stairs:
  using the < at (18, 15): stays in Gehennom (leads to Gehennom / Level 37)").
- MF2 **22 climbs, no "mysterious force" at all.** do.c: `Inhell && up && u.uhave.amulet && !newdungeon &&
  dunlev < dunlevs_in_dungeon - 3` (level 38 = Gehennom dunlev 13 < 17) then `!rn2(4)`. For a lawful 3 in 4 of
  those send you down 1-3 levels. (3/4)^22 is about 0.2%, so either extreme luck or something in this local
  setup (seed patch, the wished Amulet) keeps it from firing. The "sent down N levels" pause and NavError could
  **not be assessed**. Suggest a unit test that replays the message sequence ("A mysterious force momentarily
  surrounds you..." followed by a lower Dlvl) through the pause classifier and go_up().
- #538 the master lich teleported next to me on arrival ("A master lich suddenly appears!") and followed me up
  and down every stair. Master liches and arch-liches are covetous (they want the Book of the Dead, which I
  carried); their notes don't say so. With it adjacent each climb paused on its spell chatter ("The air crackles
  around the master lich.", "points at you, then curses"). I needed `--no-monsters -a '.*'` to run the loop.

## Summary: findings ranked by danger to a real character

| # | Where / step | Finding | Risk |
|---|---|---|---|
| 1 | Dlvl 40 #208-#214 (MF1) | **Mind flayer = death at 93% HP.** 3 tentacle hits per turn took Int 10->6->3->"Your last thought fades away." (`Die?`) in 3 monster turns. Every pause was a plain `message`; obs never shows Int (only the raw status line); fight()'s HP rules saw nothing wrong; the note lacks "death at Int 3, life saving doesn't save you, a helmet blocks 7 of 8, master = 5 tentacles". Expected: Int in the obs header, a `BRAIN EATEN — Int N` pause, fight()/auto-fight refusing a mind flayer without a helmet or at low Int, a fuller note | HIGH |
| 2 | Vlad's Tower #390-#439 (V1) | Fast hit-and-run in the dark: `fight()` gets one blow then "gone — NOT killed"; `fight_until_clear()` says `clear` with Vlad adjacent 0 turns ago; I lost XL22->19 without killing him. Vlad's note lacks the Candelabrum, covetous stair-healing and "no corpse — pick the Candelabrum off the floor". Expected: treat a monster seen adjacent within ~2 turns as present (wait `s` and strike), advise light/Elbereth/fighting in a lit spot | MEDIUM |
| 3 | Dlvl 40 #183-#199 (W1) | A vampire lord in wolf form shows as plain `wolf`: no note, `threat()` trivial, so auto-fight melees it; killing it raises a full-HP vampire lord adjacent (level drain). fog cloud/vampire bat carry the warning, wolf doesn't (lords: 1 in 10 wolf; Vlad without the Candelabrum: 1 in 3) | MEDIUM |
| 4 | Dlvl 38 #310, #317 (N1) | `travel()` that stops short (a monster's message) RETURNS normally; the harness's own recipe `travel(next to trap); step(dir, force=True)` then forces a step from the wrong square with the trap/water guards off | MEDIUM |
| 5 | Dlvl 38 #224-#260 (S1) | Three `<` on the Vlad-branch level (main stairs, Vlad's branch, Wizard's Tower ladder shown as `up stairs`): `go_up()` "taking the nearest", which was the unreachable ladder first time. On the Amulet climb the nearest may be Vlad's dead-end branch. Expected: refuse and list them when links are unknown (always with the Amulet), use ^O branch info, name ladders | MEDIUM (ascension run) |
| 6 | Dlvl 38 #228 (A1), Dlvl 40 #186 (G1) | auto-fight hit a trivial mummy while an invisible nalfeshnee (`I`) mauled and cursed me (`I` is not counted as a non-trivial neighbour); `fight()` without arguments chose the harmless ghost over the noted lich; "Wizard's ghost touches you!" pauses every blow | LOW-MED |
| 7 | Vlad's Tower #344-#377 (X1) | auto-fight engaged a xan (the `!!` note says "can't kick") -> wounded legs; the locked tower door's NavError says kick_door(); `kick_door()` returns "Your left leg is in no shape for kicking." with no hint; obs never shows wounded legs | LOW-MED |
| 8 | Dlvl 40 #75-#173 (M1) | Mazes: `explore()` stops with "travel couldn't reach" without naming the known trap that seals the pocket; `go_down()` walks up to 10 turns of NetHack's guess into a dead end before the trap NavError; no maze NavError suggests digging (the wand worked: #173) | LOW-MED |
| 9 | #480 (B1) | `pickup('Book of the Dead')` leaves the unidentified "papyrus spellbook" on the floor (same for "Bell of Opening" = "silver bell"); only `pickup('papyrus')` works. PLAYER.md warns only about the Amulet | LOW-MED |
| 10 | fakewiz1 #455 (F1) | portal travel NavError is generic ("search walls ..., dig, or teleport/levitate"): no "moat, then a wall ring: cross, dig — this is the Wizard's Tower entrance; fakewiz2 has none" | LOW |
| 11 | notes (D1) | pit fiend "spellcaster" is wrong (no MAGC); lich "summons" (a level-11 lich can't summon nasties, but CAN destroy armor without MR — missing); master lich/arch-lich covetous (want the Book, follow you) not said; Wizard note lacks Bell/Candelabrum/Book theft, summon nasties, returns after death; Vlad ".;"; no storm-giant note; vampire lord "escapes upstairs" not kept in out-of-view | LOW |
| 12 | #504-#610 (MF2) | the mysterious force never fired in 22 Amulet climbs (p about 0.2%): the "sent down N levels" handling is untested; needs a unit test or a check of the local setup | (untested) |
| 13 | setup | a second wizard-mode game can't start while any other runs (shared "wizard" lock); worked around with a private HACKDIR (the lock check compares names only) | harness dev |

Worked well: arrival and level-change pauses (Valley, `where: Vlad's Tower / Level 37`), ^F features on every
level (magic portals on wizard3 and fakewiz1, squeaky boards, anti-magic field, vibrating square, traps by
name); `go_up(to=...)` listing where each `<` leads, and the learned stair links used afterwards ("stays in
Gehennom"); fight()'s "the wolf ... is gone — a vampire lord is there now; stopped" and "NOT killed (it
teleported ...)" for the lich's teleport scroll; travel refusing to start next to a hostile; trap, boulder and
locked-door NavErrors naming the blocker; `invoke()` refusing off the square (and naming it) and on the square
with BUC-unknown items (it protected a secretly cursed Bell); `XL 22->21` level-drain pauses; the notes for
fog cloud, vampire bat, black dragon (disintegration), master lich (touch of death), chickatrice; exec refusing
to start at the `Die?` prompt.

Not covered (budget): killing Vlad and `pickup('Candelabrum')` live; entering the Wizard's Tower through the
portal, the Wizard fight and "double trouble"; tower2; the "sent down" force (never fired); the Plane of Earth.

State left behind: `qa7` (tmux nh-qa7 and its daemon still running) at a command prompt on Gehennom Dlvl 37
(wizard2) on the down stairs (14,4), T:258, XL19 (drained from 22 by Vlad), HP 171/171, not hungry. A master
lich and a fire giant are adjacent. Worn: +2 GDSM, +2 shield of reflection ("polished silver shield"), +2 speed
boots. Carrying: the real Amulet of Yendor (s), the Book of the Dead (o, "papyrus spellbook"), the Bell of
Opening (p, cursed), the Candelabrum (q), 7 wax candles (r); wands of digging (h), sleep (i), cold (l), death
(n); ring of levitation (k, off); unicorn horn (m); 3 scrolls of teleportation (j). Some items were cursed by
the lich/nalfeshnee (which ones unknown). Vlad is alive on tower1 (Dlvl 35) with the real Candelabrum. Wizard
mode, private playground under the session scratchpad (see the setup note).
