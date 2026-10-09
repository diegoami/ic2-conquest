# The Cellular Automata easter egg (H04) is a random 4-state totalistic 1D automaton: 300 cells, 400 generations, a new 10-entry rule at every N, 12 red cells in the middle as the seed

**Status:** draft from `ic2-conquest`, awaiting promotion. It answers open item 1 of `2026-10-08-cellular-automata-easter-egg-h04.md` (the rule) and most of open item 2 (what SaveBMP writes). ic2-research asked for it on 2026-10-09, after placing the 0x456969 read in `TCellAuto_NewPattern` (research `010c9c2`).

**Tags:**
- `[confirmed: decompile]`: capstone disassembly; the excerpt is tracked (`tcellauto_456668.asm`).
- `[confirmed]` (Wine): one N press redrawn pixel for pixel from the decoded model.
- `[derived]`: the meaning of the RTL and VCL calls, identified by their arguments and use, not by symbols.

## Answer

### The rule `[confirmed: decompile]`, checked in Wine

- **Cells and states:** a row of **300 cells** (indices 0-299) with **4 states**. Two boundary cells, −1 and 300, always stay 0.
- **The rule table is random:** each press of **N** fills a 10-entry table `T[0..9]` with `Random(4)` (0x4567c5 to 0x4567df, table at form field `+0x688`), after `Randomize` (0x456759) `[derived]`. So every press gives a new rule from **4^10 = 1,048,576**. Because `Randomize` reseeds from the clock, `SEED.TXT` does not make a pattern repeatable `[derived]`.
- **The seed row:** all 0, except **cells 144-155 (12 cells) = state 1** (0x4567e1 to 0x456810).
- **The update:** a totalistic radius-1 rule, `next[i] = T[old[i−1] + old[i] + old[i+1]]` for i = 0-299, applied to a copy of the row (`+0x42E`) (0x456946 to 0x45699b). The sum runs from 0 to 9, hence 10 entries.
- **400 generations** (rows 0-399), the seed row included (0x45699d: the counter runs to 0x190). The cursor is the hourglass (−11) while it computes, then back to the default.
- **Colours** (form fields `+0x1C0..+0x1CC`, set in `InitializeForm`): state 0 white `ffffff`, 1 red `ff0000`, 2 blue `0000ff`, 3 green `008000`. The code stores them as Delphi TColors `0xFFFFFF`, `0xFF`, `0xFF0000`, `0x8000`.

### Drawing `[confirmed: decompile]`

- **The window's client area is 300 × 428:** a 28-px panel with N, Save and X, then the canvas. It is centred on the screen. It opens blank: `FI_b1_04_cellauto.png` shows only the form colour `f5f5f5` over all 300 × 400 canvas pixels.
- **N first clears the canvas to white** (`Rectangle(0, 28, 300, 428)`). Row `g` is then drawn at y = 28 + g, as runs of equal state:
  - a single cell with `Pixels[x, y]`;
  - a longer run with `MoveTo(start)` / `LineTo(end)`. **`LineTo` leaves out its end point, so the last cell of every run longer than 1 stays white**, whatever its state. The same happens at the right edge (cell 299).
- **Every row is drawn twice:** once on the form canvas and once on the bitmap behind `Image1` (300 × 400, made in `InitializeForm`), at y = g.

### The Wine screenshot `[confirmed]`

- **What was checked:** `FI_b1_05_cellauto_N.png` (one N press), canvas at screen (493, 355). The model is the rule plus the drawing above (`check_cellauto.py`, `cellauto_check.json`):
  - row 0 matches on all 300 pixels: cells 144-154 red, and 155 white (the end of its run);
  - fitting `T` row by row gives **one table only: `T = 1 1 0 2 2 1 1 · · ·`**. The sums 7-9 never occur in this pattern, so `T[7..9]` and state 3 (green) are not seen;
  - **redrawing all 400 rows gives 0 mismatching pixels** over the 118,742 pixels outside the 1,258 hidden by the "New structure" tooltip (box x 4-77, y 2-18 of the canvas).
- **This pattern:** row 1 is red, with blue at 145-154. After a short transient the rows alternate blue / red, because `T[3] = 2` and `T[6] = 1`, with a 15-cell band in the middle in opposite phase. That is the stripe in the screenshot.

### SaveBMP `[derived]`, from the decompile

- **The file name is `ca` + the 10 table digits + `.BMP`**, for example `ca1102211xyz.BMP` for the pattern above. It is built from the literals `ca` and `.BMP` at 0x456a64 / 0x456a6c and the digits `'0' + T[i]`, then passed to `Image1.Picture.SaveToFile` (0x456a38).
  - It is a relative name, so the file goes to the current directory.
  - The name records the rule, so a saved pattern can be regenerated: the seed row is fixed.
- **Its content is `Image1`'s 300 × 400 bitmap.** It is never cleared in `NewPattern`, unlike the form canvas, so the unpainted run ends keep whatever that bitmap held before: its initial contents at the first press, the previous pattern's pixel after that.

## Evidence

- **Data:** `runs/experiments/data/run-exp-cellauto-rule/`: `disasm_range.py`, `tcellauto_456668.asm`, `check_cellauto.py`, `cellauto_check.json`, `README.md`.
- **Screenshots:** `FI_b1_05_cellauto_N.png` and `FI_b1_04_cellauto.png` (`FI_batch1_screenshots.tar.gz`, release `run-exp-feature-inventory`; SHA-256 in `runs/experiments/data/run-exp-feature-inventory/MANIFEST-batch1.txt`, re-checked). No save is involved: the easter egg reads no game state. Only form fields are touched in the four routines.
- **Exe:** `Imperial Conquest 2.exe`, SHA-256 starting `9d753d5d` (full hash in `run-exp-unit-icon-resources/imagelists.json`).

## Not established

- **The saved BMP's pixel format and its initial contents:** it is a device-dependent `TBitmap`, so the format likely follows the screen depth. No file was saved and read.
- **The identity of the RTL and VCL helpers** (`Randomize` 0x402744, `Random` 0x40284c, `Rectangle` 0x419ed4, `Pixels` 0x41a0e8, `MoveTo` 0x419e70, `LineTo` 0x419e38, the bitmap's width and height setters): they are identified by their arguments and use. The screenshot fit supports the drawing reading, including the missing run ends.
- **A pattern that uses green** (sums 7-9) was not drawn.
- **Open item 3 of H04** (whether the clone keeps the `CAncell` button) is the clone owner's decision, not data.
