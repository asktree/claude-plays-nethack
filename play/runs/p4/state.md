# p4 — current state (rewrite as things change)

## Character
- Name/role: P4, lawful female dwarven Valkyrie, god: Tyr. Seed 404 (local practice game).
- Turn / Dlvl / XL / HP / Pw / AC: T:9333 / DUNGEONS DL8 at (24,7) (corridor NW of the fountain room; '>' (10,15)) /
  XL10 / 107/109 / 17/17 / AC -15 / $0 loose ($2188 in bag k).
- Attributes: St 18/05, Dx 11, Co 19, In 7, Wi 9, Ch 8. Skills: long sword EXPERT, dagger Basic.
- Intrinsics: cold res (Valk), stealth, infravision, SPEED, TELEPATHY (floating eye), MAGIC RESISTANCE (worn GDSM X),
  POISON RESISTANCE, DIVINE PROTECTION ("warded"). Excalibur wielded: level-drain res + auto-search (2 vampire bites
  did nothing). Worn amulet of ESP (sees minded monsters within 8 — but mind flayer blasts LOCK ON through it).
  NO reflection, NO sleep resistance, NO fire resistance.
- LUCKSTONE K carried (Mines' End T:8679; type named "luckstone"): +3 Luck while carried, and Luck no longer times out
  (good or bad) — never do Luck-losing things now. Base Luck was 0 (enlightenment T:8565, no luck line).
- Enlightenment T:8565: PIOUSLY aligned, "You can safely pray".
- Hunger: ate a FOOD RATION at T:9333 (fed until ~T:10200). Food left: f C-ration, w tripe (dwarf: vomit risk),
  p 2 tins, J 2 lizard corpses (keep for stoning). FOOD IS SHORT: eat fresh safe corpses; prayer fixes Weak.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:3562 | Weak (hunger), DL7 (40,15) | SUCCESS. Timeout reset |
| T:4251 | (a WISH) | +50-149 timeout |
| T:6481 / T:8565 | wand of enlightenment: "You can safely pray" | prayer SAFE (no prayer since T:3562) |

## Equipment worn/wielded (AC -15)
- a: blessed rustproof +1 EXCALIBUR (wielded). X: +2 GRAY DRAGON SCALE MAIL (MR). l: blessed +2 leather cloak (MC1).
  R: uncursed +0 leather gloves. c: +3 small shield. j: +0 orcish helm. O: +0 iron shoes. o: amulet of ESP.
- A NYMPH CAN CHARM ARMOR OFF. After any nymph contact: check `inventory()` for "(being worn)".

## Key inventory (letters)
- k = BAG OF HOLDING: $2188, scrolls (uncursed ANDOVA BEGARIN, EIRIS SAZUN IDISI, KO BATE, LEP GEX VEN ZEA, STRC PRST
  SKRZ KRK, blank; 3 earth), potions (uncursed ORANGE, uncursed RUBY, blessed object detection), rings (CURSED granite,
  jade, topaz — never wear; uncursed searching), blessed oil lamp, can of grease (grease the HELMET vs mind flayers:
  u_slip_free), magic marker, gems.
- C = an UNIDENTIFIED BAG (found DL11 Mines): never put it in k (could be a bag of tricks/holding). Test it (#loot).
- K = LUCKSTONE. Gems: B black, D violet, E green (unidentified).
- Weapons: b +0 dagger, i 2 orcish daggers. (dagger y lost on Mines DL7 ~(55,9), killing a gas spore.)
- Wands: q SLEEP (4 used), m COLD (3+ used), F TELEPORTATION (4 used: 0-4 left!), U digging, P striking, r light,
  x "polymorph", T slow monster, t enlightenment (2 used).
- Tools: g KEY, G PICK-AXE (in main pack; bag it before entering shops), L unicorn horn, I camera.

## Identified appearances
- iridium wand = TELEPORTATION; hexagonal = SLEEP; curved = SLOW MONSTER; uranium = ENLIGHTENMENT; ZINC = COLD;
  crystal = digging; silver = make invisible; steel = striking; balsa = light; marble "polymorph" (named).
- spherical amulet = ESP; copper ring = searching. gray stone "luckstone" (named type) = K.
- scrolls: MAPIRO MAHAMA DIROMAT = identify; GARVEN DEH = earth; DUAM XNAHT = SCARE MONSTER; ETAOIN SHRDLU = create monster?
- potions: EMERALD = ACID; DARK = blindness; EFFERVESCENT = extra healing; BUBBLY = object detection.

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1-3 | Dungeons | see journal shift 1 (DL2 chaotic altar (5,4), general store) |
| 4 | Dungeons | up (54,5); '>' (45,15) -> DL5; '>' (72,7) -> MINES. |
| 5 | Dungeons | up (50,17), down (51,6), fountain (52,5). |
| 6 | Dungeons | up (22,14), down (37,9). |
| 7 | Dungeons | up (53,4), down (18,7). |
| 8 | Dungeons | up (48,13) in the fountain room; SLEEPING WOOD NYMPH (47,14) next to it (passed twice with Stealth); down (10,15); neutral altar (12,17). Hill orcs + manes around (24,7) T:9333. |
| 9 | Dungeons | THE ORACLE. up (7,4), down (59,9). |
| 10 | Dungeons | up (17,13) -> DL9; SOKOBAN up stairs (63,18). Nothing else explored. |
| Sok 1-4 | Sokoban | ALL SOLVED; prize taken. |
| Mines 1-3 (DL5-7) | Mines | DL7: '<' (13,6), '>' (69,9), trap door (54,6), hole (64,9). |
| 8 | MINETOWN (minetn-6) | '<' (15,13), '>' (60,18); temple of Tyr (co-aligned altar (55,17)); Bojolali's deli (42-44,16-17): out of rations (tripe left); Izchak's lighting ~(30,13); 2nd shopkeeper Kachzi Rellim ~(37,10). |
| 9 (Mines 5) | Mines | '<' (52,11), '>' (55,17); web (57,16). Peaceful Watch members wander here. |
| 10 (Mines 6) | Mines | '<' (51,10), '>' (25,13). A MIND FLAYER (awake; zaps a wand of STRIKING) and a wounded QUANTUM MECHANIC roam here; anti-magic field (31,13). The '<'->'>' route: dug passage (37,9)-(41,9). |
| 11 (Mines 7) | Mines | '<' (17,15), '>' (21,7); bear trap (41,13), sleeping gas trap (39,17). |
| 12 (Mines 8) | Mines | '<' (5,17), '>' (21,12). |
| 13 | MINES' END = CATACOMBS | DONE: luckstone taken. '<' (44,12); flint left at (4,19); level teleporter (3,17). |

## Threats / known dangers
- Nymphs (armor theft), SLEEP rays (no resistance, no reflection). At AC -15 a monster's ray still hits ~40%.
- MIND FLAYERS (Int 7!): never melee; zap F (teleport-away, no resistance roll) when adjacent/lined up; or dig down.
- Cold/fire rays destroy potions/scrolls in the open pack: keep them in the bag of holding (k).

## Objective and plan
- NEXT: continue down the main dungeon: DL8 '>' (10,15) -> DL9 (Oracle) '>' (59,9) -> DL10 (explored only around its
  '<'). Explore DL10+ for the quest portal level (DL11-16; "You receive a faint telepathic message" / magic portal),
  the big room, shops (food!), and REFLECTION (top want: silver dragon scales / shield of reflection / amulet).
- Food: buy/collect food rations whenever possible; eat fresh safe corpses (corpse()).
- Long-term: reflection, then the Castle wand of wishing (per PLAYBOOK A1). Quest needs XL14 + piously aligned (have).
