# Original SAV semantic atlas: whole-file scope and current evidence baseline

**Status: research umbrella and consolidation baseline; not a claim that every
SAV meaning is solved.** Owner requested one broad issue to establish exactly
what is stored in original-game SAV files and record the results in findings.
Track the work in [conquest issue #107](https://github.com/diegoami/ic2-conquest/issues/107).
Under the session-led workflow (owner, 2026-10-21) review is optional and
chosen per increment; no review of this entry has been performed yet.
This entry is the living index for that issue. New evidence should update its
field ledger and unresolved register, rather than restart overlapping probes.

## The question

For the declared original executable/data profile, identify every stored field,
bit range, contextual union and retained byte: its representation, meaning,
units, readers/writers, initialization and lifecycle. Account for active and
inactive state, history, presentation settings, tombstones and text tails.
Identify important runtime-only state separately. Decoding an offset is not
the same as proving its meaning or a safe value for a new campaign.

The original semantic dictionary is the primary deliverable. Exporters and
native-JSON converters consume that evidence; their success/failure does not
define the meaning of original fields. A narrow source-bound edit and a fresh
native state without original provenance are different reconstruction problems.

## Existing work: consolidate, do not restart

- [Conquest #99](https://github.com/diegoami/ic2-conquest/issues/99) and
  [research #37](https://github.com/diegoami/imperial-conquest-2-research/issues/37)
  retain the SAV/export evidence and native-validation history.
- [Research #47](https://github.com/diegoami/imperial-conquest-2-research/issues/47)
  already owns whole-program access analysis for the 31 UNKNOWN nation byte
  positions and new-record/residue/history gaps. It is a workstream of this
  whole-file umbrella, not a reason to open another duplicate unknown-byte task.
- The canonical research [serializer layout](https://github.com/diegoami/imperial-conquest-2-research/blob/51c98f1f8903822af1aca3bf2d876047bf1b7a8b/docs/reports/decompiled-sav-file-layout.md),
  nation matrix and bounded tax/lineage reports are starting evidence. The local
  [parser layout notes](../docs/sav-layout-notes.md) are a historical summary;
  later reviewed corrections override stale labels in that summary.
- Remake T184–T186 remain separately reviewed consumers. Creating this umbrella
  does not enable a writer, approve a new game run or dispatch implementers.

## Whole-file coverage skeleton

The existing read/write evidence establishes this block sequence. This table
accounts for framing, not the semantic completeness of each copied record.
`A`, `F` and `newsIndex` are values read from the file, with bounds and malformed
input handling to be recorded for the declared profile; do not silently clamp
invalid counts to make a file fit.

| Block | Stored extent | Semantic work to consolidate/check |
|---|---:|---|
| Map | 320 × 140 × 2 = 89,600 bytes | Terrain, weather, ownership/size markers, covered-cell relationships; stored overlays versus live record lookups. |
| Cities | 334 × 34 = 11,356 bytes | Every typed field, name buffer/tail, ownership versus allegiance, populations, supplies, fortification state. |
| Army count | 2 bytes | Signedness, limits, counted tombstones and relocation timing. |
| Armies | A × 656 bytes | 16-byte header and 20 × 32-byte slots; all live fields, inactive residue, text, creation/deletion/reordering. |
| Fleet count | 2 bytes | Bounds, counted tombstones and compaction. |
| Fleets | F × 26 bytes | Current versus destination XY, launched/building unions, cargo index, underlay, lifecycle and retained bytes. |
| Nations | 16 × 1,172 = 18,752 bytes | Economy, history, city lists, queues, relations, palette, UI/controller settings and unresolved regions. |
| Mercenary pool | 50 × 12 = 600 bytes | Offers, sentinels, inactive contents and template dependencies outside the SAV. |
| News index | 2 bytes | Most-recently-used index, not a count of records. |
| News slots | (newsIndex + 1) × 61 bytes | Shift behavior, encoding, terminator, tails and bounds. |
| Trailer | 55 bytes | Turn order, pending offer, current nation/seat, calendar, geometry and battle flag. |
| Conditional battle | 2,105 bytes when battle flag set | 9-byte header, 40 × 44-byte slots and 14 × 12 × 2-byte icon grid; identify runtime state not saved. |

The trailer offset is computed from preceding counts/news. It is not generally
`file length - 55` when a battle block is present. Original human-controlled
File → Save As can produce battle saves; older “never present in normal saves”
prose must not erase that reviewed correction. This task includes the conditional
block rather than declaring the strategic subset to be the whole format.

## Increment 1: ledger v1 and physical coverage (2026-10-21)

The ledger now exists as [`field-map-v1.csv`](../runs/experiments/data/run-exp-sav-atlas107/field-map-v1.csv).
It has 113 rows over 14 record types, and each row has a stable ID, offsets,
width/type, a semantic class, a value policy, a runtime address formula and
evidence. The checker is
[`scripts/sav_atlas_coverage.py`](../scripts/sav_atlas_coverage.py), with the offline test
`python3 -m tests.test_sav_atlas_coverage`. Data:
[run-exp-sav-atlas107](../runs/experiments/data/run-exp-sav-atlas107/README.md).

- **Static tiling:** every record type's rows cover its stride exactly, with
  no gap or overlap; the unit-slot and battle-slot arrays nest. Nation rows
  equal the research37 nation-matrix-v2 ranges exactly.
- **Serializer order re-read** from the pinned source (`FUN_004484D0` save,
  `FUN_004487C4` load). Trailer = turn order 32 + offer 4 + current nation,
  seat, week, year, season (serialized from 0x4A0320, 0x4A0322, 0x4A0330,
  0x4A0332, 0x4A032E: season after year) + 8 bytes of main-form geometry + the
  battle flag = 55 bytes. The geometry words are left/top (form fields 9/10)
  and then rect[3]/rect[2] of the form's vtable+0x2C call. That call is read
  here as client height/width, but this is a Delphi-VMT inference, so the
  ledger marks it PARTIAL. The battle block is a 9-byte header serialized in
  the order 0x4A0B74, B76, B78, B7D (byte), B7A, followed by 40 × 44 slots and
  a 14 × 12 icon grid.
- **Corpus framing:** all 56 SAVs walk to exactly EOF ([public](../runs/experiments/data/run-exp-sav-atlas107/corpus-public-v1.json):
  14 tracked saves; [private bundle](../runs/experiments/data/run-exp-sav-atlas107/corpus-private-bundle-v1.json):
  3 source, 23 owner-retained Windows tax-case and 16 research40 battle saves).
  The 16 battle saves carry the 2,105-byte block. No file needed `len − 55`.
- **Byte metrics (private bundle, 5,573,142 bytes):** CONFIRMED 7.75 %,
  CONTEXTUAL 91.86 % (mostly map words and text-with-tail fields whose rule is
  known), PARTIAL 0.017 %, UNKNOWN 0.374 % (31 per nation record). Physical
  coverage is 100 %. **Semantic completion is not:** the CONTEXTUAL and
  CONFIRMED rows still need the per-field reader/writer/lifecycle columns of
  the dictionary row below. The class records the established meaning, not
  closure.
- **UNKNOWN31 samples:** no nation record of the 56 files has a non-zero byte
  in +450..46A, +46D or +491..493. This extends the earlier 224-record sample;
  it is not a dead-field proof (research #47 owns that).

New frontier rows found while consolidating:

- Fleet +4/+6 are named "route target" by the
  [transport lifecycle report](https://github.com/diegoami/imperial-conquest-2-research/blob/3a349c25f77f1c8816d1410cb2931dcd4b7e9426/docs/reports/2026-10-21-transported-army-coordinate-lifecycle.md)
  and are reset to −1 each fleet turn. Their writer set and their value while
  a fleet is building are not consolidated, so they are PARTIAL with
  value policy UNRESOLVED_REFUSE.
- Battle header +4 (side to move): the tactical sweep saw memory 0 against
  file 1 after a resume, which is still unexplained, so it is PARTIAL.
- **Non-serialized state:** both save and load set the words 0x4A0328 and
  0x4A032A to −1 after the transfer. The file can therefore never carry them;
  their meaning (probably the current army/fleet selection, matching the "sampled
  army/fleet selections = −1" observation of the tax cases) is not established here.
- The parser summary [`docs/sav-layout-notes.md`](../docs/sav-layout-notes.md)
  still carries superseded labels: fleet +4/+6 "unknown", nation +0x424 "unknown",
  +0x486/+0x488 "meaning unknown" and "battle block never present in a normal
  save". The ledger supersedes them, and the notes now point to it.

## Field identity and alias corrections already supported

Use stable IDs and retain the old name/correction record so future readers do
not rediscover or mix these meanings:

| Stored field/representation | Established distinction | Existing evidence |
|---|---|---|
| Army +8 | Covered map cell; -1 while aboard, not strategic morale. | [Unit-map/record report](https://github.com/diegoami/imperial-conquest-2-research/blob/51c98f1f8903822af1aca3bf2d876047bf1b7a8b/docs/reports/decompiled-unit-map-orders-and-record-fields.md). |
| Army +14 | Strategic morale, distinct from battle-slot morale. | Same record report and parser notes. |
| Fleet +0/+2 versus +4/+6 | Current XY versus route/destination XY. | Same record report; [transport lifecycle](https://github.com/diegoami/imperial-conquest-2-research/blob/3a349c25f77f1c8816d1410cb2931dcd4b7e9426/docs/reports/2026-10-21-transported-army-coordinate-lifecycle.md). |
| Fleet +20 | Build-city index while building versus condition after launch; not one timeless field label. | Same record report; SAV safety report below. |
| Fleet +22 / army +8 | Carried-army index versus embarked sentinel; an army-side fleet pointer must not be invented. | Transport lifecycle and SAV safety report. |
| Nation +048..2E3 | Live sorted owned-city index list, not an unnamed static block. | [SAV safety finding](2026-10-17-sav-export-live-regions-and-safe-rejection-policy.md). |
| Nation +434/+43C/+448 | Historical starting comparison values, not current-value duplicates. | Same safety finding. |
| Nation +44E..44F | Two-byte conqueror nation field; “conqueror byte” is an imprecise description. | Nation matrix and original record layout. |
| Nation +486/+488 | Viewport Y/X, not unknown selected-army coordinates. | Nation matrix and [tax/alias evidence](2026-10-18-sav-export-bound-tax-subset-and-binary-alias-evidence.md). |
| Tactical grid | Stored icon/occupancy code, not a direct slot ID or a universally regenerated view. | [Crafted grid evidence](https://github.com/diegoami/imperial-conquest-2-research/blob/1c203b748ff7d067fb26c323d7dd4cdfc244fe68/docs/reports/2026-10-21-crafted-battle-grid-movement-and-line.md). |
| Unit/name/news tails | Retained historical bytes after logical emptiness/NUL, not automatically padding or extra named fields. | [Lineage finding](2026-10-18-sav-export-unknown-access-and-record-lineage-boundaries.md). |

These are examples to seed the dictionary, not a substitute for an exhaustive
field-by-field pass. A field can be physically known but still lack a proved
fresh-state initializer, historic applicability or complete reader set.

## Unresolved register: what is actually still open

1. **31 UNKNOWN positions per nation record:** +450..46A (27), +46D (1),
   +491..493 (3). Across 16 nation records these repeat over 496 stored bytes.
   Do not call them the only unknown bytes of the entire SAV. Current samples
   and bounded non-access controls do not prove global padding/dead semantics.
2. **Whole-program access frontier:** computed pointers, wide/overlapping loads,
   indirect calls/vtables and relevant callers. A negative literal-offset search
   is a lead, not reader/writer closure. Track unresolved edges explicitly.
3. **Construction and inactive records:** new-army constructor writes 96/656
   bytes; fleet construction writes 10/26. Their retained 560/16 bytes are not
   validated new-record prototypes or automatically safe zeros. Completion,
   movement/destinations, deletion, reuse and text writers must be included.
4. **Lineage and relocation:** whole 32-byte unit slots and whole army/fleet
   records can move; indices and carrier links must follow. Original byte
   identity and semantic equivalence with canonical residue are different claims.
5. **History/profile applicability:** how a fresh campaign supplies historical
   baselines and conqueror state without copying an unrelated campaign. Same
   names/current totals or an EXE hash do not establish campaign provenance.
6. **Contextual encodings/domains:** signedness, sentinel conditions, bit fields,
   state-dependent unions, text codepage/byte limits and original overflow/wrap
   behavior. Observed UI values are not necessarily the full encoded domain.
7. **Cross-record invariants:** marker/underlay versus records, city lists and
   ownership/counts, recruitment destinations, compacted indices, carrying
   relationships and battle copy-in/write-back.
8. **Non-serialized dependencies:** RNG is not in the SAV. Do not identify a
   convenient unknown byte as the seed or promise future RNG equivalence.
   Identify other runtime flags/cursors/call history separately with evidence.

Keep artifact access and compatibility validation in separate columns. The
native tax-only 3/3 sequences and subsequent hash checks of owner-provided
copies are useful evidence for that bounded transformation, not a resolution
of these whole-file semantic questions. A private path problem is not a new
field-meaning problem and should not restart the semantic investigation.

## Required dictionary row

The machine-readable ledger should store, for every field/range:

- stable ID; parent block; file and runtime address formulas; count/stride;
  width, endianness, signedness and explicit bit/union interpretation;
- meaning/units; active-state condition; sentinel and observed/legal domains;
  confidence and corrected previous aliases;
- initializer, exact readers/writers, access widths, callers and lifecycle;
  remaining alias/call-graph frontier and proof scope;
- value policy: mapped live data, proved derivation, source-preserved history/
  residue, proved canonical initializer, or unresolved/refuse;
- source/EXE/DAT/input hashes; exact instruction/source/report references;
  immutable control/result links and private binary-artifact hashes;
- evidence class: static source/disassembly, original instructions under emulator
  with stubs stated, original Wine observations or native Windows observations;
  independent review and explicit untested cases.

Start from the existing [nation matrix](../runs/experiments/data/run-exp-sav-export37/nation-matrix-v2.csv),
not another competing set of guessed names. Expand the ledger to all blocks.
Store versioned field-map/access/lifecycle tables under a task-owned tracked
data path and link their authoritative versions here. Preserve original files,
all measured output versions and failed controls. Binary data stays private;
the findings/ledger contain facts, citations and scalar receipts, not source
dumps, owner JSON contents or original screenshots/executables.

Record opaque serialization, whole-record copying and actual value-influencing
reads separately. Save/load touching every byte does not give each byte a
gameplay meaning. A span proved irrelevant to gameplay can still matter for
exact byte identity; those are separate conclusions and value policies.

## Execution and completion contract

First consolidate existing reviewed facts and stale labels; then establish
physical byte/bit coverage; resolve named semantic holes using source access
proof and discriminating controls; independently review each bounded increment
and reconcile it into the SAME map. Existing research #47 is the deep unknown/
residue stream. Use issue #107's checklist for other discovered holes rather
than proliferating equivalent tasks. No automatic child dispatch or new model
choice follows from this organizational document.

Separate two metrics:

- **Physical coverage:** every byte/bit belongs to a documented field, union or
  explicitly unresolved range in the declared format/profile; framing reaches
  the actual file end with conditional blocks accounted for.
- **Semantic completion:** meanings, active-state conditions, readers/writers,
  lifecycle and dependencies are proved at the declared scope. UNUSED/DEAD/
  PADDING classifications need whole-program proof boundaries. UNKNOWN rows
  count as physical coverage but remain blockers, not completed identification.

Close the umbrella only when reviewed evidence meets both metrics for its
explicit original EXE/DAT/profile and remaining uncertainty is not hidden in
defaults. If a broader conclusion cannot be proved, state the exact frontier
and a bounded supported profile/refusal; do not label the whole original format
“fully decoded” to unblock a converter. Exporter readiness, new native-state
outputs, original-game runtime acceptance and future behavior stay separate.

No game is launched by this plan. Future controls require their normal owner
coordination, unique copied/staged inputs, no interruption of play and no
overwrite/deletion of measured outputs. Measurements are committed/pushed as
they are made, after each batch and at least every 30 minutes. Record sources,
versions, failing attempts and review decisions in the issue and task notes.

## Input/version baseline and limitation

Current source baseline: conquest main
7fe20bedba0b9cdbb012b1b348c96507f6a65768. The existing semantic reports pin
all_app_functions.txt SHA-256
2018c205a4e4ea4a4079f2d166623fb571062832d76e19b72e11d1f0edac87d8,
original EXE9d753d5de78801f2368d06125cc87f296b92f671b686c39fd6ac149838ebba31
and DAT94d0ccfc67148d727de4c4e60aefc3c53ba9e67775bd689f0fcb2e23c12e5fbd.
Use actual hashes/profile evidence rather than infer a product version from a
filename. Patched/lab builds and other originals need explicit applicability.

This entry consolidates reviewed evidence and specifies the broad research
deliverable. It does not supply new whole-program analysis, resolve UNKNOWN31,
perform native validation, enable a general writer or change another repo.
