"""Executed in the kernel namespace at daemon start and on `nh reload`.

Wires tactics to the kernel's do/look/pause and imports the player-facing
helpers so they're available directly inside `nh exec`.
"""

import tactics.ctx as _ctx

_ctx.do = do          # noqa: F821  (provided by the kernel namespace)
_ctx.look = look      # noqa: F821
_ctx.pause = pause    # noqa: F821
_ctx.note = note      # noqa: F821
_ctx.game = game      # noqa: F821

from tactics.nav import (NavError, cursor_to, farlook, go_down, go_up, step,  # noqa: E402,F401
                         travel, travel_to)
from tactics.items import find_item, here, inventory, inventory_text  # noqa: E402,F401
from tactics import mapview  # noqa: E402,F401
from tactics.explore import explore, frontiers  # noqa: E402,F401
from tactics.survival import elbereth, engraving_here, pray, rest, search  # noqa: E402,F401
from tactics import sokoban  # noqa: E402,F401  (sokoban.push(x, y, 'hhk'), sokoban.board())
from tactics.info import corpse, mon, obj, price_candidates, wiki, wiki_page  # noqa: E402,F401
from tactics.nav import kick_door  # noqa: E402,F401
from tactics.explore import object_frontiers, search_until_change  # noqa: E402,F401
from tactics.nav import avoid, bad_squares, walk_path  # noqa: E402,F401
