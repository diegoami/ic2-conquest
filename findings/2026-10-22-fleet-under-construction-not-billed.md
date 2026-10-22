# A fleet under construction is shown on the Balance sheet but not billed at the quarter

2026-10-22. **[confirmed]** (code + one paired play). Open item 12 of research PR #57
(`2026-10-22-manual133-contradictions-consolidated.md`), from the user manual (#133).

## Answer

- **Code.** The quarterly tick `FUN_00451B40` starts with the fleet upkeep: for each fleet with an owner
  (`+0x08 ≥ 0`) **and countdown −1** (`+0x0A == -1`, launched), the owner's treasury loses `3 × ships`
  (decompile `all_app_functions.txt` from line 54723, `2018c205…`). A fleet under construction (countdown 24..0) is skipped.
- **Play** (Wine, seed build `354d8265…532f`, seed 12345, run `run-exp-fleet-bill`). Both branches start from
  `M133_session1_AUTO0725.SAV` (Rome, 270 BC Spring week 11; turn 0725, whose End turn runs the quarterly tick):

  | Branch | Treasury at load | After the order | After the quarter (`AUTO0726`, turn 0726) | Quarter's change |
  |---|---:|---:|---:|---:|
  | A, no fleet (`FB_A_nofleet_after_quarter.SAV`) | 1,781 | 1,781 | 1,804 | +23 |
  | B, 50-ship fleet ordered (`FB_B_fleet50_after_quarter.SAV`) | 1,781 | 1,281 | 1,304 | +23 |

  B's fleet was still under construction after the tick (countdown 22). B ends exactly the 500-talent build cost
  below A: the 150 talents of upkeep (3 × 50) were **not** charged.
- **The Balance sheet differs from the bill.** g1 check G2 (`2026-10-11-g1-original-checks.md`) saw an 11-ship
  fleet under construction add 33 (3 per ship) to the sheet's Fleet line at once. So the sheet's Expenditure Total
  overstates the next quarter's bill by 3 per ship of every fleet still being built.

## What this does not establish

- One pair of branches, one 50-ship fleet, one quarter. The code reading covers every case.
- The launched-fleet charge itself is not re-measured here (rules-digest §3 and research's
  `upkeep-payment-and-desertion.md` give it).

## Evidence

- `runs/experiments/data/run-exp-fleet-bill/` (log, README, `SAVES.sha256`); runner `runs/experiments/fleetbill/run.py`.
- Saves: `M133_session1_AUTO0725.SAV` (`7d20dcf4…`, listed in `runs/experiments/data/run-exp-manual133/SAVES.sha256`),
  `FB_A_nofleet_after_quarter.SAV` (`adf4988e…`), `FB_B_fleet50_after_quarter.SAV` (`483287fc…`). They are on Drive,
  `IC2/artifacts/`, not in a release.
