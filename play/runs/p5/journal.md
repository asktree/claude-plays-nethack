# p5 journal

## Shift 1
- T:1 DL1 — start: lawful female dwarven Valkyrie "P5", seed 405. St 18/01 Dx 13 Co 20 In 7 Wi 9 Ch 7. Kitten.
  Kit: a +1 long sword, b +0 dagger, c +3 small shield, d food ration, e oil lamp (all uncursed). AC6, HP 18.
- T:38 DL1 — killed a goblin in the corridor N of the arrival room. Pile under it: food ration, tripe ration,
  scroll ASHPD SODALG (i), orcish helm. Pet test in the lit doorway (30,15): "The kitten picks up an orcish helm"
  (pets never pick up cursed items) => not cursed; wearing it (g), AC5. Pit at (31,17) in the arrival room.
- T:277-300 DL1 — explore(): '>' at (75,18) (SE room). Human corpse pile (2,5) and dwarf corpse pile (48,6) =
  TRAP VICTIMS (mklev.c mktrap: a trap under them, their items ALWAYS cursed) -> avoid()ed, not touched.
- T:333 DL1 — large box (72,19) locked: force_box() with dagger b (20 turns): scroll HACKEM MUCHE (j), cloth
  spellbook (k), magenta spellbook (l). T:425 chest (32,4): forced (interrupted once by a newt), EMPTY. $17.
- T:734 DL2 — Hungry: ate ration d on an Elbereth (skipped the tripe: 50% vomiting for a dwarf). Scrolls YUM YUM (m),
  FOOBIE BLETCH (n) picked up. T:794 goblin killed -> XL2 (HP 28). Rats/jackals/kobold zombies/lichen killed.
- DL2 has TWO '>': (39,5) = GNOMISH MINES (taken T:1026), (54,18) = main Dungeons DL3. Trap-victim pile (39,16)
  (runed broadsword there = cursed, left). Locked door (19,9). Up stairs (35,12).
- T:1026 Mines 1 (DL3): arrived at (8,20) with the kitten. Peaceful gnome.
- T:1201 Mines 1 (DL3) — anti-magic field (36,12) (drains Pw only). T:1220 MAGIC TRAP (44,12): blind ~10 turns + deaf,
  "deafening roar" (trap.c: also creates 1-4 monsters next to you). Stood on the '>' (43,12) as an escape hatch and
  searched until sight returned; the unseen "I" was my kitten; only a shrieker came (killed). No damage.
- T:1249-1296 Mines 1 — took o orcish dagger (27,10), p dagger (20,6), q puce potion (10,3), r SPLINT MAIL (3,5);
  fox killed. Human corpse pile (19,18) = trap victim, avoided. Kitten -> housecat.
- T:1330 Mines 1 — large box (7,12) forced (17 turns): s effervescent potion, t orange potion, u red gem.
- T:1351 — pet test of the splint mail inconclusive (dead-end nook); WORE it anyway (a generated-cursed armor is
  almost always negative; this one is +0): AC -1. Pack now > 600 wt: no diagonal squeezes (Mines!).
- T:1370 Mines 1 — hidden RUST TRAP (17,9): splint mail rusty (AC 0). T:1419 left the housecat on Mines 1: it would not
  cross the anti-magic field in the 1-wide passage (36,12) (pets refuse seen traps 39/40). go_down() raised PetLost
  (good); went on without it.
- T:1420 Mines 2 (DL4): gecko -> XL3 (HP 40). T:1509 Hungry: ration f was ROTTEN ("Blecch!", reduced nutrition).
  '>' found by descend(explore=True).
- T:1571 DL5 = Mines 3 = MINETOWN (a ROOM-type variant: minetn-2/3/4 = central town room + random rooms joined by
  corridors; the '<' (64,6) is in an outer room). '>' (66,15).
- T:1660 DL5 — killed a guardian naga hatchling (ate it: SAFE, no poison res this time). Gas spore at distance 2:
  lined up and killed it with a thrown dagger from 2 squares — the blast missed me.
- T:1796 DL5 Minetown — sold both spellbooks in Wonotobo's general store for 150 each ($331). The sold books then covered
  the only free floor squares: no more sell_offer price-ID there.
- T:1832-1845 — temple of ODIN (neutral priestess, "forbidding feeling"). altar_test() on the neutral altar: EVERYTHING
  uncursed (orcish dagger, food, tripe, 4 scrolls, 3 potions, red gem).
- T:1860-1880 — floating eye in the street: 2 dagger hits, then all 3 daggers lay under it (a missile stops at the
  first monster). Bought a TOWEL (w, 75zm) at Ymla's hardware store (blindfold plan), but the eye drifted off the pile;
  picked the daggers up and killed it from range with 2 more throws. NO corpse (no telepathy).
- END OF SHIFT 1: T:1883, Minetown DL5 (47,13), HP 40/40, XL3, AC0, $256, not hungry, no prayer used, pet left on DL3.

## Shift 2
- T:1886 DL5 Minetown — Alley Town confirmed (map origin (24,4); altar (36,8) matches). Baliga's DELICATESSEN (51-53,13-14),
  door (50,14): bought 2 food rations (x, 68 each) + a CLEAR POTION for 8 zm (y) = UNCURSED WATER (shk.c: uncursed water
  is priced 0 -> 5 -> x1.5 = 8; blessed/cursed water would be 150+). Left: 1 ration (52,14) 68zm, a tin (52,13) 8zm.
- T:1911 DL5 — Izchak's lighting store (50-52,7-9), door (52,10): "a lamp (for sale, 75 zorkmids)" = MAGIC LAMP (base 50;
  oil lamps are already identified in my discoveries, so an oil lamp would be named). BOUGHT it (z). $37 left.
  Stock left: tallow candles 15 each (5 for 75 at (51,8)), candles 20/30 each, 5 candles for 200 (50,8) = wax.
- T:1941 DL5 — altar_test() on Odin's altar: lamp z, water y, rations, towel all UNCURSED. Named the lamp type "magic".
- T:1944 bat killed. T:1963 "You hear a jackal howling at the moon" -> T:1971 killed a WEREJACKAL (d form) in the x=33
  alley: it bit once, NO "feverish" (no lycanthropy). -> XL4 (HP 51). It dropped A - cyan potion.
- T:1984-2006 Wonotobo's general store, sell offers from (35,15): i ASHPD SODALG 50 and m YUM YUM 50 (base 100 group),
  n FOOBIE BLETCH 40 (base 80: enchant armor / remove curse), j HACKEM MUCHE 25 (= LIGHT; sold it, $62), q puce 75 and
  s effervescent 75 (base 150), t orange 150 (base 300: gain ability/gain level/paralysis), A cyan 50 (base 100).
- T:2004 Hungry: ate a food ration in the shop — ROTTEN (quarter nutrition, no side effect).
