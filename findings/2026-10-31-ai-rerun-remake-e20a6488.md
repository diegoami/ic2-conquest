# The AI comparisons rerun on remake main e20a6488 (T253 army order, T254 continuation with moves)

**Tag:** [confirmed]. The same equal-state replays as before: 16 New Game starts × 5 rounds, seed 12345, each round from
the original's own autosave.
**Task:** owner request 2026-10-31, after remake #1655 (T253) and #1657 (T254) merged.
**Remake compared:** main `e20a6488`, not released. All 80 rounds ran without error.

## Result

| Comparison | `8e2d9053` | **`e20a6488`** |
|---|---|---|
| Seats where the remake ran armies out of table order | 96 of 158 | **0 of 156** |
| Armies' first action matching the original (`army_order.py`, each run filtered by its own army report) | 668 / 679 | **679 / 680** |
| Army decision records, by cause | 691 same, 41 diplomacy, 16 state, 1 other | 692 same, 40 diplomacy, 16 state, 1 other |
| Diplomacy: same seats; deterministic first divergences | 1,110; 0 | **1,139; 0** |
| Economy: seats with a difference | 0 | 0 (1,060 same, 140 state) |
| Supply, hire, consolidation, merges: seats the same | 1,192 / 1,200 | **1,194 / 1,200** |
| Fleet branch rows differing | 27 | 27 |
| Fleet route rows: a route written on one side | 19 | 19 |

- **T253 (army order) is verified:** no seat runs its armies out of order. Every army's first action matches the original
  except the Galatia battle-draw row (679 / 680; the first version gave 678 / 679 because it filtered with the 8e2d9053
  army report, research's intake), and the two #176 seats that came from army order (S05/S09 r1) now match.
- **T254 (continuation with moves left) changes no row here.** In the original, every remaining continuation row has either
  0 moves at the ferry request or the seat replay below.
- **The 19 fleet route rows:**

  | Rows | Cause |
  |---|---|
  | 13 | diplomacy state (as before) |
  | 1 | S06 r5: state. Research's correction: its writer is `F31C` city > 100, not the continuation. |
  | 4 | S06 r3/r4, S13 r4/r5: the zero-move ferry request (`2026-10-31-ferry-route-written-at-zero-moves159.md`); the remake still stops at 0 moves |
  | 1 | S08 r2: **the original plays Carthage's seat twice** (`2026-10-31-ai-seat-replayed-after-human-battle.md`) |

- **The 6 supply/hire seats:** 5 are state, and S10 r2 is the treaty timing
  (`2026-10-31-ai-supply-hire-consolidation-merges176.md`). Two of the state seats, S03 r1 Seleucid and S06 r2 Rome, are
  also seats the original played twice.

## Still open in the remake

1. The ferry request at 0 army moves (#1652's remaining case; research #159 is now measured).
2. The post-battle treaty applied at the seat's end, not right after the battle (#176 finding).
3. The seat replay after a battle against the human (new).

## Evidence

- Data: `runs/experiments/data/run-exp-airerun-e20a/`:
  - `remake-e20a6488-v1/`: the 80 replays, with decisions, relations, AI log, events and the fleet log;
  - the reports `report-aidecide-v1.json`, `attribution-aidecide-v1.json`, `army-order-v2.json` (filtered by this run's own army report; `-v1` used the 8e2d9053
    report, kept), `report-diplo-v1.json`,
    `report-econ-v1.json`, `report-fleet-v1.json`, `report-routes-v1.json`, `report-econ2-v1.json`.
- The original's side: the hook runs and releases `run-exp-aidecide`, `run-exp-diplo`, `run-exp-econ`,
  `run-exp-fleetphase`, `run-exp-fleetroute174` and `run-exp-econ2`. Saves: starts `S00_Rome_AUTO0720.SAV` …
  `S15_thracia_AUTO0720.SAV`, and the round starts `hooked-tNN-*.SAV`.
