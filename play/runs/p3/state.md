# p3 — current state (rewrite as things change)

## Character
- Name/role: P3, lawful female dwarven Valkyrie, god: Tyr (local practice game, seed 303)
- Turn / Dlvl / XL / HP / Pw / AC: T:4718 / D7 MAIN DUNGEON (Dungeons of Doom 7) at (15,10), near the up stairs (4,14) / XL6 (Exp 423; XL7 at 640) / 73/73 / 12/12 / AC-3
- Attributes: St17 Dx12 Co19 In9 Wi9 Ch10 (Ch10 = shop prices x4/3)
- Intrinsics (source, turn): cold res (Valk), stealth (Valk), infravision (dwarf); VERY FAST from speed boots (T:4348); intrinsic speed at XL7. NOT poison resistant. Excalibur gives auto-search while wielded.
- Luck notes: none known (assume 0)
- Alignment / god anger notes: none; never prayed; no hypocrite/peaceful kills by me (the DOG killed ~4 peaceful gnomes: no penalty to me)
- Skills: long sword SKILLED (T:3435), dagger Basic
- Hunger: ate a food ration at T:4696 (next Hungry ~T:5450)

## Prayer log
| turn | reason | result |
|---|---|---|
| (none yet) | | prayer timeout surely 0 (T:3753): first prayer safe in MAJOR trouble (HP<=9 at max 63 (1/7), or Weak) |

## Equipment worn/wielded (letter: item)
- a: the blessed rustproof +2 Excalibur (wielded; enchant weapon read T:3772)
- b: uncursed +0 dagger (alternate; `x` swaps)
- c: uncursed +4 small shield (enchant armor landed on it T:4352). At +4 another enchant armor on it EVAPORATES it 3 times in 4: TAKE THE SHIELD OFF before reading enchant armor
- m: uncursed +0 orcish helm (uncursed by remove curse T:4350)
- M: +0 splint mail (bought D4 Fleac 107zm, T:4199; BUC unknown, not cursed-known)
- O: +0 faded pall = ELVEN CLOAK (bought D2 Ermenak 107zm)
- P: -1 SPEED BOOTS (the D2 "mud boots", 67zm; very fast)
- no gloves (the D2 riding gloves were GAUNTLETS OF FUMBLING: cursed -1; returned)

