# p4 — current state (rewrite as things change)

## Character
- Name/role: P4, lawful female dwarven Valkyrie, god: Tyr. Seed 404 (local practice game).
- Turn / Dlvl / XL / HP / Pw / AC: T:9927 / DUNGEONS DL13 at (5,12) (corridor just N of the LEPRECHAUN HALL's door
  (5,13); DL13 '>' (2,5)) / XL10 / 109/109 / 17/17 / AC -15 / $0 loose ($1599 in bag k).
- Attributes: St 18/05, Dx 11, Co 19, In 7, Wi 9, Ch 8. Skills: long sword EXPERT, dagger Basic.
- Intrinsics: cold res (Valk), stealth, infravision, SPEED, TELEPATHY (floating eye), MAGIC RESISTANCE (worn GDSM X),
  POISON RESISTANCE, SLEEP RESISTANCE (Grey-elf corpse T:9654, "You feel wide awake."), DIVINE PROTECTION.
  Excalibur wielded: level-drain res + auto-search. Worn amulet of ESP (sees minded monsters within 8 — but mind
  flayer blasts LOCK ON through it). NO reflection, NO fire resistance.
- LUCKSTONE K (uncursed) carried: +3 Luck while carried, and Luck no longer times out (good or bad) — never do
  Luck-losing things now (no gem-throwing at cross-aligned unicorns: random Luck gets locked in).
- Enlightenment T:8565: PIOUSLY aligned, "You can safely pray".
- Hunger: SATIATED. Ate stalker (T:9370) + 2 Grey-elves (T:9467, T:9654). Nutrition at T:9654 between ~1430 and
  ~1740 -> Hungry not before ~T:10900. Food left: f C-ration, w tripe (dwarf: vomit risk), p 2 tins wolf meat,
  lizard corpses J x2 + S (keep for stoning). Eat fresh safe corpses when not Satiated.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:3562 | Weak (hunger), DL7 (40,15) | SUCCESS. Timeout reset |
| T:4251 | (a WISH) | +50-149 timeout |
| T:6481 / T:8565 | wand of enlightenment: "You can safely pray" | prayer SAFE (no prayer since T:3562) |

## Equipment worn/wielded (AC -15)
- a: blessed rustproof +5 EXCALIBUR (wielded) — DO NOT enchant further (evaporation above +5).
- X: blessed +2 GRAY DRAGON SCALE MAIL (MR). l: blessed +2 leather cloak (MC1). R: uncursed +0 leather gloves.
  c: +3 small shield. j: uncursed +0 orcish helm. O: uncursed +0 iron shoes. o: amulet of ESP.
- A NYMPH CAN CHARM ARMOR OFF. After any nymph contact: check `inventory()` for "(being worn)".

## Key inventory (letters) — the whole main pack was IDENTIFIED T:9571 (blessed identify rolled "all")
- k = uncursed BAG OF HOLDING: $1599; scrolls: 4 uncursed IDENTIFY (save 2 for amulets/rings), uncursed REMOVE CURSE
  (reserve), ANDOVA BEGARIN (uncursed, base 100), KO BATE (base 100), EIRIS SAZUN IDISI, LEP GEX VEN ZEA, blank, 3 earth;
  potions: uncursed orange = SPEED, cursed potion of SPEED, uncursed RUBY, blessed object detection, BLACK (unknown);
  rings: CURSED granite, jade, topaz (never wear), uncursed searching; blessed oil lamp, can of grease (grease the
  HELMET vs mind flayers), magic marker, gems; C = uncursed SACK holding a 2nd WAND OF DIGGING.
- Wands (charges known): U DIGGING (0:5), m COLD (0:6), x POLYMORPH (0:5), P STRIKING (0:3), T SLOW MONSTER (0:4),
  q SLEEP (0:1), r light (0:13), t enlightenment (0:13), F TELEPORTATION (0:0) = EMPTY (wrest 1/121 only).
- K = LUCKSTONE. D = 2 AMETHYSTS. B, E = worthless glass.
- Weapons: b +0 dagger, i 2 +0 orcish daggers, Q cursed -1 elven dagger (throwing only).
- Tools: g skeleton KEY, G PICK-AXE (main pack now; bag it before entering shops), L +0 unicorn horn, I camera (0:65).

## Identified appearances
- wands: iridium = TELEPORTATION; hexagonal = SLEEP; curved = SLOW MONSTER; uranium = ENLIGHTENMENT; zinc = COLD;
  crystal = DIGGING; silver = make invisible; steel = STRIKING; balsa = LIGHT; marble = POLYMORPH.
