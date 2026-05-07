"""Tests for the safe-by-default exec system.

NetHack's role/race randomization is NOT bound to NETHACK_SEED (the
Challenge env disables `set_initial_seeds`), so spawn details vary
across test runs even at a fixed seed. What's reliably stable:
  - `Command.PICKUP` at spawn ALWAYS produces a non-empty message
    (either "stairs solidly fixed", or a pickup confirmation if the
    role spawned on items, or "nothing here").
  - `Command.LOOK` at spawn ALWAYS produces a non-empty message
    (describes the cell — staircase, fountain, item, etc.).

We assert the *pause behavior*, not the specific message text, so the
suite stays deterministic regardless of which role spawns.
"""

from __future__ import annotations


def test_pure_python_completes(fresh_server):
    """No do() calls → no possibility of pause; completes immediately."""
    server = fresh_server(seed=42)
    out = server._safe_exec_python("x = sum(range(100)); print(x)")
    assert out["status"] == "complete"


def test_message_pauses(fresh_server):
    server = fresh_server(seed=42)
    out = server._safe_exec_python("do('Command.PICKUP')")
    assert out["status"] == "paused"
    assert out["message"]  # non-empty


def test_pause_stack_includes_gamer_line(fresh_server):
    server = fresh_server(seed=42)
    out = server._safe_exec_python(
        "x = 1\n"
        "do('Command.PICKUP')\n"   # ← line 2; pauses here
        "x = 2\n"
    )
    assert out["status"] == "paused"
    stack = out["stack"]
    assert any(f["file"] == "<safe_exec>" and f["line"] == 2 for f in stack), \
        f"expected line 2 in stack, got: {stack}"
    safe_exec_frame = next(f for f in stack if f["file"] == "<safe_exec>")
    assert "do('Command.PICKUP')" in safe_exec_frame["code"]


def test_pause_then_continue_resumes(fresh_server):
    server = fresh_server(seed=42)
    out = server._safe_exec_python(
        "do('Command.PICKUP')\n"
        "x = 42\n"   # silent — no do
    )
    assert out["status"] == "paused"
    out2 = server._continue_exec()
    assert out2["status"] == "complete"
    assert server._KERNEL.get("x") == 42


def test_consecutive_messages_pause_each_time(fresh_server):
    server = fresh_server(seed=42)
    # LOOK + PICKUP at spawn: both reliably produce non-empty messages.
    out1 = server._safe_exec_python(
        "do('Command.LOOK')\n"
        "do('Command.PICKUP')\n"
    )
    assert out1["status"] == "paused"
    assert out1["message"]

    out2 = server._continue_exec()
    assert out2["status"] == "paused"
    assert out2["message"]

    out3 = server._continue_exec()
    assert out3["status"] == "complete"


def test_continue_exec_errors_when_nothing_paused(fresh_server):
    server = fresh_server(seed=42)
    out = server._continue_exec()
    assert out["status"] == "error"
    assert "no execution paused" in out["error"]


def test_autocontinue_match_all_skips_message(fresh_server):
    """`r'.+'` matches any non-empty message → all pauses suppressed."""
    server = fresh_server(seed=42)
    out = server._safe_exec_python(
        "do('Command.PICKUP')\n",
        autocontinue=[r".+"],
    )
    assert out["status"] == "complete"


def test_autocontinue_does_not_skip_non_matching(fresh_server):
    server = fresh_server(seed=42)
    # Pattern that won't match real NetHack messages from PICKUP.
    out = server._safe_exec_python(
        "do('Command.PICKUP')\n",
        autocontinue=[r"^XYZ_NEVER_MATCHES_"],
    )
    assert out["status"] == "paused"


def test_continue_exec_replaces_autocontinue_list(fresh_server):
    server = fresh_server(seed=42)
    out1 = server._safe_exec_python(
        "do('Command.PICKUP')\n"
        "do('Command.LOOK')\n",
        autocontinue=[r"^XYZ_NEVER_MATCHES_"],
    )
    assert out1["status"] == "paused"

    # Continue with a wider list that matches everything.
    out2 = server._continue_exec(autocontinue=[r".+"])
    assert out2["status"] == "complete"


def test_drop_on_other_tool_clears_paused_slot(fresh_server):
    server = fresh_server(seed=42)
    out = server._safe_exec_python(
        "do('Command.PICKUP')\n"
        "x = 1\n"
    )
    assert out["status"] == "paused"
    assert server.STATE.paused_exec is not None

    server._drop_paused()
    assert server.STATE.paused_exec is None

    out2 = server._continue_exec()
    assert out2["status"] == "error"


def test_drop_paused_via_do_call(fresh_server):
    server = fresh_server(seed=42)
    server._safe_exec_python(
        "do('Command.PICKUP')\n"
        "x = 1\n"
    )
    assert server.STATE.paused_exec is not None
    server._drop_paused()
    server._do("Command.LOOK")  # any subsequent tool call
    assert server.STATE.paused_exec is None


def test_exec_raw_does_not_pause_on_messages(fresh_server):
    server = fresh_server(seed=42)
    out = server._exec_python("do('Command.PICKUP'); do('Command.LOOK')")
    assert out["error"] is None
    do_events = [s for s in out["steps"] if s.get("event") == "do"]
    assert len(do_events) == 2


def test_starting_new_safe_exec_drops_previous(fresh_server):
    server = fresh_server(seed=42)
    out1 = server._safe_exec_python("do('Command.PICKUP')")
    assert out1["status"] == "paused"
    pe1 = server.STATE.paused_exec

    # Pure python — no do() to potentially pause.
    out2 = server._safe_exec_python("x = 1")
    assert out2["status"] == "complete"
    assert server.STATE.paused_exec is not pe1


def test_kernel_state_persists_across_safe_exec_calls(fresh_server):
    server = fresh_server(seed=42)
    server._safe_exec_python("my_var = 42")
    out = server._safe_exec_python("y = my_var * 2")
    assert out["status"] == "complete"
    assert server._KERNEL.get("y") == 84


def test_paused_thread_cleaned_up_after_drop(fresh_server):
    server = fresh_server(seed=42)
    out = server._safe_exec_python("do('Command.PICKUP'); x = 1")
    assert out["status"] == "paused"
    pe = server.STATE.paused_exec
    assert pe is not None and pe.thread.is_alive()
    server._drop_paused()
    assert server.STATE.paused_exec is None
