# p3 — current state (rewrite as things change)

## Character
- Name/role: P3, lawful female dwarven Valkyrie, god: Tyr (local practice game, seed 303)
- Turn / Dlvl / XL / HP / Pw / AC: T:3753 / D7 = MINETOWN (Grotto Town), at (36,17) south-centre of town (orc fight site) / XL5 (Exp 299; XL6 at 320) / 37/63 / 9/9 / AC5
- Attributes: St17 Dx12 Co19 In9 Wi9 Ch10 (Ch10 = shop prices x4/3)
- Intrinsics (source, turn): cold res (Valk), stealth (Valk), infravision (dwarf); speed at XL7. NOT poison resistant. Excalibur gives auto-search while wielded.
- Luck notes: none known (assume 0)
- Alignment / god anger notes: none; never prayed; no hypocrite/peaceful kills by me (the DOG killed ~4 peaceful gnomes: no penalty to me)
- Skills: long sword SKILLED (T:3435), dagger Basic
- Hunger: ate a hill orc corpse at T:3753 (not hungry)

## Prayer log
| turn | reason | result |
|---|---|---|
| (none yet) | | prayer timeout surely 0 (T:3753): first prayer safe in MAJOR trouble (HP<=9 at max 63 (1/7), or Weak) |

## Equipment worn/wielded (letter: item)
- a: the blessed rustproof +1 Excalibur (wielded)
- b: uncursed +0 dagger (alternate; `x` swaps)
- c: uncursed +3 small shield (worn)
- m: CURSED +0 orcish helm (worn; identified T:3659) — can't take it off; z (remove curse) or i (enchant armor, if it lands on the helm) would uncurse it
- NO body armor, no cloak/gloves; H: iron shoes (AC2) carried, BUC UNKNOWN (Uruk-hai drop) — altar-test before wearing

## Key inventory (letters)
- Food: D: 2 uncursed food rations; G: 1 food ration (BUC unknown, shop); E: uncursed cram ration; e: 1 uncursed candy bar (~2900 nutrition in all). Food rations are old: 1/7 rotten chance — eat on a safe square
- Ranged: l: 7 uncursed +0 darts; B: 5 CURSED -1 daggers (throw only)
- Scrolls: F: KO BATE = ENCHANT WEAPON (bought 80zm; BUC UNKNOWN — altar-test, then read with Excalibur wielded); i: uncursed ENCHANT ARMOR (hold until more armor is worn; small shield is +3: a 4th + could evaporate it only above +3); z: uncursed REMOVE CURSE (reserve); p: uncursed STINKING CLOUD
- Potions: w: blessed potion of OIL; I: orange potion (unknown, Uruk-hai drop)
- Rings: k: uncursed RING OF TELEPORT CONTROL (keep!)
- Tools: h: blindfold; o: tin whistle (calls the pet within ~10 squares); s: credit card; v: skeleton key
- Gems: g: 2 worthless yellow glass; t: worthless green glass; x: worthless black glass (junk)
- Gold: $953 (no bag: a leprechaun would take it all — spend it on armor soon)

## Identified appearances
- scrolls: ELBIB YLOH = identify; ZLORFIK = light; KO BATE = enchant weapon (price); GNIK SISI VLE = remove curse; KERNOD WEL = enchant armor; ETAOIN SHRDLU = stinking cloud
- potions: puce = oil; rings: ivory = teleport control; whistle = tin
- Price rules: being HUNGRY doubles food prices (Weak x3). Wonotobo lowballs unID'd items (offers 3/8 base; fixed per shopkeeper, shk.c set_cost `!(shkp->m_id % 4)`). A shopkeeper pays at most the cash he holds (Wonotobo paid 1054 for the black opal).
- D2 Ermenak armor: faded pall 107zm = ELVEN CLOAK (fixed appearance); riding gloves 67 = base 50 (GoP/GoDex/FUMBLING); mud boots 67 = base 50 (SPEED/water walking/jumping); combat boots 53; jungle boots 11 (elven/kicking)
- D4 Fleac's weapon shop: 2 SPLINT MAILS (AC6, base 80 -> ~107-142zm), ring mail (AC3)

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1 | Dungeons | up (43,18), down (57,6); FOUNTAIN (19,3); hole (14,6); magic trap (16,17) |
| 2 | Dungeons | up (53,3), down (36,14); fountain gone (Excalibur); Ermenak's used armor shop (69-73,12-16), door (68,16) |
| 3 | Dungeons | up (45,18) with RED MOLD (44,18) beside it (leave/enter the stair room by the doorless west doorway (43,18) diagonally — the route planner won't); down (47,9) with YELLOW MOLD (48,8). East half unexplored |
| 4 | Dungeons | up (22,5), down (60,8); MINES stairs (70,5) (room behind broken door (66,6)). Fleac's weapon shop (71-76,17-19), door (70,18) |
| 5 | Mines 1 | up (28,3) (yellow mold (27,4)), down (60,13). Traps: sleeping gas (27,11), (48,3); falling rock (12,17); magic trap (42,10); pit (21,3) |
| 6 | Mines 2 | up (8,6), down (54,7). Traps: sleeping gas (21,12), dart (11,18) |
| 7 | Mines 3 = MINETOWN (Grotto Town) | up (3,2); down (48,4) (wiki map, not yet seen); TEMPLE of ODIN (neutral, cross-aligned), priestess, altar (33,4), door (33,6); Wonotobo's GENERAL STORE (61-69,10-11), door (68,9) (obsidian 356; my sold potions/scrolls); DELI (7-10,10-11) door (9,12); TOOL shop door (58,15); IZCHAK's lighting shop door (26,19); fountains (52,10), (12,16). Wiki: bottom-right closet has a chest; the room above it has a secret closet with a ring |
- Screen coords from the wiki Grotto Town map: screen x = wiki line index + 1 (with its leading space), screen y = wiki line - 138.

## Pets
- tame little dog, with me in Minetown (kills peaceful gnomes; picks up shop gems)

## Threats / known dangers
- Orc packs roam Minetown (killed 3 Uruk-hai + 3 hill orcs at T:3715-3732; one THREW A SLEEPING POTION at me — I slept a few turns).
- Giant bats: speed 22, two bites a turn. D3 molds next to both staircases: never melee.
- Minetown watch: no fountain quaffing/dipping, no door kicking, no theft.

## Objective and plan
- DONE: XL5, Excalibur, Minetown, altar BUC test, full identify, food (~2900 nutrition), $953.
- Next shift: (1) rest to full HP (Elbereth/quiet corner; HP 37/63); (2) altar (33,4): drop F (enchant weapon), G, H (iron shoes), I — then read F on Excalibur if not cursed, wear H if not cursed (AC5 -> 3); (3) spend the gold on AC before a leprechaun gets it: D4 Fleac's SPLINT MAIL (AC6, ~107-142) and D2 Ermenak's elven cloak (107) + mud boots (1/3 speed; altar/pet-test first); (4) protection from the priestess needs 400*XL (2000 at XL5, 2400 at XL6) — not yet; (5) then Sokoban (up stairs of the level below the Oracle, D5-9 main dungeon) or deeper Mines.
