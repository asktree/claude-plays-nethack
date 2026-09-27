# p1 — current state (rewrite as things change)

## Character
- Name/role: P1 the Skirmisher — lawful female dwarven Valkyrie, god: Tyr (seed 101, local practice game)
- Turn / Dlvl / XL / HP / Pw / AC: T:5249 / **Sokoban level 6 SOLVED (Sokoban 1a, T:5249); next: Sokoban level 5 (Sokoban 2) via the `<` (33,7)** / XL6 (Exp 601; XL7 at 640) / 72/72 / 11/11 / AC2. Wielding blessed rustproof +2 EXCALIBUR. Ring f (prot. from shape changers) worn on the right hand since T:3940 (costs 1 nutrition/20 turns; take it off if food gets tight).
- Position at last update: Sokoban 6 (33,9) below the `<` (33,7); a peaceful gnome lord on the stairs. Sokoban 6's `>` (35,7) leads back to DL7 (14,15).
  Nutrition ~200 at T:5249 (ration T:4368 + a quarter of a rotten yeti T:4955): **Hungry expected ~T:5300**. Food: F 1 + P 1 food rations, Q 2 pancakes, U slime mold, j candy bar (+ cursed g candy bars, not food). Eat pancakes/slime mold first, rations last. **T: an EGG of unknown kind — NEVER eat it (could be a cockatrice egg = stoning).**
- Attributes: St18 Dx12 Co20 In10 Wi10 Ch7 (Ch7 => shop prices +50%)
- Intrinsics: cold res (Valk), stealth (Valk), infravision (dwarf), speed at XL7. Long sword skill: SKILLED (enhanced T:3441). Excalibur gives auto-search (found the DL7 secret door (17,9) by walking past).
- Luck 0 (keep it: no boulder smashing / earth scrolls / squeezing in Sokoban); alignment record high; no peacefuls killed.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:1271 | welded cursed orcish dagger (MINOR trouble — mistake) | accepted, trouble NOT fixed, timeout reset |
| T:2016 | lycanthropy (MAJOR) | "well-pleased ... You feel purified" CURED |
| T:3401 | Weak from hunger (MAJOR; prayer_check 98%, 1382 turns after the 2nd) | "well-pleased. Your stomach feels content." nutrition 900. Prayer available again since ~T:4400 (1500 turns since = 98%); always `prayer_check()` first. |

## Equipment worn/wielded (letter: item)
- **WIELDED: a: blessed rustproof +2 EXCALIBUR** (made T:4180 at the DL7 fountain (12,16); enchant weapon scroll read on it T:4182). +d5 to-hit, +d10 damage, drain resistance, auto-search.
- c: uncursed +3 small shield (worn), e: +0 studded leather armor (worn), n: +0 orcish helm (worn) -> AC2 [seen]
- The cursed corroded orcish dagger lies on the DL1 `>` (54,7). Never pick it up.

