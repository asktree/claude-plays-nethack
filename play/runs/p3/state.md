# p3 — current state (rewrite as things change)

## Character
- Name/role: P3, lawful female dwarven Valkyrie, god: Tyr (local practice game, seed 303)
- Turn / Dlvl / XL / HP / Pw / AC: T:12158 / SOKOBAN top level (Soko4 = 'Sokoban / Level 6', Dlvl 6) at (31,14) / XL13 (Exp 43365; XL14 at 80000) / 132/142 / 22/22 / AC-7
- Attributes: St18 Dx14 Co19 In9 Wi12 Ch10
- Intrinsics (source, turn): cold res (Valk), stealth (Valk), infravision (dwarf), SPEED (Valk XL7) + VERY FAST from speed boots, TELEPATHY (floating eye corpse, T:11594: blindfold h ON = see all minded monsters; telepathy_scan()). NOT poison resistant. Excalibur: +2 to searching.
- Luck: back to ~0 (the T:8033/T:8074 sacrifice Luck timed out by ~T:11700). Prayer timeout surely 0 (never prayed). Alignment fine.
- Skills: long sword EXPERT (T:5735), dagger Basic
- Hunger: ate a food ration T:11650 -> next Hungry ~T:12400. Two worn rings add hunger (~1.1/turn total).

## Prayer log
| turn | reason | result |
|---|---|---|
| (none yet) | | prayer timeout surely 0: first prayer safe in MAJOR trouble (HP<=17 at max 102 (1/6 at XL8), or Weak) |

## Equipment worn/wielded (letter: item)
- a: the blessed rustproof +3 Excalibur (wielded; enchant weapon read T:7764; safe to enchant up to +5)
- b: uncursed +0 dagger (alternate; `x` swaps)
- c: uncursed +4 small shield. At +4 another enchant armor on it EVAPORATES it 3 in 4: TAKE IT OFF before reading enchant armor
- m: uncursed +0 orcish helm; M: uncursed +0 splint mail; P: uncursed -1 SPEED BOOTS
- j: uncursed +0 CLOAK OF INVISIBILITY (WORN since T:5518). TAKE IT OFF before entering any shop (T j, W O). Invisible = monsters guess my square ("explodes at a spot in thin air", "strikes at thin air").
- O: uncursed +0 elven cloak, carried for shop visits
- J: uncursed ring of PROTECTION FROM SHAPE CHANGERS, WORN left hand (T:8137)
- k: uncursed ring of TELEPORT CONTROL, WORN right hand (T:10712) (useless on no-teleport levels: Sokoban, Medusa, Castle — swap for Z there when needed)

