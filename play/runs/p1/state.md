# p1 — current state (rewrite as things change)

## Character
- Name/role: P1 the Woman-at-arms — lawful female dwarven Valkyrie, god: Tyr (seed 101, local practice game)
- Turn / Dlvl / XL / HP / Pw / AC: **T:20025 / DL25 (almost certainly THE CASTLE: doors heard opening/crashing, a land-mine "Kaablamm" in the distance, walled maze on the left) standing ON the DL25 up stairs (2,20) in the bottom-left corner** / **XL13** (Exp 40965; XL14 at 80000) / **128/145** / 28/28 / **AC -11** (blessed +2 GRAY DRAGON SCALE MAIL + +0 SHIELD OF REFLECTION + orcish helm + elven cloak + blessed leather gloves + low boots + 4 divine protection). Wielding blessed rustproof **+6 EXCALIBUR** (long sword EXPERT; never enchant it again).
- **MAGIC RESISTANCE (GDSM) + REFLECTION x2 (shield b AND amulet I, both worn).**
- **MEDUSA IS DEAD (T:19944, her own reflected gaze).**
- Rings worn: f prot. from shape changers (RIGHT), u SLOW DIGESTION (LEFT). Amulet worn: I uncursed AMULET OF REFLECTION.
- **Gold: $0 carried, 2850 in the bag D** (the old "~$8894" figure was a bookkeeping error — the bag listing at T:19785 says 2850). Next protection: 400 x XL = 5200 (XL13) — not affordable.
- Food: last meal rock troll T:16311; slow digestion worn, not hungry. Carried: J 2 food rations, B C-ration, O K-ration, y 6 royal jelly. Bag: orange, pancake, candy bar, slime mold, fruit juice.
- Attributes: St 18/10, Dx 16, Co20 In10 Wi11 Ch7.
- Intrinsics: cold res, stealth, infravision, speed (intrinsic Fast), POISON RES, FIRE RES, TELEPATHY (blind only), MAGIC RESISTANCE (GDSM), REFLECTION (shield + amulet). Excalibur: auto-search, drain res. NO sleep res, NO shock res (ring in the bag).
- Luck >= 0. Alignment record high; no peacefuls killed.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:1271 | welded cursed dagger (MINOR — mistake) | accepted, trouble NOT fixed |
| T:2016 | lycanthropy (MAJOR) | CURED |
| T:3401 | Weak from hunger (MAJOR) | fixed |
| **T:18211** | **no trouble, timeout 0, on the DL15 co-aligned altar with plain water on it** | **"Tyr is well-pleased"; the water became HOLY WATER** |
- Lamp wish at T:18215 added 50-149. **prayer_check() at T:20014: 98% odds for MAJOR trouble (1803 turns since).** Prayer is available as an emergency heal now (HP <= 145/6 = 24 at XL13).
- Emergency healing: **t blessed FULL HEALING, w FULL HEALING, M healing**, swirly HEALING (bag). Escapes: the DL25 `<` (2,20) (you are ON it), prayer. **The Castle is NO-TELEPORT** (wands G/Z and scrolls k are useless there); soldiers (@) IGNORE Elbereth.
- **Stoning cure: S = uncursed LIZARD CORPSE.**

## Equipment worn/wielded
- a: blessed rustproof +6 EXCALIBUR (wielded). b: +0 SHIELD OF REFLECTION. x: blessed +2 GDSM (MR). n: uncursed +0 orcish helm. V: uncursed +0 elven cloak. r: blessed +0 leather gloves. z: uncursed +0 low boots. Rings f (right) + u (left). I: uncursed amulet of reflection. H: uncursed elven dagger (quivered).

