# PR 79, round 3: re-check of the round-2 fixes (R1-R7)

Round 2 (gpt-6.1-sol, rework) is pasted at the end. Fixes since (Sonnet subagent): 8387021 (R1, R4: `harness/preserve.sh`,
`harness/new_game.sh`), 07c202b (R3: `staged()` exclusive create), c2f0e3f (R5: finding text), 4b502ba (R6, R7: tests),
6131ae4 (R2: G5 preserves and keeps autosaves; recovered `-065502` autosave; replacement trial `-071546`), 1beef09 (notes).
Check `git diff 1d90fdd..HEAD`: each round-2 finding's fix, and the new code. Do not re-review code untouched since round 2.
The running notes' "Review fixes, round 3" and "END (round 3)" blocks are in `docs/progress/g1-original-checks.md`.

## Scope
This task protects: measured evidence (saves, logs, outputs are never deleted or overwritten, rule 6) and the truth of every
claim in `findings/2026-10-11-g1-original-checks.md` (each backed by a tracked output or a cited save).

## Blocking means (any one is enough; a blocking finding means rework, never approve)
1. A round-2 finding R1-R6 is not fixed as asked, or its fix does not do what the notes or finding say.
2. What this task protects can be got past: a code path in the changed files (`harness/preserve.sh`, `harness/new_game.sh`,
   `g1_lib.py` `staged()`, the G5 branch of `g1_checks.py`, `g1_recover_g5.py`) still deletes or overwrites a save or a
   measured output, or the game can be launched after preservation failed. A bypass you proved is blocking.
3. A finding sentence claims more than its tracked output shows (e.g. the recovered `-065502` autosave's attribution, which
   rests on an mtime window; the replacement trial `-071546`), or a cited log/save is absent from the data folder,
   `SAVES.sha256` or the release sync records.
4. A test that passes with the behaviour deleted (`tests/test_new_game_sh_keeps_saves.py`, `tests/test_g1_staged_unique.py`,
   `tests/test_open_keeps_same_name.py`, `tests/test_new_game_keeps_autosaves.py`).
Not blocking: wording, style, and defects in code the PR did not change. File those as follow-ups. The author's stated
limits (`new_game.sh` not run under Wine, only its helpers offline; `Game.new_game`'s calibrated form coordinates) are not
blocking unless the finding claims otherwise.
When unsure, rate it blocking and say why. An approve with a proven bypass is the costliest mistake a review can make.

## Report every blocking finding in this one review
This review is your only pass before the author fixes. Do not stop at the first blocking finding: finish reading the whole
diff and the task file, check every Done-when line and every item under "Blocking means", and report all blocking findings
together.
- Before you write the verdict, make one last pass over the full diff for anything you have not yet rated, and say
  "Final pass done" as the last line before the verdict.
- Number the findings R1, R2, … in order of severity. A finding you held back because an earlier one was already blocking is
  a review defect: if two problems share a cause, list both and say so.
- Do not rely on a later round. The author fixes everything you list, and the next review checks those fixes and new code
  only, not anything you saw but did not report.
- If you ran out of time or context before covering the whole diff, say which files or sections you did not cover. Do not
  approve in that case.

## Round 2 review (for reference)
> PR review (gpt-6.1-sol)
> rework
> R1 harness/new_game.sh:10 blocking: The shell path still overwrites retained saves on a normal rerun. Running it again with the same `<out name>` copies the new AUTO save onto `$IC2_WORK/out/$2` with ordinary `cp`, replacing the earlier output despite the new move-aside step in the game folder. Refuse an existing output destination or allocate a unique destination, and add an offline regression check that verifies the earlier save’s bytes survive a rerun.
> 
> R2 runs/experiments/data/run-exp-g1-original-checks/g1_checks.py:204 blocking: G5 bypasses the new autosave-preservation helper when it starts a game through raw File > New. It neither preserves an existing `AUTO0720.SAV` before the game writes that name nor keeps the resulting G5 autosave afterwards. The successful `-065502` log records `AUTO0720.SAV` changing, but no G5-specific AUTO0720 copy appears in `SAVES.sha256` or the new release-sync records; the preceding `-065348` attempt also started a game. Preserve existing autosaves before accepting New, then keep, hash and upload each new measured autosave under a trial-specific name. Recover available outputs or clearly identify replacement trials while retaining the current logs.
> 
> R3 runs/experiments/data/run-exp-g1-original-checks/g1_lib.py:96 blocking: `staged()` still uses unconditional `write_bytes()` on a name that is not guaranteed unique. The new paired runner accepts repeated tags, and its staging tag uses `abs(treasury)`: arguments `test:-5100 test:5100` produce the same destination within one invocation, so the second branch overwrites the first staged save with different treasury bytes and leaves its earlier hash/log pointing at replaced evidence. Use exclusive creation with a sequence/versioned name, or reject collisions before writing. Add a regression check covering repeated tags and opposite-sign treasury values.
> 
> R4 harness/new_game.sh:3 blocking: Unlike `Game.move_aside`, the shell archive name has no collision protection. If `superseded-<timestamp>` already exists and contains the same AUTO basename, `mkdir -p` reuses it and ordinary `mv` overwrites the archived save. Moreover, a failed archive operation does not stop the script from launching the game, which can then overwrite the files left behind. Allocate a genuinely new directory, refuse replacement of archived files, and abort before launch if preservation fails. This is a separate preservation bypass from R1’s final output copy.
> 
> R5 findings/2026-10-11-g1-original-checks.md:65 blocking: The revised mobilisation description still broadens the distance condition to “within … 1.” The retained extract’s source line 48820 tests `sVar1 == 1`, not `sVar1 <= 1`; distance zero qualifies only through the separate flag-zero branch with `sVar1 < 6`. State the exact equality and conditional under-six alternative so the finding does not claim that a same-position army qualifies in the ordinary branch.
> 
> R6 tests/test_open_keeps_same_name.py:40 blocking: The identical-file check does not prove the owner’s “leaves an identical one” requirement. Replacing the production `if not tgt.exists(): shutil.copy(...)` guard with unconditional copying would still pass this entire test: copying identical bytes creates no superseded folder, which is all this branch asserts. Assert that no copy/write occurs for the identical destination, for example with a copy spy or deliberately distinct source/destination metadata, and verify that removing the skip-copy behaviour makes the test fail.
> 
> R7 tests/test_new_game_keeps_autosaves.py:57 non-blocking: Freeze the timestamp during the two preservation calls. Stubbing `sleep` does not guarantee that both calls occur in the same second; crossing a clock boundary can let the test pass without exercising the directory-collision handling its docstring claims to test.
> 
> Final pass done
> rework
> 
