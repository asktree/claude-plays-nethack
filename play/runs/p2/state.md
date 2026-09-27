# p2 — current state (rewrite as things change)

## Character
- Name/role: p2 — local practice game, seed 202 (lawful female dwarven Valkyrie, god: Tyr)
- Turn / Dlvl / XL / HP / Pw / AC: T:1163 / Dlvl 3 (main dungeon) / XL3 / 40/40 / 4/4 / AC6
- Attributes (status line T:908): St:17 Dx:11 Co:19 In:11 Wi:8 Ch:9 (Cha 9 → shop prices ×4/3)
- Intrinsics (source, turn): cold res (Valk), stealth (Valk), infravision (dwarf), speed at XL7
- Luck notes: nothing done to Luck (no peacefuls killed, no mirrors)
- Alignment / god anger notes: never prayed; god not angry

## Prayer log
| turn | reason | result |
|---|---|---|
| — | none yet (first prayer fine from ~T300 in MAJOR trouble only) | — |

## Equipment worn/wielded (letter: item)
- a: uncursed +2 long sword (wielded) — enchanted from +1 at T:791
- c: uncursed +3 small shield (worn)

## Key inventory (letters) — mark evidence: [seen in inventory] vs [inferred] vs [UNVERIFIED]
- b: blessed +0 dagger (quivered, "at the ready") — throw it (`throw('b', dir)`), then pick it up [seen]
- h: orcish dagger, unknown B/U/C — THROW ONLY, never wield [seen]
- i: scroll of enchant weapon (identified), BUC unknown (goblin drop) — altar-test before reading, or read for +2→+3 [seen]
- j: scroll labeled ANDOVA BEGARIN = identify (base 20, sell offer 10) — save for a ring/wand/amulet [price-ID certain]
- p: scroll labeled HAPAX LEGOMENON — unknown (D3 floor); price-ID at a shop before reading [seen]
- o: wand of create monster (identified by engraving T:1046; charges unknown) — don't zap casually [seen]
- e: uncursed oil lamp [seen]
- Escape items: none (upstairs + Elbereth only)
- Healing: none
- Emergency cures: none carried (stoning: lizard/acidic corpse; sliming: fire/polymorph; illness: unicorn horn/prayer; curses: holy water/remove curse)
- Food: k food ration (found D1; >30-turn rotten roll applies), f tin (unknown), n lichen corpse (never rots). Last meal T:937 (ration) → next Hungry around T:1750. (Inventory corpses rot away after ~250 turns — only lizards/lichens keep.)
- Gold: $7

## Identified appearances (appearance -> identity)
- YUM YUM -> enchant weapon (formally identified)
- uranium wand -> create monster (formally identified)
- ANDOVA BEGARIN -> identify (base 20; sell offer 10) [certain]
- KO BATE -> light (D2 shop price 89 = 50×4/3×4/3) [certain given Cha mult 4/3]
- KERNOD WEL -> base 80: enchant armor OR remove curse (shop 107)
- ELBIB YLOH -> base 100 group (shop 133): confuse monster/destroy armor/fire/food det/gold det/magic mapping/scare monster/teleportation
- DAIYEN FOOELS -> base 100 group (shop 133)
- HAPAX LEGOMENON -> unknown
- cyan spellbook, gold spellbook -> 533 zm (level 4 book, or level 3 with surcharge)

## Dungeon map
| Dlvl | branch | features (stairs, altars+alignment, shops+type, fountains, stashes, traps, notes) |
|---|---|---|
| 1 | Dungeons | up stairs (8,8) NW room; down stairs (10,19) SW room; fountains (27,11) centre room and (5,18) SW room (Excalibur dips at XL5+); boulders (10,16),(37,16); fully explored |
| 2 | Dungeons | up stairs (40,6); down stairs (21,14) = GNOMISH MINES BRANCH (confirmed T:952); down stairs (74,17) = main dungeon; Kittamagh's second-hand bookstore (scrolls/spellbooks, ~6 scrolls + 2 books + a novel) at (2-5,17-19), door (6,18), far west; door (28,13) kicked open and its boulder pushed to the dead end (37,13) so east-west travel works; boulder (46,9) still in the N-S corridor below the NE room (`avoid((46,9))` is set; the NE room's gold at (56,5) is reachable via door (54,6)); fountain + 2 weapon items in the SE room (~(61,15), (63-67,15-16)) not yet checked; the game's travel likes the door/boulder corridors — use waypoints |
| 3 | Dungeons | arrived T:1028 via D2 (74,17); up stairs (21,18) in a small SW room (a broken, emptied large box sits on it); NW room (33-43,4-9) with a food pile at (35,8), east door (42,9); mostly unexplored; downstairs not found yet |
| 3 (Mines 1) | Gnomish Mines | entered T:952 from D2 (21,14), arrived at (77,13) on the far east; went straight back up; unexplored |

## Pets
- kitten (with me on D3, T:1163). It steals shop items (dropped one on a doorway = free) and moves my floor items around.

## Threats / known dangers
- None special yet. Watch for: floating eyes (never melee), gas spores, nymphs/leprechauns, hill orc packs in the Mines, soldier ants.
- Boxes: 10% trapped; drop scrolls/potions before kicking/opening; never `#force` with the long sword.

## Objective and plan
- Current objective: PLAYBOOK §C opening — explore D3 and D4, reach XL5, keep the kitten, then Excalibur (fountains on D1 (27,11)/(5,18) and D2 SE room) at XL5, then the Mines (Minetown altar for BUC tests, temple).
- Next steps: `explore()` D3 (food pile at (35,8) — check for a fresh corpse only if Hungry); find the D3 downstairs; fight one at a time; price-ID scroll p when back at the D2 bookstore (sell-offer trick).
- Mines branch: D2 (21,14). Minetown expected around Dlvl 5–7 (temple altar for BUC tests, shops).

## Harness/helper calibration notes
- `threat('goblin')` said "dangerous" (lvl 0, 1d4 weapon) while `threat('jackal')` says "trivial" — weapon-attack monsters seem over-rated; use `mon()` to sanity-check.
- Gold is autopicked up when you step on it (pickup_types:$); `,` afterwards just says "nothing here".
- After `do(...)`, read `obs.messages` immediately — calling `look()` first clears them.
- `m`-prefixed steps onto objects do NOT produce "You see here" messages; use plain steps to read shop prices.
- Shop yn prompts can wrap ("Sell i t?") — match on "offers" / "Sell" loosely.
- Pick-one menus (#loot "Do what?") close on the letter alone — do NOT add `<CR>` (it confirms an empty selection in the next menu).
- NetHack's `_` travel routes through closed doors/pushable boulders and stops there; `avoid()` doesn't change that — use waypoints or clear the obstacle.
- Never call `inventory()`/`here()` unless `obs.kind == 'command'` (they type keys).
