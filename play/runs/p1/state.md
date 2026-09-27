# p1 — current state (rewrite as things change)

## Character
- Name/role: P1 the Skirmisher — lawful female dwarven Valkyrie, god: Tyr (seed 101, local practice game)
- Turn / Dlvl / XL / HP / Pw / AC: T:4445 / Dlvl 7 / XL6 (Exp 447; XL7 at 640) / 72/72 / 11/11 / AC2. Wielding blessed rustproof +2 EXCALIBUR. Ring f (prot. from shape changers) worn on the right hand since T:3940 (take it off when leaving were-levels if hunger matters; it costs 1 nutrition/20 turns).
- Position at shift end (shift 5, T:4602): DL7 (27,15), in the corridor just E of the fountain room's E doorway (20,15), W of the stuck boulder (28,15). No monsters in view. HP 72/72. Nearest refuge: the `>` (13,8) via (20,15)->(14,14) door->(13,9).
  Ate a food ration at T:4368 (Hungry then) -> ~800+ nutrition: Hungry again ~T:5100. Food left: F 1 food ration, j 1 candy bar (+ cursed g/D, not food).
- Attributes: St18 Dx12 Co20 In10 Wi10 Ch7 (Ch7 => shop prices +50%)
- Intrinsics: cold res (Valk), stealth (Valk), infravision (dwarf), speed at XL7. Long sword skill: SKILLED (enhanced T:3441).
- Luck 0; alignment record high ("well-pleased" at T:3401); no peacefuls killed.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:1271 | welded cursed orcish dagger (MINOR trouble — mistake) | accepted, trouble NOT fixed, timeout reset |
| T:2016 | lycanthropy (MAJOR) | "well-pleased ... You feel purified" CURED |
| T:3401 | Weak from hunger (MAJOR; prayer_check 98%, 1382 turns after the 2nd) | "well-pleased. Your stomach feels content." nutrition 900. **No prayer before ~T:4400** unless life-or-death; always `prayer_check()` first. |

## Equipment worn/wielded (letter: item)
- **WIELDED: a: blessed rustproof +1 EXCALIBUR** (made T:4180 at the DL7 fountain (12,16), first dip). +d5 to-hit, +d10 damage, drain resistance, auto-search. Rust problem solved. (Enchant weapon scroll G read on it at T:~4182 — see journal for the result.)
- c: uncursed +3 small shield (worn), e: +0 studded leather armor (worn), n: +0 orcish helm (worn) -> AC2 [seen]
- The cursed corroded orcish dagger lies on the DL1 `>` (54,7). Never pick it up.

## Key inventory (letters) — EVERYTHING IDENTIFIED at T:3930 (scroll of identify hit "identify all")
- **B: BLESSED SCROLL OF TELEPORTATION** — the emergency escape (random teleport on the level; fails on no-teleport levels). Read it when melee goes bad and Elbereth/stairs are not options.
- G: scroll of enchant weapon — read plainly on Excalibur at T:~4182 (rustproof already; see journal).
- z: wand of lightning (0:3), E: wand of lightning (0:6 after 2 zaps at T:4131-4132) — 6d6 ray, bounces; never zap toward a wall < 14 squares away in line; `zap('E', dir)`.
- **h: magic marker (0:82) but CURSED** — scrolls written with it come out cursed unless the paper is blessed. Needs remove curse / holy water first. Known writable scrolls: identify, enchant weapon, teleportation, fire, light, amnesia.
- w: uncursed ring of fire resistance (not worn). f: uncursed ring of protection from shape changers (WORN, right hand). **K: 'engagement ring' — UNKNOWN type and BUC (dropped by an unseen biter on DL7 T:4555): do NOT put it on; price-ID at a shop or identify later.**
- Scrolls: i uncursed AMNESIA (NEVER READ; keep as future blank paper), x uncursed light, A uncursed fire (harmless to me with ring w on; burns adjacent monsters and my scrolls if unlucky).
- Potions: q blessed sickness (throw at a non-poison-resistant tough monster: halves its HP), u blessed blindness (junk/throw), C uncursed oil (light source / fire bomb when lit and thrown).
- y: figurine of a coyote (junk). $98.
- **Food: F: 2 uncursed food rations; j: uncursed candy bar. g: 2 CURSED candy bars + D: cursed partly eaten candy bar = always "rotten" (only for confusion-farming, never as food).**
- No healing potions, no unicorn horn, no lizard corpse. Escapes: scroll B, Elbereth (engrave where you stand; stepping off wipes it), stairs.
- Left behind: DL3 `<` room: +0 dagger b (18,5), orcish dagger p (21,5), violet gems (werejackal territory). DL6 (8,5): scale mail (unknown BUC). DL1 `>` (54,7): the cursed corroded orcish dagger — never pick it up.

