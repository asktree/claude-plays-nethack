# p5 lessons

## Shift 1
- **Corpse piles on DL1-4 are trap victims** (3.6.7 mklev.c mktrap): a human/elf/dwarf/orc/gnome corpse (aged 51+ turns)
  with 1+ ALWAYS-CURSED items (weapon/tool/food/gem) lies ON a trap (arrow, dart, rock, bear trap, sleeping gas,
  rolling boulder...). Farlook "% ... (a human corpse)" + "pile" -> avoid() the square, never take the items. p5 had 4.
- **Pets refuse known traps** (39/40): an anti-magic field in a 1-wide Mines passage kept the housecat from following me
  to the stairs. Decide early (walk it past before the trap is seen, or accept losing it).
- **Magic trap "flash + deafening roar"** = blind ~10 turns + 1-4 random monsters made next to you. Standing on the '>'
  (adjacent) as an escape hatch and searching until sight returned worked; the unseen "I" was my own kitten (don't
  swing at an I while blind unless it attacks you).
- **A thrown missile stops at the first monster, hit or miss**: all daggers land UNDER the target. Versus a floating eye
  that means it sits on your ammo. Floating eyes do drift (speed 1): wait, grab the pile, throw again. A towel (worn with
  P) is the melee fallback (the eye's passive needs you to see it).
- **Selling in a small shop**: sold items become shop goods on the free squares; sell_offer() needs an EMPTY floor
  square to re-pick your own item. Do all price-ID offers FIRST, then sell.
- **Minetown room variants** (minetn-2/3/4): a rooms-and-corridors level whose '<'/'>' are in outer random rooms joined
  by '#' corridors; desmap.identify() returns None there. Alley Town has 1-wide '|.|' alleys and mimics in shops.
- **altar_test() re-picks items**: a second floor pickup of an unknown scare monster scroll destroys it. Scrolls that
  survive a 2nd pickup are proven NOT scare monster (free information).
- Rotten food: the one known-uncursed ration was fine, a floor ration of the same age was "Blecch! Rotten" (1 in 7 for
  any non-corpse food older than 30 turns). Eat on Elbereth with nothing hostile in view.
