# Unit-map selection rendering in the original IC2 (issue #1010)

**Status:** draft; awaiting intake to `imperial-conquest-2-research` (issue #1010, v0.5.3). Player's handover 2026-10-12 evening lists this experiment as item 5 (selection frame capture). The research repo's canonical report will be at `docs/reports/2026-10-12-unit-map-selection-rendering.md` after intake.

**Tags:** `[P]` played in Wine; `[derived]` from screenshot pixel analysis and memory reads.

**Data:** `runs/experiments/data/run-exp-unit-map-selection/` (runner `sel_capture.py`, logs `sel_capture-<stamp>.log`, results `sel_results-<stamp>.json`, `SAVES.sha256`, `README.md`); screenshots and saves in release `run-exp-unit-map-selection` (https://github.com/diegoami/imperial_conquest_2/releases/tag/run-exp-unit-map-selection). Fast rollingsave seed exe (patched), Wine 10.0, no seed (loading does not reseed; the save carries its own RNG state). One fresh Wine process per unit type; the reference save is `saves/fleet-port-antium-0734.SAV` (turn 734, 270 BC Spring, Rome with armies at (101,45)/(102,45)/(102,44), fleet 2 at (101,46), 16 cities).

Screenshots: all named `sel_<stamp>_<case>_<type>.png` in the release, cited by bare filename below.
SHA-256 of each binary in `runs/experiments/data/run-exp-unit-map-selection/SAVES.sha256`.

## Answer

### Army selected (`sel_20261012-203220_army_selected.png`, SHA-256 `617968595e103ff455a65a4fcc8f51ef5ab69372689c1bd01ff257058eb5deec`)

- **Frame shape:** No frame is drawn around the tile. Border pixels of the unit tile (outer 8-pixel ring) are identical between the selected and unselected screenshots; no rhombus, diamond or other outline is visible `[P][derived]`.
- **Frame colour:** None (no frame drawn).
- **Frame size:** N/A.
- **Marker colour change:** Yes. The interior of the army marker tile shifts from a warm reddish-brown (unselected mean RGB 0.247, 0.058, 0.287) to a greenish colour (selected mean RGB 0.188, 0.673, 0.148) `[P][derived]`. The green channel roughly triples.
- **Blinking:** The selection state alternates with a visible on/off blink. Comparing `army_selected.png` (frame 1) with `army_frame2.png` (300 ms later) and `army_frame3.png` (600 ms after selected): `selected` == `frame3` (SHA-256 match, 0 pixel diff), `selected` vs `frame2` differs by 98 pixels across the 1280x1024 screen (7.4e-05 of pixels). The blink therefore cycles between two states roughly every 300 ms, returning to the "frame 1" appearance in the subsequent capture `[P][derived]`.

### Fleet selected (`sel_20261012-203220_fleet_selected.png`, SHA-256 `7031080ea8ad6cb5a9b25758d635b81bde5abf9b6837dfe1d6ba6565d1723b08`)

- **Frame shape:** No frame is drawn around the tile. Border pixels of the fleet tile are identical between selected and unselected screenshots `[P][derived]`.
- **Frame colour:** None (no frame drawn).
- **Frame size:** N/A.
- **Marker colour change:** Yes. The fleet marker interior shifts from a warm reddish tone (unselected mean RGB 0.274, 0.119, 0.406) to a greenish colour (selected mean RGB 0.252, 0.645, 0.123) `[P][derived]`. The green channel increases roughly 5x.
- **Blinking:** Identical blink pattern to the army. `fleet_selected` == `fleet_frame3` (SHA-256 match, 0 pixel diff); `fleet_selected` vs `fleet_frame2` differs by 98 pixels (7.4e-05 of pixels) `[P][derived]`.

### Town selected (`sel_20261012-203220_town_selected.png`, SHA-256 `9bf50cb1ddcf95a8a12fd7ed4b37df8d2f9ca2676d8a76d762ef20920a0cfac1`)

- **Frame shape:** No frame is drawn around the tile. Border pixels of the city tile are identical between selected and unselected `[P][derived]`.
- **Frame colour:** None (no frame drawn).
- **Frame size:** N/A.
- **Marker colour change:** The mean RGB shift is smaller for the town (unselected mean RGB 0.046, 0.157, 0.953; selected mean RGB 0.046, 0.157, 0.953 — identical in the crop at centre 545,366). However, the `town_selected` vs `town_unselected` full-image comparison shows 12,864 pixels differ (0.98% of the screen), which corresponds to the city information panel appearing in the unit map's right-hand panel when a city is selected. Within the tile crop, the city's colour is already blue-white (loyalty 100?) and does not change visibly `[P][derived]`.
- **Blinking:** Identical blink pattern: `town_selected` == `town_frame3` (SHA-256 match); `town_selected` vs `town_frame3` 0 pixel diff; `town_selected` vs `town_frame2` differs by 98 pixels `[P][derived]`.

## Open / Not established

- The 98-pixel blink alternation was observed on all three unit types at 300 ms intervals. The exact period of the blink cycle was not isolated (only 2 blink frames captured at 300 ms apart, plus a return-to-frame1 in frame3). The interval is approximately 300 ms.
- The selection frame in the prior reference (case d of `runs/2026-10-02-unit-map-mouse-orders-and-tax-range.md`: the diamond on the map tile disappears on Shift+X) was captured in the area map; this experiment captures the unit map view. No explicit frame shape (rhombus, diamond) was identified in the unit map.
- The marker colour change was observed for armies and fleets (large green-channel shift) but is subtle or absent for the town marker at the sampled tile.
- The blinking appears to be a global UI timer affecting all selected-unit types simultaneously, not per-unit.

## Comparison to the remake

The remake (`godot/MapViewer.cs:156-157 and :240, DrawSelection`) draws a 2-pixel circle (`DrawArc`, `SelectedColor`) around the selected city or unit and the marker keeps its own colour. The original IC2 unit map draws **no frame at all** around the selected unit tile. Instead, when a unit is selected, its marker colour shifts (green channel increases for armies and fleets), and a blinking on/off state cycles approximately every 300 ms affecting the selected unit's display.

The town selection shows the city info panel appearing (12,864-pixel screen change) but no border around the tile and no visible colour change within the tile crop.

A UI fix for the remake should either add a visible selection frame (rhombus or diamond matching the original's area-map selection indicator) or adopt the original's approach of a marker colour shift plus blink. The original shows no per-unit-type frame shape difference in the unit map itself.
