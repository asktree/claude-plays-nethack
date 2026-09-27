# p1 — current state (rewrite as things change)

## Character
- Name/role: P1 the Skirmisher — lawful female dwarven Valkyrie, god: Tyr (seed 101, local practice game)
- Turn / Dlvl / XL / HP / Pw / AC: T:7330 / **Sokoban level 3 = the TOP level (Sokoban Level 4a, soko1-1, 26 steps; arrived T:7204; `sokoban.solve()` 0/26 done)** / **XL8** (Exp 1851; XL9 at 2560) / **97/97** (full) / 17/17 / **AC3** (studded leather burnt by naga fire). Wielding blessed rustproof +2 EXCALIBUR (long sword EXPERT since T:6882). Rings worn: f (prot. from shape changers, right hand), **w (fire resistance, left hand, since T:6818 — keep for now; remove later to save hunger)**.
- Position at shift-7 end (T:7330): Soko3 (34,10) = the 1-wide gap in the wall between the top puzzle room (rows 8-9) and the middle room (rows 11-12), standing on a VERIFIED dust Elbereth, HP 97/97, no monsters in view. A pyrolisk (fire gaze; ring w made it harmless) was killed at (34,12) T:7330. A GIANT MIMIC (2x3d6!) that hid at (33,11) was killed there T:7215 (corpse at (33,11)). No monsters in view. `>` (27,5) back down. Holes: (34-39,5) and (41-46,5) along the top corridor; closed doors (43,15),(43,17),(43,19) on the east side = the zoo/stair area. Food item at (34,8) (unchecked).
- Attributes: St18 Dx13 Co20 In10 Wi11 Ch7 (Ch7 => shop prices +50%). ("You feel wise/agile" T:7152.)
- Intrinsics: cold res (Valk), stealth (Valk), infravision (dwarf), speed (XL7), **POISON RESISTANCE (red naga corpse, T:6853: "You feel healthy")**. Long sword skill: SKILLED -> "more confident" at T:6880 (#enhance to EXPERT). Excalibur gives auto-search.
- Luck 0 (keep it: no boulder smashing / earth scrolls / squeezing in Sokoban); alignment record high (one "hypocrite" hit T:6808: zapped from an Elbereth square); no peacefuls killed.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:1271 | welded cursed orcish dagger (MINOR trouble — mistake) | accepted, trouble NOT fixed, timeout reset |
| T:2016 | lycanthropy (MAJOR) | "well-pleased ... You feel purified" CURED |
| T:3401 | Weak from hunger (MAJOR; prayer_check 98%) | "well-pleased. Your stomach feels content." nutrition 900. Prayer available again (~3500 turns since; prayer_check() said 99.9% at T:6207); always `prayer_check()` first. |

## Equipment worn/wielded (letter: item)
- **WIELDED: a: blessed rustproof +2 EXCALIBUR** (made T:4180). +d5 to-hit, +d10 damage, drain resistance, auto-search. Rustproof = also corrosion-proof (acid blobs are safe to hit).
- c: uncursed +3 small shield (worn), e: +0 studded leather armor (worn, BURNT -1), n: uncursed +0 orcish helm (worn) -> AC3
- The cursed corroded orcish dagger lies on the DL1 `>` (54,7). Never pick it up.

## Key inventory (letters)
- **B: BLESSED SCROLL OF TELEPORTATION** — emergency escape OUTSIDE Sokoban (Sokoban levels are no-teleport).
- Wands: **z lightning (0:2)**, **E lightning (0:3)** — 6d6 ray, bounces: only zap along a line whose first wall is >= 14 squares away (or where the bounce can't return: range is 7-13 squares total). Shock destroys the target's wands (blew up an ogre's wand of magic missile T:6674). **S wand of striking (3 charges used; remaining unknown)** — force bolt 2d12, no bounce, ideal vs gelatinous cubes / floating eyes; never at a boulder in Sokoban. **Unknown wands: X crystal, Z short** (engrave-test OUTSIDE Sokoban on a quiet level).
- **h: magic marker (0:82) but CURSED** — needs remove curse / holy water first.
- Rings: w fire resistance (WORN left), **p ring of fire resistance (spare, identified)**, f prot. shape changers (WORN right). **Unknown rings (do NOT wear): K engagement, R ivory, W bronze, k agate, m coral.** Price-ID/identify later.
- Scrolls: i uncursed AMNESIA (NEVER READ), x + l uncursed light (2), A uncursed fire, **o scroll labeled ELAM EBOW (unknown, from the ogres)**, **N + O: two scrolls labeled NR 9 (probably EARTH; never read in Sokoban)**.
- Potions: q blessed sickness (throw at a tough non-poison-resistant monster), C uncursed oil, **M swirly potion (unknown)**.
- **L: bag (sack / oilskin / bag of holding; BUC unknown — test at an altar before trusting it).**
- **b: 11 darts** (Valkyrie: restricted skill, -4 to hit; still the answer to a floating eye at range). y: figurine of a coyote (junk). $165.
- **Food: P 3 food rations, Q 1 pancake, U slime mold, j uncursed candy bar, d fortune cookie. g: 2 CURSED candy bars (never). T: 2 EGGS of unknown kind — NEVER eat.** Ate at T:6207 (ration) + python/cube/red naga corpses T:6563-6853: not hungry until ~T:7500+.
- No healing potions, no unicorn horn, no lizard corpse. Escapes: Elbereth where you stand (works in Sokoban), the stairs; scroll B outside Sokoban. Prayer available (prayer_check() first).
- Left behind: DL3 `<` room: +0 dagger, orcish dagger, violet gems. DL6 (8,5): scale mail. DL7 (57,4): orcish helm; (58,8): orcish helm + orcish shield + orcish chain mail. Soko4 (33,13): orcish helm + orcish shield + knife (orc-captain's); (35,12): a tin; (48,14): ogre corpse pile (clubs).

## Identified appearances
- Scrolls: ZELGO MER identify, EIRIS SAZUN IDISI amnesia, GARVEN DEH light, HACKEM MUCHE fire, TEMOV teleportation, FOOBIE BLETCH enchant weapon. (ZLORFIK, DUAM XNAHT: base-100 class, types unknown. NR 9: probably earth, unconfirmed.)
- Potions: yellow sickness, brilliant blue blindness, cyan oil (swirly base 100, murky base 50: unknown).
- Wands: marble lightning, iridium striking, **oak = magic missile** (seen: an ogre zapped one). Rings: diamond fire resistance, iron protection from shape changers.

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1 | main | `<` (76,4). `>` (54,7) big room — cursed orcish dagger on it. SINK (55,6). Fully explored. |
| 2 | main | `<` (46,16). `>` (48,7). FOUNTAIN (25,6). TRAP DOOR (71,8) = shaft to DL5. Fully explored. |
| 3 | main + Mines branch | `<` (19,9). ARROW TRAP (19,6). **WEREJACKAL + 4 jackals + fox frozen next to the `<` at (19,8)**. Annootok's general store NW (3-7,5-8) — food rations. `>` (29,16) and `>` (46,18) — one is the Mines. Unexplored east room via door (60,8). |
| 4 | main | `>` (20,14); hidden door (17,14) -> W room with `<` (5,9). SLEEPING GAS TRAP (58,15). South half unexplored. |
| 5 | main | `<` (59,16). `>` (70,16). BURNED ELBERETH (45,18). Fully explored. |
| 6 | main | **ORACLE LEVEL.** `<` (9,7). `>` (65,10) — **HOSTILE WATER DEMON roams near it: never re-enter DL6 by its `>`**. Fountains (38,12) (39,11) (39,13) (40,12) (one used). Peaceful Oracle (39,12). |
| 7 | main (Sokoban entry level) | `<` (5,7) to DL6. `>` (13,8) in room B (13-17,6-8). **SOKOBAN `<` = (14,15) UNDER THE STATUE of a hill orc** in the fountain room C (10-19,15-17), TRAP (18,15). Orc gear (57,4),(58,8). Peaceful dwarf wanders. |
| Sokoban 6 (= Sokoban 1a) | Sokoban | **SOLVED T:5249**. `>` (35,7) back to DL7 (14,15); `<` (33,7) up (1-wide stair column (33,7-13)). |
| Sokoban 5 (= Sokoban 2a) | Sokoban | **SOLVED T:5991**. `>` (29,7); `<` (46,10) behind the (kicked-open) door (50,15). |
| Sokoban 4 (= Sokoban 3b, soko2-1) | Sokoban | **SOLVED T:6669** (all holes (38-47,15) plugged; the row-15 lane is a plain corridor now). `>` (36,16). `<` (46,10) in the stair room (44-48,7-13) behind the BROKEN door (48,14) (kicked open T:6673). **2 OGRES (clubs) loot that room** as of T:6880. Green mold at (40,11) (never touch; avoid() set). Leftover junk listed above. |
| Sokoban 3 (top) | Sokoban | **Sokoban Level 4a (soko1-1, 26 steps) — IN PROGRESS 0/26.** `>` (27,5). Holes (34-39,5), (41-46,5). Closed doors (43,15),(43,17),(43,19) east = zoo side. Giant mimic killed at (33,11) T:7215 (mimics can pose as boulders: any "boulder" not on the solver's list is suspect). |

## Threats / known dangers
- **Sokoban**: no teleport (scroll B useless), no diagonal squeezing for me, Luck penalties for smashing boulders/reading earth. **The top level has the TREASURE ZOO: go in at full HP, fight from the doorway one at a time (fight_until_clear(radius=2, stop_hp=0.5)); Elbereth if swarmed (rest on it, never attack from it).** Prize: bag of holding or amulet of reflection (the amulet is always reflection: wear it at once).
- Level spawns were heavy this shift (a monster every ~40 turns): wargs (2d6, come in threes), ogres (clubs ~10/hit; one had a wand of magic missile), red naga (fire breath burns armor and can destroy scrolls/potions), gelatinous cube (never melee: striking wand), owlbear (took 20 HP in one round), succubus (theft only; can't teleport away here), flaming sphere (harmless with ring w on).
- **Elbereth (3.6.7, verified this shift): attacking OR ZAPPING from the square erases it and costs alignment ("You feel like a hypocrite"). Rest on it, step off to fight.** Scared adjacent monsters don't interrupt counted rests.
- **A LARGE monster (python) DID squeeze diagonally between a boulder and a wall** — don't count on the "big monsters can't squeeze" rule; the HUGE ettin zombie could not.
- **DL6 (Oracle level): HOSTILE WATER DEMON** near the DL6 `>` (65,10). Never re-enter DL6 by its `>`.
- DL7: werejackals (2 killed), yellow lights (2 killed). DL3 werejackal pack camps the DL3 `<`.
- Cockatrices possible from DL8 (never touch/eat; flee hissing; no lizard/acidic corpse yet). Unknown eggs T: never eat.
- No healing items. Escapes: Elbereth where you stand, stairs; scroll B outside Sokoban. Prayer available (~99%); prayer_check() first.

## Objective and plan
1. **Top level (Sokoban 4a)**: rest to full on the Elbereth at (34,10) if not already full, then `sokoban.solve()`. It pauses on each new monster: kill it (fight_until_clear / fight), then call `solve()` again.
2. **Resume rule**: `progress()` reports `partial: {pushes_done, boulder_at}` after an interruption and `solve()` finishes that boulder itself (verified 3x in shift 7). **Only if `progress()` says done=-1 with `partial: None`** is the board off-plan: then compare with `sokoban._diff(sokoban._state(obs, lv, ox, oy), after_k)` and fix that boulder by hand with `sokoban.push()`. Beware mimics posing as boulders.
3. **The zoo**: full HP first, stand in the doorway, `fight_until_clear(radius=2, stop_hp=0.5)`; back off to an Elbereth square (not the doorway) when HP < 50%; loot the prize; wear the amulet at once if it is one.
4. Food: 3 rations + pancake + slime mold + candy bar + cookie: fine. Not hungry until ~T:7500.
5. After Sokoban: back down (Soko `>`s -> DL7 (14,15)), then DL8+ / Mines-Minetown: altar (BUC of the bag, rings, wands, rations), temple protection ($165 is far from 400 x XL = 3200), price-ID rings K/R/W/k and potion M, engrave-test wands X and Z OUTSIDE Sokoban, uncurse the marker, AC below 0. Consider removing ring w when fire is not a threat (hunger).
