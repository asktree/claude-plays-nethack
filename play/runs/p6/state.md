# p6 — current state (rewrite as things change)

## Character
- Name/role: P6, lawful female dwarven Valkyrie, god: Tyr. Seed 206 (local practice game).
- Turn / Dlvl / XL / HP / Pw / AC: T:3506 / SOKOBAN level 1 (bottom; the game calls it "Sokoban / Level 7") at (40,13),
  STANDING ON A VERIFIED DUST ELBERETH / XL4 (~143 exp; XL5 at 160) / 49/51 / 10/10 / AC-2 / $94.
- Attributes: St 14 (+1 exercise at T:3474), Dx 14, Co 19, In 8, Wi 11, Ch 10 (shop prices x4/3).
- Intrinsics: cold res (Valk), stealth (Valk), infravision (dwarf). Speed at XL7. No telepathy, NO poison resistance.
- Luck notes: nothing Luck-changing done (Sokoban solved by the rules). Alignment: no peacefuls hurt.
- Hunger: not hungry — ate a red naga hatchling corpse + a food ration at T:3474 (~900 nutrition) -> Hungry ~T:4300.
- To-hit is POOR: vs AC3 monsters (giant ants, snakes) I hit ~40%. Excalibur (+d5 hit, +d10 dmg) is the fix.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:1617 | Weak (hunger), DL4 (39,16) | SUCCESS, well-pleased; hunger fixed. |
| T:2611 | Weak (hunger), DL7 (48,7) on Elbereth, HP 27/51 | SUCCESS, well-pleased; hunger fixed (p_safe was 94%). Timeout reset: NO prayer before ~T:3600 without prayer_check() (~T:3900+ for good odds) |

