# Local NetHack 3.6.7 for harness development

Real games are played on a public server. This local build exists so the
terminal harness can be developed and tested against a vanilla 3.6.7 tty game
that we control. It has the tty and curses window ports (tty is the default),
the stock Linux hints, and one opt-in patch (`NETHACK_SEED`) for reproducible
tests. With `NETHACK_SEED` unset, it behaves like vanilla 3.6.7.

## Build

```sh
scripts/build_nethack.sh              # about 50 s the first time, then a no-op
NH_FORCE=1 scripts/build_nethack.sh   # rebuild and reinstall anyway
```

Needs `cc` (gcc), `make`, `patch` and the ncurses dev files (`libncurses-dev`).
yacc/lex (bison/flex) are optional: when either is missing, the script uses the
pre-generated `sys/share/{lev,dgn}_{yacc,lex}.c` files shipped with 3.6.7.
nroff is not needed; the preformatted Guidebook is used.

What the script does:

1. Downloads `https://www.nethack.org/download/3.6.7/nethack-367-src.tgz` once
   into `~/.cache/nethack-build/` and checks its SHA-256
   (`98cf67df6debf9668a61745aa84c09bcab362e5d33f5b944ec5155d44d2aacb2`).
2. Unpacks an unmodified copy to `~/src/nethack-3.6.7` if that path does not
   exist yet. This copy is never patched or overwritten, so other agents can
   use it for rule lookups (`src/`, `dat/`, `doc/Guidebook.txt`).
3. Unpacks a fresh build tree to `~/.cache/nethack-build/NetHack-3.6.7`,
   applies `scripts/patches/*.patch`, and generates
   `sys/unix/hints/linux-local`. That file is `hints/linux` with `PREFIX`,
   `HACKDIR` and `SHELLDIR` moved under the prefix. The hints already enable
   tty and curses (`-DCURSES_GRAPHICS`), DLB, SYSCF, DUMPLOG and TIMED_DELAY.
   It then runs `setup.sh` and `make all`. The make output goes to
   `~/.cache/nethack-build/build.log`, which contains many `-Wformat-overflow`
   warnings from vanilla code; they are harmless.
4. Installs the same files with the same modes as `make install`, without its
   `rm -rf $(HACKDIR)`. That means rebuilds keep `record`, `logfile`,
   `xlogfile`, `save/`, `dumplog/` and bones. Each file is copied to a
   temporary name and renamed into place, so rebuilding while games are
   running is safe.
5. Writes `sysconf` (see below) and a stamp file, `$NH_PREFIX/.build-stamp`.
   The stamp records the tarball, patches, script, prefix, compiler and
   lex/yacc mode. When none of these change, a re-run exits immediately.

| env var | default | meaning |
|---|---|---|
| `NH_PREFIX` | `$HOME/.local/nethack-3.6.7` | install prefix. It is compiled into the binary, so only `[A-Za-z0-9._/+-]` characters are allowed |
| `NH_BUILD_DIR` | `$HOME/.cache/nethack-build` | tarball cache, build tree and `build.log` |
| `NH_PRISTINE_SRC` | `$HOME/src/nethack-3.6.7` | where to keep the unmodified source; set to `""` to skip |
| `NH_SKIP_PATCHES` | empty | patch file names to leave out, e.g. `seed.patch` for a pure vanilla build |
| `NH_SHIPPED_LEXYACC` | `0` | `1` = use the shipped lexer/parser even if lex/yacc are installed |
| `NH_FORCE` | `0` | `1` = ignore the stamp |

## Where things are

With the default `NH_PREFIX=$HOME/.local/nethack-3.6.7` (for root this is
`/root/.local/nethack-3.6.7`):

