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
