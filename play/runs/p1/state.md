# p1 — current state (rewrite as things change)

## Character
- Name/role: P1 the Skirmisher — lawful female dwarven Valkyrie, god: Tyr (seed 101, local practice game)
- Turn / Dlvl / XL / HP / Pw / AC: T:6207 / **Sokoban level 4 (= Sokoban 3b, soko2-1; the third Sokoban level; entered T:6063)** / **XL7** (Exp 762; XL8 at 1280) / 84/84 / 14/14 / AC2. Wielding blessed rustproof +2 EXCALIBUR. Ring f (prot. from shape changers) worn on the right hand since T:3940.
- Position at shift end (shift 6, T:6207): Soko4 (41,15) standing on the plugged hole in the row-15 lane; board at solve() step 5/15. A SLEEPING MANES sits on the hole square (43,15) (2 squares E; it never moves). No other monsters in view. HP 84/84, not hungry (ate a ration at T:6207 -> Hungry ~T:7000).
- Attributes: St18 Dx12 Co20 In10 Wi10 Ch7 (Ch7 => shop prices +50%)
- Intrinsics: cold res (Valk), stealth (Valk), infravision (dwarf), **speed (XL7, "You feel quick!" T:6036)**. Long sword skill: SKILLED. Excalibur gives auto-search.
- Luck 0 (keep it: no boulder smashing / earth scrolls / squeezing in Sokoban); alignment record high; no peacefuls killed.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:1271 | welded cursed orcish dagger (MINOR trouble — mistake) | accepted, trouble NOT fixed, timeout reset |
| T:2016 | lycanthropy (MAJOR) | "well-pleased ... You feel purified" CURED |
| T:3401 | Weak from hunger (MAJOR; prayer_check 98%) | "well-pleased. Your stomach feels content." nutrition 900. Prayer available again (2800 turns since); always `prayer_check()` first. |

## Equipment worn/wielded (letter: item)
- **WIELDED: a: blessed rustproof +2 EXCALIBUR** (made T:4180 at the DL7 fountain (12,16); enchant weapon read on it T:4182). +d5 to-hit, +d10 damage, drain resistance, auto-search.
- c: uncursed +3 small shield (worn), e: +0 studded leather armor (worn), n: uncursed +0 orcish helm (worn; stolen by a nymph T:5170 and recovered) -> AC2 [seen]
- The cursed corroded orcish dagger lies on the DL1 `>` (54,7). Never pick it up.

