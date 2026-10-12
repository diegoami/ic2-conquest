# Unit-map selection rendering in the original IC2 (issue #1010)

**Status:** draft, awaiting intake to `imperial-conquest-2-research` (issue #1010, v0.5.3). Player's handover 2026-10-12 evening lists this experiment as item 5 (selection frame capture). The research repo's canonical report will be at `docs/reports/2026-10-12-unit-map-selection-rendering.md` after intake.

> **2026-10-12 (corrected after first draft):** the first draft (commit `2e36998`) reported "no frame drawn around the tile" based on a pixel analysis at `screen_centre=(641, 462)` — but that region sits BELOW the unit map (which ended around y≈420 in the 1280×1024 capture), so the analysis looked at empty space below the map and missed the frame. Visual inspection of the same screenshots, and a SHA-256 comparison that confirms `selected == frame3` (0 pixel diff, frame2 differs by 98 pixels), show a yellow rhombus drawn around the selected tile in all three cases. Corrected in this version.

**Tags:** `[P]` played in Wine; `[derived]` from screenshot inspection and memory reads.

**Data:** `runs/experiments/data/run-exp-unit-map-selection/` (runner `sel_capture.py`, logs `sel_capture-<stamp>.log`, results `sel_results-<stamp>.json`, `SAVES.sha256`, `README.md`); screenshots and saves in release `run-exp-unit-map-selection` (https://github.com/diegoami/ic2-conquest/releases/tag/run-exp-unit-map-selection — **moved from imperial_conquest_2 in the round-2 release-fix; the original imperial_conquest_2 release is being deprecated**). Fast rollingsave seed exe (patched), Wine 10.0, no seed (loading does not reseed; the save carries its own RNG state). One fresh Wine process per unit type; the reference save is `saves/fleet-port-antium-0734.SAV` (turn 734, 270 BC Spring, Rome with armies at (101,45)/(102,45)/(102,44), fleet 2 at (101,46), 16 cities).

Screenshots: all named `sel_<stamp>_<case>_<type>.png` in the release, cited by bare filename below.
SHA-256 of each binary in `runs/experiments/data/run-exp-unit-map-selection/SAVES.sha256`.

## Answer

### Army selected (`sel_20261012-203220_army_selected.png`, SHA-256 `617968595e103ff455a65a4fcc8f51ef5ab69372689c1bd01ff257058eb5deec`)

- **Frame shape:** Yellow **rhombus** (diamond) drawn around the selected tile in the unit map. Visible in `army_selected.png` and `army_frame3.png` (identical pixels, SHA-256 match); absent in `army_unselected.png` and `army_frame2.png` `[P][derived]`.
- **Frame colour:** Bright yellow.
- **Frame size:** About one cell wide on each side (the rhombus fits within roughly one map cell, oriented with its diagonals aligned to the cell's row/column axes).
- **Marker colour change:** The army marker itself (the small figure inside the tile) keeps its own colour; the selection feedback is the rhombus, not a marker recolour. The earlier "green-channel shift to 0.673" reading was the rhombus's yellow against the marker's reddish tile — i.e. the yellow rhombus over the marker, the same artifact the user's report mentions.
- **Blinking:** The rhombus blinks. `army_selected` (frame 1) and `army_frame3` (frame 3, captured 600 ms later) are identical (SHA-256 match, 0 pixel diff); `army_selected` vs `army_frame2` (frame 2, captured 300 ms later) differs by 98 pixels — the rhombus pixels are present in `selected/frame3` and absent in `frame2`. The blink is therefore ON at frame 1, OFF at frame 2, ON at frame 3 — a cycle with a period of roughly 600 ms (300 ms on, 300 ms off).

### Fleet selected (`sel_20261012-203220_fleet_selected.png`, SHA-256 `7031080ea8ad6cb5a9b25758d635b81bde5abf9b6837dfe1d6ba6565d1723b08`)

- **Frame shape:** Yellow **rhombus** around the selected fleet tile, same shape and approximate size as for the army. Visible in `fleet_selected.png` and `fleet_frame3.png` (SHA-256 match); absent in `fleet_unselected.png` and `fleet_frame2.png`.
- **Frame colour:** Bright yellow.
- **Frame size:** Same as the army — one cell wide per side.
- **Marker colour change:** The fleet marker keeps its own colour; the selection feedback is the rhombus over the cell.
- **Blinking:** Same as the army: `fleet_selected` == `fleet_frame3` (SHA-256 match), `fleet_selected` vs `fleet_frame2` differs by 98 pixels; cycle ~600 ms.

### Town selected (`sel_20261012-203220_town_selected.png`, SHA-256 `9bf50cb1ddcf95a8a12fd7ed4b37df8d2f9ca2676d8a76d762ef20920a0cfac1`)

- **Frame shape:** Yellow **rhombus** around the selected town tile, same shape and approximate size as for the army and the fleet. Visible in `town_selected.png` and `town_frame3.png` (SHA-256 match); absent in `town_unselected.png` and `town_frame2.png`.
- **Frame colour:** Bright yellow.
- **Frame size:** Same as the army and the fleet.
- **Marker colour change:** The town marker keeps its own colour; the selection feedback is the rhombus over the cell. The town tile's selected-state also brings up the city information panel on the left side of the screen (12,864-pixel full-image diff between `town_selected` and `town_unselected`) — this is the additional UI response, on top of the rhombus that all three unit types share.
- **Blinking:** Same as the army and the fleet: `town_selected` == `town_frame3` (SHA-256 match), `town_selected` vs `town_frame2` differs by 98 pixels; cycle ~600 ms.

## Open / Not established

- The exact pixel count and offset of the 98-pixel blink alternation. The 98-pixel diff between `selected`/`frame3` and `frame2` corresponds to the rhombus pixels going on/off across the three unit types; the constant 98 across army / fleet / town suggests the same rhombus drawing primitive is used for every selection (constant pixel footprint). A higher-resolution capture or a per-pixel diff log would confirm the exact count.
- The exact blink period was sampled at 300 ms intervals (3 frames). The cycle is approximately 600 ms; a finer capture (e.g. every 100 ms for 2 seconds) would pin the period precisely.
- The reference `D_1_selected.png` from `runs/2026-10-02-unit-map-mouse-orders-and-tax-range.md` (the only existing selection capture before this run) shows the same yellow rhombus on the area map (not the unit map); this run now confirms the unit-map view uses the same shape and colour.
- The "remake" view of the issue (`godot/MapViewer.cs:156-157 and :240, DrawSelection`) is read-only; the suggested fix below is for that file but lives outside this repo.

## Comparison to the remake

The remake (`godot/MapViewer.cs:156-157 and :240, DrawSelection`) draws a 2-pixel **circle** (`DrawArc`, `SelectedColor`) around the selected city or unit and the marker keeps its own colour. The original IC2 unit map draws a yellow **rhombus** (diamond, ~1 cell wide per side) around the selected unit's tile — for army, fleet, and town alike — that **blinks** at roughly 600 ms periods (300 ms on, 300 ms off).

The user's original report ("there is a rhomboid square around them to show they are selected", reported on 2026-10-11 from playing the original) matches the captures: **rhombus = yes, all three unit types, blinks = yes**.

A UI fix for the remake should:
1. Replace `DrawArc` with a rhombus-drawing primitive that fits within one map cell, oriented with its diagonals aligned to the row/column axes.
2. Use the original's yellow (the existing `SelectedColor` palette should be close enough; if not, an explicit yellow constant).
3. Add the blink: keep `~300 ms on, ~300 ms off`, possibly via a UI timer in the same form, rather than a marker recolour.

The town selection in the original also opens a side information panel; if the remake reproduces that, it would need the same panel transition at selection time.

## First-draft vs second-draft change log

- First draft (commit `2e36998`, M2.7 agent hand-back): pixel analysis at `screen_centre=(641, 462)` reported "no frame drawn". The screen_centre was below the unit-map region; the analysis looked at empty pixels.
- This second draft (hand-corrected in the main session): visual inspection of the same screenshots shows the yellow rhombus on army, fleet, and town tiles, blinking at ~600 ms periods. The SHA-256 evidence (`selected == frame3`, `selected vs frame2` differs by 98 pixels) is the same as the first draft; only the interpretation of those 98 pixels flipped (they ARE the rhombus, not an external overlay).
- The data (screenshots, SAV files, runner, logs) and the SAVES.sha256 are unchanged. Only the analysis text and the comparison section are corrected.

## First-draft release-location note

The first draft's release `run-exp-unit-map-selection` was created in `diegoami/imperial_conquest_2` (the research repo). CLAUDE.md rule 2 forbids writing to another repository: rule discoveries go to `findings/` here and the player promotes. The release was re-created in `diegoami/ic2-conquest` (this repo) with the same tag and assets; the imperial_conquest_2 release is being deprecated (see the corrected release URL in the **Data** section above).