## Key inventory (letters)
- Food: D: 1 uncursed food ration; Q: 2 food rations (D5 box); E: uncursed cram ration (never rots); e: 1 uncursed candy bar (~3100 nutrition). Food rations are old: 1/7 rotten chance — eat on a safe square (Elbereth)
- Ranged: l: 7 uncursed +0 darts; B: 5 CURSED -1 daggers (throw only)
- Scrolls: V: REMOVE CURSE (D7 floor, BUC unknown) = the reserve again; X: IDENTIFY (D7 floor, BUC unknown; save it for Sokoban rings/wands); p: uncursed STINKING CLOUD; R: stinking cloud (BUC unknown)
- Potions: w: blessed potion of OIL; I: uncursed orange potion (unknown); U: swirly potion (unknown, D5)
- Books/gems found: S: tan spellbook (unknown; don't read at In9 — sell/price-ID); T: violet gem (amethyst 600 or glass)
- Rings: k: uncursed RING OF TELEPORT CONTROL (keep!)
- Tools: h: blindfold; o: tin whistle; s: credit card; v: skeleton key; L: oil lamp (Izchak 13zm; w = blessed oil refills it)
- Gems: g: 2 worthless yellow glass; t: worthless green glass; x: worthless black glass (junk)
- Gold: $904 (no bag: a leprechaun would take it all). Protection = 400*XL = 2400 at XL6 — out of reach for now

## Identified appearances
- scrolls: ELBIB YLOH = identify; ZLORFIK = light; KO BATE = enchant weapon (price); GNIK SISI VLE = remove curse; KERNOD WEL = enchant armor; ETAOIN SHRDLU = stinking cloud
- potions: puce = oil; rings: ivory = teleport control; whistle = tin
- Price rules: being HUNGRY doubles food prices (Weak x3). Wonotobo lowballs unID'd items (offers 3/8 base; fixed per shopkeeper, shk.c set_cost `!(shkp->m_id % 4)`). A shopkeeper pays at most the cash he holds (Wonotobo paid 1054 for the black opal).
- IDENTIFIED BY WEARING: mud boots = SPEED BOOTS; riding gloves = GAUNTLETS OF FUMBLING; faded pall = elven cloak. D2 Ermenak still has: plate mail (71,14) (~800zm), bronze plate 533, combat boots 53 (base 30: fumble/levitation), jungle boots 11, orcish cloak, chain/banded/scale mails; a 'dented pot' lies outside at (63,16)
- D4 Fleac's weapon shop: 1 more splint mail 107, ring mail 133, conical hat 142 (= cornuthaum by price; useless)

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1 | Dungeons | up (43,18), down (57,6); FOUNTAIN (19,3); hole (14,6); magic trap (16,17) |
| 2 | Dungeons | up (53,3), down (36,14); fountain gone (Excalibur); Ermenak's used armor shop (69-73,12-16), door (68,16) |
| 3 | Dungeons | up (45,18) with RED MOLD (44,18) beside it (leave/enter the stair room by the doorless west doorway (43,18) diagonally — the route planner won't); down (47,9) with YELLOW MOLD (48,8). East half unexplored |
| 4 | Dungeons | up (22,5), down (60,8); MINES stairs (70,5) (room behind broken door (66,6)); TELEPORT TRAP (69,5) beside the Mines stairs; locked door (22,6). Fleac's weapon shop (71-76,17-19), door (70,18) |
| 5 | Dungeons | up (13,8), down (76,6); fountain (74,5); large box at (63,4) LOOTED (gold, 2 rations, stinking cloud, spellbook, violet gem); another LARGE BOX at (6,8) near the up stairs (not looted); exploded booby-trapped door (72,6). Not the Oracle |
| 6 | Dungeons | up (8,6), down (9,16) (room (4-12,13-17)); banded mail (12,13); @ statue (20,7). Corridors cross the map centre: NOT the Oracle |
| 7 | Dungeons | up (4,14); partly explored (rooms NW/W, a room at (21-31,2-5), a room east of (20,10)); Oracle not yet seen — the map centre is unexplored |
| 5 | Mines 1 | up (28,3) (yellow mold (27,4)), down (60,13). Traps: sleeping gas (27,11), (48,3); falling rock (12,17); magic trap (42,10); pit (21,3) |
| 6 | Mines 2 | up (8,6), down (54,7). Traps: sleeping gas (21,12), dart (11,18) |
| 7 | Mines 3 = MINETOWN (Grotto Town) | up (3,2); down (48,4) (wiki map, not yet seen); TEMPLE of ODIN (neutral, cross-aligned), priestess, altar (33,4), door (33,6), west wall dug open by a dwarf; Wonotobo's GENERAL STORE (61-69,10-11), door (68,9) (obsidian 356; my sold potions/scrolls); DELI (7-10,10-11) door (9,12); STEWE's TOOL shop (59-62,14-16) door (58,15): lock picks, oil lamps, crystal ball, mirror, tin whistle — no bag/marker; IZCHAK's lighting shop (27-30,18-20) door (26,19): oil lamps 13/18, tallow 13, wax 27/36 (buy 7 candles later); fountains (52,10), (12,16). Wiki: bottom-right closet has a chest; the room above it has a secret closet with a ring |
- Screen coords from the wiki Grotto Town map: screen x = wiki line index + 1 (with its leading space), screen y = wiki line - 138.

## Pets
- none with me: the little dog was left in Minetown (D7) at T:4040 (it wandered off in the dark)

## Threats / known dangers
- Orc packs roam Minetown (killed 3 Uruk-hai + 3 hill orcs at T:3715-3732; one THREW A SLEEPING POTION at me — I slept a few turns).
- Giant bats: speed 22, two bites a turn. D3 molds next to both staircases: never melee.
- Minetown watch: no fountain quaffing/dipping, no door kicking, no theft.

## Objective and plan
- DONE shift 4: altar test, Excalibur +2, splint mail, elven cloak, SPEED BOOTS, shield +4, XL6. AC5 -> AC-3.
- NEXT: Sokoban. Continue exploring D7 main (centre unexplored) — then D8, D9 — until the Oracle (centaur statues/fountains, D5-9); the level BELOW the Oracle has a 2nd UP staircase = Sokoban. Run sokoban.solve() there. Reason: prize (bag of holding or amulet of reflection), wands/rings on Soko 1, safe XP; the lower Mines (Mines' End) is for XL10+.
- Keep: eat when Hungry (food rations on safe squares; cram E never rots). No remove curse in reserve now: be careful with unknown armor/rings.
- Later: return to Minetown with 2400+ gold for protection (priestess of Odin, cross-aligned OK), and buy 7 candles at Izchak's.
