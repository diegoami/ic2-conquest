# Splitting an army aboard a fleet is allowed: the new army lands on a land tile next to the fleet, the rest stays aboard

**Status:** draft finding from `ic2-conquest`, awaiting promotion. For clone task T111 (Split army, plan PR #736). Task `docs/tasks/split-aboard.md`. **Wine-only.** Natural state, fixture copy only.

**Tags.** `[derived]` = read from the decompile (function, address, line of `all_app_functions.txt`; code in `runs/experiments/data/run-exp-split-aboard/code_extract_split_aboard.txt`). `[confirmed]` = seen in play with a released, hashed before/after save pair. **Only the one observed case is `[confirmed]`**: a fleet selected, Unit map > Army > Split army, one unit moved across, OK. The general rules are `[derived]` and stated separately.

**Observed (`[confirmed]`, four runs).** Fleet 2 (30 ships) at (101,46) carried army 0 (3 units, 10,700 troops). With the **fleet selected**, Unit map > Army > Split army opened the "Split army" dialog with no refusal box; after moving the first unit across and OK, army 0 stayed aboard with 2 units and 5,700 troops, and **a new army (1 unit, 5,000 troops) stood on land at (102,47)**, diagonal to the fleet, not aboard, moves 0, supplies 0, purse 0. The fleet kept carrying army 0. Saves: `SA_01_aboard_before_split.v3.SAV` → `SA_02_after_split.v2.SAV` (the calibrated re-run) and `SA_01_aboard_before_split.v2.SAV` → `SA_02_after_split.SAV` (the first run, raw screen clicks), and `SA_01_aboard_before_split.v4.SAV` → `SA_02_after_split.v3.SAV` (the third run, where the top menu bar is also found by OCR), and `SA_01_aboard_before_split.v5.SAV` → `SA_02_after_split.v4.SAV` (the fourth run, where the embark is also verified in memory and the unit selection and Transfer on the screen, each with at most two retries); the same result every time (`save_pairs.tsv`).

**Rules (`[derived]`, from the code only).**
1. **No aboard refusal in Split army.** `TUnitMap_SplitArmy` @ 0044755C checks only that the army (the selected army, or, when a fleet is selected, the army that fleet carries, :47033-47037) belongs to the current nation (:47039) and has more than one unit ("You can not split an army containing only 1 unit.", :47041-47044). `TUnitMap_JoinArmies` by contrast refuses an army aboard: "An army on a fleet cannot be combined with another." (:46976-46978).
2. **The new army is placed on land, not on the fleet.** `FUN_00449F08` @ 00449F08 asks `FUN_004492C0(position, 1)` for a tile (:48724); for the army aboard, the position is the fleet's tile. `FUN_004492C0` @ 004492C0 scans the 3 × 3 around the position (x offset outer, y offset inner, both −1 → +1) and keeps the **last** tile whose map code is in 2..11 (:47942-47943, :47960-47962; a city, army or fleet marker is 20 or more, so occupied tiles are skipped). The new army gets that tile, its `+0x8` map-cell word is set from it (:48736), and it is not aboard; purse 0, supplies 0, and moves 0 for a human owner (1 for a non-human owner, :48732-48735; see the purse finding of PR #47). In the played case the replayed scan on the before-save map gives (102,47), the tile observed (`claims_audit.py`), which supports the rule for that one position.
3. **No free land tile: no army, no message** `[derived]`. A scan that finds none leaves the position at −1 and `FUN_00449F08` creates nothing (:48725); `TUnitMap_SplitArmy` then does not open the dialog (:47047). Also nothing is created when the army table is full (`DAT_004A0324 < 0xC6`). Not played (below).

## Method

- **Code.** Read `TUnitMap_SplitArmy`, `FUN_00449F08`, `FUN_004492C0`, `TUnitMap_JoinArmies`.
- **Play.** `runs/experiments/split_aboard/split_aboard.py` on a copy of `saves/fleet-port-antium-0734.SAV` (Rome; normal build `Imperial Conquest 2 fast rollingsave seed.exe`, `SEED.TXT` 12345, own Xvfb display and game folder). Select army 0 (at (101,45)) and click the adjacent fleet at (101,46): embarked (moves 0 on both). Save. Select the **fleet**, then Unit map > Army > Split army by the menu (the army toolbar is not shown while a fleet is selected): `lib.split_army_via_menu` finds each menu level by OCR of the open menu, clicks its centre, and verifies the transition (top menu: the words army/fleet/city; submenu: split/disband; dialog: its window), at most two retries per transition; no fixed screen coordinate is used for the menu. The dialog's list row and buttons are located with `win_controls`; the split is verified by the army count. The first run used raw screen coordinates for the two submenu clicks, the second still clicked the top-level "Unit map" at a fixed point; both were kept, and the third run finds the menu bar's "Unit map" by OCR too (`bar` search in `split_army_via_menu`) and verified every transition; it reproduced the result.

## Evidence

Read from the saves with `state/sav.py`; `claims_audit.py` recomputes each line for every run (51 checks over the four runs, 0 mismatches, newest `claims_audit_output*.txt`): the rule inputs are the tracked code extract, the expected values are derived from the saves (the placement replays the scan the extract shows on the before-save map), and `test_claims_audit.py` shows a doctored save fails.

| Save | Army 0 | New army | Fleet 2 | Armies 12, 13 |
|---|---|---|---|---|
| `SA_00_start.v2.SAV` (calibrated run; the first run's `SA_00_start.SAV` is identical in these fields) | (101,45), 3 units, 10,700, moves 3, on land | – | (101,46), 30 ships, moves 29, carries −1 | (102,45) 7,100; (102,44) 5,900 |
| `SA_01_aboard_before_split.v3.SAV` | (101,46), **aboard** (cell −1), 3 units, 10,700, moves 0 | – | moves 0, carries army 0 | unchanged |
| `SA_02_after_split.v2.SAV` | (101,46), **still aboard**, 2 units, **5,700**, purse 100 | **army 14: (102,47), on land, 1 unit, 5,000**, moves 0, supplies 0, purse 0 | still carries army 0 | unchanged |

- Land tiles of the 3 × 3 around (101,46) in `SA_01`: (102,47) is the last in scan order, as the code predicts; (102,45) and (102,44) hold armies 12 and 13 and are not candidates.
- Saves and screenshots are in release `run-exp-split-aboard` (`batch-b1.tar.gz` for the first run, `batch-rerun.tar.gz` for the calibrated re-run), hashes in `MANIFEST-*.txt` and `SAVES.sha256`; `fetch_archive.py` prepares `artifacts/` for the audit.

## What this does not establish

- **Everything in the Rules block** beyond the one observed case: the general no-refusal rule, the placement scan for other positions, and the no-free-tile case.
- **The no-free-tile case** (a fleet at sea with no land within one tile) is `[derived]` only: after embarking, the fleet has 0 moves, so it cannot be sailed to open sea in the same turn from this fixture. The code gives no army, no dialog and no message.
- **Fleet capacity** is not involved in the split itself (the new army is on land). The Transfer buttons of the Army to army dialog have their own capacity message for armies aboard (`2026-10-03-army-to-army-ok-supply-rebalancing.md`); not exercised.
- **Which land tile when several are free** follows the scan order (the last one), confirmed on one position.
- Only the fleet-selected route was played; with the army selected the same function reads the army's own position (`:47037`), which for an embarked army is the fleet's tile.
- **Wine-only**, one fleet.

## Reproduction

```text
python3 runs/experiments/split_aboard/split_aboard.py     # about 1.5 minutes
python3 runs/experiments/split_aboard/fetch_archive.py     # once: the released saves into artifacts/ (hash-checked)
python3 runs/experiments/split_aboard/claims_audit.py
python3 -m unittest runs/experiments/split_aboard/test_claims_audit.py
```
