"""Reparse fourteen completed money/Split/unchanged-OK controls; hashes private."""
from pathlib import Path
import copy,hashlib,json,sys
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R));from state import sav
D=R/'runs/experiments/data/run-exp-restrictions85';A=R/'artifacts/run-exp-restrictions85'
rows=json.load(open(D/'money-unchanged-case-index-v1.json'));out=[];hashes={}
for item in rows:
 r=json.load(open(D/item['file']));batch=item['file'].split('_')[0];ss=[]
 for key in ['before_save','after_save']:
  p=A/('private-'+batch)/r[key];raw=p.read_bytes();s=sav.parse(raw);hashes[p.name]=hashlib.sha256(raw).hexdigest();ss.append(s)
 for s,name in zip(ss,['before','after']):
  assert s['turn']==734 and not s['battle_flag']
  assert [[s['armies'][i]['money'],s['armies'][i]['supplies'],s['armies'][i]['troops']] for i in [0,13]]==r['summary'][name]
 if item['id'].startswith('unchanged-'):
  expected={'unchanged-over-ok':[106,100],'unchanged-over-cancel':[206,0],'unchanged-over-reversed':[100,106],'unchanged-within':[50,20],'unchanged-both-over':[256,100],'unchanged-both-over-reversed':[100,256]}[item['id']]
  assert [ss[1]['armies'][i]['supplies'] for i in [0,13]]==expected
  for s in ss:
   for i in [0,13]:s['armies'][i]['supplies']=0;s['armies'][i]['supply_pct']=0
 elif item['id'].startswith('money-'):
  for s in ss:
   for i in [0,13]:s['armies'][i]['money']=0
 elif item['id']=='split-money-shared':
  assert r['events'][0]['working'][0]['money']==1100 and r['events'][0]['working'][1]['money']==0
  assert [a['money'] for a in r['events'][1]['working']]==[1000,100]
  for s in ss:s['armies']=s['armies'][:14];s['size']=s['tail_off']=0
 for s in ss:
  for n in s['nations']:n['view']=[0,0]
 assert ss[0]==ss[1],item['id']
 out.append(dict(id=item['id'],saves=[r['before_save'],r['after_save']],whole_parsed_state_equal_except_tested_fields_view_and_split_tombstone=True))
with (D/'audit-money-ok-v1.json').open('x') as f:json.dump(dict(cases=len(out),rows=out),f,indent=2)
with (A/'audit-money-ok-private-hashes-v1.json').open('x') as f:json.dump(hashes,f,indent=2)
print('verified',len(out),'money/OK pairs')
