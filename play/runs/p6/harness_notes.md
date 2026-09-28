# p6 harness notes (the bug tracker: step numbers, what happened, what you expected)

## Shift 1

1. (#1199, T:737 onward) The obs keeps saying `!! harness code on disk is newer than this daemon's core (src/nh:
   only a daemon restart loads it — tell the orchestrator)`. `bin/nh reload` fixed the helpers part; the core part
   needs a daemon restart, which I was told not to do. Telling the orchestrator here. No visible misbehaviour so far.
2. (#7, T:3) explore() paused on the pet's kill ("The kitten bites the newt. | The newt is killed!"). Pet combat
   lines are routine; I had to add `-a` patterns to every exec/cont. Expected: pet-vs-monster lines (bites/misses/
   kills, "X is killed!" when the pet killed it) don't pause explore()/travel() — only damage to me or the pet dying.
