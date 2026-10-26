# Human embark and mercenary hire separately truncate troop capacity

**Status:** Promoted by [Research PR86](https://github.com/diegoami/imperial-conquest-2-research/pull/86), merge `38259d83f323bf6cbad1a4ddf2cc47ecd69f719f`. The [canonical report](https://github.com/diegoami/imperial-conquest-2-research/blob/38259d83f323bf6cbad1a4ddf2cc47ecd69f719f/docs/reports/2026-10-26-human-transport-rounding83.md) and [independent verification receipt](https://github.com/diegoami/imperial-conquest-2-research/blob/38259d83f323bf6cbad1a4ddf2cc47ecd69f719f/docs/data/restrictions85-intake-v1.json) retain the evidence qualifications below.

**Tag:** [confirmed, partial], nine stock-original Wine UI controls. Research83,
parent85. Original army-transfer rounding was already promoted; this report
establishes **each different caller** and does not derive their results from it.

## Observed matrix

Private synthetic copies of`fleet-split-antium-0734.SAV`, turn0734, fleet2:
10ships, valid ownership/adjacency, enough moves. No End turn or battle.

| Resulting troops | Human embark | Mercenary hire while aboard |
|---:|---|---|
| 5000 | accepted | accepted; army4000→5000 |
| 5001 | accepted | accepted; army4000→5001 |
| 5499 | accepted | accepted; army4000→5499 |
| 5500 | refused | dialog opens, individual offer refused |

Human embark acceptance snaps the army onto the carrier, sets army cell−1 and
fleet's army pointer0, and sets **both moves0**. Refused5500 keeps army on land,
fleet empty and both moves7. Original refusal: "The army is too large for this
fleet ?"; exact private screenshot retained, OCR in public row may be imperfect.

Hire: supply100, purse30000, one distinguishable synthetic offer at adjacent
own Antium. Base army4000, offer1000/1001/1499/1500. Dialog opens for all four;
accepted offers disappear, purse30000 and both moves7 remain unchanged, existing
carrier link is retained. At5500 the offer/army remain; "This fleet has too
little space for these mercenaries." is the per-offer refusal. No charge is
inferred from the display; actual purse checked, consistent with promoted
hire-price-is-a-gate evidence.

**Separate opening gate:** base army5500 already aboard10ships, offer500:
no recruitment dialog, "Your fleet cannot carry any more troops." (R12).
This is not the per-offer R27 refusal and not a post-hire cleanup. Existing links,
units, money and moves remain. One cannot test R27 with an already failing R12.

## Exact code-derived rules, verified by these controls

- Human `TUnitMap_SelectUnit @004466CC`, friendly empty fleet branch:
  refuse when `ships < total troops div500`; otherwise`FUN_0044B79C` embarks.
- `TUnitMap_RecruitMercenaries @00446FF4`: resolve selected carrier's army,
  check slot19,100000troops, enemy city, supply, **then** opening fleet gate
  `troops div500 <= ships`.
- `TRecruitMercs_RecruitMercUnit @00441360`: purse gate,100000troops,
  then refuse when`ships < (troops+offered troops) div500`, before inserting unit.

For nonnegative legal troop counts, ten ships admit up to5499 and refuse5500.
An exact multiplication ceiling5000 is not equivalent. This only establishes
the human callers above. AI over-capacity allocation, overflow cleanup, landing,
transfer and owner-approved T216 refusal remain separate.

## Evidence / implementation handoff

`runs/experiments/data/run-exp-restrictions85/`:
`transport-pilot-v1_{embark,hire}-5001.json` (2cases) and
`transport-v2_*.json` (7cases); audits`audit-transport-pilot-v1.json` and
`audit-transport-v1.json` reparse18original-written saves, verify links, moves,
resulting troops, hire purse and offer lifecycle. Primary saved endpoints:
`transport-pilot-v1_embark-5001_before.SAV` / `_after.SAV` and
`transport-pilot-v1_hire-5001_before.SAV` / `_after.SAV`, turn0734.
Runners`runs/experiments/restrictions85/transport.py`,`common.py`.
Private originals/screenshots/identities/hashes stay in ignored
`artifacts/run-exp-restrictions85/private-<batch>/`; no public release.

Native remake4d70275aac4e155c0370a3ee23525cf34450a908 production dispatcher,
`native-extra-v3.txt`/v4: human embark and hire separately accept5000 but refuse
5001/5499/5500 (`naval.army-too-large`,`mercenary.fleet-no-space`). Synthetic
native world supplies a valid nearby own city/offer and human seat. These are
exact command executions, not full Godot/installed-build acceptance. Extra probe
v2 has the same valid transport rows but its separate fleet-money fixture had
wrong purse field order; v3/v4 fix that unrelated fixture. All versions retained.

Remake locations:`EmbarkArmyCommandHandler` capacity branch and
`HireMercenaryCommandHandler` post-hire fleet check. Intake via existing
Research83/85; no new implementation issue presumed until consolidation and live
deduplication. Use loaded divisor with the original division order for each
human caller, retain opening-vs-offer gates and all other existing policies.
Do not broaden the result into an AI redesign or generic transport helper rule.

## Provenance / limits

Stock unmodified original identity verified privately; Wine10.0 Ubuntu
10.0~repack-12ubuntu1, win32, task-owned Xvfb:757,1280×1024. Actual click/menu
entry and original saved endpoints; read-only memory verifies record timing.
Synthetic unit/link/offer/map edits documented privately; originals preserved.
No original observer patch, native Windows, owner game access, arbitrary
handler injection or remake change. Opening5500 control deliberately stages an overcapacity army; no natural lifecycle into that state was played by this study.
