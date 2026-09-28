# p5 — current state (rewrite as things change)

## Character
- Name/role: P5, lawful female dwarven Valkyrie, god: Tyr. Seed 405 (local practice game).
- Turn / Dlvl / XL / HP / Pw / AC: T:2007 / MINETOWN = Mines 3 = DL5, in Wonotobo's general store (35,15) /
  XL4 / 51/51 / 7/7 / AC0 / $62. Not hungry (ate a ration T:2004 — it was ROTTEN: only 1/4 nutrition, no effect).
- Attributes: St 18/01, Dx 13, Co 20, In 7, Wi 9, Ch 7 (shop prices x1.5, +1/3 random surcharge). Skills: long sword Basic.
- Intrinsics: cold res (Valk), stealth (Valk), infravision (dwarf). Speed comes at XL7. NO poison res, NO telepathy.
- Luck notes: 0 (nothing done to change it). Alignment: no penalties known.

## Prayer log
| turn | reason | result |
|---|---|---|
| (none) | no prayer yet: timeout started ~300, so prayer in MAJOR trouble is fine now (T:1883) | |

## Equipment worn/wielded (letter: item)
- a: uncursed +1 long sword (wielded). c: uncursed +3 small shield. g: +0 orcish helm (NOT cursed: the kitten picked it
  up). r: RUSTY +0 splint mail (BUC UNKNOWN — worn without a test; +0 makes a curse unlikely, ~5%).

## Key inventory (letters) — all [seen in inventory], BUC from the Minetown altar T:1845 / T:1941
- **z MAGIC LAMP (uncursed; type named "magic")** bought at Izchak's T:1913 for 75 (base 50). DO NOT #rub until BLESSED
  (blessed: 80% wish per djinni; uncursed only 20%). Plan: y (uncursed WATER) on a LAWFUL altar + a no-trouble prayer
  (timeout 0 needed; pray.c p_type 3 -> water_prayer(TRUE)) = holy water; #dip z into it; then rub.
  Wish: blessed +2 gray dragon scale mail (or blessed +2 silver dragon scale mail if MR comes from elsewhere).
- y: UNCURSED WATER (clear potion bought for 8 zm = shk.c price of uncursed water; altar-confirmed uncursed).
- Escape items: none (upstairs + Elbereth). Healing: none known.
- Emergency cures: none (no lizard, no unicorn horn, no holy water).
- Food: f 2 uncursed food rations (bought at Baliga's deli, one more there for 68), h uncursed tripe ration (dwarf: 50%
  vomiting — emergency only / pet food).
- Throwables: b uncursed +0 dagger (also the force_box blade), p dagger (BUC ?), o uncursed orcish dagger.
- Tools: e uncursed oil lamp; w uncursed TOWEL (wear it with P as a blindfold: safe melee vs floating eyes).
- Scrolls (all uncursed, none is scare monster): n FOOBIE BLETCH = base 80 (ENCHANT ARMOR or REMOVE CURSE: keep for an
  emergency/better armor); i ASHPD SODALG and m YUM YUM = base 100 (confuse monster, destroy armor, fire, food det.,
  gold det., magic mapping, teleportation): read on a FRESH level with the splint mail OFF (destroy armor then takes
  the helm) and the potions/n dropped next to me (fire burns inventory).
- Potions: t orange (uncursed) = base 300 (gain ability / GAIN LEVEL / paralysis); q puce, s effervescent (uncursed) =
  base 150 (blindness, gain energy, invisibility, monster det., object det.); A cyan (BUC ?) = base 100 (healing, extra
  healing, restore ability, confusion, hallucination, sleeping) — werejackal drop. u red gem (uncursed, unknown).

## Identified appearances (appearance -> identity)
- Spellbooks sold: cloth and magenta were both base 300 (offered 150 each; shop resells 450/600).
- HACKEM MUCHE = LIGHT (base 50; sold). "lamp" = MAGIC LAMP (oil lamp is known). clear = water.
- Wonotobo (Minetown general store) pays the normal half of base (not a lowballer).

## Dungeon map
| Dlvl | branch | features (stairs, altars+alignment, shops+type, fountains, stashes, traps, notes) |
|---|---|---|
| 1 | Dungeons | up (30,19); '>' (75,18). Pit (31,17). Trap-victim piles (2,5), (48,6) (a trap under each; items cursed). |
| 2 | Dungeons | up (35,12); '>' (39,5) = MINES branch; '>' (54,18) = main DL3 (unvisited). Trap victim (39,16). Locked door (19,9). |
| 3 | Mines 1 | up (8,20); '>' (43,12); MAGIC TRAP (44,12) right E of '>'; anti-magic field (36,12) in a 1-wide pass; RUST TRAP (17,9); trap victim (19,18). HOUSECAT left here ~(35,12). |
| 4 | Mines 2 | up (22,2); '>' (56,16). |
| 5 | MINETOWN (room variant: minetn-2/3/4, alleys -> probably "Alley Town") | up (64,6) (outer room NE), '>' (66,15). Temple of ODIN (NEUTRAL, cross-aligned: never pray/offer) altar (36,8), priestess peaceful. Wonotobo's general store (35-37,15-17) door (34,16): sling, can of grease, 2 potions, armor; MIMIC at (36,17). Yad's tool shop (29-31,7-10) door (31,11): glass orb (crystal ball), key, lock pick; MIMIC at (30,8). Ymla's hardware store (42-44,15-17) door (43,14): oil lamp 15, 2 whistles, 2 mirrors. Fountain (26,11) (never dip in town). ALLEY TOWN (map origin (24,4)). Baliga's DELI (51-53,13-14) door (50,14): 1 food ration 68, tin 8. IZCHAK'S lighting (50-52,7-9) door (52,10): tallow candles 15 each (need 7 for the Invocation), wax 30. The (35,15) square in Wonotobo's now holds my sold scroll (no free square left for sell_offer). Werejackal killed T:1971. |

## Pets
- None with me. Housecat left on Mines 1 (DL3) near (35,12), west of the anti-magic field.

## Threats / known dangers
- XL4 / 51 HP: hill orc packs in the Mines, dwarves are peaceful to me. No poison resistance (bees, ants, poisoned arrows).
- Minetown: don't anger the Watch (no fountain dipping/quaffing, no door kicking). Two mimics in shops (listed above).

## Objective and plan
- NEXT (shift 2): finish Minetown's east side (look for a delicatessen: buy food rations — only 1 ration left; Izchak's
  lighting shop: price every "lamp" — magic lamp = base 50 -> 75/100 zm here).
- Read-test the 4 uncursed scrolls somewhere quiet, OUT of town and away from peacefuls (fire/earth could anger the
  Watch), at full HP (or price-ID them first if a shop square is free: do sell_offer BEFORE selling anything else).
- Then back up to DL2 and down the MAIN dungeon ('>' (54,18)): XP to XL5, a fountain for EXCALIBUR (not in Minetown),
  Oracle (DL5-9), SOKOBAN (up stairs on the level below the Oracle). Protection later: 400*XL gold (1200 at XL3).
- Open questions: B/U/C of the worn splint mail (dip-test/altar not possible while worn; watch for "cursed" on removal).
