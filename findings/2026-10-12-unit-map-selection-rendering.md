# Unit-map selection rendering in the original IC2 (issue #1010)

**Status:** draft; awaiting intake to `imperial-conquest-2-research` (issue #1010, v0.5.3). Player's handover 2026-10-12 evening lists this experiment as item 5 (selection frame capture). The research repo's canonical report will be at `docs/reports/2026-10-12-unit-map-selection-rendering.md` after intake.

**Tags:** `[P]` played in Wine; `[derived]` from visual inspection of the captured screenshots.

**Data:** `runs/experiments/data/run-exp-unit-map-selection/` (runner `sel_capture.py`, logs `sel_capture-<stamp>.log`, results `sel_results-<stamp>.json`, `SAVES.sha256`, `README.md`); screenshots and saves in release `run-exp-unit-map-selection`. Fast rollingsave seed exe (patched), Wine 10.0, no seed (loading does not reseed; the save carries its own RNG state). One fresh Wine process per unit type; the reference save is `saves/fleet-port-antium-0734.SAV` (turn 734, 270 BC Spring, Rome with armies at (101,45)/(102,45)/(102,44), fleet 2 at (101,46), 16 cities).

## Answer

### Army selected

Screenshot: `army_<stamp>_selected.png` (SHA-256 in `SAVES.sha256`).

Frame shape: [rhombus / diamond / other — fill from screenshot inspection]
Frame colour: [colour(s) — fill from screenshot inspection]
Frame size: [how thick, how many cells wide — fill from screenshot inspection]
Marker colour change: [yes / no; new colour — fill from screenshot inspection]
Blinking: [yes / no; interval — fill from frame2 vs frame3 comparison]

Notes:

### Fleet selected

Screenshot: `fleet_<stamp>_selected.png` (SHA-256 in `SAVES.sha256`).

Frame shape: [rhombus / diamond / other — fill from screenshot inspection]
Frame colour: [colour(s) — fill from screenshot inspection]
Frame size: [how thick, how many cells wide — fill from screenshot inspection]
Marker colour change: [yes / no; new colour — fill from screenshot inspection]
Blinking: [yes / no; interval — fill from frame2 vs frame3 comparison]

Notes:

### Town selected

Screenshot: `town_<stamp>_selected.png` (SHA-256 in `SAVES.sha256`).

Frame shape: [rhombus / diamond / other — fill from screenshot inspection]
Frame colour: [colour(s) — fill from screenshot inspection]
Frame size: [how thick, how many cells wide — fill from screenshot inspection]
Marker colour change: [yes / no; new colour — fill from screenshot inspection]
Blinking: [yes / no; interval — fill from frame2 vs frame3 comparison]

Notes:

## Open / Not established

- [List any unit type not captured, or any limitation such as static screenshots for blinking]

## Comparison to the remake

The remake (`godot/MapViewer.cs:156-157 and :240, DrawSelection`) draws a 2-pixel circle (`DrawArc`, `SelectedColor`) around the selected city or unit and the marker keeps its colour. The original IC2 [brief description of what was observed]. A UI fix would be: [proposal if it follows from the findings].
