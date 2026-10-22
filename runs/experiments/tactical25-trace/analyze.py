"""Join fresh original observations and unchanged port phases, gated by full legacy identity."""
import argparse,hashlib,json,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--states',type=Path,required=True);p.add_argument('--validation',type=Path,required=True);p.add_argument('--pure',type=Path,required=True);p.add_argument('--model-phases',type=Path,required=True);a=p.parse_args()
ROOT=Path(__file__).resolve().parents[3];DATA=ROOT/'runs/experiments/data/run-exp-tactical25-trace'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
v=read(a.validation);assert v['pass'] and v['legacy_draws']==v['new_draws']==325 and len(v['saves'])==15 and all(x['byte_equal'] for x in v['saves'])
run=[json.loads(x) for x in (DATA/v['run']).read_text().splitlines()];assert next(x for x in run if x['event']=='states')['file']==a.states.name
assert sha(DATA/next(x for x in run if x['event']=='hook')['file'])==v['new_log_sha256']
states=read(a.states);assert states['overflow']==0;rs=states['records'];pure=read(a.pure);assert pure['states']==a.states.name and pure['validation']==a.validation.name
manifest=read(a.model_phases.with_name(a.model_phases.name+'-manifest.json'));assert manifest['exit']==0 and manifest['source_clean_after'] and manifest['build_head']=='257f2d2cd7510451d229a983553a54b89065b06c' and manifest['fixtures_head']=='6319802a75067e7730e4f6a27dce3b4e296ddd9b'
assert manifest['capture_source_sha256']==sha(Path(__file__).with_name('PortPhases.cs'))
fields=['x','y','origin','type','troops','quality','morale','moves','shots','target','name'];checks=[];goals=[];choices=[];threats=[]
def diff(o,m):
 d=[dict(slot=i,field=k,original=o['slots'][i][k],port=m['slots'][i][k]) for i in range(40) for k in fields if o['slots'][i][k]!=m['slots'][i][k]]
 for i,(x,y) in enumerate(zip(o['grid'],m['grid'])):
  if x!=y:d.append(dict(cell=[i//12,i%12],field='grid',original=x,port=y))
 counts=[sum(x==i for x in o['actor_claim_targets']) for i in range(40)]
 for i,(x,y) in enumerate(zip(counts,m['claims'])):
  if x!=y:d.append(dict(slot=i,field='claim_count',original=x,port=y))
 return d
def check(label,o,m,allow=False):
 d=diff(o,m);checks.append(dict(label=label,counter=o['counter'],original_seq=o['seq'],equal=not d,differences=d))
 if not allow:assert not d,(label,o['seq'],d[:3])
 return d
for counter in range(3,7):
 model=read(a.model_phases/f'mix-rg_s1_r5_hook-hr{counter}.json');r=[x for x in rs if x['counter']==counter and x['kind']=='marker'];p2=[x for x in r if x['site']=='0x43a544'];eng=[x for x in r if x['site']=='0x43a160'];best=[x for x in r if x['site']=='0x439e08'];assert len(p2)==3
 assert [x['eax']&65535 for x in eng]==[x['slot'] for x in model['stages'][0]['units']]
 previous=-1
 for unit,e in zip(model['stages'][0]['units'],eng):
  bs=[x for x in best if previous<x['seq']<e['seq']];assert bs
  for b in bs:
   assert b['stack_words'][1]>>16==unit['slot'] and b['eax']&65535==b['slots'][unit['slot']]['type']
   check('before target-choice helper',b,unit['before']);assert b['flags'][:2]==list(map(int,model['initial']['computer_general'])) and b['flags'][2:]==[0,0]
  target=e['edx']&65535;assert target==unit['target'];check('after claim / before engage',e,unit['after_choice'])
  choices.append(dict(counter=counter,actor=unit['slot'],original_seq=e['seq'],original_target=target,port_target=unit['target'],same=True))
  stop=min([x['seq'] for x in best if x['seq']>e['seq']]+[p2[0]['seq']]);walks=[x for x in r if e['seq']<x['seq']<stop and x['site']=='0x438d24'];expected=[d for d in unit['decisions'] if d['step'] in [4,5]]
  assert len(walks)==len(expected)
  for w,d in zip(walks,expected):
   goal=[w['edx']&65535,w['edx']>>16];assert goal==[d['x'],d['y']] and w['eax']&65535==unit['slot'];check('before Pass1 Walk',w,unit['after_choice'])
   goals.append(dict(counter=counter,actor=unit['slot'],original_seq=w['seq'],stage='pass1',wine_goal=goal,port_goal=[d['x'],d['y']],equal=True,shared_input=True))
  previous=e['seq']
 check('after Pass1 / before first Pass2',p2[0],model['stages'][1]['before'])
 p3=next(x for x in r if x['site']=='0x43abb4');check('after first Pass2 / before Pass3',p3,model['stages'][1]['after'])
 for t in [x for x in r if x['site']=='0x43a718']:
  actor=t['eax']&65535;unit=next(u for u in model['stages'][2]['units'] if u['slot']==actor);before=check('before threat helper',t,unit['before'],allow=counter==6);probe=next(x for x in pure['rows'] if x['wine_input_seq']==t['seq']);d=unit['decisions'][0];assert d['step'] in [8,9]
  w=next(x for x in rs if x['seq']==probe['wine_walk_seq']);check('before threat Walk',w,unit['before'],allow=counter==6)
  goal=probe['wine_goal'];goals.append(dict(counter=counter,actor=actor,original_seq=probe['wine_walk_seq'],stage='pass3-threat',wine_goal=goal,port_goal=[d['x'],d['y']],equal=goal==[d['x'],d['y']],shared_input=not before))
  n=len(unit['threat_order']);threats.append(dict(counter=counter,actor=actor,original_seq=t['seq'],shared_input=not before,original_wine_goal=goal,original_x86_chosen_enemy=probe['original_x86_chosen_enemy'],port_chosen_enemy=d['enemy'],original_x86_order=probe['original_x86_order'][:n],original_x86_sorted_keys=probe['original_x86_sorted_keys'][:n],port_order=unit['threat_order'],port_keys=unit['threat_keys'],same_order=probe['original_x86_order'][:n]==unit['threat_order']))
 check('after threat / before nested Pass2',p2[1],model['stages'][3]['before'],allow=counter==6)
 check('after nested Pass2 / no flank / before final Pass2',p2[2],model['stages'][5]['before'],allow=counter==6)
 melee=next(x for x in r if x['site']=='0x4393ec');check('after final Pass2 / before melee slots-grid-claims only',melee,model['stages'][5]['after'],allow=counter==6)
 assert model['stages'][4]['before']==model['stages'][4]['after'] # no model flank action in prefix
assert not any(x['site']=='0x43910c' for x in rs if x['kind']=='marker')
assert not any(x['site']=='0x43aa88' for x in rs if x['kind']=='random')
first_goal=next(x for x in sorted(goals,key=lambda x:x['original_seq']) if not x['equal']);assert first_goal['counter']==6 and first_goal['actor']==22 and first_goal['shared_input'] and first_goal['wine_goal']==[5,3] and first_goal['port_goal']==[6,4]
first_threat=next(x for x in threats if x['counter']==6 and x['actor']==22);assert len(set(first_threat['original_x86_sorted_keys']))==len(first_threat['original_x86_sorted_keys']) and max(first_threat['original_x86_sorted_keys'])<1000000
first_rank=next((x for x in threats if not x['same_order']),None)
rec=dict(provenance='Fresh Wine goals/claims and validated production state comparisons; x86 order/chosen-enemy evidence separately labelled',inputs={str(p.name):sha(p) for p in [a.states,a.validation,a.pure]},model_phases=a.model_phases.name,source_sha256=sha(Path(__file__)),checks=checks,pass1_choices=choices,walk_goals=goals,threats=threats,first_observed_goal_difference=first_goal,first_x86_order_difference=first_rank,scope='Shared gameplay inputs through first differing goal; whole-battle fixes and other residual cases not established')
out=DATA/('attribution-'+time.strftime('%Y%m%d-%H%M%S',time.gmtime())+'.json')
with out.open('x') as f:json.dump(rec,f,indent=2);f.write('\n')
print(out);print('checks',len(checks),'Pass1choices',len(choices),'first goal',first_goal,'first rank HR',first_rank['counter'])
