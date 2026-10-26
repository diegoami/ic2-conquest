"""Bounded manual-family leads; real visible GUI; see common.py."""
from common import *
import argparse
CASES=[dict(id=f'fleet-money-{m}',kind='fleet',receiver=m,donor=200) for m in [950,1000,1100]]
CASES += [dict(id='fleet-ships-only-overcap',kind='fleet',receiver=1100,donor=200,ships=True),dict(id='fleet-money-cancel',kind='fleet',receiver=950,donor=200,finish='Cancel'),dict(id='carried-disband-direct',kind='disband'),dict(id='carried-disband-after-supply',kind='disband',supply=True)]
def execute(c,g,private,stem):
 b=new_bytes();a,f,n=offsets(b)
 if c['kind']=='fleet':
  put(b,f+2*26+16,c['receiver']);put(b,f+5*26+16,c['donor'])
 else:
  army_units(b,0,[10000]);put(b,(101*140+45)*2,2);put(b,a,101);put(b,a+2,46);put(b,a+8,-1);put(b,f+2*26+22,0);put(b,a+10,23);put(b,a+12,37)
 g.open(staged(b,private,stem));before=save(g,private,stem,'before');s0=snapshot(g);events=[]
 if c['kind']=='fleet':
  g.select_fleet(5);title='Fleet to fleet transfer';g.open_dialog(title,(g.fleet_x['transfer'],drv.ARMY_TOOLBAR_Y));cs=inspect(title)
  write_new(private/(stem+'-controls.json'),cs)
  ups=sorted([x for x in cs if x['cls']=='TUpDown' and x['visible']],key=lambda x:(x['y'],x['x']))
  # First pair ships10s/1s, next supply10s/100s, last money10s/100s.
  assert len(ups)==6,ups
  arrow(g,title,ups[0] if c.get('ships') else ups[-1],-1)
  g.shot(private/(stem+'-arrow.png'));events.append(dict(phase='arrow',state=snapshot(g)))
  close(g,title,cs,c.get('finish','OK'));boxes=[]
 else:
  g.select_fleet(2)
  if c.get('supply'):
   army_menu(g,0);g.wait(lambda:g.find_windows('^Supply army$'),8,'supply through carrier');g.close_controls('Supply army',inspect('Supply army'))
  unitmap=struct.unpack('<I',g.mem(0x45e740,4))[0]
  events.append(dict(phase='before-disband',selection_fields=list(struct.unpack('<3h',g.mem(unitmap+0x220,6))),state=snapshot(g)))
  army_menu(g,6);time.sleep(.8);boxes=g.dismiss_popups();g.shot(private/(stem+'-result.png'))
 after=save(g,private,stem,'after');s1=snapshot(g)
 z0=sav.load(before);z1=sav.load(after)
 row=dict(case=c,turn=734,before_save=before.name,after_save=after.name,before=s0,after=s1,events=events,boxes=boxes)
 row['summary']=dict(fleets_before=[[s0['fleets'][str(i)]['money'],s0['fleets'][str(i)]['ships']] for i in [2,5]],fleets_after=[[s1['fleets'][str(i)]['money'],s1['fleets'][str(i)]['ships']] for i in [2,5]],treasury_change=z1['nations'][0]['treasury']-z0['nations'][0]['treasury'],boxes=boxes,army_owner=s1['armies']['0']['owner'],carrier_link=s1['fleets']['2']['army'])
 public_row(stem,row)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--version',required=True);p.add_argument('--cases',nargs='*');q=p.parse_args();session(q.version,execute,[c for c in CASES if not q.cases or c['id'] in q.cases])
