# The AI army move's no-progress fallback (FUN_0044cec8), and CB40/DB38 against the remake's ClassicalArmyNavigation

**Tag:** [confirmed] in emulation of the pinned unpatched EXE (`9d753d5d…`): the routines run unchanged in Unicorn on real
SAV grids and on the #187 live-RAM snapshot. No game run; nothing here is observed in play.
**Task:** research [#105](https://github.com/diegoami/imperial-conquest-2-research/issues/105) (for imperial_conquest_2#1592),
delegated to conquest on 2026-10-30. Remake compared: v0.8.4 (`d9cc71b`), `src/IC2.Engine/Ai/ClassicalArmyNavigation.cs`.

## Answer

1. **`FUN_0044cec8(P, &out)`: "three steps on the same medium, last direction wins."** It sets `out.x = -1`, then tries the
   eight directions `(dx, dy)` in the order dx = −1, 0, 1 (outer loop) and dy = −1, 0, 1 (inner loop), skipping (0, 0). A
   direction succeeds when each of its three cells `clamp(P + s·(dx, dy))` (s = 1, 2, 3; x clamped to 0–319, y to 0–139) has
   the same medium as P. The medium is sea when the grid code is < 2 or > 299 (so fleet markers count as sea) and land
   otherwise (terrain, city and army markers). On success `out = P + 3·(dx, dy)` (clamped), overwriting any earlier success,
   so the **last** successful direction in that order wins. **None** (`out.x = −1`) only when all eight fail. It reads no
   terrain cost, no unit and no random number (dump :51124–51196).
   - **One extra input: `DAT_004a0340`.** A probe cell of another medium is tolerated when that cell is sea and the flag is 1
     (`(flag & cellIsSea) == 0` → fail). The flag is set to **0 at the top of the army phase** (`FUN_0044f31c`, :52917) and
     to **1 at the top of the fleet phase** (`FUN_0044f608`, :53040). Every army move (`FUN_0044dba8`; all its call sites, :52418–52959, are in
     F31C or in helpers called only from F31C) runs inside the army phase (`FUN_0044fa20` calls F31C then F608, :53219–53220). **For armies the flag is
     always 0.** It is 1 for the fleet wrapper `FUN_0044e1fc` (relevant to #1409, not here).
2. **The wrapper's use** (`FUN_0044dba8`, :51792–51845). The army walks toward the target (direct line) or toward DB38's
   intermediate point. Then, **if its moves are unchanged and positive, and `local_e ≥ 0`** (on the direct path `local_e` is
   the uninitialised stack word of #97), it calls CEC8 on its **current position**, walks toward the point if one was found,
   and then **subtracts 1 move whether or not a point was found**. It then recurses while the Chebyshev distance to the
   target is > 1, moves > 0, `local_e ≥ 0` and target x ≥ 0.
3. **CB40 = `DirectLine`, D174 = `Intermediate`, DA88 = `RouteGroup`/`Classify`, CEC8 = `LocalFallback` (armies).**
   Source, line by line:
   - **CB40:** Bresenham with the minor step taken first, and the same medium test. The final sample is checked, but a
     mismatch there is overridden by `if (local_1a < local_14) local_1b = true`. That equals the remake's "excluding the final
     sample".
   - **D174:** the same group bounds (1–25, 26–39, 40–54, 55–58), the same "visible from origin, distance > 0" list, the same
     "closest to the origin among points visible from the target" and "common" picks, the same D010 hand-off, and the same
     target-local recursion. The distance helper `FUN_00449018` is Chebyshev in both.
   - **DA88:** the strict-interior region boxes, then the coordinate-split side; group 3 / 2 / 1. This is `RouteGroup`.
   - **DB38:** routes through D174 only when both points give the same (region, side). Otherwise it calls the ferry lookup
     D9A8. The remake checks `Classify(army) == Classify(target)` before calling `Intermediate`, and has no ferry branch
     (known; outside #105).
   - **CEC8:** `LocalFallback` has the same order, clamp, three-cell probe and last-wins rule, with no flag. That is correct
     for armies (flag 0).

## Controls

**Routine level** (`controls-v1.json`; 15 grids: the 14 SAVs in `saves/` and the BASE.SAV fixture):

| Routine | Cases | Original = remake port | Notes |
|---|---:|---:|---|
| CEC8, flag 0 (army phase) | 3,303 origins (army positions; on BASE.SAV every coast-adjacent land cell and every edge cell) | **3,303** | 12 "none" |
| CEC8, flag 1 (fleet phase) | the same 3,303 | 2,214 | all 400 recorded differences have a land origin. By the code only a land origin can differ: the tolerance accepts sea cells only. None is in the army phase |
| CB40 | 44,734 random pairs (distance 1–40) | **44,734** | 33,614 true |

**Wrapper level** (`wrapper-controls-v1.json`). The full `FUN_0044dba8` on the #187 RAM snapshot, all cells Plain. Rome's army
2 is at (100,40) and the march east is blocked by own army markers on (101,39), (101,40) and (101,41). Each row's
**fallback point** is the goal of the walk that follows CEC8.

| Case | Moves | Target | `local_e` | CEC8 point | Final cell | Moves left | Wrapper entries |
|---|---:|---|---:|---|---|---:|---:|
| open land | 1 | (103,40) or (106,40) | 0 | (103,43) | (100,41) | **−1** | 1 |
| open land | 2 | either | 0 | (103,43) | (100,41) | 0 | 1 |
| open land | 3 | either | 0 | (103,43) | (100,40) | 0 | 2 |
| open land | 5 | either | 0 | (103,43) ×2 | (100,41) | 0 | 3 |
| open land | 8 | either | 0 | (103,43) ×3 | (100,41) | 0 | 5 |
| open land | any | either | −1 | none called | (100,40) | unchanged | 1 |
| sea at (102,42) | m = 1–8 | either | 0 | **(103,40)**, m times | (100,40) | 0 | m |
| sea ring at Chebyshev 3 | 1–8 | (103,40) | 0 | none (all eight probes fail) | (100,40) | m − 1 | 1 |

What the table shows:
- **Moves can go to −1.** The fallback walk spends its step cost, and the wrapper then subtracts 1 regardless.
- **The army can oscillate.** At 3 moves it side-steps to (100,41), then walks back toward the target on the next recursion,
  and ends where it started.
- **The fallback can point into the blockage.** With (1,1) cut by sea, the last successful direction is (1,0): the blocked
  target's own direction. The army then stands still and burns one move per recursion.
- **A "none" still costs 1 move.**
- **`local_e = −1` skips the fallback entirely.** In play the word was never −1 (#97).

The remake's v0.8.4 faithful AI does not run this wrapper at all: it marches once per army per turn
(`2026-10-30-ai-march-continuation-missing-in-remake.md`). So these rows are the target behaviour for #1592, not a v0.8.4 diff.

**Divergent recursion (D174, both games).** When neither the target nor CEC8's point is visible from the origin, D174
recurses on the point (its "target-local fallback"). The control with sea at x = 102–103, y = 37–43 and target (103,40)
cycles (103,40) → (103,43) → (103,40) … : 1,745 CEC8/D174 pairs in Unicorn, until the 1.1 MB emulated stack ran out. The
remake's `Intermediate` throws `NotSupportedException` past depth 58, and `AiMilitaryPhase` catches it and drops the march.
In this control the target is a sea cell; a land target t can cycle only if (+1,+1) succeeds from t and (−1,−1) is the only successful
probe from t + (3,3), and neither point is visible from the army, as on a narrow diagonal strip of land.

## What this does not establish

- **Play.** No case was run in the game; the stack word of #97 and these geometries are emulated only.
- **The original's behaviour when D174 cycles in play.** The stack is 1 MB under Windows; whether the turn ends in a Delphi
  stack-overflow exception, a crash, or never arises on the real map is untested. No real-map pair was searched for a cycle.
- **D010 and D9A8 contracts beyond what #187 controlled**, and the fleet-phase sea tolerance (#1409).
- **The remake beyond v0.8.4.**

## Evidence

- Scripts: `runs/experiments/fallback105/controls.py` (Unicorn; CEC8 and CB40 against ports of `LocalFallback` and `DirectLine`)
  and `runs/experiments/fallback105/wrapper_controls.py` (whole `FUN_0044dba8` through `runs/experiments/navigation187/core.py`).
- Data: `runs/experiments/data/run-exp-fallback105/controls-v1.json` (the SHA-256 of each grid save) and
  `wrapper-controls-v1.json`. The RAM snapshot stays private (`artifacts/run-exp-strategic-fidelity/…/000.ram`, as in #187).
- Decompile: `all_app_functions.txt` (SHA-256 `2018c205…`). Lines: CB40 :50898; CEC8 :51124; D174 :51276; DA88 :51713;
  DB38 :51761; DBA8 :51792; F31C :52899; F608 :53028; FA20 :53210.
- Saves: none new. The grids are `saves/*.SAV` (each listed in `saves/README.md`) and the BASE.SAV fixture.