## Key inventory (T:20025, 44 letters, limit 52 — bag things before picking up)
- **R: WAND OF COLD (named "cold")** — freezes moat squares, incl. under a raised drawbridge.
- **h: WAND OF SLEEP (identified T:19531: "The sleep ray hits the minotaur" x2 with the bounce; 1 charge used)**. Ray bounces — reflection protects me from my own bounce.
- **j: PICK-AXE (now carried, NOT in the bag)**: dig walls/boulders/statues. Applying it wields it: re-wield Excalibur (`w` `a`) after every dig. The kernel helper `dig_dir(dirkey)` does apply-j + direction + re-wield.
- **Striking: C EMPTY ("Nothing happens" T:19139), Y used 4 (T:19145), c used 4 (T:18572).** Use Y or c for the drawbridge.
- e: WAND OF CANCELLATION (named) — NEVER in the bag of holding, never at yourself.
- l: uncursed BLINDFOLD. A: uncursed UNICORN HORN (cured hallucination + blindness this shift). S: LIZARD CORPSE. t: BLESSED FULL HEALING. w: FULL HEALING. M: HEALING.
- **m and W: blessed (oil) lamps — BOTH OUT OF OIL (W died T:19931). NO LIGHT SOURCE now.**
- G, Z: WAND OF TELEPORTATION (Z 2 used). g: WAND OF DIGGING (1 used). k: 6 scrolls of teleportation. o: WAND OF FIRE. E: wand of lightning (0:3).
- T: uncursed MAGIC MARKER (13 charges). q: 5 uncursed blank scrolls. Write only KNOWN types (remove curse via its label `write_scroll('XOR OTA')`).
- Potions: i 2 black (= probably object detection), N murky (unknown), F fruit juice.
- v: uncursed gray stone. d: KEY (for the wand-of-wishing chest: locked, never trapped).
- **D: bag of holding ("BoH prize")**: 2850 gold, wand of magic missile, scroll ELAM EBOW (100zm: confuse monster/destroy armor/food detection/magic mapping), scroll of create monster, scroll of enchant weapon, 3 scrolls of fire, scroll of light, yellow spellbook, potions: swirly HEALING, booze, sky blue CONFUSION, 2 MONSTER DETECTION (1 blessed), black, cursed speed, fruit juice; wand of lightning (0:2), wand of CREATE MONSTER, can of grease; rings REGENERATION, POLYMORPH CONTROL, SHOCK RESISTANCE, bronze (blessed, base 100), ivory, wire, coral; gems; orange, pancake, candy bar, slime mold.

## Identified appearances
- Scrolls: ZELGO MER identify, EIRIS SAZUN IDISI amnesia, GARVEN DEH light, HACKEM MUCHE fire, TEMOV teleportation, FOOBIE BLETCH enchant weapon, KERNOD WEL scare monster, THARR create monster, ZLORFIK gold detection, XOR OTA = REMOVE CURSE (named). NR 9 (200) = earth or taming. ELAM EBOW (100) unknown.
- Potions: yellow sickness, brilliant blue blindness, cyan oil, pink GAIN LEVEL, swirly HEALING, golden SPEED, ruby FULL HEALING, dark MONSTER DETECTION, orange BOOZE, sky blue CONFUSION, dark green FRUIT JUICE, clear WATER; black probably object detection; murky unknown.
- Wands: marble lightning, iridium striking, oak magic missile, crystal speed monster, short TELEPORTATION, zinc nothing, ebony CREATE MONSTER, balsa FIRE, platinum DIGGING, glass = CANCELLATION (named), uranium = COLD (named), **aluminum = SLEEP (identified)**.
- Rings: diamond fire res, iron prot. from shape changers, engagement REGENERATION, agate = base 150, twisted POLYMORPH CONTROL, clay SHOCK RES, opal SLOW DIGESTION, topaz GAIN CON.
- Amulets: spherical = STRANGULATION, hexagonal = REFLECTION. Armor: polished silver shield = SHIELD OF REFLECTION; etched helmet (one of helmet/brilliance/opp. alignment/telepathy); faded pall = elven cloak.

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1-12 | main | see older notes in journal; DL3 Mines entrance `>` (46,18); DL6 Oracle; DL7 Sokoban up (14,15); DL10 neutral altar (16,7) |
| **13** | main | **QUEST PORTAL (73,17)** (needs XL14 + piety). `<` (34,16), `>` (6,13). Yellow light east of the `<`. |
| 14 | main | `<` (54,5), `>` (35,7). Peaceful WHITE unicorn (co-aligned). |
| **15** | main | `<` (11,4). `>` (58,5). **LAWFUL ALTAR to Tyr (48,19)**. Teleport trap (35,18). |
| 16-20 | main | 16: `<` (8,17) `>` (3,7). 17: `<` (30,15) `>` (71,16). 18 ROGUE: `<` (37,4) `>` (16,2). 19: `<` (45,17) `>` (34,19). 20: `<` (49,17) `>` (39,10), POLYMORPH TRAP (9,16). |
| 21 | main | `<` (7,6), `>` (11,17). Throne room cleared (throne (48,7) intact). |
| 22 | main | `<` (42,6), `>` (4,5). |
| **23** | main | **MEDUSA'S ISLAND (variant 1) — MEDUSA DEAD (statue at (37,11))**. `<` (7,16) west strip; my dug HOLE (5,16). **`>` (38,12) in the central room**: Perseus's statue broken there: a CURSED +0 shield of reflection + a sack left on the stairs. Wand (64,17), armor (67,19) on the east islands (water). |
| **24** | main | **CORRIDOR MAZE** (levels below Medusa are mazes 4/5). **`<` (15,20)** (SW) -> Medusa's `>`. **`>` (52,11)**. Hole (34,15) (the captain's; bypass dug at (35,15)). Magic trap (43,20) (bypass dug at (43,19)). LEVEL TELEPORTER (23,4) (MR blocks it). Dart traps (66,6), (51,18). Teleport trap (76,14). |
| **25** | main | **Probably the CASTLE.** Arrived on `<` (2,20) (bottom-left corner, walled maze). RUST TRAP (4,20). Heard doors open/crash and a land mine. A wounded CAPTAIN with a WAND OF DIGGING fell from DL24 to here (somewhere). |
| Mines | Mines | Minetown = Mines 3 (DL6): temple of Odin (neutral), shops. Mines' End DL11. |
| Sokoban | | ALL SOLVED. |

