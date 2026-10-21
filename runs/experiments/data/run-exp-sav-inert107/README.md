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

## Results (2026-10-21, stamps 20261021-225237 / -225534 / -225657)

Receipts are `analysis-T1-*.json`, `analysis-T2-*.json` and `analysis-T3-*.json`.
`SAVES.sha256` holds T1 only; `SAVES.sha256.v2` holds all 12 saves.

- **T1: every prediction held.**
  - The markers survive Save As and End turn.
  - After one full round (16 seats, AI moves, an offer box), the plain
    `AUTO0721` and the marked one differ in exactly the 496 marker bytes and
    nowhere else. No reader changed any gameplay outcome in that round.
  - After File > New (Rome, seed 12345) in the marked process, the
    new-game autosave keeps every marker. Outside them it equals the reference
    `run0-start-AUTO0720-seed12345.SAV` byte for byte: its hash equals the
    marked input's. So File > New does not clear the bytes.
  - Save As also changed 2 bytes outside the INERT ranges (`0x1B2F6`,
    `0x1B2FC`). Research saw `0x1B2F6` change the same way on a plain re-save
    (G5, 2026-10-11).
- **T2: as predicted.**
  - The split fleet 5's route went from (0;0) to x = −1 at the round tick,
    and its y stayed 0.
  - All 5 route_y sentinels survived. The plain and sentinel autosaves differ
    only in those 10 bytes.
  - No AI army set a waypoint in this round.
- **T3: the unpatched original EXE gives the same result.** Its Save As of
  the marked copy is byte-identical to the seed build's (SHA-256
  `3f38a391…`), with the markers intact.

**Binaries.** The release token is not set in this cloud container, so no
release was made. The 12 saves are in the environment's Drive artifact store,
`gdrive:IC2/artifacts/run-exp-sav-inert107/` (`rclone check`: 12 matching),
and in the git-ignored `artifacts/run-exp-sav-inert107/`. To publish them:
`gh release create run-exp-sav-inert107 artifacts/run-exp-sav-inert107/*/*.SAV`.
