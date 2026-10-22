#!/usr/bin/env python3
"""Bounded original-game #31 sweep; imports the pinned existing research driver.

Requires explicit --bot, --work and --artifacts; never writes into the bot repo.
Every staged/loaded/post save is uniquely named and exclusively created.
Wine observations are not native confirmation. Never delete measured outputs.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import time

sys.dont_write_bytecode = True
P = argparse.ArgumentParser(description=__doc__)
P.add_argument('--bot', type=Path, required=True)
P.add_argument('--work', type=Path, required=True)
P.add_argument('--artifacts', type=Path, required=True)
P.add_argument('--display', default=':731')
P.add_argument('cases', nargs='+')
A = P.parse_args()
assert A.work.resolve() != Path.home() / 'ic2-work'
assert A.display not in (':99', ':453')
os.environ.update(IC2_WORK=str(A.work.resolve()), DISPLAY_IC2=A.display)
sys.path[:0] = [str(A.bot), str(A.bot / 'runs/experiments/battles')]
from harness import driver as drv
from harness import environment
from state import sav
import stage

DATA = Path(__file__).resolve().parents[3] / 'runs/experiments/data/run-exp-resupply31'
DATA.mkdir(parents=True, exist_ok=True)
A.artifacts.mkdir(parents=True, exist_ok=True)
STAMP = time.strftime('%Y%m%d-%H%M%S') + f'-{os.getpid()}'
LOG = DATA / f'wine-{STAMP}.jsonl'
LOG.touch(exist_ok=False)
SOURCE = A.bot / 'saves/fleet-port-antium-0734.SAV'
F = dict(zip(('x','y','dest_x','dest_y','owner','countdown','moves','supplies',
              'money','ships','condition','army','cell'), range(0,26,2)))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def log(event, **fields):
    with LOG.open('a') as out:
        out.write(json.dumps(dict(event=event, utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()), **fields))+'\n')
    if event not in ('driver','environment'):
        print(event, fields.get('case',''), fields.get('summary',''), flush=True)


def keep(name, content):
    p = A.artifacts / name
    with p.open('xb') as out:
        out.write(content)
    with (DATA / 'SAVES.sha256').open('a') as out:
        out.write(f'{sha(p)}  {p.name}\n')
    return p


def fleet_set(b, i, **fields):
    base = sav.ARMY_OFF+2+sav.i16(b,sav.ARMY_OFF)*sav.ARMY_LEN+2+i*sav.FLEET_LEN
    for k,v in fields.items():
        struct.pack_into('<h',b,base+F[k],v)


def prepare(subject, variant):
    b = bytearray(SOURCE.read_bytes())
    s = sav.parse(b)
    for n in range(16):
        b[stage._nation(b,n)+0x490] = int(n != 0)
        stage.set_relation(b,0,n,0)
    struct.pack_into('<2h',b,s['tail_off']+32,-1,-1)
    struct.pack_into('<2h',b,s['tail_off']+36,13,10)
    for k in range(40):
        struct.pack_into('<h',b,stage._nation(b,0)+0x2e8+8*k,0)
    merc_off=stage._nation(b,0)+16*sav.NATION_LEN
    for k in range(50):
        struct.pack_into('<h',b,merc_off+12*k+8,-1)
    # Restore all army/fleet covers; only the subject and its declared carrier remain.
    for a in s['armies']:
        if a['cell']>=0:
            struct.pack_into('<h',b,(a['x']*140+a['y'])*2,a['cell'])
        stage.set_army_field(b,a['id'],'owner',-1)
    for f in s['fleets']:
        if f['cell']>=0 and f['countdown']==-1:
            struct.pack_into('<h',b,(f['x']*140+f['y'])*2,f['cell'])
        fleet_set(b,f['id'],owner=-1)
    # Explicitly move every nonprovider city outside support radius. This also
    # removes stock-free own-city fleet grants as a possible confound.
    for c in range(334):
        stage.set_city(b,c,{'supplies':0})
        o=sav.CITY_OFF+c*sav.CITY_LEN
        struct.pack_into('<2h',b,o+14,200+(c%20),90+(c//20))
    cap=720 if subject=='fleet' else 300
    money=500; supply=50; stock=100; owner=1; relation=0
    distance=3; providers=[]; carrier=(102,49)
    if variant=='own': owner=0
    if variant=='trade': relation=1
    if variant=='alliance': relation=2
    if variant=='war': relation=3
    if variant=='negative_relation': relation=-1
    if variant=='relation4': relation=4
    if variant=='empty': stock=0
    if variant.startswith('purse'): money=int(variant[5:])
    if variant=='tiny': stock=4
    if variant=='exact': supply=cap
    if variant=='above': supply=cap+10
    if variant=='inside': distance=3 if subject=='fleet' else 4
    if variant=='outside': distance=4 if subject=='fleet' else 5
    if variant=='carrier_far': carrier=(150,90)
    if variant.startswith('own_first'):
        money=0 if variant.endswith('zero') else 1
        providers.append(dict(id=88,owner=0,stock=0 if subject=='fleet' else 1))
    if variant=='foreign_first_zero':
        money=0
        providers.append(dict(id=90,owner=0,stock=0 if subject=='fleet' else 1))
    if variant=='two_foreign':
        money=25
        providers.append(dict(id=88,owner=2,stock=100))
    providers.append(dict(id=89,owner=owner,stock=stock))
    stage.set_relation(b,0,1,relation)
    for n in range(16):
        struct.pack_into('<i',b,stage._nation(b,n)+0x438,1000)
    for p in providers:
        stage.set_city(b,p['id'],{'owner':p['owner'],'supplies':p['stock']})
        struct.pack_into('<2h',b,sav.CITY_OFF+p['id']*sav.CITY_LEN+14,102,49-distance)
    if subject=='fleet':
        fleet_set(b,2,x=102,y=49,owner=0,countdown=-1,dest_x=-1,dest_y=-1,
                  moves=0,supplies=supply,money=money,ships=90,condition=94,army=-1,cell=0)
        struct.pack_into('<h',b,(102*140+49)*2,302)
    else:
        stage.set_units(b,0,[('li',30000,6)])
        for k,v in dict(owner=0,moves=0,supplies=supply,money=money,morale=90).items():
            stage.set_army_field(b,0,k,v)
        struct.pack_into('<2h',b,stage._army(b,0),102,49)
        struct.pack_into('<h',b,stage._army(b,0)+8,-1 if subject=='aboard' else 2)
        struct.pack_into('<h',b,(102*140+49)*2,302 if subject=='aboard' else 200)
        if subject=='aboard':
            # Carrier belongs to a human, preventing its own resupply from consuming stock.
            # Deliberate record-based staging; no synchronization claim follows.
            fleet_set(b,2,x=carrier[0],y=carrier[1],owner=13,countdown=-1,
                      dest_x=-1,dest_y=-1,moves=0,supplies=720,money=100,
                      ships=90,condition=100,army=0,cell=0)
            struct.pack_into('<h',b,(carrier[0]*140+carrier[1])*2,302)
    assert len(b)==SOURCE.stat().st_size
    return b,dict(subject=subject,variant=variant,capacity=cap,providers=providers,
                  distance=distance,army_coordinates=[102,49],carrier_coordinates=list(carrier),
                  isolated_city_coordinates=True,recruit_queue_cleared=True,mercenaries_disabled=True,
                  other_units_removed=True,city_lists_and_overlays_not_rebuilt=True,
                  carrier_human_owned=subject=='aboard')


class PrivateGame(drv.Game):
    def ensure_xvfb(self):
        if subprocess.run(['xdpyinfo','-display',drv.DISPLAY],capture_output=True).returncode:
            subprocess.Popen(['Xvfb',drv.DISPLAY,'-screen','0','1280x1024x24','-nolisten','tcp'],
                             start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            time.sleep(2)
        subprocess.run(['xdpyinfo','-display',drv.DISPLAY],capture_output=True,check=True)

    def start(self):
        self.ensure_xvfb(); self.kill()
        subprocess.Popen(['setsid',drv.WINE,self.exe],cwd=drv.G,env=drv.ENV,
                         stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self.wait(lambda:self.find_windows('^Imperial Conquest 2$'),60,'main window')
        time.sleep(3)
        pids=[]
        for p in Path('/proc').iterdir():
            if not p.name.isdigit(): continue
            try:
                if not (p/'cmdline').read_bytes().startswith(b'Imperial Conquest'): continue
                env=(p/'environ').read_bytes().split(b'\0')
                if f'WINEPREFIX={drv.PREFIX}'.encode() in env and f'DISPLAY={drv.DISPLAY}'.encode() in env:
                    pids.append(int(p.name))
            except (OSError,PermissionError): pass
        assert len(pids)==1,pids
        self.pid=pids[0]


def fields(s, subject):
    rows=s['fleets'] if subject=='fleet' else s['armies']
    row=next(a for a in rows if a['owner']==0)
    return dict(unit={k:row[k] for k in ('x','y','owner','moves','supplies','money')},
                condition=row.get('condition'),
                providers=[s['cities'][i] for i in (88,89,90)],
                treasuries=[n['treasury'] for n in s['nations']],
                turn=s['turn'],current=s['current_nation'])


environment.add_sink(lambda r:log('environment',record=r),key='research31')
log('provenance',runner_sha256=sha(__file__),source_sha256=sha(SOURCE),bot_head=subprocess.check_output(
    ['git','-C',str(A.bot),'rev-parse','HEAD'],text=True).strip(),
    driver_sha256=sha(A.bot/'harness/driver.py'),stage_sha256=sha(A.bot/'runs/experiments/battles/stage.py'),
    exe_sha256=sha(drv.G/drv.EXE),work=str(A.work),display=A.display)
assert sha(drv.G/drv.EXE)=='354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f'
for index,case in enumerate(A.cases):
    subject,variant=case.split(':')
    b,edits=prepare(subject,variant)
    src=keep(f'{case.replace(":","-")}-{STAMP}-input.SAV',b)
    log('staged',case=case,input=src.name,edits=edits)
    g=PrivateGame(log=lambda message:log('driver',case=case,message=message))
    try:
        g.load(src,seed=12345)
        loaded=keep(f'{case.replace(":","-")}-{STAMP}-loaded.SAV',
                    g.save_as(f'r31_{os.getpid()}_{index}_loaded.SAV').read_bytes())
        before=sav.parse(loaded.read_bytes())
        log('before',case=case,loaded=loaded.name,fields=fields(before,subject))
        assert before['current_nation']==13
        staged=sav.parse(b)
        assert fields(staged,subject)==fields(before,subject), 'loaded support fields differ from staged input'
        for key in ('cities','armies','fleets','nations'):
            assert staged[key]==before[key], 'load changed '+key
        auto,texts=g.end_turn(timeout=180,reclick=False)
        autosave=keep(f'{case.replace(":","-")}-{STAMP}-{auto}',(drv.G/auto).read_bytes())
        post=keep(f'{case.replace(":","-")}-{STAMP}-post.SAV',
                  g.save_as(f'r31_{os.getpid()}_{index}_post.SAV').read_bytes())
        after=sav.parse(post.read_bytes())
        measured=fields(after,subject)
        log('after',case=case,post=post.name,autosave=autosave.name,fields=measured,texts=texts,
            summary=dict(supply=measured['unit']['supplies'],purse=measured['unit']['money'],
                         condition=measured['condition'],treasury=measured['treasuries'][:3]))
        assert after['current_nation']==11 and after['turn']==before['turn']==734
    except BaseException as exc:
        log('failure',case=case,exception=repr(exc))
        raise
    finally:
        g.kill()
