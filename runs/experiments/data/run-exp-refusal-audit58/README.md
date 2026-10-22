# run-exp-refusal-audit58: the predicate audit of the refusal-texts catalogue (issue #58)

Finding: `findings/2026-10-05-refusal-texts-and-conditions.md`, section "Predicate audit (issue #58)". Scripts in
`runs/experiments/refusal_texts/`: `cflow.py` (control flow of a decompiled function), `predicates_def.py` (writes the table),
`predicate_audit.py` (checks the table against the code and the catalogue against the table), `apply_corrections.py`.
Tests: `python3 -m tests.test_refusal_predicate_audit`. No Wine, no saves: every input is tracked except the optional dump
(`all_app_functions.txt`, pinned SHA-256 `2018c205…`, used only to resolve lines outside the extract).

Files are never overwritten (rule 6): a re-run writes `<stem>.vN<ext>` beside the old one.

| file | what |
|---|---|
| `predicates.json` | the structured predicates of the 73 rows (57 refusals, 13 prompts, 3 notices), read from `run-exp-refusal-texts/code_extract_refusals.v2.txt`; schema in the docstring of `predicates_def.py` |
| `predicate_audit_receipt.txt` | first audit, on the finding before the corrections: 2,106 table checks, 0 errors; 652 catalogue checks, 73 mismatches |
| `corrections.json` | the 35 cell corrections (old text, new text, mismatch kinds, why) applied to the finding by `apply_corrections.py` |
| `predicate_audit_receipt.v2.txt` | the audit after the corrections |
| `claims_audit_no_artifacts_before.txt`, `claims_audit_no_artifacts_after.txt` | `claims_audit.py` before and after the corrections in a checkout without the release artifacts: the same 174 lines (missing saves and screenshots, and the TD01/TD02 order-issued notes of 2026-10-08), 2,869 then 2,939 checks |

The claims-audit outputs and the receipts keep the bytes their programs wrote (the claims audit ends some lines with a space; `predicate_audit_receipt.v2.txt` ends with a blank line, a formatting slip fixed in the script afterwards): `.gitattributes` exempts them from the whitespace check instead of editing them.
