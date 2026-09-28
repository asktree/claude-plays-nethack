# p4 — current state (rewrite as things change)

## Character
- Name/role: P4, lawful female dwarven Valkyrie, god: Tyr. Seed 404 (local practice game).
- Turn / Dlvl / XL / HP / Pw / AC: T:10333 / DUNGEONS DL18 at (23,13) (corridor just N of a LEPRECHAUN HALL's doorway
  (23,14); ~30 sleepers) / XL10 / 109/109 / 17/17 / AC -15 / $0 loose ($2337 in bag k).
- (Shift 8 began from a `recover` restore to T:9820: the T:9820-9927 events of shift 7 on DL13 were undone.)
- Attributes: St 18/05, Dx 11, Co 19, In 7, Wi 9, Ch 8. Skills: long sword EXPERT, dagger Basic.
- Intrinsics: cold res (Valk), stealth, infravision, SPEED, TELEPATHY (floating eye), MAGIC RESISTANCE (worn GDSM X),
  POISON RESISTANCE, SLEEP RESISTANCE (Grey-elf corpse T:9654, "You feel wide awake."), DIVINE PROTECTION.
  Excalibur wielded: level-drain res + auto-search. Worn amulet of ESP (sees minded monsters within 8 — but mind
  flayer blasts LOCK ON through it). NO reflection, NO fire resistance.
- LUCKSTONE K (uncursed) carried: +3 Luck while carried, and Luck no longer times out (good or bad) — never do
  Luck-losing things now (no gem-throwing at cross-aligned unicorns: random Luck gets locked in).
- Enlightenment T:8565: PIOUSLY aligned, "You can safely pray".
- Hunger: NOT HUNGRY (Satiated wore off ~T:10240). Nutrition estimate: Hungry around ~T:10900. Food left: f C-ration,
  w tripe (dwarf: vomit risk), p 2 tins wolf meat, lizard corpses J x2 + S (keep for stoning). FOOD IS THIN: eat
  fresh safe corpses (corpse()) whenever not Satiated; buy/collect rations.

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
- k = uncursed BAG OF HOLDING: $2337; scrolls: 2 uncursed IDENTIFY, uncursed REMOVE CURSE (reserve), ANDOVA BEGARIN
  (uncursed, base 100), KO BATE (base 100), EIRIS SAZUN IDISI, LEP GEX VEN ZEA, blank, 3 earth;
  potions: uncursed SPEED, cursed SPEED, blessed OBJECT DETECTION, blessed ENLIGHTENMENT, uncursed HEALING, CURSED GAIN
  LEVEL (quaffed cursed = rise through the ceiling to the level above: an emergency exit; holy-water it for +1 XL),
  uncursed CONFUSION; rings: CURSED granite, jade, topaz (never wear), uncursed searching; blessed oil lamp, can of
  grease (grease the HELMET vs mind flayers), magic marker, gems (3 blue, 3 white, 2 yellow, 1 orange, glass);
  C = uncursed SACK holding a 2nd WAND OF DIGGING.
- d, s = WANDS OF CANCELLATION (0:3), (0:7) in the MAIN PACK — never into the bag of holding (it explodes).
- A = scroll of light (ASHPD SODALG) in the main pack.
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
- potions: EMERALD = ACID; DARK = blindness; EFFERVESCENT = extra healing; BUBBLY = object detection; ORANGE = SPEED;
  YELLOW = FULL HEALING (a centaur quaffed one T:10090: "looks completely healed"); BLACK = ENLIGHTENMENT; CLOUDY = HEALING;
  FIZZY = GAIN LEVEL; RUBY = CONFUSION (identified T:10112).
- wands: GLASS = CANCELLATION (engrave: "engraving vanishes", iridium is teleport) — d and s carried, charges unknown
  -> d (0:3), s (0:7) identified T:10112. NEVER put them in the bag of holding. Use: cancel Medusa's gaze, nymphs, etc.

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
| 13 | Dungeons | '<' (19,6), '>' (2,5); LEPRECHAUN HALL (2-7,14-19), door (5,13), ~30 SLEEPING leprechauns; wand (14,18) TAKEN (cancellation d); fountains (16,19), (4,7). |
| 14 | Dungeons | '<' (18,18); '>' found by explore (gold on it). |
| 15 | Dungeons | QUEST PORTAL LEVEL. '<' (17,14); MAGIC PORTAL (52,15); THRONE ROOM (74-76,11-15) door (73,14): court killed, '>' (74,13) under the looted chest, throne (75,12) (never sit); wood nymph asleep in the NW room (3-11,4-5); fountain (36,8); grave (66,4). |
| 16 | Dungeons | '<' (72,17). '>' found by explore (~28 turns). |
| 17 | Dungeons | ROGUE LEVEL. '<' (45,11) (arrow trap (44,9), pit (45,9)); peaceful gnome king. |
| 18 | Dungeons | '<' (5,15). LEPRECHAUN HALL (19-28,15-17) doorway (23,14), ~30 sleepers; cleared chickatrice room (2-10,5-8) door (8,9); peaceful dwarf lord. '>' NOT FOUND yet (east half unexplored). |
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
- NEXT: DL18: find the '>' (explore the east half; descend(1, explore=True) gave up after its 48-leg budget —
  call explore() directly). Optional: farm the DL18 leprechaun hall from its doorway (23,14) with $0 loose for XP +
  gold (forget_room() first; bag gold at once).
- Then DL19-20 toward MEDUSA (DL21-24). BEFORE Medusa: a BLINDFOLD/TOWEL (none carried!) or reflection; crossing
  water: wand of cold m (0:6) freezes a path, or levitation. A wand of CANCELLATION zapped at Medusa (asleep) makes
  her gaze harmless — still go blind to approach.
- XL: need XL14 (80000 exp) for the quest (portal DL15 (52,15)). Wraith corpses (+1 XL each) are the fastest help.
- Food: thin (C-ration, 2 tins, tripe): eat fresh safe corpses when not Satiated.
- Wants: REFLECTION (top), fire resistance, blindfold/towel, food rations, holy water (uncurse the gain level potion).
- Long-term: reflection, then the Castle wand of wishing (PLAYBOOK A1).
