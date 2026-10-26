"""Read-only GUI evidence reparse: recruitment defaults, providers, carried target,
synthetic tactical clicks. Original hashes/fullstates stay private; exclusive output.
"""
from pathlib import Path
import json,hashlib,sys,argparse
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R));from state import sav,battle_block as BB
D=R/'runs/experiments/data/run-exp-restrictions85';A=R/'artifacts/run-exp-restrictions85'
parser=argparse.ArgumentParser();parser.add_argument('--version',required=True);version=parser.parse_args().version
rows=[];hashes={}
def pair(batch,r,battle=False):
 out=[]
 for key in ['before_save','after_save']:
  p=A/('private-'+batch)/r[key];raw=p.read_bytes();hashes[p.name]=hashlib.sha256(raw).hexdigest();s=sav.parse(raw);assert s['turn']==734 and bool(s['battle_flag'])==battle;out.append((s,BB.block_of_save(raw) if battle else None))
 return out
# Recruitment9cases: actual create-at destination equals initial chosen town,
# score rule, exact ordered visible training rows, fresh/reopen after selection.
for f in sorted(D.glob('gui81-v3_*.json')):
 r=json.load(open(f));(b,_),(a,_)=pair('gui81-v3',r);town=r['binding']['selected_city'];n=b['nations'][0];counts={i:sum(x['city']==i for x in n['recruit_slots'])+(i==n['capital']) for i in n['city_list']}
 expected=n['capital'] if not n['recruit_slots'] else max(n['city_list'],key=lambda i:counts[i])
 assert town==expected,(f.name,town,expected)
 old=n['recruit_slots'];new=a['nations'][0]['recruit_slots'];assert new[:-1]==old and new[-1]['city']==town and new[-1]['troops']==3000
 assert r['opened']==r['reopened']==r['manual_reopen']
 visible=r['opened'][1]['count'];assert visible==sum(x['city']==town for x in old)
 rows.append(dict(id=r['case']['id'],batch='gui81-v3',selected_city=town,new_recruit_city=new[-1]['city'],reopen_resets_default=True))
# Natural providers: read all actual selected row bindings and donor changes.
for f in sorted(D.glob('gui78-natural-v2_natural-*.json')):
 if '-row' in f.name:continue
 r=json.load(open(f));(b,_),(a,_)=pair('gui78-natural-v2',r);selected=[e for e in r['events'] if e['phase']=='selected']
 if len(r['case']['fleet_ids'])==2:assert [e['fields'][6] for e in selected[2:]]==[2,-1]
 else:
  first,last=(2,1) if r['case']['fleet_ids'][0]==2 else (5,0)
  assert [e['fields'][6] for e in selected[2:]]==[first,last,last]
 for i,e in enumerate(r['events']):
  if e['phase']!='transfer10':continue
  prev=r['events'][i-1];cid,fid=prev['fields'][5:7]
  assert e['state']['armies']['0']['supplies']-prev['state']['armies']['0']['supplies']==10
  if cid>=0:assert prev['state']['cities'][str(cid)]-e['state']['cities'][str(cid)]==10
  else:assert prev['state']['all_fleets'][str(fid)]['supplies']-e['state']['all_fleets'][str(fid)]['supplies']==10
 assert a['armies'][0]['supplies']==r['summary']['army_supply']
 rows.append(dict(id=r['case']['id'],batch='gui78-natural-v2',bindings=[e['fields'] for e in selected],save_pair_reparsed=True))
for f in sorted(D.glob('gui78-switch-v3_*.json')):
 r=json.load(open(f));(b,_),(a,_)=pair('gui78-switch-v3',r);assert r['summary']['staged'][:2]==[90,90]
 assert a['cities'][72]['supplies']==90
 assert a['cities'][76]['supplies']==(-80 if r['case']['buy'] else 10)
 assert [a['armies'][0]['supplies'],a['armies'][0]['money']]==([90,82] if r['case']['buy'] else [0,100])
 rows.append(dict(id=r['case']['id'],batch='gui78-switch-v3',summary=r['summary'],save_pair_reparsed=True))
# Tactical: discriminate genuine0moves from load-reset labelled attempts.
files=list(D.glob('gui80-pilot-v1_*.json'))+list(D.glob('gui80-v2-c*_*.json'))+list(D.glob('gui80-zero-v3-c*_*.json'))+list(D.glob('gui80-clear-v4-c*_*.json'))
for f in sorted(files):
 r=json.load(open(f));batch=f.name.split('_')[0];(b,bb),(a,ab)=pair(batch,r,True);ev=r['events'];clicked=next(x for x in ev if x['action']=='enemy-click');selected=[x for x in ev if x['action']=='select-own'];zero='zero-v3' in batch
 if zero:assert selected[0]['slots'][0]['state']==0 and clicked['slots'][0]['target']==-1
 if r['case']['button']==1:
  adjacent=r['case']['select'] and not r['case']['distant'] and not zero
  assert clicked['slots'][0]['target']==(20 if adjacent else -1)
  assert clicked['selected']==-1
  assert not any('Quality' in line or 'Morale' in line or 'Moves' in line or 'Shots' in line for line in clicked['info']) if not adjacent else True
 else:
  if r['case']['select']:assert clicked['slots'][0]['ammo']==24 and clicked['slots'][0]['state']==3
  else:assert clicked['slots'][0]['ammo']==25
 clear=[x for x in ev if x['action']=='own-right-clear']
 if clear:assert clear[0]['slots'][0]['target']==-1 and clear[0]['slots'][0]['state']==4 and clear[0]['slots'][0]['ammo']==25
 # Every original-saved live slot agrees with final observation; all other
 # slots and non-target grid cells remain byte-equivalent at decoded scope.
 for i,k in enumerate([0,1,20,21]):assert ab['slots'][k]==ev[-1]['slots'][i]
 for k in set(range(40))-{0,1,20,21}:assert bb['slots'][k]==ab['slots'][k]
 changed_cells={BB.cell(bb['slots'][20]['x'],bb['slots'][20]['y'])}
 assert all(x==y for k,(x,y) in enumerate(zip(bb['grid'],ab['grid'])) if k not in changed_cells)
 assert bb['half_round']==ab['half_round']==2 and r['events'][-1]['selected']==-1
 rows.append(dict(id=r['case']['id'],batch=batch,genuine_zero_control=zero,load_reset_labelled_zero=('zero-moves'in r['case']['id'] and not zero),save_pair_reparsed=True,selected_after_click=clicked['selected'],info_after_click=clicked['info']))
with (D/('audit-gui-'+version+'.json')).open('x') as f:json.dump(dict(rows=rows,cases=len(rows)),f,indent=2)
with (A/('audit-gui-private-hashes-'+version+'.json')).open('x') as f:json.dump(hashes,f,indent=2)
print('verified',len(rows),'GUI pairs')
