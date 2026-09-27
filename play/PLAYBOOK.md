# Playbook: ascending a lawful dwarven Valkyrie in NetHack 3.6.7

`PLAYER.md` has the interface and the survival protocol; this file is the strategy. Lookups:
`knowledge/wiki/*.txt` (grep; `knowledge/INDEX.md`), kernel helpers `mon()`, `corpse()`, `obj()`,
`wiki()`, `wiki_page()`, and the source at `~/src/nethack-3.6.7/src` (if present) for exact rules.
**When a mechanic matters for a risky decision, check the wiki/source — don't trust memory.**

The only other LLM ascension (Astra, same character, 3 runs; `docs/research/astra-lessons.md`): both deaths
were **not HP deaths** — a sergeant's death ray at full HP in the Castle (no MR, no reflection), and
sliming after the invocation (no working cure at hand). The win came from patience: it retreated from the
Castle without MR and returned ~10,000 turns later fully equipped. It prayed only 4 times in 37k turns.

## A. Non-negotiables (instadeath and run-enders)

1. **No Castle, and no loitering on D20+ near soldiers, without magic resistance (MR) or reflection. Prefer
   both.** Get reflection early (Sokoban prize 50%, silver dragon scales, shield of reflection).
2. **Soldiers/sergeants/lieutenants/captains and anything seen zapping a wand may carry a death ray.** Never
   stand in line with one (row, column, diagonal) at range without MR + reflection. A **wand of sleep** is
   as bad without sleep resistance or reflection: 6d25 turns asleep beside the zapper (p3: an ogre king
   zapped one twice up its column). Monsters zap from NEXT to you too (muse.c), so melee doesn't get you out
   of the line. The harness pauses by name (SLEEP RAY / DEATH RAY / WAND ZAPPED AT YOU) and keeps a note on
   the zapper: get out of its lines, kill it at range, or zap it away.
3. **On `Slime`, `Stone`, `Strngl`, `TermIll`, `FoodPois`: stop everything; the very next action is a
   verified cure.** Keep a checked list in state.md: stoning → lizard or acidic corpse (carry 2+ lizard
   corpses from the midgame), prayer; sliming → fire (wand with known charges, scroll of fire) or a
   **self-zapped wand of polymorph — works even with MR**, prayer (not in Gehennom); illness → unicorn horn
   (apply repeatedly) or prayer; strangulation → remove the amulet, prayer.
4. **No multi-step movement/travel/explore with a hostile within 2 squares, near a known slime or
   cockatrice.** Fight one step at a time.
5. **Never batch attacks.** One `F`+direction per command, look, repeat. The harness enforces one command
   per `do`; don't defeat it with `multi=True` in fights.
