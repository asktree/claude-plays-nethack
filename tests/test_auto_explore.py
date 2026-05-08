"""Tests for tactics/auto_explore.

Uses seed=5 with Valkyrie-Human-Female-Lawful pinned, which spawns into a
room with plenty of frontier and no immediate game-event interruptions.

Hostile-handling is delegated to the message-pause path now (see
auto_explore.py module docstring) — this test file no longer covers
"halts on visible hostile" because that decision moved out of the tactic.
"""

from __future__ import annotations


def _run_auto_explore(server, **kwargs):
    """Helper: call auto_explore with kernel injection."""
    from tactics.auto_explore import auto_explore
    return auto_explore(do=server._kernel_do, observe=server._kernel_observe, **kwargs)


def test_returns_well_formed_dict(fresh_server):
    """auto_explore always returns a dict with reason/iters/targets/searches."""
    server = fresh_server(seed=5)
    result = _run_auto_explore(server, max_iters=3)
    assert isinstance(result, dict)
    assert "reason" in result
    assert "iters" in result
    assert "targets" in result
    assert "searches" in result
    assert isinstance(result["targets"], list)
    assert isinstance(result["searches"], list)
    assert result["iters"] <= 3


def test_max_iters_cap_respected(fresh_server):
    """When the loop hits max_iters, return reason names it. Pick a fresh
    spawn (lots of frontier) so we never run out of cells before the cap."""
    server = fresh_server(seed=5)
    result = _run_auto_explore(server, max_iters=2)
    # Either cap was reached, or exploration finished/halted — but iters
    # should never exceed the cap.
    assert result["iters"] <= 2
    if result["iters"] == 2:
        assert "max_iters" in result["reason"]


def test_explores_to_frontier(fresh_server):
    """From a fresh spawn, auto_explore should make at least one travel
    attempt — `targets` is non-empty."""
    server = fresh_server(seed=5)
    result = _run_auto_explore(server, max_iters=5)
    assert len(result["targets"]) >= 1


def test_search_burst_records_to_search_memory(fresh_server):
    """When @ touches a likely_secret_doors candidate, auto_explore does a
    SEARCH_BURST. Each search bumps the per-cell count via the post_do
    hook (search_record). Engineer this by manually walking @ into a
    dead-end corridor before calling auto_explore.

    For now, a softer invariant: search_memory is module-level and any
    SEARCH issued during auto_explore (via the hook) updates it. We can't
    cheaply force a candidate-adjacent state without a known dungeon, so
    just verify that *if* searches happen, they get recorded.
    """
    server = fresh_server(seed=5)
    import search_memory
    pre = dict(search_memory._counts)
    result = _run_auto_explore(server, max_iters=5)
    post = dict(search_memory._counts)
    # If auto_explore did any SEARCH bursts, search_memory grew.
    if result["searches"]:
        assert len(post) > len(pre) or sum(post.values()) > sum(pre.values())
    # If no bursts happened, that's also fine (no candidates encountered).


def test_does_not_crash_with_max_iters_zero(fresh_server):
    """max_iters=0 should return immediately with a sensible reason."""
    server = fresh_server(seed=5)
    result = _run_auto_explore(server, max_iters=0)
    assert result["iters"] == 0
    assert result["targets"] == []
    # The for-loop body runs zero times, so we exit through the end-of-
    # function path with reason 'max_iters=0 reached'.
    assert "max_iters" in result["reason"]


def test_runs_inside_safe_exec(fresh_server):
    """auto_explore should compose with safe_exec — internal Travel-mode
    prompts are auto-suppressed by DEFAULT_AUTOCONTINUE, real game events
    pause the gamer normally."""
    server = fresh_server(seed=5)
    out = server._safe_exec_python(
        "from tactics import auto_explore\n"
        "result = auto_explore(max_iters=3)\n"
    )
    # Either completed (3 iters of pure travel), or paused on a real game
    # event (item, hostile reveal, hunger, etc — those produce messages
    # that safe_exec correctly pauses on). Both are acceptable. The test
    # would fail if the Travel-prompt itself paused — that's the
    # regression we fixed via DEFAULT_AUTOCONTINUE.
    assert out["status"] in ("complete", "paused")
    if out["status"] == "paused":
        assert "Where do you want to travel to" not in out["message"]
