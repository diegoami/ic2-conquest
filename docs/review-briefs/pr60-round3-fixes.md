## Scope
Narrow review of PR #60 after round 3, chosen by the owner (2026-10-06): check ONLY the fixes of round-3 findings R1-R5 (the
gpt-6.1-sol round-3 comment on this PR) and the new code in commits 48ca883 (R1, R2), 45fb551 (R3), ef087d8 (R4),
8a9eeb9 (R5) and 2fc7e38 (outputs and the restated Method). The implementer's round-3 hand-back is a PR comment: read it,
including its own mutation list. R6 (the reviewer's own coverage limit) is not a finding to fix here. There was no new
batch: the final tracked outputs are `claims_audit_output.v17.txt` (no `--exe`/`--dat`, 11587 checks),
`claims_audit_output.v18.txt` (`--exe`, 11589) and `claims_audit_output.v19.txt` (`--exe --dat`, 11592), all 0 mismatches;
`test_claims_audit_output.v5.txt` (153 tests) and `test_runner_output.v5.txt` (62 tests); v14-v16 kept beside them, nothing
overwritten.

The owner's standing decision (2026-10-06) still holds: free-text wording is checked by review, not by the claims audit,
and the audit not catching a wording edit is NOT blocking — except where R4's class makes the wording itself the fix: a
summary line that re-looses its qualification (an unqualified "unticked row", "does not draw", "leaves the same world",
"OK with no tick") is blocking here.

This task protects: the exactness of every rule of the form the clone will copy, each backed by an independent source (the
code extract, the form resource, the DAT, a recorded play with its screenshot and save or memory dump), and no play clicked
anything it had not located and verified.

Check per finding:
- R1 floor numbers bound by operand role: in a `says` phrase of a `code floor` check, a number after a plus is the field
  address (hex only), every other number the minimum; a `calc` with an operator vouches for its result only, never its
  operands. The mutations must fail: O03 "at least 450" to "at least 1088" in prose and phrase together, the field address
  swapped, an operand used for a result.
- R2 spelled numbers: zero to twenty, a dozen, thirty to sixty, hundred, and "one" only before a counted noun; validated
  inside `says` phrases against the check's derived value. The mutation must fail: T06 "Six" to "Seven" in prose, phrase
  and the X01 fragment together.
- R3 N09 and the save-versus-memory consistency check compare the full 26-byte leader fields, extracted independently from
  the save and the dump (not decoded NUL-terminated strings); the mutation must fail: one byte after the leader's NUL
  flipped in P04's dump with SAVES.sha256, manifests, JSON `leader_hex` and the nation hash rewritten consistently.
  "Byte-identical" claims (C03, Answer 5) still compare a full-record SHA-256.
- R4 qualification: Answer 3 (and 4, 5), C03, X02, X06, N07, O05 say which rows a "left alone / does not draw" claim covers
  (New Game's initially-computer rows) and name O02's human-to-computer branch where OK draws; the audit's "qualification"
  check enforces it. The mutations must fail: qualification removed from Answer 3, the exception dropped from X06, the
  scope dropped from C03.
- R5 untouched forms and forms opened per play are derived from `scenarios.py` by `play_plans.py` (a `record_form` straight
  after `open_form`, no tick, edit, key or press between), not from the literal label; V04 is recomputed (14 untouched forms
  in 12 plays, of 17 forms opened by the 15 plays) and V01-V03 and the seed coverage read from the derivation too. The
  mutations must fail: a doctored name in P09's third form, changed form or play counts, a form read after a tick counted
  as untouched.

## Blocking means (any one is enough; a blocking finding means rework, never approve)
1. A Done-when line of `docs/tasks/leaders-form.md` fails, or cannot be run as written (the claims audit must give 0
   mismatches with and without `--exe`/`--dat`; `test_claims_audit.py` and `test_runner.py` must pass; their outputs
   tracked).
2. What this task protects can be got past: one of the round-3 mutations above (or an equivalent consistent edit you
   construct yourself) that the fixed audit still passes; a number bound by membership instead of operand role; a spelled
   number outside the recognized set; a save-versus-memory comparison that skips any byte of the leader field; a summary
   line that lost its qualification; an inventory derived from a record's label or text instead of the scenario. A bypass
   you proved is blocking, even when it looks like an edge case. Do not rate it "follow-up hardening" or "outside the
   threat model" unless the task says so; if it does, quote the line.
3. Behaviour the task forbids, or behaviour nobody asked for, inside a file the task requires (an edit to
   `harness/driver.py`; a measured output deleted or overwritten instead of versioned; a save or screenshot in git).
4. A test that passes with the behaviour it covers deleted; a count in the finding, the PR body or the hand-back with no
   tracked output behind it.
Not blocking: wording, style, and defects in code the PR did not change; the audit's inability to bind free-text wording
(the owner's decision above). File those as follow-ups.
When unsure, rate it blocking and say why. An approve with a proven bypass is the costliest mistake a review can make.

## Report every blocking finding in this one review
This review is your only pass before the author fixes. Do not stop at the first blocking finding: finish reading the whole
diff of the five commits and the parts of the task file they touch, check every item under "Blocking means", and report all
blocking findings together.
- Before you write the verdict, make one last pass over the five commits for anything you have not yet rated, and say
  "Final pass done" as the last line before the verdict.
- Number the findings R1, R2, … in order of severity. A finding you held back because an earlier one was already blocking is
  a review defect: if two problems share a cause, list both and say so.
- Do not rely on a later round: this narrow review is the last before merge.
- If you ran out of time or context before covering the five commits, say which files or sections you did not cover. Do not
  approve in that case.