6. **Send `z`/`a`/`t`/`r`... and then the direction/answer only after the prompt is on screen** (the harness
   stops a string if a prompt doesn't appear, e.g. an empty wand says "Nothing happens").
7. **Never swap a pet into water or lava** (moving onto a pet swaps places). Never let pets kill peacefuls/
   priests; never attack peacefuls; never engrave on altars.
8. **Prayer discipline**: track the last prayer turn (`bin/nh info` shows it); first prayer OK after ~T300;
   then ≥ ~1000 turns apart; **a wish adds 50–149 to the timeout**; pray only in major trouble (HP ≤ 1/7
   max or ≤ 5, Weak, deadly status); **never pray in Gehennom**.
9. **Two escapes, always** (the first may be empty): e.g. upstairs + Elbereth early; later a teleport wand,
   scrolls of teleportation, the quest artifact's invoke.
10. **Unknown charges are not available charges.** Record wand charges when known (engrave/zap results,
    shop identification); mark evidence in state.md: [seen] vs [inferred] vs [UNVERIFIED].
11. From the midgame: carry a **unicorn horn**, 2+ **lizard corpses**, a **remove curse** reserve (scroll,
    holy water, or marker + blank scroll). Wear **life saving** for boss fights once MR comes from armor.

## A2. Common early mistakes (seen in practice games — don't repeat them)
- **Never wield or wear an item of unknown B/U/C that you can't afford to have cursed.** Monster-dropped
  weapons (goblins' orcish daggers, etc.) are often cursed: a cursed weapon **welds to your hand** (no
  Excalibur, no switching back to the long sword) and cursed armor can't be removed. Test first: drop it
  where your pet will walk (a pet steps "reluctantly" over cursed items), or drop it on an altar (black
  flash = cursed). Throwing unknown daggers is fine; wielding is not.
- **Prayer only reliably fixes major trouble** (HP ≤ 1/7 max or ≤ 5, Weak/Fainting, stoning, sliming,
  strangling, lycanthropy, food poisoning/illness, stuck in rock/lava). Cursed items, a welded weapon with a
  free off-hand, blindness, etc. are *minor* trouble — at Luck 0 prayer usually won't fix them, and the
  prayer timeout resets anyway. Don't spend a prayer on minor trouble.
- Acid blobs: don't melee with your good weapon (passive corrosion); kill with thrown daggers or ignore.
- **Were-creatures** (`@` human form, `d`/`r` animal form): their animal-form bite gives lycanthropy
  ("You feel feverish") — major trouble, cured by prayer, holy water or a sprig of wolfsbane. They
  summon packs ("summons help"). When you change form you drop armor and even a welded weapon, and
  on stairs a third of what you drop falls to the level below. Fight them in `@` form or at range.
- Don't let a far-away travel target burn dozens of turns (use `travel(x, y, max_dist=N)`), and check that
  a target square isn't shop stock before "fetching" it.
- **Special rooms** (hack.c check_special_room). The entry message appears only once per room: treasure zoo,
  anthole, beehive, barracks, cockatrice nest, throne room, leprechaun hall, graveyard. Their monsters start
  asleep. The harness pauses (SPECIAL ROOM) and from then on keeps explore()/travel() out of the room and
  its other doorways.
  - Step back out unless the room is worth it.
  - To clear it, fight at the doorway (`fight_until_clear()` at full HP, one sleeper at a time, with
    `fight(x, y)`), then `forget_room()` to go in.
  - Soldier ants and killer bees are deadly early without poison resistance.
  - A cockatrice nest means stoning: gloves, a wielded weapon and a lizard corpse, or leave it.
  - A boulder can hide a trap: pushing one into a sleeping zoo moved the hero onto the magic trap under it,
    and its roar woke the whole zoo (p1: 165 → 89 HP in 3 turns). Clear a room from its doorway; never step
    into its never-seen squares while its monsters sleep.
- **Gold vaults and their teleporter** (vault.c, mklev.c). A vault is a closed 2x2 room holding 4 piles of
  gold. It has no door. A guard shows up on your 30th turn inside, asks "Hello stranger, who are you?", and
  makes you drop **all** your gold, including gold in bags.
  - Answer with your real name. For a lawful hero any other name costs alignment. "Croesus" sends the guard
    away but leaves you locked in.
  - Drop the gold and follow him out through the corridor he digs. It turns back into rock behind you, so
    keep walking to the real corridor.
  - A closet marked by a dust engraving "ad aerarium" just inside a room's door holds a one-time teleporter
    into the vault. The harness pauses and marks the closet avoided. Magic resistance makes the teleporter
    do nothing.
  - Use the teleporter on purpose only with a pick-axe or wand of digging and no gold on you: land, take the
    gold, and dig out through a vault wall before the 30 turns are up.
  - Gold lost to a guard stays on the vault floor and can be dug out the same way.

## A3. Poison, unknown items, genocide (checked in the 3.6.7 source)
- **Poison can kill outright until you have poison resistance.** Every poisonous hit (soldier ant and
  killer bee stings, centipede and giant spider bites...) poisons 1 time in 8, and a poisoning is instantly
  fatal 1 time in 30 ("The poison was deadly..."); every poisoned dart/arrow that hits: 1 in 30. So avoid
  long melees with killer bee swarms and soldier ants before you're resistant; fight them in a corridor,
  kill fast, use Elbereth. Get poison resistance early: eat killer bee / soldier ant / scorpion corpses
  (check `corpse(...)`; each gives it only with some chance), or a ring of poison resistance.
- **Unknown scrolls**: price-identify first. Read-test only at full HP, no monsters in view, not in a shop,
  not Confused, with nothing on the floor you care about. Blessed/uncursed genocide is the jackpot; an
  unknown scroll can also be amnesia (you forget the map and identities — note them in state.md first),
  fire, punishment, teleportation, create monster.
- **Genocide answers** (as a dwarven Valkyrie): **never `h`, "dwarf", `@` or "valkyrie"** — genociding
  your own race (dwarf, class `h`) or role (the valkyrie player-monster, class `@`) kills you (read.c).
  Uncursed (one species): "master mind flayer", then "mind flayer". Blessed (a whole class): `L` (liches),
  then `;` (sea monsters: eels drown you). A *cursed* scroll creates the monsters instead: answer with
  something harmless ("lichen").
- **Unknown potions**: don't drink-test while monsters are near (sleeping, blindness, hallucination) or
  while Burdened on dangerous levels. Dip-test and price-ID instead where possible; never quaff from a
  fountain for fun (water moccasins, nymphs, demons).
- **Old food can be "rotten"** (eat.c): any cursed food, and any non-corpse food older than 30 turns (50 if
  blessed) — food rations and candy bars you found included; lembas and cram never — has a 1 in 7 chance of
  "Blecch! Rotten food!": confusion, blindness for up to 50 turns, or unconsciousness for up to 10 turns
  (then the whole stack stays flagged rotten). Eat such food only on a safe square (Elbereth, no monster
  in view). Fresh safe corpses (`corpse()`) are the best food; eat before "Weak", not at "Fainting".
- **Unknown rings/amulets**: never put on (teleportitis, hunger, levitation you can't remove if cursed;
  amulet of strangulation kills in 6 turns — remove it at once, prayer fixes it).

## B. Character facts
- Valkyrie: +1 long sword (a), +0 dagger (b), +3 small shield (c), food ration; intrinsic **cold
  resistance** and **stealth**; **speed at XL7**. Strong melee. `#enhance` when told you're more confident.
- Dwarf: infravision. Most Gnomish Mines inhabitants (gnomes, gnome lords, dwarves, hobbits? no) are
  peaceful to dwarves → the Mines are comparatively safe. **Never eat dwarves** (cannibalism).
- Lawful, god **Tyr**. Excalibur: lawful + long sword + XL≥5 + fountain dips.

## C. Opening: D1–D4 (target XL5–8, Excalibur)
- Explore each level (`explore()`), fight weak monsters one at a time at doorways/corridors, keep the pet.
  Pick up: daggers (throw them: `t`, or wield later for dagger skill), armor you can wear, all wands, rings,
  amulets, scrolls, potions, tools, gems, food.
- Don't put on unidentified rings/amulets (strangulation, teleportitis, levitation-lock, hunger).
- Eat fresh safe corpses (`corpse('name', age=turns_since_death)`), keep rations for emergencies.
- **Excalibur**: at XL5+, stand on a fountain (never in Minetown) and `#dip` the long sword. 1/6 per dip;
  other outcomes ~1/30 each: water moccasins, a water nymph (steals), **a water demon** (dangerous at XL5;
  sometimes grants a wish if the level is shallow). Full HP, escape route (upstairs) planned. Fountains dry
  up — spread dips over several fountains/levels; Astra needed 6, 12 and 27 dips.
- Sokoban's entrance is the up staircase on the level **just below the Oracle** (Oracle: D5–9). The Mines
  branch staircase is on D2–4.

## D. Early-mid game: Mines → Minetown → Oracle → Sokoban → Mines' End (XL8–12, AC ≤ 0)
- **Minetown** (Mines level 3–4, ~D5–8): temple (co-aligned priest: donate **400×XL** gold — at least
  400×XL and **less than 600×XL** — for protection: the first donation gives 2–4 AC, later ones +1),
  shops (price-identify; **buy a magic marker on sight**; buy candles — the Candelabrum needs 7), altar
  (drop items to learn B/U/C). Keep the Watch peaceful: no fountain dipping/quaffing, no door breaking,
  no theft.
- **Sokoban** (4 levels, up): on arrival run `sokoban.solve()` (it identifies the variant and executes the
  verified solution push by push); if it pauses, read why, deal with the monster/pet, and `cont` or call
  `solve()` again (it resumes from the board as it is). Only if the board no longer matches the plan, solve
  by hand from `knowledge/wiki/Sokoban_Level_*.txt` with `sokoban.push(x, y, 'dirs')`.
  Boulders only move orthogonally; you can't squeeze diagonally between boulders; breaking boulders or
  reading earth costs Luck. A monster behind a boulder blocks the push — wait or deal with it. The top
  level is a zoo; fight at a chokepoint (stand in the doorway, `fight_until_clear()` at full HP). Prize: bag
  of holding or amulet of reflection.
- **Mines' End luckstone** when strong enough (XL10+). Keep it (it also locks in good Luck).
- AC: dwarvish iron helm, dwarvish mithril coat (from Mines dwarves), boots, gloves, cloak. AC ≤ 0 before
  D10; ≤ −5 before D20.
- Intrinsics to collect: poison resistance (killer bees, soldier ants, scorpions... check `corpse()`
  benefits), telepathy (floating eye corpse — kill it at range, never melee), fire/sleep/shock resistance.
  Telepathy shows only minded monsters: spheres, gas spores, zombies, mummies, golems and vortices are
  invisible to it — a dark corridor can still hold an exploding sphere.

## E. Midgame: D10–D25 (XL14+, MR and reflection, then the Castle)
- **Quest portal** level (D11–16) gives a telepathic message; the portal room may sit behind a secret door
  (search the corridor dead ends). **Walking NEXT to the quest leader (the Norn) is the visit** — no #chat.
  It needs **XL14 AND alignment record 20+ ("piously")**: below XL14 she just sends you back; with a lower
  record the rejection COUNTS, and after 7 you are expelled for good — no Bell of Opening, no ascension.
  Check first with `piety()` (a stethoscope applied to yourself; also a wand of probing at yourself or
  enlightenment); record grows +1 per hostile kill and drops with murders/hypocrisy/-5 Elbereth attacks.
  travel()/step() refuse to end next to the leader until then (quest_ok=True overrides). Nemesis **Lord
  Surtur** (fire giant king) carries the **Bell of Opening** (required): fire resistance for his lava level;
  his claw STEALS the Orb of Fate / Amulet and he teleports away to heal (usually to the up stairs) — expect
  him back. The Orb shows as "a glass orb named The Orb of Fate": `pickup('Orb of Fate')`.
- **Medusa** (D21–24): reflection or a blindfold/towel (be blind before she comes into view), a way over
  water (levitation, water walking, cold wand ice bridge, scroll of earth). With reflection her gaze kills
  her; otherwise fight blind (telepathy shows her; `fight(x, y, force=True)` on her square). She starts
  ASLEEP: noise wakes her — in the QA run a kicked-open door revealed her, awake: stoned. The harness flags a
  probable Medusa level (Dungeons of Doom 21+, water all around) with `!! PROBABLY MEDUSA'S LEVEL` and
  refuses travel/explore/kick_door there until you are Blind or wear known reflection (inventory() learns a
  worn shield of reflection / silver dragon scale mail; medusa_ok=True if you know better). Her level's
  floor can be dug down (a wand of digging skips her island — but you come back up this way with the Amulet).
  Medusa's level is 1-4 levels ABOVE the Castle (dungeon.def: medusa @ (-5, 4), castle = the bottom level):
  digging down may land on a filler level; its `<` then leads up onto Medusa's `>` on her island, next to
  her (asleep). Reflection kills her with her own gaze only if she can see you: don't be invisible then.
  **Digging down when every square touches water** (p3 shift 11, checked in dig.c/trap.c):
  1. Put on levitation first. A hole dug while levitating doesn't swallow you, and a water-filled hole
     can't drown you.
  2. Zap digging down: `zap(wand, '>')`.
  3. Take the ring off. You may "escape your hole": that's the 1-in-5 escape roll for a known trap.
  4. Press `>` on the hole. That plunges you through with no escape roll and no message; you land on a random
     square of the level below.
- **Eels** (Medusa, the Castle moat, any water): "The giant eel swings itself around you!" = HELD: its NEXT
  hit drowns you — LEVITATION DOES NOT HELP (QA death). That turn: engrave Elbereth (it flees and lets go;
  impossible while levitating), kill it, or teleport (not on the Castle: no-teleport). The harness pauses
  with `HELD — ...`. Stay 2 squares from water where eels swim.
- **Poison**: without poison resistance every poisonous bite/sting (snakes, soldier ants, bees, rabid rats,
  quasits) can kill outright (1 in 30) — the harness rates them dangerous and never auto-fights them then.
- **Castle** (the bottom level of the Dungeons, 1-4 levels below Medusa) — only per rule A1. Facts from
  castle.des / zap.c / dbridge.c (3.6.7): the raised drawbridge is in the moat on the WEST wall; **two giant
  eels sit in the moat squares right north and south of it** (sharks at the corners) — the land square in front
  of the bridge and the bridge square itself are next to both. A cold ray freezes each moat square it crosses:
  under the raised bridge it becomes ice, and on an eel's square the eel is forced out onto ice (it can't
  drown you there); the ice melts after a while. Then a force bolt / striking at the bridge: "The drawbridge
  disintegrates!" leaves walkable ice and an open gateway (and wakes the whole castle). The passtune (5 notes,
  prayer/Oracle or Mastermind with an instrument) opens it instead. Inside: 8 soldiers + a lieutenant in the
  entry courtyard, 2 soldiers per corner tower, 4 dragons, a throne-room court; storerooms of weapons, armor,
  food, gems. **The wand of wishing** is in a chest in ONE of the 4 corner towers (reached by doors from the
  long halls along the top and bottom walls), on a square with a burned Elbereth and a CURSED scroll of scare
  monster (leave it). No digging (all walls undiggable), no teleporting, soldiers ignore Elbereth. Its trap
  doors (east corridor) are the only way down, into the Valley. Minotaurs in the surrounding mazes ignore
  Elbereth.
