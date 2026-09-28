# p4 — current state (rewrite as things change)

## Character
- Name/role: P4, lawful female dwarven Valkyrie, god: Tyr. Seed 404 (local practice game).
- Turn / Dlvl / XL / HP / Pw / AC: T:8196 / MINETOWN (Gnomish Mines, Dlvl 8, minetn-6) standing ON the co-aligned
  altar of Tyr (55,17) in the temple (priest adjacent) / XL9 / 99/99 / 16/16 / AC -15 / $0 loose ($2207 in bag k).
- Attributes: St 18/02, Dx 10, Co 19, In 7, Wi 9. Skills: long sword EXPERT, dagger Basic.
- Intrinsics: cold res (Valk), stealth, infravision, SPEED (XL7), TELEPATHY (floating eye), MAGIC RESISTANCE (worn
  GDSM X), POISON RESISTANCE (scorpion T:6603), DIVINE PROTECTION 3 points (bought T:8187, 3600zm at XL9).
  Excalibur: level-drain res + auto-search. Worn amulet of ESP = telepathy within 8 while not blind.
  NO reflection, NO sleep resistance (sleep rays/wands are the big threat). MC1 from the leather cloak.
- Enlightenment T:6481: piously aligned; prayer timeout was 0 then. NO PRAYER since T:3562 (+wish T:4251) -> prayer safe.
- Hunger: ate a hill orc corpse T:7673 and a FOOD RATION T:7988 (Hungry at T:7983) -> fine until ~T:9000.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:3562 | Weak (hunger), DL7 (40,15) | SUCCESS. Timeout reset |
| T:4251 | (a WISH) | +50-149 timeout |
| T:6481 | wand of enlightenment: "You can safely pray" (no trouble -> timeout 0) | prayer SAFE |
| (none since) | | prayer available for MAJOR trouble |

## Equipment worn/wielded (AC -15)
- a: blessed rustproof +1 EXCALIBUR (wielded). X: +2 GRAY DRAGON SCALE MAIL (MR; MC0). l: BLESSED +2 LEATHER CLOAK
  (altar-tested T:8182; MC1; a nymph must take the cloak before the GDSM). R: uncursed +0 leather gloves (gloved:
  cockatrice corpses can be carried). c: +3 small shield. j: +0 orcish helm. O: +0 iron shoes. o: amulet of ESP.
- A NYMPH CAN CHARM ARMOR OFF (T:5057). After any nymph contact: check `inventory()` for "(being worn)".

## Key inventory (letters)
- k = BAG OF HOLDING (Sokoban prize, T:7603; shows as "a bag"): $2207, scrolls (uncursed ANDOVA BEGARIN, EIRIS SAZUN
  IDISI, KO BATE, LEP GEX VEN ZEA, STRC PRST SKRZ KRK, blank; 3 earth), potions (uncursed ORANGE, uncursed RUBY,
  blessed object detection), rings (CURSED granite, CURSED jade, CURSED topaz — never wear; uncursed searching),
  blessed oil lamp, can of grease, magic marker, gems (black, 2 blue, orange, 2 white, yellow). bag_take('k', ...).
- Weapons: b +0 dagger, y dagger (quivered), i 2 orcish daggers (throwables).
- Wands: q SLEEP (4 zaps used), m COLD (zinc; from the sergeant, 3+ used — may be low), F TELEPORTATION (zap monsters
  away; Sokoban/no-tele levels still allow it), U digging, P striking, r light, x "polymorph", T slow monster,
  t enlightenment.
- Tools: g KEY, G pick-axe, L unicorn horn, I camera.
- Food: n 1 food ration, f 2 C-rations, w tripe (dwarf: 50% vomit), p 2 tins, J 2 uncursed LIZARD corpses.
- 30 letters used.

## Identified appearances
- iridium wand = TELEPORTATION (named); hexagonal = SLEEP; curved = SLOW MONSTER; uranium = ENLIGHTENMENT; ZINC = COLD;
  crystal = digging; silver = make invisible; steel = striking; balsa = light; marble "polymorph" (named).
- spherical amulet = ESP; copper ring = searching.
- scrolls: MAPIRO MAHAMA DIROMAT = identify; GARVEN DEH = earth; DUAM XNAHT = SCARE MONSTER (seen T:7603 on the Sok4
  prize square: never pick one up twice); ETAOIN SHRDLU = create monster?
- potions: EMERALD = ACID (named "acid"; a hill orc threw one: "This burns!"); DARK = blindness; EFFERVESCENT = extra
  healing; BUBBLY = object detection. (sky blue: my blessed one shattered; unknown.)
- bag of tricks is identified ("bag of tricks"); any plain "bag" is a sack/oilskin/holding.

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1-3 | Dungeons | see journal shift 1 (DL2 chaotic altar (5,4), Sipaliwini's general store) |
| 4 | Dungeons | up (54,5); '>' (45,15) -> DL5; '>' (72,7) -> MINES. |
| 5 | Dungeons | up (50,17), down (51,6), fountain (52,5). |
| 6 | Dungeons | up (22,14), down (37,9). |
| 7 | Dungeons | up (53,4), down (18,7). |
| 8 | Dungeons | up (48,13) in the fountain room: a SLEEPING WOOD NYMPH at (47,14) next to it (passed with Stealth T:7950 — she stays asleep; kill only with a ranged/sleep plan), down (10,15), NEUTRAL ALTAR (12,17). |
| 9 | Dungeons | THE ORACLE. up (7,4), down (59,9). |
| 10 | Dungeons | up (17,13) -> DL9; SOKOBAN up stairs (63,18). Nothing else explored. |
| Sok 1-4 | Sokoban | ALL SOLVED; prize taken. Sok4 zoo cleared except a sleeping OCHRE JELLY (45,19); cursed scare monster scroll + burned Elbereth at (42,15). Sok2 stash (44,9): elven mithril-coat, 2 blessed spellbooks, wand of light; floating eye (45,14). |
| Mines 1-3 (DL5-7) | Mines | Mines 3 (DL7): '>' (69,9) behind a HOLE at (64,9) — bypass dug at (65,10)/(64,10)/(63,10). |
| 8 | MINETOWN (minetn-6) | '<' (15,13) in a 1-wide nook; TEMPLE of Tyr, CO-ALIGNED altar (55,17), priest; Izchak's lighting shop ~(30,13); a LARGE MIMIC posing as a potion at (43,17) (in a shop); shop items at (43-45,5-7) (wands, potions, scroll); a ring on the floor (48,13); fountains (29,17), (42,11). Down stairs not yet noted. 2 werewolves killed (T:7983 DL7, T:8146 here) — no lycanthropy. |

## Threats / known dangers
- Nymphs (armor theft), SLEEP rays/wands (no resistance, no reflection): soldiers/sergeants rarely carry them.
- Cold/fire rays destroy potions/scrolls in the open pack: keep them in the bag of holding (k).
- Werewolves: MC1 now (cloak) cuts lycanthropy chance; prayer cures it.

## Objective and plan
- NEXT (options, in order): (1) optional in Minetown: sell the 3 cursed rings for price-ID gold; look for food; keep
  the temple as a safe spot. (2) MINES' END (2-5 levels below Minetown) for the LUCKSTONE — AC -15 makes it safe.
  (3) back up to DL4, down the main dungeon to DL10 (known stairs), explore DL10+ (quest portal DL11-16, big room).
- Long-term: REFLECTION (silver dragon scales / shield of reflection / amulet), then the Castle wand of wishing.