## Key inventory (letters)
- Food: D 2 uncursed food rations; F uncursed candy bar; E uncursed cram ration (never rots)
- STONING CURE: u 3 uncursed LIZARD CORPSES (never rot)
- Ranged: t 2 uncursed elven daggers + U uncursed elven dagger (quiver), b +0 dagger. (4 cursed -1 daggers dropped on Soko4 (32,12).)
- Scrolls: o uncursed REMOVE CURSE; G 3 uncursed TELEPORTATION (normal levels only; while Confused + ring k = level teleport, but 80% 'Oops' random level at Luck 0); d uncursed unlabeled (blank); g uncursed VELOX NEB, K uncursed VE FORBRYDERNE, Q 2 uncursed NR 9 (all unknown; Q is not scare monster). Unknown pool: gold/food detection, confuse monster, destroy armor, fire, punishment, genocide, charging, taming (+scare monster for g/K).
- Spellbooks: none (thin + light green dropped at D18 (43,7): Int 9, too heavy).
- Potions: x CURSED potion of CONFUSION (smoky; a confusion source for a level teleport); H uncursed SPEED (milky); I 1 uncursed EXTRA HEALING (emergency); l uncursed emerald (unknown); r uncursed SEE INVISIBLE. COLD BREATH / fire ants destroy potions/scrolls.
- Rings: J PROTECTION FROM SHAPE CHANGERS now WORN (left hand, T:8137: stops lycanthropy, forces weres to @ form and vampires out of bat/fog form); N uncursed FIRE RESISTANCE (identified T:8173, the engagement ring); B uncursed REGENERATION (silver; identified T:8456 — wear for healing, costs extra hunger); Z uncursed LEVITATION (topaz; identified T:8456 — Medusa/Castle/escape; uncursed = removable); k uncursed TELEPORT CONTROL; (see above)
- W uncursed WAND OF TELEPORTATION (copper): 4 charges used (engrave, test, D23 minotaur T:10824, Soko4 mimic T:11859) of 4-8 -> 0-4 left, MAYBE EMPTY. Zapped at a monster it works even on no-teleport levels. brass wand = MAGIC MISSILE (seen an ice troll zap one).
- Wands (all altar-tested uncursed): n WAND OF DIGGING (found D18 T:9062; used: 1 engrave + 3 zaps (2 vault, 1 Medusa hole T:10506) -> 0-4 charges left, maybe EMPTY); V WAND OF PROBING (0:4); R WAND OF SECRET DOOR DETECTION (spiked; formally identified T:6579: it UNMASKS MIMICS within 8 squares, even on traps); (undead turning + light wands dropped at D12)
- Tools: f uncursed UNICORN HORN (apply for conf/stun/blind/sick); h blindfold (yellow light trick!); v skeleton key
- Gems (all uncursed): S black, T AMETHYST (base 600), e yellow, q white (D23), w yellowish brown (D23), y 5 orange, z 4 violet, A 6 yellowish brown (unknown, maybe glass)
- Gold: $772. Next protection costs 400*XL (5200 at XL13) at any temple priest. D8 VAULT still holds gold.

