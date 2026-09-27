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
_ctx.game_name = GAME_NAME  # noqa: F821

from tactics.nav import (NavError, cursor_to, farlook, go_down, go_up, step,  # noqa: E402,F401
                         travel, travel_to)
from tactics.items import dip, engrave_test, find_item, here, inventory, inventory_text  # noqa: E402,F401
from tactics import mapview  # noqa: E402,F401
from tactics.explore import explore, frontiers  # noqa: E402,F401
from tactics.survival import (elbereth, engraving_here, pray, prayer_check, rest,  # noqa: E402,F401
                              rest_on_elbereth, search)
from tactics import sokoban  # noqa: E402,F401  (sokoban.push(x, y, 'hhk'), sokoban.board())
from tactics.info import (corpse, last_seen, mon, obj, price_candidates, price_id, threat,  # noqa: E402,F401
                          wiki, wiki_page)
from tactics.nav import kick_door  # noqa: E402,F401
from tactics.explore import object_frontiers, search_until_change  # noqa: E402,F401
from tactics.nav import avoid, bad_squares, blockers, path_to, walk_path  # noqa: E402,F401
from tactics.combat import fight, throw, zap  # noqa: E402,F401
from tactics import options  # noqa: E402,F401  (options.bool_options(), options.set_bool('timed_delay', False))
from tactics.town import buy_protection  # noqa: E402,F401
