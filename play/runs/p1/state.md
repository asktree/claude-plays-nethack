# p1 — current state (rewrite as things change)

## Character
- Name/role: P1 the Stripling — lawful female dwarven Valkyrie, god: Tyr (seed 101, local practice game)
- Turn / Dlvl / XL / HP / Pw / AC: T:1675 / Dlvl 2 / XL3 (Exp 74; XL4 at 80) / 37/38 / 5/5 / AC2
- Position at shift end: standing ON the DL2 UP stairs `<` at (46,16) (room cols 44-50 rows 16-19). No monsters in
  view, no prompt open. Not hungry (ate the food ration T:1211 -> expect `Hungry` around T:2000; then candy bars g/j,
  lichen corpse m, or fresh safe corpses).
- Attributes: St17->18? and Dx11->12? ("You feel strong!"/"You feel agile!" at T:1639 — verify with `<C-x>`), Co20 In10 Wi10 Ch7 (Ch7 => shop prices +50%)
- Intrinsics (source, turn): cold res (Valk), stealth (Valk), infravision (dwarf), speed at XL7 ...
- Luck notes: Luck 0 (nothing that changes Luck). No peacefuls killed, no mirrors broken.
- Alignment / god anger notes: clean; alignment record >= 14 ("well-pleased" at T:1271).

## Prayer log
| turn | reason | result |
|---|---|---|
| T:1271 | welded cursed orcish dagger (MINOR trouble — mistake) | "shimmering light ... Tyr is well-pleased": prayer accepted, timeout reset (rnz(350)), but the minor trouble was NOT fixed (needs Luck>0 or an altar). **Do not pray again before ~T:2300** unless it is life-or-death (HP<1/7) and even then it is a gamble. |

## Equipment worn/wielded (letter: item)
- **WIELDED: o: cursed corroded orcish dagger — WELDED to my hand since T:1267** (damage 1-3; cannot switch weapons until uncursed)
- a: uncursed +1 long sword — in pack, NOT wieldable until the dagger is uncursed [seen]
- c: uncursed +3 small shield (worn) [seen]
- e: +0 studded leather armor (worn) [seen]
- n: orcish helm (worn since T:1131, went on fine, AC 3->2; BUC unknown) [seen]

## Key inventory (letters) — mark evidence: [seen in inventory] vs [inferred] vs [UNVERIFIED]
- p: orcish dagger (thrown at me by a goblin; BUC unknown — THROW ONLY, never wield) [seen]
- b: uncursed +0 dagger — **LEFT ON DL3 at (28,14)** (thrown at the werejackal). Retrieve only when the werejackal is gone.
- h: **magic marker** (charges unknown; write scrolls once useful ones are identified — e.g. remove curse / enchant weapon) [seen]
- k: scroll labeled ZELGO MER = **scroll of identify** [price-ID, certain]. Unread.
- i: scroll labeled EIRIS SAZUN IDISI — base 200 (sell offer 100): create monster / earth / taming / amnesia. Not worth reading blind (amnesia risk). [seen]
- f: iron ring — base 100 (offer 50): adornment / hunger / protection / prot. from shape changers / stealth / sustain ability / warning. NOT worn. [seen]
- l: 2 violet gems (stacked => same type; amethyst or glass) [seen]
- Escape items: none. Healing: none. Emergency cures: none (no lizard corpse, no unicorn horn).
- Food: g, j: candy bars (100 each); m: lichen corpse (200, never rots).
- Gold: $19
- No pet (kitten abandoned on DL1).

## Identified appearances (appearance -> identity)
- ZELGO MER -> identify (certain, base 20)
- EIRIS SAZUN IDISI -> base 200 scroll class (create monster / earth / taming / amnesia)
- ZLORFIK, DUAM XNAHT, HACKEM MUCHE -> base 100 scroll class (confuse monster / destroy armor / fire / food det. / gold det. / magic mapping / scare monster / teleportation)
- iron ring -> 100zm ring class (see above)
- swirly potion -> base 100 class (confusion / extra healing / hallucination / healing / restore ability / sleeping)
- cyan potion -> base 250 class (acid or oil)
- murky potion -> base 50 class (booze / fruit juice / see invisible / sickness)
- diamond ring -> shop price 300 (base 150 or 200)

