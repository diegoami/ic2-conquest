# T206 follow-up #1377: captured-target lifetime and live-shot guard

Current status (2026-10-25): Main PR1371 and PR1387 are merged; #1377 is closed.
Fresh b593c6e2 source/corpus audit is in
`findings/2026-10-25-current-main-battle-replay157.md` (separate intake pending).
The historical candidate/control data below is unchanged; do not apply a duplicate
patch or treat it as proof of #1355/installed-Windows acceptance.

Finding: `findings/2026-10-23-seed2-walk-captured-target1377.md`.
Promoted Research report: `docs/reports/2026-10-23-seed2-walk-captured-target1377.md`
at `diegoami/imperial-conquest-2-research@d19c20c9f58a0ce2ca77de878ef8e01c9f84ca19`
(merged PR68). Research independently reproduced retained controls, not a new
original/Wine run, production correction or broad CI/Windows acceptance.
Runners: `runs/experiments/battle-residual157/`.

Use only `movement-cached-live.patch` as the complete candidate.
`movement-cached-only.patch` deliberately omits the original's live guard and
causes the two retained cavalry failures. Both are immutable measured controls.
No patch was applied to the remake checkout or KnownFailures registry.

The strict corpus runner references the unmodified upstream test assembly's
GoldenReplay/DrawComparison and calls them directly, without registry exemptions.
Its task-local IC2.sln marker/read-only data symlink supplies asset discovery;
IC2_FIXTURES_DIR points to the privately recovered pinned6319802 inputs and DAT.
The baseline and incomplete control reuse identical compiled helper assemblies
and change only the engine/data dependencies before their first execution.
No helper, golden value, tolerance or original fixture is modified.

Authoritative controls: baseline317state/317draw, incomplete316/316,
complete318/318. Each denominator is318hooked series. Inspect full per-trial
rows, fixture pairing and exit receipts; do not infer a strict pass from a test
registry that knowingly accepts failures. The separate observed original
recorder gate is325draw tuples and18whole SAVs, not the318native series count.
The additional fixed-series mode passes5/5 on the complete candidate versus4/5
on baseline, explicitly recovering the gate alias. The27 unchanged upstream
movement/exhaustion tests also pass with no skips.

The two named seed2 series are byte-identical aliases in all18boundaries and
post save. Native source/control checks retain actual original controller
inputs and distinguish a frozen single-Walk replay from a full autonomous battle.
Complete source also preserves14prior controls and the historical assumption
control; owner full states/hashes/replays remain private.

The raw private fixture tarball, full-fixtures-v1 and original DAT/EXEs must
never enter Git or a public archive. Never run a generic archive walker here.
The public original-run bundle is explicitly selected by the prior
`archive_public.py --labels seed2-residual-v1`; it excludes those private trees
and every EXE/DAT. All saves/measurements use exclusive names, are retained,
and must not be deleted or overwritten on rerun. Commit/push every batch/30min.

Broader main CI/Godot/solution and Windows checks are downstream acceptance.
T206 can follow its owner's separately approved merge scope; this follow-up
must not reinstate its earlier merge hold. Improved163 tuning remains separate.

Public originals: `seed2-semantic-batch01.tar.gz`,562897bytes,
SHA256 `a589e6875625aeb620d1a2572bb9da81f8fb98a1cd6c7a01a2118e21d1d94325`.
Retained compiled full-corpus/replay/regression tools: `cached-live-tools-batch02.tar.gz`,
4371549bytes,SHA256 `a02049656087296f8d1ef9885a626fe26eabc32c3a7c8845959193aebdde5ad0`.
Drive folder: IC2/artifacts/run-exp-battle-residual157,
`1_NkvDEBYL1IO_2uPGPp5TffTuRHM7oxs`. Upload metadata size/parent and local
archive members/digests verified; no remote-download digest claim. No owner
inputs/traces, original EXE/DAT or full private corpus is uploaded.

For retained full-corpus replay here, set IC2_FIXTURES_DIR to the private
`artifacts/run-exp-battle-residual157/full-fixtures-v1`, then run the built
`corpus-cached-live-v1/build/bin/Corpus/debug/Corpus.dll` with two NEW output
paths (JSONL and summary JSON). Fixed-mode verification uses the later
`corpus-fixed-cached-live-v1/build/bin/Corpus/debug/Corpus.dll` and adds
`--fixed-only`. Neither program uses the KnownFailures registry. Binaries need
the .NET runtime plus the supplied assembly dependencies. Relocated binaries
also need a parent IC2.sln asset-locator marker and `data` pointing read-only to
the pinned remake data; those are input-path adapters, not another checkout.
For the checksum inventory's logical layout, extract the original bundle under
`original/`, and tool bundles at the root beside their archives.

Supplemental fixed-mode compiled tools: fixed-corpus-tools-batch03.tar.gz,3186327bytes,SHA256ba996c8328fecb9636f935278d71abee8f1c028c0f0454ddca03dbc2520bae3d, Drivefile12L6PukG6Xusn9FMu-JdOFnzMahCnB1pA in the same folder. The five-case mode is supported in this later reporter; batch02 retains the original strict318 reporter. Fixture aliasing denotes equal comparator inputs/states, not an assertion about whether legacy recordings used one or separate processes; see fixture-provenance-clarification-v1.json.
