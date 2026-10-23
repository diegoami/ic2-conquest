# Broad remake ↔ original save conversion: all 16 starts and strategic features

**Status:** [confirmed, partial], 2026-10-23. Wine observations and implementer
audit; no independent model review or native Windows acceptance.
**Task:** [conquest #153](https://github.com/diegoami/ic2-conquest/issues/153),
owner-authorized broad follow-up to the limited #151 experiment.

## Answer

**77 cases completed the full bidirectional sequence:** native JSON → actual
CLI export → independent policy check → original open/order/new save/fresh
process reopen → native import/reload/resume/order/re-export/policy check.
All selected original orders or explicit refusal controls were verified, and
all 77 fresh-reopen resaves were byte-identical to their preceding original
save. The original's first resave changed only bounded UI bytes, with no other
byte or parsed gameplay-field change from the exported input.

There were **78 scenario inputs**, including one additional synthetic
fleet-on-city overlap refused by the exporter. Together with eleven dedicated
converter/input controls, **12 refusals** produced no unsafe new output.
The 77 exported case inputs have **53 distinct SAV hashes**: some feature
cases intentionally share the same state and exercise different orders.

This is broad strategic conversion coverage, **not full game equivalence**.
Among 68 deterministic action comparisons, 64 match under the documented
normalizations/input alignment and four retain differences listed below.
Nine random combat/turn continuations are tested for playable conversion, not
equal outcomes. Known conqueror-history import loss is also reproduced.

## Actual coverage

The authoritative per-case table is
[`coverage-final.csv`](../runs/experiments/data/run-exp-sav-conversion-broad153/coverage-final.csv),
with source provenance, action, actual original save/turn, reopen result,
returned-remake action, policy result and differential count. Do not infer an
exercised action merely from a field being present in a save.

| Group | Cases / what was exercised |
|---|---|
| Human nation starts | All16: Rome, Carthage, Seleucid, Ptolemaic, Macedonia, Numidia, Gaul, Greece, Celtiberia, Illyria, Dacia, Bithynia, Galatia, Armenia, Media, Thracia. Alternating seeds7/11, one selected seed per nation. Movement where a suitable own army exists, tax otherwise; all16 returned/resumed/re-exported. |
| Progressed nations | Rome after6turns (Summer), Carthage12 (Autumn), Ptolemaic18 (Winter), Macedonia24 (next Spring/year). Each continued one turn in the instrumented original and returned. |
| Army organization | Whole-army split/join/transfer/disband; rename; unit split/join/disband; ordinary movement; a100000-troop army split;21combined-unit refusal. |
| Recruitment/economy | All5unit types; readiness18 mobilized into live quality4; queued disband;40-slot refusal; own and foreign-city supply purchases; army/fleet purse transfers; debt and tax0/40. |
| Fleets/cargo | Build; launched movement, repair, supply, split/join/transfer/scuttle;100ships accepted and101refused; embark/land; reversed army/fleet arrays; removing a fleet before a live cargo carrier. |
| Diplomacy/controllers | War and trade; peacetime alliance; refused wartime alliance and AI peace; ending trade; pending-offer notice plus explicit acceptance; two-human hotseat handoff. |
| Cities/combat/weather | Fortification; siege/capture; a native field-battle aftermath; a naval battle in original; eliminated-nation/conqueror state; Winter/rough-sea state and continuation. |
| Text/migration |23-character unit name and rename; generated mercenary alias; synthetic v4-shaped save through actual migrations. This is not validation of the owner's legacy files. |

Feature cases are mainly Rome, with explicit synthetic arrangements where
needed. They are not every action × nation × seed, long campaigns for every
nation, or every graphical/menu feature. The manifest labels naturally played
starts/progression separately from constructed native-model/JSON states.

Examples (run `run-exp-sav-conversion-broad153`): naval battle
`Q15359R.SAV`, turn0720; siege `Q15360R.SAV`, turn0720; field-battle-aftermath
continuation `Q15361R.SAV`, turn0721; hotseat `Q15357R.SAV`; exact turn for each
case is in the CSV. Reversed cargo landed via `Q15375R.SAV`, turn0720.
In `Q15377R.SAV`, turn0720, the first fleet has been scuttled and the surviving
carrier still references army13 correctly. Both imported/resumed/re-exported.

## Differences and boundaries retained

| Case | Remake versus original from the same converted state |
|---|---|
| F02 unit transfer | Recipient at(101,37) retains8moves in the remake; original sets it to0. Other compared game fields match. This is an action-level parity gap, not lost input bytes. |
| F04 LI split | Remake accepts splitting4800LI into two2400units; original refuses “too small.” Existing g2 research already establishes the original LI minimum6000. Retained first failed expectation, then explicit original-refusal control; F51 separately demonstrates a permitted5000HI split. |
| F09 mercenary hire | Native generates `Mercenary (label 1)` after alias normalization; original names the same label `Numidian`. Quantities/resources/other compared fields agree. |
| F51 HI split name | New regular name is `7th Guards Battalion` in native, `7th Guards  Battalion` in original (two spaces). Split succeeds in both. |
| F36 conqueror history | Source/native export and original retain Media's conqueror Rome; importing loses `ConqueredBy`, as already tracked by [remake #1351](https://github.com/diegoami/imperial_conquest_2/issues/1351). This is not counted as full-state equality. |

Source/import comparisons retain every raw native-state difference. RNG,
elapsed-turn counters and score baselines reset or are omitted as documented
in #151. Population is re-derived from cities, and covered-cell values are
reconstructed. The action comparison normalizes entity IDs by nation/location,
the documented mercenary alias, import-reset baselines/elapsed turn/RNG and
derived population/covered cells. It preserves unit order/text and all the
other compared game fields. Record-table order is separately compared; no pure
record-order permutation was observed in the completed action comparisons.

The recruitment driver specifies spinner **increments**, not absolute troop
counts; the original also automatically chooses a build port. Initial native
predictions with different quantities/port remain in the packet. Additional
`predict-matched-*` records use the actual observed quantity/port, without
repeating or replacing an original trial. Only those aligned comparisons
support the same-input action conclusions.

The pending-offer input displayed its correct Numidia notice unchanged.
Dismissing that notice does not accept trade; acceptance was then tested
explicitly through International Relations. The first incorrect autoaccept
expectation remains visible. The synthetic v4 migration intentionally starts
with an empty rough-sea overlay and removes the old `underSiege` members;
do not call that a byte-identical migration or an owner's save validation.

## Builds, artifacts and audit

- Effective production source: remake
  `ae614899d63ac721ee46d1e3213191fe1f43a676`, including quality4 fix PR1353.
  Read-only local base `a510c33` differs only in two production files; exact
  upstream blobs were substituted at compilation. Full source/blob/assembly
  hashes and targets are retained; this is not an official binary identity.
- Unmodified original SHA256
  `9d753d5de78801f2368d06125cc87f296b92f671b686c39fd6ac149838ebba31`
  in68successful cases. Nine combat/turn cases use instrumented seed/rollingsave
  SHA256 `354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f`,
  startup seed12345. Wine10.0, private prefix/display153,1280×1024, DejaVu Sans;
  every process fingerprint is in `environment.jsonl`.
- [Evidence packet](../runs/experiments/data/run-exp-sav-conversion-broad153/):
  `comparison-final.json`, `coverage-final.csv`, `validation-final.json`, full
  commands/stdout/stderr, live attempts, reviewed recoveries and manifests.
  Final audit:77roundtrips +12refusals,7check groups,2754artifact hash checks
  across selected saves and four retained local archives. It reports the four
  action differences instead of declaring all features equivalent.
- [Complete private artifact bundle](https://drive.google.com/file/d/16xF3L8qDSFcotMLhA5yOon2Rqm56gJXc/view):
  `batch-final.tar.gz`,21030521bytes,900files, SHA256
  `35db99998eb18955469200eb3af755d0abc6cf980cc5f9dd38a13f43905688c1`.
  [Drive folder](https://drive.google.com/drive/folders/1PwRAw0xg4WKp5MpgpcRO3Fg6B4H5dnmn)
  holds all completed batches. No EXE/DAT/prefix or owner input is in the
  bundle. Upload metadata confirms size/destination; remote download hashing
  was not performed. An early partial batch03 upload was detected by size
  readback, retained as `INCOMPLETE-do-not-use`, and separately uploaded in full.

All failed expectations, UI-helper failures and orchestration errors remain.
Supply controls replaced stale coordinates; Unicode caption reads replaced
single-character ANSI reads; foreign supplies explicitly committed Buy supplies.
The refused F55 fleet/city overlay and missing-input attempt remain; F56 is a
separate valid adjacent-sea compaction case. No original save was overwritten
or deleted. The original processes were restarted after explicit SaveAs;
normal UI Exit shutdown was not tested. No remake source was modified.

## What this does not settle, especially #1355

This packet does **not** establish Computer general battle-outcome equivalence.
Nine random continuations have different random streams and AI paths; they
are conversion/continuation checks. Tactical native save export is explicitly
refused (`OPEN_BATTLE` from a genuine saved tactical battle).

The owner's [remake #1355](https://github.com/diegoami/imperial_conquest_2/issues/1355)
reports a Ptolemaic–Seleucid Computer general outcome gap after exchange. That
is a separate, real player-visible issue. It is not explained away by these
round trips or automatically attributed to RNG. The supplied private
`saveyy` reproduction is tracked in [conquest #154](https://github.com/diegoami/ic2-conquest/issues/154):
compare actual battle-entry armies, settings, placement and first divergent
decisions/exchanges before assigning a cause. Those owner files are not part
of this generated-input artifact bundle.

Native Windows acceptance, the owner's twelve-input manifest, exhaustive state
combinations, original-battle import fidelity and independent review remain
outside this result. Conquest #99's owner gates remain open. Research should
consolidate this as broad **bounded strategic Wine conversion** with the
reported parity gaps, not a blanket fidelity or battle-readiness verdict.
