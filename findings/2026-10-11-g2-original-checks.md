# Original-side checks 3, 4, 5 and 7 of the v0.5.0 gap analysis: a 0-move army is selectable and fully usable, an unreachable click walks as far as the moves allow, Join units joins every selected unit, Split unit has a per-type floor (limit/5 per piece), and a storm cuts an army aboard to a few percent

**Status:** draft from ic2-conquest, awaiting promotion (issue #75, PR from `experiment/g2-original-checks`). Does checks 3, 4, 5 and 7 of `runs/experiments/data/run-exp-gap-v050/rows_g2.md` ("Original-side checks needed"; rows MM01, MM03, UA06, D05, D06, NEW-g2-2). Implemented by a Sonnet subagent at the owner's choice. Wine-only.

**Tags:** `[P]` played in Wine and read from game memory, the saves and the screenshots; `[derived]` the rule as stated; `[code]` the pinned decompile (`all_app_functions.txt` line numbers unless another file is named).

**Data:** `runs/experiments/data/run-exp-g2-original-checks/` (runner `g2_checks.py`, logs `g2_checks-<case>-<stamp>.jsonl`, `c7_storm_reanalysis.*`, `SAVES.sha256`); saves and screenshots in release `run-exp-g2-original-checks`. Fast rollingsave seed exe, Wine 10.0, seed 12345, one fresh process per case; staging is L1 (unit slots and army moves only, positions never edited), named in each log's `staged` line.

## Answer

### C3 (MM01): an own army with 0 moves is selected, and every button works `[P]`

`fleet-port-antium-0734.SAV` (turn 0734) has army 12 at (102,45) with moves 0 as saved. Control: the same save staged to moves 8 (`C3_20261011-185659_staged_army12_moves8_fleet-port-antium-0734.SAV`), same position, same process.

| | moves 0 (`C3_..._zero_moves_loaded.SAV`) | moves 8 (`..._control_moves8_loaded.SAV`) |
|---|---|---|
| selection after one click | army 12 (stays after 2.5 s) | army 12 |
| Information panel | "Army of Rome, Moves 0, ... Total troops 7,100" | the same with "Moves 8" |
| button strip pixels (SHA of the crop) | `29ef8738...` | `29ef8738...` (identical) |
| Supply army / Army to army transfer / Split army / Change units | all four dialogs open | all four open |

- **The original does not drop a 0-move army on selection** `[P]`. The inventory's "dropped at 0 moves" is the end of a move, not a refusal to select: after a move that leaves 0 moves the selection is cleared (C4: SEL_ARMY -1 after the army reached 0 moves) `[P]`.
- `[code]` `TUnitMap_SelectUnit` (46487): for an own army marker (`sVar5 - 200 < 0x30`, 46555) it sets the selection to the army (46562, 46644) and turns the army buttons on (46653) with no test of the army's moves; the only moves test in the function is for attacking. `TUnitMap_MoveHumanArmy` (46713) ends the selection when the army's moves are 0 after the walk (`TUnitMap_EndUMSelection`).
- Clicking a target with a 0-move army selected moves nothing and clears the selection `[P]` (C4b, step to (100,29): position and moves unchanged, selection -1).

### C4 (MM03): an unreachable target walks as far as the moves allow, no box `[P]`

`run0-start-AUTO0720-seed12345.SAV` (turn 0720): army 0 at (100,37), moves 8, target (100,25) 12 tiles north.

| Case | Target | After | Box | Saves |
|---|---|---|---|---|
| far (C4 far12) | (100,25), 12 away | army at **(100,29), moves 0**, selection cleared | none | `C4_20261011-185907_far12_before.SAV`, `..._far12_after.SAV` |
| control (C4 near5) | (100,32), 5 away | at (100,32), moves 3 | none | `..._near5_before.SAV`, `..._near5_after.SAV` |
| steps (C4b) | one click per tile (100,36)..(100,30) | moves 7,6,5,3,2,1,0; forest (100,33) costs 2 | none | `C4b_20261011-190051_steps_after.SAV` |
| river (C4b, army staged moves 11) | (100,25), river at (100,26) costs 4 | stops at **(100,27) with 1 move left** | none | `C4b_..._river_with_1_move_left_after.SAV` |

- **The click is not refused or ignored: the army walks the line and stops when it cannot pay for the next tile**, keeping what is left (1 move before the river). No box appears.
- **The walk sidesteps expensive tiles** `[P]` `[code]`: the far click spent 8 moves for 8 tiles and the near click 5 for 5, although a straight column crosses the forest at (100,33) (cost 2 when clicked alone). `FUN_0044d734` (51517) is a Bresenham walk that calls the step routine `FUN_0044d420` (51399) for each tile; the step compares the cost of the line's tile with its two lateral neighbours (`FUN_0044d31c`, 51366, the terrain cost, 10 for impassable) and takes a cheaper neighbour. The step is taken only if the tile's cost is at most the moves left (51481-51483); otherwise a human army does not move and the loop is ended (51511-51512). `TUnitMap_MoveHumanArmy` calls the walk a second time when the target is not yet reached and moves remain (46713 ff.). The tiles actually crossed were not observed, only the totals `[derived]`.

### C5 (UA06, D05, D06): Change units

**Join units (UA06)** `[P]` (`C5a`, `run0-start` army 0 staged with `li` units, `C5a_20261011-190227_*`):

| Case | Selected | Before | After |
|---|---|---|---|
| join3 | li 1000, 1200, 1500 | 4 units | **2 units: li 3,700 and the hi** (`..._join3_before.SAV`, `..._join3_after.SAV`) |
| join4 | li 1000, 1200, 1500, 1700 | 5 units | **li 5,400 and the hi** (`..._join4_*`) |
| join2 (control) | li 1000, 1200 | 4 units | li 2,200, li 1,500, hi (`..._join2_control_*`) |

The original joins **all** selected units when they are one type, regular and the total fits (the box R44 only above the type limit); the join is applied when the Change units dialog is closed with OK. The remake joins only the first two (rows_g2 UA06 (b)).

**Rename unit with two selected (D05)** `[P]` (`C5b_20261011-190426_*`): the box "You can only rename 1 unit at a time." (R36) appears, no Rename dialog, the army is unchanged (`..._after_two.SAV`); control with one unit selected renames it (`..._after_one.SAV`: "Control"). Confirms R36; the remake renames the first selected without a box.

**Split unit (UA06, D06)** `[P]` (`C5c`, logs `g2_checks-C5c-20261011-191316.jsonl`, `-190536`, `-191005`).

- **Size limit per type, read from game memory** at `0x478fca + 40·type` (the `DAT_00478fca` of R41/R44): li 15,000, hi 6,000, ar 3,500, lc 7,000, hc 2,500. The refusal threshold is `limit·2/5` (R41, `[code]` 45558): li 6,000, hi 2,400, ar 1,400, lc 2,800, hc 1,000.
- **Threshold tests: exactly the predicted line, in all five types.** A unit of `threshold - 1` gets "This unit is too small to split." and nothing changes; a unit of exactly `threshold` opens the Split unit dialog and splits in two equal halves (hi 2,400 to 1,200 + 1,200; lc 2,800 to 1,400 + 1,400; hc 1,000 to 500 + 500; li 6,000 to 3,000 + 3,000; ar 1,400 to 700 + 700).
- **100 troops: refused for every type** (all five thresholds are above 100). So "a unit of exactly 100" is not the R41 threshold for any type; the remake's accepted 1-troop and 100-troop splits (rows_g2 UA06, D06) are differences. A light infantry of 4,800 (the start army's own unit) is also refused (4,800 < 6,000).
- **Spinner range** (hi 5,000; `hi5000_probe`, `hi5000_ext_A`, `hi5000_ext_B`): the dialog shows two sizes, starting at 2,500 | 2,500, with a 100s and a 1000s spinner moving troops between them. The 1000s arrow moves 1,000 (2,500 to 3,500, then clamped), the 100s arrow 100. **Each new unit has a floor of 1,200 (= limit/5) and so a ceiling of 3,800**: the readings run 1,200 | 3,800 to 3,800 | 1,200 and two further presses past each end change nothing. OK at the low extreme gave 1,200 + 3,800 (`..._ext_A_after.SAV`), at the high extreme 3,800 + 1,200 (`..._ext_B_after.SAV`). The raw `TUpDown` controls report range 0..1000, position 500 (`win_updown.c`) and are not the sizes; the clamp is in the dialog's handler.
- The remake's engine bounds are 1..troops-1 (rows_g2 D06).

