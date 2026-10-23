# Save-conversion experiment (#151)

Finding: [six native scenarios and seven original Wine sessions](../../../../findings/2026-10-23-remake-original-save-conversion-roundtrips.md).

Authoritative final scalar records: `comparison-v6.json`, `validation-v2.json`,
all `live-*.json` final receipts, the export/import/return command receipts and
`batch2-complete-manifest.json`. Earlier comparisons, failed setup/checker calls
and `validation-attempt-v1.json` are retained as evidence, not selected results.

Private binary/native JSON artifacts are in
[Drive IC2/artifacts/run-exp-sav-conversion-roundtrip](https://drive.google.com/drive/folders/1OQWVtWzeN6k-_EgfU_3U_vFa4MjmXfqv),
`batch2-complete.tar.gz` (85 files). Its archive and every member hash are pinned
in the tracked manifest; `batch2-complete-SAVES.sha256` lists member hashes.
The original EXE/DAT and copied Wine prefix are excluded.

The scripts use `/home/diego/projects/imperial_conquest_2` read-only and redirect
build products under conquest `artifacts/run-exp-sav-conversion-roundtrip/`.
`ConversionProbe.csproj` references the built engine/data assemblies. Build the
actual CLI with `dotnet build <remake>/src/IC2.Cli/IC2.Cli.csproj --artifacts-path
<conquest>/artifacts/run-exp-sav-conversion-roundtrip/build`. The redirected CLI
also needs read-only `IC2.sln` and `data` links at that artifact root because it
finds data by walking up from its assembly. Build the adapter with its own
`--artifacts-path`; v1/v2 binaries are separately hashed by the final validator.

Procedure used:

1. `setup_runtime.py`: copy prefix without its game directory, copy only game
   binaries/data/help/audio and driver caches; no source saves copied.
2. `offline.py generate`: public GameSession commands produce initial, orders,
   turns6/12/24 and improved-ruleset control; private JSON stays outside Git.
3. `offline.py export v2`, then `offline.py policy`: actual CLI conversion,
   original-SAV importer and independent conquest checker.
4. `live.py native-initial A`; `live_batch.py`: six unmodified-original tests
   across the first and extended batches. `live_batch.py extended` adds cargo
   and an instrumented-original one-turn test. One private display/prefix,
   serial execution, fresh-process reopen, no replacement destinations.
5. `supplement.py cargo`: explicitly synthetic public-native-model cargo case
   and overwrite control. `supplement.py return`: completed original outputs
   import/reload/resume, accept tax27, re-export and pass policy checks.
6. `compare.py comparison-v6.json`: full native-state paths, all conquest
   parser fields and original byte comparisons. `validate.py <new-receipt>`:
   read-only audit of preserved outputs and hashes, no new game run.

Do not blindly rerun these commands: original names, saves and receipts must
remain immutable. A new batch needs new directories/names/versions. Never
delete a save to regenerate it. Measurements stay tracked; binaries stay on
Drive or the run release. A future live run requires applicable owner approval.

No release token was available. Optional owner publication of the already
created archives (not necessary to retrieve the Drive evidence):

```bash
gh release create run-exp-sav-conversion-roundtrip artifacts/run-exp-sav-conversion-roundtrip/batch1-conversions.tar.gz artifacts/run-exp-sav-conversion-roundtrip/batch2-complete.tar.gz --title 'Save conversion round trips (#151)' --notes 'Evidence and SHA256 manifests: findings/2026-10-23-remake-original-save-conversion-roundtrips.md'
```
