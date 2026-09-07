"""yn prompts accept only their listed keys and silently drop the rest, so a
scripted loop can burn hundreds of do() calls against "Continue? [ynq] (q)"
with the clock frozen (harness note, Dlvl 16 T=6333: ~640 keys eaten in
one exec). exec must pause the moment a prompt swallows a key, and
continue_exec(reply=...) must let the gamer answer without dropping the
parked code."""

from __future__ import annotations


def test_snapshot_reports_open_prompt(fresh_server):
    server = fresh_server(seed=42)
    assert server._snapshot()["prompt_open"] is None
    snap = server._do("Command.QUIT")  # "Really quit? [yn] (n)"
    assert snap["prompt_open"] == "yn"
    assert "PROMPT OPEN" in server._format_for_text(snap, crop_radius=4)
    server._do("n")
    assert server._snapshot()["prompt_open"] is None


def test_exec_pauses_when_prompt_swallows_key_and_reply_answers_it(fresh_server):
    server = fresh_server(seed=42)
    out = server._safe_exec_python(
        "do('Command.QUIT')\n"          # Really quit? -> pauses (Really rule)
        "do('MiscDirection.WAIT')\n"    # '.' is not y/n: swallowed
        "print('after')\n"
    )
    assert out["status"] == "paused"
    assert "Really quit?" in out["message"]
    t0 = server.STATE.last_obs["blstats"][20]

    out = server._continue_exec()
    assert out["status"] == "paused", out
    assert out["message"].startswith("prompt swallowed 'MiscDirection.WAIT'"), out["message"]
    assert "Really quit?" in out["message"]
    assert "continue_exec(reply=" in out["message"]
    # Still parked at the prompt, clock unchanged, nothing dropped.
    assert server._open_prompt_kind(server.STATE.last_obs) == "yn"
    assert server.STATE.last_obs["blstats"][20] == t0
    assert server.STATE.paused_exec is not None

    out = server._continue_exec(reply="n")
    assert out["status"] == "complete", out
    assert out["stdout"] == "after\n"
    assert server._open_prompt_kind(server.STATE.last_obs) is None
    assert not server.STATE.terminated


def test_valid_answer_in_script_does_not_pause(fresh_server):
    """A script that answers its own prompt keeps flowing (the auto-skip
    path this feature must not regress)."""
    server = fresh_server(seed=5)
    out = server._safe_exec_python(
        "do('Command.ENGRAVE')\n"
        "do('-')\n"
        "do('H'); do('i')\n"
        "do('\\r')\n"
        "print('done')\n"
    )
    assert out["status"] == "complete", out
    assert out["stdout"] == "done\n"
