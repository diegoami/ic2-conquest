# run-exp-battle-sweep: data folder notes

- `EXES-sha256-label-correction.txt`: the git label in `EXES-sha256.txt` was a blob hash; corrected there (old file kept).
- `trials.jsonl` line 1 (`hi-hi-one_s1_r1`, the first live trial, run before the runner's record schema settled) is **kept as written**:
  it uses the obsolete key `result_text` (the OCR of the Battle ended box; later rows call it `result_text_ocr`), has no `result` and
  `battle_ended_shot`, and its dialog `shot` is an absolute path in the Wine work folder (`~/ic2-work/shots/dialog-Offer_of_peace-1791098296.png`),
  not a file kept with the artifacts. Rows 2 onward share the final schema. The screenshot is copied to artifacts/run-exp-battle-sweep/shots/
  and the release as `hi-hi-one_s1_r1_dialog-Offer_of_peace-1791098296.png` (copied and uploaded on 2026-10-04; its SHA-256 is in `SAVES.sha256`).
- `sweep-table-20261004-092739.csv` is a near-empty table written by a run that crashed on a missing key (fixed); kept.

## Screenshots (added in the PR B review)
- Until this review `b2_probe.py` and `b3_crafted.py` wrote screenshots to fixed names (overwriting) and recorded no SHA-256. They now go through
  `common.shot` -> `common.keep` (versioned name, hash in SAVES.sha256). The 53 PNGs that existed when this was fixed were hashed then (not when taken).
- **Overwritten and lost:** `b2_probe.py` ran three times (the first two aborted on an End turn proof, the third, 093834, completed; also the ad-hoc
  exploration scripts of that session wrote `b2_after_end1_window.png`, `b2_after_end2_window.png`, `b2_placement_window.png`, `b2_placement_root.png`).
  `b2_placement_window.png` and `b2_after_end_turn_{1,2}_window.png` hold the last run's (093834) image; the earlier runs' versions of the same names
  were overwritten. The release copies were uploaded after the last run.
- `b2-analysis-20261004-095312.json` (137 files) and `-095840.json` (241 files) are the series analysis of the first and of the later set of trials;
  `-104523.json` adds `all_battle_saves`: every `BATTLE<nn>` save decoded (763: 345 B0, 192 B3 resumed, 226 trials/other), the complete basis of the sprite-rule claim.
- `sweep-table-*.csv` made before the `build` / `level` columns were added have no such columns: all their rows are lab, L1.

## PR B second review
- **`stage.py` mirror (R1/R2):** the earlier `consistent=True` mirror mapped defender slot `20+j` to army unit `j`. It now matches the slot's old (name, type) to exactly one unit of the army and refuses otherwise. **No B3 crafted save was affected:** every scenario of `b3_crafted.py` edited slot 0 (the attacker's, whose units follow the army order) or the grid only (`c2, c3, c4, c6, c7, d3, d6, d8`: slot 0; `c5, d5`: grid; `c1`, `c0`, `d0`, `e0`: none), none edited a defender slot, and the results stand (the battle plays from the slots anyway, B3 c4).
- **`sweep-table-20261004-105525.csv`** (new table, older ones kept): the `halflog`, `loss_rows` and `unambiguous_rows` of trials 1-6 (`hi-hi-one_s{1,2,3}_r{1,2}`), recorded in `trials.jsonl` before the half-round hook existed, are **backfilled** by `trials.py table` from the `halfrounds-<trial>.jsonl` files that `halflog.py` wrote afterwards from the same series (`trials.jsonl` itself is unchanged). Trials 7-12 carry them in their own records.
- `halflog.py` now never rewrites a written file (versioned name in a loop, file opened exclusively).

## PR B third review: claims audit
`claims-audit-20261004-110712.md` (written by `runs/experiments/battles/claims_audit.py`, which recomputes every claim from the tracked file it cites; 68 claims, 0 mismatches after the fixes below). Mismatches found while building it, all corrected in the finding / PR body / battles.md / results.md, none hidden:
- HI size-class ranges had come from B0's series only (489-816 / 2,094-3,964 / 4,226-5,900) but cited the all-series analysis (250-1,866 / 2,024-3,964 / 4,083-6,000): now the cited values.
- "261 loss rows, 150 (57 %) unambiguous" was attributed to B0's two series; it was B0 + the 1-v-1 trials. B0 alone: **125 rows, 14 (11 %)**; the 1-v-1 trials 272 of 272; aggregate 286 of 397 (earlier, 261/150 was a smaller trial set).
- The per-phase timings (18.7 s load, 19.9 s battle) were from the last trial only; the means over 12 are 19.3 s and 18.2 s.
- "30 files" of B0 series: 33. "x2 fits every file": now a computed rule, 0 violations in 241 files. "grid <-> screen": the screenshot check compares slot positions, not grid words. Test counts in results.md. The PR body's "137 files" and "520 assets".
- Every writer in `runs/experiments/battles/` that makes a measured file now goes through `common.write_new` (exclusive create, versioned name in a loop); append-only logs and jsonl are the only other writers. `tests/test_battle_trials.py::test_every_writer_survives_a_second_call_in_the_same_stamp` calls the table, compare/`write_new`, half-round-log and screenshot writers twice in one STAMP.
