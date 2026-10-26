"""Re-read retained promoted controls; no game launch, new public scalar receipt.
Original saves/hashes remain private. Nothing deleted or overwritten.
"""
from pathlib import Path
import json,sys,hashlib
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));from state import sav
DATA=ROOT/'runs/experiments/data/run-exp-restrictions85';ART=ROOT/'artifacts/run-exp-restrictions85'
rows=[];hashes={}
for label,stem in [('U1','U1_20261009-194123'),('U3','U3_20261009-194306'),('U3b','U3b_20261009-194355')]:
 paths=[ROOT/'artifacts/run-exp-supply-transfer-clamps'/(stem+'_'+phase+'.SAV') for phase in ['before','after']]
 assert all(p.is_file() for p in paths),paths
 states=[sav.load(p) for p in paths]
 for p in paths:hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
 if label=='U1':assert states[0]['armies'][13]['troops']==98000 and states[1]['armies'][13]['troops']==100000 and states[1]['armies'][0]['troops']==1000
 if label=='U3':assert states[0]['armies'][0]['troops']==10700 and states[1]['armies'][0]['troops']==15499
 if label=='U3b':assert states[0]['armies'][0]['troops']==states[1]['armies'][0]['troops']==10700 and states[1]['armies'][12]['troops']==4800
 rows.append(dict(case=label,saves=[p.name for p in paths],before={i:states[0]['armies'][i]['troops'] for i in [0,12,13] if i<len(states[0]['armies'])},after={i:states[1]['armies'][i]['troops'] for i in [0,12,13] if i<len(states[1]['armies'])}))
# Locate exact prior20slot endpoints by basename; preserve even a missing receipt.
base=ROOT/'artifacts/run-exp-transfer-20-units'
for case in ['c1_18_plus_3_left','c4_18_plus_3_right','c5_18_plus_3_cancel']:
 paths=[]
 for phase in ['BEFORE','AFTER']:
  found=list(base.glob(case+'_'+phase+'.SAV'));assert len(found)==1,(case,phase,found);paths.append(found[0])
 states=[sav.load(p) for p in paths]
 for p in paths:hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
 if 'cancel'in case:assert states[0]['armies']==states[1]['armies']
 else:assert sorted(len(states[1]['armies'][i]['units']) for i in [0,13])==[1,20]
 rows.append(dict(case=case,saves=[p.name for p in paths],before={i:[u['name'] for u in states[0]['armies'][i]['units']] for i in [0,13]},after={i:[u['name'] for u in states[1]['armies'][i]['units']] for i in [0,13]}))
with (DATA/'prior-controls-audit-v1.json').open('x') as f:json.dump(dict(rows=rows,fresh_original_execution=False,original_build='historical fast/seed patched Wine; does not establish fresh stock/Windows'),f,indent=2)
with (ART/'prior-controls-private-hashes-v1.json').open('x') as f:json.dump(hashes,f,indent=2)
print('verified',len(rows),'historical save pairs')
