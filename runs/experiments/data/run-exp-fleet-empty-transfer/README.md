# run-exp-fleet-empty-transfer

Original-side check from ic2-research (`docs/pending-requests.md` ef0d3e2): when Transfer ships empties a fleet, does the receiving fleet get the giver's money (+16) and supplies (+14), or are they lost? Earlier Ta/Tb/Tc saves had 0 on both, so nothing could be seen.

- **Runner:** `fleet_empty_transfer.py <case>`, one fresh Wine process per case, fast rollingsave seed exe, seed 12345, Xvfb. Start `saves/fleet-split-antium-0734.SAV` (fleet 2 at (101,46), fleet 5 at (101,47)). Staging (L1) patches only fleet records (ships +18, supplies +14, money +16), never x/y. Only the ship arrows are touched. Fleet 5 gives to fleet 2.
  - Td0: fleet 5 10 ships, 37 supplies, 123 money; fleet 2 20 ships, 50, 400; fleet 5 gives 5 (partial, control).
  - Td1: same values; fleet 5 gives all 10.
  - Td2: fleet 5 10 ships, 90, 123; fleet 2 5 ships, 40, 400; fleet 5 gives all 10 (room 15 x 8 = 120 < 40 + 90).
- **Logs:** `fleet_empty_transfer-<case>-<stamp>.jsonl` (fleets and Rome's treasury before and after, controls, boxes, dialog screenshot name). One run per case, none failed.
- **Results (all turn 0734, start `saves/fleet-split-antium-0734.SAV`):** Td1 `Td1_20261010-213503_before.SAV` / `_after.SAV`; Td2 `Td2_20261010-213548_before.SAV` / `_after.SAV`; Td0 `Td0_20261010-213628_before.SAV` / `_after.SAV`. Every claim in the finding is read from these.
- **Table:** `table_from_saves.md`, made by `table_from_saves.py` from the before/after saves (read-only parse with `state/sav.py`).
- **Binaries:** saves and the before-OK screenshots in release `run-exp-fleet-empty-transfer` (gitignored `artifacts/run-exp-fleet-empty-transfer/`); SHA-256 in `SAVES.sha256`.
- **Finding:** `findings/2026-10-10-fleet-emptied-by-transfer-money-and-supplies.md`.
- **Environment:** `environment-after-runs.json` is the output of `scripts/environment_check.py` (the tool also printed "Same environment as the baseline.", removed so the file is JSON). It was taken after the three runs (2026-10-10 ~21:3x), not during them, because the branch started before the environment record merged. Same machine; its font set and Wine had not changed since the 19:33 font experiment (`runs/experiments/data/run-exp-machine-move/RESULTS.md` §5). The cases were not re-run.
