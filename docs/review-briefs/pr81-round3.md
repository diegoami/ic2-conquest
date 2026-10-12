# PR 81, round 3: re-check of the round-2 fix (R1)

Round 2 (gpt-6.1-sol, rework, one finding) is pasted at the end. Fix since (Sonnet subagent): e0031b5 (the 27.5 figure
labelled a conditional calculation, 30 kept as the gate-independent upper bound, in the finding line ~86 and in
`q6_gate_check.py`; new output `q6_gate_check.v2.txt`, the old one untouched). Check `git diff 25b662d..HEAD` only.

## Scope
This task protects: the truth of every claim in the finding (each backed by a tracked output or a cited, hashed, uploaded
save; rule 5) and measured evidence (never deleted or overwritten; rule 6).

## Blocking means (any one is enough; a blocking finding means rework, never approve)
1. The round-2 finding R1 is not fixed as asked, or its fix does not do what the notes or finding say.
1b. A check the task names (1a-1f, 2, 3, 5, 6) is answered without evidence, or answered with a substitute that is not what
   rows_g3.md asks, without saying so.
2. What this task protects can be got past:
   - a measured autosave or staged save that is not kept under a case/stamp/turn-specific name, hashed in `SAVES.sha256`
     and uploaded (check the release sync records), or a code path in the new scripts that deletes or overwrites a save,
     a log or an earlier output (unconditional writes on non-unique names, `write_text` over an existing file, `cp`
     without a uniqueness guard, a New Game or turn that writes AUTO* without preserving the previous ones);
   - a "nothing happened" or "no change" observation without a positive control in the SAME Wine process;
   - a staged save that is not L1 (fields beyond the named ones changed, save length changed, names over their field size).
   A bypass you proved is blocking.
3. A finding sentence claims more than its tracked output shows: a number that the cited log does not contain, a rule
   stated as [code] without a line in the tracked code extract, a frequency compared with a prediction without the trial
   counts, an incomplete reading (e.g. the stale news buffer after File > Open) used as evidence, or a cited log/save that
   does not exist.
4. Driver clicks at fixed screen coordinates where controls could be read; a test or analysis script whose result does not
   follow from the data it reads.
Not blocking: wording, style, and defects in code the PR did not change. File those as follow-ups. Limits the finding
itself states ("What this does not establish") are not blocking unless the text elsewhere claims them as established.
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

## Round 2 review (for reference)
> PR review (gpt-6.1-sol)
> rework
> R1 findings/2026-10-12-g3-original-checks.md:86 blocking: The new 27.5 upper bound on expected trade offers is not established by `q6_gate_check.txt`. That check evaluates eligibility only before the AI seats play; the finding explicitly acknowledges that those seats can change trade relations before the offer roll. Galatia having no partner in the staged start does not prove it remains ineligible at every roll, so excluding it from the expectation’s upper bound requires additional evidence. Label 27.5 as a conditional calculation assuming the initial eleven eligible non-neighbours remain the eligible set, and retain 30 as the gate-independent upper bound; alternatively, verify eligibility at each roll. Correct the same unsupported “bound” label in `runs/experiments/data/run-exp-g3-original-checks/q6_gate_check.py:24` and write any revised output beside the preserved table.
> Final pass done
> rework
> 
