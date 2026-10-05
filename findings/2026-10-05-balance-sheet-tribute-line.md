# The Balance sheet's "Tribute" line is the nation's tax base div 4: independent of the tax rate, and credited every quarter

**Status:** draft finding from `ic2-conquest`, awaiting promotion. Question 2 of `docs/tasks/v050-rule-reads.md` (clone task T109, `imperial_conquest_2` #567). **Wine-only.** Natural state, nothing edited.

**Tags.** `[derived]` = read from the decompile (function, address, line of `all_app_functions.txt`; the functions are in `runs/experiments/data/run-exp-v050-rules/code_extract_q2_balance.txt` with those line numbers). `[confirmed]` = seen in play with a save and a screenshot.

**Answer.**
- **"Tribute" is `nation.taxBase div 4`** `[derived]` `[confirmed]`, where `taxBase` is the signed 16-bit word at nation `+0x44C` (the stored tax base, rebuilt each quarter from the cities). Rome at 0720: taxBase 2,528 → **Tribute 632**.
- **It does not depend on the tax rate** `[confirmed]`: at 10% and at 20% the Tribute line was 632 in both screenshots; only Taxes moved (252 → 505) and so the revenue total (913 → 1,166).
- **The three revenue lines** `[derived]` (`TBalanceSheet_PaintBalance` @ 0045376C): **Taxes** = `taxBase × taxRate div 100` (:55439-55440), **Tribute** = `taxBase div 4` (:55445-55451; for a negative word `(x + 3) >> 2`, i.e. truncation toward zero), **Trade** = `FUN_004499EC(nation)` (:55457) = the sum, over all 16 nations `j` (:48427-48434), of `taxBase[j] div 12` (signed division, :48430) for every `j` whose relation entry to this nation is 1 (trade) or 2 (alliance) (:48428-48429), accumulated in a signed 16-bit word (:48424, :48430). **Total** = their sum (:55456, :55461-55462). All three are `[confirmed]` on Rome (below).
- **It is the same number the quarterly tick credits**, for every nation whose unity word (`+0x440`) is above 0 (:54866): after mobilisation `max(0, mob − 3)` (:54867-54869), `treasury += taxBase × rate div 100 + ((taxBase + 3) >> 2 for a negative taxBase, else taxBase >> 2) − cities × 7 − wealth div 20000`, then `+ FUN_004499EC` (`FUN_00451B40` @ 00451B40, :54874-54879) `[derived]`, so the Balance sheet's revenue column is the quarterly credit's three positive terms. The expenditure column is the negative terms and the unit upkeep (Administration = `wealth div 20000 + cities × 7`, :55466).
- **It is not a sum of city "tribute" fields read live.** The stored taxBase at 0720 (2,528) differs from the live sum of the cities' contributions `Σ tribute × pop div maxPop << 2` (2,464): the word is the new-game value until the first quarterly rebuild, and Tribute follows the word `[confirmed]` (arithmetic from `Q2_00_start_tax10.SAV`).
- For the clone: a line "Tribute" worth a quarter of the nation's tax base, shown beside Taxes and Trade, not scaled by the tax rate.

## Method

- **Code.** Read `TBalanceSheet_PaintBalance` and `FUN_004499EC`; matched the 12 value labels to the stores by the order of the form's fields: the form's controls in the exe's resource are `lbl_tax`, `lbl_tribute`, `lbl_trade`, `lbl_totrev`, `lbl_balance`, `lbl_debtlimit`, `lbl_totexp`, `lbl_admin`, `lbl_fleets`, `lbl_recruits`, `lbl_regs`, `lbl_mercs` (`runs/experiments/data/run-exp-feature-inventory/coverage_entries.tsv`, rows `control:TBalanceSheet|TLabel|lbl_…`), and the function writes the fields at `+0x228, +0x22C, +0x230, +0x234, +0x238, +0x23C, +0x240, +0x244, +0x248, +0x24C, +0x250, +0x254` in that order. The play shows the match is right (below), so this does not rest on the field order alone.
- **Play.** `runs/experiments/v050_rules/q2_balance.py` on a copy of `run0-start-AUTO0720-seed12345.SAV` (Rome human, treasury 2,200, tax 10%, normal build, seed 12345, own display): open Strategy > Balance sheet (toolbar button), screenshot, close; Taxation to 20% (the slider); the sheet again. A save after each state (`Q2_00_start_tax10.SAV`, `Q2_01_tax20.SAV`). The screenshots' values were read by tesseract on a crop of each value box (`q2_ocr_rows.py` → `q2_balance_values.tsv`) and checked by eye on the screenshots.

## Evidence

The expected values are recomputed from the saves by `claims_audit.py` (taxBase, tax rate, cities, wealth, and Illyria's taxBase for Trade); the read values are `q2_balance_values.tsv`.

| Line | Formula | Rome, tax 10% (`Q2_00_tax10_balance_sheet.png`) | Rome, tax 20% (`Q2_01_tax20_balance_sheet.png`) |
|---|---|---|---|
| Taxes | `2,528 × rate div 100` | 252 = 252 | 505 = 505 |
| **Tribute** | `2,528 div 4` | **632 = 632** | **632 = 632** |
| Trade | Illyria (relation 1): `356 div 12` | 29 = 29 | 29 = 29 |
| Total revenue | sum | 913 = 913 | 1,166 = 1,166 |
| Administration | `2,577,000 div 20,000 + 25 × 7` | 303 = 303 | 303 = 303 |
| Balance | treasury | 2,200 | 2,200 |
| Debt limit | `wealth div 500`, capped at 20,000, then rounded down: to a multiple of 100 below 5,001; of 500 from 5,001 to 10,000; of 1,000 from 10,001 to 20,000 (:55541-55553). 2,577,000 div 500 = 5,154 → multiple of 500 → | 5,000 | 5,000 |

- Saves and screenshots are in release `run-exp-v050-rules` (`batch-q1-q3.tar.gz`), hashes in `SAVES.sha256`.
- Rome trades only with Illyria at 0720 (`relations {'Gaul': 3, 'Illyria': 1, 'Macedonia': -8}` in the save), so Trade is Illyria's `taxBase div 12`.

## What this does not establish

- **The tick's credit was not re-measured here.** The tribute term of the quarterly credit is `[derived]` from `FUN_00451B40`; the research repo's `upkeep-payment-and-desertion.md` reports the whole formula exact for the human nation in all 6 quarter pairs.
- **A negative tax base** (a nation that lost cities) shows the `(x + 3) >> 2` form; not seen in play.
- **Which line the original help calls "tribute paid"**: the help text and the nation panel were not part of this task.
- **Wine-only**, one nation.

## Reproduction

```text
python3 runs/experiments/v050_rules/q2_balance.py      # about 2 minutes
python3 runs/experiments/v050_rules/q2_ocr_rows.py     # reads the screenshots into q2_balance_values.tsv (new version each run)
python3 runs/experiments/v050_rules/fetch_archive.py      # once: the released saves and screenshots into artifacts/ (hash-checked)
python3 runs/experiments/v050_rules/claims_audit.py       # inputs: the saves, the tracked code extracts and readings; row_source_audit.py checks each rule row
```
