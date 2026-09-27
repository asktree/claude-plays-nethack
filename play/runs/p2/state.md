# p2 — current state (rewrite as things change)

## Character
- Name/role: p2 — local practice game, seed 202 (lawful female dwarven Valkyrie, god: Tyr)
- Turn / Dlvl / XL / HP / Pw / AC: T:3793 / Dlvl 5 = MINETOWN (Gnomish Mines level 3) / XL6 (Exp 348; XL7 at 640) / 62/76 / 7/7 / AC0 / $109
- Position at shift end: (49,13), the square north of the general store door (49,14), east part of the town square; command prompt; HP 62/76; large cat 3 squares south eating a gnome corpse; nothing hostile in view. A harmless fog cloud drifts around the west door (24,11).
- Attributes (T:3483): St:17 Dx:12 Co:19 In:11 Wi:8 Ch:9 (Cha 9 → shop buy prices ×4/3; carry cap 950)
- Skills: long sword SKILLED (enhanced T:3719); next #enhance when "more confident" appears
- Intrinsics (source, turn): cold res (Valk), stealth (Valk), infravision (dwarf), speed at XL7; EXTRINSIC telepathy from the amulet of ESP (worn T:2424)
- Luck notes: nothing done to Luck (no peacefuls killed by me; the cat kills peacefuls/fights watchmen = no penalty to me)
- Alignment / god anger notes: never prayed; god not angry.

## Prayer log
| turn | reason | result |
|---|---|---|
| — | none yet (first prayer fine in MAJOR trouble only; lycanthropy counts as major) | — |

## Equipment worn/wielded (letter: item)
- a: EXCALIBUR — blessed rustproof **+6** (wielded; obtained T:2422; enchanted T:3612–3613). NEVER read another enchant weapon on it (+6 = evaporation risk).
- c: uncursed +3 small shield (worn)
- y: +0 scale mail (worn since T:1681) [seen]
- E: uncursed +0 high boots (worn) [seen] (iron shoes were the same AC 2 — left on the altar)
- O: uncursed AMULET OF ESP (worn since T:2424) [seen]

## Key inventory (letters) — all BUC below is [seen] from the altar test T:3610 unless marked
- b: blessed +0 dagger — throw it (`throw('b', dir)`); stepping onto it picks it back up
- P: 12 BLESSED darts (throw, multishot), U: 7 uncursed elven arrows (no bow), S: uncursed knife
- m: uncursed PICK-AXE — currently INSIDE THE BAG s (shopkeepers only check top-level inventory, so you can enter shops with it bagged); take it out (`a`, `s`, `o`) before digging. Never carry it loose into a shop.
- d: **CURSED MAGIC LAMP** (certain: shows as "lamp" while "oil lamp" is identified; black flash on the altar) — do NOT rub; bless it (holy water) first, then #rub for the wish
- e: uncursed oil lamp; A: brass lantern (bought 16; 1500 turns of light); CANDLES: z uncursed candle + v candle + w 5 tallow candles = 7 (enough for the Candelabrum — keep them, never burn them)
- n: uncursed SACK (identified; empty — the balsa wand was inside)
- s: BAG = **bag of holding or oilskin sack** (bought 133 zm = base 100; opened as a container, so not a bag of tricks) [inferred]; contains the pick-axe. Test later: fill it and compare Burdened thresholds, or identify.
- x: curved wand = **WAND OF SLEEP** (engrave: "bugs stop moving" + shop price base 175 excludes death) [certain]; charges unknown (4–8). Ray: bounces — never zap toward a wall next to me or the cat. Primary emergency tool.
- r: balsa wand = WAND OF SLOW MONSTER (engrave-tested T:3723); charges unknown
- o: wand of create monster (identified T:1046; charges unknown)
- J: uncursed scroll of TELEPORTATION (identified T:3674) — ESCAPE ITEM: read when cornered (random teleport on the level; NOT on no-teleport levels)
- Q: ELBIB YLOH (base-100 group, BUC unknown; never drop-probe it: scare monster turns to dust), M: uncursed KO BATE (= light), D: uncursed unlabeled scroll (blank)
- F: uncursed cyan potion = BASE 300: gain ability / gain level / PARALYSIS (never quaff with monsters near; a 1-in-3 paralysis risk — prefer identify); H: uncursed clear potion (= plain water, not holy); I: uncursed magenta potion = base 100 (healing / extra healing / confusion / hallucination / restore ability / sleeping); N: uncursed murky potion (base 100 group)
- q: 2 FOOD RATIONS (bought T:3667), f: uncursed tin (unknown; tin opener K)
- u: key (= skeleton key; unlocks doors/boxes), t: tin whistle (junk). Sold: amulet of unchanging (75, T:3789).
- Gems (all uncursed, unidentified; NOTE: 3.6 shopkeepers pay fake prices for unidentified gems, so sell-price-ID of gems does NOT work): R black gem, X 2 black gems (different type from R), W yellowish brown gem, Y red gem, Z yellow gem
- Escape items: scroll of teleportation J; wand of sleep x; upstairs + Elbereth; pick-axe (dig down) outside Minetown/shops
- Healing: none known
- Emergency cures: none carried
- Food: 2 food rations + tin. Last meal: food ration at T:3433 → next Hungry around T:4230. Eat fresh safe corpses (`corpse()`) when Hungry, keep the rations.
- Left on the Minetown altar (38,9): uncursed iron shoes, cursed orcish dagger.

