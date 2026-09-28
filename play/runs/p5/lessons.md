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

## Shift 2
- **Price every "lamp" in Izchak's shop**: with the oil lamp already identified (a Valkyrie's starting lamp), an
  unidentified "lamp" IS a magic lamp — the price (base 50 -> 75/100 at Ch 7) just confirms it. Bought one for 75.
- **Uncursed water costs 8 zm at Ch 7** (shk.c: uncursed water is priced 0 -> 5 -> x1.5): a cheap "clear potion" in a
  deli is plain water — the raw material for holy water (co-aligned altar + a successful prayer blesses water there).
- **Read-test 100zm scrolls with the body armor OFF**: destroy armor takes cloak > body armor > shirt > helm > ... — with
  the mail off it ate the 1-AC helm instead of the 5-AC splint mail. Drop potions/other scrolls first (fire).
- **Never search ('s') to "wait" next to a disguised mimic** — it unmasks it. Wait with '.'.
- **Shopkeeper parked on his post**: he only steps aside at random and walks straight back while you stand in line with
  him (shk.c). Stand where one of his steps lands OFF your lines (e.g. (35,15) with him at (35,16): he went to (36,17)).
- **Minetown room variants have hidden exits**: Alley Town's exit here was the SE street corner doorway (56,19); the
  harness had "no known path" because that corner was never seen. Note town exits in state.md.
- **Hidden doors follow mklev join() order**: rooms are joined in order of their left edge; a dead-end map with unexplored
  space to the east -> search the east wall of the easternmost known room (found (45,3) in 7 turns there after 30
  fruitless turns in the other corner).
