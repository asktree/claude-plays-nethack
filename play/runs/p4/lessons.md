# p4 lessons

- **Pet curse test: do it in a LIT doorway, in view.** NetHack prints "X steps reluctantly over Y" only when you
  can see the pet's square (dog_move: cansee). In a dark corridor 2+ squares away you get no message even for a
  cursed item. Then only the pet's avoidance timing is (weak) evidence. Drop the item in the doorway of a lit room,
  stand 2 squares inside, and the answer comes in 1-3 turns (worked twice on DL1: one cursed, one clean).
- **Pets play fetch.** A kitten picks up non-cursed items (itself proof the item isn't cursed) and drops them
  near you later. Apport falls with every drop that isn't rewarded, so it may keep the item for 50+ turns. Grab
  it when the pet is busy eating, or step onto the drop square at once.
- **Always give pickup() a pattern.** A bare `pickup()` took a 350-weight large box.
- **Locked boxes.** Kicking breaks the lock 1 time in 5 (THUD = it didn't move; 15 misses happen). #force with a
  SPARE uncursed dagger (never the long sword: blades can snap). Put the re-wield in the same step, because a
  pause (Hungry) can hit between force and re-wield. Check the wielded weapon after any interrupted script.
- **go_down() may leave the pet behind.** Before stairs, make sure the pet is adjacent (or accept losing it).
- **Two '>' on one level (DL2-4):** take the nearer one. If "where:" says Dungeons Level N+1, the other is the
  Mines; `go_down(to='Mines')` then resolves it by elimination.
- Werejackal in @ form: kill it at once in melee (no lycanthropy from @-form hits). Only the jackal-form bite
  infects.
- In a shop, `sell_offer()` on unknown scrolls/potions is a cheap price-ID (2 turns). Selling a CURSED unknown
  potion (100zm offer) paid for a useful 80zm-base scroll.
- Gnomes, gnome lords and dwarves in the Mines were all peaceful to this dwarf. The hostiles on Mines 1 were a
  straw golem, a hobbit (throws daggers), a kobold shaman, and traps (pit, arrow trap, magic trap).
