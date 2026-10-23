"""Compare independently observed action tuples, retaining the first difference."""
import argparse
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--original', type=Path, required=True)
p.add_argument('--native', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
original = [json.loads(line) for line in (a.original/'semantic-actions-v1.jsonl').read_text().splitlines()]
native = json.loads(a.native.read_text())['fullBattles']
schema = {
    'move': ('TacticalMovedEvent', dict(actor='Slot',from_x='FromX',from_y='FromY',to_x='ToX',to_y='ToY',moves_left='MovesLeft')),
    'shot': ('TacticalShotEvent', dict(actor='Shooter',target='Target',bound='Bound',loss='Loss',morale_loss='MoraleLoss',target_troops='TargetTroops',target_morale='TargetMorale')),
    'melee': ('TacticalMeleeEvent', dict(actor='Attacker',target='Defender',focus='Focus',attacker_power='AttackerPower',defender_power='DefenderPower',
                                     attacker_bound='AttackerBound',defender_bound='DefenderBound',attacker_loss='AttackerLoss',defender_loss='DefenderLoss',
                                     attacker_troops='AttackerTroops',defender_troops='DefenderTroops',attacker_morale='AttackerMorale',defender_morale='DefenderMorale')),
}
rows = []
for variant in native:
    checks=[]
    for kind,(event_type,mapping) in schema.items():
        observed=[{key:r[key] for key in mapping} for r in original if r['kind']==kind]
        modeled=[{key:e['data'][field] for key,field in mapping.items()} for e in variant['events'] if e['type']==event_type]
        first=next((dict(index=i,original=o,native=n) for i,(o,n) in enumerate(zip(observed,modeled)) if o!=n),None)
        checks.append(dict(kind=kind,original_count=len(observed),native_count=len(modeled),equal=observed==modeled,first_difference=first))
    observed=[r['actor'] for r in original if r['kind']=='remove']
    modeled=[e['data']['Slot'] for e in variant['events'] if e['type'] in ['TacticalRoutedEvent','TacticalCascadeRemovedEvent']]
    checks.append(dict(kind='removal_order',original_count=len(observed),native_count=len(modeled),equal=observed==modeled,
                       first_difference=next((dict(index=i,original=o,native=n) for i,(o,n) in enumerate(zip(observed,modeled)) if o!=n),None)))
    observed_stream=[]
    for r in original:
        if r['kind'] in schema:
            mapping=schema[r['kind']][1]
            observed_stream.append(dict(kind=r['kind'],data={key:r[key] for key in mapping}))
        elif r['kind']=='remove':
            observed_stream.append(dict(kind='remove',data=dict(actor=r['actor'])))
    modeled_stream=[]
    for e in variant['events']:
        for kind,(event_type,mapping) in schema.items():
            if e['type']==event_type:
                modeled_stream.append(dict(kind=kind,data={key:e['data'][field] for key,field in mapping.items()}))
        if e['type'] in ['TacticalRoutedEvent','TacticalCascadeRemovedEvent']:
            modeled_stream.append(dict(kind='remove',data=dict(actor=e['data']['Slot'])))
    checks.append(dict(kind='combined_action_order',original_count=len(observed_stream),native_count=len(modeled_stream),
                       equal=observed_stream==modeled_stream,
                       first_difference=next((dict(index=i,original=o,native=n) for i,(o,n) in enumerate(zip(observed_stream,modeled_stream)) if o!=n),None)))
    rows.append(dict(label=variant['label'],checks=checks,all_equal=all(c['equal'] for c in checks)))
report=dict(scope='Actual movement steps, pre-rout shot/melee calculations and removal order. Other event families not asserted.',variants=rows)
with a.output.open('x') as f:
    json.dump(report,f,indent=2)
    f.write('\n')
print(json.dumps(report,indent=2))
