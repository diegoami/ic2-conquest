# run-exp-econ2: the rest of #176 (supply and hire pass, consolidation, merges, fleet order) vs remake main 8e2d9053

Owner request 2026-10-31 ("ok do 176").

- **Original** (`artifacts/run-exp-econ2/orig-v1/`, copied here by `scripts/archive_measurements.py`):
  `IC2_FLEET_HOOK=econ2_hook IC2_HOOK_LOG=econ2 python3 -m difftest.probes.fleetphase_hook_run <out> 5 <the 16 starts>`.
  `patches/econ2_hook.py` is observation-only, with eight probes (see its docstring). Each start's `inert.json` compares the
  hooked autosaves with the plain build's.
  - `smoke/`: S00, one turn.
- **Remake:** the AI logs of `runs/experiments/data/run-exp-airerun/remake-8e2d9053-v1/`. These are the same rounds from the
  original's own autosaves, on main 8e2d9053.
- **Comparison:** `runs/experiments/econ2/compare.py`, per seat (see its docstring).
- `orig-v1/`: hook logs (`<start>-econ2.jsonl`) and inert checks (16/16 identical). The saves are in release
  `run-exp-econ2`, with hashes in `SAVES.sha256`. `run.log`, `remake-diag.log`: runner output.
- `report-v1.json`: the comparison against main (1,192 / 1,200 same). `report-order-diag-v1.json`: the same, against the
  table-order diagnostic of run-exp-fleetroute174 (1,194).
- `remake-e41c-diag-v1/` (`e41c-diag.patch.txt`): all 80 rounds, each army's state as it enters the remake's supply pass
  (stderr `*-diag.txt`). `remake-e41c-diag-v2/` (`e41c-diag-v2.patch.txt`): S10 round 2, plus the hire gates. Scratch
  patches of 8e2d9053, never pushed; with `IC2_DIAG_E41C=1` they only add stderr lines.
- Finding: `findings/2026-10-31-ai-supply-hire-consolidation-merges176.md`.
