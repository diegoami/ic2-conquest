# Original-side checks 3, 4, 5 and 7 of the v0.5.0 gap analysis: a 0-move army is selectable and stays selected with its toolbar dialogs opening, an unreachable click walks as far as the moves allow, Join units joins every selected unit, Split unit has a per-type floor (limit/5 per piece), and a storm cuts an army aboard to a few percent

**Status:** draft from ic2-conquest, awaiting promotion (issue #75, PR from `experiment/g2-original-checks`). Does checks 3, 4, 5 and 7 of `runs/experiments/data/run-exp-gap-v050/rows_g2.md` ("Original-side checks needed"; rows MM01, MM03, UA06, D05, D06, NEW-g2-2). Implemented by a Sonnet subagent at the owner's choice. Wine-only.

**Tags:** `[P]` played in Wine and read from game memory, the saves and the screenshots; `[derived]` the rule as stated; `[code]` the pinned decompile: line numbers are those of `all_app_functions.txt` (SHA-256 `2018c205a4e4ea4a4079f2d166623fb571062832d76e19b72e11d1f0edac87d8`, `harness/decompile.py` PINS), and every function cited is in the tracked extract `code_extract_g2.txt` (made by `make_code_extract.py`, line-numbered, whole functions; its header names the file and hash, its index the line ranges). The storm block is cited in `FUN_004514ec` of the dump (the earlier citation of `calendar_and_endturn.txt:194` is dump line 54591).

**Data:** `runs/experiments/data/run-exp-g2-original-checks/` (runner `g2_checks.py`, logs `g2_checks-<case>-<stamp>.jsonl`, `code_extract_g2.txt`, `c7_storm_reanalysis.*`, `c7_storm_model.*`, `SAVES.sha256`); saves and screenshots in release `run-exp-g2-original-checks`. Fast rollingsave seed exe, Wine 10.0, seed 12345, one fresh process per case; staging is L1 (unit slots and army moves only, positions never edited), named in each log's `staged` line.

## Answer

### C3 (MM01): an own army with 0 moves is selected and stays selected, and the four toolbar dialogs tested open `[P]`

`fleet-port-antium-0734.SAV` (turn 0734) has army 12 at (102,45) with moves 0 as saved. Control: the same save staged to moves 8 (`C3_20261011-185659_staged_army12_moves8_fleet-port-antium-0734.SAV`), same position, same process.

| | moves 0 (`C3_..._zero_moves_loaded.SAV`) | moves 8 (`..._control_moves8_loaded.SAV`) |
|---|---|---|
| selection after one click | army 12 (stays after 2.5 s) | army 12 |
| Information panel | "Army of Rome, Moves 0, ... Total troops 7,100" | the same with "Moves 8" |
| button strip pixels (SHA of the crop) | `29ef8738...` | `29ef8738...` (identical) |
| Supply army / Army to army transfer / Split army / Change units | all four dialogs open | all four open |

- **The original does not drop a 0-move army on selection** `[P]`. The inventory's "dropped at 0 moves" is the end of a move, not a refusal to select: after a move that leaves 0 moves the selection is cleared (C4: SEL_ARMY -1 after the army reached 0 moves) `[P]`.
- `[code]` `TUnitMap_SelectUnit` (46487-46664): for an own army marker (`sVar5 - 200 < 0x30`, 46555) it stores the clicked army as the selection (46557-46562, 46644) and turns the army buttons on (46653), with no test of that army's moves in those lines; the only moves read in the function is at 46514, which sets `bVar4` for an army already selected (moves at least 1 and `FUN_004492a0`) and `bVar4` is used by the attack boxes (46564). `TUnitMap_MoveHumanArmy` (46713-46743) calls `TUnitMap_EndUMSelection` when the army's moves are 0 after the walk (46739-46741).
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
- **The walk sidesteps expensive tiles** `[P]` `[code]`: the far click spent 8 moves for 8 tiles and the near click 5 for 5, although a straight column crosses the forest at (100,33) (cost 2 when clicked alone). The walk `FUN_0044d734` (51517-51660) is a Bresenham walk (51549-51627) that calls the step routine `FUN_0044d420` (51399-51514) for each tile (51604, 51621). The step reads the cost of the line's tile and of two lateral neighbours with `FUN_0044d31c` (51366-51396: the terrain cost from the table at `0x4792f0`, or 10 for an out-of-range or non-terrain tile, or when the tile is more than one step from two reference positions kept in the walk's frame, 51376-51393), and if a neighbour is cheaper takes the cheaper one (51463-51472). The step is taken when the chosen tile's cost is at most the army's moves and `FUN_0044d31c` of it is below 10 (51481-51483), and the moves are reduced by that cost (51496-51497); otherwise it sets the loop's bound variables (51511-51512, which ends the walk, read from the Bresenham loop's use of `local_16`, not run separately) and, only when the owner flag at `DAT_00474b00` for the current player is 0 (51506-51510), also zeroes the army's moves. That flag is nonzero for the human player at 51488 (map redraw and sound only when it is set), and the human's 1 move was kept at the river (C4b, `C4b_20261011-190051_river_with_1_move_left_after.SAV`), so the zeroing is read as the computer player's branch `[derived]`. `TUnitMap_MoveHumanArmy` (46713-46743) calls the walk again when `FUN_00449018` says the target is not reached and moves remain (46728-46734). The tiles actually crossed were not observed, only the totals `[derived]`; "sidesteps" is the reading of 51463-51472 and the equal totals (8 for 8 tiles, 5 for 5), not an observed path.

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

