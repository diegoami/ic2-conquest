# run-exp-v050-rules: data of the v0.5.0 rule reads

Task `docs/tasks/v050-rule-reads.md`; scripts in `runs/experiments/v050_rules/`. Binaries (saves, screenshots) are in the release `run-exp-v050-rules` as one tar.gz per batch; `MANIFEST-<batch>.txt` lists the archive's and every member's SHA-256 and `SAVES.sha256` the same hashes one per file.

## Findings so far (newest first; relay these early)

- **Q3 done, 2026-10-05.** Disbanding a queued recruitment loses the whole recruiting cost (nothing is refunded): treasury 1,880 → 1,880 twice; the entry leaves the queue and mobilisation falls by `1 + troops × 1000 div wealth` (floor): 32 → 30 → 28. `findings/2026-10-05-disbanding-a-queued-recruitment.md`.
- **Q2 done, 2026-10-05.** The Balance sheet's "Tribute" line is `taxBase div 4` (Rome 2,528 → 632), independent of the tax rate (632 at 10% and at 20%); Taxes = `taxBase × rate div 100`, Trade = partners' `taxBase div 12`. `findings/2026-10-05-balance-sheet-tribute-line.md`.
- **Q1 done, 2026-10-05.** Only the Supply army money arrows, the Army to army money arrows and the own-city refill cap a purse at 1,000; Join armies, the merge of an emptied army, the captured purse of a won battle and the AI's army merge add without a cap. Join of two 1,000 purses gave 2,000 in play; a "+100" click in Supply army then trimmed it to 1,000 and paid the treasury 1,000. The refill on a move (E12) is not reachable from a human move (two negative observations). `findings/2026-10-05-army-purse-writes-and-the-1000-cap.md`.

## Files

| File | What |
|---|---|
| `code_extract_<name>.txt` | the decompiled functions a finding cites, verbatim, first column = line number of `all_app_functions.txt` |
| `state_log.jsonl`, `steps.log`, `q*.log` | append-only logs of the plays: one memory-state record per step (nation treasury, mobilisation, queue, listed armies) and one text line per order |
| `q2_balance_values.tsv` | the Balance sheet screenshots read row by row |
| `claims_audit_output*.txt` | the claims audit (`claims_audit.py`), versioned; the newest is current. `claims_audit_output.txt` is the first run, which had five mismatches from mis-typed line anchors in the audit itself (not in the findings' numbers); `.v2` is the corrected run and `.v3` adds the Q2 cross-checks (newest = current) |
| `MANIFEST-*.txt`, `SAVES.sha256` | hashes of the archived binaries |

Notes: the first run of `q1_purse.py` was cut short (a click on Rome's tile only deselects the army, and the driver's fixed Supply-army coordinates miss in this environment); its entries are the first lines of `steps.log` and `state_log.jsonl` and are kept.
