# p4 harness notes (the bug tracker: step numbers, what happened, what you expected)

## Shift 1

1. **explore() reports reachable frontiers as "travel couldn't reach"** (#427 DL1 T:258; #1191 DL2 T:873).
   - #427: `blocked: frontiers [(54,18), (55,14), (56,10)] travel couldn't reach`. At #493, `travel(56,10)` walked
     there at once, and the next explore() explored the whole east part of the level (3 more rooms).
   - #1191: `frontiers [(21,11), (24,9), (25,10), (29,12)] travel couldn't reach; the known routes squeeze
     diagonally between rock at [(24,9)]: NetHack refuses that while your inventory weighs more than 600`. My pack
     weighed about 250. (29,12) is the arrival room's plain east doorway. `travel(29,12)` worked right after, and
     explore() then found the locked door, the shop and 3 rooms.
   - Both times the frontiers were at or next to the arrival (up-stairs) room.
   - Expected: explore() goes to them, or at least doesn't call them unreachable. A player who trusts the verdict
     skips half the level; the Mines branch or a shop could be there. It cost me about 4 calls.

2. **go_down() silently leaves the pet behind** (#704-#739 DL1->DL2 T:463-516; #1672-#1700 DL2->DL3).
   - #739: `stairs: travel(with_pet): your pet is out of view ... going on without it` and `your pet (tame kitten)
     is not next to you — taking the > without it`. There was no pause, although the kitten was only a few squares
     behind (it had stopped to kill a grid bug). Going back for it cost 5 calls.
   - #1700: the exec paused on arrival (new monster: hobgoblin), so any pet message was lost. I only found out
     from the map later that the kitten had stayed on DL2.
   - Expected: when go_down()/go_up() started in pet-keeping mode and the pet drops out of view, PAUSE
     (PetLost, as travel(with_pet=True) documents) instead of deciding for the player. At the least, say "pet left
     behind" in the arrival snapshot, which survives a pause. PLAYBOOK C says "keep the pet".

3. **Opening locked boxes has no helper, and the ad-hoc way left the wrong weapon wielded** (#1724-#1742,
   #2172-#2215).
   - `loot_all()` says "locked" but offers nothing more (without a key). In my kick loop, "THUD!" paused
     (#1727); kick_door's ok list doesn't cover boxes.
   - At #2203, 15 kicks in a row gave only THUD. So I used #force with a spare orcish dagger. The exec paused on
     "You are beginning to feel hungry" (#2208) BEFORE my re-wield line. I was then wielding the orcish dagger, and
     the obs had NO warning. The warning exists only for non-weapons and empty hands.
   - Expected: a `force_lock()` / `open_box()` helper that kicks or forces with a spare blade (never the main
     weapon) and re-wields in a `finally`. Also an obs note `!! you wield X, not your usual weapon (a)`.

4. `pickup()` with no pattern picked up a **large box (350 wt)** (#2159). My mistake, but a pickup of a container
   or anything heavier than ~100 should need a pattern, or at least print the weight gained.

5. `inventory()` 'buc' is '' for the worn "+0 orcish helm" (#1235). With implicit_uncursed, a known enchantment
   and no curse word means uncursed. '$' is also in the list with buc ''. My "all unknown-BUC items" loop tried to
   drop gold and the worn helm onto the altar. Expected: infer 'uncursed' there, and give coins their own class.

6. `travel()` while in a pit (#2612-#2622): `NavError ... the step to (3,10) failed; messages: ['You are still
   in a pit.']`. Expected: keep trying the step (climbing out takes a few turns), like explore() did.

7. (minor) The naming prompt `Call a marble wand:` paused my script (#2554), although the script's next do() was
   the answer. `cont --reply` + the skip-duplicate logic handled it well. A `call_type(letter, name)` helper would
   save a call. engrave_test could offer it when the verdict isn't auto-identified (polymorph wasn't).

Worked well: auto-farlook labels (peaceful gnomes/dwarf/hobbit, werejackal's LYCANTHROPY note); hunt()/fight()
one-liners; sell_offer() + price_id (the Charisma surcharge was learned automatically); engrave_test (light,
polymorph); go_down(to='Mines') resolving the branch by elimination after I took the other '>'; kick_door().

### Top 3 (ranked)
1. explore()'s false "travel couldn't reach" frontiers (#427, #1191): it hides whole parts of the level.
2. go_down()/go_up() abandon the pet without pausing (#739, #1700).
3. No safe lock-opening helper, and no obs warning when a non-main weapon stays wielded after a pause (#2208).

## Shift 2

First half (T:1994-3199, previous player, cut off by a container restart; from the journal/state): no notes were
written. Journal items that touch the harness: a yellow light reached me DURING explore() ("A yellow light blocks
your path." -> explore waited a turn) and exploded (Blind ~98 turns, T:2223). PLAYER.md now says travel refuses
legs within 2 squares of a known exploder, so this may be fixed already; not re-tested. The daemon restart lost
nothing: `history` and the run files were intact (journal entries T:2496-3199 were missing and are reconstructed
from state.md).

Second half (T:3199-4257, steps #0-#1244):

1. **Shop rooms are recorded on the WRONG side of the door -> the shop guards are OFF inside shops and ON in the
   street** (safety). #974/#1000/#1158: "— in Bojolali's delicatessen (no throwing/firing/digging down here)" at
   (46,16) and (48,16), which are outside in Minetown's street; #1047 "in Izchak's lighting store" at (32,17) by
   the fountain; #1168 "in Chibougamau's general store" at (44,12) in the street. Inside the real shops there was
   NO tag: #987 at (44,16) in Bojolali's, #1043 at (30,13) in Izchak's, #1107/#1110 at (44,7)/(45,7) in
   Chibougamau's. So a throw or a dig down inside those shops would not have been refused.
   - Cause (I read the code, didn't change it): `game.py _room_rect()` on a door square steps inside with
     `next(d for d in (1, -1) if scr.at(x+d, y) not in _ROOM_EDGE)`. It tries +1 (east/south) first. All three
     doors were in the shop's EAST or SOUTH wall, and in Minetown the square outside the door is street floor (at
     #974 and #1018 it even held my dropped pick-axe '('), so it picked the outside and scanned the street.
   - Expected: the interior side is where the shopkeeper stands next to the door, or the side you did NOT come
     from (the previous hero square is outside), or the side whose wall-to-wall scan is small and closed.
2. **explore()'s travel legs step next to a dangerous hostile that is out of view behind a corner at its
   last-seen square** (#135 T:3245: 55->31; #207 T:3452: 66->45). A hostile BLACK UNICORN (speed 24) hid at
   (39,16) behind the wall corner of a 1-wide passage. Each time the leg (explore.py:446, the '.' that confirms
   the travel cursor) moved me one square west, next to it, and it got 2 rounds (butt d12 + kick d6 each).
   - `obs.gone` / `last_seen()` knew where it was. Expected: explore()/travel() keep 2+ squares from the
     last-seen square of a non-trivial fast hostile that left view in the last ~20 turns, or pause before a leg
     that passes next to it.
   - Unicorn specifics worth a note: it never steps next to a hero it can see (monmove.c NOTONL), so it only
     fights when YOU step next to it. Its note says only "fast (speed 24)" and threat() rated it 'normal' at
     XL6/66 HP although it did 20-24 per turn.
3. **Docs: the magic lamp's base price in 3.6.7 is 50, not 500** (objects.c line 665: `TOOL("magic lamp", "lamp",
   ..., 50, COPPER, ...)`). PLAYBOOK A.1 says "base 500; an oil lamp is 10", and so did my brief. At #1043 Izchak
   quoted 89zm = 50 x 4/3 (Cha 8-10) x 4/3 (unID surcharge). It WAS the magic lamp: it flashed amber (blessed)
   at #1200 and gave a wish at #1232. A player trusting "500" would have walked past it. `price_id('TOOL_CLASS',
   buy=89)` would probably have said it (I didn't try).

Smaller:
4. #755 T:4046: after I killed the Uruk-hai that zapped the steel wand, the NEXT Uruk-hai got its note "ZAPPED A
   WAND OF STRIKING AT YOU (T:4045)". The zapper was dead and the wand lay on the floor (I picked it up at #773).
   Expected: drop the note when the zapper dies (the note is per name by design, but here it misleads).
5. #658 T:3989: explore() returned `stopped: getlin 'Call a scroll labeled ETAOIN SHRDLU:'` right after
   `cont --reply 'create monster?<CR>'` had answered the prompt (heard an Uruk-hai read a scroll). Expected:
   explore goes on after the reply. It cost one call.
6. Monster notes: Uruk-hai/hill orcs say "packs" but not that their orcish arrows are ALWAYS poisoned
   (makemon.c m_initthrow), i.e. 1 in 30 instadeath per hit without poison resistance (#676 T:3998, one hit).
   A note like "archer: poisoned arrows (instadeath 1/30 per hit w/o poison res): don't stay lined up" would help.
7. PLAYER.md: attacking from an Elbereth square "costs -5 alignment". For DUST in 3.6.7, attack() calls
   u_wipe_engr(3) (uhitm.c:428) BEFORE hmon -> wakeup -> setmangry (the hypocrisy check), and the wipe always
   garbles it, so there is no penalty. The guard is fine; the sentence is inaccurate (PLAYER.md says it right in
   the Elbereth section).
8. #147 T:3248: rest_on_elbereth() paused "couldn't get a clean Elbereth here" after two garbled engravings in a
   row (1/25 per letter + random decay). Expected: a third try (it's one turn), then pause.
9. #995 T:4135: travel() out of Bojolali's right after paying stopped with "Bojolali blocks your path." (the
   shopkeeper stood beside the door). A second travel worked. Minor.

Worked well: rest_on_elbereth (hundreds of turns, re-engraving by itself); fight_until_clear(hold=N) in the nook
against the Uruk-hai pack; hunt(); throw() down a diagonal at the floating eye; desmap.identify() naming Bustling
Town at once and travel() walking the fixed map over unseen ground; the altar test with the D menu (menus
handled cleanly); farlook prices from inside the shop; rub() stopping at the wish prompt and re-wielding
Excalibur after cont --reply; the WISH PROMPT pause text; prayer_check() counting the wish.

### Top 3 (ranked)
1. Shop room on the wrong side of east/south doors: guards off inside shops, on in the street (#987, #1043,
   #1107 vs #1000, #1047, #1158, #1168) — game.py _room_rect().
2. explore()/travel() legs step next to an out-of-view dangerous hostile at its last-seen square (black unicorn,
   #135 and #207: -24 and -21 HP).
3. PLAYBOOK: magic lamp base price is 50 in 3.6.7, not 500 (#1043: the 89zm lamp was the magic lamp).

## Shift 3

1. **Stale shop rooms survive the fix** (#24, #30, #33 T:4344-4369): at (45,19), (46,18), (47,18) — all in
   Minetown's street — the obs said "— in Bojolali's delicatessen (no throwing/firing/digging down here)".
   run/p4/harness_state.json still holds the shift-2 rectangles: Bojolali's [46,14,49,19] (real shop x42-44
   y16-17), Chibougamau's [40,9,52,12] (real x43-45 y5-7), Izchak's [24,15,31,19] (real x29-31 y11-13). The fix
   only helps NEW welcomes; old wrong records are never re-checked. The live game's harness_state may have the
   same stale rectangles from before the fix: worth a one-off check/migration (drop a shop rect that doesn't
   contain its shopkeeper's post / isn't wall-enclosed).
2. **go_up() on identified Minetown: "NavError: no '<' known on this level"** (#14 T:4336). PLAYER.md says that on
   an identified special level with no '<' seen, go_up/go_down travel to where its fixed map puts them. Minetown's
   stairs are in random levregions (up: x 1-20 at the west edge), so the map can't pin them. Expected: say so
   ("the fixed map puts '<' in region x1-20: head_to() west") or head_to() that region itself. I used
   head_to(8,11), which found it at (15,13).
3. **desmap.identify() false positive: ordinary rooms-and-corridors DL7 identified as 'bigrm-1'** (#551 T:4690):
   `{'level': 'bigrm-1', 'ox': 3, 'oy': 3, 'score': 88, 'good': 154, 'bad': 30}`; the `where:` line then showed
   "(bigrm-1 map at offset (3,3): desmap.show())". The Big Room only exists on DL10-12 (dungeon.def @ (10,3)) and
   is one huge lit room; 30 bad squares should also rule it out. Risk: travel()/desmap.walk() route over "unseen"
   squares of a wrong fixed map. Expected: filter candidates by the dungeon's depth ranges (oracle 5-9, bigroom
   10-12, medusa, castle...) and reject any match with many bad squares.
4. **explore() hid the real reason it stopped (squeeze)** (#648 T:4747): `blocked: frontiers [(39,16), (39,17),
   (38,18)] travel couldn't reach [the last 8 legs went back and forth over 3 squares, showing nothing new]`.
   The only way on was a diagonal corridor step (40,15)->(39,16) between two rock squares; a manual 'b' gave "You
   are carrying too much to get through." (#649). In shift 1 the verdict named the squeeze; here it didn't, and it
   spent 8 legs oscillating. Expected: name the squeeze and suggest tunnel()/dig one orthogonal square
   (tunnel(40,16) fixed it in 1 dig).
5. (minor) fight()'s re-wield step paused on "The rabid rat misses!" (#180 T:4467): the monster's routine melee
   during the re-wield turn should be as routine as inside the fight itself. Cost one call.
6. (minor) A dark corridor explored via frontiers() + travel() advances ONE square per leg (#1177-#1260: 5 legs for
   5 squares). explore() did the same earlier. `do('Gh')` ran the whole corridor in one step (#1262). Maybe let
   explore() use a G-run along a corridor frontier.
7. (info) A digging dwarf keeps making new frontiers: find-loops of explore(max_legs=3) x40 never reported
   "explored" on DL6 (T:4747-4870).

Worked well so far: travel()'s lurker detour round the yeti's last-seen square (#24, 32 steps, clear message);
hunt() (yeti, ogre); tunnel() round the hole and the squeeze (1 dig each, weapon re-wielded); go_up() chain
DL8->DL4 and go_down(to='Dungeons') resolving the branch; eat(pattern=...) with corpse check.
8. **A nymph's charm leaves your MR body armor UNWORN and the obs doesn't say so** (#1346 T:5057): "The mountain
   nymph charms you. You gladly start removing your dragon mail. ... You gladly start removing your helm. ... steals a
   +0 orcish helm!" The THEFT pause and the STOLEN line named only the helm. The dragon mail had come off but stayed in
   the pack (the 2nd charm replaced the steal target), so I had NO magic resistance and AC 4 — only the AC number
   showed it. Expected: after any "You gladly start removing"/"You finish taking off", an obs line like `!! X (gray
   dragon scale mail) is NOT WORN — W X` (at least for body armor / cloak / MR or reflection sources).
9. **A returning thief doesn't pause** (#1386 T:5074): the nymph that had just robbed me came back into view at d=9;
   no pause (a known monster coming back isn't "new"). Only my own check in the script saw it. Expected: a monster
   with a THEFT on record (or any thief: nymph, leprechaun, monkey) pauses every time it comes into view.
10. **Lurker pause for a square in plain view, for a monster known to have teleported** (#1351 T:5062): "travel: the
    next leg passes (44,5), next to where the mountain nymph was last seen at (45,5) ... out of view now (dark, or
    behind a corner or door)". (45,5) was diagonal-adjacent to me in a LIT room (nothing there), and the harness
    itself had logged "the thief teleported off". Expected: skip last-seen squares that are in view now, and drop
    the zone for a monster seen to teleport.
11. **The wrong 'bigrm-1' id (item 3) walked me into rock** (#2062 T:5392, DL9 = the Oracle level): "travel: the
    identified special-level map has a 6-step way to (60, 7) (the seen map: none) — walking it with
    desmap.walk()" -> "It's solid stone." DL9 was ALSO identified as bigrm-1 (score 43, good 62, bad 13), and the
    `where:` line kept saying bigrm-1 after telepathy showed "peaceful Oracle" there. desmap.identify()'s candidate
    list has no depth filter for Dungeons-of-Doom specials (_candidates by file only) and `bad*4 > good` lets 30 bad
    squares pass. The real way in was a door (57,7) reached from an unseen corridor square (56,7) south of (56,6).
12. (info) Oracle-level deduction worked from the fixed Delphi position (screen x33-45, y7-17): a desmap helper
    "could this level be the Oracle?" (centre box overlaps a seen room/corridor -> no) would save the live game
    exploring whole levels. I needed a full DL6 explore to rule out DL5.
13. **SAFETY: the floating eye's note says "corner it and kill it" in Sokoban** (#3447, #3452 T:6297): `e floating eye
    ... !! NEVER melee (paralysis -> death). Ranged only, or ignore. Corpse = telepathy — BUT teleporting is blocked in
    Sokoban: corner it and kill it`. The Sokoban no-teleport suffix meant for nymphs/leprechauns got appended to the
    floating eye (probably a match on "telep" in "Corpse = telepathy"). A player following the last words melees a
    floating eye = paralysis = death. The live game enters Sokoban next.
14. (minor) The same group of 3 slow chickatrices paused as "new monster" twice (#3410 T:6280 and #3425 T:6287:
    "chickatrice at (49,14) (NEW)"): the swarm window (5 turns / 4 squares) is short for speed-4 monsters.
15. (minor) The obs `objects:` line kept `" amulet/web (31,7)` after farlook(31,7) had said "a spherical amulet" (#1686).
16. (info) "!! harness code on disk is newer than this daemon's core" was on every obs from #33 on (other agents
    committed p3 fixes mid-shift). I did NOT `bin/nh reload`, to keep tactics and core consistent.
17. (my scripting, maybe a helper) `obs.hostiles(3)` includes sessile molds; my loop "if hostiles near:
    fight_until_clear()" spun 35 times on a brown mold (#1942). A `hostiles(r, mobile=True)` would help scripts.

Worked well (second half): sokoban.solve() on levels 1 and 2 (34 pushes, zero wrong pushes): it paused exactly for a
lichen and a fog cloud trapped in pits on boulder routes, a rock piercer on a push square, an earth elemental and
rothes, and resumed from the board ("resuming step 12 after 20 of its pushes"); the COCKATRICE HISS pause with the
cure named (#3426); unlock() on the locked stair-room door with the booby-trap note (#3364); go_up()'s NavError
naming the locked door and remedies; go_up(to='Sokoban') by elimination (#2359); the leprechaun-gold obs warning
(#1704); tunnel() (2 uses); the unicorn horn via `do('aL')`; #enhance through the menu API.

### Top 3 (ranked)
1. desmap.identify() false 'bigrm-1' on ordinary DL7 (#551) and on the ORACLE level DL9 (#1772), then travel()
   walked the wrong fixed map into solid stone (#2062). No depth filter for Dungeons-of-Doom specials (bigroom is
   DL10-12 only), and `bad*4 > good` accepts 30 bad squares. The live game is heading for the Oracle (DL5-9) now.
2. SAFETY: Sokoban suffix "corner it and kill it" on the FLOATING EYE's note (#3447) — the live game's next branch.
3. Nymph charm: the GDSM (MR) left UNWORN in the pack with no obs warning (#1346), and the returning thief didn't
   pause (#1386). Also: stale wrong shop rectangles from before the fix still in harness_state (#24) — check the
   live game's file.

## Shift 4
1. **sokoban.solve() kept pushing while a hostile horse meleed me for 12 turns** (#433-#475, T:6567-6579): "The horse
   kicks! | The horse bites!" x8 lines (HP 70 -> 62) during steps 15-16, no pause; solve() ended with "hostiles in
   view: horse at (45,17)" when it was ADJACENT. The horse was a known monster ("horse [seen: telepathy]", seen from
   T:6345), so no new-monster pause, and each hit was small. A soldier ant or a cockatrice in the same spot would
   have been attacking the whole time. Expected: inside solve(), an adjacent hostile that ATTACKS (any "The X hits/
   kicks/bites/stings" line) pauses (or solve() fights it when auto_fightable), like travel()'s blockers.
2. (minor) engrave_test() paused on the WAND OF ENLIGHTENMENT's attribute menu (#303 T:6481: "unexpected menu prompt
   'P4 the Valkyrie's attributes:'"). `cont --reply '<Esc>'` finished it fine ('t': enlightenment, auto-identified).
   Expected: recognise "You feel self-knowledgeable..." + the attributes menu, print its lines (they are useful:
   "You can safely pray", alignment) and Esc it.
3. (info, good) An unseen monster on hole (44,17) behind the boulder blocked step 11 (#289): the solver's pause text
   was right ("kill it first ... throw weapons / zap an attack wand from a square in line with it"). The `I` note says
   "BLACK LIGHT ... or a stalker": a stalker isn't mindless (ESP would show it). When the `I` stands on a HOLE it must
   fly/float (gas spore, fog cloud, lights, spheres, vortices), and "unseen" there came from the boulder blocking
   sight, not invisibility. Useful additions: "thrown weapons and rays pass over boulders" and "a weapon that hits a
   monster standing on a hole falls to the level below" (my orcish dagger did, #357).
4. (minor) solve() refuses to push toward a remembered `I` it can't clear (#290); a manual push costs no time when a
   monster is behind ("You hear a monster behind the boulder", 0 turns): a retry-each-turn option (wait/search, try
   the push, up to N turns) would handle a monster that wanders off. Here it never moved (greedy approacher).
5. (minor) `approaching: large cat` paused (#479) for a cat inside a room whose door was closed (and LOCKED): it could
   not reach me. Doors that are closed/locked between us could exempt a no-hands animal.
6. (minor) unlock() ends with "opening it is safe" but leaves the door shut; the first #open failed with "The door
   resists!" (stuck; #492). An `open_door(x, y, tries=5)` that retries "The door resists!" would save a call.

Worked well: hunt() on the sleeping nymph (Stealth; killed before she acted), read_identify() with my own priority
regexes (amulet first), fight()'s EXPLODER note on the shocking sphere, zap() through the boulder (sleep ray; the
bounce couldn't reach me), throw() over the boulder, fight_until_clear() at the doorway, eat(pattern=...) + corpse().
7. **hunt() plans diagonal squeezes between two boulders in Sokoban** (#550 T:6719): `{'reason': "no way toward the
   giant mimic at (37, 15): the step to (33, 14) failed (['You are carrying too much to get through.'])"}` — the step
   (32,15)->(33,14) passes between boulders (32,14) and (33,15). In Sokoban that squeeze is ALWAYS refused
   (hack.c cant_squeeze_thru returns 3 for the hero in Sokoban; elsewhere 2 when inventory > 600). A legal route
   existed via row 16; travel(36,15) (NetHack's own travel) found it. Expected: hunt()/path_to() treat a diagonal
   between two boulders/rock as blocked (always in Sokoban, and when the pack is over 600 weight).
8. **engrave_test() says "an Elbereth is under you now" without reading it back** (#1723 T:7563): the next `:` read
   "Edbereth" (#1728). Harmless this time (it only over-restricts attacks from that square), but a player could
   trust a garbled Elbereth as protection. Expected: read it back like elbereth() does (or say "unverified").
9. (minor) The unicorn-horn messages are easy to misread: "Nothing happens." = no trouble at all, "Nothing seems to
   happen." = troubles left but none fixed this time, "This makes you feel better!" = an ATTRIBUTE point restored
   (apply.c 2080), NOT a cure. A helper `unihorn(until='nausea')` that applies until the named trouble's own cure
   line ("You feel much less nauseated now.") would help — my first loop stopped on "feel better" while the vomit
   countdown ran on (it then confused me at T:7133 mid-Sokoban; I had waited instead of pushing).
10. (minor) `approaching:`/`new monster:` pauses for SLEEPING zoo monsters seen through walls by the ESP amulet cost
   ~6 calls on Sok4 (#1588-#1610: hill orc, rock piercer, lizard, horse... one at a time as each came within 8).
   The zoo's entry message can't have fired yet (never entered). A per-room "sleeping crowd behind a wall" summary
   pause (once) would be enough.
11. (info) zap() through a boulder and down a corridor worked (#350, #1610), and throw() over a boulder (#357); the
   solver's "monster behind the boulder" pause text (#290) pointed at exactly these remedies.
### Top 3 (shift 4, ranked)
1. sokoban.solve() kept pushing while a known hostile (horse) meleed me for 12 turns (item 1, #433-#475): no pause for
   an adjacent attacker inside solve().
2. hunt() routes through Sokoban-illegal diagonal squeezes between boulders (item 7, #550).
3. engrave_test() reports an Elbereth it never read back (item 8, #1723) + unicorn-horn result messages (item 9).

## Shift 5
1. (info, good) Stealth + one-at-a-time kills of a sleeping zoo worked perfectly with fight() + my own approach()
   (path_to + walk_path to a free square next to the target): 30 kills, no sleeper woke from noise. forget_room()
   was needed first. A zoo helper `clear_sleepers(targets)` in tactics would save the boilerplate.
2. **ESP/telepathy don't show MINDLESS monsters** (#17 vs #27): my T:7521 "empty squares" plan (object detection +
   ESP) was wrong — mummies, zombies, blobs, jellies sat on them. The harness could flag, for a planned route over
   squares only "seen" by telepathy, "mindless monsters are invisible to telepathy: this square may be occupied".
3. (minor) A getlin naming prompt ("Call an emerald potion:") opened INSIDE fight() when a thrown potion hit me
   (#156). The exec paused correctly, but fight() then returned with the target alive after `cont --reply`,
   so my loop stopped (#157). Expected: fight() resumes its blows after the prompt is answered.
4. (minor) The sergeant's wand pause came as a plain "message" pause (#220) although it names the wand (zinc = cold)
   — fine, but the "ZAPPED A WAND OF COLD" note could mention "cold rays shatter POTIONS in your pack even when you
   resist cold" (I lost 2 potions, #222). Suggest: bag potions before fighting a known cold/fire zapper.
5. (minor) descend(3) raised NavError "no '>' known on this level" after 2 of 3 levels when the 3rd level (DL10) had
   no known '>' (#464). Expected: return early with a note (like at a prompt) — the caller's next statements were lost.
6. Trivial newcomers (grid bug #648, lizard, rabid rat, giant rats) paused multi-level trips ~6 times this shift. I
   wrapped trips in `with monster_filter(nontrivial):` (threat(name) != 'trivial'). A built-in
   `descend(n, pause_trivial=False)` / `go_up(..., pause_trivial=False)` would save calls.
7. (info) travel(55,17) from the Minetown '<' walked 3 squares and stopped next to a hostile werewolf that had been
   "not coming" (#778): fine (NavError explained it), but a DANGEROUS hostile seen within 6 squares in the last few
   turns could make travel pause BEFORE the leg that brings it adjacent (lycanthropy risk).
8. (info, good) buy_protection() and bag_put/bag_take worked first time (#855, #909); altar drop-testing by hand
   worked; an `altar_test(letters)` helper returning {text: buc} would be a nice addition.
### Top 3 (shift 5, ranked)
1. Mindless monsters are invisible to telepathy/ESP (#17 vs #27) — flag route squares only "known empty" by
   telepathy + object detection.
2. fight() stops after an in-fight getlin prompt ("Call an emerald potion:") is answered (#156-#157).
3. Trip helpers (descend/go_up/travel) pause for trivial newcomers (#648 etc.) and descend() raises instead of
   returning at a level with no known '>' (#464).

## Shift 6
1. **desmap.identify() false positive** (#233, T:8350): on Mines level 7 (DL11) it returned minend-1 with 42 good /
   10 bad squares and the `where:` line named it ("minend-1 map at offset (2,4)"). Mines' End can only be the branch's
   LAST level (dungeon.def (8,2) -> rn1(2,8) = 8 or 9 levels; here Mines 1 = DL5). Expected: minend-* only on the
   Mines' bottom level (or at least Mines depth >= 8), and no identification with 10 mismatches. The fixed '<' it
   placed at (38,8) was next to a seen wall on an open row. My own helper trusted it and stopped a descent.
2. **pickup(pattern, force=True) doesn't lift the gray-stone guard** (#707, T:8560): "refusing to pick up the gray
   stone ... force=True once you know" — but pickup('gray stone', force=True) raised the same PermissionError;
   do(',', force=True) worked. (The Catacombs' des places only hold a luckstone or a flint.) Either pass force through
   or change the message to say `do(',', force=True)`.
3. **trek()/travel() blocked by a STALE monster glyph** (#905, T:8695): "the way is blocked by soldier at (53, 12) —
   then trek again", 6 times with no game time, while that soldier had walked off in the dark (its '@' stayed on the
   map; the monster list no longer had it there). Expected: a monster glyph on a dark square the hero can't see and
   doesn't sense is uncertain — walk up to it (as trek(54,12) then did: the lurker pause fired and the glyph cleared).
4. (idea) desmap.show() lists no fixed OBJECTS: for the Catacombs the luckstone/flint $place squares ((3,17), (3,19),
   (70,10) here) had to come from mines.des by hand. Listing des OBJECT/TRAP places (with "one of" for shuffled
   $place lists) would make Mines' End (and the Castle's wand chest) one call.
5. (minor) exec pauses on routine monster item handling ("The soldier picks up an orcish bow.", "puts on an orcish
   helm", "removes a pair of low boots") — needed -a patterns in every call during the soldier fight.
6. **The false minend-1 id (item 1) also steered travel()** (#1229, T:8857, DL11): "travel: the identified
   special-level map has a 12-step way to (53, 15) (the seen map: none) — walking it with desmap.walk()" — over floor
   that doesn't exist; head_to()/explore() wasted ~2 calls. The id is cached in game.desmap_ids per level, so it kept
   coming back. SESSION-ONLY WORKAROUND still live in the p4 kernel: I wrapped `desmap._candidates` to drop minend-*
   maps on any Mines level but 13 and popped DL11's cached id (`desmap._p4_patched = True`). A daemon restart/reload
   removes it. Suggested fix: _depth_ok() for the Mines (minend only on the branch's bottom level; minetn at Mines
   level 3-4... per dungeon.def), and reject fixed-offset matches with bad*4 > good as the sliding path already does.
7. (minor) pay() raised RuntimeError "Pay whom? — several shopkeepers in range" (#1641) although I stood INSIDE
   Bojolali's shop, which the harness had recorded. It could answer with the shopkeeper of the shop you're in.
8. (minor) Minetown noises paused execs: "The dungeon acoustics noticeably change.", "You hear a door open." (#1591,
   #1680). Routine once per level at most.
9. (idea) `ascend(n)` / `descend(n, explore=True)`: explore for an unknown '<'/'>' then take it (my own mines_up /
   mines_down helpers did this; they're in the p4 kernel namespace). DL11's '<' needed 3 calls of head_to/explore.
10. (info, good) zap('F', dir) at an ADJACENT mind flayer twice (#1380, #1512) and the "TELEPORTED by a monster's hit
   (quantum mechanic)" pause (#1490, #1509) were exactly right; descend(6, to='Dungeons') and
   go_down(pass_hostile=True) past a sleeping nymph worked first time; tunnel() through the Catacombs was excellent.
11. (minor) hunt('quantum mechanic') walked up to it and it got the first hit (teleport). For monsters whose HIT is
   the danger (quantum mechanic, nymph, leprechaun), hunt could wait for them to step adjacent (fight_until_clear
   style) instead of stepping into their reach.
### Top 3 (shift 6, ranked)
1. desmap false identification (minend-1 on Mines level 7, 42 good / 10 bad) that is cached AND drives travel()
   routes over non-existent floor (#233, #1229).
2. trek()/travel() refuse forever (no game time) because of a STALE monster glyph on a dark square (#905).
3. pickup(pattern, force=True) doesn't lift the gray-stone guard; the refusal message tells you to use force=True
   (#707).

## Shift 7 (T:9333-9927)
- #57 T:9380 fight(28,6) paused on "The orc mummy attacks a spot beside you." while I was INVISIBLE (the stalker
  corpse). Expected: invisible-hero miss lines ("attacks a spot beside you", "strikes at thin air", "swings wildly and
  misses") are routine inside fight()/fight_until_clear()/travel(). Worked around with -a patterns.
- #773 T:9780 explore() LURKER pause for a flaming sphere "last seen at (40,11) 7 turns ago" — it had EXPLODED at T:9774
  ("The flaming sphere explodes!" after my hit). An exploding sphere/gas spore/light is dead: drop it from last_seen/
  lurk zones when its explosion message shows.
- eat(pattern=..., force=True) always answers "n" to "Continue eating?" -> the corpse stays partly eaten and gives no
  intrinsic (cpostfx runs only at the end). Idea: eat(finish=True) that answers "y" when a nutrition UPPER BOUND
  (tracked from the last "beginning to feel hungry" = 150, + nutrition of everything eaten since, - elapsed turns)
  stays below ~1800. I did it by hand twice (Grey-elf corpses) — fine, but easy to get wrong.
- eat() does not resume a meal interrupted by a benign status change ("You are no longer invisible." -> "You stop
  eating the Grey-elf corpse."): a second eat() call was needed.
- DL11 T:9751-9816: two wandering gray unicorns re-triggered "new monster: gray unicorn" pauses 4+ times as they left
  and re-entered view (the "known monster coming back into view" rule didn't catch them — two of the same species?).
  Cost ~5 calls; I added -a 'new monster: gray unicorn'.
- dig('>') paused for a gray unicorn "in view" 2 squares away. Correct by the rules, but unicorns never close in
  (NOTONL): maybe only pause for unicorns when adjacent.
- "!! harness code on disk is newer than this daemon's helpers" appeared 4 times this shift (tactics edited during
  play); `bin/nh reload` between execs worked each time.
- Good: read_identify() with my regex priorities; the shop floor walk + here() gave every price in one exec; pay()
  and bag_take/bag_put with '$' were smooth; fight_until_clear(ignore=('gray unicorn',)) held the corridor well.

## Shift 8 (T:9820-)
- #37 T:9835 (after the container restart + NetHack `recover` to T:9820): go_down() -> travel(2,5) -> head_to(2,5)
  raised "no reachable frontier left (tried 0)" and `screen_frontiers()` returned [] (#43) although the screen showed
  an unexplored doorway (21,18) and a closed door (13,4) with blank ground behind them. The harness's per-level memory
  still holds the UNDONE exploration of DL13 (T:9821-9927: '>' (2,5), fountains, leprechaun hall), so it believes
  those squares were seen. Expected: detect a restore (turn counter went BACKWARD, T:9927 -> T:9820, or the game's
  map lacks squares the harness remembers) and drop/reconcile per-level seen-map memory newer than the restored
  turn; at least compute frontiers from the current screen. Worked around with a hand-made corridor follower
  (#45-#55); remembered features ('>' (2,5)) were right, since the level itself existed before the checkpoint.
