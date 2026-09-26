# NetHack player manual

You are playing **NetHack 3.6.7** to **ascend**. One character, one life: death is permanent and (on the public
server) public. Play like an expert who has ascended many times — patient, paranoid, methodical. Speed does not
matter; survival does. A turn spent resting, searching or retreating is always cheaper than a death.

Read this whole file at the start of every shift. Then read `play/PLAYBOOK.md` sections relevant to where you
are, and your run's memory (`play/runs/<game>/state.md`, the end of `journal.md`).

---------------------------------------------------------------------------------------------------------------

## 1. The interface: the `nh` CLI (run it with Bash from the repo root)

| command | what it does |
|---|---|
| `bin/nh obs` | full map + status + messages + identified monsters (no game time) |
| `bin/nh obs --crop` | same, map cropped around you |
| `bin/nh do KEYS` | send keys, wait for the game to settle, auto-dismiss `--More--`, print the result (cropped map) |
| `bin/nh do KEYS --full` / `--brief` | same with the full map / no map |
| `bin/nh exec <<'EOF' ... EOF` | run Python in the persistent game kernel (see §2) |
| `bin/nh cont` / `bin/nh cont --reply KEYS` | resume a paused exec (optionally answering the open prompt first) |
| `bin/nh drop` | abandon a paused exec |
| `bin/nh history 40` | the last 40 game messages with turn numbers |
| `bin/nh screen` | the raw 80x24 terminal (use when the parsed view looks wrong) |

**Key notation.** Plain characters are sent as-is: `bin/nh do k` (move north), `bin/nh do 20s` (search 20
turns), `bin/nh do ','` (pick up). Special keys: `<CR>` Enter, `<Esc>` escape, `<Space>`, `<C-d>` (ctrl-d =
kick), `<C-x>` (attributes), `<C-o>` (dungeon overview), `<C-p>` (previous messages). Extended commands:
`bin/nh do '#pray<CR>'`, `'#enhance<CR>'`, `'#dip<CR>'`, `'#force<CR>'`, `'#loot<CR>'`, `'#offer<CR>'`,
`'#chat<CR>'`. Quote keys for the shell (`'<'` goes up stairs, `'>'` goes down).

**Movement keys** (vi-keys): `h` west, `j` south, `k` north, `l` east, `y` NW, `u` NE, `b` SW, `n` SE.
Shift = run (`L` runs east). `F` + direction = fight in that direction (attacks even if you can't see a
monster there; never moves you). `m` + direction = move without picking up/fighting. `.` rests one turn,
`s` searches, `20s` searches 20 turns (interrupted if something appears).

**Coordinates** are screen positions `(x, y)` = (column, row). The map occupies rows 1–21; row 0 is the
message line, rows 22–23 are the status lines. The rulers above the map give the column number.

**Reading the output.**
```
#12 T:345 Dlvl:3 HP:21/28 Pw:5/5 AC:4 XL:4 Exp:95 $12 Hungry [command]
msgs: You hit the jackal. | The jackal is killed!
<map with column rulers and row numbers>
you @ (34,10)
monsters:
  d jackal at (36,10) d=2
  f tame kitten at (33,11) d=1  <-- ADJACENT
```
- `[command]` means the game waits for a command. Anything else is an open prompt — read it and answer it:
  - `[yn]` prompts: `PROMPT (yn): Really attack the gnome? [yn] (n)` → answer with one of the listed keys.
    With our options, some confirmations require typing `yes<CR>` (e.g. praying, attacking peacefuls).
  - `[object]`: `What do you want to eat? [fg or ?*]` → type the inventory letter (`?` lists choices).
  - `[direction]`: `In what direction?` → a direction key, `.` for self, `<`/`>` for up/down.
  - `[getlin]`: free text (a name, an engraving, a wish) ending with `<CR>`.
  - `[menu]`: items with letters; type letters to toggle, then `<CR>`. `>` next page, `<Esc>` cancel.
  - `[getpos]`: a map cursor (travel/farlook). Tactics handle these; `<Esc>` cancels.
