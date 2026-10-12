# PR 84 round-7 review: round-6 review's R1 fix on `tests/test_give_cities.py`

Round-6 review (PR comment id `6129576906`, posted 2026-10-12 17:48Z) verdict was **rework** with two blocking findings. This round-7 review covers the fixes for those two findings on `experiment/g4-followups`. The round-6 fix's commit for `a7c0906` (the `test_receiver_assertion_via_give_cities` test) is the base; the round-7 commits sit on top of `c8f72cb`.

## Scope

Round-6 R2 (the brief-file commit) was fixed by dropping the brief commit from `experiment/g4-followups`; the `docs/review-briefs/pr84-round7.md` file lives only in the local working tree of the reviewer run, not on the PR branch. This round's diff is therefore only the round-6 review's R1 fix to `tests/test_give_cities.py` (no other file changes). The reviewer checks ONLY this change.

The round-7 commits amend `test_receiver_assertion_via_give_cities`. The reviewer's job is to confirm the round-6 reviewer's R1 is fixed: the wrapper now injects the rogue byte ONLY for the receiver (`n == 1`) and ONLY when `snapshot is not None`. The test must also verify that the receiver call was actually reached (i.e. an injection in the wrapper was triggered before the assertion fired) and that the caught `SystemExit` message identifies the receiver's call (e.g. references `to1` or the receiver's `_give_cities_put` tag, not the sender's). The existing `snapshot=None` control and the `finally` restoration of the original `_give_cities_put` are kept.

## Done-when

All four tests in `tests/test_give_cities.py` pass with the diff applied:

```
cd /home/diego/projects/<worktree>
python3 -m tests.test_give_cities
```

prints all of:

```
test_consistent_333_to_334: all checks passed
test_receiver_assertion_active: all checks passed
test_oversized_receiver_list_raises: all checks passed
test_receiver_assertion_via_give_cities: all checks passed
```

and exits 0. The amended `test_receiver_assertion_via_give_cities` must:

1. Call the production `L.give_cities(0, 1, [moved])(b)` — NOT `L._give_cities_put(...)` directly.
2. Monkey-patch `L._give_cities_put` with a wrapper that injects a rogue byte write at the receiver's `stage._nation(b, n) + 0x2e4` (a single byte; outside the city-list region `+0x48..+0x2e4` and the count word `+0x446..+0x448`). The injection MUST fire ONLY when `n == 1 AND snapshot is not None`. For the sender call (`n == 0` with a snapshot) the wrapper MUST NOT inject; for any call with `snapshot is None` the wrapper MUST NOT inject.
3. Track that the receiver's wrapper call actually ran the injection (e.g. set a flag such as `wrapper_injected = True` inside the `if n == 1 and snapshot is not None` branch). After `L.give_cities(0, 1, [moved])(b)` raises `SystemExit`, assert `wrapper_injected is True`. A `False` (the injection never fired) means the assertion came from the sender's `_give_cities_put` instead of the receiver's, which is the exact regression round-6 R1 caught.
4. Assert that the caught `SystemExit` message identifies the **receiver's** call. The production `_give_cities_put` raises with `tag = f"to{to} {len(t)} cities"`, so the message contains `to1 334 cities` (or the receiver's tag string). Assert at least one of `"to1"`, `"receiver"`, or the receiver-side tag is in the message; assert that the message does NOT come from the sender (e.g. no `"frm0"`, no sender-side tag).
5. Run a regression-detection control: call the wrapper directly with `n == 1, snapshot=None` (and verify no injection fires, no `SystemExit`). This proves the first part is exercising the snapshot gate.
6. Restore the original `L._give_cities_put` in a `finally` block (no contamination across tests).

## Blocking means (any one is enough; a blocking finding means rework, never approve)

1. The wrapper still injects when `n == 0` (sender) OR injects without the `snapshot is not None` gate. Round-6 R1 was that the sender's injection fires first; the new wrapper MUST limit injection to `n == 1 and snapshot is not None`.
2. The injection offset is wrong (e.g. inside the city-list region `+0x48..+0x2e4`, the count word `+0x446..+0x448`, or the `allowed` whitelist). The byte must be at `stage._nation(b, n) + 0x2e4` only.
3. The wrapper does not set a reach flag (or sets it outside the `n == 1 and snapshot is not None` branch). Without the reach flag the test cannot distinguish "the receiver's assertion fired" from "the sender's assertion fired".
4. The caught `SystemExit` is asserted with message content that does NOT identify the receiver's call (e.g. only `"outside the city-list region"` was checked, which the sender's assertion would also produce). The assertion must specifically identify the receiver.
5. The regression-detection control is missing, or it does not exercise `snapshot=None` (e.g. it calls the wrapper with `snapshot=snap` and expects no raise, which the wrapper would correctly raise on).
6. The wrapper is not restored in `finally` (a failure leaves the module patched).
7. Any of the other three existing tests (`test_consistent_333_to_334`, `test_receiver_assertion_active`, `test_oversized_receiver_list_raises`) no longer prints its `all checks passed` line, or has been silently gutted.
8. The diff includes files other than `tests/test_give_cities.py` (the round-7 changes are narrowly scoped to the R1 fix; `running-notes.md` may be amended with a progress line, but no other tracked files should be touched).

A bypass you proved is blocking.

Not blocking: wording and order of operations in the test (as long as the gating, reach flag, exception-message check, snapshot control and `finally` are all present), `running-notes.md` updates that follow the project's running-notes convention, and any change to code the round-7 commits did not touch.

## Report every blocking finding in this one review

This review is your only pass before the author fixes. Do not stop at the first blocking finding: finish reading the whole diff (`git log -p c8f72cb..HEAD -- tests/test_give_cities.py running-notes.md`) and the task file, check every Done-when line and every item under "Blocking means", and report all blocking findings together.

- Before you write the verdict, make one last pass over the full diff for anything you have not yet rated, and say "Final pass done" as the last line before the verdict.
- Number the findings R1, R2, … in order of severity. A finding you held back because an earlier one was already blocking is a review defect: if two problems share a cause, list both and say so.
- Do not rely on a later round. The author fixes everything you list, and the next review checks those fixes and new code only, not anything you saw but did not report.
- If you ran out of time or context before covering the whole diff, say which files or sections you did not cover. Do not approve in that case.
