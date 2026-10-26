"""GUI80 synthetic click/inspection controls only; no AI/battle completion.
Stock original; block staged on private copy, no live memory writes. See common.
"""
from common import *
from state import battle_block as BB
import argparse
CASES=[dict(id=f'{phase}-{name}',phase=phase,select=select,distant=distant,moves=moves,button=button) for phase in ['placement','movement'] for name,select,distant,moves,button in [('enemy-no-selection',False,False,4,1),('enemy-selected-adjacent',True,False,4,1),('enemy-selected-distant',True,True,4,1),('enemy-selected-zero-moves',True,False,0,1),('enemy-right-no-selection',False,False,4,3),('enemy-right-selected',True,False,4,3)]]
def info(g):
 count=g.i16(0x4a031c)
 return [sav.cstr(g.mem(0x49f00c+61*i,61)) for i in range(max(0,count+1))]
def observe(g):
 return dict(selected=g.i16(0x45e6a8),cursor=list(struct.unpack('<2h',g.mem(0x45e700,4))),info=info(g),slots=[BB.parse_slot(g.mem(drv.BATTLE_SLOTS+44*k,44),k) for k in [0,1,20,21]],phase=g.mem(0x4a0b7d,1)[0],side=g.i16(0x4a0b78),rng=struct.unpack('<I',g.mem(drv.RAND_SEED,4))[0])
def execute(c,g,private,stem):
 b=new_bytes();a,f,n=offsets(b);enemy_troops=30000 if c['moves']==0 else 2000;army_units(b,0,[3000,2000]);army_units(b,13,[enemy_troops,3000]);put(b,a+13*656+4,1)
 block=BB.synthetic_block([('ar',3000,7,0,'Audit own ar'),('hi',2000,7,0,'Audit own hi')],[('hi',enemy_troops,7,0,'Audit enemy hi'),('ar',3000,7,0,'Audit enemy ar')],attacker_army=0,defender_army=13,half_round=1)
 block['y1']=1 if c['phase']=='movement' else 0
 for k,x,y in [(0,3,3),(1,2,2),(20,8 if c['distant'] else 4,8 if c['distant'] else 3),(21,10,9)]:block['slots'][k].update(x=x,y=y,state=c['moves'] if k==0 else 4,target=-1)
 block['grid']=[50]*168
 for s in block['slots']:
  if s['alive']:block['grid'][BB.cell(s['x'],s['y'])]=20*s['side']+3*BB.TYPES.index(s['type'])+2
 tail=sav.parse(b)['tail_off'];b[tail+54]=1;b.extend(BB.encode_block(block))
 g.open(staged(b,private,stem));g.wait(lambda:g.in_battle(),8,'synthetic tactical load')
 before=save(g,private,stem,'before');windows=[w for w in g.find_windows() if ' v ' in w[1]];assert len(windows)==1,windows
 w=windows[0];title=w[1];g.raise_window(w[0]);events=[dict(action='open',**observe(g))]
 def cellclick(x,y,button=1):
  # Client origin of tactical form: nonclient top measured from X window rectangle.
  drv.sh('xdotool','mousemove',str(w[2]+16+x*32),str(w[3]+30+16+y*32));time.sleep(.15)
  drv.sh('xdotool','click','--window',str(w[0]),str(button));time.sleep(.7)
 if c['moves']==0:
  # Loading refreshes moves, so consume them through actual original shooting.
  cellclick(3,3)
  for attempt in range(10):
   z=observe(g)
   if z['slots'][0]['state']==0:break
   assert z['slots'][2]['troops']>0,'zero-control target must survive'
   cellclick(4,3,3);events.append(dict(action='prepare-zero-by-shot',**observe(g)))
  assert observe(g)['slots'][0]['state']==0,'zero control not reached'
 if c['select']:cellclick(3,3);events.append(dict(action='select-own',**observe(g)))
 cellclick(8 if c['distant'] else 4,8 if c['distant'] else 3,c['button']);events.append(dict(action='enemy-click',**observe(g)))
 g.shot(private/(stem+'-click.png'))
 # Read-only enemy roster through its actual toolbar button; then Cancel selection.
 g.click(w[2]+64,w[3]+14,pause=.5);events.append(dict(action='enemy-roster',**observe(g)))
 g.click(w[2]+89,w[3]+14,pause=.5);events.append(dict(action='cancel-selection',**observe(g)))
 after=save(g,private,stem,'after')
 public_row(stem,dict(case=c,turn=734,before_save=before.name,after_save=after.name,events=events,summary=dict(selected=[e['selected'] for e in events],info=[e['info'] for e in events],targets=[e['slots'][0]['target'] for e in events],moves=[e['slots'][0]['state'] for e in events],shots=[e['slots'][0]['ammo'] for e in events])))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--version',required=True);p.add_argument('--cases',nargs='*');q=p.parse_args();cases=[c for c in CASES if (not q.cases or c['id'] in q.cases) and (q.cases or c['id']!='movement-enemy-no-selection')];write_new(DATA/(q.version+'-matrix.json'),cases)
 for i,c in enumerate(cases):session(q.version+f'-c{i:02d}',execute,[c])
