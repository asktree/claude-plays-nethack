# p4 — current state (rewrite as things change)

## Character
- Name/role: P4, lawful female dwarven Valkyrie, god: Tyr. Seed 404 (local practice game).
- Turn / Dlvl / XL / HP / Pw / AC: T:6298 / SOKOBAN LEVEL 2 (Dlvl 8, soko3-1 = wiki Sokoban_Level_2b, SOLVED) / XL8 /
  85/85 / 13/13 / AC-8 / $100
- Position at end of shift 3: (51,14) inside the stair room of Sokoban level 2 (the room's door (51,15) was locked:
  unlocked with key g). Up stairs to Sokoban level 3 at (47,10).
- In the stair room right now: a FLOATING EYE at (45,14) (NEVER melee; the harness note wrongly says "corner it and
  kill it" — ignore that) and a MOUNTAIN NYMPH at (44,9) that hasn't moved for 18+ turns (probably asleep). A gold
  golem was wandering the row-16 corridor to the west. 3 chickatrices killed here (corpses at (51,15), (50,13), ...:
  never touch/eat).
- Attributes: St 18/02 (was 18/05; giant spider corpse), Dx 10, Co 19, In 7, Wi 9 ("You feel wise!" T:4369).
- Skills: long sword EXPERT (T:6279), dagger Basic.
- Intrinsics: cold res (Valk), stealth, infravision, SPEED (XL7), TELEPATHY (floating eye), MAGIC RESISTANCE (worn
  GDSM X). NOT poison resistant (giant spider corpse T:5301 gave nothing).
- HUNGER: ate food ration e at T:6150 -> fine until ~T:7000. Food left: 4 tripe rations (w) only! (Yak, 50% vomit for
  a dwarf; 200 each). Eat fresh safe corpses; buy/find rations. Prayer is safe again for Weak.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:3562 | Weak (hunger), DL7 (40,15) | SUCCESS. Timeout reset |
| T:4251 | (a WISH) | +50-149 timeout |
| T:6298 | prayer_check(): no trouble, p_safe 0.998 (2736 turns since the last prayer) | prayer available for MAJOR trouble |

## Equipment worn/wielded
- a: blessed rustproof +1 EXCALIBUR (wielded). X: +2 GRAY DRAGON SCALE MAIL (worn; MR; wished blessed). c: +3 small
  shield. j: +0 orcish helm. O: +0 iron shoes. AC -8.
- A NYMPH CAN CHARM THE GDSM OFF YOU (T:5057). After any nymph contact: check `inventory()` for "(being worn)" on X.

## Key inventory (letters)
- Daggers to throw: b +0 dagger, y dagger (quivered), f orcish dagger, i 2 orcish daggers (all uncursed).
- V uncursed elven mithril-coat (spare, 150 wt: consider dropping). G uncursed pick-axe. g KEY (unlocks doors/boxes).
- J 2 uncursed LIZARD CORPSES (stoning cure). L uncursed UNICORN HORN (cured raven blindness in 1 apply).
- Y can of GREASE (unknown BUC; grease the cloak/armor vs grabbers — no cloak yet).
- Wands: U digging, P striking, r light, R light (new), x "polymorph" (self-zap = sliming cure), T CURVED (unknown),
  t URANIUM (unknown). Engrave-test T and t next shift (not in Sokoban? engraving is fine in Sokoban).
- Rings (unknown, don't put on untested): S copper, Q granite. Amulet: o SPHERICAL (unknown: could be strangulation —
  don't wear untested).
- Scrolls: k uncursed IDENTIFY + l IDENTIFY (unknown BUC) -> read to ID o/S/Q/T/t. A + Z(2) = EARTH (GARVEN DEH, from
  Sokoban 1). n CURSED PRATYAVAYAH (enchant armor/weapon/remove curse). p uncursed blank. Unknown: d ANDOVA BEGARIN,
  D EIRIS SAZUN IDISI, H LEP GEX VEN ZEA, K KO BATE, B STRC PRST SKRZ KRK.
- Potions: h BLESSED sky blue (200 group), N blessed + F uncursed "object detection" (bubbly), v ORANGE (unknown BUC;
  an earlier orange one was cursed), m RUBY (unknown).
- Spellbooks: u BLESSED dusty (safe to read), q plaid. Tools: W blessed oil lamp, I camera, M magic marker.
- Gems: C 2 blue, s orange, z 2 white, E yellow.

## Identified appearances
- scroll MAPIRO MAHAMA DIROMAT = identify; GARVEN DEH = EARTH (Sokoban level 1's two scrolls); balsa wand = light;
  CRYSTAL = digging; SILVER = make invisible; STEEL = striking. DARK potion = BLINDNESS (a nymph hurled it: "It suddenly
  gets dark"). EFFERVESCENT potion = EXTRA HEALING (nymph quaffed: "looks much better"). ETAOIN SHRDLU = create monster?

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1-3 | Dungeons | see journal shift 1 (DL2 chaotic altar (5,4), Sipaliwini's general store) |
| 4 | Dungeons | up (54,5); '>' (45,15) -> DL5; '>' (72,7) -> MINES. |
| 5 | Dungeons | up (50,17), down (51,6), fountain (52,5). NOT the Oracle. |
| 6 | Dungeons | up (22,14), down (37,9). Fully explored; one '<'. Dwarf digging in the SE. |
| 7 | Dungeons | up (53,4), down (18,7). (harness mis-identifies it as bigrm-1) |
| 8 | Dungeons | up (48,13) (fountain room), down (10,15). |
| 9 | Dungeons | THE ORACLE (peaceful Oracle (39,12), centre unexplored). up (7,4), down (59,9) in a room entered by its west door (57,7) from corridor (56,7). Brown mold (22,14). |
| 10 | Dungeons | up (17,13) -> DL9; SOKOBAN up stairs (63,18). Nothing below explored. |
| Sok 1 (Dlvl 9) | Sokoban | soko4-1 (1b) SOLVED T:5734. down (38,10), up (38,12). |
| Sok 2 (Dlvl 8) | Sokoban | soko3-1 (2b) SOLVED T:6213. down (35,8), up (47,10) in the stair room (door (51,15) unlocked). |
| Mines 1-3 (DL5-7), Minetown (DL8) | Mines | Minetown: temple of Tyr (co-aligned, altar (55,17)), '<' (15,13); a werewolf howls there. Mines 3 (DL7): '>' (69,9) behind a HOLE at (64,9) — bypass dug at (65,10)/(64,10)/(63,10). |

## Threats / known dangers
- Nymphs: charm off worn armor (GDSM!). Kill at range or while asleep; never let one act next to you.
- Sokoban level 3+: more monsters (a zoo on the top level). Earth elementals pass through walls.
- Orcish arrows (poisoned, 1/30 instadeath w/o poison res): fight Uruk-hai from a nook.

## Objective and plan
- Next: Sokoban level 3. First deal with the stair room: the (sleeping?) nymph at (44,9) — throw daggers from a line
  (she can't teleport in Sokoban) or hit her while asleep (stealth); leave the floating eye alone (throw daggers only).
  Then '<' (47,10) -> level 3 -> `sokoban.solve()`.
- Read identify (k, l) on the amulet/rings/wands at a quiet moment. Engrave-test T and t.
- Food: only tripe left: eat safe fresh corpses; buy rations when possible.
