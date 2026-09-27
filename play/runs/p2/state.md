# p2 — current state (rewrite as things change)

## Character
- Name/role: p2 — local practice game, seed 202 (lawful female dwarven Valkyrie, god: Tyr)
- Turn / Dlvl / XL / HP / Pw / AC: T:3583 / Dlvl 5 = MINETOWN (Gnomish Mines level 3) / XL5 (Exp 279; XL6 at 320) / 63/63 / 6/6 / AC0
- Position at shift end: (27,11) in the doorway/east side of the long west hall of Minetown (24-28,4-20), command prompt, HP full; acid blob killed. Large cat 3 squares west. In view: peaceful gnomish wizard adjacent (28,12), watchman, shopkeepers; a hostile KOBOLD SHAMAN (weak spellcaster) at (33,16) inside AlliWar's shop area next to the large mimic — kill it when it comes out (melee, one blow).
- Attributes (T:3483): St:17 Dx:12 Co:19 In:11 Wi:8 Ch:9 (Cha 9 → shop prices ×4/3)
- Intrinsics (source, turn): cold res (Valk), stealth (Valk), infravision (dwarf), speed at XL7; EXTRINSIC telepathy from the amulet of ESP (worn T:2424)
- Luck notes: nothing done to Luck (no peacefuls killed by me; the cat killed several peaceful gnomes/a dwarf = no penalty)
- Alignment / god anger notes: never prayed; god not angry.

## Prayer log
| turn | reason | result |
|---|---|---|
| — | none yet (first prayer fine in MAJOR trouble only; lycanthropy counts as major) | — |

## Equipment worn/wielded (letter: item)
- a: EXCALIBUR — blessed rustproof +2 (wielded; obtained T:2422). Two scrolls of enchant weapon (i, j) to read on it after a BUC test (stop at +5)
- c: uncursed +3 small shield (worn)
- y: +0 scale mail (worn since T:1681) [seen]
- E: uncursed +0 high boots (worn) [seen]
- O: uncursed AMULET OF ESP (worn since T:2424) [seen]

