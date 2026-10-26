# Army transfer admits each unit separately, preserves order and can show two refusals

**Status:** Promoted by [Research PR86](https://github.com/diegoami/imperial-conquest-2-research/pull/86), merge `38259d83f323bf6cbad1a4ddf2cc47ecd69f719f`. The [canonical report](https://github.com/diegoami/imperial-conquest-2-research/blob/38259d83f323bf6cbad1a4ddf2cc47ecd69f719f/docs/reports/2026-10-26-partial-army-transfer85.md) and [independent verification receipt](https://github.com/diegoami/imperial-conquest-2-research/blob/38259d83f323bf6cbad1a4ddf2cc47ecd69f719f/docs/data/restrictions85-intake-v1.json) retain the evidence qualifications below.

**Tag:** [confirmed, partial], stock-original Wine17verified-selection controls;
retained six promoted patched-Wine controls independently reparsed. Research85
package2, remake1488/1489. No new battle/AI/Join-armies rule is inferred.

## Exact admission and ordering matrix

Original`TArmyToArmy_Army1Transfer00442500` and`Army2Transfer004426F0` work on
copies, source slots19→0. For **each selected occupied source slot**:

1. Refuse this unit if destination slot19 is occupied (normal packed20-unit cap).
2. Else refuse if destination troop sum plus this unit is **greater than100000**.
3. Else, if destination is carried, refuse if
   `carrier ships < (destination troops+unit troops) div500`.
4. Otherwise copy the whole unit into destination's **occupied-unit count**
   index, set destination working moves0, remove source unit and compact it.
5. Continue through the remaining lower selected slots, including after failures.

Failures do **not** roll back units already accepted. Source and destination
identities remain the form's selected A / partner B, separately tested both
arrow directions. Recipient moves change on the **copy at Transfer**, then in
the real army only on OK; donor moves stay unchanged. Money/supply are separate
from unit moves and the later OK push.

| Verified selected input | Result before/after OK | Refusals |
|---|---|---|
| Destination19 + selected source slots0/1 | slot1 appended at19; slot0 stays | one20-unit box |
| Destination18 + source slots0/1/2 | slot2→18, slot1→19; slot0 stays | one20-unit box |
| Destination98000, source slots0..3 troops500/1000/2000/1000 | slot3 fits99000; slot2 fails; slot1 fits100000; slot0 fails | one100000-troop box |
| 30ships, destination14000, one1000 added |15000 accepted | none |
| Same,1499 added |15499 accepted | none |
| Same,1500 added |15500 refused,14000 retained | onefleet-capacity box |
| Cancel after19+2 preview, each direction | globals/armies/fleets unchanged | earlier20-unit box still observed |
| Destination19units/15000troops on30ships; donor selected100/100/500 | slot2 failsfleet; slot1 fits15100/20units; slot0 failsunitcount | **two** boxes,20units thenfleet |

The first six rows are independently tested in **both directions**. The single
special mixed-failure row explains the original box ordering: after the loop,
show unit-count box if any such failure, otherwise troop-cap box if any;
**then independently** show fleet box if any. One box is not a general rule.
There is no aggregate Join-armies preflight in this different caller.

## OK/Cancel and disband extension

Before OK, actual strategic army records remain unchanged after arrows. OK
commits copies, rebalances supplies A→B then B→A and handles an emptied-army
merge. Cancel discards the copies. No carrier pointer/resource/move corruption
observed in these bounded controls. No non-growing operation was force-trimmed.

Separate same-dialog disband controls: selected army two5000troop units,
supplies206, partner10000troops/supply0. Confirm disband of one regular unit
near own Antium: working troops fall5000 while global army remains10000;
OK leaves selected5000troops/106tons, partner10000/100tons. Cancel restores both
army records intact. The disband confirmation is distinct from final dialogOK;
this does not change the owner's last-unit policy for Change units.

## Evidence and reconstruction

Fixture`fleet-split-antium-0734.SAV`,turn0734, private synthetic units/map/link/
moves edits. Donors retain an unselected unit in single-transfer controls;
receiver and carrier links staged consistently. Real lists selected with actual
Ctrl/pointer clicks; read-only`LB_GETSELCOUNT` verifies every requested row count
**before** Transfer/Disband. Copy/global snapshots separate timing. Original
Save as writes every before/after pair.

Evidence:`runs/experiments/data/run-exp-restrictions85/`:
`units-pilot-v2_partial19plus2-side0.json` plus16`units-v3_*.json`;
`audit-units-v1.json` reparses34saves, verifies selection, ordered unit identities,
per-unit failures, recipient/donor moves, Cancel and global-copy timing.
Primary saves`units-pilot-v2_partial19plus2-side0_before.SAV` / `_after.SAV`;
rounding`units-v3_transport15499-side0_before.SAV` / `_after.SAV`;
two boxes`units-v3_two-refusal-types_before.SAV` / `_after.SAV`,allturn0734.
Private screenshots/full states/identities/hashes under ignored
`artifacts/run-exp-restrictions85/private-units-*/`. No public releases.

`prior-controls-audit-v1.json` independently reparses historical U1,U3,U3b,
c1,c4,c5 from their retained final-root save pairs: same100000/15499/15500 and
20-slot/Cancel outcomes. Those originals used patched fast/seed Wine; fresh17
controls use the stock executable. No repeated historical game run required.
Gapped synthetic slot cases remain the prior report's artificial-edge evidence;
they are not silently equated with ordinary packed rosters.

**Failed stimulus records preserved and excluded:** first army-v4 multirow
attempts selected only one row; units-pilot-v1 guard detected1≠2 and stopped
before Transfer. Screenshots/receipts retained; they do not establish partial
admission. Corrected actual pointer selection passed the guard in all17 controls.

## Remake comparison / implementation handoff

Pinned4d70275aac4e155c0370a3ee23525cf34450a908, production
`ArmyTransferCommandHandler`: aggregate20/100000/fleet checks reject whole
selection. Exact preserved Research85 native dispatcher probe returns rejected
with receiver19 for19+2 (1488), and rejects single499 addition to15000 on30ships
(1489). Model/engine/source blobs verified against authoritative Git tree in
`native-source-verified-v1.json`. Native code not modified.

For1488: preserve per-slot identity, descending iteration, append-at-count,
continue-after-failure, target-only move reset, copies/Cancel/OK, empty-army
lifecycle and separate staged resources. Present both applicable refusal classes
when unit/troop and fleet failures coexist; do not label any partial admission
as total rejection. A batch command's result contract needs deliberate design
to express accepted units plus refusal information.

For1489: use the loaded divisor with original integer division at this caller;
15000/15499/15500 discriminate exact multiplication. Test both receiving sides,
links/resources/moves and a non-growing operation separately. Human embark/hire
now have their own measured Research83 report; no AI T216 redesign authorized.

## Limits

Stock unmodified original identity verified privately; Wine10.0 Ubuntu
10.0~repack-12ubuntu1,win32,task-owned Xvfb:758,1280×1024. Read-only memory and
real visible original controls, no handler injection, patch, owner desktop,
End turn, full campaign, battle or fresh native Windows. No installed Godot
acceptance or independent external review claimed. Owner policies remain intact.