## Identified appearances (appearance -> identity)
- YUM YUM -> enchant weapon; ANDOVA BEGARIN -> identify; ELAM EBOW -> scare monster (lost); unlabeled -> blank paper; KO BATE -> light; DAIYEN FOOELS -> TELEPORTATION
- KERNOD WEL -> base 80 (enchant armor / remove curse); ELBIB YLOH -> base 100 group; HAPAX LEGOMENON -> base 100 group
- uranium wand -> create monster; curved wand -> SLEEP; balsa wand -> slow monster
- silver ring -> regeneration; agate ring -> base 100 group; puce potion -> base 150; murky potion -> base 100
- hexagonal amulet -> ESP; oval amulet -> unchanging
- lamp (plain) -> magic lamp; oil lamp identified; "bag" -> sack identified (n); the other "bag" (s) = holding/oilskin
- vellum spellbook -> level 1; dull spellbook -> level 4 (sold 200); leathery spellbook -> level 3 (or 4; sold 150); cyan/gold spellbooks -> 533 zm at the D2 bookstore

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
| 5 (Mines 3) = MINETOWN | Gnomish Mines | up (74,5) in a small walled room (66-77,3-6) far NE; `#` corridor along row 3 (23-58) and (23,4)-(23,12); down (3,6) in the far-west walled room (1-11,4-7) with an ANTI-MAGIC FIELD (9,6); west hall (24-28,4-20) doors (24,6), (24,11); TOWN SQUARE x 25-44, y 11-14 with FOUNTAINS (33,12), (43,12) — NEVER dip/quaff; **TEMPLE of ODIN (NEUTRAL, cross-aligned)**: room (36-40,8-11), door (37,12) south wall, ALTAR (38,9), priest peaceful — BUC-test only, never sacrifice/pray/convert; **Kilmihil's RARE BOOKS** (29-31,7-9) door (29,10) — 5 spellbooks left (unpriced; cyan/gold types cost 533 elsewhere); **AlliWar Wickson's HARDWARE STORE** (29-31,15-17) door (30,14) — 2 leashes left; **LARGE MIMIC disguised at (30,16)** (centre square: never step on it, never `s` next to it; disguised mimics don't act); **Pasawahan's DELICATESSEN** (36-38,16-17) door (39,17) (east wall) — cream pie 13, fortune cookie 9 left; sealed closet (32-34,16-17) holds 2 kobold shamans + 2 kittens (hostile, can't get out, ignore); N-S passage x=40 (14-19) with closed door (41,17) east; **Izchak's LIGHTING STORE** (47-49,7-9) door (49,10) — left: 5 wax candles 180, 2 tools at (47,7)/(47,8) unpriced; its large mimic (49,8) is DEAD; **Ouiatchouane's GENERAL STORE** (48-50,15-17) door (49,14) — stock: 8 elven arrows 24 at (50,16), a RING (48,17), a SCROLL (49,17), a tool (48,16), a weapon (50,17) — unpriced (check next visit; buys anything, use it for sell-probes); small structure (43-46,7-9) door (45,9) and closed door (45,14) not entered; x>55 east of the square unexplored except the corridor to the `<`; watch captain patrols the south side (29-46,18-19); SW room (3-11,13-20) with a RED MOLD (6,18); Elbereth engraved in the dust at (30,11) |
| 6 (Mines 4) | Gnomish Mines | up (45,5); `>` NOT found (x<28 and the SW unexplored); LAND MINE (62,9) now a pit; traps (42,8), (74,18); cave; werejackal killed; dwarvish cloak left at (49,13); potion at (43,8) and a dart (52,12) left; rocks dropped at (50,13); brown mold corpse (64,10) |

## Pets
- LARGE CAT. Kills peaceful gnomes freely (no penalty to me), picks fights with WATCHMEN (they fight back with swords/spears; no penalty to me so far, but it may die), steals kills, picks up and carries items (took the pick-axe once, dropped it 1 square away), doesn't follow downstairs while eating. Never throw with it in the line of fire (`throw()` refuses).

## Threats / known dangers
- Werejackals (3 met, all killed). Bite in `d` form = lycanthropy 1/4 per hit → prayer cures (major trouble). Fight them in @ form / at range.
- Large mimic in the hardware store (30,16), still disguised: disguised mimics never move or attack (mon.c movemon skips them); stepping into it, searching next to it, OR THE CAT ATTACKING IT wakes it (that happened at Izchak's: it grabbed me, 11 damage, but died to one +6 Excalibur blow). At XL6 with Excalibur it is killable (level 8, 3d4, speed 3); keep the cat away from disguised mimics or accept the fight at full HP.
- Molds: yellow (stun), red (fire), green (acid), brown (cold — I'm immune). Acid blobs: harmless unless hit.
- Land mines / pits in the Mines: walk known paths; wounded legs make you Burdened for ~40 turns.
- Watch for: floating eyes (never melee), gas spores, nymphs/leprechauns, soldier ants, dwarves with mattocks (hostile ones).
- Never anger the Watch: no fountain use in town, no door kicking, no theft; never enter a shop with the pick-axe.
- Mines' End is ~5 levels deeper (Dlvl 10–11): NOT at XL5 (playbook: XL10+).

## Objective and plan
- DONE shift 5: temple + altar found and used (BUC of everything), Excalibur +6, both spellbooks sold (350), identify scroll bought and read (amulet of unchanging, sack, scroll of teleportation), 2 food rations bought, bag (holding/oilskin) + skeleton key bought, wands engrave-IDed (sleep, slow monster), long sword Skilled, all 5 shops located, 7 candles + brass lantern bought, XL6 (large mimic kill), potions F/I price-grouped, amulet sold.
- NEXT: (1) optional: price the general store's ring/scroll (48,17)/(49,17) ($109; a cheap ring could be worth it), peek through (45,9)/(45,14); (2) then leave the Mines: back up to D2 (`<` at (74,5) NE room here, then Mines 2 `<` (44,10), Mines 1 `<` (77,13)), main dungeon D5 → D6 and SOKOBAN (up stairs of D6) for the prize (bag of holding / amulet of reflection) and XP; (3) Mines' End only at XL10+; (4) get holy water (or a co-aligned altar + water) to bless the magic lamp, then #rub for a wish.
- Protection: 400×XL gold (2000 at XL5, 2400 at XL6) from the Minetown priest — cross-aligned priests still sell protection; not affordable yet ($133).
- Emergency plan: HP < 40% → wand of sleep x at the attacker (never toward the cat/an adjacent wall), or read the scroll of teleportation J, or Elbereth; upstairs (74,5) is far NE.

## Harness/helper calibration notes
- Verified this shift: the peaceful-step guard (#378) refused steps into Pasawahan/AlliWar/Kilmihil cleanly; `price_id(sell=)`/`(buy=)` lookups correct; the yn "offers ... Sell it?" prompt classified right; the identify menu and drop/pickup menus parsed fine (`obs.menu` lists only the current page: use `>` for page 2); `engrave_test()` verdicts good; `fight_until_clear()` fine.
- OPEN: `bin/nh cont` after a *message* pause inside `travel()`'s peaceful-wait loop returns from travel() without moving (#15, #124) — use the kernel `go(x,y)` wrapper (re-issues travel until arrival; lost on daemon restart, redefine: `for i in range(4): if look().hero==(x,y): break; travel(x,y)`).
- `explore()` in Minetown walks into shop doorways while carrying the pick-axe (Kilmihil blocks; harmless but it stalls) — explore by `travel()` to targets instead, or drop the pick-axe first.
- `loot_all()` only handles floor containers; a carried bag needs `a` + letter → "Do what with your bag?" → `o` → item menu → `<CR>`.
- Paying with several shopkeepers nearby opens NetHack's "Pay whom?" getpos: move the cursor with hjkl onto the shopkeeper and press `.`.
- `move_to()` helpers must wait with `.`, never `s` (searching next to the disguised mimic reveals it).
- Kernel helpers defined this shift (lost on daemon restart): `go(x,y)`, `move_to(tgt,key)`, `pick_here()`, `pay(name)`, `shk_pos(name)`, `clear_adjacent()`.
- Earlier notes still valid: never call `inventory()`/`here()` unless `obs.kind == 'command'`; `travel()` never autopicks up; plain steps read shop prices, `m`-steps don't; pick-one menus close on the letter alone; sell-probe destroys a picked-up scare monster scroll; `fight()` folds earlier rounds' messages (check `history` for "feverish"); `obs.objects` calls rocks "gem/rock" too.
