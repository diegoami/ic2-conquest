# Seed2 residual: preserve the captured destination enemy, but never shoot it dead

**Status:** [confirmed, partial], 2026-10-23. Fresh original Wine semantic trace,
conditional native replay and strict full318 corpus controls. A tested source
candidate, not a merged remake fix or native Windows acceptance.
**Tasks:** [remake #1377](https://github.com/diegoami/imperial_conquest_2/issues/1377),
[conquest #157](https://github.com/diegoami/ic2-conquest/issues/157), related #1324.
This follows the accepted-scope T206 ordering correction; it does not impose a
new hold on that separately approved bounded fix or start Improved policy tuning.

## Answer

The later seed2 mismatch is a movement-control defect. The original captures
the enemy at the requested destination once for a Walk. The remake looks it up
again after each shot. If shooting routs that enemy, the remake sees an empty
destination and can take a step the original does not take.

A capture-only correction is incomplete: the original also tests that its
captured enemy is still alive before shooting. Keeping the index without that
guard introduces shots at an already removed unit, extra Random(1) calls and
incorrect rout/morale effects. Restoring both controls matches all318 hooked
series' strict recorded-state/post checks and ordered draw streams.

| Compiled engine control | State/post matches | Ordered-draw matches |
|---|---:|---:|
| T206 faithful-order baseline | 317/318 | 317/318 |
| Capture destination once, without live-shot guard | 316/318 | 316/318 |
| Capture once plus original live-shot guard | **318/318** | **318/318** |

These use the unmodified upstream `GoldenReplay` and `DrawComparison` helpers,
not the KnownFailures registry. No expected-failure exemption, fixture change,
range substitution or comparison tolerance is used. Fixture pairing is checked
before every trial, and errors fail the result. State/post comparison means the
fields checked by those upstream helpers, not every hidden original runtime field.
The five fixed series also pass strict replay, including `gate2_s2a` explicitly;
the baseline passes4/5 and fails that exact gate alias. All27 unmodified upstream
movement/exhausted-movement tests pass on the complete candidate, with no skips.

## Three reported comparisons, one original trajectory

The #1377 comparisons are hooked `mix-rg_s2_r5_hook` state and draws, and fixed
`gate2_s2a` state. Their **18 boundary saves and post save are pairwise
byte-identical**, verified from pinned fixture6319802 and their retrieved bytes.
They share the same strategic start, seed2 and armies. These names are two
fixture aliases, not independent battle reproductions.

Start: `FLD-RG_0743_rome_army0_at_86_28.SAV`, strategic turn **0743**, Rome army0
against Gaul army10. A fresh semantic observer run `seed2-residual-v1` matches
all **325 original draw tuples and 18 entire boundary SAV files**. The reader
has no overflow/reentry, has complete sequence/RNG checks and balanced routine
boundaries. Its observation code is byte-identical to the validated seed1
observer; only two fixed-seed immediates change from1 to2.

The fresh `seed2-residual-v1-AFTER.SAV` and fresh-process
`seed2-residual-v1-REOPEN.SAV` are byte-identical to each other. New outputs and
all earlier measurements are preserved. No EXE/DAT, owner input or full private
corpus is published.

## First causal difference

All **49** original Walk calls were separately replayed through the T206 native
`TacticalMovement.MoveUnit`, using each actual original's slots, grid, claims,
controller flags, requested destination and RNG state. Exactly one differs:
counter10, Gaul slot24, original sequences **874–891**, goal **(10,3)**.

1. Slot24 starts at(12,4), troops5596, moves4 and shots4. The goal contains Rome
   slot1, a heavy-infantry unit with621troops.
2. It steps to(11,3), spending one move. Both engines agree.
3. It shoots slot1 with bound252 and losses323, then bound150 and losses190.
   The target goes621→298→108 and routs below its floor. Both engines agree on
   those draws, losses, morale and removal. Slot24 now has moves1 and shots2.
4. The original keeps captured slot1. Its adjacent/last-move branch assigns
   target1 even though that unit has just routed, and stops at(11,3), moves1.
5. The native lookup sees the cleared cell, discards that reference and steps
   into(10,3), moves0 and target−1. That is the first differing movement action.

The conditional replay still has **the same RNG state** at this point: the
extra step itself draws nothing. The changed position alters a later shooting
opportunity. The first differing global draw is217/counter11: original melee
site0x439557 draws Random(361)=333; native instead draws Random(113)=104 for a
shot. Those are different actions, not evidence that equal-input melee arithmetic
uses a different formula. Do not force the old bound into the new shot.

The guarded correction matches **49/49 Walk endpoints/RNG states** and the full
**178-action interleaving**:67 movements,62 shots,38 melee exchanges and11 removals.
It reproduces original Gaul23,431survivors/counter18; the baseline had Gaul23,667
at counter16. Both sides' observed terminal slots/grid/counter/RNG are compared.
The original post-rout snapshot at sequence890 also matches an actual native
observer snapshot on all40 slots/names, grid, claim counts, counter/side and RNG
before the different next action; see `causal-proof-v1.json`. GUI Selected and
unobserved machine fields are not asserted equal.

## Why the earlier capture-only control conflicted

The incomplete control fixes the mixed seed2 case but introduces two exact
residuals:

- `lc-ar-three-half_s1_r5_hook`: BATTLE09 slot0 morale75 versus original70;
  draw29 takes Random(1) where the original proceeds to promotion Random(4).
- `lc-ar-three_s2_r5_hook`: BATTLE11 slot0 morale80 versus original65;
  draw108 takes Random(1) instead of the original shooting Random(366).

The dead cached unit is being shot and routed again. The positive-troop test in
the original Walk at **0x438ED1**, before its shot call at0x438EE2, supplies the
missing guard. This explains the historical "capture helps mix-rg but breaks
two cavalry cases" lead without changing morale, quality or damage coefficients.

Five small native regressions give baseline3/5, capture-only4/5 and complete5/5:
last-move retention, no shooting a dead captured target, normal live-target
engagement, unchanged human movement, and defender symmetry. These are native
regressions against the original control-flow contract, not additional fresh
original synthetic-game executions.

The complete source candidate also retains the prior **14 recorded controls**:
2,331 combat draw tuples,253 available boundaries, reference185 and owner346
combined actions, plus the explicitly assumed historical48,969/counter21 control.
Owner inputs, hashes and full replays stay private.

## Reproduction and limits

Evidence: `runs/experiments/data/run-exp-battle-residual157/`, especially
`original-gate-v1.json`, `fixture-recovery-v1.json`, `walk-before-v1.json`,
`walk-cached-live-v1.json`, the three `corpus-*-v1.json` files,
`movement-regression-*-v1.json`, `seed2-cached-live-action-comparison-v1.json`
and `control-replay-v1/verification-v1.json`.
Original raw logs are retained under
`runs/experiments/data/run-exp-battle-parity157/seed2-residual-v1/`.
The source candidate is `movement-cached-live.patch`; `movement-cached-only.patch`
is a deliberately incomplete experimental control and must not be deployed.

Native source is pinned to the T206 correction candidate plus one movement-file
overlay. The original's two-control behavior is source-backed and observed in
the fresh Wine trace; corpus helpers execute the real compiled engine. Build
outputs and fixtures are outside Git; all raw text results are retained.
This session never modifies another repository's source.

Research intake, normal remake PR/CI, the wider golden-master/Godot/solution
checks and native Windows acceptance remain separate. All318 hooked series
matching does not establish every crafted-grid behavior or all game fidelity.
#1377/#1355 are not closed by this candidate, and no fixture or known-failure
registry is changed here. The owner's approved T206 scope split remains intact.
