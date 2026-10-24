# Paste-ready handoff: T206 follow-up #1377

The owner approved merging the bounded T206 ordering correction separately
once its CI is green. Do not restore its earlier hold because of this follow-up.
Keep Improved policy/Settings work separate. #1377 owns the three remaining
comparisons; #1355 keeps wider fidelity/Windows acceptance.

Conquest has completed attribution and a source candidate. New finding:
`findings/2026-10-23-seed2-walk-captured-target1377.md`, with evidence and the
one-file `movement-cached-live.patch` under
`runs/experiments/data/run-exp-battle-residual157/`.
Research intake is complete: [PR #68](https://github.com/diegoami/imperial-conquest-2-research/pull/68)
merged at `d19c20c9f58a0ce2ca77de878ef8e01c9f84ca19`.
Use the [canonical report](https://github.com/diegoami/imperial-conquest-2-research/blob/d19c20c9f58a0ce2ca77de878ef8e01c9f84ca19/docs/reports/2026-10-23-seed2-walk-captured-target1377.md).
Research independently reproduced the retained controls; no new original/Wine
run or production edit was part of that intake.

The two named seed2 series have identical18boundary/post saves and comparator
inputs. This does not establish a single physical recording process.
Fresh original observer matches325draw tuples and18wholeSAVs. Of49conditional
Walk calls, only HR10/slot24/seq874..891 differs. The original captures its
destination enemy once, shoots/routs it, retains the captured index and stops
with1move. Native re-looks up an emptycell and advances. Original0x438ED1 also
requires a positive troop count before shooting; a cache-only port omits that
guard and shoots/routs dead targets again, introducing Random(1)/morale errors.

Complete candidate changes only TacticalMovement: capture once per Walk and
guard shots with IsLive(capturedEnemy), preserving the original adjacent/last-
move branch before that guard. No formula, quality/morale coefficient, new
setting, fixture, tolerance or KnownFailures change. `movement-cached-only.patch`
is deliberately incomplete; do not apply it as the correction.

Strict unmodified GoldenReplay/DrawComparison, with no registry exemptions:
baseline317state/317draw of318, cache-only316/316, complete318/318. Five fixed
series pass (baseline4/5), all49Walks and178combined actions match. The existing
14controls,2331draws/253boundaries and historical assumption control remain
exact. Minimal movement regressions3/5→4/5→5/5;27upstream movement/exhaustion
tests pass with no skips. Full source/hash/apply and original/native common-
state proof is in the packet. Owner files and the full fixture archive stay private.

Please route the one-file correction and meaningful regressions through #1377's
normal task/PR workflow. Independently rerun the current full golden-master,
solution, Godot and CI checks; remove only the three #1377 registry entries once
their strict tests pass. Do not blanket-update any message or the separate
crafted-grid cases. Conquest did not edit this repository or run native Windows.
