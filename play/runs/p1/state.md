# p1 — current state (rewrite as things change)

## Character
- Name/role: P1 the Skirmisher — lawful female dwarven Valkyrie, god: Tyr (seed 101, local practice game)
- Turn / Dlvl / XL / HP / Pw / AC: **T:13743 / DL16 (main dungeon), standing ON THE DL16 `<` (8,17) at shift-14 end** / **XL12** (Exp 22933; XL13 at 40000, XL14 at 80000) / **137/137** / 26/26 / **AC -12** (blessed +2 GRAY DRAGON SCALE MAIL + +3 small shield + orcish helm + elven cloak + blessed leather gloves + low boots + 3 points of divine protection). Wielding blessed rustproof **+6 EXCALIBUR** (long sword EXPERT; never enchant it again). Ring worn: f prot. from shape changers (right). Left hand FREE. $4416.
- Food: ate a FIRE GIANT corpse at T:13658 (750 nutrition; "You feel very strong!"). Carried: e food ration, B C-ration, O K-ration, X orange, Q pancake, j candy bar, U slime mold, g partly eaten ROTTEN ration (every bite re-rolls Blecch). ~2000 nutrition. Keep eating fresh SAFE corpses (`corpse()`).
- Attributes: St 18/xx (giant corpse), Dx14+ Co20 In10 Wi11 Ch7.
- Intrinsics: cold res (Valk), stealth (Valk), infravision (dwarf), speed (XL7), POISON RES, FIRE RES, **TELEPATHY (floating eye corpse T:13484)**. **MAGIC RESISTANCE (GDSM)** — blocks death rays too. Excalibur: auto-search, drain res. NO sleep resistance, NO shock resistance, NO reflection.
- Luck 0 (no luckstone); alignment record high; no peacefuls killed.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:1271 | welded cursed orcish dagger (MINOR trouble — mistake) | accepted, trouble NOT fixed, timeout reset |
| T:2016 | lycanthropy (MAJOR) | "well-pleased ... You feel purified" CURED |
| T:3401 | Weak from hunger (MAJOR; prayer_check 98%) | "well-pleased. Your stomach feels content." |
- The wish (T:10728) added 50-149; **the prayer timeout has certainly been 0 since ~T:10880**. Prayer available for major trouble (HP <= 22 at 137 max, XL12: max/6). Stoning cure = prayer (no lizard).

## Equipment worn/wielded
- a: blessed rustproof +6 EXCALIBUR (wielded). c: uncursed +3 small shield. x: blessed +2 GRAY DRAGON SCALE MAIL (MR). n: uncursed +0 orcish helm. V: uncursed +0 faded pall = ELVEN CLOAK. r: blessed +0 leather gloves. z: uncursed +0 low boots. Ring f (prot. from shape changers, right).

## Key inventory (letters — several reassigned in shift 14)
- **A: uncursed UNICORN HORN** (stun from the booby trap took 3 applies this shift).
- **T: uncursed MAGIC MARKER (0:35)** + **q: 2 uncursed BLANK scrolls** (from the zoo). Write only KNOWN types: identify, enchant weapon, light, fire, amnesia, teleportation, scare monster, create monster, gold detection, **REMOVE CURSE — write it BY LABEL: `write_scroll('XOR OTA')`**. Plan: keep 1 blank for remove curse; the other for identify/scare monster when needed.
- **Escapes: G and Z = WAND OF TELEPORTATION** (Z 2 charges used of 4-8, G unknown). **k: 3 uncursed scrolls of teleportation.** Elbereth. Stairs. Prayer.
- **E: wand of lightning (0:3)** (only along a line whose first wall is >= 7 squares away, or where monsters absorb the range). **S: wand of striking** (killed the floating eye). **p: wand of CREATE MONSTER** (uncursed; sacrifice fodder at an altar). H: uncursed elven dagger (throwing).
- **D: uncursed BAG OF HOLDING ("BoH prize")**, 17 items: scroll ELAM EBOW (uncursed, unknown), 2 scrolls of FIRE (sliming cure), yellow spellbook, SWIRLY potion = HEALING, wand of lightning (0:2), wand of striking, AND (shift 14) the unknown rings **twisted (base 300: conflict/polymorph/poly control/teleport control — NEVER wear-test)**, bronze (blessed, 100), ivory (100), wire (100), coral (150), clay, opal, and the gems (black, 2 green, 2 orange, 3 red). **Pick-axe b is in the MAIN PACK** (`bag_put('D','b')` before any shop).
- s: uncursed scroll of FIRE (main pack). l: uncursed scroll of LIGHT (blank source).
- Potions: **P uncursed + u CURSED = SPEED** (a vampire drank one: "suddenly moving faster"; game-identified). **t BLESSED ruby** (unknown). w dark (unknown BUC, chest). i black (= probably object detection), F dark green, N murky (uncursed, unknown). No water.
- K: ring of REGENERATION (not worn). Tools: d uncursed KEY, W blessed oil lamp (LOW), v can of grease, b pick-axe.
- NO lizard corpse (stoning cure = prayer only), no holy water.

