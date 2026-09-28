# live — notes from the coach (dev session)

The coach watches the public ttyrec (`scripts/watch_ttyrec.py ClaudeAscends --history 3`) and practises the
same character in local games. Read this before each shift; append "ack T<turn>: ..." under an item you acted on.

## 2026-09-27 23:45 UTC — harness update on main (pull + restart the live daemon before the next shift)

`git pull --rebase`, then `bin/nh --game live daemon` (core files changed: game.py, kernel.py, mapscan.py,
render.py, tracker.py). What changes for the live game:

- **Your pet**: `go_down()`/`go_up()` no longer leave the little dog behind on their own. When it was around (in view
  within 7 squares at the start, in view now, or seen on this level in the last 60 turns) but isn't next to you at
  the stairs, they raise `PetLost` and press nothing. Fetch it, wait (`hold(n)`), or `go_down(with_pet=False)` to
  leave it. A pet that stays behind (so, or "still eating") gets a `PET: ... did NOT come along` line in the obs.
- **Weapons**: the harness knows your usual weapon (the long sword, a). The obs warns
  `!! you wield b - ..., not your usual weapon (a - ...)`. `fight()` wields the sword again first if a pick-axe
  from a dig is still in hand.
- **Locked boxes**: `force_box()` pries one open with your known-uncursed spare dagger (b), then wields the sword
  again; never kick boxes with potions in them. Locked doors: `kick_door(x, y)` (never a shop door, nothing in
  Minetown).
- `pickup()` with no pattern leaves heavy things (boxes, heavy armor, big corpses): name them in a pattern.
- `explore()` walks around boulders that NetHack's travel stops at, instead of calling that part "unreachable".
- `dip()`: in MINETOWN, "The flow reduces to a trickle." / "Hey, stop using that fountain!" now read
  `TOWN FOUNTAIN WARNING — STOP`. The next dry-up angers the Watch. Dip for Excalibur outside Minetown.
- Confused or Stunned next to water/lava: moves are refused (a random step into lava burns the bag).
- `call_type(letter, name)` names an unidentified type, e.g. after an engrave-test.

## Observations at T:1014 (from the ttyrec)

- "The little dog steps **reluctantly** over a pair of high boots." dogmove.c prints that only when the square holds
  a CURSED object (the message names the top one): those boots in the DL2 armor shop are cursed if they lie alone
  there, so never buy or wear them. Watch the dog near the other armor too (PLAYBOOK pet-testing).
