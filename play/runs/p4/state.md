# p4 — current state (rewrite as things change)

## Character
- Name/role: P4, lawful female dwarven Valkyrie, god: Tyr. Seed 404 (local practice game).
- Turn / Dlvl / XL / HP / Pw / AC: T:3199 / Gnomish Mines 3 (DL7) / XL6 / 66/66 / 9/9 / AC5 / $86
- Position at end of shift 2: (14,20) DL7, a dead-end pocket, standing on a VERIFIED dust Elbereth (T:3199).
  A hostile BLACK UNICORN (speed 24, up to ~36 dmg/turn) and a hasted kobold shaman hover 3-4 squares away.
- Attributes: St 18/05, Dx 10, Co 19, In 7, Wi 8
- Skills: long sword SKILLED (T:2834), dagger Basic.
- Intrinsics (source, turn): cold res (Valk), stealth (Valk), infravision (dwarf), speed at XL7
- Luck notes: nothing done to change Luck. (T:2302: killed an unseen biter while blind — "It bites! You get
  zapped!" = grid bug, hostile; no murder message.)
- Alignment / god anger notes: none.
- HUNGER: food ration eaten T:2493 -> expect "Hungry" around T:3290. See Food below.

## Prayer log
| turn | reason | result |
|---|---|---|
| (none yet) | | prayer timeout long expired: prayer should work in MAJOR trouble (HP <= 11 at XL6, i.e. max/6) |

## Equipment worn/wielded (letter: item)
- a: the blessed rustproof +1 EXCALIBUR (wielded; dipped T:2495 DL4 fountain, 2nd dip). c: +3 small shield (worn),
  j: +0 orcish helm (worn, not cursed).

## Key inventory (letters) — mark evidence: [seen in inventory] vs [inferred] vs [UNVERIFIED]
- b: uncursed +0 dagger; f: uncursed orcish dagger (quivered); i: 2 uncursed orcish daggers; y: dagger (BUC unknown)
  — throwing daggers (pickup_thrown picks them up when you step on them).
- G: PICK-AXE [seen] (floor, Mines 2). Random pick-axes are never generated cursed (mkobj.c), but ALTAR-TEST it
  before applying (applying wields it; a cursed one would weld and lock out Excalibur). Shopkeepers refuse entry
  with it: drop it outside shop doors.
- I: expensive camera [seen] (apply at a monster to blind it).
- J: LIZARD CORPSE [seen] — the stoning cure. Never eat it for food.
- w: tripe ration (dwarf: "Yak - dog food!", 50% vomiting -> eat only in a safe spot).
- k: uncursed scroll MAPIRO MAHAMA DIROMAT = IDENTIFY [price-ID].
- n: scroll PRATYAVAYAH: enchant armor / remove curse / enchant weapon [price-ID base 80/60].
- B: scroll STRC PRST SKRZ KRK; D: scroll EIRIS SAZUN IDISI; H: scroll LEP GEX VEN ZEA (all unknown).
- p: unlabeled scroll (blank paper); q: plaid spellbook; u: dusty spellbook (unread — Int 7, don't read)
- h: BLESSED sky blue potion, base 200: enlightenment/full healing/levitation/polymorph/speed.
- t: dark potion; F: bubbly potion (from a water nymph — nymphs often carry object detection) (unknown).
- r: WAND OF LIGHT; x: marble wand CALLED "polymorph" (engrave-test) — sliming cure (self-zap), polypiling.
- A: BAG OF TRICKS — applying it creates a monster; never put it in a bag of holding.
- Gems: C: 2 blue, E: yellow, s: orange, z: 2 white (all unknown; Minetown shops can price them).
- Escape items: none. Elbereth + upstairs + prayer.
- Healing: none known (h might be full healing, ~8%).
- Emergency cures: lizard corpse J (stoning), polymorph wand x (sliming), prayer (never used).
- Food: tripe ration (w) only. The lizard is NOT food.

## Identified appearances (appearance -> identity)
- scroll MAPIRO MAHAMA DIROMAT = identify; balsa wand = light
- CRYSTAL WAND = DIGGING (a bugbear zapped it at T:2834 and dug a hole). SILVER WAND = MAKE INVISIBLE (a hill orc
  zapped itself T:2879). Name them (call_type) when one is in the pack.
- DL2 shop price-IDs: ASHPD SODALG = light (50); ETAOIN SHRDLU = 200 group (amnesia/create mon/earth/taming);
  short wand (150 group), ebony wand (150 or 200 group), horn 20 = tooled horn.

## BUC knowledge
- Orcish helm #1 (DL1 goblin): CURSED — left on DL1 (48,8). Orcish helm #2: not cursed, worn.
- DL2 altar test T:909-916: daggers, scroll k uncursed; orange potion CURSED (sold); sky blue BLESSED.
- Unknown: pick-axe G, dagger y, scrolls B/D/H/n, potions t/F, spellbooks, camera, gems.

## Dungeon map
| Dlvl | branch | features (stairs, altars+alignment, shops+type, fountains, stashes, traps, notes) |
|---|---|---|
| 1 | Dungeons | up (52,18), down (12,8). 9 rooms, explored. Cursed orcish helm at (48,8). |
| 2 | Dungeons | up (25,12), down (17,4). FOUNTAIN (24,13) next to the up stairs. CHAOTIC altar (Loki) (5,4). Sipaliwini's GENERAL STORE (66-73,3-5), door (65,4). Kitten left here (T:~1200). |
| 3 | Dungeons | up (65,11), down (52,6). A fountain somewhere (not located). West third unexplored. |
| 4 | Dungeons | up (54,5); '>' (45,15) -> Dungeons DL5; '>' (72,7) -> GNOMISH MINES. Fountain (42,15) GONE (Excalibur). Falling rock trap (43,16) under a food pile. A sink. |
| 5 | Dungeons | up (50,17). Barely seen. |
| 5 | Mines 1 | up (35,13), down (46,14). Traps: pit (4,9), arrow trap (14,13), magic trap (59,14), spiked pit (58,13). Explored. |
| 6 | Mines 2 | up (48,18), down (42,11). Squeaky board (46,17), teleport trap/level teleporter (17,15). Explored. A looking glass at (38,14). A gas spore drifts in the east. |
| 7 | Mines 3 | up (13,6). HOLE (30,7) dug by the bugbear (leads to DL8), bear trap (28,8). East half (x>35) and '>' not found yet. Probably NOT Minetown (cave filler; no town seen). Many hill orcs came along row 8 from the east. |

## Pets
- None (kitten left on DL2 at T:~1230).

## Threats / known dangers
- DL7: BLACK UNICORN (hostile, speed 24, butt d12 + kick d6 twice a turn; it hit me for 20 in 2 turns). Its horn
  = a unicorn horn (killing a cross-aligned unicorn is fine for a lawful). It avoids lining up for throws. Stand on
  Elbereth to rest; fight it only at high HP (prayer is the net at HP <= 11).
- DL7: an INVISIBLE hill orc (zapped make invisible), maybe 1-2 more hill orcs; a hasted kobold shaman.
- DL8: the BUGBEAR with the WAND OF DIGGING (fell through its hole) + 2 hill orcs that jumped down the hole.
- Dust Elbereth: garbles 1 letter in 25 when engraved (~28% of Elbereths are born broken) and decays at random
  (1 in 70 turns at Dex 10). Always read back; re-check every few turns.

## Objective and plan
- Current objective: Minetown (probably DL8 = Mines 4): altar BUC tests, shops (price-ID), food.
- Next steps:
  (1) FOOD first: Hungry ~T:3290. Eat a FRESH safe corpse (corpse() check; hill orcs are fine; not kobolds) or the
      tripe ration on Elbereth. Buy food in Minetown.
  (2) The black unicorn: kill it for the horn if it comes adjacent while HP is high; otherwise avoid dead ends.
  (3) Explore DL7's east half for '>' (or use the hole at (30,7): step_onto it on purpose, lands at a random spot).
  (4) Minetown: temple altar -> BUC-test the pick-axe, potions, scrolls; price-ID scrolls B/D/H/n, potions F/t,
      gems; check the lighting shop for a magic lamp (base 500). Drop the pick-axe outside shops. Never dip there.
  (5) Kill the bugbear on DL8 for the wand of digging.
