"""Validate private evidence, publish only bounded scalar results.

No owner input/save hashes or full state/trace is emitted. Never overwrite data.
"""
import hashlib
import json
import struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
PRIVATE=ROOT/'artifacts/run-exp-seleucid1388/private'
DATA=ROOT/'runs/experiments/data/run-exp-seleucid1388'
def load(path):return json.loads(path.read_text())
def create(name,value):
    with (DATA/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
plain=PRIVATE/'plain-seed1-v1'
for label in ('hook-seed1-v1','hook-seed1-v2'):
    for boundary in ('before','after'):
        assert next((PRIVATE/label).glob('*-'+boundary+'.SAV')).read_bytes()==next(plain.glob('*-'+boundary+'.SAV')).read_bytes()
for label in ('plain-seed1-v1','hook-seed1-v1','hook-seed1-v2'):
    r=load(PRIVATE/label/'result.json')
    assert r['complete'] and r['turn']==756 and r['defender']==[dict(id=4,x=212,y=96,troops=78857,moves=0)]
hook=PRIVATE/'hook-seed1-v2'
records=load(hook/'records.json')
entries=[r for r in records if r['army']==4]
assert len(entries)==2
assert [(r['site'],r['goal']) for r in entries]==[(0x44f409,[191,95]),(0x44dc3a,[189,104])]
assert all(r['army_header'][:4]==[219,93,2,7] for r in entries)
ram=(hook/'defender-prewalk-ram.bin').read_bytes()
assert len(ram)==0x43000 and list(struct.unpack_from('<4h',ram,0x47c1ec+4*656-0x45e000))==[219,93,2,7]
original=load(PRIVATE/'original-helpers-v4.json')
assert original['army_score']==dict(target=24,score=828,distance=28)
assert original['waypoint']==[189,104] and original['random_draws']==0
assert all(r['original_can_reach'] for r in original['reachability'])
assert original['reachability'][1]['direct_line'] is False
assert original['regions']==[dict(goal=g,region=-1,coast=1) for g in ([219,93],[191,95],[207,95])]
full=original['full_wrapper']
after=next(hook.glob('*-after.SAV')).read_bytes()
assert bytes.fromhex(full['army_record_after'])==after[100958+4*656:100958+5*656]
assert full['final']==[212,96,2,0] and full['rng_unchanged'] and full['random_calls']==0
assert len(original['seed_controls'])==5
assert all(x['target']==24 and x['final']==[212,96,2,0] and x['rng_unchanged'] for x in original['seed_controls'])
native=PRIVATE/'native-v3'
assert load(native/'after.json')==load(PRIVATE/'native-v1/after.json')==load(PRIVATE/'native-v2/after.json')
targets=load(native/'target-diagnostics.json')
weak=next(t for t in targets if t['TotalTroops']==7000)
near=next(t for t in targets if t['TotalTroops']==31565)
assert (weak['X'],weak['Y'],weak['reachable'],weak['strength'],weak['actorStrength'])==(191,95,False,2964,22320)
assert (near['X'],near['Y'],near['reachable'],near['strength'])==(207,95,True,11529)
assert [x['value'] for x in original['field_strengths']]==[22320,26460,11529,2964]
decisions=[x for x in load(native/'decisions.json') if x['ArmyId']=='army-4']
assert decisions and all(x['TargetArmyX']==207 and x['TargetArmyY']==95 and x['ArmyScore']==212 for x in decisions)
walks=load(native/'conditional-walks.json')
matched=[]
for old,new in zip(original['walks'],walks,strict=True):
    assert old['goal']==new['goal'] and old['random_calls']==0 and old['rng_unchanged']
    stores=old['coordinate_stores']
    assert len(stores)==14
    path=[]
    for i in range(0,len(stores),2):
        assert stores[i]['field']=='x' and stores[i+1]['field']=='y'
        path.append(dict(X=stores[i]['value'],Y=stores[i+1]['value']))
    assert path==new['walk']['EnteredCells']
    assert old['final'][0:2]==[new['walk']['FinalPosition']['X'],new['walk']['FinalPosition']['Y']]
    matched.append(dict(goal=old['goal'],steps=len(path),endpoint=old['final'][:2]))
assert matched==[dict(goal=[207,95],steps=7,endpoint=[212,94]),dict(goal=[191,95],steps=7,endpoint=[213,94]),dict(goal=[189,104],steps=7,endpoint=[212,96])]
out=dict(tag='confirmed, partial',remake_pin='3c1860079db6dd9b1fb11ceb8b726c7fd95293ac',
    original_turn=756,original_live_runs=3,observed_runs=2,plain_runs=1,
    before_and_after_whole_sav_equal_across_all_three=True,observer_cpu_preservation_states=816,
    original_destination=[191,95],original_waypoint=[189,104],original_target_score=828,
    remake_destination=[207,95],remake_target_score=212,
    weak_target_reachable_original=True,weak_target_reachable_remake=False,
    original_weak_target_direct_line=False,original_region_and_coast_equal=True,
    field_strengths_agree=True,original_full_wrapper_matches_saved_army_record=True,
    paired_conditional_walks=matched,matching_conditional_steps=21,
    original_local_rng_calls=0,original_local_seed_controls=5,
    original_local_seed_control_endpoints_identical=True,
    native_diagnostic_repeats_equal=3,production_source_changed=False,owner_hashes_or_full_states_published=False,
    limits=['One owner campaign and one seeded original trajectory, not three independent scenarios.',
        'Five seed controls are original-instruction local replays, not five fresh whole-turn games.',
        'The whole End-turn action/RNG stream is not synchronized across engines.',
        'No complete strategic routing implementation, production correction or native Windows acceptance.'])
create('audit-v1.json',out)
print('PASS original inertness, captured calls, deterministic target/routing helpers, saved full army record, 21 paired steps, five local seed controls')
