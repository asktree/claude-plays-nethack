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
