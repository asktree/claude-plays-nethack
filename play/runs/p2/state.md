# p2 — current state (rewrite as things change)

## Character
- Name/role: p2 — local practice game, seed 202 (lawful female dwarven Valkyrie, god: Tyr)
- Turn / Dlvl / XL / HP / Pw / AC: **T:14052 / D21, standing ON the up stairs (49,15)** / **XL11** (Exp 16066; XL12 at 20000) / 130/131 / 18/18 / **AC -9** / $0 loose (sack n: **~3848 gold** + murky potion = EXTRA HEALING). **Slightly Burdened** (fix first: bag darts P / daggers, or drop junk). Not hungry (lembas eaten T:13651 → Hungry ~T:14250).
- FOOD: in bag i: **5 food rations**, 5 tripe rations, 2 tins, **C-ration**. Carried: p slime mold, G 2 cloves of garlic. **X + J: TWO LIZARD CORPSES (stoning cure — eat one at "You are slowing down"/Stone status).** To eat a ration: `bag_take('i', 'food ration')` (takes the stack) then bag the rest again.
- Attributes: **St:18** Dx:12 Co:19 In:11 Wi:10 Ch:9.
- Skills: long sword EXPERT; #enhance other skills when "more confident" appears.
- Intrinsics (harness knows them): cold res, stealth (Valk + elven cloak), infravision, SPEED, EXTRINSIC telepathy (amulet of ESP O) + INTRINSIC TELEPATHY, POISON RESISTANCE, SEE INVISIBLE (ring B worn, left hand). Excalibur: autosearch + DRAIN RESISTANCE while wielded (a vampire's bite did nothing T:13359). **NO magic resistance, NO reflection, NO fire resistance, NO sleep resistance, NO shock resistance** (2nd gelatinous cube corpse T:13247 gave nothing).
- Luck: 0. Alignment high (many kills).

## Prayer log
| turn | reason | result |
|---|---|---|
| T:6107–6110 | deliberate no-trouble prayer on the D11 lawful altar with 2 waters | SUCCESS, 2 holy water, timeout reset |
| T:10649 | holy-water prayer on the D11 lawful altar (2 waters; cursed worn mithril = minor trouble) | SUCCESS, "well-pleased", 2 HOLY WATER; coat NOT uncursed. Timeout reset. |
- prayer_check() at T:14052: minor trouble (cursed worn coat), **p_safe 1.0** for major trouble (3403 turns since the last prayer). Prayer unused in shifts 18–19 (the emergency button).

## Equipment worn/wielded (letter: item)
- a: EXCALIBUR — blessed rustproof **+6** (wielded). NEVER read enchant weapon on it.
- m: **CURSED** +0 elven mithril-coat (can't be taken off — uncurse with holy water only when a better suit turns up)
- H: +0 faded pall (elven cloak); E: +0 elven leather helm; w: +3 IRON SHOES; c: +3 small shield (very burnt); **Y: +0 leather gloves (D21 sergeant, worn T:14049, not cursed)**; O: amulet of ESP; B: ring of see invisible (left hand).

## Key inventory (letters)
- **TWO BAGS OF HOLDING: i and s (both uncursed). NEVER put one into the other (both explode).** n = plain sack (gold only).
- **BAG s**: pick-axe, **2 HOLY WATER**, potion of HEALING, potion of EXTRA HEALING, potion of water (BUC unknown), **1 uncursed potion of BLINDNESS (puce) = MEDUSA PLAN**, uncursed black + milky potions (unknown), potion of object detection, **5 scrolls of TELEPORTATION** (4 uncursed + 1 unknown BUC from the D19 chest), **SCROLL OF MAGIC MAPPING (uncursed) — SAVE for Medusa/Castle**, **scroll READ ME (unknown, D20)**, 2 ETAOIN SHRDLU (= earth), KIRJE = create monster, blank x2, gems.
- **BAG i**: cursed spherical amulet I (sell; ~95% bad), cursed copper ring T (sell), cursed rings (agate, sapphire, teleportation), wands make invisible, undead turning, slow monster, light, **2 wands of fire (N, Z)**, 7 candles, whistle, **glittering + dark green spellbooks (sell)**, potion of object detection, gems (violet x2, blue x2, white x2, yellowish brown, green...), food (above), brass lantern, blessed oil lamp, grease.
- **L: UNICORN HORN** (uncursed). u: key (`unlock()`).
- THROWING: e blessed +0 dagger, C, D, **F elven dagger (quivered)**; P 4 blessed darts.
- **WANDS carried: R OAK = TELEPORTATION (CURSED, recharged once: 1–7 charges; never recharge again); g, y FIRE; x SLEEP (1–5 left; the ray BOUNCES); q STRIKING (0–4 left); r slow monster; h hexagonal and Q LONG (both engrave "no message": nothing/opening/locking/probing/secret door detection).** Wand v (striking) was empty → dropped on D19.
- RINGS carried: B see invisible (worn); b IRON, uncursed, unknown (not levitation/gain str/con/adornment/protection/invisibility).

## Identified appearances (appearance -> identity)
- Scrolls: YUM YUM enchant weapon; ANDOVA BEGARIN identify; ELAM EBOW scare monster; unlabeled blank; KO BATE light; DAIYEN FOOELS teleportation; KERNOD WEL base 80 (enchant armor / remove curse); ELBIB YLOH destroy armor; ETAOIN SHRDLU = earth (not formally); KIRJE = create monster; FOOBIE BLETCH food detection; STRC PRST SKRZ KRK CHARGING; VERR YED HORRE confuse monster (named); HAPAX LEGOMENON MAGIC MAPPING; **READ ME = unknown**.
- Wands: uranium create monster; ebony striking; curved sleep; balsa slow monster; jeweled FIRE; pine light; iron make invisible; forked undead turning; oak TELEPORTATION; hexagonal + long: no engrave message.
- Rings: silver regeneration; copper unknown (cursed); agate base 100; steel shock resistance; twisted teleportation; bronze SEE INVISIBLE; sapphire, iron unknown.
- Potions: MAGENTA healing; YELLOW speed; cyan gain level; clear water; WHITE paralysis; EFFERVESCENT full healing; golden object detection; EMERALD sleeping; PUCE BLINDNESS; MURKY EXTRA HEALING; purple-red oil; fizzy polymorph; milky, black unknown.
- Amulets: hexagonal ESP; oval unchanging; spherical UNKNOWN (cursed). Faded pall = elven cloak. "bag" = bag of holding (called "holding").

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1–5 | Dungeons | D2 Mines branch (21,14) + SCROLL SHOP; D4 GENERAL STORE; D5 Oracle |
| Mines | Gnomish Mines | Minetown (Dlvl 5): temple of Odin (protection bought), many shops |
| 6 | Dungeons | up (23,15); SOKOBAN `<` (4,15); `>` (41,3). A leprechaun here carries 1635 of my gold. |
| Soko 1–4 | Sokoban | ALL SOLVED. |
| 7–10 | Dungeons | 7: up (33,13) `>` (64,16); 8: up (48,4) `>` (49,16); 9: up (31,19) `>` (43,4); 10 BIG ROOM `<` (16,8) `>` (4,16) |
| 11 | Dungeons | `<` (48,19) `>` (14,19) LAWFUL ALTAR (44,6). QUEST PORTAL LEVEL (portal not found; XL14 + piously needed). |
| 12 | Dungeons | `<` (48,3) land mine (47,4) `>` (13,4); WEAPON SHOP (Carignan): nothing useful. |
| 13 | Dungeons | `<` (74,7) `>` (66,16) LAWFUL ALTAR (17,18) |
| 14 | Dungeons | `<` (17,7) `>` (30,6) **LAWFUL ALTAR (49,6)** (closest altar), fountains (7,11), (19,17). |
| 15 | Dungeons | `<` (23,15) `>` (6,10); rolling boulder trap (9,9). **BARRACKS east (x≈47-50, y 12-19, asleep) — AVOID**. |
| 16 | Dungeons | **ROGUE LEVEL**. `<` (41,2); `>` (20,16); rust trap (18,16); dart trap (39,2). |
| 17 | Dungeons | `<` (13,15), `>` (25,18). Throne room (54-69, 3-4) cleared; throne (56,3) (never sit). Peaceful gnome lord. |
| 18 | Dungeons | `<` (50,15), `>` (45,5). FULLY EXPLORED. Traps: rolling boulder (43,3), dart (13,5), pit (5,14), magic trap (3,17); fountain (5,17). Sleeping mountain nymph (28,7) left alone. Peaceful Aleax. |
| 19 | Dungeons | `<` (31,6), **`>` (68,6)**. Explored (only a boulder-blocked corridor at (26,12) left). Sleeping gas trap (34,15); fountain (40,18); locked door (38,14). A leprechaun still loose. |
| 20 | Dungeons | `<` (46,9); **TRAP DOOR near the door (27,5) (I fell through it T:13638)**; squeaky board (30,6); rock troll wandering; `>` NOT found. Mostly unexplored. |
| 21 | Dungeons | **`<` (49,15), `>` (7,15)**. NOT Medusa (normal rooms). Treasure zoo (68-76, 14-16) CLEARED (peaceful gnome lord + tengu remain). Webs (37,16), (39,16) (large box looted). Gold at (7,11) not taken. Mountain nymph (awake) near (59,9); statue of a floating eye (54,9). Unexplored: parts of the west and south. |

## Threats / known dangers
- Stoning: X + J lizard corpses. Cockatrices: melee only with Excalibur (killed 3 this shift, no hiss landed).
- SOLDIERS/SERGEANTS (two sergeants D21 T:14028–14037, no wands dropped): stay off straight lines, close in fast.
- WAND USERS / BREATHERS: stay off their lines; never zap sleep/fire down a short corridor (bounce).
- GELATINOUS CUBES: mindless (telepathy misses them), never melee — striking wand / daggers.
- LEPRECHAUNS: keep ALL gold in sack n (`bag_put('n','$')` after every pickup).
- NYMPHS: kill asleep with hunt(), or at a doorway chokepoint as they arrive.
- No MR/reflection: must come from silver/gray dragon scales, cloak of MR, shield of reflection, amulet of reflection, wishes, quest.

## Objective and plan
- DONE shift 19: D18 finished, D19 explored, D20 barely (trap door), D21 mostly explored + zoo cleared. Gold ~3848 (protection needs 4400 at XL11 / 4800 at XL12).
- NEXT (shift 20): unburden (bag the darts/daggers or drop junk). Finish D21 (west/south; gold (7,11)), then go UP to D20 via `<` (49,15) and explore D20 (its `>` is unknown; avoid the trap door near (27,5)). Keep looking for MR/reflection and a shop/temple.
- Medusa is at D22–24 (D21 is a filler level). MEDUSA PLAN: magic mapping (bag s) on arrival, quaff the BLINDNESS potion (bag s) before she can see me, fight blind with telepathy; still need a way across water (levitation / cold wand / scroll of earth boulders?). **Don't take D21's `>` until that is solved.**
- Emergency: HP < 40% → Elbereth / potion of healing (bag s) / stairs / scroll of teleportation (bag s). Prayer when `prayer_check()` says major trouble + safe.

## Harness/helper calibration notes
- `monster_filter(lambda m: m['dist'] <= 2 or ...)` keeps explore()/hunt() quiet about far sleepers; zoo sleepers: hunt((x, y)) one at a time in a loop with HP/condition checks worked (10 kills in 2 calls).
- A 1-row throne room / zoo doorway is a perfect chokepoint; fight_until_clear() in a 1-wide corridor or doorway.
- The dungeon overview (`bin/nh info` → overview) names shop TYPES of visited levels.
