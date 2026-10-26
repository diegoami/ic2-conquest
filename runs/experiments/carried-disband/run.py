#!/usr/bin/env python3
"""Conquest218: authorized stock-original GUI caller controls.
Never overwrite/delete any save or measurement, including failed attempts.
Private original bytes/fullstates/screenshots/hashes stay ignored. No memory
writes, patches, Endturn, owner desktop, battle/AI or remake modification.
"""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,sys,time,os,threading
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'runs/experiments/restrictions85'))
import common as c
ART=ROOT/'artifacts/run-exp-carried-disband';DATA=ROOT/'runs/experiments/data/run-exp-carried-disband'
c.ART=ART;c.DATA=DATA;c.drv.DISPLAY=os.environ.get('DISBAND218_DISPLAY',':760');c.drv.ENV['DISPLAY']=c.drv.DISPLAY
write_new=c.write_new;sav=c.sav;drv=c.drv
CASES=[
 dict(id='carried-after-nooffer-recruit-toolbar-yes',mode='whole',recruit_toolbar=True,toolbar=True),
 dict(id='carried-after-nooffer-recruit-toolbar-no',mode='whole',recruit_toolbar=True,toolbar=True,confirm_no=True),
 dict(id='carried-after-nooffer-recruit-menu',mode='whole',recruit_toolbar=True),
 *[dict(id='carried-nooffer-fast-'+str(ms)+'ms',mode='whole',fast_ms=ms)for ms in [0,20,150]],
 dict(id='land-whole-no',mode='whole',land=True,confirm_no=True),
 dict(id='land-whole-yes',mode='whole',land=True),
 dict(id='land-toolbar-whole',mode='whole',land=True,toolbar=True),
 dict(id='carried-toolbar-whole',mode='whole',toolbar=True),
 dict(id='carried-whole-left',mode='whole'),
 dict(id='carried-whole-right',mode='whole',right=True),
 dict(id='carried-after-change-cancel',mode='whole',preceding='Cancel'),
 dict(id='carried-after-change-ok',mode='whole',preceding='OK'),
 dict(id='carried-change-last-ok',mode='change',finish='OK',reopen=True),
 dict(id='carried-change-last-cancel',mode='change',finish='Cancel'),
 dict(id='carried-change-regular-no-city',mode='change',finish='OK',owncity=False),
 dict(id='carried-change-merc-no-city',mode='change',finish='OK',owncity=False,merc=True,reopen=True),
 dict(id='carried-transfer-disband-ok',mode='transfer',finish='OK',reopen=True),
 dict(id='carried-transfer-disband-cancel',mode='transfer',finish='Cancel'),
 dict(id='land-after-disembark-whole',mode='whole',disembark=True),
]

def stage(case,private,stem):
 b=c.new_bytes();a,f,n=c.offsets(b);c.army_units(b,0,[5000]);c.put(b,a+10,23);c.put(b,a+12,37);c.put(b,a+6,7)
 if case.get('merc'):c.put(b,a+16,38)
 if not case.get('land'):
  c.put(b,(101*140+45)*2,2);c.put(b,a,101);c.put(b,a+2,46);c.put(b,a+8,-1);c.put(b,f+2*26+22,0)
 c.put(b,f+2*26+18,30);c.put(b,f+2*26+12,7)
 if not case.get('owncity',True):
  c.put(b,sav.CITY_OFF+89*34+18,1);c.put(b,(102*140+46)*2,37);c.put(b,n+0x26+2,3);c.put(b,n+1172+0x26,3)
 if case['mode']=='transfer':
  for aid,x,y in [(12,110,40),(13,102,45)]:
   off=a+aid*656;ox,oy=sav.i16(b,off),sav.i16(b,off+2);c.put(b,(ox*140+oy)*2,sav.i16(b,off+8))
   c.put(b,off,x);c.put(b,off+2,y);c.put(b,(x*140+y)*2,200)
  c.army_units(b,13,[3000]);c.put(b,a+13*656+10,7);c.put(b,a+13*656+12,11);c.put(b,a+13*656+6,7)
 return c.staged(b,private,stem)

