"""Reparse saved evidence, verify numerical claims; immutable output.
No original execution or native Windows acceptance; hashes remain private.
"""
import argparse,hashlib,json,sys,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from state import sav
ART=ROOT/'artifacts/run-exp-restrictions85';DATA=ROOT/'runs/experiments/data/run-exp-restrictions85'
p=argparse.ArgumentParser();p.add_argument('--version',required=True);p.add_argument('--batch',required=True);q=p.parse_args()
plan=json.loads((DATA/(q.batch+'-plan.json')).read_text());rows=[];hashes={}
for c in plan:
 stem=q.batch+'_'+c['id'];r=json.loads((DATA/(stem+'.json')).read_text())
 states=[]
 for field in ['before_save','after_save']:
  path=ART/('private-'+q.batch)/r[field];raw=path.read_bytes();s=sav.parse(raw)
  assert s['turn']==734 and s['battle_flag']==0
  hashes[path.name]=hashlib.sha256(raw).hexdigest();states.append(s)
 b,a=states
 if c['id'].startswith('paid-'):
  target=lambda s:s['armies'][0] if c['kind']=='army' else s['fleets'][2]
  old,new=target(b),target(a);room=(101 if c['kind']=='army' else 160)-c['supply'];amount=0
  expectedstaged=[0]
  for step in c['steps']:
   amount=min(max(0,amount+step*100),c['stock'],room,c['purse']*5);expectedstaged.append(amount)
  assert expectedstaged==r['summary']['staged'][:len(expectedstaged)]
  applied=amount if c['transfer'] else 0;cost=int(applied/5)
  assert [new['supplies'],new['money']]==[old['supplies']+applied,old['money']-cost]
  assert a['cities'][89]['supplies']==b['cities'][89]['supplies']-applied
  assert a['nations'][1]['treasury']==b['nations'][1]['treasury']+cost
  # Preserve entire parsed world except named money/supply fields and UI view.
  for s in states:
   t=target(s);t['supplies']=t['money']=0
   if c['kind']=='army':t['supply_pct']=0
   s['cities'][89]['supplies']=0;s['nations'][1]['treasury']=0
   for nation in s['nations']:nation['view']=[0,0]
  assert states[0]==states[1],c['id']
 elif c['id'].startswith('money-'):
  for i in [0,13]:assert [a['armies'][i]['money'],a['armies'][i]['supplies'],a['armies'][i]['troops']]==r['summary']['after'][[0,13].index(i)]
 elif c['id'].startswith('unchanged-'):
  aa,bb=b['armies'][0],b['armies'][13];s0,s1=aa['supplies'],bb['supplies']
  if c['finish']=='OK':
   first,second=(0,13) if c.get('selected',0)==0 else (13,0)
   stocks={0:s0,13:s1};caps={0:aa['troops']//100,13:bb['troops']//100}
   for i,j in [(first,second),(second,first)]:
    excess=max(0,stocks[i]-caps[i]);stocks[i]-=excess;stocks[j]+=excess
   assert [a['armies'][0]['supplies'],a['armies'][13]['supplies']]==[stocks[0],stocks[13]]
  else:assert a['armies']==b['armies']
 rows.append(dict(id=c['id'],before_save=r['before_save'],after_save=r['after_save'],parsed=True,summary=r['summary']))
with (DATA/f'audit-{q.version}.json').open('x') as f:json.dump(dict(batch=q.batch,cases=len(rows),all_pairs_reparsed=True,rows=rows),f,indent=2)
with (ART/f'audit-private-hashes-{q.version}.json').open('x') as f:json.dump(hashes,f,indent=2)
print('verified',q.batch,len(rows),'save pairs')
