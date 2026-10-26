"""Reparse all23 action controls and3 cold launches; immutable public receipt.
Whole parsed strategic state checked except named effects/camera. Raw original
bytes, full states and all per-input hashes remain private. Not a GUI replay.
"""
from pathlib import Path
import argparse,copy,json,hashlib,sys
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R));from state import sav
D=R/'runs/experiments/data/run-exp-carried-disband';A=R/'artifacts/run-exp-carried-disband'
p=argparse.ArgumentParser();p.add_argument('--version',required=True);q=p.parse_args();rows=[];hashes={};unique=set()
BATCHES=['cd218-pilot-v1','cd218-controls-v2','cd218-early-v3','cd218-fast-v4','cd218-boundary-v5']
def read(batch,name):
 path=A/('private-'+batch)/name;raw=path.read_bytes();hashes[str(path.relative_to(A))]=hashlib.sha256(raw).hexdigest();unique.add(str(path.relative_to(A)));s=sav.parse(raw);assert s['turn']==734 and not s['battle_flag'];return s

def norm(s):
 s=copy.deepcopy(s)
 for n in s['nations']:n['view']=[0,0]
 return s
for batch in BATCHES:
 for case in json.load(open(D/(batch+'-plan.json'))):
  stem=batch+'_'+case['id'];r=json.load(open(D/(stem+'.json')));b=read(batch,r['before_save']);a=read(batch,r['after_save']);expected=copy.deepcopy(b);aa=expected['armies'][0];fleet=expected['fleets'][2];nation=expected['nations'][0];city=expected['cities'][89];ev=r['events']
  # Every public observation agrees with the original-saved after endpoint.
  saved=next(x for x in ev if x['phase']=='saved')['state']
  assert [a['armies'][0]['owner'],a['armies'][0]['troops'],a['fleets'][2]['army'],a['nations'][0]['treasury'],a['cities'][89]['supplies'],a['nations'][0]['mobilization']]==[saved['armies']['0']['owner'],saved['armies']['0']['troops'],saved['carrier']['army'],saved['treasury'],saved['city_stock'],saved['mobilization']]
  if case['mode']=='whole':
   positive=(case.get('land')or case.get('disembark')or'fast_ms'in case)and not case.get('confirm_no')and not case.get('redraw')
   boxes=next(x for x in ev if x['phase']=='whole-command-returned')['boxes']
   if positive:
    assert len(boxes)==1 and 'disband'in boxes[0].lower(),(stem,boxes)
    aa['owner']=-1;nation['treasury']+=37;city['supplies']+=23
    if aa['cell']==-1:fleet['army']=-1
    else:mp=list(expected['map']);mp[aa['x']*140+aa['y']]=aa['cell'];expected['map']=tuple(mp)
   if case.get('disembark'):
    # Actual landing happens first; attribute both armies' moves/cell/coords and fleet move/link to it.
    landed=next(x for x in ev if x['phase']=='disembarked')['state'];la=landed['armies']['0'];lf=landed['carrier']
    assert la['x']==101 and la['y']==45 and la['cell']==2 and lf['army']==-1
    for k in ['x','y','cell','embarked','moves']:aa[k]=la[k]
    fleet['moves']=lf['moves'];fleet['army']=-1
   if case.get('confirm_no')and('fast_ms'in case or case.get('land')):assert len(boxes)==1,'real No prompt not exercised'
   if not positive and not case.get('confirm_no'):assert boxes==[],(stem,boxes)
   if'fast_ms'in case:
    # Actual before-state has no adjacent-city offers; no handler injection.
    near=[c for c in b['cities']if max(abs(c['x']-101),abs(c['y']-46))<=1]
    assert not any((m['x'],m['y'])==(c['x'],c['y'])for m in b['mercenaries']for c in near)
    trace=next(x for x in ev if x['phase']=='fast-selection-trace')['trace'];assert any(x['selection']==[0,-1,2]for x in trace)
    if case.get('redraw'):
     assert next(x for x in ev if x['phase']=='nooffer-before-pan')['state']['selection']==[0,-1,2]
     assert next(x for x in ev if x['phase']=='after-area-pan')['state']['selection']==[-1,-1,2]
  elif case['mode']=='change':
   changed=case['finish']=='OK'and(case.get('owncity',True)or case.get('merc'))
   opened=next(x for x in ev if x['phase']=='change-open');worked=next(x for x in ev if x['phase']=='change-disband-confirmed')
   assert opened['bound_army']==0
   assert worked['state']['armies']['0']==opened['state']['armies']['0'],'global changed before OK'
   if changed:
    aa['units']=[];aa['troops']=0;aa['supply_pct']=0
    if not case.get('merc'):nation['mobilization']-=1+5000*1000//nation['wealth']
    assert worked['working']['troops']==0
   assert a['armies'][0]['owner']==0 and a['fleets'][2]['army']==0
  elif case['mode']=='transfer':
   worked=next(x for x in ev if x['phase']=='transfer-disband-confirmed');opened=next(x for x in ev if x['phase']=='transfer-open')
   assert worked['working'][0]['troops']==0 and worked['state']['armies']==opened['state']['armies']
   if case['finish']=='OK':
    aa['units']=[];aa['troops']=0;aa['supplies']=0;aa['supply_pct']=0;aa['owner']=-1;fleet['army']=-1
    target=expected['armies'][13];target['supplies']=30;target['money']=48;target['supply_pct']=100
    nation['mobilization']-=1+5000*1000//nation['wealth']
  x,y=norm(expected),norm(a)
  if x!=y:
   print(stem,'different keys',[k for k in x if x[k]!=y[k]])
   for i,(u,v)in enumerate(zip(x['armies'],y['armies'])):
    if u!=v:print('army',i,{k:(u[k],v[k])for k in u if u[k]!=v[k]})
  assert x==y,stem
  reload_ok=False
  if r.get('reopened_save'):
   reopened=read(batch,r['reopened_save']);assert norm(reopened)==norm(a);reload_ok=True
  rows.append(dict(batch=batch,id=case['id'],saves=[r['before_save'],r['after_save']],same_process_reload_equal=reload_ok,whole_parsed_state_matches_named_effects=True,summary=r['summary']))
for k,case in enumerate(json.load(open(D/'cd218-cold-v1-matrix.json'))):
 batch=f'cd218-cold-v1-c{k:02d}';r=json.load(open(D/(batch+'_'+case['id']+'.json')));source=read(case['batch'],r['input_save']);cold=read(batch,r['output_save']);assert norm(source)==norm(cold)
 rows.append(dict(batch=batch,id=case['id'],fresh_original_process=True,source_save=r['input_save'],cold_save=r['output_save'],whole_parsed_state_equal_except_camera=True,summary=r['summary']))
with (D/('audit-'+q.version+'.json')).open('x')as f:json.dump(dict(action_controls=23,cold_process_controls=3,action_pairs=23,same_process_reload_pairs=3,cold_process_pairs=3,unique_original_written_saves=len(unique),rows=rows),f,indent=2)
with (A/('audit-private-hashes-'+q.version+'.json')).open('x')as f:json.dump(hashes,f,indent=2)
print('verified23action+3cold controls,29pairs,',len(unique),'unique original-written saves')
