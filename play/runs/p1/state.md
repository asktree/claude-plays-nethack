# p1 — current state (rewrite as things change)

## Character
- Name/role: P1 the Skirmisher — lawful female dwarven Valkyrie, god: Tyr (seed 101, local practice game)
- Turn / Dlvl / XL / HP / Pw / AC: T:2638 / Dlvl 5 / XL4 (Exp 131; XL5 at 160) / 49/49 / 8/8 / AC2
- Position at shift end: DL5, standing ON the permanent BURNED "Elbereth" at (45,18) (big S room cols 33-46 rows 17-19).
  A harmless grid bug was 3 squares away. Not hungry (food ration eaten T:2331 -> Hungry ~T:3100).
- Attributes: St18 Dx12 Co20 In10 Wi10 Ch7 (Ch7 => shop prices +50%)
- Intrinsics: cold res (Valk), stealth (Valk), infravision (dwarf), speed at XL7.
- Luck 0; alignment record high ("well-pleased" at T:2016); no peacefuls killed.
- Lycanthropy T:1780–2016: CURED by prayer. Bitten again T:2240 without infection.

## Prayer log
| turn | reason | result |
|---|---|---|
| T:1271 | welded cursed orcish dagger (MINOR trouble — mistake) | accepted, trouble NOT fixed, timeout reset |
| T:2016 | lycanthropy (MAJOR), right after the jackal transformation; prayer_check 91% | "well-pleased ... You feel purified. You return to dwarven form!" CURED. Timeout reset (rnz(350)). **No prayer before ~T:3000** unless life-or-death; always `prayer_check()` first. |

## Equipment worn/wielded (letter: item)
- **WIELDED: a: uncursed +1 long sword** [seen]
- c: uncursed +3 small shield (worn), e: +0 studded leather armor (worn), n: +0 orcish helm (worn) -> AC2 [seen]
- The cursed corroded orcish dagger lies on the DL1 `>` (54,7). Never pick it up.

## Key inventory (letters)
- **z: WAND OF LIGHTNING** (engrave-identified T:2565; charges unknown, 1 used) — 6d6 ray, bounces (never zap toward a wall next to me; engraving with it blinds). Use `zap('z', dir)`.
- w: uncursed RING OF FIRE RESISTANCE (identified by scroll T:2638; not worn — wear for fire traps / red dragons / Gehennom).
- f: iron ring (100zm class, unknown, NOT worn). y: figurine of a coyote (BUC unknown; apply = release, may be hostile).
- h: magic marker (charges unknown). Scrolls: i EIRIS SAZUN IDISI (base 200), x GARVEN DEH (unknown; price-ID hoped base 80/60). Identify scroll k USED.
- Potions: q yellow, u brilliant blue (both unknown).
- Food: g, j candy bars (100 each); m: 1 lichen corpse (200, never rots). No ration left. Eat fresh safe corpses (`corpse()` check).
- $52. No escape items, no healing potions, no unicorn horn, no lizard corpse.
- Left behind on DL3 `<` room: +0 dagger b (18,5), orcish dagger p (21,5), violet gems (20,5)/(21,5) (werejackal territory).

## Identified appearances
- ZELGO MER -> identify (used). EIRIS SAZUN IDISI -> base 200 class. ZLORFIK, DUAM XNAHT, HACKEM MUCHE -> base 100 class.
- marble wand -> lightning. diamond ring -> fire resistance. iron ring -> 100zm class.
- swirly potion -> base 100; cyan -> 250 (acid/oil); murky -> 50.
- Scroll price targets: remove curse/enchant armor base 80 (sell offer 40); enchant weapon/blank base 60 (offer 30).

## Dungeon map
| Dlvl | branch | features |
|---|---|---|
| 1 | main | `<` (76,4). `>` (54,7) big room (50-61,5-9) — cursed orcish dagger on it. SINK (55,6). Fully explored, kitten killed (feral). |
| 2 | main | `<` (46,16) room (44-50,16-19). `>` (48,7) room (48-53,6-8). FOUNTAIN (25,6). NE room (69-71,4-8): egg + fortune cookie; TRAP DOOR (71,8) = SHAFT (dropped me to DL5). Fully explored. |
| 3 | main + Mines branch | `<` (19,9) room (18-20,4-9), doorless E (21,5), W door (17,8). ARROW TRAP (19,6). **WEREJACKAL (d form) + 4 jackals + fox frozen next to the `<` at (19,8)** — arriving by the DL2 `>` means an instant bite. Annootok's general store NW (3-7,5-8). `>` (29,16) and `>` (46,18) — one is the Mines. Only corridor east of the `<` room: (22,5)-(23,10)-(24,11)-(26,11)-(27,13)-(28,14). Potion (25,11). Unexplored east room via door (60,8). |
| 4 | main | never visited (shaft skipped it). Its `<` leads to a DL3 `>`; its `>` leads to the DL5 `<` (59,16). |
| 5 | main | Arrival room (59-65,4-8). **`<` (59,16)** room (56-60,13-16). **`>` (70,16)** room (67-75,14-17). **FOUNTAIN (26,8)** NW room (door (24,9)/(37,7)) — Excalibur dips at XL5. **BURNED ELBERETH (45,18)** in the big S room (33-46,17-19; doors (32,19) W, (41,16) N, (47,18) E locked/hidden). Kicked-open door (54,5). Empty chest (38,5). Fully explored; quiet (1 imp, 1 grid bug in ~350 turns). |

## Threats / known dangers
- DL3 werejackal pack at the `<` (see map). Never melee it in d form (bite = lycanthropy 1/4, prayer now unavailable); in @ form fight only with an abort plan; it does not follow across stairs; levels are frozen while away.
- No healing/escape items: keep HP > 60% before any fight; the burned Elbereth (45,18) and the `<` (59,16) are the DL5 refuges.
- Unknown DL4 between me and home.

## Objective and plan
1. **XL5 (29 more Exp)**: fight normal DL5/DL4 monsters near the refuges (imps ~15 xp, zombies 5); use the wand of lightning only for real threats (soldier ants; dwarves/gnomes are peaceful to me — check `peaceful`).
2. **Excalibur**: at XL5, full HP, `#dip` the long sword (a) at the DL5 fountain (26,8) (`#dip<CR>`, `a`, `y`); repeat until "From the murky depths, a hand reaches up" or the fountain dries; water demon/nymph/moccasins are the risks (Elbereth square is ~20 squares away; the `<` ~35).
3. Then explore DL4 (find its `<`/`>`), return to DL3 via a `>`, price-ID scrolls x/i and potions q/u at Annootok's (sell offers), deal with the werejackal pack from range (a lightning bolt down a corridor line hits several) or avoid it.
4. Mines (gnomes/dwarves peaceful) for the Minetown altar/shops after Excalibur.
5. Food: 1 lichen + 2 candy bars only — eat fresh kills; buy rations when in the shop.