- **Monsters are identified automatically** with farlook (`;`) the first time they appear, so you see
  `peaceful dwarf`, `tame kitten`, `statue of a newt` (statues look like monsters!), `jackal`.
  Anything marked `peaceful` must not be attacked (it angers your god and/or the monster's friends).
- Status: `HP:cur/max`, `Pw`, `AC` (lower is better), `XL` experience level, `T:` game turn, then hunger
  (`Hungry`, `Weak`, `Fainting` — act!), encumbrance (`Burdened`...), conditions (`Blind`, `Conf`, `Stun`,
  `Hallu`, and the deadly ones: `Stone`, `Slime`, `Strngl`, `FoodPois`, `TermIll`).

## 2. The kernel (`bin/nh exec`)

Python in a persistent namespace. Every `do()` inside it takes one game step and **pauses the script when
anything noteworthy happens**: any message, HP loss, a new monster in view, a new status condition, hunger
getting worse, a level change, level-up, game over. You then see what happened and decide: `bin/nh cont` to
resume, or do something else (which abandons the script). This makes multi-step plans safe.

Available in the kernel:

| helper | purpose |
|---|---|
| `do(keys, quiet=False, ok=None)` | one step; `quiet=True` = don't pause on messages (info-only keys); `ok=[regex]` = these messages don't pause |
| `obs` | last snapshot: `obs.status.hp`, `.hpmax`, `.turn`, `.hunger`, `.conditions`, `obs.hero` (x,y), `obs.messages`, `obs.screen.at(x,y)`, `obs.kind` |
| `look()` | re-read the screen without acting |
| `travel(x, y)` | NetHack's travel command to a known map spot (stops when something happens) |
| `travel_to('>')` | travel to the nearest `>` (or any map symbol); `go_down()` / `go_up()` travel + use stairs |
| `explore()` | auto-explore this level using the game's own unexplored-frontier data; pauses on events; returns a summary (e.g. `explored (no reachable frontier left)` → search for secret doors or move on) |
| `frontiers()` | list unexplored frontier spots, nearest first |
| `farlook(x, y)` | describe what is at (x,y) (no game time) |
| `inventory()` / `inventory_text()` | parsed inventory (letter, text, class, buc) |
| `here()` | what's on the floor here (`:`) |
| `search(n)`, `rest(n)` | count-prefixed search / rest (interrupted by events) |
| `elbereth()` | engrave Elbereth in the dust; `engraving_here()` reads it back |
| `pray()` | pray (handles the confirmation). Read §3 first! |
| `step(dir, n)` | move n squares one at a time |
| `pause(reason)` | hand control back to yourself from inside a script |

Example — explore, and stop to think whenever anything happens:
```
bin/nh exec <<'EOF'
r = explore()
print(r)
EOF
```
When paused, the output says why (`[exec PAUSED] message; HP 20->15; new monster in view: d`). Read it,
then `bin/nh cont` or act. Write your own helpers in the kernel when you notice repetition; put reusable ones
in `play/tactics/` (then `bin/nh reload`).

Rules for scripts: never loop blindly on attacks or movement without checking `obs.status.hp`; never
send keys into a prompt you haven't seen; always handle the case where a step returns a prompt.

## 3. Survival protocol (non-negotiable)

**Every decision starts with: HP, status conditions, adjacent monsters, escape route.**

HP rules (let H = HP / max HP):
- H < 0.6: stop exploring. Fight only if clearly winning; otherwise back off, rest, heal.
- H < 0.4: disengage **now**: retreat upstairs, stand on Elbereth (`elbereth()`), quaff a known healing
  potion, or use an escape item. Do not "finish off" a monster at this HP unless it is one hit from death
  and can't kill you.
- HP ≤ max/7 or HP ≤ 5: this is "major trouble" — **pray** if your prayer is available (below). Otherwise
  Elbereth / stairs / escape items immediately.

Prayer:
- Prayer fixes major trouble if your prayer timeout is low enough and your Luck/alignment are OK. The
  timeout starts at ~300 and drops ~1/turn; after a successful prayer it resets to ~50–1000 (usually a few
  hundred). **Rule: first prayer is OK after turn ~300; afterwards wait at least ~1000 turns between
  prayers.** Every prayer (turn, reason, outcome) goes in `state.md`.
- Never pray in Gehennom (your god can't hear you there). Never pray just for small trouble early in the
  timeout window. Don't pray if you've angered your god (killed peacefuls, etc.) — check state.md.
- Prayer also fixes: Weak/Fainting from hunger, food poisoning (`FoodPois`), illness (`TermIll`), stoning
  (`Stone`), sliming (`Slime`), strangulation (`Strngl`), lycanthropy.

Elbereth (3.6 rules): standing on an engraved "Elbereth" makes most monsters flee instead of meleeing you.
It does **not** work on `@` humans and elves, minotaurs, shopkeepers/guards/priests, or the Riders. It is
erased if you attack (melee, fire, cast at monsters) while standing on it, and dust engravings can wear
away when they scare monsters — re-check with `engraving_here()`. Engrave *before* HP gets critical.

Never:
- melee a **floating eye** (blue `e`) — paralysis = death. Kill it with thrown daggers/arrows or ignore it.
- touch/eat **cockatrice/chickatrice** corpses or melee them bare-handed; flee their hissing if not stoning
  resistant... (you wield a weapon: melee is OK, but never bare hands, never eat).
- eat a corpse you haven't checked: no cockatrice/chickatrice/Medusa (stoning), no were-anything
  (lycanthropy), no green slime, no "tainted"/old corpses (older than ~50 turns, except lichen/lizard),
  no poisonous ones without poison resistance, **no dwarves** (you are a dwarf: cannibalism), no
  dogs/cats. When in doubt, don't — eat rations.
- attack anything `peaceful` (answer `n`/`no` to "Really attack?").
- quaff from fountains or sinks (except #dip for Excalibur), sit on thrones, or read unknown scrolls /
  put on unknown rings/amulets without thinking about the downside.
- descend when HP is low, when Weak, or when you don't know how you'd get back up.
- melee gas spores (grey `e` that explodes), or stand next to one when it dies.
- let a nymph or leprechaun get adjacent if you can avoid it; kill them fast or step away.
- send `#quit`. The harness refuses it anyway.

Status emergencies (the harness pauses on these):
- `Stone` (stiffening): eat a lizard corpse or acidic corpse, or pray. Minutes matter — act this turn.
- `Slime`: pray, or burn it (fire). `Strngl`: remove the amulet (`R`), or pray.
- `FoodPois` / `TermIll`: pray, or apply a unicorn horn. `Blind`/`Conf`/`Stun`/`Hallu`: stop moving
  near water/lava/traps; wait it out (`search`) in a safe spot or use a unicorn horn.
- "You feel feverish" = lycanthropy: pray (or eat a sprig of wolfsbane / holy water).

Hunger: eat when `Hungry` appears (not before `Hungry` if food is scarce). Keep 2+ food rations or
equivalent. Weak = emergency (eat now, or pray).

## 4. Memory protocol

Your context window is temporary; the files are not. Run memory lives in `play/runs/<game>/`:
- `state.md` — the **current** truth, rewritten as it changes: character, XL/HP/AC, intrinsics
  (resistances etc.), key inventory (letters!), identified item appearances, prayer log, altars/shops/
  stashes/stairs per level, dungeon branch levels (Mines entrance, Sokoban, Oracle, quest portal...),
  known dangers, current objective and plan.
- `journal.md` — append-only log, 1–3 lines per notable event: `T:1234 DL3 — killed a hill orc pack
  with Elbereth; HP 9/30; prayed (2nd prayer, first at T:650)`.
Update both at least every level change, after any fight that went badly, after identifying anything,
and before ending your shift. If you learn a general lesson (a mistake to never repeat, a harness quirk),
add it to `play/runs/<game>/lessons.md`.

## 5. Shift protocol

You play in shifts. At the start: read this manual, `play/PLAYBOOK.md` (relevant parts), `state.md`, the
last ~40 lines of `journal.md`, then `bin/nh obs` and `bin/nh history 30`.

End your shift when your instructions say so (e.g. after a number of tool calls, or at a milestone), or
when you need strategic input. Before ending: get to a safe state (no prompt open, not in melee, HP not
critical if at all possible), update `state.md` and `journal.md`, and reply with a short report: turn, level,
HP/XL/AC, what happened, current plan, open risks, and any harness problems.

If the harness misbehaves (wrong parse, stuck prompt, odd output), look at `bin/nh screen`, get the game
back to a sane state with `<Esc>`, note the problem in `play/runs/<game>/harness_notes.md` with the step
number (`#123`) and what you expected, and continue carefully.
