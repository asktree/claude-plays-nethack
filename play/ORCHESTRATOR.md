# Orchestrator runbook: the live game on Hardfought

You are the **orchestrator** of Claude's attempt to ascend NetHack 3.6.7 on the public server Hardfought
(us.hardfought.org), as the account **ClaudeAscends** (a lawful female dwarven Valkyrie). You don't play the
moves yourself: you run **player shifts** (subagents of type `nethack-player`), review them, keep the
record, fix the harness when it misbehaves, and make strategic calls. The human is hands-off; only involve
them for account/server trouble or if the game is lost.

**For the human — starting this session on your Mac** (once; ~5 minutes):
```
brew install tmux python@3.12            # skip what you already have
git clone https://github.com/asktree/claude-plays-nethack.git
cd claude-plays-nethack
git checkout claude/beautiful-newton-2fgb6f
scripts/setup.sh --allow-harness         # checks tools, runs the unit tests, pre-approves bin/nh
caffeinate -i claude remote-control      # keeps the Mac awake while the session runs
```
Then, in that session (from the terminal or the Claude Code app), say: *"You are the orchestrator of the
live game. Follow play/ORCHESTRATOR.md."* It will ask you once for the email to register with (it stays
in `play/secrets/`, never committed or shown publicly). After that it plays on its own; keep the Mac on
and online.

Read these first: `play/PLAYER.md` (the interface and survival protocol every player follows),
`play/PLAYBOOK.md` (strategy), `docs/research/astra-lessons.md` §2–4 and §8 (the only other LLM
ascension, and both of its deaths), `docs/research/servers.md` §2 and §4–5 (lobby, timeouts, disconnects).

## 0. Hard rules (server)

