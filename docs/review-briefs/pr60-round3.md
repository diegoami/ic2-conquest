## Scope
Round 3 of PR #60, the LAST review round (harness L49): after it the owner decides. Your round-2 comment on this PR found
R1-R7 (R8 non-blocking). Commits after 06754dd up to caca6e4 fix them (the implementer's round-2 hand-back is a PR comment:
read it, including its own mutation list): claims bound per assertion with `says "<phrase>" :: <check>` items, the plays
table's `what` column bound to the recorded steps, per-branch obligations from the code extract (`branches.py`), expected
step sequences parsed from `scenarios.py` (`play_plans.py`), nation fields decoded from the raw dumps, screenshot-only rows
retired or given state evidence, Answer 5 restated. New batches b7 and b8 (b8 is the evidence batch; `MANIFEST-b7.txt`,
`MANIFEST-b8.txt`, release `run-exp-leaders-form`). a16504c (main session) adds one "What this does not establish" item and
tracked outputs v11-v13 / v4.

**The owner's decision before this round (2026-10-06): free-text wording is checked by review, not by the claims audit.** The
audit binds every number and operation word; it does not bind other prose (a reversed verb such as set/cleared or
keeps/destroys, a swapped pair of nations or function roles, a scope word such as per nation/shared, a number replaced by
another that is also true). The implementer listed nine such edits that pass the audit. **That the audit cannot catch such an
edit is NOT blocking in this round.** What IS blocking is any such wording in the finding that is WRONG today: so read the
prose of every rule, fact, Answer item and clone cell against its cited code lines and recordings, and report each statement
that is false or not shown by its evidence.

Also check that R1-R7 are fixed, that no other instance of their classes remains (a claim bound by membership only, an
unaudited claim column other than the free-text residual above, inventory taken from the finding, a step label trusted, a
JSON value trusted over the dump, a [confirmed] row without its observation and state evidence, an ambiguous grouping), and
all new code since 06754dd.

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
- Do not rely on a later round: this is the last round, and the owner decides on what you report.
- If you ran out of time or context before covering the whole diff, say which files or sections you did not cover. Do not
  approve in that case.
