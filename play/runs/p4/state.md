# p4 — current state (rewrite as things change)

## Character
- Name/role: P4, lawful female dwarven Valkyrie, god: Tyr. Seed 404 (local practice game).
- Turn / Dlvl / XL / HP / Pw / AC: T:7564 / SOKOBAN LEVEL 4 (Dlvl 6, soko1-1 = wiki Sokoban_Level_4a, SOLVED T:7477)
  / XL9 / 97/99 / 16/16 / AC-8 / $176. Standing at (34,10) (the wall gap between rows 9 and 11). Not hungry.
- ALL FOUR SOKOBAN LEVELS SOLVED. Remaining: the ZOO + PRIZE on Sok4 (see plan).
- Sok2 stair room: floating eye (45,14) left alive; gold golem wandering; STASH at (44,9): elven mithril-coat,
  blessed dusty + plaid spellbooks, wand of light. Chickatrice corpses at (51,15), (50,13) (never touch).
- Sok2 also has my orcish dagger f somewhere (fell through Sok3's hole (44,17) at T:6493).
- Attributes: St 18/02 (was 18/05; giant spider corpse), Dx 10, Co 19, In 7, Wi 9 ("You feel wise!" T:4369).
- Skills: long sword EXPERT (T:6279), dagger Basic.
- Intrinsics: cold res (Valk), stealth, infravision, SPEED (XL7), TELEPATHY (floating eye), MAGIC RESISTANCE (worn
  GDSM X), POISON RESISTANCE (scorpion corpse T:6603 "You feel healthy"). Excalibur: level-drain res + auto-search.
  Worn amulet of ESP = telepathy while NOT blind within 8 squares (shows mindless-free monsters behind walls).
- Enlightenment T:6481: piously aligned; "You can safely pray" with no trouble = prayer timeout 0 then.
- HUNGER: ate food ration e at T:6150 -> fine until ~T:7000. Food left: 4 tripe rations (w) only! (Yak, 50% vomit for
  a dwarf; 200 each). Eat fresh safe corpses; buy/find rations. Prayer is safe again for Weak.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:3562 | Weak (hunger), DL7 (40,15) | SUCCESS. Timeout reset |
| T:4251 | (a WISH) | +50-149 timeout |
| T:6298 | prayer_check(): no trouble, p_safe 0.998 (2736 turns since the last prayer) | prayer available for MAJOR trouble |
| T:6481 | wand of enlightenment: "You can safely pray" (no trouble -> timeout 0) | prayer SAFE |

## Equipment worn/wielded
- a: blessed rustproof +1 EXCALIBUR (wielded). X: +2 GRAY DRAGON SCALE MAIL (worn; MR; wished blessed). c: +3 small
  shield. j: +0 orcish helm. O: +0 iron shoes. AC -8.
- A NYMPH CAN CHARM THE GDSM OFF YOU (T:5057). After any nymph contact: check `inventory()` for "(being worn)" on X.

## Key inventory (letters)
- Daggers to throw: b +0 dagger, y dagger (quivered), i 2 orcish daggers (all uncursed). (orcish dagger lost down
  the Sok3 hole (44,17) -> somewhere on Sok2.)
- G uncursed pick-axe. g KEY (unlocks doors/boxes; both Sokoban stair-room doors so far were LOCKED).
- PACK: 51/52 letters used (ONE free: keep it for the prize). Food: n FOOD RATION, f C-ration, w 1 tripe ration,
  J 2 lizard corpses. R leather gloves (BUC unknown, from a sergeant: test before wearing). V black gem (unknown).
- J 2 uncursed LIZARD CORPSES (stoning cure). L uncursed UNICORN HORN (cured raven blindness in 1 apply).
- Y can of GREASE (unknown BUC; grease the cloak/armor vs grabbers — no cloak yet).
- Wands: q SLEEP (hexagonal; 2 charges used T:6493, T:7491 — a sleep ray freezes monsters ~6d25 turns: zap down a
  line of monsters), F TELEPORTATION (iridium, named; tested T:7564 — escape tool, zap monsters away), U digging,
  P striking, r light, x "polymorph" (self-zap = sliming cure), T SLOW MONSTER (curved), t ENLIGHTENMENT (uranium).
- Rings: S uncursed SEARCHING (copper; not worn: ring hunger); unknown: Q granite, u TOPAZ (Sok3), l JADE (Sok4) —
  don't wear untested.
- Amulet: o uncursed AMULET OF ESP (WORN since T:6312).
- Scrolls: A + Z(2) = EARTH (GARVEN DEH). p uncursed blank. (cursed PRATYAVAYAH dropped/teleported away on Sok4.)
  Unknown: d ANDOVA BEGARIN, D EIRIS SAZUN IDISI, H LEP GEX VEN ZEA, K KO BATE, B STRC PRST SKRZ KRK. No identify left.
- Potions: h BLESSED sky blue (200 group), N blessed + e OBJECT DETECTION (bubbly, formally identified T:7521), v ORANGE
  (unknown BUC; an earlier orange one was cursed), m RUBY (unknown).
- Tools: W blessed oil lamp, I camera, M magic marker.
- Gems: C 2 blue, s orange, z 2 white, E yellow.

## Identified appearances
- iridium wand = TELEPORTATION (named); hexagonal wand = SLEEP; curved = SLOW MONSTER; uranium = ENLIGHTENMENT; spherical amulet = ESP; copper ring = searching.
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
| Sok 2 (Dlvl 8) | Sokoban | soko3-1 (2b) SOLVED T:6213. down (35,8), up (47,10) in the stair room (door (51,15) unlocked). Stash (44,9). |
| Sok 3 (Dlvl 7) | Sokoban | soko2-2 (3a) SOLVED T:6583. down (36,17), up (45,12) in the stair room (door (48,16) unlocked). |
| Sok 4 (Dlvl 6) | Sokoban | soko1-1 (4a) SOLVED T:7477. down (27,5). ZOO x44-48 y14-20 (asleep): east door (49,17) off corridor x=50; PRIZE pile in the NORTH closet (42,15) behind door (43,15) (object detection T:7521). |
| Mines 1-3 (DL5-7), Minetown (DL8) | Mines | Minetown: temple of Tyr (co-aligned, altar (55,17)), '<' (15,13); a werewolf howls there. Mines 3 (DL7): '>' (69,9) behind a HOLE at (64,9) — bypass dug at (65,10)/(64,10)/(63,10). |

## Threats / known dangers
- Nymphs: charm off worn armor (GDSM!). Kill at range or while asleep; never let one act next to you.
- Sokoban level 4: ZOO (monsters asleep until disturbed). Fight from the zoo's doorway; wand of sleep q for a crowd.
- Spheres explode when adjacent (4d6 elec/fire; no item damage): strike first; lights (black/yellow) = halluc/blind
  (unicorn horn L cures).

## Objective and plan
- NEXT: THE PRIZE (Sok4). The zoo sleeps; Stealth keeps sleepers asleep (disturb() never wakes anything while
  Stealthy), so only ATTACKED monsters wake. Route with only 2 kills: stand at (50,17), unlock/open the east door
  (49,17), step into the doorway, kill the Green-elf at (48,17) (it wakes alone), step to (48,17), kill the lizard at
  (48,16), step to (48,16), then diagonally over EMPTY squares (47,15) -> (46,16) -> (45,17) -> (44,16) -> (44,15)
  (re-check each square: monsters may have shifted), open door (43,15) (may be locked: key g), step into the closet
  (42,15): the prize sits on a burned Elbereth + a CURSED scroll of scare monster (never pick up the scroll: it
  crumbles; pickup('bag of holding|amulet') by pattern). The closet square is a refuge (the scroll scares
  everything but shopkeepers/priests/minotaurs/Riders), but DON'T attack from it (burned Elbereth -> hypocrisy).
  If the zoo wakes: zap SLEEP (q) down lines of monsters; the 2 ZRUTIES (45,18)/(44,17) hit up to 42/turn (slow:
  walk away); soldier (45,20) + sergeant (48,20) may have wands (stay off their lines). Teleport wand F: zapping
  MONSTERS away works even on no-teleport Sokoban (teleport.c u_teleport_mon has no noteleport check); self-teleport
  doesn't. Prayer is safe for major trouble (timeout 0 at T:6481).
- Prize: amulet of reflection -> wear it instead of ESP. Bag of holding -> bag_put() refuses dangerous items (wands of
  cancellation, bags of tricks/holding); F is teleportation, safe to bag once named.
- After the prize: down through Sok3/Sok2 (orcish dagger somewhere on Sok2; stash at Sok2 (44,9) optional) to DL10,
  then explore DL10+ / Mines' End (luckstone). Test the leather gloves R (altar/pet) before wearing.
- Then back down through Sokoban (pick up the orcish dagger on Sok2, the stash at (44,9) optional) to DL10+.
- Food: tripe/tin/garlic only: eat safe fresh corpses (zoo corpses); buy rations when possible.
