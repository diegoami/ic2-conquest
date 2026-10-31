# run-exp-fleetroute174: attributing the Carthage fleet-0 rows (#174) on remake main 8e2d9053

Owner request 2026-10-31 ("yeah start it"): attribute the 27 fleet rows of `findings/2026-10-31-ai-rerun-remake-8e2d9053.md`.

- **Original** (`artifacts/run-exp-fleetroute174/orig-v1/`, copied here by `scripts/archive_measurements.py`):
  `IC2_FLEET_HOOK=fleetroute_hook python3 -m difftest.probes.fleetphase_hook_run <out> 5 <the 16 starts>`.
  `patches/fleetroute_hook.py` is the fleet-phase hook's two probes plus the army phase's two route writers (D9A8 ferry
  rendezvous at 0x44DA74, DBA8 aboard landing at 0x44DBF7). It is observation-only, and each start's `inert.json` compares
  the hooked autosaves with the plain build's.
- **Remake** `remake-8e2d9053-v1/`: the same 80 rounds, `RemakeAdapter aiprobe ... fleetlog=` (new: each seat's
  `OriginalFleetRouteRequested`, `OriginalFleetDecision`, fleet moves and arrivals).
- **Army-order diagnostic** (found on the way):
  - `army-order-diag.patch.txt` / `-v2.patch.txt`: scratch patches of 8e2d9053, never pushed. With
    `IC2_DIAG_ARMY_ORDER=1` and in faithful mode, only the first own army in table order that still has a military
    candidate (v2: one scoring at least the minimum) is offered. That is the original F31C's one-army-at-a-time loop.
  - `remake-order-diag-v1/` (v1 patch), `remake-order-diag-v2/` (v2 patch): all 80 rounds.
  - Reports on v1: `report-aidecide-order-diag-v1.json`, `attribution-aidecide-order-diag-v1.json`,
    `report-fleet-order-diag-v1.json`, `report-diplo-order-diag-v1.json`.
  - `army-order-v1.json`, `-v2.json`, `-v3.json`: `runs/experiments/fleetroute174/army_order.py` (each army's first
    action vs the original's branch). v1 used the coarse classifier, v2 the refined one; v3 also matches armies by
    position after deaths. v4 is v3 plus the seat-order counts, and is the one cited
    (`findings/2026-10-31-army-order-within-a-seat.md`).
