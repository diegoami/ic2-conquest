# Paid Supply arrows preserve signed room and refund after Buy supplies

**Tag:** [confirmed, partial] — 17 stock-original Wine UI controls; no native
Windows acceptance. Draft for Research85,83–84 dispatch. Research main checked
at865755e04f107afc38cdb496669d882e2551aca6; original caller reviewed separately
from army transfer, embark and hiring. Related remake issue1486 remains open.

## Answer and exact rule

`TAFSupply_ChangeBuyAmount @0043FE4C` applies these operations **in order**:

1. `amount=max(0,amount±step)`; step is10 or100.
2. `amount=min(amount,foreign city stock)`.
3. `amount=min(amount,room)`; army room=`troops div100+1−supplies`,
   fleet room=`ships×8−supplies`.
4. `amount=min(amount,target purse×5)`.

There is no final nonnegative floor. Negative room makes the amount negative,
even with an empty city. `TAFSupply_TransferSupply @0043FF98` (visible button
**Buy supplies**) immediately applies `target supply+=amount`, `city stock-=amount`,
`city owner's treasury+=trunc(amount/5)`, `target purse-=trunc(amount/5)`, then
resets staging to0. Negative division truncates toward zero. It is the foreign
owner's treasury, not the purchasing nation's treasury.

Staging alone changes no strategic record. Closing via Alt+F4 before purchase
abandons it. Closing after purchase keeps the already-applied transfer. This
form has an OK button and no visible Cancel button in these controls; do not
call this transactional Army transfer Cancel behavior. `TAFSupply_OK @00440234`
just closes. The paid and free/immediate handlers remain distinct.

## Observed controls

Fixture `fleet-split-antium-0734.SAV`, turn0734, private synthetic copies:
army0 has10,000 troops (dialog cap101), or fleet2 has20ships (cap160).
Adjacent Antium89 is assigned a non-hostile foreign owner in the copy; its
stock330, target purse100 unless indicated. Inputs and both original-written
saves retained for every row.

| Control | Staged amount | Effect on target after purchase |
|---|---:|---|
| Army206tons / fleet265tons, room−105 | −105 | −105tons,+21talents |
| Room−5, each target | −5 | −5tons,+1talent |
| Room−4, each target | −4 | −4tons,0talents |
| Room−1, each target | −1 | −1ton,0talents |
| Room0, each target | 0 | unchanged |
| Room51, each target | 51 | +51tons,−10talents |
| Army room101, +100,−100,−100 | 100,0,0 | unchanged at zero |
| Army room−105, empty city | −105 | returns105tons,+21talents |
| Army0tons, purse3 | 15 | +15tons,purse0 |
| Army206tons, stage then Close | −105 | no resource change |
| Army206tons, purchase then Close | −105 then0 | refund retained |

Evidence: `runs/experiments/data/run-exp-restrictions85/supply-v2_<case>.json`,
plan`supply-v2-plan.json`, independent-of-click-path save reparse
`audit-supply-v1.json` (17pairs). For the primary control:
`supply-v2_paid-army-room--105_before.SAV` and
`supply-v2_paid-army-room--105_after.SAV`, turn0734, army206/100→101/121,
city330→435, foreign treasury−21. Fleet counterpart is
`supply-v2_paid-fleet-room--105_before.SAV` / `_after.SAV`.
The audit compares the **whole parsed world**, allowing only the named resource
fields and camera positions; all17 pairs pass. Private originals/screenshots/
identities/hashes: ignored`artifacts/run-exp-restrictions85/private-supply-v2/`.
No public binary release. Failed pilotv1 retained: it reached the dialog but
looked for the wrong button caption; it is not a completed transfer measurement.

## Remake comparison and implementation handoff

Pinned remake4d70275aac4e155c0370a3ee23525cf34450a908,
`godot/UI/Dialogs/SupplyDialogModel.cs:252–268`: final nonnegative staging and
`staged>0` submission suppress this action. Exact public reproduction from
Research85 retained unchanged in`runs/experiments/restrictions85/AuditFromBrief.cs`;
compiled against the archived pinned production/test code. Successful
`native-probe-v2.txt` reproduces room−105/staged0/no command, while direct
production`SupplyPurchase.BuyForArmy` admits−105 and ends101/121.
Build succeeds with3 existing nullable warnings. First execution's repository-
root lookup failure is preserved in`native-probe-v1.txt`; v2 executes unchanged
output beneath the extracted source root. No full test-suite/native UI/deployed
build claim.

For1486: preserve the ordered signed staging and foreign-owner account routing;
retain normal decrement-to-zero and immediate-vs-staged distinction. Deliberately
resolve the buy-command boundary: the current helper can compute negative
admission from a positive request, but its public command may reject a negative
request. Do not submit negative requests without checking that seam. Test GUI
model+dispatcher+helper together, including−1/−4/−5 refunds and Close timing.
No remake modifications or owner-policy changes in this study.

## Provenance and limits

Stock unmodified`Imperial Conquest 2.exe`, byte equality verified against the
retained original; identities and hashes private. Wine10.0 Ubuntu
10.0~repack-12ubuntu1, win32 prefix, own Xvfb:757,1280×1024. No patched observer,
seed control, memory write, owner desktop access, End turn or battle. Read-only
memory tracks staging and timing; real visible/enabled Win32 controls clicked;
original Save as writes both endpoints. Synthetic owner/stock/purse/unit edits
are documented, with private changed-byte lists; no claim these artificial
inputs are the owner's running save. Original files preserved.

Exact source sites and decompile pin verification:
`source-sites-v1.json`; full original decompile/disassembly remains private.
Original single-provider supply, capacity and purse reports were read before
these controls; this supplies previously missing live paid/signed evidence,
not a rediscovery of ordinary own-city supply. Other callers are not implied.

## Staging correction and coherent-marker revalidation (2026-10-26)

The original17 `supply-v2` controls assigned Antium's city-record owner1 but
kept its old Roman map marker36. Their measured refund/staging outcomes and
whole-before/after audits remain valid, but the opening gate used the own-marker
shortcut; those inputs alone do **not** establish natural foreign-city entry.
This inconsistency was exposed by separate GUI79 war-city controls, not hidden.

Two fresh stock-original controls now use coherent owner1/marker37 and peace in
both relation directions: `supply-marker-v3_paid-army-room--105_before.SAV` /
`_after.SAV` and `supply-marker-v3_paid-fleet-room--105_before.SAV` / `_after.SAV`,
turn0734. Both open through the original non-hostile foreign-city caller and
repeat staged−105, supply−105,purse+21,city+105,foreign treasury−21 exactly.
`audit-supply-marker-v3.json` reparses both pairs with whole-world checks;
`coherent-city-marker-v1.json` verifies marker/record ownership agreement at both
endpoints. Old inputs and measurements are retained, never rewritten.

The staged-switch multi-provider behavior is investigated separately under
Research78; no nonnegative-stock safeguard is removed by this report.
