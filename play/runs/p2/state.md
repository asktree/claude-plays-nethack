# p2 — current state (rewrite as things change)

## Character
- Name/role: p2 — local practice game, seed 202 (lawful female dwarven Valkyrie, god: Tyr)
- Turn / Dlvl / XL / HP / Pw / AC: **T:7857 / Dlvl 11** / **XL10** (Exp 5186; XL11 at 10000) / 99/121 / 16/16 / **AC -5** / $0 on me, **391 gold in the sack n**. Last meal: OWLBEAR corpse T:7312–7337 (was Satiated) → nutrition ~1000 now → next Hungry ~T:8700. Food carried: lichen corpse k (never rots), tripe ration T, tin f. NO rations — eat fresh safe corpses (poison resistant: most are fine).
- Position at shift-11 end: **ON the `<` (48,19) of D11** (SW room), no hostiles in view. The giant zombie that followed me down is dead.
- Attributes: **St:15** (17 → 14 from the scorpion T:7135; +1 by exercise T:7842 "You feel strong!") Dx:12 Co:19 In:11 Wi:9 Ch:9.
- Skills: long sword **EXPERT**; #enhance other skills when "more confident" appears.
- Intrinsics (harness knows them): cold res (Valk), stealth (Valk + elven cloak), infravision (dwarf), SPEED (XL7), EXTRINSIC telepathy (amulet of ESP O) + INTRINSIC TELEPATHY (floating eye, T:6650), **POISON RESISTANCE (scorpion, T:7135)**. Excalibur: autosearch + drain resistance while wielded. **NO magic resistance, NO reflection.**
- Luck: **about +2..+3** (sacrifices T:7124, T:7128, T:7281 each "four-leaf clover"/"brushed your foot" = +1; no luckstone → -1 per 600 turns toward 0).
- Alignment: "Tyr is well-pleased" at T:6110; many hostile kills since.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:6107–6110 | deliberate no-trouble prayer on the D11 lawful altar with 2 waters | SUCCESS, 2 holy water, timeout reset |
| — | **PRAYER TIMEOUT PROVEN 0**: sacrifices at T:7124, T:7128 and **T:7281 (giant beetle)** all gave Luck ⇒ timeout 0; nothing raised it since. `prayer_check()` knows (p_safe 1.0). **Reserved as the emergency cure (stoning: no lizard/acid corpse carried; lycanthropy; HP ≤ 1/6 max = 20).** |
- Decision (shift 11): do NOT sacrifice more for Luck while relying on this prayer — each sacrifice has a 1/10 artifact-gift chance, and a gift resets the timeout (rnz(350)). Do the holy-water prayer (2 waters in bag s) at the D11 altar (44,6) on the way back DOWN after Sokoban.

## Equipment worn/wielded (letter: item)
- a: EXCALIBUR — blessed rustproof **+6** (wielded). NEVER read enchant weapon on it. Applying a pick-axe or #rubbing a lamp WIELDS that tool — `w`,`a` afterwards.
- c: uncursed +3 small shield; y: +0 scale mail; q: uncursed +0 elven cloak; E: uncursed +0 high boots; O: uncursed amulet of ESP; j: uncursed +0 orcish helm (iron: rust monsters). Divine protection 3 points.

## Key inventory (letters)
- THROWING: **e: blessed +0 dagger (at the ready)**, C: uncursed dagger (+1 by price), D: uncursed dagger, F: uncursed elven dagger; P: 12 blessed darts. NEVER THROW INSIDE A SHOP.
- **BAG s** (uncursed; very likely a BAG OF HOLDING): pick-axe, **L: 2 uncursed potions of WATER** (for the holy-water prayer), **N: uncursed potion of HEALING**, b murky potion (base 100, unknown BUC), **J: 2 uncursed scrolls of TELEPORTATION**, U: uncursed scroll VERR YED HORRE (unknown), m: uncursed blank scroll. (Bagged against pyrolisk fire gaze on D10; `bag_take('s', 'teleportation')` = 1 call.)
- SACK n: 391 gold + a murky potion (base 100).
- WANDS: x SLEEP [2–6 charges]; g FIRE; V LIGHT; r SLOW MONSTER (balsa); **o CREATE MONSTER: EMPTY (0 charges, T:7304 "Nothing happens")**; M MAKE INVISIBLE (0:3); I UNDEAD TURNING (0:3); v STRIKING (ebony).
- RINGS: H: CURSED ring of teleportation (never wear).
- TOOLS: Q can of grease; u key; t whistle (untested); A brass lantern; d blessed oil lamp; CANDLES w (6) + z (1) = 7 for the Candelabrum.
- FOOD: k lichen corpse, T tripe ration, f tin.
- Gems (uncursed, unidentified): R black, X 2 black, Y 2 red, Z yellow, W yellowish brown — for co-aligned unicorns (+1 Luck per real gem; the unicorn teleports away after each).
- Escape items: J x2 teleport (in bag s; NOT in Sokoban), sleep wand x, striking v, Elbereth, `dig('>')` (pick-axe in bag), stairs, PRAYER (timeout 0 proven).
- Healing: potion of healing N (bag s). Emergency cures: stoning → prayer only.

