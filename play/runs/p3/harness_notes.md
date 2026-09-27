# p3 harness notes

## Shift 1

1. #1029-#1339 (D3) SESSILE MONSTERS TREATED AS MOVABLE BLOCKERS: arriving next to a red mold (44,18) by the upstairs, `explore()` returned "blocked: red mold at (44,18) stays next to you" three times (6, 19 and 6 legs, ~40 turns wasted) because its chosen frontier/route kept leading back past the mold; at #1339 `head_to()`/`travel()` printed "travel: waiting a turn for red mold at (44,18) to move" — waiting for an F that never moves. Expected: treat sessile monsters' squares (molds, lichens? no — lichens move) like avoid() squares when planning, never "wait" for them. Workaround that worked: `avoid((44,18))`.
2. #1106-#1150 (D3) explore() missed a frontier under an object pile: the goblin's corpse pile at (39,16) sat on a corridor square whose west neighbours were unseen; explore/frontiers() listed only (44,17)/(34,14) and called (34,14) unreachable. `head_to(34,14)` found the corridor at once.
3. #1628 go_down() "stairs: a hostile is close — not waiting for the pet" — the only hostile near was the sessile yellow mold (48,8) beside the `>`; the pet was left behind (it was also eating). Sessile hostiles shouldn't block the pet wait.
4. #1614 go_down()'s detour (`walk_path`) raised NavError on a trivial jackal instead of auto-fighting it like travel() does.
5. #1066 hunt('goblin') stepped "straight across unexplored dark floor" into rock: "It's solid stone." (no time used) and paused. Maybe only cut across when the squares are known floor, or treat that message as "no route".
6. #243 the obs `objects:` line silently omitted a chest 20 squares away (obs.objects had it, dist 20) — no "... N more" marker for distance-filtered objects. I only noticed it on the full screen dump.
7. #347/#465 `pickup('blindfold')` returned `[]` silently: the dog had moved the blindfold one square. Would be clearer as "nothing matching 'blindfold' here (floor: nothing)".
8. #675 `price_id()` dumped the whole Discoveries (`\`) screen into the `msgs:` line of the output. Also for armor it doesn't filter by slot (a "riding gloves" price lists cloaks/helms/boots too).
9. #202 after `^` + `.` identified the magic trap under me, `bad_squares()` was still empty until the next explore() (it read #terrain then). Fine in practice.
