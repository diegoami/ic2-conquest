# PR 84 round-9 review: round-8 follow-up to the round-7 reviewer R1 (control tightening)

Rounds 1–5 (PR #84 comments id 6127815250, 6128286048, 6129576906 et al.) reviewed the PR's broader 82-file scope (cases A–L of issue #83, the v0.5.0 gap analysis) over multiple iterations. The last usable *posted* review verdict on the broader scope is round-5/6 (R1: gating the receiver-only injection in `test_give_cities.py`; R2: the round-6 diff included the round-6 brief itself, addressed by dropping the round-6 brief commit from the branch). This round-9 review is scoped ONLY to the round-8 follow-up commit (`83cecf2`, on top of `2ec539c`, on top of `c8f72cb`) — i.e. `git log -p c8f72cb..HEAD -- tests/test_give_cities.py running-notes.md`.

## Scope (this round only)

Two new commits on `experiment/g4-followups`:

  * `2ec539c` (round-7): gate receiver-only injection, reach flag, receiver-tag assertion, `finally` restoration.
  * `83cecf2` (round-8 follow-up, addresses the round-7 reviewer's R1 inline): reset `receiver_injected = False` BEFORE the regression-detection control call, and add a `b2[off2] == b2_off2_before` byte-unchanged check after the call. The previous `assert receiver_injected is before_injected` was trivially `True is True` because the positive case had already flipped the flag.

The reviewer may use `git log -p c8f72cb..HEAD -- tests/test_give_cities.py running-notes.md` for the focused diff. Earlier rounds' comments cover the rest of the PR.

The round-8 reviewer posted R1 saying the broader diff (d50a6a98..HEAD) includes files outside these two — that is correct, those belong to earlier rounds and have already been reviewed; this round-9 brief explicitly scopes around them.

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

and exits 0. The round-7 + round-8 follow-up commits must:

1. Call the production `L.give_cities(0, 1, [moved])(b)` — NOT `L._give_cities_put(...)` directly.
2. Monkey-patch `L._give_cities_put` with a wrapper that injects a rogue byte at the receiver's `stage._nation(b, n) + 0x2e4`, ONLY when `n == 1 AND snapshot is not None`.
3. After `give_cities` raises `SystemExit`, assert the caught message contains `"to1"` (the receiver's tag) and not `"frm0"` (the sender's tag), and that the `receiver_injected` reach flag is `True`.
4. Run a regression-detection control that:
   a. Captures `b2_off2_before = b2[off2]` BEFORE the call.
   b. Resets `receiver_injected = False`.
   c. Calls `patching_put(b2, 1, [], 0, snapshot=None, allowed=set())`.
   d. Asserts no `SystemExit` fires.
   e. Asserts `b2[off2] == b2_off2_before`.
   f. Asserts `receiver_injected is False`.
5. Restore the original `L._give_cities_put` in `finally`.

## Blocking means (any one is enough; a blocking finding means rework, never approve)

1. The wrapper still injects without the `n == 1 and snapshot is not None` gate.
2. The injection offset is wrong (inside the city-list region, count word, or allowed whitelist).
3. The `receiver_injected` reach flag is missing, or its post-raise assertion is missing, or `before_injected = receiver_injected` (a trivially-true capture) is reintroduced in place of a reset-and-assert.
4. The caught `SystemExit` is asserted without a receiver-specific message check (`"to1"` present, `"frm0"` absent).
5. The regression-detection control is missing one of: `b2[off2] == b2_off2_before` AND `receiver_injected is False` AFTER the call.
6. The `b2_off2_before` capture is missing (control reduced to a single assertion).
7. The wrapper is not restored in `finally`.
8. Any of the other three existing tests (`test_consistent_333_to_334`, `test_receiver_assertion_active`, `test_oversized_receiver_list_raises`) no longer prints its `all checks passed` line, or has been silently gutted.
9. The round-7/8 changes introduce a NEW tracked file other than `tests/test_give_cities.py` (the running-notes.md progress line at the worktree root is an existing file already committed in `c8f72cb`; amending it is permitted, but no new tracked file is).

A bypass you proved is blocking.

Not blocking: the broader PR's existing files (covered by earlier rounds), wording, the running-notes edit's formatting, and any change to code these round-9 commits did not touch.

## Report every blocking finding in this one review

This review is your only pass before the author fixes. Do not stop at the first blocking finding: finish reading the focused diff (`git log -p c8f72cb..HEAD -- tests/test_give_cities.py running-notes.md`) and the task file, check every Done-when line and every item under "Blocking means", and report all blocking findings together.

- Before you write the verdict, make one last pass over the focused diff for anything you have not yet rated, and say **"Final pass done"** as the **last line on its own** before the verdict block — followed by **a blank line**, then the verdict block (the parser rejects concatenated "Final pass done" + verdict).
- Number the findings R1, R2, … in order of severity. A finding you held back because an earlier one was already blocking is a review defect: if two problems share a cause, list both and say so.
- Do not rely on a later round. The author fixes everything you list, and the next review checks those fixes and new code only, not anything you saw but did not report.
- If you ran out of time or context before covering the focused diff, say which files or sections you did not cover. Do not approve in that case.
