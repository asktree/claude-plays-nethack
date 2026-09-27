# p2 lessons

- Before ANY directional action (kick, throw, zap, F-fight), re-check the target square's occupant in the same step: pets wander onto boxes/items between turns. Never let a script run a directional action in a loop with only a "hostiles nearby" check.
- Never call helpers that send keys (`inventory()`, `here()`) unless `obs.kind == 'command'`; they can type into an open prompt.
- Shops: `m`-steps give no "You see here" line; read `obs.messages` right after `do()` (before `look()`); sell-offer price ID works (drop, decline with `n`, `,` to take back — mind piles that open a menu).
- NetHack travel (`_`) routes through closed doors and pushable boulders and then stops; use waypoints, or clear the obstacle (kick door open, push boulder to a dead end) on levels you will cross often.
- Sell-offer price ID (drop / decline / pick up) DESTROYS a scroll of scare monster that was already picked up once ("turns to dust"). Never drop-probe an unknown scroll that was picked up from the floor unless its group can't be scare monster (base 100 group can). Lost one on D4 T:1662.
- `travel()` never autopicks up (NetHack sets nopick for the travel command): after travelling to gold or a thrown dagger, press `,` or take the last step with a plain move.
- Inside a tended shop you can never swap places with your pet ("You stop. Your kitten is in the way!"); wait a turn instead of retrying. Outside shops a swap fails 1 in 7.
- Item piles in rooms can hide undiscovered traps (D3 "food pile" = sleeping gas trap; slept ~20 turns). Prefer walking to piles only when the level is quiet; consider searching/`^` when a lone item sits in an odd spot.
- Locked chests: kick from an adjacent square ("THUD!" = no luck, 1 in 5 breaks the lock); re-check the chest square for the pet before every kick. `#loot` → `o` → "All types" → item menu (filter out corpses: no gloves = never touch a cockatrice corpse).
- Yellow molds: two thrown daggers kill most of them; one sword blow to finish is acceptable (passive = short stun only if it survives). The kitten steals kills — fight things myself when XP matters, keep the kitten behind me in corridors.
- Werejackals (D3–D4 at XL3): throw a dagger while they approach, then melee; check `history` afterwards for "You feel feverish" (fight() folds earlier rounds' messages). Prayer (major trouble) is the cure; verify `prayer_check()` first.