## Key inventory (letters) — mark evidence: [seen in inventory] vs [inferred] vs [UNVERIFIED]
- b: blessed +0 dagger — throw it (`throw('b', dir)`); stepping onto it picks it back up [seen]
- h: orcish dagger, unknown B/U/C, quivered — THROW ONLY, never wield [seen]
- m: PICK-AXE (from a dwarf the cat killed on DL6, T:3279), BUC unknown — NEVER carry it into a shop (drop it outside the door); can dig down (escape) and through walls (not in Minetown!) [seen]
- d: LAMP = MAGIC LAMP (e shows as "oil lamp", so a plain "lamp" is the magic one) [inferred, strong] — keep, bless with holy water, then #rub for a wish; do not rub while uncursed/cursed
- e: uncursed oil lamp [seen]
- n: BAG (dropped by the dingo in Minetown, T:3543): sack / oilskin sack / bag of holding / bag of tricks — price-ID (holding/oilskin/tricks base 100, sack 2) or #loot at full HP (a bag of tricks bites) [seen]
- x: curved wand = wand of COLD, FIRE, LIGHTNING or SLEEP (shop price 233 = base 175) [price-ID certain]; charges 4–8 [inferred]; identify at its first zap (bouncing RAYS: never toward the cat or a wall next to me)
- o: wand of create monster (identified T:1046; charges unknown) [seen]
- i, j: 2 scrolls of ENCHANT WEAPON (identified), BUC unknown (i goblin drop, j from a Mines gnome via the cat) — BUC-test on the altar, read on Excalibur if not cursed [seen]
- D: unlabeled scroll = blank paper; J: DAIYEN FOOELS (base-100 group), M: KO BATE (= LIGHT), Q: ELBIB YLOH (base-100 group) [seen]
- V: OVAL AMULET (homunculus death drop, T:2734), unknown — NEVER put on untested (strangulation risk); altar-test, price-ID [seen]
- l: pair of IRON SHOES (AC2, weight 50), BUC unknown — altar-test, then swap for the +0 high boots (AC 0 → -1) if not cursed [seen]
- P: 12 darts, S: knife, U: 6 elven arrows (no bow), K: tin opener [seen]
- Gems: R black gem, X 2 black gems (a DIFFERENT type from R — they didn't stack), W yellowish brown gem, Y red gem, Z yellow gem (all unidentified; sell-price-ID in a shop: worthless glass sells for nothing) [seen]
- T: leathery spellbook, C: dull spellbook — unknown, do NOT read (Int 11); sell (bookshop prices: level-1 books offer 50) [seen]
- F: cyan potion, H: clear potion (= water), I: magenta potion, N: murky potion (base 100 group) — all unknown [seen]
- z: candle, g: (rocks — dropped on DL6), $94
- Escape items: none (upstairs + Elbereth; the wand x may be sleep; the pick-axe can dig down outside Minetown/shops)
- Healing: none known
- Emergency cures: none carried
- Food: ONLY f tin (unknown; tin opener K). Last meal: food ration at T:3433 → next Hungry around T:4230. BUY FOOD in Minetown (food shop / general store) and eat fresh safe corpses (`corpse()`).

## Identified appearances (appearance -> identity)
- YUM YUM -> enchant weapon; ANDOVA BEGARIN -> identify; ELAM EBOW -> scare monster (lost); unlabeled -> blank paper; KO BATE -> light
- KERNOD WEL -> base 80 (enchant armor / remove curse); ELBIB YLOH, DAIYEN FOOELS -> base 100 group; HAPAX LEGOMENON -> base 100 group
- uranium wand -> create monster; curved wand -> base 175 (cold/fire/lightning/sleep)
- silver ring -> regeneration; agate ring -> base 100 group; puce potion -> base 150; murky potion -> base 100
- hexagonal amulet -> ESP; oval amulet -> unknown
- lamp (plain) -> magic lamp [inferred]; oil lamp identified
- vellum spellbook -> level 1; cyan/gold spellbooks -> 533 zm at the D2 bookstore

## Dungeon map
| Dlvl | branch | features (stairs, altars+alignment, shops+type, fountains, stashes, traps, notes) |
|---|---|---|
| 1 | Dungeons | up (8,8); down (10,19); fountains (27,11), (5,18); fully explored |
| 2 | Dungeons | up (40,6); down (21,14) = GNOMISH MINES BRANCH; down (74,17) = main; Kittamagh's bookstore (2-5,17-19) door (6,18); door (28,13) kicked open, boulder at (37,13); boulder (46,9); SE room fountain (59,16), goblin statue (58,16); homunculus corpse (22,14) |
| 3 | Dungeons | up (21,18) under the broken large box (use `travel(21,18)`); down (51,10); SLEEPING GAS TRAP (35,8); vault; elven bow at (61,19) |
| 4 | Dungeons | up (39,18); down (12,18) via hidden passage (8,15); FOUNTAIN (22,17); UPERNAVIK'S GENERAL STORE (69-71,15-17) door (68,16); yellow molds spawn |
| 5 | Dungeons (ORACLE) | up (9,5); down (58,5); Delphi (34-44,8-16), Oracle (39,12) peaceful; fountains left (39,11), (38,12); PIT (14,15); Sokoban entrance = up stairs of D6 |
| 3 (Mines 1) | Gnomish Mines | up (77,13) far east; down (50,13); ARROW TRAP (51,4); narrow cave, peaceful gnome lords |
| 4 (Mines 2) | Gnomish Mines | up (44,10); down (8,10) far west; PIT (65,15); figurine of a green mold (12,9); many peaceful gnomes/dwarves/hobbits, a peaceful monkey (polymorphed gnome) |
| 5 (Mines 3) = MINETOWN | Gnomish Mines | up (74,5) in a small walled room (66-77,3-6) far NE; `#` corridor along row 3 (23-58) and (23,4)-(23,12); DOOR (24,6) (opened) into the town; down (3,6) in the far-west walled room (1-11,4-7) with an ANTI-MAGIC FIELD (9,6) (harmless); west hall (24-28,4-20) with doors (24,6), (24,11); FOUNTAIN (33,12) — NEVER dip/quaff here (Watch); shopkeeper Kilmihil around (30,9) (shop N/NE of the square, unexplored); shopkeeper AlliWar Wickson at (30,15) behind the closed door (30,14) — LARGE MIMIC inside at (30,16) (and another large mimic was at (49,8): `avoid()` set); TEMPLE: priest of ODIN heard (NEUTRAL, cross-aligned — BUC-test only, never sacrifice/convert), location not yet found (east half unexplored); watchmen patrol; peaceful gnomish wizard; SW room (3-11,13-20) with a RED MOLD (6,18) — leave it |
| 6 (Mines 4) | Gnomish Mines | up (45,5); `>` NOT found (x<28 and the SW unexplored); LAND MINE (62,9) now a pit; traps (42,8), (74,18); cave; werejackal killed; dwarvish cloak left at (49,13); potion at (43,8) and a dart (52,12) left; rocks dropped at (50,13); brown mold corpse (64,10) |

## Pets
- LARGE CAT (grew up T:3184 on DL6). Kills peaceful gnomes freely (no penalty to me), steals kills, carries items around, doesn't follow downstairs while eating ("still eating"). Never throw with it in the line of fire (`throw()` now refuses).

## Threats / known dangers
- Werejackals (3 met, all killed). Bite in `d` form = lycanthropy 1/4 per hit → prayer cures (major trouble). Fight them in @ form / at range.
- Large mimics in Minetown shops: never walk into an unexplained object in a shop; telepathy shows them as `m`.
- Molds: yellow (stun), red (fire), green (acid), brown (cold — I'm immune). Acid blobs: harmless unless hit.
- Land mines / pits in the Mines: walk known paths; wounded legs make you Burdened for ~40 turns.
- Watch for: floating eyes (never melee), gas spores, nymphs/leprechauns, soldier ants, dwarves with mattocks (hostile ones).
- Never anger the Watch: no fountain use in town, no door kicking, no theft; never enter a shop with the pick-axe.

## Objective and plan
- DONE this shift: Mines 1–4 explored enough; MINETOWN found at Dlvl 5; magic lamp, pick-axe, iron shoes, bag, 2nd enchant weapon, 5 gems, oval amulet collected; XL5 (Exp 275).
- NEXT (in Minetown, Dlvl 5): (1) explore the town east of the fountain to find the TEMPLE (neutral, Odin) — farlook the priest; (2) drop unknowns on the altar for BUC: scrolls i/j, amulet V, iron shoes l, bag n, lamp d, potions F/I/N, scrolls J/Q, orcish dagger h, pick-axe m (drop the pick-axe before entering any shop); (3) read a non-cursed enchant weapon on Excalibur (+2 → +3 → +4); wear the iron shoes if not cursed; (4) shops: price-ID the bag/lamp/amulet/gems/scrolls/potions with `price_id()`, sell the two spellbooks (C, T) and the worthless glass; (5) BUY FOOD (2+ rations) — Hungry again ~T:4230; (6) note the full layout in this file; (7) then Mines' End only if HP/food are fine, or return to the main dungeon / Sokoban per the orchestrator.
- Minetown temple is cross-aligned (neutral): protection can still be bought from its priest (400×XL = 2000 gold at XL5, have 94 — not now); do not sacrifice there.
- The curved wand x is the emergency weapon (zap in a straight line away from the cat).

## Harness/helper calibration notes
- FIXED since shift 3 (verified this shift where marked): `throw()`/`zap()` refuse with a pet/peaceful in the line (not triggered this shift; `friendly_in_line(dir)` used by hand); pet-vs-monster fight messages no longer pause (verified: cat fights passed silently); "Your housecat is in the way!" → travel waits/retries (verified); `travel()`'s last step avoids the doorway diagonal; stairs under objects come from `#terrain`; `explore()` lists `dead_ends`; `dip()` reports the item line; the monster label follows a grown-up pet (verified: "tame large cat" right after the grow-up); `obs.under` is the glyph.
- STILL OPEN this shift: "Pardon me, <pet>." pauses travel/explore; "You are still in a pit." pauses every turn; a closed door at a corridor end (DL5 (24,6)) is classified as a spellbook → `explore()` spun 400 steps on "That door is closed." (open doors by hand with `o`+dir before exploring through them); the anti-magic-field message isn't a trap event; after "changes into" the werejackal's label was wrong.
- Kernel helpers defined this shift (lost on daemon restart; redefine from the journal if needed): `cat()`, `toward(x,y)`, `occupant(x,y)`, `safe_step(dir)` (refuses to step into any monster), `stairs_with_cat(pos, key)` / `descend_with_cat(pos)`, `wait_and_fight()`, `wait_throw_fight()` (throws b when in line, melee when adjacent), `grab(x,y)` (skips rocks/stones via farlook).
- `obs.objects` calls rocks "gem/rock" too — check `farlook()`'s parenthetical before `,`.
- `explore()` pauses on every "The <pet> kills/bites the gnome" line when the pet hunts peacefuls: budget 1 `cont` per kill.
- `obs.hero` is None while a yes/no getlin prompt is open; scripts that unpack `obs.hero` crash then (harmless, but check `obs.kind == 'command'` first).
- Earlier notes still valid: never call `inventory()`/`here()` unless `obs.kind == 'command'`; `travel()` never autopicks up; plain steps read shop prices, `m`-steps don't; pick-one menus close on the letter alone; sell-probe destroys a picked-up scare monster scroll; `fight()` folds earlier rounds' messages (check `history` for "feverish").
