# Lessons from GPT 6 Astra's NetHack 3.6.7 ascension (CodexDelver on Hardfought)

Research digest for the claude-plays-nethack team, written 2026-09-26.

**What this covers.** GPT 6 Astra played three real games, plus a 38-turn shakedown, as **CodexDelver**, a lawful female dwarven Valkyrie on Hardfought US, from 2026-09-06 to 2026-09-21. Run 1 died of sliming on D51 after the invocation. Run 2 died to a death ray in the Castle. Run 3 **ascended at T37140**. The agent ran in an OpenAI Codex coding-agent session and played over SSH, using a tmux screen-scraping harness.

**Sources**
- The read-only clone `/home/user/kenforthewin/nethack_astra`:
  - journals: `memory/live-run.md` (run 1), `run-2.md`, `run-3.md`, `session.md`
  - `memory/run-2-emergency.json` and `run-3-emergency.json`
  - `scripts/*.py`, `EVIDENCE.md`, `docs/*.md`, `config/nethackrc`, `config/tmux.conf`
- All four public dumplogs in <https://www.hardfought.org/userdata/C/CodexDelver/nethack/dumplog/>:
  - `1788718109` (run 0, the shakedown)
  - `1788720306` (run 1)
  - `1788889409` (run 2)
  - `1788964024` (run 3, the ascension)
- Scratch copies of the dumplogs are in this session's scratchpad only. Nothing in the clone was modified.

**Conventions**
- **T** is the game turn (`T:` on the status line) and **D** is Dlvl.
- Coordinates `x,y` are **curses-screen cells** from Astra's 144×36 terminal, where map rows are 10–30. That is exactly how their journals record them. They are not NetHack-internal or NLE coordinates.
- Journal quotes are verbatim. Astra wrote a compressed, space-free shorthand (e.g. `NOMR/reflection`, `HP100→0`). It is kept wherever the wording matters.
- **[SPEC]** marks my own speculation or inference.
- **[MECH]** marks a NetHack-mechanics claim that comes from my general knowledge of 3.6, not from the Astra materials. Verify it against the 3.6.7 source before relying on it.
- Everything unmarked comes from the Astra materials or the dumplogs.
- No passwords, credentials, emails or LAN addresses are reproduced. `session.md` has redacted entries and none are copied.

---

## TL;DR: the findings that matter most

1. **Three real runs, one ascension.**
   - Run 1 reached the invocation (D52, T33169) and then was **turned to slime** on D51 at T33302.
   - Run 2 was **killed instantly at full HP (100/100) by a sergeant's wand of death** in the Castle at T12271.
   - Run 3 **ascended** at T37140 with a score of 1,766,446. Both of its amulets of life saving were unused.
2. **Both deaths were short sequences where HP did not matter.**
   - Run 2 postmortem: *"A visible-state movement guard cannot guarantee protection from a one-hit kill. The strategic error was advancing through the Castle without known magic resistance or reflection."*
   - Run 3 made "no Castle without MR or reflection; prefer both" its first rule.
   - Run 3's Sokoban amulet of reflection **reflected a sergeant's death ray at T11892**, long before the Castle.
3. **Run 3 won by being patient at the Castle.**
   - It retreated from a hasted arch-lich at T14240 (*"DO NOT DESCEND CASTLE until magic resistance/genocide/credible protection"*).
   - It gained temporary MR by **polymorphing into a gray dragon** with a ring of polymorph plus a ring of polymorph control (T24841), killed the arch-lich (T24854), and waited out the form.
   - It then levitated over the moat, came in by the back door, and took the wand of wishing (T25889).
   - Its first wish was +3 gray dragon scale mail.
4. **Eight wishes bought a complete defensive kit.** In order: permanent MR, charging (so the wishing wand could be recharged once), speed boots, a genocide of `L`, a blessed magic marker, and 3 blessed potions of gain level. The gain level potions took XL13 to XL16, which met the quest's XL14 requirement. Late in the game a djinni gave one enchant armor. A **wrested** wish (attempt 23, T36984) gave 3 blessed charging, which kept the Orb of Fate usable as a **portal detector** on the Planes.
5. **The dangerous harness pattern was sending several keys without checking what they would do.**
   - A 24-key movement batch next to a known green slime led to run 1's death.
   - `F6F6` hit a peaceful watchman.
   - `zI8` on an empty wand turned `8` into a melee attack.
   - `aR9` while deaf turned `9` into an attack.
   - `10s` without the `n` prefix under number_pad moved the hero.
   - The fix that stuck was a guard. It accepts multi-key input only at a recognised map prompt, sends movement one step at a time, and stops on damage, conditions, nearby creatures, unknown terrain, a level change, a position mismatch, or a turn jump.
6. **Perception broke whenever the screen looked unusual.** The cases were:
   - the Rogue level's ASCII `.` floor;
   - the polymorphed player glyph `D`;
   - the quest status `Home 1`;
   - the plane names `Earth`, `Air`, `Fire`, `Water` and `Astral`;
   - smoke hiding `@` on the Plane of Fire;
   - natural regeneration masking falling-rock damage.

   Each was found during play and patched mid-game with a regression test. The harness test suite reached 53 tests by the ascension.
7. **The agent checked NetHack's 3.6.7 source for mechanics, and was right to.** Facts it confirmed from the source include:
   - a self-zapped wand of polymorph ignores magic resistance (zap.c 2249–2255);
   - a wish adds 50–149 to the prayer timeout;
   - a wand of wishing can be recharged only once;
   - Vlad's branch is 9–13 levels below the Valley;
   - Plane of Fire smoke blocks line of sight.

   Two costly errors were caused by beliefs the source later contradicted: the run 1 sliming death, and misjudging where Vlad's Tower was in two runs.
8. **Memory was a verbose Markdown journal plus an "emergency JSON".**
   - The JSON began as a structured schema in run 2 (`critical_equipment`, `escape_options`, `sliming_cures`, …).
   - By run 3 it had become about 600 timestamped free-text blobs (`urgent_37116`, `latest_33790`, …).
   - Its "authoritative" structured fields stopped being updated at T7704, while play continued to T37140.
   - The durable win was the **evidence vocabulary**: "formal" (seen in the inventory) versus "inferred" versus "UNVERIFIED", and *"Unknown charges must never be treated as available charges."*
9. **Hardfought operations were mostly routine.**
   - There was one frozen game, three SSH drops (one presumed to be an idle timeout during a sandbox-approval wait), and two user-requested pauses.
   - Every interruption was recovered to the **exact turn**, through save and resume or through the lobby's stale-process recovery.
   - The dgamelaunch lobby, the account rc file, and curses `>>` "more" prompts were the operational details that mattered.
10. **Pace was roughly 500 game turns per wall-clock hour** in the winning run. Run 3 took about 74 hours of active play over three sessions (Sep 9–10, Sep 13–14, Sep 20–21) for 37,140 turns. This is derived from the ttyrec segment times in `docs/RECORDINGS.md`. Runs 1 and 2 were faster, at about 600–800 turns per hour.

---

## Contents

