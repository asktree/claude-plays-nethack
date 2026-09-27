# p2 — current state (rewrite as things change)

## Character
- Name/role: p2 — local practice game, seed 202 (lawful female dwarven Valkyrie, god: Tyr)
- Turn / Dlvl / XL / HP / Pw / AC: **T:10651 / D11 ON THE LAWFUL ALTAR (44,6)** / **XL10** (Exp 8543; XL11 at 10000) / 121/121 / 16/16 / **AC -2** / **$0 on me** (sack n: 1092 gold + murky potion). Satiated (ate an owlbear T:10423) → Hungry expected ~T:11500.
- FOOD: J 1 food ration, **l lembas wafer** (new), T 4 tripe rations (dog food: 50% vomiting for a dwarf), G 2 cloves of garlic, p slime mold, k lichen corpse, f tin. Still thin — buy food (D12 has a shop, type unknown).
- Attributes: St:17 Dx:12 Co:19 In:11 Wi:9 Ch:9.
- Skills: long sword **EXPERT**; #enhance other skills when "more confident" appears.
- Intrinsics (harness knows them): cold res, stealth (Valk + elven cloak), infravision, SPEED, EXTRINSIC telepathy (amulet of ESP O) + INTRINSIC TELEPATHY, **POISON RESISTANCE**, **SEE INVISIBLE (ring B worn, left hand)**. Excalibur: autosearch + drain resistance while wielded. **NO magic resistance, NO reflection, NO fire resistance.**
- Luck: 0. Alignment high ("Tyr is well-pleased" = record >= 14 at T:10649).

## Prayer log
| turn | reason | result |
|---|---|---|
| T:6107–6110 | deliberate no-trouble prayer on the D11 lawful altar with 2 waters | SUCCESS, 2 holy water, timeout reset |
| T:10649 | holy-water prayer on the D11 lawful altar (2 waters; cursed worn mithril = minor trouble) | **SUCCESS**, "well-pleased", 2 HOLY WATER; the coat was NOT uncursed (action roll 1-2). **Timeout reset (~50–1000): NO emergency prayer until `prayer_check()` says so (~T:11650).** |

