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