## Identified appearances (appearance -> identity)
- YUM YUM -> enchant weapon; ANDOVA BEGARIN -> identify; ELAM EBOW -> scare monster (lost); unlabeled -> blank paper; KO BATE -> light; DAIYEN FOOELS -> TELEPORTATION
- KERNOD WEL -> base 80 (enchant armor / remove curse); VERR YED HORRE -> unknown (U); ELBIB YLOH -> DESTROY ARMOR; HAPAX LEGOMENON -> base 100 group; scroll of identify: type known
- uranium wand -> create monster; ebony -> STRIKING; curved -> SLEEP; balsa -> slow monster; jeweled -> FIRE; pine -> LIGHT; iron -> MAKE INVISIBLE; forked -> UNDEAD TURNING
- silver ring -> regeneration; copper ring -> unknown (a cursed one left on the D13 altar); agate ring -> base 100 group; steel ring -> shock resistance; twisted ring -> TELEPORTATION
- puce potion -> base 150; murky potion -> base 100; **MAGENTA -> HEALING** (an ogre king quaffed one T:7383: "looks better"); YELLOW -> SPEED; cyan -> GAIN LEVEL; clear -> water ("potions called water"; blessed clear potion = HOLY WATER); WHITE -> PARALYSIS; EFFERVESCENT -> FULL HEALING; golden -> OBJECT DETECTION
- hexagonal amulet -> ESP; oval amulet -> unchanging
- lamp (plain) -> magic lamp (used up); oil lamp identified; "bag" -> sack identified (n); the other "bag" (s) = holding/oilskin
- faded pall -> ELVEN CLOAK; vellum spellbook -> level 1; dull -> level 4; leathery -> level 3/4; cloth -> unknown

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1 | Dungeons | up (8,8); down (10,19); fountains (27,11), (5,18) |
| 2 | Dungeons | up (40,6); down (21,14) = GNOMISH MINES BRANCH; down (74,17) = main; Kittamagh's bookstore (2-5,17-19) door (6,18); fountain (59,16) |
| 3 | Dungeons | up (21,18) under a broken large box; down (51,10); SLEEPING GAS TRAP (35,8); vault |
| 4 | Dungeons | up (39,18); down (12,18) via hidden passage (8,15); FOUNTAIN (22,17); UPERNAVIK'S GENERAL STORE (69-71,15-17) door (68,16) |
| 5 | Dungeons (ORACLE) | up (9,5); down (58,5); Delphi fountains; PIT (14,15) |
| 3–6 (Mines) | Gnomish Mines | Mines 1 up (77,13) down (50,13); Mines 2 up (44,10) down (8,10); MINETOWN = Mines 3 (Dlvl 5): up (74,5), down (3,6), TEMPLE of ODIN (neutral) altar (38,9) priest (protection bought), shops: Kilmihil books, AlliWar hardware (LARGE MIMIC (30,16)), Pasawahan deli, Izchak lights, Ouiatchouane general; Mines 4 (Dlvl 6) up (45,5), `>` not found |
| 6 | Dungeons | up (23,15); **SOKOBAN `<` (4,15)** (not done yet); `>` (41,3) NE room; leprechaun hall (20-25,4-7) cleared; fountain (7,6) |
| 7 | Dungeons | up (33,13); `>` (64,16) (SE, door (61,16)); SW room (5-12,17-19) BURNED ELBERETH (10,19); SPIKED PIT (23,13); a peaceful tengu |
| 8 | Dungeons | up (48,4); `>` (49,16) in a small room with a FOUNTAIN (50,15), door (49,13); hidden passage (42,5) |
| 9 | Dungeons | up (31,19) S room; `>` (43,4) small NW room door (44,4); W room (14-20,13-17); far-W room (2-6,13-16) ARROW TRAP (6,15), my HOLE (4,15); a carnivorous ape |
| 10 | Dungeons | **BIG ROOM**: `<` (16,8), `>` (4,16) in a wall corner (open neighbours only (4,15),(5,15),(5,16),(5,17) = a good holding spot, escape down). **A CROWD at T:7856 near the `>`: giant spider, giant beetle, gold golem, dust vortex, coyote, mountain centaur (arrows), pyrolisk (fire gaze: bag scrolls/potions), human zombie, a few killer bees; far east: COCKATRICE (~(50,12)), FLOATING EYE (~(48,14)), fog cloud (34,7) (vampire?)**. Loot by the `<`: **RING (18,7)**, scroll pile (17,8), gem (15,8), spellbooks (15,6), (20,11); fountain (11,11) |
| 11 | Dungeons (**QUEST PORTAL LEVEL**, portal not found — probably SE corner) | **`<` (48,19)**, fountain (52,19) **DRIED UP T:7823**, SW room (47-54,15-20); **`>` (14,19)** W room (11-24,16-19; E doorway (24,17), N doorway (20,16)); **LAWFUL ALTAR (44,6)** N-centre room (32-45,5-10); NE room (51-55,3-8); E room ICE BOX (71,7); S room (33-41,16-19) doors (33,19) W, (41,17) E; boulder (28,16); YELLOW MOLD (28,13). Bee swarm mostly KILLED T:7738–7815 (a few left N of the S room); rust monster killed. My old djinni roams, now PEACEFUL — never attack. |
| 12 | Dungeons | `<` (48,3) tiny room, **LAND MINE (47,4)**; CARIGNAN'S ANTIQUE WEAPONS (57-66,3-7) door (56,3) (potion of speed 267); NW room: fountain (12,3) **DRIED UP T:7588**, **`>` (13,4)**; middle room (25-37,10-17) LOCKED door (37,16); SE room (44-57,12-18) PIT (48,13) |
| 13 | Dungeons | `<` (74,7) NE room; `>` (66,16) SE room; **LAWFUL ALTAR to Tyr (17,18)** SW room (9-24,16-20) (unicorn: peaceful white = co-aligned, roams there); level fully explored except the boulder spur (21,6): the doors (19,20) and (45,12) lead to 1-square dead ends (searched 30 at (45,13)); NW-middle room ANTI-MAGIC FIELD (27,7) |

