# run-exp-end-of-game: the original's End of Game screens (T138)

Tracked text outputs of the experiment of `docs/tasks/end-of-game-screens.md`; finding `findings/2026-10-05-end-of-game-screens.md`. Scripts: `runs/experiments/end_of_game/`.
Binaries (saves, autosaves, staged inputs, screenshots) are in the GitHub release `run-exp-end-of-game` as `batch-b1.tar.gz` ... (hashes in `MANIFEST-*.txt` and `SAVES.sha256`; `fetch_archive.py` restores `artifacts/run-exp-end-of-game/`).

| file | what |
|---|---|
| `code_extract_end_of_game.txt`, `.v2.txt` | the decompiled functions the finding cites, with the dump's line numbers (v2 adds `FUN_00451b40`, `TPremierForm_NewPlayer/NewNation`; the audit reads the newest) |
| `staging_log.tsv` | every staged save: source and result hash, the declared byte ranges, the operations |
| `states_b*.jsonl` | game-memory readings (calendar, human seats, fall fields of the seats) at each step of a scenario |
| `ocr_b*.jsonl` | the window's OCR (psm 6 and 4), its controls and the label strings found in game memory |
| `ocr_labels*.jsonl` | per-label OCR of every captured window (the label rectangles of the form resource) |
| `single_b*.log`, `two_b*.log`, `menus_b8.log`, `base2.log` | run logs (append-only); b1/b2 one human, b2-b6 two humans (b2 and b4 are partial or superseded runs, kept), b7 full-ownership victory and victory with 250 BC, b8 menus after the game ends |
| `claims_audit_output*.txt` | the audit's output (every run writes a new version) |
| `SAVES.sha256`, `MANIFEST-*.txt` | SHA-256 of every binary and of each release archive |

Partial runs kept (rule 6): `EOG2_debt_gaul_b2` (the script stopped after OK), `EOG2_y250_both_b3/b4` (the second human's turn was not handled, then the OK check was fooled by the second window), `EOG_abdicate_b1`, the first Abdicate runs (a 3 s snapshot; the timeline run is b2).
