# Running notes: model choice, the user decides (2026-10-11)

Implementer: the main session (the owner's choice, 2026-10-11; quota suggestion shown with the question: light pick
minimax/MiniMax-M2.7 rank 1 spare reliability 0.99, heavy pick minimax/MiniMax-M3 spare 0.95). Worktree
`.claude/worktrees/model-choice`, branch `process/model-choice-user-decides`.

## Plan
1. CLAUDE.md: replace the "Choosing a model" (L50/L51) bullet with the owner's rules 1-13; adjust rule 8 and the quota line.
2. Process docs: mark every table, chain, tier or exclusion that picks a model as superseded (history kept):
   docs/environment.md (placements, DEFAULT_MODELS), docs/external-review.md (roles table, chain), docs/proposals/battles.md,
   docs/proposals/fleet-battles-and-storms.md review plans.
3. review-pr skill: the review step is rule 2 (the user names the reviewer; this skill runs only when the user names it).
4. Scripts: external_review.py runs only the model the user names (no default chain, no auto-skip); --resume already continues
   a session in a kept worktree: check it reuses the worktree.
5. Tests green; PR; ask the owner which external model reviews (rule 2); close #72 as superseded on merge.

## Progress
- 50699d3 CLAUDE.md: the rules 1-13 in; L50/L51 kept as model facts + effort, marked superseded
- ed349e1 external_review.py: --model required, one model; tests 31/31, self-test 57/57
- c76f7d9 docs/external-review.md (roles: the user's choice; history kept), docs/environment.md (placements superseded),
  four proposals (a superseded note under the title), .claude/skills/review-pr (rule 2; no fixed model; never an automatic fallback)
- Scripts, rule 13: `external_review.py --resume <run dir>` already continues the recorded session (`opencode run --session`) in a
  worktree recreated at the recorded path and head (the reviewer writes no files, so nothing is lost); no change needed.
  `opencode_watched.py` takes an explicit `--model` and never chose one.

## END (2026-10-11)
Done: plan steps 1-4; tests: tests/test_reviewer_prompt.py 31/31, external_review.py --self-test 57/57. Next: the owner names the
external reviewer (rule 2); on approval + green CI merge and close #72 as superseded. Memory notes that name old chains get a pointer.

## Review round 1 fixes
- R1+R2+R5: external_review.py: run_chain removed, run_one runs exactly one model (api failure -> exit 3, no other model); family()
  maps ids and implementer names to a family, excluded() refuses a same-family reviewer (exit 2); tests 32/32, self-test 71/71.
- R3+R4: docs/external-review.md (exit 3/4 text, failure-kind table, --model list text) and docs/environment.md (DeepSeek rows and
  the free-model 429 fallback) rewritten to the one-model rule; old chain text stays only under "History (superseded)".
- Sweep: README, scripts comments (external_review, opencode_watched), five proposals (inline superseded markers), test helper
  renamed chain -> run_one_model. Tests 32/32, self-test 71/71.

## END (round 1 fixes, 2026-10-11)
All five findings fixed; sweep done. Next: the owner names the re-reviewer (rule 2).
