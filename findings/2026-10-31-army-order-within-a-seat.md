# The original moves a seat's armies one at a time in table order; remake main picks the best action across armies

**Tag:** [confirmed]. Found on the original's own hook logs and checked in 80 equal-state rounds, with a diagnostic remake
build.
**Task:** found during the #174 fleet-0 attribution (owner request 2026-10-31).
**Remake compared:** main `8e2d9053` (T250–T252), not released.

## The difference

- **Original:** the army phase runs `FUN_0044f31c` for each own army **in table order**. Each army decides, walks and
  attacks before the next army decides, so a later army sees what the earlier ones left: their positions, their kills,
  and a war ended by a treaty after a battle.
  - The decide hook (`patches/decide_hook.py`) logs the armies in table order, each with the state at its turn.
  - Example: S03, round 2. Carthage's army 2 attacks Celtiberia's army 10 (score 1126, distance 4) and destroys it. Army
    3's inputs, logged afterwards, have no enemy army (score −10000). So army 3 takes `e84c+city>85` and marches on the
    city osca at (49,41).
- **Remake main:** `AiTurn` proposes candidates for **all** own armies on the current state. It executes the
  highest-scoring one (exact ties go to a draw from the seat's random stream), then proposes again.
  - So a later army can act first, on a state the earlier armies have not changed yet.
  - S03, round 2: army-3's march and army-2's approach both score 1651. The draw picks army-3 first. It chases army-10 at
    (38,64), 50 tiles away across the sea; army-2 destroys that army moments later.
  - In 96 of 158 seats where two or more armies acted, the remake ran them out of army-id order. Id order is the table
    order here unless a death moved records. The diagnostic below: 0 of 156.

## Measured on 80 rounds

These are the same 80 rounds as the earlier comparisons: 16 New Game starts × 5, seed 12345, each replayed in the remake
from the original's own autosave.

`runs/experiments/fleetroute174/army_order.py` takes each army's **first action** in the remake's AI log. It checks the
kind (target army, city at the original's position, resupply, or the mercenary run) against the original's branch at that
army's turn. Rows that are "diplomacy" or "state" in the army comparison are skipped.

| Remake | First actions matching the original (679 armies) |
|---|---|
| main `8e2d9053` | 668 |
| main + **table order** (diagnostic) | **678** |

- **The diagnostic** (`army-order-diag-v2.patch.txt`) is a scratch build, never pushed. In faithful mode only, it offers
  military candidates from the first own army in table order that still has one at or above the minimum score. That is
  the original's one-army-at-a-time loop. Nothing else changes: same scorers, walks and re-planning after each action.
- **The 10 armies it fixes:**
  - Carthage army 3, round 2, in S03, S04, S05, S08, S11 and S12. Main chases army-10, which army 2 is about to destroy;
    the original and the diagnostic march on osca (49,41).
  - Seleucid army 4, round 3, in S01, S07 and S13. Main approaches (220,35); the original and the diagnostic approach
    (177,41).
  - Seleucid army 4, S03, round 4. The original attacks army 0 (`army>100`); main approaches a city; the diagnostic
    approaches the target army.
- **It breaks none.** The one row left is the Galatia battle draw (S02, round 4,
  `2026-10-31-ai-rerun-remake-8e2d9053.md`).
- **Why the earlier comparisons missed it:** `aidecide/compare.py` reads each army's **first** remake decision record. The
  remake writes those on the first proposal pass, before any army has acted, so the record matched the original's
  inputs even where the army later acted on that stale state. The diplomacy, economy and fleet comparisons are
  unaffected: under the v1 diagnostic their results are the same or better (diplomacy: 1,133 same seats against 1,110, with
  no deterministic first divergence; fleets: unchanged, 27 rows).

## For the remake

In classical-faithful (`ClassicalArmyNavigation.Applies`):
- Run the military phase **one own army at a time, in live table order** (`state.Armies`, T240).
- Each army takes its target-tree action, its walk, its attack and its fallback, on the state the earlier armies left.
- No cross-army score competition, and no random tie draw between armies.
- The designed / Improved AI keeps its candidate selection.

## What this does not establish

- **Non-military candidates:** where the original places diplomacy and economy relative to the army loop is the existing
  phase order (`2026-10-30-ai-diplomacy-vs-remake-main.md`, `2026-10-31-ai-economy-vs-remake-main.md`). The diagnostic
  left those candidates in the same pool.
- **The remake's implementation:** the diagnostic is a filter on the existing loop, not a patch proposal.
- **Rounds 6+, other seeds.**

## Evidence

- Data: `runs/experiments/data/run-exp-fleetroute174/`:
  - `remake-order-diag-v2/`: the 80 diagnostic rounds;
  - `army-order-diag-v2.patch.txt`;
  - `army-order-v4.json`: the table above, per army, with the seat-order counts (v1–v3 are earlier classifier
    versions, kept);
  - `README.md`.
  - v1 of the patch is kept as measured: it also counted candidates below the minimum score, which left two armies idle.
- The normal main run: `runs/experiments/data/run-exp-airerun/remake-8e2d9053-v1/`.
- Original: `run-exp-aidecide` (decide hook logs and round-start saves). Saves cited: starts `S00_Rome_AUTO0720.SAV` …
  `S15_thracia_AUTO0720.SAV` and round starts `hooked-tNN-*.SAV` (S03 round 2 = `hooked-t01-AUTO0721.SAV`).
