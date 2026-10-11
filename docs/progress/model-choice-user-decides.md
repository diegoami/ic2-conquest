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
