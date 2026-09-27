# p1 — current state (rewrite as things change)

## Character
- Name/role: P1 the Skirmisher — lawful female dwarven Valkyrie, god: Tyr (seed 101, local practice game)
- Turn / Dlvl / XL / HP / Pw / AC: **T:~11280 / DL8 (main dungeon), standing on the `>` (47,8) at shift end** / **XL10** (Exp 5302; XL11 at 10000) / **121/121** / 21/21 / **AC -10** (blessed +2 GRAY DRAGON SCALE MAIL + +3 small shield + orcish helm + elven cloak + 3 points of divine protection). Wielding blessed rustproof +2 EXCALIBUR (long sword EXPERT). Rings worn: f prot. from shape changers (right), w fire resistance (left). $105.
- Last ate a ration at T:10611. St dropped by exercise abuse at T:10756 ("You feel weak!") — check ^X. Food: P + e(x3) = 4 rations, Q pancake, U slime mold, j candy bar.
- Attributes: St18 Dx13 Co20 In10 Wi11 Ch7 (Ch7 => shop prices x1.5, sell offers base/2).
- Intrinsics: cold res (Valk), stealth (Valk), infravision (dwarf), speed (XL7), POISON RESISTANCE (T:6853). **MAGIC RESISTANCE from the GDSM (wished T:10728).** NO sleep resistance, no reflection. Excalibur: auto-search, drain res.
- Luck 0; alignment record high (one "hypocrite" hit T:6808); no peacefuls killed.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:1271 | welded cursed orcish dagger (MINOR trouble — mistake) | accepted, trouble NOT fixed, timeout reset |
| T:2016 | lycanthropy (MAJOR) | "well-pleased ... You feel purified" CURED |
| T:3401 | Weak from hunger (MAJOR; prayer_check 98%) | "well-pleased. Your stomach feels content." Prayer available: prayer_check() p_safe 1.0 (6400+ turns). Always `prayer_check()` first; major trouble at XL9 = HP <= 18 (110/6). |

## Equipment worn/wielded (letter: item)
- **a: blessed rustproof +2 EXCALIBUR (wielded)**. c: uncursed +3 small shield. **x: blessed +2 GRAY DRAGON SCALE MAIL (MR; wished from the magic lamp T:10728, worn T:10740).** n: uncursed +0 orcish helm. V: uncursed +0 faded pall = ELVEN CLOAK (worn over the GDSM). Splint mail and burnt studded leather left on the Minetown altar.

## Key inventory (letters) — main pack is lean; the rest is in the BoH
- **D: uncursed BAG OF HOLDING ("BoH prize")** containing: **PICK-AXE** (bought 75; never carry it openly into a shop — shopkeepers block the door; never dig in Minetown), scrolls o ELAM EBOW (unknown, uncursed), t blank, A + u fire, x + l light, potion M swirly (unknown), rings W bronze (BLESSED, unknown), m coral, K engagement, R ivory, J twisted, I wire (all uncursed, unknown: sell-offer price-ID them), h magic marker (0:82) CURSED, wands z lightning (0:2), g striking (2nd).
- **B: blessed scroll of TELEPORTATION + k: scroll of teleportation (found Mines 6)** (escape; useless on no-teleport levels).
- **i: HOLY WATER (blessed clear potion; altar-tested T:10724) — remove-curse / lycanthropy insurance, or uncurse the magic marker. l: uncursed clear potion = WATER (blank a scroll, or holy water on a lawful altar).** **d: KEY** (skeleton key, bought 15). g: orange spellbook (unknown, sell), h: tin opener.
- **Z: WAND OF TELEPORTATION (called; engrave-tested + zap-tested T:9391; 2 charges used, 3-6 left)** — escape: `zap('Z', '.')` at self; or zap a nasty monster away. **E: wand of lightning (0:4)** (6d6 ray, bounces: only along a line whose first wall is >= 7 squares away). **S: wand of striking** (3 charges used).
- Food: **P, X, e(x4): 6 food rations** (4 bought T:9885 after selling the 2 potions of oil for 250), Q pancake, U slime mold, j candy bar.
- H: uncursed elven dagger (throwable). v: can of grease.
- **$28.** Protection bought (3600). Next protection point costs 400 x XL again (4000 at XL10) — low priority now.
- No healing potions, no unicorn horn, no lizard corpse. 1 holy water (i). Escapes: wand Z, scroll B, Elbereth (single monsters only), stairs. Prayer available (prayer_check() first).
- **u: GRAY STONE from the Catacombs NE closet (70,10) = LUCKSTONE or FLINT (50/50; price-ID it in Minetown: luckstone sell offer 30, flint ~0; or read an identify scroll). The other spots (3,17)/(3,19) hold the other stone + nothing.**
- **Gems carried (unidentified): p black, q 2 green, s 3 red, t 2 orange** (Catacombs seeds diamonds/emeralds/rubies/amethysts). **PICK-AXE = b, in the MAIN PACK since T:10990 (bag_put it before any shop). W: blessed OIL LAMP (the ex-magic lamp, lit; djinni spent T:10728).** Wand S striking: 5 charges used. r: scroll NR 9 (= earth?), o: amnesia (sell).
- Left behind: Mines 2 `<` (25,5): 11 cursed darts, 2 eggs. Minetown altar (33,4): cursed elven dagger, burnt studded leather. Hardware store: my old sack. DL6 (8,5): scale mail. DL3 `<` room: +0 dagger etc. Soko3 (33,9): elf gear (elven shield/bow/arrows/broadsword...). Mines 1 (18,15): a ring.

