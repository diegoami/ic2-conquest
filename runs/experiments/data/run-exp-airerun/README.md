# run-exp-airerun: the bounded AI comparisons rerun on remake main 8e2d9053 (T250–T252)

Owner request 2026-10-31: rerun the army, diplomacy, economy and fleet comparisons on remake main `8e2d9053` (#1650), which
carries the corrections from the 2026-10-30/31 findings. Finding: `findings/2026-10-31-ai-rerun-remake-8e2d9053.md`.

- `remake-8e2d9053-v1/<start>-tNN-*`: one remake replay per round (80 rounds: 16 New Game starts × 5, seed 12345), each
  imported from the original's own round-start autosave (`runs/experiments/aidecide/compare.py remake`, now also writing
  `events=`): `decisions`, `probe`, `relations`, `ailog`, `events`. All 80 ran without error.
- The original's side is unchanged: the hook runs of `run-exp-aidecide/orig-v1`, `run-exp-diplo/orig-v2`,
  `run-exp-econ/orig-v1`, `run-exp-fleetphase/orig-v1` (round-start saves in their releases).
- Reports: `report-aidecide-v1.json` + `attribution-aidecide-v1.json`, `report-diplo-v1.json`, `report-econ-v1.json`,
  `report-fleet-v1.json`.
- `aborted/remake-8e2d9053-wrong-save-dir/`: a first replay pointed at the tracked `orig-v1` folder, which holds no saves:
  rounds 2–5 failed with "file not found" (64 error files); round 1 outputs are the same runs as v1's. Kept per rule 6.
