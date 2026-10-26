"""Separate provider enumeration and carried-army UI callers; see common.py."""
from common import *
import argparse
CASES=[dict(id='providers-city-stock-low-first',kind='providers',stocks=[10,90]),dict(id='providers-city-stock-reversed',kind='providers',stocks=[90,10]),dict(id='providers-four-fleets',kind='providers',stocks=[10,90],extra=True)]
CASES += [dict(id='carried-'+name,kind='carried',city=city,other=other,full=full,stale=stale) for name,city,other,full,stale in [('carrier-alone',False,False,False,False),('city',True,False,False,False),('other-fleet',False,True,False,False),('full-city-other',True,True,True,False),('stale-coordinates',True,True,False,True)]]
def provider_state(g):
 s=snapshot(g);s['provider_cities']={str(i):g.i16(0x479590+i*34+24) for i in [85,89,91]};s['provider_fleets']={str(i):g.fleet_state(i) for i in [0,1,2,5]};return s

def execute(c,g,private,stem):
 b=new_bytes();a,f,n=offsets(b);army_units(b,0,[10000]);put(b,a+10,0);put(b,a+12,37)
 if c['kind']=='providers':
  # Distinct two synthetic cities and four own fleets around army0 at101,45.
  for cid,x,y,stock in [(85,100,44,c['stocks'][0]),(89,102,46,c['stocks'][1])]:
   co=sav.CITY_OFF+cid*34;ox,oy=sav.i16(b,co+14),sav.i16(b,co+16);put(b,(ox*140+oy)*2,2)
   put(b,co+14,x);put(b,co+16,y);put(b,co+24,stock);put(b,(x*140+y)*2,20)
  fleetids=[2,5,0,1] if c.get('extra') else [2,5]
  for k,fid in enumerate(fleetids):
   off=f+fid*26;ox,oy=sav.i16(b,off),sav.i16(b,off+2);put(b,(ox*140+oy)*2,sav.i16(b,off+24))
   x,y=[(100,45),(100,46),(101,44),(102,44)][k];put(b,off,x);put(b,off+2,y);put(b,off+8,0);put(b,off+14,100+k*10);put(b,off+16,200+k*10);put(b,(x*140+y)*2,300)
 else:
  # Carrier at101,46. Army marker removed, actual carried link valid.
  put(b,(101*140+45)*2,2);put(b,a,101);put(b,a+2,46);put(b,a+8,-1);put(b,f+2*26+22,0)
  put(b,a+10,101 if c['full'] else 0);put(b,f+2*26+14,123);put(b,f+2*26+16,321);put(b,f+5*26+14,77);put(b,f+5*26+16,217)
  if not c['city']:put(b,sav.CITY_OFF+89*34+18,1);put(b,n+0x26+2,3);put(b,n+1172+0x26,3)
  if not c['other']:
   put(b,(101*140+47)*2,0);put(b,f+5*26,110);put(b,f+5*26+2,60);put(b,(110*140+60)*2,300)
  if c['stale']:put(b,a,90);put(b,a+2,30)
 g.open(staged(b,private,stem));before=save(g,private,stem,'before');s0=snapshot(g)
 if c['kind']=='providers':g.army_tool(0,'supply','Supply army')
 else:g.select_fleet(2);army_menu(g,0)
 opened=bool(g.find_windows('^Supply army$'));events=[]
 if opened:
  cs=inspect('Supply army');lst=g.control(cs,cls='TListBox');form=struct.unpack('<I',g.mem(0x45e71c,4))[0]
  for k in range(lst['count']):
   if k:g.click_list_row(lst,k,pause=.3)
   fields=list(struct.unpack('<9h',g.mem(form+0x27e,18)))
   events.append(dict(row=k,fields=fields,lists=list_rows('Supply army'),state=provider_state(g)))
   if c['kind']=='providers':
    # Each row separately, choose small10 free-supply arrow.
    ups=sorted([x for x in cs if x['cls']=='TUpDown' and x['visible']],key=lambda x:(x['y'],x['x']))
    arrow(g,'Supply army',ups[0],1);events.append(dict(row=k,phase='supply10',state=provider_state(g)))
  g.shot(private/(stem+'-dialog.png'))
  if c['kind']=='carried':
   cs=inspect('Supply army');ups=sorted([x for x in cs if x['cls']=='TUpDown' and x['visible']],key=lambda x:(x['y'],x['x']))
   if len(ups)==4:
    arrow(g,'Supply army',ups[0],1);arrow(g,'Supply army',ups[-1],1);events.append(dict(phase='supply10-money100',state=provider_state(g)))
  close(g,'Supply army',cs,'OK')
 after=save(g,private,stem,'after');s1=snapshot(g)
 public_row(stem,dict(case=c,turn=734,before_save=before.name,after_save=after.name,before=s0,after=s1,events=events,summary=dict(opened=opened,providers=[e.get('fields') for e in events if 'fields'in e],army=[s1['armies']['0']['supplies'],s1['armies']['0']['money']],carrier=[s1['fleets']['2']['supplies'],s1['fleets']['2']['money']])))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--version',required=True);p.add_argument('--cases',nargs='*');q=p.parse_args();session(q.version,execute,[c for c in CASES if not q.cases or c['id'] in q.cases])
