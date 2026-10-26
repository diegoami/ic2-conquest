# Army transfer: signed money arrows and unconditional OK rebalance

**Tag:** [confirmed, partial], stock-original Wine. Research85 packages1/4;
Research84; remake1487. This draft does not close implementation issues.
Promoted research read first at865755e0: purse-writes row4 and army-to-army-OK
report were code-backed but lacked these exact live controls.

## Exact caller and observed rules

`TArmyToArmy_ChangeMoney @00442448` updates two **working army copies**:
`step=min(request,1000−receiver purse,giver purse)` with **no floor**. Request
is10 or100. Then giver loses step, receiver gains step. A negative step reverses
money. Both arrow directions are separate tested cases. Two presses into each
receiver900/1000/1100 establish under/at/over-cap behavior:

| Initial donor / receiver | After first arrow100 | After second |
|---|---|---|
| 100 /900 | 0 /1000 | unchanged |
| 100 /1000 | 100 /1000 | unchanged |
| 100 /1100 | 200 /1000 | unchanged |

Before OK the live army table remains unchanged; Cancel discards working money.
Split uses the **same form and handler**, verified through its real menu/button:
selected army1100, newly created empty partner0, nominal arrow100 into selected
army => working1000/100. Thus a zero-money giver does not prevent signed pullback
from an over-cap receiver. Cancel restores the selected army's money and deletes
the empty split partner. That lifecycle is not a final-unit policy correction.

`TArmyToArmy_OK @00442EF8` is unconditional: even **no-edit OK** writes copies and
pushes supply excess from selected A to B, then B back to A. Caps here are
`troops div100` (no supply-dialog+1). No dirty/no-op guard exists at this site.
Money is not rebalanced. For two10,000troop armies (caps100):

| Physical armies0/13 supplies | Action / selected | Result0/13 |
|---|---|---|
| 206 /0 | no-editOK /0 | 106 /100 |
| 206 /0 | Cancel /0 | 206 /0 |
| 206 /0 | no-editOK /13 | 100 /106 |
| 50 /20 | no-editOK /0 | 50 /20 |
| 206 /150 | no-editOK /0 | 256 /100 |
| 206 /150 | no-editOK /13 | 100 /256 |

Global records do not change merely by opening the dialog. Confirming alone
triggers the push. Unit counts, money, moves, positions and carrier links are
recorded separately from supplies in each case, so this is not an implicit turn
or ordinary supply purchase. Excess is conserved; selected army holds any total
above both caps combined. No refusal follows these no-edit controls.

## Evidence and reproduction

14 completed controls: seven money rows in`army-v2_money*.json`, one
`army-v4_split-money-shared.json`, six`army-v4_unchanged*.json`;
`money-unchanged-case-index-v1.json` indexes all14; `audit-money-ok-v1.json` reparses28saves and verifies the whole parsed world except tested resources, camera and the cancelled Split tombstone. Extra successful pilot
`army-pilot-v1_money-side0-receiver1100.json` repeats one money case.
Every completed row cites private original-written before/after SAV endpoints,
turn0734, from`fleet-split-antium-0734.SAV`, plus arrow-time working/live copies.
Examples: `army-v2_money-side0-receiver1100_before.SAV` / `_after.SAV` and
`army-v4_unchanged-over-ok_before.SAV` / `_after.SAV`.
Private input/full state/screenshots/hashes retained under ignored
`artifacts/run-exp-restrictions85/private-<batch>/`. Runners
`runs/experiments/restrictions85/army.py`,`common.py`;
source boundaries`source-sites-v1.json`. Failed Split attemptv3 had a one-unit
donor and hit the original opening guard; it is retained and not counted.
Two later multi-unit attempts in army-v4 selected only one row; explicitly
excluded from partial-admission evidence and unrelated to these valid controls.

## Remake comparison / handoff

Pinned4d70275aac4e155c0370a3ee23525cf34450a908:
`ArmyDialogModels.cs` outer nonnegative money capacities suppress signed pullback
(1487); exact native reproduction retains giver100/receiver1100 and composes
nothing. Restore per-press signed arithmetic on working previews, both directions
and repeated presses. Test Split as its own opening caller with the shared form.

`ArmyTransferModel.ComposeOk` returns null without edits and
`ArmyTransferCommandHandler` rejects an all-zero order. NativeExtra production
model+dispatcher (`native-extra-v3.txt`, also v4) gives no command/rejection,
supplies206/0, contradicting original no-editOK106/100. Research84 is the
existing research route. An implementation handoff must allow a confirmed
unchanged OK to reach the unconditional rebalance, while Cancel remains inert.
Do not make every zero command a generic action without resolving the GUI/command
contract. Tests only on balanced armies cannot distinguish the rules.

This is not authority to change army-to-army provider QoL, no-wrap saturation,
last-unit restrictions or automatic funding reserve. No remake modification.

## Limits

Stock unmodified original, privately verified identity, Wine10.0 Ubuntu
10.0~repack-12ubuntu1, win32 prefix, task-owned Xvfb:758,1280×1024. Actual visible
UI arrows/OK/Cancel; read-only memory for timing; original Save as endpoints.
No original patch, native Windows, deployed remake GUI, owner desktop, End turn
or AI run. Exact source/template revisions retained in the task evidence.
Disband inside this same dialog is a separate extension still in progress;
these rows establish unchanged OK without it. Static caller/working-copy evidence
and runtime outcomes remain distinct.
