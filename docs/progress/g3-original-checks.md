# Running notes: g3-original-checks (issue #80)

Implementer: Claude Sonnet subagent (the owner's choice). Branch `experiment/g3-original-checks`, worktree `.claude/worktrees/g3`.
Data: `runs/experiments/data/run-exp-g3-original-checks/`; binaries in `artifacts/run-exp-g3-original-checks/` (git-ignored), release `run-exp-g3-original-checks`.

## Plan
Checks 1 (a-f), 2, 3, 5, 6 of `runs/experiments/data/run-exp-gap-v050/rows_g3.md` ("Original-side checks needed"); 4 needs no check. Template: the g1 experiment (`run-exp-g1-original-checks`, reviewed four times), its review fixes applied from the start: every autosave kept under a case/stamp/turn name and hashed (`keep_auto`), a positive/negative control in the SAME Wine process for each staged case, staged saves L1 (named fields only, length asserted, exclusive creation), claims backed by a tracked log or code extract.
- Runner `g3_checks.py <case>`, library `g3_lib.py` (copy of g1_lib plus calendar staging, memory snapshots of cities/nations/armies/news, a round helper). One fresh Wine process per case, fast rollingsave seed exe, seed 12345, Xvfb :99.
- Quarter tick runs inside the End turn that ends week 11 (`FUN_004514ec` calls `FUN_00451b40` when the week wraps to 1). Staged week = the save tail's week word (L1).
- Case plan: Q1a (own-allegiance city loyalty 2: Capua, Venusia, Pisae + controls), Q1b (Heraclea loyalty 2, Rome-held Greek-allegiance, Tarrentum untouched as internal control), Q1c (Greece unity 0 with 9 vs 7 Greek-allegiance cities at loyalty 5), Q1d (mercenary at purse 0 vs 100, one and two mercenary units), Q1e (winter rounds, 15 cities at stock 0, 10 controls at full stock), Q1f (all 15 AI nations at -50,000, repeated in one process), Q2 (natural six rounds from the start save with Balance sheets before the quarter round), Q3 (news order read from memory and the News window), Q5 (rough sea, only if a faithful staging works), Q6 (Rome at peace with all, repeated rounds counting offer boxes).
- Rule 6: commit and push each batch; `scripts/archive_measurements.py run-exp-g3-original-checks --commit`; `release_sync.py` after every batch.

## Progress
