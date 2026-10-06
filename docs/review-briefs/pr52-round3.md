## Scope
Round 3 of PR #52, the LAST review round (harness L49): after it the owner decides. Your round-2 comment on this PR found
R1 (the plays table's `rows` column checked only against the finding's own `play [confirmed]` cells) and R2 (the runner's
load path inherited `Game.open` -> `dismiss_popups`, which clicks an assumed OK position; `eog.py` had the same assumption).
Commits since round 2: 445e9ba (R1, R2, runner tests, b8 partial), c783584..adccf64 (b8c1-b8c4: the 14 remaining plays and
their archives), ca9f17a (re-run summary, finding rebuilt, `test_doctored_save` now doctors the latest batch's control save).
All 56 plays were re-run in b8 with the fixed runner (`MANIFEST-b8.txt`, `MANIFEST-b8c1.txt`..`MANIFEST-b8c4.txt`, release
`run-exp-refusal-texts`). The finding states that the guessed load-time click did fire in b1-b7 (news or offer boxes).

This task protects: the finding's claims (refusal texts, conditions, play attributions, counts) are each backed by an
independent source (the code extract, a recorded play, a save), and no play clicked anything it had not located and verified.

Check that R1 and R2 are fixed, and that no other instance of their classes remains anywhere in the PR: a check that compares
the finding with itself or is always true; a runner path that can click a fallback, fixed or guessed coordinate (including
dismissals, menus and dialogs); a claim column the audit does not compare with a source. Also check the commits after 445e9ba
(the b8 records, the re-run summary, the rebuilt finding and the changed test).

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
- Do not rely on a later round. This is the last round: the owner decides on what you report.
- If you ran out of time or context before covering the whole diff, say which files or sections you did not cover. Do not
  approve in that case.
