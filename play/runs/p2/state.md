# p2 — current state (rewrite as things change)

## Character
- Name/role: p2 — local practice game, seed 202 (lawful female dwarven Valkyrie, god: Tyr)
- Turn / Dlvl / XL / HP / Pw / AC: T:~6115 / **Dlvl 11 (main dungeon, QUEST PORTAL LEVEL)** / XL8 (Exp 2246; XL9 at 2560) / 104/104 / 11/11 / **AC -4** (3 points of divine protection T:4517 + orcish helm T:5932) / gold: see inventory. Last meal: owlbear corpse finished T:5880 (not Hungry before ~T:6800).
- Position: see the end of journal.md (shift-8 end entry). D11 map fully known except the SE corner (nymph area). NEW PET: a tame DJINNI (from the magic lamp, T:6114; lvl 7, AC 4, 2d8 weapon, flies, speed 12) — it only follows on stairs when adjacent.
- Attributes (T:3483): St:17 Dx:12 Co:19 In:11 Wi:8 Ch:9 (Cha 9 → shop buy prices ×4/3; carry cap 950). "You feel wise!" T:6027.
- Skills: long sword **EXPERT** (enhanced T:3719 Skilled, T:6231 Expert = the Valkyrie maximum); #enhance other skills when "more confident" appears
- Intrinsics (source, turn): cold res (Valk), stealth (Valk), infravision (dwarf), SPEED (XL7, T:4212); EXTRINSIC telepathy from the amulet of ESP (worn T:2424); Excalibur gives automatic searching. NO poison resistance. NO magic resistance, NO reflection (the lamp wish failed — plan B needed).
- Luck notes: nothing done to Luck (no peacefuls killed by me).
- Alignment: "Tyr is well-pleased" at T:6110 = alignment record >= 14 (quest entry needs >= 20 and XL14).

## Prayer log
| turn | reason | result |
|---|---|---|
| T:6107–6110 | DELIBERATE no-trouble prayer standing on the lawful altar D11 (44,6) with 2 potions of water on it (pray(force=True) after prayer_check p_safe 1.0) | SUCCESS: "shimmering light ... The potions on the altar glow light blue ... Tyr is well-pleased" → 2 holy water (used on the lamp). Prayer timeout RESET at T:6110 (rnz(350): median ~350, long tail). Next emergency prayer: run prayer_check(); roughly safe from ~T:7100 (66% at +300, 87% at +500, 95% at +1000). |

## Equipment worn/wielded (letter: item)
- a: EXCALIBUR — blessed rustproof **+6** (wielded; re-wielded T:6115 after the lamp rub). NEVER read another enchant weapon on it. NOTE: applying the pick-axe or #rubbing a lamp WIELDS that tool — always `w`,`a` afterwards.
- c: uncursed +3 small shield (worn); DIVINE PROTECTION 3 points
- y: +0 scale mail (worn) [seen]; E: uncursed +0 high boots (worn) [seen]; O: uncursed AMULET OF ESP (worn) [seen]; **j: uncursed +0 orcish helm (worn, altar-tested T:5930)**

## Key inventory (letters) — BUC [seen] from altars unless marked
- b: blessed +0 dagger (throw it; stepping onto it picks it back up); P: 12 BLESSED darts; U: 7 uncursed elven arrows (no bow); S: uncursed knife
- m: uncursed PICK-AXE — carried LOOSE (top-level); put it back in the bag s (`bag_put('s','m')`) before any shop. `dig('>')` = escape to a random spot of the level below.
- d: **blessed OIL LAMP** (the ex-magic lamp: the djinni came out T:6114 as a TAME pet, no wish; 1000–1500 turns of oil)
- e: uncursed oil lamp; A: brass lantern; CANDLES: z + v + w(5) = 7 (for the Candelabrum — never burn them)
- n: uncursed SACK: holds ~201+ gold (+140 bagged T:6115 if bag_put succeeded — check) + scroll Q (ELBIB YLOH, base 100) + M (light) + D (blank) + cloth SPELLBOOK i (unread, BUC unknown) + potions I (magenta, base 100), N (murky, base 100). Take out with `bag_take('n', pattern)` — PATTERN BY IDENTIFIED NAME when the type is known (the white potion was listed as "potion of paralysis"); put in with `bag_put('n', letter)`.
- s: BAG = bag of holding or oilskin sack [inferred], currently EMPTY
- WANDS: x = SLEEP (curved, uncursed) [2–6 charges left: used T:3720 engrave, T:5903 gremlin]; g = FIRE (jeweled, uncursed; 6d6 ray, bounces, burns MY scrolls/potions if it hits me — bag them first; sliming cure; permanent-Elbereth engraver); V = LIGHT (pine); r = SLOW MONSTER (balsa); o = CREATE MONSTER
- J: uncursed scroll of TELEPORTATION (top-level) — ESCAPE ITEM
- L: uncursed GOLDEN potion (unknown); B: CURSED ring of shock resistance (never wear)
- FOOD: NO rations on me. f: uncursed tin (unknown; tin opener K). Lichen corpse from D11 (51,6) if picked up T:6115 (never rots). A FOOD RATION lies at D11 (18,8) (NW closet) — fetch it. An ICE BOX at D11 (71,7) (E room) may hold preserved corpses. Eat fresh safe corpses (`corpse()`).
- u: key (skeleton key), t: tin whistle
- Gems (all uncursed, unidentified): R black, X 2 black (other type), Y 2 red, Z yellow, W yellowish brown
- Escape items: scroll of teleportation J; wand of sleep x (and fire g); Elbereth (works); `dig('>')`; prayer NOT available until the timeout runs out (see log).
- Healing: none known. Emergency cures: none carried (no lizard corpse, no unicorn horn).

