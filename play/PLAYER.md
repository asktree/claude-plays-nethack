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
| `bin/nh cont` / `bin/nh cont --reply KEYS` | resume a paused exec (optionally answering the open prompt first). Use `--reply` only for a prompt your script does NOT answer itself; if the script's next `do()` sends exactly the same keys, the harness skips it (it would otherwise be typed as commands) |
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

**Reading the output.** The `#N` in the header counts harness steps (keys sent), not game turns — quote it
when reporting harness problems. Game time is `T:`.
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
    **Pick-one menus** (e.g. `#loot`'s "Do what with the box?") close on the letter itself: send just the
    letter. The harness sends menu keys one at a time and stops (unsent keys reported) when a letter
    closes the menu or opens another, so a trailing `<CR>` can't confirm an empty selection in the next one.
  - `[getpos]`: a map cursor (travel/farlook). Tactics handle these; `<Esc>` cancels.
- **Monsters are identified automatically** with farlook (`;`) the first time they appear, so you see
  `peaceful dwarf`, `tame kitten`, `statue of a newt` (statues look like monsters!), `jackal`. Labels
  follow each monster; when same-looking monsters crowd together (a werejackal and the jackals it
  summoned, peaceful and hostile gnomes) they are looked at again, and a returning monster that was
  peaceful is re-checked, so a hostile never inherits a peaceful label.
  Anything marked `peaceful` must not be attacked (it angers your god and/or the monster's friends).
  Dangerous monsters get a `!!` note underneath (special threat, and "stronger than you" when their
  difficulty is well above your XL). Take those notes seriously.
- Status: `HP:cur/max`, `Pw`, `AC` (lower is better), `XL` experience level, `T:` game turn, then hunger
  (`Hungry`, `Weak`, `Fainting` — act!), encumbrance (`Burdened`...), conditions (`Blind`, `Conf`, `Stun`,
  `Hallu`, and the deadly ones: `Stone`, `Slime`, `Strngl`, `FoodPois`, `TermIll`).

## 2. The kernel (`bin/nh exec`)

Python in a persistent namespace. Every `do()` inside it takes one game step and **pauses the script when
anything noteworthy happens**: any message, HP loss, a new monster in view, a new status condition, hunger
getting worse, a level change, level-up, game over. You then see what happened and decide: `bin/nh cont` to
resume, or do something else (which abandons the script). This makes multi-step plans safe. A swarm or pack
pauses once: more members of a species that paused in the last 5 turns, turning up within 4 squares of it,
don't pause again (they are in the monster list). The obs shows `!! you WIELD a blessed lamp — not a weapon`
(or `EMPTY-HANDED`) when the harness knows you hold no weapon — e.g. after a raw `#rub` or applying a
pick-axe; `rub()`/`dig()` wield your weapon again themselves. Attacking a cockatrice while known to be
empty-handed without gloves (or with the weapon state unknown: run `inventory()`) is refused.

Available in the kernel:

| helper | purpose |
|---|---|
| `do(keys, quiet=False, ok=None)` | one step; `quiet=True` = don't pause on messages (info-only keys); `ok=[regex]` = these messages don't pause |
| `obs` | last snapshot: `obs.status.hp`, `.hpmax`, `.xl`, `.exp` (points), `.ac`, `.turn`, `.gold`, `.hunger`, `.conditions`, `.ldesc`; `obs.hero` (x,y); `obs.messages`; `obs.kind` (`command`, `yn`, `menu`...), `obs.prompt`; `obs.screen.at(x,y)`, `obs.screen.chars` (24 strings), `obs.screen.dump()`; `obs.monsters` (dicts: ch,x,y,color,dist,desc,note,new,tame,peaceful,statue,pet), `obs.hostiles(radius)`, `obs.adjacent_hostiles()`; `obs.gone` (dangerous monsters that left view in the last ~20 turns, also printed as `out of view: ...` — a gas spore in the dark is invisible even to telepathy); `obs.objects` (ch,x,y,kind,pile,color,dist; a gray `*` is `rock/gray stone`, a coloured one `gem/glass`); `obs.features` (name,x,y: stairs, fountain, altar, doors, traps...; the one under you is listed as e.g. `fountain (under you)`; `obs.under` is its glyph (`'{'`, `'>'`...) or None — stairs under an object/statue are learned from the "There is a staircase down here." message when you step there or look with `:`); `obs.menu` (iterate it for selectable items: `.letter`, `.text`, `.selected`; `.page`/`.pages` — the iterator covers the CURRENT page only: press `>` for the next one) |
| `look()` | re-read the screen without acting (a fresh snapshot: its `.messages` is empty — read the messages of a step from the snap `do()` returned) |
| `travel(x, y)` | NetHack's travel command to a known map spot (the last square is a plain step, so gold and your thrown weapons there are picked up — NetHack's travel itself never picks anything up) (stops when something happens). It goes in **short legs** (8 squares, 4 with a hostile around) because NetHack's travel only stops for a monster that is already adjacent — a fast monster could otherwise reach you unseen during one long leg; `leg=0` = one long leg. It opens closed doors in the way (travel itself never does). NetHack never starts a travel next to a non-tame monster: `travel()` then waits for a peaceful to move, and raises `NavError` naming the hostile/peaceful, a locked door, or "no known path" instead of silently not moving. `blockers()` lists non-tame monsters adjacent to you. NetHack's travel refuses to start next to ANY non-tame monster, so with a peaceful beside you `travel()` takes plain steps along its own route (never into a monster), then waits, then steps back out of a 1-wide corridor to let a peaceful come out (twice) before giving up. `path_to(x, y, through_monsters=True)` tells "a monster is in the way" from "no route". If a monster steps onto the target square, the last step raises `NavError` instead of attacking it. `travel(x, y, with_pet=True)`: bring your pet — 3-square legs, waiting ('.') while it is more than 2 squares behind (up to 12 turns in all, never with a hostile within 3); raises `PetLost` if it drops out of view |
| `travel_to('>')` | travel to the nearest `>` (or any map symbol; stairs/fountains/altars hidden under items or monsters are remembered); `go_down()` / `go_up()` travel, re-travel after routine stops, check you are on the stairs, wait up to `wait_pet=6` turns for a nearby pet to come next to you (it only follows when adjacent), then use them (NavError instead of pressing `>` elsewhere). When your pet is within 7 squares at the start they travel in **pet-keeping legs** (`with_pet`, below) and say so when they leave it behind. With two staircases on a level (a branch: Mines, Sokoban) they take the one that stays in your branch — the harness learns where each staircase leads whenever you take or arrive on it (`game.stair_links`) — or the one toward `to='Mines'` / `to='Sokoban'` / `to='Dungeons'`; if neither is known yet they say so and take the nearest. `travel()` refuses a target square occupied by a non-tame monster |
| `explore()` | auto-explore this level using the game's own unexplored-frontier data; pauses on events; returns a dict whose `reason` is `explored ...` only when nothing reachable is left (→ search for secret doors or move on; `r['dead_ends']` / `dead_ends()` lists corridors that just stop — stand on one and `search(15)`), or `blocked: ...` naming locked doors (kick them yourself with `kick_door(x, y)` — never shop doors or in Minetown), frontiers cut off by avoided squares, boulders in the way or next to unexplored space (`r['boulders']`; travel never pushes boulders — step into one to push it), or an adjacent hostile. **auto_fight** (default on, also for `travel()`): hostiles next to you that are all trivial for you (`auto_fightable(m)`: `threat()` trivial, not sessile, no passive attack, no danger note — newts, rats, jackals...) are fought on the spot with `fight()` and don't cause a new-monster pause (it prints `auto-fight: ...`); anything else pauses as before. `auto_fight=False` turns it off |
| `frontiers()` | list unexplored frontier spots, nearest first |
| `farlook(x, y)` | describe what is at (x,y) (no game time) |
| `inventory()` / `inventory_text()` | parsed inventory: list of dicts with keys `letter`, `text`, `class`, `buc` |
| `here()` | what's on the floor here (`:`) |
| `dig('>')` / `dig('h')` | dig down (through to the level below: an escape) or sideways with your pick-axe/mattock: applies again past the pit stage, then wields your weapon again. Not on stairs/altars/fountains, in Sokoban, or in shops (the shopkeeper grabs your pack) |
| `eat(letter=None)`, `pickup(pattern=None)` | `eat('q')` eats inventory item q, declining the floor-corpse questions NetHack asks first (`eat()` eats the floor food instead); `pickup('dagger|ration')` looks first and takes only matching objects (all if no pattern; a lone non-matching object is left alone). The eating and pickup guards still apply |
| `loot_all()` | take everything out of the container on your square (`#loot`; handles the pick-one "Do what?" menu and "Auto-select every item"); a locked box is first unlocked with your key/lock pick/credit card if you carry one, else it says so — kick it (`<C-d>`+dir, expect "WHAMM!"/"THUD!") or `#force` with a blade |
| `unlock()`, `unlock(x, y)` | unlock the box under you / the locked door next to you with your key, lock pick or credit card (answers the direction, says y to "unlock it?", never to "lock it?"; retries when interrupted). Not shop doors |
| `bag_put(bag, 'mq')`, `bag_take(bag, pattern=None)` | a CARRIED container (`loot_all()` is for floor ones): put items in one by one (the "stash one item" choice), take out everything or the items whose text matches `pattern`. Identified/named types are listed BY NAME ("potion of paralysis", "potions called water"), so the pattern is also tried against their unidentified look from `discoveries()` (`'white'` finds the paralysis potion); nothing matching → `LookupError` listing the contents. Only for a known container: applying a bag of tricks makes a monster |
| `discoveries()`, `with_looks(text, disco)` | the `\` list (no game time) as `[(name, look)]`: `('potion of paralysis', 'white potion')`, `('potion called water', 'clear potion')`, `('magic lamp', 'lamp')`. A potion a monster drinks in view is identified by the game itself ("drinks an effervescent potion ... looks completely healed" = full healing). A blessed clear potion ("potions called water" once named) is holy water |
| `search(n)`, `rest(n)` | count-prefixed search / rest (interrupted by events) |
| `elbereth()` | engrave Elbereth in the dust where you stand, read it back, re-engrave once if garbled; `engraving_here()` reads what's here (flags a BROKEN Elbereth). Refuses while hallucinating or stunned (half / a quarter of the letters come out garbled) and warns while confused |
| `rest_on_elbereth(turns=100)` | heal on a verified Elbereth: re-engraves when broken, rests in bursts, stops at full HP or when something that ignores Elbereth comes near |
| `head_to(x, y)` | make for a spot across UNEXPLORED space (mazes, the Mines, Gehennom, a level you fell into): while no known path leads there it travels to the frontier square (walkable, beside never-seen space) nearest to (x, y), looks again, and repeats; then `travel()`s the rest. `screen_frontiers()` lists those squares. (`explore()` itself now side-steps a peaceful that blocks NetHack's travel with a few plain steps) |
| `path_to(x, y)` | our known-map path to (x,y) avoiding known traps/avoid() squares (None = no known path); walk it one checked step at a time with `walk_path(path)` |
| `fight(x=None, y=None, stop_hp=0.45)` | melee adjacent hostiles one checked blow at a time until dead/gone; below stop_hp it pauses unless the adjacent hostiles' worst-case damage is under a third of your HP (a newt can't hurt you at 21 HP). Prints the target's passive attacks (acid, rust...) with their worst case per hit before the first blow; refuses paralysing/sliming/disenchanting ones, stoning ones only when you wield nothing (a wielded weapon protects your hands; the cockatrice's own touch can still start stoning), and pauses when one hit's passive could take more than half your current HP (energy vortex, spotted jelly...) — `allow_passive=True` overrides. `fight(x, y)` on an `I` square swings at the unseen monster there. It also pauses before meleeing a monster that EXPLODES on you (yellow light: ~100 turns blind; black light: hallucination; spheres) unless you're already blind — kill those at range. Never touches peacefuls/pets. **Run fights with `bin/nh exec --hp-pause 0.4`** so ordinary hits below 70% HP don't pause every round |
| `fight_until_clear(radius=2, stop_hp=0.5)` | hold your square at a chokepoint (a zoo's doorway, a corridor) and fight a crowd: melees whatever comes adjacent (via fight()), waits a turn while hostiles within `radius` approach, returns `{'reason': 'clear' | 'HP ...' | '... not coming' | 'max_turns', 'kills', 'turns'}`. Newly seen monsters pause only if `threat()` says dangerous (or unknown); HP loss/messages still pause — run it with `--hp-pause 0.4`. Not for fights in the open (you get surrounded) |
| `throw('o', 'l')`, `zap('f', 'h')` | throw item o east / zap wand f west, checking each prompt (a zap sends the direction only if asked — an empty wand won't turn it into a move); the thrown item's own hit/miss message doesn't pause. Both refuse (pause) when your pet or a peaceful is in the line of fire — before the first hostile for a throw, anywhere on the line for a zap (`friendly_in_line(dir, ray=)` checks; `force=True` overrides). Bounced rays aren't checked |
| `dip_into('d', 'T')` | `#dip` item d INTO potion T (a fountain here is declined): holy water — cursed item "glows amber" = now uncursed, uncursed "glows with a light blue aura" = now blessed; unholy water — "black aura" = cursed, blessed "glows brown" = uncursed. Returns outcome + the item's text before/after |
| `rub('d', max_rubs=1)` | `#rub` a lamp (stops at the first djinni). #rub WIELDS the lamp; it wields your weapon again afterwards (`rewield=True`). Magic lamp: 1/3 per rub a djinni; blessed → wish 80% (uncursed 20%, cursed 5%/80% hostile). The wish prompt pauses: answer ONLY with `cont --reply '...<CR>'` |
| `dip('a')` | one `#dip` into the fountain/pool you stand on, prompts answered, outcome classified (EXCALIBUR, WISH, WATER DEMON, fountain dried up, item rusted...), plus the item's inventory line before/after (a silent fountain curse shows only there). Excalibur odds: 1/6 per dip at XL5+; a fountain dries up ~1 dip in 3, so expect 2–3 fountains |
| `engrave_test('f')` | engrave-identify wand f in one call (writes a dust "x" first if nothing is engraved here, answers the prompts, writes Elbereth); returns/prints the verdict ("sleep or death", "digging", ...). Refuses on a burned/permanent engraving; pauses on a wish prompt. Not in shops |
| `buy_protection()` | next to a peaceful temple priest: donates exactly 400 x XL gold (the protection band is 400–599 x XL) and reports the outcome and AC change; never leaves the offer prompt empty (that angers the priest) |
| `pay(x=None, y=None)` | pay the shopkeeper for everything you picked up (`p`, "Itemized billing?" → no). With several shopkeepers in range the game asks "Pay whom?": pass that shopkeeper's square. Shop tips: the square just inside the door is the shopkeeper's post — nothing is offered or priced there (step one further in to sell); prices ("for sale, N zorkmids") appear only on plain steps, not `m`-steps or travel; a shopkeeper blocks the door while you carry a pick-axe/mattock (`bag_put()` it first) |
| `threat('gnome lord')` | `trivial` / `normal` / `dangerous` vs you now (difficulty vs XL, worst-case hit vs HP, notes) — use it to ignore harmless monsters consistently |
| `last_seen('gas spore')` | monsters that recently left view: last position, turn, turns ago |
| `prayer_check()`, `pray(force=False)` | trouble class (major/minor/none) + estimated chance the timeout is low enough + advice; `pray()` refuses without major trouble and ≥80% odds (force=True overrides); its own good messages don't pause, and it prints a one-line verdict (SUCCESS/FAILED, holy water made, troubles fixed, gifts). Read §3! |
| `step(dir, n)` | move n squares one at a time; like every movement helper (`travel`'s last step, `walk_path`) it NEVER attacks: a monster (not your pet) on the next square → `NavError` — attack on purpose with `do('F' + dir)` or `fight()` |
| `avoid((x,y), ...)`, `bad_squares()`, `walk_path(cells)` | mark squares to avoid on this level (`avoid(clear=True)` forgets them). Known traps are remembered automatically — on each level the harness reads the game's own trap memory with `#terrain`, so traps hidden under objects count too — and both survive daemon restarts; `travel()`/`explore()` detour around them |
| `pause(reason)` | hand control back to yourself from inside a script |
| `mon('soldier ant')` | monster stats (level, speed, attacks, resistances, corpse benefits) + danger note |
| `corpse('killer bee', age=0, poison_res=False)` | is this corpse safe for us to eat? (SAFE/RISKY/DEADLY/NEVER + benefits) |
| `obj('speed boots')`, `price_candidates('SCROLL_CLASS', 20)` | object facts; price-identification candidates by base price |
| `price_id('SCROLL_CLASS', buy=133)` / `price_id('SCROLL_CLASS', sell=40)` | shop price identification with the exact shk.c rules (your Charisma, the fixed 1-in-4 +1/3 surcharge on unidentified items, lowballing shopkeepers): the unidentified items consistent with the quoted unit price and/or the sell offer for one item. Quote several numbers to narrow it down |
| `wiki('regex')`, `wiki_page('Floating eye')` | search/read the offline NetHack wiki (`knowledge/wiki/`) |
| `sokoban.solve()` | Sokoban: recognises which of the 8 levels you're on and how far along the board is, then runs the level's **verified** solution one boulder at a time, checking the board after every push (pauses on anything unexpected; `solve(max_steps=3)` for a few steps). `sokoban.progress()` shows level, step k/N and the next push. The solutions come from the wiki, replayed in a simulator of the 3.6 rules |
| `sokoban.board()`, `sokoban.push(x, y, 'hhk')` | Sokoban by hand (if the board deviated from the plan): show the board; push the boulder at (x,y) left,left,up with checked walking |

Also `bin/nh info`: the harness's own memory — current branch/level (from the game's `^O` overview),
prayer log with turns-ago, per-level stairs/fountains/altars seen.

Status while polymorphed: the game shows `HD:n` instead of `Xp`; `obs.status.polymorphed` is True,
`obs.status.hd` is the form's hit dice and `obs.status.xl` keeps your own level (a pause says
"polymorphed" / "back in your own form"). While a full-screen menu covers the status lines,
`obs.status` is the last readable one with `obs.status.stale == True`.

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

