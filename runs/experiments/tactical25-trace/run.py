"""Fresh original mix-rg trace; unique outputs, no fixture writes or save deletion."""
import argparse,csv,hashlib,io,json,os,shutil,struct,subprocess,sys,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--exe',required=True);a=p.parse_args()
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'patches'))
if not os.environ.get('IC2_WORK','').startswith('/tmp/ic2-tactical25-trace-') or os.environ.get('DISPLAY_IC2')!=':719':raise SystemExit('Private work/display required')
from harness import driver as D,environment
from state import hook_log as L,sav
# Same enlarged saved Unit-map layout as the immutable B11 runner (common.py:33).
D.VIEW_COLS,D.VIEW_ROWS=29,27
import battle_hook as H
DATA=ROOT/'runs/experiments/data/run-exp-tactical25-trace';ART=ROOT/'artifacts/run-exp-tactical25-trace';STAMP=time.strftime('%Y%m%d-%H%M%S',time.gmtime())+'-'+str(os.getpid());logpath=DATA/('run-'+STAMP+'.jsonl');logpath.touch(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def log(event,**kw):
 rec=dict(event=event,utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**kw)
 with logpath.open('a') as f:f.write(json.dumps(rec,default=str)+'\n');f.flush()
 print(event,flush=True)
def keep(p):
 dst=ART/(STAMP+'-'+p.name)
 with dst.open('xb') as f:f.write(p.read_bytes())
 with (DATA/'SAVES.sha256').open('a') as f:f.write(sha(dst)+'  '+dst.name+'\n')
 return dict(name=dst.name,sha256=sha(dst),bytes=dst.stat().st_size)
def pids():
 out=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   if (p/'cmdline').read_bytes().startswith(b'Imperial Conquest') and ('WINEPREFIX='+str(D.PREFIX)).encode() in (p/'environ').read_bytes().split(b'\0'):out.append(int(p.name))
  except (OSError,PermissionError):pass
 return out
class PrivateGame(D.Game):
 def ensure_xvfb(self):
  if subprocess.run(['xdpyinfo','-display',D.DISPLAY],capture_output=True).returncode==0:return
  self.xvfb=subprocess.Popen(['Xvfb',D.DISPLAY,'-screen','0','1280x1024x24','-nolisten','tcp'],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(2)
  subprocess.run(['xdpyinfo','-display',D.DISPLAY],capture_output=True,check=True)
 def start(self):
  self.ensure_xvfb();self.kill()
  subprocess.Popen(['setsid',D.WINE,self.exe],cwd=D.G,env=D.ENV,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  self.wait(lambda:self.find_windows('^Imperial Conquest 2$'),60,'main window');time.sleep(3)
  mine=pids()
  if len(mine)!=1:raise D.DriverError('Expected one private game process, got '+str(mine))
  self.pid=mine[0]
environment.add_sink(lambda r:log('environment',record=r),key='tactical25-trace')
g=PrivateGame(exe=a.exe,log=lambda line:log('driver',message=line));kept=False
try:
 assert not list(D.G.glob('BATTLE*.SAV')),'Fresh game folder required; never overwrite boundary saves'
 log('input',exe=keep(D.G/a.exe),start=keep(D.G/'MIX-RG_start.SAV'),turn=sav.load(D.G/'MIX-RG_start.SAV')['turn'],work=str(D.WORK),display=D.DISPLAY)
 g.start();log('started',pid=g.pid);opened=g.open(D.G/'MIX-RG_start.SAV');log('loaded',dialogs=opened,armies=[g.army_state(i) for i in [0,10]])
 a0=g.army_state(0);a10=g.army_state(10);assert (a0['x'],a0['y'],a10['x'],a10['y'])==(86,28,85,28)
 g.select_army(0,a0['x'],a0['y']);g.click_tile(a10['x'],a10['y'],pause=0.0)
 g.wait(lambda:g.in_battle() and g.find_windows(' v '),45,'battle opens');log('battle_open',header=g.battle_state(),seed=int.from_bytes(g.mem(D.RAND_SEED,4),'little'))
 result=g.play_battle(on_dialog='no');log('battle_finished',result=result)
 ctl,recs=L.read_process(g.mem)
 cols=('seq','kind','site','eax','edx','ecx','seed_before','seed_after','result','counter','side','flag','ebp');path=DATA/('hook-'+STAMP+'.csv')
 with path.open('x',newline='') as f:
  w=csv.writer(f);w.writerow(cols)
  for r in recs:w.writerow([hex(r[k]) if k in ['site','ebp'] else r[k] for k in cols])
 log('hook',control=ctl,records=len(recs),chain_breaks=L.chain_check(recs),result_misses=L.result_check(recs),file=path.name)
 rawpath=ART/(STAMP+'-hookbuf.bin')
 with rawpath.open('xb') as f:f.write(g.mem(H.BUF,len(recs)*H.REC))
 with (DATA/'SAVES.sha256').open('a') as f:f.write(sha(rawpath)+'  '+rawpath.name+'\n')
 log('saves',files=[keep(p) for p in sorted(D.G.glob('BATTLE*.SAV'))]);kept=True
except BaseException as e:
 log('failure',error=repr(e),windows=g.find_windows() if g.pid else [])
 raise
finally:
 if not kept:log('partial_saves',files=[keep(p) for p in sorted(D.G.glob('BATTLE*.SAV'))])
 g.kill()
 if hasattr(g,'xvfb'):g.xvfb.terminate()
 log('end')
