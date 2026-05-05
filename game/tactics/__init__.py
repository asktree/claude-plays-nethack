"""Tactics: side-effecting procedures the gamer can call inside game.exec().

Contrast with views/ (read-only) — tactics actually take game actions, often
sequencing many do() calls behind one function. They abstract common
multi-step idioms so the gamer doesn't reinvent them in scratch loops.

Imported flat: `from tactics import travel_to`.
"""

from .travel_to import travel_to

__all__ = ["travel_to"]
