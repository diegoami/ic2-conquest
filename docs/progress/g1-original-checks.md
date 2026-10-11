# Running notes: g1-original-checks (issue #78)

Implementer: Sonnet subagent (the owner's choice). Branch `experiment/g1-original-checks`, worktree `.claude/worktrees/agent-ab471223174aee68e`.
Data: `runs/experiments/data/run-exp-g1-original-checks/`; binaries in `artifacts/run-exp-g1-original-checks/` (git-ignored), release `run-exp-g1-original-checks`.

## Plan
Checks 2, 3, 5, 6, 7, 8, 9, 10 of `runs/experiments/data/run-exp-gap-v050/rows_g1.md` ("Original-side checks needed"). Runner `g1_checks.py <case>` (library `g1_lib.py`), one fresh Wine process per case, seed 12345, L1 staging labelled per case.
- G2: `G2_merc`, `G2_fleet`, `G2_debt`, `G2_depose` (Balance sheet read by OCR of kept images, cross-checked with a recomputation from game memory of `TBalanceSheet_PaintBalance`).
- G3: `G3_cap` (natural 3-partner target; staged own cap + control).
- G5: `G5 patched|original`; G6: `G6 ...` (WM_SYSCOMMAND SC_CLOSE through win_close.exe: no window manager under Xvfb, so no X button); G7: `G7 <seed>`; G8: recruit dialog; G9: mobilise refusal (staged: army table full); G10: news header from game memory (0x49f994 + 61 * i).
- Rule 6: commit and push each batch; `scripts/archive_measurements.py run-exp-g1-original-checks --commit`; release synced with `release_sync.py`.

## Progress
- G2_merc, G2_fleet, G2_debt run (see logs). Notes: a staged mercenary `hc` (label 35, q9) save made the process unreadable (`PermissionError` on /proc/<pid>/mem, log `g1_checks-G2_merc-20261011-232227.jsonl` or the one holding that error); re-done with `hi` and `li` mercenaries.
