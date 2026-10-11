# run-exp-g2-original-checks

Original-side checks 3, 4, 5 and 7 of the v0.5.0 gap analysis (`../run-exp-gap-v050/rows_g2.md`, "Original-side checks needed"; issue #75).

- **Runner:** `g2_checks.py <case>`, one fresh game process per case, fast rollingsave seed exe, seed 12345, Xvfb. Cases: `C3` (0-move army), `C4` (unreachable target + near control), `C4b` (per-tile costs, river stop), `C5a` (Join 3 / 4 / 2 units), `C5b` (Rename with two selected, one as control), `C5c` (Split unit: threshold, spinner range; test specs `type:troops[:mode]`).
- **`win_updown.c`:** reads the range and position of up-down controls (built to `~/ic2-work/win_updown.exe`).
- **`c7_storm_reanalysis.py`:** check 7, no Wine run: re-reads the R85sA cell of `run-exp-storms` and recomputes the decompile's storm rule; outputs `c7_storm_reanalysis.json` / `.txt`.
- **`release_sync.py`:** uploads artifacts to release `run-exp-g2-original-checks` (never deletes); `release-sync-*.json` records each call.
- **Logs:** `g2_checks-<case>-<stamp>.jsonl`, one JSON line per step, never overwritten. Notes on the runs:
  - `g2_checks-C5c-20261011-190536.jsonl`: first Split probe (hi 5,000, default OK; the spinner positions it recorded are the controls' internal values, not sizes).
  - `g2_checks-C5c-20261011-191005.jsonl`: hi 5,000 probe with sizes read by OCR from the dialog.
  - `g2_checks-C5c-20261011-191204.jsonl`: failed start, the refusal box was not closed before the Change units dialog (runner bug, fixed); nothing was applied.
  - `g2_checks-C5c-20261011-191316.jsonl`: the 18 threshold, 100-troop and extreme tests.
- **Binaries:** saves and screenshots in release `run-exp-g2-original-checks` (git-ignored `artifacts/run-exp-g2-original-checks/`); SHA-256 in `SAVES.sha256`.
- **Finding:** `findings/2026-10-11-g2-original-checks.md`.
