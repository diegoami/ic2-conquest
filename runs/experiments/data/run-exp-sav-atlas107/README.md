# Issue #107 SAV atlas: field map and coverage receipts

Task: [conquest issue #107](https://github.com/diegoami/ic2-conquest/issues/107). Finding:
[original SAV semantic atlas](../../../../findings/2026-10-21-original-sav-semantic-atlas.md).

- `field-map-v1.csv`: the machine-readable ledger. 113 rows over 14 record
  types: map cell, city, army count, army, army unit slot, fleet count, fleet,
  nation, mercenary, news index, news slot, trailer, battle block and battle
  unit slot. Offsets are relative to the record. `rec:<type>` rows nest a
  sub-record array. `semantic` is one of:
  - `CONFIRMED`: the meaning is established by code and/or reviewed saves.
  - `CONTEXTUAL`: the meaning depends on a documented state rule (a sentinel, a union, a tombstone, or text with a retained tail after the NUL).
  - `PARTIAL`: there is a named reading, but its writer set, domain or lifecycle is not consolidated.
  - `UNKNOWN`: the meaning is not established.

  Nation rows reuse research37's `nation-matrix-v2.csv` ranges exactly. The
  checker enforces this.
- `corpus-public-v1.json`: the checker on the 14 tracked `saves/`. Their writer
  is the bot's patched lab EXE, not the pinned original.
- `corpus-private-bundle-v1.json`: the checker on the 42 SAVs of the private
  migration bundle `ic2-research-inputs-20261021` (archive SHA-256
  `2bea418b…3008e`, 128/128 files verified 2026-10-21 in the cloud session).
  The groups are:
  - `source-saves`: 3 owner source saves.
  - `native-evidence`: 23 owner-retained original-Windows tax-case saves. The `N?I` files are transport copies of the exporter candidates, not original-writer output.
  - `research40-saves`: 4 crafted battle inputs and 12 original Wine battle outputs.

  Paths are relative to the bundle root. No bytes or values are copied, only
  sizes, SHA-256 hashes, counts and metric totals.

Reproduce (`field-map-v1.csv` SHA-256
`a09a5b5b5f5efcae54cce671f4ae7ece1e952a87ab9deff60c68b8e5a8f66e22`):

```bash
python3 scripts/sav_atlas_coverage.py --root . saves --out runs/experiments/data/run-exp-sav-atlas107/<new-name>.json
B=$HOME/ic2-inputs/ic2-research-inputs-20261021
python3 -I scripts/sav_atlas_coverage.py --root $B $B/source-saves $B/native-evidence $B/research40-saves --out runs/experiments/data/run-exp-sav-atlas107/<new-name>.json
python3 -m tests.test_sav_atlas_coverage
```

`--out` refuses an existing file. A re-run gets a new name, and the old
receipts are kept. No game was started and no SAV was written. There are no
binaries to upload: the inputs are hashed inside the receipts.

What the receipts do **not** show:

- Physical coverage (every byte belongs to a ledger row, and the serializer walk ends at EOF) is not semantic completion.
- That the UNKNOWN ranges are zero in every sampled file is not a default or a dead-field proof.
- Framing a crafted file shows that it frames. It does not show that the original accepts the file.
