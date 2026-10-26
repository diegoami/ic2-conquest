# AI embark overflow: receiver context, raw allocation and safe refusal

**Tag:** [confirmed, partial: conditional original instruction execution and
accepted native commands; retained-artifact audit]. **Status:** conquest draft
for Research intake, PR223; no promotion or production change.
**Issue:** [conquest174](https://github.com/diegoami/ic2-conquest/issues/174).

## Result

The original boards the army **before** finding the overflow receiver: it frees
the source land cell, centres the search on the fleet and zeros source moves.
Moving overflow units then zeros the newly created receiver's moves too. Current
native T216 queries placement on the pre-board army and gives the receiver its
initial AI move. Seven accepted mixed-unit rows differ only in receiver position
and moves; an eighth, all-overflow row also differs in resources. These eight
rows represent **five distinct inputs**, not eight independent scenarios.

The original full raw 198-army branch is destructive: it deletes overflow units
and writes resource words through receiver index−1 into a city's name. This
supports **retaining T216's owner-approved atomic refusal**, not copying those
effects. Human/designed refusal and native resource-conservation policy remain
unchanged. The optional control intended to isolate a false no-safe-receiver
refusal was not run; no such refusal is established here.

Evidence throughout: run `run-exp-fleet-overflow174`, turn 0720, per-case
`private-original-v1/<case>/before.SAV` and `expected.SAV`. These are diagnostic
RAM projections, **not original Save As outputs**. Scalar results and runners
are in [the data packet](../runs/experiments/data/run-exp-fleet-overflow174/)
and [runner directory](../runs/experiments/fleet-overflow174/). Full original
RAM/SAV/states, input hashes, traces and native full states stay private in
ignored `artifacts/run-exp-fleet-overflow174/`; there is no public binary release.

## Method and source boundary

Original stock EXE identity is checked by `fleet174-actions/common.py` (SHA256
starts `9d753d5d`). `original.py` first recovered the retained
`fleet-controls-v3/embark-units-4000-2000/{before,expected}.ram` complete-RAM
baseline. It then executed unmodified B79C instructions on explicitly constructed
synthetic inputs; only the helper-only no-land control enters F8FC directly.
Actual game helpers and RNG are not replaced. No new original game was launched.

The inputs reconstruct adjacent land armies, fleet 0 at (40,33), source 0 at (39,34),
ten ships/capacity 5000, valid quality 7, declared occupied cells and raw counts.
Mixed source slots are 4000 LI + 2000 HI, money 100, supply 90. Human helper and no-land
fixtures are deliberately non-equivalent boundaries, not human UI or naturally
reached new embarkations.

Each of 16 declared controls ran under two CPU initializations: EAX=0, EDX=0
(EDX=5000 at direct F8FC entry), synthetic return address/stack, callee-saved
registers initially zero versus EBX/ESI/EDI=0x12345678 and EBP=0x80e000;
EFLAGS=0x202 versus 0x246. Both variants produced equal complete game RAM and
preserved callee-saved registers. There were zero observed original Random calls
and no seed change. This checks those declared assumptions, not exhaustive CPU
contexts or an actual AI caller capture.

Native pin is Main `4d70275aac4e155c0370a3ee23525cf34450a908`, also current
Main at the 2026-10-26 source check. Eight public source/data blobs match the
retained tree exactly (`source-pins-v1.json`): embark handler, SplitPlacement,
whole-slot partitioner, importer, T216 contract, world, terrain and faithful
rules. Fifteen `EmbarkArmyCommand` requests use the real dispatcher on imported
before containers. All 15 input gates cover the declared army/unit, launched
fleet/link, city/name and nation projections, plus occupied army/fleet terrain
against actual World. This is a measured projection, not every SAV field.
Expected outputs are compared directly; corrupt expected SAVs are never imported
and normalized into native states.

Native-v2 additionally queries unchanged SplitPlacement on a **diagnostic staged
post-board state**. This does not alter production or substitute a staged result
for an accepted command. `comparison-v2.json` / `native-v2.json` are authoritative;
the final audit's qualifications below supplement their preliminary labels.

## Observations

All rows cite their case's projected save pair at turn 0720 in the run above.
Existing occupied armies are 3000-troop controls and remain byte-unchanged.

| Case(s) | Original observation | Native command / classification |
|---|---|---|
| `free-receiver` | New raw receiver 1 at (40,34), moves 0; 4000 aboard/2000 ashore | Accepts; receiver(40,35), moves 1. Placement/moves discrepancy |
| `vacated-source-only`, `existing-own`, `existing-own-source-only` | Same input across three labels. Occupied(40,34) unchanged; new receiver 2 at vacated(39,34), moves 0 | Accepts; receiver(40,35), moves 1. Three rows, one input |
| `existing-enemy`, `existing-enemy-source-only` | Same input across two labels, enemy occupant unchanged; receiver 2 at (39,34), moves 0 | Accepts; receiver(40,35), moves 1. Two rows, one input |
| `raw197` | Creates raw record 197, count197→198; receiver(40,34), moves 0 | Accepts, all troops/stores retained; receiver(40,35), moves 1 |
| `single-all-overflow` | All 6000 ashore in raw record 1, source 0 tombstoned, carrier cleared; receiver(40,34)/moves 0, money 33/supply 30 | Accepts; receiver(40,35)/moves 1, money 100/supply 90. Additional conservation-policy difference |
| `raw198`, `raw198-all-overflow` | No receiver; 2000/6000 overflow troops removed respectively; city315 name words overwritten with 30/33 | Typed `naval.no-safe-overflow-receiver` refusal, full serialized state unchanged; intended safety |
| `raw198-tombstone` | Raw count 198 blocks creation despite one dead record; overflow removed and same negative-index writes | Import has 197 live armies, command accepts. Raw-table/model boundary policy |
| `raw198-at-cap`, `raw198-below-cap`, `human-at-cap` | 5000/4999/5000 aboard, no overflow helper | All accept, exact measured projection matches |
| `human-helper-overcap` | Direct B79C human entry boards 6000 without calling F8FC | Refuses `naval.army-too-large`, unchanged. Direct helper bypasses UI eligibility; preserve human policy |
| `helper-only-no-land` | Direct F8FC on an already-aboard synthetic army with neighboring land removed; deletion/resource corruption branch | No native comparison. Not natural adjacent-embark evidence |

The 16 labels have 13 byte-distinct inputs; duplicate groups are listed in
`checkpoint-v1.json` and rechecked in `audit-v2.json`. Preliminary counts remain 8
accepted discrepancies,3 projection matches, 2 safe full-table refusals,1 raw/model
boundary, 1 human boundary and1 helper diagnostic. Audit refines the 8 discrepancies
to 7 position/moves-only rows plus 1 with additional resource difference. No prior
measurement or classification file was rewritten.

### Receiver search and moves

B79C restores source terrain at 44B7E9, snaps coordinates at 44B7FB/44B806,
zeros army moves at 44B80A, then conditionally invokes F8FC at 44B833. F8FC calls
49F08 using the source's **now fleet-centred** coordinates. The creator calls
492C0's last-qualifying 3×3 scan; it always allocates a new raw record rather
than reusing/merging an adjacent own or enemy army. In ACB4, source moves 0 causes
the receiver's initially assigned AI move 1 to become0 before return.

Current T216 calls `SplitPlacement.ArmyCellFor(state, world, army)` before
boarding and retains `NewArmyMovesAiSeat` on its receiver. Diagnostic staged
post-board queries reproduce **every successful original receiver coordinate**.
The read-only audit separately rederived all 30 pre/post query results from World
and occupancy. This isolates a bounded placement-context/movement issue; it does
not establish a tested production correction or a full-loop AI choice.

The occupied controls block the fleet-neighborhood alternative but still allow
native (40,35), outside the fleet's 3×3 area and within the source's. They show a
wrong accepted coordinate, not a false refusal. The proposed control blocking
alternatives in the union of both neighborhoods remains unexecuted.

### Full table, tombstones and resource safety

49F08 initializes receiver index−1 and rejects raw count≥198. It does not reuse
dead raw slots. F8FC deletes units if creation failed, yet unconditionally writes
one-third supply/money through that negative index. In the synthetic controls,
`Army[-1]+10/+12` alias city315 name offsets0/2, receiving 30 and 33 respectively.
Private watched-write traces and expected RAM bytes agree. These are original
instruction effects conditional on these inputs, not native recommendations.

In `single-all-overflow`, AB90 marks source 0 dead and clears the carrier, but
ABE0 is never called. Raw count remains 2; live receiver is raw 1. The source
tombstone contains money 67/supply 60; the live receiver has33/30. Native replaces
its source model record with a live receiver holding 100/90, preserving resources
under T216. Earlier broad wording about original compaction must not be read as
an observed ABE0 callback in this call chain. Import/model dropping of dead
records is separate from original raw compaction. Raw198 with a tombstone
remains full for original allocation while importing as 197 live native records.
No export/reimport acceptance was tested here.

### Caller and human limits

A valid adjacent land army vacates its own eligible land cell before F8FC
searches. A fixture with no land anywhere around the fleet cannot stand in for
that natural new-embark caller. This packet's no-land helper entry changes
terrain and starts aboard; it is diagnostic only. Human direct B79C likewise
bypasses UI capacity checks. Existing promoted human rounding evidence is
[a separate finding](2026-10-26-human-transport-rounding83.md), not a new
discovery or a reason to change human refusal.

## Audit, corrections and limits

The author's separate **read-only** audit reparsed 32 retained endpoints,
checked RAM→projected SAV byte identity, SAV→JSON and exact declared shapes,
32 retained call/write/CPU trace records, 15 native full-state projections,
per-case/aggregate v2 agreement and terrain/query calculations. All 128 initial
private hashes match. New private `closure-v2.json` inventories 255 files; hashes
and full traces stay private. Audit-v1 stopped on Python tuple versus JSON array
comparison, fixed by canonical JSON equality; its failure and private source
extract remain. This was an audit-tool issue, not a game failure.

This resume did not reexecute original instructions, rerun native commands or
rebuild native. Prior native build-v1 failed on a runner property typo; build-v3
completed with zero warnings/errors and execution-v2 completed. All earlier
versions/failures remain. Audit verifies retained traces, not a fresh full-RAM
instruction replay. It is self-audit, not independent review.

This refines Research74's untested allocation/existing-receiver boundaries and
qualifies its compaction wording. It does not reopen the whole troop-loss fix:
current T216 preserves whole troops in accepted controls. The narrow follow-up
candidate is accepted faithful-AI receiver context/moves, **after promotion**.
Keep typed atomic refusal, human/designed behavior, conservation policy and
raw/model boundary decisions explicit. Main owns any reviewed implementation.

No whole-turn/AI caller, RNG-stream parity, original UI, Godot, Windows or native
original-compatible export acceptance is claimed. No owner files, new campaign,
battle/bot queue or other-repository write was involved. #174 retains wider
route/caller-aligned coverage; #178 was not started.
