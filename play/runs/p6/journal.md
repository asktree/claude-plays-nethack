# p6 journal

## Shift 1
- T:1 DL1 — start: lawful female dwarven Valkyrie "P6", seed 206. St 13 Dx 14 Co 19 In 8 Wi 11 Ch 10. Kitten.
  Kit: a +1 long sword, b +0 dagger, c +3 small shield, d food ration (all uncursed). Up stairs (18,6), tiny room.
- T:1-338 DL1 — explore() auto-fought newts, lichens, a grid bug, a jackal, a sewer rat. DL1: '>' (7,6), up (18,6),
  fountain (6,15) (SW room). Low boots (7,14), scroll READ ME (4,15), lichen corpse, gold.
- T:447 DL1 — pet test of the low boots in the lit stair room: kitten stood on them, no message -> not cursed. Wore
  them (e), AC5.
- T:564 DL2 — a kobold threw a MAGENTA potion: "somewhat dizzy" + Confused -> magenta = confusion or booze
  (named "dizzy"). Killed the kobold: XL2.
- T:731 Hungry; ate the (T:1) food ration, no rot effect. DL2: '>' (61,7), up (38,6), 3 FOUNTAINS (2,3) (40,4)
  (68,18); vault guard footsteps (a vault somewhere).
- T:965 DL2 — acid blob in a corridor: dagger hit, then ONE sword blow -> "Your long sword corrodes!" (blob lived).
  Finished it with 2 kicks (leather boots can't corrode; one splash -6). Took the ACID BLOB CORPSE (h: stoning cure).
- T:1000 killed a kobold -> XL3 (40 HP). It dropped 13 darts (i). Falling rock trap at (3,6) (-3 HP).
- T:1043-1079 large box (15,18) locked: force_box() with the dagger, 11 turns. Scrolls ASHPD SODALG (k), PHOL ENDE
  WODAN (l), puce potion (m), 2 yellowish brown gems (n). Emerald potion (j) from the NW room.
- T:1160 DL3 — explored the east half: a bat (35->28 HP) killed. TWO '>' on DL3: (49,7) and (52,18). Scroll GARVEN
  DEH (o) at (46,5). West half of DL3 unreached (dead ends (58,20) (41,8) (31,13) not searched).
- T:1325 took DL3 '>' (49,7) -> Dungeons DL4 (^O) => DL3 (52,18) = GNOMISH MINES branch (by elimination).
- T:1390-1452 DL4 — FLOATING EYE in the SW room (9,18): 13 darts from (9,17) (8 hits, unskilled d3-2 ~1 each), the
  dagger missed; it survived. All missiles stop at the monster's square (hit or miss) -> lay under it. Waited 45
  turns (it didn't move), fetched 5 rocks from the up stairs; on return the eye AND the whole pile were gone (no
  message; the kitten probably carries the darts/dagger). Eye last seen (12,19). LOST: 13 darts, +0 dagger b.
- T:1515 Hungry; T:1576 DL4 hidden passage at (25,8) (dead end (25,9)); cash register chime + "someone cursing
  shoplifters" = a SHOP on DL4. T:1595 hidden passage at (36,10) (dead end (36,9)). Dead end again at (39,16).
- T:1614 WEAK -> T:1617 PRAYED (1st prayer): SUCCESS, "Tyr is well-pleased", hunger fixed. Next prayer not before
  ~T:2700 (prayer_check()).
- T:1210 — "Your acid blob corpse rots away." (carried corpses other than lizard/lichen vanish after ~250 turns).
- T:1620 DL4 — hidden door (39,17) south of the dead end; 2 jackals + a dwarf zombie came through: held the corridor,
  fight_until_clear() killed both jackals (no damage). The dwarf zombie hit twice (T:1631, T:1634); explore() walked
  on past it (my -a pattern had silenced its hits). Large kobold left alone.
- T:1666 DL4 — KADIRLI'S USED ARMOR DEALERSHIP (58-67,3-8), door (58,9); '>' (63,18). A MIMIC posing as ']' (63,5).
  Priced the stock by farlook from inside (see state.md). Bought +2 STUDDED LEATHER ARMOR (47zm; spe>0 => never
  generated cursed) and leather gloves q (11zm, untested). Wore the armor: AC5 -> AC0. $0 left.
- T:1678-1686 — a giant bat in the shop: 40 -> 21 HP before it died (fast, erratic; I hit ~60%). No prayer
  available, so I set an Elbereth fallback at HP<17 (not needed). Rested to 35/40 by T:1811 in the shop's front row.
- The kitten carried shop goods around (crossbow bolt, hiking boots, long sword, the "piece of cloth" cloak,
  dwarvish cloak) => all those are NOT cursed. My dagger b + 5 darts came back (the kitten had dropped them in my
  path; pickup_thrown took them); 8 darts still missing.