## Dungeon map
| Dlvl | branch | features (stairs, altars+alignment, shops+type, fountains, stashes, traps, notes) |
|---|---|---|
| 1 | main | up stairs in start room NE corner (~76,4). DOWN stairs (54,7) in the big room (cols 50-61, rows 5-9). SINK (55,6). Boulders in corridors (23,4), (40,13), (37,14). Left on floor: ring mail (36,11), morning star (23,17), broken large box (18,3). Kitten is here. Fully explored. |
| 2 | main | **UP stairs (46,16)** in a room cols 44-50 rows 16-19 (doors: (44,19) W open, doorways (45,15)/(47,15) N, (51,17) E -> corridor east). **DOWN stairs (48,7)** in a room cols 48-53 rows 6-8 (W doorway (47,8) — newts/geckos kept coming through it; hidden door (47,6) NW, closed; S door (48,9) closed — an acid blob oozed under it and roams around (47,10); E door (53,7) open). FOUNTAIN (25,6) in the N-central room — Excalibur dips at XL5+ (needs the long sword wieldable!). Boulders (18,6), (13,14), (16,14), (58,19). Potion on the floor at (56,19) (unknown). Yellow mold corpse (50,16): poisonous, do not eat. Old corpses (47,8). Locked door (71,9) kicked open; TRAP DOOR just north of it. East/north part still unexplored. |
| 3 | main + Mines branch | Arrived by trap door at (5,17). SW room cols 5-14 rows 15-17, doors (13,14) N and (15,16) E; hidden passage (16,15)->(16,14) north to the `<` room. **UP STAIRS (19,9)** in a small room (cols 18-20, rows 4-9; doors (17,8) W, (21,5) E). ARROW TRAP (19,6) (known; 9 arrows, human corpse, rocks on it). Annootok's GENERAL STORE NW corner (floor cols 3-7 rows 5-8, door (3,9), shk home square (3,8); normal 1/2-price buyer; stock: thick spellbook 800, scrolls ZLORFIK/DUAM XNAHT/HACKEM MUCHE 150, swirly potion 150 x2, cyan potion 375, murky potion 100, diamond ring 300, scimitar 23, food ration 68, cram 53, 2 lembas 136, 2 oranges 28). Middle room cols 42-48 rows 5-9: doors (41,5) W open, (43,10) S doorway, (48,10) S closed. Corridor row 3 (35-50,3) links (41,4) to a corridor (50,4)-(50,9) then east along row 9 to a door (60,8) of an unexplored E room. Small room cols 29-32 rows 12-16 with **`>` (29,16)**, doors (28,14) W doorway, (33,12) E, (33,15) E closed, (29,11) N. SE room cols 42-49 rows 16-18 with **`>` (46,18)**, doors (48,15) N (was hidden), (50,17) E; corridors along rows 16 and 18 east to a tiny room cols 58-60 rows 16-18 (doorways (57,16), (57,18), (60,15) N). Orcish shield left at (47,16). Unknown potion in the corridor at (25,11). My dagger b at (28,14). A gold VAULT exists (guard footsteps). One of the two `>` is the Gnomish Mines branch (unknown which). Old corpses (34,12), (42,15), (52,14): do not eat. |

## Pets
- kitten on DL1, abandoned (not worth fetching).

## Threats / known dangers
- **DL3: WEREJACKAL** (@ form seen at T:1411 near the `>` room W door (28,14); regenerates; hits up to 6; in jackal form its bite gives lycanthropy 1/4 per hit; Elbereth works only on the animal form; it does NOT follow up stairs). With the welded dagger: do not fight it — walk away (a monster that moves cannot also attack that turn).
- **Welded cursed dagger: melee damage only 1-3.** Even geckos take 3-4 rounds. Avoid hill orcs, dwarves with picks/mattocks, anything marked `!!`; fight only at choke points; retreat to stairs early (HP < 60%).
- Prayer effectively unavailable until ~T:2300.
- Acid blobs on DL2 (near (48,9)) and DL3 (SE corridor): harmless unless meleed (passive acid + corrosion) — walk around them.
- Arrow trap DL3 (19,6). Trap door DL2 north of (71,9).

## Objective and plan
- Current objective: **uncurse the welded dagger** so the +1 long sword can be wielded again. Ways: scroll of remove curse (base 80: sell offer 40) or enchant weapon (base 60: offer 30) — read unknown scrolls only after a shop sell-offer shows base 60/80; holy water. Prayer will NOT fix it at Luck 0. Fountain dips uncurse only 4/30 per dip, 1/3 dry-up per dip, and risk demons/nymphs/snakes: last resort only, and not the Excalibur fountain.
- Next steps: 1) explore the rest of DL2 carefully from `<` (46,16): E corridor from (51,17), N doorways, the potion at (56,19); 2) collect every scroll/potion, price-ID at Annootok's on DL3 (avoid the werejackal: it hangs around the DL3 `>` room; the DL3 `<` room is reached from the DL2 `>` (48,7)); 3) XL4 at 80 Exp (6 more) from weak monsters only; 4) eat when Hungry; 5) Excalibur at XL5 once the sword is wieldable; Mines only after the sword is back.
- Open questions: which DL3 `>` is the Mines? iron ring identity; violet gems (2, same type); magic marker charges; St/Dx values after the exercise gains.
