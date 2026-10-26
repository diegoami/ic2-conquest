"""Reparse six coherent GUI79 controls; exclude stale-coordinate/marker attempts."""
from pathlib import Path
import json,hashlib,sys
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R));from state import sav
D=R/'runs/experiments/data/run-exp-restrictions85';A=R/'artifacts/run-exp-restrictions85';rows=[];hashes={}
cases=[('gui79-v1','carried-city'),('gui79-v1','carried-full-city-other'),('gui79-moved-v2','carried-moved-carrier'),('gui79-close-v3','carried-close'),('gui79-marker-v4','carried-carrier-alone'),('gui79-marker-v4','carried-other-fleet')]
for batch,cid in cases:
 r=json.load(open(D/(batch+'_'+cid+'.json')));ss=[]
 for field in ['before_save','after_save']:
  p=A/('private-'+batch)/r[field];raw=p.read_bytes();hashes[p.name]=hashlib.sha256(raw).hexdigest();ss.append(sav.parse(raw))
 b,a=ss;assert b['turn']==a['turn']==734 and not a['battle_flag']
 for s in ss:
  army=s['armies'][0];fleet=s['fleets'][2];assert army['embarked'] and fleet['army']==0 and (army['x'],army['y'])==(fleet['x'],fleet['y'])
  assert (sav.cell(s,s['cities'][89]['x'],s['cities'][89]['y'])-20)%16==s['cities'][89]['owner']
 assert [a['armies'][0]['supplies'],a['armies'][0]['money']]==([101,137] if r['case']['full'] else [10,137])
 supplied=next(e for e in r['events'] if e.get('phase')=='supply10-money100');assert supplied['state']['armies']['0']['money']==137
 supplier=5 if r['case']['other'] else 2
 assert a['fleets'][supplier]['money']==b['fleets'][supplier]['money']-100
 assert a['fleets'][supplier]['supplies']==b['fleets'][supplier]['supplies']-(0 if r['case']['full'] else 10)
 fleetcontrol=next(e for e in r['events'] if e.get('phase')=='supply-fleet-control')
 if cid=='carried-carrier-alone':assert fleetcontrol.get('opened') is False
 else:assert fleetcontrol['fields'][2:]==[-1,2]
 rows.append(dict(id=cid,batch=batch,saves=[r['before_save'],r['after_save']],cargo_coordinates=[a['armies'][0]['x'],a['armies'][0]['y']],supplier=supplier,close=r['case'].get('finish','OK'),fleet_control_open=fleetcontrol.get('opened',True)))
with (D/'audit-carried-v1.json').open('x') as f:json.dump(dict(cases=len(rows),rows=rows),f,indent=2)
with (A/'audit-carried-private-hashes-v1.json').open('x') as f:json.dump(hashes,f,indent=2)
print('verified',len(rows),'coherent carried-target pairs')
