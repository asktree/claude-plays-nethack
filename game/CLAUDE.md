# You are playing NetHack.

You play through the `nethack` MCP server. Four tools, that's the whole surface.

## Tools

- **`reset()`** — start a new game. Call this once at the beginning.
- **`observe()`** — return the current observation without taking an action.
- **`do(action)`** — take one action. `action` is an int (0..120) or a name like `"Command.READ"`, `"CompassDirection.N"`, `"north"`, `"MORE"`. Full table below.
- **`exec(python_code)`** — run Python in a persistent kernel. **Use this when you'd otherwise call `do()` many times in a row, or when a custom view function would render the dungeon better than the default screen.** The kernel persists across calls (imports, variables, your own helper functions). In scope each call: `obs` (current snapshot with raw `chars`/`colors` grids), `do(action)` (returns new snapshot), `observe()`. The `game/views/` and `game/tactics/` directories are on `sys.path` — `from views import crop`.

## Observation shape

Each tool returns a dict:
- `screen` — the rendered TTY screen as a multi-line string. What a human sees.
- `message` — the top-of-screen message line (e.g. `"You hit the kobold."`).
- `blstats` — bottom-line stats: `hitpoints`, `max_hitpoints`, `depth`, `time`, `experience_level`, `hunger_state`, `armor_class`, `gold`, `energy`, `max_energy`, `x`, `y`, plus the six attribute scores.
- `inventory` — list of `{letter, text}` for what you're carrying.
- `cursor` — `[row, col]` of the cursor on the TTY (your `@` is usually here). Note **row first, NLE order**.
- `terminated` / `truncated` — game-over flags.
- `reward` (on `do`) — gym reward for the step.
- `chars`, `colors` — only present inside `exec()`. 24x80 raw grids of glyph codes / color codes.

## How to play

1. Call `reset()` to start.
2. Read the screen, message, and blstats.
3. Call `do(...)` for a single action, or `exec(...)` to script a sequence.
4. If a `--More--` prompt or menu appears, send `"MORE"` (which sends `\r`) or the appropriate key.
5. Repeat. Stay alive. Descend. Win.

## Views (pure read-only renderings)

Inside `exec(...)`, import from `views/`:

- **`crop(obs, radius=4)`** — centered (2r+1)×(2r+1) ASCII window around your `@`. Better for spatial reasoning than parsing the full 80-col screen.

You can write new views — pure functions over `obs` returning strings or simple data. Add them in `game/views/`. Don't put side-effecting code in views; that belongs in tactics (later).

## Trajectory

Every `do()` is logged to `trajectory/<timestamp>-<session>.jsonl` automatically.

## What does not exist yet

- No `tactics/` library yet. You can compose actions with `exec()`; bring it up if you find yourself wanting reusable scripts.
- No persistent memory between runs.
- No save/load yet.
- No token budget meter yet.

## Practical advice

- NetHack rewards careful play. Don't rush descents — clear floors, find items, level up.
- Don't melee floating eyes (paralysis). Don't melee cockatrices (stoning).
- Pray when you're in real trouble (low HP, starving, stuck) — but not often, your god has a temper.
- Identify items cautiously. Read scrolls when surrounded by useful targets only after you have a sense of what they might be.
- Your pet helps. Let it fight when you can.
- Eat regularly but not constantly. Track your hunger state in `blstats`.

You know the game. Play.

## Action table (NetHackChallenge-v0, 121 actions)

