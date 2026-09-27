# p2 — current state (rewrite as things change)

## Character
- Name/role: p2 — local practice game, seed 202 (lawful female dwarven Valkyrie, god: Tyr)
- Turn / Dlvl / XL / HP / Pw / AC: **T:7248 / Dlvl 13** / **XL9** (Exp 3885; XL10 at 5120) / 107/113 / 14/14 / **AC -5** / $0 on me, 83 gold in the sack n. Last meal: FOOD RATION at T:7248 (ate at Hungry) → next Hungry ~T:8000. Food left: lichen corpse k (never rots), tripe ration T (50% vomit for a dwarf), tin f. NO rations left — eat fresh corpses (poison resistant now: kobolds etc. are fine).
- Position at shift-10 end: **ON the LAWFUL ALTAR to Tyr, D13 (17,18)**, SW altar room (9-24,16-20). A PEACEFUL WHITE UNICORN (co-aligned: NEVER attack; throw gems at it when lined up = +1 Luck per real gem) wanders the room. No hostiles in view.
- Attributes: **St:14** (was 17; -3 from the scorpion corpse T:7135 — restore ability / golden-glow prayer boon restores it) Dx:12 Co:19 In:11 Wi:9 Ch:9. Carry cap now ~875 and I am CLOSE TO IT (a 40-wt corpse made me Burdened at St 17): keep the pack light.
- Skills: long sword **EXPERT**; #enhance other skills when "more confident" appears.
- Intrinsics (source, turn): cold res (Valk), stealth (Valk + elven cloak), infravision (dwarf), SPEED (XL7), EXTRINSIC telepathy (amulet of ESP O) + INTRINSIC TELEPATHY (floating eye, T:6650), **POISON RESISTANCE (scorpion corpse, T:7135: "You feel healthy")**. Excalibur autosearch. **NO magic resistance, NO reflection.**
- Luck: **positive, >= +2** (two sacrifices T:7124/T:7128 each gave "You think something brushed your foot" = Luck +1). No luckstone → it decays 1 per 600 turns.
- Alignment: "Tyr is well-pleased" at T:6110 (record >= 14); many hostile kills since.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:6107–6110 | deliberate no-trouble prayer on the D11 lawful altar with 2 waters | SUCCESS, 2 holy water, timeout reset |
| — | **T:7124: the raven sacrifice gave Luck (not "hopeful feeling") ⇒ PRAYER TIMEOUT WAS ALREADY 0 (verified).** It stays 0 until I pray. prayer_check() still says ~88–90% (it doesn't know) — trust the sacrifice evidence: an emergency prayer is SAFE now (Luck > 0, god not angry). A no-trouble prayer on this altar with waters on it = holy water; with Luck 2–3 the pat-on-head boon is 1/4 golden glow (+5 max HP AND Str restored to 17). |

## Equipment worn/wielded (letter: item)
- a: EXCALIBUR — blessed rustproof **+6** (wielded). NEVER read enchant weapon on it. Applying a pick-axe or #rubbing a lamp WIELDS that tool — `w`,`a` afterwards.
- c: uncursed +3 small shield; y: +0 scale mail; q: uncursed +0 elven cloak; E: uncursed +0 high boots; O: uncursed amulet of ESP; j: uncursed +0 orcish helm. Divine protection 3 points.

## Key inventory (letters) — 41 items
- THROWING: **e: blessed +0 dagger (at the ready)**, C: uncursed dagger (+1 by price), D: uncursed dagger, F: uncursed elven dagger; P: 12 blessed darts. NEVER THROW INSIDE A SHOP.
- BAG s (uncursed; very likely a BAG OF HOLDING — weight arithmetic): pick-axe, N magenta potion (base 100), b murky potion (unknown BUC, from a kobold lord), L 2 uncursed potions of object detection (= holy-water stock: dilute twice at a fountain). `bag_take('s', ...)`.
- SACK n: 83 gold + a murky potion (base 100).
- SCROLLS: **J: 2 uncursed TELEPORTATION** (escape); **U: uncursed VERR YED HORRE (unknown, new)**; m: uncursed unlabeled (blank).
- WANDS: x SLEEP [2–6 charges]; g FIRE; V LIGHT; r SLOW MONSTER (balsa); o CREATE MONSTER (**~10 zaps used this shift; few charges left?**); M MAKE INVISIBLE (0:3); I UNDEAD TURNING (0:3); **v: uncursed STRIKING (ebony, engrave-tested T:7091)**.
- RINGS: H: CURSED ring of teleportation (never wear).
- TOOLS: Q can of grease; u key (unlock box: apply, `.`, y); t whistle (untested); A brass lantern; d blessed oil lamp; CANDLES w (6) + z (1) = 7 for the Candelabrum.
- FOOD: k lichen corpse, T tripe ration, f tin.
- Gems (uncursed, unidentified): R black, X 2 black, Y 2 red, Z yellow, W yellowish brown — good unicorn gifts for Luck.
- Dropped at D13 (18,17) T:7133: cloth spellbook, oil lamp, scroll of light, cursed ring of shock resistance, tin opener. On the altar: cursed copper ring, Uruk-hai shield, orcish helm, 7 elven arrows. (18,18): oil lamp, knife, scroll of destroy armor.
- Escape items: 2 scrolls of teleportation J; wand of sleep x; wand of striking v; Elbereth (not on the altar square); `dig('>')` (pick-axe in bag s); upstairs; PRAYER (timeout 0 verified).
- Healing: none. Emergency cures: stoning → prayer only (no lizard/acid blob corpse).

## Identified appearances (appearance -> identity)
- YUM YUM -> enchant weapon; ANDOVA BEGARIN -> identify; ELAM EBOW -> scare monster (lost); unlabeled -> blank paper; KO BATE -> light; DAIYEN FOOELS -> TELEPORTATION
- KERNOD WEL -> base 80 (enchant armor / remove curse); VERR YED HORRE -> unknown (U); **ELBIB YLOH -> DESTROY ARMOR**; HAPAX LEGOMENON -> base 100 group; scroll of identify: type known
- uranium wand -> create monster; **ebony wand -> STRIKING**; curved wand -> SLEEP; balsa wand -> slow monster; jeweled wand -> FIRE; pine wand -> LIGHT; **iron wand -> MAKE INVISIBLE; forked wand -> UNDEAD TURNING**
- silver ring -> regeneration; copper ring -> unknown (a cursed one left on the D13 altar); agate ring -> base 100 group; steel ring -> shock resistance; **twisted ring -> TELEPORTATION**
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
| 13 | Dungeons | **`<` (74,7)** NE room (70-77,4-8), hidden door (70,6); **`>` (66,16)** SE room (~64-72,12-18); **LAWFUL ALTAR to Tyr (17,18)** in the SW room (9-24,16-20): doors (13,16) N, (19,16) N (dead-end stub (19,15) searched 12), E doorway (24,18), **HIDDEN DOOR (19,20) in the S wall (found T:7125, closed, unexplored beyond → the south-middle)**; hill orc statue (12,19); NW room (3-15,4-8) (chest (6,5) looted: scroll U + copper ring), door (9,8); middle room (40-55,7-12); NW-middle room (24-35,3-9) with an ANTI-MAGIC FIELD (27,7); boulder (21,6) (corridor spur, blocked); dead end (41,6) unsearched. Unexplored: south-middle (x 26-63, rows 13-21) via (19,20), north strip. Wood nymph killed T:6931 (her corpse (14,5)). |

## Pets
- None. The tame djinni was left on D11 (T:6399) and has surely gone untame by now (≈T:7070) — forget it.

## Threats / known dangers
- **POISON RESISTANT since T:7135**: killer bees/soldier ants/spiders are now ordinary melee (still fight swarms at chokepoints — damage adds up). Poisonous corpses are safe food now.
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
- DONE shift 10: D13 NW room + chest; jaguar (eaten), wood nymph (asleep, 1 blow), yellow light, pony, quantum mechanic; create-monster altar camping: fire elemental, 3 Uruk-hai, spotted jelly, iguana, paper golem, acid blob, kobold lord, a 1/23 GROUP (3 wolves, scorpion, raven, imp + a peaceful white unicorn) → Exp 3050 → 3885; POISON RESISTANCE; Luck +2; prayer timeout verified 0; wand of striking; hidden door (19,20).
- NEXT (shift 11):
  1. Rest to full on the altar. Then more create-monster rounds from the altar ONLY at >= 95% HP (a 1/23 zap makes 2–8 monsters; a fire elemental cost 27 HP). Sacrifice LIGHT fresh corpses (< 50 turns): carry them onto the altar and `#offer` (see the offer_carried() pattern in harness notes). Each sacrifice now = Luck +1..+2 and a 1/10 gift chance. Monsters that die ON the altar square can be offered from the floor whatever their weight.
  2. Explore south through the hidden door (19,20) (explore() should now path through it) — the unexplored south-middle.
  3. Throw the 7 unidentified gems at the co-aligned white unicorn whenever it is in a straight line within range (+1 Luck per real gem; `throw(letter, dir, force=True)` because the harness refuses peacefuls in line).
  4. HOLY WATER: the 2 object-detection potions (bag s) → dilute twice at the D12 fountain (12,3) (next to D12's `>` (13,4), i.e. up from D13 `<` (74,7)) → drop the waters on this altar → pray with no trouble (timeout 0 verified; do it only if no sacrifice/prayer has reset it). Maybe first price-ID/read-test U.
  5. XL10 (1235 Exp to go), then descend D14+ at full HP. MR/reflection still missing: Sokoban prize (D6 `<` (4,15)) remains the most reachable reflection source.
- Emergency plan: HP < 40% → Elbereth (step off the altar first) / upstairs / scroll J / sleep wand x; PRAYER IS SAFE NOW (timeout verified 0, Luck > 0) — use it for major trouble (HP < 1/6 max = 18).

## Harness/helper calibration notes
- Verified shift 9: walk_path()/step() refuse to walk into monsters (shopkeeper), farlook shows shop prices, pay(), eat() of shop corpse + pay(), engrave_test(), identify menus via obs.menu pages, altar D/X/. drop + ,/. pickup, fight() inside an engulfer.
- Verified shift 8: `zap()` down a corridor, `fight()` on a sleeper, `fight_until_clear()` in corridors/doorways (radius matters: 4 reported "clear" with orcs at 5–7), `explore()` (hidden passage, stairs, fountain), `avoid()`, altar drop test, `dip()` on a fountain (x2), `pray(force=True)` no-trouble prayer, `cont --reply` for the "Call a clear potion:" prompt, `bag_take` by identified name, `pickup(pattern)`, `#enhance` menu, `go_down(wait_pet=0)` under pressure.
- Verified shift 10: the false Excalibur wield warning is GONE; fight() passive refusal (fire elemental, allow_passive=True for one blow), fight_until_clear() vs a 6-monster group from the altar, throw() in a line, loot_all() auto-unlocking a chest, engrave_test() (striking), bag_put() of 3 potion stacks, eat() of a poisonous corpse, farlook while blind (remembered objects).
- Earlier notes still valid: never call `inventory()`/`here()` unless `obs.kind == 'command'`; `travel()` never autopicks up; pick-one menus close on the letter alone; `obs.menu` lists only the current page.
