# Splitting an army aboard a fleet is allowed: the new army lands on a land tile next to the fleet, the rest stays aboard

**Status:** draft finding from `ic2-conquest`, awaiting promotion. For clone task T111 (Split army, plan PR #736). Task `docs/tasks/split-aboard.md`. **Wine-only.** Natural state, fixture copy only.

**Tags.** `[derived]` = read from the decompile (function, address, line of `all_app_functions.txt`; code in `runs/experiments/data/run-exp-split-aboard/code_extract_split_aboard.txt`). `[confirmed]` = seen in play with a save pair.

**Answer.**
1. **There is no aboard refusal in Split army** `[derived]` `[confirmed]`. `TUnitMap_SplitArmy` @ 0044755C checks only: the army (the selected army, or, when a fleet is selected, the army that fleet carries, :47033-47037) belongs to the current nation (:47039); and it has more than one unit ("You can not split an army containing only 1 unit.", :47041-47044). `TUnitMap_JoinArmies` by contrast refuses an army aboard: "An army on a fleet cannot be combined with another." (:46976-46978). With the fleet selected, Unit map > Army > Split army opened the "Split army" dialog and the split worked.
2. **The new army is placed on land, not on the fleet** `[derived]` `[confirmed]`. `FUN_00449F08` @ 00449F08 asks `FUN_004492C0(position, 1)` for a tile (:48724); for the army aboard, the position is the fleet's tile. `FUN_004492C0` @ 004492C0 scans the 3 × 3 around the position (x offset outer, y offset inner, both −1 → +1) and keeps the **last** tile whose map code is in 2..11 (:47942-47943, :47960-47962, the codes of free terrain: a city, army or fleet marker is 20 or more, so occupied tiles are skipped). The new army gets that tile, its own `+0x8` map-cell word is set from it (:48736) and it is not aboard; purse 0, supplies 0, moves 0 as for any split (:48738-48740, see the purse finding of PR #47). A scan that finds no free land tile leaves the position at −1 and `FUN_00449F08` creates **nothing** (:48725): no army, no message, the dialog does not open (:47047) `[derived]`. Also nothing is created when the army table is full (`DAT_004A0324 < 0xC6`).
3. **In play** (fleet 2, 30 ships, at (101,46); army 0, 3 units, 10,700 troops, embarked on it): no refusal box; the Split army dialog opened; after moving the first unit across and OK, army 0 stayed aboard with 2 units and 5,700 troops, and **a new army 14 (1 unit, 5,000 troops) stood on land at (102,47)**, diagonally next to the fleet, not aboard, moves 0, supplies 0, purse 0. The fleet kept carrying army 0.

## Method

- **Code.** Read `TUnitMap_SplitArmy`, `FUN_00449F08`, `FUN_004492C0`, `TUnitMap_JoinArmies`.
- **Play.** `runs/experiments/split_aboard/split_aboard.py` on a copy of `saves/fleet-port-antium-0734.SAV` (Rome; normal build `Imperial Conquest 2 fast rollingsave seed.exe`, `SEED.TXT` 12345, own Xvfb display and game folder). Select army 0 (at (101,45)) and click the adjacent fleet at (101,46): embarked (moves 0 on both). Save. Select the **fleet**, open the menu Unit map > Army > Split army (the army toolbar is not shown while a fleet is selected), transfer the first unit, OK, save. Menu positions were found by screenshot (`SA_menu_army_submenu.png`).

## Evidence

Read from the saves with `state/sav.py`; `claims_audit.py` recomputes each line (28 checks, 0 mismatches, `claims_audit_output.txt`), including the placement by replaying the scan on the map of `SA_01`.

| Save | Army 0 | New army | Fleet 2 | Armies 12, 13 |
|---|---|---|---|---|
| `SA_00_start.SAV` | (101,45), 3 units, 10,700, moves 3, on land | – | (101,46), 30 ships, moves 29, carries −1 | (102,45) 7,100; (102,44) 5,900 |
| `SA_01_aboard_before_split.SAV` | (101,46), **aboard** (cell −1), 3 units, 10,700, moves 0 | – | moves 0, carries army 0 | unchanged |
| `SA_02_after_split.SAV` | (101,46), **still aboard**, 2 units, **5,700**, purse 100 | **army 14: (102,47), on land, 1 unit, 5,000**, moves 0, supplies 0, purse 0 | still carries army 0 | unchanged |

- Land tiles of the 3 × 3 around (101,46) in `SA_01`: (102,47) is the last in scan order, as the code predicts; (102,45) and (102,44) hold armies 12 and 13 and are not candidates.
- Saves and screenshots are in release `run-exp-split-aboard` (`batch-b1.tar.gz`), hashes in `MANIFEST-b1.txt` and `SAVES.sha256`.

## What this does not establish

- **The no-free-tile case** (a fleet at sea with no land within one tile) is `[derived]` only: after embarking, the fleet has 0 moves, so it cannot be sailed to open sea in the same turn from this fixture. The code gives no army, no dialog and no message.
- **Fleet capacity** is not involved in the split itself (the new army is on land). The Transfer buttons of the Army to army dialog have their own capacity message for armies aboard (`2026-10-03-army-to-army-ok-supply-rebalancing.md`); not exercised.
- **Which land tile when several are free** follows the scan order (the last one), confirmed on one position.
- Only the fleet-selected route was played; with the army selected the same function reads the army's own position (`:47037`), which for an embarked army is the fleet's tile.
- **Wine-only**, one fleet.

## Reproduction

```text
python3 runs/experiments/split_aboard/split_aboard.py     # about 1.5 minutes
python3 runs/experiments/split_aboard/claims_audit.py
```
