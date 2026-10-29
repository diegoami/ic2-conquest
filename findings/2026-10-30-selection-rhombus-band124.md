# The selection rhombus's black pixels are taxicab distance 14 to 17 from the pixel-corner centre (15.5, 15.5)

**Tag:** [confirmed] from the EXE's form resource. `TerrainList` image 12 in the `TUnitMap` form of the pinned
`Imperial Conquest 2.exe` (`9d753d5d…`) was compared pixel by pixel with every candidate rule. No image is reproduced here.
**Task:** research [#124](https://github.com/diegoami/imperial-conquest-2-research/issues/124), for imperial_conquest_2
T242/#1010, delegated to conquest on 2026-10-30. It refines `2026-10-30-unit-map-selection-drawing1010.md` ("240 black,
784 white, corners at the edge midpoints, 3–4 px thick").

## Answer

With pixel coordinates x, y = 0…31 (x to the right, y down, as drawn on the tile), a pixel of image 12 is **black exactly when**

    14 ≤ |x − 15.5| + |y − 15.5| ≤ 17

and white otherwise. The centre is the **pixel corner (15.5, 15.5)**, the middle of the 32 × 32 tile, not a pixel centre.
The distance then takes only whole values (1 for the four pixels around the middle), so the band is four whole
distances: 14, 15, 16 and 17. That gives **240 black and 784 white pixels**, which is the image exactly (0 missing, 0
extra).

**It is the only such rule.** I tried centres 15, 15.5, 16 and 16.5 on each axis independently, and every band [lo, hi] with
10 ≤ lo ≤ hi ≤ 23. Only (15.5, 15.5) with [14, 17] reproduces the image.
- With centre (16, 16), the band 14..17 gives 238 pixels: 29 black pixels missed and 27 extra, 56 wrong in all.
- With centre (16, 16), the band 15..18 also gives 238: 57 missed and 55 extra, 112 wrong in all.

(Corrected 2026-10-30: the first version said "29 / 57 of them wrong", counting only the missed pixels; research noted it.)

So both candidates from the T242 brief differ from the image on any whole-pixel centre.

**Row by row** (black runs as inclusive column ranges; the image is symmetric top to bottom and left to right):

| rows | black columns |
|---|---|
| 0 and 31 | 14–17 |
| 1 and 30 | 13–18 |
| 2 and 29 | 12–19 |
| y = 3…14 and 31 − y | (14 − y)…(17 − y) and (14 + y)…(17 + y) |
| 15 and 16 | 0–2 and 29–31 |

The rows 3–14 formula gives 11–14 and 17–20 for row 3, and 0–3 and 28–31 for row 14.

The line is 4 pixels wide in each row, except rows 15 and 16, where it meets the tile's edge and is 3 pixels: the "3–4 px" of
the 1010 finding. The diamond's corners touch the middle of each tile edge (columns 14–17 on rows 0 and 31; rows 15–16 on
columns 0–2 and 29–31).

## What this does not establish

- How the image is drawn: that part is the 1010 finding (SRCERASE, image 12 of `TerrainList`, drawn for any selected cell).
- Any other image in the list. Images 0–11 are the terrain tiles.

## Evidence

- Script: `runs/experiments/selection1010/band_rule.py`. It reads the image through `capture.image12()`, i.e. from the EXE's
  `TUnitMap` form resource, the `TerrainList` `Bitmap` property: 13 images, image 12 at grid cell (0, 3) of the 128 × 128
  bitmap, mask all opaque.
- Data: `runs/experiments/data/run-exp-selection1010/band-rule-v1.json`, holding the counts, the only match and the black runs
  of every row.
- No image is written by the script or kept in the repository.
