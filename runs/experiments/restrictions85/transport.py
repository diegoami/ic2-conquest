"""Separate human embark/hire callers, exact Research83 controls. See common.py."""
from common import *
import argparse
CASES=[dict(id=f'{kind}-{num}',kind=kind,total=num) for kind in ['embark','hire'] for num in [5000,5001,5499,5500]]
CASES+=[dict(id='hire-opening-overcap',kind='hire',total=6000,base=5500)]

def execute(c,g,private,stem):
 b=new_bytes();a,f,n=offsets(b);total=c['total'];base=c.get('base',4000)
 army_units(b,0,[total if c['kind']=='embark' else base]);put(b,a+6,7);put(b,a+10,100);put(b,a+12,30000);put(b,f+2*26+18,10);put(b,f+2*26+12,7)
 if c['kind']=='hire':
  # Legal embarked link/marker plus one public synthetic offer at adjacent Antium.
  x,y=101,46;ox,oy=sav.i16(b,a),sav.i16(b,a+2);put(b,(ox*140+oy)*2,sav.i16(b,a+8))
  put(b,a,x);put(b,a+2,y);put(b,a+8,-1);put(b,f+2*26+22,0)
  mo=n+16*1172
  # Remove other offers only from this synthetic copy, retain all originals.
  for k in range(50):put(b,mo+12*k+8,-1)
  struct.pack_into('<6h',b,mo,102,46,1,0,total-base,6)
 g.open(staged(b,private,stem));before=save(g,private,stem,'before');s0=snapshot(g)
 if c['kind']=='embark':
  boxes=g.embark(0,2);opened=None;during=snapshot(g)
 else:
  g.select_fleet(2)
  if not g.army_x:g.calibrate_army_toolbar()
  g.click(g.army_x['mercs'],drv.ARMY_TOOLBAR_Y,pause=1)
  time.sleep(1);boxes=g.dismiss_popups();opened=bool(g.find_windows('^Recruit mercenary unit$'))
  if opened:
   cs=inspect('Recruit mercenary unit');write_new(private/(stem+'-controls.json'),cs)
   lst=g.control(cs,cls='TListBox');g.click_list_row(lst,0,pause=.4)
   g.shot(private/(stem+'-offer.png'))
   g.click_control(g.control(cs,text='Recruit unit'),pause=.8);boxes+=g.dismiss_popups()
   during=snapshot(g)
   try:cs=inspect('Recruit mercenary unit')
   except subprocess.CalledProcessError:cs=[]
   if cs:g.close_controls('Recruit mercenary unit',cs)
  else:during=snapshot(g)
 g.shot(private/(stem+'-result.png'));after=save(g,private,stem,'after');s1=snapshot(g)
 row=dict(case=c,turn=734,before_save=before.name,after_save=after.name,before=s0,during=during,after=s1,opened=opened,boxes=boxes)
 row['summary']=dict(opened=opened,boxes=boxes,troops=[s0['armies']['0']['troops'],s1['armies']['0']['troops']],army_cell=s1['armies']['0']['cell'],carrier_army=s1['fleets']['2']['army'],moves=[s1['armies']['0']['moves'],s1['fleets']['2']['moves']])
 public_row(stem,row)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--version',required=True);p.add_argument('--cases',nargs='*');q=p.parse_args();session(q.version,execute,[c for c in CASES if not q.cases or c['id'] in q.cases])
