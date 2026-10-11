# Running notes: g2-original-checks (issue #75)

Implementer: Sonnet subagent (the owner's choice). Branch `experiment/g2-original-checks`, worktree `.claude/worktrees/agent-a2d5dc6c44f0841d6`.
Data: `runs/experiments/data/run-exp-g2-original-checks/`; binaries in `artifacts/run-exp-g2-original-checks/` (worktree, git-ignored), release `run-exp-g2-original-checks`.

## Plan
- C3 (MM01, 0-move army): `g2_checks.py C3` on `fleet-port-antium-0734.SAV` (army 12 has moves 0 as saved; control = the same army staged to moves 8).
- C4 (MM03, unreachable target): `C4` on `run0-start` (army 0 at (100,37), target (100,25) 12 tiles north; control (100,32)).
- C5 (Change units): `C5a` Join 3/4 units, `C5b` Rename with two selected, `C5c` Split unit threshold + spinner range (type size table read from game memory at 0x478fca).
- C7 (storm): run-free re-analysis of the existing R85sA cell (`c7_storm_reanalysis.py`); fresh Wine only if a gap is left.
- Rule 6: commit and push each batch, `scripts/archive_measurements.py run-exp-g2-original-checks --commit`.

## Progress
- (start) branch created, win_updown.c (spinner range reader) built, g2_checks.py written.
- C3, C4, C4b, C5a, C5b run; C5c running (17/18 tests); C7 re-analysis done (no Wine); decompile reading of the move/select/storm code done. Batch commit now.
- C5c done (18 tests), archived, released (132 files). Findings draft and README written; PR opened.

## END
All four checks answered; C7 from existing R85sA data (no new Wine). Nothing blocked.
