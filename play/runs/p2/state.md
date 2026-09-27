# p2 — current state (rewrite as things change)

## Character
- Name/role: p2 — local practice game, seed 202 (lawful female dwarven Valkyrie, god: Tyr)
- Turn / Dlvl / XL / HP / Pw / AC: **T:11747 / D16 = ROGUE LEVEL, corridor (23,4) just east of doorway (22,4)** / **XL11** (Exp 10143; XL12 at 20000) / 103/129 / 18/18 / **AC -1** (orcish helm very rusty) / $24 loose (sack n: **1307 gold** + murky potion). Not hungry (ate a food ration T:11307 → Hungry ~T:12100).
- FOOD: **o 4 food rations** (Rogue ghost's pile), l lembas wafer, p slime mold, k lichen corpse, G 2 cloves of garlic; in bag i: 4 tripe rations, tin. **X LIZARD CORPSE (stoning cure — eat it at "You are slowing down"/Stone status).**
- Attributes: **St:18** Dx:12 Co:19 In:11 Wi:9 Ch:9.
- Skills: long sword EXPERT; #enhance other skills when "more confident" appears.
- Intrinsics (harness knows them): cold res, stealth (Valk + elven cloak), infravision, SPEED, EXTRINSIC telepathy (amulet of ESP O) + INTRINSIC TELEPATHY, POISON RESISTANCE, SEE INVISIBLE (ring B worn, left hand). Excalibur: autosearch + drain resistance while wielded. **NO magic resistance, NO reflection, NO fire resistance, NO sleep resistance.**
- Luck: 0. Alignment high ("well-pleased" at T:10649; +kills since).

## Prayer log
| turn | reason | result |
|---|---|---|
| T:6107–6110 | deliberate no-trouble prayer on the D11 lawful altar with 2 waters | SUCCESS, 2 holy water, timeout reset |
| T:10649 | holy-water prayer on the D11 lawful altar (2 waters; cursed worn mithril = minor trouble) | SUCCESS, "well-pleased", 2 HOLY WATER; coat NOT uncursed. Timeout reset. |
- prayer_check() at T:11118: minor trouble (cursed worn coat), 73%. By ~T:11650+ it should be ~90%+: CHECK prayer_check() before any emergency prayer.

## Equipment worn/wielded (letter: item)
- a: EXCALIBUR — blessed rustproof **+6** (wielded). NEVER read enchant weapon on it.
- m: **CURSED** +0 elven mithril-coat (can't be taken off — uncurse with holy water only when a better suit turns up); q: uncursed +0 elven cloak (burnt); c: +3 small shield (very burnt); E: +0 high boots (very burnt); j: +0 orcish helm (**very rusty**, rust monster D16) — replace when a better helmet turns up; O: amulet of ESP; B: ring of see invisible (left hand).

## Key inventory (letters)
- **TWO BAGS OF HOLDING: i and s (both uncursed). NEVER put one into the other (both explode).** n = plain sack (gold only).
- **BAG s**: pick-axe, **2 HOLY WATER**, potion of HEALING, murky potion, puce potion (base 150), POTION OF OBJECT DETECTION, 2 scrolls of TELEPORTATION, 2 ETAOIN SHRDLU (= earth), scrolls VERR YED HORRE, FOOBIE BLETCH, STRC PRST SKRZ KRK (unknown), KIRJE = create monster, blank x2, ENCHANT WEAPON, gems.
- **BAG i**: cursed rings (agate, sapphire, teleportation), wands make invisible (0:3), undead turning (0:3), slow monster, light, ebony W (striking), 7 candles, whistle, **scroll HAPAX LEGOMENON (new unknown)**, 2nd potion of object detection, blue + white gems, 4 tripe rations, brass lantern, blessed oil lamp, grease, tin.
- **L: UNICORN HORN** (uncursed) — cured raven blindness in 1 apply.
- THROWING: e blessed +0 dagger, C, D (quivered), F elven dagger; P 12 blessed darts.
- **WANDS carried: R OAK = TELEPORTATION (CURSED, 0–3 charges); g, N, y, Z FIRE; x SLEEP (1–5 left; the ray BOUNCES — never zap it toward unknown rock/walls near me); v ebony (striking); r slow monster; h hexagonal (unknown, engrave: no message).**
- RINGS carried: B see invisible (worn); **b IRON, uncursed, unknown**. Unknown potion carried: **Y milky** (D16).
- TOOLS: u key (`unlock()`), L unicorn horn.

## Identified appearances (appearance -> identity)
- Scrolls: YUM YUM enchant weapon; ANDOVA BEGARIN identify; ELAM EBOW scare monster; unlabeled blank; KO BATE light; DAIYEN FOOELS teleportation; KERNOD WEL base 80 (enchant armor / remove curse); ELBIB YLOH destroy armor; ETAOIN SHRDLU = earth (not formally); KIRJE = create monster; VERR YED HORRE, FOOBIE BLETCH, STRC PRST SKRZ KRK, HAPAX LEGOMENON unknown.
- Wands: uranium create monster; ebony striking; curved sleep; balsa slow monster; jeweled FIRE; pine light; iron make invisible; forked undead turning; oak TELEPORTATION; hexagonal: no engrave message.
- Rings: silver regeneration; copper unknown (cursed one left on D13); agate base 100; steel shock resistance; twisted teleportation; bronze SEE INVISIBLE; sapphire, iron unknown.
- Potions: MAGENTA healing; YELLOW speed; cyan gain level; clear water; WHITE paralysis; EFFERVESCENT full healing; golden object detection; EMERALD sleeping; puce base 150; murky base 100; milky unknown.
- Amulets: hexagonal ESP; oval unchanging. Faded pall = elven cloak. "bag" = bag of holding (called "holding").

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1–5 | Dungeons | D2 Mines branch (21,14) + SCROLL SHOP; D4 GENERAL STORE; D5 Oracle |
| Mines | Gnomish Mines | Minetown (Dlvl 5): temple of Odin (protection bought), many shops |
| 6 | Dungeons | up (23,15); SOKOBAN `<` (4,15); `>` (41,3). A leprechaun here carries 1635 of my gold. |
| Soko 1–4 | Sokoban | ALL SOLVED. |
| 7–10 | Dungeons | 7: up (33,13) `>` (64,16); 8: up (48,4) `>` (49,16); 9: up (31,19) `>` (43,4); 10 BIG ROOM `<` (16,8) `>` (4,16) |
| 11 | Dungeons | `<` (48,19) `>` (14,19) LAWFUL ALTAR (44,6). QUEST PORTAL LEVEL (portal not found; XL14 + piously needed). |
| 12 | Dungeons | `<` (48,3) land mine (47,4) `>` (13,4); WEAPON SHOP (Carignan) x57-66 y3-7, door (56,3): nothing useful; buys only weapons/armor. |
| 13 | Dungeons | `<` (74,7) `>` (66,16) LAWFUL ALTAR (17,18) |
| 14 | Dungeons | `<` (17,7) `>` (30,6) **LAWFUL ALTAR (49,6)**, fountains (7,11), (19,17). Explored (boulder (49,13) blocks one corridor). |
| 15 | Dungeons | `<` (23,15) `>` (6,10); rolling boulder trap (9,9). **BARRACKS east (x≈47-50, y 12-19, soldiers + sergeant, asleep) — AVOID** (harness avoid() block set there). |
| 16 | Dungeons | **ROGUE LEVEL**. `<` (41,2); `>` NOT FOUND YET (unexplored: south/east rooms). 3 frost giants killed; **1 frost giant left** (wanders the row-16 corridors), a snake. Ghost pile (30,10): plate mail, bow, arrows, two-handed sword (likely cursed) left. Egg at (17,4) left. |

## Threats / known dangers
- Prayer: check `prayer_check()` first (last prayer T:10649).
- Stoning: X lizard corpse carried. Cockatrices: melee only with Excalibur.
- WAND USERS / BREATHERS / SOLDIERS: stay off their lines; never zap sleep toward nearby unknown rock (bounce).
- YELLOW LIGHTS: kill with one blow as they step adjacent, or at range.
- LEPRECHAUNS: keep ALL gold in sack n (`bag_put('n','$')` after every pickup).
- No MR/reflection: must come from silver/gray dragon scales, cloak of MR, shield of reflection, amulet of reflection, wishes, quest.

## Objective and plan
- NEXT (shift 17):
  1. D16: rest to full on a safe spot, then finish exploring (the 4th frost giant: fight it 1-on-1 in a corridor/doorway — it went down in 2 turns each time), find `>`.
  2. D17+ new levels: look for MR/reflection (dragons, shops, armor), a stethoscope, gold for protection (400×XL = 4400 at XL11; have 1331), better helmet.
  3. Price-ID the 4 unknown scrolls, iron ring b, milky/puce/murky potions at the next general store/scroll shop (none known below D4).
  4. Uncurse the mithril-coat (holy water) only when a better body armor appears. Quest at XL14 + piously (portal on D11). Medusa D21–24 needs reflection or blindness + a water crossing.
- Emergency: HP < 40% → Elbereth / potion of healing (bag s) / stairs / scroll of teleportation (bag s). Prayer only when `prayer_check()` says it's safe.

## Harness/helper calibration notes
- `monster_filter(lambda m: ...)` silences far-away known threats during explore() (used for wandering frost giants).
- fight_until_clear() in a 1-wide corridor killed a frost giant in 2 turns with no damage.
- The dungeon overview (`bin/nh info` → overview) names shop TYPES of visited levels — check it before a shop detour.
