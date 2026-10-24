"""One private original End-turn control. Never overwrite/delete a save/log.

Requires #1388 owner authorization; no battle orders or desktop Computer Use.
"""
import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import time
import traceback
from pathlib import Path
import observer as O

ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser()
p.add_argument('label');p.add_argument('--observer',action='store_true')
p.add_argument('--seed',type=int,default=1)
a=p.parse_args()
assert a.label.replace('-','').isalnum()
out=ROOT/'artifacts/run-exp-seleucid1388/private'/a.label
out.mkdir(parents=True,exist_ok=False)
work=out/'runtime';work.mkdir()
source=Path('/home/diego/ic2-work')
shutil.copytree(source/'prefix',work/'prefix',symlinks=True,
    ignore=lambda d,n:['IC2'] if Path(d)==source/'prefix/drive_c' else [])
game=work/'prefix/drive_c/IC2';game.mkdir()
for path in (source/'prefix/drive_c/IC2').iterdir():
    if path.is_file() and path.suffix.lower() in {'.dat','.dll','.hlp','.cnt','.ini','.bmp'}: shutil.copy2(path,game/path.name)
    if path.name=='WAVS':shutil.copytree(path,game/path.name)
for path in source.iterdir():
    if path.name in {'win_controls.exe','win_slider.exe','toolbar.json','army_toolbar.json','battle_toolbar.json'}:shutil.copy2(path,work/path.name)
b=(source/'build/Imperial Conquest 2 fast rollingsave seed.exe').read_bytes()
sites=O.configure(b)
if a.observer:b,sites,caves=O.build(b)
exe='Imperial Conquest 2 strategic1388.exe'
with (game/exe).open('xb') as f:f.write(b)
with (game/'SEED.TXT').open('x') as f:f.write(str(a.seed)+'\n')
os.environ['IC2_WORK']=str(work)
os.environ['DISPLAY_IC2']=':788'
sys.path.insert(0,str(ROOT))
from harness import driver as D,environment
from state import sav
environment.set_data_folder(out)

def write(name,value):
    with (out/name).open('x') as f:json.dump(value,f,indent=2)
def log(s):
    with (out/'driver.log').open('a') as f:f.write(str(s)+'\n')
class PrivateGame(D.Game):
    def ensure_xvfb(self):
        if subprocess.run(['xdpyinfo','-display',D.DISPLAY],capture_output=True).returncode==0:raise RuntimeError('Dedicated display in use')
        self.xvfb=subprocess.Popen(['Xvfb',D.DISPLAY,'-screen','0','2560x1440x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
        time.sleep(2)
    def show(self,x,y):
        w=self.find_windows('^Unit map$')[0]
        D.VIEW_COLS=max(1,(w[4]-20)//32);D.VIEW_ROWS=max(1,(w[5]-70)//32)
        D.UNIT_PAINT=(335+w[2]-333,96+w[3]-75)
        return super().show(x,y)

g=PrivateGame(exe=exe,log=log);result={'complete':False,'observer':a.observer,'seed_input':a.seed}
try:
    g.start()
    g.open(ROOT/'artifacts/run-exp-battle1355/private-v1/inputs/classical-mediterranean-saveyy.sav',strict=False)
    result['rng_before_end']=struct.unpack('<I',g.mem(D.RAND_SEED,4))[0]
    for label in ['before']:
        src=g.save_as(f'S1388-{a.label}-{label}.SAV');shutil.copy2(src,out/src.name)
    cal=g.calendar();me=g.i16(D.CUR_NATION)
    g.tool('end_turn')
    start=time.monotonic();messages=[]
    while time.monotonic()-start<240:
        if g.in_battle():raise RuntimeError('Unexpected battle: stop without battle orders')
        if g.find_windows('^End turn \\?$'):
            cs=g.controls('End turn ?');g.click_control(g.control(cs,text='End turn'),pause=.6)
        messages+=g.dismiss_popups(strict=False)
        if g.i16(D.CUR_NATION)==me and g.calendar()!=cal:
            time.sleep(1)
            if g.i16(D.CUR_NATION)==me and not g.popups():break
        time.sleep(.2)
    else:raise RuntimeError('End turn did not complete')
    result['rng_after_end']=struct.unpack('<I',g.mem(D.RAND_SEED,4))[0]
    if a.observer:
        records,raw=O.read(g);write('records.json',records)
        with (out/'records.bin').open('xb') as f:f.write(raw)
        assert struct.unpack('<I',g.mem(O.CTL+12,4))[0]==1
        with (out/'defender-prewalk-ram.bin').open('xb') as f:f.write(g.mem(O.SNAP,O.SNAP_SIZE))
    src=g.save_as(f'S1388-{a.label}-after.SAV');shutil.copy2(src,out/src.name)
    state=sav.load(out/src.name);write('after.json',state)
    result.update(complete=True,turn=state['turn'],messages=messages,
        defender=[dict(id=x['id'],x=x['x'],y=x['y'],troops=x['troops'],moves=x['moves']) for x in state['armies'] if x['owner']==2 and x['troops']==78857])
except Exception:
    result['error']=traceback.format_exc()
    try:g.shot(out/'failure.png')
    except Exception:pass
finally:
    g.kill()
    if hasattr(g,'xvfb'):g.xvfb.terminate();g.xvfb.wait(timeout=10)
    write('result.json',result)
print(json.dumps({k:v for k,v in result.items() if k not in {'rng_before_end','rng_after_end','messages'}}))
sys.exit(0 if result['complete'] else 1)
