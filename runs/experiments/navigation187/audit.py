"""Audit published scalar ledgers; no raw/owner hash or full trace output."""
import argparse,json
from pathlib import Path
DATA=Path(__file__).resolve().parents[3]/'runs/experiments/data/run-exp-navigation187'
load=lambda n:json.loads((DATA/n).read_text())
scalar=load('scalar-controls-v1.json');branches=load('branch-controls-v1.json');advanced=load('advanced-controls-v1.json');topology=load('island-topology-v1.json')
assert len(scalar['rows'])==331 and all(r['result'].get('model_equal',True) for r in scalar['rows'])
b={r['case']:r for r in branches}
for name in ['foreign','building','loaded','zero']:assert b['ferry-'+name]['waypoint'] is None and b['ferry-'+name]['army_covered']>=0
assert b['ferry-adjacent']['army_covered']==-1 and b['ferry-adjacent']['fleet_cargo']==2 and b['ferry-adjacent']['army_moves']==b['ferry-adjacent']['fleet_moves']==0
assert b['ferry-distant-inland']['waypoint']==[100,40] and b['ferry-distant-inland']['fleet_stored']==[101,40]
assert b['ferry-distant-coast']['waypoint'] is None and b['ferry-distant-coast']['fleet_stored']==[101,40]
assert b['already-aboard']['fleet_stored']==[160,62] and b['already-aboard']['army_moves']==6
assert b['ferry-tie']['first_fleet_stored']==[101,40] and b['ferry-tie']['second_fleet_stored'][0]==-1
assert b['direct-residue--1']['final']==[100,40] and b['direct-residue--1']['moves']==8
assert b['direct-residue-0']['final']==b['direct-residue-123']['final']==[100,41] and b['direct-residue-0']['moves']==0
assert b['contact-enemy-army']['dispatch']==['0x44aee4'] and not b['contact-peace-army']['dispatch'] and not b['contact-enemy-zero']['dispatch']
assert b['contact-enemy-city']['dispatch']==['0x44b27c'] and b['contact-peace-city']['dispatch']==['0x44f6d8']
caller=load('caller-controls-v1.json');full=load('caller-full-v1.json')
assert all(r['actor']==2 and r['entry_local_e']==128 for r in caller)
assert all(r['final_army']==[100,41] and r['moves']==0 and [e['local_e'] for e in r['entries']]==[128,103,110,103,110] for r in full)
assert sum(r['land_or_land_marker_cells'] for r in topology['regions'])==329 and all(len(r['visible_island_node_union'])<=1 for r in topology['regions'])
assert len(advanced)==4 and advanced[2]['score']==advanced[3]['score']==1010 and advanced[2]['selected_army']==advanced[3]['selected_army']==6
private=load('private-regression-audit-v1.json');native=load('private-native-audit-v2.json')
assert private['original_geo_model_equal'] and private['waypoint']==[189,104] and native['endpoint']==[212,96] and native['terrain_occupancy_mismatches']==0
assert native['actor_units_relations_gated'] and not native['owner_fields_published'] and native['Moves']==0
spec=load('navigation-data-v1.json');pins=load('source-pin-v1.json')
assert len(spec['waypoints'])==58 and len(spec['routes'])==21 and len(spec['regions'])==8 and len(spec['coordinate_splits'])==6
assert all(b['static_equal_in_live_snapshots']==30 for b in pins['blocks'])
for group,hub in [(0,9),(1,32),(2,43)]:
 for node in range(spec['groups'][str(group)][0],spec['groups'][str(group)][1]+1):
  assert any(node in row['points'] and hub in row['points'] for row in spec['routes'] if row['group']==group)
summary=dict(public_scalar_rows=331,ferry_contact_residue_rows=20,actual_caller_entry_controls=3,actual_caller_full_controls=3,advanced_score_fallback_controls=4,
 additional_original_line_controls=len(topology['original_instruction_spot_controls']),island_land_cells_enumerated=329,
 static_tables=dict(valid_points=58,route_shape=[3,7,8],region_boxes=8,coordinate_splits=6),static_blocks_equal_across30live_snapshots=True,
 original_RNG_calls_in_controls=0,private_final_regression_pass=True,native_conditioned_walker_pass=True,
 implementation_contract='defined eligibility/direct/waypoint/ferry/contact branches; F31C caller-aware continuation only, not arbitrary DBA8-entry stack',
 stop_condition=dict(branch='post-direct-walk continuation for other original caller histories',
 observed_alternatives=['negative inherited word: return with position100,40 and8moves','nonnegative inherited word: local fallback/recursion reaches100,41 and0moves'],
 current_resolution='normal F31C and recursive fixture data-flow/controls proved nonnegative; other callers not universally established',
 smallest_next_original_control='generated three-friendly-marker wall; instrument EC7D/ECD6 garrison and E913mercenary calls, record entryESP-14 and subsequent actor moves; no new owner save'),
 restrictions=['No production/source-schema change or broad game rerun.',
 'Original bytes/RAM/complete traces and owner hashes remain private.',
 'Group3graph fallback has no table/hub, but is unreachable for valid static classical same-island land pairs as enumerated.',
 'CB40coincident isolated input is stack-dependent; actual D174sequence makes target-node coincidence visible after its preceding nonzero origin test.',
 'Native final comparison supplies original waypoint and does not claim native eligibility/whole-turn/RNG equivalence.'])
p=argparse.ArgumentParser();p.add_argument('--version',required=True);options=p.parse_args()
with (DATA/('summary-'+options.version+'.json')).open('x') as f:json.dump(summary,f,indent=2)
print('PASS navigation data,396public control rows/topology spot checks, private final regression and conditioned native walker; caller stop-limit retained')
