# PR 79, round 4: re-check of the round-3 fixes (R1-R3)

Round 3 (gpt-6.1-sol, rework) is pasted at the end. Fixes since (Sonnet subagent): 7cbc6d9 (R1: `preserve.sh` fails closed
when the game folder cannot be listed), 46f896a (R3: injected `mv` failure for any UID; `new_game.sh` run with stubbed
wine/xdotool/wineserver; test-only overrides `IC2_ENV_SH`, `WINESERVER`), 18a0174 (R2: `g1_recover_g5.py` exclusive
creation and `.vN` names; `tests/test_g1_recover_g5.py`). Check `git diff 86a40d4..HEAD`: each round-3 finding's fix and the
new code (including the new test-only overrides: they must not open a way past preservation in normal use). Do not
re-review code untouched since round 3. Notes: "Review fixes, round 4" / "END (round 4)" in `docs/progress/g1-original-checks.md`.

## Scope
This task protects: measured evidence (saves, logs, outputs are never deleted or overwritten, rule 6) and the truth of every
claim in `findings/2026-10-11-g1-original-checks.md` (each backed by a tracked output or a cited save).

## Blocking means (any one is enough; a blocking finding means rework, never approve)
1. A round-3 finding R1-R3 is not fixed as asked, or its fix does not do what the notes or finding say.
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

## Round 3 review (for reference)
> PR review (gpt-6.1-sol)
> rework
> R1 harness/preserve.sh:8 blocking: Enumeration failure is treated as “nothing to preserve.” For a non-root user, a game directory with write/search permissions but no read permission makes `compgen -G "$g/AUTO*"` fail, so this function returns success without moving existing autosaves. The caller then launches the game; known filenames remain accessible and writable, allowing New Game to overwrite `AUTO0720.SAV`. Fail closed when the game directory cannot be enumerated, distinguishing that from a successfully checked empty directory. Add an offline regression check proving that enumeration failure prevents launch.
> 
> R2 runs/experiments/data/run-exp-g1-original-checks/g1_recover_g5.py:12 blocking: The new recovery script does not enforce its “never overwrites” guarantee. Two invocations can both pass `dst.exists()` before either copies; the second `shutil.copy2` then opens the first invocation’s retained save for replacement. If their stamps match, line 18 also truncates the same recovery log through unconditional `write_text`. Independently, an existing recovery-log destination is never checked. Reserve both save and log destinations with exclusive creation, refusing collisions or allocating versioned names before appending hashes. Add collision checks asserting that earlier save and log bytes survive.
> 
> R3 tests/test_new_game_sh_keeps_saves.py:45 blocking: The only preservation-failure assertion is skipped when the test runs as root, where making the destination read-only does not induce a failed move. Consequently, deleting the helper’s failure-return behaviour can still leave the entire test passing in that environment, contrary to the brief’s explicit mutation-test requirement. Inject a deterministic move failure instead of relying solely on permissions, assert the non-zero result regardless of UID, and verify that removing failure propagation makes the test fail. Also exercise the caller’s abort behaviour rather than relying only on the presence of an `exit 1` string.
> 
> Final pass done
> rework
> 
