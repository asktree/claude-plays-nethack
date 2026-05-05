"""Views: pure read-only functions that re-render the latest observation.

Imported inside `game.exec()`'d code, e.g.:

    from views import crop
    print(crop(obs, radius=4))

Conventions:
- Each view takes `obs` (the snapshot dict from observe()/do()) as its first arg.
- Views are pure: no side effects, no game.do() calls. Tactics handle that.
- Views return strings or simple data structures, not rich objects.
"""

from .crop import crop
from .likely_secret_doors import likely_secret_doors
from .unexplored import unexplored

__all__ = ["crop", "likely_secret_doors", "unexplored"]
