# run-exp-cellauto-rule

H04 open item 1 (the Cellular Automata easter egg's rule), asked by ic2-research on 2026-10-09 after the 0x456969 read. A static read plus an
offline check against the existing Wine screenshot. No new game run, and no new saves or screenshots.

- `disasm_range.py` → `tcellauto_456668.asm`: `TCellAuto_InitializeForm` (0x456668), `TCellAuto_NewPattern` (0x456744),
  `TCellAuto_SaveBMP` (0x4569c0) and `TCellAuto_OK` (0x456a70), as a capstone 5.0.7 linear sweep of `Imperial Conquest 2.exe` (read-only; its SHA-256 starts `9d753d5d`).
- `check_cellauto.py` → `cellauto_check.json`: it models the decoded rule and drawing, finds the canvas in `FI_b1_05_cellauto_N.png`, masks the
  "New structure" tooltip, fits the 10-entry table depth-first row by row, and redraws all 400 rows to compare them with the screen.
- Inputs: `FI_b1_05_cellauto_N.png` (after one N press) and `FI_b1_04_cellauto.png` (before), from `FI_batch1_screenshots.tar.gz` in release
  `run-exp-feature-inventory`. Their SHA-256 are in `../run-exp-feature-inventory/MANIFEST-batch1.txt` and match.
