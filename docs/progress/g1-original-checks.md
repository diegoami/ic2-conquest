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
- G3_cap (natural_target3, own3), G5 (patched, original), G6 (patched game, nogame_menu, nogame_sysclose; original game) run. G6 original game: first attempt hung at A2 and was killed by the timeout (log kept, wineserver -k), second run complete. Batch committed and pushed.
- G2_depose (3 runs), G7 (seeds 1-10, 12345), G10 (third run is the usable one: news lines are C strings at 0x49f994 + 61 i; first two logs read them wrongly, kept), G8 (natural, low_both), code extract v2, exe strings, g7_summary written. Batch committed and pushed.
- G9 run (padded army table refusal + control); committed and pushed.
- Finding `findings/2026-10-11-g1-original-checks.md`, README, g5_diff written; PR opened.

## END
All eight checks (2, 3, 5, 6, 7, 8, 9, 10) answered; nothing blocked. Not done: a real X-button click (SC_CLOSE posted instead), staged hc mercenary (crashed the process on load), G3 ally/war target. No reviewer, no merge.

## Review fixes (PR #79; subagent Sonnet, wound down at the owner's request)

- 485fb74 R1(a,c): `Game.new_game` moves AUTO* aside; offline test; G10 usable run's autosaves recovered (`g1_recover.py`).
- next commit: R1(b) `keep_auto` in runner (G2_depose, G10, pair), R2 `G2_depose_pair` + 6 logs, R3 staging length assert and name check, finding "Review fixes" section.

## END (review fixes)
Done: R1 (a driver + test, c recovery; b runner keeps autosaves in G2_depose, G10 and the pair case); R2 (4 paired logs: control deposes, -5,100 and -4,990 do not, both orders); R3 code (assert + name validation) and text.
Remaining, with the next step:
- R1 G10 replacement not needed (usable run recovered); G2_depose first-run saves are lost (stated). Also list other deletion paths in the PR: `harness/driver.py` Xvfb lock (not a measurement), `set_seed(None)` unlinks SEED.TXT (input file, value in SEED.LOG), `save_as(overwrite=True)` caller-scratch only; `harness/new_game.sh` fixed to move aside; `Game.open` copies a save over a same-named file in the game folder (not fixed: decide).
- R3: run `python3 g1_checks.py G2_merc hc` (name "Egyptian Cav  Battalion" already in `g1_checks.py`), verify Balance sheet, write it into the finding.
- R4: text note added; still qualify the "agreed" sentence in the Data paragraph and cite `-232104` there.
- R5: correct the `FUN_0044a120` text (last qualifying army kept, capacity checked after, troop gate includes the incoming unit); extend `make_code_extract.py` with the helper bodies (`FUN_0044a120`, `FUN_0044a4e0`, `FUN_00449f08`) or narrow the claim.
- R6: extend `make_exe_strings.py` with "already trades with", "trades with 3" and variants (negative search kept), or narrow the claim to the observed refusal and `TPolitics_MakeTrade`.
- R7: replace the raw clicks (117,117) and (344,194) in the G5 branch of `g1_checks.py` with control-derived targeting (inspect `g.controls("Imperial Conquest 2")` on the New Game form), verify Rome's human flag and the form's closing, re-run `G5 patched`.
After each Wine run: `scripts/archive_measurements.py run-exp-g1-original-checks --commit` (it printed it did not commit because of an ignored __pycache__ path; commit by hand), `python3 runs/experiments/data/run-exp-g1-original-checks/release_sync.py`.

## Review fixes, round 2 (Sonnet subagent, 2026-10-12)
Plan: Game.open, then R3 rerun, R4, R5, R6, R7, one commit each, push after each.
- 1a496dd Game.open moves a differing same-named file aside (`Game.move_aside`, shared with new_game); `tests/test_open_keeps_same_name.py`; finding note on other deletion paths.
- 79515de R3: `G2_merc hc` run, `g1_checks-G2_merc-20261012-065006.jsonl`: Mercenary units 86, Total 963 = 877 + 86 (no crash); R4 text (qualified agreement, `-232104` cited); data archived, release synced (28 files).
- 5264b2a R5: G9 code reading corrected; extract v3 (callees) and v4 (min/max helpers); interpretations marked.
- 0909951 R6: `exe_strings_g1.v2.txt`: "already trades with", "trades with 3" etc. NOT FOUND (exact and case-insensitive).
- 8166ff3 R7: G5 branch uses `g.controls("Human and computer leaders")`; `g1_checks-G5-20261012-065502.jsonl`: human [0], form closed, G5 result unchanged; release synced (27 files).