- **Wishes** (after MR/reflection are covered as needed): blessed +2 gray dragon scale mail (MR) → "2
  blessed scrolls of charging" (recharge the wand of wishing **exactly once**, to 3) → blessed +2 speed
  boots → "2 blessed scrolls of genocide" (genocide `L` liches first) → blessed magic marker → blessed
  potions of gain level if short of XL14 → blessed amulet of life saving / reflection if missing.
  Ask for +2 (not +3) and "2" (not 3) of stackables. Wrest the last wish only somewhere safe.
  At the "For what do you wish?" prompt the harness pauses: answer ONLY with `cont --reply '<wish><CR>'`.
  Never Esc it or send an empty line — NetHack turns an empty wish into a RANDOM object (the harness
  refuses both). A blessed magic lamp: #rub it (it gets wielded — re-wield your weapon after); the djinni
  appears 1 time in 3 per rub and grants the wish 80% of the time when blessed.
- Stop enchanting Excalibur at +5 (evaporation risk above). Never controlled-polymorph into your own race.
  Never put a wand of cancellation into a bag of holding.

## F. Gehennom (MR mandatory; prayer doesn't work)
- Valley of the Dead via the Castle trapdoors (the Castle has no down stairs; its trap doors are the way —
  obs names them `trap door` once looked at). Temple of Moloch — don't anger its priest; its altar is
  UNALIGNED: never pray or #offer there.
