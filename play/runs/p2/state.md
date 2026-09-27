# p2 — current state (rewrite as things change)

## Character
- Name/role: p2 — local practice game, seed 202 (lawful female dwarven Valkyrie, god: Tyr)
- Turn / Dlvl / XL / HP / Pw / AC: **T:16573 / D28 = THE CASTLE, standing ON THE WAND-OF-WISHING SQUARE (66,18) in the SE TOWER (x64-68, y17-18): cursed scroll of SCARE MONSTER on the floor (NEVER pick it up) + burned Elbereth = no melee from anything except minions/Riders/shk/priests** / **XL12** (Exp 39110) / **139/139** / 19/19 / **AC -8** / $0 loose + ~5200 gold in BAG OF HOLDING s.
- **NOT BLIND now** (towel T removed T:16550). Put it on again (P T) for gazes/light explosions or a telepathy census.
- **WAND OF WISHING U: recharged ONCE (T:16566, "glows blue" = 3) → 1 used since → 2 CHARGES LEFT. NEVER RECHARGE IT AGAIN (explodes).** Spare BLESSED SCROLL OF CHARGING in bag s (for another wand: fire or sleep).
- **WISHES (T:16551-16568, all from the wand)**: 1) "blessed +2 gray dragon scale mail" → d, came out **+0** (20% rule: objnam.c `spe > rnd(5)` resets +2 to +0). 2) "2 blessed scrolls of charging" → m (one read on U, one in bag s). 3) "blessed amulet of life saving" → n (octagonal amulet = LIFE SAVING, worn). 4) "blessed +2 speed boots" → o (riding boots = SPEED BOOTS, came out **+0**, worn: Very fast).
- **NOW: MAGIC RESISTANCE (GDSM) + REFLECTION (shield W) + LIFE SAVING (amulet n) + VERY FAST.**
- FIRE WANDS: g, y, N EMPTY; l unknown (used 3x); **M = new wand of fire (from the red dragon's pile, charges unknown)**. SLEEP: x (4 used, 0-4 left), **J (soldier's, 3 zapped this shift: T:16234, 16243, 16470)**. STRIKING: q probably empty, **S EMPTY ("Nothing happens" T:16453)**. **z, A = 2 ALUMINUM wands (soldiers', unknown: magic missile/cold/lightning/death/digging/...; engrave-test when safe)**.
- FOOD: bag i: 4 food rations, 5 tripe, 2 tins, C-ration. Carried: t 2 C-rations, v 1 K-ration, p slime mold, G 2 garlic, **X = 2 LIZARD CORPSES**. Ate a K-ration T:16403 (Hungry).
- Attributes: St 18/xx, Dx 13, Co 19, In 11, Wi 10, Ch 9. Long sword EXPERT.
- Intrinsics: cold res, stealth, infravision, speed (+ speed boots = VERY FAST), telepathy (intrinsic; amulet of ESP O now NOT worn), POISON RES, SEE INVISIBLE (ring B). Excalibur: drain res + autosearch. REFLECTION, **MAGIC RESISTANCE**. No fire/sleep/shock res.
- Luck: 0. Alignment: many kills, no hypocrisy this shift.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:6107–6110 | no-trouble prayer on the D11 altar with 2 waters | SUCCESS, 2 holy water |
| T:10649 | holy-water prayer on the D11 altar | SUCCESS, 2 HOLY WATER |
- No prayer since. **4 WISHES T:16551-16568 added 200-596 to the timeout → prayer UNRELIABLE until ~T:17000-17200** (prayer_check() tracks it). Life saving is the backstop now.

## Equipment worn/wielded
- a: EXCALIBUR blessed rustproof +6 (wielded). NEVER enchant again.
- d: +0 GRAY DRAGON SCALE MAIL (MR; BUC not shown, wished blessed); H +0 faded pall (uncursed, removable); E +0 elven leather helm; Y +0 leather gloves; o +0 SPEED BOOTS; **W: +0 shield of reflection (CURSED per medusa.des — can't be removed)**; n AMULET OF LIFE SAVING; B ring of see invisible.
- Dropped on (66,18): the uncursed +0 elven mithril-coat (uncursed with holy water T:16554) and the thoroughly rusty +3 iron shoes.

## Key inventory (letters)
- **TWO BAGS OF HOLDING: i and s. NEVER put one into the other.**
- U WAND OF WISHING (2 charges, recharged once). j: 1 HOLY WATER (blessed potion called water) left in the main pack. c extra healing, k healing, f blindness. Z scroll of earth. T towel. L unicorn horn. u key. O amulet of ESP (spare).
- THROWING: e blessed dagger, C, D, F elven dagger (quivered); P 11 blessed darts.
- WANDS: R oak (cursed; teleportation by use); fire g/y/N empty, l ?, M ?; sleep x, J; striking q (empty?), S EMPTY; slow monster r; light V; h hexagonal (nodir, = secret door detection?); Q long (directional, no visible effect); z, A aluminum (unknown).
- **BAG s**: ~5200 gold, 1 BLESSED SCROLL OF CHARGING, pick-axe, water (BUC ?), black potion, object detection, 4 teleportation scrolls (3 uncursed + 1 ?), READ ME, create monster, 2 blank, gems.
- **BAG i**: cursed rings (copper T, agate, teleportation), wands make invisible / undead turning / slow monster, candles, whistle, object detection, gems, food, lantern, oil lamp, grease.

## Identified appearances
- Scrolls: YUM YUM enchant weapon; ANDOVA BEGARIN identify; ELAM EBOW scare monster; KO BATE light; DAIYEN FOOELS teleportation; KERNOD WEL base 80; ELBIB YLOH destroy armor; ETAOIN SHRDLU earth; KIRJE create monster; FOOBIE BLETCH food detection; STRC PRST SKRZ KRK charging; VERR YED HORRE confuse monster; HAPAX LEGOMENON magic mapping; READ ME unknown.
- Wands: uranium create monster; ebony striking; curved sleep; balsa slow monster; jeweled fire; pine light; iron make invisible; forked undead turning; oak = teleportation (by use).
- Rings: silver regeneration; steel shock res; twisted teleportation; bronze see invisible; sapphire aggravate monster; agate base 100; copper, iron unknown.
- Potions: magenta healing; yellow speed; cyan gain level; clear water; white paralysis; effervescent full healing; golden object detection; emerald sleeping; puce blindness; murky extra healing; purple-red oil; fizzy polymorph; dark green invisibility; milky sickness; black unknown.
- Amulets: hexagonal ESP; oval unchanging; **OCTAGONAL = LIFE SAVING (wished)**.
- Boots: **RIDING BOOTS = SPEED BOOTS (wished)**. Wands: aluminum = unknown (2 carried, z A). Faded pall = elven cloak. **Polished silver shield = shield of reflection.**

## Dungeon map
| Dlvl | features |
|---|---|
| 1–5 | D2 Mines branch; D4 general store; D5 Oracle. Minetown (Mines 5) temple of Odin |
| 6–10 | D6 Sokoban (ALL SOLVED); D10 Big Room |
| 11 | lawful altar (44,6); quest portal level (portal not found; XL14 + piously) |
| 12–19 | D12 weapon shop; D13 altar (17,18); D14 `<` (17,7) `>` (30,6) altar (49,6); D15 barracks (avoid); D16 Rogue; D17 `<`(13,15) `>`(25,18); D18 `<`(50,15) `>`(45,5); D19 `<`(31,6) `>`(68,6) |
| 20 | `<` (46,9) `>` (12,19); trap door (27,4) |
| 21 | `<` (49,15) `>` (7,15) |
| 22 | `<` (3,18) `>` (76,4); trap door (32,21) |
| 23 | `<` (25,5) (hidden door (24,4)); rest unexplored; trapper near (39,17). My hole at (25,6). |
| 24 | **CO-ALIGNED TEMPLE OF TYR, altar (28,10), priestess** (room x25-31 y9-11). `>` (58,8). Fountain (51,16). **Protection: 400*XL = 4800 at XL12 — I have 4924: BUY IT when back up here.** |
| 25 | `<` (55,19); dug down at (56,19) |
| 26 | landed (69,17), dark room; dug down there |
| **27** | **MEDUSA (medusa-4; screen = map + (2,1)). Medusa DEAD T:15501 (mirror); her statue (13,8). `>` (12,9) in her room x11-13 y8-10 (doors (12,7) N locked, (14,9) E locked, (12,11) S OPEN; iron bars (10,9)). South room x11-13 y12-14 (door (10,13) W closed; bars (14,14)) — Perseus statue broken there: scimitar + 46 rocks left. `<` (75,9) FAR EAST across water. Kraken in the inner water x8-9 (y8-10); sleeping YELLOW DRAGON + 2 babies outside the north room (~(6-7,5-6)); giant spider roaming outside east; black nagas (peaceful adults), pythons (drown from water), eels.** The north room (12,5) and west room (6,9) unexplored. |
| **28** | **THE CASTLE** (magic-mapped). `<` (4,10) in the west maze (2 open neighbours: (3,10), (4,9)); courtyard x8-12 y10-14 (exit to the maze only at (7,14)); DRAWBRIDGE DESTROYED T:15542 (span (13,12) + eel squares (13,11)/(13,13) filled with earth boulders = floor); fountain (18,12); throne (44,12); trap doors (48..63,12); **wand of wishing TAKEN T:16550 from the SE tower chest (66,18)** (scare monster scroll + burned Elbereth still there; my mithril + iron shoes dropped there). Doors: (40,16) unlocked+open, (63,17) open, (34,12)/(23,12) open. Burned-Elbereth FORT at (11,12) (west courtyard). Scroll `?` at (4,12) in the maze (unknown). |

## Threats
- **Castle status T:16573**: DEAD this shift: green dragon, RED DRAGON, PURPLE WORM (from inside), lich #1 (destroyed), CAPTAIN (slept, then killed), ogre king, gargoyle, cockatrice, red naga, hostile golden naga, rust monster, ogre, xorn, ROCK TROLL (x2 — it revives), ICE TROLL, troll, 3 sergeants, ~10 soldiers, 4 unseen mindless things ("destroy" = zombies/mummies). The barracks and the throne room are EMPTY (troll corpses there may revive).
- Still alive: lich #2 (was in the west corridor (25,12) T:16508, slow), soldiers in the north hall (~5, row 7) and the SW tower/south-hall west end (~3), 2 white + silver + BLACK dragon in the x55 storeroom alcoves (black = disintegration: reflection handles it), Olog-hai + titanothere + lizard in the east yard (x65-70, y9-15, outside the tower), storm giant, disenchanter, xorn, leocrotta, lurker above x2, rock piercers (west courtyard/maze), eels/sharks in every moat. Peaceful: 2 titans, golden naga, tengu.
- Elbereth ignorers: @ soldiers, minotaurs, lawful minions, shk/guards/priests, blinded monsters. Scare monster (the tower square) ignores only minions/Angels/Riders/shk-in-shop/priest-in-temple/the Wizard.
- EEL WATER: never stand next to the moat. hunt() does NOT avoid water squares (walked me to (13,11) next to an eel, T:16426) — use travel()/step() near the moat.
- Prayer unreliable until ~T:17000-17200 (4 wishes). Life saving worn.

## Plan (next shift)
- START: `bin/nh obs`; I'm on the SE-tower wishing square (66,18) = safest square on the level. HP full.
- **2 WISHES LEFT on U (never recharge again).** Suggested: "blessed ring of levitation" (cross Medusa's water to go UP: D24 temple of Tyr — buy protection 400*XL = 4800 at XL12, I have ~5200; quest portal D11-16 at XL14) and "2 blessed scrolls of genocide" (L then ;) or "blessed gauntlets of power". Ask +1 on armor if a sure bonus matters (+2 has a 20% chance to come out +0, twice this shift).
- Use the spare BLESSED CHARGING (bag s) on the new fire wand M after engrave-testing it, or on sleep J.
- Engrave-test z/A (aluminum) off the Elbereth square when no monsters are near.
- Then: Castle trap doors (48..63,12; reached from the throne room through the secret door (46,12) — search there) → the Valley (Gehennom: MR + reflection + life saving now; no prayer there). Or go up first for protection/quest with levitation.
- Leaving the tower: south hall (row 17) west → door (40,16) (open) → throne room. Soldiers may come down the hall one at a time: fight them in the 1-wide hall.
