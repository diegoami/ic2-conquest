#!/usr/bin/env python3
"""Bounded ORIGINAL UI research, authorized by conquest #206/Main #1456.

Never overwrite/delete saves or measurements. Unique --version per attempt.
No battle, End turn, memory writes, original patches or remake writes.
Private full states/hashes/screenshots stay in artifacts; public case scalars
are written immediately, exclusively and committed after each batch.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
ART = ROOT / 'artifacts/run-exp-manual-funding1456'
DATA = ROOT / 'runs/experiments/data/run-exp-manual-funding1456'
WORK = ART / 'work-v1'
os.environ.update(IC2_WORK=str(WORK), DISPLAY_IC2=':756', IC2_EXE='Imperial Conquest 2.exe')
from harness import driver as drv
from state import sav


def write_new(path, obj):
    with path.open('x') as f:
        json.dump(obj, f, indent=2); f.write('\n')


# Predictions fixed before execution, from 0044005C. All staged money edits
# use allowlisted fields only; no positions/map/owners/counter edits.
CASES = [
    dict(id=f'army-debt-{label}', kind='army', provider='city', treasury=t,
         purse=100, direction=1, expected=[t-100,200,50])
    for label,t in [('negative',-100),('zero',0),('low-positive',50)]
] + [
    dict(id='army-at-cap',kind='army',provider='city',treasury=-100,purse=1000,direction=1,expected=[-100,1000,50]),
    dict(id='army-over-cap',kind='army',provider='city',treasury=-100,purse=1100,direction=1,expected=[0,1000,50]),
    dict(id='army-reverse',kind='army',provider='city',treasury=-100,purse=100,direction=-1,expected=[0,0,50]),
    dict(id='army-reverse-limited',kind='army',provider='city',treasury=-100,purse=50,direction=-1,expected=[-50,0,50]),
    dict(id='army-fleet-limited',kind='army',provider='fleet',treasury=-100,purse=100,direction=1,expected=[-100,150,0]),
    dict(id='army-fleet-empty',kind='army',provider='fleet',treasury=-100,purse=100,fleet_money=0,direction=1,expected=[-100,100,0]),
    dict(id='army-fleet-over-cap',kind='army',provider='fleet',treasury=-100,purse=1100,direction=1,expected=[-100,1000,150]),
    dict(id='army-fleet-reverse',kind='army',provider='fleet',treasury=-100,purse=100,direction=-1,expected=[-100,0,150]),
    dict(id='army-fleet-reverse-cap',kind='army',provider='fleet',treasury=-100,purse=100,fleet_money=950,direction=-1,expected=[-100,50,1000]),
] + [
    dict(id=f'fleet-debt-{label}',kind='fleet',provider='city',treasury=t,purse=100,direction=1,expected=[t-100,200,50])
    for label,t in [('negative',-100),('zero',0),('low-positive',50)]
] + [
    dict(id='fleet-at-cap',kind='fleet',provider='city',treasury=-100,purse=1000,direction=1,expected=[-100,1000,50]),
    dict(id='fleet-over-cap',kind='fleet',provider='city',treasury=-100,purse=1100,direction=1,expected=[0,1000,50]),
    dict(id='fleet-reverse',kind='fleet',provider='city',treasury=-100,purse=100,direction=-1,expected=[0,0,50]),
    # Original fleet-target branch always transfers with NATIONAL treasury,
    # even if a neighbouring fleet is selected as its supply provider.
    dict(id='fleet-fleet-provider',kind='fleet',provider='fleet',treasury=-100,purse=100,direction=1,expected=[-200,200,50]),
]


def offsets(b):
    na=sav.i16(b,sav.ARMY_OFF)
    f0=sav.ARMY_OFF+2+na*sav.ARMY_LEN+2
    nf=sav.i16(b,f0-2)
    return sav.ARMY_OFF+2,f0,f0+nf*sav.FLEET_LEN


def stage(case,path):
    b=bytearray((ROOT/'saves/fleet-split-antium-0734.SAV').read_bytes())
    old=bytes(b);a,f,n=offsets(b);allowed=set()
    edits=[(n+0x438,'<i',case['treasury']),
           (a+12 if case['kind']=='army' else f+2*26+16,'<h',case['purse']),
           (f+(2 if case['kind']=='army' else 5)*26+16,'<h',case.get('fleet_money',50))]
    for off,fmt,value in edits:
        struct.pack_into(fmt,b,off,value);allowed.update(range(off,off+struct.calcsize(fmt)))
    assert all(x in allowed for x,(u,v) in enumerate(zip(old,b)) if u!=v)
    with path.open('xb') as out:out.write(b)


def balances(path,case):
    s=sav.load(path)
    return [s['nations'][0]['treasury'],
            s['armies'][0]['money'] if case['kind']=='army' else s['fleets'][2]['money'],
            s['fleets'][2 if case['kind']=='army' else 5]['money']]


def inspect(title):
    text=drv.sh(drv.WINE,str(WORK/'funding-controls.exe'),title)
    out=[]
    for line in text.splitlines():
        parts=line.split('\t');cls,txt,x,y,w,h,en,vis=parts[:8]
        out.append(dict(cls=cls,text=txt,x=int(x),y=int(y),w=int(w),h=int(h),enabled=bool(int(en)),visible=bool(int(vis))))
        if len(parts)==13:out[-1].update(zip(['count','item_h','top','cx','cy'],map(int,parts[8:])))
    return out


class Game(drv.Game):
    def record_environment(self):
        # This handoff requires original identities/hashes private. The shared
        # recorder automatically mirrors hashes into tracked runner data, so
        # retain its full fingerprint privately and publish platform only.
        from harness import environment
        self.environment=environment.fingerprint(drv.PREFIX,self.exe,drv.DISPLAY,drv.G)
        write_new(self.private_dir/'environment.json',self.environment)

    def ensure_xvfb(self):
        if not Path('/tmp/.X11-unix/X756').exists():
            self.display_process=subprocess.Popen(['Xvfb',':756','-screen','0','1280x1024x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            time.sleep(2)

    def start(self):
        self.ensure_xvfb()
        self.process=subprocess.Popen([drv.WINE,self.exe],cwd=drv.G,env=drv.ENV,stdout=self.private_log,stderr=self.private_log)
        self.wait(lambda:self.find_windows('^Imperial Conquest 2$'),40,'original main window')
        time.sleep(3)
        for p in Path('/proc').glob('[0-9]*'):
            try:
                env=(p/'environ').read_bytes()
                if b'WINEPREFIX='+str(drv.PREFIX).encode()+b'\0' not in env:continue
                if not (p/'cmdline').read_bytes().startswith(b'Imperial Conquest'):continue
                self.pid=int(p.name); self.i16(drv.CUR_NATION); return
            except (OSError,ValueError):continue
        raise RuntimeError('Own original process not found')


def execute(case,g,private,version):
    stem=f'{version}_{case["id"]}'
    staged=private/(stem+'_staged.SAV');stage(case,staged)
    g.open(staged)
    before=g.save_as(stem+'_before.SAV')
    shutil.copy2(before,private/before.name)
    observed_before=balances(before,case)
    assert observed_before==[case['treasury'],case['purse'],case.get('fleet_money',50)]
    title='Supply army' if case['kind']=='army' else 'Supply fleet'
    if case['kind']=='army':g.army_tool(0,'supply',title)
    else:
        g.select_fleet(2)
        g.click(g.fleet_x['supply'],drv.ARMY_TOOLBAR_Y,pause=1)
        g.wait(lambda:g.find_windows('^Supply fleet$'),8,title)
    time.sleep(1)
    controls=inspect(title)
    lists=[c for c in controls if c['cls']=='TListBox']
    assert len(lists)==1
    if case['provider']=='fleet':
        # Last provider is the last own adjacent fleet, after city rows.
        # Read list count with the read-only inspection helper (below).
        count=lists[0]['count']
        g.click_list_row(lists[0],count-1,pause=0.7)
        controls=inspect(title)
    # Original form instance pointer + provider/target fields, READ ONLY.
    form=struct.unpack('<I',g.mem(0x45e71c,4))[0]
    form_fields=dict(zip(['city','provider_fleet','target_army','target_fleet'],struct.unpack('<4h',g.mem(form+0x288,8))))
    if case['provider']=='city':assert form_fields['city']>=0 and form_fields['provider_fleet']<0
    else:assert form_fields['city']<0 and form_fields['provider_fleet']==(2 if case['kind']=='army' else 5)
    ups=sorted([c for c in controls if c['cls']=='TUpDown' and c['visible']],key=lambda c:(c['y'],c['x']))
    assert len(ups)==4,ups
    money=ups[-1]
    g.shot(private/(stem+'_dialog-before.png'))
    assert money['visible'] and money['enabled']
    # Targeted HWND click through an actually visible/enabled control, with
    # hover and focus first. No handler invocation, no command injection.
    win=g.find_windows('^'+title+'$')[0][0]
    g.raise_window(win)
    drv.sh('xdotool','mousemove',str(money['x']+money['w']//2),str(money['y']+int(money['h']*(0.25 if case['direction']>0 else 0.75))))
    time.sleep(0.3)
    drv.sh('xdotool','click','--window',str(win),'1');time.sleep(0.8)
    g.shot(private/(stem+'_dialog-after.png'))
    g.close_controls(title,controls)
    after=g.save_as(stem+'_after.SAV');shutil.copy2(after,private/after.name)
    observed_after=balances(after,case)
    a=sav.load(before);b=sav.load(after)
    assert a['turn']==b['turn']==734 and not a['battle_flag'] and not b['battle_flag']
    row=dict(case,requested_step=case['direction']*100,before=observed_before,after=observed_after,
             prediction_match=observed_after==case['expected'],control_enabled=money['enabled'],
             control_visible=money['visible'],form_fields=form_fields,turn=734,
             before_save=before.name,after_save=after.name,total_conserved=sum(observed_before)==sum(observed_after))
    write_new(private/(stem+'_controls.json'),controls)
    write_new(DATA/(stem+'.json'),row)
    print(json.dumps(row),flush=True)
    assert row['prediction_match'] and row['total_conserved'],row


def main():
    p=argparse.ArgumentParser();p.add_argument('--version',required=True);p.add_argument('--cases',nargs='*');args=p.parse_args()
    DATA.mkdir(parents=True,exist_ok=True)
    private=ART/('private-'+args.version);private.mkdir()
    selected=[c for c in CASES if not args.cases or c['id'] in args.cases]
    write_new(DATA/(args.version+'_plan.json'),selected)
    g=Game(log=lambda x:None)
    g.private_dir=private
    with (private/'wine.log').open('x') as log:
        g.private_log=log
        try:
            g.start()
            for case in selected:execute(case,g,private,args.version)
        except BaseException as e:
            write_new(DATA/(args.version+'_failure.json'),dict(type=type(e).__name__,message=str(e)))
            raise
        finally:
            subprocess.run(['/usr/lib/wine/wineserver','-k'],env=drv.ENV,capture_output=True)
            if hasattr(g,'display_process'):g.display_process.terminate()
    hashes={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in private.iterdir() if x.is_file()}
    write_new(private/'hashes.json',hashes)


if __name__=='__main__':main()
