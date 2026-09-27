# p2 — current state (rewrite as things change)

## Character
- Name/role: p2 — local practice game, seed 202 (lawful female dwarven Valkyrie, god: Tyr)
- Turn / Dlvl / XL / HP / Pw / AC: **T:6886 / Dlvl 13** / **XL9** (Exp 3050; XL10 at 5120) / 109/113 / 7/14 / **AC -5** (3 points of divine protection T:4517 + orcish helm + elven cloak) / $0 on me, 83 gold in the sack n. Last meals: warhorse corpse T:6150 + floating eye T:6650 (tiny) → expect Hungry ~T:7000–7200 (food: ration l, lichen k, tin f).
- Position at shift-9 end: **D13 (18,18), one step EAST of the LAWFUL ALTAR to Tyr (17,18)** in the SW altar room (9-24,16-20; door (19,16) N closed, E doorway (24,18) — its booby-trapped door already exploded). No monsters in view. My junk (scroll of destroy armor, knife, 7 elven arrows) lies on (18,18). NO PET (djinni left on D11).
- Attributes (T:3483): St:17 Dx:12 Co:19 In:11 Wi:8 Ch:9 (Cha 9 → shop buy prices ×4/3; carry cap 950). "You feel wise!" T:6027.
- Skills: long sword **EXPERT** (T:3719 Skilled, T:6231 Expert = the Valkyrie maximum); #enhance other skills when "more confident" appears.
- Intrinsics (source, turn): cold res (Valk), stealth (Valk + elven cloak), infravision (dwarf), SPEED (XL7, T:4212); EXTRINSIC telepathy from the amulet of ESP (worn T:2424) + **INTRINSIC TELEPATHY (floating eye corpse, T:6650)** → the amulet slot is free for life saving/reflection when found; Excalibur gives automatic searching. NO poison resistance. **NO magic resistance, NO reflection** (the lamp wish failed → plan B needed).
- Luck notes: nothing done to Luck (no peacefuls killed by me).
- Alignment: "Tyr is well-pleased" at T:6110 = alignment record >= 14 (quest entry needs >= 20 and XL14).

## Prayer log
| turn | reason | result |
|---|---|---|
| T:6107–6110 | DELIBERATE no-trouble prayer standing on the lawful altar D11 (44,6) with 2 potions of water on it (pray(force=True) after prayer_check p_safe 1.0) | SUCCESS: "shimmering light ... The potions on the altar glow light blue ... Tyr is well-pleased" → 2 holy water (both used on the lamp). Prayer timeout RESET at T:6110 (rnz(350): median ~350, long tail). Next emergency prayer: run prayer_check(); ~92% safe at T:6900, 95% at T:7110, 98% at T:7610. The D13 altar (17,18) is CO-ALIGNED: a no-trouble prayer there once the timeout is 0 blesses water on it. |

## Equipment worn/wielded (letter: item)
- a: EXCALIBUR — blessed rustproof **+6** (wielded). NEVER read another enchant weapon on it. NOTE: applying the pick-axe or #rubbing a lamp WIELDS that tool — always `w`,`a` afterwards.
- c: uncursed +3 small shield (worn, iron: rust monsters can rust it); DIVINE PROTECTION 3 points
- y: +0 scale mail (worn) [seen]; **q: uncursed +0 ELVEN CLOAK ("faded pall", worn T:6298; altar-tested; it absorbs rust-monster touches aimed at the suit)**; E: uncursed +0 high boots (worn); O: uncursed AMULET OF ESP (worn); **j: uncursed +0 orcish helm (worn, altar-tested T:5930)**

