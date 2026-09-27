# p1 — current state (rewrite as things change)

## Character
- Name/role: P1 the Woman-at-arms — lawful female dwarven Valkyrie, god: Tyr (seed 101, local practice game)
- Turn / Dlvl / XL / HP / Pw / AC: **T:15291 / DL19 (main dungeon), standing ON THE DL19 `<` (45,17) at shift-15 end** / **XL12** (Exp 25321; XL13 at 40000, XL14 at 80000) / **137/137** / 26/26 / **AC -12** (blessed +2 GRAY DRAGON SCALE MAIL + +3 small shield + orcish helm + elven cloak + blessed leather gloves + low boots + 3 points of divine protection). Wielding blessed rustproof **+6 EXCALIBUR** (long sword EXPERT; never enchant it again). Ring worn: f prot. from shape changers (right). Left hand FREE. $4597.
- Food: ate a food ration at T:14925 (Not hungry). Carried: J food ration, B C-ration, O K-ration, **y 6 lumps of ROYAL JELLY** (200 each, heal d20), X orange, Q pancake, j candy bar, U slime mold, g partly eaten ROTTEN ration. ~3000 nutrition. Keep eating fresh SAFE corpses (`corpse()`).
- Attributes: St 18/10, Dx 15+ ("You feel agile!" T:15177), Co20 In10 Wi11 Ch7.
- Intrinsics: cold res (Valk), stealth (Valk), infravision (dwarf), speed (XL7), POISON RES, FIRE RES, TELEPATHY. **MAGIC RESISTANCE (GDSM)**. Excalibur: auto-search, drain res. NO sleep resistance (elf-lord corpse T:14637 gave nothing), NO shock resistance, NO reflection.
- Luck 0 (no luckstone); alignment record high; no peacefuls killed.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:1271 | welded cursed orcish dagger (MINOR trouble — mistake) | accepted, trouble NOT fixed, timeout reset |
| T:2016 | lycanthropy (MAJOR) | "well-pleased ... You feel purified" CURED |
| T:3401 | Weak from hunger (MAJOR; prayer_check 98%) | "well-pleased. Your stomach feels content." |
- The wish (T:10728) added 50-149; **the prayer timeout has certainly been 0 since ~T:10880**. Prayer available for major trouble (HP <= 22 at 137 max, XL12: max/6). Stoning cure = prayer (no lizard).

## Equipment worn/wielded
- a: blessed rustproof +6 EXCALIBUR (wielded). c: uncursed +3 small shield. x: blessed +2 GRAY DRAGON SCALE MAIL (MR). n: uncursed +0 orcish helm. V: uncursed +0 faded pall = ELVEN CLOAK. r: blessed +0 leather gloves. z: uncursed +0 low boots. Ring f (prot. from shape changers, right). H: uncursed elven dagger (quivered).

## Key inventory (letters as of T:15291)
- **A: uncursed UNICORN HORN** (fixes stun/blindness in 1-5 applies).
- **T: uncursed MAGIC MARKER (0:22)** (identify written T:14719 cost 13). Blanks: **q uncursed unlabeled scroll, M unlabeled scroll (BUC unknown)**. Write only KNOWN types (identify, enchant weapon, light, fire, amnesia, teleportation, scare monster, create monster, gold detection, REMOVE CURSE — write it BY LABEL: `write_scroll('XOR OTA')`). Keep one blank for remove curse.
- **h: scroll of IDENTIFY** (found DL17, BUC unknown) — use on the next unknown amulet/ring worth knowing (topaz/twisted rings in the bag).
- **Escapes: G and Z = WAND OF TELEPORTATION** (Z 2 charges used of 4-8, G unknown). **Scrolls of teleportation: k x3 (uncursed), L, R (BUC unknown).** Elbereth. Stairs. Prayer.
- **o: WAND OF FIRE** (balsa, engrave-identified T:14819; charges unknown, 1 used) — SLIMING CURE (zap self / burn), burns permanent Elbereth, fire ray.
- E: wand of lightning (0:3). **Wands of striking: C (1+ charges used), Y (new), S = EMPTY (0 charges: "Nothing happens" — can be wrested or discarded).** p: wand of CREATE MONSTER.
- **D: uncursed BAG OF HOLDING ("BoH prize")**, 17 items: scroll ELAM EBOW (unknown), 2 scrolls of FIRE, yellow spellbook, SWIRLY potion = HEALING, wand of lightning (0:2), unknown rings **twisted (base 300: NEVER wear-test)**, bronze (blessed, 100), ivory (100), wire (100), coral (150), clay, opal, **topaz (new, DL16)**, and gems (black, 2 green, 2 orange, 3 red). **Pick-axe b is in the MAIN PACK** (`bag_put('D','b')` before any shop).
- s: uncursed scroll of FIRE (main pack). l: uncursed scroll of LIGHT.
- Potions: **P uncursed + u CURSED = SPEED**. **t BLESSED ruby** (unknown). w, e dark (unknown), i black (probably object detection), F dark green, N murky, I orange (new), m sky blue (= confusion or booze). No water.
- K: ring of REGENERATION (not worn). Tools: d uncursed KEY, W blessed oil lamp (LOW), v can of grease, b pick-axe.
- NO lizard corpse (stoning cure = prayer only), no holy water.

