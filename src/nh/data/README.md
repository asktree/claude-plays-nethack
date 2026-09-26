# NetHack 3.6.7 game data (`nh.data`)

Machine-readable tables for an agent that sees NetHack only as an 80x24 tty
screen (default ASCII symbols, colour on). The JSON files are generated from
the 3.6.7 C sources with no hand-typed data. The rules in `corpses.py` and
the prose `display_rules` are hand-ported, with the C function each one comes
from cited.

```
python scripts/gen_nh_data.py ~/src/nh367-data/NetHack-3.6.7 [--cc-check]
```

The generator (`scripts/gen_nh_data.py`) runs `src/monst.c`, `src/objects.c`
and `src/drawing.c` through a small C preprocessor written in Python (macros,
`#if`/`#ifdef`, objects.c's recursive two-pass `#include`) and evaluates the
brace initialisers as C constant expressions. `--cc-check` also compiles
monst.c and objects.c with the system C compiler and checks every struct field
against the parser; all 382 monsters and 454 objects match. Output is
deterministic: `tests/test_nh_data.py` regenerates it and compares bytes when
the source tree is available.

**Build assumptions.** This is a stock Unix tty build: `TEXTCOLOR` and `MAIL`
are defined and `CHARON` is not. `MAIL` adds the *mail daemon* monster (index
311) and the *scroll of mail* (index 339), so every later index moves up by
one. For a build without MAIL, such as NLE (which the older `game/` harness
uses), run the generator with `--no-mail`. `_meta.mail` records which build
the files describe.

Colours throughout are NetHack `CLR_*` numbers: 0 black, 1 red, 2 green,
3 brown, 4 blue, 5 magenta, 6 cyan, 7 gray, 8 no_color, 9 orange,
10 bright_green, 11 yellow, 12 bright_blue, 13 bright_magenta, 14 bright_cyan,
15 white. Each record also carries the lower-case name of its colour.

## Reading colours off a tty

These rules come from `win/tty/termcap.c`, `init_hilite()`, for a Unix
terminfo build. They are also stored in `features.json` under
`tty_color_rendering`.

| NetHack colour | escape sent | decode as |
|---|---|---|
| 1-6 | `setaf(c)` (SGR 31-36) | c |
| 9-14 | bold + `setaf(c-8)` (SGR 1;31 .. 1;36) | base + 8 |
| 15 white | bold + `setaf(7)` (1;37) | 15 |
| 7 gray, 8 no_color | **no colour escape** (terminal default foreground) | 7 (8 looks identical) |
| 0 black | bold + `setaf(0)` (dark gray) if `use_darkgray` (default); otherwise it is drawn the same as blue (4) | 0 |

So gray and no_color cannot be told apart on screen. When a lookup for
`X|7` fails, also try `X|8` (for example `I|8`, the remembered-unseen-monster
marker).

## monsters.json

`{"_meta": {...,"count": 382}, "monsters": [ ... ]}`, with one record per
line, in `mons[]` order (the index is the PM number).

| field | meaning |
|---|---|
| `index`, `name`, `pm` | position in `mons[]`, name, and `PM_*` constant as makedefs names it. Were-creature `@` forms are `PM_HUMAN_WERE*`; the three were names each appear twice. |
| `symbol`, `class`, `class_value` | default tty letter (`def_monsyms`), `S_*` class, and class number. Ghosts and shades use `' '`. |
| `color`, `color_value` | display colour |
| `level`, `speed`, `ac`, `mr` | base level, movement rate, AC, and magic resistance (0-127) |
| `alignment`, `alignment_name` | raw `maligntyp` (-128 = `A_NONE`, "unaligned") |
| `geno` | `{"value", "flags": ["G_UNIQ","G_NOHELL","G_HELL","G_NOGEN","G_SGROUP","G_LGROUP","G_GENO","G_NOCORPSE"] subset, "frequency": 0-7}` |
| `attacks` | non-empty slots only: `{"slot", "type": "AT_*", "damage_type": "AD_*", "dice": "NdM", "n", "d"}`. For `AT_BREA` the sides are ignored by the game; `AT_BOOM` with 0 dice rolls (level+1)dM. |
| `weight`, `nutrition` | corpse weight (`cwt`) and nutrition (`cnutrit`) |
| `sound`, `size`, `size_value` | `MS_*` (aliases resolved: `MS_ORC` is reported as `MS_GRUNT`, `MS_ANIMAL` as `MS_BURBLE`), `MZ_*` (`MZ_HUMAN` = `MZ_MEDIUM`) |
| `resistances`, `conveys` | `MR_*` names. `conveys` is the raw field. Eating can only grant fire, cold, sleep, disintegration, shock and poison resistance from it (`MR_ACID`/`MR_STONE` never). Use `corpses.py` for what a corpse actually gives. |
| `flags1`, `flags2`, `flags3` | decoded `M1_*`/`M2_*`/`M3_*`. Single bits are listed first, then composites whose bits are all set: `M1_NOLIMBS` (includes `M1_NOHANDS`), `M1_OMNIVORE` (= CARNIVORE and HERBIVORE), `M3_WANTSALL`/`M3_COVETOUS`. |
| `flags_raw` | `[mflags1, mflags2, mflags3]` as integers |
| `difficulty` | the literal `difficulty` field of `MON()`, which 3.6.7 uses for generation |
| `difficulty_mstrength` | recomputed with a port of makedefs `mstrength()`. Agrees with `difficulty` for all 382 monsters. |

## objects.json

`{"_meta", "shuffle_groups", "gem_color_variants", "wand_of_nothing_direction", "objects": [...]}`.
`objects` has 454 records in `objects[]` order (the index is the otyp).

| field | meaning |
|---|---|
| `index`, `name`, `otyp` | `oc_name` (null for the 23 unused extra scroll/wand descriptions) and the `onames.h` constant (`WAN_STRIKING`, `RIN_PROTECTION_FROM_SHAPE_CHAN` truncated as makedefs does; null for glass gems) |
| `full_name` | identified singular name as `xname()` prints it: "wand of striking", "pair of speed boots", "set of red dragon scales", "jacinth stone" |
| `appearance`, `unidentified_name` | `oc_descr` and the pre-identification name ("runed arrow", "ebony wand", "scroll labeled ZELGO MER", "red gem"). For shuffled classes this is only the default appearance; see `shuffle_group`. Items with `name_known` always show their real name. |
| `class`, `class_symbol` | `*_CLASS` and its default tty symbol |
| `color`, `color_value` | default colour. In shuffled groups the colour belongs to the *appearance*. |
| `cost`, `weight` | base price and weight |
| `prob`, `effective_prob` | `oc_prob` per mille within its class. Rings are all 0 in objects.c, and `init_objects()` sets each to about 35 (`effective_prob`). Gem probabilities are also rescaled per dungeon depth (`setgemprobs`). |
| `material` | `obj_material_types` name (null = 0, e.g. worm tooth) |
| `magic`, `merge`, `charged`, `unique`, `nowish`, `name_known`, `uses_known` | `oc_*` bits. `charged` means "may have +n or (n)". |
| `property` | `oc_oprop` as a `prop.h` name (for example `TELEPAT`, `FIRE_RES`), or null |
| `shuffle_group` | key into `shuffle_groups`, or null |
| `weapon` | weapons, weapon-tools, gems and rocks: `small_damage`/`large_damage` ("d8"), `sdam`, `ldam`, `to_hit`, `skill` (`P_*`; a leading `-` means ammo or missile for that skill), `skill_value`, `kind` (melee/launcher/ammo/missile), `damage_types` (pierce/slash/whack), `bimanual` |
| `armor` | `ac` (the AC bonus), `mc`, `category` (`ARM_*`), `delay`, `bulky` |
| `food` | `nutrition`, `delay` |
| `wand` | `direction` (NODIR/IMMEDIATE/RAY; null for unused descriptions) |
| `spellbook` | `level`, `direction`, `school` (`P_*_SPELL`), `delay` |
| `ring` | `chargeable`, `hard` |
| `gem` | `hard`, `glass`, `value` |
| `raw` | every `struct objclass` field (`oc_*`) exactly as compiled |

`shuffle_groups` follows `o_init.c shuffle_all()`. It covers whole classes
(amulet, potion, ring, scroll, spellbook, wand, venom) minus fixed members,
plus the helmet, gloves, cloak and boots ranges. Each group records
`{class, first, last, materials_shuffled, names (full names), appearances: [{appearance, color, color_value, material, unidentified_name}]}`.
Description, colour and hardness move together, and material moves too
except for armour. The scroll group has 41 labels for 21 scrolls and the wand
group 27 for 24, so some labels go unused in any given game.
`gem_color_variants` lists the per-game recolouring of turquoise, aquamarine
and fluorite.

## glyph_index.json

All keys are `"<char>|<color>"` (e.g. `"d|3"`).

| section | value |
|---|---|
| `monsters` | monster names drawn with that letter and colour |
| `monsters_by_char` | all monsters per letter, for when colour is unreliable |
| `objects` | list of `{"name", "unidentified_name"?}` for fixed-appearance items, `{"appearance", "unidentified_name", "shuffle_group"}` for shuffled ones (the identity is any member of `shuffle_groups[g].names`), and gem recolour `variant`s. Boulders use `` ` ``. Corpses and statues are left out here (see below). |
| `corpses` | monsters whose corpse appears as `%` in *that monster's* colour (`mapglyph.c` draws corpses with `mon_color`). G_NOCORPSE monsters are omitted. |
| `statues` | statues are drawn as the monster's **letter** in white (15). Any white letter may be a statue. |
| `features` | `S_*` map symbols (the same as `features.json` `by_glyph`) |
| `special` | the `I` marker, the `]` strange object (usually a mimic), and warning digits `0`-`5` |
| `shuffle_groups` | group names and appearances (summary) |

## features.json

| field | meaning |
|---|---|
| `cmap` | all 96 `defsyms[]`: `index`, `id` (`S_*`), `char`, `color`, `color_value`, `explanation`, `category` (stone/wall/door/obstacle/floor/corridor/stairs/furniture/terrain/trap/effect/swallow/explosion), and `trap_type` for traps |
| `traps` | `trap.h` type number, name, `cmap` id, char, and colour (a web is `"`, the vibrating square `~`) |
| `by_glyph` | `"<char>\|<color>"` to map features, e.g. `"#\|7"` covers corridor, lit corridor, sink and cloud |
| `warnings` | warning digits and colours |
| `other_symbols` | boulder `` ` `` and invisible `I` |
| `object_classes`, `monster_classes` | default class symbols and `explain` text |
| `zap_colors`, `explosion_colors` | from `decl.c zapcolors[]` and `mapglyph.c explcolors[]` |
| `display_rules` | prose notes from `mapglyph.c`: hero glyph, statues, corpses, lit corridors, dark room, shuffled colours |
| `tty_color_rendering` | the escape-to-colour table above |

## corpses.py

```python
from nh.data.corpses import corpse_info, corpse_verdict, taint_chance, Verdict
v = corpse_verdict("jackal corpse", hero_race="human", hero_role="Valkyrie",
                   age_turns=80, has_poison_res=False)
