"""Publication audit of immutable public ledgers, without a game/owner input."""
import argparse,json
from pathlib import Path
D=Path(__file__).resolve().parents[3]/'runs/experiments/data/run-exp-strategic-tracks'
load=lambda n:json.loads((D/n).read_text())
actual=load('native-phases-v2.json');synthetic=load('native-synthetic-v1.json');providers=load('fleet-native-providers-v1.json')['rows'];cargo=load('fleet-native-v2.json');mixed=load('fleet-native-v3.json');original=load('fleet-original-v3.json')
econ=[x for x in actual+synthetic if x['phase']=='economy'];dip=[x for x in actual+synthetic if x['phase']=='diplomacy']
names=['rome','carthage','seleucid','ptolemaic','macedonia','numidia','gaul','greece','celtiberia','illyria','dacia','bithynia','galatia','armenia','media','thracia']
assert len(econ)==35 and all(r['complete'] and r['Rejected']==0 and r['all_draws_consumed'] and r['economy_projection_equal'] for r in econ)
assert all((r['own'],r['threat'])==(r['original_power'][0]['own'],r['original_power'][0]['threat']) for r in econ)
assert len(dip)==24
for r in dip:
 o=r['original_facts'];assert r['busy']==o['busy'] and r['war_target']==(None if o['war_target'] is None else names[o['war_target']])
assert len(providers)==23 and all(r['projection_equal'] for r in providers)
assert len(cargo)==8 and sum(r['projection_equal'] for r in cargo)==6 and all(r['accepted'] for r in cargo)
assert len(mixed)==4 and sum(r['projection_equal'] for r in mixed)==1
assert all(r['troops_before']==r['troops_after_original'] for r in mixed)
assert [r['troops_after_native'] for r in mixed]==[5000]*4
phases=load('phase-replay-summary-v1.json');assert phases==dict(phases=45,complete=45,whole_RAM_matches=45,draws=54)
assert all(r['whole_SAV_equal'] for r in load('live-inertness-v1.json')['controls'])
rows=actual+synthetic+providers+cargo+mixed
summary=dict(original_observed_phases=45,exact_replayed_exits=45,original_draws=54,economy_comparisons=35,economy_projection_matches=35,diplomacy_busy_war_target_comparisons=24,diplomacy_busy_war_target_matches=24,fleet_provider_matches=23,valid_cargo_comparisons=12,cargo_matches=7,embark_overflow_discrepancies=5,all_native_input_gate_fields=sum(r['input_checks'] for r in rows),main_followup=1412,limits=['not whole-turn/native RNG parity','diplomacy alliance/trade candidate outputs are observations, not full parity assertions','eight invalid quality50 cargo v1 inputs retained and excluded; v2/v3 use valid quality7','provider rows recovered from persisted complete per-case output before v1 cargo import failure','route arrival retention proved; next fresh-stack phase is diagnostic, not universal coincident-line behavior','overflow no-land/no-free-slot/existing-receiver and human UI branches untested'])
p=argparse.ArgumentParser();p.add_argument('--version',required=True);a=p.parse_args()
with (D/('summary-'+a.version+'.json')).open('x') as f:json.dump(summary,f,indent=2)
print(json.dumps(summary))
