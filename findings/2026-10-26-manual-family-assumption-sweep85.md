# Bounded manual-family assumption sweep: fleet purse routing and unproved guards

**Scope:** Research85 package5 only: manual supply/funding, army/fleet transfer,
embark/hire/disband and associated cleanup. No battle/AI/serializer sweep.
Draft for Research consolidation; source revision4d70275aac4e155c0370a3ee23525cf34450a908,
research865755e0. Original bytes/private evidence remain ignored/private.

## Restriction ledger and disposition

| Restriction / exact original caller | Evidence and boundary | Remake / history | Intake disposition |
|---|---|---|---|
| Paid staging must be nonnegative | `TAFSupply_ChangeBuyAmount0043FE4C`: floor before signed room; stock Wine17controls, including negative refunds | `SupplyDialogModel.AdjustStaged/TransferStaged`;1486 | proved original discrepancy; separate signed-paid-supply85 report |
| Army money arrows cannot reverse a positive request | `TArmyToArmy_ChangeMoney00442448`: signed min(step,1000−receiver,giver); stock Wine both directions/Split | `ArmyDialogModels` outer zero floors;1487 | proved discrepancy; separate army-money-and-unchanged-ok85 report |
| Selected army transfer must fit as a whole | `TArmyToArmy_Army1Transfer00442500` /`Army2Transfer004426F0`: descending per-slot admission; retained U1/c1/c4/c5 reparse plus new verified-selection controls | `ArmyTransferCommandHandler` aggregate gates;1488 | existing issue, preserve per-unit limits/ordering; details in partial-transfer report when complete |
| Transport always uses exact ships×500 | Separate human embark004466CC, hire opening00446FF4 and hire offer00441360 use truncating division; stock Wine9controls | `EmbarkArmyCommandHandler`,`HireMercenaryCommandHandler`;Research83, transfer1489 | proved per-caller discrepancy; no AI-policy inference |
| Unchanged Army transferOK is inert | `TArmyToArmy_OK00442EF8` unconditionally pushes selected A then B; six stock Wine no-edit controls | `ComposeOk` null / all-zero dispatcher refusal;Research84 | proved discrepancy; preserve Cancel |
| A Transfer ships money arrow may send overflow to treasury | `TFleetToFleet_ChangeMoney00443A90`: signed receiver1000 cap on copies; partial`TFleetToFleet_OK00443B48` does not route overflow to treasury | `FleetTransferModel` caps only giver, dispatcher caps receiver and credits treasury;1326 alreadyopen | runtime discrepancy, retain existing1326; no duplicate issue |
| Independent ±1000 command ceiling is an original rule | GUI arrows have10/100requests; receiver cap and signed applied amount are different concepts. Current`SupplyDialogModel.PressMoney` forwards nominal signed request | `TransferMoneyCommandHandler` ceiling cites T105 hazard/audit prose, not original arbitrary-size command | CLI/model-only policy; no new player-reachable GUI discrepancy established; correct provenance claim, don't silently remove API policy |
| Embarked Disband army is always allowed because handler lacks a cell check | `TUnitMap_DisbandArmy004476AC` reads form army field+220 only; direct carrier selection and after Supply still+220=−1, so menu does nothing | `DisbandArmyCommandHandler` explicit embarked refusal; residual in closed802 | unresolved GUI reachability; two tested routes do NOT demonstrate a gameplay defect. Do not infer invocation from handler body alone |
| All-mercenary desertion must clear carrier link | Quarterly`FUN_00451B40`→remove`0044AC3C`→delete`0044AB90`; delete's embarked branch resolves fleet at army coordinates and writes fleet+22=−1 | `QuarterlyEconomySystem` explicit model-invariant adaptation; its comment says original cleanup unmeasured | code-derived but unplayed: original cleanup supports consistent valid links. Do not call this a new runtime result or remove the model invariant |

## Fleet money: exact controls and rule

Private synthetic`fleet-split-antium-0734.SAV`,turn0734: selected donor fleet5,
10ships,purse200; partner fleet2,20ships,receiver purse as below. No ships
transferred in money-arrow controls;100-arrow points into fleet2.

