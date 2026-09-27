"""Kernel handles for tactics. Filled in by play/kernel_boot.py.

Tactics call ctx.do(...) so that, when run inside `nh exec`, every step gets
the kernel's pause-on-event behavior for free.
"""

do = None      # do(keys, *, force=False, quiet=False) -> Snap
look = None    # look() -> Snap
pause = None   # pause(reason)
note = None    # note(text)
game = None    # nh.game.Game
monster_filter = None   # with monster_filter(fn): only newcomers with fn(m) true pause
_set_activity = None    # set_activity(text): shown with any pause while a helper works
hp_rules = None         # with hp_rules(stop_hp): fight-style HP pauses (kernel)
defer_far = None        # with defer_far(6): far newcomers pause only when they come near (kernel)


def activity(text: str = "") -> None:
    """Tell the kernel what the running helper is doing (no-op outside it)."""
    if _set_activity is not None:
        _set_activity(text)


def no_monster_pauses():
    """A block of no-time keystrokes (farlook, inventory, discoveries): a
    monster labelled for the first time there isn't news — no game time
    passes, so nothing moved."""
    import contextlib
    return monster_filter(lambda m: False) if monster_filter is not None else contextlib.nullcontext()


def last():
    """Most recent snapshot (captures one if none yet)."""
    s = game.last
    return s if s is not None else look()


def require_command(what: str):
    """Raise if the game isn't at the command prompt (a helper that starts a
    new command must never type into an open prompt/menu)."""
    s = last()
    if s.state.kind != "command":
        raise RuntimeError(f"{what}: the game is not at the command prompt ({s.state.kind}: "
                           f"{s.state.prompt!r}) — answer or <Esc> it first")
    return s
