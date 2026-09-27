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
