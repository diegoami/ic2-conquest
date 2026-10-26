"""Army dialog controls, real UI and read-only records. See common.py."""
from common import *
import argparse
CASES=[]
for side in [0,1]:
 for receiver in [900,1000,1100]:
  CASES.append(dict(id=f'money-side{side}-receiver{receiver}',mode='money',purses=[100,receiver] if side==0 else [receiver,100],side=side,presses=2,finish='OK'))
CASES += [dict(id='money-overcap-cancel',mode='money',purses=[100,1100],side=0,presses=1,finish='Cancel'),dict(id='split-money-shared',mode='money',purses=[1100,100],side=1,presses=1,split=True,counts=[[5000,5000],[10000]],finish='Cancel')]
for label,sups,selected,finish in [('over-ok',[206,0],0,'OK'),('over-cancel',[206,0],0,'Cancel'),('over-reversed',[206,0],13,'OK'),('within',[50,20],0,'OK'),('both-over',[206,150],0,'OK'),('both-over-reversed',[206,150],13,'OK')]:
 CASES.append(dict(id='unchanged-'+label,mode='unchanged',supplies=sups,selected=selected,finish=finish))
for side in [0,1]:
 CASES += [dict(id=f'partial19plus2-side{side}',mode='units',counts=[[1000]*3,[1000]*19] if side==0 else [[1000]*19,[1000]*3],side=side,rows=[0,1],finish='OK'),dict(id=f'partial18plus3-side{side}',mode='units',counts=[[1000]*3,[1000]*18] if side==0 else [[1000]*18,[1000]*3],side=side,rows=[0,1,2],finish='OK')]
 CASES.append(dict(id=f'troop100000-side{side}',mode='units',counts=[[500,1000,2000,1000],[24500]*4] if side==0 else [[24500]*4,[500,1000,2000,1000]],side=side,rows=[0,1,2,3],finish='OK'))
 for total in [15000,15499,15500]:
  # Donor retains slot0, one transferred unit increases receiver to boundary.
  donor=[1000,total-14000];recipient=[14000]
  CASES.append(dict(id=f'transport{total}-side{side}',mode='units',counts=[donor,recipient] if side==0 else [recipient,donor],side=side,rows=[1],carrier=13 if side==0 else 0,finish='OK'))
CASES.append(dict(id='partial19plus2-cancel',mode='units',counts=[[1000]*3,[1000]*19],side=0,rows=[0,1],finish='Cancel'))

CASES += [dict(id='two-refusal-types',mode='units',counts=[[100,100,500],[790]*18+[780]],side=0,rows=[0,1,2],carrier=13,finish='OK'),dict(id='partial19plus2-right-cancel',mode='units',counts=[[1000]*19,[1000]*3],side=1,rows=[0,1],finish='Cancel')]

def setup(c):
 b=new_bytes();a,f,n=offsets(b)
 for idx,aid in enumerate([0,12,13]):
  army_units(b,aid,c.get('counts',[[10000],[10000]])[0 if aid==0 else 1])
  put(b,a+aid*656+10,c.get('supplies',[0,0])[0 if aid==0 else 1]);put(b,a+aid*656+12,c.get('purses',[100,100])[0 if aid==0 else 1]);put(b,a+aid*656+6,7)
 # Move army13 synthetically to known plain tile beside0, army12 away. Keep map consistent.
 def relocate(aid,x,y,cell=2):
  off=a+aid*656;ox,oy=sav.i16(b,off),sav.i16(b,off+2);oldcell=sav.i16(b,off+8)
  put(b,(ox*140+oy)*2,oldcell if oldcell>=0 else 0)
  put(b,off,x);put(b,off+2,y);put(b,off+8,cell)
  if cell>=0:put(b,(x*140+y)*2,200)
 relocate(12,110,40);relocate(13,102,45)
 if c.get('carrier') is not None:
  aid=c['carrier'];off=a+aid*656
  relocate(aid,101,46,-1);put(b,f+2*26+22,aid);put(b,f+2*26+18,30)
 return b

def copies(g,form):
 fields=list(struct.unpack('<6h',g.mem(form+0x76c,12)))
 return dict(ids=fields,working=[sav.parse_army(g.mem(form+o,656),fields[i*1]) for i,o in enumerate([0x24c,0x4dc])],global_state=snapshot(g))

def execute(c,g,private,stem):
 b=setup(c);g.open(staged(b,private,stem));before=save(g,private,stem,'before');s0=snapshot(g)
 selected=c.get('selected',0)
 if c.get('carrier')==selected:g.select_fleet(2);army_menu(g,2);g.wait(lambda:g.find_windows('^Army to army transfer$'),8,'army transfer through selected carrier')
 else:g.army_tool(selected,'split' if c.get('split') else 'transfer','Split army' if c.get('split') else 'Army to army transfer')
 title='Split army' if c.get('split') else 'Army to army transfer'
 cs=inspect(title);write_new(private/(stem+'-controls.json'),cs)
 form=struct.unpack('<I',g.mem(0x45e72c,4))[0];events=[dict(phase='open',**copies(g,form))];boxes=[]
 if c['mode']=='money':
  ups=sorted([x for x in cs if x['cls']=='TUpDown' and x['visible']],key=lambda x:(x['y'],x['x']))
  assert len(ups)==4,ups
  # Money row is lower row, right spinner100, up transfers right->left.
  for i in range(c['presses']):
   arrow(g,title,ups[-1],-1 if c['side']==0 else 1);events.append(dict(phase='arrow',**copies(g,form)))
 elif c['mode']=='units':
  lists=sorted([x for x in cs if x['cls']=='TListBox'],key=lambda x:x['x']);lst=lists[c['side']]
  win=g.find_windows('^'+title+'$')[0][0];g.raise_window(win)
  drv.sh('xdotool','keydown','ctrl')
  try:
   for k in c['rows']:point_click(g,title,lst['cx']+lst['w']//2,lst['cy']+lst['item_h']*k+lst['item_h']//2)
  finally:drv.sh('xdotool','keyup','ctrl')
  g.shot(private/(stem+'-selection.png'))
  buttons=sorted([x for x in cs if x['text']=='Transfer'],key=lambda x:x['x'])
  g.click_control(buttons[c['side']],pause=.8)
  boxes=g.dismiss_popups();events.append(dict(phase='transfer',boxes=boxes,**copies(g,form)))
 g.shot(private/(stem+'-before-close.png'))
 close(g,title,cs,c['finish']);after=save(g,private,stem,'after');s1=snapshot(g)
 row=dict(case=c,turn=734,before_save=before.name,after_save=after.name,before=s0,after=s1,events=events,boxes=boxes)
 row['summary']=dict(before=[[s0['armies'][str(i)]['money'],s0['armies'][str(i)]['supplies'],s0['armies'][str(i)]['troops']] for i in [0,13]],after=[[s1['armies'][str(i)]['money'],s1['armies'][str(i)]['supplies'],s1['armies'][str(i)]['troops']] for i in [0,13]],working_money=[[a['money'] for a in e['working']] for e in events],boxes=boxes)
 public_row(stem,row)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--version',required=True);p.add_argument('--cases',nargs='*');q=p.parse_args();session(q.version,execute,[c for c in CASES if not q.cases or c['id'] in q.cases])