- END OF SHIFT 1: T:1811, DL4 (60,8) in the armor shop, HP 35/40, XL3, AC0, $0. Kitten adjacent. No hostiles in view
  (the mimic 3 squares away is stationary).

## Shift 2
- T:1811-1857 DL4 — killed a large kobold in the SW-middle room, took its 19 gold ($19; the cloak costs 89).
- T:1902 DL4 — bought an ELVEN LEATHER HELM (s, 11zm) from Kadirli ($8 left).
- T:1935 DL4 — pet test in the 1-wide corridor outside the shop door: dropped helm s + gloves q on (58,11) (next to
  me), the kitten stepped on with NO "reluctantly" message and picked up the gloves => both NOT cursed. Wore both:
  AC -2 (both +0). (The kitten had carried a shop long sword out to (58,11): free, left there.)
- T:1943 killed a gecko; T:1952 destroyed the DL4 dwarf zombie at the stair room door -> XL4 (HP 51/51).
- T:1962 DL4 stair room: took a white gem (t) and an orcish dagger (u, BUC unknown: throwing only).
- T:1973 DL5 — arrived (13,16) up stairs, small room with a FOUNTAIN (12,13). Kitten killed a giant bat.
- T:2348 DL6 Hungry. T:2256 "Off with her head!" = a THRONE ROOM on DL6 (not found; avoid). Hidden doors (35,12),
  (9,19); DL6 '>' (8,17). T:2410 killed a giant ant (no corpse); T:2414 ate the lichen (last food).
- T:2427 DL7 — up stairs (11,10). T:2447 a hostile housecat at the room door: killed, but 51 -> 34 HP.
- T:2475-2490 DL7 corridor (48,7): auto-fight killed a fox; then TWO GIANT ANTS (speed 18, AC3: I hit them only ~40%)
  took me 39 -> 25. Elbereth (verified) at (48,7): ants and a rock piercer "turn to flee". Hungry T:2523.
- T:2538 tried to kill the rock piercer (speed 1) for food: missed, an ant came back, piercer bit: 27 -> 18 HP (35%).
  Re-engraved Elbereth, rested to 27. T:2608 Weak -> T:2611 PRAYED (2nd prayer, 994 turns after the 1st): SUCCESS,
  hunger fixed. Kitten lost somewhere on DL7 (last seen near the up stairs room (19,11)).
- T:2801 full HP on the Elbereth at (48,7). 113 exp (XL5 needs 160). Explored east: T:2811 a GIANT SPIDER (lvl 5, speed
  15, poison 2d4; ~2% instadeath per full melee from poison) bit me at (56,9) next to the DL7 '>' (58,6). Elbereth
  (garbled twice, the helper re-engraved). Also on DL7: giant ants, giant bat, little dog, dingo, a WEREJACKAL (howling).
- T:2929 full HP. My wait-loop fired when the spider stepped out of view (out of view != far): it ended up ON the stairs
  next to me. Re-engraved Elbereth at (57,7) (no damage), the spider fled, stepped onto '>' with nothing adjacent.
- T:2935 DL8 — arrived at up stairs (60,8), alone (kitten lost on DL7). Peaceful dwarf lord here. DL7 room (55-68,3-8)
  has a scroll (64,6) and food (67,4) left behind.
- T:3091 DL8 — explore: TWO up staircases (60,8) and (51,15) => DL7 was the ORACLE level and (51,15) leads to
  SOKOBAN. Trapped closet "Vlad was here" (38,1) marked avoided. Gold: $19 -> $94 (enough for the 89zm cloak).
- T:3126 SOKOBAN 1 (soko4-2 / wiki 1a): took a food ration on the arrival stairs. sokoban.solve() did 16/16 pushes by
  T:3444 with interruptions: giant rat, goblin (killed; dropped 2 scrolls VENZAR BORGAVVE), acid blob (killed with a
  thrown orcish dagger hit + a KICK — sword untouched), little dog (killed, 51 -> 42), red naga hatchling (killed).
  A stale trap record at every filled pit of the (33,8-13) column made the step guard refuse; forced those steps after
  game.rescan_terrain() showed no trap there (harness_notes #4).
- T:3445 Weak again (hunger ran ~1.1/turn); T:3474 ate the red naga hatchling corpse ("You feel strong!": St 14 from
  exercise, no resistance) + a food ration. Loot: 2 candy bars + 1 more, food ration, moonstone ring (y), scrolls x.
- T:3504 a SNAKE (poisonous, speed 15) bit once at (40,13); Elbereth (garbled once, re-engraved, verified). The snake
  went out of view at (39,14) — probably hiding under the orcish dagger (38,14).
- END OF SHIFT 2: T:3506, Sokoban 1 (40,13) ON ELBERETH, HP 49/51, XL4 (~143 exp), AC-2, $94, not hungry. No pet.
