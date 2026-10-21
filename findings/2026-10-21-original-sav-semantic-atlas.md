# Original SAV semantic atlas: whole-file scope and current evidence baseline

**Status: research umbrella and consolidation baseline; not a claim that every
SAV meaning is solved.** Owner requested one broad issue to establish exactly
what is stored in original-game SAV files and record the results in findings.
Track the work in [conquest issue #107](https://github.com/diegoami/ic2-conquest/issues/107).
Under the session-led workflow (owner, 2026-10-21) review is optional and
chosen per increment; no review of this entry has been performed yet.
This entry is the living index for that issue; its authoritative ledger is
[`field-map-v2.csv`](../runs/experiments/data/run-exp-sav-atlas107/field-map-v2.csv) (increment 3). New evidence should update its
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
  increment 2 below identifies them as the selected army and the selected fleet.
- The parser summary [`docs/sav-layout-notes.md`](../docs/sav-layout-notes.md)
  still carries superseded labels: fleet +4/+6 "unknown", nation +0x424 "unknown",
  +0x486/+0x488 "meaning unknown" and "battle block never present in a normal
  save". The ledger supersedes them, and the notes now point to it.

## Increment 2: static reader/writer index (2026-10-21)

[`scripts/sav_atlas_access.py`](../scripts/sav_atlas_access.py) resolves every
literal address in the pinned decompilation that falls in a serialized runtime
table to a ledger field. The field offset is (address − base) mod stride, plus
any constant inside a following `[...]`, scaled by stride ÷ index multiplier.
Two ambiguity rules apply:

- A label just below a table base counts as that table's record −1 only when
  the expression is indexed. This is Ghidra's `F − 1` form; a constant label there is
  the previous table's.
- An index multiplier selects the table whose stride it divides.

Each hit is classed write, read or escape. An escape is an address that is
taken: a **seed** stores it in a pointer variable, and an **arg** passes it to
a call. Offline test: `python3 -m tests.test_sav_atlas_access`, 16 synthetic
cases. Outputs: [access-index-v1.csv](../runs/experiments/data/run-exp-sav-atlas107/access-index-v1.csv),
[summary](../runs/experiments/data/run-exp-sav-atlas107/access-summary-v1.json) and per-hit
refs, which hold function, address, line and class only, never source text.

- **Controls:** the index reproduces three writer sets from the reviewed
  reports exactly.
  - `FUN_0044A004` (fleet order) writes fleet +8/+10/+18/+20/+22, F++ and the treasury.
  - `FUN_0044A050` (launch) writes +10/+14/+16/+20/+22/+24.
  - `FUN_00437DE4` (battle copy-in) writes army morale +14, both pause settings, the battle flag, the side and the counter.

  A first version misattributed `0x4A031C` and the `F − 1` labels. Those
  faults were fixed before the recorded run and are what the two ambiguity
  rules address.
- **Totals:** 2,632 literal hits (350 write, 1,847 read, 435 escape), 0
  unresolved offsets, and 114 multi-field accesses (for example x,y read as
  one dword). 82 of the 111 leaf fields have a literal writer.
- **The 29 fields with no literal writer** are written by paths this scan
  cannot attribute:
  - string copies (city, nation, leader, unit and news text);
  - whole-slot or whole-record moves (unit label and quality, battle-slot copy-in through pointer seeds);
  - DAT load and NewGame (colours, the 270 BC baselines, turn order, mercenary fill);
  - pointer seeds (fleet x).

  These are the next per-field step, not dead fields.
- **Fleet +4/+6 (PARTIAL):**
  - `FUN_0044D9A8` passes `&fleet[i]+4` as the out-pointer `param_4` of `FUN_0044CD08`, which ends with a 4-byte store `*param_4 = …`. That is the route target written as one x,y dword.
  - `FUN_0044DBA8` passes the same address as `param_3`, which is a read
    (corrected in increment 3: `param_3` is written too).
  - +6 has no literal access of its own because it is reached only through this dword.

  The per-turn −1 reset reported earlier is still not located; it is in the pointer frontier
  (located in increment 3: the round tick at `0x451723`).
- **UNKNOWN31:** there is still **no** literal access to +450..46A, +46D or
  +491..493 in any of the 16 nation records, including indexed forms. The
  earlier inventory covered nation 0 only. This scan is not closure: 36
  functions seed a nation-record pointer, 44 pass a nation address on, and 35
  functions index army, city, fleet or nation strides through pointer
  variables (57 lines). Research #47's whole-program pass has to clear those
  before any dead-field claim.
- **Runtime-only globals:** `0x4A0328` holds the selected army and `0x4A032A`
  the selected fleet ([fleet-orders-live](https://github.com/diegoami/imperial-conquest-2-research/blob/16f019397e65ba521bbcee7acea2a7d2c9bd7c93/docs/reports/2026-10-02-fleet-orders-live.md)).
  Save and load reset both to −1, which matches the tax cases' "selections −1"
  observation. `0x4A031C` is a further unserialized global next to the news
  index; it is not identified here.

## Increment 3: machine-code index, initialisation provenance and ledger v2 (2026-10-21)

**The authoritative ledger is now
[`field-map-v2.csv`](../runs/experiments/data/run-exp-sav-atlas107/field-map-v2.csv)**
(v1 kept beside it, unchanged). It adds three columns to every row:
`start_value` (DAT, NewGame or BSS zero), `writers` (every writing function
the machine-code index found, loaders excluded) and `uncertainty`. Classes:
78 CONFIRMED, 31 CONTEXTUAL, 3 INERT, 1 PARTIAL, **0 UNKNOWN**. No game was
run and no SAV was written; no review was run on this increment.

**The 29 fields without a literal writer, verified.** `access-index-v1.csv`
has 111 leaf rows and 29 with `n_write = 0`, as reported. They were not
dead: most of their writers are in code the decompilation does not contain.

- **Decompilation gap.** Of the application's direct call targets, 7 have no
  decompiled body, and 3 class methods are missing as well. Three of the
  missing functions write the SAV tables wholesale: the DAT loader
  `0x4481A0`, the SAV loader `0x4487C4` and the NewGame initialiser
  `0x448AA4`. Both `TPremierForm.InitialiseForm` (program start, `0x45A935`)
  and `TPremierForm.NewGame` (`0x45AA2D`) call the DAT loader and then the
  initialiser. The split-fleet creator `0x447C04` is also undecompiled.
- **Machine-code index.**
  [`scripts/sav_atlas_asm.py`](../scripts/sav_atlas_asm.py) disassembles the
  pinned EXE (capstone) function by function. It follows literal
  displacements, registers and stack slots holding a table address, push/pop,
  forward branches, StrCopy/StrCat/Move/FillChar/word-swap helpers (each
  identified from its own code), TStream `Read`/`Write` (VMT slots 0/4) and
  `rep movs/stos`. Test: `python3 -m tests.test_sav_atlas_asm`, 9 hand-encoded
  cases. Run [`asm-index-v2.csv`](../runs/experiments/data/run-exp-sav-atlas107/asm-index-v2.csv)
  (v1 attributed a multi-field scalar block to its first field only; v2
  fixes that, and both are kept): 3,414 hits, every one of the 111 leaf fields
  has a writer.
  - **Control:** the index reproduces 250 of the 252 v1 decompile writer
    pairs. The other 2 are v1 false positives found by reading the lines:
    `TAreaMap.ToggleMap` toggles `NATION.areamap_toggle`, not the current
    nation, and `0x43CF3C` writes the info-text buffer at `0x49F00C + 61k`, not a
    battle slot.
  - **Heuristics, stated:** facts flow in linear order, forward branches
    carry them, and after a `jmp` only callee-saved registers and stack slots
    are kept (loop bodies entered from the bottom). An index term scaled by the
    stride is taken as a whole number of records. Register-argument escapes are
    over-approximate (a stale `ecx` passed to a scalar function is listed), so
    an escape is a lead, not a write. Hits below `0x436000` (System/VCL, where
    only inline data decoded as code matched) are listed, not indexed.
- **DAT layout, complete.** The DAT loader's 36 TStream reads consume the
  140,706-byte DAT exactly.
  [`scripts/sav_atlas_init.py`](../scripts/sav_atlas_init.py) checks each read's
  destination and length against the EXE's instruction bytes; test
  `python3 -m tests.test_sav_atlas_init`. The DAT holds the map, the 334 cities,
  15 armies, 2 fleets and 16 nation records of 1,055 bytes from DAT 0x1B100
  (the offset research found independently). Each nation record holds name,
  relations, neighbours, city list, recruitment, wealth, treasury, unity,
  mobilisation, capital, cities, tax, tax base and conqueror. They are followed
  by 14 constant tables that are not saved, the 52 × 20-byte mercenary
  label-name table, the 251-record mercenary pool (templates 0–200, live slots
  201–250), the 16 × 12 × 26-byte leader-name table and the 40 news slots (27
  texts).
- **Corpus provenance** ([private](../runs/experiments/data/run-exp-sav-atlas107/init-provenance-private-bundle-v1.json),
  [public](../runs/experiments/data/run-exp-sav-atlas107/init-provenance-public-v1.json); 56 saves,
  counts only). Every check holds in every file, and the contrast fields
  that change in play (city owner and population, current wealth,
  treasury and cities) differ in many files. The checks:
  - city name (all 14 bytes), x, y and allegiance equal the DAT;
  - nation name equals the DAT;
  - wealth0/treasury0/cities0 equal the DAT value;
  - the leader is one of its nation's 12 DAT names;
  - the colours equal the 48 NewGame constants;
  - the turn order is a permutation;
  - every filled merc slot's (x, y, label, type) equals a template's;
  - fresh saves reproduce the 27 DAT news texts byte for byte.

**What each of the 29 is.** The full text is in the ledger; in short:

| Fields | Writers and lifecycle | Class |
|---|---|---|
| CITY.name, x, y, allegiance; NATION.name | Static: only the DAT and SAV loaders write them. | unchanged |
| NATION.wealth0, treasury0, cities0 | Start-of-game values. The DAT loader copies the just-read current value (`0x4482C3`, `0x4482E0`, `0x448330`); there is no other writer. | CONFIRMED |
| NATION.leader | NewGame copies one of the nation's 12 DAT names (Random(12)). It is rewritten by `FUN_00449078`, `FUN_0044C360`, deposition `FUN_0044C8F0` (it draws until the name differs) and `TPickLeaders.OK`. | CONTEXTUAL |
| NATION.colours | 3 fixed dwords per nation, set only by NewGame (`0x448C9B`–`0x448E63`). | CONFIRMED |
| TRAILER.turn_order | NewGame fills 0..15 and swaps each position with Random(16), which is not a uniform shuffle. Seat 0 starts; current = order[0]. Nothing else writes it. | CONFIRMED |
| SLOT.label, quality, name | Recruit arrival `FUN_0044A4E0` sets label 0, quality = recruit state div 4 and the name from `FUN_0044A218` ("Nth Foot/Guards/Bowmen/Lancers/Dragoons Battalion"). Merc hires set the pool label, quality and ethnic name. Whole-slot moves (`FUN_00437CAC`, `FUN_0044AC3C`, `FUN_0044ACB4`), army copies (`TArmyToArmy.OK`, `TChangeArmyUnits.OK`, which commits Rename, `TBattleOver.OK`) and army compaction also write them. | unchanged |
| FLEET.x | The pointer writes of the AI step `FUN_0044DD70`, split `0x447C04`, `TFleetToFleet.OK` and compaction `FUN_0044AD7C`. | unchanged |
| FLEET.route_x / route_y | The AI fleet waypoint (below). | PARTIAL → CONTEXTUAL |
| MERC.x, y, label, type, quality | From the DAT, then only the restock `FUN_00449130` (NewGame runs it too), copying a template. | unchanged |
| NEWS.text | DAT texts 0–26; appended by `FUN_00449240`, which shifts when full. | unchanged |
| BSLOT.label, type, quality | Only the battle copy-in `FUN_00437DE4`, from the army slot. | unchanged |
| NATION.unknown27, unknown1, unknown3 | Inert (below). | UNKNOWN → INERT |

- **Trailer client size (PARTIAL → CONFIRMED).** The saver stores
  `GetClientWidth` (`0x412880`: rect[2] of VMT+0x2C GetClientRect) at
  `0x4A033E` and `GetClientHeight` (`0x4128C4`: rect[3]) at `0x4A033C`. The
  loader passes them to `SetClientWidth` (`0x420C58`, which calls
  `0x412898` = SetClientSize(Point(value, ClientHeight))) and to
  `SetClientHeight` (`0x420C84`). So the file holds +0x32 ClientHeight and
  +0x34 ClientWidth, as the ledger had named them.
- **Fleet +4/+6 (now CONTEXTUAL).** This is the tile the owner's AI fleet
  phase `FUN_0044F608` steers the fleet to (through `FUN_0044E1FC`); x = −1
  means none.
  - **Writers:** `FUN_0044CD08` walks a Bresenham line until the tile class
    changes. It writes its `param_3` (the last tile before the change) and
    its stack `param_4` (the first tile after it).
    - `FUN_0044D9A8` (rendezvous) passes `&fleet.route` as `param_4`.
    - `FUN_0044DBA8` (aboard army) passes it as `param_3`, which is
      **written**. Increment 2 called that pass a read; this corrects it.
  - **Reset:** the round tick `FUN_004514EC` sets route_x = −1 for every live
    fleet (`0x451723`); route_y is never reset.
  - **New records:** the fleet order (`FUN_0044A004`) and the split
    (`0x447C04`) do not set it, so a new record keeps the slot's old bytes
    until the next tick. This explains the only non-−1 route among the 219
    live fleets of the corpus: the just-split fleet of
    `saves/fleet-split-antium-0734.SAV` holds (0;0).
- **NATION +0x450..0x46A, +0x46D, +0x491..0x493 (UNKNOWN → INERT).** In the
  machine-code index, the only instructions that touch these bytes are the SAV
  loader's whole-table read (`0x4488B2`) and the saver's write.
  - **Displacement scan** ([`asm-dispscan-v1.json`](../runs/experiments/data/run-exp-sav-atlas107/asm-dispscan-v1.json)):
    across all application code, every memory operand whose displacement lies
    in these ranges, with any base register, was listed. There are 5, all
    `lea` of nation+0x450, the base of the sub-record that holds hints to
    shoot_delay; it is dereferenced only at +0x1B and beyond. The pad bytes
    have 0 operands.
  - **Initialisation:** the DAT does not hold them, NewGame does not set them
    (it sets every other non-DAT nation field), and the tables are in BSS, so
    they are zero at program start.
  - **File > New does not clear them.** They carry whatever the last loaded
    SAV in that process held, and they are zero in every original lineage
    begun by New Game (56/56 sampled).
  - **Layout:** +0x46D and +0x491..0x493 are exactly the natural-alignment
    holes of an unpacked Delphi record (+0x46D before the i16 array at
    +0x46E; +0x491 to +0x493 pad 1,169 used bytes to 1,172). +0x450..0x46A
    are the first 27 bytes of the settings sub-record.
  - **Proof scope:** this is static, at the scope of the stated index
    heuristics. It is not a formal alias proof, and whether the source declared
    a field there cannot be known from the binary. Research #47 owns
    confirmation; the ledger states the scope in `uncertainty`.
- **File > New leaves other state too.** The DAT loader rewrites only what it
  reads. Army records 15..197 and fleet records 2.. keep their old bytes
  beyond the new counts, and are therefore not saved. The battle block is
  dropped by clearing the flag (`0x448ACA`).
- **Byte metrics with v2** ([public](../runs/experiments/data/run-exp-sav-atlas107/corpus-public-v2.json),
  [private](../runs/experiments/data/run-exp-sav-atlas107/corpus-private-bundle-v2.json)):
  56/56 framed to EOF. Private bundle: CONFIRMED 7.75 %, CONTEXTUAL 91.87 %,
  PARTIAL 0.001 % (battle side), INERT 0.374 %, UNKNOWN 0.

**Remaining gaps.**

- `BATTLE.side` stays PARTIAL. Memory 0 against file 1 after a resume is
  still unexplained; its writers are `FUN_00437DE4` and `FUN_00439C20`.
- The CONTEXTUAL rows have their writer sets now, but their per-writer
  formulas and domains are restated only where they were in question.
- Reader sets are in the index (`reader_functions`), but they are not yet
  joined into the ledger.
- Native or emulator confirmation of the INERT claim and of the route
  lifecycle needs a game run, which the owner must authorise.

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
   +491..493 (3). *Increment 3: classed INERT on static machine-code
   evidence with a stated proof scope; research #47 to confirm.* Across 16 nation records these repeat over 496 stored bytes.
   Do not call them the only unknown bytes of the entire SAV. Current samples
   and bounded non-access controls do not prove global padding/dead semantics.
2. **Whole-program access frontier** (*increment 3: the machine-code index
   covers the 10 undecompiled functions and register/slot pointers; escapes
   and indirect calls remain leads*): computed pointers, wide/overlapping loads,
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
deliverable. Increment 3 adds static whole-program evidence (machine-code
index, DAT layout, initialisation provenance) and the INERT classification
with its proof scope. It does not perform native validation, enable a general
writer or change another repo.
