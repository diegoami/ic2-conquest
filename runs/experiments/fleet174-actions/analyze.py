"""Accepted-action/movement analysis; preserve distinct comparison boundaries."""
import argparse,collections,csv,json
from common import *
p=argparse.ArgumentParser();p.add_argument('--version',required=True);options=p.parse_args()
old={r['case']:r for r in json.loads((DATA/'original-actions-v1.json').read_text())}
new={r['caseName']:r for r in json.loads((DATA/'native-actions-v2.json').read_text())}
paths=json.loads((DATA/'native-paths-v1.json').read_text());directPaths={r['caseName']:r for r in paths if r['label']=='conditioned-direct'}
assert len(old)==len(new)==23 and all(r['status'] in ['complete','stopped-before-naval-combat'] for r in old.values())
rows=[]
for name,o in old.items():
 n=new[name];d=n['direct'];stores=o['coordinate_stores'];assert len(stores)%2==0
 entered=[]
 for i in range(0,len(stores),2):
  assert stores[i]['field']=='x' and stores[i+1]['field']=='y';entered.append([stores[i]['value'],stores[i+1]['value']])
 r=dict(case=name,original_status=o['status'],original_destination=o['native_direct_goal'],original_terminal=list(o['final_fleet0'][:2]),original_moves=o['final_fleet0'][6],
  original_steps=len(entered),native_direct_present=d is not None,native_direct_accepted=None,native_path_equal=None,native_terminal_equal=None,native_moves_equal=None,native_terminal=None,native_moves=None)
 if d is not None:
  assert directPaths[name]['canonical_state_equal']
  nativeEntered=[[p['X'],p['Y']] for route in directPaths[name]['routes'] for p in route['EnteredCells']]
  r.update(native_direct_accepted=d['IsAccepted'],native_terminal=[d['after']['X'],d['after']['Y']],native_moves=d['after']['Moves'],
   native_path_equal=entered==nativeEntered,native_terminal_equal=list(o['final_fleet0'][:2])==[d['after']['X'],d['after']['Y']],native_moves_equal=o['final_fleet0'][6]==d['after']['Moves'])
 rows.append(r)
assert new['rough-ai-one']['direct']['after']['Moves']==1 and old['rough-ai-one']['final_fleet0'][6]==0
assert new['rough-human-one']['direct']['after']['Moves']==old['rough-human-one']['final_fleet0'][6]==1
assert new['rough-ai-three']['direct']['after']['Moves']==old['rough-ai-three']['final_fleet0'][6]==0
for name in ['stored-zero','cargo-zero']:
 assert old[name]['movement_calls'][0]['moves']==0 and old[name]['final_fleet0'][:2]==[49,62] and old[name]['stored_route']==[48,66]
 assert new[name]['direct']['IsRejected'] and new[name]['direct']['after']['Moves']==0
for name in ['cargo-positive','cargo-zero']:
 o=old[name];d=new[name]['direct'];cargo=d['after']['cargo']
 assert o['final_army3'][:2]==o['final_fleet0'][:2] and cargo['X']==d['after']['X'] and cargo['Y']==d['after']['Y']
 assert cargo['AboardFleetId']=='fleet-0' and cargo['CoveredTileCode'] is None
 assert list(o['final_army3'][:2])==[cargo['X'],cargo['Y']]
live=BASE/'live'
for part in ['before','after']:
 assert next((live/'live-rom-hook-v1').glob('*-'+part+'.SAV')).read_bytes()==next((live/'live-rom-plain-v1').glob('*-'+part+'.SAV')).read_bytes()
gate=json.loads((DATA/'live-phase-replay-v1.json').read_text());assert len(gate)==15 and all(r['whole_captured_RAM_equal'] for r in gate)
meta=json.loads((DATA/'live-rom-hook-v1/phase-records.json').read_text());moving=0
for i in range(0,30,2):
 a=(live/'live-rom-hook-v1/snapshots'/f'{i:03}.ram').read_bytes();z=(live/'live-rom-hook-v1/snapshots'/f'{i+1:03}.ram').read_bytes()
 nf=short(a,0x4a0326)
 if any(xy(a,0x49c26c+26*k)!=xy(z,0x49c26c+26*k) for k in range(nf)):moving+=1
