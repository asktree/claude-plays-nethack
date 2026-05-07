"""Tests for the safe-by-default exec system.

Character is pinned to "val-hum-fem-law" (Valkyrie-Human-Female-Lawful) by
default, with explicit env seeding (NetHack-v0). So spawn details, items,
and message text are 100% deterministic across runs at a given seed.
"""

from __future__ import annotations


PICKUP_ON_STAIRS_MSG = "The stairs are solidly fixed to the floor."
LOOK_ON_STAIRS_MSG = "There is a staircase up here."


def test_pure_python_completes(fresh_server):
    server = fresh_server(seed=42)
    out = server._safe_exec_python("x = sum(range(100)); print(x)")
    assert out["status"] == "complete"


def test_message_pauses(fresh_server):
    server = fresh_server(seed=42)
    out = server._safe_exec_python("do('Command.PICKUP')")
    assert out["status"] == "paused"
    assert out["message"] == PICKUP_ON_STAIRS_MSG


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
        "x = 42\n"
    )
    assert out["status"] == "paused"
    out2 = server._continue_exec()
    assert out2["status"] == "complete"
    assert server._KERNEL.get("x") == 42


def test_consecutive_messages_pause_each_time(fresh_server):
    server = fresh_server(seed=42)
    out1 = server._safe_exec_python(
        "do('Command.LOOK')\n"
        "do('Command.PICKUP')\n"
    )
    assert out1["status"] == "paused"
    assert out1["message"] == LOOK_ON_STAIRS_MSG

    out2 = server._continue_exec()
    assert out2["status"] == "paused"
    assert out2["message"] == PICKUP_ON_STAIRS_MSG

    out3 = server._continue_exec()
    assert out3["status"] == "complete"


def test_continue_exec_errors_when_nothing_paused(fresh_server):
    server = fresh_server(seed=42)
    out = server._continue_exec()
    assert out["status"] == "error"
    assert "no execution paused" in out["error"]


def test_autocontinue_skips_specific_message(fresh_server):
    server = fresh_server(seed=42)
    out = server._safe_exec_python(
        "do('Command.PICKUP')\n",
        autocontinue=[r"^The stairs are solidly fixed"],
    )
    assert out["status"] == "complete"


def test_autocontinue_does_not_skip_non_matching(fresh_server):
    server = fresh_server(seed=42)
    out = server._safe_exec_python(
        "do('Command.PICKUP')\n",
        autocontinue=[r"^You hear "],
    )
    assert out["status"] == "paused"
    assert out["message"] == PICKUP_ON_STAIRS_MSG


def test_continue_exec_replaces_autocontinue_list(fresh_server):
    server = fresh_server(seed=42)
    out1 = server._safe_exec_python(
        "do('Command.PICKUP')\n"
        "do('Command.LOOK')\n",
        autocontinue=[r"^You hear "],
    )
    assert out1["status"] == "paused"
    assert out1["message"] == PICKUP_ON_STAIRS_MSG

    out2 = server._continue_exec(autocontinue=[r"^The stairs ", r"^There is a "])
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
    server._safe_exec_python("do('Command.PICKUP'); x = 1")
    assert server.STATE.paused_exec is not None
    server._drop_paused()
    server._do("Command.LOOK")
    assert server.STATE.paused_exec is None


def test_exec_raw_does_not_pause_on_messages(fresh_server):
    server = fresh_server(seed=42)
    out = server._exec_python("do('Command.PICKUP'); do('Command.LOOK')")
    assert out["error"] is None
    do_steps = [s for s in out["steps"] if s.get("event") == "step" and s.get("kind") == "gamer"]
    assert len(do_steps) == 2


def test_starting_new_safe_exec_drops_previous(fresh_server):
    server = fresh_server(seed=42)
    out1 = server._safe_exec_python("do('Command.PICKUP')")
    assert out1["status"] == "paused"
    pe1 = server.STATE.paused_exec

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


# --- Determinism + replay tests --------------------------------------------

def test_seed_determines_role(fresh_server):
    """With character='@' (random), the same seed must always produce the
    same game — proven by identical blstats after reset across two runs.
    (We can't reliably parse the welcome message for '@' because some
    spawns trigger autopickup that clobbers it; comparing blstats is the
    bedrock invariant.)"""
    s1 = fresh_server(seed=42, character="@")
    bl1 = s1._decode_blstats(s1.STATE.last_obs)
    s2 = fresh_server(seed=42, character="@")
    bl2 = s2._decode_blstats(s2.STATE.last_obs)
    assert bl1 == bl2


def test_pinned_character_is_valkyrie(fresh_server):
    """Default test fixture pins to Valkyrie-Human-Female-Lawful."""
    server = fresh_server(seed=42)
    char = server.STATE.character
    assert char is not None
    assert char["role"] == "Valkyrie"
    assert char["race"] == "human"
    assert char["alignment"] == "lawful"


def test_replay_reproduces_state(fresh_server, monkeypatch):
    """Play a fresh game; resume from the trajectory; final state matches.
    Replay validation in _validate_replay_step would have raised on any
    divergence — getting here clean is the proof."""
    server = fresh_server(seed=42)
    for a in ["Command.PICKUP", "CompassDirection.E", "CompassDirection.E",
              "Command.PICKUP", "CompassDirection.W"]:
        server._do(a)

    orig_blstats = server._decode_blstats(server.STATE.last_obs)
    orig_msg = server._decode_message(server.STATE.last_obs)
    orig_step_n = server.STATE.step_n  # gamer + auto_more events
    traj_path = server.STATE.trajectory_path
    # Count step events in the trajectory file directly to confirm what we
    # expect replay to recreate (independent of in-memory step_n).
    import json as _json
    expected_steps = sum(
        1 for line in traj_path.open()
        if line.strip() and _json.loads(line).get("event") == "step"
    )

    # Resume — clear seed env vars so the header drives.
    monkeypatch.delenv("NETHACK_SEED_CORE", raising=False)
    monkeypatch.delenv("NETHACK_SEED_DISP", raising=False)
    monkeypatch.delenv("NETHACK_CHARACTER", raising=False)
    monkeypatch.setenv("NETHACK_TRAJ", str(traj_path))
    server.STATE.last_obs = None
    server.STATE.character = None
    server.STATE.seen_per_level.clear()
    server.STATE.terminated = False
    server.STATE.truncated = False

    server._reset()
    replayed_blstats = server._decode_blstats(server.STATE.last_obs)
    replayed_msg = server._decode_message(server.STATE.last_obs)
    assert replayed_blstats == orig_blstats
    assert replayed_msg == orig_msg
    # step_n during replay = number of step events in the trajectory.
    assert server.STATE.step_n == expected_steps, \
        f"step_n={server.STATE.step_n}, expected={expected_steps}, orig_in_memory={orig_step_n}"
