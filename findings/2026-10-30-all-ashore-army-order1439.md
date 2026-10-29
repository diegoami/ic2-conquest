# All-ashore AI embark with several live armies: the original appends the receiver, and the next sweep moves it into the source's slot

**Tag:** [confirmed] in emulation of the pinned unpatched EXE (`9d753d5d…`) for the table order immediately after the embark
and after the dead-record sweep. [derived] (code reading) for when the sweep runs relative to the rest of the turn. No game run.
**Task:** imperial_conquest_2#1439 (T216 follow-up), delegated by research on 2026-10-30. It extends
`2026-10-26-fleet-overflow-receiver174.md` (Research PR89), which measured one army only. Remake compared: v0.8.4
(`d9cc71b`), `EmbarkArmyCommandHandler.cs` lines 111–160.

## Answer

1. **At the embark, the original appends.** In all four controls, the overflow helper F8FC's allocator 49F08 creates the land
   receiver as a **new raw record at index = count**, and the count word goes 5 → 6. The emptied source is then deleted by
   AB90, which **tombstones it in place**: owner −1, troops 0, position the fleet's (40,33). **ABE0 (compaction) is not
   called**, and an existing tombstone is **not reused** (case `source2-of5-tombstone1`). This holds for the source at raw
   index 0, 2 and 4 of five live armies.
2. **The next sweep moves the receiver into the source's slot.** `FUN_0044adb0` walks the army table from the top index down
   and, for each record with owner −1, calls ABE0(i). ABE0(i) is a **swap-remove**: it copies the last record into slot i,
   repoints any fleet link to the moved record, and decrements the count (dump :49396–49426, :49537–49568). With the source's
   tombstone the only dead record, the appended receiver (last) lands **exactly at the source's index**. In the controls the
   swept order is `[receiver, F1, F2, F3, F4]`, `[F2, F1, receiver, F3, F4]` and `[F4, F1, F2, F3, receiver]`.
3. **The remake's v0.8.4 in-place replacement equals the swept state** for these cases. Its receiver takes the source's
   live-model index (with a new id, `<source>-overflow`). For a partial overflow it appends, which equals the original's
   allocation at count.

| Case (`v2_<case>.json`) | Raw table after B79C (index: name) | After the sweep | Remake v0.8.4 live order |
|---|---|---|---|
| `source0-of5` | 0 †, 1 F1, 2 F2, 3 F3, 4 F4, **5 C** | **C**, F1, F2, F3, F4 | **C**, F1, F2, F3, F4 |
| `source2-of5` | 0 F2, 1 F1, 2 †, 3 F3, 4 F4, **5 C** | F2, F1, **C**, F3, F4 | F2, F1, **C**, F3, F4 |
| `source4-of5` | 0 F4, 1 F1, 2 F2, 3 F3, 4 †, **5 C** | F4, F1, F2, F3, **C** | F4, F1, F2, F3, **C** |
| `source2-of5-tombstone1` (index 1 already dead) | 0 F2, 1 †, 2 †, 3 F3, 4 F4, **5 C** | F2, **F4**, **C**, F3 | F2, **C**, F3, F4 (if the remake dropped the old dead record in order) |

† = tombstone (owner −1, troops 0); C = the receiver (6000 troops, the source's units).

## Where the orders differ, and when

- **Between the embark and the next sweep** (derived from the code):
  - The army phase `FUN_0044f31c` snapshots the count when it starts (`sVar3 = DAT_004a0324`, :52922), so the appended
    receiver is **not visited** in the rest of that phase; the tombstone is skipped (owner ≠ nation).
  - The sweep runs only in `FUN_00451fdc`: once at its start, then before each AI seat's `FUN_0044fa20` (:54946, :54950).
    No sweep runs between the last AI seat and the next human seat.
  - So when the embarking seat is the **last AI seat before a human seat**, the human turn, and the autosave written at its
    start, see the **uncompacted** table (tombstone at the source index, receiver last) until the human's End turn.
- **With another tombstone in the table**, the sweep's swap-remove reorders unrelated armies (F4 moves into the older dead
  slot). This is the general dead-record sweep, not the embark path. Whether the remake keeps dead records or removes them
  preserving order was not checked here.

## What this does not establish

- Play: no live control. The autosave timing and the turn-order consequence above are derived from the code.
- Save/load of an uncompacted table: whether loading such a SAV keeps the tombstone and the receiver's last position. The
  load path was not traced; no sweep call was found outside `FUN_00451fdc`.
- The remake's dead-army removal policy (the tombstone row's remake column is conditional).
- More than one embark in the same phase, and fleets (FUN_0044ad7c, the fleet sweep, was not exercised).

## Evidence

- Script: `runs/experiments/ashore1439/original.py`, built on `runs/experiments/fleet-overflow174/original.py` (the #174
  complete-RAM baseline `fleet-controls-v3/embark-units-4000-2000`). It runs unmodified B79C (EAX = the source index), then
  unmodified `FUN_0044adb0`. It asserts no Random call.
- Data: `runs/experiments/data/run-exp-ashore1439/v2_*.json`: the tables before, after and after the sweep, and the calls
  (embark, overflow, allocate, landscan, moveunit, removeunit, deletearmy). `v1_*` is the same run without the sweep.
- RAM and diagnostic SAV projections stay private in `artifacts/run-exp-ashore1439/private-v1|v2/`, as for #174; they are not
  original Save As outputs. Saves: none new (synthetic RAM projections only).
- Decompile `all_app_functions.txt` (SHA-256 `2018c205…`): ABE0 :49396, ADB0 :49537, F31C :52899, 451FDC :54940.
