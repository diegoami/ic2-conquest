"""Approved #171: one End turn in an isolated original runtime per new label.

Every save/output is preserved. Unexpected human battles stop with diagnostics.
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
p=argparse.ArgumentParser();p.add_argument('case');p.add_argument('label');p.add_argument('--plain',action='store_true');a=p.parse_args()
assert all(x.replace('-','').isalnum() for x in (a.case,a.label))
BASE=ROOT/'artifacts/run-exp-strategic-fidelity';OUT=BASE/'original'/a.label
OUT.mkdir(parents=True,exist_ok=False)
DATA=ROOT/'runs/experiments/data/run-exp-strategic-fidelity'/a.label;DATA.mkdir(exist_ok=False)
WORK=OUT/'runtime';SOURCE=Path('/home/diego/ic2-work')
shutil.copytree(SOURCE/'prefix',WORK/'prefix',symlinks=True,
    ignore=lambda d,n:['IC2'] if Path(d)==SOURCE/'prefix/drive_c' else [])
GAME=WORK/'prefix/drive_c/IC2';GAME.mkdir()
for f in (SOURCE/'prefix/drive_c/IC2').iterdir():
    if f.is_file() and f.suffix.lower() in {'.dat','.dll','.hlp','.cnt','.ini','.bmp'}:shutil.copy2(f,GAME/f.name)
    if f.name=='WAVS':shutil.copytree(f,GAME/f.name)
for f in SOURCE.iterdir():
    if f.name in {'win_controls.exe','win_slider.exe','toolbar.json','army_toolbar.json','battle_toolbar.json'}:shutil.copy2(f,WORK/f.name)
binary=(SOURCE/'build/Imperial Conquest 2 fast rollingsave seed.exe').read_bytes()
if not a.plain:binary,sites,caves=O.build(binary)
exe='Imperial Conquest 2 strategic171.exe'
with (GAME/exe).open('xb') as f:f.write(binary)
with (GAME/'SEED.TXT').open('x') as f:f.write('1\n')
os.environ['IC2_WORK']=str(WORK);os.environ['DISPLAY_IC2']=':789'
sys.path.insert(0,str(ROOT))
from harness import driver as D,environment
from state import sav
environment.set_data_folder(DATA)
def write(folder,name,value):
    with (folder/name).open('x') as f:json.dump(value,f,indent=2)
def log(s):
    with (DATA/'driver.log').open('a') as f:f.write(str(s)+'\n')
class PrivateGame(D.Game):
    def ensure_xvfb(self):
        if subprocess.run(['xdpyinfo','-display',D.DISPLAY],capture_output=True).returncode==0:raise RuntimeError('Dedicated display already occupied')
        self.xvfb=subprocess.Popen(['Xvfb',D.DISPLAY,'-screen','0','2560x1440x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
        time.sleep(2)
    def start(self):
        self.ensure_xvfb();self.kill()
        subprocess.Popen(['setsid',D.WINE,self.exe],cwd=D.G,env=D.ENV,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self.wait(lambda:self.find_windows('^Imperial Conquest 2$'),60,'main window');time.sleep(3)
        pids=[]
        for path in Path('/proc').iterdir():
            if not path.name.isdigit():continue
            try:
                if not (path/'cmdline').read_bytes().startswith(b'Imperial Conquest'):continue
                env=(path/'environ').read_bytes().split(b'\0')
                if f'WINEPREFIX={D.PREFIX}'.encode() in env and f'DISPLAY={D.DISPLAY}'.encode() in env:pids.append(int(path.name))
            except (OSError,PermissionError):continue
        assert len(pids)==1,pids
        self.pid=pids[0]
g=PrivateGame(exe=exe,log=log);result=dict(case=a.case,label=a.label,plain=a.plain,complete=False)
def collect():
    if a.plain or (DATA/'records.json').exists():return
    records,raw,snapshots=O.read(g);write(DATA,'records.json',records)
    with (OUT/'records.bin').open('xb') as f:f.write(raw)
    snaps=OUT/'snapshots';snaps.mkdir()
    for i,snapshot in enumerate(snapshots):
        with (snaps/f'{i:03}.ram').open('xb') as f:f.write(snapshot)
    result.update(records=len(records),snapshots=len(snapshots))
    write(DATA,'snapshot-hashes.json',{f'{i:03}.ram':hashlib.sha256(s).hexdigest() for i,s in enumerate(snapshots)})
try:
    g.start();result['load_messages']=g.open(BASE/'inputs-v1'/(a.case+'.SAV'),strict=False)
    src=g.save_as('SF-'+a.label+'-before.SAV');shutil.copy2(src,OUT/src.name)
    before=sav.load(OUT/src.name);write(OUT,'before.json',before)
    result['before_turn']=before['turn'];cal=g.calendar();me=g.i16(D.CUR_NATION)
    result['rng_before_end']=struct.unpack('<I',g.mem(D.RAND_SEED,4))[0]
    g.tool('end_turn');started=time.monotonic();messages=[]
    while time.monotonic()-started<300:
        if g.in_battle():
            write(OUT,'unexpected-battle.json',g.battle_state());g.shot(OUT/'unexpected-battle.png')
            raise RuntimeError('Human tactical battle opened; no battle orders issued')
        if g.find_windows('^End turn \\?$'):
            cs=g.controls('End turn ?');g.click_control(g.control(cs,text='End turn'),pause=.6)
        messages+=g.dismiss_popups(strict=False)
        if g.i16(D.CUR_NATION)==me and g.calendar()!=cal:
            time.sleep(1)
            if g.i16(D.CUR_NATION)==me and not g.popups():break
        time.sleep(.2)
    else:raise RuntimeError('Original End turn did not complete')
    result['rng_after_end']=struct.unpack('<I',g.mem(D.RAND_SEED,4))[0]
    collect()
    src=g.save_as('SF-'+a.label+'-after.SAV');shutil.copy2(src,OUT/src.name)
    state=sav.load(OUT/src.name);write(OUT,'after.json',state)
    result.update(complete=True,after_turn=state['turn'],messages=messages,armies=len(state['armies']),fleets=len(state['fleets']))
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
    saves={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.SAV')}
    write(DATA,'save-hashes.json',saves)
print(json.dumps(result))
sys.exit(0 if result['complete'] else 1)