1. [Run timelines](#1-run-timelines)
2. [Deaths: circumstances, root causes, prevention](#2-deaths)
3. [Near-death and crisis moments (all runs)](#3-near-death-and-crisis-moments)
4. [The winning strategy in detail (run 3)](#4-winning-strategy-run-3)
5. [The harness](#5-the-harness)
6. [Memory practices](#6-memory-practices)
7. [Hardfought operational details](#7-hardfought-operational-details)
8. [Recommendations: player rules and harness features](#8-recommendations)
9. [Appendices](#appendices)

---

## 1. Run timelines

### 1.0 Overview

All runs used the same character: CodexDelver, a lawful female dwarven Valkyrie serving Tyr. Dumplog times are server-local US Eastern; UTC is given here.

| | Run 0 (shakedown) | Run 1 | Run 2 | Run 3 |
|---|---|---|---|---|
| Dumplog id (= game start, Unix epoch) | 1788718109 | 1788720306 | 1788889409 | 1788964024 |
| Game start (UTC) | 09-06 18:08 | 09-06 18:45 | 09-08 17:43 | 09-09 14:27 |
| Game end (UTC) | 09-06 18:44 | 09-08 17:07 | 09-09 14:17 | 09-21 20:04 |
| Outcome | `#quit` at T38 | "turned to slime by a green slime", D51, T33302 | "killed by a death ray", D25 (Castle), T12271 | **ASCENDED**, Astral Plane, T37140 |
| Final XL / max HP | 1 / 18 | 18 / 165 | 11 / 100 | 19 / 200 |
| Final AC | 6 | 6 as a slime (AC −19 before death) | −5 | −9 |
| Score | 9 | 715,300 | 82,870 | 1,766,446 |
| Creatures vanquished | 2 | 1269 | 313 | 1481 |
| Wishes used | 0 | 11 | 0 | 8 |
| Genocides | none | `L` (4 lich species) | none | `L` (4 lich species) |
| Elbereth engravings (conduct) | 0 | 10 | 26 | 21 |
| Castle / Medusa level | – | D29 / D25 | D25 / D23 | D28 / D27 |
| Sokoban prize | – | amulet of reflection (a spare; a worn amulet was already reflection) | bag of holding | amulet of reflection |

**Special-level layout by run (from the dumplog overviews)**

| Feature | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| Mines branch | D4 (Mines 5–12) | D4 (5–12) | D3 (4–12) |
| Minetown | D7 (Tyr temple, co-aligned) | D7 (Tyr temple) | D6 (neutral Odin temple) |
| Oracle | D5 | D8 | D9 |
| Sokoban entrance | D6 | D9 | D10 |
| Quest portal | D11 | D14 | D15 |
| Big room | D12 | – | – |
| Vlad's Tower branch | D42 | – | D41 |
| Vibrating square level | D52 | – | D51 |
| Sanctum | – | – | D52 |

### 1.1 Run 0: shakedown (T1–T38, quit)

The dumplog shows three save/restore cycles at T38 (`Really save? [yn] (n) y` … `Restoring save file...` … `welcome back to NetHack!`), followed by `#quit`. `session.md` records that save/restore was verified to match the turn, HP and map, and that controls were tested (number_pad, `k` = kick, arrow keys misfire). `live-run.md` says: *"Shakedown character retired via #quit. Fresh character started normally."*

**Lesson.** Verify the save/restore round-trip and the key bindings with a throwaway character before the real game.

### 1.2 Run 1 (Sep 6–8): invocation completed, then sliming

| Milestone | Turn | Where | Detail |
|---|---|---|---|
| Start | 1 | D1 | St17 Dx15 Co17 In10 Wi7 Ch9. The stream went live 18:44 UTC. |
| Gas spore misread as a floating eye | 1241 | early | The explosion left HP at 7. Lesson recorded: farlook with `;`. |
| Telepathy | 1949 | | Floating eye corpse. |
| Prayers for Weak (hunger) | 4324, 5161, 6010 | | All successful. Prayer at T6900 uncursed the helm. |
| **Excalibur** | 6349 | D5 (Oracle level) fountain | On the 6th dip. |
| Mines | 6582 | Mines 1 = D5 | Minetown D7 (T6920) has a co-aligned Tyr temple. Poison resistance T7056. XL7 and speed T7850. |
| Pet kills the temple priest | 10602 | Minetown | Tamed chameleon "Mercury" killed the Tyr priest, ending the sanctuary. |
| **Sokoban** | 11400–14099 | up from D6 | Soko1 T11683, Soko2 T12369, Soko3 T12855, Soko4 holes T13950. The amulet worn since T7181 was identified as **reflection** at T12813 (frost reflected). The prize at T14099 was a *spare* amulet of reflection. |
| Watch turned hostile | 14427 | Minetown | Batched `F6F6` killed a rock mole; a peaceful watchman stepped in and was hit. |
| Quest portal message | 15015 | D11 | XL9, too low for the quest. |
| Remote game froze | 15474 | D12 | Recovered through reconnect and `r` Resume last save (§7). |
| Magic lamp, but no wish | 16234 | D14 | Blessed lamp rubbed; the djinni said "It is about time!" and vanished. |
| **First wish** | 16678 | D15 | Engrave-testing an unidentified pine wand of wishing granted a wish: gray dragon scale mail (asked for blessed +2, got +0). The next zap (T16687) showed the wand was empty. |
| Genocide | 18045 | | Blessed genocide of class `L`. |
| Luckstone bought, Excalibur +2 | ~20082 | D23 shop | The shop identified the wishing wand as (0:0). |
| **Pet drowned by the hero** | 20546 | D25 Medusa (variant 4) | The hero stood on water in water walking boots and stepped onto the pet Relay on land, which **swapped Relay into the water**. Result: god anger 1, alignment −15, prayer unsafe. |
| **Medusa** | 20721 | D25 | Killed by her own reflected gaze while the hero was blindfolded. |
| **Castle** | 21606–21873 | D29 | Arrived by falling through a D28 trapdoor. Drawbridge destroyed with striking from range (T21617). Blessed scroll of earth filled the moat (T21630). A soldier ignored Elbereth (HP44, T21659), so the hero read taming and tamed two xorns. **Wand of wishing in the NE tower chest (67,15)** at T21873 (details in §4.4). |
| Near-stoning | 21971–21975 | Castle | Olog-hai wielding a cockatrice corpse (see §3). |
| Minotaur ambush | 22017 | | HP 109→66. |
| God anger repaired | 22798 | | Sacrificed a red naga. |
| Reverse genocide for XP | 22826–22838 | | Cursed genocide of wraiths; the wraiths were eaten for XL12→15. |
| **Quest** | 23286–23804 | portal D11 19,14 | Accepted at XL15 (T23371). Wished for a blessed wand of death (T23677); one zap killed Lord Surtur (T23678). Walked into lava in Home 6 (T23682) and escaped with a teleport wand. Quest complete T23804. |
| Prayer too soon after a wish | 23916 | | Tyr anger 1, Luck −3, Wis 12→11. Atoned by sacrifice at T23940. |
| Permanent see invisible (not crowning) | 24120–24122 | D19 altar | The prayer at T24120 made holy water. It blessed a potion of see invisible, and quaffing it gave permanent see invisible. Run 1 was never crowned: its dumplog has no "Hand of Elbereth" line. |
| **Valley** | 24365 | D30 | Entered through the Castle trapdoor at 49,21. |
| Temple priest angered | 24632 | Valley | A force-attack batch hit the Moloch priest. |
| Demon lords | 25970 / 26375 / 26389 / 29915 | D34 / – / – / D43 | Asmodeus (lured onto the upstairs), Baalzebub, Juiblex, Orcus. |
| Wrested wish | 26008 | | The old wand P gave 2 blessed charging. |
| **Vlad** | 29475 (candles 29586) | tower levels 39–41, branch on D42 | Searched D37–42 because the range was misjudged. |
| **Wizard's tower** | 32809–32813 | entered via the fake-tower portal on D48 | Wizard killed with a death wand (T32809); Book taken (T32813). |
| Wrested wish | 33004 | | Castle wand: 3 blessed remove curse requested, 1 granted. |
| **Invocation** | 33169 | D52, vibrating square 22,23 | Succeeded. |
| Collapse | 33170–33302 | D52→D51 | Wizard resurrected and stole the Orb (T33172), Bell (T33186) and Book (T33235). "Double Trouble" (two Wizards) at T33185. **Cursed gloves pinned a levitation ring on**, so the hero could not descend or pick up items. |
| **Death** | 33302 | D51 11,29 | Turned to slime. The Sanctum was never entered. See §2.1. |

**XL / HP / AC progression, run 1**

| T | XL | max HP | AC |
|---|---|---|---|
| 569 | 1 | 18 | 6 |
| 1601 | 3 | 34 | −1 |
| 5260 | 6 | 60 | −2 |
| 7956 | 7 | 69 | −4 |
| 11313 | – | – | −10 (mithril coat bought for 320 zm at T11260, plus a robe) |
| 13113 | 8 | 79 | |
| 15292 | 10 | 100 | |
| 16687 | – | – | −12 (gray dragon scale mail from the wish) |
| 19446 | 11 | 112 | |
| 22838 | 15 | – | (via the reverse-genocided wraiths) |
| 23954 | – | 140 | −23 |
| 24567 | 17 | 154 | |
| 30258 | 18 | – | |
| 33286 | 18 | 165 (HP 148) | −19 |

### 1.3 Run 2 (Sep 8–9): death ray in the Castle

| Milestone | Turn | Where | Detail |
|---|---|---|---|
| Start | 1 | | Began 17:43 UTC. St18/02 Dx16 Co15 In8 Wi7 Ch9. |
| Kitten killed | 414 | D2 | Arrow trap. |
| Sokoban | 1497–5118 | entrance through a **hidden door** on D9 (a trapdoor had dropped the hero from D8) | Reading identify at T1517 identified the whole inventory. Soko1 T2117 (chameleon "Proteus" tamed), Soko2 T2881, Soko3 T3601 (sleep resistance T3629 from a Grey-elf; poison resistance T3712 from a black naga hatchling), Soko4 T4566 (lightning wand found under a boulder). A wraith drained a level (T4974). Proteus died around T5072–5093. **Prize: bag of holding** (T5118). The scare monster scroll crumbled when picked up. |
| Gelatinous cube | 5236–5243 | | The hero chased a fleeing cube; it turned and paralysed them. HP 64→33. Elbereth saved the run. |
| **Excalibur** | 5904 | D4 fountain | 12 dips in total: 8 at D9 (dried at T5519), 3 at D5 (dried and made pools), 1 at D4. |
| Mines / Minetown | 6226– | Minetown D7 (Tyr temple) | First prayer T6465. **Bought protection twice**: 3200 zm at T6471 and 3600 zm at T9504 (AC −7). Mines End D12 (Wine Cellar) luckstone T6971. Excalibur +4 at T7398. |
| Quest portal message | – | D14 | "Summoned by the Norn" (dumplog). |
| **Polymorph trap** | 10165 | D22 | The hero became a large mimic; the +3 elven mithril-coat was **destroyed**. The plan was to pray to restore hands. |
| Medusa | 10970–11137 | D23 | Entered blindfolded. Dug down to the D24 maze and came back up blind. **Killed with 5 Excalibur hits while blind** (T11137). Perseus' statue held only rocks. |
| Fire resistance | 11032 | D24 | Red naga corpse. |
| Level teleporter | 11161 | D24→D12 | Separated from the pets. Prayer T11279 (success). |
| **Castle** | 11658– | D25 | A hole on D23 dropped the hero **two** levels into the Castle maze. A scare monster scroll was dropped on the Castle upstairs as a **permanent ward** (T11867; it repels minotaurs, unlike Elbereth). Scroll of earth filled the moat (T11924). The last striking charge was wrested to destroy the gate (T12026). All three liches killed (demilich T12134). A sergeant's lightning did 24 HP and blinded the hero (T12211). |
| **Death** | 12271 | D25 Castle central hall 32,21 | See §2.2. |

**XL / HP / AC progression, run 2**

| T | XL | max HP | AC |
|---|---|---|---|
| 4566 | 8 | 77 | −2 |
| 5523 | 8 | 75 | −1 |
| 6582 | 8 | 80 | −3 |
| 9504 | – | – | −7 (second protection purchase) |
| 10149 | 10 | 92 (as a human) | mithril lost at T10165 |
| 11294 | 10 | 92 | −5 (+0 elven mithril-coat worn T11287) |
| 11938 | 11 | 100 | −5 |
| 12271 | 11 | 100 | −5 |

### 1.4 Run 3 (Sep 9–21): ascension

The stated strategy at the start of `run-3.md` was:

> *"secure early armor and food, keep the pet alive, identify escape resources, and complete Sokoban. Do not attempt the Castle without known magic resistance or reflection; prefer both. Healing and a high HP total do not protect from instant death. Avoid lining up with unknown wand users. Every combat action is individually reviewed; safe movement batches use guards... Preserve all failures."*

| Milestone | Turn | Where | Detail |
|---|---|---|---|
| Start | 1 | D1 | Created 14:27 UTC Sep 9. St17 Dx9 Co20 In10 Wi9 Ch10, HP18, AC6. Little dog; oil lamp. |
| Mines | 631 | Mines branch D3; Mines 1 = Dlvl4 | XL3. |
| **Minetown** | ~1436–1503 | D6 | Neutral altar (Odin); no co-aligned priest. **Bought a magic marker for 67 zm** at the hardware store (T1503). |
| Telepathy | 2118 | | Floating eye. |
| Error: zapped the pet | 2606 | | After aborting an engrave-test, zapped the unknown wand (striking) into the pet dog. |
| Elbereth written with the marker | 2725 | | |
| Poison resistance; XL6 | 2977 | | |
| **Bones #1** | 3282 | D7 | "Jamiro" (Val-Hum-Fem-Law, killed by a giant spider). Ghost; weapons and armor looted. |
| Speed (XL7) | 3812 | | |
| Scare monster crumbled | 3823 | | A price-check drop and re-pick. |
| Oracle fountains exhausted | 4081 | D9 | 18 dips; all 4 fountains dried. |
| Empty-wand error | 4214 | | `zI8` got "Nothing happens" and the `8` became a melee attack. |
| **Excalibur** | 4532 | D10 fountain | The 27th dip overall ("blessed rustproof +2"). |
| **Sokoban** | 5085–7967 | entrance D10 70,18; Soko1b = Dlvl9 | Levels solved T5085, T5721, T6216, T7523. **Prize: amulet of reflection, worn** (T7967). |
| Pets lost | 7842, ~8002 | | Pony killed by a soldier ant; the dog killed by a rock piercer while the hero rested. Logged as an error. |
| Fire resistance | 8298 | | |
| **Mines End** | ~9633–10001 | D12 (Mimic of the Mines) | Sleep resistance (T9633). Gray stone kick-tested as a loadstone (T9945). **Luckstone** (T10001). |
| Pet polymorphed | 10089 | | A dog ate a chameleon and became an iron golem. |
| First prayer | 11568–11577 | D14 lawful altar | Holy water, blessed the marker, wrote identify. |
| Quest portal | 11731 | D15 47,27 | |
| **Death ray reflected** | 11892 | | A sergeant's death ray was **reflected by the amulet**. The hero then took the wand of death. |
| User pause | 12025 | D18 (Rogue level) | Sep 10 11:56 UTC to Sep 13 12:15 UTC. |
| Wand IDs | 12762 | | Death (0:1), teleportation (0:6), locking (0:5). |
| Scrolls burned | 12912 | | A delayed blindfold let a pyrolisk burn scrolls. |
| Level teleport trap | 13146 | D25→D4 | |
| Second prayer | 13565 | D14 | Holy water. |
| **Medusa** | 14133–14235 | D27 (tree variant) | Cold wand ice bridge (T14138); scroll of earth to fill water (T14211); ravens blinded the hero repeatedly (17 ravens killed); crossed by jumping. Medusa fled downstairs; the hero followed and **killed her on the Castle upstairs (D28) with 6 Excalibur hits in total**, blindfolded and wearing reflection. |
| **Castle retreat** | 14240 | D28 | A hasted arch-lich waited at the upstairs. *"NO MR: immediately RETREATED... DO NOT DESCEND CASTLE until magic resistance/genocide/credible protection."* |
| Scare monster written | 14330 | | Blessed scare monster written from its label. |
| **Bones #2** | 14734 | D23 | "deathdruid" (Arc-Dwa-Mal-Law, fell into a spiked pit). **Blessed bag of holding**, Grayswandir, stethoscope, pick-axe, unicorn horn, and 6 holy waters inside the bag. Silver dragon scales left behind because of weight. |
| Armor bought | 15761 | | +4 ring mail, AC −5. |
| Free action | 16566 | | Ring identified and worn. Levitation and polymorph rings identified at T16813. |
| Charging identified | 20802 | | Marker recharged to (1:50). Rings of polymorph control, conflict, stealth and aggravate monster identified at T20807. |
| Own-race polymorph experiments | 21292, 21310 | | Controlled polymorph into own race cost XL12→10→8 (HP91). Abandoned. |
| Luck and genocide attempts | 21772–21884 | | Gems thrown to unicorns for Luck. Two attempts to write genocide failed (type unknown to the hero). |
| SSH drop | 22734 | D14 | Sep 14 03:44:41 UTC. Recovered with `p` from the lobby (stale process) in 9 s at the exact turn. |
| Excalibur +3 | 23020 | | |
| **Gray dragon plan** | 24841–25505 | D27/D28 | Stripped armor, then ring of polymorph plus polymorph control gave **gray dragon form (MR)**. Arch-lich destroyed (T24854); its cold touch shattered 2 extra healing potions and its death spell failed. Natural reversion at T25492 (651 turns); re-equipped at T25505. |
| **Castle entry** | 25580–25906 | D28 | Levitated over the north moat (sharks took 36 HP). Entered by the back door 65,21 over the rear trapdoors. Ring of conflict in the court. Cancellation used on a disenchanter and a lich. |
| **Wand of wishing** | 25889 | NW tower chest 13,15 | The NE tower 67,15 was empty (verified T25840). |
| **Wishes 1–5** | 25891–25915 | | +3 GDSM (T25891); 2 blessed charging (T25906); speed boots (T25907, +0); the wand recharged to (1:3) (T25912); 2 blessed genocide, 1 granted, `L` genocided (T25913); blessed magic marker (T25914). |
| Error: angered a naga | 26038 | | Jumped into an invisible peaceful naga. The stethoscope got cursed. |
| **Drawbridge tune** | 26106 | | Mastermind with a harp found passtune **CBADD**; opened from 16,21. |
| Enchant weapon | 26427–26921 | | Cancelled a junk pile into blank scrolls and water; prayer (T26430) blessed the water; wrote enchant weapon. **Excalibur +4, +5, then +6** (T26921): *"NEVER ENCHANT EXCAL AGAIN."* |
| **Valley** | 26768 | D29 | Through the Castle trapdoor 49,21. |
| User pause | 26955 | D29 | Sep 14 11:54 UTC to Sep 20 15:10 UTC. A vampire lord was adjacent at the save. |
| SSH drop | 26986 | | Sep 20 15:47:46 UTC, during a sandbox-approval wait; presumed idle timeout. Exact restore. |
| Disintegration resistance | 27222 | | Black dragon. |
| **Wish 6** | 27772 | D32 | 3 blessed potions of gain level, all granted: **XL13→16**. |
| **Quest** | 28330–28652 | portal D15 | Entered T28330 (guard patched for `Home N`); accepted T28350. **Lord Surtur** killed about T28509 (sleep wand plus Excalibur). Bell taken T28513. SSH died at 20:17:18 UTC with a menu open; exact restore at T28520. **Orb** picked up at T28530–28532. Quest complete T28652. |
| Shock resistance | 29369 | | From a blue dragon statue that animated. |
| **Juiblex** | 29410–29414 | | His engulf caused terminal illness; the unicorn horn failed once and then cured it. Dug out; Juiblex killed. |
| Vlad range corrected | 30362 | | "D37–41". |
| Speed lost | 31089 | | A shade removed intrinsic speed (speed boots still worn). |
| **Vlad's Tower** | 31264–31870 | branch D41 5,21 | Amulet of life saving from a chest (T31340). **Crisis T31456–31473** (see §3). Yeenoghu killed T31532. **Vlad killed T31701** (thrown paralysis potion plus 7 Excalibur hits); Candelabrum; 7 candles attached T31870. |
| **Bones #3** | 32179 | D44 | "Jamiro" again (Val-Hum-Fem-Law, touch of death). Wands of death and teleportation, a **cursed magic lamp**, reflection amulets, polymorph control. |
| Second life-saving amulet | 33155 | | |
| **Wizard's tower** | 33206–33451 | D47 decoy; D49 fake-tower portal 39,21 leads into the tower (D45) | Wizard killed with the death wand (T33440); Book taken (T33451). |
| Curse repaired | 33633–33816 | | The Wizard cursed the gloves; remove curse written with the marker and read (T33816). |
| **Invocation** | 33792–33794 | D51 45,19 | "You feel a strange vibration under your feet" (T33792). Invocation T33794. Second Wizard kill T33806. |
| **Sanctum** | 33882–33947 | D52 | High priest of Moloch killed with a death ray (T33882). **Genuine Amulet** taken (T33887). Out of the Sanctum at T33947. |
| **Ascent** | 33947–36680 | D51→D1 | Invocation items cached on D42 (T34460). **11 "mysterious force" setbacks** (T34116–35436). Wizard killed a 3rd, 4th, 5th and 6th time (T34777, T35158, T35634, T36017). Orcus (T34772), Geryon (T35338) and Asmodeus (T35728) killed. |
| **Crowning** | 36363 | D14 altar 13,13 | "Hand of Elbereth". The same prayer blessed 4 waters. |
| Lamp wish and upgrades | 36369–36625 | | Magic-lamp djinni: 3 blessed enchant armor requested, 1 granted (T36369). A second lamp's djinni was peaceful and gave no wish (T36374). Gloves +3, AC −9 (T36386). Death wand recharged (T36387). Full healing bought in the D4 shop (T36625). |
| **Earth** | 36680–36747 | | Wizard killed a 7th time on arrival (T36681; plane parser patched here). The Orb found the portal (T36690). |
| **Air** | 36747–36803 | | The Orb found the portal (T36782). |
| **Fire** | 36803–37002 | | Smoke blocks line of sight and the Orb was empty. **Wrest succeeded on attempt 23** (T36984): 3 blessed charging, all granted. Orb recharged; portal found (T36995). |
| **Water** | 37002–37105 | | Rode the air bubbles. Orb failures forced a second recharge (T37053). Portal entered T37105. |
| **Astral** | 37106–37140 | | Guardian angel granted (conflict off). Riders identified. Full healing T37116. Pestilence and 2 Moloch priests killed with a death ray (T37125); HP fell to 3. Then the **lawful altar at 10,20** (§4.17). **Ascended T37140.** |

**XL / HP / AC progression, run 3**

| T | XL | max HP | AC | Note |
|---|---|---|---|---|
| 1 | 1 | 18 | 6 | |
| 360 | 2 | | | |
| 631 | 3 | 41 | | |
| 1243 | 4 | 53 | | |
| 1458 | | | −2 | |
| 1670 | 5 | 66 | | |
| 2977 | 6 | 72 | | |
| 3812 | 7 | 82 | | speed |
| 4551 | 8 | 94 | | |
| 6481 | 9 | 106 | | |
| 9077 | 10 | 118 | | |
| 14155 | 11 | 126 | | |
| 15761 | | | −5 | +4 ring mail |
| 17574 | 12 | 134 | | |
| 21292 / 21310 | 10 → 8 | 91 | | own-race polymorph losses |
| 22426 | 10 | 116 | | |
| 25670 | 11 | 124 | | |
| 25904 | | | −10 | GDSM |
| 26780 | 12 | 132 | | |
| 27772 | 16 | 164 | | 3 gain level potions |
| 33841 | 17 | 176 | −6 | armor burned |
| 34028 | 18 | 184 | | |
| 36386 | | | −9 | gloves +3 |
| 36415 | 19 | 192 | | |
| 37116 | 19 | 200 | | blessed full healing |
| 37140 | 19 | 200 (HP 35) | −9 | ascended |

---

## 2. Deaths

There are two deaths. Run 0 was a deliberate quit.

### 2.1 Run 1: turned to slime on D51, T33302 (XL18, max HP 165)

#### Circumstances

The final summary in `live-run.md` reads:

> "Invocation completed, maximum dungeon level52; Sanctum never entered. Hero died11,29 D51. Baluchitherium killed33292; green slime killed33295-ish, but sliming began during an unsafe 24-key movement batch near known slime. At33297 Slime status recognized; attempted zh. but h was EMPTY, and the spare period spent time. Then removing robe/GDSM consumed the remaining turns. CRITICAL CORRECTION verified zap.c lines2249-2255: SELF-ZAPPING POLYMORPH IGNORES MAGIC RESISTANCE. Could have used zY. immediately in GDSM (gray dragon) without removing armor; charged Y1:6 remained."

The dumplog's final messages confirm the sequence:

- *"The green slime touches you! You don't feel very well."*
- The hero killed the slime.
- *"What do you want to zap? … Nothing happens."* The fire wand was h (0:0).
- The invisible Wizard of Yendor kept hitting and cursing.
- *"What do you want to take off?"* The hero removed the robe.
- *"You have become a green slime."*

The final inventory still held **Y, an uncursed wand of polymorph (1:6)**. It also held a blessed potion of extra healing, and wands of cold (0:1), lightning (0:1), magic missile (0:7) and teleportation (0:4, 0:1, 0:4).

The situation before the fatal minutes (T33170–33300):

- The Wizard had resurrected after the invocation and stolen the Orb, Bell and Book.
- There were two Wizards ("Double Trouble", T33185).
- Wizard curses had cursed the gloves. That made the worn **levitation ring impossible to remove**, so the hero could not go down stairs or pick anything up.
- Every uncursing resource was used up: *"No holy water, remove curse, charging or wishing remain."*
- The plan was to walk to a D50 magic trap and hope to uncurse. That walk went through a corridor next to a known green slime.

#### Root causes

- **Tactical.** A raw 24-key movement batch next to a known slimer; an empty fire wand was tried first; turns were spent removing armor.
- **Strategic.**
  - No verified sliming cure was held before Gehennom. Their own lesson: *"VERIFY usable fire charges before Gehennom"*.
  - No uncursing reserve was kept for the Wizard's curses.
  - A levitation ring was worn in the Wizard fight. Their lesson: *"do not wear levitation during Wizard fight if avoidable"*.
- **Knowledge.** A false belief that magic resistance (from the gray dragon scale mail) would block a self-zapped polymorph. The source disproves this. [MECH] Prayer, the usual sliming cure, is useless in Gehennom, which made the polymorph wand the key resource.
- **Harness.** Movement batches in run 1 were raw. The guarded walker (`guard.walk`) was only added for run 2. Nothing stopped input when the `Slime` status appeared.

#### What would have prevented it

1. A guarded walker that refuses to start or continue with a hostile within 2 squares, and stops on any new status such as `Slime`. This was implemented for run 2.
2. An **emergency-cures inventory** that is checked before Gehennom, listing sliming cures (fire with known charges, a polymorph wand or potion, a scroll of fire) and stoning cures. Run 2's emergency JSON added `sliming_cures` and `stoning_cures` fields for exactly this reason.
3. Knowing in advance that a self-zapped polymorph cures sliming even with MR.
4. Keeping a remove-curse or holy-water reserve through the Wizard fight, and taking off levitation-type rings before stepping into range of the Wizard's curses.

### 2.2 Run 2: killed by a death ray in the Castle, T12271 (XL11, HP 100/100)

#### Circumstances

From `run-2.md` (FINAL):

> "Killed instantly at full HP100/100 by a sergeant's wand of death in the Castle central hallway, hero32,21. XL11/18092, AC-5. No ascension. The guarded eastward batch sent three steps, then stopped at the death prompt. A visible-state movement guard cannot guarantee protection from a one-hit kill. The strategic error was advancing through the Castle without known magic resistance or reflection. Require at least one before another Castle attempt; prefer both for broader protection."

Postmortem details:

- The worn amulet was magical breathing.
- The bag held 2 full healing and 2 extra healing potions, which *"would not prevent this instantaneous death ray."*
- Zero wishes had been used.
- The dumplog's last messages: the hero removed the blindfold after telepathically farlooking the throne room, then *"The sergeant zaps a uranium wand! The death ray hits you!"*

60 turns earlier (T12211), another sergeant's **lightning** had hit for 24 HP and blinded the hero. The run-2 JSON entry `newest_12213` warns: *"DO NOT realign row21/diagonal casually; no SHOCKRES/reflection/MR known."* The hero was then killed while walking along row 21 of the central hallway.

The dumplog inventory shows an **uncursed ring of conflict** and **green dragon scales** (poison resistance only) in the bag.

#### Root causes

- **Strategic (primary).** Entering the Castle with neither MR nor reflection. Run 2's Sokoban prize was a bag of holding, not reflection. No gray or silver dragon source was reached; gray dragons were seen in the Castle, but *"GraySCALESpossibleMR NOTobtained"*.
- **Tactical.**
  - Walking the long straight central hall, a firing lane, while soldiers with wands were known to be present (lightning at T12211).
  - Taking the blindfold off, giving up the safe telepathic view, and then advancing.
  - Conflict was available and not used. [SPEC] Conflict would have turned the soldiers on each other, as run 3 did in the court.
- **Harness/perception.** The guard only reasons about the visible 5×5 neighbourhood. It cannot see a wand user in a lit hall or around a doorway, and it cannot rule out an instant kill.

#### What would have prevented it

1. The rule adopted for run 3: **no Castle without MR or reflection; prefer both.**
2. [SPEC] If entering anyway: approach the wand from the rear or the moat side, as run 3 did, avoiding the central hall and the barracks. Put on conflict before contact. Never stand in line with an unidentified `@` more than 1 square away.

### 2.3 Common thread

Both deaths were **not HP deaths**:

- Sliming: 10 turns of warning, but only a few specific items can cure it.
- A death ray: zero warning.

HP bars, healing potions and "HP below 2/3" guards did not help. Both runs had plenty of healing. What was missing was:

1. a precomputed "instadeath checklist": for each class (death ray, disintegration, stoning, sliming, strangling, drowning, level drain), which intrinsic or item protects and which item cures;
2. a harness that stops multi-step actions the moment any of those conditions appears.

---

## 3. Near-death and crisis moments

The rule column is the general lesson. Turn numbers are from the journals.

### 3.1 Run 1

| T | What happened | How survived | Rule |
|---|---|---|---|
| 1241 | A gas spore mistaken for a floating eye exploded; HP 7. | Luck. | Farlook (`;`) every unfamiliar or ambiguous glyph before melee. |
| 4324, 5161, 6010 | Weak from hunger. | Prayer (all worked). | Prayer is a hunger fix early on, if the timeout is likely low. Better: carry food and track the last prayer turn. |
| 14427 | `F6F6` killed a rock mole; then *"peaceful watchman stepped into second forceattack!"* The whole Watch turned hostile. | Withdrew from Minetown without killing any guards. | **Never batch force-fights.** One `F` per inspected screen. |
| 15474 | The remote game froze (§7). | Reconnect and resume at the same turn. | A frozen screen is a transport problem until proven otherwise. Do not start a new game. |
| 16172 | *"batched farlook+F4 hit PEACEFUL TENGU"*. | Disengaged. | The same rule. |
| 20546 | *"hero74,18water moved6 ontoRelay75,18land, swappedRelayintowater... You drown Relay."* Result: anger 1, −15 alignment, prayer unsafe. | Sacrificed a red naga at T22798. | **Never swap a pet into water or lava.** With water walking or levitation, you can stand where the pet cannot. |
| 21659 | A soldier ignored Elbereth in the Castle; HP 44. | Read taming and tamed two xorns. | Elbereth does not stop `@` humans or minotaurs (their note; [MECH] monmove.c `onscary`). Keep a non-Elbereth answer. |
| 21971–21975 | An Olog-hai wielding a **cockatrice corpse** hit the hero *during a 3-attack batch*, and stoning started (*"3attackbatch caused stiffening"*). | Ate a lizard; was re-infected; **polymorphed the Olog-hai into a green slime** (!), ate a lizard again, killed the slime with fire. | Carry 2+ lizard corpses. Kill cockatrice-wielders at range. Polymorphing an enemy can create a worse enemy. |
| 22017 | Minotaur ambush in the Castle maze; HP 109→66. | Fought and retreated. | Castle mazes hold minotaurs. Elbereth does not work on them; a scare monster scroll does. |
| 22842 | Engraved on an altar: Wis −1, alignment −1. | – | Never engrave on altars. |
| 23682 | On quest Home 6, walked into **lava** after misreading `}` from the visual spacing. | Teleport wand (T23685). | *"ALWAYS Pg BEFORE moving after landing, never assume floor by visual spacing. Use Map features for '}'."* (`Pg` = put on ring g, levitation.) |
| 23916 | Prayed too soon after a wish: Tyr anger 1, Luck −3, Wis 12→11. | Atoned by sacrifice at T23940. | Wishes add 50–149 to the prayer timeout (makewish, zap.c ~5098). Track it. |
| 24632 | *"Forceattack batch killed giant zombie E, then PRIEST STEPPED IN and got hit."* The Moloch priest turned hostile. | – | *"NO MORE forceattack batches NEAR PEACEFULS."* |
| 33170–33302 | Post-invocation collapse. | Did not survive. | See §2.1. |

### 3.2 Run 2

| T | What happened | How survived | Rule |
|---|---|---|---|
| 414 | The kitten died to an arrow trap. | – | Pets die to traps too. Mark traps. |
| 3055 | An Elbereth macro (`E-Elbereth…`) was sent while a loot popup was open. The keys landed in an eating prompt. | Recovered. | **Multi-key input only at a recognised map prompt** (became `command_preflight`). |
| 4974 | A wraith drained a level. | – | Kill wraiths fast; eat the corpse for a level. |
| 5236–5243 | Followed a fleeing gelatinous cube; it turned and **paralysed** the hero. HP 64→33. | Elbereth. | Never chase engulfers or paralysers into melee without free action. |
| 6563 | cmdassist "Invalid direction key" popup. | Escape, Ctrl-R, then separate keys. | Popups swallow keys. Check the prompt before every key. |
| 6698 | *"zV attempt Nothing happens… queued4 became MOVE swapped Toffee"*. A mountain centaur was adjacent. | Nothing worse happened. | **Send the zap and the direction as separate, verified inputs.** |
| 10165 | Polymorph trap: became a large mimic; the +3 elven mithril-coat was destroyed. | Planned prayer; replaced the armor at T11287. | Before MR, avoid unknown `^`. Polymorph traps can destroy body armor and leave you without hands. |
| 11161 | Level teleporter D24→D12; pets left behind. | Walked back. | Identify traps (`^`) before stepping on unknown ones in the deep dungeon. |
| 11669 | A minotaur hit for 39 HP in the Castle maze. | The expensive camera blinded it. | A camera and a scare monster ward are good against minotaurs. |
| 12211 | A sergeant's lightning did 24 HP and blinded the hero. | Unicorn horn; moved off the line. | Soldiers carry attack wands. Stay off their lines. |
| 12271 | Death ray. | Died. | §2.2. |

### 3.3 Run 3 (the winning run's close calls)

| T | What happened | How survived | Rule |
|---|---|---|---|
| 2606 | Aborted an engrave-test and then zapped the unknown wand (striking) **into the pet**. | The dog survived. | Engrave-test cleanly. Never zap unknown wands toward pets. |
| 4214 | `zI8` on an empty wand; `8` became a melee attack. | No harm. | As in run 2. |
| 7653–7654 | In Soko4, an unseen heavy attacker (likely a giant zombie) took 29 HP; lowest HP 43/106. | Disengaged north and healed. | Retreat from unseen damage. |
| 7842, ~8002 | Pony killed by a soldier ant; dog killed by a rock piercer while the hero rested. | – | Resting next to unresolved threats kills pets. |
| 11892 | A **sergeant's death ray was reflected** by the amulet. | Reflection (the Sokoban prize). | Get reflection before D20. |
| 12912 | A delayed blindfold let a pyrolisk burn scrolls. | – | Blindfold before gaze monsters come into view. |
| 13146 | Level teleport trap, D25→D4. | Walked back down. | Mark and avoid known `^`. |
| 14240 | A hasted arch-lich was waiting at the Castle upstairs. | **Immediate retreat.** | Without MR, a Castle arch-lich is a stop sign. |
| 21292, 21310 | Own-race controlled polymorph experiments cost 4 XL (12→8). | Abandoned. | Controlled self-polymorph into your own race is a "new man" roll (±2 XL each time). Don't. |
| 24841–25505 | Gray dragon form: no container access. The arch-lich's cold touch shattered 2 extra healing potions. | Won; waited out the form in a locked room. | Plan the form's duration (they computed min 333 turns and retreated early). Pack everything first. |
| 25580–25906 | Sharks took 36 HP while the hero levitated over the moat. | Kept moving. | Levitation does not protect from eels and sharks next to the moat edge. |
| 26038 | Jumped into an invisible peaceful naga; it was angered. | – | Clear landing squares (stethoscope or farlook) before `#jump`. |
| 29410–29414 | Juiblex's engulf gave **terminal illness**. The unicorn horn failed once, then cured it. | Horn, then dug out. | Carry a unicorn horn. Apply repeatedly. |
| 31089 | A shade's touch removed intrinsic speed. | Speed boots. | Keep extrinsic backups of key intrinsics. |
| 31456–31473 | **Vlad plus a minotaur** (min HP 68), then a teleport landed the hero between a fire ant and a second minotaur (HP 58/168). The sleep wand was empty. | **Wore life saving (T31458)**, teleported self with the last charge (T31472), then **invoked the Orb of Fate for a level teleport** (T31473) to D40. Recovered to full at D39. | Put on life saving *before* the boss fight. Keep two escape items, because the first may be empty. The quest artifact's invoke is an emergency escape. |
| 31473–31535 | Orcus zapped a death wand at least 6 times. | **MR (GDSM)**: *"Deathray hit hero31477: explicitly unaffected, MR confirmed."* | MR is the Gehennom entry ticket. |
| 31715–31724 | Falling-rock traps hit the hero, but regeneration hid the net HP loss, so the batch did not stop. | Harness fix (falling-rock message count). | Detect damage from messages, not only HP deltas. |
| 32778 | `aR9` while **deaf**: no direction prompt appeared, and `9` became an attack on a hostile flesh golem (4 HP lost). | – | *"when impaired send aR THEN direction only after prompt."* |
| 33225 | Sent `10s` meaning "search 10"; under number_pad `1` became a SW move and `0` opened inventory. | Escaped with no harm. | With number_pad on, a count needs the `n` prefix (`n10s`). |
| 33633 | The Wizard cursed the gloves. | Wrote remove curse with the magic marker (T33816). | Keep marker ink and a blank scroll, or holy water, for exactly this. |
| 34116–35436 | 11 "mysterious force" setbacks while carrying the Amulet up. | Persistence. | Budget the turns. Keep going. |
| 36842 | Pressed Esc at `>>`/--More-- intending to stop a `g`/travel run; the run continued. | No damage. | Esc at a more-prompt does not cancel a run already in motion. |
| 37121–37126 | **Astral:** Pestilence gave terminal illness plus stun, twice. The death wands were empty until the last blessed charging was read (T37123). The first death ray missed (T37124); the second killed Pestilence and 2 Moloch priests (T37125). HP fell to 4, then 3. | Unicorn horn; full healing had been drunk at T37116; the wand of death. Life saving was worn and not used. | Arrive on Astral at full HP with life saving worn, a verified-charged death wand, full healing and a unicorn horn. |
| 37132 | A third teleport-wand zap angered a **peaceful Angel of Tyr** (collateral). | Pressed on to the altar. | Rays and beams hit everything on the line. Check the whole line on Astral. |

**Overall pattern.** Almost every non-lethal crisis in run 3 was survived with a pre-positioned resource:

- reflection, MR, life saving already worn;
- a second escape (a teleport wand, then the Orb);
- a unicorn horn;
- a marker plus blank scroll for remove curse.

Run 3's journals track these as named reserves with *"never recharge"*, *"never bag"* or *"READY"* annotations.

---

## 4. Winning strategy (run 3)

### 4.1 Shape of the game

Run 3 followed a conservative order:

1. Mines to Minetown, where a magic marker was bought early.
2. Oracle and Excalibur.
3. Sokoban, for the amulet of reflection.
4. Mines End luckstone.
5. A long, careful midgame (D14–D27) that gathered IDs, rings and bones loot.
6. **Refused the Castle until it had MR**, and got MR without a wish by polymorphing into a gray dragon.
7. Wishes on permanent defences, then gain level to open the quest.
8. Quest.
9. Gehennom, in the order: Juiblex, Vlad's Tower, the Wizard's tower, the invocation.
10. Ascent, crowning, a final upgrade pass, the Planes, Astral.

The run used about 37k turns. Roughly T25900–T28650 (Castle wishes to quest complete) was the pivot from "careful explorer" to "overpowered".

### 4.2 Intrinsics and properties: when and how they were obtained

| Property | Source | T |
|---|---|---|
| Cold resistance, stealth, infravision | Dwarven Valkyrie start | 1 |
| Telepathy | Floating eye corpse | 2118 |
| Poison resistance | Fresh snake corpse, "You feel healthy" | 2940 (noted T2977) |
| Speed (intrinsic) | XL7 | 3812. Lost to a shade at T31089; speed boots covered it. |
| Drain resistance, auto-search | Excalibur (wielded) | 4532 |
| **Reflection** | Sokoban amulet | 7967. Worn until life saving took the slot (T31458 in Vlad's Tower; T37012 on Water/Astral). |
| Fire resistance | Red naga corpse, "You feel a momentary chill" | 8298 |
| Sleep resistance | Green-elf corpse, "You feel wide awake" | 9633 |
| Luck | Luckstone (Mines End) | 10001, plus unicorn gems (T21772–21884) |
| Free action | Ring | 16566 |
| **Magic resistance** | Temporary: gray dragon form (T24841–25492). Permanent: **+3 GDSM wish** (T25891). | |
| Very fast | Speed boots (wish) | 25907 |
| Displacement | Cloak of displacement | worn most of the midgame |
| Disintegration resistance | Black dragon corpse | 27222 |
| Shock resistance | Blue dragon (animated statue) corpse | 29369 |
| Half physical and half spell damage, warning | Orb of Fate carried [MECH: quest artifact carry properties] | 28530 |
| Levitation (on demand) | Ring | identified T16813 |
| Conflict (on demand) | Ring | identified T20807 |
| See invisible | **Crowning** (T36363) [MECH: `gcrownu` grants see invisible] | 36363 |
| Life saving (spare x2) | Chest in Vlad's Tower (T31340); a second at T33155 | |

Final "attributes" block from the dumplog, verbatim list:

> the Hand of Elbereth; piously aligned; magic-protected; fire, cold, sleep, disintegration, shock, poison resistant; level-drain resistant; saw invisible; telepathic; warned; automatic searching; infravision; invisible to others; displaced; stealthy; warded; half physical damage; half spell damage; very fast; free action; life would have been saved; extremely lucky; extra luck; good luck did not time out.

### 4.3 Final kit (dumplog, abridged)

- **Wielded:** blessed rustproof +6 Excalibur.
- **Worn:**
  - blessed +3 gray dragon scale mail;
  - blessed fireproof +0 speed boots;
  - blessed +3 leather gloves (thoroughly burnt);
  - +3 small shield;
  - +0 cloak of displacement;
  - +0 elven leather helm;
  - Hawaiian shirt;
  - amulet of life saving;
  - ring of free action.
- **Carried:**
  - spare amulet of life saving and amulet of reflection;
  - rings of levitation and conflict;
  - wands of death (1:4), (1:0) and (0:0);
  - teleportation (0:3);
  - lightning (0:7);
  - cancellation (0:1);
  - fire (0:1);
  - Orb of Fate (2:4), recharged twice;
  - blessed unicorn horn, stethoscope, skeleton key, blindfold, lit blessed oil lamp, luckstone.
- **Bag of holding (56 items):**
  - +4 Grayswandir;
  - two blessed magic markers, (1:3) and (1:1);
  - magic harp;
  - rings of polymorph, polymorph control, teleport control, stealth and aggravate monster;
  - a potion of gain level;
  - scrolls of taming, earth, fire, teleportation and blank;
  - many spent wands;
  - a sack holding amulet of ESP, restore ability, and more.

**Left behind:** the Bell, Book and Candelabrum were cached on D42 after the invocation (T34460).

### 4.4 Wishes

**Run 3 (8 wishes, per the dumplog conduct):**

| # | T | Source | Request | Result |
|---|---|---|---|---|
| 1 | 25891 | Castle wand of wishing (NW tower chest 13,15) | blessed +3 gray dragon scale mail | +3 GDSM, blessed (dumplog). **Permanent MR.** |
| 2 | 25906 | same wand | 2 blessed scrolls of charging | 2 granted |
| 3 | 25907 | same wand | blessed fixed +3 speed boots | **+0**; blessed fireproof in the dumplog |
| – | 25912 | recharge | read blessed charging on the (empty) wishing wand | *"BLUE GLOW => 1:3 … NEVER RECHARGE AGAIN would explode"* |
| 4 | 25912–25913 | same wand | 2 blessed scrolls of genocide | **1** granted; read blessed, class `L` (lich, demilich, master lich, arch-lich) |
| 5 | 25914 | same wand | blessed magic marker | (0:35) when identified |
| 6 | 27772 | same wand (last charge) | 3 blessed potions of gain level | 3 granted: XL13→14→15→16, unlocking the quest |
| 7 | 36369 | djinni from a bones magic lamp (cursed; blessed with holy water from the crowning prayer; rubbed 8 times) | 3 blessed scrolls of enchant armor | **1** granted: gloves to +3, AC −9 |
| 8 | 36984 | **wrested** from the (1:0) wishing wand on the Plane of Fire, attempt 23 | 3 blessed scrolls of charging | 3 granted: Orb recharged twice, the death wand once |

**Run 1 (11 wishes):**

- GDSM (T16678, from engrave-testing a random D15 wand of wishing; +2 requested, +0 given).
- From the Castle wand (and the recharged old wand):
  - 2 blessed charging;
  - speed boots (+0);
  - blessed greased bag of holding;
  - blessed ring of levitation (T22851);
  - ring of free action (T23407);
  - blessed wand of death (T23677);
  - magic marker (T23904);
  - 3 blessed enchant armor (T23941, 1 granted).
- Two wrested wishes:
  - 2 blessed charging (T26008);
  - 3 blessed remove curse (T33004, 1 granted).

**Observations about wish outcomes**

- Enchantment requests often came back as +0: speed boots twice, GDSM once.
- Quantity requests were granted sometimes: 2 charging yes, 2 genocide no, 3 gain level yes, 3 enchant armor no (twice), 3 charging yes, 3 remove curse no.
- [MECH] In 3.6 `readobjnam`, a requested count `n > 1` is honoured only if `n < rnd(6)`: 2/3 for 2 and 1/2 for 3. A requested enchantment `s` is zeroed if `s > rnd(5)`: kept 80% of the time for +2 and 60% for +3. Plan wishes around expected values.
- Wish order in run 3 was **MR first**, then **charging** (to double the wand), then mobility, then **genocide of L**, then **marker** (flexible scrolls), then **XP**.
- They never wished for artifacts (conduct: "You did not wish for any artifacts").
- They explicitly planned to "preserve one emergency" wish; the reserve was eventually spent on gain level.

### 4.5 Genocides

- **Run 3:** one blessed genocide, class `L`, at T25913. The erinyes also show as extinct in the dumplog. [MECH] That is the birth limit (3) being reached, not a genocide.
- **Run 1:** blessed `L` at T18045. Also a **cursed (reverse) genocide of wraiths** at T22826; eating the resulting wraiths gave XL12→15.
- **Run 2:** none.

`L` is the obvious choice for a melee Valkyrie. Arch-liches guard the Castle entrance, and master and arch-liches cast destroy armor, curse items and touch of death. Run 3 had to beat a Castle arch-lich *before* it could wish, which is why it genocided `L` immediately after.

### 4.6 Prayer

Run 3 prayed only **four times** in 37,140 turns (journal):

1. **T11568:** first prayer, at the D14 co-aligned altar, to make holy water.
2. **T13565:** holy water; blue glow.
3. **T26430:** blessed water for writing enchant weapon.
4. **T36363:** crowning ("Hand of Elbereth"); blessed 4 waters at the same time.

It **never prayed in Gehennom** (*"No prayer Gehennom"*), tracked the last prayer turn in every snapshot, and treated `prayer timeout ≈ unknown` as unsafe.

Run 1 prayed more (T4324, T5161, T6010, T6900, T8286, T10627, T16232, T23916 (failed: too soon after a wish), T24120). Run 2 prayed at T6465, T9493 and T11279.

### 4.7 Elbereth and scare monster

**Counts (dumplog conduct):** 10 (run 1), 26 (run 2), 21 (run 3).

**How they used them**

- Dust Elbereth as an emergency rest spot.
- Semi-permanent Elbereth written with the magic marker (T2725, T4520).
- Burned Elbereth with fire or lightning wands.
- Explicitly *"do NOT attack from ward"*.

**Limits they recorded:**

- Elbereth does not affect `@` humans or minotaurs (a soldier ignored it at T21659 in run 1).
- A **scare monster scroll on the floor *does* repel minotaurs** (*"Floor ward repels MINOTAURS per official monmove.c 147 unlike Elbereth"*, run 2 T11867).
- Neither stops ranged attacks.
- A scare monster scroll crumbles on the second pickup (pickup.c 1423–1436). This bit them in run 2 (T5118) and run 3 (T3823). Run 2 therefore **dropped a scare monster scroll on the Castle upstairs as a permanent ward** and never picked it up.
- The Castle's wand-of-wishing chest square already holds a cursed scare monster scroll and a burned Elbereth. Both runs noted these and left them *"UNTOUCHED NEVER pick"*.

### 4.8 Pets

Pets mattered early and not late.

**Run 3**

- Little dog (start), a tamed pony (T5022), a horse (T4551), and a second little dog (T5487), with up to 5 pets at once in the Sokoban period.
- The pony and the first dog died around T7842–8002.
- A pet dog ate a chameleon corpse and became an iron golem (T10089).
- No pet reached the endgame.

**Pet-related disasters in run 1**

- The chameleon pet killed the Minetown **temple priest** (T10602).
- The hero **drowned a pet** by swapping it into water (T20546): god anger and −15 alignment.

**Harness support for pets**

- `wait-pets` (bounded search until the `f` and `u` pet glyphs are adjacent).
- Pet detection by reverse-video `hilite_pet`.
- The magic whistle.

Their "no pet deaths" goal was abandoned quietly after the midgame. [SPEC] A late-game pet adds little for a Valkyrie with Excalibur and costs attention.

### 4.9 Identification practices

- **Engrave-testing wands**, with care. In run 1, engrave-testing an unknown wand of wishing *granted a wish* (T16678).
- **Altar BUC testing**; reading identify; writing identify with the marker once ink and blanks existed (T11577, T25915).
- **Stethoscope** on bosses (e.g. *"Yeenoghu … level25 HP100/100 AC-5"*, T31529).
- **Telepathic farlook** while blindfolded to identify throne-room occupants and the Riders.
- **Kick-testing** gray stones to catch a loadstone (T9945).
- A strict state vocabulary:
  - "FORMAL" = the game said so, in the inventory or a message;
  - "inferred";
  - "UNVERIFIED".
- *"Only record observed identities and charges. Unknown is not charged."* (run-2 JSON `verification_policy`).

### 4.10 Medusa (run 3, D27 tree variant; also runs 1 and 2)

**Run 3**

1. Cold-wand ice bridge (T14138) and a scroll of earth (T14211) to cross the water.
2. Killed many ravens, which kept blinding the hero.
3. Crossed the last gap by jumping.
4. Blindfolded (on at T14221, off at T14236) while wearing the reflection amulet.
5. Medusa fled down the stairs to the Castle level. The hero followed and killed her on the Castle upstairs with Excalibur (6 hits in total, T14235).

**Run 1:** Medusa died to her own reflected gaze while the hero was blindfolded (T20721).

**Run 2:** no reflection or levitation, so the hero **dug down on D23 away from the water** (hole at 7,25), found the D24 up stairs, **came back up blind**, and killed her with Excalibur (T11137, 5 hits, 8 HP lost).

**Rule:** blindfold before arrival; reflection makes her gaze harmless and even lethal to her.

### 4.11 The Castle (run 3), step by step

1. **T14240: refused.** There was no MR, and a hasted arch-lich was at the upstairs.
2. **Temporary MR by polymorph** (T24624–24855):
   - Packed all armor and weapons into the bag (the form cannot use containers).
   - Wore the ring of polymorph plus the ring of polymorph control and waited for the ring to trigger (T24625–24841), then removed the polymorph ring.
   - Became a **gray dragon** (MR, flying, HD15).
   - Computed the minimum form duration and set an early retreat deadline.
   - Killed the arch-lich in 11 dragon attack actions (T24854) and a stalker in 5. Lost 2 extra healing potions to frost.
   - Retreated to a locked room on D27 and waited for the form to expire naturally at T25492.
   - Re-equipped at T25505.
3. **Entry** (T25580–25906): levitated over the **north moat**, taking 36 HP from sharks. Came through the back door at 65,21 above the rear trapdoors. Wore the ring of conflict in the court. Used cancellation on a disenchanter and a lich.
4. **The chest.** NE tower 67,15 was empty (T25840). The **NW tower chest 13,15** held the wand (T25889). The floor had a cursed scare monster scroll and a burned Elbereth, both left.
5. **Wishes 1–5 immediately**, including permanent MR and the `L` genocide.
6. **Drawbridge.** Harp Mastermind for the passtune (**CBADD**, T26106).
7. **Exit to the Valley** through the Castle trapdoor at 49,21 (T26768).

**Run 1 Castle:** arrived by trapdoor, destroyed the drawbridge with striking, filled the moat with blessed earth, tamed two xorns with a taming scroll, and found the wand in the NE tower.

**Run 2 Castle:** scare monster ward on the upstairs, moat filled with earth, gate broken by wresting the last striking charge. Died in the central hall.

### 4.12 Valley and Gehennom

**Valley:** entered through the Castle trapdoor in both runs 1 and 3. Their notes: *"Valley prohibits teleportation, mapping and wall digging."* Run 1 angered the Valley's Moloch priest with a force-attack batch.

**Vlad's Tower range.** Both runs misjudged where the branch was. The run-3 correction (T30362) cites dungeon.def: the branch is on Gehennom (9,5), i.e. Valley+9 to Valley+13.

| Run | Levels searched | Actual branch |
|---|---|---|
| Run 1 | D37–42 | D42 (tower 39–41) |
| Run 3 | – | D41 at 5,21 (tower 40–38) |

**Vlad's Tower fight (run 3)**

- Vlad teleports around and heals. He needed 13+ Excalibur hits over several engagements.
- The minotaur crisis is described in §3.3.
- Final kill (T31701): a **thrown potion of paralysis** plus 7 Excalibur hits.
- Candelabrum taken; 7 candles attached (T31870).

**Demon lords killed**

- Run 1: Asmodeus (lured onto the up stairs), Baalzebub, Juiblex, Orcus.
- Run 3: Juiblex, Yeenoghu, Orcus, Geryon, Asmodeus.
- Orcus's death wand fired at least 6 times, all absorbed by MR.
- Run 3 skipped Baalzebub.

**Fake towers**

- Run 3: a decoy on D47; the **magic portal inside the fake tower on D49 (39,21)** led into the real tower (D45 internal, T33206).
- Run 1: the fake-tower portal on D48.

### 4.13 Wizard of Yendor

Kill counts: run 3 killed him **7 times** (T33440, 33806, 34777, 35158, 35634, 36017, 36681); run 1 killed him twice.

**First kill.** In both runs, with a **wand of death** (run 3: *"WIZARD FIRSTDEATH33440 killed i DEATH SECONDhero westfrom45,20"*).

**His harassment**

- Curses items. In run 3 the gloves at T33633, fixed with marker-written remove curse at T33816. In run 1 the gloves plus levitation, which was fatal.
- Steals invocation items. Run 1 lost the Orb, Bell and Book at T33172–33235.
- Summons nasties.
- "Double Trouble" clones.

**Run 3's counter**

- MR and reflection on;
- life saving ready;
- a marker plus blank scroll reserve for remove curse;
- kill him every time he appears.

### 4.14 Invocation and Sanctum (run 3)

**Finding the square.** The vibrating square was found by walking: *"You feel a strange vibration under your feet"* (D51 45,19, T33792).

**Before the ritual.** They read `spell.c` to check what happens with cursed invocation items:

> *"at invocation square cursed book SAFE fails scrambled; cursed bell/candelabrum also fails; if unprimed uncursed items raises dead so review every result."*

**The ritual** (T33793–33794):

1. Light the 7 candles.
2. Ring the Bell.
3. Read the Book, within 5 turns.

**Sanctum**

- The high priest denounced the hero (T33881) and was **killed with a death ray** (T33882).
- Moloch lightning was reflected.
- The genuine Amulet was taken (T33887), and the hero was back on D51 by T33947.
- Note to self: *"Amulet now blocks level tele … DO NOT OFFER Moloch altar."*

### 4.15 The ascent with the Amulet

- Cached the invocation items on D42 (T34460).
- **11 "mysterious force" setbacks** (T34116–35436). Some sent the hero back 2–3 levels.
- Killed the Wizard 4 more times on the way, plus Orcus, Geryon and Asmodeus.
- **Crowned at the D14 altar** (T36363).
- Made a final upgrade pass:
  - lamp wish, then gloves to +3;
  - death wand recharged;
  - full healing bought in the D4 shop (T36625).
- Took the D1 up stairs to the Planes (T36680).

### 4.16 The Elemental Planes

**Portal detection: the Orb of Fate as a crystal ball**

- Apply the Orb, then `^` (traps) to reveal the magic portal (`aw^`).
- Costs: 45% failure at Int 11 (detect.c), 1–10 turns of helplessness on success, and side effects on failure (blindness, hallucination, "nothing").
- Charges ran out on Air. A **wrested wish for charging** (Fire, T36984) recharged it. A second blessed recharge on Water (T37053) was needed after three failures in a row.
- Alternative they considered: the Amulet's portal "warmth" (wizard.c) works only while the Amulet is worn or wielded, 1/15 per turn. They wore it briefly on Fire and then restored reflection (T36996).

**Per plane**

| Plane | Turns | Notes |
|---|---|---|
| **Earth** | T36680–36747 | Wizard killed on arrival. The **plane-name parser bug** was found here (§5.5). Orb found the portal. |
| **Air** | T36747–36803 | Orb found the portal. |
| **Fire** | T36803–37002 | Smoke **blocks line of sight** (vision.c 2747–2794) and often **overlays the `@` glyph**, which broke the guard's hero detection. Fire vortices and pit fiends. |
| **Water** | T37002–37105 | *"NEVER step } only blank air bubble."* Bubbles carry the hero and the portal; coordinates drift every turn; levitation does not work in water. Killed water elementals, a green dragon, eels and krakens with Excalibur. Life saving worn and reflection off from T37012. |

### 4.17 Astral Plane: how the correct altar was found

**Preparation before arrival**

- **Conflict off** (T37100), so Tyr would send a tame guardian angel (granted T37106).
- Free action on (T37101); levitation on; life saving worn.
- Full healing, a C-ration, and the last blessed charging ready.

**Source read.** `endgame.des` 479–690:

- altars at 10,20, 40,16 and 70,20, with **random alignments**;
- Riders at shuffled positions.

**Riders.** Identified by **telepathic farlook** (T37108): Pestilence west, Death centre, Famine east. Their rules:

- *"NEVER deathray Death"* (zap.c 3663: a death ray heals Death).
- Do not teleport Riders (teleport.c 1576: they relocate next to the hero).
- Never touch Rider corpses.
- Death rays work on Pestilence and Famine (no MR).

**Route choice.** The **western** temple: nearest, and its Rider (Pestilence) was killable with a death ray. The locked door at 26,23 was opened with the skeleton key.

**Fight and approach**

- A Moloch priestess at the door died to 3 Excalibur hits (T37121).
- Pestilence's terminal illness was cured with the unicorn horn (T37123).
- A recharged death wand killed Pestilence and two Moloch priests (T37125). HP fell to 3.
- Teleport-wand zaps cleared the approach. The third one angered a peaceful Angel of Tyr (T37132).

**Identifying the altar**

1. Saw the **high priest of Tyr** (T37139). That priest's name tells you the temple's god.
2. **Removed the ring of levitation** (you cannot offer while floating).
3. Stepped onto 10,20.
4. Pressed `:` (look here): *"There is a high altar to Tyr (lawful) here."*
5. `#offer` the Amulet: *"You ascend to the status of Demigoddess..."*

[SPEC] The western temple being lawful was partly luck. The route choice was made before the alignment was known. Had it been wrong, the plan would have needed another crossing past Death or Famine.

### 4.18 Bones

Hardfought shares bones between players. Run 3 used three bones piles, each time killing the ghost first:

| Level, T | Player | Loot |
|---|---|---|
| **D7, T3282** | Jamiro, killed by a giant spider | Early weapons and armor. |
| **D23, T14734** | deathdruid, Archeologist, fell into spiked pit | **Blessed bag of holding** (holding 6 holy waters), **Grayswandir**, stethoscope, pick-axe, **unicorn horn**, wands. Left silver dragon scales because of weight. [SPEC] Wearing them would have freed the amulet slot for life saving earlier. |
| **D44, T32179** | Jamiro again, touch of death | **Wands of death and teleportation**, a **cursed magic lamp** (later blessed and rubbed for wish 7), reflection amulets, polymorph control. A bag with 3 cancellation wands was deliberately **never put in the bag of holding**. |

**How they handled bones loot**

- Uncursed containers with holy water *before* opening them.
- Treated all bones wand charges as unknown.
- *"Name does NOT prove bones/prior run origin. No old-run map/item assumptions."*

The dumplog also records a fourth bones level on D17 ("114514", death ray while helpless). The journal never mentions it.

### 4.19 Money, shops and protection

- **Run 2:** bought priest protection twice (3200 zm at T6471, 3600 at T9504).
- **Run 3:**
  - bought a **magic marker for 67 zm** in Minetown (T1503), the single best purchase of the run;
  - +4 ring mail (T15761);
  - full healing (T36625).
- **Run 1:** bought a mithril coat (320 zm, T11260) and a luckstone.
- **Gold handling:** stored in the bag of holding, with a guarded helper (`stash-gold`).

---

## 5. The harness

### 5.1 Architecture

```
Codex agent (GPT 6 Astra, "high"/"medium" effort) ── shell commands ──►
  python3 scripts/session.py {screen|keys|start|credential|stash-gold|wait-pets|wrest-wish|...}
     │  every input: audit.require_healthy()  → fail closed
     │                audit.record('input_requested', screen_before, game_turn)  BEFORE sending
     ▼
  tmux -S /tmp/nhstream-<sha256(root)[:12]>.sock   session "hardfought", pane 144×36
     │  send-keys -l  (literal) | send-keys <name> (--named) | send-keys -H 3b (lone ';')
     │  capture-pane -p -e  → terminal.py (SGR + DEC special graphics) → text
     ▼
  ssh -F /dev/null -tt  nethack@us.hardfought.org
       StrictHostKeyChecking=yes, pinned ed25519 host key, PubkeyAuthentication=no,
       ServerAliveInterval=30, ServerAliveCountMax=3, ConnectTimeout=15
     ▼
  Hardfought dgamelaunch lobby  →  nh367-hdf (NetHack 3.6.7-1, curses UI, account rc CodexDelver.nh36rc)
```

Side systems:

- `audit.py`: a hash-chained evidence ledger, recorder heartbeat and checkpoints.
- A read-only viewer: `session.py serve` plus `web/index.html` polling `/state`.
- `obs.mjs`: OBS WebSocket control for the Twitch stream.
- Publication scripts.

None of these affect gameplay, except that the audit gate blocks input when unhealthy.

There was **no engine API**. `docs/METHODOLOGY.md` says observations were only the 144×36 text screen (plus optional annotations), and memory was external (Markdown journals, the emergency JSON, working instructions).

### 5.2 Script by script

**`scripts/session.py`** is the only input path.

| Subcommand | What it does |
|---|---|
| `start` | Creates the tmux session, or respawns a dead pane. **Workaround:** tmux 3.6a crashes if `window-size manual` is configured before the first session exists, so it calls `resize-window` after creation. |
| `screen [--compact]` | Prints the decoded screen (§5.3). |
| `keys VALUE [--named] [--why TEXT] [--raw] [--settle S] [--compact]` | The main input command. Behaviour described below. |
| `stash-gold --bag X --expected-gold N` | A three-step inventory transaction. Each step verifies the *exact* expected prompt text before the next key: `"Do what with your bag called HOLDING?"` → `s` → `"What do you want to stash? [$"` → `$` → `"You put N gold pieces into the bag called HOLDING."` It aborts if the status line changes mid-menu, the cursor leaves the message area, or gold is not 0 at the end. |
| `wrest-wish LETTER X Y [--limit ≤20]` | Repeatedly `z`+letter on a known-empty wishing wand. Requires the hero at x,y and the last message ending "Nothing happens." Stops on HP drop, 3 unchanged turns, Hungry/Weak/Faint/Blind/Conf/Stun, or any monster or warning digit within 4 tiles. |
| `wait-pets X Y [--limit ≤25]` | Searches in place until both `f` and `u` pet glyphs are adjacent. Stops on damage, bad conditions or another adjacent monster. |
| `credential username\|password` | Refuses unless the broadcast is hidden and the matching prompt ("username", "password" / "and again") is visible and "logged in as:" is not. Sends the secret with `sensitive=True` (never logged or printed), then Enter. |
| `attach` | Read-only `tmux attach -r`. |
| `hide` / `show` | Stream privacy toggles. |
| `note` | Public commentary. |
| `serve` / `viewer` | HTTP viewer. |

`keys` behaviour:

- Multi-character, non-named, non-raw input must pass `guard.command_preflight`: there must be a recognised map prompt.
- Pure digit strings `[12346789]{2,}` go to the **guarded walker**.
- `(F<dir>){2,}` is rejected: *"Repeated combat input must be inspected between attacks."*
- `--raw` bypasses the gate and is logged as `raw_input_override` with the `--why` text.
- After sending, it sleeps `--settle` seconds (0–10, default 1), then prints the screen.

**`scripts/guard.py`** holds the conservative movement batching. Its header says *"Conservative movement batching over visible terminal state, not a game oracle."* The rules are in §5.5.

- `observe()` detects pets as reverse-video cells (foreground `#0a1012` plus a background, i.e. the curses `hilite_pet` rendering) whose glyph is a letter (not `I`) or one of `@&:;'`.
- `settled()` polls every 0.15 s. It returns once at least 0.75 s has passed *and* the screen has been unchanged for 0.3 s, and gives up after 4 s ("Terminal did not settle; inspect animations or prompts").

**`scripts/terminal.py`** turns tmux SGR output into styled text runs.

- It maps **DEC Special Graphics** (tmux wraps line-drawing in SO/SI): `a`→`▒` (dark corridor), `~`→`·` (floor), `q`/`x`/`l`/`k`/`m`/`j`→box lines.
- Reverse video becomes foreground `#0a1012`, and this is what pet detection keys on.
- A comment warns it must never interpret terminal text as HTML.

**`scripts/route.py`** is a read-only BFS over the remembered screen map from the cursor to x,y.

- Walkable cells: `` ▒·<>$%!?=()[/*`"_ `` plus `-|` doorways (no diagonal moves through doorways; no squeezing diagonally between two blank rock cells).
- `--allow-traps` adds `^`.
- Output is JSON `keys` (capped by `--limit`), with the warning *"Proposal only: excludes known traps, water, boulders, and occupied tiles; does not predict monster movement."*
- The keys were then fed to the guarded walker.

**`scripts/sokoban.py`** plans a push sequence for one boulder (`X Y PUSHES`, with pushes in r/l/u/d) using cardinal BFS to the square behind the boulder.

- `--execute` runs at most 50 guarded steps (default 20).
- After every step it checks that the cursor equals the predicted hero position, that the **boulder and hole sets equal the prediction**, that HP has not dropped and is at least 2/3, that no DANGERS or Burdened appear, and that no unconfirmed monster is present.
- It auto-dismisses the read-only "Things that are here:" popup, but never "Pick up what?" or `[yn`.
- `--inspect-bystanders` farlooks every visible creature before every step (`;@` + keypad offsets + `.`) and accepts only a fresh "(peaceful|tame …)" description.
- `--allow-pet-swaps` lets it walk into verified tame pets, but never push into any creature.
- `--hidden-hole X,Y` marks holes hidden under items.

**`scripts/audit.py`** (not gameplay logic, but it gates input): see §5.9.

**Tests.** `test_guard.py`, `test_session.py`, `test_sokoban.py`, `test_terminal.py`, `test_audit.py` and `test_publication.py`.

- Test names show the regression history: `test_planes_preserve_identity_and_existing_safety_checks`, `test_quest_home_preserves_branch_identity_and_prompt_checks`, `test_gray_dragon_requires_title_hd_and_cursor_glyph`, `test_macros_require_map_or_reviewed_menu_override`, `test_falling_rock_stops_even_when_healing_masks_damage`, `test_ascii_floor_without_admitting_rogue_walls_or_traps`, `test_standalone_semicolon_is_sent_as_hex_byte`, `test_unexpected_second_prompt_never_sends_gold`.
- The journal says 53 tests passed at ascension.
- The published repo has 63 `test_*` functions. [SPEC] The difference is probably the publication tests added afterwards.

### 5.3 Observation format

What the agent saw from `screen --compact`, reconstructed from `print_screen`. This is an illustrative, synthetic example.

```
Terminal cursor (x,y; usually hero when no menu): 45,19
01 You feel a strange vibration under your feet.
10  ...
18                                          ·····
19                                         ·@··%
20                                          ··{·
33 CodexDelver the Swashbuckler  St:18/10 Dx:17 Co:20 In:11 Wi:16 Ch:12  Lawful
34 Dlvl:51 $:0  HP:168(168) Pw:38(38) AC:-6  Xp:17/411893 T:33792
Map features (x,y): @@44,19 %@47,19 {@46,20 ...
Neighbors of @(44,19): 7:·(43,18) 8:·(44,18) 9:·(45,18) 4:·(43,19) 6:·(45,19) 1:blank(43,20) 2:·(44,20) 3:·(45,20)
```

Details:

- Rows are printed as two-digit row numbers followed by the first 82 columns. Pure border rows are dropped.
- The permanent-inventory sidebar is to the right of column ~82 and is cut off in compact mode, so inventory detail needs a full `screen` or `i`.
- "Map features" lists every non-floor, non-wall character in map rows 10–30 as `char@col,row`. `}` is deliberately excluded, which is exactly why lava and water could be misread.
- "Neighbors" gives the 8 keypad-labelled neighbours of each `@`.
- The **terminal cursor** is the key signal: in NetHack's curses UI the cursor sits on the hero at a map prompt, and sits in the message window or a menu otherwise.

**Layout facts every parser depended on**

- Message window at rows 1–7 (`msg_window:reversed`, so the newest line is at the bottom).
- Map at rows 10–30 and columns 0–80.
- Title and status at row 33; `Dlvl/HP/T` status at row 34.
- Inventory sidebar at x ≥ 82.
- `boulder:0` renders boulders as `0` (which Sokoban relies on).
- `!implicit_uncursed` always shows "uncursed".
- `hilite_pet` gives the reverse-video pets.
- `time` and `showexp` put `T:` and `Xp:` on the status line.

### 5.4 Prompt and `--More--` detection

There was **no explicit prompt parser**. Detection was implicit.

- **Map-prompt test (`guard.state`).** Status row 34 must match `HP:(\d+)\((\d+)\)` and `T:(\d+)`, plus one of `Dlvl:(\d+)`, `^\s*│?\s*Home ([1-9]\d*)\s` or `^\s*│?\s*(Earth|Air|Fire|Water|Astral)\s`. The cursor must be inside the map (rows 10–30, cols 0–80), and the character under the cursor must be `@` (or `D` when the title says "the Gray Dragon" and the status shows `HD:15`). If any of this fails, the state is "not at a recognised map prompt". Any popup, menu, `--More--`/`>>`, `[yn]` question, direction prompt or getlin therefore reads as "not a map", which stops batches and multi-key macros.
- **Curses "more" is `>>`**, shown at the end of the message line; *"Curses `>>` needs Space."* The agent dismissed it manually. No auto-More existed. Pressing Esc at `>>` does **not** cancel an in-progress run or travel (T36842).
- **Popups** were read and handled by the model, with helper exceptions: sokoban.py auto-dismisses only the read-only "Things that are here:" display, and stash-gold matches exact prompt strings.
- **Settling** was the heuristic stability wait in §5.2. Animations (zaps, explosions, clairvoyance popups) needed `--settle 3` or manual re-reads. Ctrl-R redraw was used when the status looked stale (T24375). It did **not** restore a smoke-covered hero on the Plane of Fire (T36804).
- **Failures of this approach**, all in §5.6:
  - it cannot tell a direction prompt from "nothing happened" (the empty-wand cases);
  - it cannot see prompts that never appear because of a condition (deafness);
  - it depends on the `@` glyph being visible (polymorph, smoke).

### 5.5 Movement guard rules (verbatim logic of `guard.preflight` / `guard.changed`)

**Before each step** (movement digits 1–4 and 6–9 only, at most 24 per batch):

1. The state is recognised, as in §5.4. Otherwise: *"Not at a recognized map input prompt."*
2. No status word from `DANGERS = ('Slime','Stone','Ill','FoodPois','TermIll','Stun','Conf','Blind','Hallu','Weak','Faint','Hungry','Strngl','Held')`.
3. HP is at least 2/3 of max (*"Health below two-thirds."*).
4. **No creature or warning glyph within 2 tiles.** That is any letter, or any of `@&12345;:'`, in the 5×5 box, excluding reverse-video pets. (*"Nearby creature or warning; inspect before continuing."*)
5. The next tile is inside the map.
6. The next tile is in `` '▒·.#<>$%!?=()[/*`"_' ``. Otherwise: *"Next tile is unknown, blocked, a door, water, or a trap."*

**After each step** (wait for `settled()`; *"Terminal did not settle"* stops the batch):

1. The state is still recognised (*"Unexpected prompt or unrecognized state."*).
2. HP did not decrease (*"Damage taken."*).
3. There is no new visible "a rock falls on your head" message. Messages across wrapped lines are joined and compared by count.
4. The dungeon level is unchanged.
5. The position equals the previous position plus the step's delta.
6. The turn counter advanced by at most 2 (*"Unexpected time advancement."*).
7. No DANGER word appears.

Every step is audited (`guarded_step`, including the screen afterwards), and so is the batch result (`guarded_batch`).

### 5.6 Bugs and perception failures (with fixes)

| Run / T | Symptom | Class | Fix |
|---|---|---|---|
| R1 T11993 | A raw Sokoban batch was interrupted by an ape and a boulder was misplaced. | Blind multi-key | `sokoban.py --execute` with per-step board prediction checks. |
| R1 T12855 | The "Things that are here:" popup blocked execution. | Popup | Auto-dismiss only that read-only popup. |
| R1 T12961 | A hole hidden under an item was invisible to the planner. | Perception | `--hidden-hole`. |
| R1 T14427, 16172, 24632 | Batched `F` attacks hit peacefuls (watchman, tengu, Moloch priest). | Blind multi-key | Reject `(F<dir>){2,}`; rule: one attack per inspected screen. |
| R1 T23682 | Lava `}` misread by visual spacing; the hero walked into lava. | Perception | Rule: read "Map features" coordinates or use `#terrain`; levitate before moving on arrival. |
| R1 ~T33295 | A raw 24-key batch next to a known green slime. | Blind multi-key | `guard.walk` (run 2). |
| R2 T3055 | An Elbereth macro fired while a loot popup was open; keys went into an eat prompt. | Prompt | `command_preflight`: multi-key only at a map prompt; `--raw` plus `--why` for reviewed menu input. |
| R2 T6563 | A cmdassist "Invalid direction key" popup. | Prompt | Escape, Ctrl-R, then separate keys. |
| R2 T6698, R3 T4214 | Empty wand ("Nothing happens"); the queued direction became a move (swapped with a pet) or a melee attack. | Blind multi-key | Rule: send `z`+letter, verify "In what direction?", then send the direction. |
| R2 T8665 | Rogue level: the guard rejected ASCII `.` floor. | Parser | Whitelist `.`, with a test that walls and traps are still rejected (38 tests). |
| R3 T12878–12880 | A standalone `;` (farlook) was swallowed by **tmux command parsing**; the next key moved the hero. | Transport | Send a lone `;` as hex byte `3b` (47 tests). |
| R3 T24375 | The status display looked stale. | Transport / perception | A logged Ctrl-R showed the game had advanced; not a disconnect. |
| R3 T24843 | Polymorphed into a gray dragon: the player glyph was `D`, so the guard rejected `Ry`. | Parser | Single reviewed keys, then gray-dragon recognition requiring "the Gray Dragon" in the title *and* `HD:15` (T25505). |
| R3 T28330 | The quest status shows `Home 1`, not `Dlvl`; input was rejected before sending. | Parser | `Home N` identity (49 tests). |
| R3 T31715–31724 | Falling-rock traps: **regeneration hid the HP loss**, so the batch continued. | Perception | Compare visible counts of the "a rock falls on your head" message (52 tests). |
| R3 T32778 | `aR9` while **deaf**: no direction prompt, so `9` became an attack. | Blind multi-key | *"when impaired send aR THEN direction only after prompt."* |
| R3 T33225 | Literal `10s`: under number_pad, `1` moved the hero SW and `0` opened a menu. | Keymap | Rule: counts need `n` (`n10s`, `n20s`). |
| R3 T36681 | On the Plane of Earth the status says `Earth`, not `Dlvl`, so `zh` was rejected while the Wizard stood adjacent. | Parser | Sent `z`, `h`, `9` separately (the Wizard died), then added a plane-name parser with a distinct `Plane:<name>` identity (53 tests). *"change checkpointed/tested/verified BEFORE resumed gameplay."* |
| R3 T36804 | Plane of Fire: **smoke overlays the `@` glyph** even when not blind, so the guard rejected `PP`. | Perception | Separate `P` and menu keys; Ctrl-R did not help. |
| R3 T36842 | Esc at `>>` did not stop a `g` run. | Prompt | Awareness only. |
| Sandbox | A sandboxed `screen` falsely reported "no session" (tmux socket access denied); OBS status and audit start also needed escalation; SSH died while an approval was pending (T26986). | Environment | Always escalate tmux access; never leave the game idle behind an approval. |

### 5.7 Features added mid-game and why

| When | Feature | Trigger |
|---|---|---|
| R1 ~T5937, ~T8248 | Compact screen with the neighbours list, then the cursor line | Doorway coordinates and hero position were hard to read from the raw screen. |
| R1 ~T6349 | `wait-pets` | Bringing pets downstairs safely. |
| R1 T11400 / T11993 | Sokoban planner / guarded `--execute` | Push planning; then the ape incident. |
| R1 T12855, T12961 | Popup auto-dismiss, `--hidden-hole` | Sokoban execution stalls. |
| R1 late | `route.py`, `--settle` (e.g. `--settle 3`) | Long routes; animations. |
| R1 T26008 | `wrest-wish` | Up to 121 expected zaps of an empty wand. |
| After R1's death | `audit.py` recorder and fail-closed gating | Provenance for the claim. Also records every input with the screen before it. |
| R2 start | Guarded digit batches; rejection of repeated `F` | The R1 death and the peaceful hits. |
| R2 T3055 | `command_preflight`, `--raw --why` | The macro-into-popup incident. |
| R2 T8665 | ASCII `.` floor | Rogue level. |
| R2 T8996 | `stash-gold` | A multi-prompt bag transaction without a blind macro. |
| R3 (Sokoban) | `--inspect-bystanders`, `--allow-pet-swaps` | Peaceful Sokoban monsters and pets blocking pushes. |
| R3 T12879 | Hex `;` | The tmux separator bug. |
| R3 T25505 | Gray dragon form | The polymorph plan. |
| R3 T28330 | `Home N` | Quest levels. |
| R3 ~T31724 | Falling-rock message check | Regeneration masking damage. |
| R3 T36681 | Plane names | Earth. |

**Process rule they followed.** Every harness change got a regression test, a code checkpoint and an audit verify *before* play resumed. The ledger records *"No raw/direct-input bypass"* each time.

### 5.8 tmux, SSH, reconnects, hangups and idle timeouts

| Configuration | Value |
|---|---|
| tmux config | `status off`, `default-terminal screen-256color`, `history-limit 3000`, `destroy-unattached off`, `exit-empty off`, **`remain-on-exit on`** (a dead SSH pane stays inspectable and is respawned with `respawn-pane`). |
| Socket | Private socket per project root (`/tmp/nhstream-<hash>.sock`). |
| Sessions | `hardfought` (game) and `viewer`. |
| SSH keepalive | 30 s × 3. |

`send()` refuses when the pane is dead (*"No live SSH pane; inspect screen and reconnect."*). Retries after a drop were *"rejected before input"*, so no keystroke ever went into a half-dead session.

| When (UTC) | Run / T | Event | Recovery |
|---|---|---|---|
| Sep 7 ~05:33–05:40 | R1 T15474 | Game **unresponsive**. Comma, `:`, Escape, Ctrl-R, Ctrl-Q and Ctrl-C all ignored. SSH was alive, the lobby worked on a separate connection, and a spectator view showed the same frozen frame. | Hide the stream, then SSH escape `~.`, then `start`, hidden-credential login, `r` Resume last save. *"RESTORED SAME T15474 HP100."* The plan if the game were stale was Hardfought's crash-recovery page. |
| Sep 10 11:56 | R3 T12025 | User pause | `S`, `y`, Space, lobby shows "Resume last save [nh367-hdf]". |
| Sep 14 03:44:41 | R3 T22734 | SSH broke. One guarded key had been queued with no effect; the next input was rejected. | `start` + `credential`, then **`p` from the lobby recovered the stale nh367-hdf process after 9 s**. Exact position, turn and HP. "New-moon warning on restore." |
| Sep 14 11:54 | R3 T26955 | User pause (6 days) | Saved. On Sep 20 *"Old SSH lobby connection had closed during pause"*; reconnected and restored exactly. |
| Sep 20 15:47:46 | R3 T26986 | Pane died (exit status 7) **while a network/sandbox approval was pending**. | Reconnected and restored. *"Cause presumed idle timeout, not confirmed."* |
| Sep 20 20:17:18 | R3 ~T28520 | Pane died (status 7) **with a bag menu open**. | Hidden-credential reconnect restored exactly (Home 5, T28520, HP151) at 20:35–36. |

### 5.9 The audit layer, and why a game harness should care

`audit.require_healthy()` gates every input. It requires:

- a recorder heartbeat under 15 s old;
- an active terminal pipe;
- at least 5 GiB free disk;
- transcript lag of at most 1 MiB;
- the executing Codex thread ID matching the manifest.

Each input is written as `input_requested` (with `screen_before` and the parsed `game_turn`) *before* it reaches tmux, then `input_queued` or `input_failed`. The ledger is hash-chained. Checkpoints plus `verify` ran every ~30 minutes, and server ttyrecs and dumplogs were fetched with SHA-256.

**Gameplay value**

- It is fail-closed: no input can go out on an unknown state.
- It makes postmortems possible, because every keystroke is paired with the screen it was typed against.
- Final size: *"611082 events"*, about 815 MB of transcript source.

### 5.10 What the harness did *not* have

This is a check of `scripts/` against what an engine-backed harness gives for free.

- No structured parse of inventory, messages or status conditions beyond the guard's regexes.
- No automatic `--More--` handling.
- No monster identification apart from the Sokoban bystander farlook.
- No persistent per-level map memory. Maps lived as coordinates in the journals, e.g. *"UP75,13 … DOWN57,26"*.
- No explicit charge or resource tracking. It was done by hand in the JSON.
- No token-cost controls.

All of this was carried by the model plus the journals.

---

## 6. Memory practices

### 6.1 The memory files

| File | Size | Role |
|---|---|---|
| `memory/session.md` | 7 KB | Bootstrap and procedures (see below). |
| `memory/live-run.md`, `run-2.md`, `run-3.md` | 272 KB / 189 KB / 649 KB | Per-run journals, **newest section first**. |
| `memory/run-2-emergency.json`, `run-3-emergency.json` | 144 KB / 463 KB | The "compact" verified-state file. It was meant to be read quickly under pressure. |
| `EVIDENCE.md` | 123 KB | Provenance log: checkpoints, ttyrec hashes, harness changes, interruptions. |

`session.md` holds:

- the environment (host, controls, key quirks);
- *"Read this file at the start of each session, then inspect the actual game screen. Update it before stopping: character, turn, location, inventory discoveries, threats, goals, unresolved prompts, save status, and recording links. Never put passwords or stream keys here. Keep observations separate from guesses."*

The journals start with a `FINAL:` or `CURRENT` block. After that come `## T<turn> — <headline>` sections, and older material is marked with `OLDER:` or "THIS SUPERSEDES…" lines.

### 6.2 What the journal tracked, per entry

Reconstructed from hundreds of entries. Each entry was a dense single paragraph, and the same fields recurred:

- **Position and vitals.** `CURRENT D41 13,14 HP92/168 XP359693 AC-6`, plus hunger, encumbrance, Pw, and attribute changes.
- **Equipment toggles, by inventory letter.** Examples: `uLEV ON/OFF`, `q` (blindfold) `OFF`, `x` (conflict) `OFF`, `C` (free action) `LEFT`/`RIGHT` hand, `Q` (life saving) `ON`, `X` (reflection) `OFF … READY`, `ExcalWIELD`.
- **Resources with evidence grade.** Examples:
  - `hDEATHFORMAL1:1` (the charge count as seen in inventory);
  - `I sleep EMPTY31472`;
  - `Nfire0:3 ONE hero use`;
  - `M dig TWO hero, charges unknown`;
  - tags `NEVER RECHARGE`, `NEVER BAG` (cancellation), `READY`, `inferred`.
- **Consumables.** Healing potions, charging scrolls, holy water count, blank scrolls and marker ink, food, and the **last meal turn**.
- **Prayer.** The last prayer turn (*"LASTPRAYER13565"*), and *"No prayer Gehennom"*.
- **Threats.** Monster, coordinates, turn last seen, and how it was identified (*"farlook confirmed"* vs *"unID, don't assume type"*), including peacefuls that must not be attacked.
- **Maps.** `UP x,y` / `DOWN x,y`, doors (`OPEN`/`LOCKED`/`BROKEN`), traps (`AVOID`), **routes as coordinate chains** (`Route UP from 37,17 S37,18 SW36,19 …`), and floor caches.
- **Errors.** `ERROR<T>: … Preserve error`. Mistakes were logged permanently and never erased. The run-3 journal has explicit ERROR entries for T2606, T4214, T26038, T32778, T33225, T37132 and others.
- **Source citations for mechanics.** E.g. *"Source zap.c2137 success1/121 per attempt"*, *"teleport.c1576 RIDER tele … relocates ADJACENT hero"*.
- **Ops.** Audit checkpoint ids and the time of the next audit.

### 6.3 Emergency JSON: structure (field names verbatim)

**Run 2** has 30 top-level keys. The explicitly structured part is:

```
run_id, last_verified_turn, status, precedence,
live: {                                  # 124 keys: 20 structured + ~104 time-keyed text blobs
  level, hero:[x,y], hp, max_hp, ac, xl, xp, gold_outside, conditions:[], blindfold,
  pet, weapons, healing, wands, bag, other, fountains, route, latest_route, intrinsics,
  newest_<T> (97 of them, newest first: newest_12269 … newest_6371),
  newest_route_<T>, combat_<T>, emergency_<T>, pet_correction_<T>
},
latest_override_<T> (9: 5523, 5473, 5441, 5263, 5129, 5103, 5072, 4977, 4831):
    { level, hero, hp, max_hp, ac, xl, xp, dx, gold | gold_outside | gold_in_bag,
      conditions, blindfold, pet, changes, resources, plan, route, danger, ward },
uncertain_wand:  { letter, appearance, identity, evidence, uses, remaining_charges, warning },
current_state:   { level, hero, hp, max_hp, ac, xl, xp, gold, conditions, pet },
lightning:       { letter, appearance, identity, uses, remaining_charges, warning },
digging:         { letter, identity, uses, remaining_charges, last_used, warning },
latest_resource_changes: { <inventory letter>: "<what changed, turn>" },
current_threats: [str], intrinsics: [str],
escape_options:  [ {letter, appearance, identity, uses, remaining_charges, warning}
                 | {letter, identity, quantity, warning} ],
healing_options: [], sliming_cures: [], stoning_cures: [],
latest_items_3730: [ {letter, identity, quantity, picked_turn, [uses, remaining_charges, test_turn, warning]} ],
new_items:       [ {letter, identity, quantity, picked_turn, location:[x,y], note} ],
critical_equipment: [ {letter, identity, enchantment, buc, wielded|worn, quantity, in_pack, warning} ],
verification_policy: "Only record observed identities and charges. Unknown is not charged. Verify before entering dangerous areas; update after use or theft.",
lessons: [ "Movement batches use guarded incremental input; no raw movement batches near monsters.",
           "Stop immediately on Slime or Stone; never spend remaining turns on an unverified remedy.",
           "Self-zapping polymorph is not blocked by magic resistance (NetHack 3.6.7 zap.c lines 2249-2255).",
           "Never put a wand of cancellation into a bag of holding." ]
```

The `status` and `precedence` fields were used to invalidate everything below them, e.g. *"DEAD status supersedes ALL objects below, including the formerly named live object."*

**Run 3** has 579 top-level keys, of which 574 are free-text blobs (median 726 characters). They were **inserted newest first**, so reading the head of the file gives the latest state.

```
run_id, FINAL_VERIFIED, FINALIZED, ASCENDED_37140,
urgent_<T>            ×99   (T32584 … T37116)
latest_<T>            ×101  (T30682 … T33790)
urgent_update_<T>     ×92   (T25792 … T30648)
newest_snapshot_<T>   ×226  (T7905 … T25906)
audit_<HHMM> ×34, audit_update_<HHMM> ×5, audit_verify_<HHMM> ×3, audit_0446_verify   # UTC wall-clock audit notes
status, resume_snapshot, last_verified_turn (= 30648), paused_snapshot_26955, pause_evidence_final,
inventory_curse_24855, correction_14743, wand_g_latest, speed_update_10089,
current_authoritative_snapshot            # says "T7704 … supersedes older live fields"
live: { latest_override, level, hero, up, down, hp, max_hp, pet_latest, food_latest, pw, ac, xl, xp,
        gold, conditions, strength, dexterity, wisdom, skills,
        inventory: { <letter>: "<identity, BUC, enchant, provenance, turn>" },
        pet, threats:[str], prayer, magic_defenses, emergency_items, intrinsics, food_used },
item_identifications: {}, maps: { minetown }, rules: [4 strings]
```

The run-3 `rules`:

1. *"Never import randomized identities or maps from earlier runs."*
2. *"Do not attempt Castle without known magic resistance or reflection; prefer both."*
3. *"Unknown wand charges are not guaranteed available."*
4. *"Every game input through audited session.py; individually review combat actions."*

### 6.4 What worked and what didn't

**Worked**

- **Evidence grading** (`FORMAL` vs `inferred` vs `UNVERIFIED`; "unknown charges are not available charges"). The agent never trusted a charge it had not seen and always had a fallback. At T31472 the sleep wand was empty and it moved straight to the Orb.
- **A reserve list with hard constraints**: "NEVER recharge" for the wishing wand and marker after one recharge, "NEVER bag" for cancellation, "keep one charging for …".
- **A per-turn "CURRENT" line** at the top of every update, which made reorientation after compaction or a restart quick.
- **Recording errors permanently.** Recurring error classes (blind multi-key input, peacefuls) were visibly re-learned less often in run 3.
- **Saving the reasons as well as the facts**, e.g. *"NO MR: immediately RETREATED"*.

**Didn't work**

- **Schema drift.** Run 2's JSON had typed fields (`critical_equipment`, `escape_options`, `sliming_cures`), but they stopped being updated. `current_state` still describes Sokoban (T4566) even though the run died at T12271.
- In run 3 the typed `live` object and `current_authoritative_snapshot` froze at **T7611/T7704**, and `last_verified_turn` froze at **30648**, while play continued to 37140. Only the newest text blob was current. An agent that trusted the typed fields would have been wrong by 30,000 turns.
- **Unbounded growth.** 463 KB of JSON cannot be read under pressure. The file was "compact" only in name.
- **Map memory as prose.** Coordinates and route strings were hand-copied from the screen, and some misreadings (lava at T23682) came from exactly that.

[SPEC] A better design keeps a **small typed state file** (`as_of_turn` per field, schema-validated, where stale fields are an error) plus an **append-only event log**. The harness should fill in everything the game can tell it: position, vitals, conditions, inventory letters, and charges when `(x:y)` is shown. The agent writes only IDs, plans and hypotheses.

---

## 7. Hardfought operational details

### 7.1 Connection and login flow

1. **SSH** to `nethack@us.hardfought.org`. This is Hardfought's public dgamelaunch entry, so there is no SSH key or account at this layer.
   - Astra pinned the server's ED25519 host key in `config/known_hosts` and connected with `StrictHostKeyChecking=yes`.
   - `session.md` records the fingerprint as `SHA256:6I4FoeQJSX90yDFeWb7XTuq/AeuOFo2F2QEDSwgLWmY`, *"verified against Hardfought's published ED25519 fingerprint"* on 2026-09-06.
   - `docs/SETUP.md` adds: *"Verify Hardfought's current SSH host key through a trusted channel."*
2. **dgamelaunch menu: register or log in.**
   - Registration asks for a password twice ("and again"); login asks for username, then password.
   - Astra typed credentials only through `session.py credential` while the stream was hidden. The helper checks that the right prompt is on screen, sends the secret unlogged, then Enter.
   - Credentials were generated with `secrets.token_hex` into `.runtime/credentials.json` (mode 0600, gitignored).
3. **Logged-in lobby** shows `Logged in as: <name>`. The NetHack 3.6.7 game is `nh367-hdf`. When a save exists the lobby offers **"Resume last save [nh367-hdf]"**.
   - Keys the journals report:
     - `r`: Resume last save (run 1, T15474);
     - **`p`: play, which also reattached or recovered a stale running process** (run 3, T22734, *"p from lobby recovered stale nh367-hdf process after9sec"*).
   - On Sep 6 `session.md` said to restore from the "version menu" with uppercase `V`. Menu letters evidently differ between screens and dates. **Read the menu before pressing anything.**
4. **Options.** Hardfought keeps a per-account server-side rc (`CodexDelver.nh36rc`).
   - Astra installed `config/nethackrc`, backed up the previous server file, and diffed the result (*"only an extra final blank line"*).
   - [SPEC] It was edited through the lobby's options editor; the materials do not say how.

### 7.2 rc options (`config/nethackrc`) and why they mattered

```
OPTIONS=windowtype:curses
OPTIONS=windowborders:2,perm_invent
OPTIONS=color,menucolors,hilite_pet,hilite_pile
OPTIONS=showexp,showscore,time,hitpointbar
OPTIONS=lit_corridor,dark_room,!use_darkgray
OPTIONS=msg_window:reversed,msghistory:60
OPTIONS=menu_objsyms,!implicit_uncursed
OPTIONS=statushilites:10
OPTIONS=number_pad:1,!autopickup,autodig,fruit:slime mold,boulder:0
+ HILITE_STATUS for hunger, encumbrance, conditions (stone/slime/strngl/foodpois/termill in red inverse), HP%/Pw% bands
+ MENUCOLOR rules for blessed/cursed/uncursed/holy/unholy/worn/wielded/"named empty"/food/gold
```

Harness-relevant consequences:

| Option | Effect |
|---|---|
| curses | "More" is `>>`. The status and perm-inventory geometry is what the parsers expect. The cursor rests on `@` at map prompts. |
| `hilite_pet` | Reverse-video pets, used by the guard. |
| `boulder:0` | Boulders are `0` (the Sokoban planner depends on this). |
| `time` | `T:` is present (the guard needs it). |
| `!implicit_uncursed` | Every item shows its BUC state once it is known. |
| `number_pad:1` | **`k` kicks**; counts need `n` (`n20s`). Arrow keys misfired (named Up opened a take-off menu). |
| `!autopickup` | No accidental pickups (for example of scare monster scrolls). |
| `autodig` | Walking into rock with a wielded pick digs. |

### 7.3 Save, restore and pauses

- **Save:** `S`, then `y`, then Space at the curses `>>`. That returns to the lobby, where "Resume last save" should be visible.
- **Restore** returned the exact turn, HP and map every time: the T38 shakedown, and the two multi-day pauses (T12025 and T26955). After one restore (T22734) the journal notes a *"New-moon warning on restore"* ([MECH] the moon phase comes from the server clock).
- **Disconnects.** The game process can outlive the SSH session; the lobby's play/resume reattaches (§5.8). No saved game was ever lost.
- **Frozen game** (R1 T15474). SSH was alive and the lobby worked from a second connection, but the game ignored keys. The recovery was a fresh connection plus resume. The documented fallback, if a stale game blocks, is Hardfought's crash-recovery instructions at <https://www.hardfought.org/nethack/>.

### 7.4 Server behaviour and artifacts

- **Version string:** `NetHack Version 3.6.7-1 post-release - last build Sat May 23 11:43:56 2026 (8b4a575d7e9df6eacf187bfed899886b4b79e5f6, branch:hardfought)`.
- **Clock:** server-local times are **US Eastern**. The run 3 dumplog says ended 16:04:42, which EVIDENCE maps to 20:04:42 UTC.
- **Dumplogs:** `https://www.hardfought.org/userdata/<Initial>/<name>/nethack/dumplog/<game-start-epoch>.nh.txt` (and `.nh.html`), written at game end. The four CodexDelver ids decode to the four game start times. The text dump includes the final screen and last messages, inventory with container contents, attributes, vanquished, genocided, conduct and the dungeon overview.
- **ttyrecs:** one segment per connection, named `YYYY-MM-DD.HH:MM:SS.mmm.ttyrec`, under `.../nethack/ttyrec/`.
  - While active the segment is uncompressed and still growing.
  - Once finalized it is gzipped, and the uncompressed URL returns 404.
  - Some finalized segments are served from S3 (`https://hdf-us.s3.amazonaws.com/ttyrec/...`).
  - Astra hashed and archived partial snapshots of the growing file throughout play.
- **Bones are shared across players.** Run 3 met four bones levels (D7, D17, D23, D44), two left by the same player.
- **In-game mail** can arrive. At T37125 on Astral a scroll of mail arrived. Astra **left it unread** and flagged it as possible human interference for provenance purposes. The final inventory still has *"G - an uncursed scroll of mail"*.
- **Spectators** can watch a game read-only through dgamelaunch. A spectator session was used to confirm the T15474 freeze.
- **End of game.** The disclosure prompts (`Do you want your possessions identified? [ynq]` … attributes, vanquished, genocided, conduct, overview) must all be answered. Then *"Hardfought finalized the game and returned to its lobby"* with no save.

### 7.5 Timeouts and hangups

Two SSH drops ended with the pane exiting with status 7.

- One was during a pending sandbox or network approval (15:47:46 UTC Sep 20); Astra *"presumed idle timeout, not confirmed"*.
- One was with a bag menu open (20:17:18 UTC Sep 20).

Client keepalives (`ServerAliveInterval=30`) were already on. [SPEC] So the limit, if it is one, is on user input, not TCP.

**Operational rule:** never leave the game idle behind a long operation. Save first if a wait of many minutes is likely.

---

## 8. Recommendations

**How to read this section**

- §8.1 is a **candidate player rulebook**, ordered by lethality. Most items cite the Astra turn that taught it.
- The dev CLAUDE.md says "No seeded tactics … Don't preempt". These are knowledge and constraints, not tactic code. Whether to put them in `game/CLAUDE.md` now or hold them back to watch what the gamer reaches for is the team's call.
- §8.2 covers harness features, mapped onto the current `claude-plays-nethack` server and onto a future Hardfought terminal adapter. As of today the server has `observe`, `do`, `exec` / `continue_exec` (pause on any message, autocontinue regexes, "Really" always pauses, swallowed-yn detection), `harness_note`, auto-`--More--`, `prompt_open` from NLE `internal`, a Monsters block tagged from fork descriptions, the `seen` overlay, a no-progress limit, hooks, and tactics `travel_to` / `walk_to` / `auto_explore` / `look_at`.

### 8.1 Player rules, most important first (53 rules)

Each rule gives its evidence: R*n* = run, T = turn.

#### P0: instadeath and run-ending (never violate)

1. **No Castle, and no loitering at D20+ near soldiers, without magic resistance or reflection. Prefer both.** Evidence: R2 died at full HP (T12271); R3 retreated at T14240, and its reflection saved it at T11892.
2. **Get reflection early.** [MECH] Sokoban's prize is either an amulet of reflection or a bag of holding, depending on the level variant. Other sources are silver dragon scales and a shield of reflection. Evidence: R3 T11892 (death ray reflected); R2 got the bag instead and died.
3. **Treat soldiers (sergeant, lieutenant, captain) and any monster seen zapping a wand as carrying a death ray.** Never stand in line with one (row, column or diagonal) at range without MR plus reflection. Evidence: R2 lightning at T12211, then a death ray at T12271.
4. **On `Slime`, `Stone`, `Strngl`, `TermIll` or `FoodPois`, stop everything; the very next action is a verified cure.** Keep a checked list:
   - stoning: lizard or acidic corpse (carry at least 2 lizards);
   - sliming: fire (a wand with known charges, a scroll of fire), or polymorph;
   - illness: unicorn horn or prayer.

   Evidence: R1 death; R1 T21971–75; R3 T29410, T37123.
5. **A self-zapped wand of polymorph cures sliming even when you have MR** (zap.c 2249–2255). Prayer does not help in Gehennom. Evidence: R1 died holding `Y` (1:6).
6. **No multi-step movement, travel or runs with a hostile within 2 squares, near a known slime or cockatrice, or onto unexplored terrain.** Evidence: R1 death (a 24-key batch next to a slime).
7. **Never batch attacks.** One `F`+direction, look, repeat. Farlook anything that might be peaceful. Evidence: R1 T14427 (the Watch), T16172 (a tengu), T24632 (the Moloch priest).
8. **Send `z`/`a`/`t` and the direction as separate inputs.** Send the direction only after "In what direction?" is on screen. An empty wand ("Nothing happens") or deafness means there is no prompt, and the direction key becomes a move or an attack. Evidence: R2 T6698; R3 T4214, T32778.
9. **Wear the amulet of life saving for boss fights and the endgame** once MR comes from armor (GDSM), so the amulet slot is free. **Keep two escapes**, because the first may be empty. Evidence: R3 T31458–31473 (teleport wand, then the Orb invoke); T37012.
10. **Arrive on Astral** at full HP with:
    - life saving worn;
    - a death wand with *verified* charges;
    - full healing;
    - a unicorn horn;
    - **conflict off** (so the guardian angel is tame);
    - free action on.

    Evidence: R3 T37100–37140. Its death wands ran dry during the approach (L and H tested empty at T37121–22), and only the last blessed charging scroll (T37123) made the Pestilence kill possible.
11. **Riders.** Identify each with farlook or telepathy.
    - **Never death-ray Death** (it heals him, zap.c 3663).
    - **Never teleport a Rider** (it relocates next to you, teleport.c 1576).
    - Never touch Rider corpses.
    - Death rays kill Pestilence and Famine.
12. **Before `#offer`,** confirm the temple priest's god by farlook ("high priest of Tyr"), take off levitation, step onto the altar, and press `:` to read "high altar to Tyr (lawful)". Evidence: R3 T37139–37140.
13. **Never swap a pet into water or lava.** Moving onto a pet swaps you. Water walking or levitation lets you stand where the pet cannot. Evidence: R1 T20546 (anger, −15 alignment).
14. **Prayer discipline.**
    - Track the last prayer turn.
    - A wish adds 50–149 to the prayer timeout.
    - Pray only in major trouble with a likely-low timeout.
    - Never pray in Gehennom.

    Evidence: R1 T23916. R3 prayed only 4 times in 37k turns.
15. **Don't wear a ring you cannot afford to have stuck (levitation) under gloves during the Wizard fight.** Keep a remove-curse reserve (a scroll, marker plus blank, or holy water) until the Amulet is on the altar. Evidence: R1 T33188 (fatal); R3 T33633→T33816 (fixed).
16. **Carry a unicorn horn from the midgame on.** Apply it repeatedly; one failure means "apply again". Evidence: R3 T29410 and T37123/37125 (terminal illness cured twice).

#### P1: strategy

17. **Order:** Mines to Minetown (buy a marker if one is for sale), Oracle and Excalibur, **Sokoban**, Mines End luckstone, then the midgame. All three runs broadly did this.
18. **Excalibur.** Dip a long sword into fountains once XL ≥ 5 [MECH]. Expect many dips (R3 needed 27; R2 needed 12). Dips dry up fountains, so spread them across levels. Evidence: R3 T4532; R2 T5904.
19. **Buy a magic marker on sight.** It wrote Elbereth, identify, scare monster, remove curse and enchant weapon in R3. Evidence: T1503, T14330, T25915, T26430, T33816.
20. **First wishes:** MR (GDSM) → 2 blessed charging → speed boots → blessed genocide (for `L`) → blessed magic marker → 3 blessed gain level if short of XL14. Ask for +2, not +3: [MECH] `readobjnam` zeroes an enchantment `s` when `s > rnd(5)`. Ask for 2 of an item rather than 3 ([MECH] 2/3 vs 1/2 grant odds). Evidence: R3 T25891–27772.
21. **Recharge the wand of wishing exactly once**, with blessed charging (→ 3 charges). A second recharge explodes it. Wrest the last wish (about 1/121 per zap) only at a safe, quiet spot (R3 took 23 tries on Fire). **Magic markers also recharge only once.** Evidence: R3 T25912, T36984; R1 T26008, T33004.
22. **Genocide `L` as soon as a blessed genocide is available.** Liches cast destroy armor, curse items and touch of death, and an arch-lich guards the Castle entrance. Evidence: R1 T18045; R3 T25913.
23. **The quest requires XL14.** Gain level is the fast route (XP thresholds XL13 = 40000, XL14 = 80000, exper.c). Evidence: R3 T27093, T27772.
24. **Vlad's Tower is on Valley+9 to Valley+13** (dungeon.def: Gehennom (9,5)). Search there first. Evidence: both runs searched the wrong range (R1 D37–42; R3 T30362).
25. **The real Wizard's tower is entered through the magic portal inside a fake-tower level.** There are decoy towers. Evidence: R3 D47 decoy, D49 portal; R1 D48.
26. **Invocation.** Walk the bottom level until "You feel a strange vibration under your feet". Check the BUC of the Bell, Book and Candelabrum (cursed items fail). Then light the candles, ring the Bell and read the Book, in that order, within a few turns. Evidence: R3 T33792–33794.
27. **After the invocation the Wizard returns repeatedly.** Kill him with a death wand each time. Cache or secure the invocation items once used. Evidence: R1 lost all three items (T33172–33235); R3 killed him 7 times.
28. **With the Amulet, expect "mysterious force" setbacks** (R3: 11 of them, T34116–35436). Budget turns and food.
29. **Planes.** Use a crystal ball (the Valkyrie's Orb of Fate): apply, then `^`, shows the portal as a trap. Carry charging for it. Fire smoke blocks line of sight. On Water, move only inside air bubbles; the portal drifts with its bubble. Evidence: R3 T36690–37105.
30. **The Castle wand is in a corner tower chest** (R1 NE 67,15; R3 NW 13,15). Check both. Leave the cursed scare monster scroll and the burned Elbereth on that square alone.
31. **Enter the Castle from the back**: levitate over the moat, use the trapdoor-side door, and wear conflict in the court. Avoid the central hall and barracks. Evidence: R3 T25580–25906; R2 died in the central hall.
32. **MR without a wish:** gray dragon form via ring of polymorph plus polymorph control. Pack all gear first (the form cannot use containers), compute the form's duration, and expect potion breakage. Evidence: R3 T24841–25505.
33. **Carry 2+ lizard corpses; kill cockatrice-wielders at range.** Evidence: R1 T21971.
34. **Stethoscope bosses** to see their real HP. Evidence: R3 T31529 (Yeenoghu HP100).
35. **Stop enchanting Excalibur at +5.** Reading enchant weapon at +6 or above risks evaporation (wield.c 806). Evidence: R3 T26921.
36. **Never controlled-polymorph into your own race** ("new man": −2 to +2 XL each time). Evidence: R3 T21292/21310 (−4 XL).
37. **Never put a wand of cancellation, or a bag containing one, into a bag of holding.** Evidence: R2 lessons; R3 T32169.

#### P2: tactical hygiene

38. **Farlook every ambiguous glyph** (gas spore vs floating eye, `I` markers, statues). Evidence: R1 T1241.
39. **Don't chase fleeing engulfers or paralysers.** Get free action before the Castle. Evidence: R2 T5236; R3 T16566.
40. **Blindfold before gaze monsters come into view** (Medusa, pyrolisk, umber hulk). Evidence: R3 T12912, T33754.
41. **Scare monster scroll:** pick it up at most once (it crumbles on the second pickup, including a price-check re-pick). Use it as a permanent floor ward; it repels minotaurs (and, [MECH], `@` humans). Evidence: R2 T5118, T11867; R3 T3823.
42. **Elbereth** does not stop `@` humans or minotaurs, and never attack from it. It is fine for resting. Evidence: R1 T21659; R2 JSON.
43. **After arriving on a level with lava or water,** levitate or read the terrain (`#terrain`, coordinates) before moving. Never trust visual spacing for `}`. Evidence: R1 T23682.
44. **Check landing squares for invisible monsters before `#jump`.** Evidence: R3 T26038.
45. **Don't rest next to unresolved threats with pets unattended.** Evidence: R3 T7842, ~T8002.
46. **Under number_pad, counts need `n` (`n20s`); `k` kicks; don't use arrow keys.** Evidence: R3 T33225; `session.md`.
47. **Keep a luckstone and feed Luck** (gems to co-aligned unicorns, sacrifices). Evidence: R3 T10001, T21772–21884.
48. **Engrave-test unknown wands.** Engraving with a wand of wishing grants a wish. Never zap unknown wands toward pets. Evidence: R1 T16678; R3 T2606.
49. **Don't engrave on altars, don't let pets kill temple priests, and don't force-fight near any peaceful.** Evidence: R1 T22842, T10602, T24632.
50. **Level teleporters and trapdoors separate you from pets and caches.** Mark every `^` and identify it with the `^` command. Evidence: R2 T11161; R3 T13146.
51. **Before MR, avoid unknown traps.** Polymorph traps destroy body armor. Evidence: R2 T10165.
52. **Shops and temples:**
    - buy markers, full healing and armor;
    - [MECH] donate 400×XL to a temple priest for protection (R2 paid 3200 at XL8 and 3600 at XL9);
    - stash gold in the bag.

    Evidence: R2 T6471/T9504; R3 T1503/T36625.
53. **Always look at the screen after any interruption** (reconnect, popup, animation) before the next key. The run-3 journal's standard phrase: *"Review screen after resume before combat."*

### 8.2 Harness features, prioritized, and how they map onto claude-plays-nethack

> **Note.** While this report was being written, commit `641f9f6` added `src/nh`, a tmux terminal harness for real NetHack 3.6.7. Its commit message and a grep of the code show it already:
> - sends keys one logical unit at a time and stops the rest when a command finishes early or a `[yn]` prompt cannot take the next key;
> - pauses its kernel on messages, HP loss, new monsters, status conditions and level changes;
> - parses `Home N` and `Astral Plane` status lines.
>
> The gap table below is written against the NLE MCP server (`src/claude_plays_nethack/server.py`). Check the H-P0 and H-P2 items against `src/nh` as well.

**Astra component → our equivalent → gap**

| Astra | claude-plays-nethack today | Gap to close |
|---|---|---|
| `guard.preflight` / `changed` (HP, conditions, proximity, terrain, level, position, turn jump) | `exec` pauses on any message; a synthesised hostile-arrival message; swallowed-`yn` pause | **No pause on silent HP loss, condition bits, hostiles already within 2, hazardous next tile, level change, turn jump or position mismatch.** |
| `command_preflight` (map prompt required) | `prompt_open` = `yn` / `getlin` from NLE `internal` | Prompt *kinds* are coarse. There is no "expected prompt" check before a direction or item key. |
| Manual `>>` handling | auto-`--More--` including wrapped markers | Good. Keep joining all messages into the result, as now. |
| `--inspect-bystanders` farlook | Monsters block tagged `[hostile]/[peaceful]/[tame]` | Good. Add warning digits (1–5) and remembered-invisible `I` markers. |
| `route.py` | `walk_to`, `travel_to` | Run them under the same safety monitor. |
| `sokoban.py` | none | Backlog, until the gamer reaches for it ("no seeded tactics"). |
| `stash-gold`, `wrest-wish`, `wait-pets` | `exec` kernel | Optional vetted helpers. |
| Emergency JSON | `harness_note`, trajectory | **No typed state or resource ledger.** |
| Audit ledger (`input_requested` before send) | trajectory JSONL v2, per step | Could add a per-`do` "intent" string (Astra's `--why`). |
| Reconnect, save, credentials | not needed for local NLE | Needed for a Hardfought adapter (§8.2 H-P2). |

**H-P0 (directly prevents Astra's death or near-death classes)**

1. **Safety monitor for every multi-step path** (`exec`, `travel_to` / `walk_to`, any future repeat helper). After each `env.step`, pause with a reason when any of these hold:
   - HP dropped by any amount, even with no message (regeneration masking, R3 T31715);
   - HP is below a threshold (Astra used 2/3);
   - a **`blstats.condition` bit** is newly set (Stone, Slime, Strngl, FoodPois, TermIll, Blind, Deaf, Stun, Conf, Hallu, Lev);
   - hunger reaches Weak;
   - level or dungeon changed;
   - `time` jumped by more than 2 on a single step (paralysis, sleep, falls);
   - the position is not the expected one;
   - a hostile is within Chebyshev distance 2 (not only new arrivals);
   - the next target cell is water, lava, a trap or unknown.

   NLE gives all of this exactly, with no screen parsing. It fits naturally next to the existing swallowed-`yn` pause in `_drive_paused`. It is a perception and safety feature, not a tactic.
2. **Emergency banner.** While Stone, Slime, Strngl, TermIll or FoodPois is set, every tool result begins `*** EMERGENCY: <condition> since T<n> ***`, and `exec` refuses to auto-continue. This is the missing piece in R1's death. The banner does not choose a cure; that stays with the gamer.
3. **Prompt-kind awareness.**
   - Classify open prompts by text as well as by flag: direction (`In what direction?`), object selection (`What do you want to <verb>? [...]`), confirmation `[yn]`/`[ynq]`, getlin, menu, and `--More--`.
   - In `exec`, pause before sending a direction or letter key when the expected prompt is not open. The empty-wand, deaf and `10s` incidents are all "key sent into the wrong prompt state".
   - Extend the banned-autocontinue list with meaning-changing failures: `^Nothing happens`, `^You don't have`, `^Never mind`, `^You can't`, `cannot hear`.
4. **Peaceful-contact guard.** Refuse `F`+direction and plain moves into a monster tagged `[peaceful]` or `[tame]` unless an explicit override is given, and report it. Astra angered peacefuls 5 times: three force-fight batches (T14427, T16172, T24632), a `#jump` into an invisible naga (T26038), and ray collateral (T37132). `exec` already always pauses on "Really…?"; this closes the force-fight path. Pair it with item 9 (ray-line preview) for the collateral case.
5. **Resource ledger maintained by the harness.**
   - Parse inventory strings for charges `(x:y)` and BUC.
   - Log every zap, engrave, read, quaff and apply as `{letter, item text, turn, resulting message}` in the trajectory.
   - Expose `observe()['ledger']` with: observed uses since the last formal count, last result ("Nothing happens" means likely empty), last prayer turn, wishes used (detect "For what do you wish?"), and luck items.
   - This makes Astra's best rule, *"unknown charges are not available charges"*, mechanical.
6. **Identity and status robustness tests.** The engine gives the status, but tactics and views that assume `@` at the cursor, or that `chars` equals terrain, will break the way Astra's did. Add fixtures for: polymorphed hero (e.g. `D`), invisible hero without see invisible, blind (telepathy-only map), smoke or gas overlays, the Rogue level ASCII tiles, `Home N` quest levels, and the Planes. Fail closed.

**H-P1 (large quality-of-play gains)**

7. **Typed state file plus append-only journal.**
   - The harness writes the machine-knowable fields (position, vitals, conditions, inventory letters and charges, level features, last prayer turn), each with `as_of_turn`.
   - The gamer writes IDs, plans and hypotheses, with `FORMAL` / `INFERRED` / `UNVERIFIED` grades.
   - Stale fields are flagged in `observe()`.
   - This addresses Astra's JSON drift (§6.4).
8. **Hazard view.** Classify glyphs into terrain and list water, lava, traps, boulders, doors and stairs with coordinates around `@`. This is the NLE equivalent of Astra's "Map features" plus `#terrain`. It would have prevented R1's lava step.
9. **Ray-line preview.** For a proposed zap direction, list monsters on the path, including likely bounces, tagged hostile, peaceful or tame. Evidence: R3 T37132 (Angel of Tyr); R2 "avoid rebounds near walls".
10. **Guarded travel and runs.** Make `_` travel and `G`/`shift` runs go through the safety monitor, stepwise if necessary. Esc at `--More--` does **not** stop a run in progress (R3 T36842).
11. **A bounded-repeat primitive** with stop conditions (Astra's `wrest-wish`, `wait-pets`, `n20s` search), so tactical loops don't need bespoke guards. For wresting, stop on any message other than "Nothing happens", on an HP change, or on a monster within 4.
12. **Sokoban planner plus guarded executor** with board-prediction checks after each push. Astra needed it after an ape broke a raw batch. Put it in the backlog and add it when the gamer reaches Sokoban.
13. **Per-step intent string.** Let `do()` accept an optional short `why` and record it in the trajectory, as Astra's `--why` did. This makes the pairing of keystroke, intent and screen trivial for postmortems. The Claude session JSONL already has reasoning, but aligning the two is laborious.

**H-P2 (future Hardfought terminal adapter)**

14. **Transport:**
    - tmux + ssh with a pinned host key and `remain-on-exit on`;
    - refuse to send on a dead pane;
    - `send-keys -l` for literals; the `;` byte as hex (tmux separator bug); never arrow keys;
    - `capture-pane -e`, SGR decoding and DEC-graphics mapping;
    - the settle heuristic (≥0.75 s total, 0.3 s quiet, 4 s cap).
15. **Screen state machine:**
    - cursor on `@` inside the map region means a map prompt;
    - `>>` at the end of a message line is curses "more";
    - menu, popup and question detection from the message window and cursor row;
    - status parsers for `Dlvl`, `Home N`, the planes and polymorph titles, each with fixtures.
      - The level labels Astra actually saw were `Dlvl:N`, `Home N` on the quest, bare `Earth`/`Air`/`Fire`/`Water` on the elemental planes (its guard regex, confirmed against botl.c), and `Astral Plane` on Astral (dumplog final status line).
      - When polymorphed, the title reads e.g. "the Gray Dragon" and the status shows `HD:15` in place of `Xp`.
16. **Lobby automation:**
    - a credential helper that checks the prompt and never logs;
    - a login → lobby → `p`/`r` → game flow;
    - stale-process recovery;
    - after any reconnect, block gameplay keys until turn, HP and position match the last recorded state.
17. **Idle policy.** Save before long waits or approvals. Watch for status-7 pane deaths. Never leave the game in a menu while blocked.
18. **Artifacts.** Fetch the dumplog (`<start-epoch>.nh.txt`) at game end and archive ttyrec segments, remembering that they are gzipped after finalization. The dumplog is the authoritative postmortem source.
19. **Mail and spectators.** Detect in-game mail and have a policy (read or ignore); Astra ignored it for provenance. Spectators are harmless.
20. **Version-controlled server rc** diffed against the server copy after every edit. The parsers depend on it.

### 8.3 Process lessons

- **Check mechanics in the 3.6.7 source before acting on a belief.** Astra's worst losses came from wrong beliefs (MR blocks self-polymorph; the Vlad range) and its best moves from source reading (the gray dragon MR plan, Rider rules, portal detection). Give the gamer a searchable copy of the 3.6.7 source and spoilers.
- **Keep errors permanently and re-read them at session start.** Astra's `ERROR<T>: … Preserve error` entries made recurring failure classes visible.
- **Change the harness only between moves:** tests, then checkpoint, then resume. Astra patched its guard 6 times mid-game without a single harness-caused death.
- **Budget for about 500 game turns per hour** and about 37k turns for a careful ascension (Astra's winning run: about 74 hours of active play). A "bigger model, fewer turns" approach does not change the turn count, only the cost per turn.

---

## Appendices

### A. Key verbatim quotes

- R2 death: *"A visible-state movement guard cannot guarantee protection from a one-hit kill. The strategic error was advancing through the Castle without known magic resistance or reflection."*
- R1 death: *"sliming began during an unsafe 24-key movement batch near known slime … SELF-ZAPPING POLYMORPH IGNORES MAGIC RESISTANCE. Could have used zY. immediately in GDSM"*
- R1 lessons: *"no blind movement batches near dangerous monsters; stop on fresh messages/status changes; VERIFY usable fire charges before Gehennom; maintain uncursing reserve; do not wear levitation during Wizard fight if avoidable."*
- R3 at T14240: *"NO MR: immediately RETREATED … DO NOT DESCEND CASTLE until magic resistance/genocide/credible protection."*
- R3 at T25912: *"nWISHWAND NOW RECHARGED ONCE … NEVERRECHARGEAGAIN would explode."*
- R3 at T37140: *"Real Amulet P offered at western high altar10,20, explicitly verified lawful with look-underfoot before offering."*
- Run-2 JSON `verification_policy`: *"Only record observed identities and charges. Unknown is not charged. Verify before entering dangerous areas; update after use or theft."*
- `EVIDENCE.md`, run 2 safety changes: *"Digit-only movement batches … are now sent one step at a time, waiting for a settled screen and stopping for damage, conditions, nearby creatures, unknown/unsafe terrain, prompts, unexpected movement or excess turn advancement. This is conservative visible-state checking, not perfect perception."*

### B. Materials reviewed

| Area | Coverage |
|---|---|
| Journals | `memory/live-run.md`, `run-2.md` and `run-3.md` in full (chunked); `memory/session.md` |
| Emergency JSON | `memory/run-2-emergency.json` and `run-3-emergency.json`: structure fully enumerated; key entries read |
| Scripts | `session.py`, `guard.py`, `route.py`, `sokoban.py` and `terminal.py` in full; `audit.py` and the tests skimmed; publication scripts, `obs.mjs` and `web/*.html` not gameplay-relevant |
| Other | `EVIDENCE.md` (connection incidents, harness changes, run summaries); `docs/METHODOLOGY.md`, `SETUP.md`, `RECORDINGS.md`; `config/nethackrc`, `tmux.conf` |
| Hardfought | Dumplog listing plus `1788718109`, `1788720306`, `1788889409` and `1788964024` `.nh.txt` |

The clone at `/home/user/kenforthewin/nethack_astra` was not modified.
