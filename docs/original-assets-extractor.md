# Portable original-asset extractor for Research218 / remake1740

The deliverable is [scripts/extract_original_assets.py](../scripts/extract_original_assets.py),
a single portable Python 3.10+ standard-library file. Copying that one file is
sufficient; it has no conquest imports, Wine, Ghidra, pefile or ImageMagick
dependency. Original/extracted media is private, supplied by the user and never
distributed with the tool. The separate research session qualified tool 1.0.1 at
`1544d666c45004f1eda362cb84a4701e0e4143d2` for this supported static profile.
Actual remake integration, native composition and runtime packaging remain separate.

Reviewed tool SHA-256:
`5d266a075ce1cc75ccb359f2b4a64aa5bbf82e2dca031965c729e6abd53a97f5`.

Canonical contract: Research PR219 at
`a0870dd26b86f74233334e7d9500309082403933`,
`docs/reports/2026-11-07-original-assets218-extraction-spec.md`.
Remake key crosswalk baseline: `55bd7fcef91e41b179a6df9851384bb687932e8e`.
Only the EXE profile pinned in `setup/pins.txt` is qualified. Unknown hashes
receive explicit unsupported metadata; they do not get silently decoded as this
profile. The metadata schema is `ic2-original-assets/1`, tool version `1.0.1`.

## Main-session retrieval and shipping boundary

Retrieve the tool and this document from the **exact reviewed conquest commit**
reported by research, rather than a moving branch or an earlier inventory-only
head of PR346. Retrieve `tests/test_original_assets.py` for development validation.
The delivery receipt records the source file SHA-256; verify it after download.

Main owns packaging the runtime, calling the tool and integrating its output
with the game's per-machine asset selection/cache. This implementation needs
Python 3.10+; do not assume it is installed on a player's machine. Main must
explicitly bundle a supported interpreter, choose an installer-managed runtime,
or port the tested contract into the existing .NET runtime. A .NET port is new
consumer/integration work; do not claim the Python file runs inside Godot alone.
Use process argument arrays, not shell interpolation, for user-selected paths.
No main-repository edits or distribution decisions were made by conquest.

## CLI

Metadata-only inspection (the executable and WAV directory are independent,
explicit inputs):

```bash
python3 extract_original_assets.py --exe '/installation/Imperial Conquest 2.exe' \
  --wav-root '/installation/WAVS' --metadata '/receipts/scan-v1.json'
```

Omit `--wav-root` when sounds are unavailable. A missing directory or partial
installation is reported per sound; there is no directory guess or download.
Filenames are matched case-insensitively, while ambiguous duplicate names are
reported and symlinked sound files are unsupported.

Optional private conversion:

```bash
python3 extract_original_assets.py --exe '/installation/Imperial Conquest 2.exe' \
  --wav-root '/installation/WAVS' --metadata '/receipts/export-v1.json' \
  --media-dir '/private-cache/new-export-v1'
```

The media directory must be new and outside all Git checkouts; the metadata
receipt must be outside it. Existing output files/directories are never
overwritten. Files publish atomically, and `manifest.json` publishes last with
the private output hashes. A failed export leaves its existing output intact;
use a new output directory for a retry, never delete measured data to regenerate
it. The tool does not replace or alter the source installation.

Exit 0 means the supported static scan completed with no malformed/unsupported
assets or supplied sound files. Missing sounds, unresolved semantic mappings and
native-compositing limits can still exist: inspect per-category/per-asset status.
Exit 2 means unsupported profile, malformed input, unsupported encoding, ambiguous
supplied sounds, or publication failure. JSON records available bounded partial
results when scanning succeeds far enough; a filesystem/publication failure may
leave no new metadata receipt. Stdout is a small JSON summary, stderr diagnostics.
No game process is launched.

## Output contract

The JSON contains:

- `source`: source hash, supported profile and disposition. No absolute private
  input path, original pixels, samples or waveform dump is included.
