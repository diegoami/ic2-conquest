# Disbanding a regular unit lowers mobilisation by 1 + troops × 1000 div wealth; a mercenary does not (in Change units and in Army to army transfer)

**Status:** draft finding from `ic2-conquest`, awaiting promotion. Question 5 of `docs/tasks/v050-rule-reads.md` (clone task T136, `imperial_conquest_2` #706). **Wine-only.** Natural state, nothing edited; fixture copies only.

**Tags.** `[derived]` = read from the decompile (function, address, line of `all_app_functions.txt`; code in `runs/experiments/data/run-exp-v050-rules/code_extract_q5_disband_unit.txt`). `[confirmed]` = seen in play with a save before and after.

**Answer.**
- **A regular unit disbanded in Change units lowers the nation's mobilisation by `1 + troops × 1000 div wealth`, floored at 0** `[derived]` `[confirmed]` (`TChangeArmyUnits_RemoveUnit` @ 004452C4: `mob := max(0, mob − 1 − troops × 1000 div wealth(+0x430))`, :45787-45792). Rome (wealth 2,577,000), HI 5,900: `5,900 × 1000 div 2,577,000 = 2`, so **30 → 27** (`Q5A_00_start.SAV` → `Q5A_01_after_disband_regular.SAV`). The division is an integer division (floor). It is the same expression that queueing a recruit adds (`TArmyRecruits_RecruitUnit` :56000-56005), but queueing caps the result at 100 and this subtracts without a cap, so the two are inverse only without clipping (see the T108 finding).
- **A mercenary unit does not change it** `[derived]` `[confirmed]`: the test is `slot +0 == 0` (:45787); a mercenary's `+0` is its label. Rome's army 1 after disbanding the hired Samnite (label 38): mobilisation 30 → 30.
- **Nothing else changes**: treasury unchanged (2,200), purse (100) and supplies unchanged; the army's troops fall by the unit's troops. No refund of any kind.
- **The same rule is in the other disband button**: Army to army transfer's two Disband buttons call `TArmyToArmy_RemoveUnit` @ 00442DD8 (:44483-44488, with `param_4 = 1` from `TArmyToArmy_Army1Disband` :44316 and `Army2Disband` :44402) with the identical formula `[derived]`. Transferring a unit between the armies (`param_4 = 0`, :44461) changes no mobilisation. Not run in play.
- **The value is committed at OK, not at Disband** `[derived]`: the dialog works on a copy (`+0x1D8` in `TChangeArmyUnits`, `+0x772` in `TArmyToArmy`), copied to the nation (`+0x442`) by `TChangeArmyUnits_OK` (:45820) and `TArmyToArmy_OK` (:44585); **Cancel discards it** (`TChangeArmyUnits_Cancel` :45839 does not write back).
- **Where a regular unit may be disbanded** `[derived]`: `TChangeArmyUnits_Disband` @ 004450C8 does nothing unless at least one row is selected (:45717-45718) and the Confirm "Are you sure you want to disband N unit(s)." is answered Yes (:45734). It then walks the 20 slots from the last to the first, only slots with troops > 0 that are selected (:45736-45742). **A regular unit (`+0 == 0`) is disbanded only when an own city lies in the 3 × 3 around the army** (`FUN_004494E4`, stored in the form at `+0x1D6` by `TChangeArmyUnits_InitializeForm` :45408-45410; the scan, :48086-48121, takes the last own city found); without one that unit is skipped and, after the loop, "An army must be near its own city to disband a regular unit." is shown once (:45743-45758); the other selected units are still processed. A mercenary has no such condition (:45743-45748). In Army to army transfer the same flag is computed for the selected army A (`TArmyToArmy_InitializeForm` :43793-43796, form `+0x770`) and also gates partner B's Disband (:44397, :44311). (The refusal was not run.)

## Method

- **Code.** `TChangeArmyUnits_Disband` @ 004450C8, `_RemoveUnit` @ 004452C4, `_OK` @ 00445378, `_Cancel`, `_InitializeForm` @ 004449F4 (copies the army record and the mobilisation word into the form), `TArmyToArmy_RemoveUnit`, `FUN_004494E4`, `FUN_00449018` (Chebyshev distance).
- **Play.** `runs/experiments/v050_rules/q5_disband_unit.py` (normal build, seed 12345, own display). Part A: copy of `run0-start-AUTO0720-seed12345.SAV`, army 0 at (100,37) next to Arretium (own city): army toolbar > Change units > row 3 (HI 5,900) > Disband > Yes > OK. Part B: copy of `merc-hire-free-0720.SAV`, army 1 at (120,53) next to Heraclea: row 6 (the Samnite mercenary) > Disband > Yes > OK. Saved before and after each; screenshots of the selection, the Confirm box ("Are you sure you want to disband 1 unit.") and the dialog afterwards.

## Evidence

Read from the saves with `state/sav.py` (`claims_audit.py` recomputes the expected values; wealth 2,577,000):

| Save | Treasury | Mobilisation | The army's units (troops; `merc` = label) | Purse / supplies |
|---|---|---|---|---|
| `Q5A_00_start.SAV` (army 0) | 2,200 | 30 | LI 4,800; HI 5,000; HI 5,200; **HI 5,900**; LC 900; HC 1,900 (23,700; all regular) | 100 / 170 |
| `Q5A_01_after_disband_regular.SAV` | 2,200 | **27** = 30 − 1 − 2 | the HI 5,900 gone (17,800) | 100 / 170 |
| `Q5B_00_start.SAV` (army 1) | 2,200 | 30 | six regular units and the **Samnite LI 3,868 (merc label 38)**, 25,868 | 100 / 176 |
| `Q5B_01_after_disband_merc.SAV` | 2,200 | **30** | the Samnite gone (22,000) | 100 / 176 |

Saves and screenshots: release `run-exp-v050-rules` (`batch-q4-q6.tar.gz`), hashes in `SAVES.sha256`.

## What this does not establish

- **The floor vs rounding** was separated for the queue (T108 finding: 4,000 → 1.55 → 1) but not here: 5,900 gives 2.29, the same under both. The code expression is the same integer division.
- **The refusal away from an own city, Cancel, the Army to army transfer's Disband buttons and several units at once** are `[derived]` only.
- **A unit disbanded below 0 mobilisation** (the floor at 0): code only.
- **Wine-only**, Rome, turn 0720.

## Reproduction

```text
python3 runs/experiments/v050_rules/q5_disband_unit.py    # about 3 minutes
python3 runs/experiments/v050_rules/claims_audit.py
```
