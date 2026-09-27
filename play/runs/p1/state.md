# p1 — current state (rewrite as things change)

## Character
- Name/role: P1 the Skirmisher — lawful female dwarven Valkyrie, god: Tyr (seed 101, local practice game)
- Turn / Dlvl / XL / HP / Pw / AC: T:3899 / Dlvl 6 / **XL6** (Exp 322 at T:3899; XL7 at 640) / 65/72 / 11/11 / AC2
- Position (shift 5, T:3922): DL7, just arrived on the `<` (5,7) (small room 3-6,6-8, doorway E (7,7)). DL6 above has a HOSTILE WATER DEMON loose near its `>` (65,10) and the Oracle chamber: do not go back up through it.
  Not hungry: prayer at T:3401 set nutrition to 900 -> Hungry ~T:4150, Weak ~T:4250 (Hungry->Weak takes only ~100 turns!).
- Attributes: St18 Dx12 Co20 In10 Wi10 Ch7 (Ch7 => shop prices +50%)
- Intrinsics: cold res (Valk), stealth (Valk), infravision (dwarf), speed at XL7. Long sword skill: SKILLED (enhanced T:3441).
- Luck 0; alignment record high ("well-pleased" at T:3401); no peacefuls killed.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:1271 | welded cursed orcish dagger (MINOR trouble — mistake) | accepted, trouble NOT fixed, timeout reset |
| T:2016 | lycanthropy (MAJOR) | "well-pleased ... You feel purified" CURED |
| T:3401 | Weak from hunger (MAJOR; prayer_check 98%, 1382 turns after the 2nd) | "well-pleased. Your stomach feels content." nutrition 900. **No prayer before ~T:4400** unless life-or-death; always `prayer_check()` first. |

## Equipment worn/wielded (letter: item)
- **WIELDED: a: uncursed +1 long sword, THOROUGHLY RUSTY** (3 fountain dips at T:3225-3227; -3 damage until Excalibur restores it — Excalibur creation clears erosion and makes it rustproof)
- c: uncursed +3 small shield (worn), e: +0 studded leather armor (worn), n: +0 orcish helm (worn) -> AC2 [seen]
- The cursed corroded orcish dagger lies on the DL1 `>` (54,7). Never pick it up.

## Key inventory (letters)
- **z, E: TWO WANDS OF LIGHTNING** (z engrave-identified T:2565, 1 charge used; E found DL6 (11,18) T:3464, charges unknown) — 6d6 ray, bounces (never zap toward a wall next to me; never in a 3-wide room). `zap('z', dir)`.
- w: uncursed RING OF FIRE RESISTANCE (not worn). f: iron ring (100zm class, unknown, NOT worn). y: figurine of a coyote.
- h: magic marker (charges unknown).
- Scrolls: i EIRIS SAZUN IDISI (base 200), x GARVEN DEH (unknown), A HACKEM MUCHE (base 100 class), B TEMOV (unknown). Identify scroll k USED.
- Potions: q yellow, u brilliant blue (unknown), C cyan (base 250 class: acid or oil).
- **Food: F: 2 FOOD RATIONS (found DL6 T:3675 and T:3813)**; g: 2 candy bars, j: 1 candy bar (g/j differ in BUC, both unknown), D: partly eaten candy bar = the piece flagged rotten at T:3116 (eat.c touchfood() splits one item off BEFORE the rotten roll, so only D carries the orotten flag; g/j just have the normal 1/7 old-food roll). Priority: fresh SAFE corpses when Hungry, then rations.
- $98. No escape items, no healing potions, no unicorn horn, no lizard corpse.
- Left behind: DL3 `<` room: +0 dagger b (18,5), orcish dagger p (21,5), violet gems (werejackal territory). DL6 (8,5): scale mail (unknown BUC, 250 wt, only +1 AC — left).

