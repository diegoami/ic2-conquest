# Issue #107 SAV atlas: field map and coverage receipts

Task: [conquest issue #107](https://github.com/diegoami/ic2-conquest/issues/107). Finding:
[original SAV semantic atlas](../../../../findings/2026-10-21-original-sav-semantic-atlas.md).

- `field-map-v6.csv` (**authoritative**, increment 6): v5 plus the native
  fleet-leftover evidence of [run-exp-sav-fleetmoves107](../run-exp-sav-fleetmoves107/README.md).
  The checker defaults to v6.
- `field-map-v5.csv` (increment 5): v4 plus residue,
  text-tail and history notes. Value policies changed: route → `LIVE_AND_RESIDUE`,
  INERT → `PRESERVE_OR_ZERO`, `CITY.allegiance` → `HISTORICAL_PROFILE`. Classes
  are unchanged.
- `field-map-v4.csv` (increment 4): v3 with the native
  evidence of [run-exp-sav-inert107](../run-exp-sav-inert107/README.md) added
  to the INERT and fleet-route rows (evidence and uncertainty only; classes
  unchanged, so the v3 corpus receipts still apply).
- `field-map-v3.csv` (increment 3): v2 plus a `readers`
  column (from `asm-index-v2.csv`, saver excluded) and `BATTLE.side` resolved
  as the side to move. Classes: 79 CONFIRMED, 31 CONTEXTUAL, 3 INERT, 0 PARTIAL,
  0 UNKNOWN. `scripts/sav_atlas_coverage.py` defaults to v3 (`--field-map`
  selects v1 or v2).
- `field-map-v2.csv` (increment 3, superseded by v3): v1's rows and columns
  plus `start_value` (DAT, NewGame or BSS zero), `writers` (from
  `asm-index-v2.csv`, loaders excluded) and `uncertainty`. It adds the class
  `INERT`: no instruction reads or writes the bytes except the SAV
  loader/saver; they are not initialised and are carried from the loaded file.
  Classes: 78 CONFIRMED, 31 CONTEXTUAL, 3 INERT, 1 PARTIAL, 0 UNKNOWN.
- `field-map-v1.csv`: the first ledger, kept unchanged. 113 rows over 14 record
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

- `access-index-v1.csv`, `access-refs-v1.jsonl`, `access-summary-v1.json`: the
  static reader/writer index from `scripts/sav_atlas_access.py`, run on the
  pinned `all_app_functions.txt` (SHA-256 `2018c205…87d8`). It holds one row per leaf
  field with its writers, readers and escapes (`function@address`), one JSON line
  per hit (function, address, source line number, kind, form and fields; no
  source text), and a summary with the escape (seed/arg) and pointer frontiers.
  It is literal-address resolution only, so it does not close alias, escape or
  indirect-call paths. `access-index-v1.csv` has CRLF line ends (Python csv default at
  the time), kept as measured; `.gitattributes` exempts it from `git diff --check`.

- `asm-index-v1.csv` / `-v2.csv`, `asm-refs-*.jsonl`, `asm-summary-*.json`: the
  machine-code index from `scripts/sav_atlas_asm.py` (capstone) on the pinned
  EXE (SHA-256 `9d753d5d…ba31`). It covers the 10 functions that are absent
  from the decompilation, among them the DAT loader `0x4481A0`, the SAV
  loader `0x4487C4` and the NewGame initialiser `0x448AA4`. v2 fixes one
  thing: v1 credited a block transfer that spans several scalar fields to
  the first field only. The refs hold addresses, classes and field ids, never
  code bytes. Hits below `0x436000` (library code) are listed in the summary,
  not indexed.
- `asm-dispscan-v1.json`: every memory operand whose displacement falls in
  the inert nation ranges (and two control fields), with any base register.
- `init-provenance-private-bundle-v1.json`, `init-provenance-public-v1.json`:
  from `scripts/sav_atlas_init.py`.
  - The DAT layout is checked against the loader's instruction bytes, and the
    36 reads sum to the 140,706-byte DAT.
  - The 48 NewGame colour constants are extracted.
  - Per group, the receipt has per-check equal/total counts against the DAT
    and NewGame values, with contrast fields. It holds counts only.
- `corpus-public-v2.json`, `corpus-private-bundle-v2.json`, `corpus-public-v3.json`,
  `corpus-private-bundle-v3.json`: the coverage checker with ledgers v2 and v3.

Reproduce (`field-map-v1.csv` SHA-256
`a09a5b5b5f5efcae54cce671f4ae7ece1e952a87ab9deff60c68b8e5a8f66e22`):

```bash
python3 scripts/sav_atlas_coverage.py --root . saves --out runs/experiments/data/run-exp-sav-atlas107/<new-name>.json
B=$HOME/ic2-inputs/ic2-research-inputs-20261021
python3 -I scripts/sav_atlas_coverage.py --root $B $B/source-saves $B/native-evidence $B/research40-saves --out runs/experiments/data/run-exp-sav-atlas107/<new-name>.json
python3 -m tests.test_sav_atlas_coverage
python3 scripts/sav_atlas_access.py --source $B/decompile/all_app_functions.txt --out-dir runs/experiments/data/run-exp-sav-atlas107 --tag <new-tag>
python3 -m tests.test_sav_atlas_access
pip install capstone
python3 scripts/sav_atlas_asm.py --exe "$B/original/Imperial Conquest 2.exe" --decompile $B/decompile/all_app_functions.txt --out-dir runs/experiments/data/run-exp-sav-atlas107 --tag <new-tag> [--field-map ...v1.csv]
python3 scripts/sav_atlas_asm.py ... --tag <new-tag> --disp-scan NATION.unknown27 NATION.unknown1 NATION.unknown3 NATION.hints NATION.human
python3 -I scripts/sav_atlas_init.py --exe "$B/original/Imperial Conquest 2.exe" --dat "$B/original/Imperial Conquest 2.dat" --root $B $B/source-saves $B/native-evidence $B/research40-saves --out runs/experiments/data/run-exp-sav-atlas107/<new-name>.json
python3 -m tests.test_sav_atlas_asm; python3 -m tests.test_sav_atlas_init
```

Note: `asm-*-v1` ran with ledger v1 as its field map, and `asm-*-v2` with v1 as
well (the v2 ledger was built from it). The offsets are identical in v1 and v2.

`--out` refuses an existing file. A re-run gets a new name, and the old
receipts are kept. No game was started and no SAV was written. There are no
binaries to upload: the inputs are hashed inside the receipts.

What the receipts do **not** show:

- Physical coverage (every byte belongs to a ledger row, and the serializer walk ends at EOF) is not semantic completion.
- That the UNKNOWN ranges are zero in every sampled file is not a default or a dead-field proof.
- Framing a crafted file shows that it frames. It does not show that the original accepts the file.
