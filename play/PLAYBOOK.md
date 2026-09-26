# Playbook: ascending a lawful dwarven Valkyrie in NetHack 3.6.7

This is the strategic plan. `PLAYER.md` has the interface and the survival protocol; this file says what to do
and when. Knowledge lookups: `knowledge/wiki/*.txt` (grep it; `knowledge/INDEX.md` lists pages),
`src/nh/data/*.json` (monsters/objects), and the NetHack source at `~/src/nethack-3.6.7/src` for exact rules.
When a mechanic matters for a risky decision, **check the source or wiki instead of trusting memory**.

Lessons from the only other LLM ascension (Astra, same character, 3 runs, `docs/research/astra-lessons.md`):
both of its deaths were *not HP deaths* — a death ray at full HP in the Castle (no MR, no reflection) and
sliming after the invocation (no cure in reserve). The winning run was slow and patient: it retreated from the
Castle when it lacked magic resistance and came back ~10,000 turns later fully equipped.

## 0. Character facts
- Valkyrie: starts with +1 long sword, +0 dagger, +3 small shield, 1 food ration; intrinsic **cold resistance**
  and **stealth**; gets **speed** at XL7. Excellent melee. Long sword and dagger skills matter.
- Dwarf: infravision (see warm-blooded monsters in the dark); most Gnomish Mines inhabitants (gnomes, dwarves,
  gnome lords, hobbits? no — hobbits aren't) are **peaceful** to you → the Mines are relatively safe.
  **Never eat dwarves** (cannibalism: Luck −2..−5, aggravate).
- Lawful, god Tyr. Co-aligned altars say "lawful". Excalibur is available (lawful + long sword + XL≥5).
- `#enhance` whenever the game says "You feel more confident in your weapon skills".

## 1. Opening: D1–D4 (target: XL5–8, Excalibur)
- Explore each level fully (`explore()`), fight weak monsters in melee, let the pet help. Pick up: daggers
  (throwing: `t`/`f`), armor you can wear, all wands, rings, amulets, scrolls, potions, tools, gems.
  Don't wear/put on unidentified rings or amulets (strangulation, teleportitis, hunger, levitation lock).
  Armor from the floor can be cursed: prefer to test it (pet steps over it = not cursed; altar drop) or accept
  the risk only for real upgrades.
- Eat corpses of safe fresh kills to save rations (check with the corpse rules). Newts, rats, jackals, etc. are fine.
- **Excalibur**: at XL5+, stand on a fountain (not in Minetown — the Watch objects) and `#dip` the long sword
  (`#dip<CR>`, choose the long sword, answer `y` to "into the fountain?"). Each dip has 1/6 chance. Risks per
  failed dip (~1/30 each): water moccasins, a water nymph (steals), a **water demon** (very dangerous at XL5;
  sometimes grants a wish instead). Prepare: full HP, known escape route (upstairs close), pet nearby,
  Elbereth doesn't work on the fountain square — if a demon appears hostile, retreat upstairs / pray if HP
  crashes. Fountains dry up; use several. Astra needed 6, 12 and 27 dips in its three runs.
- Sokoban's entrance is the **up staircase on the level just below the Oracle** (Oracle is D5–9). The Gnomish
  Mines branch down-stairs are on D2–4.

## 2. Early-mid game: Mines to Minetown, Sokoban (target: XL8–12, AC ≤ 0)
- **Minetown** (Mines level 3–4, i.e. D5–8): temple (co-aligned priest: buy protection — donate 400×(XL+1)
  gold when you have ≥ that; 600×(XL+1) if XL≥... check wiki `Priest`/`Donating`), shops (price-identify),
  altar (drop items to learn B/U/C). Keep the Watch peaceful: don't break doors, don't dip/quaff fountains
  there, don't anger shopkeepers. Buy/collect **candles** (you need 7 for the Candelabrum much later; Izchak's
  lighting shop sells them).
- **Sokoban** (4 levels up): do it early (XL 6–10). Solutions are in `knowledge/wiki/Sokoban_Level_*.txt`
  — identify the variant and follow the solution exactly. Rules: boulders can't be pushed diagonally; don't
  break/destroy boulders or read earth there (Luck penalty); watch for monsters behind boulders. Prize at the
  top: **bag of holding** or **amulet of reflection** (both huge). The top level has a zoo — fight at a choke
  point.
- Mines' End has a **luckstone**; worth it when strong enough (XL10+).
- Build AC: dwarvish iron helm (hard hat), dwarvish mithril coat (from dwarves in the Mines!), boots, gloves,
  cloak. Aim for AC ≤ 0 before D10, ≤ −5 before D20.
- Get **poison resistance** (eat killer bees, soldier ants?, scorpions, etc. — check corpse info), and
  telepathy (floating eye corpse — eat it, never melee it; kill with thrown daggers).

## 3. Mid game: D10–D25 (target: XL14+, MR and reflection)
- **Magic resistance (MR)** sources: gray dragon scale mail (wish), cloak of magic resistance, Magicbane (no),
  quest artifacts (no, Orb of Fate gives none)... Most likely: a wish.