- **Size limit per type, read from game memory** at `0x478fca + 40·type` (the `DAT_00478fca` of R41/R44): li 15,000, hi 6,000, ar 3,500, lc 7,000, hc 2,500. The refusal threshold is `limit·2/5` (R41, `[code]` `TChangeArmyUnits_SplitUnit` 45520-45581: 45558 compares the unit's troops with `(size limit·2)/5`; label 0 only, 45556, else 45572 "You can only split regular units."): li 6,000, hi 2,400, ar 1,400, lc 2,800, hc 1,000.
- **Threshold tests: exactly the predicted line, in all five types.** A unit of `threshold - 1` gets "This unit is too small to split." and nothing changes; a unit of exactly `threshold` opens the Split unit dialog and splits in two equal halves (hi 2,400 to 1,200 + 1,200; lc 2,800 to 1,400 + 1,400; hc 1,000 to 500 + 500; li 6,000 to 3,000 + 3,000; ar 1,400 to 700 + 700).
- **100 troops: refused for every type** (all five thresholds are above 100). So "a unit of exactly 100" is not the R41 threshold for any type; the remake's accepted 1-troop and 100-troop splits (rows_g2 UA06, D06) are differences. A light infantry of 4,800 (the start army's own unit) is also refused (4,800 < 6,000).
- **Spinner range** (hi 5,000): the dialog shows two sizes, starting at 2,500 | 2,500, with a 100s and a 1000s spinner moving troops between them. The 1000s arrow moves 1,000 (2,500 to 3,500, then clamped), the 100s arrow 100. **Each new unit has a floor of 1,200 and so a ceiling of 3,800** (1,200 equals limit/5 of hi 6,000 `[derived]`; the clamp's code was not located): the readings run 1,200 | 3,800 to 3,800 | 1,200 and further presses past each end change nothing. OK at the low extreme gave 1,200 + 3,800, at the high extreme 3,800 + 1,200.
  - **Evidence with kept images (the new run, review fix R3):** `g2_checks-C5c-20261011-195827.jsonl` (`hi5000_probe`, `hi5000_ext_A`, `hi5000_ext_B`, same staging, seed 12345, fresh Wine process). Every reading of the two size boxes is one line item in the `split_test` line's `size_readings` (reading index, the full-dialog screenshot `C5c_20261011-195827_<test>_rd<NNN>_full.png`, the two enlarged crops `..._rd<NNN>_left.png` / `..._right.png`, the OCR text and value): 70 readings in the probe, 10 in each extreme test, all in `SAVES.sha256` and in the release. Probe: 1000s up 2,500|2,500, 3,500|1,500, 3,800|1,200, 3,800|1,200, 3,800|1,200; 1000s down from 3,800|1,200 to 1,200|3,800 (steps of 1,000 then the clamp), three equal readings at the end; 100s up from 1,200|3,800 to 3,800|1,200 in 26 steps of 100, then three equal readings; 100s down the same in reverse. `hi5000_ext_A` (low extreme, `C5c_20261011-195827_hi5000_ext_A_after.SAV`, army 0 slots 1,200 + 5,000 + new 3,800) and `hi5000_ext_B` (high extreme, `..._ext_B_after.SAV`: 3,800 + 5,000 + new 1,200), both turn 0720 staged. The probe was cancelled and left the army as it was (`..._probe_after.SAV`: 5,000 + 5,000).
  - **The earlier run's images were overwritten:** in `g2_checks-C5c-20261011-191316.jsonl` (and `-191005`) `sizes()` wrote the same `_split.png`, `_split_8.png`, `_split_140.png` on every reading, so only the last survives and none were kept or hashed; those two logs hold the OCR values only. The new run's readings reproduce the earlier values (floor 1,200, ceiling 3,800, steps of 1,000 and 100).
  - The raw `TUpDown` controls report range 0..1000, position 500 (`win_updown.c`) and are not the sizes; the clamp is in the dialog's handler.
- The remake's engine bounds are 1..troops-1 (rows_g2 D06).

### C7 (NEW-g2-2): a storm leaves an army aboard a damaged fleet with 3 to 8 percent of its men, or none `[P]` `[code]`

No new run: the cell R85sA of `run-exp-storms` (`2026-10-03-storms-and-losses-at-sea.md`) is exactly the case (Carthage fleet 0, 90 ships, condition 85, rough sea, army 2 aboard, 5 seeds; the fleet is damaged and not sunk: 90 to 65 ships in 5 of 5, condition 60 (four seeds) or 61 (one)). Re-read by `c7_storm_reanalysis.py` (hashes checked): army 2 before is **11,000 troops** in 5 units (li 4,000, hi 3,000, ar 2,000, lc 1,000, hc 1,000; `FIX_T4_R85sA.SAV`, turn 720). After the storm, turn 721:

| Seed | Army 2 after |
|---|---|
| 1 (`ST_R85sA_seed1_AUTO0721.SAV`) | **one unit, hi 678** |
| 2 | one unit, hc 312 |
| 3 | one unit, hi 850 |
| 4 | **gone** (fleet's carried army -1) |
| 5 | one unit, hc 312 |

(seeds 2 to 5: `t4_trials.json`, saves not kept.) The remake's loss of half in a round is far milder.

- **Storm damage to the fleet (`[code]`, `FUN_004514ec`, `FUN_0044b4f8`; all line numbers in `code_extract_g2.txt`).** The weekly sea block draws the storm damage `dmg` (54553-54592: `rand(100 - condition)/10` at least 1, doubled up to 5 in the season with `DAT_004a032e == 3`, tripled up to 8 when the fleet field at +0x18 is 1, then `2·dmg+1` when `FUN_004494e4` finds no own city next to the fleet and `dmg/2` otherwise; for condition 85 the first term is 1, the cell is in Spring, and the cell's rough-sea flag and open sea give 3 and then 7 `[derived]`). With `dmg` below 6 only the condition drops by `dmg` (54587-54589); with 6 or more it calls `FUN_0044b4f8(fleet, 100, dmg + 100)` (54591). `FUN_0044b4f8` (49843-49882) computes `x = max(1, 10000/(dmg+100))` (49853-49854, `FUN_00448fd8` is max) and **`d = x·x/100`** (49856): 86 for `dmg` 7 (x = 93), 88 for 6, 84 for 8. Then, **separately**, **ships lose `ships·d/300`** (49857-49859) and **condition loses `condition·d/300`** (49860-49862), each its own value. Cell R85sA: ships 90 - 90·86/300 = 90 - 25 = **65** (5 of 5), condition 85 - 85·86/300 = 85 - 24 = **61**.
- **A separate step, not storm damage:** a fleet with 0 supplies (the field at +0xe) loses 3 moves and `rand(2)` condition in the same weekly block (54618-54621, run after the storm call). R85sA's fleet had **80 supplies after the move** (the `before` state of all five trials, `run-exp-storms/t4_trials.json`: seed 1 line 4955, 80 in seeds 2 to 5 too), and 90 ships. The weekly block first subtracts the ship count from the supplies and clamps at zero (`max(0, supplies - ships)`, 54539-54542), so 80 - 90 gives **0 before the storm**; the zero-supply penalty (54618-54621) then fires after the storm call, so condition 61 becomes **60 or 61**: 60 in seeds 1, 2, 3 and 5, 61 in seed 4 (`t4_trials.json`; seed 1 `ST_R85sA_seed1_AUTO0721.SAV` has condition 60, supplies 0, ships 65). Condition below 40 is "lost at sea" (54593-54600); it was not reached. `dmg` 7 (d 86) is also what the data need: d 84 would leave 85 - 23 = 62, minus 0 or 1, so 61 or 62, and condition 60 was observed.
- **Damage to the carried army (`FUN_0044ae20`, 49573-49605, called at 49864):** each of the 20 slots loses **`(troops / (rand(15) + 105)) · d`** (integer division, `rand(15)` is 0..14: `FUN_0040284c`, 1587-1591; 49584-49591), before rounding about `d/(rand+105)`, 72 to 82 percent at d 86. Then, from slot 19 down to 0 (49592-49603), a unit with `0 < troops < limit/10` is removed when its label field is 0, or `< limit/5` when it is above 0 (`FUN_0044ac3c` copies the last occupied slot over it; 49430-49461). Back in `FUN_0044b4f8`, when `d > 70` (49865) it computes `n = FUN_0044a66c` (the last occupied slot index + 1, 49019-49039) and removes **`n·d/250 + 1`** random slots (49867-49876, each a `rand(FUN_0044a66c)`, recomputed each time). The earlier text said `units·d/250 + 1`: `n` is the slot span after the under-limit removals, not the five starting units.
- **Model of the army rule** (`c7_storm_model.py`, exact enumeration of all 15⁵ rolls at d 86 for the army of `FIX_T4_R85sA.SAV` turn 0720, `c7_storm_model.txt`; a uniform draw stands in for the game's generator): li and lc are always removed (at most 1,162 and 312, under limit/10 of 1,500 and 700), ar is never removed in that step (366 to 624, over 350), hi is removed only at its smallest result (592, under 600), hc only at 226 (under 250); one to three units survive (ar always, hi and hc usually), then `n·86/250 + 1` random removals (2 for n = 3, 1 for n = 1 or 2) leave one unit with probability 0.907 (ar 0.382, hi 0.329, hc 0.196) and **no unit with probability 0.093** (a single survivor, `n = 1`, is removed by the one removal). The single unit's troops: hc **312** only, hi **678, 764 or 850**, ar 366 to 624.
- **The five seeds against the model:** hi 678 (seed 1, `ST_R85sA_seed1_AUTO0721.SAV`, turn 0721), hc 312 (seeds 2 and 5), hi 850 (seed 3), none (seed 4): each outcome is one the model gives, and 312 exactly twice and 850 are its end values. The earlier statement that 678 lay "inside 592 to 850" is replaced: 592 is below the limit/10 line and removed, 678 is the next value (a roll giving a quotient of 27). No ar survived in 5 seeds, which the model gives probability about 0.09 (0.618⁵), not excluded. The `random_whole_unit_removals` field in `c7_storm_reanalysis.*` counts 5 starting units and is superseded by the model.

## What the remake does

`rows_g2.md`: MM01 selects any own marker regardless of moves (`ResolveLeftClickOnMarker`), which matches the original (the row's "differs" was the inventory's wording; the original also keeps a 0-move army selected and usable). MM03: `MoveArmy` goes as far as the moves allow ("spending 8 of 8 moves"), the same outcome; whether it sidesteps costly tiles was not compared. UA06/D05: Join joins two only, Rename acts on the first selected without a box, no R41 test. D06: spinners 1000s 0..1000 and 100s 0..900, engine 1..troops-1, accepts a 1-troop and a 100-troop split. NEW-g2-2: the remake halves the army per storm round.

## What this does not establish

- C3: only the army with 0 moves at its own position, in one save; the dialogs were opened and closed with OK unchanged, not used for transfers or splits (those are in earlier findings).
- C4: the tiles crossed by the sidestepping walk were not observed, only start, end and moves; one direction (north) and two terrain features (forest, river) were tried. The second walk call in `TUnitMap_MoveHumanArmy` was read, not isolated.
- C5: Join was tested for li only; the "total too large" refusal (R44) was not repeated. Split was tested in one fixed army (a 5,000 hi beside it) with unit label 0 (regular); mercenaries (R39) were not repeated. The size table was read from memory, not from the DAT file. The 100s and 1000s arrows' step (100 and 1,000) is seen on a 5,000 unit only.
- C7: the storm evidence is a synthetic cargo (an army put aboard by an edit, `run-exp-storms` R85sA); the five-unit army, one damage level (d 86, `dmg` 7) and 5 seeds. Seeds 2 to 5 rest on `t4_trials.json` (no saves). A natural storm with a carried army was not found; the formula's other values of `d` were recomputed, not observed. The derivation of `dmg` 7 reads `FUN_004494e4` as "an own city next to the fleet" and the +0x18 field as the rough-sea flag; neither was isolated. The model's random draws are uniform, not the game's generator. The `FUN_0044ab90` path (army emptied) was not read.
