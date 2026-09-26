# p1 journal (local practice game, seed 101)

T:30 DL1 — first kill: jackal in the corridor below the big room. Found sink (55,6) and downstairs (54,7) on DL1.
T:54 DL1 — picked up and wore studded leather armor from the floor (+0, uncursed in effect): AC 6 -> 3. Picked up an iron ring (unknown, not worn).
T:130–380 DL1 — killed newt, grid bug, 2 jackals. Dropped ring mail (36,11) and a morning star (23,17) as dead weight.
T:388 DL1 — kicked open a locked large box in the small NW room (2 potions shattered): got candy bar, scroll ZELGO MER, violet gem.
T:393 DL1 — ate a fresh jackal corpse (saving the ration). DL1 fully explored by explore().
T:466 DL1 — destroyed a kobold zombie next to the stairs; descended to DL2 at ~T:470 with HP 17/18, XL1.
T:506–686 DL2 — killed lichen (corpse kept, m), jackal, 2 grid bugs, newt, lichen -> XL2 (HP 29/29). Found FOUNTAIN at (25,6) on DL2 (Excalibur later), upstairs at (47,16). Pushed a boulder at (18,7).
T:787 DL2 — killed a large kobold in the SE corridors. T:815 kicked open a locked door at (71,9) (2 kicks).
T:819 DL2->DL3 — TRAP DOOR just beyond the kicked door dropped me to DL3 at (5,17), HP 29/29. DL2 downstairs never found; DL3 upstairs unknown.
T:840–863 DL3 — found Annootok's general store in the NW corner. Price-ID: ZELGO MER = identify; iron ring = 100zm class. Recorded full stock in state.md. $19 only, bought nothing.
T:892–905 DL3 — searched at the corridor dead end (16,15): hidden passage north. Killed a coyote and a sewer rat. Found the UP stairs at (19,9); an arrow trap at (19,6) hit me for 2.
T:947–960 DL3 — killed 2 coyotes one at a time at the doorway choke point (41,5), no damage. Hungry at T:970.
T:1019–1023 DL3 — mistake: my corpse finder picked a shop item and travel walked me 49 turns back to the shop; the coyote corpse was then too old, so I ate the lichen corpse (Not Hungry). Two `>` on DL3: (29,16) and (46,18) => Gnomish Mines branch is on DL3.
T:1053 DL3 — shift ended standing on `<` (19,9): HP 29/29, XL2, AC3, $19, never prayed, no pet. Food: 1 ration + candy bar.