## Identified appearances
- Scrolls: ZELGO MER identify, EIRIS SAZUN IDISI amnesia, GARVEN DEH light, HACKEM MUCHE fire, TEMOV teleportation, FOOBIE BLETCH enchant weapon, KERNOD WEL scare monster, THARR create monster, ZLORFIK gold detection, **XOR OTA = REMOVE CURSE** (named). NR 9 (200) = earth or taming. ELAM EBOW, DUAM XNAHT (100) unknown.
- Potions: yellow sickness, brilliant blue blindness, cyan oil, pink gain level, swirly HEALING, **golden SPEED**, sky blue = confusion or booze; black probably object detection; dark green, murky, ruby, dark unknown.
- Wands: marble lightning, iridium striking, oak magic missile, crystal speed monster, short TELEPORTATION, zinc nothing, **ebony CREATE MONSTER**.
- Rings: diamond fire resistance, iron protection from shape changers, engagement REGENERATION, agate = base 150.
- Armor: **etched helmet = one of helmet/brilliance/opposite alignment/telepathy** (a blessed one left on the DL15 altar: no upgrade possible for me, 1/4 opposite alignment).
- Tools: "bag" = sack, BoH is D; "lamp" base 50 = magic lamp.

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1 | main | `<` (76,4). `>` (54,7). SINK (55,6). |
| 2 | main | `<` (46,16). `>` (48,7). FOUNTAIN (25,6). TRAP DOOR (71,8) = shaft to DL5. |
| 3 | main + Mines branch | `<` (19,9). General store NW (3-7,5-8). Main `>` (29,16); MINES `>` (46,18). |
| 4 | main | `>` (20,14); hidden door (17,14) -> W room with `<` (5,9). Sleeping gas trap (58,15). |
| 5 | main | `<` (59,16). `>` (70,16). |
| 6 | main | ORACLE. `<` (9,7). `>` (65,10). Fountains (38,12) (39,11) (39,13) (40,12). |
| 7 | main (Sokoban up) | `<` (5,7). `>` (13,8). Sokoban `<` (14,15) under the hill-orc statue. |
| 8 | main | `<` (7,8). `>` (47,8). Fountains (42,8) and (48,16). SINK (22,3). Pit (7,11). |
| 9 | main | `<` (64,5). `>` (72,13) in a closet behind door (71,12). |
| 10 | main | `<` (19,7). NEUTRAL ALTAR (Odin) (16,7). `>` NOT FOUND; dug down from (39,16). Green mold (43,13). |
| 11 | main | `<` (18,5), `>` (10,14). |
| 12 | main | `<` (9,16), `>` (11,5). Mountain nymph with a wand of teleportation roams it. |
| **13** | main | **QUEST PORTAL: MAGIC PORTAL at (73,17) in the SE room** (not entered). `<` (34,16), `>` (6,13). Rolling boulder trap (17,13), anti-magic field (47,4), pit (51,19). |
| 14 | main | `<` (54,5), `>` (35,7). Closed VAULT at (75-76,17-18) (not dug). |
| **15** | main | `<` (11,4). **`>` (58,5)** (room 58-65,4-6; reached via hidden door (57,6)). **LAWFUL ALTAR to Tyr (48,19)** (SE room; grave (48,18); a blessed etched helmet left on the altar). **ZOO (71-76,16-19) CLEARED** (door (70,17)); corpses/junk armor left there, plus my dropped cyan+pink spellbooks, tin opener and spare ring of fire resistance at (71,19). Fire giant corpse + boulder (18,20) in the SW corridor. Teleport trap (35,18). Chest (2,16) looted (empty now). Booby-trapped door (45,7) gone. |
| **16** | main | **arrived `<` (8,17)** in a closet room (5-8,15-17) with two LOCKED doors: east (9,17) UNLOCKED at T:13743 (not opened yet), west (4,15) still locked. Nothing else explored. |
| Mines 1-8 | Mines | Minetown = Mines 3 (DL6): temple of Odin (neutral) (33,4), general store, hardware store; `>` (48,4) behind door (52,7). Mines' End (DL11): LUCKSTONE still in a SW closet (3,17)/(3,19). |
| Sokoban | Sokoban | ALL SOLVED, prize (BoH) taken. |

## Threats / known dangers
- Booby-trapped doors: 2 exploded on me (DL14, DL15): KABOOM wakes everything within ~15 squares and stuns (horn: 1-3 applies). The trap fires on UNLOCKING; if unlock succeeds quietly, opening is safe.
- Fire gazes/breath burn scrolls and boil potions even with fire resistance: kill fast; important scrolls/potions in the BoH.
- Incubi/succubi: armor removal (cloak THEN body armor in the same seduction). Kill at a chokepoint.
- Cockatrices/chickatrices: melee only with Excalibur; gloves now worn (can handle their corpses carefully); no lizard — prayer is the stoning cure.
- Soldiers/wand users: MR blocks death rays; sleep rays are NOT blocked (no sleep res) — avoid lines at range.
- No shock resistance: energy vortices / lightning bounces hurt and can destroy wands/rings.

## Depth decision (shift 14)
- Continue DL16-18 now: AC-12, MR, telepathy, fire/cold/poison res, speed, stealth, Excalibur +6, 137 HP, prayer available — the (DL+XL)/2 monster band (~14) is well inside what I handle. **Stop before Medusa (~DL21-24)**: no reflection, no levitation/water crossing, no blindfold/towel. Stealth + zoos: sleeping monsters stay asleep; kill them one at a time.

## Objective and plan (after shift 14)
1. DL16: open the east door (9,17) (unlocked) and explore; find `>`. Arrive/leave at full HP.
2. XP toward XL14 (quest portal DL13 (73,17)): wraith corpses (+1 XL each, eat at once), potions of gain level; kills alone are slow (XL13 at 40000).
3. **Reflection** still missing — required before Medusa/Castle (shield of reflection, amulet, silver dragon scales). Sleep resistance would help.
4. Altar DL15 (48,19): wand of create monster p = sacrifice fodder for Luck/a gift if ever worth the time; holy water needs potions of water (dilute potions twice in a fountain — DL8/Oracle).
5. Luckstone at Mines' End when convenient; $4416 + DL14 vault could buy +1 protection (400 x XL = 4800 at XL12) from the Minetown priest — low priority.
