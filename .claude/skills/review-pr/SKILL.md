---
name: review-pr
description: Review a pull request of this repo in a detached git worktree at the PR's head and post the review as one comment on the PR. The Claude fallback when the OpenCode reviewer (scripts/external_review.py) exits 3. Use when the user asks to review PR <n>. Never merges, approves, pushes or edits.
model: opus
allowed-tools: Read, Grep, Glob, Bash(git fetch:*), Bash(git worktree add:*), Bash(git worktree remove:*), Bash(git worktree list:*), Bash(git worktree prune:*), Bash(git update-ref:*), Bash(git rev-parse:*), Bash(git -C:*), Bash(git diff:*), Bash(git log:*), Bash(git show:*), Bash(git merge-base:*), Bash(git status:*), Bash(gh pr view:*), Bash(gh pr diff:*), Bash(gh pr comment:*), Bash(python3 -m tests.test_orders:*), Bash(mkdir:*), Bash(test:*), Bash(echo:*)
---

Review PR $ARGUMENTS of this repository and post the review as one comment on it. This is the Claude fallback
for `scripts/external_review.py`; `docs/external-review.md` describes the OpenCode reviewer, and this skill uses
the same comment shape.

## Rules (read `CLAUDE.md` first and follow its hard rules)

- No EXE, DAT, screenshot or video in git; never write to another repository; every claim of progress cites a
  save; the player's words in a strategy file are never edited; no run starts before the player approves it.
- You are a reviewer: never create `runs/<id>/`, never open or comment on an issue, never start a run, never
  commit, push, merge, approve or edit a PR, and never edit a tracked file in the worktree. The only write to
  GitHub is the one comment in **Post**. Scratch, if you need any, goes in the git-ignored `rendered/` of the
  worktree.

## Setup: a detached worktree at the PR head

```bash
N="$ARGUMENTS"
case "$N" in ''|*[!0-9]*) echo "not a PR number: $N"; exit 1;; esac
ROOT="${IC2_REVIEW_ROOT:-$HOME/ic2-work/review}"      # outside the repo
WT="$ROOT/pr$N-claude"
BASE=$(gh pr view "$N" --json baseRefName -q .baseRefName)
# explicit refspecs: a bare `git fetch origin <branch>` only reliably sets FETCH_HEAD, and the PR may come from a fork
git fetch -q origin "+pull/$N/head:refs/review/pr$N" "+refs/heads/$BASE:refs/remotes/origin/$BASE"
HEAD_SHA=$(git rev-parse "refs/review/pr$N")
test "$HEAD_SHA" = "$(gh pr view "$N" --json headRefOid -q .headRefOid)" || echo "the PR head moved; fetch again"
mkdir -p "$ROOT" && git worktree add --detach "$WT" "$HEAD_SHA"
git -C "$WT" rev-parse HEAD        # must print $HEAD_SHA; this is the commit under review
```

Do all reading and experiments in `$WT` (pass `git -C "$WT"`). Put `$HEAD_SHA` in your comment: the review is of
that commit. The diff is `git -C "$WT" diff "refs/remotes/origin/$BASE...$HEAD_SHA"`.

## What to review

1. **Correctness.** Do the tests assert what the docstrings claim? Are the expected numbers a coincidence of one
   save? Does the code handle the popup or refusal paths the game can produce?
2. **Driver pitfalls** (CLAUDE.md): no hardcoded screen coordinates (derive them), verify every order's effect on
   memory or the save, retry at most twice, never click End turn twice.
3. **Fragile spots**: multi-select, typing into pre-filled boxes, clicks into an inactive window, a stale dialog
   left open, caches under `$IC2_WORK`.
4. **Docs**: `coverage.md` and `tests/results.md` agree with what the code and tests do; a PR that changes an
   expected number updates `tests/results.md`.
5. **Style**: matches the surrounding code in comment density, naming and idiom.
6. **Decisions only the player can make** (keeping a save in `saves/`, where artifacts live, whether a run counts
   as approved under rule 4): list them separately, not buried in non-blocking prose.

## Run (only if the game environment is set up)

The real prerequisites are `setup/setup.sh` and `$IC2_WORK/fixtures/BASE.SAV` (`docs/wsl-setup.md`,
`tests/test_orders.py`). Run only the tests the PR touches, `python3 -m tests.test_orders <names>`, from `$WT`.
Say the wall-clock up front: each named test takes 30 to 100 seconds, the full suite about 15 minutes, and a run
leaves Wine and Xvfb processes behind. Compare with the "Last full run" line in `tests/results.md` and report any
failure honestly. If the environment is not set up, say so; do not claim tests passed.

## Post

One comment, in the shape `scripts/external_review.py` uses (so it can be read by the same eye):

```text
PR review (Claude Opus)
<approve | rework | decision>
R1 <file:line> blocking|non-blocking: <what to change>
R2 ...
Decisions for the player: <or "none">
Reviewed head <HEAD_SHA>. What I ran: <commands and PASS/FAIL, or "static review only">
<the same verdict again>
```

`approve` = no blocking finding; `rework` = at least one blocking finding; `decision` = a choice only the player
can make. Never write close, fix or resolve immediately before `#<n>` (write "see #<n>"). End with
`🤖 Generated with [Claude Code](https://claude.com/claude-code)` on its own line after the final verdict.

Post it from standard input so no file is written:

```bash
gh pr comment "$N" --body-file - <<'EOF'
(the review text)
EOF
```

If the write is refused (the session's GitHub proxy may refuse some writes), do not claim it was posted: end your
answer with the review text and the exact command above for the player to run.

## Cleanup (after posting, or if the session ends early)

```bash
git worktree remove --force "$WT"; git update-ref -d "refs/review/pr$N"; git worktree prune
```

If a session died mid-review, run `git worktree list` in the main checkout, remove any `pr<N>-claude` entry and
`git worktree prune`.
