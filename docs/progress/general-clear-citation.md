# Computer General source citation correction — 2026-10-16

## Plan and authorization

The owner authorized this session for the original-AI queue, with MiniMax as
reviewer. Research intake identified an incorrect symbol in the merged draft:
the second Information-window general-clear handler is FUN_0043abb4, not
FUN_0043a544. Preserve all measured outputs and the original line references.

## Progress

- Verified the pinned dump SHA through `harness.decompile.check()` and the
  nearest enclosing function headers for 39835-39838 and 40254-40257.
- Corrected the symbol only; behavior, line ranges, saves and observations stay
  as recorded. Added an exclusively created, line-numbered source extract of
  FUN_0043abb4 so the corrected citation is locally reviewable. Existing source
  extracts and measurements are retained unchanged.
- No game run or remake edit. Same owner-selected MiniMax M3 reviewer.

## END

Citation correction prepared; review, merge and research relay are recorded on
the resulting PR. Research issue #25's prerequisite gate is unchanged.
