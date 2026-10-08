# Army to army transfer: the 20-unit check per unit, and what gaps in a target army do

**Status:** a draft from `ic2-conquest`, awaiting promotion. The research session asked for it on 2026-10-08. It is the transfer-dialog path of L11's "20 units per army" bullet (R28 / R31 in `2026-10-05-refusal-texts-and-conditions.md`) and extends `2026-10-08-join-armies-20-unit-gate-counts-last-slot.md` (research `6466d56`).

**Tag:** `[confirmed]` for cases c1, c3, c4 and c5. `[confirmed]` for the observations in c2, c2b and c6; their cause is `[derived]` or open (see below).

## Answer

- **The check is per unit, highest selected slot first, and it reads the target copy's slot 19.** A target with 18 units and 3 selected source units: slots 2 and 1 move, landing in the target's slots 18 and 19. Then the **lowest-slot unit (slot 0) is refused**, with **one** box, R28 *"This army already has 20 units."* (`TArmyToArmy_Army1Transfer` :44118-44155: the loop runs `sVar9 = 0x13 … 0`, the test is `*(short *)(param_1 + 0x750) < 1`, where +0x750 is the target copy's slot 19 troops). **c1**
- **The second button behaves the same.** Army2Transfer, R31, with the 18 + 3 case in the other direction: slots 2 and 1 move to slots 18 and 19, slot 0 is refused, one box. **c4**
- **Cancel after a clamped transfer writes nothing.** The save's army table is byte-identical before and after. The dialog works on copies (+0x24c and +0x4dc); only `TArmyToArmy_OK` writes them back (:44585-44603). **c5**
- **Moved units land at the target's unit *count*, not at last occupied + 1 and not in the first free slot.** Target slots {0, 9}: the two moved units went to **slots 2 and 3** (`TArmyToArmy_MoveUnit` :44440-44446 writes at `TArmyToArmy_UnitsTotal(target)`; that function is not in our extracts, and the observation fits a count of occupied slots). **c3**
- **Gaps make this placement destructive.** Target slots {0, 2} (count 2): the moved unit was written into **slot 2, over the target's unit there** (S13-2, 1,000 men, lost). The source army, now empty, was removed. **c6**
- **A partner whose only unit is in slot 19 is opened as "Split army", and the partner is deleted on OK and on Cancel.** Same toolbar button (Transfer units), and no new army is created (the army count is 14 before and after the click). But the dialog's caption is **"Split army"** (`TArmyToArmy_InitializeForm` :43782-43783 sets that caption when the form's flag `+0x778`, `param_1[0x1de]`, is set). The transfer of S0-0 is refused with R28. After **OK** (c2) and after **Cancel** (c2b) the partner, army 13, is gone together with its unit; `TArmyToArmy_Cancel` deletes the partner when that flag is set (:44656-44657). The flag is set by `TUnitMap_ArmyToArmyTransfer` (0x447288) or by `FUN_00441b50`, neither of which is in our extracts. The `[derived]` guess is that the dialog treats a partner whose slot 0 is empty as a new, empty split partner.

| Case | Army 0 (left) slots | Partner slots | Moved from | Caption | Box | Result |
|---|---|---|---|---|---|---|
| c1 | 0-2 | 0-17 | left, rows 0-2 | Army to army transfer | R28 ×1 | S0-2 → 18, S0-1 → 19; S0-0 stays |
| c2 | 0 | 19 | left, row 0 | **Split army** | R28 | S0-0 stays; **partner deleted** (its unit lost) |
| c2b | 0 | 19 | left, row 0, **Cancel** | **Split army** | R28 | **partner deleted** (its unit lost) |
| c3 | 0-1 | 0, 9 | left, rows 0-1 | Army to army transfer | none | S0-1 → **2**, S0-0 → **3**; army 0 removed (empty) |
| c4 | 0-17 | 0-2 | right, rows 0-2 | Army to army transfer | R31 ×1 | S13-2 → 18, S13-1 → 19; S13-0 stays |
| c5 | 0-2 | 0-17 | left, rows 0-2, **Cancel** | Army to army transfer | R28 | army table byte-identical |
| c6 | 0 | 0, 2 | left, row 0 | Army to army transfer | none | S0-0 → slot 2, **overwriting S13-2**; army 0 removed |

The partner was army 13, (102,44), in every case. Army 12, (102,45), is also adjacent and had the same layout; it was untouched each time.

**Reachability:** c2, c2b, c3 and c6 need an army with gaps in its slots. In normal play the slots stay packed: removals compact them (`TArmyToArmy_RemoveUnit` shifts the higher slots down, :44490-44500; `FUN_0044ac3c` moves the last unit into the hole), so these cases probably arise only in an edited save (`[derived]`). This is the same caveat as the Join case-5 unit loss.

## Evidence

run-exp-transfer-20-units: `<case>_{PRE,BEFORE,AFTER}.SAV` for c1_18_plus_3_left, c2_target_only_slot19, c2b_target_only_slot19_cancel, c3_target_gap_0_9, c4_18_plus_3_right, c5_18_plus_3_cancel, c6_target_gap_0_2, plus `c1_18_plus_3_left_selection.png` (all three rows selected) (release `run-exp-transfer-20-units`; SHA-256 in `runs/experiments/data/run-exp-transfer-20-units/SAVES.sha256`); `probe_transfer20.py`, `probe_transfer20.log`, `probe_transfer20_*.json`. Three failed attempts, all from harness problems, are kept as `attempts-1-3.tar.gz` and described in `attempts.log`; none of them is cited.

## Method

`saves/fleet-port-antium-0734.SAV`: Rome army 0 at (101,45), with armies 12 at (102,45) and 13 at (102,44) adjacent. The 20 slots of armies 0, 12 and 13 are rewritten with regular heavy-infantry units of 1,000 men, quality 7, named `S<army>-<slot>`, so troops stay far below 100,000 (R29/R32 cannot fire) and no army is aboard a fleet (R30/R33). Fast rollingsave seed exe, seed 12345, Xvfb :99. Load, save `BEFORE`; select army 0, press Transfer units, wait for the dialog under either caption; ctrl-click the rows (the rows are 10 px high); press that list's Transfer; collect boxes; press OK or Cancel; save `AFTER`.

## Not established

- The body of `TUnitMap_ArmyToArmyTransfer` (0x447288) and `TArmyToArmy_UnitsTotal`: what sets the split flag, and whether `UnitsTotal` is exactly the count of occupied slots.
- Whether normal play can produce an army with a gap.
