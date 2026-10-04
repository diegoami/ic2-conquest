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

## PR B fourth review
- **`b2_probe.py` End turn retry removed.** In `b2-verify-20261004-093600.log` the probe's retry fired (a no-sign timeout is not proof the first click did nothing: it may still be queued); the retry also gave no sign and the run aborted before its third phase. `b2-verify-20261004-093449.log` (earlier code, no retry) aborted the same way. The claims of B2 (memory = Save As block, slots and grid decode, slot positions on the screen, the icon check `b2-icons-20261004-111640.json`) rest on the completed run `b2-verify-20261004-093834.json`, whose two End turn clicks were each proven (`end_turn_proven attempt=1` twice, no `no_sign` line); neither earlier run wrote a phase after its second click. Nothing needed a re-run.
- **End turn clicks audit** (`grep` over `runs/experiments/battles/` and `harness/`): proven now: `Game.play_battle` (`end_turn_proven`), `b0_probe.end_turn_until_over` (its own proof loop, same rule), `common.battle_end_turn` (used by `b2_probe.py` and, since this review, by `b0_probe.cmd_savein`, whose three End turn clicks were blind `g.click(...)` with a 2.5 s pause: that is the file family of the B0 Save As probe; its recorded logs `b0-savein-*` were made with the old blind clicks, the saves it made are cited by the finding of B0 only for "block 12 present", which does not depend on the click). Not battle clicks and left as they are: `Game.end_turn` (strategic End turn, documented reclick-after-8-s, `reclick=False` available). Nothing else clicks End turn.
- `b2-icons-20261004-111617.json` is the first try of the icon check (it hashed the whole 32 px tile, whose border shows the neighbour's colour, so one word mapped to two hashes); kept. `b2-icons-20261004-111640.json` hashes the inner 26 x 26 pixels and is the one cited.

## PR B5 (follow-ups of PR #36's last review)
- R4: `b0_probe.end_turn_until_over` now uses `Game.battle_progress_mark()` (flag, titles, BATTLEnn count and the half-round counter), so "the same rule" above is true from this PR on. **The `b0-savein-*` and the B0 gate logs (`runs/experiments/data/run-exp-battle-probe/`) predate this change** (and the savein logs predate even the proven clicks): they were made with the earlier proofs.
- R5: `b2-analysis-20261004-112837.json` (and `-112840`, a second identical run) carries `all_battle_saves[...]["violating_files_by_scenario"]`: the 14 grid-violating B3 files are c5: 5, c6: 5, d5: 3, d6: 1 (all in B3's resumed series).

## Where the saves and screenshots are (releases; the 1000-asset limit)
- `run-exp-battle-sweep` holds **1000 assets, GitHub's per-release limit** (HTTP 422 "file_count limited to 1000 assets per release" on the 1001st): the 521 assets of PR #35/#36 and the first 479 saves of the sweep (the trials up to `li-lc-one_s1_r1_BATTLE05.SAV`), loose. Nothing was deleted or replaced.
- `run-exp-battle-sweep-b5` (created by `release_sync.py` when the limit was hit, before the name `-2` was asked for): the **sweep saves from there on, one `.tar.gz` per batch** (`b5-saves-<batch>-<stamp>.tar.gz`, 19 archives) and the sweep's screenshots, loose. Members and their SHA-256: the tracked `release-manifest-<stamp>.json` files (one per archive set); per-file SHA-256 also in `SAVES.sha256`.
- `run-exp-battle-sweep-2`: from the B8 batch on (`b8-saves.tar.gz` + `MANIFEST-b8.txt` tracked here, and the B8 screenshots loose). `release_sync.py` skips every name already loose in any of the three releases or listed as a member in a manifest. A save is therefore cited by its bare file name and found by that name in the loose assets of `run-exp-battle-sweep`, or as a member of the archive the manifest names.
- `b2-analysis` files made after the sweep include the sweep's own series in "B4 trials and other sweep series".

## B8 notes
- `b8-ladder-2026*.jsonl` (the v1 run, 12 units per side): the defender's block is only 3 cells wide, so more than 9 defenders **share cells** (rows y = 9, 10, 11 ... overlap) and a shared cell shows one grid word for two units; `b8_analyze.py` and `b8_ladder.observe` ignore such units. The v1 run was stopped during `hc` (killed by its own time limit). `b8-ladder-v2-*.jsonl` (9 per side) is the dataset the thresholds come from. Both are kept.
- `b8-layout-20261004-192710.jsonl`: the layout run (tooltips, unit info, surrender box answered No, move phase, result box).

## PR #40 review fixes
- `b8-layout-20261004-192710.jsonl` `unit_info_click`: written by the first version of `b8_layout.py`, which recorded the click without checking that a panel opened. I looked at `b8_layout_unit_info_click_gaul_slot20.png`: it **does** show the Information panel ("Gaul's army / 4th Guards Battalion / Heavy infantry / Troops 5,900"), and the event's `popups` text holds the same words. The script now records `panel_shown` and refuses to continue without the panel. Files kept, nothing re-captured.
- Output files are always created exclusively (`common.write_new`, also for `Log` files, the B8 jsonl files and the release archives): a re-run in the same second gets a new name and never appends to or overwrites an earlier measurement.

## PR #40 round 2: target-choice wording
- `b5-targets-20261004-193033.csv` (kept) ranks the enemy a unit's word 9 first named **in the resulting snapshot** only; its numbers (664 events, nearest 664, uniquely nearest 147, fewest troops 507) are ranks in that snapshot, not the state when the AI chose. `b5-targets-20261004-194118.csv` (new, `b5-summary-20261004-194118.json`) adds `prev_*` columns, ranks in the previous snapshot (nearest 602, uniquely nearest 97, fewest troops 546, same 664 events), with the limit that positions change during the move phase. The finding states both and draws no inference about the AI's rule. `claims_audit.py` now recomputes all of these from the `halfrounds-*.jsonl` logs, independently of `b5_analyze.py`, and checks the csv against that.
