# run-exp-cellauto-rule

H04 open item 1 (the Cellular Automata easter egg's rule), asked by ic2-research on 2026-10-09 after the 0x456969 read. A static read plus an
offline check against the existing Wine screenshot. No new game run, and no new saves or screenshots.

- `disasm_range.py` → `tcellauto_456668.asm`: `TCellAuto_InitializeForm` (0x456668), `TCellAuto_NewPattern` (0x456744),
  `TCellAuto_SaveBMP` (0x4569c0) and `TCellAuto_OK` (0x456a70), as a capstone 5.0.7 linear sweep of `Imperial Conquest 2.exe` (read-only; its SHA-256 starts `9d753d5d`).
- `check_cellauto.py` → `cellauto_check.json`: it models the decoded rule and drawing, finds the canvas in `FI_b1_05_cellauto_N.png`, masks the
  "New structure" tooltip, fits the 10-entry table depth-first row by row, and redraws all 400 rows to compare them with the screen.
- Inputs: `FI_b1_05_cellauto_N.png` (after one N press) and `FI_b1_04_cellauto.png` (before), from `FI_batch1_screenshots.tar.gz` in release
  `run-exp-feature-inventory`. Their SHA-256 are in `../run-exp-feature-inventory/MANIFEST-batch1.txt` and match.

## SaveBMP in Wine (2026-10-09, after promotion at research 8c46579; ic2-research request for the player)

- `save_bmps.py` → `save_bmps-20261009-134302.jsonl` (N, Save, N, Save at seed 12345) and `save_bmps-20261009-134435.jsonl`
  (Save before N; then SEED.TXT = 12345, N, Save; SEED.TXT = 777, N, Save). Every new `ca*.BMP` is copied out under a new name.
- `probe_save_before_n.py` → `save_before_n-20261009-134535.jsonl`: Save before N writes nothing anywhere in the prefix, and shows no popup.
- `trace_save_before_n.py` → `trace_excerpt-20261009-134727.txt` (WINEDEBUG=+seh,+file; the full trace is in the release): no file call
  and no exception on Save before N; on N, SEED.TXT is read and SEED.LOG appended; on Save after N, `CreateFileW("ca1102211003.BMP")`, a relative
  name resolved to `C:\IC2\`.
- `mem_cellauto.py` → `mem_cellauto-20261009-134836.jsonl`: the CellAuto form (global 0x4A0B9C), with `Image1.Picture.Graphic` nil at open
  and after the pre-N Save, a TBitmap after N; table `1 1 0 2 2 1 1 0 0 3` after N. The logged class name has an off-by-one read
  (`\x07TBitma`: the length byte, then 6 characters).
- `analyze_bmp.py` → `bmp_check_1_seed12345.json`, `bmp_check_2_seed777.json`: header fields, painted pixels against the model, unpainted run
  ends against the previous file.
- Binaries (BMPs, screenshots, the full trace): release `run-exp-cellauto-rule`, SHA-256 in `SAVES.sha256`.