## Identified appearances (appearance -> identity)
- YUM YUM -> enchant weapon; ANDOVA BEGARIN -> identify; ELAM EBOW -> scare monster (lost); unlabeled -> blank paper; KO BATE -> light; DAIYEN FOOELS -> TELEPORTATION
- KERNOD WEL -> base 80 (enchant armor / remove curse); ELBIB YLOH -> base 100 group; HAPAX LEGOMENON -> base 100 group
- uranium wand -> create monster; curved wand -> SLEEP; balsa wand -> slow monster; jeweled wand -> FIRE; pine wand -> LIGHT
- silver ring -> regeneration; agate ring -> base 100 group; steel ring -> shock resistance
- puce potion -> base 150; murky potion -> base 100; magenta -> base 100; YELLOW -> SPEED; cyan -> GAIN LEVEL; clear -> water (called "water"; "blessed clear potion" = HOLY WATER); WHITE -> PARALYSIS (formally identified); **EFFERVESCENT -> FULL HEALING** (a hill orc quaffed one T:5915: "looks completely healed"); golden -> unknown
- hexagonal amulet -> ESP; oval amulet -> unchanging
- lamp (plain) -> magic lamp (used up); oil lamp identified; "bag" -> sack identified (n); the other "bag" (s) = holding/oilskin
- vellum spellbook -> level 1; dull -> level 4; leathery -> level 3/4; cloth -> unknown (i, in the sack)

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1 | Dungeons | up (8,8); down (10,19); fountains (27,11), (5,18) |
| 2 | Dungeons | up (40,6); down (21,14) = GNOMISH MINES BRANCH; down (74,17) = main; Kittamagh's bookstore (2-5,17-19) door (6,18); fountain (59,16) |
| 3 | Dungeons | up (21,18) under a broken large box; down (51,10); SLEEPING GAS TRAP (35,8); vault |
| 4 | Dungeons | up (39,18); down (12,18) via hidden passage (8,15); FOUNTAIN (22,17); UPERNAVIK'S GENERAL STORE (69-71,15-17) door (68,16) |
| 5 | Dungeons (ORACLE) | up (9,5); down (58,5); Delphi fountains; PIT (14,15) |
| 3–6 (Mines) | Gnomish Mines | Mines 1 up (77,13) down (50,13); Mines 2 up (44,10) down (8,10); MINETOWN = Mines 3 (Dlvl 5): up (74,5), down (3,6), TEMPLE of ODIN (neutral) altar (38,9) priest (protection bought), shops: Kilmihil books (29-31,7-9), AlliWar hardware (29-31,15-17) with a disguised LARGE MIMIC (30,16), Pasawahan deli (36-38,16-17), Izchak lights (47-49,7-9), Ouiatchouane general (48-50,15-17); Mines 4 (Dlvl 6) up (45,5), `>` not found |
| 6 | Dungeons | up (23,15); SOKOBAN `<` (4,15) (skipped); `>` (41,3) NE room; leprechaun hall (20-25,4-7) cleared; fountain (7,6); 2 gold-carrying leprechauns roam |
| 7 | Dungeons | up (33,13); `>` (64,16) (SE, door (61,16)); SW room (5-12,17-19) with a BURNED ELBERETH at (10,19); SPIKED PIT (23,13); a peaceful tengu |
| 8 | Dungeons | up (48,4); `>` (49,16) in a small room (48-50,14-16) with a FOUNTAIN (50,15), door (49,13); hidden passage (42,5); east third unexplored |
| 9 | Dungeons | up (31,19) S room; `>` (43,4) small NW room (39-43,4-6) door (44,4); W room (14-20,13-17) axe at (16,14); far-W room (2-6,13-16) with an ARROW TRAP (6,15) and MY HOLE at (4,15); a carnivorous ape wanders |
| 10 | Dungeons | **BIG ROOM** (irregular variant: wall fragments, trees, fountains (11,11), (65,11)); up (16,8); `>` (4,16) far W; loot: spellbooks (15,6), (20,11), scrolls (22,15), (26,10), (48,17), potion (29,17); **DANGER: KILLER BEE HIVE + giant spider + pyrolisk + mountain centaur + ghoul near the `<`** — never linger |
| 11 | Dungeons (**QUEST PORTAL LEVEL**, telepathic message from the Norn on arrival; portal itself NOT found — probably in the unexplored SE corner) | **`<` (48,19)** and **FOUNTAIN (52,19)** (still active) in the SW room (47-54,15-20; ape statue (53,16); E door (54,18) → corridor E toward the nymph area); **`>` (14,19)** in the W room (11-24,16-19; gold (18,19); E door (24,19) closed); **LAWFUL ALTAR (44,6)** in the N-centre room (32-45,5-10; hill orc statue (41,6); doors (30,6) W closed, (46,8) E doorway, (39,10) S); NE room (51-55,3-8): doorways (55,4) E, (50,3)/(50,8) W, lichen corpse (51,6), old giant rat corpse (53,5), scimitar + orcish dagger pile (56,5), gremlin corpse (56,6) (poisonous); E room (69-73,4-10) doors (69,7) open, (69,9) closed, **ICE BOX (71,7)**; NW closet (15-19,6-10) door (19,10): **FOOD RATION (18,8)**, studded leather armor (16,9); S room (33-41,16-19) door (33,19); YELLOW MOLD (28,13) in the corridor (avoid); boulders (48,9), (28,16); hidden passage near (24,9); WOOD NYMPH AWAKE roaming the SE (last (68,18) T:6084) — kill only asleep/at range (sleep wand), never let her adjacent |

