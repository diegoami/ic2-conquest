# run-exp-refusal-texts: tracked measurements

Task `docs/tasks/refusal-texts.md`; finding `findings/2026-10-05-refusal-texts-and-conditions.md`; scripts `runs/experiments/refusal_texts/`; binaries in the release `run-exp-refusal-texts` (per-batch `batch-bN.tar.gz`, hashes in `MANIFEST-bN.txt` and `SAVES.sha256`).

| file | what |
|---|---|
| `call_sites.tsv` | every message-box call of the decompile: function, line, literal, box type, button word (`sites.py`) |
| `code_extract_refusals*.txt` | the decompiled functions the finding cites, first column = line of `all_app_functions.txt` (`make_extract.py`; `.v2` adds the two form-initialising functions and two helpers) |
| `literals_in_scope.tsv`, `class_sites.tsv` | every string literal of the `T*_*` functions with its category; calls per class (`scan_literals.py`, `class_table.py`) |
| `plays_bN.jsonl`, `ocr_bN.jsonl`, `play_bN.log` | one record per play (input, control and after save hashes, boxes, OCR), the per-box readings, the log; `bN` = the batch |
| `ocr_reread.jsonl` | a second, tighter OCR of every box screenshot (`ocr_reread.py`) |
| `staging_log.tsv`, `stage.log` | every staged save: source and result hash, the declared byte ranges, the operations |
| `SAVES.sha256`, `MANIFEST-*.txt` | SHA-256 of every save and screenshot, and of each batch archive and its members |
| `claims_audit_output*.txt` | the claims audit's outputs (never overwritten; the newest is the finding's) |

Plays that failed or were repeated keep their files: `F03` (b2; no refusal appeared because the fleet was next to a city, the next save step failed; replaced by `F03b`), `UA04` (b1, run twice: `.v2` files), `T02`/`CU01` first attempts in b2 failed on a click-budget bug (the budget is now per play) and were re-run in b3; `A01` shows a join that succeeded (replaced by `A01b` for the refusal); `TR3` shows a transfer that passed (replaced by `TR3b`).