- `resources`: PE type/name/language identities, raw offsets/sizes and code page.
  Numeric IDs remain numbers and named identities remain strings.
- `forms`: parsed DFM class/name and resource index. All binary DFM properties
  appear as assets, including unsupported properties with a reason.
- `assets`: component/property identity, format, cell/frame order, colour/mask
  geometry, source semantic ID, candidate consumer key and mapping status.
- `sounds`: ten logical sound names, discovered basename, availability, PCM
  channels/rate/depth/frames/duration, decode validation and candidate sfx key.
  Supplied audio provenance is not automatically labelled original or converted.
  Filesystem failures use `wav-file-io-error`, exception class and errno;
  absolute input paths and raw filesystem exception text are excluded from JSON.
- `summary`, `diagnostics`, `categories`, `validation_status` and `limits`:
  explicit bounded results and unresolved coverage. `passed-static` does not
  imply rendered, audible, native Windows or remake acceptance.
- `extractor_sha256` and `cache_identity`: source/profile/tool/schema identities,
  supplied WAV content and states, export mode and conversion policy. The tool
  does not implement cache-hit reuse; main must validate a completed manifest
  and its output hashes before selecting a cache. Recoloured caches additionally
  require the exact nation-colour inputs in the consumer's identity.

Media filenames are generated safe identifiers, not resource names or source
paths. In metadata-only mode they describe prospective output names; no media
exists until export. The private manifest additionally records output hashes.

## Conversion and rendering boundaries

- Image lists: indexed colour PNG plus separate black/white mask PNG for every
  stored cell. Spare sheet cells are excluded by the declared count. Keep masks
  separate until the consumer implements the correct AND/XOR/raster operation;
  do not indiscriminately turn palette colours or mask bits into alpha.
- Button glyphs: stored horizontal frames converted to RGBA PNG with the specific
  TSpeedButton bottom-left colour key. This covers stored frame images, not all
  VCL disabled/pressed synthesis. General command mappings are candidates by
  form/component correspondence, not a consumer rendering proof.
- PE bitmap resources: supported indexed DIBs converted to RGB PNG. Six cursor
  groups and the application icon reconstruct native CUR/ICO containers with
  original hotspot and XOR/AND planes; alpha/rendering equivalence is partial.
- WAV files: validated 8/16-bit mono/stereo integer PCM; private exports preserve
  the exact supplied WAV file without resampling or pretending it is the shipped
  version. Main can load supported files directly or perform an explicitly
  qualified consumer conversion. No audibility/latency test is claimed.
- Units: source purple/white/blue map once to nation +0x424/+0x428/+0x42C, with
  Delphi TColor channel order normalized. `recolour`, `tcolor_rgb`, `srcerase`
  and `masked_xor` are reusable tested helpers. Export does not pre-recolour.
  City/nation-button owner artwork retains its own palette; Numidia's unit fill
  and city fill intentionally differ.
- Rivers: six shape identities persist despite one generic consumer key. Owner
  identity persists for all city/capital variants. SRCERASE selection remains a
  runtime operation, not a transparent yellow cursor. Newer scenarios, seamless
  surface textures and unresolved Area-map point meanings retain explicit gaps.

## Validation and reproducibility

Run synthetic tests without original inputs:

```bash
python3 -m unittest tests.test_original_assets
```

Tests generate their own PE/DFM/BMP/WAV fixtures. They cover bounded resource
identities, malformed/truncated data, bitmap depths/padding/orientation, masks,
frame slicing, colour substitution hazards, raster truth tables, WAV partial
installations, immutable output and execution of an isolated copied tool.

Original validation receipts live under
`runs/experiments/data/run-exp-assets218/`. Old versions remain immutable; the
running notes identify the final code/content pin and receipts to review.
Private exports and their hashes stay outside public git and releases.
The research session reviewed the extractor packet; main separately validates
actual installation discovery, loading/fallback, crisp scaling, per-owner/river
support and screen consumers before shipping an original-assets option.
