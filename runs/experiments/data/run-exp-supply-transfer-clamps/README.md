# run-exp-supply-transfer-clamps

The original-side checks 1, 2 and 6 of the v0.5.0 gap analysis (`runs/experiments/data/run-exp-gap-v050/rows_g2.md`, "Original-side checks needed"): which providers the original's Supply dialog accepts (UA01, UF01), what Transfer ships does with an armed fleet, a fleet over 100 ships and every ship moved (UF03), and whether Transfer unit clamps per unit at 100,000 troops and at a full fleet (UA03, R29, R30).

- **Runner:** `supply_transfer.py <case>`, one fresh game process per case, fast rollingsave seed exe, seed 12345, Xvfb.
  - P1-P5: providers (`saves/run0-start-AUTO0720-seed12345.SAV`, `saves/fleet-port-antium-0734.SAV`).
  - Ta1-Ta3, Tb1, Tc1, Tc2: Transfer ships (`saves/fleet-split-antium-0734.SAV`).
  - U1, U2, U3, U3b: Transfer unit clamps (`saves/fleet-port-antium-0734.SAV`).
  - The docstring gives the code reading each case tests and the staging (L1, labelled; positions are never edited, units are moved in play).
- **Logs:** `supply_transfer-<case>-<stamp>.jsonl`, one JSON line per step. Never overwritten; a re-run writes a new file.
  - `supply_transfer-P1-20261009-192610.jsonl` is a failed first start: the main window took more than 40 s to appear. Nothing was played.
  - `supply_transfer-P1-20261009-192723.jsonl` has no positive control. The control (the same army next to Arretium) was added before the later runs.
- **Binaries:** saves and screenshots in release `run-exp-supply-transfer-clamps` (gitignored `artifacts/run-exp-supply-transfer-clamps/` while running); SHA-256 in `SAVES.sha256`.