| idx | name | key |
|---|---|---|
| 0 | CompassDirection.N | k |
| 1 | CompassDirection.E | l |
| 2 | CompassDirection.S | j |
| 3 | CompassDirection.W | h |
| 4 | CompassDirection.NE | u |
| 5 | CompassDirection.SE | n |
| 6 | CompassDirection.SW | b |
| 7 | CompassDirection.NW | y |
| 8 | CompassDirectionLonger.N | K |
| 9 | CompassDirectionLonger.E | L |
| 10 | CompassDirectionLonger.S | J |
| 11 | CompassDirectionLonger.W | H |
| 12 | CompassDirectionLonger.NE | U |
| 13 | CompassDirectionLonger.SE | N |
| 14 | CompassDirectionLonger.SW | B |
| 15 | CompassDirectionLonger.NW | Y |
| 16 | MiscDirection.UP | < |
| 17 | MiscDirection.DOWN | > |
| 18 | MiscDirection.WAIT | . |
| 19 | MiscAction.MORE | \r |
| 20 | Command.EXTCMD | # |
| 21 | Command.EXTLIST | M-? |
| 22 | Command.ADJUST | M-a |
| 23 | Command.ANNOTATE | M-A |
| 24 | Command.APPLY | a |
| 25 | Command.ATTRIBUTES | ^X |
| 26 | Command.AUTOPICKUP | @ |
| 27 | Command.CALL | C |
| 28 | Command.CAST | Z |
| 29 | Command.CHAT | M-c |
| 30 | Command.CLOSE | c |
| 31 | Command.CONDUCT | M-C |
| 32 | Command.DIP | M-d |
| 33 | Command.DROP | d |
| 34 | Command.DROPTYPE | D |
| 35 | Command.EAT | e |
| 36 | Command.ENGRAVE | E |
| 37 | Command.ENHANCE | M-e |
| 38 | Command.ESC | ESC |
| 39 | Command.FIGHT | F |
| 40 | Command.FIRE | f |
| 41 | Command.FORCE | M-f |
| 42 | Command.GLANCE | ; |
| 43 | Command.HISTORY | V |
| 44 | Command.INVENTORY | i |
| 45 | Command.INVENTTYPE | I |
| 46 | Command.INVOKE | M-i |
| 47 | Command.JUMP | M-j |
| 48 | Command.KICK | ^D |
| 49 | Command.KNOWN | \\ |
| 50 | Command.KNOWNCLASS | ` |
| 51 | Command.LOOK | : |
| 52 | Command.LOOT | M-l |
| 53 | Command.MONSTER | M-m |
| 54 | Command.MOVE | m |
| 55 | Command.MOVEFAR | M |
| 56 | Command.OFFER | M-o |
| 57 | Command.OPEN | o |
| 58 | Command.OPTIONS | O |
| 59 | Command.OVERVIEW | ^O |
| 60 | Command.PAY | p |
| 61 | Command.PICKUP | , |
| 62 | Command.PRAY | M-p |
| 63 | Command.PUTON | P |
| 64 | Command.QUAFF | q |
| 65 | Command.QUIT | M-q |
| 66 | Command.QUIVER | Q |
| 67 | Command.READ | r |
| 68 | Command.REDRAW | ^R |
| 69 | Command.REMOVE | R |
| 70 | Command.RIDE | M-R |
| 71 | Command.RUB | M-r |
| 72 | Command.RUSH | g |
| 73 | Command.RUSH2 | G |
| 74 | Command.SAVE | S |
| 75 | Command.SEARCH | s |
| 76 | Command.SEEALL | * |
| 77 | Command.SEEAMULET | " |
| 78 | Command.SEEARMOR | [ |
| 79 | Command.SEEGOLD | $ |
| 80 | Command.SEERINGS | = |
| 81 | Command.SEESPELLS | + |
| 82 | Command.SEETOOLS | ( |
| 83 | Command.SEETRAP | ^ |
| 84 | Command.SEEWEAPON | ) |
| 85 | Command.SHELL | ! |
| 86 | Command.SIT | M-s |
| 87 | Command.SWAP | x |
| 88 | Command.TAKEOFF | T |
| 89 | Command.TAKEOFFALL | A |
| 90 | Command.TELEPORT | ^T |
| 91 | Command.THROW | t |
| 92 | Command.TIP | M-T |
| 93 | Command.TRAVEL | _ |
| 94 | Command.TURN | M-t |
| 95 | Command.TWOWEAPON | X |
| 96 | Command.UNTRAP | M-u |
| 97 | Command.VERSION | M-v |
| 98 | Command.VERSIONSHORT | v |
| 99 | Command.WEAR | W |
| 100 | Command.WHATDOES | & |
| 101 | Command.WHATIS | / |
| 102 | Command.WIELD | w |
| 103 | Command.WIPE | M-w |
| 104 | Command.ZAP | z |
| 105 | TextCharacters.PLUS | + |
| 106 | TextCharacters.MINUS | - |
| 107 | TextCharacters.SPACE | (space) |
| 108 | TextCharacters.APOS | ' |
| 109 | TextCharacters.QUOTE | " |
| 110 | TextCharacters.NUM_0 | 0 |
| 111 | TextCharacters.NUM_1 | 1 |
| 112 | TextCharacters.NUM_2 | 2 |
| 113 | TextCharacters.NUM_3 | 3 |
| 114 | TextCharacters.NUM_4 | 4 |
| 115 | TextCharacters.NUM_5 | 5 |
| 116 | TextCharacters.NUM_6 | 6 |
| 117 | TextCharacters.NUM_7 | 7 |
| 118 | TextCharacters.NUM_8 | 8 |
| 119 | TextCharacters.NUM_9 | 9 |
| 120 | TextCharacters.DOLLAR | $ |

Movement aliases also accepted: `north south east west ne nw se sw up down`.
