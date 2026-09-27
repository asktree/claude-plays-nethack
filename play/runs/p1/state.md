# p1 — current state (rewrite as things change)

## Character
- Name/role: P1 the Skirmisher — lawful female dwarven Valkyrie, god: Tyr (seed 101, local practice game)
- Turn / Dlvl / XL / HP / Pw / AC: **T:9807 / MINETOWN (Mines level 3 = Dlvl 6) at (66,15)** (1-wide N-S corridor between the general store above and the hardware store/fountain room below) / **XL9** (Exp 3998; XL10 at 5120) / **110/110** / 18/18 / **AC -5** (splint mail + +3 small shield + orcish helm + elven cloak + **3 points of divine protection bought T:9719**). Wielding blessed rustproof +2 EXCALIBUR (long sword EXPERT). Rings worn: f prot. from shape changers (right), w fire resistance (left).
- Not hungry (cram ration eaten T:9650; two rings worn => Hungry again ~T:10200). No monsters hostile in view at shift end; Minetown watch + peaceful gnomes/hobbits/gnomish wizard around.
- Attributes: St18 Dx13 Co20 In10 Wi11 Ch7 (Ch7 => shop prices x1.5, sell offers base/2).
- Intrinsics: cold res (Valk), stealth (Valk), infravision (dwarf), speed (XL7), POISON RESISTANCE (T:6853). NO sleep resistance, no MR, no reflection. Excalibur: auto-search, drain res.
- Luck 0; alignment record high (one "hypocrite" hit T:6808); no peacefuls killed.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:1271 | welded cursed orcish dagger (MINOR trouble — mistake) | accepted, trouble NOT fixed, timeout reset |
| T:2016 | lycanthropy (MAJOR) | "well-pleased ... You feel purified" CURED |
| T:3401 | Weak from hunger (MAJOR; prayer_check 98%) | "well-pleased. Your stomach feels content." Prayer available: prayer_check() p_safe 1.0 (6400+ turns). Always `prayer_check()` first; major trouble at XL9 = HP <= 18 (110/6). |

## Equipment worn/wielded (letter: item)
- **a: blessed rustproof +2 EXCALIBUR (wielded)**. c: uncursed +3 small shield. **Y: uncursed splint mail (bought Minetown T:9664, altar-tested, worn T:9710).** n: uncursed +0 orcish helm. V: uncursed +0 faded pall = ELVEN CLOAK (worn over the splint mail). The burnt studded leather was left on the Minetown altar.