## Key inventory (letters) — EVERYTHING IDENTIFIED at T:3930 (scroll of identify hit "identify all")
- **B: BLESSED SCROLL OF TELEPORTATION** — emergency escape OUTSIDE Sokoban (Sokoban levels are no-teleport: it fails there).
- z: wand of lightning (0:3), E: wand of lightning (0:6) — 6d6 ray, bounces; never zap toward a wall < 14 squares away in line; `zap('E', dir)`.
- **h: magic marker (0:82) but CURSED** — needs remove curse / holy water first. Known writable scrolls: identify, enchant weapon, teleportation, fire, light, amnesia.
- w: uncursed ring of fire resistance (not worn). f: uncursed ring of protection from shape changers (WORN, right hand). **K: 'engagement ring' — UNKNOWN type and BUC: do NOT put it on; price-ID/identify later.**
- Scrolls: i uncursed AMNESIA (NEVER READ; future blank paper), x uncursed light, A uncursed fire.
- Potions: q blessed sickness (throw at a tough non-poison-resistant monster), C uncursed oil (light source / fire bomb).
- y: figurine of a coyote (junk). $137.
- **New from Sokoban 1 (all unidentified, BUC unknown): L bag (not a bag of tricks: #loot did not bite; sack/oilskin/BoH — put nothing valuable in until tested), M swirly potion, N + O two scrolls labeled NR 9 (the entry level's pair = almost certainly EARTH; never read in Sokoban), R ivory ring (don't wear), S iridium wand (engrave-test it OUTSIDE Sokoban on a quiet level; never zap unknown wands in Sokoban), T egg (never eat).**
- **Food: F: 1 uncursed food ration; j: uncursed candy bar. g: 2 CURSED candy bars + D: cursed partly eaten candy bar = always "rotten" (never as food).**
- No healing potions, no unicorn horn, no lizard corpse. Escapes: Elbereth (engrave where you stand; stepping off wipes it), stairs; scroll B outside Sokoban.
- Left behind: DL3 `<` room: +0 dagger b (18,5), orcish dagger p (21,5), violet gems (werejackal territory). DL6 (8,5): scale mail (unknown BUC). DL7 (57,4): orcish helm; (58,8): orcish helm + orcish shield + orcish chain mail (Mordor orc drops, unknown BUC). DL1 `>` (54,7): the cursed corroded orcish dagger — never pick it up.

## Identified appearances (all learned)
- Scrolls: ZELGO MER identify, EIRIS SAZUN IDISI amnesia, GARVEN DEH light, HACKEM MUCHE fire, TEMOV teleportation, FOOBIE BLETCH enchant weapon. (ZLORFIK, DUAM XNAHT: base-100 class from shop prices, types unknown.)
- Potions: yellow sickness, brilliant blue blindness, cyan oil (swirly base 100, murky base 50: unknown).
- Wands: marble lightning. Rings: diamond fire resistance, iron protection from shape changers.

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1 | main | `<` (76,4). `>` (54,7) big room (50-61,5-9) — cursed orcish dagger on it. SINK (55,6). Fully explored. |
| 2 | main | `<` (46,16). `>` (48,7). **FOUNTAIN (25,6)**. TRAP DOOR (71,8) = shaft to DL5. Fully explored. |
| 3 | main + Mines branch | `<` (19,9) room (18-20,4-9). ARROW TRAP (19,6). **WEREJACKAL (d form) + 4 jackals + fox frozen next to the `<` at (19,8)**. Annootok's general store NW (3-7,5-8) — food rations here. `>` (29,16) and `>` (46,18) — one is the Mines, the other leads to DL4 `<` (5,9). Unexplored east room via door (60,8). |
| 4 | main | `>` (20,14) room (18-27,11-14); hidden door (17,14) W (open) -> W room (3-8,9-13) with **`<` (5,9)**. Hidden door (43,9) -> gold room (44-50,6-10). Food room (58-61,12-15): **SLEEPING GAS TRAP (58,15)** (known to the harness). South half (rows 16-21) unexplored. |
| 5 | main | Arrival room (59-65,4-8). **`<` (59,16)** room (56-60,13-16). **`>` (70,16)** room (67-75,14-17). FOUNTAIN (26,8) DRIED UP. **BURNED ELBERETH (45,18)** in the big S room (33-46,17-19); its E door (47,18) broken. Fully explored. |
| 6 | main | **ORACLE LEVEL.** `<` (9,7) lit NW room (7-17,4-7): scale mail (8,5) left. `>` (65,10) in the E room (56-69,8-10), door (55,10). Delphi room (34-44,8-16); Oracle's chamber (37-41,10-14), doorway (37,11) + mole hole (38,10); FOUNTAINS (38,12) (39,11) (39,13) (40,12) — **a HOSTILE WATER DEMON roams near the `>` (65,10)**: never re-enter DL6 by its `>`. Peaceful Oracle (39,12). |
| 7 | main (Sokoban entry level) | `<` (5,7) to DL6 (room 3-6,6-8; empty chest (4,7)). **`>` (13,8)** in room B (13-17,6-8), S doorway (13,9), broken secret door (17,9) -> 1-square stub (17,10). **SOKOBAN `<` = (14,15) UNDER THE STATUE of a hill orc** in the fountain room C (10-19,15-17): TRAP (18,15) (known), doors (14,14) N, (9,16) W, (20,15) E doorway, (20,17) E open door (nothing behind it). Room D (28-33,7-11): doors (27,10) W, (34,7) (34,9) (34,11) E. Room E (48-56,3-7): doors (47,3) (47,5) W, (57,4) E; orc gear (57,4),(58,8). NE room F (64-69,4-8) via broken door (68,9). SE room G (58-71,17-19): doors (57,18) W, (61,16) N. Corridor boulders (28,15),(35,13) sit on corridor corners: squeeze past diagonally (pack < 600 wt). Dead ends searched: (49,13) 21x, (17,10) 16x — nothing. The south-middle band (cols 21-56, rows 12-21) is solid rock as far as anyone can tell. A PEACEFUL DWARF wanders the corridors (never attack). Corpses: ape (20,7), kitten (22,15), werejackal (30,13), giant rat (37,10). |
| Sokoban 6 (= Sokoban 1a) | Sokoban | **SOLVED T:5249** (all holes filled). `>` (35,7) back to DL7; `<` (33,7) up to Sokoban 5. Leftover boulders (37,9),(38,9); cursed candy bar (36,10); corpses (37,14). Killed here: yeti, werejackal, gecko, mountain nymph. |

## Threats / known dangers
- **Sokoban**: no teleport (scroll B useless), no diagonal squeezing between boulders; Luck penalties for smashing boulders/reading earth/squeezing; the top level has a treasure zoo (fight it at the door, one at a time, full HP). Prize: bag of holding or amulet of reflection.
- **DL6 (Oracle level): HOSTILE WATER DEMON** (AC-4, ~36 HP, 3x 1d3, summons demons 1/13 per round, speed 12) near the DL6 `>` (65,10). Never re-enter DL6 by its `>`.
- DL7: yellow lights appeared twice (both dead); future lights: no potion of blindness left — avoid/stairs. Werejackals: 2 killed; keep ring f on there.
- DL3 werejackal pack camps the DL3 `<` (19,8).
- Poisonous biters/stingers (centipedes, killer bees, water moccasins, soldier ants): each poisoned hit has a 1/30 instadeath roll — no poison resistance yet (blue jelly corpses give 13%: eat a fresh one if it drops).
- Cockatrices possible from DL8 (never touch/eat; flee hissing; no lizard/acidic corpse yet).
- No healing items. Escapes: Elbereth where you stand, stairs; scroll B outside Sokoban. Prayer: ~98% available (last T:3401); prayer_check() first.
- Thieves (monkeys, nymphs): drop wands + marker before fighting one.

## Objective and plan
1. **Solve Sokoban with `sokoban.solve()`** (4 levels up: 6 -> 5 -> 4 -> 3). When it pauses: read why (monster, item on a boulder path, board mismatch), deal with it, call `solve()` again (it resumes from the board); `sokoban.progress()` = step k/N. Push by hand only if solve() says the board no longer matches. Pick up the scrolls of earth if any (never read them in Sokoban). Fight the top-level zoo from the doorway at full HP; Elbereth if swarmed (works in Sokoban).
2. Food: Hungry ~T:5100. Eat fresh SAFE corpses when Hungry; the last ration is the reserve. If food runs out: the DL3 general store sells rations (far); Sokoban monsters' corpses.
3. After Sokoban (with the prize): back down to DL7 via the Sokoban `>`s, then DL8+ for the Mines/Minetown detour (altar for BUC, temple protection with gold, shops to price-ID ring K), uncurse the marker (remove curse / holy water), AC below 0.
4. Keep ring f on for now (weres can appear anywhere; +5% hunger only). Don't wear ring K (unknown). No poison resistance: avoid bee/ant swarms.