## Identified appearances
- ZELGO MER -> identify (used). EIRIS SAZUN IDISI -> base 200 class. ZLORFIK, DUAM XNAHT, HACKEM MUCHE -> base 100 class.
- marble wand -> lightning. diamond ring -> fire resistance. iron ring -> 100zm class.
- swirly potion -> base 100; cyan -> 250 (acid/oil); murky -> 50.
- Scroll price targets: remove curse/enchant armor base 80 (sell offer 40); enchant weapon/blank base 60 (offer 30).

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1 | main | `<` (76,4). `>` (54,7) big room (50-61,5-9) — cursed orcish dagger on it. SINK (55,6). Fully explored. |
| 2 | main | `<` (46,16). `>` (48,7). **FOUNTAIN (25,6)** (Excalibur backup — but reaching DL2 means passing the DL3 `<` werejackal camp). TRAP DOOR (71,8) = shaft to DL5. Fully explored. |
| 3 | main + Mines branch | `<` (19,9) room (18-20,4-9). ARROW TRAP (19,6). **WEREJACKAL (d form) + 4 jackals + fox frozen next to the `<` at (19,8)**. Annootok's general store NW (3-7,5-8) — food rations here. `>` (29,16) and `>` (46,18) — one is the Mines, the other leads to DL4 `<` (5,9). Unexplored east room via door (60,8). |
| 4 | main | `>` (20,14) room (18-27,11-14); hidden door (17,14) W (now open) -> corridor -> W room (3-8,9-13) with **`<` (5,9)**. Hidden door (43,9) -> gold room (44-50,6-10), closed door (51,9) E, doorway (43,6) W with the row-6 corridor (boulder pushed to (27,6), STUCK there — dead end or hidden corridor). Food room (58-61,12-15): **SLEEPING GAS TRAP (58,15)** (known to the harness), old gnome corpse; boulder (63,14) outside its door (62,14) — enter via (62,12). NE room (73-76,3-5), E room (74-76,14-18). South half of the map (rows 16-21) unexplored. Level "explored" per explore(). |
| 5 | main | Arrival room (59-65,4-8). **`<` (59,16)** room (56-60,13-16). **`>` (70,16)** room (67-75,14-17). **FOUNTAIN (26,8) DRIED UP (T:3228)**. **BURNED ELBERETH (45,18)** in the big S room (33-46,17-19); its E door (47,18) KICKED OPEN (broken) -> direct corridor to the `<`. Centipede corpse (40,17). Fully explored. |
| 6 | main | **ORACLE LEVEL.** `<` (9,7) lit NW room (7-17,4-7): scale mail (8,5) left. `>` (65,10) in the E room (56-69,8-10), door (55,10). Delphi room (34-44,8-16), doors: (43,7) N (kicked open), (33,10) & (33,15) W doorways; 8 centaur STATUES (harmless). Oracle's chamber walls (37-41,10-14), doorway (37,11); **FOUNTAINS (38,12) (39,11) (39,13) (40,12)**, peaceful Oracle (39,12) — never attack. Corridors: row 5-6 E from the `<` room to col 48 -> (46,8)-(46,18) S -> row 18 E/W; tiny room (24-26,17-19) with armor (24,18)+spellbook (25,18), boulders (25,14),(26,15) NE of it (unexplored beyond). Rock mole corpse (35,11) T:3813. Killed here: rock mole x2, monkey, dog, kobold zombie, rock piercer, giant bat, floating eye (no corpse). |

## Threats / known dangers
- DL3 werejackal pack at the `<` (19,8). Never melee it in d form (bite = lycanthropy 1/4; prayer spent until ~T:4400).
- Poisonous biters/stingers (centipedes, killer bees, water moccasins, soldier ants): each poisoned hit has a 1/30 instadeath roll (1/8 of hits poison) — avoid swarms without poison resistance; Elbereth works on them.
- No healing/escape items: keep HP > 60% before any fight; refuges: DL6 `<` (9,7) [stairs], DL5 burned Elbereth (45,18). Prayer NOT available until ~T:4400.
- Monkeys/nymphs steal: drop the wands + marker before fighting a thief (worked T:3382).
- Dust Elbereth degrades ~1/76 per turn while standing on it and when walked over: re-engrave and verify with `engraving_here()` right before relying on it. Attacking from any Elbereth square erases it (3.6) — never fight from (45,18).

## Objective and plan
1. **Explore DL6** (find `>`, fountains, food): start from `<` (9,7); frontiers: the long east corridor (rows 5-6), the SE rooms. Fight one at a time near the stairs; retreat up at HP < 50%.
2. **Excalibur**: dip `a` at the next fountain (Oracle level DL6-9 has 4) at FULL HP: engrave dust Elbereth on the adjacent square first, `here()` to confirm the fountain, `#dip<CR>`, `a`, `y`; read every outcome; 1/30 each of water demon (flee — equal speed, it never catches a straight-line runner; 15% it grants a WISH: "blessed +2 gray dragon scale mail"), water nymph (steals), water moccasins (Elbereth + doorway choke). Each failed dip: 1/3 the fountain dries. Success removes the rust.
3. **Food**: eat fresh safe corpses immediately when Hungry (~T:4150); the rotten candy bars only on a safe square. Consider buying rations at Annootok's when a safe DL3 route exists (Mines branch `>` on DL3 avoids the `<` camp).
4. Then Sokoban (the `<` on the level below the Oracle) and the Mines (gnomes/dwarves peaceful) for Minetown's altar/shops; XL6 at 320 Exp.
