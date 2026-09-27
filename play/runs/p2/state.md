# p2 — current state (rewrite as things change)

## Character
- Name/role: p2 — local practice game, seed 202 (lawful female dwarven Valkyrie, god: Tyr)
- Turn / Dlvl / XL / HP / Pw / AC: **T:9920 / SOKOBAN LEVEL 4 (top, Dlvl 2, "Sokoban_Level_4a") — puzzle 23/26 steps done** / **XL10** (Exp 6941; XL11 at 10000) / 121/121 / 16/16 / **AC -4** / $143 on me (391 in the sack n). Last meal: food ration T:9248 → **Hungry expected ~T:10000 (soon!)**.
- FOOD: J 2 food rations, T 4 tripe rations (dog food: 50% vomiting for a dwarf), G 2 cloves of garlic, p slime mold, k lichen corpse, f tin.
- Position at shift-13 end: **(34,10)** = the gap in the row-10 wall of Soko 4 (between the rows 9 and 11 boulder rooms). An UNSEEN monster (not shown by telepathy: mindless or invisible) sits at (34,8) behind boulder B (34,9) and blocks the next push. Giant mimic #2 disguised as a boulder at (29,6) (top-left, off the solution routes).
- Attributes: **St:17** (+1 T:9676 by exercise) Dx:12 Co:19 In:11 Wi:9 Ch:9.
- Skills: long sword **EXPERT**; #enhance other skills when "more confident" appears.
- Intrinsics (harness knows them): cold res, stealth (Valk + elven cloak), infravision, SPEED, EXTRINSIC telepathy (amulet of ESP O) + INTRINSIC TELEPATHY, **POISON RESISTANCE**. Excalibur: autosearch + drain resistance while wielded. **NO magic resistance, NO reflection, NO fire resistance.**
- Luck: probably **0** now (the +3 from the T:7124–7281 sacrifices timed out by ~T:9000). Alignment −5 at T:9254 ("You feel like a hypocrite": zapped from engrave_test's Elbereth) — record is large, harmless.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:6107–6110 | deliberate no-trouble prayer on the D11 lawful altar with 2 waters | SUCCESS, 2 holy water, timeout reset |
| — | **PRAYER TIMEOUT PROVEN 0** (sacrifice Luck messages T:7124, 7128, 7281; no prayer since). `prayer_check()` knows. Reserved as the emergency cure (stoning, lycanthropy, HP ≤ 20). |
- Holy-water prayer (2 waters in bag s) at the D11 altar (44,6) on the way back DOWN after Sokoban.

## Equipment worn/wielded (letter: item)
- a: EXCALIBUR — blessed rustproof **+6** (wielded). NEVER read enchant weapon on it.
- **m: +0 elven mithril-coat (BUC UNKNOWN, worn since T:8028; if cursed, dip in holy water)**; q: uncursed +0 elven cloak (faded pall); c: +3 small shield (**very burnt**); E: +0 high boots (**burnt**); j: +0 orcish helm; O: amulet of ESP.

## Key inventory (letters)
- **L: UNICORN HORN** (from the gray unicorn T:8927; unicorn death-drop horns are never generated cursed — mkobj.c TOOL_CLASS has no blessorcurse for it → safe to APPLY against confusion/stun/blindness/hallucination/sickness).
- THROWING: e blessed +0 dagger, D dagger, F elven dagger; P 12 blessed darts. (C dagger lost in Soko 4's bottom room around (33,19).)
- **WANDS: R OAK = TELEPORTATION** (engrave: engraving vanishes; zaps teleported a boulder + a giant mimic, then a 2nd boulder; used 4 charges incl. engrave → 0–4 left; **NEVER zap it along a line of Sokoban boulders you need**; in Sokoban you can't self-teleport). g FIRE (used 3), N FIRE (used ≥4), y FIRE (used ≥3); x SLEEP [2–6]; v STRIKING (ebony; breaks boulders = −1 Luck in Sokoban); r SLOW MONSTER (balsa; the 2nd balsa wand U was stolen by a monkey — it lies at Soko 4 (31,13), the row-13 gap: pick it up); V LIGHT; M make invisible (0:3); I undead turning (0:3); **h HEXAGONAL: engrave no effect (nothing/opening/locking/probing/secret door detection or empty)**. Empty create monster wand dropped in Soko 2 (44,7).
- **BAG s** (holding): pick-axe, 2 potions of WATER, potion of HEALING, murky potion, 2 scrolls of TELEPORTATION, scrolls VERR YED HORRE, FOOBIE BLETCH, KIRJE, blank x2, ENCHANT WEAPON, + ALL GEMS (black x3, green, red x2, white, yellow, yellowish brown). s is a "bag" (holding or oilskin?) — never put a cancellation wand in it (R is teleportation, OK). SACK n: 391 gold + murky potion.
- **b: 2 scrolls ETAOIN SHRDLU = almost surely EARTH** (unbagged).
- RINGS: o AGATE (base 100, from Soko 2), B bronze, S sapphire (unknown), X ring of TELEPORTATION (BUC unknown, Soko 3), H CURSED teleportation. Never put on unknown rings.
- K: puce potion (base 150 group).
- TOOLS: Q grease; u key (`unlock(x, y)`); t whistle; A brass lantern; d blessed oil lamp; candles w (6) + z (1).

## Identified appearances (appearance -> identity)
- Scrolls: YUM YUM enchant weapon; ANDOVA BEGARIN identify; ELAM EBOW scare monster; unlabeled blank; KO BATE light; DAIYEN FOOELS teleportation; KERNOD WEL base 80 (enchant armor / remove curse); ELBIB YLOH destroy armor; ETAOIN SHRDLU = earth (Sokoban 1, not formally); VERR YED HORRE, FOOBIE BLETCH, KIRJE unknown.
- Wands: uranium create monster; ebony striking; curved sleep; balsa slow monster; jeweled FIRE; pine light; iron make invisible; forked undead turning; **oak TELEPORTATION** (not formally); hexagonal: no engrave message.
- Rings: silver regeneration; copper unknown; agate base 100; steel shock resistance; twisted teleportation; bronze, sapphire unknown.
- Potions: MAGENTA healing; YELLOW speed; cyan gain level; clear water; WHITE paralysis; EFFERVESCENT full healing; golden object detection; EMERALD sleeping; puce base 150; murky base 100.
- Amulets: hexagonal ESP; oval unchanging. Faded pall = elven cloak.

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1–5 | Dungeons | see journal; D2 Mines branch (21,14); D5 Oracle |
| Mines | Gnomish Mines | Minetown (Dlvl 5): temple of Odin (protection bought), shops |
| 6 | Dungeons | up (23,15); **SOKOBAN `<` (4,15)**; `>` (41,3) |
| Soko 1 (Dlvl 5) | 1b | SOLVED T:8389; `>` (38,10) to D6, `<` (38,12) |
| Soko 2 (Dlvl 4) | 2b | SOLVED T:8866; `>` (35,8), `<` (47,10) in the NE stair room, door (51,15) open |
| Soko 3 (Dlvl 3) | 3b | SOLVED T:9222; `>` (36,16), `<` (46,10) in the NE stair room (44-48,7-13), door (48,14) unlocked+open; orcish loot (48,13)/(47,13) |
| **Soko 4 (Dlvl 2)** | **4a** | `>` (27,5) top-left. Holes on row 5 (34..49): 13 plugged, **3 left** (47..49,5) = steps 24 (B), 25 (A), 26 (E). ZOO room x=44..48, y=14..20, doors (43,15), (43,17), (43,19) west, (49,17) east (reached by the x=50 corridor from (50,5)). A WAND at (50,5); a RING at (29,8); my stolen balsa wand at (31,13). |
| 7–13 | Dungeons | 7: up (33,13) `>` (64,16); 8: up (48,4) `>` (49,16); 9: up (31,19) `>` (43,4); 10 BIG ROOM `<` (16,8) `>` (4,16); 11: `<` (48,19) `>` (14,19) LAWFUL ALTAR (44,6); 12: `<` (48,3) land mine (47,4) `>` (13,4); 13: `<` (74,7) `>` (66,16) LAWFUL ALTAR (17,18) |

## SOKOBAN 4 SOLVER PATCH (kernel only — RE-APPLY after any daemon restart / reload before `sokoban.solve()`)
Boulder P was teleported away (T:9311), spare O took its role, spare Q never moves, giant mimic #2 shows as a boulder at level (3,2) = screen (29,6):
```
lv = sokoban._levels()['soko1-1']
def fix(lst):
    t = type(lst[0]) if lst else tuple
    out = [b for b in lst if tuple(b) != (3, 12)]
    for extra in ((9, 12), (3, 2)):
        if extra not in [tuple(b) for b in out]:
            out.append(t(extra))
    return out
lv['boulders'] = fix(lv['boulders'])
for st in lv['steps']:
    st['after']['boulders'] = fix(st['after']['boulders'])
```
(If the mimic at (29,6) moves or dies, drop (3,2) from the lists again.) Then `with monster_filter(lambda m: m['dist'] <= 2): sokoban.solve()`.

## Threats / known dangers
- **WAND USERS**: Grey-elf (D10) and mountain centaur (Soko 2) had WANDS OF FIRE (6d6, bounce). Stand where only adjacent squares line up.
- YELLOW LIGHTS: one Excalibur blow failed to kill 3 times → ~100 turns blind. Kill at range or avoid.
- Cockatrices: only with Excalibur; stoning cure = prayer only (no lizard). One killed in Soko 4 (T:~9391; its "touch" didn't hiss).
- Soko 4 zoo is waking: quantum mechanic (last seen (42,17)), yeti/monkey/wumpus/gecko already came out and died. Giant mimic #2 at (29,6) (disguised; don't touch it by accident — or kill it deliberately at full HP: 2 blows).
- No MR/reflection: the Sokoban prize (50% amulet of reflection, else bag of holding) is the goal.

## Objective and plan
- NEXT (shift 14):
  1. EAT when Hungry (~T:10000): a food ration (J) on a quiet square.
  2. Re-apply the solver patch (above) if the kernel was restarted. Deal with the unseen monster at (34,8) behind boulder B (34,9): step to (33,9)/(35,9) side via row 9? (row 9 is reachable only through the gap I'm standing in: go (33,9) — wait for it / `fight(34,8)` from (33,9) or (35,9)). Then `sokoban.solve()` for steps 24–26.
  3. Pick up the balsa wand at (31,13), the ring at (29,8) and the wand at (50,5).
  4. ZOO: at FULL HP, open ONE door and fight in the doorway with `fight_until_clear()` (the east door (49,17) from the x=50 corridor is a 1-wide approach — good chokepoint). Kill the zoo, take the prize (amulet of reflection or bag of holding) — do NOT put on an unknown amulet unless it is the Sokoban prize (the prize amulet is reflection when it's an amulet).
  5. Afterwards back down to D11: holy-water prayer at the altar (bless 2 waters; BUC-test the mithril-coat, rings, unicorn horn), then D13+.
- Emergency: HP < 40% → Elbereth (not vs @/minotaurs) / potion of healing (bag) / upstairs; PRAYER (timeout 0 proven, Luck ~0) for HP ≤ 20, stoning, lycanthropy. NO teleport scrolls in Sokoban (no-teleport level).

## Harness/helper calibration notes
- `sokoban.solve()` resumes cleanly after every pause; wrap it in `with monster_filter(lambda m: m['dist'] <= 2): ...`.
- `engrave_test()` leaves an ELBERETH under you — step off before zapping/attacking anything (−5 alignment "hypocrite").
- Kernel additions (lost on restart): `hunt(name)`; combat.ROUTINE += `^You are almost hit by `, `^The poison doesn't seem to affect you`, `^The .+ misses[.!]$`.
- path_to() doesn't know a door hidden under a corpse pile (routes diagonally into it).