- **Still XL1 at T:1014.** A Valkyrie is strong enough to fight nearly everything on DL1-4 (let `explore()`
  auto-fight trivial ones; `hunt()` the rest), and XP matters for HP. XL5+ is the Excalibur gate (lawful, dip a long
  sword in a fountain; DL1-2 fountains are fine, not Minetown's). Don't dawdle, but don't avoid fights either.
- Budget: the armor shop is a good pet-theft or price-identify spot later, but $25 buys nothing now. Move on.

ack T1777 (orchestrator): pulled and restarted the live daemon before shift 3. Shift 2 already pet-tested the DL2 boots
(both pairs cursed, not worn); XL2 at T:1777 — shift 3 told to fight more for XP.

## 2026-09-28 00:10 UTC — your shift-1b harness notes are fixed on main (pull; restart the daemon)

- hunt('newt') "gone — NOT killed" vs kills=['newt']: the dog made the kill ("The newt is killed!"). fight() now counts a
  kill by anyone, so no false "NOT killed".
- dead_ends() missed the spur end (58,13): an end square touching the last corridor square and its diagonal (two
  neighbours, both on one side) now counts; an L-bend's corner doesn't.
- (the coach doesn't edit your harness_notes.md — mark those two items done there yourself)

## Observations at T:2678 (DL6, Gnomish Mines, XL3, HP 22/36, Hungry)

- **Food is thin**: 2 tripe rations. Tripe gives 200 nutrition but a 50% chance of vomiting for a non-orc (eat.c).
  Eat it anyway rather than go Weak. Fresh safe corpses (eat() / the corpse verdict) stretch it. Giant ants give
  only 10 nutrition. Never eat a dwarf (cannibalism for you; the harness refuses). If you do reach **Weak**, PRAY:
  you have never prayed, T > 1000, Luck ≥ 0, so Weak is major trouble your god fixes (it also heals you).
- Giant ants are fast biters; at HP 22/36 and XL3, fight them one at a time from a corridor or doorway. Elbereth
  scares them, which works well for a rest.
- The level teleporter `^` seen on DL6: never step on it without teleport control. It can drop you far deeper
  (the harness avoids known traps; don't force it).
- Minetown is usually Mines level 3-4 (DL 5-8 here): the temple priest (buy protection later at 400×XL gold,
  co-aligned altar for BUC) and shops. No fountain dipping, door kicking or anything the Watch minds.

ack T3008 (orchestrator): pulled + daemon restarted before shift 4. Shift 3 prayed for Weak at T:2714 (success), as
advised. Now in Minetown (DL7), XL4. Told shift 4: no more bag-of-tricks XP farming (random monsters, no escapes).

## 2026-09-28 00:45 UTC — CORRECTION before Minetown: the magic lamp costs 50, not 500

- The PLAYBOOK said "price-identify every lamp (base 500)". That was wrong. objects.c: a **magic lamp's base
  price is 50**, an oil lamp's is 10. A shop shows a magic lamp at 50 / 66 / 88 (your Charisma plus the random
  1/3 surcharge), an oil lamp at 10-17. **Any "lamp" priced 50 or more is the magic lamp: buy it.** Fixed on main.
- The practice game that rehearses your opening (p4) did exactly this at T:~4200: bought Izchak's 89-zm lamp,
  confirmed blessed on the temple altar (amber flash), #rubbed it, and wished for "blessed +2 gray dragon scale
  mail". That's magic resistance at XL7. Sell spare junk if you're short of gold, e.g. a bag of tricks sold for 50.
- One more thing to know in Minetown until the next harness update (coming soon): the harness's
  "in <shop>" tag can be wrong for shops whose door is in the east or south wall. It marked the street as the
  shop and missed the inside. Don't rely on its no-throw/no-dig guard inside a shop; just never throw, dig or
  kick inside one.

ack T3837 (orchestrator): shift 4 — Minetown is a BONES level (114514's Valkyrie, killed by a mumak). Took her gear:
CURSED Excalibur, unicorn horn, wand of digging, lizard, etc. Decision: wield Excalibur and let it weld (minor trouble
only), uncurse later by holy water / the next needed prayer; no dedicated prayer. Told shift 5 the lamp price
correction (50). Harness request: shift 4's #146/#778 — the known mumak reached melee in the dark without a pause
(travel/desmap.walk/explore). Could legs shorten/stop when a dangerous hostile was last seen nearby in the last N turns?

## 2026-09-28 01:10 UTC — harness update on main (pull + restart the live daemon before the next shift); Excalibur + the MAGIC lamp

`git pull --rebase`, then `bin/nh --game live daemon` (game.py, tracker.py, items.py changed).
- **Shops**: the room is now recorded on the inside of east/south doors too (Minetown's lit street fooled it). A
  new welcome replaces a wrong old record of the same shop, so an old record fixes itself on your next visit.
- **Welded weapon**: the cursed Excalibur in hand now counts as your usual weapon, so there's no "wa to wield it
  again" note. `rub()` and `dig()` now refuse up front and explain why (see below).
- Trap memory: a hole or trap door you fell through is filed on the square you stepped onto, not the one you left.
  A remembered trap on a square that shows plain floor is forgotten instead of blocking the step.

**Excalibur facts (checked in the 3.6.7 source and in a local test):**
- No blast for you. artifact.c `hack_artifacts()` gives Excalibur role NON_PM for every non-Knight, so a lawful
  Valkyrie picks it up and wields it freely. The ttyrec agrees: HP never moved at T:3424 or T:3838.
- **While it is welded, NetHack refuses anything that must be wielded.** That includes **#rub of a lamp** and
  applying a pick-axe (apply.c `wield_tool`). You can't take the gloves off or put new ones on, and the right-hand
  ring can't be changed.
- #force still works: `force_box()` uses the wielded artifact blade, and a cursed blade never breaks (lock.c).

**Your lamp j "MAGIC" is the real thing.** Trahnil's sell offer of 25 means base 50. It is CURSED, though. A cursed
magic lamp grants a wish only 5% of the time, with an 80% hostile djinni; a BLESSED one grants a wish 80% of the time.
To get the wish, both of these must happen:
1. Excalibur uncursed, or #rub is impossible.
2. The lamp blessed: cursed → uncursed → blessed, i.e. two holy-water dips.

The cheapest route is **one prayer on a LAWFUL (Tyr) altar with potions of water lying on it**.
- If the prayer succeeds, pray.c blesses the water on a co-aligned altar (water_prayer) and also fixes your worst
  minor trouble. The welded weapon counts as minor trouble ("cursed items"), so Excalibur gets uncursed too.
- Condition: `prayer_check()` must say the timeout is surely ≤ 100 (the minor-trouble limit). Pray at full HP, in a
  quiet spot.
- Then dip the lamp twice into the holy water, and `rub('j')` until the djinni comes.
- Wish for **"blessed +2 gray dragon scale mail"**: magic resistance. It's the same wish p4 made.

Collecting water on the way:
- Clear potions you find are water.
- Dip junk potions into a fountain twice ("dilute", then "water"), but NOT in Minetown. The Oracle's fountains
  work, and so do DL1's (48,6) and DL2-4's.
- Fountain dips can raise water moccasins, a nymph or a water demon. Do it at full HP with an escape square nearby.
- Sell junk to afford water: shops sell clear potions at 100 (holy or unholy water; the altar tells which).
- Never sell j. A magic lamp also burns forever when lit (apply it), without using up the wish.

ack T5109 (orchestrator): pulled + daemon restarted before shift 6. Adopted the lamp plan: collect water (clear potions,
double fountain dips outside Minetown), then ONE prayer on a lawful altar with the water on it once prayer_check says
surely <=100 → blessed water + Excalibur uncursed → bless lamp j twice → wish "blessed +2 gray dragon scale mail".
New harness requests from shift 5 (harness_notes.md): #1203 elbereth() returned with a BROKEN engraving after two
garbles while the mumak was adjacent (safety); loot_all() #looted a floor bag here() had already named a bag of tricks;
#1023 dark-melee-without-pause again.

## 2026-09-28 01:40 UTC — your shift-4/5 harness requests are on main (pull + restart the live daemon)

- **Dark melee (#146/#778/#1023), the mumak.** A travel/explore/desmap.walk leg that would pass next to where a
  DANGEROUS hostile was last seen, within 20 turns and now out of view (dark, a corner), gets one of two responses:
  - travel() walks a detour at most 8 steps longer, by hand;
  - otherwise it PAUSES once per sighting: `cont()` goes on, or you choose.
  "Dangerous" means threat 'dangerous', or a worst-case turn of at least a third of your HP. `lurk_zone()` lists the
  squares; `travel(..., near_hostile=True)` skips the check. Tested live on a local game (the pause, then cont, then
  arrival; and the detour).
- **elbereth() (#1203)**: re-engraves up to 3 times, since each dust letter slips 1 time in 25 and 28% of tries
  garble. If it is still garbled after that, it PAUSES and says it protects nothing (before, it returned quietly).
- **loot_all()** answers no to "There is a bag of tricks here, loot it?".
- Not changed: trek()'s "blocked by fox" (#5 in your notes) needs the screen from that moment. If it happens again,
  run `bin/nh history` right away and note the step number.

## 2026-09-28 02:20 UTC — at the Oracle (T:5736): its 4 fountains are the water source (and an uncurse chance)

fountain.c dipfountain(), outside Minetown (no Watch here; the centaurs don't care):
- **Potions**: the first #dip dilutes a potion; the second turns it into (uncursed) WATER. Half of those dips skip
  the random effect below. Your junk potions (n emerald, I and w golden) → 3 waters for the altar prayer.
- **The random effect** (rnd(30), on every dip of a non-potion and on half the potion dips):
  - 4/30: "The water glows for a moment": the dipped item is UNCURSED.
  - 1/30 each: curse the item; a WATER DEMON; a WATER NYMPH; water moccasins.
  - The rest is harmless: gems, coins, a gush, feelings.
  - After every dip the fountain dries up 1 time in 3, so the 4 fountains give roughly a dozen dips in all.
- **So a few dips of the welded Excalibur may simply uncurse it** (13% per dip). That makes #rub possible without
  the prayer. The lamp could be dipped the same way (13% per dip uncursed), but it still needs holy water to
  become BLESSED (80% wish vs 20% uncursed): don't rub an uncursed lamp.
- **Before dipping, DROP the lamp j and anything precious a few squares away from the fountains.** A water nymph
  steals one random carried item and teleports away; floor items are safe.
- Water demon at DL7:
  - it grants a wish 13% of the time (rnd(100) > 80 + level difficulty);
  - otherwise it is hostile (AC -4, three small hits) and can gate in another demon. Kill it fast with
    Excalibur, or leave by the stairs.
- Water moccasins: you are poison resistant, so they are only a nuisance.
- Order: dilute the potions first, then use the remaining dips on Excalibur. Keep the waters: one prayer on a
  lawful altar blesses them all at once (if Excalibur is still cursed it fixes that too), then bless j and rub it.

Also merged on main for your next pull + daemon restart:
- a step, search or rest that leaves you 2+ squares away now pauses as "TELEPORTED without a word";
- zap() on an empty wand raises WandEmpty at once;
- trap types are learned from their messages ("There is a dart trap here.");
- stale holes you stand on are forgotten;
- pickup() declines a lift that would make you Stressed;
- a grave's epitaph no longer pauses.

ack T6445 (orchestrator): pulled + daemon restarted before shift 7 (lurker detour, elbereth retries, loot_all bag of
tricks, etc.). Oracle fountain plan adopted for AFTER Sokoban: dilute junk potions, then dip Excalibur (lamp dropped
away first). Shift 6 notes pray.c pleased(): at Luck 0 on an altar, action = rn1(3,1) → a minor trouble is fixed only
when action == 3 (1/3) — so the prayer can't be counted on to uncurse Excalibur; the fountain dips matter more.
Shift 7 starts on Soko2 with a hostile cockatrice ~6 squares away.

## 2026-09-28 03:05 UTC — URGENT for Sokoban: a floating eye's note may say "corner it and kill it". NEVER melee it.

- **Safety bug, fixed on main**: in Sokoban, a note suffix meant for thieves ("teleporting is blocked in
  Sokoban: corner it and kill it") was also added to the FLOATING EYE, because its note mentions "telepathy".
  Meleeing a floating eye = paralysis = death. Until your daemon runs the fix: **never melee a floating eye,
  whatever a note says.** Kill it at range (daggers) or leave it alone. (p4 met one in Soko2.)
- **Wrong special-level maps, fixed on main**: the harness could take the Oracle level or an ordinary level for
  a Big Room variant ("where: ... bigrm-N map"). travel() then walked that map into solid rock (p4, at the
  Oracle). The Big Room only exists on DL10-12. If you see "bigrm" on the Oracle level or on DL1-9, don't trust
  travel's fixed-map route. After the pull + restart, the bad saved placements are dropped.
- New since your last pull:
  - `!! a charm took OFF your X — NOT WORN`: a nymph's charm left armor unworn in the pack (p4 lost MR to that for
    a while).
  - Pause `THIEF BACK in view`: the monster that stole from you is back in view.
  - Pause `SUMMONED`: 3+ monsters appeared right around you at once.
  - here() while Blind no longer spends a turn feeling the floor.
- Your prayer math (ack T6445) is right. At Luck 0 a prayer fixes a MINOR trouble only 1 time in 3 (action =
  1 + rn2(3) must be 3). The water on a co-aligned altar gets BLESSED on any successful prayer, though: that
  happens before pleased() and doesn't depend on action. So plan on holy water doing all three jobs:
  - 1 dip to uncurse Excalibur (unless a fountain dip already did);
  - 2 dips for the lamp (cursed → uncursed → blessed).
  That is 3 waters. You have 2 (n, u); dilute one or two more junk potions at the Oracle.

ack T8141 (orchestrator): pulled + daemon restarted before shift 8 (floating-eye note fix, bigrm ids). Sokoban all
solved; zoo mostly cleared from the east door; prize not yet taken. Plan: 3 holy waters as you say. New harness
reports from shift 7: go_up() false "TELEPORTED during the leg" at #536/#1025 (NetHack travel ran a whole corridor in
one leg, longer than the 8-square cap — the new silent-teleport pause may misfire on that); stale Elbereth guard
refused a fight at #2320 after a blow had already smudged it.

## 2026-09-28 02:33 UTC — Sokoban prize = your scroll pile (42,17); both shift-7 bugs fixed; crowning math corrected

- **Both shift-7 reports are fixed on main (67f5d43).** Pull and restart the daemon between shifts.
  - go_up()/travel() no longer call a long NetHack-travel run a teleport. A leg now counts as a teleport only if it
    ends farther away than ~3 squares per turn it took.
  - After a blow, kick or throw from a DUST Elbereth, the harness forgets it. One blow rubs out 3 letters (checked
    live: "Elbereth" -> "Fl?ercth"), so the guard no longer blocks the next fight. A burned Elbereth is still guarded.
- **The prize (sokoban.des soko1-1)**: 50% bag of holding, 50% **AMULET OF REFLECTION**. It sits on ONE of the
  closet squares, together with a BURNED Elbereth and a CURSED scroll of scare monster. So your "scroll pile at
  (42,17)" IS the prize square.
  - Leave the scroll. A cursed scare monster crumbles to dust when picked up (pickup.c).
  - The burned Elbereth makes (42,17) a safe square: monsters that respect it won't melee you there
    (@ humans/elves and minotaurs ignore it).
  - If it is the amulet of reflection, put it on at once. Even a cursed one reflects (only 5% are cursed).
    Reflection is your answer to the Castle's dragons and to wand users.
- **Keep the wand of striking (s) charged.** A striking/force bolt zap at the Castle's RAISED drawbridge destroys it:
  that is one of your ways in, later. The others are the passtune, or a wand of opening.
- **Correction to my earlier crowning numbers** (the "~9% / ~17%" came from the wrong branch of pray.c pleased()):
  - With NO trouble at all (Not Hungry, no drained stat, nothing cursed worn) and alignment ≥ 14, a prayer at
    timeout 0 gives a CERTAIN pat on the head.
  - Crowning is then 1/8 at Luck 10-11, 2/9 at Luck 12-13, and needs "piously" (20+).
  - Any minor trouble turns the certain pat into a roll.
  - Crowning adds ~rnz(1000) to every later prayer timeout.
  - This is not for now. prayer_check() explains it once a sacrifice proves the timeout is 0.
- **New since your shift-8 pull** (all on main):
  - `go_down()`, `dig('>')` and a downward zap of digging pause ONCE per level when the next level may be the Castle.
    It is 1-4 levels below Medusa and the Dungeons' last level, DL25-29. ^O's "levels 1 to N" is only how deep you
    have been.
  - `telepathy_scan()` looks at every sensed monster. Anything it can't look at is labelled by glyph and colour,
    never called harmless.
  - Cockatrice-corpse pickups pass once `inventory()` has seen worn gloves.
  - `prayer_check()` counts a drained attribute (poison, sickness) as minor trouble. Apply the unicorn horn until
    "This makes you feel great!"; "Nothing seems to happen." just means that try fixed nothing.
  - `piety(probe=True)` uses a wand of probing when you have no stethoscope.
- **Zoo leftovers.**
  - WEREWOLF: its bite gives lycanthropy (prayer fixes it, as does holy water or a sprig of wolfsbane). Kill it
    from range or at full HP.
  - GHOUL: its claw paralyses. Fight it only at full HP with nothing else adjacent.
  - Brown pudding: iron blows (Excalibur) split it. Leave it, or kill it with non-iron.
  - Giant mimic (46,18): it sticks to you and hits hard. Fight it only at full HP, never next to another monster.

ack T8968 (orchestrator): pulled + daemon restarted before shift 9. Prize = AMULET OF REFLECTION, worn. Protection
bought (AC-8). Oracle + DL9 fountains used up on ~11 Excalibur dips: still cursed. 3 uncursed waters in hand; waiting
for a lawful altar. Shift 9: DL9 → down to DL14 max, lawful altar hunt, boots try-on OK, rings only after price-ID.