- **Never press `t`** in the lobby (TNNT tournament: bots banned). Only the vanilla NetHack 3.6.7 game.
- **Never answer `y` to "Destroy old game?"** (erases the game). The harness refuses it anyway.
- **Stale-process countdown** ("There are some stale nh367-hdf processes, will recover in N seconds. Press a
  key NOW...") → send **nothing** for ~20 s. The harness refuses keys while it's on screen.
- **Idle timeout: 30 min without game output = hangup-save.** The daemon sends a `^R` redraw after 20 min
  of silence, but only at the command prompt. So **never leave the game at a prompt, menu or `--More--`
  between shifts**, and never think for 30 minutes inside a wish/genocide prompt (a hangup there cancels it;
  after offering the Amulet on Astral it would make the game unwinnable).
- One game connection at a time. No reconnect storms. Don't spam the server.
- Credentials live only in `play/secrets/hardfought.json` (gitignored). Never print or commit them.

## 1. One-time setup on this machine

```
scripts/setup.sh --allow-harness     # tmux, ssh, Python >= 3.10, .venv, unit tests; and pre-approves
                                     # the harness commands for Claude Code on this machine only
                                     # (.claude/settings.local.json, not committed)
scripts/build_nethack.sh             # optional: local 3.6.7 for practice games
```
Create `play/secrets/hardfought.json` (the human provides the email):
```
python3 - <<'PY'
import json, secrets, string, pathlib
pw = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
p = pathlib.Path("play/secrets/hardfought.json"); p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps({"user": "ClaudeAscends", "password": pw, "email": "<EMAIL FROM THE HUMAN>"}))
p.chmod(0o600); print("written")
PY
```

## 2. Connect, register, install the rc file, start the game

```
bin/nh start-remote live --server hardfought    # tmux session nh-live running ssh; daemon started
bin/nh --game live screen                        # the dgamelaunch logged-out menu (l/r/w/q)
```
Watch it yourself any time: `tmux -L nh attach -r -t nh-live` (read-only).

First time only — register (this also logs you in):
```
bin/nh --game live exec <<'EOF'
from tactics import server
print(server.register())
EOF
```
Later sessions: `server.login()` instead.

The harness refuses plain keystrokes while the lobby is on screen (a stray key there can start a game or
enter the TNNT tournament): the `tactics.server` helpers pass `force=True`; when you navigate a menu by hand,
read the screen and use `bin/nh --game live do KEY --force`.

**Install the rc file** (`play/hardfought.nethackrc` — tested on the local build; it presets the character,
turns off in-game mail, and restores the screen layout the parser expects). From the logged-in lobby, open
`j) Manage settings` and read the screen (`bin/nh --game live screen`) — this submenu has never been
captured verbatim, so choose by reading: edit the **NetHack 3.6.7** config (`nh36rc`), with the `virus`
editor if asked. Once the editor is open:
```
bin/nh --game live exec <<'EOF'
from tactics import server
server.vi_replace_buffer(open("play/hardfought.nethackrc").read())
EOF
```
Verify: `curl -s https://www.hardfought.org/userdata/C/ClaudeAscends/nethack/ClaudeAscends.nh36rc | diff - play/hardfought.nethackrc`
(must be identical, apart from possibly a trailing newline). Fix and repeat until it is.

**Start the game**: from the lobby press `1` (NetHack, various versions), read the submenu, and pick
**NetHack 3.6.7** (Astra used `V`; confirm on screen). Never pick a variant, 5.0.0, or TNNT. With our rc the
game starts with no questions: expect "welcome to NetHack! You are a lawful female dwarven Valkyrie."
If it asks "Shall I pick character's race, role...", the rc didn't load — quit that screen with `q`/Esc if
possible and fix the rc first. On later sessions use `p) Play last game [nh367-hdf]` (`server.play_last_game()`)
or `r) Resume last save`.

Check that the rc took effect (no game time):
```
bin/nh --game live exec <<'EOF'
o = options.bool_options()
print({k: o.get(k) for k in ("timed_delay", "sparkle", "autodescribe", "mail", "autopickup", "rest_on_space")})
EOF
```
Expect `timed_delay: False, sparkle: False, autodescribe: False, mail: False`. If one is wrong, fix it for this
session with `options.set_bool('timed_delay', False)` etc., and fix the rc file for the next game.

Then create the run memory: `mkdir -p play/runs/live`, copy `play/runs/TEMPLATE-state.md` to
`play/runs/live/state.md`, create `journal.md`, and note the game's start time and dumplog URL
(`https://www.hardfought.org/userdata/C/ClaudeAscends/nethack/dumplog/`).

## 3. The shift loop

Each shift is one `nethack-player` subagent (model: the strongest available, e.g. `fable`), run in the
background. Prompt template:

> Game: `live` — the REAL game on Hardfought (public record; one life). Working directory: the repo root.
> Always use `bin/nh --game live ...`. Follow your standing instructions (play/PLAYER.md, play/PLAYBOOK.md,
> memory in play/runs/live/). Current objective: <objective from state.md / your review>. Specific cautions:
> <anything from your review>. Budget: ~120 tool calls, then stop at a safe point (command prompt, no
> prompt/menu open, not in melee), with state.md and journal.md updated. Log harness problems in
> play/runs/live/harness_notes.md. Final reply: turn, Dlvl, HP/max, XL, AC, what happened, plan, risks.

Between shifts (every time):
1. Read the report and `bin/nh --game live obs`; confirm the game sits at the command prompt.
2. Skim the new journal lines and harness notes. Fix harness bugs **before** the next shift if they could
   cause a death (edit `src/nh`/`play/tactics`, run `scripts/setup.sh` tests, then `bin/nh --game live
   reload` for tactics or `bin/nh --game live daemon` for core code — the ssh connection lives in tmux and
   survives daemon restarts).
3. Commit and push the run memory:
   `git add play/runs/live && git commit -m "live: T<turn> D<dlvl> <summary>" && git pull --rebase && git push`.
4. Decide the next objective. Consult PLAYBOOK.md and the Astra lessons. Big decisions (entering the
   Castle, Gehennom, Medusa, the quest; using a wish) deserve a dedicated planning step: read the relevant
   wiki pages (`knowledge/wiki/`), write the plan into state.md, and hand it to the next shift.
5. Launch the next shift.

Checkpoints worth a pause and a careful plan: first descent below Dlvl 4, Minetown, Sokoban, Oracle, quest
portal, big room, Medusa, Castle, Valley, each Gehennom lord, Vlad's, Wizard's tower, invocation, Sanctum,
the ascent, each Plane, Astral.

## 4. Disconnects

The pane dies (`bin/nh --game live screen` shows `Pane is dead (status N ...)`):
1. `bin/nh --game live restart` (new ssh in the same tmux session), then `server.login()`.
2. Lobby shows `r) Resume last save [nh367-hdf]` → `server.resume_last_save()`.
3. It shows `[none]` but a game should exist: check https://www.hardfought.org/nh/index.php (is ClaudeAscends
   playing?). If listed: `server.play_last_game()` and send **nothing** during the stale-process countdown
   (`server.wait_out_stale()`). If not listed and no save: **stop** — it may be a crash; ask the human to
   contact the admins (#hardfought on Libera, or admin@hardfought.org). Never start a new game over it.
4. After restoring, check turn/HP/position against state.md.

## 5. When to involve the human

- Account problems, bans, server outages longer than a few hours, a crash needing admin recovery.
- The character dies (report with the dumplog link; don't start a new game without the human's go-ahead).
- The game is won: report the ascension with the dumplog link.

## 6. Coordination with the dev session (the coach)

Another Claude session (in the cloud) develops the harness on the same branch and watches the live game
through Hardfought's public, growing ttyrec (`scripts/watch_ttyrec.py ClaudeAscends` — HTTPS only).
- Pull before each shift (`git pull --rebase`) to get harness fixes; after core changes restart the
  daemon (`bin/nh --game live daemon`), after tactics changes `bin/nh --game live reload`.
- **Read `play/runs/live/coach.md` before each shift** — the coach writes observations, warnings and
  strategy suggestions there. Acknowledge items you acted on (append "ack T<turn>: ...").
- Keep your commits to `play/runs/live/` (harness fixes are fine too — pull/rebase first; the coach
  avoids editing `play/runs/live/` except `coach.md`).
- Push memory after every shift so the coach sees current state.
