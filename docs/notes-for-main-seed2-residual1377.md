# Main handoff: #1377 is merged; preserve its acceptance evidence

Main PR1387 merged at `3c1860079db6dd9b1fb11ceb8b726c7fd95293ac`.
#1377 is closed/status:merged. The complete capture-once plus live-shot-guard
correction is present in current audited Main b593c6e2; no duplicate patch or
registry edit is needed. KnownFailures.json is empty at that pin.

Canonical rule report: Research PR68 at
`d19c20c9f58a0ce2ca77de878ef8e01c9f84ca19`,
`docs/reports/2026-10-23-seed2-walk-captured-target1377.md`.
The original source packet remains in
`runs/experiments/data/run-exp-battle-residual157/`; cached-only.patch is a
historical incomplete control, not the correction to apply.

Fresh current-Main audit is
`findings/2026-10-25-current-main-battle-replay157.md`, promoted by Research PR76
at `b90f6910493dbf3da5a333e45004e0b2e059270e`:
use the [canonical current audit](https://github.com/diegoami/imperial-conquest-2-research/blob/b90f6910493dbf3da5a333e45004e0b2e059270e/docs/reports/2026-10-25-current-main-battle-replay157.md).
It compiles actual current engine/test helpers and passes all318strict state
and ordered-draw comparisons,5fixed series,14recorded-entry controls and2420
ordinary tactical tests/0failure/0skip. No fixture, tolerance, registry exemption
or replacement controller. All5862retained corpus files equal the pinned archive.

These current results supersede the old packet's production-pending status;
they do not change its historical317/316/318 controls or imply a newly recorded
Original battle. Full owner/fixture traces and private hashes stay private.
#1355's installed-build/natural-entry/native-Windows acceptance remains separate,
as does optional Improved policy work. No paused battle queue is resumed.
