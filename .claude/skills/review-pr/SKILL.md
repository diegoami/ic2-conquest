---
name: review-pr
description: Review a pull request of this repo in an isolated git worktree and post the review as one comment on the PR. Use when the user asks to review PR <n>. Never merges, approves or pushes.
---

Review PR $ARGUMENTS of this repository and post the review as a comment on it.

## Setup (worktree, so the main checkout is untouched)

```bash
N=$ARGUMENTS
BRANCH=$(gh pr view $N --json headRefName -q .headRefName)
git fetch origin
git worktree add ../ic2-conquest-review-$N origin/$BRANCH
cd ../ic2-conquest-review-$N
```

Do all reading and experiments there. Remove it when done: `git worktree remove ../ic2-conquest-review-$N`.

## Rules

Read `CLAUDE.md` first and follow its hard rules: no EXE, DAT, screenshot or video in git; never write to another repository; every claim of progress cites a save; the player's words in a strategy file are never edited.

## What to review (`gh pr diff $N`)

1. **Correctness.** Do the tests assert what the docstrings claim? Are the expected numbers a coincidence of one save? Does the code handle the popup or refusal paths the game can produce?
2. **Driver pitfalls** (CLAUDE.md): no hardcoded screen coordinates (derive them), verify every order's effect on memory or the save, retry at most twice, never click End turn twice.
3. **Fragile spots**: multi-select, typing into pre-filled boxes, clicks into an inactive window, a stale dialog left open, caches under `$IC2_WORK`.
4. **Docs**: `coverage.md` and `tests/results.md` agree with what the code and tests do.
5. **Style**: matches the surrounding code in comment density, naming and idiom.

## Run (if the game environment is set up, see `docs/wsl-setup.md`)

Run the tests the PR touches (`python3 -m tests.test_orders <names>`) in the worktree and report the result honestly, including any failure. If the environment is not set up, say so; do not claim tests passed.

## Post

One comment, no approval, no merge, no push to the PR branch:

```bash
gh pr comment $N --body-file <file outside git, e.g. /tmp/review-$N.md>
```

Structure: **Verdict** (one line), **Blocking**, **Non-blocking**, **What I ran** (commands and PASS/FAIL). Cite `file:line` for each finding. End the comment with:
`🤖 Generated with [Claude Code](https://claude.com/claude-code)`
