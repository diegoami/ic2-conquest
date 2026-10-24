# #1388: strategic target and routing boundary

Finding: `findings/2026-10-24-seleucid-strategic-target-routing1388.md`.
`audit-v1.json` is the validated public scalar result; source blobs/build identity
are in `source-pin-v1.json`. Scripts live in `runs/experiments/seleucid1388/`.
All owner input/save/state/RAM/full-log hashes and binary evidence stay private
under `artifacts/run-exp-seleucid1388/private/`; no public binary archive is
appropriate. Never run the generic archive walker over this experiment.

Native source was copied using read-only `git archive` from remake commit
`3c1860079db6dd9b1fb11ceb8b726c7fd95293ac`, selecting `Directory.Build.props`,
`src/IC2.Engine` and `src/IC2.Data`. Every archived blob matched its Git identity.
Build Engine, then Probe.csproj with `/home/diego/.dotnet/dotnet`; projects build
inside this checkout. Probe arguments are data-repository root, private native
input JSON and a NEW private output directory.

Original runtime prerequisites match the prior #1355/#157 isolated Wine harness.
`test_observer.py` uses `/home/diego/.local/bin/python3.12` (Capstone/Unicorn).
Run before `original.py LABEL --observer --seed 1`; control omits `--observer`.
Every label must be new. The runner uses private display :788, 2560×1440, copies
the Wine prefix/data and uses the original-input copy without editing it. It
issues one End turn, checks completion, saves and stops. No battle orders.
The RAM observer takes the defender pre-walk snapshot once into scratch memory.
`original_replay.py RAM_PATH NEW_PRIVATE_JSON` runs actual original helpers;
its stdout is scalar only. `audit.py` fails if its output already exists: use a
new version when rerunning, never remove a measurement to regenerate it.

Retained setup slips: engine-build-v1 could not find `dotnet` on PATH; v2 uses
the installed absolute path and passes with three existing Data nullable
warnings. Initial observer layout exceeded the old cave capacity; layout was
enlarged before live use. CPU v1 precedes RAM snapshot support; CPU v2 adds it;
CPU v3 explicitly exercises defender snapshot copying. All 816 controls pass.
Original replay v1 used a wrong Random hook address; its no-RNG assertion is
superseded by final helper v4, which checks 0x40284C and seed preservation.
Replay execution v3 preserved a syntax error, corrected in v4/v5. Full helper
v2 stdout was retained privately because it included detailed coordinate stores.
No measured result/save was overwritten or deleted.

Latest private helper evidence is `original-helpers-v4.json`, native diagnostic
output is `native-v3/`; the first original hook run and plain control are v1,
atomic-snapshot original run is `hook-seed1-v2/`. Those names are local private
aliases, not independent public fixture cases. Failed/superseded outputs remain.
