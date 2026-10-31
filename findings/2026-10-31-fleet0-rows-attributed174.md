# Carthage fleet 0, attributed: 8 rows are the same outcome, 13 follow a diplomacy divergence, 6 are a port gap (the mercenary run's continuation walk)

**Tag:** [confirmed] for the original: an observation-only hook on the route writers, inert in 80 of 80 turns. The remake
side is measured with its own fleet events plus a code reading.
**Task:** conquest #174, owner request 2026-10-31 ("yeah start it"). This attributes the 27 differing rows of
`2026-10-31-ai-fleets-vs-remake-main.md`, rechecked in `2026-10-31-ai-rerun-remake-8e2d9053.md`.
**Remake compared:** main `8e2d9053`, not released.

> **Correction (2026-10-31, after research PR #162 and the e20a6488 recheck).** Two of the 6 "continuation" rows are
> something else, so the tally is **8 no difference / 14 state / 4 continuation (all at 0 army moves) / 1 seat replay**.
> - **S06 r5 is state.** Its route writer is `F31C` city > 100 with 9 moves, not the continuation: the route-moves hook
>   names the caller (`2026-10-31-ferry-route-written-at-zero-moves159.md`), which this finding's hook could not.
> - **S08 r2 is the seat replay.** The original plays Carthage's seat twice after army 2's battle with the human's army, and
>   the first pass's fleet phase moves fleet 0 away, so the continuation (with 9 moves) gets a ferry route instead of
>   embarking (`2026-10-31-ai-seat-replayed-after-human-battle.md`).
> - The 4 remaining continuation rows (S06 r3/r4, S13 r4/r5) all have the army at **0 moves** at the write. So remake T254
>   (the continuation with moves left) does not change them; the zero-move case does.
> The text below is kept as first written.

## Method

- **Original:** `patches/fleetroute_hook.py`, one observation-only build that logs, per seat:
  - the fleet phase's own branch inputs (the two probes of `patches/fleetphase_hook.py`);
  - **both writers of a fleet's stored route** (`2026-10-30-fleet-route-lifetime131.md` §1):
    - `FUN_0044d9a8`'s ferry rendezvous, at 0x44DA74 after its `call FUN_0044cd08`: the fleet, the route written, and the
      army's point;
    - `FUN_0044dba8`'s aboard landing cell, at 0x44DBF7.
  - Runs: 16 New Game starts × 5 End turns, seed 12345, the same starts as every earlier comparison. The hooked autosaves
    are **byte-identical to the plain build in 80 of 80 turns**.
- **Remake:** the same 80 rounds from the original's autosaves. `RemakeAdapter aiprobe ... fleetlog=` logs each seat's
  `OriginalFleetRouteRequested` (its army-phase route writer, T247) and `OriginalFleetDecision`.
- **Comparison** (`runs/experiments/fleetroute174/compare.py`), per round, nation and fleet:
  - the routes the army phase wrote on each side, and the fleet-phase branch;
  - the nation's army rows from the army comparison (`run-exp-airerun/report-aidecide-v1.json`).

## Result: the 27 rows

| Group | Rows | Cause |
|---|---|---|
| "none" against "idle" | **8** | **Not a difference.** The fleet has no route and 0 moves. The original's fleet phase does nothing, and the remake logs that as `idle`. The earlier comparer treated the two labels as different. |
| a route written on one side, during a diplomacy divergence | **13** | **State.** Every one is a round where Carthage's army 3 is a "diplomacy" row in the army comparison: the war with Celtiberia ends after a battle on one side only. S00 r2 example: in the original, army 2's battle ends the war, so army 3 has no enemy and walks home over land. In the remake the war goes on, army 3 marches across the sea, and its ferry request gives fleet 0 the route (86,76). |
| a route written only in the original | **6** | **Port gap: the mercenary run's continuation walk** (below). |

**Total: 27.** Every row is a route written by one side's army phase. The fleet phase itself agrees wherever both sides
have the same route and moves, as the fleet finding established.

## The port gap: after the mercenary run, the original also makes the continuation walk

**Rows:** S06 rounds 3, 4 and 5, S13 rounds 4 and 5, and S08 round 2. All are Carthage's army 3 on the
`e84c+city>85` branch.
- In S06 round 5 the army rows are "state-battle" (a battle earlier in the round), but the writer is the same
  continuation walk.

**Original (`FUN_0044f31c`, after `call FUN_0044e84c` at 0x44F485):**
- The mercenary run walks the army to the offer.
- Then, **in the same army turn**: army score > 70 → walk at the army target (0x44F4A3); otherwise city score > 85 → walk at
  the city target (0x44F4C7) (`2026-10-30-ai-decisions-vs-remake-main.md`).
- Here the second walk needs a ferry. `FUN_0044d9a8` writes fleet 0's route from the army's position **after** the run:
  - S06 round 3: army point (83,84), route (85,78);
  - S06 round 4 and later: (78,85);
  - S08 round 2: (87,77) → (86,77).
- The army itself does not move further: the saves show it on the run's last tile (S06: (83,84), then (78,85)).
- The fleet, though, keeps a stored route and goes to (85,78) instead of to port.

**Remake (`AiMilitaryPhase.cs:389–400`, `Kind.MercenaryRun`):**
- "The one march a turn allows an army goes to the run while there is an offer to run to." The continuation
  (`MarchAtCityTarget`, `ChaseArmy`) is proposed only when there is no offer.
- The run is identical: army-3 walks (86,78) → (83,84) → (78,85) in S06, as in the original.
- No continuation walk follows, so no ferry request is made, and fleet 0 takes the port branch.

**For the remake (classical-faithful):**
- After the mercenary-run walk, run the continuation walk too, in the same army turn, with the moves left and the
  original's `> 70` / `> 85` tests. That includes the ferry rendezvous it can trigger.
- If the army has no moves left, the walk still asks for a ferry: `FUN_0044d9a8` writes the route whatever the army's moves,
  and the fleet sails on it.

## What this does not establish

- **The continuation walk's effect on the army:** in these rows the army does not move, because it is out of moves or
  waiting for the ferry. A run that ends on land with moves left would also move the army. That case did not occur here.
- **No remake diagnostic build was made for this gap.** The remake side is its own fleet events plus the code comment
  quoted above.
- **The 13 diplomacy rows:** their underlying divergences (a treaty after a battle on one side) are the "battle" and "draw"
  first divergences of the diplomacy comparison. They are not re-attributed here.
- **The army order gap** (`2026-10-31-army-order-within-a-seat.md`) changes none of these 27 rows: under the table-order
  diagnostic, the fleet report is the same 27 rows.
- **Rounds 6+, other seeds, the hunt branch** (no fleet had a hunt candidate).

## Evidence

- Data: `runs/experiments/data/run-exp-fleetroute174/`:
  - `orig-v1/`: hook logs and the inert checks;
  - `remake-8e2d9053-v1/`: the 80 replays with `fleetlog`;
  - `report-routes-v1.json`;
  - `README.md`.
- Release `run-exp-fleetroute174` (hooked and plain autosaves; hashes in `SAVES.sha256`).
- Saves cited: starts `S06_Gaul_AUTO0720.SAV`, `S08_Celtiberia_AUTO0720.SAV`, `S13_armenia_AUTO0720.SAV` and the other
  starts. The round starts are `hooked-tNN-*.SAV`. S06's army-3 positions are read from `hooked-t02`, `-t03` and
  `-t04-*.SAV` in `run-exp-aidecide`.
- Code:
  - `patches/fleetroute_hook.py`;
  - `difftest/probes/fleetphase_hook_run.py` (`IC2_FLEET_HOOK=fleetroute_hook`);
  - `difftest/remake_adapter/AiProbe.cs` (`fleetlog=`);
  - `runs/experiments/fleetroute174/compare.py`.
