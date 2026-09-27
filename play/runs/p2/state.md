# p2 — current state (rewrite as things change)

## Character
- Name/role: p2 — local practice game, seed 202 (lawful female dwarven Valkyrie, god: Tyr)
- Turn / Dlvl / XL / HP / Pw / AC: T:2706 / Dlvl 2 (main dungeon) / XL5 (Exp 205; XL6 at 320) / 63/63 / 6/6 / AC0
- Position at shift end: STANDING ON THE GNOMISH MINES STAIRCASE D2 (21,14), command prompt, nothing hostile in view, housecat 3 squares east at (24,14) (it dawdles; take one plain step toward it / wait until adjacent, then `>`).
- Attributes (status line T:1662): St:17 Dx:11 Co:19 In:11 Wi:8 Ch:9 (Cha 9 → shop prices ×4/3)
- Intrinsics (source, turn): cold res (Valk), stealth (Valk), infravision (dwarf), speed at XL7; EXTRINSIC telepathy from the amulet of ESP (worn T:2424)
- Luck notes: nothing done to Luck (no peacefuls killed, no mirrors)
- Alignment / god anger notes: never prayed; god not angry. prayer_check() at T:1240: p_safe 1.0.

## Prayer log
| turn | reason | result |
|---|---|---|
| — | none yet (first prayer fine in MAJOR trouble only; lycanthropy counts as major) | — |