## Pets
- TAME DJINNI (since T:6114, D11). Lvl 7, AC 4, flies, weapon 2d8. Keep it adjacent when taking stairs. It cannot be stolen from; it can kill the nymph.

## Threats / known dangers
- **No poison resistance**: killer bees (D10 hive), soldier ants, giant spiders, snakes, quasits, spiked pits → each poisonous hit = 1/8 × 1/30 death. Fight them one at a time in corridors, with Elbereth, or the fire wand along a line.
- **No magic resistance / no reflection**: no Castle, no lingering on D20+ near soldiers; avoid unknown wand zappers at range. Plan B for MR: cloak of magic resistance (shops/monsters), gray dragon scales (D20+ dragons), the Castle wand (needs MR first...), Sokoban (skipped) — reconsider Sokoban's prize (bag of holding / amulet of reflection) via D6 (4,15) once XL is higher.
- Yellow lights: NEVER melee (explode → blind). Pyrolisk: kill fast or break line of sight; bag burnables first.
- Gremlins at NIGHT (real clock 22:00–06:00): curse claw steals intrinsics — sleep-ray them or fight by day.
- Mummies/zombies/gas spores are mindless: telepathy does not show them.
- Nymphs steal (also worn items and the wielded weapon); leprechauns steal gold (keep it in the sack).
- Cockatrices (one killed on D11 T:5953): only Excalibur, never touch/eat corpses; no lizard corpse carried yet — prayer is unavailable for ~1000 turns, so avoid cockatrices until then.
- Werejackals: fight in @ form/at range; "You feel feverish" → prayer (unavailable now) or holy water (none left).
- Mines' End luckstone only at XL10+.

## Objective and plan
- DONE shift 8: D11 mapped (`<`, `>`, fountain, altar), gremlin + orc pack + cockatrice killed, orcish helm (AC -4), holy-water prayer SUCCEEDED (2 holy water), magic lamp blessed and rubbed → tame djinni, NO WISH.
- NEXT:
  1. Food: pick up the FOOD RATION at D11 (18,8) (NW closet, on the way to the `>`); keep the lichen corpse; check the ICE BOX (71,7) for preserved corpses when passing the E room (nymph area — sleep wand ready).
  2. Descend to D12+ with the djinni adjacent on the stairs; explore near the stairs, farm XP carefully toward XL9–10 (XL8 is low for D12). Look for shops (cloak of MR, rations), a unicorn horn, lizard corpses.
  3. MR plan B (see threats). Quest needs XL14 and alignment >= 20 (already >= 14).
  4. Prayer is on cooldown from T:6110: keep HP high; escapes = upstairs, Elbereth, scroll J, sleep wand, dig('>').
- Emergency plan: HP < 40% → Elbereth / upstairs / scroll J / sleep wand x (never toward an adjacent wall); prayer only if prayer_check() says the odds are good.

## Harness/helper calibration notes
- Verified this shift: `zap()` down a corridor, `fight()` on a sleeper, `fight_until_clear()` in a corridor, `explore()` (hidden passage, stairs, fountain), `avoid()`, altar drop test, `dip()` on a fountain (x2), `pray(force=True)` no-trouble prayer, `cont --reply` for the "Call a clear potion:" prompt, `bag_take` by identified name, `pickup(pattern)`.
- GAPS (details in harness_notes.md Shift 8): travel()'s final step attacks a monster that stepped onto the target (#148); `bag_take` patterns must use identified names; no `dip_into(item, potion)` helper; `#rub`/pick-axe unwield Excalibur silently; bogus "throne" features on D11 in `bin/nh info`; gremlin night rule missing from danger notes.
- Earlier notes still valid: never call `inventory()`/`here()` unless `obs.kind == 'command'`; `travel()` never autopicks up; pick-one menus close on the letter alone; `obs.menu` lists only the current page.
