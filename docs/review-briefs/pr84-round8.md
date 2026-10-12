# PR 84 round-8 review: round-7 follow-up (control tightening) on `tests/test_give_cities.py`

Round-6 review (PR comment id `6129576906`) verdict was rework with R1 (test gates injection for any nation, masking the regression if the receiver drops `snapshot=snap`) and R2 (round-6 diff included `docs/review-briefs/pr84-round6.md` itself). Both were addressed:

  * R2: the brief commit was dropped from `experiment/g4-followups` (force-pushed back to `c8f72cb`); the round-7/8 brief lives only in the reviewer's local working tree, not on the PR branch. Round-8's diff therefore does NOT contain `docs/review-briefs/*`.
  * R1 round-7: `a7c0906` was the round-6 test (which let the regression-detection property slip). Round-7 commit `2ec539c` gates the wrapper to `n == 1 and snapshot is not None`, adds a `receiver_injected` reach flag, asserts the caught `SystemExit` message contains `"to1"` (the receiver's tag) and not `"frm0"` (the sender's tag), and asserts `receiver_injected is True` after the raise.

Round-7 review was attempted with `openai/gpt-6.1-sol#medium` (session `ses_ecebb171fffedPa4co6kR4qD1Y`, run dir `rendered/pr84-1815cb/run-1`). The model's final message contained a real, correct R1 — that `assert receiver_injected is before_injected` in the regression-detection control was trivially `True is True` because the positive case had already flipped the flag — but its final message format had `Final pass donePR review (gpt-6.1-sol)` on a single line (no newline), so the script's parser classified the run as `bad-format` (process failure) and posted nothing.

Round-7 follow-up commit `83cecf2` addresses that R1 inline (without waiting for a round-7 review comment to be reposted): the control now (a) captures `b2[off2]` before the call and asserts the byte is unchanged after (a real injection check at the +0x2e4 offset), and (b) resets `receiver_injected = False` before the control and asserts it stays `False`. Both adversarial simulations pass: production `snapshot=None` for the receiver (a regression at `g4_lib.py:453`) makes the positive case fail with "give_cities via patched _give_cities_put did NOT raise"; weakening the wrapper gate to drop `and snapshot is not None` makes the control fail with "snapshot=None control flipped the receiver +0x2e4 byte".

## Scope

This round's commits on `experiment/g4-followups` are:

  * `2ec539c` (round-7): gate receiver-only injection, reach flag, receiver-tag assertion, `finally` restoration.
  * `83cecf2` (round-7 follow-up): reset `receiver_injected = False` and add `b2[off2]` byte-unchanged check in the snapshot=None control.

The diff vs base (`d50a6a98`) covers `tests/test_give_cities.py` and `running-notes.md` only. Reviewer checks ONLY these two commits.

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

and exits 0. The `test_receiver_assertion_via_give_cities` test (after round-7 + round-7 follow-up commits) must:

1. Call the production `L.give_cities(0, 1, [moved])(b)` — NOT `L._give_cities_put(...)` directly.
2. Monkey-patch `L._give_cities_put` with a wrapper that injects a rogue byte write at the receiver's `stage._nation(b, n) + 0x2e4` (a single byte; outside the city-list region `+0x48..+0x2e4` and the count word `+0x446..+0x448`). The injection MUST fire ONLY when `n == 1 AND snapshot is not None`.
3. Track reach with `receiver_injected = True` inside the gate. After `L.give_cities(...)` raises `SystemExit`, assert both:
   a. `"to1"` (the receiver's tag) is in the caught message and `"frm0"` (the sender's tag) is NOT — guards against a sender-origin abort slipping past the raised-flag check.
   b. `receiver_injected is True` — proves the gated receiver injection actually fired (a sender-origin abort would leave it False).
4. Run a regression-detection control that:
   a. Captures `b2_off2_before = b2[off2]` BEFORE the call.
   b. Resets `receiver_injected = False`.
   c. Calls `patching_put(b2, 1, [], 0, snapshot=None, allowed=set())`.
   d. Asserts no `SystemExit` fires.
   e. Asserts `b2[off2] == b2_off2_before` (the wrapper did NOT write to the receiver's +0x2e4 byte, even with the gate held out).
   f. Asserts `receiver_injected is False`.
5. Restore the original `L._give_cities_put` in a `finally` block.

## Blocking means (any one is enough; a blocking finding means rework, never approve)

1. The wrapper still injects without the `n == 1 and snapshot is not None` gate (e.g. drops `snapshot is not None`, drops `n == 1`, or both).
2. The injection offset is wrong (e.g. inside the city-list region, the count word, or the `allowed` whitelist) — the byte must be at `stage._nation(b, n) + 0x2e4`.
3. The `receiver_injected` reach flag is missing, OR the assertion after the raise is missing, OR `before_injected = receiver_injected` (a trivially-true capture) is reintroduced in place of a reset-and-assert.
4. The caught `SystemExit` is asserted with content that does not specifically identify the receiver (`"to1"` tag or `"receiver"` in lower-case) AND rejects a sender-origin message (`"frm0"` not in the message).
5. The regression-detection control is missing one of the post-call checks: `b2[off2] == b2_off2_before` AND `receiver_injected is False`.
6. The `b2_off2_before` capture is missing (control reduced to a single assertion).
7. The wrapper is not restored in `finally`.
8. Any of the other three existing tests no longer prints its `all checks passed` line, or has been silently gutted.
9. The diff includes files beyond `tests/test_give_cities.py` and `running-notes.md`.
10. The change is **not verifiable** — i.e. an adversarial mutation that flips `g4_lib.py`'s receiver call to `snapshot=None` does NOT cause the positive case to fail. (Run a quick adversarial: replace `snapshot=snap` with `snapshot=None` on line 453 of `g4_lib.py`, run the test, expect the failure "give_cities via patched _give_cities_put did NOT raise on rogue +0x2e4 byte"; restore the file.)

A bypass you proved is blocking.

Not blocking: wording and order of operations in the test (as long as every check in the spec above is present), `running-notes.md` updates that follow the project's running-notes convention, and any change to code these round-8 commits did not touch.

## Report every blocking finding in this one review

This review is your only pass before the author fixes. Do not stop at the first blocking finding: finish reading the whole diff (`git log -p c8f72cb..HEAD -- tests/test_give_cities.py running-notes.md`) and the task file, check every Done-when line and every item under "Blocking means", and report all blocking findings together.

- Before you write the verdict, make one last pass over the full diff for anything you have not yet rated, and say **"Final pass done"** as the **last line on its own** before the verdict block — followed by **a blank line**, then the verdict block. (The round-7 attempt concatenated `Final pass done` and `PR review (gpt-6.1-sol)` on one line and the parser rejected it; please avoid that.)
- Number the findings R1, R2, … in order of severity. A finding you held back because an earlier one was already blocking is a review defect: if two problems share a cause, list both and say so.
- Do not rely on a later round. The author fixes everything you list, and the next review checks those fixes and new code only, not anything you saw but did not report.
- If you ran out of time or context before covering the whole diff, say which files or sections you did not cover. Do not approve in that case.
