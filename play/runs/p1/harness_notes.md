# p1 harness notes (shakedown)

Format: step `#N` — command — expected — what happened.

- `#0`→`#2` — `exec` with only `inventory_text()` / `print(obs.status)` — expected the step counter not to move
  for info-only calls (docs say obs/inventory take "no game time") — the header step went from #0 to #2. Not a
  bug per se (it counts key sends, `i` + `<Esc>`), but the docs should say what `#N` counts (key sends, not turns),
  otherwise "step number" is ambiguous when reporting problems.
- `#2` — `obs` vs `screen` — parsed view matches raw terminal for the starting room. Good.
- `#65` — `exec` fight step — wanted to write a safe fight loop ("attack while a hostile is adjacent and HP > x")
  but the kernel `obs` has no parsed monster list (`dir(obs)` = elapsed, hero, keys, kind, message, messages, n,
  prompt, screen, state, status, stop_reason, unsent). The CLI prints `monsters: d jackal at (57,12) d=1 ADJACENT`
  so the parse exists; please expose it as `obs.monsters` (glyph, name, x, y, dist, peaceful/tame flags).
  FEATURE REQUEST (high): `obs.monsters` + `adjacent_hostiles()` helper.
- `#65` — `do("Fb", ok=[...])` — fine. Note for docs: the kill message is "You kill the jackal!" (not "is
  killed"), so the example regexes in PLAYER.md ("The jackal is killed!") are misleading for `ok=` patterns.
- `#79` — reading item positions off the cropped map — I misread `[$|` by one column (thought `$` was at 60,
  it was at 61) and my pickup helper landed on an empty square. The monsters list gives exact coords; objects
  don't. FEATURE REQUEST (medium): print an `objects:` list (`[ armor at (60,6)`, `$ gold at (61,6)`, `> stairs
  down at (54,7)`) under the map, and expose `obs.objects` / `obs.features` in the kernel. Also the cropped
  ruler is harder to read than the full one because the tens digit sits over a non-zero units digit.
- `#82`, `#88` — `travel(x,y)` inside exec — expected it to arrive; it paused twice on trivial pet chatter
  ("The kitten picks up a gold piece", "You swap places with your kitten"). `explore()` uses an `ok=BENIGN`
  list but `travel()` (tactics/nav.py:89) does not. FEATURE REQUEST (medium): a shared default benign list for
  all helpers (pet picks up/drops/swap places, "You see here", "There is nothing here to pick up") — each
  needless pause costs a whole tool call.
- `#253`→`#329` — my `grab(37,9)` / `grab(36,11)` — both hit empty squares; the real spots were (36,9) and
  (35,11). Second time I've miscounted columns from the cropped map: the crop ruler's tens digit sits above
  the units `0`, but the row starts on an arbitrary column (e.g. 13 or 35), so you must solve for the offset.
  Suggest: print `cols 13-37` next to the ruler, or start crops on a multiple of 10. Better: an `objects:` list
  (see above). I wrote a kernel `objects()` scanner as a stopgap.
- `#329` — `explore()` — paused on "You stop. | Your kitten is in the way!" — benign; add to BENIGN.
- `#329` — `explore(max_legs=40)` default is low: it stopped at "max_legs reached" mid-level with no event.
  Suggest default ~150 or return only on events/frontier exhaustion.
- `#562` — `obs` monsters list while a `[yn]` prompt was open — showed `f white PET? at (23,3)` instead of
  `tame kitten`. Understandable (farlook can't run inside a prompt) but the label should say why, e.g.
  `f (unidentified: prompt open)`; "white PET?" reads like a parser bug.
- `#562` — `print(obs.screen)` in exec — the Screen repr is ~34KB (all chars + attributes); it blew the output
  into a persisted file. Give Screen a compact `__repr__`/`__str__` (the 24 lines) and an explicit
  `.dump()` for the full thing. `obs.screen.chars` (list of 24 strings) is what I actually wanted — document it.
- `#560` — my own `grab()` picked up a large box blindly (350 wt). Wish: `here()`-style peek before pickup, or a
  `pickup(x,y, exclude=...)` helper that refuses boxes/chests/boulders and warns on cockatrice corpses.
- `#569` — `#loot` flow — worked cleanly through exec (`yn` -> menu -> menu -> menu), and the MENU rendering in
  the CLI output is clear. Good.
- `#588`, `#591` — fight loop vs a newt — three tool calls for one newt: pause on `HP 17->15` (even though the
  step had `ok=` patterns), then pause on "The kitten eats a newt corpse". FEATURE REQUEST (high): let `do()`
  take `hp_floor=N` (pause on HP loss only when HP < N or a single hit >= X), and treat pet eating/picking up
  as benign by default. Against a real threat the HP pause is right; against newts it burns the call budget.
- `#593`+ — `print(travel(...))` — the return value is a `Snap` whose repr embeds the whole Screen (35KB). Same
  fix as above: compact reprs. Helpers returning Snap should document it (PLAYER.md says travel "stops when
  something happens" but not what it returns).
- `#889`→`#892` — `explore()` then `cont` — BUG: explore keeps re-issuing the same travel leg into a boulder
  ("A boulder blocks your path", T stays 634, step count rises). It never marks the leg failed. Expected:
  treat "blocks your path"/"in vain" as leg failure, add the square to `unreachable`/`skip`, try pushing the
  boulder once with a plain move, or return. Also: "A boulder blocks your path" comes from the travel command,
  so travel-based helpers can't push boulders at all; document that and offer `push(dir)`.
- `#1160` — `explore()` — paused with "This door is locked." instead of handling it (the result dict has a
  `locked` list, so it seems intended). Suggest: on a locked door, explore records it and moves to the next
  frontier, and offers `kick_door(x,y)`. My manual kick loop worked (2 kicks).
- `#1166` — `explore()` stepped onto an unseen trap door right behind the kicked door -> fell to DL3. Not a
  harness bug, but the pause label was good ("level: Dlvl:2 -> Dlvl:3"). Wish: after a level change, the
  harness could print the full map automatically instead of the crop (nothing is known yet anyway).
- `#1219` — `do('dk')` in a shop (sell offer) — BUG (high): the message "You drop a scroll... | Annootok offers
  10 gold pieces for your scroll labeled ZELGO MER. | Sell it? [ynaq] (y)" wrapped onto screen row 1. The
  harness then (a) reported `[command]` although a yn prompt was open, (b) parsed the wrapped text "aq] (y)"
  as monsters `a`, `q`, `y` on row 1 ("new monster in view: @,a,q,y" pause), (c) put the hero at the cursor
  (8,1) and listed my real `@` as a "white" monster. Expected: detect wrapped message lines (row 1 used by
  the message window / --More--) and exclude them from the map parse; detect the `[ynaq]` prompt even when
  wrapped. In a real game a false "hero at (8,1)" could make a helper walk into something.
- `#1217` — pickup in a shop — the "Pick up what?" menu lines are overlaid on the map rows, so a menu parser
  must `search`, not `match`, from the line start. A kernel `obs.menu` (list of (letter, text, selected)) would
  avoid every script re-parsing the screen; the CLI already prints the parsed menu, so expose it.
- `#1253` — `explore()` from inside a shop — "Annootok blocks your path" pause: travel can't pass a peaceful on
  the exit square and explore doesn't know to wait. Wish: `leave_shop()` (wait for the shk to move off the
  door-side square, then step out), and explore treating "X blocks your path" as "wait 1-2 turns, retry".
- `#1274` — `explore()` after finding a hidden passage — BUG (high): returned "explored (no reachable frontier
  left), legs 0" although a freshly found corridor led north from (16,14). The corridor square held a coyote
  corpse (`%`), so the frontier finder apparently doesn't count object-covered squares as passable. Objects on
  corridors/doorways are common; the frontier logic should use the remembered terrain (or NLE glyph layers /
  `seenv`), not the top-most screen character. Same likely applies to `$`, `)` etc. on corridors.
- `#1269` — `search(15)` — worked and paused correctly on "You find a hidden passage". Good. A `search_until_change(max_turns)`
  helper (stop when the map gains squares) would save a call or two.
- `#1407` — `do('s')` while a coyote stepped back into view — "new monster in view: d" pause fired for a monster
  I had already seen (it left line of sight for a turn). Suggest tracking seen monsters per level for ~20
  turns so re-appearances don't pause (or pause only if it is adjacent/approaching).
- `#1433` — map now shows two `>` on DL3 (Mines branch). Wish: the `obs` footer could list stairs/features
  (`< (19,9)  > (29,16)  > (46,18)  fountain ...`) and `<C-o>`-style branch info; I had to read them off the map.
- General: the CLI's per-call header (`#N T:.. HP..`) is excellent; `[exec PAUSED] <reason>` labels are clear.
  The cost model is the problem: nearly every trivial fight took 2-3 tool calls because of HP-loss and pet/
  benign-message pauses. A `do(..., pause_hp_below=N)` knob and a broader BENIGN default would roughly halve
  the calls per level.
- `#1436` — my kernel `objects()` helper listed shop stock as loot and a `travel()` walked me 49 turns back into
  the shop (my bug, but instructive): a harness-provided object list should carry `for_sale`/shop-square flags,
  and `travel()` should take `max_turns=` so one bad target can't burn 50 turns silently.

## Ranked summary (what would matter most in a real game)
1. Wrapped message/prompt lines misparsed as map + `[command]` while a `[ynaq]` prompt is open (#1219). Could make a script act on a phantom map / send keys into a prompt.
2. `explore()` frontier ignores corridor squares covered by objects (#1274) and loops forever on boulders (#889); default `max_legs=40` stops mid-level (#210).
3. No `obs.monsters` / `obs.objects` / `obs.menu` in the kernel (#65, #79, #1217): every safe loop has to re-parse the screen; coordinates were miscounted twice by hand from the cropped ruler.
4. Pause noise: HP-loss and pet/benign messages pause even with `ok=` (#588, #591, #82); 2-3 calls per trivial fight. Need `pause_hp_below=` and a shared BENIGN default.
5. Reprs: `Snap`/`Screen` print 35KB (#562, #593).
6. Missing helpers: `leave_shop()` (#1253), `kick_door()`/locked-door handling in explore (#1160), `search_until_change()`, stairs/features footer (#1433), re-seen monsters counted as new (#1407).

## Shift 2 (restored game from T:818; step counter restarted at #20)

- `#20`->`#25` — `exec` with only info calls (`dir()`, `obs.monsters`, `frontiers()`) — expected no step advance — counter +5. Still unclear what `#N` counts; PLAYER.md should say "key sends". Low impact.
- `#25` — `obs.monsters/objects/features/menu/hostiles()/adjacent_hostiles()` all exist in the kernel now (shift-1 #65/#79/#1217 FIXED as far as presence goes; behaviour to be verified when monsters/objects appear).
- `#67`->`#70` — `explore(skip={(19,6)})` — expected the square (a known-to-me arrow trap under a food pile) to be avoided — explore walked straight onto it (arrow, -3 HP). Either `skip` is ignored for object frontiers (`object_frontiers()` pile at (19,6)) or travel legs path through skipped squares. BUG (medium): document what `skip` covers; ideally a kernel-level `avoid` set that both target selection and travel honour (needed for known-but-undisplayed traps, e.g. after a level restore or a trap door seen from afar).
- `#61`->`#65` — `do('e')` then answering the parsed `[yn]` prompt from the script (`obs.kind == 'yn'`, `obs.prompt` has the full text) — worked cleanly; `obs.prompt` is exactly what a script needs. Good.
- `#55` — `step()` paused on "new monster: coyote" mid-sequence with a clear label and the `<-- ADJACENT`/`(NEW)` markers in the monster list. Good. The monster entry dict (`ch,x,y,color,pet,dist,new,desc,statue,tame,peaceful,note`) is exactly what fight loops need.
- `#31`/`#32` — `search_until_change(40)` returns `(True, Snap)`; Snap repr is now compact (shift-1 #562/#593 FIXED).
- `#303`->`#305` — `do(',')` on a single-object square (inside my grab helper, resumed via `cont`) — expected the pickup to complete silently — paused on the *result* message "i - a scroll labeled ...". The confirmation of the action you just took should be benign by default for `,` (and for `e`/`q`/`r`: "You finish eating", etc.), or `do()` should take `ok=True` = "don't pause on messages produced by this key, only on HP/monsters/status". Cost: 1 extra call per pickup.
- `#72` — `obs.menu` is a `Menu` object (`.items` of `MenuItem(letter,text,selected,header,y)`, `.page`, `.pages`) — not iterable; PLAYER.md says "list of (letter, text, selected)". Make `Menu` iterable over non-header items or fix the doc. `MenuItem.header` is handy.
- `#77` — `inventory()` returns dicts (KeyError on `it[0]`); PLAYER.md says "(letter, text, class, buc)". Document the keys.
- `#334` — `explore()` pause "message; new monster: @ at (48,16), o at (43,16)" after "The goblin throws an orcish dagger!" — BUG (HIGH): the snapshot the pause reported was STALE: it said T:1111, hero (46,16), map `.` at (46,16) and `@` at (48,16); `bin/nh screen` right after showed T:1113 and the cursor/hero at (48,16); `farlook(48,16)` = "you (dwarven valkyrie called p1)". So the travel leg kept going 2 turns after the message the harness stopped on (probably the auto-`--More--` pump stepped the game but the pause used the pre-More observation), the hero position lagged, and my own `@` was listed as a NEW white `@` monster (unidentified, no farlook). A script that trusts `obs.hero` here would move from the wrong square; a "human @ adjacent" false alarm could also trigger needless escapes. Expected: after auto-More, re-read the observation before parsing/pausing; never list the hero glyph as a monster (blstats x,y is ground truth); label unidentified monsters as such.
- `#334` — same pause: the `o` was listed as "o gray" with no farlook result although the message named it a goblin; after a manual `farlook` it became "goblin". Identification seems to be skipped when the pause fires during a stale snapshot.
- `#596`->`#605` — `pray()` and `wield` flows worked cleanly (confirmation handled, compact Snap returned). But I wasted the game's first prayer on a *minor* trouble (welded cursed dagger) that prayer cannot fix at Luck 0. WISH (HIGH, survival): `pray()` (or a `prayer_check()` helper) should print what the game would consider your trouble (major/minor/none, from status+inventory: HP<1/7, Weak, FoodPois, Stone, Slime, Strngl, welded weapon, cursed worn items), the estimated prayer timeout from `bin/nh info`'s prayer log, and the Luck caveat ("minor trouble is only fixed with Luck>0 or on an altar") — and require `force=True` to pray without major trouble. The PLAYER.md §3 text should also state the minor-trouble rule explicitly.
- `#596` — `do('o')` in the wield prompt paused on "The orcish dagger welds itself to your hand!" — correct and useful pause (not in my `ok=` list). Wish: `inventory()` entries could carry a `buc` field even when unknown (`'unknown'`) so scripts can refuse to wield/wear unknown-BUC items; mine did not check.
- `#629` — `do('i')` at the drop prompt in the shop — BUG (HIGH, REGRESSION/NOT FIXED — same as shift-1 #1219): message+prompt "You drop a scroll labeled EIRIS SAZUN IDISI. | Annootok offers 100 gold pieces for your scroll labeled EIRIS SAZUN IDISI. | Sel" wrapped; row 1 held "[ynaq] (y)". The harness reported `[command]` (a `[ynaq]` prompt was open), listed phantom monsters `y,q,a,n,y gray` on row 1, `objects` ") weapon (15,1)", "( tool (13,1)", "[ armor (6,1)" from the wrapped text, and put the hero at (17,1) (cursor). The exec paused on "new monster" so no harm, but a script reading `obs.kind == 'command'` would have sent its next command into the prompt. The wrapped-prompt detection apparently only covers some patterns; "Sel|l it? [ynaq] (y)" split across rows 0/1 is not caught. Expected: treat row 1 as message continuation whenever row 0 is a full-width message (or when the tty cursor sits on row 0/1), detect `[ynaq]`/`[yn]` anywhere in rows 0-1, and never place the hero on rows 0-1.
- `#629` — with the wrapped prompt, `bin/nh do n` (used next) is how I answer it; the CLI should print `PROMPT (ynaq)` here.
- `#685` — after `<` (Dlvl 3 -> 2) the CLI header still says `where: The Dungeons of Doom / Level 3` while the status line says Dlvl:2. The overview line should refresh on a level change (or be derived from `Dlvl` when the `^O` cache is stale). Low-medium: a script keyed on `where:` would think it is still on DL3.
- `#663`->`#667` — `elbereth()` engraved fine, but the dust engraving read back as "_lbere?h" one turn later (hit by the werejackal + my dagger throw). Wish: `elbereth()` could return the read-back text and warn when it is no longer exactly "Elbereth"; PLAYER.md should say throwing/melee from the square also spoils it in 3.6.
- `#679` — my own path bug ("It's a wall.") cost no turn; `safe_step` correctly reported "did not move". The `obs.messages` capture is reliable for such checks. Good.
- Werejackal handling: the `!! bite -> LYCANTHROPY` note was exactly the reminder needed. Wish: the note could add "@ form: weapon only, no infection; d form bites infect" and "REGENERATES" for M1_REGEN monsters (that fact decided my retreat).
- `#701` — correction to `#685`: the `where:` header refreshed on the next step (one-step lag after a level change), so it is a lag, not a permanent staleness. Still worth deriving from the status line.
- `#699`->`#701` — `bin/nh exec --hp-pause 40` accepted (percent, it seems) and no HP pause fired at 22/38 while a gecko kept biting; the fight finished in one call. Good; document the unit and the default (70) in PLAYER.md. Below 70% a trivial gecko fight cost 4 calls (#695-#699) before I found the flag: consider pausing on HP loss below the threshold only when the *attacker* is not already in the `ok=` list or when the hit is >= 20% of max.
- `#706` — second stale snapshot (same class as #334): the pause after "The goblin throws an orcish dagger! | You are almost hit..." (a `--More--` step) showed the thrown `)` drawn ON my stairs square (48,7) with no `@` anywhere on the map and `you @ (48,8)` — I had not moved (I was searching). `bin/nh screen` immediately after showed `@` at (48,7); `look()` then agreed. BUG (HIGH): the observation captured mid-`--More--` is not the settled screen; hero position/glyphs are unreliable on exactly the steps where a fight loop is about to act. Fix: after the auto-More pump, re-render/re-read before parsing; sanity-check `hero` against the `@` on the map (blstats x,y) and flag mismatches loudly.

### Shift 2 — verification of shift-1 complaints
1. Wrapped `[ynaq]` sell prompt misparsed as `[command]` + phantom monsters + hero on row 1 (#1219): **NOT FIXED** — reproduced at `#629` with the same symptoms.
2. explore(): corridor squares covered by objects (#1274) — no recurrence observed (walked corpse-covered corridors fine); boulder loop (#889) and locked doors (#1160) not encountered this shift; `max_legs` default now 150 (fixed). NEW: `skip=` did not keep explore off a known trap square (`#70`).
3. `obs.monsters` / `obs.objects` / `obs.features` / `obs.menu` / `hostiles()` / `adjacent_hostiles()`: **FIXED and good** (dict entries with x,y,peaceful,tame,dist,note). Doc mismatches: `Menu` is not iterable (use `.items`), `inventory()` returns dicts.
4. Pause noise: **much better** — pet/benign chatter did not pause once; HP pause only below 70% (and `--hp-pause N` works). Remaining: pickup/eat result messages pause (`#305`), and below 70% every trivial bite pauses (4 calls for one gecko, `#695-#699`).
5. Reprs: **FIXED** (compact `Snap`).
6. Helpers: `kick_door`, `search_until_change`, `travel(max_dist)`, features footer, `bin/nh info`: present and used (search_until_change worked at `#32`). `leave_shop()` still missing (manual wait loop worked). Re-seen-monster pauses: not measured.

### Shift 2 — ranked summary (survival impact)
1. **Stale observation on `--More--` steps** (`#334`, `#706`): hero position and map glyphs from before the auto-More pump; my own `@` reported as a new white `@` monster; thrown dagger drawn on my square with no `@`. Exactly the moments a fight loop acts on `obs.hero`/`adjacent_hostiles()`. Re-read the screen after pumping More; cross-check hero vs blstats.
2. **Wrapped prompt misparse** (`#629`): `[command]` while a `[ynaq]` prompt is open — a script would type into the prompt (e.g. `y` = sell). Detect prompts across rows 0-1; never put the hero on rows 0-1.
3. **No prayer advisor** (`#596`): the harness let me burn the game's first prayer on a minor trouble at Luck 0. `pray()` should print trouble class + timeout estimate + the Luck rule and need `force=True` without major trouble.
4. **`explore(skip=)` ignored for object piles / path squares** (`#70`): walked onto a known arrow trap.
5. Call-budget items: pickup/eat result pauses (`#305`), per-hit pauses below 70% (`#695`), `Menu`/`inventory()` doc mismatches (`#72`, `#77`), `where:` one-step lag (`#685`), `elbereth()` not reporting the read-back (`#667`).

## Shift 3 (daemon restarted; counter from #1 at T:1675)

- `#6` — `prayer_check()` exists and is trouble-aware (55% at 402 turns = P(timeout==0) for "none"; matches rnz(350) math). Good.
- `#6` — `bad_squares()` remembered the DL2 trap door (71,8), but NOT the DL3 arrow trap (19,6) seen before the restart (`avoid((19,6))` added by hand). Wish: persist known traps per level across daemon restarts (they are in the game's own trap memory: `^` under objects).
- `#15` — `do(',')` pickup result "q - a yellow potion." no longer pauses (shift-2 #305 FIXED). `,` pickup + gold pickup fine.
- `#33` — `fight(56,9)` vs lichen: one call, clean. `#39` — `fight()` paused on "XL 3->4" (reasonable).
- `#42` — `where:` header refreshed immediately on Dlvl 2->3 (shift-2 #685 lag not reproduced).
- `bin/nh info` "levels" table attributes DL2 features (fountain (25,6), up stairs (46,16)) to "Level 3: T826-1466" — the level-record keying lagged a step at the T:1466 level change. Low impact but misleading.
- `#55`->`#117` — `explore()` with `avoid((24,11))` (gas spore on the only corridor): 62 key sends, game time unchanged (T:1746), then "explored (no reachable frontier left)" with 8 unreachable frontiers. Expected: recognise that all frontiers are cut off by an avoided square after one failed attempt (or report "blocked by avoid squares"), not re-issue travel legs ~60 times. Medium: wastes the no-progress budget.
- `#119` — my own script bug: gas spore not visible at distance 2 in a dark corridor (not infravisible) -> "gone". The `obs.monsters` list can't show unseen monsters, fine, but a `last_seen` record for a monster that just left view (position + turn) would help scripts.
- `#141`,`#144`,`#147` — `throw('p','l')` pauses on its own result ("The orcish dagger misses the gas spore." / "The violet gem hits the gas spore."): 1 call per throw. Expected: hit/miss messages of the thrown item are ROUTINE for `throw()`.
- `#150` — BUG (medium): snapshot taken during the gas-spore explosion animation: explosion glyphs parsed as `/ wand (19,4)`, `/ wand (21,6)`, `throne (19,6)`, `throne (21,4)`, and Exp stayed 82 (it was 88 on `look()` a step later). The settle check (cursor on @) does not cover the explosion/animation frames (tmp_at). Expected: after "explodes"/"You kill" wait for the animation to clear (or re-read when the screen has `/-\` `| |` `\-/` around a blast centre).
- `#160`,`#180` — monster labels: after "The werejackal summons help!", all three `d` were listed as "werejackal" with the LYCANTHROPY note; `farlook()` of each said two were plain jackals. The identification cache seems to be per glyph/colour, not per monster. BUG (medium): a fight script targeting "the werejackal" would pick the wrong one; the danger note on harmless jackals is noise.
- `#176`->`#187` — below 70% HP every bite paused the fight loop (1 call/turn) even with the messages in `ok=`; relaunching with `exec --hp-pause 0.4` fixed it (`#224` ran 8 rounds in one call). Suggest documenting `--hp-pause` in PLAYER.md §2 and defaulting fight loops to it.
- `#224` — `elbereth()` returned the read-back ("-lbereth") — shift-2 wish implemented, and it caught a spoiled engraving. Good.
- `#231` — `do('<')` inside exec paused with "level: Dlvl:3 -> Dlvl:2" and the DL2 map was correct at once (no stale-snapshot symptom this time).
- `#235` — `fight(47,12)` vs a newt at HP 21/49 refused ("below 45%"); the guard is right in general but a `stop_hp` override per call worked (`fight(..., stop_hp=0.2)`). Wish: the refusal could mention the target's danger (a newt cannot threaten 21 HP) or take `mon()` difficulty into account.
- `#259`,`#260` — `fight()` vs an acid blob: paused on each "You are splashed" (correct — 7 HP each), but the helper did not warn beforehand that acid blobs splash passively (the PLAYBOOK does). Wish: `fight()` prints the target's passive attacks (acid splash, cold, paralysis) before the first blow.
- `#261` — abandoned kitten on DL1 after ~1450 turns: `obs.monsters` correctly shows `tame: False, peaceful: False` and farlook says plain "kitten" (feral). Good — the flags are trustworthy.
- `#272` — `do(',')` picking up gold paused on "$ - a gold piece." although the same pickup at `#28` ("$ - 3 gold pieces.") did not pause. The pickup-result exemption seems inconsistent (maybe only when followed by another message?). Low.
- `#276` — `rest(20)` paused on "hunger: Hungry" with a clear label. Good.
- `#293` — `rest(20)` paused on the lycanthrope transformation with label "HP 30->10/10; XL 4->0" and the header showed `HD:2`/`XL:0`: the polymorphed status line (HD instead of Xp) is parsed as XL 0. Low impact, but a script keyed on `obs.status.xl` would misjudge; suggest `obs.status.polymorphed`/`hd`.
- `#296` — `prayer_check()` (major: lycanthropy, 91% at 740 turns) and `pray()` (confirmation handled; paused on "XL 0->4" after "You feel purified. You return to dwarven form!") worked exactly as documented. This is the shift-2 #596 wish implemented well. Good.
- Note for PLAYBOOK: a lycanthrope's transformation RELEASES/DROPS a welded cursed weapon and drops worn armor; on a `>` square 1/3 of dropped items fall to the level below (my shield + helm did). Useful (and a hazard).
- `#318`->`#321` — `travel(48,7)` with an acid blob adjacent: returned at once with hero unchanged, no message, T unchanged (NetHack's travel/run stops immediately when a hostile is adjacent). BUG (low-medium): the helper should report "did not move: hostile adjacent" (and `explore()`/`travel_to()` likewise) instead of silently returning a Snap; a script that assumes progress would loop.
- `#432` — `explore()` paused with "You stop in front of the door." at a closed door (61,9); after `cont` it opened the door and went on. The pause is unnecessary (explore's own door handling follows); add it to explore's BENIGN list. Low (1 call per closed door).
- `#379` — trap door fall label "level: Dlvl:2 -> Dlvl:5" and the new-level crop were correct immediately. Good.
- `#572`->`#596` — `search(15)` found a hidden door (47,18) (good pause label); `explore()` then reported both remaining frontiers as `locked` [(47,18), (54,5)] and stopped next to (54,5) without kicking. Same as shift-1 #1160: explore should offer/perform `kick_door` (or `#force`/unlock) on locked doors when nothing else is reachable, since "explored" here really means "blocked by locked doors".
- `#814`,`#817` — `fight(39,13)` vs an imp paused every round on "The imp casts aspersions on your ancestry." (monster chatter, not in ROUTINE). Expected: ROUTINE covers monster taunts/noises ("casts aspersions", "makes a rude gesture", shrieks, howls) — 1 wasted call per round.
- `#835`->`#840` — engrave flow: `do('E')` -> object prompt parsed, `do('z')` paused on the auto-identify message ("This marble wand is a wand of lightning!"), and the CLI printed `PROMPT (getlin): What do you want to burn into the floor here?` — clear and correct; answered via `bin/nh do 'Elbereth<CR>'`. `engraving_here()` works while Blind ("You feel the words"). Good. Wish: a `engrave_test('z')` helper that asks for the text up front and reports the identification, so this costs 1 call instead of 3.

### Shift 3 — verification of shift-2 complaints
1. Stale observation on `--More--` steps (`#334`, `#706`): **not reproduced** in ~840 steps, including level changes, thrown daggers and the goblin-style arrival ambush (`#372`: 6 monsters listed correctly with positions). Looks FIXED. One related new case: the snapshot taken during the gas-spore explosion animation (`#150`) parsed blast glyphs as wands/thrones and showed a stale Exp — the settle check should also wait for animation frames to clear.
2. Wrapped `[ynaq]` prompt misparse (`#629`): not exercised (no shop visit this shift). Unverified.
3. No prayer advisor (`#596`): **FIXED** — `prayer_check()` gives trouble class (none/major incl. lycanthropy), turns since the last prayer and P(timeout ok) that matches rnz(350) math; `pray()` handled the confirmation. Decisive for this shift's survival.
4. `explore(skip=)` / traps (`#70`): `bad_squares()` + `avoid()` exist and travel honoured them; but traps seen before the daemon restart are forgotten (DL3 arrow trap), and `explore()` with an avoided square on the only path re-tried ~60 legs without game time (`#55`->`#117`).
5. Call-budget items: pickup result no longer pauses (`#15`, FIXED; but gold pickup paused once at `#272`); eat/wear/wield results are quiet; `--hp-pause` (fraction) works and is essential in fights (`#224`); `Menu` iterable (used at `#296`, `#305`); `elbereth()` reports the read-back (`#224`). Still pausing needlessly: throw hit/miss (`#141`), monster taunts in `fight()` (`#814`), "You stop in front of the door" (`#432`), "You are in full health" during a wait (`#842`).

### Shift 3 — ranked summary (survival impact)
1. **Per-monster identification cache** (`#160`/`#180`): summoned jackals labelled "werejackal" with the lycanthropy warning — a script choosing "the werejackal" by `desc` would hit the wrong target or flee from harmless jackals. Identify each monster (farlook per glyph position), not per glyph/colour.
2. **Animation-frame snapshot** (`#150`): explosion glyphs parsed as objects/features + stale status. Wait for `tmp_at` frames to clear before parsing.
3. **Silent no-ops**: `travel()` with a hostile adjacent returns immediately with no message (`#318`->`#321`); `explore()` re-issues ~60 blocked legs (`#55`->`#117`); `explore()` reports "explored" when only locked doors remain (`#596`). Each can hide a real blockage from a script.
4. **Lost trap memory across daemon restarts** (`#6`): the known DL3 arrow trap was no longer in `bad_squares()`.
5. **Polymorphed status parse** (`#293`): `HD:2` shown as `XL:0`; add a polymorph flag.
6. Budget: throw/taunt/door/full-health pauses (see above) — roughly 8 extra calls this shift.
7. `bin/nh info` level features keyed one step late at a level change (`#42` note): DL2 fountain listed under "Level 3".
- `#859`->`#864` — scroll of identify flow: the CLI rendered the "What would you like to identify first?" menu with class headers, and the script selected by text via `obs.menu`. The header line showed "(status unreadable)" while the menu covered the status rows — harmless here, but a script reading `obs.status.hp` during a full-screen menu gets nothing; document it.
- `#853` — my own script treated a grid bug in view as a reason not to read a scroll; a `threat_level()` helper (trivial/normal/dangerous from `mon()` vs XL) would let scripts ignore harmless monsters consistently.

## Shift 4 (T:2638 -> T:3578, DL5 -> DL4 -> DL5 -> DL6; ~85 tool calls)
- `#24` — `fight()` vs a grid bug paused on "The grid bug bites! You get zapped!" although HP did not change (49/49). Expected: with `--hp-pause` the HP guard covers damage; a monster's hit message alone (no HP change) should be routine. Low (1 call).
- `#29`, `#640`, `#651` — `travel()` (inside `go_up()`/`go_down()`/plain `travel`) paused three times on stepping onto an engraving ("Something is written here in the dust. | You read: ..."), each costing a `cont`. NetHack itself stops the travel there. Expected: engraving-read messages in travel's BENIGN list, and travel re-issued until arrival.
- `#641` — BUG (medium): `go_down()`: its `travel_to('>')` was interrupted after one step (engraving read at (27,8)); `go_down()` then sent `>` anyway -> "You can't go down here." It must verify `obs.hero` is on the stairs (re-travel) before pressing `>`/`<`. Harmless here (2 wasted calls); with `<` and a monster adjacent it would waste a melee turn.
- `#398` -> `#401` — `explore()` returned `blocked: frontiers [(64,14),(65,15)] travel couldn't reach` although (64,14) was orthogonally adjacent to me and I had just walked through (65,15). The real cause was the boulder at (63,14): NetHack's `_` travel paths THROUGH boulders and then refuses the step ("A boulder blocks your path."). `travel(58,15)` at `#401` raised `NavError` quoting that message — good and clear. Wish: explore/travel treat boulder squares as impassable when planning and report "blocked by boulder at (x,y)".
- `#439` — `explore()` said `explored (no reachable frontier left)` (0 legs) while I stood in a corridor whose only continuation was behind a pushable boulder. Wish: list boulders as a frontier kind ("push boulder at (x,y)").
- `#457` — `search(15)` paused on "You find a hidden door." with the feature parsed (closed door (17,14)); `explore()` then went through it (#476). Good.
- `#537` — my `hold_and_fight()` loop (search 1 turn until a hostile is adjacent, then `fight()`, `ok=` for monster attack messages) killed a hill orc in one call. `#575`-`#578` — my `hunt()` helper (step toward, then `fight()`) + one pause on "XL 4->5". Good.
- `#620` — (my script, but a harness gap) while standing ON the fountain, `obs.features` no longer lists it (the `@` covers the glyph), so my "fountain still here?" check via `obs.features` said "gone" before the first dip. `here()` ("There is a fountain here.") is reliable. Wish: `obs.features` includes the feature under the hero (the game knows it; `#terrain`/`:`).
- `#625`->`#637` — `#dip` flow: `do('#dip<CR>')` -> `obs.kind == 'object'` with prompt "What do you want to dip?"; `do('a')` -> yn prompt "Dip the long sword into the fountain?"; `do('y')` -> outcome pause. 1 `cont` per dip. Works; a `dip('a')` helper would save the boilerplate.
- `#663` — `rest(20)` paused on "hunger: Hungry"; `#823` — `do('s')` in my loop paused on "hunger: Weak" (Hungry -> Weak took only 94 turns). Both correct and important.
- `#825` — `prayer_check()` (major: Weak, 98%) and `pray()` (confirmation handled, outcome messages shown) worked exactly as documented. Good.
- `#805`, `#807` — `do('d')` + letter: "You drop a wand of lightning." paused each time (drop results are as routine as pickup results). Low.
- `#892` — explore's new-monster pause listed the dog with "!! fast (speed 16)" — useful. `#899` — `fight()` paused on "You feel more confident in your weapon skills." (wanted). `#901` — `#enhance` menu parsed (`Pick a skill to advance:`, item text "long sword [Basic]"); selecting the letter enhanced immediately. Good.
- `#408` — `travel(58,15)` walked onto an unknown SLEEPING GAS TRAP under an item pile ("A cloud of gas puts you to sleep!", ~10 turns asleep). Nothing the harness could know in advance; but the trap is now in `#terrain`, and `here()` at `#409` reported "There is a sleeping gas trap here." correctly. Wish: after a trap message, print the trap's type and coordinates in the pause label.
- Per-monster labels: no mislabel seen (2nd dwarf zombie, 2nd elf zombie were tracked as separate monsters). Uncertain case `#40`->`#76`: during my 40-iteration `do('s')` loop the second dwarf zombie walked up and became adjacent without a "new monster" pause (the loop only ended by its iteration cap). Expected: a second monster of a species just killed counts as new.
- Rotten-food note for PLAYBOOK: any non-blessed food item older than 30 turns (rations, candy bars...) has a 1/7 "Blecch! Rotten food!" roll (25% confusion, ~19% blind up to 50 turns, ~19% unconscious up to 10 turns); when it knocks you out the WHOLE STACK gets flagged rotten (my 3 candy bars). Eat old items only on a safe square (burned Elbereth) — `corpse()` mentions the roll, an `eat()` helper could warn too.

### Shift 4 — ranked summary
1. `go_down()`/`go_up()` press the stairs key without checking arrival after an interrupted travel (`#641`).
2. Boulders: explore/travel plan through them (NetHack `_` behaviour) and then report the wrong cause — "unreachable" adjacent squares, "explored" with a pushable boulder as the only lead (`#398`, `#439`); the NavError text at `#401` was the only clue.
3. `obs.features` drops the feature under the hero (`#620`); engraving-read pauses during travel (`#29`, `#640`, `#651`) — together ~5 extra calls.
