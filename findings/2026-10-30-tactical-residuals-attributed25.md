# All 36 residual series of the 318-series tactical corpus are attributed: four Main commits removed them

**Status:** promoted by research PR #108, with two corrections (marked below); rules spec §8 and pending-requests #25
updated there.
**Tag:** [confirmed]: the unchanged strict corpus replay (state and ordered draws, no KnownFailures) run on Main's own engine
and test helpers at 23 distinct pins (corrected from "21"), on the same private fixtures. No game run, no fixture, bound or tolerance change.
**Task:** research [#25](https://github.com/diegoami/imperial-conquest-2-research/issues/25) (build imperial_conquest_2#1107),
delegated to conquest on 2026-10-30.

## Answer

At the #25 inventory pin `257f2d2` (PR1156) the replay gives exactly the inventory: **282 series exact in state, 283 in
draws, 36 residual**. At current Main (`b593c6e`, the #157 audit) it gives 318/318. Replaying at every Main commit in between
that touches `src/IC2.Engine/Battle` or `src/IC2.Data` assigns **each of the 36 residuals to exactly one commit**. No series
broke at any step.

| Commit | Change | Residuals removed |
|---|---|---|
| `32f3ce7` (2026-10-18; `30e1386`, the first tested pin with the fix and main together, merges main **into** the fix branch: corrected from "merged into main by") | "Fix Pass2 weighted candidate eligibility and strict minimum" | **23** |
| `65cfc1f` (2026-10-18) | "Correct threat movement actor shooting mode and radius" | **11**, including the state-only `ar-hi-three_s3_r5_hook` and `hi-ar-three_s3_r5_hook` |
| `f0cd629`, PR1371 / T206 | later-pass slot order (GeneralOrders, GeneralPassTwo, GeneralPassThree, ComputerGeneral) | **1**: `mix-rg_s1_r5_hook` |
| `3c18600`, PR1387 / #1377 | captured Walk target, positive-troop shot guard (TacticalMovement) | **1**: `mix-rg_s2_r5_hook` |

The other 14 tactical-touching commits change no series' result. Two of them, `305b2b1` and `b2d6b52`, sit on main
before the Pass2 branch was merged, so 36 remain there.

**Lists** (`attribution-v1.txt`):
- `32f3ce7`: ar-hc-three_s1, ar-li-three_s2, hc-ar-three_s1, hc-ar-three_s3, hc-hc-three_s2, hc-hi-three_s3, hi-ar-three_s1,
  hi-lc-three_s1, hi-li-three_s3, lc-hi-three_s1, lc-hi-three_s2, lc-li-three_s2, lc-li-three_s3, li-hc-three_s1,
  li-hc-three_s3, li-hi-half-three_s1, li-hi-half-three_s3, li-hi-one-three_s1, li-hi-one-three_s3, li-hi-three_s2,
  li-lc-three_s1, li-lc-three_s2, li-lc-three_s3;
- `65cfc1f`: ar-hi-three_s2, ar-hi-three_s3, ar-lc-three_s2, ar-li-three_s1, ar-li-three_s3, hi-ar-three_s2, hi-ar-three_s3,
  lc-ar-three_s1, lc-ar-three_s2, li-ar-three_s2, mix-rg_s3;
- PR1371: mix-rg_s1;
- PR1387: mix-rg_s2.

All names carry the suffix `_r5_hook`.

## What this changes for #25

- **"Establish the surviving complete causal paths"** (#25's done-when): at current Main **none survive**. Each former
  residual is exact after one identified source change and stays exact afterwards.
- **`mix-rg_s1`**, #25's pinned starting case (draw 24, HR6, site `0x439557`), is not removed by the threat-actor
  correction (`65cfc1f`), which #25 had suggested evaluating. It stays residual until PR1371's later-pass slot order.
- **`ar-hi-three_s3`**, the state-only residual (218 equal draws, BATTLE19 slot 2 y 3 vs 4), is removed by `65cfc1f`.
- **The original-side traces #25 asked for** (runtime claims, the shot general pass, the 24 stopped-before-shot Pass2 stages)
  are not needed to attribute these 36. Each residual disappears with one source change, and the strict replay then
  matches every recorded state and draw.

## What this does not establish

- *Why* each commit fixes its series instruction by instruction: this is attribution by source change, not a per-series
  causal trace. Attribution is per commit; within PR1371, its four files were not separated.
- Anything beyond this recorded corpus: natural End-turn battle entry, the deployed build, and native Windows remain as
  in `findings/2026-10-25-current-main-battle-replay157.md`.
- The intermediate pins were built only to replay the corpus; their other behaviour was not checked.

## Evidence

Runner `runs/experiments/tactical25-attrib/run_pins.py` (the #157 `Corpus.cs` unchanged, compiled per pin against that pin's
`tests/IC2.Engine.Tests`, sources from `git archive` of the read-only clone). Receipts in
`runs/experiments/data/run-exp-tactical25-attrib/`:
- `pins-v1.json`: 4 pins;
- `pins-v2.json`: 5 pins, adding PR1371's parent `a99d414`;
- `pins-v3.json`: 20 pins, every tactical-touching commit from PR1156 to `a99d414`;
- in all, 23 distinct pins (v3's 20 plus `f0cd629`, `3c18600` and `b593c6e`);
- `attribution-v1.txt`.

Per-series rows and fixture paths stay private (artifacts). Fixtures: the private pinned corpus of the #157 audit (revision
`6319802a`).
