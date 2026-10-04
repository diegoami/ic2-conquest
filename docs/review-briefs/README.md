# Review briefs

One file per reviewed PR (`pr<n>.md`), passed to the external reviewer with
`python3 scripts/external_review.py --pr <n> --brief-file docs/review-briefs/pr<n>.md`; the script appends it to the brief it
generates. Kept in git so a review can be replayed with the same brief.

**Every brief carries a "Blocking means" section written for its task** (player's instruction, 2026-10-04, from the harness's
PR 29 replay: a reviewer proved three bypasses live, rated them "not blocking" and approved; harness lesson L47). Until the
reviewer prompt in `.opencode/agents/external-reviewer.md` comes from a harness version that has L47, the section goes in each
brief in full, never as a pointer. The template:

```
## Scope
This task protects: <one line: the guard, check, permission, invariant, rule value or file this task exists to protect>.

## Blocking means (any one is enough; a blocking finding means rework, never approve)
1. A Done-when line fails, or cannot be run as written.
2. What this task protects can be got past: <name it>. A bypass you proved is blocking, even when it looks like an edge case.
   Do not rate it "follow-up hardening" or "outside the threat model" unless the task says so; if it does, quote the line.
   <On a guard task: list the forbidden actions or results the guard must stop.>
3. Behaviour the task forbids, or behaviour nobody asked for, inside a file the task requires.
4. <project-specific items, e.g. a constant with no evidence; a test that passes with the behaviour deleted; a status written
   into a document; a claim with no tracked output behind it>.
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
```

The second section was added after #38, where one reviewer reported one blocker per round over eight rounds.

**Before merging an approve with "not blocking" findings, read them.** If one is a proven way past what item 2 names, treat the
review as rework, say so on the PR, and record it in `docs/model-trials.md`.