## END (round 2)
Done: all six items (commits above); offline tests `test_new_game_keeps_autosaves` and `test_open_keeps_same_name` pass. Not done / uncertain: `Game.new_game` in the driver still uses its calibrated fixed form coordinates (only the G5 branch was asked); the hc staging's price-4 reading of the formula is inferred from the 86 (not read from code); G5 original exe not re-run (only patched asked). Failed attempts `g1_checks-G5-20261012-065259.jsonl` and `-065348.jsonl` kept. No merge, no review requested.

## Review fixes, round 3 (Sonnet subagent, 2026-10-12)
Plan: R1+R4 (new_game.sh), R3, R5, R6+R7 (tests), R2 (G5 re-run), one commit each, push after each.
- 8387021 R1, R4: `harness/preserve.sh` (unique superseded dir, `mv -n` + check, abort before launch; unique output name `.N`); `tests/test_new_game_sh_keeps_saves.py`.
- 07c202b R3: `staged()` exclusive create with `.vN` suffix; `tests/test_g1_staged_unique.py`.
- c2f0e3f R5: finding states `sVar1 == 1` and the conditional `< 6` branch.
- 4b502ba R6, R7: copy spy + mtime check in `test_open_keeps_same_name`; frozen clock in `test_new_game_keeps_autosaves`. R6 guard-removal check: with `if not tgt.exists():` replaced by `if True:` in `Game.open`, the test FAILED ("identical file copied again"); restored with `git checkout`, passes.
- 6131ae4 R2: G5 supersedes AUTO* before File > New and keeps its autosave; recovered `G5_20261012-065502_recovered_AUTO0720.SAV`; replacement trial `g1_checks-G5-20261012-071546.jsonl`; finding "Review fixes, round 3"; data archived (66 binaries hashed), release synced (11 files, no 403).

## END (round 3)
Done: R1-R7, all offline tests pass (`test_new_game_keeps_autosaves`, `test_open_keeps_same_name`, `test_new_game_sh_keeps_saves`, `test_g1_staged_unique`). Evidence per item above. Not done / limits: the G5 autosaves of `-233302`, `-065259`, `-065348` are not recoverable (stated in the finding; the one live `AUTO0720.SAV` is hash-identical to the start save, so its link to run `-065502` rests on the mtime window); `Game.new_game` keeps its fixed form coordinates; `new_game.sh` itself was not run under Wine (shell helpers tested offline). Next step: the owner's re-review. No merge, no review requested.

## Review fixes, round 4 (Sonnet subagent, 2026-10-12)
Plan: R1 (preserve.sh fails closed), R3 (injected mv failure + new_game.sh launch stub test), R2 (exclusive creation in the recovery script), one commit each, push after each.
- 7cbc6d9 R1: `supersede_autos` lists the folder via `preserve_ls` and fails closed (non-zero, "cannot list") when it fails or the folder is missing; a successful empty listing is success. Test injects a failing `preserve_ls`. Mutation: listing failure ignored (`|| true`) -> test FAILED; restored.
- (R3 commit below) failure to move injected by a stub `mv` on PATH (no UID dependence); `harness/new_game.sh` run for real with fake wine/xdotool/wineserver (`IC2_ENV_SH`, `WINESERVER` overrides, tests only) asserting no launch + non-zero when mv fails and launch + the file kept when it works. Mutations: propagation after `mv -n` removed -> FAILED; caller's abort replaced by `|| true` -> FAILED; both restored, all 4 offline tests pass.
- (R2 commit below) `g1_recover_g5.py`: `reserve()` exclusive creation (`'xb'` for the save, `'x'` for the log) with `.vN` names on collision, no exists()-then-copy; main guarded and `recover()` testable; `tests/test_g1_recover_g5.py` (temp dirs) asserts earlier save/log bytes survive and SAVES.sha256 is only appended. Mutation: `'x'` -> `'w'` in `reserve` -> "earlier save replaced", FAILED; restored. The recovery was NOT re-run on the real game folder; the existing recovered save and log are untouched.

## END (round 4)
R1 7cbc6d9: `supersede_autos` fails closed on a listing failure (injected `preserve_ls`); mutation (`|| true`) fails the test. R3 46f896a: stub `mv` on PATH + `new_game.sh` run with fake wine/xdotool/wineserver (`IC2_ENV_SH`, `WINESERVER` test overrides): no launch and non-zero exit when preservation fails, launch when it works; two mutations (no propagation after `mv -n`; caller abort -> `|| true`) both fail the tests. R2 (commit after this note): exclusive creation for save and log, versioned names, collision tests; mutation fails. All five offline tests pass (new_game_sh_keeps_saves ~12 s, new_game_keeps_autosaves, open_keeps_same_name, g1_staged_unique, g1_recover_g5). Left: nothing known; `new_game.sh` still not run under real Wine (only stubs). Next step: owner's re-review. No merge, review request or label change.
