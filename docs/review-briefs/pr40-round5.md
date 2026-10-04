## Scope
This task protects: the integrity of the B5/B8 measurements and of the findings draft built on them. Every number in findings/2026-10-04-tactical-battle-sweep.md must be recomputable from a tracked file in runs/experiments/data/run-exp-battle-sweep/, and the claims audit must check each claim against the tracked raw inputs, not against an analyser's output. No measured output may be overwritten or deleted (CLAUDE.md rule 6), and no EXE, DAT, save, screenshot or video may enter git (rule 1).

## How to review
- Your sandbox cannot run Python (only py_compile) or the game. The main session ran these at the head before this review: the four suites (python3 -m tests.test_driver_battle 22 pass, tests.test_battle_stage 16, tests.test_battle_trials 7, tests.test_battle_b5_b8 7), and claims_audit.py (claims-audit-20261004-195251.md: 104 claims, 0 mismatches). Do not take those as proof of correctness. Check by reading:
  - Does each test assert the behaviour it names, so that deleting the behaviour would make it fail? Name the line that would have to change.
  - Does each audit claim recompute its value from raw inputs (saves via audit_inputs.py, trials.jsonl, live-run records) rather than from an analyser output?
  - Do the finding's numbers match the tracked files? Count them yourself with grep/wc/sort/uniq where you can, e.g. Offer-of-peace rows and winners in trials.jsonl.
- Prove a finding before reporting it, by quoting the code path and the input that triggers it. Otherwise label it "unverified" and say what would prove it.
- Keep all scratch output inside the worktree. Run git one command at a time. Never touch `.git`.

## Blocking means (any one is enough; a blocking finding means rework, never approve)
1. A Done-when line fails, or cannot be run as written.
2. What this task protects can be got past. Any one of these is enough:
   - a claim in the finding that no tracked output supports, or that a tracked output contradicts (spot-check at least 10 numbers yourself: the win table, the size matrix, the B8 thresholds, the Offer-of-peace count, promotions, captured talents, the attribution counts, the target-choice ranks);
   - a claim in claims_audit.py that is checked against an analyser output (b5-summary-*.json, b5-targets-*.csv or any other file the analysers write) instead of being recomputed from the raw tracked inputs (trials.jsonl, halfrounds-*.jsonl, B0 logs), unless the audit output states that the check shares code with the analyser;
   - a code path in the changed runners/analysers that can overwrite, truncate, append to or delete an existing measured file (same-second name collisions included);
   - a binary added to git;
   - a save cited by the finding that is in no SAVES.sha256 / release-manifest entry;
   - an observation of the AI general stated as a rule or as how the AI chooses;
   - a decompiled-report [R-code] fact presented as measured without the data check.
   A bypass you proved is blocking, even when it looks like an edge case. Never rate it "follow-up hardening" or "outside the threat model" unless the task says so; if it does, quote the line.
3. Behaviour the task forbids, or behaviour nobody asked for, inside a file the task requires: for example writes to another repository, a blind End-turn click (clicking End turn again without proof the first did something), or edits outside the battles experiment paths without reason.
4. Project-specific:
   - a test that passes with the behaviour it checks deleted;
   - a statistic that overreads 3 seeds per cell as a probability;
   - a mismatch between the data README's release map (run-exp-battle-sweep, -b5, -2) and the release-manifest files.
Not blocking: wording, style, and defects in code the PR did not change. File those as follow-ups.
When unsure, rate it blocking and say why. An approve with a proven bypass is the costliest mistake a review can make.

## Report every blocking finding in this one review
This review is your only pass before the author fixes. Do not stop at the first blocking finding: finish reading the whole diff and the task file, check every Done-when line and every item under "Blocking means", and report all blocking findings together.
- Before you write the verdict, make one last pass over the full diff for anything you have not yet rated, and say "Final pass done" as the last line before the verdict.
- Number the findings R1, R2, … in order of severity. A finding you held back because an earlier one was already blocking is a review defect: if two problems share a cause, list both and say so.
- Do not rely on a later round. The author fixes everything you list, and the next review checks those fixes and new code only, not anything you saw but did not report.
- If you ran out of time or context before covering the whole diff, say which files or sections you did not cover. Do not approve in that case. The diff is large in data files (over 300): you may sample data files, but cover all code (runs/experiments/battles/, state/, harness/, tests/, setup/, scripts/), the finding, the task file and the data README.

## This is round 5
Round 4 (glm-5.3, comment on this PR) raised:
- R1: the LC row of the B8 threshold table said "off by 1 / 2"; it is now "off by 1";
- R2: stale test and claim counts, plus a dead b2-analysis read in claims_audit.py;
- R3: the release_sync docstring said pngs go to -b5.
They were fixed in commit 11de117, and the main session re-ran claims_audit.py after the fix (claims-audit-20261004-201404.md: 104 claims, 0 mismatches). The PR body's counts were also updated.
Check that each fix is real and complete, for example that no other "100 claims" or "6 tests" remains in a changed file. Then review the code that commit changed. Your round-4 review already covered the rest of the PR: do not re-open it unless you find a proven bypass of item 2 you missed. If you do, list it and say so.
