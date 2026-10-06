## Scope
Narrow review of PR #64 after round 1, chosen as the last pass before merge: check ONLY the fixes of round-1 findings R1-R3
(the gpt-5.6-luna round-1 comment on this PR) and the new code and files in commit 2130379. The implementer's hand-back is a PR
comment: read it.

- R1: `DEFAULT_VARIANT` holds only variants its model offers (the never-read `minimax/MiniMax-M2.7: None` entry removed; the
  empty-OFFERS branch returns the bare base before DEFAULT_VARIANT is consulted).
- R2: the off-peak zai pricing test uses a quota record with `peak_now: False`, not one with no pricing block.
- R3: the probe times and the self-test output are tracked (`runs/experiments/data/run-exp-new-providers/probes.v1.txt`,
  `self-test.v1.txt`, `README.md`) and the PR body cites them.

This task protects: the effort normalisation never sends a model a variant it does not offer, and every number the PR states
has a tracked output behind it.

## Blocking means (any one is enough; a blocking finding means rework, never approve)
1. `python3 scripts/external_review.py --self-test` and `python3 tests/test_reviewer_prompt.py` not passing.
2. What this task protects can be got past: a `DEFAULT_VARIANT` value not in its model's `OFFERS` tuple; an `effort()` result
   carrying a variant the model does not offer; a pricing test that does not exercise the state its name says; a number in the
   PR body or README with no tracked output behind it; a tracked file that contradicts the PR body (a probe time, a count).
   A bypass you proved is blocking, even when it looks like an edge case. Do not rate it "follow-up hardening" or "outside
   the threat model" unless the task says so; if it does, quote the line.
3. Behaviour the task forbids, or behaviour nobody asked for, in commit 2130379 (a change to DEFAULT_MODELS or any review
   chain; a key, token or `auth.json` path anywhere; a measured output deleted or overwritten instead of versioned).
4. A test that passes with the behaviour it covers deleted.
Not blocking: wording, style, and defects in code the commit did not change. File those as follow-ups.
When unsure, rate it blocking and say why. An approve with a proven bypass is the costliest mistake a review can make.

## Report every blocking finding in this one review
This review is your only pass before the author fixes. Do not stop at the first blocking finding: read commit 2130379's whole
diff and every item under "Blocking means", and report all blocking findings together.
- Before you write the verdict, make one last pass over the commit for anything you have not yet rated, and say
  "Final pass done" as the last line before the verdict.
- Number the findings R1, R2, … in order of severity. A finding you held back because an earlier one was already blocking is
  a review defect: if two problems share a cause, list both and say so.
- Do not rely on a later round: this narrow review is the last before merge.
- If you ran out of time or context before covering the commit, say which files or sections you did not cover. Do not
  approve in that case.
