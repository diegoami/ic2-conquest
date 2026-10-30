# run-exp-aidecide: AI army decisions, original vs remake main (10d3bb81)

Owner request 2026-10-30: compare the AI's decisions with the remake code, option 1 (run both, then read the code where
they disagree), with remake `main` as the reference. Finding: `findings/2026-10-30-ai-decisions-vs-remake-main.md`.

- `orig-v1/<start>-decide.jsonl`: the original's F31C inputs per army and round (`patches/decide_hook.py`,
  `difftest/probes/decide_hook_run.py`), 16 New Game starts × 5 End turns, seed 12345. `orig-v1/<start>/inert.json`: the
  hooked autosaves are byte-identical to the plain build's in 80 of 80 turns. `orig-v1/crashed/`: a partial S06 run, stopped
  when a second run used the same game folder (rerun complete in `orig-v1/S06_Gaul_AUTO0720*`).
- `remake-10d3bb81-v3/<start>-tNN-*`: remake main, each round imported from the original's autosave before it
  (`runs/experiments/aidecide/compare.py remake`): `decisions` (the remake's DecisionRecords), `probe` (marches),
  `relations` (the matrix after the round), `ailog` (its AI lines). `-v2` is the same without AI logs (identical results);
  `remake-10d3bb81/` holds the first S00 run.
- `report-v2.json`: the comparison (`compare.py compare`); `report-v1.json` the same without the capital-defence flag.
  `attribution-v1.json`: the cause per row (`attribute.py`).
- `capdef/`, `walk-S01/`: the capital-defence and walk hooks on S01 and S05, one round.
- `diagnostics/`: one-line scratch patches of remake main (never pushed) and their probe output:
  `raw-resupply.patch.txt` (skip the reachable-resupply tier, env `IC2_PROBE_RAW_RESUPPLY=1`; all 80 rounds in
  `raw-resupply/`), `f4c7.patch.txt` (the city > 85 continuation marches at the city target; `f4c7/`),
  `capdef-attack.patch.txt` (a capital-defence responder that ends next to its threat attacks it; `capdef-attack/`, with
  main's own AI logs for S01 and S05).
- `smoke*`: the first BASE.SAV turn-1 check (11 of 11 the same).
- Saves: `SAVES.sha256`; binaries in release `run-exp-aidecide` (`aidecide-saves.tar.xz`).
