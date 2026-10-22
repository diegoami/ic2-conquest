# PR 79, round 2: re-check of the review fixes (R1-R7) and the Game.open change

Round 1 (gpt-6.1-sol, rework) is pasted at the end. Since then two fix rounds (Sonnet subagent) landed on this branch:
round 1 fixes 485fb74, 3d324d1, 2792eab (R1, R2, R3 code side); round 2 1a496dd (Game.open), 79515de (R3 rerun, R4),
5264b2a (R5), 0909951 (R6), 8166ff3 (R7), f739f2b (notes). The running notes are `docs/progress/g1-original-checks.md`
("Review fixes" and "Review fixes, round 2", with their END blocks). Check each R item's fix and the new code since round 1
(`git diff 2792eab~3..HEAD` covers both fix rounds; the round-1 fixes start at 485fb74). Do not re-review untouched code.

Owner's decision for this round (2026-10-12): `Game.open` in `harness/driver.py` must not overwrite a same-named file in the
game folder; it moves a differing one aside (like `Game.new_game`) and leaves an identical one.

## Scope
This task protects: measured evidence (saves, logs, outputs are never deleted or overwritten, rule 6) and the truth of every
claim in `findings/2026-10-11-g1-original-checks.md` (each backed by a tracked output or a cited save).

## Blocking means (any one is enough; a blocking finding means rework, never approve)
1. An R1-R6 item of round 1 is not fixed as asked, or its fix does not do what the notes or finding say.
2. What this task protects can be got past: a code path in the changed files (`harness/driver.py` `Game.new_game`,
   `Game.open`, `Game.move_aside`, `harness/new_game.sh`, the g1 runner and staging helpers) still deletes or overwrites
   a save or a measured output, or a re-run can overwrite an earlier one. A bypass you proved is blocking.
3. A finding sentence still claims more than its tracked output shows (e.g. the R5 code reading against
   `code_extract_g1*.txt`, the R6 absence claim against `exe_strings_g1*.txt`, the R3 hc outcome against its log, the R4
   OCR agreement), or a cited log/save does not exist in the data folder, `SAVES.sha256` or the release sync records.
4. A test that passes with the behaviour deleted (`tests/test_new_game_keeps_autosaves.py`,
   `tests/test_open_keeps_same_name.py`); a staged save whose length changes; an earlier measured file rewritten instead
   of versioned beside it.
Not blocking: wording, style, and defects in code the PR did not change. File those as follow-ups. The author's own
"left or uncertain" list (fixed coordinates still in `Game.new_game`, the price-4 inference, G5 original not re-run) is
not blocking unless the finding claims otherwise.
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

## Round 1 review (for reference)
> PR review (gpt-6.1-sol)
> rework
> R1 runs/experiments/data/run-exp-g1-original-checks/g1_checks.py:235 blocking: Preserve the measured turn saves before another trial can overwrite them. G10 logs `AUTO0721.SAV` through `AUTO0726.SAV` but never calls `keep`; none of those trial-specific saves appears in `SAVES.sha256` or the upload records. The three G10 runs reuse those names. G2_depose likewise logs `AUTO0721.SAV` at line 65 without archiving it, and subsequent G7 calls invoke `Game.new_game`, which deletes `AUTO*` files. Archive each measured autosave under a case/stamp/turn-specific name, hash and upload it, and cite it in the finding. Recover the original outputs if available; otherwise retain the existing logs and add clearly identified replacement trials rather than presenting missing saves as preserved evidence.
> 
> R2 runs/experiments/data/run-exp-g1-original-checks/g1_checks.py:57 blocking: The deposition “no box” observations lack the required positive control in the same process. Each treasury is tested through a separate invocation and `g.load`; the environment records confirm different PIDs for the -5,100, -5,200 and -4,990 cases. Add a deposition-triggering control in the same Wine process as each non-deposition test, opening the appropriate staged saves between branches. Keep the existing measurements and cite the new paired logs; the separate -5,200 process does not meet the brief’s same-process requirement.
> 
> R3 runs/experiments/data/run-exp-g1-original-checks/g1_lib.py:98 blocking: Validate the encoded unit-name length before assigning it to the 24-byte slice. `Egyptian Dragoons  Battalion` is 28 bytes, and `ljust(24)` does not truncate: the assignment inserts four bytes and shifts every subsequent save field. Thus the retained `hc` attempts are malformed-save trials, not staging confined to the named unit fields as the finding claims. Use a name fitting the format’s 23-byte-plus-NUL limit, assert that staging preserves the save length, and document the old attempts as staging-corrupted while preserving their artifacts and logs.
> 
> R4 findings/2026-10-11-g1-original-checks.md:7 blocking: Correct the assertion that OCR and memory agreed in every sheet reading. In `g1_checks-G2_merc-20261011-231938.jsonl`, lines 3 and 6 record the mercenary OCR value as `null`, while memory reports 0 and 18 respectively; those records also lack `ocr_attempts`. Line 13 nevertheless cites that first log for the control’s mercenary value. Explicitly identify its incomplete OCR measurements, qualify the agreement/attempt-retention claims, and cite a later complete control reading, such as `-232104`, for the fully OCR-cross-checked figures.
> 
> R5 findings/2026-10-11-g1-original-checks.md:65 blocking: Make the mobilisation code reading match the extract. `FUN_0044a120` selects the last qualifying nearby army during its loop and checks capacity only afterwards; it does not search for any nearby army with room. Its troop gate also includes the incoming queued unit, not merely the army’s existing total. The interpretations of slot capacity, distance and “no free tile” rely on helpers whose bodies are absent from this extract. Correct the selection and combined-troop description, and either retain pinned extracts of the supporting helpers or narrow the claim to the conditions directly shown.
> 
> R6 findings/2026-10-11-g1-original-checks.md:29 blocking: Back the whole-executable absence claim with a retained negative search, or narrow it to the observed refusal and the quoted `TPolitics_MakeTrade` branch. `exe_strings_g1.txt` lists selected positive literals, and `make_exe_strings.py` never searches for `already trades with 3 nations`; it therefore cannot establish that this wording is absent from the executable.
> 
> R7 runs/experiments/data/run-exp-g1-original-checks/g1_checks.py:160 non-blocking: Replace the raw New Game clicks at `(117,117)` and `(344,194)` with control-derived targeting and explicit verification of Rome’s human flag and form dismissal. The retained runs succeeded, but these fixed coordinates introduce a fragile driver path alongside otherwise control-based interactions.
> 
> Final pass done
> rework
> 