| Initial giver / receiver | Original result | National treasury |
|---|---|---|
| 200 /950 | 150 /1000 | unchanged |
| 200 /1000 | 200 /1000 | unchanged |
| 200 /1100 | 300 /1000 | unchanged |
| 200 /1100, **one ship only**, no money arrow | ships9/21, purses200/1100 | unchanged |

Thus receiver purse1000 is **the money arrow's signed cap**, not an unconditional
partial-OK cap. A ship-only partial transfer leaves an over-cap purse untouched.
The original preserves giver/receiver balances, with no treasury diversion.

NativeExtra production model+dispatcher at the pin (`native-extra-v4.txt`):
GUI model emits a100-money command in all three corresponding states. Results
are giver100/receiver1000 with treasury gains50/100/200 respectively. This is a
GUI-composed command mismatch, not merely an oversized CLI request. Ship-only
GUI command1/0/0 leaves giver200,receiver1000,treasury+100, contradicting the
original's unchanged1100purse. Existing1326 is the correct route. Preserve the
owner's independent no-wrap saturation and carrier/over100 safety choices.

Evidence: `sweep-pilot-v1_fleet-money-950.json`,
`sweep-v2_fleet-money-{1000,1100}.json`,
`sweep-v2_fleet-ships-only-overcap.json`, plus `sweep-v2_fleet-money-cancel.json` confirming Cancel commits nothing;
all under`runs/experiments/data/run-exp-restrictions85/`. Endpoints named in each
row, e.g.`sweep-v2_fleet-ships-only-overcap_before.SAV` / `_after.SAV`,turn0734.
Private full records/screenshots/identities/hashes under ignored
`artifacts/run-exp-restrictions85/private-sweep-*/`. No public release.
NativeExtra v1 compile failure retained;v2 fleet fixture had donor0 and exercised
insufficient money, so it is NOT cap evidence. v3 fixes fields;v4 additionally
verifies the GUI composition and ship-only discriminating case. Source and all
prior logs retained; no prior measurement overwritten.

## Caller and lifecycle limits

Carried-disband controls use the **actual Unit map > Army > Disband army menu**,
not direct handler injection. Before invocation form+220/222/224 is−1/−1/2
in both routes; army remains alive, fleet link0, purse/supply/treasury unchanged.
Source caller does not resolve a carried army as Supply/Hire do. This explains
why the seemingly absent handler guard is insufficient evidence. Other original
selection routes remain untested; no owner-machine access required or attempted.

Desertion cleanup is a static call-chain audit on the pinned original, not a
quarter-boundary experiment. For a well-formed army/fleet link, original deletion
clears it; malformed duplicate/stale-coordinate states can differ from the
remake's invariant cleanup. They are not a proved player-facing restriction.

The ±1000 command ceiling is separate from applied magnitudes: an original
nominal100 arrow can pull more than1000 back from a sufficiently over-cap purse;
remake's current UI forwards nominal100 and its helper computes signed admission.
This audit did not demonstrate rejection on that GUI route. Do not promote the
T105 test/task sentence into original arbitrary-command semantics.

## Deliberate policies preserved

Read live decision records, retained in`brief-v1/`:
1340 comment6346182785 explicitly retains Transfer ships carrying-army and
combined-over100 refusals;565 comments5967204282/5967652858 retain last-unit
Change units refusal and naming policy. No-wrap32767 saturation (PR758/963,
T193), Improved affordability, QoL automatic-funding reserve and T216 safe
no-receiver refusal remain owner choices under the dispatch brief. This study
neither revokes them nor widens one handler's rule across other callers.

## Runtime provenance

Stock unmodified original (privately verified),Wine10.0 Ubuntu
10.0~repack-12ubuntu1,win32,task-owned Xvfb:757,1280×1024. Real UI clicks and
original-written saves; read-only memory observes copies/caller fields. Historical
partial controls used patched fast/seed Wine and are labeled separately. No
fresh native Windows, original patch, live memory write, owner running game,
remake code, release gate or owner-policy change.