## Key inventory (letters)
- **B: BLESSED SCROLL OF TELEPORTATION** — emergency escape OUTSIDE Sokoban (Sokoban levels are no-teleport: it fails there; nymphs can't teleport away either).
- z: wand of lightning (0:3), E: wand of lightning (0:6) — 6d6 ray, bounces; never zap toward a wall < 14 squares away in line; `zap('E', dir)`. Shock destroys wands/rings if it bounces onto you.
- **S: WAND OF STRIKING** (engrave-tested T:5280; force bolt 2d12, no bounce; breaks boulders -> never zap it at a boulder in Sokoban: -1 Luck).
- **h: magic marker (0:82) but CURSED** — needs remove curse / holy water first.
- Rings: w uncursed fire resistance (not worn); f uncursed protection from shape changers (WORN). **Unknown rings (do NOT wear): K engagement ring, R ivory ring, W bronze ring.** Price-ID/identify later.
- **Unknown wands (engrave-test on a quiet level OUTSIDE Sokoban): X crystal wand; a 3rd unknown wand still lies at Soko4 (33,14) (pick it up).**
- Scrolls: i uncursed AMNESIA (NEVER READ; future blank paper), x uncursed light, A uncursed fire, **N + O: two scrolls labeled NR 9 (the Sokoban entry level's pair = almost certainly EARTH; never read them in Sokoban)**.
- Potions: q blessed sickness (throw at a tough non-poison-resistant monster), C uncursed oil, **M swirly potion (unknown)**.
- **L: bag (not a bag of tricks: #loot did not bite; sack / oilskin sack / bag of holding; BUC unknown — put nothing valuable in until it is tested at an altar / with a known item).**
- y: figurine of a coyote (junk). $137.
- **Food: P 3 food rations (BUC unknown, Sokoban finds), Q 1 pancake, U slime mold, j uncursed candy bar. g: 2 CURSED candy bars (never). T: 2 EGGS of unknown kind — NEVER eat (cockatrice eggs stone you).** Eat when Hungry (~T:7000); a ration lasts ~750 turns.
- No healing potions, no unicorn horn, no lizard corpse. Escapes: Elbereth where you stand (works in Sokoban), the stairs; scroll B outside Sokoban. Prayer available (prayer_check() first).
- Left behind: DL3 `<` room: +0 dagger, orcish dagger, violet gems (werejackal territory). DL6 (8,5): scale mail. DL7 (57,4): orcish helm; (58,8): orcish helm + orcish shield + orcish chain mail (unknown BUC). DL1 `>` (54,7): the cursed orcish dagger — never.

## Identified appearances
- Scrolls: ZELGO MER identify, EIRIS SAZUN IDISI amnesia, GARVEN DEH light, HACKEM MUCHE fire, TEMOV teleportation, FOOBIE BLETCH enchant weapon. (ZLORFIK, DUAM XNAHT: base-100 class, types unknown. NR 9: probably earth, unconfirmed.)
- Potions: yellow sickness, brilliant blue blindness, cyan oil (swirly base 100, murky base 50: unknown).
- Wands: marble lightning, iridium striking. Rings: diamond fire resistance, iron protection from shape changers.

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1 | main | `<` (76,4). `>` (54,7) big room — cursed orcish dagger on it. SINK (55,6). Fully explored. |
| 2 | main | `<` (46,16). `>` (48,7). FOUNTAIN (25,6). TRAP DOOR (71,8) = shaft to DL5. Fully explored. |
| 3 | main + Mines branch | `<` (19,9). ARROW TRAP (19,6). **WEREJACKAL + 4 jackals + fox frozen next to the `<` at (19,8)**. Annootok's general store NW (3-7,5-8) — food rations. `>` (29,16) and `>` (46,18) — one is the Mines. Unexplored east room via door (60,8). |
| 4 | main | `>` (20,14); hidden door (17,14) -> W room with `<` (5,9). SLEEPING GAS TRAP (58,15). South half unexplored. |
| 5 | main | `<` (59,16). `>` (70,16). BURNED ELBERETH (45,18). Fully explored. |
| 6 | main | **ORACLE LEVEL.** `<` (9,7). `>` (65,10) — **HOSTILE WATER DEMON roams near it: never re-enter DL6 by its `>`**. Fountains (38,12) (39,11) (39,13) (40,12) (one used). Peaceful Oracle (39,12). |
| 7 | main (Sokoban entry level) | `<` (5,7) to DL6. `>` (13,8) in room B (13-17,6-8). **SOKOBAN `<` = (14,15) UNDER THE STATUE of a hill orc** in the fountain room C (10-19,15-17), TRAP (18,15). Orc gear (57,4),(58,8). Peaceful dwarf wanders. South-middle band is solid rock (searched). |
| Sokoban 6 (= Sokoban 1a) | Sokoban | **SOLVED T:5249**. `>` (35,7) back to DL7 (14,15); `<` (33,7) up (1-wide stair column (33,7-13): a peaceful monster in it blocks you — wait at (33,15) and slip past via (34,14)->(33,13)). |
| Sokoban 5 (= Sokoban 2a) | Sokoban | **SOLVED T:5991**. `>` (29,7); `<` (46,10) behind the (kicked-open) door (50,15). |
| Sokoban 4 (= Sokoban 3b, soko2-1) | Sokoban | **IN PROGRESS: sokoban.solve() step 5/15 done** (holes (38-41,15) plugged; remaining holes (42-47,15)). `>` (36,16). `<` (46,10) in the stair room behind the CLOSED (probably locked) door (48,14) at the E end of the row-15 lane: kick it. **A sleeping MANES sits on the hole (43,15): after step 6 plugs (42,15), step onto (42,15) and F-attack east to kill it (a monster in the hole blocks the boulder of step 7). NEVER step onto an unplugged hole square.** Loot left: wand (33,14), food (35,12), food (31,9). |

## Threats / known dangers
- **Sokoban**: no teleport (scroll B useless), no diagonal squeezing, Luck penalties for smashing boulders/reading earth. **After this level comes the top level (dungeon level 3) with the TREASURE ZOO: fight it at the door one at a time at full HP; Elbereth works.** Prize: bag of holding or amulet of reflection.
- **DL6 (Oracle level): HOSTILE WATER DEMON** near the DL6 `>` (65,10). Never re-enter DL6 by its `>`.
- DL7: werejackals (2 killed), yellow lights (2 killed; no potion of blindness left). DL3 werejackal pack camps the DL3 `<`.
- Poisonous biters/stingers: 1/30 instadeath per poisoned hit — no poison resistance yet.
- Cockatrices possible from DL8 (never touch/eat; flee hissing; no lizard/acidic corpse yet). Unknown eggs T: never eat.
- Nymphs: in Sokoban they cannot teleport — corner and kill; elsewhere drop wands/marker first.
- No healing items. Escapes: Elbereth where you stand, stairs; scroll B outside Sokoban. Prayer available (~98%); prayer_check() first.

## Objective and plan
1. **Finish Sokoban 3b**: `sokoban.solve()` from step 6 (if `progress()` says done=-1 the board is mid-step: compare with `sokoban._diff(sokoban._state(obs, lv, ox, oy), after_k)` and finish that boulder's remaining moves with `sokoban.push()`, then solve() again). After step 6: kill the manes on (43,15) from (42,15). Pick up the wand (33,14). Kick the stair-room door (48,14), climb the `<` (46,10).
2. **Sokoban top level (dungeon level 3)**: solve(), then the zoo behind the door: full HP, fight from the doorway one at a time (Elbereth if swarmed), loot the prize (bag of holding / amulet of reflection — the prize-square amulet is always reflection: wear it at once).
3. Food: 3 rations + pancake + slime mold + candy bar: fine. Hungry ~T:7000.
4. After Sokoban: back down (Soko `>`s -> DL7 (14,15)), then DL8+ / Mines-Minetown detour: altar (BUC of the bag, rings, wands, rations), temple protection ($137 is far from 400 x XL = 2800), price-ID rings K/R/W and potion M, engrave-test wands X + the (33,14) wand OUTSIDE Sokoban, uncurse the marker (remove curse / holy water), AC below 0.
5. Keep ring f on for now (+5% hunger only). Don't wear unknown rings. No poison resistance: avoid bee/ant swarms.