| path | what |
|---|---|
| `$NH_PREFIX/bin/nethack` | launcher: vanilla `sys/unix/nethack.sh`. It exports `HACKDIR`, changes into it and runs the binary |
| `$NH_PREFIX/lib/nethackdir/` | `HACKDIR`, the playground |
| `…/nethackdir/nethack`, `recover`, `nhdat`, `symbols`, `license` | the game binary, the crash-recovery tool and the game data |
| `…/nethackdir/sysconf` | system config. It is regenerated on every build, so change the script instead of editing it |
| `…/nethackdir/dumplog/<name>.<YYYYMMDDhhmmss>.txt` | one dump per finished game |
| `…/nethackdir/xlogfile`, `logfile`, `record` | per-game log lines and the top-ten list |
| `…/nethackdir/save/<uid><name>.gz` | save files |
| `…/nethackdir/<uid><name>.<n>` | lock and level files of games in progress, e.g. `0tester1.0` |
| `~/src/nethack-3.6.7/` | unmodified 3.6.7 source |

`nethack --showpaths` prints the paths that the binary actually uses.

### sysconf: the three changes from vanilla

- `WIZARDS=*`: any user can run `nethack -D` (wizard mode).
- `MAXPLAYERS=0`: lock files are named `<uid><playername>`. Any number of
  games with different names can run at once. Starting a second game under a
  name that is already playing gets the "game in progress" prompt (see
  Gotchas). A value from 1 to 25 would switch to shared `alock`, `block`, …
  letter locks, which have no per-name check.
- `DUMPLOGFILE=dumplog/%n.%D.txt`: `%n` is the player name. `%D` is the time
  the game ended, local time (the container runs in UTC). The end time is
  used because every seeded game has the same frozen start time. The path is
  relative to the playground the game runs in: `$HACKDIR/dumplog/`, or
  `$NETHACKDIR/dumplog/` for a private playground (see Wizard mode).

## Running a game

The character can be set from the command line:

```sh
NH_PREFIX=$HOME/.local/nethack-3.6.7
tmux new-session -d -s nhtest -x 80 -y 24 \
  "NETHACKOPTIONS='gender:female,align:lawful,!autopickup,time,showexp,color' \
   $NH_PREFIX/bin/nethack -u tester1 -p valkyrie -r dwarf"
tmux capture-pane -p -e -t nhtest                  # screen, with SGR escapes
tmux display -p -t nhtest '#{cursor_x} #{cursor_y}' # cursor (0-based)
```

For test runs that should not depend on the machine, use an options file with
the `@file` form and a private `HOME`:

```sh
cat > /tmp/t1/nethackrc <<'EOF'
OPTIONS=role:valkyrie,race:dwarf,gender:female,align:lawful
OPTIONS=!autopickup,time,showexp,color
EOF
tmux new-session -d -s nhtest -x 80 -y 24 -e HOME=/tmp/t1 \
  -e NETHACKOPTIONS=@/tmp/t1/nethackrc -e NETHACK_SEED=42 \
  "$NH_PREFIX/bin/nethack -u tester1"
```

How options are read in 3.6.7:

- The `/path` or `@/path` form of `NETHACKOPTIONS` reads only that file.
- An options string in `NETHACKOPTIONS` is applied **on top of**
  `~/.nethackrc`; it does not replace it.
- With `NETHACKOPTIONS` unset, only `~/.nethackrc` is read.
- `sysconf` `OPTIONS=` lines, if any, always apply first.

Pinning the character. The Unix port of 3.6.7 accepts `-u name`, `-p role`,
`-r race`, `-@` (random), `-D`, `-X` and `-d dir`. There is **no `-g` or
`-a`**. Set gender and alignment with the `gender:` and `align:` options, or
use the name suffix `-u tester1-val-dwa-fem-law`. If any of the four is left
unset, the game shows a "Shall I pick…" or "Is this ok? [ynq]" menu first.
This happens even when the combination is forced: Valkyries are always female
and dwarves are always lawful.

What a new tty game shows at 80x24:

1. Only if a lock exists for the name: `There is already a game in progress
   under your name.  Destroy old game? [yn] (n)`. See Gotchas.
2. The legacy intro text ("It is written in the Book of …"), ending in
   `--More--`. `!legacy` skips it.