- spherical amulet = ESP; copper ring = searching. gray stone = luckstone (K).
- scrolls: MAPIRO MAHAMA DIROMAT = identify; GARVEN DEH = earth; DUAM XNAHT = SCARE MONSTER; STRC PRST SKRZ KRK =
  ENCHANT WEAPON; PRATYAVAYAH = REMOVE CURSE; NR 9 = PUNISHMENT; ASHPD SODALG = light (price); TEMOV = base 200
  (amnesia/create monster/taming); YUM YUM, KO BATE, ANDOVA BEGARIN = base 100; ETAOIN SHRDLU base 200 ("create monster?").
- potions: EMERALD = ACID; DARK = blindness; EFFERVESCENT = extra healing; BUBBLY = object detection; ORANGE = SPEED.

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1-3 | Dungeons | see journal shift 1 (DL2 chaotic altar (5,4), general store) |
| 4 | Dungeons | up (54,5); '>' (45,15) -> DL5; '>' (72,7) -> MINES. |
| 5-7 | Dungeons | DL5 up (50,17) down (51,6); DL6 up (22,14) down (37,9); DL7 up (53,4) down (18,7). |
| 8 | Dungeons | up (48,13) (SLEEPING WOOD NYMPH (47,14) beside it); down (10,15); neutral altar (12,17). |
| 9 | Dungeons | THE ORACLE. up (7,4), down (59,9). |
| 10 | Dungeons | up (17,13); SOKOBAN up (63,18). KILTAMAGH'S SECOND-HAND BOOKSTORE (scrolls) (2-6,8-13), door (7,10), reached through the '<' room's west door (14,14). '>' NOT FOUND (hidden: dead ends (57,2) (59,9) (64,7)); I dug a hole at (40,17). |
| 11 | Dungeons | partly explored; 2 hostile GRAY UNICORNS, a horse, a leprechaun. Stairs unknown (zapped a hole at (56,10)). |
| 12 | Dungeons | '>' (8,7) in the NW room (4-13,5-9). '<' unknown. |
| 13 | Dungeons | '<' (19,6), '>' (2,5); LEPRECHAUN HALL (2-7,14-19), door (5,13), ~30 SLEEPING leprechauns; a WAND on the floor (14,18) in the SE room (fountain (16,19)); fountain (4,7). |
| Sok 1-4 | Sokoban | ALL SOLVED; prize taken. |
| Mines 1-3 (DL5-7) | Mines | DL7: '<' (13,6), '>' (69,9). |
| 8 | MINETOWN (minetn-6) | '<' (15,13), '>' (60,18); temple of Tyr (co-aligned altar (55,17)); deli out of rations; Izchak ~(30,13). |
| 9-12 | Mines | DL9 '<' (52,11) '>' (55,17); DL10 '<' (51,10) '>' (25,13) MIND FLAYER + quantum mechanic roam; DL11 '<' (17,15) '>' (21,7); DL12 '<' (5,17) '>' (21,12). |
| 13 | MINES' END (Catacombs) | DONE (luckstone). '<' (44,12). |
- QUEST PORTAL = DL15 MAGIC PORTAL at (52,15) (found by explore/auto-search T:~9980), in the small room (50-52,14-17):
  doors (49,15) W, (52,13) N [-> 'Vlad was here' closet (52,12) = one-time TRAP DOOR], doorway (53,16) E. DL15 '<' (17,14).
  Norn's message on arrival T:9886. BIG ROOM: none (DL10-12 ordinary).

## Threats / known dangers
- Nymphs (armor theft). Leprechauns steal only LOOSE gold: keep $0 loose (bag_put('k','$') after any pickup).
- MIND FLAYERS (Int 7!): never melee; F is EMPTY now -> dig down (U / pick-axe) or leave the level.
- Fire: no resistance (flaming sphere blast -14). Keep scrolls/potions in the bag.
- At AC -15 a monster's RAY still hits ~40%: soldiers/wand users remain dangerous without reflection (sleep is now resisted).

## Objective and plan
- NEXT: DL13 leprechaun hall: farm it from the doorway (5,13) with $0 loose (Stealth keeps sleepers asleep; with no
  gold to steal a leprechaun only scratches 1d2). Each carries gold -> temple protection (+1 AC per 4000 at XL10).
  Pick up their gold INTO THE BAG right away. forget_room() is needed for the harness to let you in.
- Fetch the wand at (14,18) (SE room). Then DL13 '>' (2,5) -> DL14 -> DL15/16: the quest portal message.
- Wants: REFLECTION (top), fire resistance, food rations. Quest needs XL14 + piously aligned (have the piety).
- Long-term: reflection, then the Castle wand of wishing (PLAYBOOK A1).
