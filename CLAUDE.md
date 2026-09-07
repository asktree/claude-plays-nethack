# claude-plays-nethack — dev rulebook

You are working ON the harness, not playing the game. The player-Claude lives in `game/`.

## Workspace layout

```
.                       <- you are here (advisor / dev)
├── pyproject.toml
├── src/claude_plays_nethack/
│   └── server.py       <- FastMCP server: reset, observe, do, list_actions
├── run.sh              <- launches gamer-Claude in game/
└── game/               <- gamer-Claude's cwd
    ├── CLAUDE.md       <- player rulebook (with full action table embedded)
    ├── .mcp.json       <- registers nethack MCP server
    └── trajectory/     <- jsonl per session, gitignored
```

The split exists so that:
- Your CLAUDE.md (this file) addresses the dev role; the gamer's addresses the player role.
- Your session logs land at `~/.claude/projects/-Users-em-Coding-claude-plays-nethack/`; the gamer's land at `~/.claude/projects/-Users-em-Coding-claude-plays-nethack-game/`. Cleanly separable.

## Reading what the gamer did

- **Game trajectory** — `game/trajectory/<timestamp>-<session>.jsonl`. One line per `do()`: action, keycode, reward, blstats snapshot, message.
- **Gamer's reasoning + tool calls** — Claude Code session jsonl at `~/.claude/projects/-Users-em-Coding-claude-plays-nethack-game/<session>.jsonl`. Full conversation including the gamer's thinking about each move.
- Read both together for post-mortems. Timestamps line up.

## Running

`./run.sh` from the project root cd's into `game/` and launches `claude` there. Gamer picks up `game/CLAUDE.md` and `game/.mcp.json` automatically.

Env vars that change harness behavior at startup:

| var | meaning |
|---|---|
| `NETHACK_TRAJ=<path>` | resume the game in this trajectory file (replays all logged steps, then live mode). `latest` = most recent file in `game/trajectory/`. |
| `NETHACK_REPLAY_TO=<n>` | with `NETHACK_TRAJ`, branches the trajectory: cp + truncate to first `n` step events, then live. Original file untouched. |
| `NETHACK_SEED_CORE=<int>` | core seed for fresh runs (drives all NetHack RNG including character selection when `NETHACK_CHARACTER=@`). |
| `NETHACK_SEED_DISP=<int>` | disp seed (anti-TAS RNG). Defaults to core if omitted. |
| `NETHACK_SEED_LGEN=<int>` | optional level-gen seed; if unset, level gen rolls off the core RNG. |
| `NETHACK_CHARACTER=<spec>` | character spec passed to NLE. `@` (default) = random role/race/gender/align (deterministic given seed). `val-hum-fem-law` etc pins all four. Errors if conflicts with a resume-mode trajectory header. |
| `NETHACK_NO_PROGRESS_LIMIT=<n>` | abort after this many `_do` calls in a row without the in-game clock advancing. Default 10000. |
| `NETHACK_MAX_EPISODE_STEPS=<n>` | override NLE's internal step cap (default 5000 → NLE force-quits the game). We default to 1e9 so long games aren't truncated. Set to a smaller value only for tests that exercise the cap. |
| `NETHACK_SEED=<int>` | shorthand: sets both core and disp to the same int. |

## Stack

- Python 3.12 (brew). NLE rebuilt with `CC=/usr/bin/clang` to dodge a libc++ symbol mismatch — see memory note `nle_build_macos.md`.
- **Forked NLE** at `/Users/em/Coding/nle-fork` — patched to expose `obs.seenv` (per-cell `levl[].seenv` bitmask, NetHack's ground-truth visibility data). Patches: `include/nletypes.h`, `win/rl/winrl.cc`, `win/rl/pynethack.cc`, `nle/nethack/nethack.py`, `nle/env/base.py`, `CMakeLists.txt` (https sourceware for bzip2 since git:// port 9418 is firewalled). Second patch (2026-09-07): `ubirthday` is derived from the time seed when `fix_moon_phase` is on (`src/u_init.c`, `src/nlernd.c`, `include/nlernd.h`) — vanilla reads the wall clock for shopkeeper names, anthole species and glass-gem prices, so same-seed games diverged at the first shop. Trajectories recorded before that patch won't replay past their first shop. Reinstall via `cd /Users/em/Coding/nle-fork && CC=/usr/bin/clang CXX=/usr/bin/clang++ pip install --no-cache-dir .` from the project venv.
- FastMCP 3.x for the server. Test in-process via `from fastmcp import Client; Client(mcp)`.
- Env: `NetHack-v0` (the base NLE env — full 121-action space, supports `env.seed(core, disp, reseed=False, lgen)` for full determinism). We re-implement Challenge's no-progress timeout at the harness level.

## Trajectory format (v2)

Line 0 is a `header` event with seeds, character spec, env id, originating session. Subsequent lines are `step` events — one per `env.step()` call:

- `kind="gamer"` — the gamer issued this action via `_do`.
- `kind="auto_more"` — the harness pumped a `--More--` prompt automatically.

Replay = read each step event in order, call `env.step(action_index)`, validate post-step `blstats`/`message` against the recording. Errors loudly on divergence (NLE version mismatch, fork drift, etc).

## Design principles (don't drift from these without redesign)

- **MCP not bash.** The persistent NLE kernel needs to live in the server process; per-call subprocess restarts kill the tactical-loop pattern.
- **NetHack vocabulary unchanged.** Don't wrap actions into `move_north()` etc — NLE enums (`Command.READ`, `CompassDirection.N`) ARE the domain vocabulary. The gamer already knows them.
- **No seeded tactics.** The `tactics/` infra goes in only after we observe what the gamer reaches for. Don't preempt.
- **Trajectory logging in `do()`, not via PostToolUse.** Tactical loops will call `do` many times per Claude tool call; PostToolUse would miss them.
- **Token budget will tie to XP, not depth.** LLMs rush descents; a depth-rebate would reward the failure mode.
