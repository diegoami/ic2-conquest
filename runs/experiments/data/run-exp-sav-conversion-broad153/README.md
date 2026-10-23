# Broad conversion matrix — conquest #153

Owner authorized broader feature coverage and starts from several nations after
the limited #151 test. This packet expands the sample to all16nation starts,
four progressed nation/season checkpoints, targeted strategic feature cases,
explicit converter/input refusals, and a synthetic legacy-format migration.
The final finding and validation select the completed records; intermediate
comparisons/coverage files are dated work-in-progress evidence, not pass claims.

Sources are pinned in `build-source-pin-v1.json`: production code equivalent to
remake `ae614899d63ac721ee46d1e3213191fe1f43a676` (quality4 fix), built against
read-only local base `a510c33` with its two changed production source files
substituted at compile time. Downloaded blobs were verified against their Git
object identities. Source checkout and its untracked files were not changed;
there was no clone or second checkout. Assembly metadata can name the local
base; assembly hashes, source pin and substitution targets define the actual
tested build, not an official-release binary identity.

Use `case-manifest-*.jsonl` and `coverage-*.csv` to distinguish:

- State validation/export and independent Python policy checks.
- Opening in the original, an actual order/refusal, and fresh-process resave.
- Importing that original-written result into the remake, native reload/resume,
  another order and re-export/policy checking.
- Comparing the same deterministic action in each engine versus simply
  observing a random continuation. Original and remake RNG streams differ.
- Gameplay-derived versus synthetic inputs. Several feature cases intentionally
  share identical source SAV bytes but exercise different actions; case count
  is not a count of distinct worlds or byte-distinct saves.

Scripts:

1. `prepare_build.py`, `overlay.targets`: exact upstream production sources,
   redirected CLI build. Task adapters reference those assemblies only.
2. `Program.cs`, `FeatureCases.cs`: public engine/session native generation,
   import, resume and command execution. `negative.py` adds real CLI refusals
   and a synthetic v4-shaped migration; it is not an owner's legacy save.
   `lineage.py` creates explicit native-array reorder/cargo-compaction cases.
3. `offline.py`: each command's full argv/stdout/stderr/exit is immutable.
4. `setup_runtime.py`: private Wine prefix/game directory, no source saves
   copied. `live.py` executes original orders and records byte-stable reopen.
5. `resume_live.py`: only reviewed failures get distinct v2 attempts; all
   successful attempts are skipped. `reviewed-recovery-plan-*` and diagnostics
   retain the reasons. Never retry an unknown failure automatically.
6. `match_predictions.py`: GUI spinner arguments are increments, and the
   original chooses a fleet build port. Retain first predictions, then compare
   a separate native command with the *observed actual* quantity/port. This
   alignment does not repeat an original trial or hide a difference.
7. `compare.py`, `coverage.py`: raw source/import changes, raw original SAV
   comparisons and explicit action/return coverage. Comparisons normalize
   identity by nation/location, but keep unit order and text differences.
   Import-reset score baselines/elapsed-turn/RNG and derived covered cells are
   named separately from game fields. Nothing claims full native-state equality.
8. `bundle.py`: exclusive new archives/manifests of saves, native JSON and PNG;
   no EXE, DAT, prefix or credentials. Earlier batches are never overwritten.

Private binaries/native JSON are on
[Drive IC2/artifacts/run-exp-sav-conversion-broad153](https://drive.google.com/drive/folders/1PwRAw0xg4WKp5MpgpcRO3Fg6B4H5dnmn).
Local mirrors are under `artifacts/run-exp-sav-conversion-broad153/`. Scripts
assume those paths and a private display `:153`. One original process at a
time; never run two copies of the live runner against the same prefix/display.

Never delete or overwrite a save or measurement to regenerate it. New work
needs a new attempt/version and unique original-game SaveAs names. Continue
measurement commits/pushes after each batch and at least every30min. Original
Windows acceptance, the owner's twelve saves, exhaustive state combinations,
full-length campaigns and all graphics/UI features remain separate from this
Wine-based conversion experiment. The paused battle queue is not resumed.
