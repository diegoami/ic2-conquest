# Static extractor validation packet — Research218

No game, Wine instance or retained screenshot/pixel probe was run. Original and
extracted media stays private outside Git and public releases. This directory
contains source identities, resource/format metadata and scalar validation only.
Never overwrite/delete measured outputs or saves to regenerate them; use new
receipt/media-directory names. Older receipt versions remain immutable.

## Inputs and expectations

- Original EXE pin: `setup/pins.txt` (`9d753d5d…`).
- Contract/checker receipt: Research PR219 merge
  `a0870dd26b86f74233334e7d9500309082403933`.
- Remake key source pin: `55bd7fcef91e41b179a6df9851384bb687932e8e`.
- Existing conquest inventory: `run-exp-unit-icon-resources` at source
  `f71c70ffa9ccf8f7cfbb5335fb28c4c44d341ed6`.
- Ten supplied WAV files recovered from the already verified private backup.
  Their PCM is decoded and preserved as supplied; original-versus-converted
  provenance is not inferred from the filenames or older measurements.

## Receipts

- `pe-dfm-layout-v1.json`: initial bounded-profile discovery of actual PE resource
  identities and binary DFM property paths. Produced with pefile plus the retained
  form parser before the independent portable reader was implemented.
- `extractor-initial-v1.json`: first new tool metadata scan; supplied WAV root
  omitted. It predates later hardening; its code identity is historical.
- `extractor-private-export-v2.json`: first private-media export, before final
  command-mapping/source-identity changes. Preserved as measured.
- `extractor-private-export-v3.json`: complete scalar receipt for the 1.0.0
  candidate, before the research-requested filesystem-error redaction fix.
- `private-export-validation-v1.json`: every private output hash verified, all
  generated PNG/CUR/ICO files accepted by host ImageMagick `identify`, retained
  list expectations matched, command-key candidate counts checked.
- `synthetic-tests-v1.txt`: isolated synthetic suite, no original media fixtures.
- `extractor-private-export-v5.json`, `private-export-validation-v2.json` and
  `synthetic-tests-v2.txt`: current 1.0.1 candidate after research's metadata
  privacy correction; 36 tests pass. All 362 media payloads match the previously
  externally decoded files byte-for-byte, and all new output hashes verify.
- `extractor-isolated-v4.json` and `isolation-and-overwrite-validation-v1.json`:
  exact copied tool run with Python `-I` outside the repository; existing private
  export refused without altering any of its 362 payloads. Same tool hash as v3.
- `key-crosswalk-validation-v1.json`: all 89 distinct proposed keys exist in the
  pinned 100-key remake union. Six surface and five generic unit-icon keys have
  no proposed mapping; owner/river suitability is not implied by key existence.

The current tool SHA-256 is
`5d266a075ce1cc75ccb359f2b4a64aa5bbf82e2dca031965c729e6abd53a97f5`.
It is recorded independently in the receipt and the private export validation.
The earlier 1.0.0 SHA-256 was `558bdb33...`, retained in its immutable receipts.
Any later code change needs a new receipt identity/version, not edits to these.

## Result and limits

73 resource leaves; 29 forms; 11 image lists containing 128 images; 63 glyph
sheets containing 79 stored frames; ten resource bitmaps; six native cursor
groups and one native icon group. All ten supplied WAV files validate/decode.
The export holds 345 PNGs, six CURs, one ICO and ten WAVs (362 payloads).

Metadata retains 36 UI-command candidates and eight battle-toolbar mappings.
Candidate component/key correspondence does not prove consumer rendering.
Image-list masks remain separate images; native cursor/icon XOR/AND planes
remain native containers. The consumer still owns correct compositing, owner
city variants, six river shapes, runtime recolouring/selection and partial-pack
fallback. No rendered, audible, native Windows, original-layout or shipped-game
acceptance is claimed. Research review is requested for the source packet.
