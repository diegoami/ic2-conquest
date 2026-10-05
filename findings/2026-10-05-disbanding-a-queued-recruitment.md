# Disbanding a queued recruitment: the whole recruiting cost is lost, nothing is refunded, and mobilisation falls back by 1 + troops × 1000 div wealth

**Status:** draft finding from `ic2-conquest`, awaiting promotion. Question 3 of `docs/tasks/v050-rule-reads.md` (clone task T108, `imperial_conquest_2` #566). **Wine-only.** Natural state, nothing edited; fixture copies only.

**Tags.** `[derived]` = read from the decompile (function, address, line of `all_app_functions.txt`; the code is in `runs/experiments/data/run-exp-v050-rules/code_extract_q3_disband_queue.txt` with those line numbers). `[confirmed]` = seen in play with a save before and after.

**Answer.**
- **100% of the money already invested is lost.** The cost `troops div 200 × recruitPrice[type]` is taken from the treasury when the unit is queued (`TArmyRecruits_RecruitUnit` @ 00454E78, :55996-55999), if the order passes its gates: the nation's queue word (`+0x420`) is below 1, i.e. fewer than 40 units ("You have reached your limit of 40 units.", :55949, :56033); mobilisation is not already 100 ("Your mobilisation rate is already 100%.", :55950-55953); the chosen city has fortification above 74, or is the capital, or the list row is "All cities" (:55956-55958; else "This city's fortification has fallen below 75%.", :56026); a unit type is chosen (:55959). Disbanding the entry (`TArmyRecruits_DisbandUnits` @ 004553B0 → `FUN_0044A610`) never writes the treasury: no refund, whether the unit is "not ready" or ready `[derived]`. In play, two disbands left the treasury at 1,880 both times `[confirmed]`.
- **The queue entry goes and the entries after it shift up** (`FUN_0044A610` @ 0044A610, :49003-49013: each later slot's 8 bytes are copied over the previous one), and the nation's "queue full" word (`+0x420`) is cleared (:49014) `[derived]`; the unit count fell 5 → 4 → 3 `[confirmed]`.
- **Mobilisation is given back**: `mobilisation := max(0, mobilisation − 1 − troops × 1000 div wealth)` per disbanded entry (:56157-56166), the reverse of what queueing added (`mobilisation := min(100, mobilisation + troops × 1000 div wealth + 1)`, :56000-56005) **only when the recruit order did not hit the cap of 100 and the formula's inputs (troops, wealth) are unchanged in between** `[derived]`: the increase is capped at 100, the decrease is not, so from 99, with a unit whose step is 2 (`troops × 1000 div wealth` = 1, plus 1), a recruit gives 100 and its disband gives 98, not 99. The division is an integer division (floor): HI 3,200: 32 → **30** (1.24 → 1); HI 4,000: 30 → **28** (1.55 → 1, not 2) `[confirmed]`.
- **The order**: select one or more entries in the unit list of a city (ctrl for several), press Disband, answer "Are you sure you want to disband N unit(s)." (Yes / No / Cancel, :56133-56148); nothing happens if no entry is selected (:56131-56132) or the answer is not Yes (:56148). Entries are processed from the last list row to the first, only the selected ones (:56150-56170), each with the formula above using its own troops (the queue slot `+0x2E8`, :56157). No distance, readiness or ownership condition. (A wealth of 0 would divide by zero; not reachable in these saves.)
- So queueing and disbanding the same unit costs the whole recruitment price and nothing else: the net effect on the nation is `−cost` talents and, **in this uncapped case with unchanged wealth**, the mobilisation back where it was (32 → 30 here, the value before the recruit in `run0-start-AUTO0720-seed12345.SAV`); near 100 or after wealth changed it need not be.

## Method

- **Code.** Read `TArmyRecruits_DisbandUnits`, `FUN_0044A610`, `TArmyRecruits_RecruitUnit` and `TArmyRecruits_MobilizeUnits`. The recruit price is the table at `DAT_00478FD2` (stride 0x28), the quarterly price the one at `DAT_00478FD4`.
- **Play.** `runs/experiments/v050_rules/q3_disband_queue.py` on a copy of `recruit-hi3200-0720.SAV` (Rome, 0720: treasury 1,880 after queueing HI 3,200 for 320; mobilisation 32; five queued units at Rome), the normal build, seed 12345, own display. Army recruits (toolbar) > city Rome > the unit row > Disband > Yes. Saved after each disband. The screenshots of the selected row, of the Confirm box and of the dialog afterwards are in the release.

## Evidence

Values read from the saves with `state/sav.py` (`claims_audit.py` recomputes each); wealth 2,577,000.

| Save | Treasury | Mobilisation | Queue at Rome (troops, state) |
|---|---|---|---|
| `Q3_00_start.SAV` (= `recruit-hi3200-0720.SAV`) | 1,880 | 32 | LI 5,500 (9), HI 3,500 (13), HI 4,000 (17), HC 1,000 (17), **HI 3,200 (0, "not ready")** |
| `Q3_01_after_disband_hi3200.SAV` | **1,880** (320 not refunded) | **30** = 32 − 1 − 3,200×1000 div 2,577,000 (1) | LI 5,500, HI 3,500, HI 4,000, HC 1,000 |
| `Q3_02_after_disband_hi4000.SAV` | **1,880** | **28** = 30 − 1 − 4,000×1000 div 2,577,000 (1) | LI 5,500, HI 3,500, HC 1,000 (the entries after the removed one shifted up) |

- The queueing cost was 320 (`run0-start-AUTO0720-seed12345.SAV` treasury 2,200 → 1,880, `3,200 div 200 × 20`), so 320 talents were lost by the first disband. The 4,000 entry was queued by the new-game fill: its price (`4,000 div 200 × 20` = 400) is `[derived]`, not observed.
- The second disband separates the floor from rounding: 4,000 × 1000 / 2,577,000 = 1.55, so rounding would give 27 and the floor gives 28; the save shows 28.

## What this does not establish

- **The price paid for entries that were already in the queue before the first save** (the new-game fill) was not observed; the rule is that nothing is refunded for any entry.
- **The quarterly "Army recruits" expense** (billed per occupied queue slot in the city-unit loop of `FUN_00451B40`, `TBalanceSheet_PaintBalance` :55486-55499) stops with the entry by the code; the Balance sheet after the disband was not read.
- **Several entries at once**: processed in sequence by the same formula (each its own `1 + troops×1000 div wealth`); not run with a multi-selection.
- **Wine-only**, Rome, one turn.

## Reproduction

```text
python3 runs/experiments/v050_rules/q3_disband_queue.py     # about 3 minutes
python3 runs/experiments/v050_rules/claims_audit.py
```
