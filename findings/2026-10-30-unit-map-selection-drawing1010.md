# Unit-map selection: the selected tile is image 12 drawn with SRCERASE (tile inverted, black rhombus line), for any selected cell, with no blink

**Tag:** [confirmed]. The drawing routine is read in the decompile and the image extracted from the EXE's form resource. Five
controlled Wine captures match the resulting per-pixel model on all 1,024 pixels of the tile, for an army, a fleet, a town, a
capital and a foreign town.
**Task:** imperial_conquest_2#1010 (selection rendering), delegated by research on 2026-10-30.
**Supersedes** the open points of research's `2026-10-12-unit-map-selection-rendering.md`: town selection, recolouring, exact
geometry and colour, blink, and zoom.

## Answer

1. **The routine.**
   - `TUnitMap_SelectUnit` (0x4466CC) stores the selected cell (`+0x21A`) and calls the nested `FUN_004465a8` before it looks
     at what the cell holds. So **the same drawing runs for a town, an army or a fleet**, own or foreign.
   - If the cell lies in the visible part of the unit map, `FUN_004465a8`:
     1. takes **image 12 of `TerrainList`** (the image list whose images 0–11 are the terrain codes);
     2. sets the canvas `CopyMode` to **0x00440328 (`SRCERASE`: destination = source AND NOT destination)**;
     3. draws the image at the tile's position, `((x − viewX)·32, (y − viewY)·32 + 30)`;
     4. sets `CopyMode` back to `SRCCOPY` (0xCC0020).

   (dump :46487–46531 and the function at 0x4465A8)
   - `TUnitMap_PaintForm` re-runs `SelectUnit` after every repaint, so the selection is redrawn with the map.
   - `TUnitMap_EndUMSelection` erases it by repainting the tile (`TUnitMap_PrintMapSquare`) and clearing the selection words.
   - A selected cell scrolled out of view is not drawn.
2. **The image.** `TerrainList` in the `TUnitMap` form resource holds 13 images of 32×32 (a 128×128 8-bit bitmap plus an
   all-zero, i.e. fully opaque, mask). **Image 12** is white with a **black rhombus outline**:
   - its four corners are at the midpoints of the tile's edges (rows 0 and 31, columns 0 and 31);
   - the line is 3–4 pixels thick;
   - 240 pixels are black and 784 white.
3. **What the player sees, per pixel.**
   - On the 784 white image pixels, the **tile's own colour is inverted**: blue sea turns yellow, the purple Rome army tile
     turns light green, and the marker icon is inverted too.
   - On the 240 rhombus pixels the result is **black**.
   - So the "bright yellow rhombus" of the October draft is the inverted sea and land of the tile around and inside a black
     rhombus line. The marker **is recoloured** (inverted).
4. **No blink.** The game has no timer of its own: the only `SetTimer` in the program is the VCL hint timer (`FUN_00424b7c`,
   window 0). In the captures, the tile is identical at 0.4 s, 1.4 s and 2.9 s after the click. The 98-pixel differences of
   October were the horizontal scrollbar, as research found.
5. **Zoom.** The unit map has one tile size: 32 px, a constant shift by 5 in `PaintForm`, `PrintMapSquare` and the drawing
   routine. A larger window shows more tiles, not larger ones.

## Captures

The seed build under Wine ran one fresh process per case on `saves/fleet-port-antium-0734.SAV` (Rome, 270 BC, seed 12345).
Each case clicks the cell once, with no unit selected before. Columns: the cell; the tile's pixel origin; the pixels equal to
the model (image-12 white → the "before" pixel inverted, black → black) at 0.4 s, 1.4 s and 2.9 s; and whether the three
frames are equal. From `recheck-v2.json`.

| Case | Cell | Tile origin | Model match /1024 (t0, t1, t2) | Frames equal |
|---|---|---|---|---|
| own army 0 | (101,45) | (624,446) | 1024, 1024, 1024 | yes |
| own fleet 2 | (101,46) | (624,478) | 1024, 1024, 1024 | yes |
| own town Fregellae | (104,44) | (720,414) | 1024, 1024, 1024 | yes |
| own capital Rome | (101,43) | (624,382) | 1024, 1024, 1024 | yes |
| foreign town Caere (Gaul) | (99,42) | (560,350) | 1024, 1024, 1024 | yes |

`captures-v1.json` holds the same screenshots measured with a tile origin one pixel to the right: 884–929 matches, the
offset's error, kept as measured. The October army capture (release `run-exp-unit-map-selection`, `army_unselected` vs
`army_selected`, `frame2` and `frame3`) also matches the model on 1,024 of 1,024 pixels at (624,446). The October **town**
case clicked (101,47), which is not a town (Antium is at (102,46)), so nothing was selected; that is why its screenshot showed
news.

## What this does not establish

- **Native Windows rendering.** Wine implements `SRCERASE` as the GDI definition. On a palettized (256-colour) Windows
  display, the inverted colours would go through the system palette and could differ in shade.
- **Selection by keyboard, or after a scroll that brings a selected cell back into view** (the code redraws it on the next
  repaint; not captured).
- **The area map's cursor** (`TAreaMap_UnitMapCursor`), a different routine.

## Evidence

- Scripts: `runs/experiments/selection1010/capture.py` (now with the corrected origin) and `recheck.py`.
- Data: `runs/experiments/data/run-exp-selection1010/` (`captures-v1.json`, `recheck-v2.json`, `SAVES.sha256`,
  `environment.jsonl`).
- Screenshots: 20 PNGs `v1-<case>-{before,t0,t1,t2}.png` in `artifacts/run-exp-selection1010/` (release
  `run-exp-selection1010`, pending the player).
- EXE resource: `Imperial Conquest 2.exe` (`9d753d5d…`), form `TUnitMap`, component `TerrainList`, the `Bitmap` property.
- Save: `saves/fleet-port-antium-0734.SAV` (start only; no save written).