## Identified appearances (all learned)
- Scrolls: ZELGO MER identify, EIRIS SAZUN IDISI amnesia, GARVEN DEH light, HACKEM MUCHE fire, TEMOV teleportation, FOOBIE BLETCH enchant weapon. (ZLORFIK, DUAM XNAHT: base-100 class from shop prices, types unknown.)
- Potions: yellow sickness, brilliant blue blindness, cyan oil (swirly base 100, murky base 50: unknown).
- Wands: marble lightning. Rings: diamond fire resistance, iron protection from shape changers.

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1 | main | `<` (76,4). `>` (54,7) big room (50-61,5-9) — cursed orcish dagger on it. SINK (55,6). Fully explored. |
| 2 | main | `<` (46,16). `>` (48,7). **FOUNTAIN (25,6)** (Excalibur backup — but reaching DL2 means passing the DL3 `<` werejackal camp). TRAP DOOR (71,8) = shaft to DL5. Fully explored. |
| 3 | main + Mines branch | `<` (19,9) room (18-20,4-9). ARROW TRAP (19,6). **WEREJACKAL (d form) + 4 jackals + fox frozen next to the `<` at (19,8)**. Annootok's general store NW (3-7,5-8) — food rations here. `>` (29,16) and `>` (46,18) — one is the Mines, the other leads to DL4 `<` (5,9). Unexplored east room via door (60,8). |
| 4 | main | `>` (20,14) room (18-27,11-14); hidden door (17,14) W (now open) -> corridor -> W room (3-8,9-13) with **`<` (5,9)**. Hidden door (43,9) -> gold room (44-50,6-10), closed door (51,9) E, doorway (43,6) W with the row-6 corridor (boulder pushed to (27,6), STUCK there — dead end or hidden corridor). Food room (58-61,12-15): **SLEEPING GAS TRAP (58,15)** (known to the harness), old gnome corpse; boulder (63,14) outside its door (62,14) — enter via (62,12). NE room (73-76,3-5), E room (74-76,14-18). South half of the map (rows 16-21) unexplored. Level "explored" per explore(). |
| 5 | main | Arrival room (59-65,4-8). **`<` (59,16)** room (56-60,13-16). **`>` (70,16)** room (67-75,14-17). **FOUNTAIN (26,8) DRIED UP (T:3228)**. **BURNED ELBERETH (45,18)** in the big S room (33-46,17-19); its E door (47,18) KICKED OPEN (broken) -> direct corridor to the `<`. Centipede corpse (40,17). Fully explored. |
| 6 | main | **ORACLE LEVEL.** `<` (9,7) lit NW room (7-17,4-7): scale mail (8,5) left. `>` (65,10) in the E room (56-69,8-10), door (55,10). Delphi room (34-44,8-16), doors: (43,7) N (kicked open), (33,10) & (33,15) W doorways; 8 centaur STATUES (harmless). Oracle's chamber walls (37-41,10-14), doorway (37,11); **FOUNTAINS (38,12) (39,11) (39,13) (40,12)**, peaceful Oracle (39,12) — never attack. Corridors: row 5-6 E from the `<` room to col 48 -> (46,8)-(46,18) S -> row 18 E/W; tiny room (24-26,17-19) with armor (24,18)+spellbook (25,18), boulders (25,14),(26,15) NE of it (unexplored beyond). Rock mole corpse (35,11) T:3813. Killed here: rock mole x2, monkey, dog, kobold zombie, rock piercer, giant bat, floating eye (no corpse). |
| 7 | main (level below the Oracle: SOKOBAN entrance = a 2nd `<` here, NOT FOUND YET after explore(): it must be behind the boulders (35,13) [corridor (29-34,13), push E] or (28,15) [corridor (21-27,15) E of the fountain room, push E], or a secret door) | `<` (5,7) to DL6 (small room 3-6,6-8; empty chest (4,7)). **`>` (13,8)** in room (13-17,6-8), S doorway (13,9) -> corridor (13,10-13) -> door (14,14) -> S room (9-19,15-17): FOUNTAIN GONE (Excalibur), TRAP (18,15) (known), statue (14,15), E doorway (20,15), door (20,17). Room (28-33,7-11): doors (34,7) open, (34,9) doorway, (34,11) closed, (27,10) W doorway. NE room (64-69,4-8) via door (68,9) (kicked open) — empty. Gold (64,17) SE (unreached?), gold (51,3). Corpses: ape (20,7), kitten (22,15), werejackal (30,13) — never eat weres. Killed here: iron piercer, ape, housecat? (no: DL6), yellow light, sewer rat, rope golem, iguana, kitten, 2 werejackals, newt. |

