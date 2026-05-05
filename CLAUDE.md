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

## Stack

- Python 3.12 (brew). NLE rebuilt with `CC=/usr/bin/clang` to dodge a libc++ symbol mismatch — see memory note `nle_build_macos.md`.
- FastMCP 3.x for the server. Test in-process via `from fastmcp import Client; Client(mcp)`.
- Env: `NetHackChallenge-v0` (full 121-action space).

## Design principles (don't drift from these without redesign)

- **MCP not bash.** The persistent NLE kernel needs to live in the server process; per-call subprocess restarts kill the tactical-loop pattern.
- **NetHack vocabulary unchanged.** Don't wrap actions into `move_north()` etc — NLE enums (`Command.READ`, `CompassDirection.N`) ARE the domain vocabulary. The gamer already knows them.
- **No seeded tactics.** The `tactics/` infra goes in only after we observe what the gamer reaches for. Don't preempt.
- **Trajectory logging in `do()`, not via PostToolUse.** Tactical loops will call `do` many times per Claude tool call; PostToolUse would miss them.
- **Token budget will tie to XP, not depth.** LLMs rush descents; a depth-rebate would reward the failure mode.
