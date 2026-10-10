
## Scope
This task protects CLAUDE.md rule 8 (the owner's highest priority, 2026-10-10): a delegated OpenCode run's failure is never passed silently to
another model; only a provider API that does not answer moves the chain to the next model; a run that dies keeps its progress and can be
resumed in the same session; running jobs are visible in plain words.

## Blocking means (any one is enough; a blocking finding means rework, never approve)
1. A process failure (idle-timeout, total-timeout, nonzero-exit after resumes, cut-off, bad-format, permission-rejected, default-agent,
   unknown-model, unknown-agent, no-executable) can still reach the next model, or can post a comment, or exits with anything but 6.
2. An API failure (429, 5xx, quota/usage limit, network error, no session) is classified `process`, or model text in stdout that merely
   mentions "429" or "rate limit" makes a run `api` (a false fallback).
3. A resume does not continue the SAME session id, starts a new session, loses the brief, or can resume more than 2 times; or
   `--resume` can post a review for a head SHA other than the PR's current head.
4. A run dir, result.json or progress record is deleted or overwritten without a kept copy (CLAUDE.md rule 6).
5. The session DB is opened writable, or anything reads or prints `auth.json`.
6. A test that passes with the behaviour it names deleted (check at least the fallback, resume and exit-6 tests).
7. The default chain contains DeepSeek or Alibaba models.
Not blocking: wording, style, and defects in code the PR did not change. File those as follow-ups.
When unsure, rate it blocking and say why. An approve with a proven bypass is the costliest mistake a review can make.

## Report every blocking finding in this one review
This review is your only pass before the author fixes. Do not stop at the first blocking finding: finish reading the whole
diff, check every item under "Blocking means", and report all blocking findings together.
- Before you write the verdict, make one last pass over the full diff for anything you have not yet rated, and say
  "Final pass done" as the last line before the verdict.
- Number the findings R1, R2, … in order of severity. If two problems share a cause, list both and say so.
- If you ran out of time or context before covering the whole diff, say which files or sections you did not cover. Do not
  approve in that case.

## Round 2
This is round 2. Round 1 (gpt-5.6-luna) found R1 result.json overwritten without a kept copy, R2 API evidence taken from model stdout, R3 the 2-resume limit reset by each manual --resume. Check that each fix holds (try to get past it), then review the new code. Report every blocking finding.
