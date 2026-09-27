# p2 — current state (rewrite as things change)

## Character
- Name/role: p2 — local practice game, seed 202 (lawful female dwarven Valkyrie, god: Tyr)
- Turn / Dlvl / XL / HP / Pw / AC: T:5880 / **Dlvl 11 (main dungeon, QUEST PORTAL LEVEL)** / XL8 (Exp 2013; XL9 at 2560) / 104/104 / 11/11 / **AC -3** (3 points of divine protection bought T:4517) / $0 on me, 201 gold in the sack n. Last meal: owlbear corpse finished T:5880 (not Hungry before ~T:6800).
- Position at shift-7 end (T:~5870): D11 at (54,4), the east doorway of the NE room (51-55,3-8), just finished eating an owlbear corpse, HP 104/104, nothing hostile in view (a wood nymph roams the far SE). The altar room (32-45,5-10) is 10 squares west. Arrived on D11 by FALLING through a hole I dug on D10 — D11's real `<` and `>` and the quest portal are NOT yet found (find them first next shift). NO PET.
- Attributes (T:3483): St:17 Dx:12 Co:19 In:11 Wi:8 Ch:9 (Cha 9 → shop buy prices ×4/3; carry cap 950)
- Skills: long sword SKILLED (enhanced T:3719); next #enhance when "more confident" appears
- Intrinsics (source, turn): cold res (Valk), stealth (Valk), infravision (dwarf), SPEED (XL7, T:4212); EXTRINSIC telepathy from the amulet of ESP (worn T:2424); Excalibur gives automatic searching. NO poison resistance (killer bees / soldier ants / spiders / snakes / quasits / spiked pits all carry a 1-in-240-per-hit instadeath).
- Luck notes: nothing done to Luck (no peacefuls killed by me).
- Alignment / god anger notes: never prayed; god not angry; prayer timeout has been 0 since ~T:300 (never used).

## Prayer log
| turn | reason | result |
|---|---|---|
| — | none yet. PLAN: the first prayer is reserved either for MAJOR trouble or for the HOLY-WATER prayer on the lawful altar D11 (44,6) with TWO potions of water on it (see plan) | — |

## Equipment worn/wielded (letter: item)
- a: EXCALIBUR — blessed rustproof **+6** (wielded; obtained T:2422; enchanted T:3612–3613). NEVER read another enchant weapon on it. NOTE: applying the pick-axe WIELDS the pick-axe — always `w`,`a` afterwards (done T:5818).
- c: uncursed +3 small shield (worn); DIVINE PROTECTION 3 points (AC -3 total)
- y: +0 scale mail (worn) [seen]; E: uncursed +0 high boots (worn) [seen]; O: uncursed AMULET OF ESP (worn) [seen]

## Key inventory (letters) — BUC [seen] from altars unless marked
- b: blessed +0 dagger (throw it; stepping onto it picks it back up); P: 12 BLESSED darts; U: 7 uncursed elven arrows (no bow); S: uncursed knife
- m: uncursed PICK-AXE — now carried LOOSE (top-level) since the D9/D10 digging; put it back in the bag s (`bag_put('s','m')`) before any shop. Dig down = `apply m`, `>`; first apply makes a pit, the second the hole; you land at a RANDOM spot of the level below.
- d: **CURSED MAGIC LAMP** — do NOT rub; needs 2 holy waters (cursed→uncursed→blessed), then #rub for the wish (80% with blessed)
- e: uncursed oil lamp; A: brass lantern; CANDLES: z + v + w(5) = 7 (for the Candelabrum — never burn them)
- n: uncursed SACK: holds 104 gold + scroll Q (ELBIB YLOH) + M (light) + D (blank) + cloth SPELLBOOK i (unread, BUC unknown) + potions I (magenta, base 100), N (murky, base 100), T (WHITE = PARALYSIS, unknown BUC), H (uncursed clear = plain WATER). Take out with `bag_take('n', pattern)`; put in with `bag_put('n', letter)`. Items inside are safe from fire/cold/theft.
- s: BAG = bag of holding or oilskin sack [inferred], currently EMPTY
- WANDS: x = SLEEP (curved, uncursed) [certain; 3–7 charges left]; **g = FIRE (jeweled, uncursed, identified T:5095; used 1 charge engraving)** — 6d6 ray, bounces, burns MY scrolls/potions/spellbooks if it hits me (bag them first), kills bee swarms in a line; also the sliming cure and a permanent-Elbereth engraver; V = LIGHT (pine, uncursed); r = SLOW MONSTER (balsa); o = CREATE MONSTER
- J: uncursed scroll of TELEPORTATION (top-level again) — ESCAPE ITEM
- L: uncursed GOLDEN potion (unknown); B: CURSED ring of shock resistance (never wear)
- q: NO FOOD RATIONS LEFT (last eaten T:4918–4925). f: uncursed tin (unknown; tin opener K). Last meals: giant ant corpse T:5204, jaguar corpse T:5470 → not Hungry before ~T:6300. EAT FRESH SAFE CORPSES (`corpse()`); buy/find rations.
- u: key (skeleton key), t: tin whistle
- Gems (all uncursed, unidentified): R black, X 2 black (other type), Y 2 red, Z yellow, W yellowish brown
- Escape items: scroll of teleportation J; wand of sleep x (and fire g); Elbereth (works: T:5814 the dust vortex and centaur fled while I dug); pick-axe (dig down: ~8 turns, random landing spot)
- Healing: none known. Emergency cures: none carried.

