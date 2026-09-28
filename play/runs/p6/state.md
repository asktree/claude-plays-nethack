# p6 — current state (rewrite as things change)

## Character
- Name/role: P6, lawful female dwarven Valkyrie, god: Tyr. Seed 206 (local practice game).
- Turn / Dlvl / XL / HP / Pw / AC: T:1811 / DUNGEONS DL4 at (60,8), INSIDE Kadirli's used armor dealership (front
  row, free floor) / XL3 / 35/40 / 7/7 / AC0 / $0.
- Attributes: St 13 (low for a Valk), Dx 14, Co 19, In 8, Wi 11, Ch 10 (shop prices x4/3).
- Intrinsics: cold res (Valk), stealth (Valk), infravision (dwarf). Speed at XL7. No telepathy (the floating eye got
  away), no poison resistance.
- Luck notes: nothing Luck-changing done. Alignment: no peacefuls hurt.
- Hunger: not hungry. Prayer fixed hunger at T:1617 (nutrition ~900) -> Hungry again around T:2450-2500.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:1617 | Weak (hunger), DL4 (39,16) | SUCCESS, well-pleased; hunger fixed. Timeout reset (~50-1000): NO prayer before ~T:2600 without prayer_check() |

## Equipment worn/wielded (AC0)
- a: uncursed CORRODED +1 long sword (wielded; acid blob T:966 — Excalibur's dip removes erosion).
- r: +2 studded leather armor (worn; bought 47zm; positive enchantment => generated non-cursed, mkobj.c).
- c: uncursed +3 small shield. e: +0 low boots (pet-tested not cursed T:447).

## Key inventory (letters) — [seen in inventory T:1811]
- b: uncursed +0 dagger (quivered). i: 5 darts (BUC unknown; 8 more lost/kitten-carried). p: 5 rocks.
- q: leather gloves (bought 11zm, +0 or negative, BUC UNKNOWN ~13% cursed) — NOT worn: pet-test first (lit doorway).
- Scrolls (unknown): f READ ME, k ASHPD SODALG, l PHOL ENDE WODAN, o GARVEN DEH. Price-ID before reading.
- Potions (unknown): j emerald, m puce. Named type: MAGENTA = "dizzy" (confusion or booze; a kobold threw one).
- n: 2 yellowish brown gems (citrine or glass).
- Escape items: none (upstairs + Elbereth). Healing: none.
- Emergency cures: NONE carried (the acid blob corpse ROTTED AWAY at T:1210: only lizard/lichen corpses keep).
  Stoning -> pray (when the timeout allows) or a fresh acidic corpse / lizard.
- Food: g lichen corpse only. FOOD IS SHORT: eat fresh safe corpses (jackals etc.), look for rations.

## Identified appearances (appearance -> identity)
- magenta potion = confusion or booze (vapour "somewhat dizzy"), named "dizzy".

## Dungeon map
| Dlvl | branch | features (stairs, altars+alignment, shops+type, fountains, stashes, traps, notes) |
|---|---|---|
| 1 | Dungeons | up (18,6), '>' (7,6); fountain (6,15). |
| 2 | Dungeons | up (38,6), '>' (61,7); FOUNTAINS (2,3) (40,4) (68,18); falling rock trap (3,6); a vault (guard footsteps). |
| 3 | Dungeons | up (69,8); '>' (49,7) -> DL4; '>' (52,18) = GNOMISH MINES (by elimination). West half unexplored. |
| 4 | Dungeons | up (23,15) (under a rock); '>' (63,18). KADIRLI'S USED ARMOR DEALERSHIP (58-67, 3-8), door (58,9). Many hidden passages (25,8) (36,10), hidden door (39,17). Floating eye loose (last (12,19)). Dwarf zombie somewhere. |
- Sokoban: up staircase on the level BELOW the Oracle (Oracle DL5-9). Not found yet.

## Kadirli's armor shop (DL4) — prices at Cha 10 (x4/3; +10zm per + enchantment point)
- MIMIC posing as ']' at (63,5): never touch; stay 2+ squares away.
- "piece of cloth" 89zm = base 50 + unID surcharge -> CLOAK OF PROTECTION or DISPLACEMENT; the kitten carried it
  (=> NOT cursed). BUY FIRST when I have ~89zm (or let the kitten carry it out: pet theft).
- +1 scale mail 73 (61,4) (AC5); +1 studded leather 33 (65,5); orcish helm 13 (60,6); elven leather helm 11 (65,4);
  dwarvish cloak 67 (kitten carried it: not cursed); hiking boots 67/93 (93 = +2, base 50: jumping/speed/water
  walking), mud boots 67, combat boots 53 (base 40?); plate mail 800; ring mails 133 (+0)/banded 120-133.
- The kitten wanders the shop picking things up (pet theft): items it picks up are proven non-cursed.

## Pets
- tame kitten, in the shop with me (61,7). It carried my lost darts/dagger (got the dagger + 5 darts back).

## Threats / known dangers
- Floating eye on DL4 (never melee). Mimic in the shop. Dwarf zombie on DL4 (slow, hits for ~d6+1).
- No prayer until ~T:2600+ (prayer_check()). HP emergencies: Elbereth / upstairs.

## Objective and plan
- Next shift: rest to full; buy nothing more ($0) unless gold turns up — the "piece of cloth" cloak (89zm) is the
  prize here. Pet-test gloves q (lit doorway) before wearing. Then DL4 '>' (63,18) -> DL5+ toward the ORACLE
  (DL5-9); the level below the Oracle has Sokoban's extra UP staircase. Do Sokoban first (bag of holding /
  amulet of reflection), then Minetown (Mines from DL3 (52,18)).
- Excalibur: XL5+, dip at a fountain (DL2 has three, DL1 one). Fixes the corroded sword.
- Food: eat fresh safe corpses; the lichen is the last food item.