## Key inventory (letters) — main pack is lean; the rest is in the BoH
- **D: uncursed BAG OF HOLDING ("BoH prize")** containing: **MAGIC LAMP (uncursed; "lamp" bought for 75 = base 50 => magic lamp; DO NOT #rub until BLESSED: uncursed = 20% wish and the lamp is spent; blessed = 80%)**, **PICK-AXE** (bought 75; never carry it openly into a shop — shopkeepers block the door; never dig in Minetown), scrolls o ELAM EBOW (unknown, uncursed), t blank, A + u fire, x + l light, potion M swirly (unknown), C 2 potions of oil, rings W bronze (BLESSED, unknown), m coral, K engagement, R ivory, J twisted, I wire (all uncursed, unknown: sell-offer price-ID them), h magic marker (0:82) CURSED, wands z lightning (0:2), g striking (2nd).
- **B: blessed scroll of TELEPORTATION** (escape; useless on no-teleport levels).
- **Z: WAND OF TELEPORTATION (called; engrave-tested + zap-tested T:9391; 2 charges used, 3-6 left)** — escape: `zap('Z', '.')` at self; or zap a nasty monster away. **E: wand of lightning (0:4)** (6d6 ray, bounces: only along a line whose first wall is >= 7 squares away). **S: wand of striking** (3 charges used).
- Food: **P + X: 2 food rations**, Q pancake, U slime mold, j candy bar. (4 more food rations for sale at 68 each in the general store.)
- H: uncursed elven dagger (throwable). v: can of grease.
- **$65.** Protection bought (3600). Next protection point costs 400 x XL again (4000 at XL10) — low priority now.
- No healing potions, no unicorn horn, no lizard corpse, no holy water. Escapes: wand Z, scroll B, Elbereth (single monsters only), stairs. Prayer available (prayer_check() first).
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
| Mines 1 (Dlvl 4) | Mines | `<` (6,20), `>` (27,6). Ring at (18,15). Pit (4,7). |
| Mines 2 (Dlvl 5) | Mines | `<` (25,5), `>` (16,10). Iron piercer near (20,11). |
| **Mines 3 (Dlvl 6) = MINETOWN** | Mines | **I AM HERE (66,15).** `<` (3,2) (arrival ambush by 3 soldier ants, all killed). **TEMPLE OF ODIN (neutral, cross-aligned; never #offer/pray there): altar (33,4), door (33,6), peaceful priestess.** **General store (Asidonhopo) (61-69,10-11), door (68,9): 4 food rations @68, scimitar, sling.** **Hardware store (Nosalnef) (59-62,14-16), door (58,15): key 15, large box 12, blindfold 30, leash 30, tin opener 45, drum 38, lock pick 30.** Fountains (12,16) (52,10) (68,19) — never use (Watch). Doors not yet opened: (73,4), (73,7), (71,19), (60,7), (52,7), (9,12), (22,17), (27,15). **`>` NOT FOUND YET** (unexplored: east beyond (73,x)/(71,19), southwest). |
| Sokoban 3-6 | Sokoban | ALL SOLVED, zoo cleared, prize taken. Leftover elf gear on Soko3 (33,9). |

## Threats / known dangers
- Soldier ants (speed 18, bite 2d4 + sting 3d4; NOT stalkers): fight from a staircase square, climb at ~55% HP. Black lights (2 met): invisible, explode -> ~60-100 turns Hallu: stand still, attack only what attacks you.
- Sokoban levels are no-teleport. Cockatrices exist in this dungeon (wield a weapon; never eat/touch). Elves/humans ignore Elbereth. Dust Elbereth erodes one letter per scared monster (3.6): single-monster tool only.
- Minetown: no fountain use, no door kicking, no digging, no theft. Cross-aligned temple: no prayer/offering there.
- No MR/reflection: never the Castle/Gehennom; avoid soldiers with wands.

## Objective and plan
1. **Next shift, first**: find the Minetown `>` (explore east: doors (73,4), (73,7), (71,19); and the southwest). Optional: sell-offer price-ID the 6 unknown rings in the general store (drop, read the offer, answer `n`, pick up).
2. **Magic lamp -> wish (top priority project)**: make HOLY WATER: dilute the 2 potions of oil (or the swirly potion) twice in an Oracle-level fountain (DL6, 4 fountains; each dip risks drying it / a water moccasin, fine) to get uncursed water; then find a LAWFUL altar and pray on it with the water on the altar when prayer_check() is safe and there is no trouble (timeout is 0 now: 6400 turns since T:3401) -> holy water; dip the lamp -> blessed; `#rub` -> 80% wish: GRAY DRAGON SCALE MAIL (magic resistance). Alternative if a co-aligned altar is far: keep the lamp until one is found (Mines' End/main dungeon altars).
3. Then: main dungeon down from DL7 `>` (13,8) (DL8+) for XP/loot with AC -5; or Mines' End luckstone (5-6 Mines levels below Minetown; XL10+ advised). Watch for a unicorn horn, lizard corpses, potions of water/holy water, gauntlets/boots/dwarvish iron helm.
4. Uncurse the magic marker (holy water #2 or remove curse) -> write scrolls (enchant armor, remove curse, genocide...) with the blank scroll.
5. Food: 2 rations + pancake + slime mold + candy bar (~1700 turns); buy the remaining 4 rations when gold allows (68 each).