## Equipment worn/wielded (letter: item)
- a: EXCALIBUR — blessed rustproof **+6** (wielded). NEVER read enchant weapon on it.
- m: **CURSED** +0 elven mithril-coat (can't be taken off — uncurse with holy water only when a better suit (dragon scales!) turns up); q: uncursed +0 elven cloak (burnt); c: +3 small shield (very burnt); E: +0 high boots (very burnt); j: +0 orcish helm; O: amulet of ESP; **B: ring of see invisible (left hand)**.

## Key inventory (letters)
- **TWO BAGS OF HOLDING: i (uncursed, EMPTY) and s (uncursed, 21 items).** Proven T:10651: `#name` the type of i "holding" → s also shows "bag called holding". **NEVER put i into s or s into i (both explode, contents lost).** n is a plain sack (gold).
- **BAG s**: pick-axe, **2 BLESSED potions of water (HOLY WATER)**, potion of HEALING, murky potion, puce potion (base 150), 2 scrolls of TELEPORTATION, 2 ETAOIN SHRDLU (= earth), scrolls VERR YED HORRE, FOOBIE BLETCH, STRC PRST SKRZ KRK (all 3 unknown), KIRJE = CREATE MONSTER, blank x2, ENCHANT WEAPON, + all gems.
- **L: UNICORN HORN** (uncursed, altar-tested).
- THROWING: e blessed +0 dagger (back in the pack), C uncursed dagger, D uncursed dagger (quivered), F elven dagger; P 12 blessed darts.
- **WANDS: R OAK = TELEPORTATION, CURSED** (0–3 charges; a cursed wand explodes 1 zap in 100; works on monsters even in Sokoban); g, N, y, Z FIRE (4 wands, all uncursed); x SLEEP (1–5 left; the ray BOUNCES — never zap it where it can come back to me: no sleep resistance); v STRIKING; r + U SLOW MONSTER (r used on the leprechaun T:10519 — immediate beam, no bounce: the safe way to slow a fleeing thief); V LIGHT; M make invisible (0:3); I undead turning (0:3); h HEXAGONAL uncursed (engrave: no message → opening/locking/probing/nothing/secret door detection).
- RINGS: B see invisible (worn); **b IRON, uncursed, unknown**; o AGATE (base 100) CURSED; S sapphire CURSED; H CURSED teleportation. (X, another cursed teleportation ring, left on the D11 altar.) Never put on unknown rings.
- TOOLS: Q grease; u key (`unlock(x, y)`); t whistle; A brass lantern; d blessed oil lamp; candles w (6) + z (1).

## Identified appearances (appearance -> identity)
- Scrolls: YUM YUM enchant weapon; ANDOVA BEGARIN identify; ELAM EBOW scare monster; unlabeled blank; KO BATE light; DAIYEN FOOELS teleportation; KERNOD WEL base 80 (enchant armor / remove curse); ELBIB YLOH destroy armor; ETAOIN SHRDLU = earth (not formally); KIRJE = create monster; VERR YED HORRE, FOOBIE BLETCH, STRC PRST SKRZ KRK unknown.
- Wands: uranium create monster; ebony striking; curved sleep; balsa slow monster; jeweled FIRE; pine light; iron make invisible; forked undead turning; oak TELEPORTATION; hexagonal: no engrave message.
- Rings: silver regeneration; copper unknown (cursed one left on D13); agate base 100; steel shock resistance; twisted teleportation; **bronze SEE INVISIBLE**; sapphire, iron unknown.
- Potions: MAGENTA healing; YELLOW speed; cyan gain level; clear water; WHITE paralysis; EFFERVESCENT full healing; golden object detection; EMERALD sleeping; puce base 150; murky base 100.
- Amulets: hexagonal ESP; oval unchanging. Faded pall = elven cloak. "bag" = bag of holding (called "holding").

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1–5 | Dungeons | see journal; D2 Mines branch (21,14); D5 Oracle |
| Mines | Gnomish Mines | Minetown (Dlvl 5): temple of Odin (protection bought), shops |
| 6 | Dungeons | up (23,15); **SOKOBAN `<` (4,15)**; `>` (41,3). **A SLOWED LEPRECHAUN here carries my 1635 gold** (it read teleportation, T:10522). |
| Soko 1–4 | Sokoban | ALL SOLVED. Soko 4 (Dlvl 2): prize taken; left: giant mimic at (29,6), a large mimic, unicorn horn (45,19), glass piercer (44,14). |
| 7–10 | Dungeons | 7: up (33,13) `>` (64,16); 8: up (48,4) `>` (49,16); 9: up (31,19) `>` (43,4); 10 BIG ROOM `<` (16,8) `>` (4,16) (Green-elf, floating eye, peaceful tengu, large mimic around) |
| **11** | Dungeons | `<` (48,19) `>` (14,19) **LAWFUL ALTAR (44,6)**. **QUEST PORTAL LEVEL** ("You again sense the Norn pleading for help" on arrival) — portal not found yet (secret door?); only needed at XL14 + "piously". |
| 12 | Dungeons | `<` (48,3) land mine (47,4) `>` (13,4); a SHOP (heard; type unknown) |
| 13 | Dungeons | `<` (74,7) `>` (66,16) LAWFUL ALTAR (17,18) |

## Threats / known dangers
- **NO EMERGENCY PRAYER until ~T:11650** (reset T:10649). Emergency kit instead: Elbereth, potion of healing (bag s), scrolls of teleportation (bag s — consider keeping one unbagged), wand of teleportation R (cursed), upstairs.
- WAND USERS / BREATHERS: stand where a ray can't bounce back off a wall right behind you.
- YELLOW LIGHTS: kill with one blow as they step adjacent, or at range. BLACK LIGHTS are now VISIBLE (see invisible ring).
- Cockatrices: only with Excalibur; stoning cure = none now (no lizard, prayer on timeout) — AVOID cockatrices until the prayer is back or a lizard corpse is found.
- LEPRECHAUNS: keep ALL gold in sack n, always (lost 1635 on D6).
- No MR/reflection: must come from silver/gray dragon scales, cloak of MR, shield of reflection, amulet of reflection, wishes, quest.

## Objective and plan
- NEXT (shift 16):
  1. From the D11 altar go down: D12 — find the SHOP (heard): if it is a general store/delicatessen buy food; price-ID the 3 unknown scrolls (VERR YED HORRE, FOOBIE BLETCH, STRC PRST SKRZ KRK), the iron ring b and the puce potion (sell offers). Read-test only price groups without big downsides, at full HP, off-shop.
  2. D13 (altar) → D14+ new levels: explore for MR/reflection, gold (protection: 400×XL = 4000 at XL10 / 4400 at XL11 — have 1092), food, a stethoscope (for `piety()`).
  3. Uncurse the mithril-coat (dip into 1 holy water) only when a better body armor appears. Keep the other holy water (lycanthropy cure / blessing).
  4. Quest at XL14 + piously (portal on D11). Medusa D21–24 needs reflection or blindness + a water crossing.
- Emergency: HP < 40% → Elbereth / potion of healing (bag s) / stairs / scroll of teleportation. Prayer only when `prayer_check()` says it's safe again.

## Harness/helper calibration notes
- The mysterious-force tengu message is permanent in the harness now (no kernel patch needed).
- hunt() handles engulfers now; fight() on the fire elemental: passive info + one-blow `max_blows=1, allow_passive=True` works.
- prayer_check() does NOT count a cursed WORN armor piece as minor trouble (NetHack does).
- `#name` → `o` → letter → "holding<CR>" works through `do()` step by step.
- pickup() returns a list of messages.
