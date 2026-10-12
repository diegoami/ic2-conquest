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
- 0fc0bef plan + library. 8574910 batch 1: Q1ab (rebellion: Capua/Venusia -> Carthage/Illyria by the neighbour score, Heraclea -> Greece loyalty 90, Ariminum/Arretium/Pisae(Gaul dead) -> Gaul by the war-army rule; Pisae natural was captured by Gaul first), Q1c rebirth (9 cities, 9 defect lines), Q1d mercenary desertion, Q1e winter famine. Release `run-exp-g3-original-checks` created with 66 files.
- Batch 2 (this commit): Q1f (2 x 12 rounds: 32 of 312 debtor trials deposed; unity variant), Q2 natural and Q2b staged quarter pair, Q3 (news order), Q5 move (rough sea cost 3 vs 1), `g3_report.py`, `autosave_news.py`, `news_scan.py`. Findings so far: the Balance sheet before the tick does not predict the tick (tax base and wealth are rebuilt in it); the after-state sheet does (+21 = observed). Q1c_dead (Greece really eliminated), Q5 storm and Q6 running in a chain.
- Lessons: the news memory buffer can keep stale tail lines after a File>Open (Q1c seven_control showed lines of the previous game), so new lines are taken from the autosave's own news list (`autosave_news-*.jsonl`).
- Batch 3-4: Q5 storm (cond 80, 60: tripled roll shown), Q6 (120 trials: 27 trade, 9 alliance from the 3 neighbours), Q1c_dead, finding written, analysis_g3.txt, code_extract_g3.v2.txt.

## END
Done: checks 1a-f, 2, 3, 5 (move cost 3 and storm roll x3 with staged cell/word), 6; all with in-process controls. Not done: a natural rough-sea tile beside a fleet (staged instead); unhalved storm branch; two war armies for rule (c); AI nations' quarter income; no review requested, not merged. Next step: owner picks the reviewer; fix findings in `findings/2026-10-12-g3-original-checks.md`.