## Identified appearances (appearance -> identity)
- YUM YUM -> enchant weapon; ANDOVA BEGARIN -> identify; ELAM EBOW -> scare monster (lost); unlabeled -> blank paper; KO BATE -> light; DAIYEN FOOELS -> TELEPORTATION
- KERNOD WEL -> base 80 (enchant armor / remove curse); ELBIB YLOH -> base 100 group; HAPAX LEGOMENON -> base 100 group
- uranium wand -> create monster; curved wand -> SLEEP; balsa wand -> slow monster; **jeweled wand -> FIRE; pine wand -> LIGHT**
- silver ring -> regeneration; agate ring -> base 100 group; steel ring -> shock resistance
- puce potion -> base 150; murky potion -> base 100; magenta -> base 100; YELLOW -> SPEED; cyan -> GAIN LEVEL; clear -> water; **WHITE -> PARALYSIS** (a mountain centaur threw one at me T:5812: "Something seems to be holding you"); golden -> unknown
- hexagonal amulet -> ESP; oval amulet -> unchanging
- lamp (plain) -> magic lamp; oil lamp identified; "bag" -> sack identified (n); the other "bag" (s) = holding/oilskin
- vellum spellbook -> level 1; dull -> level 4; leathery -> level 3/4; cloth -> unknown (i, in the sack)

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1 | Dungeons | up (8,8); down (10,19); fountains (27,11), (5,18) |
| 2 | Dungeons | up (40,6); down (21,14) = GNOMISH MINES BRANCH; down (74,17) = main; Kittamagh's bookstore (2-5,17-19) door (6,18); fountain (59,16) |
| 3 | Dungeons | up (21,18) under a broken large box; down (51,10); SLEEPING GAS TRAP (35,8); vault |
| 4 | Dungeons | up (39,18); down (12,18) via hidden passage (8,15); FOUNTAIN (22,17); UPERNAVIK'S GENERAL STORE (69-71,15-17) door (68,16) |
| 5 | Dungeons (ORACLE) | up (9,5); down (58,5); Delphi fountains; PIT (14,15) |
| 3–6 (Mines) | Gnomish Mines | Mines 1 up (77,13) down (50,13); Mines 2 up (44,10) down (8,10); MINETOWN = Mines 3 (Dlvl 5): up (74,5), down (3,6), TEMPLE of ODIN (neutral) altar (38,9) priest (protection bought), shops: Kilmihil books (29-31,7-9), AlliWar hardware (29-31,15-17) with a disguised LARGE MIMIC (30,16), Pasawahan deli (36-38,16-17), Izchak lights (47-49,7-9), Ouiatchouane general (48-50,15-17); Mines 4 (Dlvl 6) up (45,5), `>` not found |
| 6 | Dungeons | up (23,15); **SOKOBAN `<` (4,15)** (skipped); `>` (41,3) NE room; leprechaun hall (20-25,4-7) cleared; fountain (7,6); 2 gold-carrying leprechauns roam |
| 7 | Dungeons | up (33,13); **`>` (64,16)** (SE, door (61,16)); NW room (11-24,3-5); N room (34-38,3-5); E room (44-53,7-9) doorway (54,9); SW room (5-12,17-19) with a BURNED ELBERETH at (10,19); SPIKED PIT (23,13); boulders (35,9), (30,8), (30,10), (24,11); arrows (31,18), mummy wrapping (35,16), axe/scimitar left; a peaceful tengu |
| 8 | Dungeons | up (48,4); **`>` (49,16)** in a small room (48-50,14-16) with a FOUNTAIN (50,15), door (49,13); hidden passage (42,5) W of the `<` room; rooms W/SW; locked doors (10,11), (20,16) are shortcuts only; east third unexplored |
| 9 | Dungeons | up (31,19) S room (29-41,16-19); **`>` (43,4)** small NW room (39-43,4-6) door (44,4); W room (14-20,13-17) doors (13,14) W, (18,12) N, (21,16) E, axe at (16,14); far-W room (2-6,13-16) door (7,15) with an ARROW TRAP (6,15) and MY HOLE at (4,15) (leads to a random D10 spot); NW room (4-13,3-7) tool at (7,4); NE room (20-34,3-7) tool at (24,7); a carnivorous ape wanders |
| 10 | Dungeons | **BIG ROOM** (irregular variant with wall fragments, trees, fountains (11,11), (65,11)); up (16,8); **`>` (4,16)** far W; loot seen: spellbooks (15,6), (20,11), scrolls (22,15), (26,10), (48,17), potion (29,17), food; **DANGER: a KILLER BEE HIVE (7+ bees) + giant spider + pyrolisk (fire gaze burns scrolls/potions at range) + mountain centaur (throws potions) + ghoul + beetles near the `<`** — never linger; bees are 12+ squares from the `>` |
| 11 | Dungeons (**QUEST PORTAL LEVEL**: "faint telepathic message from the Norn" on arrival) | **LAWFUL ALTAR (44,6)** in the N-centre room (32-45,5-10), statue of a hill orc (41,6) = my landing spot, doors (30,6) W closed, (46,8) E doorway, (39,10) S; boulder (48,9); `<` and `>` and the magic portal NOT found yet; a wood nymph (69,19) far SE (item thief — kill at range or avoid) |