## Equipment worn/wielded (AC-2)
- a: uncursed CORRODED +1 long sword (wielded; acid blob T:966 — Excalibur's dip removes erosion).
- r: +2 studded leather armor (positive enchantment => generated non-cursed, mkobj.c).
- c: uncursed +3 small shield. e: +0 low boots (pet-tested T:447).
- s: +0 elven leather helm, q: +0 leather gloves (both pet-tested NOT cursed T:1935, worn).

## Key inventory (letters) — [seen in inventory T:3506]
- b: uncursed +0 dagger, u: orcish dagger (BUC unknown: throw only), i: 4 darts (quivered), p: 5 rocks.
- Food: z food ration, w 3 candy bars. (A 2nd food ration left on Sokoban 1 at (36,10).)
- Scrolls (unknown): f READ ME, k ASHPD SODALG, l PHOL ENDE WODAN, o GARVEN DEH, x 2 VENZAR BORGAVVE (a pair: likely
  a common type, e.g. identify). Price-ID before reading.
- Potions (unknown): j emerald, m puce. Named type: MAGENTA = "dizzy" (confusion or booze).
- y: MOONSTONE RING (unknown; never put on untested). t: white gem, n: 2 yellowish brown gems.
- Escape items: none (stairs + Elbereth). Healing: none.
- Emergency cures: NONE (stoning -> pray when the timeout allows). Keep a lizard corpse if one turns up.

## Identified appearances (appearance -> identity)
- magenta potion = confusion or booze (vapour "somewhat dizzy"), named "dizzy".

## Dungeon map
| Dlvl | branch | features (stairs, altars+alignment, shops+type, fountains, stashes, traps, notes) |
|---|---|---|
| 1 | Dungeons | up (18,6), '>' (7,6); fountain (6,15). |
| 2 | Dungeons | up (38,6), '>' (61,7); FOUNTAINS (2,3) (40,4) (68,18); falling rock trap (3,6); a vault (guard footsteps). |
| 3 | Dungeons | up (69,8); '>' (49,7) -> DL4; '>' (52,18) = GNOMISH MINES (by elimination). West half unexplored. |
| 4 | Dungeons | up (23,15) (under a rock); '>' (63,18). KADIRLI'S USED ARMOR DEALERSHIP (58-67, 3-8), door (58,9). Hidden passages (25,8) (36,10), hidden door (39,17). Floating eye loose (last (12,19)). Spare long sword (58,11) outside the shop door. |
| 5 | Dungeons | up (13,16), FOUNTAIN (12,13) in the up-stair room; '>' (31,15). East half unexplored (boulder (29,10) with a monster behind it; boulder (18,17)). |
| 6 | Dungeons | up (40,7); '>' (8,17) (SW room behind hidden door (9,19)); hidden door (35,12). THRONE ROOM somewhere unexplored (east x>=64?) — "Off with her head!": avoid. A metal-eater ("crunching sound"). Gold left at (23,14) (24,4). |
| 7 | Dungeons = ORACLE LEVEL (inferred: DL8 has the Sokoban stairs; the Delphi with its FOUNTAINS should be at the map centre, around (34-44,7-15), unseen) | up (11,10), '>' (58,6) in the NE room (55-68,3-8) (scroll (64,6), food (67,4) there). DANGEROUS: GIANT SPIDER (poison, lvl 5, fast) near the '>'; giant ants x2; dingo; little dog; giant bat; WEREJACKAL (howling). KITTEN LOST here. |
| 8 | Dungeons | up (60,8) -> DL7; up (51,15) -> SOKOBAN. Peaceful dwarf lord. TRAPPED CLOSET (38,1): one-time trap door (avoided). '>' not found yet. |
| Soko 1 | Sokoban (soko4-2 = wiki Sokoban_Level_1a) | SOLVED (16/16, T:3444). '>' (35,7) -> DL8, '<' (33,7) -> Sokoban 2. Left: food ration (36,10), orcish dagger (38,14) — a SNAKE is probably hiding under it. |

## Kadirli's armor shop (DL4) — prices at Cha 10 (x4/3; +10zm per + enchantment point)
- MIMIC posing as ']' at (63,5): never touch; stay 2+ squares away.
- "piece of cloth" 89zm = base 50 + unID surcharge -> CLOAK OF PROTECTION or DISPLACEMENT; the kitten carried it
  (=> NOT cursed). I NOW HAVE $94: BUY IT on the next pass through DL4.
- +1 scale mail 73 (61,4); +1 studded leather 33 (65,5); orcish helm 13 (60,6); dwarvish cloak 67 (not cursed);
  hiking boots 67/93 (93 = +2, base 50: jumping/speed/water walking), mud boots 67, combat boots 53; plate mail 800.
- Items a pet drops INSIDE a shop become shop stock: never pet-test your own things near a shop.

## Pets
- NONE with me. The kitten was lost on DL7 (last seen ~T:2440 near the up-stair room (19,11)).

## Threats / known dangers
- HERE: a SNAKE (poisonous, speed 15, AC3) hiding next to me (last seen (39,14); probably under the ')' at (38,14)).
  I stand on Elbereth at (40,13). Snakes respect Elbereth. Don't melee it at XL4 (poison: 1/240 death per bite).
- DL7: giant spider by the '>' (58,6) — the way back from DL8 to DL7 arrives right there.
- No prayer until ~T:3600+ (prayer_check()). HP emergencies: Elbereth (verified by elbereth()) / stairs.

## Objective and plan
1. Deal with the snake from Elbereth: wait for it to show, then leave via the '<' (33,7) to Sokoban 2 or pick up the
   food ration (36,10) first (route via row 8, away from row 14). Take the snake at range only.
2. XL5 (~17 exp to go) -> Excalibur. Fountains: the Oracle's Delphi on DL7 (unseen, centre), DL5 (12,13) by its up
   stairs, DL2 x3. The Oracle's centaurs are peaceful; the DL7 spider is the risk.
3. Sokoban levels 2-4 (prize: bag of holding or amulet of reflection; the top level is a zoo — fight from a doorway at
   full HP). Then back up: buy the cloak on DL4 ($94 >= 89), then Mines/Minetown via DL3 (52,18).
