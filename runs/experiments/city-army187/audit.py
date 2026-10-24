"""Public scalar publication audit; never opens owner assets or emits hashes."""
import argparse,json
from pathlib import Path
D=Path(__file__).resolve().parents[3]/'runs/experiments/data/run-exp-city-army187';load=lambda n:json.loads((D/n).read_text())
o=load('original-scalar-v1.json');n=load('native-scalar-v3.json');p=load('projection-gate-v1.json');c=load('component-gate-v1.json');grid=load('branch-grid-native-v2.json')
assert o['original_city']==dict(target=287,score=495,distance=28) and o['original_enemy']==dict(target=24,score=828,distance=28)
assert o['original_branch']==o['scorer_sequence_branch'] and o['original_branch']['kind']=='AttackArmy' and o['original_branch']['recorded_enemy_destination_matches']
assert o['read_only_complete_RAM_identity'] and o['original_RNG_calls']==0 and c['original_RNG_calls']==0 and c['complete_RAM_identity']
assert n['input_identity_gate_passed'] and n['checked_fields']==2908 and n['terrain_and_occupancy_cells_checked']==44800 and n['terrain_and_occupancy_mismatches']==0
assert p['map_city_army_fleet_nation_queue_relation_mercenary_bytes_equal'] and p['turn_order_and_seat_calendar_equal'] and p['decoded_JSON_equals_container']
assert n['city_defense_comparisons']==40 and n['city_defense_mismatches']==n['adjusted_defense_mismatches']==0 and n['assault_strength']==o['original_assault_strength']
assert not n['original_city_reachable'] and n['original_eligible_native_unreachable']==36 and n['native_city']==dict(target=253,Score=330,Distance=6,Skipped=36)
assert n['native_enemy']==dict(target=24,Score=828,Distance=28) and n['native_branch']==n['military_phase_branch']=='AttackCity'
assert n['original_score_fed_branch']==n['original_city_only_fed_branch']==n['original_eligibility_only_branch']=='AttackArmy'
assert n['original_eligibility_only_city']==dict(target=287,score=495,distance=28) and n['diagnostic_native_formula_matches_production_choice']
assert n['original_candidate_observations']==40 and n['native_empty_region_formula_mismatches']==5 and n['original_geography_formula_mismatches']==0
assert len(grid)==32 and sum(not r['equal'] for r in grid)==7 and all(r['army_score']==100 or r['city_score']==100 for r in grid if not r['equal'])
assert load('branch-grid-original-v1.json')==load('branch-grid-original-v2.json')
summary=dict(private_same_boundary=True,import_projection_and_relevant_input_gates_pass=True,native_import_fields=2908,terrain_occupancy_cells=44800,defense_candidate_matches=40,assault_strength_equal=True,primary_cause='designed city direct-walk eligibility rejects original winner and changes final city-versus-army branch',secondary='empty geographic map changes5candidate scores, not the winning city after eligibility alignment in this state',branch_predicates_not_the_cause_of_private_case=True,independent_score100_controls=32,independent_score100_mismatches=7,followups=dict(city_policy=1417,score100_boundary=1418),limits=['same-state conditional, not whole End turn or command acceptance','diagnostic eligibility-only formula model, not production patch','32 synthetic branch rows are score-fed, not naturally reached campaign states','no owner paths/hashes/full states/raw traces published','Research promotion and Main scope review before behavior changes'])
p=argparse.ArgumentParser();p.add_argument('--version',required=True);a=p.parse_args()
with (D/('summary-'+a.version+'.json')).open('x') as f:json.dump(summary,f,indent=2)
print('PASS public scalar attribution, complete projection gates and32 original/native branch controls')