3. `Velkommen tester1, welcome to NetHack!  You are a lawful dwarven
   Valkyrie.` (the greeting differs by role). If another message is queued,
   a `--More--` follows. It can wrap onto row 2 because the welcome line and
   `--More--` together are longer than 80 columns. On a full moon (today,
   2026-09-26, is one), the next message is `You are lucky!  Full moon
   tonight.`; on a new moon it is `Be careful!  New moon tonight.`.
4. The live map. Row 0 is messages, rows 1–21 are the map, and rows 22–23 are
   the two status lines. The cursor sits on `@`.

Quitting cleanly: `#quit` then Enter, `Really quit? [yn] (n)` → `y`. In
wizard mode, `Dump core? [ynq] (q)` → `n`. Then `Do you want your possessions
identified? [ynq] (n)` → `q`. In tty the process exits with status 0. In
curses there is one more `>>` prompt; press Enter. The dumplog and the
xlogfile line are written at this point.

Curses (`OPTIONS=windowtype:curses`) works, but it looks different from tty.
The `--More--` prompt is `>>`. Popups have borders. The map uses the
line-drawing `curses` symset unless a symset is set explicitly. Under
`LANG=C`, `tmux capture-pane` without `-e` shows those characters as
`lqqk`/`x`, and floor as `~`. The same seed gives the same game in tty and
curses.

## Deterministic games: `NETHACK_SEED`

`scripts/patches/seed.patch` changes three files: `src/hacklib.c`,
`src/u_init.c` and `include/extern.h`. Setting `NETHACK_SEED=<decimal
integer>` makes a new game reproducible:

- Both RNGs (core and display) are seeded with the value. Normally NetHack
  reseeds from `/dev/urandom` every time a level is created or revisited; with
  the seed set, it does not.
- Game logic that reads the wall clock sees a frozen time,
  **2001-01-01 12:00:00 UTC** (a Monday, moon phase 1, daytime). This covers
  the moon phase (no full or new moon message or luck change), Friday the
  13th, `night()`, `midnight()`, and the game's birthday. The birthday picks
  shopkeeper names, the anthole species, unidentified glass gem prices and
  T-shirt text. As a result, seeded dumplogs say `Game began 2001-01-01
  12:00:00`, and the xlogfile has `starttime=978350400` and
  `birthdate=20010101`. End times and realtime are real.
- Unset or empty: vanilla behavior. Any other value that is not a decimal
  integer makes the game print `NETHACK_SEED="…" is not a decimal integer.`
  and exit with status 1 before it touches the terminal.

What was checked, using `tmux capture-pane -e` plus the cursor position:

- The same seed gave byte-identical screens for the intro, the welcome, the
  first map, and the map after `20s` (20 turns with monsters moving).
- In wizard mode, the same seed gave an identical Dlvl 5 after `^V 5`, which
  means new-level generation is deterministic.
- Seeds 42, 43 and 7 all differed from each other, and so did unseeded runs.
- Two separate builds gave identical screens for seed 42.
- A vanilla build (`NH_SKIP_PATCHES=seed.patch`) ignores the variable.

What can still make seeded runs diverge:

- **Bones.** A level may load bones left in the shared `HACKDIR` by an earlier
  test that died. The 1-in-3 roll is seeded; whether a bones file exists is
  not. Use `OPTIONS=!bones`, or a private playground.
- **`record`.** Player-monster statues and graveyard corpses take their names
  from the top-ten file, and a named corpse uses the RNG differently. Games
  scoring 0 points (for example, quitting on turn 1) do not add entries.
- **Save and restore.** The RNG state is not saved. A restored game is
  reseeded from `NETHACK_SEED`, so it is reproducible but does not continue
  the original random sequence.
- **Different options, role or race.** These change the game. The player
  name does not affect the RNG, but it appears on screen, so compare runs
  that use the same name.
- **Mail delivery.** `MAIL` is compiled in, as in vanilla. It is harmless in
  a container; `OPTIONS=!mail` removes it entirely.

