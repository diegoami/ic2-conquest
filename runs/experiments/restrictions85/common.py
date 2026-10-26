"""Owner-authorized Research85/GUI controls (conquest211).
Never delete/overwrite measured files or saves; unique batch versions mandatory.
Original bytes, full states/screenshots and hashes stay private. No End turn,
original patch, game-memory write, owner-desktop access or remake modification.
"""
import importlib.util,json,os,struct,subprocess,sys,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('funding_base',ROOT/'runs/experiments/manual-funding1456/run.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
drv=base.drv;sav=base.sav
ART=ROOT/'artifacts/run-exp-restrictions85';DATA=ROOT/'runs/experiments/data/run-exp-restrictions85'
WORK=Path(os.environ.get('RESTRICTIONS85_WORK',str(ART/'work-v1')));base.WORK=WORK
drv.WORK=WORK;drv.PREFIX=WORK/'prefix';drv.G=drv.PREFIX/'drive_c/IC2';drv.DISPLAY=os.environ.get('RESTRICTIONS85_DISPLAY',':757')
drv.ENV.update(DISPLAY=drv.DISPLAY,WINEPREFIX=str(drv.PREFIX))
drv.TOOLBAR_CACHE=WORK/'toolbar.json';drv.ARMY_TOOLBAR_CACHE=WORK/'army_toolbar.json';drv.FLEET_TOOLBAR_CACHE=WORK/'fleet_toolbar.json'
write_new=base.write_new;inspect=base.inspect
class Game(base.Game):
 def ensure_xvfb(self):
  # Reuse only servers created by this task's two retained pilots.
  owned={':757':1764560,':758':1782883}
  pid=owned.get(drv.DISPLAY)
  if pid and Path(f'/proc/{pid}/cmdline').exists():
   cmd=Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
   assert cmd[:2]==[b'Xvfb',drv.DISPLAY.encode()],cmd
   write_new(self.private_dir/'display.json',dict(display=drv.DISPLAY,pid=pid,origin='same-task retained pilot Xvfb'));return
  self.display_process=subprocess.Popen(['Xvfb',drv.DISPLAY,'-screen','0','1280x1024x24','-nolisten','tcp'],stdout=self.private_log,stderr=self.private_log);time.sleep(2)
  assert self.display_process.poll() is None,'Xvfb failed; do not attach unknown display'

def session(version,fn,cases):
 private=ART/('private-'+version);private.mkdir()
 write_new(DATA/(version+'-plan.json'),cases)
 g=Game(log=lambda x:None);g.private_dir=private
 with (private/'runtime.log').open('x') as log:
  g.private_log=log
  try:
   g.start()
   for c in cases:
    stem=version+'_'+c['id'];fn(c,g,private,stem)
  except BaseException as e:
   write_new(DATA/(version+'-failure.json'),dict(type=type(e).__name__,message=str(e)))
   raise
  finally:
   subprocess.run(['/usr/lib/wine/wineserver','-k'],env=drv.ENV,capture_output=True)
   if hasattr(g,'display_process'):g.display_process.terminate();g.display_process.wait(timeout=10)
   write_new(private/'hashes.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in private.iterdir() if p.is_file()})

def offsets(b):return base.offsets(b)
def new_bytes():return bytearray((ROOT/'saves/fleet-split-antium-0734.SAV').read_bytes())
def put(b,off,v,fmt='<h'):struct.pack_into(fmt,b,off,v)
def army_units(b,aid,counts):
 a,_,_=offsets(b);off=a+aid*656
 b[off+16:off+656]=bytes(640)
 for k,num in enumerate(counts):
  u=off+16+32*k;struct.pack_into('<4h',b,u,0,1,num,7)
  name=f'A{aid}S{k}'.encode();b[u+8:u+8+len(name)]=name

def staged(b,private,stem):
 old=new_bytes();changes=[i for i,(a,z) in enumerate(zip(old,b)) if a!=z]
 write_new(private/(stem+'-stage.json'),dict(changed_offsets=changes))
 p=private/(stem+'_staged.SAV')
 with p.open('xb') as f:f.write(b)
 return p

def snapshot(g):
 return dict(armies={str(i):sav.parse_army(g.army_rec(i),i) for i in [0,12,13]},fleets={str(i):g.fleet_state(i) for i in [2,5]},
             city_stock=g.i16(0x479590+89*34+24),foreign_treasury=struct.unpack('<i',g.mem(drv.NATIONS+1172+0x438,4))[0],
             selected=[g.i16(drv.SEL_ARMY),g.i16(drv.SEL_FLEET)])
def save(g,private,stem,phase):
 name=stem+'_'+phase+'.SAV';p=g.save_as(name);dest=private/name
 assert not dest.exists();dest.write_bytes(p.read_bytes());return dest

def point_click(g,title,x,y):
 win=g.find_windows('^'+title+'$')[0][0];g.raise_window(win)
 drv.sh('xdotool','mousemove',str(x),str(y));time.sleep(.15)
 drv.sh('xdotool','click','--window',str(win),'1');time.sleep(.45)
def arrow(g,title,c,direction):
 assert c['visible'] and c['enabled'],c
 point_click(g,title,c['x']+c['w']//2,c['y']+int(c['h']*(.25 if direction>0 else .75)))
def close(g,title,cs,finish):
 if finish=='Close':
  win=g.find_windows('^'+title+'$')[0][0];g.raise_window(win);drv.sh('xdotool','key','--window',str(win),'alt+F4');time.sleep(1)
 else:g.close_controls(title,cs,text=finish)
def public_row(stem,row):write_new(DATA/(stem+'.json'),row);print(stem,json.dumps(row.get('summary',{})),flush=True)

def army_menu(g,item):
 """Actual Unit map > Army menu, usable with a carrier selected.
 TPremierForm DFM: Army is first submenu; items supply0,mercs1,transfer2,
 split3,join4,change5,disband6. Keyboard navigation, no command injection.
 """
 g.reset_ui();g.click(270,36,pause=.3)
 for key in ['Down','Right']+['Down']*item+['Return']:g.key(key,pause=.2)
 time.sleep(.6)

def list_rows(title):
 out=[]
 for line in drv.sh(drv.WINE,str(WORK/'lists85.exe'),title).splitlines():
  p=line.split('\t')
  if p[0]=='LIST':out.append(dict(x=int(p[1]),y=int(p[2]),count=int(p[3]),selected=int(p[4]),cls=p[5],rows=[]))
  else:out[-1]['rows'].append(bytes.fromhex(p[2]).decode('latin1'))
 return out
