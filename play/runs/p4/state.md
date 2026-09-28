# p4 — current state (rewrite as things change)

## Character
- Name/role: P4, lawful female dwarven Valkyrie, god: Tyr. Seed 404 (local practice game).
- Turn / Dlvl / XL / HP / Pw / AC: T:4257 / MINETOWN = Gnomish Mines 4 (DL8), "Bustling Town" (minetn-6) / XL7 /
  57/78 / 10/10 / AC-8 / $8
- Position at end of shift 2: (55,17) DL8, ON the lawful altar of Tyr in the co-aligned temple (peaceful priest).
- Attributes: St 18/05, Dx 10, Co 19, In 7, Wi 8; Cha 8-10 (shop prices x4/3).
- Skills: long sword SKILLED (T:2834), dagger Basic.
- Intrinsics (source, turn): cold res (Valk), stealth (Valk), infravision (dwarf), SPEED (XL7, T:4076),
  TELEPATHY (floating eye corpse, T:4096: see minded monsters while blind), MAGIC RESISTANCE (worn GDSM X).
  NOT poison resistant (unicorn corpse T:3678 gave nothing).
- Luck notes: nothing done to change Luck. Alignment: many hostile kills, no peacefuls harmed.
- HUNGER: prayer fixed hunger T:3562 (900), black unicorn corpse T:3678 (+300). Not hungry at T:4257; expect
  Hungry around T:4700-4800. Food: S (food ration). Eat when Hungry.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:3562 | Weak (hunger), DL7 (40,15) | SUCCESS, "Your stomach feels content". Timeout reset (rnz 350) |
| T:4251 | (a WISH, not a prayer) | +50-149 prayer timeout. prayer_check() at T:4257: 0% safe. Assume NO prayer before ~T:4900; always prayer_check() |

## Equipment worn/wielded (letter: item)
- a: blessed rustproof +1 EXCALIBUR (wielded). X: +2 GRAY DRAGON SCALE MAIL (worn; wished blessed T:4251; MR).
  c: uncursed +3 small shield. j: +0 orcish helm (not cursed). O: uncursed +0 iron shoes (worn T:4124). AC -8.

## Key inventory (letters) — everything below was altar-tested T:4121/T:4245 [seen]
- Daggers to throw: b uncursed +0 dagger, y uncursed dagger, f uncursed orcish dagger (quivered), i 2 uncursed
  orcish daggers.
