# PR104: complete Kimi review and dispositions

Reviewed head `95d906e3c2db1e2fa53a76f21fb22acb1401eb90`, base `c8f11fceaa5b414724e7925f025c2185fdbf1dcd`. Actual implementer gpt-6.1-sol medium (OpenAI). Reviewer `kimi-code-plan-global/k3#high`, session `ses_eb18aae9cffeBTpJ4Xo6hh4Xf7`. Full returned result and posted comment read before edits. Verdict **APPROVE**, three nonblocking notes; static-only private-path limitation retained.

## Complete returned result

```json
{
  "class": "ok",
  "kind": null,
  "model": "kimi-code-plan-global/k3#high",
  "agent": "external-reviewer",
  "session": "ses_eb18aae9cffeBTpJ4Xo6hh4Xf7",
  "text": "Reviewed in the printed worktree top level `/home/diego/projects/ic2-work/sav-export37-closure-review/review/04cb64`, HEAD `95d906e3c2db1e2fa53a76f21fb22acb1401eb90`, base `c8f11fceaa5b414724e7925f025c2185fdbf1dcd`. Static review only (private Windows paths unavailable in this sandbox): read the finding, native README, validation manifest v2, all three completion records, both autonomous control comparisons, control1 comparison script/record, retained failures, run notes, the review brief, all six new scripts (all pass `py_compile`), and sampled per-action JSON receipts including window enumerations and decoded caption strings.\n\nPR review (k3)\napprove\nR1 runs/experiments/sav_export37_native/verify_native_packet.py:19 non-blocking: `stage['L'] != stage['O'] != stage['E']` is a chained comparison, so it never checks L≠E; use three pairwise comparisons or `len({L,O,E})==3` so the \"order and turn each changed the save\" check is complete (currently covered indirectly by the completion records and receipts).\nR2 runs/experiments/data/run-exp-sav-export37-native/README.md:13 non-blocking: the recruit-configuration clicks and case3's supply-warning \"End turn\" confirmation (e.g. `case2-recruit-lightinfantry-select-v1.json`, `case3-turn-confirm-end-v1.json`) were ad-hoc bridge invocations not contained in any committed script, so the committed scripts alone do not reproduce the sequences end to end; say so explicitly in the README next to the script list.\nR3 runs/experiments/data/run-exp-sav-export37-native/case1-order-effect-v1.json:1 non-blocking: unlike cases2/3, this record omits the `economy` treasury/mobilization pair (it lives only in `case1-completion-v1.json`); align the schema or note the difference so later readers don't read the omission as a missing check.\napprove",
  "stdout": "/home/diego/projects/ic2-work/sav-export37-semantics/rendered/pr104-04cb64/run-1/stdout.log",
  "stderr": "/home/diego/projects/ic2-work/sav-export37-semantics/rendered/pr104-04cb64/run-1/stderr.log",
  "cause": null
}
```

## Complete posted comment

```text
PR review (k3)
approve
R1 runs/experiments/sav_export37_native/verify_native_packet.py:19 non-blocking: `stage['L'] != stage['O'] != stage['E']` is a chained comparison, so it never checks L≠E; use three pairwise comparisons or `len({L,O,E})==3` so the "order and turn each changed the save" check is complete (currently covered indirectly by the completion records and receipts).
R2 runs/experiments/data/run-exp-sav-export37-native/README.md:13 non-blocking: the recruit-configuration clicks and case3's supply-warning "End turn" confirmation (e.g. `case2-recruit-lightinfantry-select-v1.json`, `case3-turn-confirm-end-v1.json`) were ad-hoc bridge invocations not contained in any committed script, so the committed scripts alone do not reproduce the sequences end to end; say so explicitly in the README next to the script list.
R3 runs/experiments/data/run-exp-sav-export37-native/case1-order-effect-v1.json:1 non-blocking: unlike cases2/3, this record omits the `economy` treasury/mobilization pair (it lives only in `case1-completion-v1.json`); align the schema or note the difference so later readers don't read the omission as a missing check.
approve

```

## Dispositions

- R1 fixed: validator requires three distinct complete byte values for load/order/end-turn, closing the L==E!=O gap. A synthetic counterexample executes the actual assertion and confirms rejection; existing private evidence is rechecked read only in validationv3.
- R2 fixed: native README explicitly identifies ad-hoc recruitment configuration and case3 confirmation bridge calls, preserved per-action logs, and scripts’ lack of self-contained end-to-end replay.
- R3 documented: README points to case1-completion-v1.json for economy pairs and explains the case2/3 schema difference. Immutable case1-order-effect-v1.json remains untouched.

No native/UI action, new candidate, independent review, merge or relay performed for these nonblocking changes.
