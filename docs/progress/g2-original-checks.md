# Running notes: g2-original-checks (issue #75)

Implementer: Sonnet subagent (the owner's choice). Branch `experiment/g2-original-checks`, worktree `.claude/worktrees/agent-a2d5dc6c44f0841d6`.
Data: `runs/experiments/data/run-exp-g2-original-checks/`; binaries in `artifacts/run-exp-g2-original-checks/` (worktree, git-ignored), release `run-exp-g2-original-checks`.

## Plan
- C3 (MM01, 0-move army): `g2_checks.py C3` on `fleet-port-antium-0734.SAV` (army 12 has moves 0 as saved; control = the same army staged to moves 8).
- C4 (MM03, unreachable target): `C4` on `run0-start` (army 0 at (100,37), target (100,25) 12 tiles north; control (100,32)).
- C5 (Change units): `C5a` Join 3/4 units, `C5b` Rename with two selected, `C5c` Split unit threshold + spinner range (type size table read from game memory at 0x478fca).
- C7 (storm): run-free re-analysis of the existing R85sA cell (`c7_storm_reanalysis.py`); fresh Wine only if a gap is left.
- Rule 6: commit and push each batch, `scripts/archive_measurements.py run-exp-g2-original-checks --commit`.

## Progress
- (start) branch created, win_updown.c (spinner range reader) built, g2_checks.py written.
- C3, C4, C4b, C5a, C5b run; C5c running (17/18 tests); C7 re-analysis done (no Wine); decompile reading of the move/select/storm code done. Batch commit now.
- C5c done (18 tests), archived, released (132 files). Findings draft and README written; PR opened.

## Review fixes (PR #77, GPT-6.1 Sol review ses_ed3f05ca...; fixer: Sonnet subagent)
- R1 extract: `make_code_extract.py` -> `code_extract_g2.txt` (pinned dump SHA in header); `c7_storm_model.py` -> `c7_storm_model.txt` (exact enumeration of the army rule); `c7_storm_reanalysis.py` now writes next free version (R3 part; re-run gave `.v2` files, identical text); `g2_checks.py` `sizes()` writes unique images (R3 runner part).
- f06f938: R1 extract/model scripts, R3 versioned c7 writer and unique-image runner (pushed).
- 07f16f9: new C5c spinner run `g2_checks-C5c-20261011-195827.jsonl` (hi:5000 probe, ext_A, ext_B; 90 readings, 285 binaries hashed in SAVES.sha256, release synced: first call hit a GitHub TLS handshake timeout after 240 uploads, the same idempotent sync was run once more and uploaded the remaining 45; release holds 417 assets).
- next commit: finding narrowed and corrected (R1 citations to the extract and dump lines, C4 human/computer flag reading, R2 storm formulas and C7 numbers, R3 new run cited, earlier images stated overwritten); README.

## END
All four checks answered; C7 from existing R85sA data (no new Wine). Nothing blocked.
Review fixes R1, R2, R3 done (see above); no reviewer run, no merge.

## Review round 2 fixes (PR #77, GPT-6.1 Sol review ses_ed3d9fca...; fixer: Sonnet subagent)
- R1: `g2_checks.py save()` passes `<case>_<stamp>_<name>` to `save_as()`; `Game.save_as()` now raises DriverError on an existing destination (new `overwrite=False` parameter, explicit opt-in); `tests/test_save_as.py` offline test. Callers: `tests/test_orders.py`, `tests/make_fleet_fixture.py`, `tests/make_battle_fixtures.py` reuse fixed scratch names and now pass `overwrite=True` (the PR lists them).
- R2 + R3: finding line 80 corrected (80 supplies after the move in all five R85sA trials; the weekly block's `max(0, supplies - ships)` at 54539-54542 zeroes them before the storm; zero-supply penalty 54618-54621 after it; 60/61 result kept). Both line ranges are already inside the whole-function `FUN_004514ec` of `code_extract_g2.txt` (verified by reading 54536-54545 and 54616-54623 there), so no new extract version was needed. Title and C3 heading narrowed to "stays selected, four tested toolbar dialogs open".

## END (round 2)
R1, R2, R3 done; no Wine run, no reviewer, no merge. Nothing blocked.

## Review round 3 fixes (PR #77, GPT-6.1 Sol review ses_ed3cc322...; fixer: Sonnet subagent)
- R1 (commit "R1: make_battle_fixtures ..."): `build_once` saves `FLD-RG_build_<tag>-<stamp>.SAV` without overwrite, then `C.keep` + `record_sha` (SAVES.sha256) at once and logs `build_kept`, before the next build starts; main passes the returned kept paths to the comparison; `FLD-RG.SAV` kept from build a's path; report lists `builds`.
- R2 (commit "R2: release_sync ..."): refusal record holds the complete `cmd` list, `command_shell` (shlex.join), cwd; the same line is printed. No tokens involved.
- `overwrite=True` calls, decided:
  - `tests/make_battle_fixtures.py:50`: measured output -> FIXED (above), no overwrite.
  - `tests/make_fleet_fixture.py:79` (`FLEET2_STAGE.SAV` in the game folder): scratch the script wrote itself in the same run, copied at once to `FLEET2.SAV` -> overwrite kept. Note: that `shutil.copy` to `FLEET2.SAV`/`FLEET.SAV` (`$IC2_WORK/fixtures`) replaces a regenerable fixture, not a measurement; unchanged.
  - `tests/test_orders.py` lines 59, 68, 83, 139, 164, 179, 193, 204, 218, 234, 253, 282, 295, 558, 604, 907: scratch `T_*.SAV` in the game folder, each copied straight away by `keep()` to the test output folder -> overwrite kept (regression-test scratch, rerun regenerates; `keep()` there replaces the test's own copy).
  - `tests/test_orders.py:865, 890` (`dummy.SAV`, `dummy_before.SAV`): scratch read back at once -> overwrite kept.
- Checks (offline only, no Wine): py_compile of both scripts, import of `tests.make_battle_fixtures`, `tests/test_save_as.py`.

## END (round 3)
R1 and R2 done; no Wine run, no reviewer, no merge. Nothing blocked.
