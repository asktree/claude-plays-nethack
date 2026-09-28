# p6 lessons

## Shift 1
- **Thrown missiles stop at the first monster in their path, hit OR miss** (zap.c bhit): against a stationary
  floating eye every dart and the dagger piled up UNDER it, and it wouldn't move for 45 turns. Before a missile
  duel, count: unskilled darts do d3-2 (min 1) — 13 darts (~8 hits) did ~8 damage and a level-2 eye has up to 16
  HP. Throw from 2+ squares only if you can walk round to the pile; better: wait until a skilled missile stack
  (daggers) or a blindfold makes melee safe.
- **Carried corpses rot away after ~250 turns** (except lizard and lichen): the acid blob corpse "rots away" (T:1210).
  It is not a portable stoning cure; a lizard corpse is.
- **Shop prices reveal enchantment**: armor/weapons cost +10zm base per + point (shk.c getprice). Armor with spe>0
  is generated only by the non-cursed branch (mkobj.c: blessed 50%, never cursed) => a price above base proves the
  item isn't cursed. +2 studded leather at 47zm (=35x4/3 at Cha 10) was the safe buy.
- **A pet that picks an item up proves it isn't cursed** — in a shop the kitten "tested" a whole row of stock for free.
- **Acid blob**: even one sword blow can corrode (1 in 6 per hit). Kick it (leather boots can't corrode) or leave it.
- **Prayer for Weak is a good deal early** (T:1617: 900 nutrition when food is short) but it leaves no prayer for
  ~1000 turns: after that, fight with an Elbereth fallback set BEFORE HP drops (giant bat took me 40 -> 21).
- **Don't -a (autocontinue) a non-trivial monster's hit lines in explore loops**: I silenced a dwarf zombie's hits and
  explore() walked on with it adjacent.
- DL4 had three hidden passages in a row: when explore() says "blocked: boulders ... no down stairs seen yet",
  check dead_ends() and search there (10-20 turns each) before pushing boulders.

## Shift 2
- **XL4 with a +1 long sword hits AC3 monsters only ~40%** (1 + AC + XL + 1 vs d20). Two giant ants (speed 18) took
  me 51 -> 18 over two fights; a giant spider or a snake would have cost ~25-35 HP plus a ~2% poison-instadeath risk
  per full melee (1/8 poisoned per bite, 1/30 of those deadly). Don't go below the Oracle before XL5+Excalibur; leave
  poisonous fast monsters to Elbereth/stairs/range until poison resistance.
- **Elbereth + rest_on_elbereth() is a complete survival loop** vs ants, bats, dogs, spiders, snakes, piercers: every
  one "turned to flee" for 400 turns. Engrave BEFORE the HP drop (it can come out garbled 1-3 times in a row).
- **"Out of view" is not "far away"**: my wait-for-a-gap loop treated the spider stepping into the dark as a gap; it
  was standing next to the stairs. Wait for "not in view for several turns AND last seen far", or a fresh "turns to
  flee" right before moving.
- **Stairs escape**: a monster follows only if adjacent when you press '>'. Right after it "turns to flee" from
  Elbereth next to the stairs, one step + '>' leaves it behind (T:2935).
- **Pet test in a 1-wide corridor next to you** works even in the dark (adjacent squares are always seen): the kitten
  had to cross the drop square to reach me — no "steps reluctantly" + it picked the gloves up = not cursed.
- **Hunger**: after a prayer (900 nutrition) Hungry came ~740 turns later and Weak ~95 after that. Keep 2 rations;
  Sokoban levels carry several (Soko 1: 3 rations + 3 candy bars).
- **Acid blob**: thrown daggers/darts, then a KICK finished it — no sword contact, no corrosion.
