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

## Shift 4
- **Sleeping nymph + Stealth = free kill**: disturb() never wakes anything while you are Stealthy (monmove.c), so
  hunt() can walk up to a sleeping nymph and hit first (Excalibur killed one in 2 blows before she acted).
- **Tripe for a dwarf: "Yak - dog food!" starts a VOMITING countdown** (50%): conf at 11, stun at 8, vomit at 0.
  The unicorn horn cures it, but only "You feel much less nauseated now." proves it: "This makes you feel better!"
  means an ATTRIBUTE point was restored (3.6.7 apply.c: the horn still restores lost St/Dex... points) and "You feel
  less confused" only fixed the symptom. Never push Sokoban boulders while a vomit countdown may be running:
  wait (search) or apply the horn until "much less nauseated". Old food (Sokoban's tripe) is rotten 1 time in 7.
- **Blocked Sokoban push by an unseen monster on a hole**: a failed push costs no time. ESP not showing it = mindless
  flyer. Rays and thrown weapons pass over boulders; a ray bounces off the far wall but its range (7-13) is
  limited — count squares before zapping. A weapon hitting a monster over a hole falls to the level below.
- Engrave-test in Sokoban works; do it one square away from where you will zap (the test leaves an Elbereth).
- Scorpion corpse (fresh) gave POISON RESISTANCE at the first try (50%); eat it before bigger risks.
- **Soldiers lined up in a corridor**: get out of their line first (wands), then a SLEEP RAY down the corridor
  freezes them ~6d25 turns (sleep_monst sets mfrozen: hitting doesn't wake them) — 3 sergeants died without a swing
  back. Count the bounce: range 7-13, each hit -2; from 6+ squares before the far wall it can't come back to you.
- **Object detection finds the Sokoban prize closet** (one of three behind the zoo): plan a route over the zoo's EMPTY
  squares (the ones next to the room's first door get no monster) so only 1-2 sleepers need killing.
- **Collectors (centaurs, monkeys, nymphs) pick up floor items**: a wand seen on the floor was gone 60 turns later; it
  was in the forest centaur's death pile.
- Unicorn horn messages: "Nothing happens." = no trouble; "Nothing seems to happen." = trouble not fixed this time.

## Shift 5
- **Telepathy/ESP never shows MINDLESS monsters** (mummies, zombies, blobs, jellies, golems): a zoo route planned from
  object detection + ESP had monsters on half its "empty" squares. Open the door and LOOK before committing.
- **A sleeping zoo + Stealth = a farm**: kill sleepers one at a time from free squares (most die to one blow; only the
  target wakes; melee makes no noise in 3.6.7). 30 kills, 2 zruties included, for -15 HP total and ~$5800 of gold.
  The closet with the burned Elbereth + scare monster scroll was the fallback refuge.
- **Soldiers/sergeants zap wands at melee range** (muse.c: before melee). The sergeant's wand of COLD shattered 2
  potions although I resist cold: bag potions/scrolls in the bag of holding before any fight with a wand carrier.
- **Zoo gold -> temple protection**: 400*XL (3600 at XL9) gave 3 AC points the first time (rn1(3,2)). Buy BEFORE
  levelling (XL10 costs 4000). A co-aligned altar BUC-tests everything by dropping it (amber = blessed, black = cursed).
- **Werewolves in wolf form**: each bite that hits = 1/4 lycanthropy with MC0 (GDSM has MC0!). Wear a cloak (MC1+).
  Fight them from a 1-wide passage: the summoned wolves then come one at a time.
- **A sleeping nymph next to the stairs**: watch 3-4 turns from a distance (no movement = asleep) and walk past with
  Stealth instead of risking a failed one-blow kill (she then steals: maybe the GDSM or the bag).

## Shift 6
- **Mines' End (Catacombs) luckstone, cheaply**: mines.des `$place = {(1,15),(68,6),(1,13)}` + the map offset gives the
  3 spots; SHUFFLE puts the luckstone, the flint (both on LEVEL TELEPORTERS: harmless with MR, "wrenching sensation")
  and nothing. The maze walls dig (not the closets): tunnel() with the pick-axe along one row is fast and
  predictable; the stair room's exits are SECRET doors (tunnel digs through them). To tell luckstone from flint:
  carry the stone and zap enlightenment — an uncursed luckstone shows "You are lucky" (+3); no luck line = flint.
- **Mines' End is the Mines' 8th or 9th level** (dungeon.def (8,2) = rn1(2,8)); a desmap "minend" match anywhere
  shallower is false. Check the depth before trusting an identification.
- **Mind flayer with low Int**: don't melee. A wand of TELEPORTATION zapped at it (even adjacent) has no resistance
  roll and sends it away; digging down is the other clean exit. Its psychic blast locks on through an amulet of ESP
  (~25 HP in a few turns). Grease the helmet (can of grease) before any planned fight: tentacles slip off it.
- **Quantum mechanics** teleport you on a hit (MC1 stops only 30%): it can drop you next to the monster you fled
  from. Kill them fast or keep away when something worse is on the level.
- **At AC -15 a monster's RAY still hits ~40%** (zap.c zap_hit: AC_VALUE(-15) = -rnd(15)); only melee to-hit is
  crushed by low AC. Wand carriers (soldiers) remain dangerous without reflection/sleep resistance.
- **Food rations can be rotten** (1 in 7 once older than 30 turns): "Blecch!" = confusion (unicorn horn) and HALF the
  nutrition — hunger comes back ~400 turns later. Keep 2+ rations; buy every ration in reach.
- **Gas spore in a dark corridor**: step back until 2 squares away and throw a dagger down the line even when you
  can't see it — "You kill it!" and its blast (adjacent squares only) misses you.
- **Soldier squads in a maze**: a 1-wide dug tunnel with a wall on each side is a perfect chokepoint; 4 soldiers +
  undead died for 1 HP. The room side of a doorway (walls both sides) did the same against 7 Uruk-hai.

## Shift 7
- **An identify stack that won't merge is a different B/U/C.** Of 5 shop identify scrolls, 4 stacked and 1 didn't: that
  one was blessed and rolled "identify everything" (scroll: blessed -> rn2(5) items, 0 = ALL). Read the odd one first.
- **Price-ID with a stack of the same label at two prices**: 80 and 107 for one label -> base 60 (80 = x4/3, 107 =
  x4/3 x4/3) = ENCHANT WEAPON; a lone 107 is then base 80 (enchant armor / remove curse). Cha 8 multiplier = x4/3.
- **Eating a corpse while Satiated safely**: bound your nutrition from the last "You are beginning to feel hungry"
  (= 150) + everything eaten since - 1/turn (+1 per 20 with an amulet, +1 per melee swing). Choking needs 2000. eat()
  answers "no" to "Continue eating?" (partly eaten = NO intrinsic): do the 'e' / 'y' loop by hand with force=True
  when the upper bound stays < ~1800. A timed-out intrinsic ("You are no longer invisible.") interrupts a meal:
  just eat again.
- **Grey-elf corpse = sleep resistance 6/15 = 40%** each; the 2nd elf gave it. Stalker corpse: temporary invisibility
  + 60 turns stun (unicorn horn cured it in 1 apply).
- **Niches**: a monster seen by telepathy in blank "rock" right above a room's top wall is in a niche; its (secret)
  door is in that wall (search from inside the room), not from the corridor beside it.
- **Quest portal depth**: dungeon.def CHAINBRANCH "The Quest" "oracle" + (6,2) -> Oracle level + 6 or 7. The Big Room
  is DL10-12 (40%). Don't spend calls exploring DL10-14 hunting for the portal message.
- **Leprechaun halls**: keep $0 loose (bag it), and they are harmless sleepers you can farm for gold with Stealth.
- **Digging down with monsters around**: dig() (pick-axe) stops for any non-trivial hostile in view; a wand of
  digging zapped down ('>') is one turn and needs no pit phase.

## Shift 8
- **After a `recover` restore, the harness still remembers the undone future of the level** (features, special rooms,
  and its seen-map): head_to()/screen_frontiers() found "no frontier" on a mostly blank map. Remembered STAIRS were
  right (the level existed before the checkpoint) — walk there by hand (follow corridors) instead of head_to().
- **Quest portal level**: the Norn's message came on arriving at DL15 = Oracle (DL9) + 6. explore() with Excalibur's
  auto-search then revealed the MAGIC PORTAL (it showed up in features as `magic portal`) without any deliberate search.
- **Throne room court = XP farm with Stealth**: the court is generated asleep; ESP shows it through rock. Enter, kill
  one sleeper at a time from squares next to it (most die in 1-2 Excalibur blows; others don't wake). 11 kills, 0 damage.
  The throne-room CHEST (here on the '>') held $503, a blessed identify, a gain level potion and a wand of cancellation.
- **A monster quaffing a potion identifies it for you**: "looks completely healed" = full healing (yellow here).
- **An unknown-BUC identify from a chest may be blessed**: read it FIRST, with the most interesting items out of the bag.
- **Engrave-test by elimination**: "The engraving on the floor vanishes!" = cancellation / teleportation / make
  invisible; with the other two already identified it is CANCELLATION — keep it out of the bag of holding.
- **Chickatrices**: speed 4, one Excalibur blow each; fight them one at a time from a doorway square (walls both
  sides). A touch hit hisses 1 time in 3, and a hiss starts stoning only 1 in 10 — keep lizard corpses ready.
- **descend(1, explore=True) has a leg budget (48)**: on a big level it gives up with unexplored space left; then
  call explore() directly.
- **Monsters behind rock**: ESP shows a wraith 2 squares away with rock between; dig() one square toward it and hunt().

## Shift 9 (DL18-20: what the live game should know)
- **Sleeping COURT on DL19 = 28 kills for ~5 HP and XL10 -> 11** (hunt() loop, nearest first, HP check between targets;
  -a 'new monster: (court species)'). Court monsters are made hostile even if the species would be peaceful (gnome lord,
  gnome king for a dwarf): fight() still looks first. The ogre-king ruler carried a WAND OF SLEEP (sleep resistance made it
  harmless; its bounce slept the ogre king itself) and the other ogre king read a teleport scroll when hit. The court
  chest (under a corpse pile, not visible) held $202 + enchant weapon + a scroll + gems: visit every pile with here().
- **Trolls revive in 5-30 turns and a ROTTEN troll corpse can't be eaten** ("Blecch! Rotten food!" flags it): eat the
  first troll corpse at once (15 turns; stop to kill a reviving one, then eat() resumes the meal); each revival is just
  more XP at AC -15 (troll hits mostly miss, ~1 damage each).
- **Hunger estimates drift**: after a full troll (800) I was still not Satiated -> nutrition had been < 200. Eat big safe
  corpses whenever not Satiated; you can't choke on a meal STARTED while not Satiated (eat.c canchoke).
- **Trappers (DL20) engulf out of nowhere**: ESP showed one, it left ESP range, and explore() walked into it 4 turns later.
  At AC -15 the digestion timer is long (~25+ turns): fight() from inside, every blow hits (2 Excalibur blows). A wand of
  digging zapped inside also frees you.
- **Gelatinous cube**: passive paralysis is only 1-4 turns (d(1,4), 2/3 while it survives a blow), its touch ~1 dmg at
  AC -15: fight(x, y, allow_passive=True) is fine when NOTHING else is around (mindless monsters don't show on ESP).
- **Freezing sphere**: harmless with cold resistance (Valkyrie), even when it explodes. A LICH's cold touch is resisted too,
  and MR blocks its destroy-armor; kill it fast (curse items is its one real threat, only adjacent).
- **Pack over 600 blocks diagonal squeezes** ("You are carrying too much to get through."): tunnel(x, y) one square.
- **Enchant weapon at exactly +5 is safe** (wield.c chwepon evaporates only when spe > 5 BEFORE the read): Excalibur +6 now,
  "suddenly vibrates unexpectedly" = stop forever.
- **MEDUSA ARRIVAL (dat/medusa.des 3.6.7, all 4 variants)**: Medusa is always inside a closed building (walls/locked doors)
  far from the '<'; medusa-1/2 generate her asleep; every FALL/levelport arrival region ('down' TELEPORT_REGION) is on the
  up-stairs side. Her gaze needs couldsee() (monmove.c: m_respond when she is active and her square is in your line of
  sight) and she waits (STRAT_WAITFORU) until she can see you. So arriving by the '<', a hole or a trap door is safe;
  exploring toward her building is not. The camera applied at yourself blinds you 5+rnd(25) turns (zap.c: flashburn;
  it can't be renewed while already Blind): a cheap way to arrive blind and read the level with telepathy.
- **Coming back UP from below Medusa lands on HER '>' next to her** (medusa-3/4: awake). Stay above her until the quest is
  done or a blindfold/towel/reflection is in hand.
