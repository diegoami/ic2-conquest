# run-exp-sav-inert107: native checks of two static #107 claims

Owner-approved run (session, 2026-10-21; proposal recorded in
[issue #107](https://github.com/diegoami/ic2-conquest/issues/107#issuecomment-6328308006)).
Headless Wine 9 + Xvfb in the cloud container, built by `setup/setup.sh`.
The seed build is `fast rollingsave seed` (SHA-256 `354d8265…532f`), with
seed 12345. The original is SHA-256 `9d753d5d…ba31`.

- **T1:** INERT nation bytes (+0x450..0x46A, +0x46D, +0x491..0x493). The start
  save and a marked copy each go through load, Save As and End turn. Then the
  marked process runs File > New (Rome).
- **T2:** fleet waypoint. `fleet-split-antium-0734.SAV` and a copy with route_y
  sentinels (1000 + fleet index, on live fleets with route_x = −1) each go
  through load, Save As and End turn.
- **T3:** the marked copy goes through load and Save As in the unpatched
  original EXE.

The scripts are in `runs/experiments/sav-inert107/`: `craft.py` (inputs),
`run.py` (driver) and `analyse.py` (receipt).

Files here: per-test step logs (`T*-<stamp>.jsonl`), the analysis receipts and
`SAVES.sha256`. The saves are in `artifacts/run-exp-sav-inert107/` and the
release `run-exp-sav-inert107`.
