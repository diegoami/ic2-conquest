# The AI fleet move FUN_0044e1fc: target replacement, waypoint, the no-progress swing, recursion and arrival

**Tag:** [confirmed] from the disassembly (0x44E1FC–0x44E41B, `FUN_0044939c`), and in emulation. 41 fleet-phase cases were
traced level by level with no helper, Random, movement or contact routine replaced. All 21 waypoint calls (D174) return
exactly what the research #187 portable model gives for group 0.
**Task:** research [#131](https://github.com/diegoami/imperial-conquest-2-research/issues/131) part 3 (remake #1405, #1409).
Parts 1–2 are `2026-10-30-fleet-route-lifetime131.md`.
**Background:**
- `2026-10-24-army-navigation-rule187.md`: D174, CB40, CEC8 and the navigation tables, not repeated here.
- `2026-10-30-ai-fleet-moves-in-play1409.md`: the same steps seen in play.
- `2026-10-24-fleet-accepted-movement174.md`: the low-level walker E094 and its AI move zeroing.

## The contract

`E1FC(fleet f, target T)`; P is the walk point, m0 the moves at entry.

```
code := map[T]                               (read once at entry, 0x44E221; the ORIGINAL target's cell)
P := T
if CB40(pos, T):                             direct line (#187 rule; at distance 0 its result is undefined, see below)
    E094(f, T)                               walk toward T
else:
    if 2 <= code <= 247:  P := 939C(T, sea)  land, city or army cell: replace the target by a sea cell (below)
    P := D174(group 0, pos, P)               the #187 waypoint rule, sea waypoints 1-25; the replaced point is
                                             NOT re-tested with CB40
    if P.x >= 0:  E094(f, P)
if moves == m0 and moves > 0 and P.x >= 0:   no progress
    Q := CEC8(pos)                            fleet-phase flag = 1 (sea tolerance)
    if Q.x != -1:  E094(f, Q)
    moves -= 1                                charged even when CEC8 finds nothing (0x44E2CE)
if dist(pos, T) > 1 and moves > 0 and P.x >= 0 and T.x >= 0:
    E1FC(f, T)                                recursion with the ORIGINAL target
if dist(pos, T) == 1 and moves > 0:          arrival, by code (each level, after its own recursion returns)
    code < 2        : E094(f, T) when the cell's terrain cost < moves
    2..11 (land)    : FUN_0044b840 landing, if the fleet carries an army
    20..99 (city)   : FUN_0044f7e4 when the nation is NOT at war with the city's owner
    300..347 (fleet): FUN_0044b5d0 naval combat when the target fleet's owner is at war with the fleet's owner
    otherwise (armies 200..247 included): nothing
```

**`FUN_0044939c(T, flag, out)`.** E1FC calls it with flag 0, which asks for codes 0–1 (sea); flag 1 asks for 2–11 (land).
- **The search:** square neighbourhoods of growing radius r = 0, 1, 2, … around T, with clamped coordinates, x offset in the
  outer loop and y offset in the inner. It stops after the first radius with a match.
- **Within that radius the last match wins,** i.e. the largest x offset, then the largest y offset.
- **With flag 0,** cells that `FUN_004496bc` excludes are skipped (x > 247, or x > 213 and y > 98).
- **Examples:** (47,64) → (48,65); (45,68) → (46,69); (47,63) → (48,64).

## Expected rows (`part3-v3.json`)

All cases start from the fleet174 synthetic Carthage state, fleet 0 at (49,62); the derived cases are declared in `phase.py`
and `part3.py`. "First destination" is what F608 hands to E1FC. The other columns are what E1FC actually does.

| Case | First destination | Line | 939c | D174 waypoint | Walks (end cell) | End, moves | Arrival |
|---|---|---|---|---|---|---|---|
| route on sea, 3 away (`phase-stored-a`) | (48,66) | yes | — | — | direct (48,64); level 1 direct (48,66) | (48,66), 25→21 | none (distance 0) |
| **land route across the coast** (`route-landing-cargo`) | (47,64) | no | (48,65) | **(75,69), node 5, common-visible** | waypoint → (74,69) | (74,69), 25→0 | none; **the army aboard follows to (74,69)** |
| port pick, west coast (`phase-peace`) | city (45,68) | no | (46,69) | (75,69) | waypoint → (74,69) | (74,69), 0 | none |
| inland route (`route-inland`) | (41,57) | no | (48,64) | (75,69) | waypoint → (74,69) | (74,69), 0 | none |
| **adjacent land target, army aboard** (`adjacent-landing-cargo`) | (47,64) from (48,64) | yes | — | — | direct: no step; **CEC8 (51,67)**, −1 move; level 1 direct → (48,65) | (48,65), 25→0 | **landing at level 1** (army to (47,64), fleet cargo −1) |
| adjacent land target, no cargo | (47,64) from (48,64) | yes | — | — | same swing | (48,65), 25→18 | none |
| **adjacent own port** (`adjacent-own-port`) | city (47,63) from (48,64) | yes | — | — | same swing, back to (48,64) | (48,64), 25→18 | **port call at level 1 and again at level 0** |
| **fleet starts on its route** (`route-reached`) | (48,66) at (48,66) | no (distance 0) | — | (39,78), node 4 | waypoint → (39,78); level 1 direct → (48,66) | (48,66), 25→1 | none |
| route on the adjacent sea cell (`p3-no-progress-sea-target`) | (49,63) | yes | — | — | direct → (49,63) | (49,63), 25→24 | none (distance 0) |
| **stored route, zero moves** (`route-zero-moves`, `cargo-zero`) | (48,66) | yes | — | — | direct: no step | (49,62), 0 | none: every later step needs moves > 0 |
| hunt, enemy fleet 3 away (`phase-war`) | (48,65) | yes | — | — | direct → (48,64) | (48,64), 25→23 | naval combat (run stops before it) |

**The land-route trip east is the rule, not an accident.**
- The original target (47,64) fails the direct line.
- E1FC replaces it by (48,65), only 3 cells from the fleet on open water. It does not re-test the line.
- D174 then takes the common-visible waypoint **nearest the origin** (#187), node 5 at (75,69), 26 away.
- With 25 moves the fleet stops at (74,69), one short. The route is cleared at the round tick, so nothing continues it unless
  the army phase writes it again.

**The no-progress swing.**
- The direct walk cannot enter land, so the moves are unchanged.
- CEC8 from the fleet's sea cell picks (51,67), the last successful direction 3 cells out. That costs 3 moves plus the
  1-move charge.
- The recursion walks back next to the target (3 more).
- 7 moves for no net progress. This is the oscillation seen in play (#1409).

**Arrival runs at every level.** A level that ends at distance 1 with moves left runs the arrival branch after its recursion
returns. In `adjacent-own-port` both levels end beside the port, so `FUN_0044f7e4` runs **twice** in one move. Landing sets
the fleet's moves to 0, so the outer level does nothing after it.

**First destination is not accepted movement.**
- F608's destination (a port, a route, a hunt target) is only the `T` above. The cells the fleet actually walks are the
  direct line, the 939c and D174 point, the CEC8 cell and the recursion.
- A proposal test that compares destinations, like fleet174's native proposals, cannot see the difference between "port
  (45,68)" and "sail to (74,69)".

## What this does not establish

- **CB40 at distance 0 reads an uninitialised temporary** (#187). In `route-reached` it returned false, which sent the fleet
  on its 24-move round trip. Another stack history could return true, giving no move.
- **Naval combat, and arrival on a city at war,** are not executed (the runs stop at `FUN_0044b5d0`). The sea-step arrival
  branch did not occur here.
- **The walker E094's own rules** (cost, rough sea, the AI zeroing) are fleet174's. **D174 internals** are #187's; here they
  are only checked: 21 of 21 calls match.
- **Full-seat RNG and naval-result parity:** not measured.

## Evidence

- Script: `runs/experiments/fleetroute131/part3.py`, using `phase.py`'s inputs and cases plus two of its own, and the #187
  model `runs/experiments/navigation187/model.py`.
- Data: `runs/experiments/data/run-exp-fleetroute131/part3-v3.json`.
  - `part3-v1.json` and `part3-v2.json` are kept and superseded. They closed a level early whenever E1FC jumped to 0x44E302
    without recursing, which also hid the naval-combat stop in v1. Their D174 checks are unaffected (21 of 21).
- Disassembly: E1FC 0x44E1FC–0x44E41B, `FUN_0044939c` 0x44939C–0x4494E2, `FUN_004496bc` 0x4496BC–0x4496DF.
