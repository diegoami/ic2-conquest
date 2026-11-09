# run-exp-assets223: toolbar glyphs → remake command keys (research #223)

Static only: no game, Wine instance, screenshot or pixel probe was run, and no
media was written. The scan reads the pinned original EXE read-only through the
accepted extractor's parsers (`scripts/extract_original_assets.py`, v1.0.1,
SHA-256 `5d266a07…`) and keeps only scalars: component paths, hints, OnClick
identifiers, published-field offsets, handler addresses (from the decompile's
`delphi_symbols.tsv`), glyph geometry, the palette index of the transparent key,
identical-image group numbers, and per-index counts for `TAreaMap.PointsList`
and `TAreaMap.MapsList`. It writes no pixels, crops or digests of original content.

Measurements are kept (rule 6). Never delete or overwrite a receipt. A re-run
writes a new name (`command-glyphs-v2.json`, …): the script refuses to write
over an existing file.

## Inputs (pins)

- Original EXE SHA-256 `9d753d5de78801f2368d06125cc87f296b92f671b686c39fd6ac149838ebba31` (`setup/pins.txt`).
- Decompile `all_app_functions.txt` SHA-256 `2018c205a4e4ea4a4079f2d166623fb571062832d76e19b72e11d1f0edac87d8`,
  59,228 lines; `delphi_symbols.tsv` from the same decompile set (`$IC2_DECOMPILE`, fetched by `harness/decompile.py`).
- Save `saves/fortify-arretium-0720.SAV` (tracked, `saves/README.md`). It is used only to classify the 320×140 map
  tiles by terrain code when MapsList is checked against the map.
- Remake key source: `diegoami/imperial_conquest_2` at `55bd7fcef91e41b179a6df9851384bb687932e8e`
  (`assets/packs/authored/manifest.json`), the same pin the extractor's key crosswalk used.

## Reproduce

```bash
python3 -I runs/experiments/data/run-exp-assets223/scan_command_glyphs.py \
  --exe "$IC2_WORK/prefix/drive_c/IC2/Imperial Conquest 2.exe" \
  --extractor scripts/extract_original_assets.py \
  --symbols "$IC2_DECOMPILE/delphi_symbols.tsv" --dump "$IC2_DECOMPILE/all_app_functions.txt" \
  --save saves/fortify-arretium-0720.SAV --repo . \
  --out runs/experiments/data/run-exp-assets223/command-glyphs-v2.json
```

The receipt's `pins.pins_match` must be `true`. The stdout summary for v1 was
`{"pins_match": true, "glyph_sheets": 63, "with_candidate_key": 44}`.

## Receipts

- `command-glyphs-v1.json` (2026-11-09): the first and current receipt, cited by
  `findings/2026-11-09-assets223-command-glyph-crosswalk.md`.
