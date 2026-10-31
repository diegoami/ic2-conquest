# run-exp-unit-map-selection: unit-map selection frame capture (issue #1010)

Captures what the selection frame looks like in the original IC2 unit map for armies, fleets and towns: shape, colour, size, blinking, and marker colour change.

## Reference save

`saves/fleet-port-antium-0734.SAV` (turn 734, 270 BC Spring, Rome as human):
- Army 0: (101, 45), 10,700 troops
- Army 12: (102, 45), 7,100 troops
- Army 13: (102, 44), 5,900 troops
- Fleet 2: (101, 46), 30 ships (Mediterranean sea tile)
- City Antium: (101, 47), Roman city

## Cases

| case | tile (x,y) | description |
|------|------------|-------------|
| army | (101, 45) | Rome's army 0 |
| fleet | (101, 46) | Rome's fleet 2 (sea tile) |
| town | (101, 47) | Antium, Roman city |

## Runner

`sel_capture.py`: one fresh Wine process per case.

Per case:
1. Load reference save (no seed — loading does not reseed)
2. Bring tile into unit map via area map click (show, not select)
3. Park mouse on neutral point
4. Screenshot unselected state
5. Click tile to select unit
6. Screenshot selected state
7. Two more captures 300 ms apart (blinking check)
8. Save game with selection active

## Outputs

- `sel_capture-<stamp>.log`: runner log (JSONL lines)
- `sel_results-<stamp>.json`: per-case memory state and file list
- `SAVES.sha256`: SHA-256 of every binary produced
- Screenshots: `CASE_<stamp>_[unselected|selected|frame2|frame3].png`
- Saves: `SEL_<CASE>_<stamp>.SAV`
- All binaries in release `run-exp-unit-map-selection`

## Controls

- Wine 10.0, Xvfb :99, fast rollingsave seed exe
- Seed: None (save carries its own RNG state; loading does not reseed)
- Driver: `harness/driver.py` `Game` class, `Game.load`, `Game.open`, `Game.save_as`
- Map click: `Game.show` → `UNIT_PAINT` offset (337, 96) + 32 px per tile
- Selection check: `SEL_ARMY` (0x4A0328) and `SEL_FLEET` (0x4A032A) from game memory
