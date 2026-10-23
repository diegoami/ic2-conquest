# T206 follow-up #1377: captured-target lifetime and live-shot guard

Finding: `findings/2026-10-23-seed2-walk-captured-target1377.md`.
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
