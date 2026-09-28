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

## Shift 2 (resumed)
- **Unicorns never step next to a hero they can see** (monmove.c m_move: NOTONL; every adjacent square is "in
  line"), and teleport 50% of the time when boxed in. They only melee when YOU step next to them (or they can't
  see you: don't blind one with the camera). So stepping one square away always ends the fight. Rule used: be
  adjacent only while HP >= the max damage of one unicorn turn (black: 2 moves x (d12+d6) = 36). It hides behind
  wall corners, so explore()/travel() walk you into it: watch where it was last seen.
- **In NetHack 3.6.7 the MAGIC LAMP's base price is 50** (objects.c), not 500. With Cha 8-10 the lamp was 89zm
  (50 x 4/3 x 4/3). An oil lamp would be 13 or 18. Always compute: price / Cha factor / (1 or 4/3).
  Calibrate the Cha factor with an identified item (food ration base 45 sold at 60 = x4/3).
- **Orcish arrows from a monster's starting inventory are ALWAYS poisoned** (makemon.c m_initthrow) and each hit
  is a 1-in-30 instadeath without poison resistance (attrib.c poisoned: rn2(10+20)). Monsters only fire when
  lined up and < 8 squares away; they wield the bow when you come within dist^2 64 ("wields an orcish bow!" =
  that one is the archer). Fight packs from a square whose lines are all adjacent squares or walls.
- **Melee from a DUST Elbereth**: attack() wipes 3 letters (u_wipe_engr(3)) before the monster is angered, so the
  engraving is always broken first and there is no hypocrisy penalty (3.6.7 uhitm.c line 428, mon.c setmangry).
  The harness still refuses it: step off first.
- Luck-0 prayer OFF an altar fixes only MAJOR trouble (pray.c pleased(): action = rn1(Luck+2, 1) <= 2): praying
  while merely Hungry wastes it — wait for Weak. On a co-aligned altar/shrine the roll is rn1(Luck+3(+1 shrine), 1),
  so actions 3-4 can fix minor trouble too.
- A blessed spellbook skips the failure roll (spell.c study_book) — but a "dull" one can still put you to sleep.
- Minetown: desmap.identify() names the variant; the level file (dat/mines.des) gives every shop and the temple.
  Shopkeepers refuse entry with a pick-axe: drop it right outside the door and be quick (dwarves pick them up).
- Nymphs start with a mirror (50%) and a potion of object detection (50%): two nymphs' bubbly potions = object
  detection.

## Shift 3
- **Finding the Oracle level cheaply**: oracle.des puts the Delphi (11x9 room + walls) at the map centre, screen
  x 33-45, y 7-17, and random rooms keep a margin from it. A seen room or corridor inside that box rules the level
  out. With DL6/7/8 ruled out that way, a full explore of DL6 (one '<' only) ruled out DL5 -> Oracle DL9, Sokoban
  '<' on DL10. Telepathy while blinded showed "peaceful Oracle" and confirmed it.
- **Nymphs charm armor off**: "You gladly start removing your dragon mail" = MR gone. Stealing weights WORN items x5
  (steal.c), so the GDSM is ~10% of any theft. Never walk up to an awake nymph (hunt() gives her the first move):
  throw daggers from a line, or hit her while she's asleep. After any theft, check inventory for "(being worn)".
  A fleeing wounded nymph drinks potions (effervescent = extra healing) and picks up your thrown daggers; they come
  back to you when you walk over them later (pickup_thrown).
- **Diagonal corridor squeeze**: with a pack over 600, "You are carrying too much to get through." Dig one
  orthogonal square with tunnel() (1 dig) instead of trusting explore()'s "couldn't reach".
- **Holes in Mines corridors**: a hole in a 1-wide corridor cuts the level; tunnel() round it through the walls
  (Mines walls dig).
- **Giant spider corpse at St 18/xx**: the poison costs rnd(4) points off the 18/xx percentile — no damage-bonus
  loss down to 18/01. 1/3 chance of poison resistance (it failed this time).
- **Sokoban**: sokoban.solve() handles it; monsters trapped in pits on a boulder's route must die first (let the
  solver fill the pit next to it, then stand there). The stair room's door may be locked: carry a key. Chickatrices
  are speed 4: fight them from the doorway, then from the corridor square below it (one attacker at a time);
  keep 2 lizard corpses.