ports=json.loads((DATA/'accepted-port-affordability-v1.json').read_text());assert ports[0]['IsAccepted'] is False and ports[1]['IsAccepted'] is True
accepted=[]
for name,n in new.items():
 assert n['ai']['CommandsRejected']==0 and n['ai']['ProjectionMismatches']==0 and not n['ai']['HitActionCap']
 count=0
 for c in n['ai']['commands']:
  if c['Kind'] not in ['naval.move-fleet','battle.attack-fleet']:continue
  assert c['IsAccepted'];prefix=BASE/'native-v2'/name/f'accepted-fleet-{count}3-before.json';count+=1
  before=json.loads(prefix.read_text());relation=before['Relations']['Matrix'][1][3]
  accepted.append(dict(case=name,kind=c['Kind'],goal=c['command'].get('X') is not None and [c['command']['X'],c['command']['Y']],relation_at_dispatch=relation,
   status='actually accepted in full native AiTurn; phase history differs from original fleet-only run'))
for case,relation in [('phase-peace',0),('phase-trade',1),('phase-alliance',2)]:
 assert any(r['case']==case and r['kind']=='naval.move-fleet' and r['relation_at_dispatch']==relation for r in accepted)
for kind,want in [('ai',[0x49c278]),('human',[])]:
 folder=BASE/'affordability-v1'/kind;a=(folder/'before.ram').read_bytes();z=(folder/'after.ram').read_bytes()
 assert [RAM_BASE+i for i,(x,y) in enumerate(zip(a,z)) if x!=y]==want
assert all(r['canonical_state_equal'] for r in paths)
summary=dict(synthetic_original_cases=23,completed_original_phases_or_walks=sum(r['status']=='complete' for r in old.values()),
 stopped_before_naval_combat=sum(r['status']=='stopped-before-naval-combat' for r in old.values()),
 native_full_AI_runs=23,accepted_native_fleet_moves=sum(r['kind']=='naval.move-fleet' for r in accepted),accepted_native_naval_attacks=sum(r['kind']=='battle.attack-fleet' for r in accepted),
 native_AI_rejections=0,native_AI_action_caps=0,conditioned_direct_commands=21,conditioned_accepted=sum(r['native_direct_accepted'] is True for r in rows),
 conditioned_paths_equal=sum(r['native_path_equal'] is True for r in rows),conditioned_terminals_equal=sum(r['native_terminal_equal'] is True for r in rows),
 conditioned_move_budgets_equal=sum(r['native_moves_equal'] is True for r in rows),conditioned_path_terminal_budget_all_equal=sum(r['native_path_equal'] is True and r['native_terminal_equal'] is True and r['native_moves_equal'] is True for r in rows),
 native_path_observer_replays=33,all_replay_states_equal=True,live_original_runs=2,live_observer_plain_whole_savs_equal=True,
 observed_original_phases_replayed=15,observed_moving_phases=moving,whole_phase_RAM_matches=15,observer_CPU_checks=120,
 stored_zero_moves_now_tested=True,original_stored_zero_attempts_walk_but_does_not_move=True,cargo_sea_positive_zero_terminal_checks_pass=True,
 protected_native_attack_rejected_unchanged=True,unprotected_native_attack_accepted=True,
 affordability_paired_input_difference='controller byte only',original_AI_move_budget=0,original_human_move_budget=1,native_AI_move_budget=1,native_human_move_budget=1,
 limits=['Original naval combat was not executed or compared; three controls intentionally stop before it.',
 'Native full-seat runs use an explicitly declared SplitMix stream; they are not equivalent phase histories to original fleet-only controls.',
 'Conditioned commands test actual acceptance/movement on measured original pre-move inputs and goals, bypassing AI target choice.',
 'Protected-port approach differs from protected-port attack; the latter is rejected by the native engine.',
 'Cargo checked at sea and at zero moves; disembarkation, capacity and combat losses remain outside this batch.',
 'One generated Roman-start observer/plain pair, not two independent campaigns or Windows acceptance.'])
with (DATA/('summary-'+options.version+'.json')).open('x') as f:json.dump(summary,f,indent=2)
with (DATA/('movement-ledger-'+options.version+'.json')).open('x') as f:json.dump(rows,f,indent=2)
with (DATA/('accepted-fleet-ledger-'+options.version+'.json')).open('x') as f:json.dump(accepted,f,indent=2)
with (DATA/('movement-ledger-'+options.version+'.csv')).open('x',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
print(json.dumps({k:v for k,v in summary.items() if k in ['synthetic_original_cases','completed_original_phases_or_walks','stopped_before_naval_combat','accepted_native_fleet_moves','accepted_native_naval_attacks','conditioned_accepted','conditioned_paths_equal','conditioned_move_budgets_equal','observed_moving_phases']}))
