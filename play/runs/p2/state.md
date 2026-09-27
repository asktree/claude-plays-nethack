# p2 — current state (rewrite as things change)

## Character
- Name/role: p2 — local practice game, seed 202 (lawful female dwarven Valkyrie, god: Tyr)
- Turn / Dlvl / XL / HP / Pw / AC: T:1931 / Dlvl 4 (main dungeon) / XL3 (Exp 69; XL4 at 80, XL5 at 160) / 40/40 / 4/4 / AC2
- Position at shift end: corridor (27,14) on D4, kitten adjacent, nothing hostile in view, command prompt.
- Attributes (status line T:1662): St:17 Dx:11 Co:19 In:11 Wi:8 Ch:9 (Cha 9 → shop prices ×4/3)
- Intrinsics (source, turn): cold res (Valk), stealth (Valk), infravision (dwarf), speed at XL7
- Luck notes: nothing done to Luck (no peacefuls killed, no mirrors)
- Alignment / god anger notes: never prayed; god not angry. prayer_check() at T:1240: p_safe 1.0.

## Prayer log
| turn | reason | result |
|---|---|---|
| — | none yet (first prayer fine in MAJOR trouble only; lycanthropy counts as major) | — |

## Equipment worn/wielded (letter: item)
- a: uncursed +2 long sword (wielded) — enchanted from +1 at T:791
- c: uncursed +3 small shield (worn)
- y: +0 scale mail (worn since T:1681; bought D4 shop; the kitten stood on it without "reluctantly" → not cursed) [seen]