## Identified appearances
- Scrolls: ZELGO MER identify, EIRIS SAZUN IDISI amnesia, GARVEN DEH light, HACKEM MUCHE fire, TEMOV teleportation, FOOBIE BLETCH enchant weapon, KERNOD WEL scare monster, THARR create monster, ZLORFIK gold detection, **XOR OTA = REMOVE CURSE** (named). NR 9 (200) = earth or taming. ELAM EBOW, DUAM XNAHT (100) unknown.
- Potions: yellow sickness, brilliant blue blindness, cyan oil, pink gain level, swirly HEALING, golden SPEED, sky blue = confusion or booze; black probably object detection; dark green, murky, ruby, dark, orange unknown.
- Wands: marble lightning, iridium striking, oak magic missile, crystal speed monster, short TELEPORTATION, zinc nothing, ebony CREATE MONSTER, **balsa FIRE**.
- Rings: diamond fire resistance, iron protection from shape changers, engagement REGENERATION, agate = base 150.
- Amulets: **spherical = STRANGULATION** (a cursed one dropped on DL16 (4,7)).
- Armor: etched helmet = one of helmet/brilliance/opposite alignment/telepathy.
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
| **15** | main | `<` (11,4). **`>` (58,5)** (via hidden door (57,6)). **LAWFUL ALTAR to Tyr (48,19)** (SE room). ZOO (71-76,16-19) CLEARED; junk + spare spellbooks/fire-res ring at (71,19). Teleport trap (35,18). |
| 16 | main | `<` (8,17) in a closet (5-8,15-17); **`>` (3,7)** in the tiny west room (2-4,5-7) behind the closet's west door (4,15) -> corridor north. Teleport trap (49,11), bear trap (67,12), land mine (71,14). Yellow molds (2,5), (52,8). Cursed amulet of strangulation dropped at (4,7). |
| 17 | main | `<` (30,15), **`>` (71,16)** (SE room). BEEHIVE (2-10,16-20) cleared (jelly taken). FOUNTAIN (64,4) in the NE room. Burned ELBERETH at (42,5) (corridor). Trap (34,15). |
| **18** | main | **ROGUE LEVEL** (stairs shown as `%`, doors `+`; explore() misreads it). `<` (37,4), **`>` (16,2)** in a tiny NW room. Mostly unexplored (dark rooms). |
| **19** | main | `<` (45,17) (arrival room 40-48,16-19). **THRONE ROOM / COURT at ~(59-70,17-19)**, ~26 sleeping monsters seen by telepathy: YELLOW DRAGON (63,19), WHITE DRAGON (69,19), stone giant, rock troll, ogre king, orc-captain, mountain centaur, gnomish wizard, bugbears, hobgoblins, goblins, Uruk-hai, Mordor orc, kobold/gnome lords. Fountain somewhere ("water falling on coins"). Floating eye ~(24,14). NW room (20-32,4-9). `>` NOT FOUND yet. |
| Mines 1-8 | Mines | Minetown = Mines 3 (DL6): temple of Odin (neutral) (33,4), general store, hardware store; `>` (48,4) behind door (52,7). Mines' End (DL11): LUCKSTONE still in a SW closet (3,17)/(3,19). |
| Sokoban | Sokoban | ALL SOLVED, prize (BoH) taken. |

## Threats / known dangers
- **Booby-trapped doors fire on OPENING as well as on unlocking** (DL17 T:14761: an unlocked closed door exploded when opened). KABOOM wakes everything within ~15 squares and stuns (horn: 1-3 applies). Never open an unexplored door next to a sleeping zoo/court.
- **DL19 court**: sleeping; stealth keeps them asleep. If fought: from a doorway/corridor square outside the room, one at a time; kill the dragons first while they sleep (yellow = acid breath 4d6 unresisted; white = cold, resisted). Their breath is a ray: never stand in line at range.
- Fire gazes/breath burn scrolls and boil potions even with fire resistance: important ones in the BoH.
- Energy vortices: passive shock up to 9d4 while it lives (took 25 at T:15199) — kill in few blows; engulf drains Pw.
- Ravens blind (horn cures; they re-blind — kill them first).
- Incubi/succubi: armor removal. Cockatrices/chickatrices: melee only with Excalibur; prayer is the stoning cure.
- No sleep resistance: sleep rays (soldiers' wands) not blocked.

## Depth decision (shift 15)
- DL19 reached with zero trouble (worst HP 112/137). DL19 and DL20 cannot be Medusa (earliest DL21). **Stop descending at DL20** until reflection (or a blindfold/towel) + a way across water (levitation / water walking / cold wand ice) are in hand. Arriving on a level whose `<` sits on an island in water = Medusa: go straight back up.

## Objective and plan (after shift 15)
1. DL19: find the `>` (unexplored east/south; the court is in the SE ~(59-70,17-19)). Consider clearing the court with the stealth method (doorway, one sleeper at a time; dragons first) for XP and its throne-room chest — only at full HP with the `<` as retreat.
2. XP toward XL14 (quest portal DL13 (73,17)): wraith corpses (+1 XL each, eat at once), gain level potions.
3. **Reflection** still missing — required before Medusa/Castle. Use scroll h / the marker's identify on promising unknown amulets. Lizard corpse still missing.
4. Altar DL15 (48,19) for BUC tests (h, L, R, M, e, w, I, m unknown BUC). Holy water needs potions of water.
5. Luckstone at Mines' End; $4597 -> protection from the Minetown priest needs 400 x XL = 4800 at XL12 (almost there).