v.verdict        # Verdict.DEADLY (str enum: SAFE < RISKY < DEADLY < NEVER)
v.reasons        # ("DEADLY: 20% chance it is tainted ...", "RISKY: 28% chance of 'you feel sick' ...")
v.benefits, v.notes, v.taint_chance, v.monster, v.as_dict(), str(v)
```

These are ports of `eat.c` (`eatcorpse`, `cprefx`, `cpostfx`, `givit`,
`intrinsic_possible`, `maybe_cannibal`, `rottenfood`), `mon.c`
(`make_corpse`, `corpse_chance`, `undead_to_corpse`, lycanthrope reversion in
`mondead`) and `were.c`. The module docstring lists the exact order of
events.

- **NEVER**: Riders; petrification (cockatrice, chickatrice, Medusa) without
  stoning resistance; green slime (and its globs); lycanthropy (either form,
  since the corpse is always the `@` form); cannibalism (orcs and Cavemen are
  exempt); little dog, dog, large dog, kitten, housecat or large cat for
  anyone other than orcs and Cavemen (permanent Aggravate monster).
- **DEADLY**: any chance that the meat is tainted. `rotted = age/(10+rn2(20))`
  (+2 if cursed, -2 if blessed), and rotted > 5 is fatal food poisoning. For an
  uncursed corpse this starts at 60 turns and is certain from 174.
  Lichen, lizard and Rider corpses never rot, and acid blobs are exempt.
  Zombies, mummies and vampires leave a base-race corpse that is already 100
  turns old (35% tainted when fresh). Starting to eat while Satiated (choking)
  is also DEADLY.
- **RISKY**: poisonous without resistance (80%: -1d4 Str, 1d15 HP), acidic
  without resistance (1d15), mild sickness from age, stun (bats, yellow
  light, stalker), 200 turns of hallucination (`AD_STUN`/`AD_HALU` attackers,
  violet fungus), polymorph (chameleon, doppelganger), mimic helplessness,
  disenchanter, and quantum mechanic (toggles speed).
- `corpse_info(name)["intrinsics"]` gives the probability of each intrinsic
  from one full corpse: one candidate is picked uniformly, then
  P(level > rn2(chance)) with chance 15, teleportitis 10, teleport control 12,
  telepathy 1. Examples: floating eye telepathy 1.0, killer bee poison
  resistance 0.30, hill giant +Str 0.5.

Not modelled: the hero being polymorphed, ice boxes, and the
Samurai/Japanese item names.
