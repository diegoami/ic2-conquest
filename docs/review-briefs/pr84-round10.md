# PR 84 round-10 review: round-9 reviewer's R1 fix (`tests/test_give_cities.py` strict receiver-tag check)

Round-9 reviewer (PR comment id 6129964973) R1: the round-7 follow-up's `assert "to1" in msg or "receiver" in msg.lower(), ...` accepts a generic message such as `"receiver failure"` with neither nation tag, weakening the receiver-specific check. Round-9 also noted the docstring's claim ("the caught `SystemExit` message contains `"to1"` ...") was not enforced by the assertion.

Round-10 commit `c81399b` (single-line change) addresses R1: the assertion is now strictly `"to1" in msg`, and the separate `"frm0" not in msg` check stays. The fallback to `"receiver" in msg.lower()` is removed.

The full chain of gates and checks (round-7 commits `2ec539c` and `83cecf2`) is unchanged: the wrapper still gates on `n == 1 and snapshot is not None`, the `receiver_injected` reach flag is asserted after the raise, and the regression-detection control still captures `b2_off2_before` and asserts the byte is unchanged.

## Scope (this round only)

Just `c81399b` on top of `83cecf2`. Diff:
```
git log -p 83cecf2..HEAD -- tests/test_give_cities.py
```
shows a 1-line change in the receiver-tag assertion. `running-notes.md` may have a progress line.

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

and exits 0. The change to `test_receiver_assertion_via_give_cities`:

1. The post-raise assertion is EXACTLY `assert "to1" in msg` (no `"receiver" in msg.lower()` fallback, no other permissive alternatives).
2. The separate `assert "frm0" not in msg` check is preserved.
3. All other round-7 + round-8 follow-up checks remain in place: the wrapper gate is still `if n == 1 and snapshot is not None:`, `receiver_injected` is still asserted `True` after the raise, and the control still asserts `b2[off2] == b2_off2_before` AND `receiver_injected is False` after the `snapshot=None` call.

## Blocking means (any one is enough; a blocking finding means rework, never approve)

1. The permissive fallback (`or "receiver" in msg.lower()` or any other `or`-clause on the receiver-tag check) is reintroduced — directly reversing the round-9 fix.
2. The `"frm0" not in msg` cross-check is missing.
3. The wrapper gate (`if n == 1 and snapshot is not None`) is weakened (e.g. drops `n == 1`, drops `snapshot is not None`, or both).
4. The `receiver_injected` reach-flag assertion or the `b2[off2] == b2_off2_before` byte-unchanged assertion is missing.
5. Any of the other three existing tests no longer prints its `all checks passed` line, or has been silently gutted.
6. The round-10 commit introduces a NEW tracked file beyond the optional `running-notes.md` amendment.

A bypass you proved is blocking.

Not blocking: wording and order of checks within the test, the running-notes.md progress-line formatting, and the broader PR (covered by earlier rounds).

## Report every blocking finding in this one review

This review is your only pass before the author fixes. Do not stop at the first blocking finding: finish reading the focused diff (`git log -p 83cecf2..HEAD -- tests/test_give_cities.py running-notes.md`) and the task file, check every Done-when line and every item under "Blocking means", and report all blocking findings together.

- Before you write the verdict, make one last pass over the focused diff for anything you have not yet rated, and say **"Final pass done"** as the **last line on its own** before the verdict block — followed by **a blank line**, then the verdict block (the parser rejects concatenated "Final pass done" + verdict).
- Number the findings R1, R2, … in order of severity.
- Do not rely on a later round. The author fixes everything you list, and the next review checks those fixes and new code only.
- If you ran out of time or context before covering the focused diff, say which files or sections you did not cover. Do not approve in that case.