### C7 (NEW-g2-2): a storm leaves an army aboard a damaged fleet with 3 to 8 percent of its men, or none `[P]` `[code]`

No new run: the cell R85sA of `run-exp-storms` (`2026-10-03-storms-and-losses-at-sea.md`) is exactly the case (Carthage fleet 0, 90 ships, condition 85, rough sea, army 2 aboard, 5 seeds; the fleet is damaged and not sunk: 90 to 65 ships, condition 60 or 61 in 5 of 5). Re-read by `c7_storm_reanalysis.py` (hashes checked): army 2 before is **11,000 troops** in 5 units (li 4,000, hi 3,000, ar 2,000, lc 1,000, hc 1,000; `FIX_T4_R85sA.SAV`, turn 720). After the storm, turn 721:

| Seed | Army 2 after |
|---|---|
| 1 (`ST_R85sA_seed1_AUTO0721.SAV`) | **one unit, hi 678** |
| 2 | one unit, hc 312 |
| 3 | one unit, hi 850 |
| 4 | **gone** (fleet's carried army -1) |
| 5 | one unit, hc 312 |

(seeds 2 to 5: `t4_trials.json`, saves not kept.) The remake's loss of half in a round is far milder.

- `[code]` `calendar_and_endturn.txt:194` calls `FUN_0044b4f8(fleet, 100, dmg + 100)` for a storm with damage 6 or more (49841). It sets `d = (max(1, 10000/(dmg+100)))² / 100` (86 for the rough-sea damage 7), takes `ships·d/300` off ships and condition, and for a carried army calls `FUN_0044ae20(army, d)` (49571): **each unit loses `(troops / (rand(15)+105)) · d`** (about 72 to 82 percent at d 86), a regular unit left under limit/10 (a mercenary under limit/5) is removed, and with `d > 70` `units·d/250 + 1` further random slots are removed.
- The recomputation reproduces the data: 90 to 65 ships (d 86); hc 1,000 to **312** is the rand-14 end of the formula (312 exactly, twice); hi 3,000 to 850 is also its end, and 678 lies inside its 592 to 850 range (`c7_storm_reanalysis.txt`).

## What the remake does

`rows_g2.md`: MM01 selects any own marker regardless of moves (`ResolveLeftClickOnMarker`), which matches the original (the row's "differs" was the inventory's wording; the original also keeps a 0-move army selected and usable). MM03: `MoveArmy` goes as far as the moves allow ("spending 8 of 8 moves"), the same outcome; whether it sidesteps costly tiles was not compared. UA06/D05: Join joins two only, Rename acts on the first selected without a box, no R41 test. D06: spinners 1000s 0..1000 and 100s 0..900, engine 1..troops-1, accepts a 1-troop and a 100-troop split. NEW-g2-2: the remake halves the army per storm round.

## What this does not establish

- C3: only the army with 0 moves at its own position, in one save; the dialogs were opened and closed with OK unchanged, not used for transfers or splits (those are in earlier findings).
- C4: the tiles crossed by the sidestepping walk were not observed, only start, end and moves; one direction (north) and two terrain features (forest, river) were tried. The second walk call in `TUnitMap_MoveHumanArmy` was read, not isolated.
- C5: Join was tested for li only; the "total too large" refusal (R44) was not repeated. Split was tested in one fixed army (a 5,000 hi beside it) with unit label 0 (regular); mercenaries (R39) were not repeated. The size table was read from memory, not from the DAT file. The 100s and 1000s arrows' step (100 and 1,000) is seen on a 5,000 unit only.
- C7: the storm evidence is a synthetic cargo (an army put aboard by an edit, `run-exp-storms` R85sA); the five-unit army, one damage level (d 86) and 5 seeds. Seeds 2 to 5 rest on `t4_trials.json` (no saves). A natural storm with a carried army was not found; the formula's other values of `d` were recomputed, not observed.
