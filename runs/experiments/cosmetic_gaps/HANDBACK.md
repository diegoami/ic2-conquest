# Cosmetic gaps (#723): Sonnet hand-back, 2026-10-06

The Sonnet agent was killed by a Claude 5-hour quota reset (`429`, the 5h window exhausted at 02:42 UTC, resets
2026-10-07 05:14 UTC). I had committed and pushed b1 and was running batch b2's S1–S3 when the API rejected calls. No
finding, no claims audit, no tests written. Everything that was measured is in `runs/experiments/data/run-exp-cosmetic-gaps/`
and on the release `run-exp-cosmetic-gaps`.

## What was established before the kill (b1 = 4/4 plays ok, tracked)

- **T1 — empty-leader title**: `Imperial Conquest 2` at process start (the game window's `xdotool getwindowname`).
  ([confirmed]; play `CG_T1_b1b`, runs/experiments/data/run-exp-cosmetic-gaps/plays_b1b.jsonl, screenshot in the b1 release).
- **T2 — named-leader title**: format `<Nation>'s turn   (<leader>)` after the leaders form (Carthage, Hannibal). T2 also
  confirmed T1's spacing through the play with a known leader.
- **T3 — colour toggle**: the `TAreaMap` `sb_areatog` byte flips `1 → 0 → 1` across two clicks (both tooltip-proven). The
  drawn-marker cleared-on-two-clicks claim was not tested.
- **T4 — window positions**: `StoreFormPositions` writes the four-window geometry; the load restore was verified by
  moving a window, saving, and reading the saved bytes.

## What was started but not finished (b2, partial)

- **S1 — army move → SOUND1.WAV**: confirmed by strace (the strace `openat` of `WAVS/SOUND1.WAV` was captured at the
  move's step mark). ([confirmed]).
- **S2 — fleet move**: failed (`plays_b2.jsonl` shows the error; `wav_opens_CG_S2_b2.txt` is the strace extraction);
  b2a was the retry and is in the same jsonl.
- **S3 — city capture / file-open**: failed; b2a was the retry and is in the same jsonl.

The remaining seven sound mappings (S2–S10), the Buy supplies caption (UA01, own and foreign city), and any second-opinion
plays for M04/M05/A01 stay in the to-do list.

## State left on disk (resume from here)

- Branch `experiment/cosmetic-gaps` is pushed; last commit `cd8870f` ("b1 done: T1-T4"). The uncommitted `runs/experiments/
  data/run-exp-cosmetic-gaps/plays_b2.jsonl` and the modified `scenarios.py`/`SAVES.sha256`/`toolbar.log` were NOT in the
  last commit. I commit them now as `partial b2 evidence` (rule 6 — never lose a measured output); a future session
  continues from there.
- Release `run-exp-cosmetic-gaps` exists on GitHub; b1 archive is uploaded; b2 is not archived (the strace and jsonl are
  in `runs/experiments/data/`, not in `artifacts/` yet — see `archive_batch.py`).

## Process slips to report (the original one)

- The first run of T1 hit a hidden VCL `TApplication` window: `find_windows` returned two, one a 1×1 window that hid the
  real game window. `cg.main_wid` was patched to pick the visible one (filters `w[4] > 1 and w[5] > 1`).
- T1 first attempt (`b1`) unpacked `g.find_windows(...)` into four values instead of the expected three; the fix was
  `wid, _title = main_wid(g)` → `wid = main_wid(g)[0]`.
- `_screen_words` was used but not imported; the import was added.
- No process was killed by pattern; everything by pid or by Wine/Xvfb teardown.

## Decisions the player should make

- Whether to keep `experiment/cosmetic-gaps` as the resume branch or fold its runner into `experiment/refusal-texts`
  / `experiment/leaders-form` and start a fresh branch. The runner already imports `lib.py`, `eog.py`, `play_lib.py`,
  and the leaders-form `verified_reset`; it does NOT edit `harness/driver.py` (rule 1).
- Whether the partial b2 is worth resuming, or whether to start over from b1 with a tighter S1–S10 grid and the dialogs
  for UA01 (M04, M05, A01 already have b1 evidence; M06 needs b2/b3; UA01 needs a new batch).

## What I (the agent) did NOT do

- No `findings/2026-10-06-cosmetic-gaps.md`. No claims audit (the matching `claims_audit.py` in this experiment did not exist
  yet — the leaders-form audit was the model to copy). No `test_runner.py` / `test_claims_audit.py`. No tests, no audit
  outputs. Those are the next session's work, with the b1 evidence as the first claim.