## Identified appearances
- Scrolls: ZELGO MER identify, EIRIS SAZUN IDISI amnesia, GARVEN DEH light, HACKEM MUCHE fire, TEMOV teleportation, FOOBIE BLETCH enchant weapon, KERNOD WEL scare monster. **THARR and NR 9: both base 200 = create monster / earth / taming (NR 9 came from Sokoban => almost surely EARTH; THARR then = create monster or taming).** ELAM EBOW unknown. ZLORFIK, DUAM XNAHT: base-100 class.
- Potions: yellow sickness, brilliant blue blindness, cyan oil; swirly unknown (base 100 or 50?).
- Wands: marble lightning, iridium striking, oak magic missile (seen), **crystal SPEED MONSTER (sold), short TELEPORTATION, zinc NOTHING (sold; base 100, no engrave effect)**.
- Rings: diamond fire resistance, iron protection from shape changers; **agate = base 150 (cursed one sold)**.
- Tools: "bag" = sack (L, left), BoH is D; "lamp" at base 50 = magic lamp.

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1 | main | `<` (76,4). `>` (54,7) big room — cursed orcish dagger on it. SINK (55,6). |
| 2 | main | `<` (46,16). `>` (48,7). FOUNTAIN (25,6). TRAP DOOR (71,8) = shaft to DL5. |
| 3 | main + Mines branch | `<` (19,9) (werejackal pack frozen next to it at (19,8); harmless with ring f worn). Annootok's general store NW (3-7,5-8) — food rations. **Main `>` (29,16); MINES `>` (46,18).** |
| 4 | main | `>` (20,14); hidden door (17,14) -> W room with `<` (5,9). SLEEPING GAS TRAP (58,15). |
| 5 | main | `<` (59,16). `>` (70,16). Route between them is roundabout (north room, doors (59,7)/(64,4)). |
| 6 | main | ORACLE LEVEL. `<` (9,7). `>` (65,10) (water demon KILLED T:8820). Fountains (38,12) (39,11) (39,13) (40,12) — use them to dilute potions into WATER for holy water. Peaceful Oracle. Scale mail at (8,5). |
| 7 | main (Sokoban entry) | `<` (5,7). `>` (13,8) in room B. Sokoban `<` = (14,15) under the hill-orc statue. Orc gear (57,4),(58,8). |
| **8** | main | `<` (7,8) NW room; `>` (47,8) in the W-centre room (fountain (42,8), tool (46,8)). PIT (7,11). SINK (22,3) in the N room (door (17,3) was locked: opened with the key). Fountain (48,16). Hidden passage (11-13,13). Killer bees near the `<` on arrival. |
| Mines 1 (Dlvl 4) | Mines | `<` (6,20), `>` (27,6). Pit (4,7). Dug bypass (9,19)-(8,19) into the stair nook (the corridor (6-13,18) gets blocked by peaceful gnomes). |
| Mines 2 (Dlvl 5) | Mines | `<` (25,5), `>` (16,10). Iron piercer near (20,11). |
| **Mines 3 (Dlvl 6) = MINETOWN = GROTTO TOWN** | Mines | **`>` (48,4)** in the closet room (48-52,4) behind door (52,7) (unlocked with my key; lock pick left on (52,4)). `<` (3,2) (arrival ambush by 3 soldier ants, all killed). **TEMPLE OF ODIN (neutral, cross-aligned; never #offer/pray there): altar (33,4), door (33,6), peaceful priestess.** **General store (Asidonhopo) (61-69,10-11), door (68,9): 4 food rations @68, scimitar, sling.** **Hardware store (Nosalnef) (59-62,14-16), door (58,15): key 15, large box 12, blindfold 30, leash 30, tin opener 45, drum 38, lock pick 30.** Fountains (12,16) (52,10) (68,19) — never use (Watch). Doors not yet opened: (73,4), (73,7), (71,19), (60,7), (52,7), (9,12), (22,17), (27,15). Door (71,19) locked (chest closet per wiki). |
| Mines 4 (Dlvl 7) | Mines | `<` (6,12), `>` (73,17). TELEPORT TRAP (7,12), land mine->pit (13,3), bear trap (70,7), blue jelly (64,7). |
| Mines 5 (Dlvl 8) | Mines | `<` (73,6), `>` (60,12). Pit (72,9). Lynx seen. |
| Mines 6 (Dlvl 9) | Mines | `<` (68,13), `>` (7,12). Peaceful gnomes/dwarves; lichen NW. |
| Mines 7 (Dlvl 10) | Mines | `<` (20,14), `>` (27,16). Web (26,8), key on (26,12), blue jelly (21,11), stalker corpse (22,10). |
| **Mines 8 (Dlvl 11) = MINES' END (CATACOMBS)** | Mines | `<` (44,12) in the 9x5 room, hidden doors (39,12) (unfound) and (49,12) (open). Map = wiki Catacombs with screen x = col+1, y = line+3. LUCKSTONE/FLINT SPOTS: NE closet corner (70,10) [door (75,9) open, reached via the strip x=76 from (76,12) — I dug (76,11)], SW closets (3,17) and (3,19) [secret doors (4,17)/(4,19)]: one has the luckstone, one a flint, one nothing; the stones sit on LEVEL TELEPORTERS (no MR: stepping = ~50% random level 1-10, trap then gone). Gray stone pile also at (68,15). Spellbook (76,8). Maze, unmappable, dark: keep the magic lamp lit. Two vampires somewhere (ring f keeps them in V form). |
| Sokoban 3-6 | Sokoban | ALL SOLVED, zoo cleared, prize taken. Leftover elf gear on Soko3 (33,9). |

## Threats / known dangers
- Soldier ants (speed 18, bite 2d4 + sting 3d4; NOT stalkers): fight from a staircase square, climb at ~55% HP. Black lights (2 met): invisible, explode -> ~60-100 turns Hallu: stand still, attack only what attacks you.
- Sokoban levels are no-teleport. Cockatrices exist in this dungeon (wield a weapon; never eat/touch). Elves/humans ignore Elbereth. Dust Elbereth erodes one letter per scared monster (3.6): single-monster tool only.
- Minetown: no fountain use, no door kicking, no digging, no theft. Cross-aligned temple: no prayer/offering there.
- MR now covered (GDSM). Still NO REFLECTION: avoid lining up with wand users; Castle only with reflection too (PLAYBOOK A1 prefers both).

## WISH DONE (T:10728, Minetown temple)
- Lamp W was already BLESSED (bought so; never altar-tested before). First #rub: djinni "I am in your debt" -> wished `blessed +2 gray dragon scale mail` -> got it blessed +2 (amber flash; AC -5 -> -10). Holy water i NOT used. Prayer timeout +50..149 from the wish (irrelevant: 7300 turns since the last prayer).

## Objective and plan (after shift 11)
0. **Done this shift: WISH -> blessed +2 GDSM (MR). AC -10. XL10.** Gray stone was a FLINT (left in the shop).
1. **Main dungeon down from the DL8 `>` (47,8)**: XP toward XL14 (quest), a LAWFUL ALTAR (holy water: put water potions on it and pray when prayer_check() is safe; BUC tests), unicorn horn, lizard corpses, REFLECTION (silver DSM/amulet/shield). Big Room / quest portal (DL11-16) ahead. Still no reflection: never stand in line with soldiers/wand users at range.
2. **Scroll-writing project**: blank scrolls (dip the amnesia scroll o and the 2 light scrolls (in the BoH) into a fountain — DL8 has (42,8) and (48,16) — or into the water potion l), then write IDENTIFY with the CURSED magic marker h (0:82; cursed identify still IDs one item each; writing needs the blank + marker out of the bag, `apply h`, "identify"). Read them on: J twisted ring (base 300: conflict/polymorph/poly control/teleport control), K engagement (200: free action/levitation/regen/searching/slow digestion/teleportation), m coral (150), y bronze (blessed, 100), F dark green potion, M swirly potion (BoH), C clay ring (unknown price), z ZLORFIK, ELAM EBOW (BoH). Never wear-test J.
3. **A: scroll of enchant weapon (BUC unknown)**: altar-test first (cursed = -1), or dip it into the holy water i (-> blessed: Excalibur +1..+3, cap +5) and read it.
4. **Holy water i**: keep as remove-curse / emergency insurance unless used on A or the marker.
5. **Luckstone**: still at Mines' End SW closets (3,17)/(3,19) (secret doors (4,17)/(4,19)); with MR the level teleporters are harmless ("wrenching sensation"). Do it when next in the Mines (also: protection purchase = 4000 zm at XL10; Minetown temple).
6. Pick-axe b is in the MAIN PACK: bag_put('D','b') before entering any shop. Sink at DL8 (22,3) (ring kick-test / potion ID) if ever useful.
