# Cellular Automata SaveBMP (H04 item 2): a 24-bit bottom-up BMP of 300 × 400 named `ca<rule>.BMP` in the game folder. Nothing is written before the first N, and run ends keep the previous pattern's pixels. The seed build makes N repeatable

**Status:** draft from `ic2-conquest`, awaiting promotion. It settles the last open part of H04 item 2 (research `8c46579`, "Not established" of `2026-10-09-cellular-automata-rule-h04.md`), at ic2-research's request for the player. It also corrects two points of that draft (below).

**Tags:**
- `[confirmed]` (Wine): read from the saved files, game memory and a Wine file trace.
- `[confirmed: decompile]`: capstone disassembly; excerpts in the data folder.
- `[derived]`: inferred, not checked.

## Answer

### 1. The file format `[confirmed]` (Wine)

**Every file has the same header** (`bmp_check_*.json`):
- `BM`, file size **360,054** bytes, pixel data at offset 54;
- BITMAPINFOHEADER (40 bytes): **300 × 400, height positive (bottom-up)**, 1 plane, **24 bits per pixel, BI_RGB (no compression)**;
- image size 360,000 (900 bytes per row, no padding needed); resolution 0 × 0; clrUsed 0, **no palette**.

The pixels are the four state colours as RGB: `ffffff`, `ff0000`, `0000ff`, `008000`.

**Display dependence** `[derived]`:
- The bitmap is a Delphi 2 `TBitmap`, which has no PixelFormat property (that came with Delphi 3). It is a device-dependent bitmap, so the saved depth may follow the display.
- Under Wine on Xvfb at 24-bit depth it is 24 bpp. A desktop at 256 colours or 16-bit may write another depth.
- Added to the player's `run-exp-desktop-palette/STEPS.md`.

### 2. Before the first N there is no bitmap, so Save writes nothing. The first bitmap starts white `[confirmed]` (Wine)

- **Game memory** (`mem_cellauto-20261009-134836.jsonl`): `Image1.Picture.Graphic` (form global `0x4A0B9C`, then `+0x1BC`, `+0xAC`, `+4`) is **nil** when the window opens and after a Save click, and a `TBitmap` after N.
- **No file is written** before N. Two Save clicks wrote nothing anywhere in the prefix and opened no box (`save_bmps-20261009-134435.jsonl`, `save_before_n-20261009-134535.jsonl`). A `WINEDEBUG=+seh,+file` trace of that click shows **no file call and no exception** (`trace_excerpt-20261009-134727.txt`).
- `TPicture.SaveToFile` (0x41b9c8) calls the graphic's SaveToFile only when the graphic is non-nil `[confirmed: decompile]`.
- **The bitmap is made at the first draw:** `TImage.GetCanvas` (0x42bb44) creates a TBitmap of `Image1`'s Width × Height (300 × 400) when the picture is empty `[confirmed: decompile]`. So the bitmap made in `InitializeForm` does not survive as the picture: in memory the picture is empty at open. Why the assignment at 0x41b940 leaves it empty is not traced.
- **Its initial contents are white:** in the first file after the first N (`ca1102211003.BMP`), all **1,204 unpainted run ends are `ffffff`**. All 118,796 painted pixels match the model, 0 mismatches.
- **`Image1` is invisible** (form property `Visible = False`). The bitmap is an off-screen copy: the screen shows only the form canvas, which N clears to white. Only the saved file shows the run ends' leftover contents.

### 3. The content carries over between N presses `[confirmed]` (Wine)

- **The test:** N at seed 12345, then Save; then N at seed 777, then Save (`ca1203011231.BMP`).
- **The second file:** all 96,132 painted pixels match the model, and **all 23,868 unpainted run ends equal the first file's pixel at the same place** (`bmp_check_2_seed777.json`): red 11,538, blue 11,885, white 445.
- **This pattern uses green** (sum 9 → 3; 25,990 px), which the screenshot of the earlier draft did not show.

### 4. The file name and the folder `[confirmed]` (Wine)

- The name is exactly **`ca` + the 10 table digits + `.BMP`**: `ca1102211003.BMP` with the table read from memory as `1 1 0 2 2 1 1 0 0 3`.
- It is opened as a relative name (`CreateFileW(L"ca1102211003.BMP")`, create-always), so it **lands in the current directory**. Under the harness that is the game folder `C:\IC2\`, even after a File > Open from another folder.
- A second save with the same rule overwrites the file.

## Corrections to `2026-10-09-cellular-automata-rule-h04.md` (research `8c46579`)

- **"SEED.TXT does not make a pattern repeatable" is wrong for the seed build.**
  - `patches/seed_patch.py` sends `System.Randomize` itself through the SEED.TXT cave, and its note lists 0x456759 (the CA's call) as the second caller.
  - So in `Imperial Conquest 2 fast rollingsave seed.exe` every N press reseeds from SEED.TXT and logs a line to SEED.LOG (`trace_excerpt-…`). At a fixed seed, every N gives the **same** rule. Seed 12345 gave `1102211003` in three processes, and the same file hash `d3efe808…` (`SAVES.sha256`).
  - The original exe reseeds from the clock `[derived]`.
  - The rule fitted from the 2026-10-08 screenshot (`1 1 0 2 2 1 1 · · ·`) is this same seed-12345 rule.
- **The saved bitmap is not "made in InitializeForm".** At open the picture is empty, and the saved bitmap is the one `TImage.GetCanvas` makes at the first draw (above).

## Evidence

- **Data:** `runs/experiments/data/run-exp-cellauto-rule/`:
  - scripts `save_bmps.py`, `probe_save_before_n.py`, `trace_save_before_n.py`, `mem_cellauto.py`, `analyze_bmp.py`;
  - logs `save_bmps-20261009-134302.jsonl`, `save_bmps-20261009-134435.jsonl`, `save_before_n-20261009-134535.jsonl`, `trace_excerpt-20261009-134727.txt`, `mem_cellauto-20261009-134836.jsonl`, `bmp_check_1_seed12345.json`, `bmp_check_2_seed777.json`;
  - `SAVES.sha256`, `README.md`.
- **Release** [`run-exp-cellauto-rule`](https://github.com/diegoami/ic2-conquest/releases/tag/run-exp-cellauto-rule):
  - `20261009-134435_1_N_seed12345_ca1102211003.BMP` and `20261009-134435_2_N_seed777_ca1203011231.BMP` (the cited pair);
  - the files of the first run `20261009-134302_*`;
  - screenshots `cellauto_*`, `save_before_n_*`, and the full trace `trace-20261009-134727.log`.
- **Builds:** `Imperial Conquest 2 fast rollingsave seed.exe` (the harness default); Wine 9.0, Xvfb 1280 × 1024 × 24. The start position is `saves/run0-start-AUTO0720-seed12345.SAV` (only to get a running game; the CA reads no game state).

## Not established

- **The depth on a desktop** at 256 colours or 16-bit: asked of the player in `run-exp-desktop-palette/STEPS.md`.
- **The original (clock) exe's CA under Wine:** not run. Its N presses should differ every time.
- **Why the picture is empty at open** although `InitializeForm` assigns a 300 × 400 bitmap (0x41b940 not traced further).