## Threats / known dangers
- **Castle (wiki Castle.txt)**: up stairs in the small left maze; castle in the middle surrounded by a MOAT with 4 SHARKS + 4 GIANT EELS (stay 2+ squares from water; HELD = Elbereth doesn't work on... engrave anyway / kill it). Barracks on both sides of the entry hall (soldiers, sergeants, lieutenants, captains), 2 soldiers per corner tower, 8 soldiers + a lieutenant in the atrium. Throne room: 27 monsters from E H L M N O R T X Z (LICHES), chest behind the throne. Two random DRAGONS in each alcove between the storerooms. Floor undiggable (except trap-door squares); castle walls undiggable, maze walls diggable. No down stairs: the TRAP DOORS at the back (east) lead to the Valley. No teleport on the level. Mazes and some floors are unlit (and I have no light source now).
- **WAND OF WISHING**: locked (never trapped) chest in one of the 4 corner rooms, on a burnt Elbereth + scroll of scare monster, 2 soldiers each. Key d opens it (`unlock()` / `loot_all()`).
- Soldiers (@) ignore Elbereth; MR + reflection cover wand death rays; they hit hard in groups — fight in corridors/doorways; zap SLEEP (h) down a line of them.
- Fire elementals/fire breath destroy potions/scrolls. Quantum mechanics teleport (not on the Castle). Gelatinous cubes: force bolt from range.

## Objective and plan (after shift 21)
1. **Confirm DL25 is the Castle**: explore east from (2,20) through the west maze; the moat `}` and the castle's west wall with the DRAWBRIDGE (middle row) appear. If it is a filler maze instead: find `>` (dig through maze walls with the pick-axe j rather than searching).
2. **Drawbridge (3.6.7 zap.c, checked)**: stand in the drawbridge's row, 2+ squares west of the moat edge (eels), nothing friendly in line. (a) `zap('R','l')` COLD east: the moat under the raised bridge turns to ice (DB_ICE). (b) `zap('Y','l')` (or c) STRIKING east: the force bolt passes the span and hits the portcullis -> destroy_drawbridge: the span becomes ICE (walkable), the portcullis a doorway. Order matters (cold first, else the span becomes open moat). Never stand on the drawbridge/portcullis squares before it's destroyed.
3. Then fight the soldiers at the gate one line at a time (sleep ray h first), heal with the potions, retreat to the west maze / `<` if HP < 60%. Check all 4 corner towers for the wishing chest.
4. Wishes (PLAYBOOK E): 2 blessed scrolls of charging (recharge the wand once), blessed +2 speed boots, 2 blessed scrolls of genocide, blessed magic marker, blessed potions of gain level (XL14 for the quest), blessed amulet of life saving.
5. XL14 (80000 Exp) + piety for the quest (DL13 portal).