- Incubi (`&`, from the Valley on): they take off your armor and RINGS — a levitation ring over water or lava
  is then death. Kill them at range, answer n to "remove your ...?". A **succubus can't seduce a female
  Valkyrie** (mhitu.c could_seduce: same gender), only claw — an ordinary fight. Vampires hide as fog
  clouds, vampire bats and wolves (killing the shape makes the vampire rise).
- Juiblex (swamp; engulf → illness), Orcus (town; wand of death), Asmodeus, Baalzebub.
- **Mind flayers / master mind flayers** (`h`, purple): each tentacle hit your HELMET doesn't stop (it stops 7
  in 8) eats your brain: −1-2 Int, and with Int at 3 the next one KILLS you — life saving doesn't help. Never
  fight one helmetless or at low Int (`fight()` refuses; the obs header shows `LOW-Int:N` at 6 or less and a
  `BRAIN EATEN` pause names your Int). Kill them at range (wand of sleep/striking/death, daggers), Elbereth,
  or leave. Blessed genocide of `h` removes them (and dwarves — fine this late).
- **Where things are** (dat/dungeon.def; Gehennom has 20-24 levels, the Valley is Gehennom level 1, so
  Gehennom level N = the Valley's Dlvl + N - 1): Asmodeus 2-7, Juiblex's swamp 4-7, Baalzebub 6-9, the Vlad's
  Tower staircase 9-13, Orcus Town 10-15, the Wizard's Tower (three stacked levels) from 11-16, the two
  fake-tower levels 6th to 3rd from the bottom, the vibrating square on the level just above the Sanctum
  (the last level).
- **Vlad's Tower branch is on Gehennom level 9–13 (8–12 below the Valley)**. Search there: with several `<`
  on that level, `go_up()` looks at each and leaves tower ladders for last. A ladder with an object on it
  looks like stairs, and the one you can reach is preferred. The branch staircase leads into the tower.
- **Vlad** has the **Candelabrum**; attach 7 candles to it. He is very fast and covetous: he teleports next
  to you, hits, and teleports off to heal.
  - Hold your square with `fight_until_clear(radius=3, hold=30, unseen=True)`. It fights him each time he
    comes back (QA: this killed him twice, dark or lit). A light source doesn't help.
  - Keep Elbereth for healing breaks.
  - He leaves NO corpse: the Candelabrum drops where he dies (`pickup('Candelabrum')`).
  - Wolves down here may be vampire lords. The obs says so, and auto-fight leaves them to you.
- **Wizard's Tower** (dat/yendor.des). The Wizard has the **Book of the Dead**. He resurrects and harasses,
  so keep remove-curse reserves, and don't wear levitation near him.
  - **The tower**: the west part (28x12) of three stacked levels; the rest of each level is a maze.
    - Its outer walls can't be dug or phased through. The levels are no-teleport with a hard floor.
    - The level stairs are outside the tower.
  - **The way in** is the magic portal on the fake-tower level **fakewiz1**. Each of the two fake-tower levels
    has a tiny walled chamber (3 squares plus a nook above and below) inside a moat ring, with a kraken in the
    moat and a lich and a vampire lord inside.
    - Only one of the two chambers holds the portal, at its center. The other holds a random amulet.
    - Freeze the moat, dig through the chamber wall (these walls can be dug), kill the guards, and step onto
      the portal. Squeaky boards surround the center.
    - The portal lands you inside the lowest tower level. Its up ladder leads to the middle level, whose up
      ladder leads to the top level.
  - **Top level**: the Wizard sleeps in a closed 3x1 room with a hell hound and a vampire lord. The Book lies
    under him.
    - The room is ringed by walls, then a moat holding 4 krakens, 4 giant eels and 2 piranhas. Their wraps
      drown you, and travel() refuses the moat's edge while they're in sight.
    - Freeze a path with a cold ray or frost horn (a cold ray also forces an eel out of hiding onto the ice),
      then dig through the room's wall. The walls inside the moat can be dug.
    - Squeaky boards sit at the room's two gaps.
    - He WAITS until he SEES you or is hurt: waking him (a whistle, a squeaky board) is not enough, because
      mon.c wake_nearto() leaves a unique's "wait for you" strategy on (monmove.c clears it only on sight or
      damage; so do Vlad and the quest nemeses). p1 shift 33 blew a whistle and he stayed put for 30+ turns.
      Open a sightline instead (zap digging across the moat: it digs one wall square of the maze level) and
      fight where few can reach you. Dig it STRAIGHT, in his row or column: vision.c doesn't see through a
      diagonal gap between two wall corners more than one square deep (p1 shift 34 dug (39,12) diagonally to
      him at (40,11) and waited 37 turns for nothing; a ray north through (40,13) woke him at once).
    - Inside his tower he heals at the tower's LADDER (teleport.c rloc(): the down ladder; the up ladder on the
      bottom level), not at the level's up stairs: covetous_ring() knows. His death drops the Book where he
      stood: over the moat it sinks — freeze that square and the invocation items come up onto the ice.
    - Kill him and take the Book. He comes back later ("double trouble", curses, summoned nasties); magic
      resistance stops his touch of death.
