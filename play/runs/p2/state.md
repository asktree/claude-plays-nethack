# p2 — current state (rewrite as things change)

## Character
- Name/role: p2 — local practice game, seed 202 (lawful female dwarven Valkyrie, god: Tyr)
- Turn / Dlvl / XL / HP / Pw / AC: **T:13120 / D18, standing ON the up stairs (50,15)** / **XL11** (Exp 13401; XL12 at 20000) / 131/131 / 18/18 / **AC -8** / $0 loose (sack n: **1443 gold** + murky potion = EXTRA HEALING). Not hungry (ate a food ration T:12820 → Hungry ~T:13600).
- FOOD: in bag i: **5 food rations**, 5 tripe rations, 2 tins. Carried: l lembas wafer, p slime mold, k lichen corpse, G 2 cloves of garlic. **X LIZARD CORPSE (stoning cure — eat it at "You are slowing down"/Stone status).** To eat a ration: `bag_take('i', 'food ration')` first.
- Attributes: **St:18** Dx:12 Co:19 In:11 Wi:9 Ch:9.
- Skills: long sword EXPERT; #enhance other skills when "more confident" appears.
- Intrinsics (harness knows them): cold res, stealth (Valk + elven cloak), infravision, SPEED, EXTRINSIC telepathy (amulet of ESP O) + INTRINSIC TELEPATHY, POISON RESISTANCE, SEE INVISIBLE (ring B worn, left hand). Excalibur: autosearch + drain resistance while wielded. **NO magic resistance, NO reflection, NO fire resistance, NO sleep resistance, NO shock resistance** (gelatinous cube corpse T:12206 gave nothing).
- Luck: 0. Alignment high ("well-pleased" at T:10649; many kills since).

## Prayer log
| turn | reason | result |
|---|---|---|
| T:6107–6110 | deliberate no-trouble prayer on the D11 lawful altar with 2 waters | SUCCESS, 2 holy water, timeout reset |
| T:10649 | holy-water prayer on the D11 lawful altar (2 waters; cursed worn mithril = minor trouble) | SUCCESS, "well-pleased", 2 HOLY WATER; coat NOT uncursed. Timeout reset. |
- prayer_check() at T:13120: minor trouble (cursed worn coat), **p_safe 0.998** for major trouble (2471 turns since the last prayer). Prayer NOT used in shift 18 (kept as the emergency button).

