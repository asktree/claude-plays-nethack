# live — harness notes (bug tracker for the live game)

- setup: `scripts/nh-connect.sh` lacked the executable bit -> `start-remote` died with 'permission denied' (fixed, committed).
- setup: lobby username/password/email prompts parsed as `unknown`, so each keystroke waited the full recheck budget
  (30-70 s per step); `register()` then timed out at 30 s although registration had succeeded. Fixed: any screen with the
  Hardfought banner is `dgl`; register() waits 120 s. Registration on Hardfought returns to the logged-out-looking screen
  briefly, then shows the logged-in lobby.
- the virus editor screen parses as `[extcmd]` (lines starting with `#`): use `exec --at-prompt` for vi_replace_buffer().
- shift 1b #~240: hunt('newt') printed "fight: the newt at (37,5) is gone — NOT killed" and then returned
  {'reason': 'killed', 'kills': ['newt']} — contradictory; unclear whether the newt died.
- shift 1b: dead_ends() returned [] on DL1 while standing at an obvious corridor dead end (58,13) (a spur off the start
  room's east doorway). Harmless, but the explore verdict then didn't list it.