## Pets
- NONE (the large cat stayed in Minetown, T:3800).

## Threats / known dangers
- **No poison resistance**: killer bees (D10 hive), soldier ants, giant spiders, snakes, quasits, spiked pits → each poisonous hit = 1/8 poison × 1/30 death. Fight them one at a time in corridors, with Elbereth, or the fire wand along a line; never a swarm in the open. Eating bee corpses costs Str without resistance (80%).
- Yellow lights: NEVER melee (explode → blind ~80 turns; happened T:5573). Pyrolisk: kill fast or break line of sight; bag burnables first.
- Mummies/zombies are mindless: telepathy does not show them. Gas spores too.
- Nymphs steal (also worn items); leprechauns steal gold (keep it in the sack).
- Cockatrices from D8: only Excalibur, never touch/eat corpses.
- Werejackals: fight in @ form/at range; "You feel feverish" → prayer.
- Mines' End luckstone only at XL10+.

## Objective and plan
- DONE shift 7: D6 → D7 → D8 → D9 → D10 (Big Room) → D11 (quest portal level) by T:5833. Wands of FIRE and LIGHT identified; white potion = paralysis; lawful altar found on D11 next to my landing spot.
- NEXT (shift 8):
  1. Find D11's `<` and `>` (escape route first). Kill the wood nymph at range if it approaches (thrown dagger b / sleep wand), never let it get adjacent.
  2. HOLY WATER PLAN: get a 2nd potion of water (dilute the white paralysis potion T twice in a fountain — D8 (50,15) or D10 (65,11)/(11,11) [bees!] or any D11/D12 fountain; each dip 1/30 water demon etc.), put both H + the new water ON the lawful altar (44,6), `prayer_check()` (no trouble → needs timeout 0 → it is 0 unless I pray before), then `pray()` standing on the altar → both become HOLY WATER → `#dip` the magic lamp d twice (cursed → uncursed → blessed) → `#rub` d for the WISH: "blessed +2 gray dragon scale mail" (magic resistance; swap the scale mail). Note the prayer resets the timeout (~350–1000 turns without an emergency prayer): do it at full HP in a cleared area.
  3. Food: no rations. Eat fresh safe corpses; consider the tin f. Buy rations if a shop appears.
  4. XL8 is low for D12+: farm XP carefully; the Sokoban prize is skipped; D12 next after D11 is mapped. The quest itself needs XL14.
- Emergency plan: HP < 40% → Elbereth (verified working) / upstairs / scroll J / sleep wand x (never toward an adjacent wall); prayer only for major trouble (`prayer_check()` first).

## Harness/helper calibration notes
- Verified this shift: `eat('q')`, `pickup(pattern)`, `bag_put`/`bag_take`, `go_down()` at single-`>` levels, `fight_until_clear()` (but see the yellow-light gap), `elbereth()` in a pit, `engrave_test()`, `travel()` resume via `cont`, `explore()` frontier/boulder/locked-door reports.
- GAPS: `fight()`/`fight_until_clear()` attacked an adjacent YELLOW LIGHT (blindness); falling through a hole makes the obs claim `up stairs (under you)`; the pick-axe direction prompt is classified as `object`; message text can leak into the monster list right after a level change; getobj re-prompts after "You don't have that object". Details in harness_notes.md (Shift 7).
- Earlier notes still valid: never call `inventory()`/`here()` unless `obs.kind == 'command'`; `travel()` never autopicks up; pick-one menus close on the letter alone; `obs.menu` lists only the current page.
