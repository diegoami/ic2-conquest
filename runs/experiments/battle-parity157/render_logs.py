"""Readable companion logs; raw observed JSON remains authoritative."""
import argparse
import json
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('folder',type=Path)
p.add_argument('--native',type=Path,required=True)
a=p.parse_args()
entry=json.loads((a.folder/'result.json').read_text())
actions=[json.loads(line) for line in (a.folder/'semantic-actions-v1.jsonl').read_text().splitlines()]
with (a.folder/'original-battle-log-v1.txt').open('x') as f:
    f.write('Original IC2 / fixed-seed1 lab / semantic observer\n')
    f.write('Intervals use original sequence numbers. Walk summaries overlap their individual steps.\n')
    f.write('Placement is a routine boundary capture; individual placement-write order is not asserted.\n\n')
    f.write('Actual tactical entry: slot/type/troops/quality/morale/moves/ammunition\n')
    for s in entry['entry']['slots']:
        if s['troops']>0:
            f.write(f"{s['slot']:2} {s['type']:2} {s['troops']:6} {s['quality']:2} {s['morale']:3} {s['state']:2} {s['ammo']:3}\n")
    f.write('\nActions (all input fields and draw values are in semantic-actions-v1.jsonl):\n')
    for r in sorted(actions,key=lambda x:(x['begin_seq'],x['end_seq'])):
        prefix=f"HR{r['counter']:02} seq{r['begin_seq']:04}..{r['end_seq']:04} {r['kind']:17} slot{r['actor']:02} "
        kind=r['kind']
        if kind in ['move','step_without_move']:
            detail=f"({r['from_x']},{r['from_y']}) -> ({r['to_x']},{r['to_y']}), moves {r['moves_before']} -> {r['moves_left']}"
        elif kind=='shot':
            detail=f"-> slot{r['target']:02}, bound {r['bound']}, loss {r['loss']}, morale loss {r['morale_loss']}, remaining {r['target_troops']} morale {r['target_morale']}"
        elif kind=='melee':
            detail=f"-> slot{r['target']:02}, focus {r['focus']}, powers {r['attacker_power']}/{r['defender_power']}, bounds {r['attacker_bound']}/{r['defender_bound']}, losses {r['attacker_loss']}/{r['defender_loss']}, remaining {r['attacker_troops']}/{r['defender_troops']}, morale {r['attacker_morale']}/{r['defender_morale']}"
        elif kind=='walk':
            detail=f"goal {r['goal']}, ({r['before']['x']},{r['before']['y']}) -> ({r['after']['x']},{r['after']['y']})"
        elif kind=='rout_check':
            detail=f"troops {r['before']['troops']} -> {r['after']['troops']}, morale {r['before']['morale']} -> {r['after']['morale']}"
        else:
            detail='removed'
        f.write(prefix+detail+'\n')
for variant in json.loads(a.native.read_text())['fullBattles']:
    with (a.folder/('native-'+variant['label']+'-battle-log-v1.jsonl')).open('x') as f:
        counter=entry['entry']['half_round']
        for i,e in enumerate(variant['events']):
            if e['type']=='TacticalSetUpEvent':
                counter=e['data']['Counter']
            f.write(json.dumps(dict(index=i,counter=counter,**e),separators=(',',':'))+'\n')
print('Rendered original and all native variants; original snapshot inputs retained')