## Wizard mode

`nethack -D …`. The Debug-Mode Quick Reference is `dat/wizhelp` (press `?`
in the game). The main commands:

- `^W` wish, `^F` map the level, `^V` level teleport (`?` gives a menu),
  `^T` teleport, `^G` create a monster, `^I` identify the pack, `^E` find
  hidden things, `^X` extended enlightenment.
- Extended commands: `#levelchange`, `#wizintrinsic`, `#wizmakemap`,
  `#terrain`, `#wizwhere`, `#polyself`.

Wizard mode has these quirks:

- **The name is always `wizard`.** `-u` is ignored, the lock is `0wizard.*`,
  and the dumplog is `wizard.*.txt`. So only one wizard game can run per
  playground. For parallel wizard games, give each its own playground. The
  sysconf is still read from the real `HACKDIR`:

  ```sh
  pg=/tmp/pg1; mkdir -p $pg/save $pg/dumplog
  for f in nhdat symbols license; do ln -s $NH_PREFIX/lib/nethackdir/$f $pg/; done
  touch $pg/record $pg/logfile $pg/xlogfile $pg/perm
  NETHACKDIR=$pg NETHACKOPTIONS=@/tmp/t1/nethackrc $NH_PREFIX/bin/nethack -D
  ```

  Locks, saves, `xlogfile` and dumplogs then stay in `$pg`. A fresh
  playground also gives seeded tests an empty `record` and no bones.
- **Extra prompts.** Quitting asks `Dump core? [ynq]` (answer `n`). Death asks
  `Die? [yn]`; `n` revives you. A death that could leave bones asks
  `Save bones? [yn]`.
- Wizard games write a dumplog and an xlogfile line (`flags` has bit 0x1
  set), but they never enter `record`.

## Gotchas

- **Stale locks always prompt.** Vanilla `unixconf.h` defines `NETWORK`,
  which turns off the check for whether the locking process is still alive.
  Any `<uid><name>.*` lock less than 3 days old therefore triggers `There is
  already a game in progress under your name.  Destroy old game? [yn] (n)`,
  even when the process is gone. SIGKILL, SIGTERM or a crash leave such
  locks behind.
  - Answer `y` only if nothing is running under that name.
  - Or delete `$HACKDIR/<uid><name>.*` before starting.
  - Or rebuild a save from the level files with
    `$HACKDIR/recover -d $HACKDIR <uid><name>`.
  - `n` exits with status 1 and leaves the running game alone.
- **SIGHUP saves the game.** `tmux kill-session`, or closing the terminal,
  makes NetHack save to `save/<uid><name>.gz` and release its locks. The
  next start under that name prints `Restoring save file...` and continues
  that game. To end a test game, `#quit` it, or delete the save afterwards.
- **Do not kill nethack processes by pattern** (`pkill -f nethack`). Other
  agents run games with the same binary. Kill your own tmux sessions by
  exact name, and use a private socket (`tmux -L <name>`) for harness runs.
- 3.6.7 option names: `align:` is correct; `alignment:` is 3.7 only. An
  unknown option stops startup at `Hit return to continue:`.
- Leftover arguments after the options (for example from `-g female`) are
  ignored, and the game prints `MAXPLAYERS are set in sysconf file.` before
  the screen clears.
- Names listed in `GENERICUSERS` (`player`, `games`, `nethack`, …) make the
  game ask `Who are you?`. Use other names.
- The tty port requires a terminal (`You must play from a terminal.`), and
  `TERM` must have a terminfo entry. `tmux-256color` and `screen` both work.
- `TIMED_DELAY` is on, as on public servers. Zaps and thrown objects animate
  with short delays, so capture only after the screen has stopped changing.
- The install belongs to the user who built it. HACKDIR files are mode 0600,
  as in vanilla, so another Unix user fails with `Unable to open SYSCF_FILE.`
- `make install` would wipe HACKDIR, and `make all` needs nroff for the
  Guidebook. The script avoids both.
