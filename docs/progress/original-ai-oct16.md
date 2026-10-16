# Original AI research queue — 2026-10-16

## Authorization and ownership

The owner authorized all assigned research in this Codex session, with MiniMax
as reviewer. Implementer family: OpenAI. Reviewer: MiniMax M3 thinking, one
review at a time, no other delegate or fallback model authorized. This resumes
only the scoped tactical research in research issues #24/#25, not the old
paused battle-development queue or a domination run. Research owns static
analysis/intake; original-game probes and drafts belong here.

Branch `research/original-ai-oct16`, base `6d72bbf`; worktree
`/tmp/ic2-conquest-ai-research`. Private Wine workspace
`/tmp/ic2-ai-oct16-work`, copied from the installed prefix without modifying it.

## Queue and dependencies

1. #5: audit promoted AI-mover-contact evidence; do not repeat answered probes.
2. #22: region boundary/scoring observations and reproducible target controls.
3. #23: embarked/disembarked/ineligible automatic-resupply controls.
4. #24: Computer General placement/setup/Walk/reload truth table and controls.
5. #26: fleet purse/supply/repair threshold matrix and noneligible controls.
6. #25: only after #24 and build #1103/#1105 corrections are integrated into
   the comparison. Closed issue state alone does not prove that integration.

Every measurement is kept under a task-owned tracked data path; binary saves,
images and instrumented executables remain gitignored and receive tracked
SHA-256 references and release uploads after each batch. Never delete a save,
including to regenerate it. Each run uses unique stamped names; reruns append
or version rather than overwrite. Commit and push after every batch and at
least every 30 minutes. Record exact edits, seeds, executable/source hashes,
field deltas, provenance and unresolved cases. Wine is not native Windows proof.

## Progress

- Read all six research issue scopes and existing promoted #5 report.
- #5 source names both natural AI-AI and AI-human contacts, siege observations
  and staged human controls; explicitly Wine-only with residual questions.
- Build #1103 and #1105 are closed; #1104 remains open pending predicate proof.
- No game probe or measured result yet. Existing installed prefix and pinned
  decompile are being checked before using the private workspace.

## Findings reporting baseline

The initial baseline is `origin/main` at `6d72bbf`. No findings were added by
PR #87. This queue does not claim to have delivered any research relay.

## END / resumption

Work in progress: continue preflight, then immutable experiments in queue order.
No result is final or reviewed yet. Do not run #25 from issue status alone.
