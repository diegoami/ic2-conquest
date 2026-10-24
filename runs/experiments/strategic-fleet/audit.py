"""Verify bounded fleet results without equating proposals and execution."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DATA=ROOT/'runs/experiments/data/run-exp-strategic-fleet'
old={r['case']:r for r in json.loads((DATA/'original-fleet-controls-v1.json').read_text())}
result=json.loads((DATA/'native-fleet-controls-v1.json').read_text());new={r['caseName']:r for r in result['rows']}
assert len(old)==len(new)==14 and all(x['gate'] for x in new.values())
for case in ['peace','trade','alliance','war-stronger','score100']:
 assert old[case]['original']['site']==0x44f6be
for case in ['war','war-weaker','score101']:assert old[case]['original']['site']==0x44f69a
for case in ['no-moves','actor-construction']:
 assert not old[case]['original'] and not new[case]['proposals']
for case,goal in [('stored-a',[48,66]),('stored-b',[47,67])]:
 assert old[case]['original']['site']==0x44f667 and old[case]['original']['goal']==goal and not old[case]['draws']
assert new['peace']['nativeStateSha256']==new['stored-a']['nativeStateSha256']==new['stored-b']['nativeStateSha256']
assert new['peace']['proposals']==new['stored-a']['proposals']==new['stored-b']['proposals']
assert all(len(new[c]['proposals'])==1 for c in ['peace','trade','alliance','war','war-stronger','war-weaker'])
assert all(not new[c]['proposals'] for c in ['same-owner','target-construction','score100','score101'])
summary=dict(cases=14,fleet_and_relation_gate_checks=result['checkedFields'],original_game_launched=False,native_game_launched=False,
 original_strength_rng_executed=True,original_stored_goals=[[48,66],[47,67]],
 identical_imported_decision_state_for_absent_and_two_stored_routes=True,
 identical_native_march_proposals_for_those_three=True,
 original_peace_trade_alliance_choose_port=True,native_peace_trade_alliance_offer_foreign_fleet_march=True,
 original_hunt_boundary_scores=[100,101],zero_moves_and_construction_outer_gates_match=True,
 classification=dict(fleet_march_weights='explicitly designed native policy; not an unintended defect claim',
 stored_destination='documented absent native field/canonical export reset; faithful feature/state-support gap'),
 limits=['Synthetic fleet-phase controls, not fresh original live boundary traces.',
 'Native measurements are offered fleet marches, not full greedy-loop accepted commands.',
 'No matched naval combat/RNG-stream equivalence or full fleet strategy acceptance.',
 'Ports are original measured choices; native port-selection parity not established.'])
with (DATA/'summary-v1.json').open('x') as f:json.dump(summary,f,indent=2)
print('PASS14 fleet controls; stored-route state-support gap isolated; designed proposals kept distinct from accepted choices')