## Equipment worn/wielded (letter: item)
- a: EXCALIBUR — blessed rustproof **+6** (wielded). NEVER read enchant weapon on it.
- m: **CURSED** +0 elven mithril-coat (can't be taken off — uncurse with holy water only when a better suit turns up)
- H: **+0 faded pall (elven cloak), BUC unknown** (from a Green-elf, D17) — replaced the burnt one
- E: **+0 elven leather helm, BUC unknown** (Green-elf, D17) — replaced the thoroughly rusty orcish helm
- w: **+3 IRON SHOES, BUC unknown** (floor, D16 (65,20)) — replaced the very burnt high boots
- c: +3 small shield (very burnt); O: amulet of ESP; B: ring of see invisible (left hand).
- (Everything BUC-unknown above was put on voluntarily: if one turns out cursed it is minor trouble; holy water fixes it.)

## Key inventory (letters)
- **TWO BAGS OF HOLDING: i and s (both uncursed). NEVER put one into the other (both explode).** n = plain sack (gold only).
- **Y: 1 uncursed scroll of MAGIC MAPPING** (carried) — SAVE for Medusa's level / the Castle.
- **BAG s**: pick-axe, **2 HOLY WATER**, potion of HEALING, **potion of EXTRA HEALING (D18)**, **potion of water (D18, BUC unknown)**, **1 uncursed potion of BLINDNESS (puce) = MEDUSA PLAN (quaff before her level: blind 250–450 turns, telepathy shows her; unicorn horn cures)**, uncursed **black potion** and **milky potion** (unknown; dilution fodder / quaff-test), potion of object detection (uncursed), **4 scrolls of TELEPORTATION (uncursed)**, 2 ETAOIN SHRDLU (uncursed, = earth), KIRJE = create monster, blank x2, gems.
- **BAG i**: **cursed spherical amulet I (NOT to wear: ~95% strangulation/sleep/change; sell)**, **cursed copper ring T (sell)**, cursed rings (agate, sapphire, teleportation), wands make invisible (0:3), undead turning (0:3), slow monster, light, striking (q, uncursed, 2nd), 7 candles, whistle, **uncursed glittering spellbook (to sell)**, potion of object detection, gems (+ violet gem D18), 5 food rations, 5 tripe, 2 tins, brass lantern, blessed oil lamp, grease.
- **L: UNICORN HORN** (uncursed).
- THROWING: e blessed +0 dagger, C, D (quivered), F elven dagger; P 12 blessed darts.
- **WANDS carried: R OAK = TELEPORTATION (CURSED: 1% backfire per zap; RECHARGED ONCE T:12583 → 1–7 charges; never recharge it again); g, N, y, Z FIRE; x SLEEP (1–5 left; the ray BOUNCES); v STRIKING (3 used on the gelatinous cube T:12191, charges unknown); r slow monster; h hexagonal (unknown, engrave: no message).**
- RINGS carried: B see invisible (worn); **b IRON, uncursed, unknown** (wear-test T:12587: no message, no St/Co/Ch/AC change → not levitation/gain str/con/adornment/protection/invisibility).
- TOOLS: u key (`unlock()`), L unicorn horn.

## Identified appearances (appearance -> identity)
- Scrolls: YUM YUM enchant weapon; ANDOVA BEGARIN identify; ELAM EBOW scare monster; unlabeled blank; KO BATE light; DAIYEN FOOELS teleportation; KERNOD WEL base 80 (enchant armor / remove curse); ELBIB YLOH destroy armor; ETAOIN SHRDLU = earth (not formally); KIRJE = create monster; **FOOBIE BLETCH food detection; STRC PRST SKRZ KRK CHARGING; VERR YED HORRE confuse monster (named); HAPAX LEGOMENON MAGIC MAPPING** (all T:12582–12584). Still unknown types: the other of enchant armor/remove curse, fire, gold detection, amnesia, genocide, punishment, stinking cloud, taming.
- Wands: uranium create monster; ebony striking; curved sleep; balsa slow monster; jeweled FIRE; pine light; iron make invisible; forked undead turning; oak TELEPORTATION; hexagonal: no engrave message.
- Rings: silver regeneration; copper unknown (cursed one left on D13; another in bag i); agate base 100; steel shock resistance; twisted teleportation; bronze SEE INVISIBLE; sapphire, iron unknown.
- Potions: MAGENTA healing; YELLOW speed; cyan gain level; clear water; WHITE paralysis; EFFERVESCENT full healing; golden object detection; EMERALD sleeping; **PUCE BLINDNESS; MURKY EXTRA HEALING**; purple-red oil; fizzy polymorph; milky, black unknown.
- Amulets: hexagonal ESP; oval unchanging; spherical UNKNOWN (I, CURSED → almost surely strangulation/restful sleep/change). Faded pall = elven cloak. "bag" = bag of holding (called "holding").

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1–5 | Dungeons | D2 Mines branch (21,14) + SCROLL SHOP; D4 GENERAL STORE; D5 Oracle |
| Mines | Gnomish Mines | Minetown (Dlvl 5): temple of Odin (protection bought), many shops |
| 6 | Dungeons | up (23,15); SOKOBAN `<` (4,15); `>` (41,3). A leprechaun here carries 1635 of my gold. |
| Soko 1–4 | Sokoban | ALL SOLVED. |
| 7–10 | Dungeons | 7: up (33,13) `>` (64,16); 8: up (48,4) `>` (49,16); 9: up (31,19) `>` (43,4); 10 BIG ROOM `<` (16,8) `>` (4,16) |
| 11 | Dungeons | `<` (48,19) `>` (14,19) LAWFUL ALTAR (44,6). QUEST PORTAL LEVEL (portal not found; XL14 + piously needed). |
| 12 | Dungeons | `<` (48,3) land mine (47,4) `>` (13,4); WEAPON SHOP (Carignan): nothing useful; buys only weapons/armor. |
| 13 | Dungeons | `<` (74,7) `>` (66,16) LAWFUL ALTAR (17,18) |
| 14 | Dungeons | `<` (17,7) `>` (30,6) **LAWFUL ALTAR (49,6)** (closest altar), fountains (7,11), (19,17). |
| 15 | Dungeons | `<` (23,15) `>` (6,10); rolling boulder trap (9,9). **BARRACKS east (x≈47-50, y 12-19, asleep) — AVOID** (avoid() set). |
| 16 | Dungeons | **ROGUE LEVEL**. `<` (41,2); **`>` (20,16)** (bottom-left room); rust trap (18,16); dart trap (39,2). All 4 frost giants dead. Ghost pile (30,10): plate mail, bow, arrows, two-handed sword left. |
| 18 | Dungeons | **`<` (50,15), `>` (45,5)**. Traps: rolling boulder (43,3) (empty), dart (13,5), land mine → pit (5,14), magic trap (3,17); fountain (5,17). West, centre, NE explored; SE/E rooms (x 58–70, y 10–19) not fully. Peaceful Aleax. |
| 17 | Dungeons | **`<` (13,15), `>` (25,18)**. Hidden door (36,18) east of the `>` room, hidden corridor (38,7). **THRONE ROOM (54-69, 3-4)**: court CLEARED (Elvenking, hill giant, gnome king, centaur, bugbears, hobgoblins...), throne (56,3) (never sit), paper golem's blank scrolls (54,3). Chests at (58,3) (empty now) and (66,13) (looted). A PEACEFUL gnome lord wanders there. |

## Threats / known dangers
- Prayer: check `prayer_check()` first (last prayer T:10649; p_safe 0.99 at T:12478).
- Stoning: X lizard corpse carried. Cockatrices: melee only with Excalibur.
- WAND USERS / BREATHERS / SOLDIERS: stay off their lines; never zap sleep toward nearby unknown rock (bounce).
- GELATINOUS CUBES: never melee (passive paralysis) — wand of striking (v) / thrown daggers; they resist fire/cold/sleep/shock.
- YELLOW LIGHTS: kill with one blow as they step adjacent, or at range.
- LEPRECHAUNS: keep ALL gold in sack n (`bag_put('n','$')` after every pickup).
- No MR/reflection: must come from silver/gray dragon scales, cloak of MR, shield of reflection, amulet of reflection (maybe amulet I!), wishes, quest.

## Objective and plan
- DONE shift 18: altar BUC test + read/quaff tests (see journal). Amulet I cursed → not worn.
- NEXT (shift 19): finish exploring D18 (east/south-east rooms), then D18 `>` (45,5) → D19, D20 (still above Medusa: D21–24). Look for MR/reflection, shops (price-ID; sell the spellbook, amulet, copper ring for protection gold: need 4400 at XL11, have 1443).
- MEDUSA (D21–24) PLAN: magic mapping (Y) on arrival, quaff the potion of BLINDNESS (bag s) BEFORE she can see me, fight blind with telepathy; still need a way across water (levitation / scroll of earth? / cold wand — none yet). Don't go below D20 until that is solved.
- Emergency: HP < 40% → Elbereth / potion of healing (bag s) / stairs / scroll of teleportation (bag s). Prayer only when `prayer_check()` says it's safe.

## Harness/helper calibration notes
- `monster_filter(lambda m: ...)` silences far-away known threats during explore(); it does NOT silence the crowded-level "approaching: X" pauses (neither does `defer_far(1)`).
- A 1-row throne room is a perfect corridor: `hunt((x, y))` on each sleeper in turn, one call per kill.
- fight_until_clear() in a 1-wide corridor killed a frost giant in 2 turns with no damage.
- The dungeon overview (`bin/nh info` → overview) names shop TYPES of visited levels — check it before a shop detour.