## Equipment worn/wielded (letter: item)
- a: EXCALIBUR — blessed rustproof +2 (wielded; obtained T:2422 at the Oracle's fountain, 2nd dip). Read enchant weapon i on it after a BUC test (stop at +5)
- c: uncursed +3 small shield (worn)
- y: +0 scale mail (worn since T:1681; bought D4 shop; the kitten stood on it without "reluctantly" → not cursed) [seen]

## Key inventory (letters) — mark evidence: [seen in inventory] vs [inferred] vs [UNVERIFIED]
- b: blessed +0 dagger — throw it (`throw('b', dir)`); stepping onto it picks it back up (thrown-weapon autopickup) [seen]
- h: orcish dagger, unknown B/U/C, "at the ready" (quivered) — THROW ONLY, never wield [seen]
- x: curved wand = wand of COLD, FIRE, LIGHTNING or SLEEP (shop price 233 = base 175) [price-ID certain]; charges 4–8 (fresh shop stock) [inferred]; NOT engrave-tested (lightning would blind me) — identify it at its first zap: all four are bouncing RAYS, never zap toward the kitten or at a wall next to me
- o: wand of create monster (identified by engraving T:1046; charges unknown) — don't zap casually [seen]
- i: scroll of enchant weapon (identified), BUC unknown (goblin drop) — read for +2→+3 (or on Excalibur later) [seen]
- D: unlabeled scroll = blank paper (chest) [seen]
- J: scroll DAIYEN FOOELS (base-100 group), M: scroll KO BATE (= LIGHT, D2 shop price), Q: scroll ELBIB YLOH (base-100 group) [seen]
- O: uncursed AMULET OF ESP (worn since T:2424; identified by scroll) — telepathy: monsters within ~8 squares shown even when not blind, all of them when blind [seen]
- P: 12 darts (Valkyries are restricted in darts: -4 to hit, still usable missiles), S: knife [seen]
- R: black gem (unknown), K: tin opener, U: 6 elven arrows (no bow; the elven bow lies on D3 (61,19)) [seen]
- T: leathery spellbook (D5 Delphi floor), C: dull spellbook — both unknown, do NOT read (Int 11); sell/price-ID [seen]
- E: uncursed +0 high boots (identified by scroll T:2424; worn) [seen]
- F: cyan potion, H: clear potion (= water), I: magenta potion, N: murky potion (base 100: confusion/extra healing/hallucination/healing/restore ability/sleeping) — all unknown [seen]
- z: candle (for the Candelabrum eventually) [seen]
- e: uncursed oil lamp [seen]
- Escape items: none (upstairs + Elbereth; the wand x may be sleep)
- Healing: none known (potion F unknown)
- Emergency cures: none carried (stoning: lizard/acidic corpse; sliming: fire/polymorph; illness: unicorn horn/prayer; curses: holy water/remove curse)
- Food: k food ration (found D1; >30-turn rotten roll applies — eat on a safe square), f tin (unknown; tin opener K). NO lembas left. Last meal T:2678 (lembas 800) → next Hungry around T:3450. Buy/find food in the Mines; eat fresh safe corpses.
- Gold: $94 (75 from the D5 leprechaun)
- Sold/lost earlier: vellum spellbook, cursed ring of regeneration, murky potion, scroll HAPAX LEGOMENON, tin whistle, 2 eggs (D4 shop); scroll ELAM EBOW = SCARE MONSTER turned to dust; scroll of identify B used (T:2422).

## Identified appearances (appearance -> identity)
- YUM YUM -> enchant weapon (formally identified)
- ANDOVA BEGARIN -> identify (formally identified when read T:1664)
- ELAM EBOW -> scare monster (turned to dust on second pickup; named "scare monster")
- unlabeled scroll -> blank paper
- uranium wand -> create monster (formally identified)
- curved wand -> base 175: cold / fire / lightning / sleep
- silver ring -> ring of regeneration (formally identified; mine was cursed, sold)
- agate ring -> base 100 group (adornment/hunger/protection/prot. shape changers/stealth/sustain ability/warning); the D4 shop's one is CURSED (kitten stepped reluctantly)
- puce potion -> base 150 (blindness/gain energy/invisibility/monster det./object det.)
- murky potion -> base 100 (confusion/extra healing/hallucination/healing/restore ability/sleeping/water)
- HAPAX LEGOMENON -> base 100 group (confuse monster/destroy armor/fire/food det/gold det/magic mapping/teleportation)
- KO BATE -> light (D2 shop price 89) [certain]
- KERNOD WEL -> base 80: enchant armor OR remove curse (D2 shop 107)
- ELBIB YLOH, DAIYEN FOOELS -> base 100 group (D2 shop 133)
- vellum spellbook -> level 1 book (sold for 50)
- cyan spellbook, gold spellbook -> 533 zm (level 4 book, or level 3 with surcharge) at the D2 bookstore

## Dungeon map
| Dlvl | branch | features (stairs, altars+alignment, shops+type, fountains, stashes, traps, notes) |
|---|---|---|
| 1 | Dungeons | up stairs (8,8) NW room; down stairs (10,19) SW room; fountains (27,11) centre room and (5,18) SW room (Excalibur dips at XL5+); boulders (10,16),(37,16); fully explored |
| 2 | Dungeons | up stairs (40,6); down stairs (21,14) = GNOMISH MINES BRANCH (confirmed T:952); down stairs (74,17) = main dungeon; Kittamagh's second-hand bookstore (scrolls/spellbooks) at (2-5,17-19), door (6,18), far west; door (28,13) kicked open and its boulder pushed to the dead end (37,13) so east-west travel works; boulder (46,9) in the N-S corridor below the NE room (`avoid((46,9))`); SE room (58-66,15-17) with a fountain (59,16), a goblin statue (58,16); its elven arrows taken, weapon at (60,17) checked in shift 3 (see journal) |
| 3 | Dungeons | up stairs (21,18) SW room UNDER the empty broken large box (`travel_to('<')` fails: use `travel(21,18)`); hidden passage found near (30,13); down stairs (51,10) in a small room (49-51,6-10); SLEEPING GAS TRAP at (35,8) in the NW room (known, avoided); a vault exists (guard footsteps); locked door (68,12) only leads to explored corridor; elven bow left at (61,19); explored except the far east strip |
| 5 | Dungeons (ORACLE) | up stairs (9,5) NW room; down stairs (58,5) in the NE room (53-68,5); Delphi: centaur-statue room (34-44,8-16), doorways (33,10)/(36,7)/(39,7), Oracle subroom (38-40,11-13) entered by the doorless doorway (39,14); FOUNTAINS left: (39,11), (38,12) (the other two vanished/dried up); peaceful Oracle at (39,12) — never F toward her. PIT at (14,15) in the SW room (9-16,12-16). Spellbook on the floor at (44,14). SE room (57-70,15-19). Unexplored: frontier (19,17) SW, corridor (31,8)-(32,9) west of Delphi (diagonal squeeze), east/south parts. Sokoban entrance = the up staircase of D6. |
| 3 (Mines 1) | Gnomish Mines | entered T:952 from D2 (21,14), arrived at (77,13) on the far east; went straight back up; unexplored |
| 4 | Dungeons | (fully explored except the north dead end above door (41,4))  up stairs (39,18) in a small SW-centre room (33-39,18-19); down stairs (12,18) in the SW room (5-12,18-19), reached via the far-west room's bottom doorway (14,12), corridor to (9,15), then a HIDDEN passage (8,15) (found by searching); statue of an orc zombie (9,18). Far-west room (11-14,6-11) doors (15,6)/(15,10) emptied. FOUNTAIN at (22,17) in a small room (22-24,16-18), door (25,16) — Excalibur candidate. UPERNAVIK'S GENERAL STORE (69-71,15-17), door (68,16) — stock left: puce potion (200), murky potion (133), cursed ring of regeneration (267), cursed agate ring (178), vellum spellbook (133), leather armor (7), HAPAX LEGOMENON (133), whistle, eggs. Rooms: NW-centre (39-47,5-9) with the emptied broken chest (43,5), north door (41,4); west room (22-29,8-10); NE (56-66,6-9); middle (49-58,17-19) with an unchecked tool at (50,19). Yellow molds keep spawning here (4 killed). |

## Pets
- HOUSECAT (grew up T:2099 on D5). Steals kills (werejackals, rock mole, centipedes), carries items around, in a shop you can't swap with it. I hit it once with a thrown dagger (T:2100, still tame) — never throw with it in the line of fire.

## Threats / known dangers
- Werejackals: two met (D3 T:1255, D4 T:1577), both killed. Bite in `d` form = lycanthropy 1/4 per hit → cure by prayer (major trouble). Kill fast; throw daggers while they approach.
- Yellow molds (passive stun) — kill with thrown daggers, finish with one blow.
- Watch for: floating eyes (never melee), gas spores, nymphs/leprechauns, soldier ants, hill orc packs in the Mines.
- Undiscovered traps under item piles (the D3 sleeping gas trap was under a "food pile").
- Boxes: 10% trapped; drop scrolls/potions before kicking/opening; never `#force` with the long sword.

## Objective and plan
- DONE this shift: D4 `>` found, XL5 reached, EXCALIBUR obtained (T:2422).
- Current objective: enter the GNOMISH MINES (standing on the D2 branch stairs (21,14); Mines 1 arrival point was (77,13) far east). As a dwarf most gnomes/dwarves/hobbits are PEACEFUL: never attack them, farlook before every fight, expect little XP there. Go down to MINETOWN (Mines 3–4 = Dlvl 5–6): altar (BUC-test scroll i before reading it on Excalibur, spellbooks C/T, potions F/I/N, scrolls J/Q), temple (protection needs 400×XL gold = 2000+, have 94), shops (sell the two spellbooks, price-ID). Keep the Watch peaceful (no fountain use in town). XL6 at 320 Exp.
- Alternative worth raising with the orchestrator: SOKOBAN (its entrance is the up staircase of D6, just below the Oracle level D5) gives reflection or a bag of holding; at XL5 with Excalibur/AC0 the first levels are feasible; the top-level zoo wants XL8+.
- The curved wand x is the emergency weapon: zap it (`zap('x', dir)`) at the first dangerous monster in a straight line (not toward the kitten) — this also identifies it.
- Eat when Hungry: ration k on a safe square (rotten roll: eat on Elbereth/with nothing in view), fresh safe corpses (`corpse()`), buy food in Minetown.

## Harness/helper calibration notes
- `obs.under` is the map SYMBOL under you ('{', '>', '<'), not a name — test `obs.under == '{'`.
- `fight()` pauses on every monster taunt (imps: "Doth pain excite thee?"); for chatty monsters use a custom loop: re-check `hostile_at(x,y)` (not tame/peaceful/statue) before each `F`+dir, stop at HP < 30, pass `ok=[...]` for the routine hit/miss lines.
- `throw()` does NOT check the line of fire: verify no pet stands between you and the target (I hit the housecat at T:2100).
- `explore()` can say "explored" while a seen dead-end corridor leads into unknown space (D4 (9,15): search there), and "blocked ... travel couldn't reach" when the frontier is only reachable through a diagonal squeeze (inventory > 600: "You are carrying too much to get through") — find another entrance.
- `path_to()` returned None for a floor square holding a spellbook (`+` at D5 (44,14)); walk to a neighbour with travel() and step on.
- Stepping onto your own thrown dagger picks it up (autopickup of thrown weapons); a `,` afterwards on a lone corpse picks up the CORPSE (single object = no menu) — check "You see here" first.
- Known pit: `do(dir, force=True)` to enter on purpose (1d6 damage, 2-3 turns to climb out); the leprechaun's gold was autopicked up on landing.
- In a tended shop you can never swap with your pet ("You stop. Your kitten is in the way!"); outside, a swap fails 1 in 7.
- Sell-probe price ID (drop, decline, `,`) DESTROYS a scare monster scroll that was picked up before. Only probe scrolls whose group can't be scare monster, or accept the loss.
- Kicking a locked box says "THUD!" (lock breaks 1 in 5); `loot_all()` handles the pick-one menus.
- Gold is autopicked up when you step on it with a plain step (pickup_types:$); `,` afterwards just says "nothing here".
- After `do(...)`, read the returned snap's `.messages` immediately — calling `look()` first clears them.
- `m`-prefixed steps onto objects do NOT produce "You see here" messages; use plain steps to read shop prices.
- Pick-one menus (#loot "Do what?") close on the letter alone — do NOT add `<CR>`.
- `travel()`'s final plain step can be an illegal diagonal out of a doorway ("You can't move diagonally out of an intact doorway"): finish with orthogonal steps yourself near doors.
- `travel_to('<')` fails when the staircase is under an object and the harness never saw it bare (D3): travel by coordinates and confirm with `:` ("There is a staircase up here").
- Plain `travel()` refuses to start when the pet stands on the first square of the route ("Your housecat is in the way!"): take one plain step (swap) first.
- Never call `inventory()`/`here()` unless `obs.kind == 'command'` (they type keys).