## Identified appearances
- scrolls: ELBIB YLOH = identify; ZLORFIK = light; KO BATE = enchant weapon; GNIK SISI VLE = remove curse; KERNOD WEL = enchant armor; ETAOIN SHRDLU = stinking cloud; MAPIRO MAHAMA DIROMAT = teleportation; ANDOVA BEGARIN = magic mapping; DAIYEN FOOELS = create monster; ZELGO MER = amnesia; KIRJE = earth
- potions: SMOKY = CONFUSION; puce = oil; orange = extra healing; white = object detection; golden = see invisible; swirly = blindness; YELLOW = INVISIBILITY; CLOUDY = FULL HEALING (seen quaffed by leprechauns); FIZZY = GAIN LEVEL, MILKY = SPEED (seen quaffed by D21 undead) -> H is a potion of SPEED
- rings: ivory = teleport control; agate = invisibility; emerald = protection from shape changers
- wands: steel = undead turning; tin = slow monster; spiked = secret door detection; runed = light; hexagonal = probing; forked = digging; COPPER = TELEPORTATION
- armor: opera cloak = invisibility; mud boots = speed; riding gloves = fumbling; faded pall = elven cloak. whistle = tin. wands: BRASS = MAGIC MISSILE.
- Price rules: HUNGRY doubles food prices. Wonotobo (Minetown) lowballs unID'd items (3/8 base).

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1 | Dungeons | up (43,18), down (57,6); FOUNTAIN (19,3); hole (14,6); magic trap (16,17) |
| 2 | Dungeons | up (53,3), down (36,14); Ermenak's armor shop (69-73,12-16), door (68,16) |
| 3 | Dungeons | up (45,18) with RED MOLD (44,18); down (47,9) with YELLOW MOLD (48,8) |
| 4 | Dungeons | up (22,5), down (60,8); MINES stairs (70,5); TELEPORT TRAP (69,5); Fleac's weapon shop (71-76,17-19) (daggers?) |
| 5 | Dungeons | up (13,8), down (76,6); fountain (74,5); unlooted large box (6,8) |
| 6 | Dungeons | up (8,6), down (9,16); "heard: shop" somewhere unexplored |
| 7 | Dungeons | up (4,14), DOWN (72,4) (was under gold); spiked pit (22,4); boulder (40,3) |
| 8 | Dungeons | up (17,6), down (70,10). **VAULT (2-3,17-18): ~$1650 of MINE + the vault's gold (~4x450)**: dig in with a pick-axe/wand of digging, grab it, leave in <30 turns. WEREWOLF (@) seen near (56,13). |
| 9 | Dungeons = ORACLE | up (61,8), down (19,3). Fountains (38-40,11-13). Monkey with my remove curse fled west. |
| 17 | Dungeons | up (5,8), DOWN (69,3). SPOTTED JELLY (46,7) (sessile; travel passes next to it). Explored: 5 rooms, dead door (63,5), stuck boulder corridor (27,15). Empty large box (5,10). |
| 24 | Dungeons (MAZE) | up (28,8), DOWN (21,12). T:11737 a CROWD at the up stairs: 2 MINOTAURS ((29,10) and (39,4)), PURPLE WORM (33,12), 2 fire ants, soldier ant, ogre lord, warhorse, owlbear, dog, 2 chickatrices, GIANT MIMIC (50,18). They don't move while I'm away. Wand (31,18), gold (24,8), armor (21,20). Castle is D25 or D26. |
| 23 | Dungeons (CORRIDOR MAZE, below Medusa) | up (8,8) (-> Medusa's `>` in her palace: blindfold ON + stay invisible), DOWN (38,20). Traps: pits (11,4), (34,8), TELEPORT trap (49,14), rolling boulder (47,20), rust trap (71,20). BOTH MINOTAURS KILLED. Left: python, LURKER ABOVE (25,18) (engulfer), large dog, floating eye (43,8), titanothere, hill giant. Visored helmet (7,18) left (unknown helm). Unexplored pockets behind boulders (41,6), (69,6), (60,18) (gold (61,18) behind it). |
| 22 | Dungeons = MEDUSA (medusa-4) | arrival up stairs (71,13) on a small EAST island; MY HOLE at (71,15) (falls to D23). Medusa + down stairs in the far-west palace ($place: map (4,8)/(10,4)/(10,8)/(10,12)); PERSEUS' STATUE in another palace room (75% shield of reflection, cursed +0; 25% levitation boots) — needs a wand of striking/force bolt to break. Kraken in the palace moat; giant eels, jellyfish, ~14 snakes, black nagas (one peaceful), python, pit viper. Level is noteleport (monsters CAN be teleported by wand W). |
| 21 | Dungeons | up (39,18), DOWN (62,15) (room 61-65,13-17). GRAVEYARD (63-71,4-8), doors S (63,9), W (62,7): 9 wraiths + 3 vampires + ghouls killed; still ASLEEP inside: 2 MARILITHS, 4 ghosts, ~12 zombies; 2 unlooted LARGE BOXES (67,4), (69,6). Fountain (4,3) in the W room (2-11,2-8). A winter wolf cub roams the SW. |
| 20 | Dungeons | up (28,13), DOWN (72,14) (room 72-76,14-17, doors (71,15) west, (75,13) top). Fountain (25,5) in room (22-30,4-7). **GIANT BEEHIVE** (killer bees, asleep) below the doorway (3,14) in the SW: avoided (x0-11,y15-20) — never enter without poison resistance. Roaming soldier ants (2 killed). Partly explored (north-east, south). |
| 19 | Dungeons | up (33,9), DOWN (76,12). Fountain (33,17). Trapped closet (32,21) behind (32,20): vault teleporter or LEVEL TELEPORTER (avoided); an unfound VAULT (~4000 gold: dig in with the wand if charges allow). Locked door (61,13) north of the room (52-61,14-17) unexplored; locked (8,14), (32,10). Spellbook (15,19) left. |
| 18 | Dungeons | up (42,6) (room 42-44,5-7; my junk at (43,7): 2 spellbooks, spare wand of secret door detection). **DOWN (6,13) is INSIDE AN ANTHOLE** (room 4-9,13-17, SOLDIER ANTS asleep, ~food on many squares; doors (10,13) (closed by me) and doorless (10,16)). Plan: open (10,13) from (11,13), kill the sleeping ants on (9,13),(8,13),(7,13) one blow each, step onto `>`. VAULT (9-10,4-5) emptied via a dug tunnel from the NW room (19,4). Gold in rock (15,3). Rooms: NW (19-34,3-6), NE (55-70,7-12), SW (15-24,15-20), S (38-41,16-18). |
| 16 | Dungeons = QUEST PORTAL LEVEL | arrived T:8457 at the up stairs (4,5): "faint telepathic message from the Norn ... Shrine of Destiny". MAGIC PORTAL to the quest at (46,5) (room 42-52,4-7). Temple of ODIN (neutral, peaceful priestess), altar (18,8) (room 12-23,6-11). Start room door (7,8) + hidden door (13,8). Booby-trapped door (52,7) exploded. LAWFUL ALTAR (58,18) in a small room (56-60,18-19), no priest: co-aligned sacrifice spot on the portal level. DOWN (70,9). Vault somewhere ("counting money"). Trap-door closet (22,5). Quest needs XL14 + piety 20. |
| 15 | Dungeons = ROGUE LEVEL | up (10,5), DOWN (36,10) (shown as %). Conical hat (36,9) left. Not the portal level (no message). |
| 14 | Dungeons | up (65,8), DOWN (16,6). MORGUE (68-75,14-17): a sleeping VAMPIRE (68,17) (left asleep) + a few zombies; wraiths/ghosts/ghouls killed. CHAOTIC ALTAR of Loki (41,17) (BUC tests). Trap under a scroll (42,19). Hidden corridor (35,16). Not the quest portal level. |
| 13 | Dungeons | up (12,4), DOWN (26,16), fountains (15,5), (30,17). LAWFUL ALTAR OF TYR (40,9) (plain altar, no priest): sacrifice fresh corpses here; free BUC tests. Fully explored. One-time TRAP DOOR closet (59,21) behind a secret door (59,20) ("Vlad was here"). Not the quest portal level. |
| 12 | Dungeons | up (51,14), DOWN (11,13). LEPRECHAUN HALL (27-40,4-7) cleared; 1-2 leprechaun thieves may still roam with ~$900. Junk dropped at (33,5). Elf loot pile (42,10): elven bow, 9 elven arrows, broadsword, short sword, shield, 2 elven leather helms, scroll of create monster. Explored except behind a boulder (34,10). |
| 11 | Dungeons | up (33,9), DOWN (63,10) reached via the HIDDEN DOOR (53,17) of the small room (49-53,14-18) (unlocked). TEMPLE OF LOKI (chaotic, peaceful priest), altar (52,7). Grave (39,11). Fountain (38,9). Not the quest portal level. |
| 10 | Dungeons | up (74,12) (from D9), SOKOBAN up stairs (4,8) (far west room), down (55,12), fountain (60,12), grave (74,16). HIDDEN DOOR (50,11). **TEMPLE OF ODIN (neutral), peaceful priestess, altar (38,5)**: protection 400*XL; altar BUC tests. Mummy wrapping (9,7). Locked door (71,14). |
| 9 | SOKOBAN 1 (soko4-1) | SOLVED. down (38,10) -> D10 (4,8); up (38,12). Junk pile (35,17): cursed blindness, amnesia, tripe. A crossbow + 3 crossbow bolts at (42,7) (left there). |
| 8 | SOKOBAN 2 (soko3-1) | SOLVED. down (35,8), up (47,10). Wood nymph killed T:11808. |
| 7 | SOKOBAN 3 (soko2-1 = Level 3b) | SOLVED T:6568. down (36,16), up (46,10); stair-room door (48,14) unlocked. |
| 6 | SOKOBAN 4 (soko1-1 = Level 4a, PRIZE + ZOO) | **T:12158: ONE HOLE LEFT, (48,5).** The mimic and boulder L were teleported away by wand W (T:11859); M, N, R, P, J, D, B pushed by hand. LAST BOULDER A is at (31,12): `sokoban.push_wiki(31, 12, 'urrruuuluuurrrrrrrrrrrrrrr')` (spares E (37,9), (29,16), (35,16)). An ICE TROLL with a WAND OF MAGIC MISSILE roams the upper rooms (last (34,10), on A's route): kill it first (it revives: eat or leave the corpse far away). The solver can't resume (holes differ from its plan): use push_wiki. Then row 5 -> (50,5) -> east corridor (ZRUTY + bugbear awake there) -> zoo door (49,17). ZOO (44-48,14-20) ~23 asleep incl. Elvenking, 2 Grey-elves, SCORPION (poison-res corpse), water nymph, xan, wererat, rust monster; PEACEFUL dwarf king (47,14) and couatl (47,16). OLD NOTES: Row 5 holes (34..39) filled; boulder L sits at (39,5); a **GIANT MIMIC (L10, HP 50 max, AC 7, breathless, not fire-resistant)** sits on the HOLE (40,5) right behind it: the boulder can't be pushed and the mimic can't be reached in melee (walls around, holes east). It never moves (Sokoban monsters never step into known holes). Killing it needs ~50 ranged damage in one go (it regenerates 1 HP/20 turns): wand of fire/cold/lightning/magic missile (rays pass boulders; cold is safest for me: a bounce can't hurt me), or 4-5 LIT POTIONS OF OIL (a lit oil potion explodes 4d4 on the target square hit or miss), or ~20 daggers. NOT striking/digging/force bolt (they break the boulder first: Sokoban Luck -1). NOT stinking cloud (breathless). Everything thrown there lies on the hole square and gets BURIED when the boulder plugs it. The zoo room (44-48,14-20), entrance door (49,17) from the east corridor (50,5..17); closets (42,15/17/19). Down stairs (27,5). A second giant mimic was killed at (37,12); a VAMPIRE BAT flutters around (poisonous bite). |
| 5 | Mines 1 | up (28,3), down (60,13) |
| 6 | Mines 2 | up (8,6), down (54,7) |
| 7 | Mines 3 = MINETOWN | up (3,2); Temple of ODIN altar (33,4); Wonotobo's general store door (68,9); deli door (9,12); Stewe's tools door (58,15); Izchak's lighting door (26,19) (potions of oil? base 250 = too dear); fountains (52,10), (12,16) |

## Pets
- none

## Threats / known dangers
- Soko4 (here): ICE TROLL with a WAND OF MAGIC MISSILE (revives), ZRUTY (up to ~42/turn, slow) + bugbear on the east corridor, the ZOO (asleep; 2 peacefuls inside: dwarf king, couatl — fight() looks before each blow).
- D24: minotaur pair + purple worm + ants queue at the up stairs (28,8). D23: lurker above (25,18).
- D22 MEDUSA: see the plan below (invisible = she stays frozen; blindfold + telepathy for any fight).
- Poison: NOT resistant (soldier ants, bees, scorpions, snakes: 1/240 death per poisonous hit). Winter wolves / fire ants destroy potions and scrolls.
- D14 morgue vampire (asleep), D17 spotted jelly, D18 anthole around its `>`, D20 giant beehive, D8 werewolf, D3 molds by the stairs.

## Objective and plan
- NOW (next shift): finish SOKOBAN 4. (1) Kill the ice troll (magic missile wand; wait for it at a spot where it must come adjacent; drop nothing). (2) `sokoban.push_wiki(31, 12, 'urrruuuluuurrrrrrrrrrrrrrr')` to plug the last hole (48,5) (check the board first: A must still be at (31,12)). (3) Walk row 5 east to (50,5); kill the zruty (slow: 2-3 blows, full HP) and bugbear. (4) The ZOO via its east door (49,17): at full HP, from the doorway, one sleeper at a time (stealth keeps the rest asleep); never hit the peaceful dwarf king/couatl; kill the water nymph and xan early, wererat in @ form only (ring J). Eat the SCORPION corpse fresh (poison res chance). (5) PRIZE: 50% amulet of reflection / 50% bag of holding.
- Then: Minetown (D4 -> Mines 3 = D7): buy a PICK-AXE at Stewe's tools shop if stocked (Perseus' statue needs it); protection costs 5200 at XL13 ($772 now). Consider the D8 vault gold.
- Then back down: stairs to D21, then D22 Medusa's east island via D21's `>`; or a level teleport (quaff x = cursed confusion, read G with ring k; 80% random level at Luck 0 — raise Luck first). Perseus: see the Medusa plan.
- XP: XL14 at 80000 (43365 now) for the quest (portal D16 (46,5); also piety 20).
- MR is still missing: no Castle (D25/26) without MR or reflection (PLAYBOOK A1).
- THE WAY BACK DOWN/UP PAST MEDUSA (worked out T:11740 from the 3.6.7 source):
  * Medusa (M3_WAITFORU, made by sp_lev with NO_MM_FLAGS) stays FROZEN in "wait for you" mode until she can SEE me (m_canseeu: impossible while I am INVISIBLE — she has no see-invisible) or is DAMAGED. While waiting, dochug returns before her gaze code (monmove.c 388-430): no gaze, no moves. So: cloak of invisibility ON = she never activates. Never zap or hit her unless Blind (a zap calls m_respond = her gaze; damage ends her wait).
  * I now have TELEPATHY (floating eye, T:11594): blindfold h ON = I see her and every minded monster, and her gaze can't work (canseemon false while Blind).
  * Route A (stairs): at D23 `<` (8,8): blindfold ON, climb. I arrive on her `>` in one palace room ($place[0] of (4,8),(10,4),(10,8),(10,12) map coords; desmap gives screen coords); she is shoved next to me, frozen. Leave her alone. The palace doors are LOCKED (key v, works blind); the hall's exits are SECRET doors (19,3) NE and (13,14) S (map coords) -> land strip row 15 -> water east. Swap ring k -> Z (levitation; D22 is no-teleport anyway) and float east to the up stairs (east island, map x 67-74). Kraken sits in the palace's inner moat at map (7,7) (next to the west room); 2 giant eels + 2 jellyfish roam: telepathy shows them, stay 2+ squares away (a wrap drowns you even while levitating). Yellow dragon + babies ASLEEP at map (4-5,4-5) NW outside the palace (stealth keeps them asleep).
  * Route B (no Medusa at all): a CONFUSED (or cursed) read of a teleport scroll with ring k on = choose any level. A level teleport INTO D22 without the Amulet lands in the EAST region (TELEPORT_REGION down = map (64,1)-(74,17)), next to its up stairs. USED T:11738 from D23 (smoky potion = confusion, scroll p): arrived D10 — but 4 in 5 such reads go to a random level at Luck 0. All teleport scrolls now tested UNCURSED; x (cursed confusion potion) is the next confusion source.
  * Perseus' statue (medusa-4): in one of the 3 other palace rooms: 75% cursed +0 SHIELD OF REFLECTION, 25% levitation boots, 50% +2 scimitar, 50% sack. Breaking it needs a PICK-AXE/mattock applied at it (dig.c DIGTYP_STATUE), a wand of striking or force bolt. Crystal ball lies in the moat at map (7,8) (under water).
- Carried escapes: G 3 uncursed scrolls of TELEPORTATION (not on no-teleport levels: Sokoban, Medusa, Castle), W wand of teleportation (0-4 charges, maybe EMPTY), wand of digging n (0-4, maybe empty), ring Z levitation, I extra healing, H potion of speed, unicorn horn f, prayer (timeout 0, never prayed; Luck ~0), 3 lizard corpses (u), stairs.
- Unknowns: scrolls K (VE FORBRYDERNE), Q 2x NR 9, g VELOX NEB (all uncursed); potion l emerald; gems S, e, q, w, y, z, A (T = amethyst).
- Shops: TAKE OFF the cloak of invisibility (T j, W O) before entering.
- Later: D24 wand (31,18) (crowd at its stairs), D21 graveyard boxes (67,4)/(69,6); D8 vault gold (dig in), D19 unfound vault, Mines' End luckstone, protection 400*XL at any temple.
