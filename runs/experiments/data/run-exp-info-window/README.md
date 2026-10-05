# run-exp-info-window: the Information window (T140 for the clone's v0.5.0)

> **READY (2026-10-05, batch 1, pushed as commit 05b5990): priorities (a)-(e) are done, with code citations and in-play captures.** Batch 2 completed the rest of the panels, the coverage check and the findings draft `findings/2026-10-05-information-window-fields-and-bands.md`.
> Evidence: `code_word_tables.tsv` (tables and index expressions, decompile line numbers `F:<n>` in ReTools `all_app_functions.txt`),
> `band_edges.tsv` (every edge, confirmed or derived), `band_samples.tsv` (value, expected word, seen word, screenshot),
> `claims_audit_summary.txt` (0 mismatches). The answers:
>
> **(a) Bands.** All word tables are BSS filled from `Imperial Conquest 2.DAT` (loader `FUN_004481a0`), 11-byte strings.
> *Unity* (nation): `unity div 100` (truncating) into the table: 0-4 `very low`, 5 `low`, 6 `normal`, 7 `high`, 8 `very high`, 9 `excellent`,
> index 10+ prints nothing; so words change at 500, 600, 700, 800, 900 and at 1000 the word goes blank (unity is capped at 990 in play, so blank is unreachable).
> *Loyalty* (city): the same table, `loyalty div 10`: 0-49 `very low`, 50-59 `low`, 60-69 `normal`, 70-79 `high`, 80-89 `very high`, 90-99 `excellent`, 100+ blank.
> *Morale* (own army): `(m-51) sar 2` (or `(m-48) sar 2` below 51) into the same table from entry 4: 51-54 `very low`, 55-58 `low`, 59-62 `normal`,
> 63-66 `high`, 67-70 `very high`, 71-74 `excellent`, 75+ blank (the saves reach 73). *Quality* (unit lists, mercenaries): no band, the field 0..9 is the index:
> 0-3 `not ready`, 4 `very poor`, 5 `poor`, 6 `average`, 7 `good`, 8 `very good`, 9 `elite`, 10+ blank.
> Also found: foreign-city *Tribute* word: field `<=10` `poor`, 11-30 `moderate`, 31-100 `rich`, 101-10000 `very rich`, above 10000 the number is shown instead.
> **(b) Fortification bracket** = the sum of `troops` over ALL of the controlling nation's recruit slots whose city is this city, whatever their state
> (a state-24 trained unit counts), shown only when the sum is positive, own or foreign city. So the digest ("the queue is the garrison") is right and the
> help ("conscripts being trained") is only partly right. Staged and seen: 1,000 (state 0) + 2,000 (state 24) at one city showed `61% (3,000)`.
> **(c)** per unit slot `s = i16(trunc(troops / 200) * price[type])` (the product is stored in a signed 16-bit `short`, F:41084; price = DAT unit table +0x24, quarterly): **Regulars cost** = sum of `s` over regular slots (label 0); **Mercenary pay** = sum of `trunc((s * quality) / 5)` over mercenary slots (label != 0, int product, signed truncating division, F:41089); the two sums are 32-bit and not narrowed; plain integers, text `talents per quarter`, own army only. (Revised in the PR #46 rework: batch 1 said 'unrestricted'.)
> **(d) Sea** = `calm` when the fleet's `+0x18` field is 0, else `rough`; that field is the map code under the fleet (0 sea, 1 storm square), cleared and re-rolled
> weekly by the weather overlay (`FUN_00451304`) and copied from the destination cell on every fleet step. No season, ship or supply rule is involved.
> **(e) Foreign nation panel**: Nation, Leader, Capital, Cities (plain integer), Population (`1,234,000`, thousands separators), Unity (word),
> `Tax rate N%`; Mobilized and Treasury are blank for a foreign nation. Relations rows: `<Name>` then the word at the right; the word table is
> `peace, trade, ally, war`, but the code prints a word only when the value is > 0, so peace (0) is really blank, as is any value <= 0; a conquered nation's row is
> `( X conquerred by Y )`; the nation's own row is blank.

Rule 6 holds: every output here is tracked and versioned (never overwritten); screenshots and staged saves are in the GitHub release `run-exp-info-window`
as per-batch tar.gz archives, listed with SHA-256 in `MANIFEST-<batch>.txt` and `SAVES.sha256`.

## Files
- `captures.tsv`: every capture (batch, save, kind, target, staged values, screenshot name and SHA-256, OCR text).
- `claims_audit_*`: the audit of every captured panel line against the code model (`runs/experiments/info_window/panel_model.py`).
- `band_samples.tsv`, `band_edges.tsv`: per staged value the expected and the seen word; per edge confirmed or derived.
- `code_word_tables.tsv`: the tables as the DAT holds them.
Scripts: `runs/experiments/info_window/` (`iw_lib.py` own display :730 and game folder `~/ic2-work-info`, `stage.py` L1 save editor, `batch_a*.py`, `audit.py`, `edges.py`).
