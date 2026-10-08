# Recruit unit: an accepted order takes the first free queue slot

**Status:** a draft from `ic2-conquest`, awaiting promotion. It closes the `[derived]` "filled from the front" note in `2026-10-08-recruit-40-slots-gate-reads-slot-39.md` (research `02303d0`). The research session asked for it on 2026-10-08.

**Tag:** `[confirmed]` (Recruit unit at the capital).

## Answer

- One Recruit unit order fills **exactly one** slot: the **first slot whose troops field is 0**, scanned from slot 0 to slot 39. The order does not append after the last occupied slot.
- The new slot holds (state **0**, the chosen type, the troops, the city): here (0, hi, 3,200, 85). Each order took **320 talents** from the treasury and raised mobilization by 2 (30 → 32).
- Because the R46 gate reads only slot 39 and the search takes the first free slot, a queue with a hole can be refused while slots are free. That happens only when slot 39 is occupied before the lower slots, which needs a disband or a patched save. In case 3 the order filled slot 0 and then slot 39, and only then did R46 fire.

| Case | Occupied before | Order 1 → slot | Order 2 → slot | Order 3 |
|---|---|---|---|---|
| 1 empty queue | none | **0** | | |
| 2 gap at slot 1 | 0, 2-5 | **1** (not 6) | | |
| 3 gap at slot 0 | 1-38 | **0** | **39** | **refused** (R46); `c3_gap_slot0_2.SAV` and `_3.SAV` byte-identical (`606e7f87272622a3…`) |

Treasury per accepted order: 2,200 → 1,880 (cases 1-3, order 1) and 1,880 → 1,560 (case 3, order 2), so 320 each time; nothing was taken on the refusal. Mobilization went 30 → 32 → 34, unchanged on the refusal.

## Code (`TArmyRecruits_RecruitUnit`, `runs/experiments/data/run-exp-refusal-texts/code_extract_refusals.v2.txt`)

```
55949  if (*(short *)(&DAT_00474a90 + DAT_004a0320 * 0x494) < 1) {         // R46 gate: slot 39 troops (+0x420)
55961    sVar8 = -1; sVar3 = 0; puVar6 = &DAT_00474670;
55964    do {
55965      if ((*(short *)(puVar6 + DAT_004a0320 * 0x494 + 0x2e8) == 0) && (sVar8 == -1)) {   // +0x2E8 = slot troops
55966        sVar8 = sVar3;                                                  // first free slot
           }
55968      sVar3 = sVar3 + 1; puVar6 = puVar6 + 8;
55970    } while (sVar3 != 0x28);                                            // 40 slots
55972    puVar1 = &DAT_00474954 + DAT_004a0320 * 0x24a + sVar8 * 4;          // that slot
55973    puVar1[2] = troops; puVar1[1] = type; *puVar1 = 0;                  // state 0
55977/80 puVar1[3] = city (or the capital when no city is chosen)
55996    treasury (+0x438) -= (troops / 200) * price[type]                   // DAT_00478fd2 + type * 0x28
56000    mobilization (+0x442) += troops * 1000 / wealth (+0x430) + 1, capped at 100 by FUN_00448fd0
```

The 320 talents agree with `(3200 / 200) × price`, with a heavy-infantry price of 20. The dialog's *Initial cost* label was not read in this run, so the comparison with the label is `[derived]`.

Evidence: run-exp-recruit-slot-landing, `c1_empty_{PRE,0,1}.SAV`, `c2_gap_slot1_{PRE,0,1}.SAV`, `c3_gap_slot0_{PRE,0,1,2,3}.SAV` (release `run-exp-recruit-slot-landing`; SHA-256 in `runs/experiments/data/run-exp-recruit-slot-landing/SAVES.sha256`); `probe_landing.py`, `probe_landing.log`, `probe_landing_c1_empty_c2_gap_slot1_c3_gap_slot0.json`.

## Method

BASE.SAV (270 BC Spring week 1, Rome human), with Rome's 40 slots cleared and the listed slots set to (12, hi, 3,200, 85). Fast rollingsave seed exe, seed 12345, Xvfb :99. Load, save (`_0`), then per order `g.recruit(city_row=1, unit_type="hi", thousands=2)` and save (`_k`). The slots are compared between consecutive saves.

## Not established

- The mercenary path (a separate request, in progress).
- The *Initial cost* label text next to the 320 taken.
