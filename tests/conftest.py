"""Shared fixtures for the test suite.

Tests run against a real NetHack-v0 env with explicit `env.unwrapped.seed(
core, disp, reseed=False)` per test, so:
  - Same seed → same role/race/dungeon/monster/item — every detail.
  - Tests can assert specific NetHack message text without role flakiness.
  - One env per session, reseed-and-reset per test (no env-recreate cost).

Default character is pinned to "val-hum-fem-law" (Valkyrie-Human-Female-
Lawful) so tests don't depend on whatever role "@" produces — Valkyrie
spawns with the same starting kit/items deterministically. Override per
test by passing `character="..."` to fresh_server.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
GAME_DIR = REPO_ROOT / "game"

if str(GAME_DIR) not in sys.path:
    sys.path.insert(0, str(GAME_DIR))


@pytest.fixture
def fresh_server(tmp_path, monkeypatch):
    """Reset all server-side STATE singletons and start a clean game at the
    requested seed/character. Returns the server module so tests call helpers
    directly (server._do, server._safe_exec_python, etc).

    Usage:
        def test_something(fresh_server):
            server = fresh_server(seed=42)  # Valkyrie by default
            ...
        def test_alt_role(fresh_server):
            server = fresh_server(seed=42, character="wiz-elf-mal-cha")
            ...
    """
    monkeypatch.setenv("NETHACK_TRAJECTORY_DIR", str(tmp_path / "traj"))
    monkeypatch.setenv("NETHACK_LIVE_STATE", str(tmp_path / "live.json"))
    (tmp_path / "traj").mkdir()

    from claude_plays_nethack import server

    def _start(seed: int, character: str = "val-hum-fem-law"):
        # Tell the harness which seed/character to use. Cleared at fixture
        # teardown via monkeypatch.
        monkeypatch.setenv("NETHACK_SEED_CORE", str(seed))
        monkeypatch.setenv("NETHACK_SEED_DISP", str(seed))
        monkeypatch.setenv("NETHACK_CHARACTER", character)
        # Make sure no resume-mode env vars leak in.
        monkeypatch.delenv("NETHACK_TRAJ", raising=False)
        monkeypatch.delenv("NETHACK_REPLAY_TO", raising=False)
        # Force a fresh env per test. Reusing the env across tests is
        # supposed to be safe (env.unwrapped.seed() + env.reset() is
        # deterministic in isolation), but pytest's stdout capture seems
        # to interact with NLE's ttyrec/save-state in a way that produces
        # nondeterministic blstats across tests when reused. Closing and
        # rebuilding per test costs ~1s but eliminates the flake.
        if server.STATE.env is not None:
            try:
                server.STATE.env.close()
            except Exception:
                pass
            server.STATE.env = None
            server.STATE.env_character = None
        # Reset STATE singletons.
        server.STATE.last_obs = None
        server.STATE.last_info = None
        server.STATE.seen_per_level.clear()
        server.STATE.character = None
        server.STATE.terminated = False
        server.STATE.truncated = False
        server.STATE.paused_exec = None
        server.STATE.step_n = 0
        server.STATE.no_progress_count = 0
        server.STATE.last_time = None
        server.STATE.replaying = False
        server.STATE.last_hostile_counts = __import__("collections").Counter()
        # Hooks: clear and re-load for predictable per-test state.
        server.HOOKS = {"post_do": [], "post_reset": [], "post_observe": []}
        server._HOOKS_LOADED = False
        server._load_hooks()
        # search_memory module-level state.
        if "search_memory" in sys.modules:
            sys.modules["search_memory"]._counts.clear()
        # _reset will close+rebuild env if character changed; otherwise reseed
        # the existing one. NetHack-v0 supports env.unwrapped.seed().
        server._reset()
        return server

    yield _start

    try:
        from claude_plays_nethack import server as _s
        _s._drop_paused()
    except Exception:
        pass


@pytest.fixture
def resume_server(tmp_path, monkeypatch):
    """Resume the env from a recorded trajectory fixture.

    Copies the fixture into tmp_path (so live appends from the resumed game
    don't pollute the fixture), points NETHACK_TRAJ at the copy, and invokes
    _reset() — which replays every step event in order, validating each
    against the recording, then leaves the env at the resume point ready
    for live actions.

    Use for repro tests built from real game state: snapshot the current
    trajectory under tests/fixtures/, then write a test that resumes and
    runs whatever sequence reproduces the bug.
    """
    import shutil
    from pathlib import Path

    def _resume(fixture_path):
        fixture_path = Path(fixture_path)
        traj_dir = tmp_path / "traj"
        traj_dir.mkdir()
        target = traj_dir / fixture_path.name
        shutil.copy(fixture_path, target)

        monkeypatch.setenv("NETHACK_TRAJECTORY_DIR", str(traj_dir))
        monkeypatch.setenv("NETHACK_LIVE_STATE", str(tmp_path / "live.json"))
        monkeypatch.setenv("NETHACK_TRAJ", str(target))
        # Resume reads seeds + character from the header — env vars must not
        # conflict, so clear any leftovers.
        for v in ("NETHACK_REPLAY_TO", "NETHACK_CHARACTER",
                  "NETHACK_SEED_CORE", "NETHACK_SEED_DISP", "NETHACK_SEED"):
            monkeypatch.delenv(v, raising=False)

        from claude_plays_nethack import server

        # Same singleton-reset dance as fresh_server: NLE env reuse can
        # smuggle state across tests.
        if server.STATE.env is not None:
            try:
                server.STATE.env.close()
            except Exception:
                pass
            server.STATE.env = None
            server.STATE.env_character = None
        server.STATE.last_obs = None
        server.STATE.last_info = None
        server.STATE.seen_per_level.clear()
        server.STATE.character = None
        server.STATE.terminated = False
        server.STATE.truncated = False
        server.STATE.paused_exec = None
        server.STATE.step_n = 0
        server.STATE.no_progress_count = 0
        server.STATE.last_time = None
        server.STATE.replaying = False
        server.STATE.last_hostile_counts = __import__("collections").Counter()
        server.HOOKS = {"post_do": [], "post_reset": [], "post_observe": []}
        server._HOOKS_LOADED = False
        server._load_hooks()
        if "search_memory" in sys.modules:
            sys.modules["search_memory"]._counts.clear()

        server._reset()  # triggers replay codepath via NETHACK_TRAJ
        return server

    yield _resume

    try:
        from claude_plays_nethack import server as _s
        _s._drop_paused()
    except Exception:
        pass


@pytest.fixture
def play(fresh_server):
    """Convenience: start at seed/character, optionally play actions, return
    (server, last_snap)."""
    def _play(seed: int, actions=(), character: str = "val-hum-fem-law"):
        server = fresh_server(seed, character=character)
        snap = server._observe()
        for a in actions:
            snap = server._do(a)
        return server, snap
    return _play
