"""Real supply UI arrows and staged Transfer. See common.py evidence rules."""
from common import *
import argparse
CASES=[dict(id='paid-army-room-'+str(room),kind='army',supply=101-room,purse=100,stock=330,steps=[1],transfer=True,finish='OK') for room in [-105,-5,-4,-1,0,51]]
CASES += [dict(id='paid-army-'+label,kind='army',supply=supply,purse=purse,stock=stock,steps=steps,transfer=tr,finish=finish) for label,supply,purse,stock,steps,tr,finish in [
 ('decrement-zero',0,100,330,[1,-1,-1],True,'OK'),('empty-city-overcap',206,100,0,[1],True,'OK'),
 ('poor-purse',0,3,330,[1],True,'OK'),('stage-close',206,100,330,[1],False,'Close'),('transfer-close',206,100,330,[1],True,'Close')]]
CASES += [dict(id='paid-fleet-room-'+str(room),kind='fleet',supply=160-room,purse=100,stock=330,steps=[1],transfer=True,finish='OK') for room in [-105,-5,-4,-1,0,51]]

def execute(c,g,private,stem):
 b=new_bytes();a,f,n=offsets(b);army_units(b,0,[10000]);put(b,a+10,c['supply'] if c['kind']=='army' else 0);put(b,a+12,c['purse'])
 put(b,f+2*26+14,c['supply'] if c['kind']=='fleet' else 0);put(b,f+2*26+16,c['purse'])
 put(b,sav.CITY_OFF+89*34+18,1);put(b,sav.CITY_OFF+89*34+24,c['stock']);put(b,n+0x26+2,0);put(b,n+1172+0x26,0)
 g.open(staged(b,private,stem));before=save(g,private,stem,'before');s0=snapshot(g)
 title='Supply army' if c['kind']=='army' else 'Supply fleet'
 if c['kind']=='army':g.army_tool(0,'supply',title)
 else:
  g.select_fleet(2);g.open_dialog(title,(g.fleet_x['supply'],drv.ARMY_TOOLBAR_Y))
 cs=inspect(title);write_new(private/(stem+'-controls.json'),cs)
 ups=sorted([x for x in cs if x['cls']=='TUpDown' and x['visible']],key=lambda x:(x['y'],x['x']))
 assert len(ups)==2,(ups,cs)
 form=struct.unpack('<I',g.mem(0x45e71c,4))[0]
 fields=list(struct.unpack('<4h',g.mem(form+0x288,8)));assert fields[0]==89,fields
 events=[dict(phase='open',staged=g.i16(form+0x290),state=snapshot(g))]
 for step in c['steps']:
  arrow(g,title,ups[-1],step);events.append(dict(phase='arrow',direction=step,staged=g.i16(form+0x290),state=snapshot(g)))
 g.shot(private/(stem+'-staged.png'))
 if c['transfer']:
  g.click_control(g.control(cs,text='Buy supplies'),pause=.6);events.append(dict(phase='transfer',staged=g.i16(form+0x290),state=snapshot(g)))
 close(g,title,cs,c['finish']);after=save(g,private,stem,'after');s1=snapshot(g)
 row=dict(case=c,turn=734,before_save=before.name,after_save=after.name,form_fields=fields,events=events,after=s1)
 target=lambda s:s['armies']['0'] if c['kind']=='army' else s['fleets']['2']
 row['summary']=dict(staged=[e['staged'] for e in events],target_before=[target(s0)['supplies'],target(s0)['money']],target_after=[target(s1)['supplies'],target(s1)['money']],city=[s0['city_stock'],s1['city_stock']],foreign_treasury_change=s1['foreign_treasury']-s0['foreign_treasury'])
 public_row(stem,row)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--version',required=True);p.add_argument('--cases',nargs='*');q=p.parse_args()
 session(q.version,execute,[c for c in CASES if not q.cases or c['id'] in q.cases])
