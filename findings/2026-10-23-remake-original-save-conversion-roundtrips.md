# Remake → original IC2 → remake: six scenarios, seven Wine sessions

**Status:** [confirmed, partial], 2026-10-23. Original-program observations under
Wine/Xvfb; not native Windows acceptance or a lossless-conversion claim.
**Task:** [conquest #151](https://github.com/diegoami/ic2-conquest/issues/151),
explicitly approved by the owner in the desktop session.

## Answer

Six distinct native saves exported through the remake CLI, opened in the
unmodified original, accepted a tax order, saved to new files, and reopened in a
fresh original process. All six reopened resaves were byte-identical to the
original-written preceding save. The recruitment/fleet-order scenario also
completed one turn in the instrumented original: `AUTO0721.SAV`, Spring week 3,
270 BC. Its explicit SaveAs and fresh-reopen resave were byte-identical too.

All seven original-written results imported into the remake, survived native
save/reload, resumed as playable sessions, accepted tax 27, and re-exported.
The returned exports passed the conquest policy checker; among the fields read
by conquest's independent Python parser, the only difference from each
original-written result was the requested tax change, 26 → 27.

Native metadata and derived statistics differ across the conversion boundary;
the measured differences are listed below. This evidence supports these tested
strategic states, not general export readiness or closure of #99.

## Revisions, runtime and artifacts

- Conquest base: `e05570573b02ebb91b41b6e2d80d7f4ac2dedaff`.
- Remake: `a510c33f0aaa2998ff1186127ff18eb13f489496` (PR #1350).
  No source or build products were written into that checkout. Its assemblies
  were built into this experiment's ignored artifacts directory.
- .NET SDK 10.0.401; Wine 10.0 (Ubuntu package
  `10.0~repack-12ubuntu1`); private Xvfb display, 1280×1024, DejaVu Sans,
  no Liberation fonts. Full fingerprints are in `environment.jsonl`.
- Unmodified `Imperial Conquest 2.exe` SHA256:
  `9d753d5de78801f2368d06125cc87f296b92f671b686c39fd6ac149838ebba31`.
- Instrumented `Imperial Conquest 2 fast rollingsave seed.exe` SHA256:
  `354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f`.
  Only the seventh session uses it, with startup seed 12345.
- Tracked commands, stdout/stderr, hashes, comparisons and validator:
  [`runs/experiments/data/run-exp-sav-conversion-roundtrip/`](../runs/experiments/data/run-exp-sav-conversion-roundtrip/).
  Final comparison: `comparison-v6.json`; audit: `validation-v2.json`.
- Binary/private artifacts:
  [Drive IC2/artifacts/run-exp-sav-conversion-roundtrip](https://drive.google.com/drive/folders/1OQWVtWzeN6k-_EgfU_3U_vFa4MjmXfqv).
  [Complete bundle](https://drive.google.com/file/d/10BGy85kM1jUA7iXCdvwzkYXcc1z6fZzQ/view),
  `batch2-complete.tar.gz`, 3,118,135 bytes, 85 files, SHA256
  `c21c8607eb1def47b7ea592d2494dd5b9a72ef9dea0cf1342b26205b94fdd91f`.
  The earlier `batch1-conversions.tar.gz` and both manifests remain available.
  Upload completion, file size and parent folder were verified with Drive
  metadata readback; a remote download/hash comparison was not performed.
  No EXE, DAT or prefix was included in either archive. No release was created:
  `IC2_RELEASE_TOKEN` is absent. Drive storage succeeded.

## Scenarios and original-program checks

The five gameplay-derived saves use a fresh classical-mediterranean /
classical-faithful session, seed 7, human Rome. The initial snapshot is the
first human Rome seat, after any preceding AI seats. All have 334 cities and
no eliminated nation or open battle. The additional cargo case is explicitly
synthetic, constructed through public native model records rather than play.

| Case | Native state | Armies / fleets / building / cargo | Original saves: immediate / order / fresh reopen | Original turn |
|---|---|---|---|---|
| A | Initial human turn | 14 / 2 / 0 / 0 | `P151AI.SAV` / `P151AO.SAV` / `P151AR.SAV` | 0720 |
| B | Tax25; 1,000 HI queued at Rome; 10 ships ordered at Neapolis | 14 / 3 / 1 / 0 | `P151BI.SAV` / `P151BO.SAV` / `P151BR.SAV` | 0720 |
| C | Same game, 6 turns later | 13 / 4 / 2 / 0 | `P151CI.SAV` / `P151CO.SAV` / `P151CR.SAV` | 0726 |
| D | 12 turns later, including launched construction | 17 / 4 / 2 / 0 | `P151DI.SAV` / `P151DO.SAV` / `P151DR.SAV` | 0732 |
| E | 24 turns later | 15 / 6 / 1 / 0 | `P151EI.SAV` / `P151EO.SAV` / `P151ER.SAV` | 0744 |
| F | Synthetic Rome army aboard a launched fleet | 14 / 2 / 0 / 1 | `P151FI.SAV` / `P151FO.SAV` / `P151FR.SAV` | 0720 |
| G | B again, instrumented original, then one End turn | 14 / 3 / 1 / 0 initially | `P151GI.SAV` / `P151GO.SAV`; `P151GT.SAV` / `P151GR.SAV` after turn | 0720 → 0721 |

For each, the actual `IC2.Cli --export-sav <native.json> --output <new.sav>
--template <original.sav>` interface wrote the input. The explicit template was
`run0-start-AUTO0720-seed12345.SAV`, used by the converter for interface settings.
All six exports passed `scripts/sav_export_policy_check.py` without `--source`.
The original was run in a copied private prefix without copying existing saves.
No original/owner save or measured output was overwritten or deleted.

All seven immediate original saves differ from their exports by exactly one
byte at the current nation's `+0x482`, inside `NATION.infowin` geometry
(atlas v13). Nothing else in the file differs. The original tax order changes
exactly one byte at `NATION.tax`, `+0x44A`; requested values are checked in the
save. Every fresh reopen produces an exactly matching file. Processes were
restarted after explicit SaveAs using the isolated wineserver; UI Exit/clean
application shutdown was not tested.

F's native army and fleet use matching owner, coordinates and reciprocal
references. `P151FR.SAV` retains army cell −1 and the carrier's army index 0.
It does not establish a natural embark/disembark sequence or cargo combat.

G advances exactly one calendar tick, 0720 → 0721. Its `AUTO0721.SAV`,
`P151GT.SAV` and `P151GR.SAV` all hash to
`beaf8057c6d5bd922a2511e24752e88c1f7b328c650b45ce43e311a59adfd264`.
This is continuation evidence in the instrumented original, not matching
future AI or combat outcomes between the two engines.

## What does not round-trip identically

`comparison-v6.json` compares all native state members after normalizing entity
IDs by record index and the documented mercenary-name alias, excluding RNG and
a launched fleet's native-only build-city metadata. It retains every observed
difference instead of declaring equal state:

| Source snapshot | Native field differences |
|---|---:|
| Initial | 11 |
| Orders | 12 |
| After 6 turns | 52 |
| After 12 turns | 55 |
| After 24 turns | 57 |
| Synthetic cargo | 11 |

The differences fall only in `Calendar.TurnIndex`, nation `Population`,
`PopulationAtStart`, `TreasuryAtStart`, `CityCountAtStart`, and fleet
`CoveredTileCode`. Exact paths, values and per-class counts are retained.
The importer starts elapsed turns at 0, keeps the actual BC/season/week, resets
the score baselines to import time and recomputes population from owned cities.
The native snapshots' population counters can already lag city ownership.
Several native fleets have a null covered-cell value where import reconstructs
sea code 0. Those are measured normalization boundaries, not silent equality.

Original SAV has no recoverable RNG stream. The importer supplies scenario seed
270; after the returned remake's accepted tax order the root seed is
11400714819323198755. This is exactly one normal `CommandDispatcher` advance
(`RngStreams.GoldenGamma`), even though the tax handler needs no random draw.
It is not original/remake RNG continuity.

Known upstream conqueror-history import loss remains tracked in
[remake #1351](https://github.com/diegoami/imperial_conquest_2/issues/1351).
None of these source snapshots has an eliminated nation, so this experiment
does not exercise or resolve that defect.

## Refusals, audit and remaining scope

- `improved` ruleset: actual CLI returns 2, `UNSUPPORTED_RULESET`, no SAV written.
- Existing destination: actual CLI returns 2, `Destination already exists`;
  SHA256 of the earlier export is unchanged.
- Final audit: 8 check groups pass, including 164 per-artifact SHA256 checks
  across the two retained bundles, all seven session receipts, the precise
  original byte differences, cargo references and all return continuations.
- Infrastructure failures remain recorded: redirected CLI assemblies initially
  lacked their `IC2.sln` ancestor; experiment-only read-only layout links fixed
  that. Initial checker calls omitted required `--out`; corrected invocations
  were separately retained. The first audit wrongly expected an accepted
  command to leave RNG unchanged; `validation-attempt-v1.json` records that
  error and the source-backed correction. No game trial failed or was rerun
  to hide a result.
- This is implementer validation, without an independent model review. It does
  not cover the owner's twelve JSON files, format-4 migration, native Windows,
  hotseat, pending offers, all refusal classes, battle saves, eliminated nations,
  all seeds, or naturally played cargo loading/landing. #99's owner gates remain.

Research can consolidate the result as **bounded Wine acceptance and playable
bidirectional strategic conversion**, keeping the normalization and untested
cases explicit.
