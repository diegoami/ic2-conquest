# Original recruitment default scores queued units with a capital bonus; retain T162 design

**Status:** Promoted by [Research PR86](https://github.com/diegoami/imperial-conquest-2-research/pull/86), merge `38259d83f323bf6cbad1a4ddf2cc47ecd69f719f`. The [canonical report](https://github.com/diegoami/imperial-conquest-2-research/blob/38259d83f323bf6cbad1a4ddf2cc47ecd69f719f/docs/reports/2026-10-26-recruitment-default-gui81.md) and [independent verification receipt](https://github.com/diegoami/imperial-conquest-2-research/blob/38259d83f323bf6cbad1a4ddf2cc47ecd69f719f/docs/data/restrictions85-intake-v1.json) retain the evidence qualifications below.

**Tag:** [confirmed, partial], nine stock-original Wine controls. Research81/82.
Reconciles the older capital/most-training wording with exact initialization and
current T162 policy. No remake change is requested by this report.

## Original caller: exact decision rule

`TArmyRecruits_InitializeForm0045489C` calls list builder`004544E0`, then
`SetCityRecruits0045495C`. Disassembly of the missing list builder was retained
privately; the rule is independent of remake tests/task wording:

- Build eligible towns in the nation's **city-list order**, keeping the existing
  promoted capital/fortification/training eligibility.
- If recruitment slot0's troops are0, choose the capital. This is tested for
  no queues; a gapped table with later queues is code-derived/unplayed.
- Otherwise score each eligible town: **occupied queued-unit count +1 if capital**.
  Select the greatest score; use strict greater-than, so the **first listed**
  town keeps a tied score. Troop amounts/readiness and queue-slot order do not
  break ties in this code.
- More than one town with queues inserts All cities at the top, **without
  replacing the chosen city**. Select the row that maps to the chosen ID.
- `SetCityRecruits` displays that town's queue and "Create unit at <town>".
  If All cities is manually chosen, creation destination resolves to capital;
  this previously promoted rule is preserved, not rediscovered here.

## Nine runtime controls

Private`fleet-split-antium-0734.SAV`,turn0734. Qualified noncapital80Tarquinii is
placed before capital85Rome in the nation's list;90AlbaFucens supplies another
tie control. Queue rows staged independently of city order. Original selects:

| Queue pattern | Selected town |
|---|---|
| none | Rome85 |
| capital only | Rome85 |
| Tarquinii only | Tarquinii80 |
| Tarquinii1unit,Rome2 | Rome85 |
| Tarquinii1,Rome1 | Rome85 (score1vs2) |
| same,queue slots reversed | Rome85 |
| Tarquinii1,Alba1,capital0 | Tarquinii80 (first score1tie) |
| same,queue slots reversed | Tarquinii80 |
| Tarquinii2,Rome1 | Tarquinii80 (score2tie,firstlisted) |

For each: record actual selected list row, visible training rows and selected
city field+23C; close/reopen, manually select another town, close/reopen again.
The default is recalculated, not persisted from manual selection. A small
accepted3000LI recruit goes to the selected town in all9cases. Private opening
screenshots retain the actual Create unit at label; source binding and the
original-written queue endpoint independently establish its destination.

## Current remake: an explicit design difference

Pinned4d70275a`RecruitUnitDialogModel.DefaultCity` is first listed;
`RecruitUnitDialog` opens All cities when its T162 condition applies. Production
model probe`native-gui-v3.txt` confirms first-listed on no queue and Allcities
on two-town queues. That differs from the original decision rule above.

**Do not silently replace it.** Archived T162 (`brief-v1/policy-T162.md`), planned
from owner report1001 and implemented PR1014, expressly opens All cities when
training away from capital would otherwise be hidden; otherwise it preserves
its then-current default. Live1001 decision comments and archivedtask retained
in`policy-main1001.json`. Current T166 membership still requires two distinct
queued towns, consistent with promoted membership evidence. This is a documented
UX policy, not newly proved original behavior. Existing Max/full-battalion
policy, readiness, mobilisation, debt, eligibility and cost rules remain intact.

Intake disposition: correct the old broad prose to the exact scoring rule and
record the T162 divergence. An original-default option or a change to current
opening policy needs an explicit owner decision, not an automatic fidelity fix.

## Evidence / limits

Data`runs/experiments/data/run-exp-restrictions85/gui81-v3_*.json`; nine before/
after pairs reparsed in`audit-gui-v1.json`, including queue destination, score,
visible count and every reopen observation. Primary:
`gui81-v3_capital-bias-tie-score_before.SAV` / `_after.SAV`,turn0734.
Runners`recruit.py`,`lists.c`,`common.py` under`runs/experiments/restrictions85/`.
Original full files/images/identities/hashes and disassembly private under
ignored`artifacts/run-exp-restrictions85/`. Two runner pilots failed on a toolbar
signature and wrong window title; both retained, neither counted as recruitment.

Stock unmodified original privately verified;Wine10.0 Ubuntu10.0~repack-12ubuntu1,
win32,task-owned1280×1024Xvfb. Actual original menu/list/button actions; read-only
form fields; no memory patch, native Windows, owner desktop, Endturn, remake
modification or external reviewer. Gapped queues and malformed duplicate town
lists are code-derived/unplayed; no claim of exhaustive recruitment lifecycle.
