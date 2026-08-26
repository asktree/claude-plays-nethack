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


# --- Auto-skip on in_yn/in_getlin prompts ----------------------------------

def test_yn_prompt_pauses_when_no_followup(fresh_server):
    """A bare `do('Command.ENGRAVE')` produces a yn-prompt and PARKS NetHack
    there. With our auto-skip on in_yn (allow_all_modes=True so NLE doesn't
    auto-ESC), the safe_exec thread completes silently — the next gamer
    action would be the prompt response."""
    server = fresh_server(seed=5)
    out = server._safe_exec_python("do('Command.ENGRAVE')")
    # Auto-skip suppresses the pause; thread runs to end of body.
    assert out["status"] == "complete"
    # NetHack still parked at the engrave-tool prompt.
    internal = server.STATE.last_obs.get("internal")
    assert internal is not None
    assert int(internal[1]) == 1, "expected in_yn_function=1 (engrave tool prompt)"


def test_engrave_full_sequence_runs_to_completion(fresh_server):
    """Pre-written multi-step engrave: tool '-' (fingers), text 'Hi', then \\r
    to commit. Auto-skip lets the whole sequence run as one block without
    safe_exec round-trips. Verifies the no-pause-on-prompt path end-to-end
    AND that allow_all_modes=True is in effect (otherwise NLE would auto-ESC
    the prompts and the sequence would never reach the writing stage)."""
    server = fresh_server(seed=5)
    out = server._safe_exec_python(
        "do('Command.ENGRAVE')\n"
        "do('-')\n"               # use fingers (engrave in dust)
        "do('H'); do('i')\n"      # text input "Hi"
        "do('\\r')\n"              # commit getlin
    )
    assert out["status"] == "complete"
    # NetHack should have left the prompt; in_yn / in_getlin both clear.
    internal = server.STATE.last_obs.get("internal")
    assert internal is not None
    assert int(internal[1]) == 0
    assert int(internal[2]) == 0
    # The recorded trajectory should include the gamer's actions plus the
    # auto-MORE pump that fires after the "You write in the dust..." message.
    import json
    step_kinds = []
    for line in server.STATE.trajectory_path.open():
        obj = json.loads(line)
        if obj.get("event") == "step":
            step_kinds.append(obj["kind"])
    assert step_kinds.count("gamer") == 5  # ENGRAVE, '-', 'H', 'i', '\r'
    assert step_kinds.count("auto_more") >= 1  # the dust-message --More--


# --- stdout capture --------------------------------------------------------

def test_print_output_surfaced_on_complete(fresh_server):
    """`exec()` is the gamer's primary debugging surface — prints have to come
    back. Regression: was previously swallowed because _create_paused_exec
    didn't redirect stdout."""
    server = fresh_server(seed=42)
    out = server._safe_exec_python("print('hello'); print(42)")
    assert out["status"] == "complete"
    assert out["stdout"] == "hello\n42\n"


def test_print_output_surfaced_on_pause(fresh_server):
    """Stdout from before a pause is delivered with the pause result, not
    held until completion."""
    server = fresh_server(seed=42)
    out = server._safe_exec_python(
        "print('before pickup')\n"
        "do('Command.PICKUP')\n"   # pauses on PICKUP_ON_STAIRS_MSG
        "print('after pickup — never runs unless continued')\n"
    )
    assert out["status"] == "paused"
    assert "before pickup" in out["stdout"]
    assert "after pickup" not in out["stdout"]


def test_print_buffer_clears_between_segments(fresh_server):
    """Each return from _drive_paused flushes the buffer, so the gamer sees
    only the prints from the segment that just ran — not a cumulative
    re-delivery."""
    server = fresh_server(seed=42)
    out = server._safe_exec_python(
        "print('seg1')\n"
        "do('Command.PICKUP')\n"
        "print('seg2')\n"
    )
    assert out["status"] == "paused"
    assert "seg1" in out["stdout"]
    out2 = server._continue_exec()
    assert out2["status"] == "complete"
    # seg1 was already delivered; seg2 prints after the pause resumes.
    assert "seg1" not in out2["stdout"]
    assert "seg2" in out2["stdout"]


def test_format_safe_exec_includes_stdout_block(fresh_server):
    """The text formatter renders captured stdout as `=== stdout ===` —
    that's how the gamer actually sees it in their tool_result."""
    server = fresh_server(seed=42)
    out = server._safe_exec_python("print('visible to gamer')")
    rendered = server._format_safe_exec_result(out)
    assert "=== stdout ===" in rendered
    assert "visible to gamer" in rendered


# --- messages-from-segment tracking ---------------------------------------

