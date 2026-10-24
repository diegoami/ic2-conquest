# Computer general: later-pass iteration changes the owner battle's winner

**Status:** [confirmed, partial], 2026-10-23. Fresh original Wine execution,
CPU/live recorder validation and diagnostic native controls. This describes the
original packet; production status has advanced as recorded below.
Promoted 2026-10-23 in research PR #67 at
[`63b463cd`](https://github.com/diegoami/imperial-conquest-2-research/blob/63b463cd51822690c5ad8d2aa4f77e0f0175d469/docs/reports/2026-10-23-battle-general-later-pass-iteration1355.md).
Research independently reran the retained offline tools/binaries and validated
the recorded controls; no independent rebuild or new original/Wine run was
performed. The canonical report clarifies measured state versus hidden fields,
three pilot Selected defaults and the historical assumptions. Source evidence
is retained unchanged.

**Production update, 2026-10-25:** the ordering fix merged in Main PR1371,
followed by captured-target/live-guard PR1387. The four ordering files in audited
Main `b593c6e2` match the validated candidate bytes exactly. Fresh current-Main
replay passes 318 strict state/draw series, 14 recorded entry controls including
the owner case, and 2,420 tactical tests. See
[the current-Main audit](2026-10-25-current-main-battle-replay157.md), promoted by
Research PR76 at `b90f6910493dbf3da5a333e45004e0b2e059270e`.
#1355/native acceptance remains separate. The pre-fix
behavior described below is historical, not a claim against current Main.
**Task:** [conquest #157](https://github.com/diegoami/ic2-conquest/issues/157),
following [the owner #1355 reproduction](2026-10-23-ptolemaic-seleucid-computer-general-gap1355.md).

## Answer

The original's later Computer general passes iterate in **slot order**. The
remake runs those passes in **type order, then slot order**, reusing pass one's
ordering. On the owner's mixed, interleaved army this changes movement, draw
consumption and the eventual winner.

This is a **new fixed-seed 1 control** from the owner's preserved after-End save,
not a rerun of the previous natural-RNG 48,969/20,946 survivor measurements.
The new original has the same 73,564 attacking and 78,857 defending troops but
newly generated tactical morale/placement under the declared lab seed.

| Controller | Attacker survivors | Defender survivors | Terminal counter |
|---|---:|---:|---:|
| Original, observer off or on | 0 | **51,178** | **15** |
| Production remake, actual original entry and RNG | **38,088** | 0 | 23 |
| Native diagnostic: slot order in pass three only | 0 | 52,068 | 14 |
| Native diagnostic: slot order in both later passes | 0 | **51,178** | **15** |

The last row also matches **all 498 combat draw bounds/results**, all 40 terminal
slots including names, all 168 grid cells, terminal RNG, and all 14 available
after-placement/movement boundaries at counters 2–15. These are unchanged native
unit/combat routines called with different loop ordering in a task-owned harness;
the remake repository and production assemblies were not modified.

Saves: `owner-seed1-prefix-v1-AFTER.SAV` and
`owner-seed1-prefix-v1-REOPEN.SAV`, strategic turn **0756**; original plain
control `owner-seed1-plain-v1-AFTER.SAV` and its fresh reopen. Every `BATTLE01.SAV`
through `BATTLE15.SAV` is retained in each private runtime. Owner input bytes,
hashes, screenshots and full traces remain private, outside Git/Drive/releases.
The public scalar audit is
`runs/experiments/data/run-exp-battle-parity157/owner-iteration-audit-v3.json`
(earlier v1/v2 retained).

The earlier historical entry was also replayed as an explicitly labelled
assumption control: production gives the same **22,090 / counter 29** as before;
pass-three-only gives **40,130 / counter 23**; both later passes give
**48,969 / counter 21**, matching the original historical result. That replay
retains the earlier assumed clear claims/flags and selected=-1. It does not
invent observations of those missing historical fields or claim exact equality
of the historical event stream.

## First observed decision divergence on shared input

The existing tactical25 observer was rebuilt byte-identically and applied to
this new run. It captures actual slots, grid, actor-target claims, flags, stack,
helper/pass entries and Walk requests, rather than approximating them by polling.

All **60 individual pass-one engagements** through counter 6 agree on chosen
target, requested Walk goal and post-engage slots/grid/claim counts when each
native routine receives the original's contemporaneous input.

At counter **3**, pass three:

| Original sequence | Original next actor | Native next actor | Shared input? |
|---:|---:|---:|---|
| 74 | 0 | 0 | yes |
| 76 | 1 | 1 | yes |
| **78** | **2** | **10** | **yes** |

The inputs at sequence 78 still have identical 40 slots, grid and claim counts.
The native general chooses which unit acts next differently before its next
unit routine executes. This establishes an iteration discrepancy; it is not
an attribution from different final survivor totals alone.

Changing pass three alone restores the entire first movement phase, including
its RNG state. That variant matches measured boundaries through counter 6,
then differs at counter 7. Changing both later passes restores every measured
remaining boundary and the complete terminal tactical result in this control.

Static original checks agree: `FUN_0043A544` starts at own-first and advances
through its twenty slots; `FUN_0043ABB4` does the same for threat and flank.
The native `GeneralPassTwo.Apply` and `GeneralPassThree.Apply` instead call
`GeneralOrders.InOrder`, whose order is type then slot. Earlier tactical25 work
listed iteration as a source-backed lead; this control establishes its causal
effect on a new owner-derived case.

## Recorder and control validity

Reference input `FLD-RG_0743_rome_army0_at_86_28.SAV`, turn **0743**, seed 1,
fixture revision `6319802a75067e7730e4f6a27dce3b4e296ddd9b`:

- Fresh observer matches **325 complete reference draw tuples and 15 whole SAVs**.
- Computer-general-only and computer-general-plus-initial-End controls agree on
  all 320 combat draws and all 15 whole SAVs in that reference case.
- The first collector stopped before result acknowledgement and missed five
  post-battle draws. Its two strict failures are retained. The corrected collector
  preserves the pre-result log and adds a post-writeback log; its full check passes.
- In the owner case, observer-on/off also gives 15 byte-identical whole boundary
  saves and identical terminal slots/grid/counter/RNG. Both save and fresh reopen
  succeed byte-identically. Nation controllers were checked: human attacker,
  computer defender; placement claims are actually clear and general flags off.
- Fresh CPU checks cover existing recorder registers/flags/stack/seed, reentry,
  overflow and active snapshot payloads. They are separate from live inertness.

Production routines come from the previously pinned effective engine
`ae614899d63ac721ee46d1e3213191fe1f43a676`; live main
`8e5f0a35c9dd45a8ec31b38154406843b131013a` adds the #1356 presentation change,
with no production tactical-source difference in the inspected comparison.
The reused engine build/source receipts are in the broad #153 evidence.

Public reference binaries are archived in `reference-batch01.tar.gz`, Drive
`IC2/artifacts/run-exp-battle-parity157/`; its manifest and SHA-256 are tracked.
No EXE/DAT, prefix, registry or owner input is included.

## Full movement and exchange logs

A separately expanded observer now captures movement-step entry/exit, Walk
exit, shot/melee-pass/rout exits, removal, placement and setup boundaries through
the whole battle. It preserves original register/flag/stack/seed semantics in
the CPU checks, passes the complete reference325-draw/15-SAV live gate, and
matches all15 owner plain-control boundary files and terminal state/RNG.

The original owner trace has **2,310 semantic records**, with balanced routine
boundaries and no gaps/overflow/reentry. Independent decoding and native
comparison give:

| Action family | Original count | Both-later-pass slot-order control |
|---|---:|---|
| Actual movement steps | 162 | every actor, step, coordinate and moves-left matches |
| Shots | 108 | every bound, loss, target troops and morale value matches |
| Melee exchanges | 57 | every actor/target, focus, power, bound, loss, troops and morale value matches |
| Removals | 19 | every removed slot and its order matches |
| Combined action stream | **346** | all tuples and interleaving match |

Melee actor/focus/powers are decoded from the original's observed stack locals;
they are not supplied by the port. Shot/melee completion is observed before
the first rout call, so cascade removals cannot be mistaken for direct losses.
The complete498 combat draw sequence also matches. In the public reference,
all185 combined actions (63moves/78shots/34melee/10removals) match this control;
the production general differs later in that reference battle too.

Private readable original log: `original-battle-log-v1.txt` in the owner
semantic run; native production and both diagnostic variants have separate
event JSONL files. Public reference logs and
`reference-semantic-comparison-v2.json` are tracked. A positive parser control
passes and five corruption controls reject sequence gaps, missing snapshots,
incorrect draw results, unknown markers and unbalanced routine boundaries.

## Declared synthetic pilot

All **12** declared synthetic strategic inputs complete original attack,
SaveAs/fresh reopen and matched-entry native replay. Each production/control
variant matches its original's full measured tactical state/result/RNG,
combat draws and available boundaries: **1,528 combat draws and 225 boundaries**
across the original cases. Nation pairs are Rome–Gaul, Ptolemaic–Seleucid and
Carthage–Numidia. Cases cover single melee/ranged/cavalry units, small mixed
formations, one slot permutation, quality4/9 and army morale50/90.

These small fixtures do **not** trigger the iteration defect. This is useful
negative coverage, not evidence that mixed battles in general agree. Original
copy-in generates each measured tactical entry; native replay starts there.
The pilot therefore tests subsequent battle behavior, not independent strategic
copy-in or JSON/export conversion equivalence. Actual tactical morale, quality
and original RNG are held equal for each engine comparison. See
`pilot-manifest-v1.json` and `pilot-audit-v2.json`.

## Limits and next tests

### Compiled source correction follow-up

The owner subsequently chose faithful behavior first, with a separately
selectable improved general investigated afterward. Remake #1355 remains the
fidelity task; [#1362](https://github.com/diegoami/imperial_conquest_2/issues/1362)
tracks the optional-controller investigation and waits on that baseline.

A four-file source correction is now prepared in
`runs/experiments/data/run-exp-faithful-general157/faithful-general-portable.patch`.
It preserves pass one's type order and uses lazy live-slot order in pass two
and all pass-three entrypoints. Original/patched source hashes are pinned to
main8e5f0a3. The patch passes read-only application checks and was compiled as
the actual engine through source overlays; no other checkout was modified.

Six focused regressions pass after the patch; the unchanged engine fails the
actual threat/shooting-order cases and lacks the new iterator. The real patched
`ComputerGeneral`, without a diagnostic replacement controller, reproduces all
14 recorded controls: **2,331 combat draw tuples, 253 available boundaries**,
terminal tactical state/RNG, reference185 and owner346 combined actions.
The historical assumption control also recovers48,969/counter21.
See that folder's `verification-v1.json` and README for receipts, preserved
preparation failures, scope and downstream acceptance still required.

This is a tested source-correction candidate, not a merged/deployed remake fix.
Full318-corpus, native Windows, independent copy-in and strategic writeback
acceptance remain open. The proposed optional general is not implemented.

This supports an **AI fidelity/order defect**. It does not measure whether the
original AI is generally stronger. No morale/training/exchange-formula change
is needed to recover this control, but independent kernels and parameter
sweeps are still needed to establish their broader fidelity.

The old prefix observer stops after counter6; the new semantic capture continues
through the full battle and actually samples selected=-1. Individual placement
write order and silent target writes are not asserted. Native strategic
writeback remains separate from tactical equality.
The v3 diagnostic's middle pass-two interval included subsequent flank effects;
those retained rows are not isolated pass-two evidence. Later versions omit it.

Further seeds, the full25-melee/15-ranged kernel matrix, full318-series corpus
and native Windows remain separate work. Historical survivor/counter recovery
above retains its explicit assumptions and is weaker than a fresh exact trace.
Upstream #1355 and conquest #157 stay open. Correction proposals belong in the
remake workflow with a minimal regression and broader corpus verification.
