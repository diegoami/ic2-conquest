# AI fleet phase, original vs remake main: the branch rule matches; one fleet's route and moves state differs

**Tag:** [confirmed, partial]. The original's own hook was compared with remake main on the same states (150 fleet
decisions). The 26 differences are not attributed yet (see "Open").
**Task:** conquest #174 (strategic fidelity: fleet hunt, port and stored-destination decisions), owner request
2026-10-31.
**Remake compared:** main `05b02936` (T247 ported the original fleet phase), not released.
**Method:** the same as the army, diplomacy and economy comparisons (`2026-10-30-ai-decisions-vs-remake-main.md` and
following).

## Method

- **Original:** `patches/fleetphase_hook.py`, an observation-only build with two probes in the fleet phase
  `FUN_0044f608`. Together they log, per own launched fleet:
  - 0x44F65B: the port pick (`FUN_0044e9a8`), the stored route, the position and the moves;
  - 0x44F682: `FUN_0044f4f8`'s hunt score and target.

  The branch follows from F608's own tests: route_x ≥ 0 → stored route; otherwise, with moves > 0, a hunt score
  > 100 → hunt; otherwise a port → port; otherwise nothing.
  - Runs: 16 New Game starts × 5 End turns, seed 12345. The hooked autosaves are **byte-identical to the plain build in
    80 of 80 turns**, and the same files as the army, diplomacy and economy runs.
- **Remake:** the same rounds from those autosaves; its `fleet phase: fleet-N BRANCH, support S, hunt H` lines (the
  diplomacy run's logs).
- **Comparison** (`runs/experiments/fleetphase/compare.py`): per round, nation and fleet, the branch and the hunt score.

## Result: 150 fleet decisions

| | Decisions |
|---|---|
| **same** (branch, and the hunt score where the original computed one) | **124**: 87 port, 37 stored route |
| differs | 26 |

- **No fleet hunted in either game:** every hunt score was −10000 (no candidate). So the hunt branch and its score-100
  boundary were not exercised by these starts.
- **All 26 differences are one fleet, Carthage's fleet 0, in rounds 2–5.** It is the fleet that sails (49,62) → (74,71)
  in round 1 through a D174 waypoint (`2026-10-30-fleet-move-contract131.md`). Three patterns:

  | Pattern | Rows | Original | Remake main |
  |---|---|---|---|
  | route gone in the original | 9 | no stored route (route_x −1) → **port** (city 46 from (74,71), in round 2 of 7 starts) | **stored-route** |
  | route kept in the original | 9 | **stored route** (e.g. (85,78), also once the fleet stands on it) | **port** |
  | no moves in the original | 8 | **moves 0** at its turn → nothing | **port** |

  The round-start saves show fleet 0 with moves 26 in S00 r2 and S03 r3. Yet in S03 r3 the original's decision sees
  moves 0, so its moves changed earlier in that round, before its fleet phase.

**So the branch rule itself agrees wherever both games see the same route and moves.** What differs is that one fleet's
route and moves state at its turn. That is the route lifetime of research #131:
- the route is present iff route_x ≥ 0;
- writers: D9A8/DBA8 through CD08, and the round tick (0x451723) setting x = −1;
- a fleet's moves can also be spent by an army transport (the CD08 landing request charges moves).

## Open (not attributed)

Which writer differs: the round tick's clear, the arrival, the army phase's transport request (D9A8, T247's "same-turn
transport routes"), or the import of route_y/route_x from the save (the saver writes them; `state/sav.py` does not decode
fleet +4/+6).

The next step is a route/moves hook at those writers on the 26 rounds, plus a decode of fleet +4/+6 in the round-start
saves. Not done here: the owner wound the session down after this comparison.

## What this does not establish

- **The hunt branch:** no fleet had a hunt candidate in these starts.
- **The port choice itself:** the remake logs the branch, not the port city.
- **Rounds 6+, other seeds, fleets carrying armies.**

## Evidence

- Data: `runs/experiments/data/run-exp-fleetphase/`:
  - `orig-v1/`: hook logs and inert checks;
  - `report-v1.json`;
  - `smoke/`.
- Release `run-exp-fleetphase` (`fleetphase-saves.tar.xz`; hashes in `SAVES.sha256`).
- Saves cited: starts `S00_Rome_AUTO0720.SAV` … `S15_thracia_AUTO0720.SAV`; the round starts are `hooked-tNN-*.SAV`
  (S00 r2 and S03 r3 above).
- Code:
  - `patches/fleetphase_hook.py`, `difftest/probes/fleetphase_hook_run.py`;
  - `runs/experiments/fleetphase/compare.py`.
