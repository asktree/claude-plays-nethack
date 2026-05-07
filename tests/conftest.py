"""Shared fixtures for the test suite.

We test against real NLE — no mocks, no hand-crafted obs. Each test gets a
deterministic game via `fresh_server(seed=N)`, which:
  - clears server STATE singletons (last_obs, character, seen_per_level,
    paused_exec, hooks)
  - points trajectory + live_state at tmp paths so the production
    game/trajectory dir is never touched
  - reloads game/hooks/*.py so hook state is identical regardless of test order
  - clears search_memory's module-level dict
  - calls _reset() with the requested seed

Tests express "play to a setup state" via seed + scripted prefix actions;
fixture-files for very long setups go in tests/fixtures/ if and when they
become painful.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
GAME_DIR = REPO_ROOT / "game"

# Make game-side modules importable for tests (search_memory, views, tactics).
if str(GAME_DIR) not in sys.path:
    sys.path.insert(0, str(GAME_DIR))


@pytest.fixture
def fresh_server(tmp_path, monkeypatch):
    """Reset all server-side singletons and start a clean game at the
    requested seed. Returns the server module so tests call helpers
    directly (server._do, server._safe_exec_python, etc).

    Usage:
        def test_something(fresh_server):
            server = fresh_server(seed=42)
            snap = server._observe()
            ...
    """
    monkeypatch.setenv("NETHACK_TRAJECTORY_DIR", str(tmp_path / "traj"))
    monkeypatch.setenv("NETHACK_LIVE_STATE", str(tmp_path / "live.json"))
    (tmp_path / "traj").mkdir()

    # Import here so monkeypatched env vars are picked up.
    from claude_plays_nethack import server

    def _start(seed: int):
        monkeypatch.setenv("NETHACK_SEED", str(seed))
        # NetHackChallenge disables `set_initial_seeds`, so calling
        # env.reset(seed=N) repeatedly on the same env doesn't truly reseed
        # NetHack's internal RNG — multiple resets at the same seed produce
        # different states. Workaround: close the env and recreate it.
        # Cost: ~1s per test (dlopen of nethack.so), acceptable for our
        # suite size and bought in exchange for full determinism.
        if server.STATE.env is not None:
            try:
                server.STATE.env.close()
            except Exception:
                pass
            server.STATE.env = None
        # Wipe singletons that survive across resets.
        server.STATE.last_obs = None
        server.STATE.last_info = None
        server.STATE.seen_per_level.clear()
        server.STATE.character = None
        server.STATE.terminated = False
        server.STATE.truncated = False
        server.STATE.paused_exec = None
        # Reload hooks so all tests start from the same registry state.
        server.HOOKS = {"post_do": [], "post_reset": [], "post_observe": []}
        server._HOOKS_LOADED = False
        server._load_hooks()
        # Clear search_memory across tests so counts don't bleed.
        if "search_memory" in sys.modules:
            sys.modules["search_memory"]._counts.clear()
        server._reset()
        return server

    yield _start

    # Cleanup: kill any thread the test left parked.
    try:
        from claude_plays_nethack import server as _s
        _s._drop_paused()
    except Exception:
        pass


@pytest.fixture
def play(fresh_server):
    """Convenience: start a game at `seed`, optionally play `actions`,
    return (server, last_snap)."""
    def _play(seed: int, actions=()):
        server = fresh_server(seed)
        snap = server._observe()
        for a in actions:
            snap = server._do(a)
        return server, snap
    return _play
