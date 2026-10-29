# The original's AI fleet move in play: route waypoints, the no-progress swing, and fleets that burn their moves next to a land target

**Tag:** [confirmed] in play. The seed build ran under Wine with an observation-only hook in `FUN_0044e1fc`. The hooked
autosaves are byte-identical to the plain build's in all 12 End turns.
**Task:** imperial_conquest_2#1409 (faithful fleet decisions and destination execution), delegated by research on 2026-10-30.
It also closes the leftover of research #42 ("the route-finder branch reads runtime sea-route tables, so the Unicorn maps
cannot run it").
**Background:** `2026-10-24-fleet-accepted-movement174.md`, `2026-10-30-paths-in-play-and-fleet-walks42.md`,
`2026-10-29-ai-fleet-hunt-absent-in-remake233.md`, `2026-10-30-ai-move-fallback-point105.md` (the CEC8 contract).

## Answer

`FUN_0044e1fc(fleet, target)` is the fleet twin of the army wrapper (disassembly in `patches/fleet_hook.py`):

1. **The direct-line test, then a walk.**
   - If CB40 passes, the fleet walks (`FUN_0044e094`) straight toward the target.
   - Otherwise it walks toward `FUN_0044d174(group 0, fleet, target)`. Before that, a target on a land, city or army cell
     (codes 2–247) is first replaced through `FUN_0044939c`. D174's group 0 is waypoints 1–25.
2. **No progress: the fallback.** If the moves are unchanged and positive, and the point word is ≥ 0, it calls CEC8 on the
   fleet's cell, walks there, and subtracts 1 move.
3. **Recursion** while the distance is > 1, moves remain, the point word is ≥ 0 and the target x is ≥ 0.
4. **Then the arrival part** at distance 1 (sea step, landing, city or fleet contact), not logged here.

**In play** (3 starts × 4 AI End turns, seed 12345; 138 records; 18 top-level AI fleet moves, 43 levels including recursion):

| Measure | Count |
|---|---:|
| levels with the direct line | 29 |
| levels through D174 | 14: **13 return a route-table waypoint** (ids 5, 6, 7, 9, 22 of the remake's `ClassicalArmyNavigation` points, all in group 0's range 1–25); **1** returns (108,60), which is `CEC8(fleet cell)`, D174's origin-local fallback |
| D174 returned none | 0 |
| no-progress fallbacks (CEC8) | 13, all with a point (none returned none) |
| top-level calls that recursed | 16 of 18; maximum depth 2 |

**The behaviour that matters: a fleet next to a land target oscillates.** Every fallback in play came from a fleet already
at distance 1 from its target, a land cell it cannot enter:

- **The direct walk cannot step,** so CEC8 sends the fleet three cells out and the recursion brings it back next to the
  target.
- **Carthage's fleet 0** at (110,63) → (113,60) → (110,62) spends 7 moves (26 → 19). At (105,63) beside (104,64) it
  returns to the **same cell**, spending 7 moves twice per turn (26 → 19 → 12).
- **Nation 3's fleet 1** at (189,93) beside (190,94), in every one of 8 turns over both starts:
  1. CEC8 → (192,93) or (193,93);
  2. from there the line is blocked, so D174 → waypoint 22 (182,85);
  3. back on the direct line → (189,93).

  It ends **where it began, with 22 or 23 of its 28 moves spent**.

The fleets do still reach the arrival part with moves left (6 and 19 in those rows). The swing costs moves, not the contact.

**The fleet-phase flag never mattered here.** CEC8's sea tolerance (`DAT_004a0340 = 1`, #105) changes the result only for a
land origin. E1FC's own CEC8 is always called on the fleet's sea cell, and the one D174 fallback in play was origin-local, on
a sea cell. A **land target's** local fallback inside D174 (target-local) would use the tolerance; it did not occur in these
turns.

**The remake (v0.8.4)** has no AI fleet routing at all (`2026-10-29-ai-fleet-hunt-absent-in-remake233.md`). For #1409 the
contract is the sequence above: group-0 waypoints, the CEC8 swing with its −1 move, recursion, then arrival. The oscillation
next to a land target is the original's behaviour; reproducing it is a decision for the main project.

## What this does not establish

- **The arrival part** after the walk (landing, siege, fleet attack) is not logged; the counts above stop at "after moves".
- **D174's internals** in play (the visible list, D010 route rows) beyond the returned point; which waypoint it *should* pick
  was not recomputed against the remake's `Intermediate` with group 0.
- **The FUN_0044939c target replacement** for land targets (its output is not logged; the target word logged is the one the
  wrapper was called with).
- **Wider play:** 3 starts and 4 turns. `fleets-adjacent-at-sea-0723.SAV` (both seats human) gave no AI fleet call.

## Evidence

- Hook: `patches/fleet_hook.py`. Five probes in E1FC: the CB40 result, D174's point, CEC8's point, the recursion, and the
  position and moves after the walk. Each stub saves and restores every register and the flags. Runner:
  `difftest/probes/fleet_hook_run.py`; analysis: `runs/experiments/fleethook1409/analyze.py`.
- Data: `runs/experiments/data/run-exp-fleethook1409/`:
  - `*-fleet.jsonl`: the records;
  - `summary-v1.json`: every call, level by level;
  - `<start>/inert.json`: hooked vs plain autosave hashes, identical in 12 of 12 turns;
  - `SAVES.sha256`.
- Saves (run `run-exp-fleethook1409`, artifacts): `hooked-t01-AUTO0735.SAV` … `hooked-t04-AUTO0738.SAV` and the `plain-*`
  twins for `fleet-port-antium-0734`; `hooked-t01-AUTO0721.SAV` … `t04-AUTO0724.SAV` for BASE; and the same for
  `fleets-adjacent-at-sea-0723`. The release upload is pending the player (see the PR).
- Starts: `saves/fleet-port-antium-0734.SAV`, `saves/fleets-adjacent-at-sea-0723.SAV`, and the fixture BASE.SAV; startup seed
  12345.
