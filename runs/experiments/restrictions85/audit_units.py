"""Audit 17 verified-selection controls from retained original saves and copies.
Never overwrites; original hashes private. Excludes wrong-selection attempts.
"""
from pathlib import Path
import copy,json,hashlib,sys
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R));from state import sav
D=R/'runs/experiments/data/run-exp-restrictions85';A=R/'artifacts/run-exp-restrictions85';out=[];hashes={}
for batch in ['units-pilot-v2','units-v3']:
 for c in json.load(open(D/(batch+'-plan.json'))):
  stem=batch+'_'+c['id'];r=json.load(open(D/(stem+'.json')))
  sel=json.load(open(A/('private-'+batch)/(stem+'-selection.json')));assert sorted(sel,key=lambda x:x['x'])[c['side']]['selected_count']==len(c['rows'])
  ss=[]
  for key in ['before_save','after_save']:
   p=A/('private-'+batch)/r[key];raw=p.read_bytes();hashes[p.name]=hashlib.sha256(raw).hexdigest();ss.append(sav.parse(raw))
  b,a=ss;assert b['turn']==a['turn']==734 and not a['battle_flag']
  assert r['events'][0]['global_state']['armies']==r['events'][-1]['global_state']['armies'],'global army changed at arrow'
  if c['finish']=='Cancel':assert a['armies']==b['armies'] and a['fleets']==b['fleets']
  if c['mode']=='units':
   src,dst=(0,13) if c['side']==0 else (13,0);su=copy.deepcopy(b['armies'][src]['units']);du=copy.deepcopy(b['armies'][dst]['units']);moved=[];failed=[];types=set()
   for k in sorted(c['rows'],reverse=True):
    u=next(x for x in su if x['slot']==k);total=sum(x['troops'] for x in du)+u['troops']
    why='units' if len(du)>=20 else 'troops' if total>100000 else 'fleet' if c.get('carrier')==dst and total//500>30 else None
    if why:failed.append(u['name']);types.add(why);continue
    moved.append(u['name']);du.append(u);su.remove(u)
   if c['finish']=='OK':
    assert [u['name'] for u in a['armies'][src]['units']]==[u['name'] for u in su]
    assert [u['name'] for u in a['armies'][dst]['units']]==[u['name'] for u in du]
    assert a['armies'][dst]['moves']==(0 if moved else b['armies'][dst]['moves'])
    assert a['armies'][src]['moves']==b['armies'][src]['moves']
   nboxes=int(bool(types&{'units','troops'}))+int('fleet'in types);assert len(r['boxes'])==nboxes
  else:
   moved=[];failed=[]
   if c['finish']=='OK':assert a['armies'][0]['troops']==5000 and [a['armies'][i]['supplies'] for i in [0,13]]==[106,100]
  out.append(dict(id=c['id'],saves=[r['before_save'],r['after_save']],selection_verified=True,moved_in_order=moved,refused_units=failed,boxes=r['boxes'],before_moves=[b['armies'][i]['moves'] for i in [0,13]],after_moves=[a['armies'][i]['moves'] for i in [0,13]],summary=r['summary']))
with (D/'audit-units-v1.json').open('x') as f:json.dump(dict(cases=len(out),rows=out),f,indent=2)
with (A/'audit-units-private-hashes-v1.json').open('x') as f:json.dump(hashes,f,indent=2)
print('verified',len(out),'selected-unit/disband pairs')
