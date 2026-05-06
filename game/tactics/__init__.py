"""Tactics: side-effecting procedures the gamer can call inside game.exec().

Contrast with views/ (read-only) — tactics actually take game actions, often
sequencing many do() calls behind one function. They abstract common
multi-step idioms so the gamer doesn't reinvent them in scratch loops.

Imported flat: `from tactics import travel_to`.
"""

from .auto_explore import auto_explore
from .look_at import look_at, look_at_nearest
from .safe_do import Interrupted, safe_do
from .travel_to import travel_to, travel_to_nearest

__all__ = [
    "Interrupted", "auto_explore", "look_at", "look_at_nearest",
    "safe_do", "travel_to", "travel_to_nearest",
]
