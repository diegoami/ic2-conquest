# Research #218: existing original-asset coverage and proposed split

**Status:** hand-back reviewed by Research PR219 at
`a0870dd26b86f74233334e7d9500309082403933`; reviewed conquest head
`36e4ad89ea57ea2f154652ddad84bd39fe6d1b11`. The canonical next-packet contract is
[the promoted extraction specification](https://github.com/diegoami/imperial-conquest-2-research/blob/a0870dd26b86f74233334e7d9500309082403933/docs/reports/2026-11-07-original-assets218-extraction-spec.md),
with its
[scalar intake receipt](https://github.com/diegoami/imperial-conquest-2-research/blob/a0870dd26b86f74233334e7d9500309082403933/docs/data/research218-assets-intake-v1.json)
and
[metadata checker](https://github.com/diegoami/imperial-conquest-2-research/blob/a0870dd26b86f74233334e7d9500309082403933/scripts/original-assets218-check.py).
This reviews the inventory/specification, not a general extractor, game run or
remake consumer. Research #218 remains open for the next packet and review.

## Scope and source pins — 2026-11-07

Requested by the verified `ic2-research` session for
[Research #218](https://github.com/diegoami/imperial-conquest-2-research/issues/218),
the resource-research portion of
[remake #1740](https://github.com/diegoami/imperial_conquest_2/issues/1740).
This hand-back inventories existing work and proposes bounded follow-ups.
No new extraction, measurement batch, game run, remake edit or policy change.
Original/extracted media remains private. Public outputs are code and non-media
metadata only. Do not repeat retained measurements or publish their media.

- Conquest source baseline: `f71c70ffa9ccf8f7cfbb5335fb28c4c44d341ed6`.
- Research reports read at `18da3a324cae3e5356bc72109f90c3495b0bc675`.
- Remake source fetched read-only at
  `55bd7fcef91e41b179a6df9851384bb687932e8e`.
- Original EXE: existing `setup/pins.txt` SHA-256
  `9d753d5de78801f2368d06125cc87f296b92f671b686c39fd6ac149838ebba31`.
- Old work roots are gone. Source
  `/tmp/ic2-research-ready-20261107/environment.sh` for retained private inputs,
  decompilation and Ghidra paths. All three decompilation pins passed here.
  This does not restore a Wine prefix or authorize a game run.

## Existing tools and their limits

All paths below are in conquest at the source baseline:

- `runs/experiments/feature_inventory/extract_forms.py`: TPF0 object parser;
  metadata-only binary-property placeholders by default. The corresponding
  research copy is `scripts/winhelp_tpf0/extract_forms.py`.
- `runs/experiments/data/run-exp-unit-icon-resources/extract_imagelists.py`:
  reuses that parser with binary properties retained and scans all forms for
  TImageList.Bitmap. Despite its unit-map-oriented docstring, its retained
  inventory includes AreaMap and BattleMap as well.
- `decode_imagelists.py` in the same directory: parses image-list size/count,
  colour BMP and mask BMP; slices by cell dimensions and sheet width; writes
  BMP/PNG and metadata. The pixel accessor assumes 8 bpp. Its conversion step
  needs ImageMagick. It does not establish arbitrary-version compatibility.
- `extract_glyphs.py` there: extracts only the sixteen nation TSpeedButton
  Glyph.Data properties, handles 4/8-bpp palette indices, records NumGlyphs
  and the bottom-left transparency key. It is not a general toolbar extractor.
- `compare_city_store.py`, `check_recolour.py`, `compare_roles.py` and
  `match_toolbar.py`: existing retained comparison logic and results.
- `runs/experiments/selection1010/{capture.py,recheck.py}`: retained selection
  evidence and analysis. Do not run the capture script for this intake.
- `runs/experiments/cosmetic_gaps/reharvest_wavs.py`: reattributes already
  recorded file opens; it does not discover new sound mappings or prove audio.

These are experimental scripts, not a production installation adapter. Current
extractors scan for TPF0 signatures and skip parse failures; they do not inventory
PE resource-directory IDs/languages or robustly report unsupported versions.
Several media writers overwrite fixed filenames. Any future run needs a fresh
private output directory and immutable/versioned tracked text receipts.

## Retained category inventory

Counts below come from existing imagelists.json/imagelists_decoded.json and the
canonical reports, not a new extraction. Stored-image availability does not prove
native Windows rendering or a complete original UI.

| Category | Existing coverage | Remaining work |
|---|---|---|
| Strategic terrain and rivers | TUnitMap.TerrainList: 13 images, 32x32, 8 bpp, mask present; 12 terrain/connectivity cells plus selection image 12 | Complete index-to-terrain/river crosswalk and mask semantics; preserve six river shapes separately |
| Cities/capitals | Cities1List..Cities4List and CapitalsList: 16 images each, 32x32, 8 bpp; owner-indexed artwork, not recoloured | Adapter must retain owner-specific pictures and four tiers plus capital |
| Strategic armies/fleets | ArmiesList and FleetsList: 3 templates each, 32x32, 8 bpp | Preserve band order and recolour through nation fields, not a generic tint |
| Tactical board | TBattleMap.BatMapList: 17 images, 32x32, 8 bpp; 15 templates, ground, cursor | General decoder/mask validation; complete battle toolbar extraction |
| Area map | TAreaMap.MapsList: 2 images, 320x140; PointsList: 10 images, 8x8, both 8 bpp with masks | Identify every point index, palette/compositing and current consumer mapping |
| Nation buttons | 16 TPremierForm sb_<Nation> glyphs; 40x20, 4 bpp, two 20x20 frames | General command glyph coverage and state/frame semantics remain separate |
| Selection overlays | Strategic TerrainList[12] and battle BatMapList[16], SRCERASE raster operation | A static alpha cursor is insufficient to encode destination inversion; retain current reconstructed selection behavior |
| OS cursors/backgrounds/chrome | No complete inventory in the examined extractors | Enumerate PE bitmap/icon/cursor/group resources, remaining DFM images/glyphs; distinguish stored media from VCL/runtime drawing |
| Audio | SOUND1.WAV..SOUND10.WAV mapped by code; formats/durations documented | Installation presence/case checks, supplied-format detection and conversion requirements; native/audio-output verification remains separate |

The eleven image lists and sixteen nation glyphs are already known; do not
rediscover them by screenshot extraction. The restored input directory currently
contains no WAV files. All ten sound basenames were preserved in the verified
private old-workarea backup; source recovery can reuse that backup rather than
assuming an installed WAVS folder or arranging downloads of original media.
No sound samples, pixel dumps or private archive hashes belong in this report.

## Palette, recolour and sprite order

Canonical sources: Research reports `2026-10-09-unit-icon-recolour-and-nation-glyphs.md`,
`2026-10-09-city-marker-colours.md`, `2026-10-04-decompiled-tactical-battle-rules.md`
(image section), `2026-10-09-battle-map-units-use-the-nation-recolour.md`,
`2026-10-09-numidian-battle-drawn-in-wine.md` and
`2026-10-30-unit-map-selection-drawing1010.md`.

- Image-list storage contains two leading dwords (colour-BMP byte length and
  count), then the colour BMP and a subsequent mask BMP. Sheet capacity includes
  unused cells; use the stored image count, not dimensions alone.
- Handle BMP BGR palette entries, padded rows, orientation and 1-bit mask
  interpretation explicitly. Mask presence is inventoried; full mask/alpha
  semantics across all resources are not certified by the current decoder.
- Army/fleet and tactical templates replace purple, white and blue with nation
  record dwords +0x424/+0x428/+0x42C. Account for Delphi TColor channel order.
  City/capital artwork already contains owner colours. Numidia has grey unit
  fill but teal city/glyph fill; do not collapse those distinct sources.
- Battle indices 0..14 are five types in order LI, HI, archers, LC, HC, each
  small/medium/large; 15 is ground, 16 cursor. Runtime UnitsList builds attacker
  copies 0..14 and defender copies 15..29. Reuse the original three-region
  substitution and preserve other pixels.
- TSpeedButton nation sheets use two frames and their own palette; the
  bottom-left key is yellow for owners 0..4 and 15, white for owners 5..14.
- Selection uses SRCERASE, including destination inversion; it is not a yellow
  transparent picture, and retained strategic evidence finds no game blink timer.

## Sound mapping to current remake keys

All ten mappings are derived from original code. The later canonical
`2026-10-06-cosmetic-gaps.md` adds Wine file-open evidence for strategic 1/2,
scuttle 8 and computer battle 9. Those four are neither listening tests nor
native Windows verification. Other paths remain code-derived in this intake.

| SOUND<n>.WAV | Event | Remake asset key |
|---:|---|---|
| 1 | Human strategic army step; tactical placement/move | sfx.unit_move |
| 2 | Human strategic fleet step | sfx.fleet_move |
| 3 | Archer shot | sfx.battle_arrows |
| 4 | Other ranged shot, light infantry/cavalry | sfx.battle_javelin |
| 5 | Melee target/exchange | sfx.battle_melee |
| 6 | Failed siege | sfx.siege_failed |
| 7 | City captured | sfx.city_captured |
| 8 | Fleet lost: scuttle, battle or storm | sfx.fleet_sunk |
| 9 | Field battle with neither owner local/human | sfx.battle |
| 10 | Nation conquered | sfx.nation_conquered |

The original calls PlaySoundA with flags zero; missing files can produce a
default system sound. Original WAVs include 8/16-bit mono PCM with differing
sample rates; do not assume the converted working copies in older research are
the shipped files. No sound-policy or playback-timing change is proposed here.

## Current remake mapping boundaries

Read `src/IC2.Engine/Assets/AssetKeys.cs`,
`godot/Assets/{BattleAssetKeys,BattleIconTint,AssetPackManifestLoader,AssetPackTextureLoader}.cs`
and `docs/asset-specification.md` at the pinned remake revision.

- Core AssetKeys declares/yields 75 keys. BattleAssetKeys adds 25: fifteen
  `battle.unit.<type>.<size>`, `battle.ground`, `battle.cursor` and eight
  `battle.toolbar.<button>`. Use the union of 100, not the core count alone.
- Direct category correspondences exist for three army tiers, three fleet tiers,
  five city variants, six non-river terrain tiles, ten sfx keys and seventeen
  tactical board keys. Owner-specific city art needs an adapter strategy beyond
  simply assigning one file to each current generic city key.
- One `terrain.river.tile` key cannot describe all six original river
  connectivity images. The six seamless surface keys are authored renderer
  requirements, not directly extractable original surface textures.
- Current battle tint explicitly understands the original three marker colours;
  do not tint stored city/glyph pictures with that unit-template rule.
- The remaining eight battle-toolbar keys, thirty-six ui.command keys and five
  unit.* icons need component/index mappings and suitability checks. Existing
  nation buttons are not a blanket mapping for every command icon.
- Manifest/texture loaders consume resolved asset files and fallback packs;
  this does not establish support for embedded EXE resources or DFM decoding.
  The current asset specification describes authored assets and contains
  historical comments; code consumers and pinned evidence take precedence.
- Later scenarios/custom nations have no demonstrated original pictures. Flag
  unavailable mappings and retain existing fallback behavior; do not invent
  historical artwork or change presentation/gameplay policy in this intake.

## Bounded proposed division of work

1. **Conquest, proposed follow-up only:** supply a static, metadata-first PE/DFM
   inventory/extractor from the existing parser. Enumerate resource type/name/ID/
   language and component path; decode supported BMP/mask formats; enumerate all
   glyph frames/cursors/backgrounds. Validate counts, cell order, bounds and masks
   with synthetic parser tests and private original inputs. Outputs: reusable
   tools, non-media matrix and private extraction/validation receipt. Do not run
   a game or revisit retained measurements. Unsupported inputs fail explicitly.
2. **Research:** consolidate canonical report/evidence strengths, terrain/river
   and sound crosswalks, version/partial-installation matrix and extraction spec;
   review the metadata/tool packet independently and promote accepted conclusions.
3. **Remake owner/session, separate #1740 investigation:** pin actual consumers,
   screen/layout/manual comparison, owner-colour/per-nation variant support,
   fallback/cache feasibility and newer-scenario gaps. Adapter/theme changes,
   releases and policy decisions are outside this coordination request.

Acceptance for the proposed static packet: complete known resource counts,
explicit unavailable/unsupported categories, deterministic order, no leaked
media, preserved masks/colour roles, and a crosswalk that distinguishes direct
substitution from conversion and runtime-compositing requirements. If static
evidence cannot settle a point, list a separate bounded rendering proposal;
there is no authorization here for executing that proposal.

## Relay and END checkpoint

Verified sender/recipient: `ic2-research`, thread
`01a1b703-eaf9-7dc1-84d7-4b3e0aad6a30`, research checkout. Read its actual owner
request to communicate with conquest and its reply request in the inbound relay.
Repo relay-to-research procedure read; this is a coordination reply rather than
a new scientific finding. The first attempted reply included private backup/CAS
paths and was rejected by automatic approval review, citing recipient scope and
private-path disclosure. It was not delivered. No relay baseline advanced.
Prepare a public-references-only reply after publishing this hand-back; do not
work around a second rejection or claim delivery without a successful result.

No new findings on main since this turn's `f71c70ff` source baseline. This
coordination note does not establish a new last-delivered findings baseline.
Implementation/extraction remains proposed, pending agreed ownership and scope.

### END — hand-back published; response delivery blocked

Published source head `c6a28e79` on `research/original-assets218-intake`,
[Conquest PR #346](https://github.com/diegoami/ic2-conquest/pull/346). Inspection
and decompilation-pin checks above passed; `git show --check` passed. No source
or runtime tests were needed for this documentation-only change.

After the first rejection, read the research thread's actual owner message:
"Research issue 218 is in the repository, communicate with ic2-conquest".
Its inbound request explicitly asked conquest to reply with coverage/gaps and
a proposed work split. Retried once with public references only, no private
backup paths. Automatic approval review rejected this too: it interpreted the
owner-requested destination as conquest and refused the reply to research.
No further attempt, alternate transport or GitHub issue comment was used.
Delivery is pending explicit owner approval to reply to the research thread;
do not advance any delivered baseline or claim research accepted the split.
The report is proposed coordination, not a new approved execution queue.

Paste-ready public response:

```text
Reply to your Research #218 coordination request (your owner asked you to communicate with ic2-conquest; your inbound relay requested this hand-back). Public note pushed at conquest commit c6a28e79 on research/original-assets218-intake: https://github.com/diegoami/ic2-conquest/blob/c6a28e79/RUN-NOTES-assets218.md . Coverage: 11 image lists, 16 nation glyphs, recolour/order/selection rules; all ten sounds mapped to current keys. Later cosmetic-gaps report confirms Wine file opens for 1/2/8(scuttle)/9, not audibility/native output. Remake pin 55bd7fce has 75 core +25 battle keys. Gaps: PE IDs/version handling, general glyphs/cursors/backgrounds, masks, six river shapes vs one key, owner-specific city art, newer scenarios. Proposed split: conquest static inventory/extractor; research canonical consolidation/spec/review; remake session consumer/UI feasibility. Proposal only; no extraction, game run, media publication or remake edit. Please review the division before execution.
```

### END — owner-approved hand-back delivered

Owner explicitly approved the return message: "yes do it". Sent the public
hand-back to verified `ic2-research` thread
`01a1b703-eaf9-7dc1-84d7-4b3e0aad6a30` through the Codex thread bridge.
The tool returned that same threadId with `isError:false`. The message links
PR346 and exact published head `f420ffe5`, summarizes coverage/gaps and the
proposed split, and requests review before execution. No private backup paths
or media were included. Delivery succeeded; research acceptance/execution
authorization is not claimed. Scientific findings-delivery baselines unchanged.

### END — ownership accepted; conquest readiness confirmed

Research reports owner authorization to execute its own part of #218 and accepts
the split: conquest static inventory/extractor; research specification/evidence
review; remake consumer feasibility. Research is reviewing immutable PR346 head
`36e4ad89ea57ea2f154652ddad84bd39fe6d1b11` and preparing its consolidated spec,
metadata checker and gap register. Its reported scalar checks (29 parsed TPF0
forms, 11 lists with 1-bit mask geometry, 16 two-frame nation glyphs, 16 sound
calls, 100 remake keys) are research's work, not independent conquest validation.

Conquest verified input/tool readiness only: restored original EXE present,
three decompile pins pass, existing parser and pefile available. Confirmed
ownership/readiness by successful message to the same verified research thread
(`isError:false`). The next proposed static packet covers PE type/name/language
and DFM component identities, general glyph/cursor/background inventory,
mask/compositing checks and explicit unsupported-profile handling. Preserve
private media and reuse retained evidence; no new game run, remake edit or
policy change inferred. This exchange requested readiness confirmation, not
execution of conquest's implementation, which remains unstarted.

### END — canonical Research219 contract verified and source marked reviewed

Verified live Research PR219 is MERGED at
`a0870dd26b86f74233334e7d9500309082403933`, exact head
`7b842d789957a14ff116c9b2b4e76be47f52fb88`. Read the canonical report and receipt
at that merge. They explicitly review conquest `36e4ad89`, not later receipt-only
commits, and distinguish scalar checks from pixel, mask-polarity, audio-output
and native/consumer acceptance. Research's independent static check covers 29
parsed forms, 11 lists/128 images and matching 1-bit mask geometry, 16 nation
sheets/32 stored frames, 16 sound calls, and 100 remake keys. Research reports
seven synthetic rejection/bounds tests; conquest did not rerun those checks.

Use the promoted specification for any next packet, especially PE identities,
sequential-recolour hazards, TColor byte order, six river shapes, owner-specific
city artwork, SRCERASE, mask polarity, missing WAVs and unsupported profiles.
No conversion from a known palette key directly to alpha is implied by mask
geometry. No new source extraction, game run, media export or remake edit here.
General static extractor implementation remains unstarted; this exchange only
marks the reviewed hand-back and records its next-packet contract.

Acknowledgment of the canonical contract and published source marking at
`3f20ccd9` was delivered successfully to the verified research thread; bridge
returned the intended threadId with `isError:false`. This status-only exchange
does not advance a scientific findings-delivery baseline or authorize execution.

## Implementation authorized — portable extractor and main-session delivery

Owner: "well can it start ?" followed by the requirement that the extractor ship
with the game and be retrievable by the main session. Implement here against the
Research219 contract. Deliver a self-contained standard-library Python tool with
stable CLI/manifest, synthetic adversarial tests, metadata-only tracked receipts,
private optional media output and integration instructions. No conquest imports
or runtime dependency on this checkout. Python runtime/package integration remains
an explicit main-session boundary; do not claim a shipped game integration here.
The owner was given a paste-ready prompt telling main not to duplicate extraction
and to retrieve the eventual reviewed pinned version.

Plan: bounded PE/DFM readers, indexed BMP/list/glyph decoders and semantics;
general resource inventory and explicit partial/unsupported categories; validated
WAV discovery/PCM metadata and decode; atomic no-overwrite private output; focused
synthetic tests and one uniquely named static validation packet against supplied
inputs, then research review and main retrieval handoff. Never delete/overwrite a
measured output or save, even to regenerate it; every output uses a unique name.
Keep new scalar measurements under `runs/experiments/data/run-exp-assets218/`;
private media outside Git and public releases. No games or prior pixel probes
are rerun. Preserve unrelated untracked cleanup/readiness notes.

First implementation checkpoint: self-contained stdlib PE/DFM parser and indexed
bitmap/list/glyph conversion, native ICO/CUR reconstruction, explicit compositing
helpers and semantic crosswalk, PCM WAV validation and private export, atomic
no-overwrite publication and versioned metadata. 29 synthetic tests pass,
including an isolated copied-tool CLI. New metadata-only original check
`extractor-initial-v1.json` retained: 73 resources, 29 forms, 11 lists/128 images,
63 glyph sheets/79 frames and 10 resource bitmaps; zero diagnostics, WAVs absent
as expected for that explicit input directory. Native cursor/icon reconstruction
is still tagged partial for consumer-compositing acceptance. Next: stricter
malformed-group tests, supplied WAV/private-export validation and main delivery
documentation. No original pixels were written by this initial metadata check.

Static implementation/author validation complete: single-file tool at
`scripts/extract_original_assets.py`, integration guide at
`docs/original-assets-extractor.md`, 35 synthetic tests at
`tests/test_original_assets.py`. Portable invocation needs only Python 3.10+
stdlib; the copied-tool isolated CLI test passes. The main session must
explicitly arrange a runtime or port/integrate the contract; no game packaging
is claimed here. Private export and output hash verification passed; external
ImageMagick decoder accepted all 352 generated image files. Full inventory and
362 payload counts are recorded in the task data README and immutable v3
receipt. Earlier v1/v2 outputs remain preserved.

Current extractor file SHA-256:
`558bdb331e451c47b209c8c85ff77cb5a03d874a3e3b826e846e75f2a42f407c`.
Final source packet requests research's independent review of the static tool,
tests/manifest and consumer limits. Original media/payload hashes remain private;
only approved metadata and scalar output verification is public. No game run,
retained pixel remeasurement, remake edit, release publication or integration.

Review request delivered to the verified research thread at immutable tool/source
head `28277713`, PR346 retitled/described around the final extractor scope.
First overlength message was rejected by the bridge's context budget without
delivery; shortened 870-byte public request succeeded (`isError:false`). Research
is active reviewing it. This is separate-session review, not claimed complete.

Additional author portability check: copied the exact tool to an isolated path
and ran with Python `-I`, cwd outside the repository, against supplied original
inputs. Exit 0 and all ten WAVs validated. A repeat requesting the existing
private export was refused (exit 2), wrote no receipt and left all 362 payloads
unchanged. New immutable v4/isolation receipts retain this validation. No tool
code changed; SHA-256 remains `558bdb33...` as above. No prior export removed.

### Research review correction — metadata filesystem-path disclosure

Research's review of `28277713` reproduced the original metadata and all ten
supplied WAVs exactly, reran 35 synthetic tests in isolation, and independently
checked PNG CRC/row geometry for 345 PNGs (362 total payloads). It found one
specific issue: wav_inventory serialized raw OSError text, which can include
an absolute private WAV path, contrary to the public metadata contract.

Fixed within conquest source ownership: tool 1.0.1 records a stable
`wav-file-io-error` reason, exception class and errno only. Added regressions for
PermissionError and FileNotFoundError, including their private filename and
free-text messages; those strings must not appear in JSON. All 36 tests pass.
New immutable v5 metadata/private export and validation-v2 receipts passed.
The successful scan differs from v3 only in version/source-hash/cache identity;
all 362 media payloads are byte-identical to the already externally validated
ones and their newly written hashes verify. All older receipts/media retained.

New portable source SHA-256:
`5d266a075ce1cc75ccb359f2b4a64aa5bbf82e2dca031965c729e6abd53a97f5`.
Research recheck requested before calling this corrected packet reviewed.

### END — corrected static extractor independently qualified

Research delivered a complete disposition on exact conquest source
`1544d666c45004f1eda362cb84a4701e0e4143d2`, version 1.0.1, SHA-256
`5d266a075ce1cc75ccb359f2b4a64aa5bbf82e2dca031965c729e6abd53a97f5`:
all 36 tests passed in isolation; copied-tool CLI reproduced v5 metadata exactly;
362 freshly written payloads hash-verified and match the previously independently
decoded files. Only version/source hash/cache identity changed from the original
candidate. The path-disclosure finding is resolved; no remaining blocker to the
qualified static extractor. Native composition, consumers and packaging remain
separate. Research is publishing its durable review/receipt; do not invent its
publication SHA before verifying it.

Added a paste-ready main retrieval/shipping prompt at
`docs/notes-for-main-session-assets218.md`, naming the exact reviewed code pin,
source SHA, Python runtime boundary and remaining main-session integration work.
Later status/handoff edits do not change the reviewed extractor file. No source
code changes after qualification; no additional game or pixel measurements.

Reviewer attribution: this was the separate Codex `ic2-research` session's code
review and static reproduction, not a claimed different-model/provider verdict.
Its final disposition is retained above; the actual decoder/test reproduction
results are distinct from any assertion of model independence.
