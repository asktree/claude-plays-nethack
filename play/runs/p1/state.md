# p1 — current state (rewrite as things change)

## Character
- Name/role: P1 the Woman-at-arms — lawful female dwarven Valkyrie, god: Tyr (seed 101, local practice game)
- Turn / Dlvl / XL / HP / Pw / AC: **T:18487 / DL21 (main dungeon), standing at (43,6) just inside the WEST doorway (42,7) of the DL21 throne room at shift-19 end** / **XL12** (Exp 34658; XL13 at 40000, XL14 at 80000) / **129/137** / 26/26 / **AC -11** (blessed +2 GRAY DRAGON SCALE MAIL + **+0 SHIELD OF REFLECTION** + orcish helm + elven cloak + blessed leather gloves + low boots + 4 points of divine protection). Wielding blessed rustproof **+6 EXCALIBUR** (long sword EXPERT; never enchant it again).
- **MAGIC RESISTANCE (GDSM) + REFLECTION (shield, formally identified T:18472 when a dragon's breath bounced off it).**
- **Rings worn: f prot. from shape changers (RIGHT), u SLOW DIGESTION (LEFT).**
- **Gold: $0 carried, ~$7659 in the bag** ($6044 + 1371 + 244). Next protection: 400 x XL = 4800 (XL12) / 5200 (XL13).
- Food: last meal rock troll T:16311; slow digestion worn, not hungry. Carried: J 2 food rations, B C-ration, O K-ration, y 6 royal jelly, X orange, Q pancake, j candy bar, U slime mold, F potion of fruit juice.
- Attributes: St 18/10, Dx 16, Co20 In10 Wi11 Ch7.
- Intrinsics: cold res, stealth, infravision, speed (XL7), POISON RES, FIRE RES, TELEPATHY (blind only), MAGIC RESISTANCE (GDSM), REFLECTION (shield). Excalibur: auto-search, drain res. NO sleep res (reflection covers sleep RAYS), NO shock res (ring in the bag).
- Luck >= 0 (the prayer at T:18211 succeeded). Gray stone v is uncursed (luckstone or not). Alignment record high; no peacefuls killed.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:1271 | welded cursed dagger (MINOR — mistake) | accepted, trouble NOT fixed |
| T:2016 | lycanthropy (MAJOR) | CURED |
| T:3401 | Weak from hunger (MAJOR) | fixed |
| **T:18211** | **no trouble, timeout 0, on the DL15 co-aligned altar with plain water on it** | **"Tyr is well-pleased"; the water became HOLY WATER** |
- **The lamp wish at T:18215 added 50-149 on top of rnz(350) from T:18211. DO NOT PRAY before ~T:19300 unless dying (prayer_check() said 14% at T:18487).** Emergency healing: t blessed FULL HEALING, swirly HEALING (bag), Elbereth, stairs, teleport wands G/Z + 6 teleport scrolls k.
- **Stoning cure: S = uncursed LIZARD CORPSE** (prayer is not available now).

## Equipment worn/wielded
- a: blessed rustproof +6 EXCALIBUR (wielded). **b: +0 SHIELD OF REFLECTION (wished T:18215, blessed per the wish; came out +0)**. x: blessed +2 GDSM (MR). n: uncursed +0 orcish helm. V: uncursed +0 elven cloak. r: blessed +0 leather gloves. z: uncursed +0 low boots. Rings f (right) + u (left). H: uncursed elven dagger (quivered — throw at floating eyes).

## Key inventory (T:18487, 44 letters, limit 52)
- **l: uncursed BLINDFOLD** (altar-tested T:18207) — safe to wear (P / R).
- **e: glass wand = WAND OF CANCELLATION (named "cancellation")**: engrave "vanishes" + a zapped little dog stayed visible (make invisible can't be resisted). **NEVER put it in the bag of holding** (explodes the bag). Never zap it at yourself.
- A: uncursed UNICORN HORN. S: uncursed LIZARD CORPSE. t: BLESSED POTION OF FULL HEALING.
- m: blessed (oil) lamp — the former magic lamp, djinni used. Light source.
- Escapes: **G and Z = WAND OF TELEPORTATION** (Z 2 charges used of 4-8). **g = WAND OF DIGGING** (zap `>` = hole down). **k: 6 scrolls of teleportation.** Elbereth. Stairs.
- o: WAND OF FIRE. E: wand of lightning (0:3). Wands of striking C, Y (force bolt: breaks statues/boulders; DESTROYS a drawbridge).
- T: uncursed MAGIC MARKER (0:22). q: 5 uncursed unlabeled scrolls (blanks). Write only KNOWN types (remove curse via its label `write_scroll('XOR OTA')`).
- p: scroll of ENCHANT WEAPON (not for Excalibur). s: scroll of FIRE.
- Potions: i 2 black (= probably object detection), N murky (unknown, uncursed), F fruit juice, P uncursed SPEED, h cursed SPEED.
- v: uncursed gray stone (flint/touchstone/luckstone; not a loadstone). d: KEY.
- **D: bag of holding ("BoH prize")**: ~$7659 gold, **the PICK-AXE is inside (`bag_take("D","pick-axe")` before digging)**, scroll ELAM EBOW, 2 scrolls of fire, scroll of light, scroll of create monster, yellow spellbook, potions: swirly HEALING, booze, sky blue CONFUSION, 2 MONSTER DETECTION; wand of lightning (0:2), wand of CREATE MONSTER, can of grease, blessed oil lamp; rings REGENERATION, POLYMORPH CONTROL, SHOCK RESISTANCE, bronze (blessed, base 100), ivory (100), wire (100), coral (150); gems.
- `bag_take('D', 'gold')` now takes coins only.

## Identified appearances
- Scrolls: ZELGO MER identify, EIRIS SAZUN IDISI amnesia, GARVEN DEH light, HACKEM MUCHE fire, TEMOV teleportation, FOOBIE BLETCH enchant weapon, KERNOD WEL scare monster, THARR create monster, ZLORFIK gold detection, **XOR OTA = REMOVE CURSE** (named). NR 9 (200) = earth or taming. ELAM EBOW, DUAM XNAHT (100) unknown (confuse monster / destroy armor / food detection / magic mapping).
- Potions: yellow sickness, brilliant blue blindness, cyan oil, pink GAIN LEVEL, swirly HEALING, golden SPEED, ruby FULL HEALING, dark MONSTER DETECTION, orange BOOZE, sky blue CONFUSION, **dark green FRUIT JUICE**, clear WATER; black probably object detection; murky unknown.
- Wands: marble lightning, iridium striking, oak magic missile, crystal speed monster, short TELEPORTATION, zinc nothing, ebony CREATE MONSTER, balsa FIRE, platinum DIGGING, **glass = CANCELLATION (named)**.
- Rings: diamond fire res, iron prot. from shape changers, engagement REGENERATION, agate = base 150, twisted POLYMORPH CONTROL, clay SHOCK RES, opal SLOW DIGESTION, topaz GAIN CON.
- Amulets: spherical = STRANGULATION. Tools: magic lamp (formally identified). Armor: **polished silver shield = SHIELD OF REFLECTION**; etched helmet (one of helmet/brilliance/opp. alignment/telepathy); faded pall = elven cloak.

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1 | main | `<` (76,4). `>` (54,7). SINK (55,6). |
| 2 | main | `<` (46,16). `>` (48,7). FOUNTAIN (25,6). TRAP DOOR (71,8). |
| 3 | main + Mines | `<` (19,9). General store NW. Main `>` (29,16); MINES `>` (46,18). |
| 4 | main | `<` (5,9), `>` (20,14). Sleeping gas trap (58,15). |
| 5 | main | `<` (59,16). `>` (70,16). |
| 6 | main | ORACLE. `<` (9,7). `>` (65,10). Fountains. Gray unicorn killed T:17569 (its horn left at ~(27,6)). |
| 7 | main (Sokoban up) | `<` (5,7). `>` (13,8). Sokoban `<` (14,15) under the hill-orc statue. Magic trap (18,15). |
| 8 | main | `<` (7,8). `>` (47,8). |
| 9 | main | `<` (64,5). `>` (72,13). |
| 10 | main | `<` (19,7). NEUTRAL ALTAR (16,7). **`>` (4,10) (under a lizard statue)**. |
| 11 | main | `<` (18,5), `>` (10,14). |
| 12 | main | `<` (9,16), `>` (11,5) (door (11,6) below it). Peaceful gnomish wizard. |
| **13** | main | **QUEST PORTAL (73,17)**. `<` (34,16), `>` (6,13). YELLOW LIGHT still alive (drifted east of the `<`, last (44,16) T:18127) — strike it when adjacent. Anti-magic field (47,4). |
| 14 | main | `<` (54,5), `>` (35,7). Closed VAULT (75-76,17-18). Peaceful WHITE unicorn (co-aligned: throw it gems for Luck). |
| **15** | main | `<` (11,4). `>` (58,5). **LAWFUL ALTAR to Tyr (48,19)** (blessed etched helmet + my old +3 small shield left on it). Teleport trap (35,18). Peaceful fire giant. |
| 16 | main | `<` (8,17); `>` (3,7). Yellow mold (2,5). Cursed amulet of strangulation (4,7). |
| 17 | main | `<` (30,15), `>` (71,16) (peaceful ALEAX there; squeaky board (70,17)). Fountain (64,4). |
| **18** | main | **ROGUE LEVEL — FULLY EXPLORED (T:16928)**: `<` (37,4), `>` (16,2). Rooms NW, N-mid, W-mid, centre (32-41,9-13, pit (35,12)), S-mid (26-50,18-21), SE (57-71,16-21). Rogue ghost pile at (38,10): FAKE Amulet of Yendor, ring mail, bow, arrows, two-handed sword, food ration. Chain mail (27,19). No reflection here. |
| 19 | main | `<` (45,17), `>` (34,19). FULLY EXPLORED. Trap door (64,7). |
| 20 | main | `<` (49,17), `>` (39,10). Graveyard cleared. Teleport traps (59,4), (21,5); POLYMORPH TRAP (9,16). Heard a VAULT. NOT Medusa. |
| **21** | main | NOT Medusa. `<` (7,6) (chest (8,5) looted), `>` (11,17), fountain (27,5). Floating eye ~(29,16). **THRONE ROOM (43-5x,4-7), throne (48,7)**: half cleared (see plan); leprechaun ~(70,7). |
| Mines 1-2 | Mines | DL4 `<` (6,20) `>` (27,6); DL5 `<` (25,5) `>` (16,10). |
| Minetown | Mines 3 = DL6 | GROTTO TOWN. `<` (3,2), `>` (48,4). Temple of ODIN (neutral) altar (33,4) — never pray there. Hardware store (59-62,14-16): large box, tin opener, leash, bag. General store (61-69,10-11): 2 oil. Black unicorn roams (hostile). |
| Mines' End | DL11 | LUCKSTONE in a SW closet (3,17)/(3,19). |
| Sokoban | | ALL SOLVED. |

## Threats / known dangers
- **DL21 throne room, where I stand**: STILL ASLEEP (stealth keeps them so): fire giant (50,5), WHITE DRAGON (52,6), 2 orc shamans, ~6 bugbears, ~6 hobgoblins, maybe more east of x=52. AWAKE: a wounded GREEN DRAGON (hit 2x; hit-and-run, breathes poison = harmless to me: poison res + reflection; it fled west through the doorway (42,7) into the corridor and carries the wand of magic missile it picked up at (44,5)). The poison-gas clouds in the room blind me 1 turn per turn inside them (telepathy then shows everything).
- Booby-trapped doors fire on opening as well as on unlocking. Nymphs/monkeys/leprechauns: drop D and A first / bag the gold.
- Fire gazes/breath burn scrolls/potions: bag the important ones. Demons gate demons.
- Quantum mechanics teleport (MR doesn't stop it). Yellow lights: strike when adjacent, or wear the blindfold.

## Objective and plan (after shift 19)
1. **Finish the DL21 court** (stealth sweep, one sleeper at a time; fight() adjacent ones directly — hunt() refuses while ANOTHER hostile is adjacent). Kill the white dragon while it sleeps; kill the green dragon when it comes back (it will; it's slower than me). Then loot the court (royal chest? gold), consider sitting on the throne (48,7) (bag gold first, full HP; ~1/3 sits have an effect, 1/13 of those a wish).
2. **Medusa / Castle route (recorded plan):** Medusa is on DL22-24 (DL21 isn't). With reflection, her gaze kills HER; the harness now lets travel run there (reflection known). Water crossing, in order of preference:
   a. **Dig down** on Medusa's level near the arrival `<` (every variant has a diggable floor; stay 2+ squares from water: eels) with wand g or the pick-axe -> land in the Castle's WEST region (where the Castle `<` is) -> climb the Castle `<` -> arrive on Medusa's `>` in her hall, next to her: reflection turns her to stone on her first gaze (don't be blindfolded for that). Then break **PERSEUS'S STATUE** there with a force bolt (C/Y) or the pick-axe: 25% LEVITATION BOOTS (+0), 75% cursed +0 shield of reflection (do NOT wear), 50% blessed +2 scimitar, 50% sack.
   b. The CASTLE MOAT then needs one of: levitation/water walking (boots from Perseus?), a wand of cold/frost horn (freeze the drawbridge square, then force-bolt the drawbridge from a distance -> ice/floor + open doorway), ONE BOULDER or a scroll of EARTH (a boulder in the raised drawbridge's moat square makes floor under it; then force-bolt the drawbridge: it collapses onto floor and leaves a doorway), or the passtune (2 lucky prayers, or Mastermind with any tonal instrument: flute/horn/bugle/harp; sergeants carry bugles). NR 9 scrolls (earth or taming) are worth read-testing when found; once earth is known the marker can write it cheaply.
   c. Never stand on the drawbridge or the portcullis square when it is destroyed/opened/closed (crushing = death).
3. XP toward XL13/14 (quest portal DL13 (73,17) needs XL14; `piety()` needs a stethoscope). Keep the magic marker charges (22) for a scroll of scare monster / remove curse / earth.