## Key inventory (letters) — BUC [seen] from altars unless marked
- b: blessed +0 dagger (quivered); **C: uncursed dagger (+1 by shop price 19 zm)**, **D: uncursed dagger**, **F: uncursed elven dagger** — throwing daggers (Valkyrie dagger skill can reach Expert); P: 12 BLESSED darts. NEVER THROW INSIDE A SHOP (auto-sold).
- PICK-AXE: inside bag s (uncursed bag = holding or oilskin) — `bag_take('s','pick-axe')` before `dig('>')`; keep it bagged near shops.
- d: **blessed OIL LAMP**; e: uncursed oil lamp; A: uncursed brass lantern; CANDLES: w (6 uncursed) + z (1 uncursed) = 7 (for the Candelabrum — never burn them)
- n: uncursed SACK: 83 gold + a MURKY potion (base 100). s: uncursed BAG (holding/oilskin) holding the pick-axe.
- SCROLLS: **J: 2 uncursed TELEPORTATION** (escape); i: uncursed KO BATE (= light); m: uncursed unlabeled (blank).
- POTIONS: **L: uncursed OBJECT DETECTION** (golden); N: uncursed MAGENTA (base 100); murky (base 100) in the sack.
- p: uncursed CLOTH SPELLBOOK (unknown; Valkyrie casting is poor — low priority)
- WANDS: x = SLEEP (uncursed) [2–6 charges left]; g = FIRE (uncursed; 6d6 ray, bounces; bag burnables first if it can hit me); V = LIGHT; r = SLOW MONSTER (uncursed); o = CREATE MONSTER; **M = MAKE INVISIBLE (0:3)**; **I = UNDEAD TURNING (0:3)**
- RINGS: **H: CURSED ring of TELEPORTATION** (never wear; bought 267 zm); B: CURSED ring of shock resistance (never wear)
- TOOLS: **Q: uncursed CAN OF GREASE**; u: uncursed key (skeleton key: apply, direction `.` for a box here); t: uncursed whistle (tin or magic, untested)
- FOOD: l: uncursed food ration; k: uncursed lichen corpse (never rots); f: uncursed tin (tin opener lost track: open with `apply`/eat).
- Gems (all uncursed, unidentified): R black, X 2 black (other type), Y 2 red, Z yellow, W yellowish brown
- Inventory count 46/52 after dropping junk (a full pack stops bag_take: "Your knapsack cannot accommodate any more items").
- Escape items: 2 scrolls of teleportation J; wand of sleep x (and fire g); Elbereth; `dig('>')` (pick-axe in bag s); upstairs; prayer per the log.
- Healing: none. Emergency cures: none (no lizard, no unicorn horn).