- **Reflection** sources: amulet of reflection (Sokoban 50%), shield of reflection, silver dragon scale mail.
- **Wishes**: magic lamps (bless and #rub), wand of wishing (Castle), fountains/thrones (rare), djinni from
  smoky potions. First wish: MR if missing (blessed +2 gray dragon scale mail), else reflection.
- Quest portal level (D11–16) gives a telepathic message. The Valkyrie quest needs **XL14**. Its nemesis
  Lord Surtur (fire giant) carries the **Bell of Opening** (required for the endgame). Fire resistance helps.
- **Medusa** (D21–24): needs reflection or blindness (blindfold/towel) against her gaze, and a way over water
  (levitation, water walking, jumping, freezing the water with cold). Don't look at her without protection.
- Instadeath checklist before going deeper than ~D20:
  | threat | protection | cure |
  |---|---|---|
  | death ray (wand/spell), touch of death | MR (death ray: also reflection) | none — prevent |
  | disintegration breath (black dragon) | reflection or disint. res | none |
  | stoning (cockatrice, Medusa gaze) | reflection/blindness vs gaze; gloves | lizard corpse, acidic corpse, prayer, stone to flesh |
  | sliming (green slime, Juiblex) | avoid melee range | fire (wand/scroll/spell), polymorph (self-zap works even with MR), prayer (not in Gehennom) |
  | strangulation (amulet) | don't wear unknown amulets | remove it, prayer |
  | drowning (eels, krakens) | magical breathing, stay away from water edges | escape/teleport; don't fight eels next to water |
  | level drain | MR doesn't stop it; Excalibur does (drain res) | restore ability doesn't; gain level |
  | lycanthropy | avoid were-bites | prayer, holy water, wolfsbane |
  | illness/food poisoning | don't eat bad corpses | unicorn horn, prayer |

## 4. The Castle (below Medusa) — **only with MR, preferably MR + reflection**
- The wand of wishing is in one of the corner towers (in a chest). Astra: run 1 NE tower, run 3 NW tower.
- Ways in: play the passtune on a musical instrument (learn it: prayer boon or Mastermind game with an
  instrument near the drawbridge), destroy the drawbridge (force bolt/striking), levitate over the moat, or
  scroll of earth. Beware soldiers with wands, liches, minotaurs in the maze, sharks/eels in the moat.
- Standard wishes (adapt): MR (blessed +2 gray dragon scale mail) if missing; "2 blessed scrolls of charging"
  (recharge the wand of wishing once); blessed +2 speed boots; blessed amulet of life saving; reflection if
  missing; blessed magic marker; blessed genocide (liches `L` or mind flayers `h`); blessed potions of gain
  level (for quest XL14); blessed +2 gauntlets of power... Wishes add to the prayer timeout (50–149).
- Trapdoors at the east end of the Castle drop to the **Valley of the Dead** (Gehennom).

## 5. Gehennom (MR mandatory)
- **Prayer does not work in Gehennom.** Carry cures: unicorn horn, lizard corpses, holy water/remove curse,
  fire source for sliming, escape items (teleport wand/scrolls; cursed scroll of teleportation = level teleport).
- Levels: Valley (temple of Moloch; undead), then mazes with Juiblex (swamp; engulf → illness), Orcus (town;
  wand of death), Asmodeus, Baalzebub. **Vlad's Tower** branch is 9–13 levels below the Valley (go up the
  tower; Vlad has the **Candelabrum**; attach 7 candles). **Wizard's Tower**: entered via the portal on a fake
  wizard tower level; the Wizard of Yendor has the **Book of the Dead**. He resurrects and harasses forever.
- Invocation at the vibrating square (bottom of Gehennom): ring the Bell (apply), light the Candelabrum
  (apply), read the Book → stairs to the Sanctum. Kill the high priest of Moloch, take the Amulet of Yendor.
- Keep remove curse/holy water and an uncursing plan for the Wizard's curses; don't wear levitation near him.

## 6. Ascension run
- Climb to D1 with the Amulet (the "mysterious force" sends you back down sometimes — keep going).
- Elemental Planes via D1's up stairs: Earth, Air, Fire, Water — find each plane's magic portal.
- Astral Plane: three high temples; find the **lawful** altar (farlook the altar / the priest alignment),
  stand on it and `#offer` the Amulet. Arrive with full HP, life saving worn, escape items, a charged attack
  wand. The Riders (Death, Famine, Pestilence) are there — avoid them.

## 7. General good habits
- Keep a stash on a known level (upstairs of a quiet level) for spare stuff; log it in state.md.
- Name/call item types as you learn them (`#name` / `C`), and write identified appearances in state.md.
- Use shops to price-identify: base prices tell scroll/potion/ring/wand classes (see wiki `Price_identification`).
- Engrave-test unknown wands (`E`, choose the wand) — cheap identification (don't do it in shops).
- Pets: keep one strong pet early; don't let it die needlessly; never swap it into water.
- Track Luck: don't kill peacefuls, don't break mirrors, pray correctly. A luckstone locks in good Luck.
