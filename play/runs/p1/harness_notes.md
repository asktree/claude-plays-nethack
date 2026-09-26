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