def observed(g):
 form=struct.unpack('<I',g.mem(0x45e740,4))[0]
 armies={str(i):sav.parse_army(g.army_rec(i),i) for i in [0,13]}
 # Only controlled target/partner scalar records are public; fullworld onlySAV.
 return dict(selection=list(struct.unpack('<3h',g.mem(form+0x220,6))),globals=[g.i16(drv.SEL_ARMY),g.i16(drv.SEL_FLEET)],
             cursor=list(struct.unpack('<2h',g.mem(form+0x21a,4))),armies=armies,carrier=g.fleet_state(2),
             treasury=struct.unpack('<i',g.mem(drv.NATIONS+0x438,4))[0],mobilization=g.i16(drv.NATIONS+0x442),city_stock=g.i16(0x479590+89*34+24))

def toolbar(g,tool,label,carried=True):
 guess=g.army_x.get(tool,{'disband':493,'mercs':372}[tool])+(150 if carried else 0)
 for x in [guess,guess+3,guess-3,guess+6,guess-6]:
  drv.sh('xdotool','mousemove',str(x),str(drv.ARMY_TOOLBAR_Y));time.sleep(.8)
  if any(w[1]==label for w in g.find_windows('.',tooltips=True)):return x
 raise AssertionError('actual toolbar tooltip not found: '+label)

