# Join armies: the 20-unit gate counts slots up to the last occupied one (row L11, 20 units per army)

**Status:** a draft from `ic2-conquest`, awaiting promotion. Row L11's last `[derived]` bullet; refusal R03 in `2026-10-05-refusal-texts-and-conditions.md`. The research session asked for it on 2026-10-08 (ask A).

**Tag:** `[confirmed, partial]` for "20 units per army" (Join armies; the transfer-dialog path `TArmyToArmy_Army1Transfer` was not run). `[confirmed]` for the reading of `FUN_0044a66c`.

## Answer

- **The gate is `FUN_0044a66c(kept) + FUN_0044a66c(partner) < 21`**, and `FUN_0044a66c` returns **the index of the last occupied slot + 1**, not the number of units and not the first free slot. Two armies with 7 real units between them (kept: slots 0 and 15; partner: slots 0-4) are **refused** with R03, because 16 + 5 = 21. That settles the two readings in research's reports: the "first free unit slot" comment in `decompiled-mobilization-and-mercenary-restock.md` would give 1 + 5 = 6 and accept.
- 10 + 10 = 20 is **accepted**; 10 + 11 = 21 is **refused** with *"These 2 armies combined contain more than 20 units."* (OCR `'e These 2 armies combined contain more than 20 unis aK'`).
- **Where the units land on an accepted merge:** the partner's units are appended **after the kept army's last occupied slot**, and the kept army's gaps stay empty. The order is partner slot 0, then its last unit, then the next-to-last, and so on: the loop always moves slot 0, and the removal fills slot 0 with the last unit (`FUN_0044ac3c`). The kept army's moves become 0 and the partner is deleted.
- **A partner whose slot 0 is empty loses its units.** The merge loop runs only while the partner's slot 0 holds troops (:46988). With slot 0 empty it moves nothing, and the partner is still deleted (:46996). Case 5: the partner had 3,000 men in slots 1-3; after the Join the kept army had only its own 5 units, and Rome's armies went from 3 to 2. In normal play every removal compacts the slots (`FUN_0044ac3c` moves the last unit into the hole), so an army with slot 0 empty probably arises only in an edited save (`[derived]`).
- **On a refusal nothing changes in the game state.** The before and after saves differ in one byte: Rome's unit-map view origin x (nation +0x488, 92 → 102), which the selection click scrolled (see `2026-09-29-nation-view-origin-and-unit-map-clicks.md`). Armies and fleets are identical, and army 0 keeps its 3 moves.

| Case | Kept (army 0) slots | Partner slots | Gate value | Real units | Result | Kept army after |
|---|---|---|---:|---:|---|---|
| c1 | 0-9 | 0-9 | 20 | 20 | **accepted** | slots 0-9 own; 10 = P-0, 11-19 = P-9…P-1; moves 0 |
| c2 | 0-9 | 0-10 | 21 | 21 | **refused** R03 | unchanged, moves 3 |
| c3 | 0, 15 | 0-4 | **21** | **7** | **refused** R03 | unchanged |
| c4 | 0, 9 | 0-9 | 20 | 12 | **accepted** | slots 0, 9 own (1-8 still empty); 10 = P-0, 11-19 = P-9…P-1 |
| c5 | 0-4 | 1-3 (slot 0 empty) | 9 | 8 | **accepted, partner's 3 units lost** | slots 0-4 own only; partner deleted |

The partner was army 13 at (102,44). `FUN_00449d64` (:48596-48622) keeps the **last** adjacent own army in record order, and army 12 at (102,45) is also adjacent; both had the same layout, and the unit names (`S13-k`) show which one merged.

## Code (`code_extract_refusals.txt`, `code_extract_q1_purse.txt`)

```
// FUN_0044a66c @ 0044a66c  (:49021-49039)
iVar3 = -1; iVar1 = 0; puVar2 = &DAT_0047c1ec;
do {
  if (0 < *(short *)(puVar2 + param_1 * 0xa4 + 5)) iVar3 = iVar1;   // slot iVar1's troops (army +0x14 + 32*k)
  iVar1 = iVar1 + 1; puVar2 = puVar2 + 8;                            // 32 bytes per slot
} while ((short)iVar1 != 0x14);
return iVar3 + 1;                                                     // last occupied slot + 1

// TUnitMap_JoinArmies (:46982-46996)
iVar2 = FUN_0044a66c(kept); iVar3 = FUN_0044a66c(partner);
if (iVar2 + iVar3 < 0x15) {                                           // else R03 (:47011)
  if (FUN_0044a698(kept) + FUN_0044a698(partner) < 0x186a1) {         // troops; else R04
    while (0 < partner.slot[0].troops) FUN_0044acb4(partner, kept, 0);
    kept.money += partner.money; kept.supplies += partner.supplies;
    FUN_0044ab90(partner);                                            // partner deleted
    kept.moves = 0; ...

// FUN_0044acb4(src, dst, k) (:49466-49489): copy src.slot[k] to dst.slot[FUN_0044a66c(dst)], then FUN_0044ac3c(src, k)
// FUN_0044ac3c(army, k) (:49432-): moves the army's last occupied slot into slot k
```

## Evidence

run-exp-join-20-units: `<case>_{PRE,BEFORE,AFTER}.SAV` for c1_10_10, c2_10_11, c3_gap_value21, c4_gap_value20, c5_partner_slot0_empty (release `run-exp-join-20-units`; SHA-256 in `runs/experiments/data/run-exp-join-20-units/SAVES.sha256`); `probe_join20.py`, `probe_join20.log`, `probe_join20_*.json`.

## Method

`saves/fleet-port-antium-0734.SAV` (Rome armies 0 at (101,45), 12 at (102,45) and 13 at (102,44)). The 20 slots of each army are cleared, then the listed slots get a regular unit (label 0, heavy infantry, 1,000 men, quality 7, name `S<army>-<slot>`). The totals stay far below 100,000, so R04 cannot fire. Fast rollingsave seed exe, seed 12345, Xvfb :99. Load, save `BEFORE`, `g.join(0)` (select army 0, Join armies), save `AFTER`.

## Not established

- The transfer-dialog path (`TArmyToArmy_Army1Transfer`, its 20-unit branch).
- Whether normal play can produce an army with slot 0 empty (case 5's unit loss).
