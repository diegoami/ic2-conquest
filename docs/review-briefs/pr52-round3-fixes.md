## Scope
Narrow review of PR #52 after round 3, chosen by the owner (2026-10-06): check ONLY the fixes of round-3 findings R2-R7 (the
gpt-6.1-sol round-3 comment on this PR) and the new code in commits 2875bd8, dfdff49, 6eb845c, 9cfcdb7. R1 (auditing the
`[derived]` condition and effect columns against structured predicates) is deferred by the owner to issue #58 and is NOT a
blocking finding here; the finding's "not audited" disclosure with its pointer to #58 is the intended state.
The b9 batch re-ran the 23 plays whose runner path changed (`MANIFEST-b9.txt`, `rerun_summary.v5.txt`); untouched plays keep
their b8 records. Tracked outputs: `claims_audit_output.v13.txt`, `test_claims_audit_output.v6.txt`, `test_runner_output.v2.txt`.

This task protects: the finding's claims (refusal texts, conditions, play attributions, counts) are each backed by an
independent source (the code extract, a recorded play, a save, a screenshot), and no play clicked anything it had not located
and verified.

Check per finding: R2 every intermediate selection and action transition verified, failing closed, with bounded retries;
R3 no runner path to an inherited guessed or fixed coordinate, and the AST guard actually catches one; R4 the task's required
confirmations and combined cases are enforced from sources other than the finding's own cells, and removing them consistently
fails; R5 a missing or changed screenshot is a mismatch; R6 tracked passing outputs exist and the failed v4 is not overwritten;
R7 the TR3 wording and Method line.

## Blocking means (any one is enough; a blocking finding means rework, never approve)
1. A Done-when line of `docs/tasks/refusal-texts.md` fails, or cannot be run as written (the claims audit must give 0
   mismatches and its tests must pass: `claims_audit.py`, `test_claims_audit.py`, `test_runner.py`).
2. What this task protects can be got past: a consistent change to the finding (both tables changed together, as in your
   round-2 R28/R31 + T01/T01r example, or any other) that the audit still passes; a play row whose attribution does not follow
   from that play's recorded clicks mapped to the extract's handler; a click in the runner whose target was not located
   (control enumeration, OCR, tooltip) and whose effect is not verified; a box without an OK control that is clicked instead of
   stopping the run. A bypass you proved is blocking, even when it looks like an edge case. Do not rate it "follow-up
   hardening" or "outside the threat model" unless the task says so; if it does, quote the line.
3. Behaviour the task forbids, or behaviour nobody asked for, inside a file the task requires (e.g. an edit to
   `harness/driver.py`; a measured output deleted or overwritten instead of versioned; a save or screenshot in git).
4. A test that passes with the behaviour it covers deleted (in particular the changed `test_doctored_save`); a count in the
   finding or the PR body with no tracked output behind it; a b8 record that cites a play the manifests do not contain; a
   finding statement about b1-b7 (the fired click) not backed by the cited logs.
Not blocking: wording, style, and defects in code the PR did not change. File those as follow-ups.
When unsure, rate it blocking and say why. An approve with a proven bypass is the costliest mistake a review can make.

## Report every blocking finding in this one review
This review is your only pass before the author fixes. Do not stop at the first blocking finding: finish reading the whole
diff and the task file, check every Done-when line and every item under "Blocking means", and report all blocking findings
together.
- Before you write the verdict, make one last pass over the full diff for anything you have not yet rated, and say
  "Final pass done" as the last line before the verdict.
- Number the findings R1, R2, … in order of severity. A finding you held back because an earlier one was already blocking is
  a review defect: if two problems share a cause, list both and say so.
- Do not rely on a later round: this narrow review is the last before merge.
- If you ran out of time or context before covering the whole diff, say which files or sections you did not cover. Do not
  approve in that case.
