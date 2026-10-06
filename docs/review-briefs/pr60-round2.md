## Scope
Round 2 of PR #60 (the original's leaders form, clone #719). Your round-1 comment on this PR found R1-R12. Commit 06754dd
(and the commits before it after d91664d) fixes them: the claims audit rewritten (prose numbers bound to checks, inventory
from the resource/task/plays, derived meaning checked as the code's operations, clicks bound to the pointer read back and the
helper's control line, seeds from `SEED.TXT`), immediate post-tick state and screenshot (H04), verified form actions and menu
steps, a form model in the runner tests, `verified_reset` replacing `reset_ui`/`NEUTRAL`, `--exe`/`--dat` required when
requested, W07 and the +0x440 statement corrected with facts V01-V04, counts by unique recording. All 15 play ids were
re-recorded in batch b6 (`MANIFEST-b6.txt`, release `run-exp-leaders-form`); b1-b5 are kept but not cited. The implementer's
hand-back (a PR comment) lists what each class sweep found.

Check that R1-R12 are fixed, and that no other instance of their classes remains anywhere in the PR: a claim the audit does
not bind to an independent source (including always-true checks, play-ID exemptions and inventory taken from the finding);
a [confirmed] claim the cited observation cannot show; an intermediate step not verified, or a test that cannot fail; a click
at a fixed or guessed position; a requested check that silently disappears; a statement the tracked data contradicts; a count
that does not count what it says. Also check all new code since d91664d. The implementer names three residual caveats in the
hand-back (form-only [confirmed] rows cite a screenshot and no save; Answer numbers bound to the union of the cited rows; the
plays table's "what" column not audited): rate each one.

This task protects: **the exactness of every rule of the form the clone will copy**, each backed by an independent source
(the code extract, the form resource, the DAT, a recorded play with its screenshot and save or memory dump), and no play
clicked anything it had not located and verified.

## Blocking means (any one is enough; a blocking finding means rework, never approve)
1. A Done-when line of the task fails, or cannot be run as written (the claims audit must give 0 mismatches, with and without
   `--exe`; `test_claims_audit.py` and `test_runner.py` must pass; their outputs tracked).
2. What this task protects can be got past:
   - a claim in the finding (a literal, a control property, a rule, an offset, a count, a pool name, a play outcome) that can be
     changed, alone or consistently across several tables, and the audit still passes;
   - a check that compares the finding with itself, or that is always true, or whose expected value is typed into the checker;
   - a `[confirmed]` row whose screenshot, save or memory dump is missing, unhashed, or does not show what the row says; a
     `[derived]` row whose code line does not contain what it claims;
   - a runner click whose target was not located (control enumeration, OCR) or whose effect was not verified, a guessed or
     fixed coordinate anywhere in the runner, an intermediate click (a tick, a name edit, a menu step) not checked to have
     registered, or a box without the needed control that is clicked instead of stopping the run;
   - a conclusion drawn from a play that cannot show it (e.g. "OK has no check" while a refusing case was never played; the
     draw's pool claimed from fewer observations than the code shows).
   A bypass you proved is blocking, even when it looks like an edge case. Do not rate it "follow-up hardening" or "outside the
   threat model" unless the task says so; if it does, quote the line.
3. Behaviour the task forbids, or behaviour nobody asked for, inside a file the task requires (an edit to
   `harness/driver.py`; a measured output deleted or overwritten instead of versioned; a save or screenshot in git; a write to
   another repository; a pattern kill in a script).
4. A test that passes with the behaviour it covers deleted; a count in the finding or the PR body with no tracked output
   behind it; a failed play cited as evidence; a staged or edited save not labelled as such.
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
- Do not rely on a later round. The author fixes everything you list, and the next review checks those fixes and new code
  only, not anything you saw but did not report.
- If you ran out of time or context before covering the whole diff, say which files or sections you did not cover. Do not
  approve in that case.
