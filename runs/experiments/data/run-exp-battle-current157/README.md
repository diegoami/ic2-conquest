# Current-Main tactical audit #157 — 2026-10-25

Finding: `findings/2026-10-25-current-main-battle-replay157.md` (intake pending).
Main pin b593c6e28939c1c7154f9a41d0436a8f14f352dc. T206/PR1371 and movement
PR1387 are already merged; #1377 closed. No duplicate patch is prepared.

Authoritative summary: summary-v1.json / audit-execution-v1.log. Current engine
and test helpers freshly built from the authoritative archive, without overlay:
318strict state+ordered-draw series,5fixed series,14recorded entries,2420tactical
tests/0failure/0skip, ordering6 and movement5 regressions pass. Expected-failure
registry empty. All5862retained battle files match their pinned archive after
execution; Original DAT pin matches. Recorded owner entry matches terminal and
semantic action comparisons. The historical control retains its assumptions.

GoldenReplay.Passed includes conclusion and available recorded post-field
comparisons; Fresh-mode fixture starts exercise copy-in, Resume starts use a
saved block. Early scalar wording about no strategic copy-in acceptance refers
to the unverified natural owner End-turn-to-battle flow, not fixture copy-in.
Series names can alias one trajectory;318 is not an independent-scenario count.

## Reproduction

Recover a new task-owned archive of Main b593c6e, preserving raw mixed encodings.
Build Corpus.csproj against that archive's Engine.Tests project. The current
project reference targets artifacts/run-exp-battle-current157/source-v1 here.
No old tactical overlay or fixture/registry/tolerance edit. A separate local
harness supplies only a task-owned IC2.sln/data asset-locator adapter.

`run_corpus.py --fixtures PRIVATE_CORPUS --version UNIQUE` runs unchanged
GoldenReplay/DrawComparison directly without KnownFailures.Check. Add
`--fixed-only` with a distinct version for fixed-series replay. Raw rows and
errors stay private; aggregate counts and code-assembly hashes are public.
The pinned private fixture revision is6319802a75067e7730e4f6a27dce3b4e296ddd9b.
Do not publish its raw archive, file list, per-input hashes, DAT or Original EXE.

Compile the retained Replay/Regression/MovementRegression tools against the
fresh current engine/data. verify_controls.py takes explicit private owner and
historical input arguments; do not put those paths in public logs/comments.
The actual original input recordings stay unchanged. Current tactical xunit
run uses the same fixture root and FullyQualifiedName~Battle.Tactical, with
TRX/log private. verify_inputs.py checks raw corpus archive equality and emits
only aggregate fixture/test/registry counts. audit.py --version UNIQUE needs
only the public scalars and writes a fresh summary; no game or owner input.

All saves/measurements, including failed attempts, are immutable/versioned.
Never delete an old save/output to rerun. No new Original/Wine run or SAV was
created in this audit. No native Windows/Computer Use or paused battle queue.
Code and compiled tools are retained locally; no owner/raw-corpus public archive.

The source scan's first attempt assumed UTF8 and failed before writing a ledger.
The Latin1 scan preserves raw bytes; source-audit-v2 is final. The separate build
correctly compiled current Main, with three existing Data warnings. No unchanged
baseline build was mislabelled a candidate. Public audit, compile and diff pass;
self-review only. Installed-build and Main1355 acceptance remain unverified.

Recorded-runtime qualification: three pilot inputs lack the selected-slot field
and retain the existing −1 default disclosed in Research67. The owner control
has its selected slot observed. recorded-runtime-assumptions-v1.json records
these aggregate facts; no missing field was backfilled and no result changed.