def test_messages_collected_across_pause(fresh_server):
    """All messages observed during a segment are returned, in order. The
    `→` marker tags the most-recent one so view.sh can bold it."""
    server = fresh_server(seed=42)
    # ENGRAVE produces "What do you want to write with?" (yn-prompt, auto-skip),
    # then '-' produces another prompt, then 'H'/'i'/\r commit. Each step's
    # snap message gets recorded — even the auto-skipped ones.
    out = server._safe_exec_python(
        "do('Command.ENGRAVE')\n"
        "do('-')\n"               # use fingers
        "do('H'); do('i')\n"      # write "Hi"
        "do('\\r')\n"              # commit
    )
    assert out["status"] == "complete"
    msgs = out.get("messages") or []
    # Multiple prompts/messages fired across the segment.
    assert len(msgs) >= 2, f"expected 2+ messages, got {msgs}"
    # Renderer emits the multi-msg block.
    rendered = server._format_safe_exec_result(out)
    assert "=== messages " in rendered
    assert "→ " in rendered  # latest marker


def test_single_message_no_block(fresh_server):
    """When only one message fires, skip the block — the post_state's
    `msg: ...` line already carries it."""
    server = fresh_server(seed=42)
    out = server._safe_exec_python("do('Command.PICKUP')")
    rendered = server._format_safe_exec_result(out)
    assert "=== messages " not in rendered
    # PICKUP_ON_STAIRS_MSG still surfaces via the paused-result formatting.
    assert PICKUP_ON_STAIRS_MSG in rendered


def test_do_return_value_has_grids(fresh_server):
    """`result = do(...)` inside exec must return a complete snapshot —
    chars/glyphs/etc. — not a slim one. Otherwise gamer code breaks
    surprisingly when it tries result['chars'] vs the obs global."""
    server = fresh_server(seed=42)
    out = server._safe_exec_python(
        "result = do('Command.LOOK')\n"
        "assert 'chars' in result, list(result.keys())\n"
        "assert 'glyphs' in result\n"
        "assert 'descriptions' in result\n"
    )
    assert out["status"] in ("complete", "paused"), out


def test_kernel_obs_refreshed_after_do_inside_safe_exec(fresh_server):
    """`obs` global inside safe_exec must update after each do() — same
    behavior as _exec_python's non-pausing kernel. Previously stale.

    Uses seed=5 (clean spawn, no visible hostiles) + Command.SEARCH so the
    step is silent (no synth message fires) and the assertion line gets
    a chance to run.
    """
    server = fresh_server(seed=5)
    out = server._safe_exec_python(
        "before = obs['blstats']['time']\n"
        "do('Command.SEARCH')\n"
        "after = obs['blstats']['time']\n"
        "assert after >= before, f'obs stale: {before} -> {after}'\n"
    )
    assert out["status"] == "complete", out


def test_messages_buffer_clears_between_segments(fresh_server):
    """Per-segment isolation: the messages list is flushed each return so
    a continue_exec sees only post-pause messages."""
    server = fresh_server(seed=42)
    out = server._safe_exec_python("do('Command.PICKUP')")
    assert out["status"] == "paused"
    msgs1 = out.get("messages") or []
    out2 = server._continue_exec()
    msgs2 = out2.get("messages") or []
    # The PICKUP message is in segment 1, not segment 2.
    assert any(PICKUP_ON_STAIRS_MSG in m for m in msgs1)
    assert not any(PICKUP_ON_STAIRS_MSG in m for m in msgs2)


def test_autocontinue_rejects_monster_arrival_pattern(fresh_server):
    """A bare `^You see` also matches "You see <monster> come into view" —
    the only warning before a fast monster is adjacent. Must be refused
    before any game state is touched."""
    import pytest

    server = fresh_server(seed=42)
    with pytest.raises(ValueError, match="come into view"):
        server._safe_exec_python("do('Command.PICKUP')\n", autocontinue=[r"^You see"])
    # Narrower item-only pattern is fine.
    out = server._safe_exec_python(
        "do('Command.PICKUP')\n", autocontinue=[r"^You see here"]
    )
    assert out["status"] == "paused"


def test_autocontinue_rejection_keeps_paused_exec(fresh_server):
    server = fresh_server(seed=42)
    out1 = server._safe_exec_python("do('Command.PICKUP')\ndo('Command.LOOK')\n")
    assert out1["status"] == "paused"
    import pytest

    with pytest.raises(ValueError):
        server._safe_exec_python("print(1)", autocontinue=[r"come into view"])
    # The original exec is still parked and resumable.
    out2 = server._continue_exec()
    assert out2["status"] == "paused"
    assert out2["message"] == LOOK_ON_STAIRS_MSG
