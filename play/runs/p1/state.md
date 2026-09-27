# p1 — current state (rewrite as things change)

## Character
- Name/role: P1 the Skirmisher — lawful female dwarven Valkyrie, god: Tyr (seed 101, local practice game)
- Turn / Dlvl / XL / HP / Pw / AC: **T:11997 / DL13 (main dungeon, QUEST PORTAL LEVEL), standing on the `<` (34,16) at shift-12 end** / **XL10** (Exp 6156; XL11 at 10000, XL14 at 80000) / **121/121** / 21/21 / **AC -10** (blessed +2 GRAY DRAGON SCALE MAIL + +3 small shield + orcish helm + elven cloak + 3 points of divine protection). Wielding blessed rustproof **+6 EXCALIBUR** (long sword EXPERT; "suddenly vibrates unexpectedly" at +6 = NEVER read enchant weapon on it again). Rings worn: f prot. from shape changers (right), w fire resistance (left). $708.
- Last ate a food ration at T:11318. Food: e = 3 uncursed food rations, Q pancake, U slime mold, j candy bar (enough for ~4000 turns).
- Attributes: St18 Dx14+ Co20 In10 Wi11 Ch7 (Dex up at T:11729; the unicorn horn restored a lowered attribute at T:11965).
- Intrinsics: cold res (Valk), stealth (Valk), infravision (dwarf), speed (XL7), POISON RESISTANCE. **MAGIC RESISTANCE (GDSM).** Excalibur: auto-search, drain res. NO sleep resistance, NO reflection.
- Luck 0 (no luckstone); alignment record high; no peacefuls killed.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:1271 | welded cursed orcish dagger (MINOR trouble — mistake) | accepted, trouble NOT fixed, timeout reset |
| T:2016 | lycanthropy (MAJOR) | "well-pleased ... You feel purified" CURED |
| T:3401 | Weak from hunger (MAJOR; prayer_check 98%) | "well-pleased. Your stomach feels content." |
- The wish (T:10728) added 50-149 to the timeout; rnz(350) after T:3401 is <= ~3500, so **the prayer timeout has certainly been 0 since ~T:10880**. Prayer is available for major trouble (HP <= 20 at 121 max, XL10: max/6). On a CO-ALIGNED (lawful) altar a no-trouble prayer now would succeed and bless water potions standing on the altar.

## Equipment worn/wielded
- a: blessed rustproof +6 EXCALIBUR (wielded). c: uncursed +3 small shield. x: blessed +2 GRAY DRAGON SCALE MAIL (MR). n: uncursed +0 orcish helm. V: uncursed +0 faded pall = ELVEN CLOAK. Rings w (fire res, left), f (prot. from shape changers, right).
- The obs line "!! you WIELD the blessed rustproof +6 Excalibur — not a weapon" is a HARNESS FALSE ALARM (inventory confirms "(weapon in hand)").

