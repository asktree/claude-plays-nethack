# p2 — current state (rewrite as things change)

## Character
- Name/role: p2 — local practice game, seed 202 (lawful female dwarven Valkyrie, god: Tyr)
- Turn / Dlvl / XL / HP / Pw / AC: **T:8912 / SOKOBAN LEVEL 2 (Dlvl 4, "Sokoban_Level_2b" SOLVED)** / **XL10** (Exp 6225; XL11 at 10000) / 107/121 / 16/16 / **AC -4** / $108 on me (391 in the sack n). Last meal: food ration T:8903 (was Hungry at T:8869) → next Hungry ~T:9700.
- FOOD: J 2 food rations, T 4 tripe rations (dog food: 50% vomiting for a dwarf), G 2 cloves of garlic, p slime mold, k lichen corpse, f tin. OK for ~3000 turns.
- Position at shift-12 end: **(50,16)**, the dead-end corridor square WEST of the stair-room door (51,15) (door open, ape/centaur corpses in the doorway). Only monsters in the doorway or at (51,16) can reach me here. In the stair room: a hostile **GRAY UNICORN** (cross-aligned: killing it costs no Luck; horn = UNICORN HORN — in Sokoban unicorns don't avoid your line) and an **ETTIN ZOMBIE** (mindless: invisible to telepathy, slow, 2x d10 claws). Room loot: a WAND (45,10), a RING (44,7); Sokoban `<` (47,10) leads to level 3.
- Attributes: **St:16** (+1 T:8802 by exercise) Dx:12 Co:19 In:11 Wi:9 Ch:9.
- Skills: long sword **EXPERT**; #enhance other skills when "more confident" appears.
- Intrinsics (harness knows them): cold res, stealth (Valk + elven cloak), infravision, SPEED, EXTRINSIC telepathy (amulet of ESP O) + INTRINSIC TELEPATHY, **POISON RESISTANCE**. Excalibur: autosearch + drain resistance while wielded. **NO magic resistance, NO reflection, NO fire resistance.**
- Luck: about +2 (three sacrifices T:7124–7281; slowly times out without a luckstone).

## Prayer log
| turn | reason | result |
|---|---|---|
| T:6107–6110 | deliberate no-trouble prayer on the D11 lawful altar with 2 waters | SUCCESS, 2 holy water, timeout reset |
| — | **PRAYER TIMEOUT PROVEN 0** (sacrifice Luck messages T:7124, 7128, 7281; no prayer since). `prayer_check()` knows. Reserved as the emergency cure (stoning, lycanthropy, HP ≤ 20). |
- Holy-water prayer (2 waters in bag s) at the D11 altar (44,6) on the way back DOWN after Sokoban.

## Equipment worn/wielded (letter: item)
- a: EXCALIBUR — blessed rustproof **+6** (wielded). NEVER read enchant weapon on it.
- **m: +0 elven mithril-coat (BUC UNKNOWN, worn since T:8028 — came from a centaur's pile on D10; if it turns out cursed, dip in holy water)**; q: uncursed +0 elven cloak (faded pall); c: +3 small shield (**burnt twice**); E: +0 high boots (**burnt**); j: +0 orcish helm; O: amulet of ESP.

## Key inventory (letters)
- THROWING: e blessed +0 dagger, C dagger (at the ready), D dagger, F elven dagger; P 12 blessed darts.
- **WANDS: g FIRE (mine, used 3 on D10), N FIRE (Grey-elf's, used ≥3), y FIRE (centaur's, used ≥1)**; x SLEEP [2–6]; v STRIKING (ebony); r + U SLOW MONSTER (balsa); V LIGHT; M make invisible (0:3); I undead turning (0:3); o create monster (EMPTY).
- **BAG s** (probably holding): pick-axe, 2 potions of WATER, potion of HEALING, murky potion, 2 scrolls of TELEPORTATION, scroll VERR YED HORRE, blank scroll, + new: scrolls FOOBIE BLETCH, KIRJE, unlabeled (blank), ENCHANT WEAPON. SACK n: 391 gold + murky potion.
- **b: 2 scrolls ETAOIN SHRDLU = almost surely EARTH** (Sokoban level 1 pair; unbagged).
- RINGS: B bronze (unknown), S sapphire (unknown), H CURSED teleportation (never wear). Never put on unknown rings (polymorph would break the mithril).
- K: puce potion (base 150 group). Gems: i green, l white, + R/X black, Y red, Z yellow, W yellowish brown (for co-aligned unicorns).
- TOOLS: Q grease; u key (unlocks doors: `unlock(x, y)`); t whistle; A brass lantern; d blessed oil lamp; candles w (6) + z (1).

## Identified appearances (appearance -> identity)
- Scrolls: YUM YUM enchant weapon; ANDOVA BEGARIN identify; ELAM EBOW scare monster; unlabeled blank; KO BATE light; DAIYEN FOOELS teleportation; KERNOD WEL base 80 (enchant armor / remove curse); ELBIB YLOH destroy armor; ETAOIN SHRDLU = earth (Sokoban 1, not formally); VERR YED HORRE, FOOBIE BLETCH, KIRJE unknown.
- Wands: uranium create monster; ebony striking; curved sleep; balsa slow monster; jeweled FIRE; pine light; iron make invisible; forked undead turning.
- Rings: silver regeneration; copper unknown; agate base 100; steel shock resistance; twisted teleportation; bronze, sapphire unknown.
- Potions: MAGENTA healing; YELLOW speed; cyan gain level; clear water; WHITE paralysis; EFFERVESCENT full healing; golden object detection; **EMERALD = SLEEPING** (centaur threw one T:7930); puce base 150; murky base 100.
- Amulets: hexagonal ESP; oval unchanging. Faded pall = elven cloak.

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1–5 | Dungeons | see journal; D2 Mines branch (21,14); D5 Oracle |
| Mines | Gnomish Mines | Minetown (Dlvl 5): temple of Odin (protection bought), shops |
| 6 | Dungeons | up (23,15); **SOKOBAN `<` (4,15)**; `>` (41,3) |
| Soko 1 (Dlvl 5) | Sokoban 1b | **SOLVED T:8389**; `>` (38,10) to D6, `<` (38,12); an egg left at (42,14) |
| Soko 2 (Dlvl 4) | Sokoban 2b | **SOLVED T:8866**; `>` (35,8), `<` (47,10) in the NE stair room (43-51,10-14), door (51,15) (was locked; unlocked + opened) |
| 7 | Dungeons | up (33,13); `>` (64,16) |
| 8 | Dungeons | up (48,4); `>` (49,16), fountain (50,15) |
| 9 | Dungeons | up (31,19); `>` (43,4) |
| 10 | Dungeons BIG ROOM | `<` (16,8), `>` (4,16) corner; crowd CLEARED T:7960; left: 3 GREEN-ELVES (east), large mimic "statue" (44,13), peaceful tengu + gnome; cockatrice corpse (17,9); my scale mail + destroy armor at (38,9); spellbooks (15,6), (20,11) |
| 11 | Dungeons (quest portal level) | `<` (48,19), `>` (14,19), LAWFUL ALTAR (44,6), fountains dried |
| 12 | Dungeons | `<` (48,3), LAND MINE (47,4), weapon shop, `>` (13,4) |
| 13 | Dungeons | `<` (74,7), `>` (66,16), LAWFUL ALTAR (17,18) |

## Threats / known dangers
- **WAND USERS**: a Grey-elf (D10) and a mountain centaur (Soko 2) both had WANDS OF FIRE: 6d6 per hit, bolts BOUNCE off walls (hit me twice in a dead end), burn shield/boots/scrolls. Get out of their line; fight where they can only line up when adjacent.
- YELLOW LIGHTS: one Excalibur blow failed to kill 3 times (T:7623, T:8074 → ~100 turns blind). Kill at range with daggers first or avoid.
- Cockatrices: only Excalibur; stoning cure = prayer only (no lizard).
- No MR/reflection: Sokoban prize (50% amulet of reflection) is the goal.

## Objective and plan
- NEXT (shift 13):
  1. From (50,16): kill the gray unicorn (UNICORN HORN!) and the ettin zombie when they come to the door (hold loop: fight adjacent, else search); then enter the room, take the wand (45,10) and ring (44,7).
  2. `<` (47,10) → Sokoban level 3, `sokoban.solve()` (resume after each pause; filter known distant monsters with `monster_filter`). Then level 4 (zoo: fight at a chokepoint at full HP) → prize.
  3. Afterwards down to D11: holy-water prayer at the altar (bless 2 waters; test the mithril-coat and rings there), then D13+.
- Emergency: HP < 40% → Elbereth (not vs @/minotaurs) / potion of healing N (bag) / upstairs; PRAYER (timeout 0 proven) for HP ≤ 20, stoning, lycanthropy. NO teleport scrolls in Sokoban.

## Harness/helper calibration notes
- Sokoban: `sokoban.solve()` resumes cleanly after every pause; wrap it in `with monster_filter(lambda m: m['dist'] <= 2 or <not a known species>)` to stop re-pauses on known monsters behind walls. go_up(to='Sokoban') didn't know the D6 stair links — pressed `<` on (4,15) by hand.
- travel()'s final plain step auto-picks up thrown daggers (pickup_thrown): pickup('dagger') afterwards finds nothing — that's fine.
- Kernel helpers this shift (lost on daemon restart): `hunt(name)` (step toward the nearest such monster, fight when adjacent), `duel(name)` (wait with `s`, fight when adjacent), `pick(adj)` (priority target), a hold loop (fight adjacent else `s`).
