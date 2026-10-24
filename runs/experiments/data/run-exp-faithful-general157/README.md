# Faithful Computer general correction candidate

Current status (2026-10-25): Main PR1371 and PR1387 are merged; #1377 is closed.
Fresh b593c6e2 source/corpus audit is in
`findings/2026-10-25-current-main-battle-replay157.md` (promoted by Research PR76 at
`b90f6910493dbf3da5a333e45004e0b2e059270e`).
The historical candidate/control data below is unchanged; do not apply a duplicate
patch or treat it as proof of #1355/installed-Windows acceptance.

Owner direction: reproduce the original first; investigate a separately selectable
improved general later. Remake fidelity issue #1355 remains the first task;
optional-controller investigation is #1362, related to planning #1361.

`faithful-general-portable.patch` is the proposed four-file correction against
remake main `8e5f0a35c9dd45a8ec31b38154406843b131013a`. It adds a lazy live-slot
iterator for the later passes, switches pass two and all pass-three entrypoints,
and corrects comments. Pass one retains type order. No combat formula, new
setting, save schema or redesigned controller is included.

`source-pin-v2.json` gives original Git blob/SHA256 and patched SHA256 per file.
Both patches pass `git apply --check` against the read-only source checkout.
The portable patch uses UTF8-safe context; the full-context patch is retained too.
Before applying downstream, verify the source pins or rebase deliberately.

The actual engine was compiled through `overlay-v2.targets`, with outputs here,
without modifying or cloning the remake checkout. The pre-existing quality4
source overlay supplies the two production differences between the local base
and effective main; prior source receipts are in the broad #153 evidence.

Validation:

- `regression-before-v1.json`: unchanged engine retains pass-one ordering but
  fails the later-pass checks. Actual threat and shooting APIs both act in order
  1,0 when the original requires0,1. Three new-iterator checks also fail before.
- `regression-after-v1.json`:6/6 pass, including defender-side bounds, live
  liveness and battle-end checks. No diagnostic replacement general is used.
- `verification-v1.json`:14 actual compiled-engine replays pass (12 declared
  synthetic cases, reference and owner). All2331combat draw tuples,253boundary
  states and complete terminal tactical states/RNG agree with original records.
  Reference185 and owner346 combined semantic action tuples agree exactly.
- Historical assumption control recovers48969survivors/counter21; the missing
  old runtime fields remain explicitly assumed, not fabricated observations.
- No fresh Wine run. Original strategic copy-in, native writeback, full318
  corpus, native Windows and downstream CI/production merge remain separate.

Reference controls cite original turn0743 and `BATTLE01.SAV` onward in the prior
public reference/pilot archives. Owner control turn0756 and its boundary/post/
reopen SAVs remain private. New owner replay outputs are private; only scalar
audits are published. Public source/outputs use exclusive new names, no save or
measurement was deleted/overwritten.

Two initial failures are preserved: a contents-API text-encoding mismatch and
an unchanged baseline build that incorrectly ran after preparation failed.
`initial-failure-classification-v1.json` excludes that build from candidate
evidence. Raw git/blobs bytes verify correctly and preserve mixed encodings;
v2 preparation/build is the candidate. The engine build retains three existing
IC2.Data nullable warnings; the verification tools build without warnings.

Reproduction tools: `runs/experiments/faithful-general157/prepare.py`,
`Regression.cs`, `Replay.cs`, `verify.py`. Outputs/binaries stay versioned under
`artifacts/run-exp-faithful-general157`; public build/hash receipts are here.
For local builds, provide EnginePath/DataPath to the task-owned projects and
redirect all artifacts here. Never write generated projects into the remake.

Candidate binary archive contains shared engine DLLs and replay/regression tools,
not a deployed game. To execute extracted tools, place the shared engine DLLs
beside their respective tool DLLs; their source builds already do that. No original
EXE/DAT, owner input, full owner trace, Wine prefix or credentials are included.

Research intake PR67 is merged at63b463cd51822690c5ad8d2aa4f77e0f0175d469;
its same-named report is canonical. The source candidate is ready for the
remake's normal triage/branch/CI process. Research reran retained tools/binaries,
not an independent rebuild or new original/Wine run. This checkout does not
apply the source correction to the remake repo.
Do not close #1355 merely because this candidate reproduces these controls.