**Harness guards** (they raise `PermissionError` / refuse the keys; `force=True` / `--force` overrides —
think twice): moving or `F`-fighting into a **floating eye, gas spore or green slime** (unless you're
Blind); answering `y` to eating a corpse that is certain death or permanent harm (cockatrice, chickatrice,
Medusa, green slime, were-creatures, Riders, **dwarves** — cannibalism, dogs/cats) **or possibly tainted**:
the harness records every kill (monster, square, turn), so a corpse you saw die less than ~50 turns ago is
fine, while an older one or one of unknown age (you didn't see it die there) is refused — tainted meat is
fatal food poisoning. Lichens and lizards never rot. `corpse(name, age)` explains a verdict;
`game.kills[game.level_key()]` lists this level's records `(name, (x, y), turn)`; confirming
"Really attack ...?" (NetHack asks that only about **peaceful** monsters); a plain step onto a **known trap**
(NetHack doesn't ask; go around, or force=True to jump into a hole/trap door or enter a magic portal on
purpose); **while hallucinating**, attacking/moving into any monster (NetHack doesn't ask "Really attack?"
then, and a peaceful or a floating eye looks like anything); **while blind**, attacking an `I` (remembered
unseen monster: could be a shopkeeper/priest); **while confused/stunned**, any step next to a peaceful or a
floating eye (your step can go astray into it); genocide answers that would genocide your own race or role
(class `h`/`@`, "dwarf", "valkyrie" — `master mind flayer` at a *class* prompt means class `h`!); any key
after death except the end-of-game answers; any key in the server lobby (use `tactics.server` helpers);
`#quit`; `y` to "Destroy old game?"; Esc, an empty line or command-looking text at the **wish** prompt (an
empty wish is a random object — the harness pauses there: answer with `cont --reply '<wish><CR>'`); a bare prefix key (`F`, `m`, `g`, `G`, `M`) at the end of a `do()` (NetHack silently waits for its direction — send `do('Fh')`); any key during the server's stale-process countdown; `y` to "Beware,
there will be no return! Still climb?" (the up stairs of dungeon level 1 end the game without the Amulet);
picking up a **cockatrice/chickatrice corpse** (`,` when it's the only object here, or confirming a pickup
menu with it selected — wear gloves and force=True); **while blind**, stepping onto a square known to hold
one (you feel what you step on; bare-handed that is instant stoning); **attacking from your Elbereth square**
(melee, or a throw/fire/zap/kick whose direction has a monster in line — down, up and empty lines are fine:
it erases the engraving and costs −5 alignment — step off first; the harness knows the square's engraving
from the last "You read: ..." message, and forgets it after a downward zap); a plain step into a **peaceful** (you can't
swap places with peacefuls; wait a turn or go around); a plain step into **water/lava `}`**
(NetHack only stops running/travel, not a single step; lava is death without fire resistance) unless
levitating/flying; **eating while Satiated** and `y` to "Continue eating?" (choking is death 19 times in 20;
force=True only for an emergency cure like a lizard corpse against stoning); `y` to a **tin** that smells
like something never to be eaten (cockatrices/"chicken", Medusa, dwarves, dogs/cats, were-creatures, green
slime) and to any tin while hallucinating; picking up an unknown **gray stone** (kick it first: a loadstone
doesn't budge — cursed ones can't be dropped).

What the monster list shows in odd states: while hallucinating every monster is `hallu` (no names, no
"new monster" pauses; everything is looked at again when it ends); `I` markers are `unseen`; a `]` is a
**mimic** (kept out of travel routes); when **engulfed**, `obs.engulfed` is True and the list holds just
the engulfer — `fight()` attacks it with `F` + any direction.

## 3. Survival protocol (non-negotiable)

**Every decision starts with: HP, status conditions, adjacent monsters, escape route.**

HP rules (let H = HP / max HP):
- H < 0.6: stop exploring. Fight only if clearly winning; otherwise back off, rest, heal.
- H < 0.4: disengage **now**: retreat upstairs, stand on Elbereth (`elbereth()`), quaff a known healing
  potion, or use an escape item. Do not "finish off" a monster at this HP unless it is one hit from death
  and can't kill you.
- HP ≤ 5, or HP ≤ max/5 (XL1–5; /6 at XL6–13, /7 at XL14–21): this is "major trouble" — **pray** if
  `prayer_check()` says the odds are good (below). Otherwise Elbereth / stairs / escape items immediately.

Prayer (exact 3.6.7 rules, `pray.c`) — **always run `prayer_check()` first; `pray()` refuses unless it's sensible:**
- Prayer works only if the prayer timeout is ≤ 200 with **major** trouble (≤ 100 with minor trouble, 0 with
  none), your Luck ≥ 0, and your god isn't angry. The timeout starts at 300 and drops 1 per turn; after a
  successful prayer it resets to a random value (median ~350, long tail); each wish adds 50–149.
- **Praying too soon is a disaster**: −3 Luck, your god gets angry, and divine wrath strikes. So never pray
  "just in case". Chance the timeout is low enough for major trouble, by turns since the last successful
  prayer: 300 → 66%, 500 → 87%, 800 → 92%, 1000 → 95%, 1500 → 98%. First prayer: fine from ~T:100 in major
  trouble (timeout 300 − turn ≤ 200).
- **Major trouble** = stoning, sliming, strangling, lava, food poisoning/illness, Weak/Fainting hunger,
  lycanthropy, and **low HP: HP ≤ 5, or HP ≤ maxHP/5 at XL1–5 (/6 at XL6–13, /7 at XL14–21, /8 at XL22–29)**,
  with maxHP capped at 15×XL for this test. Everything else (cursed items, a welded weapon with a free
  off-hand, blindness, confusion, stun, hallucination, Hungry) is *minor* and not worth a prayer at Luck 0.
- Never pray in Gehennom. Log every prayer (turn, reason, result) in state.md (`bin/nh info` also tracks it).

Elbereth (3.6.7 rules, from the source): standing on an engraving that reads exactly "Elbereth" makes most
monsters flee instead of meleeing you. It does **not** scare `@` humans and elves, minotaurs,
shopkeepers, vault guards, peacefuls or **blind** monsters, and does nothing in Gehennom or on the Planes.
**Every step smudges dust engravings on the square you leave and the one you enter** — engrave where you
stand, when you need it (a pre-made one is usually broken when you step back onto it). Attacking, firing,
applying or kicking while standing on it smudges it too (and attacking a monster it scares costs
alignment: "You feel like a hypocrite"); dust also decays at random. `elbereth()` reads it back and
re-engraves once if a letter slipped; `engraving_here()` flags a BROKEN one. While Blind, dust can't be
felt: an engraving made blind is unverified. Engrave *before* HP gets critical.

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
