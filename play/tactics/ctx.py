"""Kernel handles for tactics. Filled in by play/kernel_boot.py.

Tactics call ctx.do(...) so that, when run inside `nh exec`, every step gets
the kernel's pause-on-event behavior for free.
"""

do = None      # do(keys, *, force=False, quiet=False) -> Snap
look = None    # look() -> Snap
pause = None   # pause(reason)
note = None    # note(text)
game = None    # nh.game.Game


def last():
    """Most recent snapshot (captures one if none yet)."""
    s = game.last
    return s if s is not None else look()