## Key inventory (letters)
- **A: uncursed UNICORN HORN** (from the DL10 gray unicorn; altar-tested). Apply for Conf/Stun/Blind/Hallu/sickness — it worked at once on confusion.
- **T: uncursed MAGIC MARKER (0:35)** (was cursed; uncursed with the holy water T:11284). Costs: identify 7-13, enchant weapon/armor/remove curse 8-15, scare monster/teleport 10-19. Can only write KNOWN types: identify, enchant weapon, light, fire, amnesia, teleportation, scare monster, create monster. No blank scrolls left (blank more with fountain dips: `dip('<scroll>')` on a fountain square).
- **Escapes: Z and G = WAND OF TELEPORTATION** (identified T:11849; Z has 2 charges used of 4-8, G unknown) — `zap('Z', '.')` at self, or zap a nasty monster away. **k: uncursed scroll of teleportation** (the blessed one B burned T:11961). Elbereth. Stairs. Prayer.
- **E: wand of lightning (0:4)** (only along a line whose first wall is >= 7 squares away). **S: wand of striking** (5+ charges used). H: uncursed elven dagger (throwable).
- **D: uncursed BAG OF HOLDING ("BoH prize")**, holds 6 items: scroll ELAM EBOW (uncursed, unknown), 2 scrolls of FIRE (keep: sliming cure), yellow spellbook (unknown), swirly potion (uncursed, unknown), wand of lightning (0:2), wand of striking. **Pick-axe b is in the MAIN PACK** (`bag_put('D','b')` before entering any shop).
- Rings (all uncursed unless noted, unknown): **J twisted (base 300: conflict / polymorph / poly control / teleport control — NEVER wear-test: polymorph would destroy the GDSM)**, **K = RING OF REGENERATION (identified T:11296; wear when hurt, take off when healed — hunger)**, m coral (150), y bronze (BLESSED, 100), R ivory (100), I wire (100), C clay (price unknown), u opal (price unknown, from DL10).
- Potions: F dark green (uncursed), P golden (unknown BUC), N murky (unknown BUC). No water left (the pyrolisk boiled it).
- Scrolls: z ZLORFIK (uncursed, base 100), k teleportation. (ELAM EBOW in the bag.)
- Spellbooks L pink, M cyan (uncursed; sell/price-ID; don't read).
- Tools: d uncursed KEY (unlocks doors/boxes: `unlock(x, y)`, `loot_all()` does boxes itself), W blessed oil lamp (LOW ON OIL, off), v can of grease, h tin opener, b pick-axe (dig('>') = fast descent/escape).
- Gems (uncursed, unidentified): p black, q 2 green, s 3 red, t 2 orange.
- NO lizard corpse (stoning cure = prayer only), no holy water, no healing potions.

## Identified appearances
- Scrolls: ZELGO MER identify, EIRIS SAZUN IDISI amnesia, GARVEN DEH light, HACKEM MUCHE fire, TEMOV teleportation, FOOBIE BLETCH enchant weapon, KERNOD WEL scare monster, **THARR = CREATE MONSTER** (a leprechaun read one: an owlbear appeared). NR 9 (base 200) = earth or taming (my copy burned). ELAM EBOW, ZLORFIK (100), DUAM XNAHT (100) unknown.
- Potions: yellow sickness, brilliant blue blindness, cyan oil; **sky blue = CONFUSION or BOOZE** (its vapour: "You feel somewhat dizzy"); swirly, dark green, golden, murky unknown.
- Wands: marble lightning, iridium striking, oak magic missile (seen), crystal speed monster, **short = TELEPORTATION (Z, G)**, zinc nothing.
- Rings: diamond fire resistance, iron protection from shape changers, **engagement = REGENERATION**, agate = base 150.
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
| 8 | main | `<` (7,8). `>` (47,8). Fountains (42,8) (used for 2 scroll dips, still there) and (48,16). SINK (22,3). Pit (7,11). |
| 9 | main | `<` (64,5). `>` (72,13) in a closet behind door (71,12) (was locked; unlocked). Rest unexplored. |
| **10** | main | `<` (19,7). **NEUTRAL ALTAR (Odin) (16,7)** — BUC testing only. `>` NOT FOUND (boulders (10,9)/(11,9) block a west corridor); I dug down from (39,16) (hole there now). Green mold (43,13). Rooms explored: altar room, SW statue room, N room, centre room, small S room, E room. |
| 11 | main | `<` (18,5), `>` (10,14). Landed at (38,5) (credit card at (38,6)). Doors (64,14), (58,8) were locked (unlocked). |
| 12 | main | `<` (9,16), `>` (11,5). Mountain nymph with a wand of teleportation roams it. Peaceful gnomish wizard. |
| **13** | main | **QUEST PORTAL LEVEL** (Norn's message on arrival; portal not found yet). `<` (34,16), `>` (6,13). ROLLING BOULDER TRAP (17,13). ANTI-MAGIC FIELD (47,4) (1d4 with MR). Closed door (31,9). Boulders (25,13), (39,14). |
| Mines 1-8 | Mines | Minetown = Mines 3 (DL6, Grotto Town): temple of Odin (neutral) (33,4), general store (61-69,10-11), hardware store (59-62,14-16); `>` (48,4) behind door (52,7). Mines' End = Mines 8 (DL11, Catacombs): `<` (44,12); LUCKSTONE still in a SW closet (3,17)/(3,19) (secret doors (4,17)/(4,19)); level teleporters harmless with MR. Details in journal. |
| Sokoban | Sokoban | ALL SOLVED, prize (BoH) taken. |

## Threats / known dangers
- **Fire gazes/breath burn scrolls and boil potions even with fire resistance** (pyrolisk cost 3 scrolls + 2 potions): kill pyrolisks/red nagas/hell hounds at once, keep scrolls/potions that matter in the BoH.
- Nymphs/leprechauns: AC-10 makes their theft attacks miss often; kill them in one blow when adjacent; nymphs may carry a teleport wand.
- Cockatrices: melee only with Excalibur (never bare-handed); let them come to you; no lizard corpse — prayer is the stoning cure.
- Soldiers/wand users: no reflection — avoid lines at range (sleep rays: no sleep resistance).
- Soldier ants, black lights (hallucination), yellow lights (blindness: unicorn horn now).

## Objective and plan (after shift 12)
1. **XP toward XL14 for the quest** (portal is on DL13; find it by exploring/searching DL13 later — the Norn needs XL14). Continue down the main dungeon DL14-18 carefully (AC-10, Excalibur +6, MR, unicorn horn), fighting at chokepoints; go back up at < 50% HP. Big Room not seen (DL10-12 were normal levels).
2. **Reflection** still missing (silver dragon scales / shield or amulet of reflection) — required before Medusa/Castle (PLAYBOOK A1). Also sleep resistance would help.
3. **Lizard corpses** (stoning cure), **holy water** (a LAWFUL altar: put water on it and pray — prayer timeout is 0), **more blank scrolls** (fountain dips) for the marker (0:35): 2-3 identify scrolls → J twisted ring first, then the potions.
4. Unknown rings: J (300) never wear-test; C clay / u opal: price-ID in a shop first.
5. Luckstone at Mines' End SW closets when convenient; protection costs 4400 at XL11 (400 x XL).
