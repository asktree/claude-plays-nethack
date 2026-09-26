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
