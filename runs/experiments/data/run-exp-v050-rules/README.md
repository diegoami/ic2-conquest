# run-exp-v050-rules: data of the v0.5.0 rule reads

Task `docs/tasks/v050-rule-reads.md`; scripts in `runs/experiments/v050_rules/`. Binaries (saves, screenshots) are in the release `run-exp-v050-rules` as one tar.gz per batch; `MANIFEST-<batch>.txt` lists the archive's and every member's SHA-256 and `SAVES.sha256` the same hashes one per file.

## Findings so far (newest first; relay these early)

- **Q6 done, 2026-10-05.** A refused attack declares nothing: the original checks legality first (army selected, moves >= 1, adjacent), then asks "Are you sure you want to attack...?" (any relation but war), then declares war (relation 3 both ways, plus the target's allies), then attacks. Played as Gaul against Greece's Genua: army 4 tiles away, and adjacent with 0 moves: no box, relation 0/0 unchanged; adjacent with moves: box, No changes nothing, Yes: 3/3 and "GAUL DECLARES WAR ON GREECE." `findings/2026-10-05-refused-attack-declares-nothing.md`.
- **Q5 done, 2026-10-05.** Disbanding a regular unit in Change units lowers mobilisation by `1 + troops x 1000 div wealth` (HI 5,900: 30 -> 27); a mercenary does not (30 -> 30). Committed at OK; same rule in Army to army's Disband. `findings/2026-10-05-disbanding-a-regular-unit-lowers-mobilisation.md`.
- **Q4 done, 2026-10-05 (the task's premise is wrong; corrected after review).** The mercenary hire price is only a gate: refused when `purse < (troops x price div 1000) x quality`, nothing is subtracted (purse 30 -> 30 twice). Three different formulas: the gate, the dialog's "Quarterly cost" (`troops x price x quality div 1000`, an estimate) and the actual quarterly pay (`((troops div 200) x price x quality) div 5`, 30 for the Samnite, 28 for the HC the box calls 34; the army panel read 30 then 58). `findings/2026-10-05-mercenary-hire-price-is-a-gate-not-a-charge.md`.
- **Q3 done, 2026-10-05.** Disbanding a queued recruitment loses the whole recruiting cost (nothing is refunded): treasury 1,880 → 1,880 twice; the entry leaves the queue and mobilisation falls by `1 + troops × 1000 div wealth` (floor): 32 → 30 → 28. `findings/2026-10-05-disbanding-a-queued-recruitment.md`.
- **Q2 done, 2026-10-05.** The Balance sheet's "Tribute" line is `taxBase div 4` (Rome 2,528 → 632), independent of the tax rate (632 at 10% and at 20%); Taxes = `taxBase × rate div 100`, Trade = partners' `taxBase div 12`. `findings/2026-10-05-balance-sheet-tribute-line.md`.
- **Q1 done, 2026-10-05.** Only the Supply army money arrows, the Army to army money arrows and the own-city refill cap a purse at 1,000; Join armies, the merge of an emptied army, the captured purse of a won battle and the AI's army merge add without a cap. Join of two 1,000 purses gave 2,000 in play; a "+100" click in Supply army then trimmed it to 1,000 and paid the treasury 1,000. The refill on a move (E12) is not reachable from a human move (two negative observations). `findings/2026-10-05-army-purse-writes-and-the-1000-cap.md`.

## Files

| File | What |
|---|---|
| `code_extract_<name>.txt` | the decompiled functions a finding cites, verbatim, first column = line number of `all_app_functions.txt` |
| `state_log.jsonl`, `steps.log`, `q*.log` | append-only logs of the plays: one memory-state record per step (nation treasury, mobilisation, queue, listed armies) and one text line per order |
| `q4*.log`, `q5.log`, `q6*.log` | order logs of the Q4-Q6 plays |
| `q2_balance_values.tsv` | the Balance sheet screenshots read row by row |
| `claims_audit_output*.txt` | the claims audit (`claims_audit.py`), versioned; the newest is current. `claims_audit_output.txt` is the first run, which had five mismatches from mis-typed line anchors in the audit itself (not in the findings' numbers); `.v2` is the corrected run and `.v3` adds the Q2 cross-checks, `.v4` the Q4-Q6 sections with one mis-typed anchor, `.v5` is the current run (newest = current) |
| `MANIFEST-*.txt`, `SAVES.sha256` | hashes of the archived binaries |

Notes: the first run of `q1_purse.py` was cut short (a click on Rome's tile only deselects the army, and the driver's fixed Supply-army coordinates miss in this environment); its entries are the first lines of `steps.log` and `state_log.jsonl` and are kept.

## Reproducing the audit (any checkout)

```text
python3 runs/experiments/v050_rules/fetch_archive.py     # downloads the release archives, checks them against MANIFEST-*.txt, extracts into artifacts/run-exp-v050-rules/
python3 runs/experiments/v050_rules/claims_audit.py      # inputs: the archived saves, the tracked code extracts, dat_unit_prices.tsv, the tracked screen readings, the logs
python3 runs/experiments/v050_rules/row_source_audit.py  # row_source_audit.psv (rule, source line, quote, conditions) against the extracts and the findings
python3 -m unittest runs/experiments/v050_rules/test_claims_audit.py   # a doctored expected value must fail
python3 runs/experiments/v050_rules/check_dump_vs_extract.py   # optional: extracts against the Ghidra dump
```

Paths derive from the scripts' location (`paths.py`); `IC2_ARTIFACTS`, `IC2_DUMP` (default: the pinned dump in `~/ic2-work/decompile`, `harness/decompile.py`), `IC2_DAT`, `IC2_WORK_V050` override. `extract_dat_prices.py` reads the DAT file (SHA-256 recorded in `dat_unit_prices.tsv`), `q4_ocr_displayed_cost.py` and `q2_ocr_rows.py` read screenshots into the tracked tsv files, `archive_batch.py BATCH` packs the not yet archived binaries (saves/, inputs/, png) into `batch-BATCH.tar.gz`, writes `MANIFEST-BATCH.txt` and uploads. Plays (`q*.py`) need Wine, a private game folder copy and a free Xvfb display; they write only new versioned files.

## PR #47 review rework (2026-10-05)

New files: `row_source_audit.psv` and `row_source_audit_table*.tsv` (140 rows), `dat_unit_prices.tsv`, `q4_displayed_cost.tsv`, `q4_panel_pay.tsv`, `code_extract_rework_extra.txt`, `q1c.log`, `q4b.log`, `claims_audit_output.v6+` (the rewritten audit; earlier outputs kept), `MANIFEST-rework.txt`; plays `q1c_own_city_click.py` and `q4b_panel_pay.py`.