def execute(case,g,private,stem):
 events=[]
 def record(phase,**kwargs):
  e=dict(phase=phase,state=observed(g),**kwargs);events.append(e)
  write_new(DATA/(stem+f'-step{len(events):02d}.json'),e)
  return e
 p=stage(case,private,stem);g.open(p);before=c.save(g,private,stem,'before');record('loaded')
 if case.get('land'):g.select_army(0,*g.army_pos(0))
 else:g.select_fleet(2)
 record('selected')
 if case.get('right'):
  x,y=g.show(*g.fleet_pos(2));win=g.find_windows('^Unit map$')[0][0];g.raise_window(win)
  drv.sh('xdotool','mousemove',str(x),str(y));drv.sh('xdotool','click','--window',str(win),'3');time.sleep(.5);record('right-fleet-click')
 if case.get('disembark'):
  boxes=g.disembark(2,101,45);record('disembarked',boxes=boxes)
  assert g.army_state(0)['cell']>=0 and g.fleet_state(2)['army']==-1
  g.select_army(0,*g.army_pos(0))
 if case.get('recruit_toolbar'):
  st=sav.load(before);near=[x for x in st['cities'] if max(abs(x['x']-101),abs(x['y']-46))<=1]
  assert not any((m['x'],m['y'])==(city['x'],city['y'])for m in st['mercenaries']for city in near),'no-offer precondition'
  x=toolbar(g,'mercs','Recruit mercenaries');record('verified-recruit-toolbar',x=x,tooltip='Recruit mercenaries')
  g.click(x,drv.ARMY_TOOLBAR_Y,pause=.8);boxes=g.dismiss_popups();opened=bool(g.find_windows('^Recruit mercenary unit$'))
  record('nooffer-recruit-returned',boxes=boxes,recruit_dialog_open=opened);assert not opened
 if case.get('preceding') or case['mode']=='change':
  c.army_menu(g,5);g.wait(lambda:g.find_windows('^Change units$'),8,'Change units');cs=c.inspect('Change units')
  form=struct.unpack('<I',g.mem(0x45e73c,4))[0]
  record('change-open',bound_army=g.i16(form+0x1d4),nearby_city=g.i16(form+0x1d6),working=sav.parse_army(g.mem(form+0x1da,656),0))
  if case['mode']=='change':
   lst=g.control(cs,cls='TListBox');c.point_click(g,'Change units',lst['x']+lst['w']//2,lst['y']-8);g.click_list_row(lst,0,pause=.3)
   selection=c.list_rows('Change units');assert selection[0]['selected_count']==1,selection
   g.click_control(g.control(cs,text='Disband'),pause=.7);boxes=g.dismiss_popups()
   record('change-disband-confirmed',boxes=boxes,working=sav.parse_army(g.mem(form+0x1da,656),0),working_mobilization=g.i16(form+0x1d8))
   g.shot(private/(stem+'-working.png'))
  c.close(g,'Change units',cs,case.get('preceding',case.get('finish','Cancel')));record('change-returned')
 if case['mode']=='transfer':
  c.army_menu(g,2);g.wait(lambda:g.find_windows('^Army to army transfer$'),8,'Army transfer');cs=c.inspect('Army to army transfer')
  form=struct.unpack('<I',g.mem(0x45e72c,4))[0];ids=list(struct.unpack('<2h',g.mem(form+0x76c,4)));assert ids==[0,13],ids
  record('transfer-open',bound_armies=ids)
  lst=min([x for x in cs if x['cls']=='TListBox'],key=lambda x:x['x']);c.point_click(g,'Army to army transfer',lst['x']+lst['w']//2,lst['y']-8);g.click_list_row(lst,0,pause=.3)
  selection=sorted(c.list_rows('Army to army transfer'),key=lambda x:x['x']);assert selection[0]['selected_count']==1,selection
  disband=min([x for x in cs if x['text']=='Disband'],key=lambda x:x['x']);g.click_control(disband,pause=.7);boxes=g.dismiss_popups()
  record('transfer-disband-confirmed',boxes=boxes,working=[sav.parse_army(g.mem(form+o,656),i) for o,i in [(0x24c,0),(0x4dc,13)]])
  g.shot(private/(stem+'-working.png'));c.close(g,'Army to army transfer',cs,case['finish']);record('transfer-returned')
 if case['mode']=='whole':
  record('before-whole-command')
  if 'fast_ms'in case:
   merc=toolbar(g,'mercs','Recruit mercenaries');dis=toolbar(g,'disband','Disband army');g.select_fleet(2)
   form=struct.unpack('<I',g.mem(0x45e740,4))[0];trace=[];stop=threading.Event();origin=time.monotonic()
   def sample():
    with open(f'/proc/{g.pid}/mem','rb',buffering=0)as f:
     while not stop.is_set():
      f.seek(form+0x220);raw=f.read(6);values=list(struct.unpack('<3h',raw))
      if not trace or values!=trace[-1]['selection']:trace.append(dict(ms=round((time.monotonic()-origin)*1000,3),selection=values))
      time.sleep(.001)
   thread=threading.Thread(target=sample);thread.start()
   try:
    record('verified-fast-toolbar-pair',recruit_x=merc,disband_x=dis,spacing_ms=case['fast_ms'])
    drv.sh('xdotool','mousemove',str(merc),str(drv.ARMY_TOOLBAR_Y),'click','1','sleep',str(case['fast_ms']/1000),'mousemove',str(dis),str(drv.ARMY_TOOLBAR_Y),'click','1');time.sleep(.8)
   finally:stop.set();thread.join()
   record('fast-selection-trace',trace=trace)
  elif case.get('toolbar'):
   found=toolbar(g,'disband','Disband army',carried=not case.get('land',False))
   record('verified-disband-toolbar',x=found,tooltip='Disband army');g.shot(private/(stem+'-toolbar-tooltip.png'));g.click(found,drv.ARMY_TOOLBAR_Y,pause=.7)
  else:c.army_menu(g,6)
  time.sleep(.7)
  if case.get('confirm_no') and g.find_windows('^Confirm$'):
   box=g.find_windows('^Confirm$')[0];boxes=[g.read_popup(box)];g._answer_confirm(box[0],yes=False)
  else:boxes=g.dismiss_popups()
  record('whole-command-returned',boxes=boxes)
 g.shot(private/(stem+'-final.png'));after=c.save(g,private,stem,'after');record('saved')
 reopened=None
 if case.get('reopen'):
  g.open(after);record('fresh-load-after');reopened=c.save(g,private,stem,'reopened');record('fresh-save-after')
 row=dict(case=case,turn=734,before_save=before.name,after_save=after.name,reopened_save=reopened.name if reopened else None,events=events)
 last=events[-1]['state'];row['summary']=dict(army_owner=last['armies']['0']['owner'],troops=last['armies']['0']['troops'],carrier_link=last['carrier']['army'],treasury=last['treasury'],city_stock=last['city_stock'],mobilization=last['mobilization'],selection=last['selection'])
 c.public_row(stem,row)

def main():
 q=argparse.ArgumentParser();q.add_argument('--version',required=True);q.add_argument('--cases',nargs='*');args=q.parse_args()
 exe=drv.G/'Imperial Conquest 2.exe';assert exe.read_bytes()==Path('/home/diego/ic2-work/build/Imperial Conquest 2.exe').read_bytes()
 c.session(args.version,execute,[x for x in CASES if not args.cases or x['id']in args.cases])
if __name__=='__main__':main()