## Threats / known dangers
- **DL6 (Oracle level): a HOSTILE WATER DEMON** (AC-4, ~36 HP, 3 attacks 1d3, summons demons 1/13 per round, speed 12 = mine) is loose, last seen ~3 squares from the DL6 `>` (65,10) at T:3922 (levels freeze: it is still there). Never re-enter DL6 by its `>`; Elbereth makes it flee; walking away at equal speed it gets no attacks; a non-fleeing stalker adjacent to you on stairs FOLLOWS you.
- DL7: the yellow light is DEAD (T:4052, potion-of-blindness vapours trick). Future lights: same trick needs a potion of blindness or a blindfold/towel — none left; otherwise avoid/stairs.
- **DL7: a WEREJACKAL** (howl heard T:3939). Ring f (protection from shape changers, WORN since T:3940) blocks lycanthropy and keeps it in @ form (which ignores Elbereth, hits d4, summons jackals 1/10 per round). Keep the ring on while on DL7; never eat its corpse.
- DL3 werejackal pack camps the DL3 `<` (19,8).
- Poisonous biters/stingers (centipedes, killer bees, water moccasins, soldier ants): each poisoned hit has a 1/30 instadeath roll — no poison resistance yet.
- No healing items. Escapes: blessed scroll of teleportation B, Elbereth engraved where you stand (stepping off wipes it), stairs. Prayer NOT available until ~T:4400 (last prayer T:3401); always prayer_check() first.
- Thieves (monkeys, nymphs): drop wands + marker before fighting one.

## Objective and plan
1. **Find the Sokoban `<` on DL7.** explore() is exhausted; both boulders (35,13) and (28,15) are stuck. The unexplored south-middle band (cols 21-56, rows 12-21) must connect via hidden passages: `search(15)` x2-3 at the corridor dead ends (27,15) [W of the boulder], (36,12)/(37,12), (26,10) W doorway corridor, (58,15); along the fountain room's S wall (row 18) and E wall; the room (28-33,7-11)'s S wall (row 12); the SE room (58-72,17-19)'s N/W walls. Kick nothing in shops. If found: the Sokoban `<` is the up staircase that is NOT (5,7). Sokoban: follow knowledge/wiki solutions with sokoban.push(); never read amnesia; the prize (bag of holding / amulet of reflection) is the goal.
2. Fallback if no passage after ~150 turns of searching: go down the `>` (13,8) to DL8 (cockatrices become possible at DL8 with XL6: never touch/eat, melee only with Excalibur, flee hissing; no lizard/acidic corpse yet) and look for another route/items; return to DL7 later.
3. Keep the ring f on while on DL7 (weres). Don't wear ring K (unknown). Poison resistance still missing: avoid bee/ant swarms.
4. Food: F 1 ration + j 1 candy bar; Hungry expected ~T:5100. Eat fresh SAFE corpses (`corpse()`) when Hungry. Prayer available again ~T:4400+ (last T:3401, now safe by turn count: prayer_check() first).
5. Longer term: Mines/Minetown (altar for BUC, temple protection with gold, shops to price-ID ring K and sell junk), uncurse the 82-charge marker (remove curse / holy water) to write scrolls; get AC below 0.
