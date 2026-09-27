# p2 lessons

- Before ANY directional action (kick, throw, zap, F-fight), re-check the target square's occupant in the same step: pets wander onto boxes/items between turns. Never let a script run a directional action in a loop with only a "hostiles nearby" check.
- Never call helpers that send keys (`inventory()`, `here()`) unless `obs.kind == 'command'`; they can type into an open prompt.
- Shops: `m`-steps give no "You see here" line; read `obs.messages` right after `do()` (before `look()`); sell-offer price ID works (drop, decline with `n`, `,` to take back — mind piles that open a menu).
- NetHack travel (`_`) routes through closed doors and pushable boulders and then stops; use waypoints, or clear the obstacle (kick door open, push boulder to a dead end) on levels you will cross often.