## Pets
- None. The old djinni on D11 is peaceful now.

## Threats / known dangers
- POISON RESISTANT: killer bees/soldier ants/spiders are ordinary melee (bees ~26 Exp each at XL9, 1 blow).
- **No magic resistance / no reflection**: no Castle, no lingering on D20+ near soldiers; polymorph traps (D8+) would polymorph me.
- **YELLOW LIGHTS: one Excalibur blow does NOT reliably kill (T:7623 it survived and blinded me ~100 turns). Kill at range (4+ dagger hits first) or walk away; they resist sleep.**
- Cockatrices (D10 far east): only Excalibur, never touch/eat corpses; stoning cure = prayer only.
- Gremlins at night steal intrinsics; rust monsters rust the orcish helm only; nymphs/monkeys steal; leprechauns steal gold (keep it in the sack).
- Mindless monsters (spheres, gas spores, zombies/mummies) are invisible to telepathy.
- SHOPS: throwing inside a shop sells the item.

## Objective and plan
- DONE shift 11: create-monster wand emptied on the D13 altar (iguana, dingo, ochre jelly, owlbear, rothe, dwarf zombie + wanderers giant beetle, gnome mummy, monkey); giant beetle SACRIFICED (+1 Luck, timeout still 0); owlbear eaten; ogre king (magenta = healing), 3 rothes, leprechaun, blue jelly, wererat (@ form), ~15 killer bees, rust monster, giant ant(s), giant zombie; **XL10 at T:7853**; St 15; 2 waters made (both fountains dried); 308 gold.
- NEXT (shift 12):
  1. Rest to full on the D11 `<` (48,19) (search bursts).
  2. Up to D10 at full HP: hold the `>` corner (4,16) and kill the crowd (giant spider, beetle, gold golem, coyote, centaur, zombie) — never the floating eye in melee; the cockatrice only with Excalibur, never bare-handed. Keep scrolls/potions bagged (pyrolisk). Then pick up the RING (18,7), scrolls (17,8), gem (15,8) next to the `<` (16,8) and go up.
  3. D9 → D8 → D7 → D6, then **SOKOBAN** (`<` (4,15) on D6): `sokoban.solve()`; the prize (50% amulet of REFLECTION). Teleport scrolls don't work there; Elbereth does. Zoo on the top level: fight at a chokepoint.
  4. Afterwards back down: bless the 2 waters at the D11 altar (no-trouble prayer, only if the timeout is still proven 0), then D13+ at XL10–11.
- Emergency plan: HP < 40% → stairs / Elbereth (not on an altar) / potion of healing N (bag) / sleep wand x; PRAYER (timeout 0 proven, Luck > 0) for major trouble (HP ≤ 20 = 1/6 of 121, stoning, lycanthropy...).

## Harness/helper calibration notes
- Verified shift 11: `offer()` (floor corpse on the altar → "four-leaf clover" classified, timeout proof recorded); `zap('o', None)` for non-directional wands (the direction arg is required); `monster_filter()` context manager in my own loops; `dip()` reports "fountain dried up"; `bag_take` by identified name ("potion of healing"); `fight()` at 1 blow per call vs exploders refused → raw `do('Fl')`.
- Kernel helpers defined this shift (lost on daemon restart): `camp(max_zaps)` (rest to 95%, zap create monster, fight_until_clear), `hold(radius, max_turns, ignore)` (strike adjacent hostiles, `s` otherwise, bees don't pause), `go_fighting(x, y, tries, ignore)` (travel, fighting whatever is adjacent when travel refuses).
- Earlier notes still valid: never call `inventory()`/`here()` unless `obs.kind == 'command'`; `travel()` never autopicks up; pick-one menus close on the letter alone; `obs.menu` lists only the current page.
