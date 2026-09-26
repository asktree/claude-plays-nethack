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
