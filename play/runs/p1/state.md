# p1 — current state (rewrite as things change)

## Character
- Name/role: P1 the Skirmisher — lawful female dwarven Valkyrie, god: Tyr (seed 101, local practice game)
- Turn / Dlvl / XL / HP / Pw / AC: **T:13184 / DL15 (main dungeon), standing ON THE LAWFUL ALTAR (48,19) at shift-13 end** / **XL11** (Exp 10562; XL12 at 20000, XL14 at 80000) / **129/129** / 24/24 / **AC -10** (blessed +2 GRAY DRAGON SCALE MAIL + +3 small shield + orcish helm + elven cloak + 3 points of divine protection). Wielding blessed rustproof **+6 EXCALIBUR** (long sword EXPERT; never enchant it again). Ring worn: f prot. from shape changers (right). Left hand FREE (fire res ring w removed T:13068 — intrinsic now). $1218.
- Last ate a food ration at T:13007. **Food is LOW**: e = 1 uncursed food ration, g = partly eaten ROTTEN ration (every bite re-rolls Blecch), Q pancake, U slime mold, j candy bar (~1300 nutrition). Eat fresh SAFE corpses (`corpse()`), pick up every food ration/lembas/cram.
- Attributes: St18 Dx14+ Co20 In10 Wi11 Ch7.
- Intrinsics: cold res (Valk), stealth (Valk), infravision (dwarf), speed (XL7), POISON RES, **FIRE RES (pyrolisk corpse T:13067, "momentary chill")**. **MAGIC RESISTANCE (GDSM).** Excalibur: auto-search, drain res. NO sleep resistance, NO reflection.
- Luck 0 (no luckstone); alignment record high; no peacefuls killed.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:1271 | welded cursed orcish dagger (MINOR trouble — mistake) | accepted, trouble NOT fixed, timeout reset |
| T:2016 | lycanthropy (MAJOR) | "well-pleased ... You feel purified" CURED |
| T:3401 | Weak from hunger (MAJOR; prayer_check 98%) | "well-pleased. Your stomach feels content." |
- The wish (T:10728) added 50-149; **the prayer timeout has certainly been 0 since ~T:10880**. Prayer available for major trouble (HP <= 21 at 129 max, XL11: max/6). On the DL15 LAWFUL ALTAR a no-trouble prayer would succeed and BLESS any potions of water standing on the altar (none carried yet).

## Equipment worn/wielded
- a: blessed rustproof +6 EXCALIBUR (wielded). c: uncursed +3 small shield. x: blessed +2 GRAY DRAGON SCALE MAIL (MR). n: uncursed +0 orcish helm. V: uncursed +0 faded pall = ELVEN CLOAK. Ring f (prot. from shape changers, right).

