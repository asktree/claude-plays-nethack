# p1 — current state (rewrite as things change)

## Character
- Name/role: P1 the Woman-at-arms — lawful female dwarven Valkyrie, god: Tyr (seed 101, local practice game)
- Turn / Dlvl / XL / HP / Pw / AC: **T:20376 / DL25 = THE CASTLE (inside!)**, standing at **(32,12)** in the corridor between the antechamber and the throne room (on a partly eaten ICE TROLL corpse — trolls revive; a wand of digging lies here too) / **XL13** (Exp 51631; XL14 at 80000) / **97/145** / 28/28 / **AC -10** (orcish helm now very rusty) / **Burdened** (the cursed bag doubles its contents' weight).
- A LIEUTENANT lies ASLEEP (sleep ray T:20359, 6d25 turns) ON the throne-room door (34,12) = a plug; awake soldiers behind it (one zaps a wand of STRIKING — MR says Boing). Throne room still has 2 fire giants (one sped up), 2 ogre lords, a troll, soldiers, and a PEACEFUL black naga (35,13) — never attack it.
- **MAGIC RESISTANCE (GDSM) + REFLECTION x2 (shield b + amulet I).** MEDUSA DEAD (T:19944).
- Rings worn: f prot. from shape changers (RIGHT), u slow digestion (LEFT). Amulet I = amulet of reflection, now **CURSED** (can't remove; harmless).
- Food: ate royal jelly T:20274 + part of an ice troll T:20376. Carried: J 2 food rations, B C-ration, O K-ration, y 5 royal jelly.
- Attributes: St 18/xx (royal jelly "You feel strong!"), Dx 16, Co20 In10 Wi11 Ch7.
- Intrinsics: cold res, stealth, infravision, speed (Fast), POISON RES, FIRE RES, TELEPATHY (blind only — the BLINDFOLD l shows every minded monster on the level: used 4x this shift), MR (GDSM), REFLECTION. NO sleep/shock res.
- Luck >= 0. Alignment record high; no peacefuls killed.

## !!! CURSED BAG OF HOLDING (T:~20334, an invisible lich's curse-items spell)
- **D "BoH prize" is CURSED: DO NOT OPEN IT** (#loot/apply/bag_take/bag_put: each opening makes every item inside vanish with 1/13 chance). It holds 2850 gold, the LAST FULL HEALING (w), swirly HEALING, rings (regeneration, polymorph control, shock res...), wands (magic missile, lightning 0:2, create monster), scrolls (enchant weapon, 3 fire...), can of grease, etc. Fix FIRST: blessed scroll of remove curse (read -> uncurses the whole pack) or holy water (#dip the bag). -> plan the first wish accordingly.
- Also cursed now: k 6 scrolls of teleportation (cursed = random LEVEL teleport), Z wand of teleportation.
- Potions LOST to lich cold touches (destroy_item works through cold resistance): t blessed full healing, M healing, murky N, fruit juice, the 2nd black potion. The 1st black potion was quaffed = **OBJECT DETECTION** (identified). **No healing potion outside the bag: prayer is the emergency heal.**

## Prayer log
| turn | reason | result |
|---|---|---|
| T:1271 | welded cursed dagger (MINOR — mistake) | accepted, trouble NOT fixed |
| T:2016 | lycanthropy (MAJOR) | CURED |
| T:3401 | Weak from hunger (MAJOR) | fixed |
| **T:18211** | **no trouble, timeout 0, on the DL15 co-aligned altar with plain water on it** | **"Tyr is well-pleased"; the water became HOLY WATER** |
- Lamp wish T:18215 added 50-149. ~2165 turns since the last prayer: prayer_check() ~98% for MAJOR trouble (HP <= 145/6 = 24 at XL13). NOT prayed this shift.
- Escapes: the DL25 `<` (2,20) far west (through the courtyard + my dug maze passages); the Castle is NO-TELEPORT. Soldiers ignore Elbereth.
- **Stoning cure: S = uncursed LIZARD CORPSE.**

## Equipment worn/wielded
- a: blessed rustproof +6 EXCALIBUR (immune to disenchanters: DRLI defence, checked in zap.c drain_item). b: +0 SHIELD OF REFLECTION. x: blessed +2 GDSM. n: very rusty +0 orcish helm. V: +0 elven cloak. r: blessed +0 leather gloves. z: +0 low boots. f+u rings. I: CURSED amulet of reflection. H: elven dagger (quivered).

## Key inventory (T:20376)
- Wands: **R COLD** (4 used: 1 engrave + 3 zaps; 0-4 left), **h SLEEP** (3 used), **s SLEEP** (new, from a soldier, 1 used), **p MAGIC MISSILE** (new), Y striking (5 used: 0-3 left), c striking (4 used), C striking EMPTY, e CANCELLATION (never in a bag), o FIRE, E lightning (0:3), g DIGGING (1 used), G/Z teleportation (useless here).
- l BLINDFOLD (telepathy scans), A UNICORN HORN, S LIZARD CORPSE, d KEY (for the wishing chest + locked doors), j PICK-AXE, T MAGIC MARKER (0:13), q 4 blank scrolls, m/W empty lamps, v uncursed gray stone.

## Identified appearances
- Scrolls: ZELGO MER identify, EIRIS SAZUN IDISI amnesia, GARVEN DEH light, HACKEM MUCHE fire, TEMOV teleportation, FOOBIE BLETCH enchant weapon, KERNOD WEL scare monster, THARR create monster, ZLORFIK gold detection, XOR OTA = REMOVE CURSE (named). NR 9 (200) = earth or taming. ELAM EBOW (100) unknown.
- Potions: yellow sickness, brilliant blue blindness, cyan oil, pink GAIN LEVEL, swirly HEALING, golden SPEED, ruby FULL HEALING, dark MONSTER DETECTION, orange BOOZE, sky blue CONFUSION, dark green FRUIT JUICE, clear WATER, **black OBJECT DETECTION**; cloudy = PARALYSIS? (a soldier's thrown cloudy potion: "Something seems to be holding you") .
- Wands: marble lightning, iridium striking, oak magic missile, crystal speed monster, short TELEPORTATION, zinc nothing, ebony CREATE MONSTER, balsa FIRE, platinum DIGGING, glass CANCELLATION, uranium COLD, aluminum SLEEP.
- Rings: diamond fire res, iron prot. from shape changers, engagement REGENERATION, agate = base 150, twisted POLYMORPH CONTROL, clay SHOCK RES, opal SLOW DIGESTION, topaz GAIN CON.
- Amulets: spherical STRANGULATION, hexagonal REFLECTION. Armor: polished silver shield = SHIELD OF REFLECTION; faded pall = elven cloak.

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
| **25** | main | **THE CASTLE.** `<` (2,20) SW maze. Rust trap (4,20). My dug openings (6,15), (7,13). Courtyard x8-12 y10-14. DRAWBRIDGE DESTROYED T:20078; gateway (13,12)=ICE (refrozen T:20245; red naga fire melted it once; re-zap cold R if it is `}`), doorway (14,12). Antechamber x15-22, corridor y=12 x24-33, throne room x35-45 y9-15 (throne (44,12), royal chest (45,12)). **WISHING CHEST = SE TOWER (66,18)** (object detection T:20211). Trap doors (48..63,12). |
| Mines | Mines | Minetown = Mines 3 (DL6): temple of Odin (neutral), shops. Mines' End DL11. |
| Sokoban | | ALL SOLVED. |

## Threats / known dangers
- **Castle (wiki Castle.txt)**: up stairs in the small left maze; castle in the middle surrounded by a MOAT with 4 SHARKS + 4 GIANT EELS (stay 2+ squares from water; HELD = Elbereth doesn't work on... engrave anyway / kill it). Barracks on both sides of the entry hall (soldiers, sergeants, lieutenants, captains), 2 soldiers per corner tower, 8 soldiers + a lieutenant in the atrium. Throne room: 27 monsters from E H L M N O R T X Z (LICHES), chest behind the throne. Two random DRAGONS in each alcove between the storerooms. Floor undiggable (except trap-door squares); castle walls undiggable, maze walls diggable. No down stairs: the TRAP DOORS at the back (east) lead to the Valley. No teleport on the level. Mazes and some floors are unlit (and I have no light source now).
- **WAND OF WISHING**: locked (never trapped) chest in one of the 4 corner rooms, on a burnt Elbereth + scroll of scare monster, 2 soldiers each. Key d opens it (`unlock()` / `loot_all()`).
- Soldiers (@) ignore Elbereth; MR + reflection cover wand death rays; they hit hard in groups — fight in corridors/doorways; zap SLEEP (h) down a line of them.
- Fire elementals/fire breath destroy potions/scrolls. Quantum mechanics teleport (not on the Castle). Gelatinous cubes: force bolt from range.

## Objective and plan (after shift 22)
Castle geometry: screen x = mapx+8, y = mapy+4. Towers NW (12,6), NE (66,6), SW (12,18), **SE (66,18) = the chest**. Tower doors (15,7), (63,7), (15,17), **(63,17)**. Throne-room doors to the halls: (40,8) top, **(40,16) bottom (locked; key d / unlock())**. Halls y=7 / y=17.
1. Recover HP (97/145) in the corridor chokepoint (32,12)/(33,12): only (34,12) [door] and (31,12) can reach me. Finish eating the troll corpse or keep killing it when it revives. Kill the lieutenant plug when ready and fight the throne room one at a time at the door (hold loop: fight_until_clear radius 1 + unseen-I handling). Sleep wands h/s down row 12 when a queue forms.
2. Throne room: peaceful black naga (35,13) — leave it. Then unlock (40,16), hall east to (62,17), door (63,17), 2 tower soldiers, chest at (66,18): `loot_all()` (key d). Do NOT pick up the cursed scare monster scroll. Stand ON the chest square (scare monster: soldiers flee too).
3. Wishes (zap the wand; the harness pauses at the prompt; `cont --reply '...<CR>'`): 1) "2 blessed scrolls of remove curse" (uncurse the BAG before ever opening it, + the amulet) — or "2 blessed scrolls of charging" first if the wand shows (0:3)?: never engrave-test it. Then "2 blessed scrolls of charging" (recharge ONCE at 0 charges -> 3), blessed +2 speed boots, 2 blessed genocide (L, then ;), blessed amulet of life saving... (PLAYBOOK E). Write every wish in the journal.
4. Invisible LICHES are around (3 killed): their cold touch destroys potions even with cold res and they cast curse items. Hit an adjacent `I` at once (F-dir); keep potions bagged (after the bag is uncursed).
5. XL14 (80000) + piety for the quest (DL13 portal).
