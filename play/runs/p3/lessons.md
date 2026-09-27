# p3 lessons

- #force a locked chest with the +0 dagger, never the long sword: lock.c breaks a blade ~0.7%/turn (rn2(1000-spe) > 992) and succeeds 2*oc_wldam %/turn (dagger 6%, long sword 24%). `x` to swap, `#force` + `y`, `x` back. Took 8 turns at T:191.
- A sessile mold beside stairs/doorways confuses explore()/travel() (they wait for it to "move" or keep returning next to it): `avoid((x, y))` its square as soon as you see it, and step around it by hand (doorless doorways allow diagonal steps).
- "You smell charred flesh" (or other odd flavor lines) with no cause = you stepped on a MAGIC TRAP (trap.c domagictrap); `^` then `.` names the trap under you. Magic traps can also summon monsters: avoid the square.
- Pets move items around: farlook the item again before a pickup trip (the blindfold moved 1 square); items a pet carried are not cursed.
- A hostile little dog (speed 18) bites twice a turn: 9 HP in one round at XL3/AC5. Treat fast d's as "normal", not trivial, below XL5.
- Explore dead-end problem: a level whose half is blank (D3 east) hides a corridor; searching one doorway/dead end 12-15 turns may not be enough — note it and move on, come back later.