T:818 DL3 — (container restart) game restored from crash-recovered level files: everything after T:818 (shop visit, coyotes, hidden passage, finding < at 19,9) is UNDONE. Map knowledge of DL3 from the journal may still guide exploration.
T:849 DL3 — (shift 2, restored timeline) re-found the hidden passage at (16,15)->(16,14) after 10 searches; explore() went north.
T:858–866 DL3 — killed a sewer rat and a coyote at the corridor choke point (16,9) west of the `<` room door (17,8); re-found `<` at (19,9). Ate the fresh coyote corpse at T:875 (Not Hungry). HP 21/29.
T:959 DL3 — explore() walked onto the arrow trap at (19,6) despite skip= (-3 HP); the pile there had a MAGIC MARKER (h) + candy bar (g): picked up both.
T:990–1098 DL3 — killed jackal, gnome zombie, jackal, giant rat, gecko one at a time at doorways/corridors; no damage. Scroll EIRIS SAZUN IDISI (i) picked up at (48,18) in the SE room (down stairs (46,18)).
T:1121–1123 DL3 — found a hidden door at (48,15) N of the SE room; killed a goblin (it threw an orcish dagger) -> XL3, HP 38/38.
T:1131 DL3 — wore the goblin's orcish helm (n): AC 3 -> 2. Orcish dagger (o) kept for throwing.
T:1171–1188 DL3 — acid blob in the tiny E room (58-60,16-18): no melee (sword corrosion); threw both daggers (1 hit), it survived, looped around and got the daggers back. Blob left alive, slow, in the row-18 corridor.
T:1205–1211 DL3 — Hungry; ate the food ration (d). Food left: candy bars g, j; lichen corpse m. Explore continues on the N side.
T:1267 DL3 — MISTAKE: wielded the picked-up orcish dagger (o) to kill an acid blob without corroding the sword — it was CURSED and welded to my hand. Killed the blob with it (no splash). Exp 53.
T:1271 DL3 — PRAYED (1st prayer) hoping to uncurse the welded dagger: "shimmering light ... Tyr is well-pleased" but no glow message: minor trouble is not fixed at Luck 0. Prayer timeout now reset (~50–1000). Long sword (a) cannot be wielded until the dagger is uncursed.
T:1358–1361 DL3 — walked to Annootok's store; sell-offer on scroll EIRIS SAZUN IDISI = 100 => base 200 (create monster/earth/taming/amnesia): declined, kept it. Harness wrapped-prompt bug reproduced (#629).
T:1383–1407 DL3 — killed 3 garter snakes (Exp 59). HP 34/38.
T:1411–1425 DL3 — WEREJACKAL (@ form, regenerates, hits for up to 6) adjacent at the `>` room W door (28,14). With the welded d3 dagger melee was a losing, lycanthropy-risking trade: stepped back, engraved Elbereth (degraded at once), threw dagger b (hit), then walked away step by step (a moving monster gets no attack) to the `<` room; it did not pursue into view. Dagger b LEFT on the floor at (28,14). HP 27/38.
T:1431 DL2 — arrived on the DL2 DOWN stairs `>` (48,7) (never found before). Hidden door found at (47,6) while resting.
T:1452–1478 DL2 — killed a newt, a gecko (it bit 4 times: HP 30 -> 22; a welded d3 dagger makes even geckos slow) and a goblin (threw an orcish dagger at me first). Exp 68. HP 20/38: resting on the stairs.
T:1535–1639 DL2 — picked up the goblin's orcish dagger (p, throwable, BUC unknown: never wield). Rested on `>` to 38/38; St and Dx exercise gains. Picked up 2 violet gems at (51,7) (stacked with l => same type as my violet gem).
T:1650–1672 DL2 — explore(): killed a newt in the corridor (an acid blob oozed in through the S door (48,9): left alone); in the `<` room killed a yellow mold (stun-aware loop: attack, then search until the stun clears) — Exp 74. HP 36/38. Shift ends heading to `<` (46,16).
T:1686–1724 DL2 — (shift 3) picked up a yellow potion (q) at (56,19), $3 at (71,17); killed 2 lichens (corpses: m now 2) -> XL4 at T:1733 (HP 49/49). NE room (69-71,4-8) holds only an egg + fortune cookie behind the trap door (71,8): skipped.
T:1737–1773 DL3 — gas spore blocked the only corridor east of the `<` room; lured it into the lit `<` room and killed it at range (dagger p missed, gems: 2 hits) — no damage. Exp 88.
T:1774–1780 DL3 — WEREJACKAL (@ form, wielding my old +0 dagger b) came for me. Fought it in the corner (18,4): first round it changed to jackal form, bit me: "You feel feverish" = LYCANTHROPY (T:1780).
T:1784–1795 DL3 — it summoned 2 jackals; killed both (Exp 90) but the were regenerates faster than the d3 dagger hurts it; HP 49 -> 22. Elbereth came out as "-lbereth" (useless). Walked to `<` (one free bite) and climbed: werejackals don't follow (no M2_STALK).
T:1801 DL2 — on `>` (48,7), HP 21/49, lycanthropic. Plan: rest here; when the jackal transformation comes it RELEASES the welded cursed dagger (drop_weapon: "you must release your weapon"); then pray (lycanthropy = major trouble, ~88% odds at ~530 turns since T:1273) -> purified + rehumanized; wield the long sword, re-wear the dropped armor.
T:1805–1920 DL2/DL1 — killed a newt and a lichen (3rd lichen corpse); an acid blob at the DL2 `<` room N door splashed me twice for 7 (HP 35 -> 21): stopped, went up to DL1. Killed the feral kitten (1 hit, Exp 100), a newt. Hungry at T:1937: ate a lichen corpse.
T:2013 DL1 — on the `>` (54,7): "You turn into a werejackal!" — armor fell off, the CURSED DAGGER WAS DROPPED ("You find you must drop your dagger!"); the small shield and orcish helm fell DOWN THE STAIRS to DL2 (land on the DL2 `<` (46,16)).
T:2016 DL1 — PRAYED (2nd prayer; 743 turns after the 1st; prayer_check 91%): "Tyr is well-pleased. You feel purified. You return to dwarven form!" Lycanthropy CURED, back to XL4, HP 32/49, AC10 (naked). Cursed dagger + studded leather on the floor at (54,7).
T:2017–2025 DL1/DL2 — wielded the +1 long sword (a); picked up + wore the studded leather; went down to DL2 `<` (46,16) and recovered the shield (c) and helm (n): AC2 again. The cursed dagger stays on the DL1 `>` (54,7).
T:2028–2067 DL2 — an acid blob chased me across the level (blocks counted rests); killed it with the long sword (one splash, -2), then a kobold zombie in the `>` room W doorway (47,8). Exp 106. The doorway pile: acid blob corpse + FOOD RATION + brilliant blue potion.
T:2132–2177 DL2 — Hungry again (lichen = 200 nutrition only): ate the 2nd lichen corpse. Destroyed 2 orc zombies at the `>` room W doorway (47,8) with the long sword, no damage. Exp 116. Rested to 49/49 on the `>` (48,7); going down to DL3 to recover daggers b/p and the gems near the `<`, avoiding the werejackal (a fresh bite = new lycanthropy with the prayer spent).
T:2178 DL3 — arrived on `<` (19,9): the werejackal (d form) was adjacent at (19,8) and swung at once (missed). Went straight back up.
T:2240 DL3 — second try after 60 turns: it was STILL at (19,8) (levels are frozen while you are away, so it never reverts to @ or wanders); it bit me on arrival (HP 46/49, no fever) and summoned 4 jackals + a fox. Climbed at once. LESSON: a monster left adjacent to stairs stays there; don't re-enter that way. New route to DL3: the DL2 trap door (71,8) (25% chance of a deeper shaft).
T:2275 DL2 -> DL5 — stepped onto the DL2 trap door (71,8) to bypass the camped DL3 `<`: "You fall down a deep shaft!" — landed on DL5 at (63,6) in a small room (59-65,4-9) with a ring on the floor. HP 49/49, XL4. No stairs known on DL5/DL4: find `<` first; Elbereth is the only escape until then.
T:2311–2403 DL5 — quiet level: found `>` (70,16), `<` (59,16), a diamond ring (w), ate the food ration (T:2331). Hidden door (47,18) (locked); kicked open the locked door (54,5) in 4 kicks.
T:2403–2509 DL5 — explore() mapped the west: FOUNTAIN (26,8) in the NW room; scroll GARVEN DEH (x) + $25 at (25,9); figurine of a coyote (y) at (25,6).
T:2531–2538 DL5 — imp in the corridor (39,13): killed in 3 hits (HP 49 -> 42), Exp 131. It dropped a WAND.
T:2565 DL5 — engrave-tested the imp's marble wand: "This marble wand is a wand of lightning!" — burned ELBERETH into the floor at (45,18) in the big S room (permanent safe square on DL5). Chest at (38,5) not yet looted.
T:2565–2605 DL5 — blinded by the lightning flash for ~40 turns; waited it out on the burned Elbereth. Chest at (38,5) was empty (T:2621).
T:2638 DL5 — read the scroll of identify (k) on the diamond ring: uncursed RING OF FIRE RESISTANCE (w). Shift 3 ends on the burned Elbereth (45,18): HP 49/49, XL4 (Exp 131), AC2, $52, T:2638. Next: XL5 then Excalibur at the DL5 fountain (26,8).