- V: uncursed ELVEN MITHRIL-COAT (spare body armor, 150 wt; sells for ~120 at Chibougamau's general store).
- S: uncursed food ration. J: 2 uncursed LIZARD CORPSES (stoning cure; never eat as food).
- L: uncursed UNICORN HORN (from the black unicorn, T:3651): apply for conf/stun/blind/hallu/sickness.
- Wands: U uncursed WAND OF DIGGING (from the bugbear; escape: zap down), P uncursed WAND OF STRIKING (monster
  used it; charges unknown), r uncursed wand of light, x uncursed wand called polymorph (sliming cure: zap self).
- Tools: M uncursed MAGIC MARKER (charges unknown), G uncursed pick-axe (applying is safe now; drop it outside
  shop doors — shopkeepers block you), I uncursed expensive camera, W blessed lamp (was the MAGIC lamp; after the
  djinni it is now an OIL lamp: a light source only).
- Scrolls: k uncursed IDENTIFY (MAPIRO MAHAMA DIROMAT); n CURSED PRATYAVAYAH (enchant armor/remove curse/enchant
  weapon — don't read while cursed); p uncursed blank (unlabeled) — write with M; uncursed unknown: B STRC PRST
  SKRZ KRK, D EIRIS SAZUN IDISI, H LEP GEX VEN ZEA, K KO BATE.
- Potions: h BLESSED sky blue (200 group: enlightenment/full healing/levitation/polymorph/speed); t BLESSED dark
  (unknown); N BLESSED + F uncursed "object detection" (bubbly: both carried by nymphs — strong inference).
- Spellbooks: u BLESSED dusty (blessed books never fail to read in 3.6 — safe to read to learn/ID it),
  q uncursed plaid (Int 7: don't read).
- Gems: C 2 blue, E yellow, s orange, z 2 white (uncursed, unknown).
- Escapes: wand of digging (zap > = hole down), Elbereth, upstairs. Healing: none known (h may be full healing).
- Emergency cures: 2 lizard corpses (stoning), polymorph wand self-zap (sliming), unicorn horn (sickness, conf,
  stun, blind). Prayer NOT available now.

## Identified appearances (appearance -> identity)
- scroll MAPIRO MAHAMA DIROMAT = identify; balsa wand = light; CRYSTAL wand = digging; SILVER wand = make
  invisible; STEEL wand = striking (the one in P).
- ETAOIN SHRDLU = 200 group; an Uruk-hai read one out of sight (T:3988) -> probably CREATE MONSTER (called
  "create monster?").
- bubbly potion = called "object detection" (inference). Magic lamp is known now (discoveries).
- DL2 shop price-IDs: ASHPD SODALG = light (50); short wand (150 group), ebony wand (150 or 200 group), horn 20 =
  tooled horn.

## Dungeon map
| Dlvl | branch | features (stairs, altars+alignment, shops+type, fountains, stashes, traps, notes) |
|---|---|---|
| 1 | Dungeons | up (52,18), down (12,8). Cursed orcish helm at (48,8). |
| 2 | Dungeons | up (25,12), down (17,4). Fountain (24,13). CHAOTIC altar (5,4). Sipaliwini's general store (door 65,4). Kitten left here (T:~1200). |
| 3 | Dungeons | up (65,11), down (52,6). A fountain somewhere. West third unexplored. |
| 4 | Dungeons | up (54,5); '>' (45,15) -> DL5; '>' (72,7) -> MINES. Fountain gone (Excalibur). Falling rock trap (43,16). |
| 5 | Dungeons | up (50,17). Barely seen. |
| 5 | Mines 1 | up (35,13), down (46,14). Traps: pit (4,9), arrow (14,13), magic (59,14), spiked pit (58,13). |
| 6 | Mines 2 | up (48,18), down (42,11). Squeaky board (46,17), teleport/level teleporter (17,15). |
| 7 | Mines 3 | up (13,6). HOLE (30,7), bear trap (28,8), a TRAP DOOR in the east (I fell through it ~T:4103 near (47-50,12-13); the harness has it). '>' never found. West 2/3 explored. |
| 8 | Mines 4 = MINETOWN "Bustling Town" (minetn-6, map offset (20,4)) | CO-ALIGNED TEMPLE of Tyr (51-56,16-18), door (50,17), LAWFUL ALTAR (55,17), peaceful priest. Izchak's lighting store (29-31,11-13), door (30,14) — candles; the magic lamp is bought. Bojolali's delicatessen (42-44,16-17), door (45,16): 1 food ration left (60zm), tripe, clear potion = water (9zm). Chibougamau's GENERAL STORE (43-45,5-7), door (44,8): 2 wands, potions, scroll, weapon for sale; buys anything. Tool shop (36-38,8-10), door (39,9) (not visited). Fountains (29,17), (42,11): NEVER dip/quaff here. Up stairs somewhere x=1-20, DOWN stairs somewhere x=61-75 (not seen yet). Watchmen peaceful. |

## Pets
- None (kitten left on DL2 at T:~1230).

## Threats / known dangers
- Uruk-hai / hill orc packs: their ORCISH ARROWS ARE ALWAYS POISONED (makemon m_initthrow) — each arrow that hits
  is a 1-in-30 instant death without poison resistance. Never walk a 1-wide corridor lined up with an orc that
  has a bow; fight from a square where every square in line is adjacent or wall (a nook).
- Woodland-elves (and all elves) are hostile to a dwarf: elven broadswords hit for ~10; '@' ignore Elbereth.
- Dust Elbereth: garbles 1 letter in 25 when engraved; decays 1 in 70 turns. Always read back.

## Objective and plan
- Current objective: finish Minetown, then Mines' End or back up to the main dungeon (Sokoban/Oracle).
- Next steps:
  (1) Rest to full HP in the temple (safe). Maybe read the BLESSED dusty spellbook u (can't fail).
  (2) Optional money: sell V (elven mithril-coat, ~120) at Chibougamau's; price-ID scrolls/potions there with
      sell_offer(); then buy the last food ration at Bojolali's (60).
  (3) Find Minetown's '>' (east, x 61-75) and '<' (west, x 1-20); record them.
  (4) With MR + AC-8 the Mines' End is reasonable at XL8+ (luckstone). Otherwise go up to DL4 and continue the main
      dungeon (Sokoban up from the level below the Oracle). Keep the wand of digging for escapes.
  (5) Protection from the priest costs 400*XL (2800 at XL7): collect gold; it is worth it later.
