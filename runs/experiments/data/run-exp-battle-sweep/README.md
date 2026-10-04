# run-exp-battle-sweep: data folder notes

- `EXES-sha256-label-correction.txt`: the git label in `EXES-sha256.txt` was a blob hash; corrected there (old file kept).
- `trials.jsonl` line 1 (`hi-hi-one_s1_r1`, the first live trial, run before the runner's record schema settled) is **kept as written**:
  it uses the obsolete key `result_text` (the OCR of the Battle ended box; later rows call it `result_text_ocr`), has no `result` and
  `battle_ended_shot`, and its dialog `shot` is an absolute path in the Wine work folder (`~/ic2-work/shots/dialog-Offer_of_peace-1791098296.png`),
  not a file kept with the artifacts. Rows 2 onward share the final schema. The screenshot is copied to artifacts/run-exp-battle-sweep/shots/
  and the release as `hi-hi-one_s1_r1_dialog-Offer_of_peace-1791098296.png` when it still exists (see the PR thread).
- `sweep-table-20261004-092739.csv` is a near-empty table written by a run that crashed on a missing key (fixed); kept.