## Identified appearances (appearance -> identity)
- YUM YUM -> enchant weapon; ANDOVA BEGARIN -> identify; ELAM EBOW -> scare monster (lost); unlabeled -> blank paper; KO BATE -> light; DAIYEN FOOELS -> TELEPORTATION
- KERNOD WEL -> base 80 (enchant armor / remove curse); **ELBIB YLOH -> DESTROY ARMOR**; HAPAX LEGOMENON -> base 100 group; scroll of identify: type known
- uranium wand -> create monster; curved wand -> SLEEP; balsa wand -> slow monster; jeweled wand -> FIRE; pine wand -> LIGHT; **iron wand -> MAKE INVISIBLE; forked wand -> UNDEAD TURNING**
- silver ring -> regeneration; agate ring -> base 100 group; steel ring -> shock resistance; **twisted ring -> TELEPORTATION**
- puce potion -> base 150; murky potion -> base 100; magenta -> base 100; YELLOW -> SPEED; cyan -> GAIN LEVEL; clear -> water (type named "water"; "blessed clear potion" = HOLY WATER); WHITE -> PARALYSIS (formally identified); **EFFERVESCENT -> FULL HEALING** (a hill orc quaffed one T:5915: "looks completely healed"); **golden -> OBJECT DETECTION**; potion of speed = yellow (shop D12)
- hexagonal amulet -> ESP; oval amulet -> unchanging
- lamp (plain) -> magic lamp (used up); oil lamp identified; "bag" -> sack identified (n); the other "bag" (s) = holding/oilskin
- **faded pall -> ELVEN CLOAK**; vellum spellbook -> level 1; dull -> level 4; leathery -> level 3/4; cloth -> unknown (i, in the sack)

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1 | Dungeons | up (8,8); down (10,19); fountains (27,11), (5,18) |
| 2 | Dungeons | up (40,6); down (21,14) = GNOMISH MINES BRANCH; down (74,17) = main; Kittamagh's bookstore (2-5,17-19) door (6,18); fountain (59,16) |
| 3 | Dungeons | up (21,18) under a broken large box; down (51,10); SLEEPING GAS TRAP (35,8); vault |
| 4 | Dungeons | up (39,18); down (12,18) via hidden passage (8,15); FOUNTAIN (22,17); UPERNAVIK'S GENERAL STORE (69-71,15-17) door (68,16) |
| 5 | Dungeons (ORACLE) | up (9,5); down (58,5); Delphi fountains; PIT (14,15) |
| 3–6 (Mines) | Gnomish Mines | Mines 1 up (77,13) down (50,13); Mines 2 up (44,10) down (8,10); MINETOWN = Mines 3 (Dlvl 5): up (74,5), down (3,6), TEMPLE of ODIN (neutral) altar (38,9) priest (protection bought), shops: Kilmihil books (29-31,7-9), AlliWar hardware (29-31,15-17) with a disguised LARGE MIMIC (30,16), Pasawahan deli (36-38,16-17), Izchak lights (47-49,7-9), Ouiatchouane general (48-50,15-17); Mines 4 (Dlvl 6) up (45,5), `>` not found |
| 6 | Dungeons | up (23,15); SOKOBAN `<` (4,15) (skipped); `>` (41,3) NE room; leprechaun hall (20-25,4-7) cleared; fountain (7,6); 2 gold-carrying leprechauns roam |
| 7 | Dungeons | up (33,13); `>` (64,16) (SE, door (61,16)); SW room (5-12,17-19) with a BURNED ELBERETH at (10,19); SPIKED PIT (23,13); a peaceful tengu |
| 8 | Dungeons | up (48,4); `>` (49,16) in a small room (48-50,14-16) with a FOUNTAIN (50,15), door (49,13); hidden passage (42,5); east third unexplored |
| 9 | Dungeons | up (31,19) S room; `>` (43,4) small NW room (39-43,4-6) door (44,4); W room (14-20,13-17) axe at (16,14); far-W room (2-6,13-16) with an ARROW TRAP (6,15) and MY HOLE at (4,15); a carnivorous ape wanders |
| 10 | Dungeons | **BIG ROOM** (irregular variant: wall fragments, trees, fountains (11,11), (65,11)); up (16,8); `>` (4,16) far W; loot: spellbooks (15,6), (20,11), scrolls (22,15), (26,10), (48,17), potion (29,17); **DANGER: KILLER BEE HIVE + giant spider + pyrolisk + mountain centaur + ghoul near the `<`** — never linger |
| 11 | Dungeons (**QUEST PORTAL LEVEL**, the Norn's plea on every arrival; portal NOT found — probably the unexplored SE corner) | **`<` (48,19)** and **FOUNTAIN (52,19)** (active) in the SW room (47-54,15-20; ape statue (53,16); E door (54,18) → corridor E toward the nymph area); **`>` (14,19)** in the W room (11-24,16-19; E door (24,19) closed, N doorway (20,16)); **LAWFUL ALTAR (44,6)** in the N-centre room (32-45,5-10; hill orc statue (41,6); doors (30,6) W closed, (46,8) E doorway, (39,10) S; a cursed elven leather helm lies on the altar); NE room (51-55,3-8): doorways (55,4) E, (50,3)/(50,8) W; scimitar + orcish dagger (56,5), gremlin corpse (56,6) (poisonous); E room (69-73,4-10) doors (69,7) open, (69,9) closed, **ICE BOX (71,7)**; NW closet (15-19,6-10) door (19,10): studded leather armor (16,9); S room (33-41,16-19) doors (33,17) W doorway, (33,19) W open, (41,17) E doorway, (41,19) E closed; corridor chokepoint (30,19) (rock on all diagonals) between the S room and the W room's door (24,19); YELLOW MOLD (28,13) (avoid); boulders (48,9), (28,16) (the latter blocks the corridor west of the bee junction); hidden passage near (24,9). **DANGERS T:6385–6389: KILLER BEE SWARM (9+ bees) at the corridor junction (27-32,12-16) north of the S room; a RUST MONSTER in the S room/corridor (31,19); the WOOD NYMPH awake in the SE (last (68,18) T:6084)** |
| 12 | Dungeons | `<` (48,3) in a tiny room (46-49,3-5): **LAND MINE (47,4)** (avoided), doors (49,2) N, (50,5) E, (45,4) W, doorway (46,6); **CARIGNAN'S ANTIQUE WEAPONS OUTLET** (57-66,3-7), door (56,3) (4 small mimics killed; stock: long swords 20, daggers 5, silver spear, shuriken, bronze plate mail 533, potion of speed 267 at (57,6)); NW room (10-19,2-6): **FOUNTAIN (12,3)**, **`>` (13,4)**, gold (17,5); middle room (25-37,10-17), LOCKED door (37,16) (travel routes through it — waypoint (38,12)); SE room (44-57,12-18): hidden PIT (48,13), emptied large box (53,17), doors (52,12) N, (50,18) S (dead end (50,19) searched 15); corridor dead end (49,1) unsearched; east strip x>67 unknown. A leprechaun roams (NW room). |
| 13 | Dungeons | **`<` (74,7)** in the NE room (70-77,4-8), hidden door (70,6) (found); **`>` (66,16)** in the SE room (~64-72,12-18); **LAWFUL ALTAR to Tyr (17,18)** in the SW room (9-24,16-20), door (19,16) closed N, E doorway (24,18) (booby trap spent), hill orc statue (12,19); middle room (40-55,7-12) doors (39,11) W, (46,12) S; NW-middle room (24-35,3-9) with an ANTI-MAGIC FIELD (27,7) (drains Pw only), boulder (21,6). Unexplored: x<9, the south-middle (x 26-63, rows 13-21), the north strip. |

## Pets
- TAME DJINNI (from the lamp T:6114) — **LEFT ON D11** at T:6399 (last seen (29,19) T:6389, between the rust monster and the bee swarm). Lvl 7, AC 4, flies, weapon 2d8, poison resistant. Its tameness (5) drops by 1 per ~150 turns apart; after ~700 turns it goes peaceful/untame (≈T:7070) — NOT fetched in shift 9 (bee swarm next to D11's `>`). Fetching it means facing the swarm level again; only with Elbereth ready and the corridor chokepoint plan. It cannot be stolen from; it followed me on 4-square waypoints but lost me on 8-square travel legs twice.

## Threats / known dangers
- **No poison resistance**: killer bees (D10 hive, D11 swarm), soldier ants, giant spiders, snakes, quasits, spiked pits → each poisonous hit = 1/8 × 1/30 death. Fight them one at a time in 1-wide corridors (rock on the diagonals), with Elbereth, or the fire wand along a line; never a swarm in a room.
- **No magic resistance / no reflection**: no Castle, no lingering on D20+ near soldiers; avoid unknown wand zappers at range. Plan B for MR: cloak of magic resistance (shops/monsters), gray dragon scales (D20+), the Castle wand (needs MR first...), reconsider the Sokoban prize via D6 (4,15) once XL is higher.
- Yellow lights: NEVER melee (explode → blind). Pyrolisk: kill fast or break line of sight; bag burnables first.
- Gremlins at NIGHT (real clock 22:00–06:00 in the game's timezone, UTC here): curse claw steals intrinsics — sleep-ray them or fight by day.
- Rust monsters: no HP damage; the elven cloak covers the suit, Excalibur is rustproof; the orcish helm and small shield can rust — acceptable, kill them for XP.
- Mummies/zombies/gas spores are mindless: telepathy does not show them.
- Nymphs steal (also worn items and the wielded weapon); leprechauns steal gold (keep it in the sack).
- Cockatrices (one killed on D11 T:5953): only Excalibur, never touch/eat corpses; no lizard corpse carried and prayer is on cooldown → avoid them for now.
- Werejackals: fight in @ form/at range; "You feel feverish" → prayer (check the timeout first) or holy water (none left).
- SPHERES (shocking/flaming/freezing) are MINDLESS: telepathy never shows them; one exploded out of a dark corridor on D12 (4d6 elec). Booby-trapped doors (D13) explode on opening (damage + stun).
- SHOPS: throwing anything inside a shop auto-sells it ("You relinquish ..."); things thrown in from outside become shop property. Buy back or don't throw.
- Land mine D12 (47,4) next to the `<`: stepping on it = rnd(16) damage + wounded legs + it becomes a pit.
- Mines' End luckstone only at XL10+.

## Objective and plan
- DONE shift 9: D12 explored (weapon shop, fountain, `>`); 4 shop mimics, chickatrice, energy vortex, large dog, floating eye, violet fungus, gnome mummy, monkey, leprechaun (fled) → **XL9** (Exp 2404 → 3050); **INTRINSIC TELEPATHY**; 3 throwing daggers bought; identify ×2 (6 items known: teleportation ring, make invisible, undead turning, object detection, destroy armor); 2nd teleport scroll; grease; D13: `<`, `>`, **co-aligned LAWFUL ALTAR (17,18)**, everything BUC-tested uncursed.
- NEXT (shift 10):
  1. D13: finish exploring (west x<9, south-middle, north strip) with the altar room as the base; kill things near the altar and SACRIFICE fresh corpses there (`#offer`, corpses < 50 turns old: Luck, prayer-timeout reduction, gift chance ~1/10 per sacrifice at Luck ≥ 0 — a random LAWFUL or unaligned artifact; Mjollnir is neutral and cannot be my gift). Never sacrifice my own race (dwarves) or pets; never engrave on the altar.
  2. HOLY WATER: dilute junk potions (magenta N, murky in the sack; the D12 fountain (12,3) is 9 squares from D12's `>` (13,4)) into water, drop them on the D13 altar and pray (no trouble) once prayer_check() says the timeout is surely 0 (≥ ~1000 turns after T:6110 is still not a guarantee — rnz(350) can be large; only pray without trouble if p_safe is 1.0).
  3. XP toward XL10 (5120): D13–D14 at full HP; poison-resistance still missing (killer bees/soldier ants in corridors only).
  4. MR plan B: cloak of magic resistance (shops/monster drops), gray dragon scales; reflection: Sokoban prize (D6 `<` (4,15)) is a candidate once strong enough for a long detour.
  5. The djinni on D11 goes untame ≈T:7070: forget it unless the swarm is gone.
- Emergency plan: HP < 40% → Elbereth / upstairs / scroll J / sleep wand x (never toward an adjacent wall); prayer only if prayer_check() says the odds are good (last prayer T:6110).

## Harness/helper calibration notes
- Verified shift 9: walk_path()/step() refuse to walk into monsters (shopkeeper), farlook shows shop prices, pay(), eat() of shop corpse + pay(), engrave_test(), identify menus via obs.menu pages, altar D/X/. drop + ,/. pickup, fight() inside an engulfer.
- Verified shift 8: `zap()` down a corridor, `fight()` on a sleeper, `fight_until_clear()` in corridors/doorways (radius matters: 4 reported "clear" with orcs at 5–7), `explore()` (hidden passage, stairs, fountain), `avoid()`, altar drop test, `dip()` on a fountain (x2), `pray(force=True)` no-trouble prayer, `cont --reply` for the "Call a clear potion:" prompt, `bag_take` by identified name, `pickup(pattern)`, `#enhance` menu, `go_down(wait_pet=0)` under pressure.
- GAPS (details in harness_notes.md Shift 9): FALSE '!! you WIELD ... Excalibur — not a weapon' warning on every obs since the shift-9 daemon restart (ignore it while inventory shows 'a - ... Excalibur (weapon in hand)'); engulf border read as 'trap at <my square>' in pause text; throw() doesn't refuse inside shops (auto-sell); travel() keeps routing through known locked doors (use waypoints); bag_take stops silently on a full pack.
- Earlier notes still valid: never call `inventory()`/`here()` unless `obs.kind == 'command'`; `travel()` never autopicks up; pick-one menus close on the letter alone; `obs.menu` lists only the current page.
