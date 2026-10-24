"""Approved176/177/174: diplomacy/economy/fleet phase observer/plain controls.

One End turn, no battle orders. Unique output/prefix per label; never overwrite.
"""
import argparse,hashlib,json,os,shutil,struct,subprocess,sys,time,traceback
from pathlib import Path
import phase_observer as O
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('--plain',action='store_true');a=p.parse_args();assert a.label.replace('-','').isalnum()
BASE=ROOT/'artifacts/run-exp-strategic-tracks';OUT=BASE/'live'/a.label;OUT.mkdir(parents=True,exist_ok=False)
DATA=ROOT/'runs/experiments/data/run-exp-strategic-tracks'/a.label;DATA.mkdir(exist_ok=False)
SOURCE=Path('/home/diego/ic2-work');WORK=OUT/'runtime'
shutil.copytree(SOURCE/'prefix',WORK/'prefix',symlinks=True,ignore=lambda d,n:['IC2'] if Path(d)==SOURCE/'prefix/drive_c' else [])
GAME=WORK/'prefix/drive_c/IC2';GAME.mkdir()
for f in (SOURCE/'prefix/drive_c/IC2').iterdir():
 if f.is_file() and f.suffix.lower() in {'.dat','.dll','.hlp','.cnt','.ini','.bmp'}:shutil.copy2(f,GAME/f.name)
 if f.name=='WAVS':shutil.copytree(f,GAME/f.name)
for f in SOURCE.iterdir():
 if f.name in {'win_controls.exe','win_slider.exe','toolbar.json','army_toolbar.json','battle_toolbar.json'}:shutil.copy2(f,WORK/f.name)
binary=(SOURCE/'build/Imperial Conquest 2 fast rollingsave seed.exe').read_bytes()
if not a.plain:binary,cave=O.build(binary)
exe='Imperial Conquest 2 strategic tracks.exe'
with (GAME/exe).open('xb') as f:f.write(binary)
with (GAME/'SEED.TXT').open('x') as f:f.write('1\n')
os.environ['IC2_WORK']=str(WORK);os.environ['DISPLAY_IC2']=':790'
sys.path.insert(0,str(ROOT));from harness import driver as D,environment;from state import sav
environment.set_data_folder(DATA)
def write(folder,name,value):
 with (folder/name).open('x') as f:json.dump(value,f,indent=2)
def log(s):
 with (DATA/'driver.log').open('a') as f:f.write(str(s)+'\n')
class PrivateGame(D.Game):
 def ensure_xvfb(self):
  if subprocess.run(['xdpyinfo','-display',D.DISPLAY],capture_output=True).returncode==0:raise RuntimeError('Dedicated display occupied')
  self.xvfb=subprocess.Popen(['Xvfb',D.DISPLAY,'-screen','0','2560x1440x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True);time.sleep(2)
 def start(self):
  self.ensure_xvfb();self.kill();subprocess.Popen(['setsid',D.WINE,self.exe],cwd=D.G,env=D.ENV,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  self.wait(lambda:self.find_windows('^Imperial Conquest 2$'),60,'main window');time.sleep(3);pids=[]
  for path in Path('/proc').iterdir():
   if not path.name.isdigit():continue
   try:
    if not (path/'cmdline').read_bytes().startswith(b'Imperial Conquest'):continue
    env=(path/'environ').read_bytes().split(b'\0')
    if f'WINEPREFIX={D.PREFIX}'.encode() in env and f'DISPLAY={D.DISPLAY}'.encode() in env:pids.append(int(path.name))
   except (OSError,PermissionError):continue
  assert len(pids)==1,pids
  self.pid=pids[0]
g=PrivateGame(exe=exe,log=log);result=dict(label=a.label,plain=a.plain,complete=False)
def collect():
 if a.plain or (DATA/'phase-records.json').exists():return
 records,raw,snaps=O.read(g);write(DATA,'phase-records.json',records)
 with (OUT/'phase-records.bin').open('xb') as f:f.write(raw)
 folder=OUT/'snapshots';folder.mkdir()
 for i,b in enumerate(snaps):
  with (folder/f'{i:03}.ram').open('xb') as f:f.write(b)
 result['phase_records']=len(records)
try:
 g.start();g.open(ROOT/'artifacts/run-exp-fleet-actions174/live-input-v1/ROM720.SAV',strict=False)
 result['records_before_end']=0 if a.plain else struct.unpack('<I',g.mem(O.CTL,4))[0]
 for part in ['before']:
  src=g.save_as('ST176-'+a.label+'-'+part+'.SAV');shutil.copy2(src,OUT/src.name)
  write(OUT,part+'.json',sav.load(OUT/src.name))
 cal=g.calendar();me=g.i16(D.CUR_NATION);g.tool('end_turn');start=time.monotonic();messages=[]
 while time.monotonic()-start<300:
  if g.in_battle():raise RuntimeError('Human tactical battle opened; no battle orders issued')
  if g.find_windows('^End turn \\?$'):
   cs=g.controls('End turn ?');g.click_control(g.control(cs,text='End turn'),pause=.6)
  messages+=g.dismiss_popups(strict=False)
  if g.i16(D.CUR_NATION)==me and g.calendar()!=cal:
   time.sleep(1)
   if g.i16(D.CUR_NATION)==me and not g.popups():break
  time.sleep(.2)
 else:raise RuntimeError('End turn did not complete')
 collect();src=g.save_as('ST176-'+a.label+'-after.SAV');shutil.copy2(src,OUT/src.name);after=sav.load(OUT/src.name);write(OUT,'after.json',after)
 result.update(complete=True,turn=after['turn'],messages=messages)
except Exception:
 result['error']=traceback.format_exc()
 try:collect()
 except Exception:result['collection_error']=traceback.format_exc()
 try:g.shot(OUT/'failure.png')
 except Exception:pass
finally:
 g.kill()
 if hasattr(g,'xvfb'):g.xvfb.terminate();g.xvfb.wait(timeout=10)
 write(DATA,'result.json',result)
 write(DATA,'save-hashes.json',{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in OUT.glob('*.SAV')})
print(json.dumps(result));sys.exit(0 if result['complete'] else 1)
