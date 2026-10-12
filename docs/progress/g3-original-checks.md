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

## Review fixes, round 1 (Sonnet subagent, 2026-10-12)
Plan: fix R1-R9 of the gpt-6.1-sol review of PR #81 without a new Wine run (all are script, scan, report and text fixes); new outputs beside the old ones as versions.
- e3bb864 R1: `release_sync.py` writes its record with `versioned.write_new` (also when nothing is uploaded); offline test `release_sync_offline_test.py` (three same-second records -> `.json`, `.v2.json`, `.v3.json`).
- 3656b18 R2/R4: `news_scan2.py` (nations matched, whole treaty blocks, any distance, per-file SHA-256, versioned outputs `news_scan.v2/v3.txt`, `news_scan_summary*.txt`); `news_scan_v1_hashes.txt` reproduces "870 distinct" from the v1 list; `news_scan.txt` untouched.
- 1dddd87 R3/R7/R9 data: `q6_gate_check.txt` (both trade gates on the start save: 11 of 12 non-neighbours pass, Galatia has no trade partner), `code_extract_g3.v3.txt` (adds `FUN_0044fa20`, lines 53208-53234), `analysis_g3.v2.txt` (OCR proposer-name check: 32 exact + 4 `liyia` variants, 0 disagreements), `news_scan2_selftest.py` (reverse-order positive control).
- next commit: finding text for R2-R9 (see END).

## END (review round 1)
- R1 e3bb864: versioned sync record + offline test (`release_sync_offline_test.py`, its output file beside it).
- R2/R4 3656b18, 1dddd87: `news_scan2.py`, `news_scan.v3.txt`, `news_scan_summary.v2.txt` (1,246 saves read, 1,218 with both, 883 distinct, 907 blocks, 907 matched, 0 reverse, 0 unmatched); positive control `news_scan2_selftest.py`; `news_scan_v1_hashes.txt` (870 reproduced); finding section 3 rewritten.
- R3 1dddd87 + d88ccc9: both gates, fewer-than-three branch, `q6_gate_check.txt`; 30 stated as a ceiling, 27.5 with the gates.
- R5 d88ccc9: before-to-after vs capped increment (550, undeposed to 423); cooldowns -1..-5 only.
- R6 d88ccc9: alive vs dead Greece differences listed (Athens 166 keeps capital; Tarrentum unchanged); "thaw only" removed.
- R7 1dddd87, d88ccc9: `code_extract_g3.v3.txt` with FUN_0044fa20 (actual bounds 53208-53234, not 53236); line-5 reference fixed; v1, v2 kept.
- R8 d88ccc9: replay disclosed; 20 independent pairs at condition 60 (means 2.15 / 0.30), the 32-pair pool withdrawn.
- R9 1dddd87, d88ccc9: proposer-name check in `g3_report.py`, `analysis_g3.v2.txt`.
Left: nothing known. No Wine run, so no archive_measurements or release sync was needed (no new binaries). Not merged, no label change.

## Review fixes, round 2 (Sonnet subagent, 2026-10-12)
Plan: R1 only: relabel 27.5 as conditional, keep 30 as the gate-independent bound; fix label in q6_gate_check.py; revised output beside the preserved one (no Wine run, no per-roll verification).
- R1 (this commit): finding text, `q6_gate_check.py` label, new `q6_gate_check.v2.txt` (`q6_gate_check.txt` untouched).

## END (review round 2)
R1 fixed: 27.5 is now stated as a conditional calculation (assuming the initial eleven eligible non-neighbours stay the eligible set; unverified because AI seats change trade relations before the rolls); 30 is the gate-independent upper bound. Label corrected in `q6_gate_check.py`; revised output `q6_gate_check.v2.txt`; original preserved. No Wine run. Ready for re-check.