## Key inventory (letters)
- **A: uncursed UNICORN HORN** — cured stun (booby-trapped door) and hallucination (black light) at once this shift.
- **T: uncursed MAGIC MARKER (0:35)**. Can write KNOWN types: identify, enchant weapon, light, fire, amnesia, teleportation, scare monster, create monster, gold detection, **REMOVE CURSE — write it BY LABEL: `write_scroll('XOR OTA')` (type is only *named*; dowrite() matches the real name "remove curse" first and then fails 14/15 — the label goes through label_known() and always works; write.c)**. No blank scrolls: blank l (scroll of light) by dipping it in a fountain.
- **Escapes: Z and G = WAND OF TELEPORTATION** (Z 2 charges used of 4-8, G unknown). **k: uncursed scroll of teleportation.** Elbereth. Stairs. Prayer.
- **E: wand of lightning (0:4)** (only along a line whose first wall is >= 7 squares away). **S: wand of striking.** H: uncursed elven dagger.
- **D: uncursed BAG OF HOLDING ("BoH prize")**, 6 items: scroll ELAM EBOW (uncursed, unknown), 2 scrolls of FIRE (sliming cure), yellow spellbook, **SWIRLY potion = HEALING** (uncursed), wand of lightning (0:2), wand of striking. **Pick-axe b is in the MAIN PACK** (`bag_put('D','b')` before any shop).
- Rings (uncursed unless noted, unknown): **J twisted (base 300: conflict/polymorph/poly control/teleport control — NEVER wear-test)**, **K = REGENERATION**, **w = FIRE RESISTANCE (redundant now)**, m coral (150), y bronze (BLESSED, 100), R ivory (100), I wire (100), C clay, u opal.
- Potions (all uncursed, altar-tested T:13184): **i black = probably OBJECT DETECTION** (dropped by a wood nymph; nymphs are generated with it), F dark green, P golden, N murky. No water.
- Scrolls: l uncursed LIGHT (blank source), k teleportation.
- Spellbooks L pink, M cyan (uncursed; sell; don't read).
- Tools: d uncursed KEY, W blessed oil lamp (LOW), v can of grease, h tin opener, b pick-axe.
- Gems (uncursed, unidentified): p black, q 2 green, s 3 red, t 2 orange.
- NO lizard corpse (stoning cure = prayer only), no holy water.

## Identified appearances
- Scrolls: ZELGO MER identify, EIRIS SAZUN IDISI amnesia, GARVEN DEH light, HACKEM MUCHE fire, TEMOV teleportation, FOOBIE BLETCH enchant weapon, KERNOD WEL scare monster, THARR create monster, **ZLORFIK = GOLD DETECTION** (read T:12373), **XOR OTA = REMOVE CURSE** (named; my copy was cursed: "scroll disintegrates"). NR 9 (200) = earth or taming. ELAM EBOW, DUAM XNAHT (100) unknown.
- Potions: yellow sickness, brilliant blue blindness, cyan oil, pink gain level, **swirly HEALING** (umber hulk drank two), sky blue = confusion or booze; black probably object detection; dark green, golden, murky unknown.
- Wands: marble lightning, iridium striking, oak magic missile, crystal speed monster, short TELEPORTATION, zinc nothing.
- Rings: diamond fire resistance, iron protection from shape changers, engagement REGENERATION, agate = base 150.
- Tools: "bag" = sack, BoH is D; "lamp" base 50 = magic lamp.

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1 | main | `<` (76,4). `>` (54,7). SINK (55,6). |
| 2 | main | `<` (46,16). `>` (48,7). FOUNTAIN (25,6). TRAP DOOR (71,8) = shaft to DL5. |
| 3 | main + Mines branch | `<` (19,9). General store NW (3-7,5-8). Main `>` (29,16); MINES `>` (46,18). |
| 4 | main | `>` (20,14); hidden door (17,14) -> W room with `<` (5,9). Sleeping gas trap (58,15). |
| 5 | main | `<` (59,16). `>` (70,16). |
| 6 | main | ORACLE. `<` (9,7). `>` (65,10). Fountains (38,12) (39,11) (39,13) (40,12). |
| 7 | main (Sokoban up) | `<` (5,7). `>` (13,8). Sokoban `<` (14,15) under the hill-orc statue. |
| 8 | main | `<` (7,8). `>` (47,8). Fountains (42,8) and (48,16). SINK (22,3). Pit (7,11). |
| 9 | main | `<` (64,5). `>` (72,13) in a closet behind door (71,12). |
| 10 | main | `<` (19,7). NEUTRAL ALTAR (Odin) (16,7). `>` NOT FOUND; dug down from (39,16). Green mold (43,13). |
| 11 | main | `<` (18,5), `>` (10,14). |
| 12 | main | `<` (9,16), `>` (11,5). Mountain nymph with a wand of teleportation roams it. |
| **13** | main | **QUEST PORTAL: MAGIC PORTAL at (73,17) in the SE room** (found T:12322; not entered). `<` (34,16), `>` (6,13). Rolling boulder trap (17,13), anti-magic field (47,4), pit (51,19). Light brown spellbook left at (30,10). |
| 14 | main | `<` (54,5), `>` (35,7). Closed VAULT at (75-76,17-18) (gold detection; not dug). Booby-trapped door already exploded (~41,3). |
| **15** | main | `<` (11,4). **LAWFUL ALTAR to Tyr (48,19)** in the SE room (door (43,17) was locked, unlocked; west doorway ~(42,19)). **ZOO somewhere unexplored** ("seal barking"). Teleport trap (35,18) (MR blocks it). CHEST at (2,16) (W room) not looted. `>` NOT FOUND yet. |
| Mines 1-8 | Mines | Minetown = Mines 3 (DL6): temple of Odin (neutral) (33,4), general store, hardware store; `>` (48,4) behind door (52,7). Mines' End (DL11): LUCKSTONE still in a SW closet (3,17)/(3,19). |
| Sokoban | Sokoban | ALL SOLVED, prize (BoH) taken. |

## Threats / known dangers
- Fire gazes/breath/claws (pyrolisk, fire elemental, red naga, hell hound) burn scrolls and boil potions even with fire resistance: close in and kill at once; keep important scrolls/potions in the BoH.
- Nymphs: most are generated ASLEEP (stealth won't wake them) — this one woke; "pretends to be friendly" = missed theft; one blow kills.
- Invisible things: black lights (hallucination: unicorn horn), stalkers ("It hits!": fight the `I`).
- Cockatrices: melee only with Excalibur; no lizard — prayer is the stoning cure.
- Soldiers/wand users: no reflection — avoid lines at range (sleep rays: no sleep resistance).

## Objective and plan (after shift 13)
1. **DL15 first**: explore the rest (find `>` and the ZOO; open the zoo only from a doorway chokepoint at full HP with `fight_until_clear`), loot the chest (2,16). **Use the altar**: sacrifice fresh corpses of hostile kills (`#offer` standing on it) for Luck/possible gift; bring any potions of water here and pray when the timeout allows to make holy water (the timeout is 0 now — praying with no water only gives a minor boon and resets the timeout; not worth it without water).
2. **Food**: pick up all rations, eat fresh safe corpses; don't dive with < 2 rations.
3. XP toward XL14 (quest; portal DL13 (73,17)). Wraith corpses = +1 level each (eat at once). Continue down DL16-18 carefully (AC-10, MR, fire res, Excalibur +6), chokepoints; go back up at < 50% HP.
4. **Reflection** still missing — required before Medusa/Castle. Sleep resistance would help.
5. Blank scrolls: dip l (light) in a fountain (DL8 has 2) -> write REMOVE CURSE by label or identify (J twisted ring first).
6. Luckstone at Mines' End when convenient; vault on DL14 (~3000 gold) + $1218 could buy protection (400 x XL) at the Minetown priest — low priority.