## Key inventory (letters) — mark evidence: [seen in inventory] vs [inferred] vs [UNVERIFIED]
- b: blessed +0 dagger — throw it (`throw('b', dir)`), then pick it up with a PLAIN step (travel arrival never autopicks up) [seen]
- h: orcish dagger, unknown B/U/C, "at the ready" (quivered) — THROW ONLY, never wield [seen]
- x: curved wand = wand of COLD, FIRE, LIGHTNING or SLEEP (shop price 233 = base 175) [price-ID certain]; charges 4–8 (fresh shop stock) [inferred]; NOT engrave-tested (lightning would blind me) — identify it at its first zap: all four are bouncing RAYS, never zap toward the kitten or at a wall next to me
- o: wand of create monster (identified by engraving T:1046; charges unknown) — don't zap casually [seen]
- B: scroll of identify (from the D4 chest; BUC unknown) — use on the cyan potion F or the boots E / spellbook C [seen]
- i: scroll of enchant weapon (identified), BUC unknown (goblin drop) — read for +2→+3 (or on Excalibur later) [seen]
- D: unlabeled scroll = blank paper (chest) [seen]
- C: dull spellbook, unknown (chest) — do NOT read (Wis 8 / 4 Pw: a Valkyrie can't cast anyway); sell or price-ID [seen]
- E: pair of high boots (AC 2), BUC UNKNOWN (D4 floor) — do NOT wear until BUC-tested (altar, or kitten test: drop where it walks) [seen]
- F: cyan potion, unknown (D4 corridor) [seen]
- z: candle (for the Candelabrum eventually) [seen]
- e: uncursed oil lamp [seen]
- Escape items: none (upstairs + Elbereth; the wand x may be sleep)
- Healing: none known (potion F unknown)
- Emergency cures: none carried (stoning: lizard/acidic corpse; sliming: fire/polymorph; illness: unicorn horn/prayer; curses: holy water/remove curse)
- Food: A 1 lembas wafer (800, never rots), k food ration (found D1; >30-turn rotten roll applies — eat on a safe square), f tin (unknown). Last meal T:1931 (lembas) → next Hungry around T:2700.
- Gold: $6 (spent 293 at the D4 shop)
- Sold/lost this shift: vellum spellbook (level 1), cursed ring of regeneration, murky potion (base 100), scroll HAPAX LEGOMENON (base 100), tin whistle, 2 eggs; scroll ELAM EBOW = SCARE MONSTER turned to dust (re-pickup).

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
| 2 | Dungeons | up stairs (40,6); down stairs (21,14) = GNOMISH MINES BRANCH (confirmed T:952); down stairs (74,17) = main dungeon; Kittamagh's second-hand bookstore (scrolls/spellbooks) at (2-5,17-19), door (6,18), far west; door (28,13) kicked open and its boulder pushed to the dead end (37,13) so east-west travel works; boulder (46,9) in the N-S corridor below the NE room (`avoid((46,9))`); fountain + 2 weapon items in the SE room (~(61,15), (63-67,15-16)) not yet checked |
| 3 | Dungeons | up stairs (21,18) SW room; down stairs (51,10) in a small room (49-51,6-10); SLEEPING GAS TRAP at (35,8) in the NW room (known, avoided); a vault exists (guard footsteps); locked door (68,12) only leads to explored corridor; elven bow left at (61,19); explored except the far east strip |
| 3 (Mines 1) | Gnomish Mines | entered T:952 from D2 (21,14), arrived at (77,13) on the far east; went straight back up; unexplored |
| 4 | Dungeons | up stairs (39,18) in a small SW-centre room (33-39,18-19); DOWNSTAIRS NOT FOUND YET — unexplored: far west room (interior ~(9-14,8-12), potion at (14,9), doors (15,6)/(15,10) closed), whatever is south of the fountain room, and the dead-end corridor north of door (41,4) (search there). FOUNTAIN at (22,17) in a small room (22-24,16-18), door (25,16) — Excalibur candidate. UPERNAVIK'S GENERAL STORE (69-71,15-17), door (68,16) — stock left: puce potion (200), murky potion (133), cursed ring of regeneration (267), cursed agate ring (178), vellum spellbook (133), leather armor (7), HAPAX LEGOMENON (133), whistle, eggs. Rooms: NW-centre (39-47,5-9) with the emptied broken chest (43,5), north door (41,4); west room (22-29,8-10); NE (56-66,6-9); middle (49-58,17-19) with an unchecked tool at (50,19). Yellow molds keep spawning here (4 killed). |

## Pets
- kitten (with me on D4, T:1931). It kills things I fight (stole 2 werejackals, a newt, 2 jackals), carries shop items around (an item it drops outside the shop is free), stole gold on D3. In a shop you can't swap places with it.

## Threats / known dangers
- Werejackals: two met (D3 T:1255, D4 T:1577), both killed. Bite in `d` form = lycanthropy 1/4 per hit → cure by prayer (major trouble). Kill fast; throw daggers while they approach.
- Yellow molds (passive stun) — kill with thrown daggers, finish with one blow.
- Watch for: floating eyes (never melee), gas spores, nymphs/leprechauns, soldier ants, hill orc packs in the Mines.
- Undiscovered traps under item piles (the D3 sleeping gas trap was under a "food pile").
- Boxes: 10% trapped; drop scrolls/potions before kicking/opening; never `#force` with the long sword.

## Objective and plan
- Current objective: find the D4 `>` (west/south-west unexplored; search the north dead end if needed), then D5 for XP — reach XL5 (need 91 more Exp; small fry give ~1 now) fighting one monster at a time. Then Excalibur: the nearest fountain is D4 (22,17) (also D1 (27,11)/(5,18), D2 SE room) — dip('a') at full HP with the upstairs route known. Then the Gnomish Mines via D2 (21,14) (Minetown altar for BUC tests of E/B/i/C, temple).
- The curved wand x is the emergency weapon: zap it (`zap('x', dir)`) at the first dangerous monster in a straight line (not toward the kitten) — this also identifies it.
- BUC-test the high boots E (kitten/altar) before wearing: AC 2 → 0.
- Read identify B when something worth it comes (or on potion F now if idle).
- Eat when Hungry: lembas A first, then ration k on a safe square; fresh safe corpses when available.

## Harness/helper calibration notes
- `travel()` arrival never autopicks up (NetHack sets nopick during travel, cmd.c:4821): press `,` or take the last step with a plain move.
- In a tended shop you can never swap with your pet ("You stop. Your kitten is in the way!"); outside, a swap fails 1 in 7.
- Sell-probe price ID (drop, decline, `,`) DESTROYS a scare monster scroll that was picked up before. Only probe scrolls whose group can't be scare monster, or accept the loss.
- Shop "Sell it? [ynaq]" prompt may come back as kind `unknown`: match on the prompt text.
- Kicking a locked box says "THUD!" (lock breaks 1 in 5); `#loot` → `o` shows a type menu first ("All types" = a).
- explore() may report a lit room as "unreachable" when the dark corridor leading to it is simply unwalked: walk it by hand from the nearest known square.
- Gold is autopicked up when you step on it with a plain step (pickup_types:$); `,` afterwards just says "nothing here".
- After `do(...)`, read `obs.messages` immediately — calling `look()` first clears them.
- `m`-prefixed steps onto objects do NOT produce "You see here" messages; use plain steps to read shop prices.
- Pick-one menus (#loot "Do what?") close on the letter alone — do NOT add `<CR>`.
- Never call `inventory()`/`here()` unless `obs.kind == 'command'` (they type keys).
- `,` on a square with a single object picks it up without a menu — check "You see here" first.
