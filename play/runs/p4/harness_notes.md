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
