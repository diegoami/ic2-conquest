# Enemy click inspection and melee-target precedence are separate in the original

**Status:** Promoted by [Research PR86](https://github.com/diegoami/imperial-conquest-2-research/pull/86), merge `38259d83f323bf6cbad1a4ddf2cc47ecd69f719f`. The [canonical report](https://github.com/diegoami/imperial-conquest-2-research/blob/38259d83f323bf6cbad1a4ddf2cc47ecd69f719f/docs/reports/2026-10-26-tactical-enemy-click-gui80.md) and [independent verification receipt](https://github.com/diegoami/imperial-conquest-2-research/blob/38259d83f323bf6cbad1a4ddf2cc47ecd69f719f/docs/data/restrictions85-intake-v1.json) retain the evidence qualifications below.

**Tag:** [confirmed, partial], stock-original Wine synthetic tactical GUI controls.
Research80/82, not a combat-arithmetic or computer-general investigation.
Existing tactical reports were read first; this resolves their ambiguous "a unit"
selection prose. No original/native Windows battle acceptance is claimed.

## Exact original caller and observed precedence

`TBattleMap_OnMapClick00437308` sends a left click on any occupied cell to
`SelectUnit0043747C`. That calls per-unit details`00438504` **before** deciding
whether the unit is friendly. It does not need to select an enemy to inspect it.

| State/action | Original result |
|---|---|
| Left enemy, no friendly selected | enemy basic details; selected slot stays−1; cursor points at clicked cell |
| Friendly selected, enemy distant | enemy basic details; friendly selection cleared; no target assigned |
| Friendly selected, adjacent enemy, movespositive | own unit's target becomes enemy slot; selection/cursor cleared; own details show planned enemy target |
| Friendly selected, adjacent enemy, actual0moves | enemy basic details; selection cleared; no target assigned |
| Right enemy, no friendly selected | no inspection/action |
| Right enemy, friendly has moves/shots and range | actual shot, immediate loss feedback; moves and shots each decrease1 for these archer controls |
| Right own unit with an assigned target | clears that unit's target; distinct from Cancel selection |
| Cancel selection toolbar | clears selection/cursor/details; **keeps** an already assigned target |

Placement and movement phases were tested separately. Left-click target-setting
is not itself an exchange: no troops/moves/shots change there; melee is resolved
at the separate turn boundary, which was not executed. Right-click shooting is
an actual exchange even in these loaded placement-phase inputs; no AI or battle
completion was allowed. Do not infer a complete natural placement lifecycle from
a deliberately loaded tactical snapshot.

## What information is exposed

Original per-unit enemy click: nation, name/mercenary marker, type, troops.
**No enemy quality, morale, moves or shots**. Own click adds quality/morale words,
moves and shots; after targeting, the planned-enemy section adds only name,
type and troop count. Enemy roster button`EnemyUnitDetails004378F8` shows
name/mercenary marker,type,troops. Actual shot feedback identifies both units,
types,troops and troop losses; it does not expose enemy quality/morale/moves/
shots. Those routes were recorded independently, not assumed interchangeable.

No demonstrated enemy-information leak in the pinned remake was found. Existing
`EnemyRows`,`SelectedLines`,`ParticipantLines` withhold the relevant private
fields; its enemy hover/roster presentation remains a separate useful route.

## Controls, evidence and corrections

Private synthetic tactical block on a copy of`fleet-split-antium-0734.SAV`,turn0734:
own3000archers+2000HI,enemy2000HI+3000archers; adjacent/distant placement varied.
No live memory write or observer patch. The original loads, initializes/refills
moves and advances the saved input counter1 to the observed before-counter2;
**both original-written endpoints stay at2 throughout the tested clicks**.

A raw staged0moves field is refreshed to4 on load. The two early zero-labelled
rows are retained **as positive-move controls**, not evidence of zero behavior.
Truezero controls instead use four real original right-click shots against a
surviving30000HI synthetic target, then reselect the archer at actual0moves.
The subsequent enemy click inspects without assigning a target in both phases.
No memory alteration was used to manufacture the branch.

Data`runs/experiments/data/run-exp-restrictions85/`:
`gui80-pilot-v1_movement-enemy-no-selection.json`,11`gui80-v2-cNN_*.json`,
2`gui80-zero-v3-cNN_*.json`,and2explicit`gui80-clear-v4-cNN_*.json` controls.
Thus14unique matrix controls plus2load-reset repeats. Each has original Save as
before/after endpoints and phase/selection/cursor/target/moves/shots/info/RNG
observations; four live slots are synthetic and all original bytes stay private.
Examples:`gui80-pilot-v1_movement-enemy-no-selection_before.SAV` / `_after.SAV`,
`gui80-zero-v3-c01_movement-enemy-selected-zero-moves_before.SAV` / `_after.SAV`.

Runners`runs/experiments/restrictions85/tactical_gui.py`,`common.py`;
`audit-gui-v1.json` covers first14executions; `audit-gui-v2.json` adds right-own-clear controls, verifies every other tactical slot and non-target grid cell stays unchanged, and reparses all32tactical endpoint saves. Original screenshots/full states/identities/hashes and
missing-handler disassembly stay ignored under
`artifacts/run-exp-restrictions85/private-gui80-*/`. No public binary release.

## Remake comparison and implementation handoff

Pinned4d70275a production`TacticalBattleViewModel.ForLeftClick` returnsNone for an
enemy with no own selection. `native-gui-v3.txt` verifies that exact branch;
original corresponding click shows basic details while selected remains−1.
Thus inspect intent and friendly command selection should be modeled separately
if original click parity is desired. Do not introduce an enemy command-selection
state merely to display its basic details.

With friendly selection the model returnsAttack for any occupied enemy and
leaves eligibility to engine; original also clears friendly selection when
inspection replaces a noneligible attack. Any final scene-level correction needs
to verify rejection/selection behavior there, beyond this Godot-free model probe.
The report does not claim deployed GUI verification. Existing hover inspection,
owner-approved layout/colors/animation and safe morale-word bounds remain policy;
no request to remove them or expose hidden enemy fields.

## Limits

Stock unmodified original privately verified;Wine10.0 Ubuntu10.0~repack-12ubuntu1,
win32,own1280×1024Xvfb:759,one fresh process per case. Real UI clicks and
original-written saves,read-only memory for observation. Synthetic troop/phase/
position inputs; no native Windows, owner running game, Endturn command, natural
battle-entry validation, AI general, arithmetic comparison or remake modification.
No external reviewer. Right-click range extremes, dead units, routed removal,
hotseat perspective and roster click-to-navigation are outside this bounded pass.
