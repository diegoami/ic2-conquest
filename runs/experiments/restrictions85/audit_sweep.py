"""Reparse seven original sweep controls; exact fleet arrow/OK/Cancel outcomes."""
from pathlib import Path
import json,hashlib,sys
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R));from state import sav
D=R/'runs/experiments/data/run-exp-restrictions85';A=R/'artifacts/run-exp-restrictions85';out=[];hashes={}
for batch in ['sweep-pilot-v1','sweep-v2']:
 for c in json.load(open(D/(batch+'-plan.json'))):
  r=json.load(open(D/(batch+'_'+c['id']+'.json')));ss=[]
  for field in ['before_save','after_save']:
   p=A/('private-'+batch)/r[field];raw=p.read_bytes();hashes[p.name]=hashlib.sha256(raw).hexdigest();ss.append(sav.parse(raw))
  b,a=ss;assert b['turn']==a['turn']==734 and not a['battle_flag'];assert b['nations'][0]['treasury']==a['nations'][0]['treasury']
  if c['kind']=='fleet':
   exp={'fleet-money-950':[1000,150,20,10],'fleet-money-1000':[1000,200,20,10],'fleet-money-1100':[1000,300,20,10],'fleet-ships-only-overcap':[1100,200,21,9],'fleet-money-cancel':[950,200,20,10]}[c['id']]
   assert [a['fleets'][2]['money'],a['fleets'][5]['money'],a['fleets'][2]['ships'],a['fleets'][5]['ships']]==exp
  else:
   assert a['armies']==b['armies'] and a['fleets']==b['fleets']
   assert r['events'][0]['selection_fields']==[-1,-1,2]
  out.append(dict(id=c['id'],saves=[r['before_save'],r['after_save']],parsed=True,summary=r['summary']))
with (D/'audit-sweep-v1.json').open('x') as f:json.dump(dict(cases=len(out),rows=out),f,indent=2)
with (A/'audit-sweep-private-hashes-v1.json').open('x') as f:json.dump(hashes,f,indent=2)
print('verified',len(out),'sweep pairs')
