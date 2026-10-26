# Research85 and GUI78–81 — immutable evidence and implementation handoff

Owner-authorized isolated original investigation: conquest211, Research85/82.
Source pins: remake4d70275aac4e155c0370a3ee23525cf34450a908;
research865755e04f107afc38cdb496669d882e2551aca6.13public source blobs verified
in`native-source-verified-v1.json`; original identities/hashes stay private.
No original bytes/screenshots/full decompile/private save hashes in this packet.
No remake modification, owner desktop use, release change or policy changes.

## Findings and exact intake rules

| Route | Finding / exact handoff |
|---|---|
| Main1486 / Research85 | `findings/2026-10-26-signed-paid-supply85.md`: floor before signed room; negative paid giveback/refund; immediate Buy vs staged Close; command-boundary design needed. Old17inputs had inconsistent cityowner/mapmarker; two coherent marker37 repeats confirm original foreign-city entry and outcomes. |
| Main1487 | `findings/2026-10-26-army-money-and-unchanged-ok85.md`: signed min(request,1000−receiver,giver) on working copies, both directions/Split; Cancel inert. |
| Research84 | Same report: unchangedOK must reach A→B/B→A rebalance; keep Cancel inert. Decide GUI/zero-command seam explicitly. |
| Main1488 | `findings/2026-10-26-partial-army-transfer85.md`: per-unit descending slots, continue after failure, append-at-count, recipient moves0, copies/Cancel/OK, partial result/refusal contract. Two refusal classes may both show. |
| Main1489 | Same report: carrier check uses post-unit troops div500;15499accepted,15500refused on30ships; no AI policy inference. |
| Research83 | `findings/2026-10-26-human-transport-rounding83.md`: human embark/open-hire/per-offer-hire separately measured; ten ships accept5499/refuse5500. Keep other gates and T216 policy. |
| Main1326 / Research85 sweep | `findings/2026-10-26-manual-family-assumption-sweep85.md`: fleet arrow signed receivercap, no treasury diversion; ship-only OK leaves overcap purse. Existing1326, no duplicate. ±1000 ceiling CLI-only; carriedDisband reachability unresolved; desertion unlink code-derived/unplayed. |
| Research78 | `findings/2026-10-26-supply-provider-gui78.md`: tile scan, first/last city sortedstock, first/second/last fleet, callback skipped/duplicate/invalid rows. Paid staging survives provider switch and Buy can make stocknegative. These unsafe original defects need explicit owner/design disposition, not automatic replication. Preserve provider/money QoL. |
| Research79 | `findings/2026-10-26-carried-army-supply-gui79.md`: cargo binding supported, carrier supplies itself, actual move synchronizes coords, immediate effects surviveClose; FleetSupply separate. Invalid stale-coordinate/marker controls excluded. |
| Research80 | `findings/2026-10-26-tactical-enemy-click-gui80.md`: enemy inspection separate from own selection; adjacent positive-move target assignment, actualzero inspection, rightshoot/ownclear/Cancel distinct. No enemy private-field leak demonstrated. Model no-selection clickNone differs, deployed scene untested. |
| Research81 | `findings/2026-10-26-recruitment-default-gui81.md`: capital/queue-count+1 score, strict firstlisted ties; Allcities does not replace original default. T162 explicitly chooses other default UX; preserve owner policy. |

## Audit/reproduction map

All outputs use exclusive versioned names. Never delete a save, including a
failed attempt; never overwrite a measurement. Preserve originals and private
hashes. Commit/push each batch and <=30min. Each public row cites its original-
written SAV endpoints and turn0734. All private original artifacts remain at
ignored`artifacts/run-exp-restrictions85/private-<batch>/`.

- `audit-supply-v1.json`:17pairs, whole parsed-world equality except tested
  resources and camera. `audit-supply-marker-v3.json` +`coherent-city-marker-v1.json`:
  two coherent foreign-marker repeats.
- `audit-money-ok-v1.json`:14pairs, whole parsed-world equality except money/
  supply/view and cancelled Split tombstone.
- `audit-units-v1.json`:17verified-selection unit/disband pairs, ordered
  admission/refusal, global-vs-working timing, donor/receiver moves and Cancel.
- `prior-controls-audit-v1.json`:6historical patched-Wine pairs reread(U1/U3/U3b,
  c1/c4/c5), no fresh original run.
- `audit-transport-pilot-v1.json`,`audit-transport-v1.json`:9pairs, separate
  embark/hire boundaries, opening gate, links, moves, purse, offer lifecycle.
- `audit-sweep-v1.json`:7pairs, fleet money/ship-only/Cancel and two carried
  Disband menu paths. No claim those menu paths reached Disband handler.
- `audit-gui-v1.json`:9recruitment+5natural/switch providers+14tactical pairs;
  includes two load-reset positive-move repeats, not false zero evidence.
- `audit-carried-v1.json`:6coherent pairs with marker/link/coords/supplier checks.
- `audit-gui-v2.json` adds explicit own-right-clear cases, verifies all other tactical slots/non-target grid cells and covers30GUIpairs; prior audit remains immutable. Failed/partial attempts remain named in notes and reports.

Original runtime: stock unmodified EXE, Wine10.0 Ubuntu10.0~repack-12ubuntu1,
win32, three private prefixes/displays757/758/759. Earlier same-task server
reuse/bind failures documented; final runner requires creating its own server,
never attaches an unknown display. No owner game interruption or Windows use.
No observer patch or game-memory writes. GUI80 uses synthetic saved battle
blocks, no Endturn/AI/battle completion. Original load refills moves/counter;
actual before-state and truezero-through-shooting are recorded, not assumed.

Python/C runners are in`runs/experiments/restrictions85/`. `setup.py` copies a
retained stopped private prefix, preserving symlinks (never traverse z:). Existing
paths require adjustment on another host; do not install system packages or
launch an original as a compatibility check. Actual experiments require the
owner authorization recorded on211 and runtime permissions for private Wine/
Xvfb/proc access. `--version` must be fresh; `--cases` narrows a planned batch.

Native public synthetic aid: exact unchanged85 code`AuditFromBrief.cs`/`Audit.csproj`;
`NativeExtra.cs` for actual model/dispatcher calls;
`NativeGui.cs` for GUI-free production model comparisons. Reference the archived
public source under ignored`artifacts/run-exp-restrictions85/remake4d70275a`.
Build with local.NET10, then copy output under that source tree before executing
from its root (testbed searches upward for IC2.sln). Authoritative logs:
`native-probe-v2.txt`,`native-extra-v4.txt`,`native-gui-v3.txt`.
Compile/runtime failures and incorrect earlier fixture variants retained and
qualified, not silently replaced. No full-suite/native Godot/deployed-build/
native Windows acceptance; self-review only.

## Remaining implementation/owner questions

- Express partial success plus refusals in remake commands; permit unchanged
  confirmedOK without making arbitrary zero orders actions.
- Resolve signed paid amount vs existing buy-command request semantics.
- Preserve T162 opening UX, T207 reserve, Improved affordability, no-wrap policy,
 1340Transfer-ships refusals,565last-unit/name policy and T216 safe refusal.
- Choose safe handling for original invalid provider rows and negative-stock
  staged-switch exploit; source truth does not authorize unsafe parity.
- Carried whole-army Disband through another legitimate original selection
  route remains unproved; do not request a correction without that control.
- No new Windows acceptance or running-build identity checks were performed.
  Promotion/implementation acceptance belongs to Research/Main, not these rows.
