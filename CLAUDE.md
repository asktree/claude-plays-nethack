# claude-plays-nethack

Goal: Claude ascends **NetHack 3.6.7** on the public server **Hardfought** (account `ClaudeAscends`,
lawful female dwarven Valkyrie), fully autonomously, on the public record (dumplogs, ttyrecs, xlogfile).

## Which role are you?

- **Player** (you were given a game name and a shift budget): follow `play/PLAYER.md` and
  `play/PLAYBOOK.md`; memory in `play/runs/<game>/`. The `nethack-player` agent type is this role.
- **Orchestrator of the live game**: follow `play/ORCHESTRATOR.md`.
- **Harness developer**: read on.

## Layout

```
bin/nh                      CLI: start-local / start-remote / restart / obs / do / exec / cont / info ...
src/nh/                     the terminal harness
  tmuxterm.py               game runs in a tmux pane (socket -L nh); capture + send-keys; raw log via pipe-pane
  screen.py, parse.py       screen model (chars/colors/inverse), state classification, status parsing
  game.py                   settle detection, unit-wise key sending with safety stops, --More--, messages
  kernel.py                 persistent Python namespace; exec pauses on events (messages, HP, monsters...)
  daemon.py                 per-game unix-socket server (run/<game>/daemon.sock); keepalive for remote
  monitor.py, danger.py     auto-farlook monster tracking + danger notes
  tracker.py                harness memory: branch/level via ^O, prayers, per-level features
  mapscan.py, render.py     map scans (monsters/objects/features) and LLM-facing text
  data/                     monsters/objects JSON from 3.6.7 source; corpse rules (eat.c)
play/
  PLAYER.md, PLAYBOOK.md    the player's manual and strategy
  ORCHESTRATOR.md           running the live campaign
  tactics/                  kernel helpers (travel, explore, farlook, inventory, sokoban, server lobby...)
  kernel_boot.py            wires tactics into the kernel (`bin/nh reload` re-runs it)
  nethackrc                 canonical options; hardfought.nethackrc = + server extras (tested locally)
  runs/<game>/              run memory (state.md, journal.md, lessons.md, harness_notes.md)
  secrets/                  credentials (gitignored)
knowledge/                  offline NetHackWiki (wiki/ gitignored; scripts/fetch_wiki.py regenerates)
docs/research/              astra-lessons.md (first LLM ascension post-mortem), servers.md (Hardfought/NAO)
scripts/                    setup.sh, build_nethack.sh (local 3.6.7), nh-connect.sh (ssh), gen_nh_data.py
tests/                      test_nh_parse/data/monitor.py, test_sokoban_data.py, test_tactics.py
run/                        runtime state per game (gitignored): raw.log, events.jsonl, harness_state.json
```

The old NLE-based MCP harness (`src/claude_plays_nethack/`, `game/`) is kept for reference; its notes are
in `docs/legacy-nle-CLAUDE.md`.

## Development rules

- Test against the local build: `bin/nh start-local <name> --seed N [--wizard]`; restart the daemon after
  core changes with `bin/nh --game <name> daemon`; tactics changes: `bin/nh --game <name> reload`.
  Don't restart the daemon of a game a player agent is using mid-shift.
- Unit tests: `PYTHONPATH=src python3 -m pytest -q tests/test_nh_parse.py tests/test_nh_data.py tests/test_nh_monitor.py tests/test_sokoban_data.py tests/test_tactics.py` (the other files in tests/ belong to the legacy NLE harness).
- Every harness change that could affect safety (key sending, prompt detection, pausing) needs a test or a
  live check on a local game. A misparse on the live server can kill the character.
- Player feedback lives in `play/runs/*/harness_notes.md` — treat it as the bug tracker.
- Commit messages end with the attribution lines the session provides.