- **Invocation** (checked in a wizard-mode run): walk the bottom level until "You feel a strange vibration
  under your feet" (obs: `vibrating square` in features once seen, `(under you)` on it). All three items must
  be UNCURSED. Attach the candles by applying the CANDLES ("Attach your candles to your candelabrum? y"; it
  holds 7) — never light the candelabrum off the square (the candles are "rapidly consumed"). On the square:
  apply the candelabrum ("...glows with a strange light!" = 7 candles, right square), apply the Bell ("issues
  an unsettling shrill sound..."; each ring uses a charge — "But it makes no sound." = empty, needs charging),
  then read the Book within 4 turns ("You are standing at the top of a stairwell leading down!").
  "You have a feeling that something is amiss" = not primed (bell too long ago, candles not 7/lit) and it
  raises the dead. `invoke()` does all of this with every check (refuses off the square, with a cursed or
  BUC-unknown item — force=True for unknown — or fewer than 7 candles). **The way back**: the new `>` is
  ringed by 8 fire traps, 2 rows of floor, then a 2-wide moat, and you come back up onto it with the Amulet:
  `step_onto(x, y)` onto one fire trap (fire resistance: no HP loss, but scrolls/potions/spellbooks can
  burn — bag them; without it `step_onto(x, y, risky=True)`: 2d4 HP and some max HP too), then FREEZE the moat with a wand of cold / frost horn ("The moat is bridged with ice!")
  and walk across — or levitate, but put the ring on your LEFT hand: in the wizard-mode test the Wizard's
  harassment cursed the wielded sword, and a cursed weapon locks the right-hand ring on ("You cannot free a
  weapon hand to remove the ring.") — stuck floating above the up stairs. Keep remove curse / holy water.
- **Sanctum** (no-teleport, no magic mapping): entering the temple turns the high priest(ess) of Moloch
  hostile — clerical spells (insects, paralysis without MR, lightning, fire pillars, curses) and a 4d10
  weapon. Each hit on it while YOU stand in its temple (door included) may bring Moloch's lightning:
  reflection stops the damage, not the flash — you go BLIND (telepathy + a blindfold makes the flash
  harmless; else keep the unicorn horn ready). It never leaves its temple: ranged attacks from outside
  avoid the lightning. Take the Amulet with `pickup('Amulet of Yendor')` (spelled out).

## G. Ascension run
- Climb to D1 with the Amulet ("mysterious force" setbacks — budget turns and food). Kill the Wizard each
  time he returns (death wand), keep the Amulet safe.
- The Wizard (often invisible: `I`) STEALS the Amulet ("It steals the Amulet of Yendor!": a `THEFT` pause
  and a `!! STOLEN` obs line) and teleports off; he keeps coming back to harass — kill him to get it back.
  He follows you through level teleports and onto the Planes.
- Planes: apply the Orb of Fate (crystal ball) or read magic mapping to find each plane's portal; carry
  charging for it. On Air and Water the game keeps no map — the harness remembers the portal (`magic portal
  (remembered)` in features) so `travel(x, y)` can aim at it. Air: levitate or fly (otherwise 3 steps in 4
  fail); clouds `#` block sight. Fire: smoke blocks sight. Water: levitation and water walking don't work;
  move only inside air bubbles with `step()` (`travel()` refuses there: the bubbles drift and it walks you
  into the water — soaked scrolls, diluted potions, rust, drowning without magical breathing).
- **Astral**: arrive at full HP with life saving worn, a death wand with verified charges, full healing,
  a unicorn horn, conflict off, free action. Identify the Riders: **never death-ray Death, never teleport a
  Rider**. Player-monsters there (`valkyrie called ...`) are level 15-30, often with artifacts. Before
  `#offer`: confirm the priest's god by farlook ("high priest of Tyr" — shown only from next to it; the obs
  keeps it once seen; a priest standing on its altar is named in `features`), take off levitation,
  step onto the altar, `:` should read "high altar to Tyr (lawful)". Then `ascend()`: it re-checks all of that (Astral Plane, on an altar, not
  levitating, the `:` look names YOUR alignment — another god's altar ends the game without winning — and one
  real Amulet in the pack) and offers it (verified in a wizard-mode run: "You ascend to the status of
  Demigoddess..."). (From afar
  every Astral altar reads "aligned high altar"; the alignment shows only from an adjacent square — obs
  updates it then.)

## H. Habits
- Farlook every ambiguous glyph (the harness does it for new monsters; statues look like monsters).
- Mark every trap (`^`); identify with the `^` command; avoid unknown traps before MR (polymorph traps
  destroy armor; level teleporters and trap doors separate you from pets and stashes).
- Levels with water/lava: read the terrain before moving; never trust visual spacing around `}`.
- Keep a stash on a quiet level near the upstairs; log it in state.md.
- Name item types as you learn them (`#name` → item type); record identifications in state.md.
- Engrave-test unknown wands (not in shops; never zap unknown wands toward pets).
- Scare monster scroll: pick up at most once (it crumbles on the second pickup); it's a permanent floor
  ward that even minotaurs respect.
- After any interruption (reconnect, popup), look at the screen before the next key.
