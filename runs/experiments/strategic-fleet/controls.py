"""Synthetic fleet-phase instruction controls; no original/native game launched.

Execute original RNG and automatic prepass; stop before first actual movement.
All snapshots and SAVs are diagnostic containers, never original Save As.
"""
import hashlib,json,struct,sys
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EDX,UC_X86_REG_ESP,UC_X86_REG_EIP
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));from state import sav
BASE=ROOT/'artifacts/run-exp-strategic-fleet';OUT=BASE/'controls-v1';OUT.mkdir(parents=True,exist_ok=False)
DATA=ROOT/'runs/experiments/data/run-exp-strategic-fleet'
old=ROOT/'artifacts/run-exp-strategic-fidelity';RAM_BASE=0x45e000
raw=(old/'original/N-rome-hook-v1/snapshots/000.ram').read_bytes()
template=next((old/'original/N-rome-hook-v1').glob('*-before.SAV')).read_bytes();parsed=sav.parse(template)
def read(ram,address,n):return ram[address-RAM_BASE:address-RAM_BASE+n]
def short(ram,address):return struct.unpack('<h',read(ram,address,2))[0]
def cell(ram,x,y):return short(ram,0x45e870+2*(x*140+y))
def put(ram,address,value):struct.pack_into('<h',ram,address-RAM_BASE,value)
actor=(49,62)
def line(a,b):
    x,y=a;dx=abs(b[0]-x);sx=1 if x<b[0] else -1;dy=-abs(b[1]-y);sy=1 if y<b[1] else -1;e=dx+dy;p=[a]
    while (x,y)!=b:
        v=2*e
        if v>=dy:e+=dy;x+=sx
        if v<=dx:e+=dx;y+=sy
        p.append((x,y))
    return p
def sea_goal(distance):
    options=[]
    for x in range(actor[0]-distance,actor[0]+distance+1):
        for y in range(actor[1]-distance,actor[1]+distance+1):
            if 1<=x<319 and 1<=y<139 and max(abs(x-actor[0]),abs(y-actor[1]))==distance and cell(raw,x,y)<2:
                first=line(actor,(x,y))[1]
                if cell(raw,*first)<2:options.append((x,y))
    return min(options)
near=sea_goal(3);far=sea_goal(18);storedA=sea_goal(4);storedB=sea_goal(5)
specs=[dict(name=n,relation=r) for n,r in [('peace',0),('trade',1),('alliance',2),('war',3)]]
specs += [dict(name='war-stronger',relation=3,ships=100),dict(name='war-weaker',relation=3,ships=10),
    dict(name='target-construction',relation=3,countdown=5),dict(name='same-owner',relation=0,target_owner=1),
    dict(name='stored-a',relation=0,stored=storedA),dict(name='stored-b',relation=0,stored=storedB),
    dict(name='no-moves',relation=0,moves=0),dict(name='actor-construction',relation=0,actor_countdown=5),
    dict(name='score100',relation=3,ships=90,goal=far),dict(name='score101',relation=3,ships=89,goal=far)]
with (DATA/'case-manifest-v1.json').open('x') as f:json.dump(dict(cases=specs,near=near,far=far,seed=0,
    kind='synthetic fleet-phase states from retained generated snapshot; no game run',native_scope='proposals, not accepted full-turn actions'),f,indent=2)
exe=Path('/home/diego/ic2-work/build/Imperial Conquest 2.exe').read_bytes();assert hashlib.sha256(exe).hexdigest()=='9d753d5de78801f2368d06125cc87f296b92f671b686c39fd6ac149838ebba31'
pe=struct.unpack_from('<I',exe,0x3c)[0];n,opt=struct.unpack_from('<H',exe,pe+6)[0],struct.unpack_from('<H',exe,pe+20)[0];sections=[]
for i in range(n):
    o=pe+24+opt+40*i;vs,va,rs,rp=struct.unpack_from('<4I',exe,o+8);sections.append((0x400000+va,rp,rs))
def project(ram):
    na,nf=short(ram,0x4a0324),short(ram,0x4a0326)
    b=read(ram,0x45e870,89600)+read(ram,0x479590,11356)+struct.pack('<h',na)+read(ram,0x47c1ec,na*656)
    b+=struct.pack('<h',nf)+read(ram,0x49c26c,nf*26)+read(ram,0x474670,18752)+read(ram,0x49da10,600)
    news=100958+len(parsed['armies'])*656+2+len(parsed['fleets'])*26+18752+600
    tail=bytearray(template[parsed['tail_off']:parsed['tail_off']+55])
    for offset,address in [(36,0x4a0320),(38,0x4a0322),(40,0x4a0330),(42,0x4a0332),(44,0x4a032e)]:struct.pack_into('<h',tail,offset,short(ram,address))
    tail[54]=0
    return b+template[news:parsed['tail_off']]+tail
rows=[]
for spec in specs:
    ram=bytearray(raw);put(ram,0x4a0320,1);put(ram,0x4a0322,parsed['turn_order'].index(1));struct.pack_into('<I',ram,0x45e030-RAM_BASE,0)
    for i,j in [(1,3),(3,1)]:put(ram,0x474670+i*1172+0x26+2*j,spec['relation'])
    # Restore both old fleet cells before positioning; regenerate valid markers.
    for i in (0,1):
        base=0x49c26c+i*26;x,y=short(ram,base),short(ram,base+2)
        put(ram,0x45e870+2*(x*140+y),short(ram,base+24))
    goal=tuple(spec.get('goal',near))
    for i,pos,owner,ships,countdown,moves in [(0,actor,1,90,spec.get('actor_countdown',-1),spec.get('moves',25)),(1,goal,spec.get('target_owner',3),spec.get('ships',70),spec.get('countdown',-1),25)]:
        base=0x49c26c+i*26
        for off,val in [(0,pos[0]),(2,pos[1]),(4,-1),(6,-1),(8,owner),(10,countdown),(12,moves),(18,ships),(20,100),(22,-1),(24,cell(ram,*pos))]:put(ram,base+off,val)
        if countdown<0:put(ram,0x45e870+2*(pos[0]*140+pos[1]),owner+(300 if ships<25 else 316 if ships<50 else 332))
        else: # Valid construction records use an own-city index at +20.
            put(ram,base+20,next(c['id'] for c in parsed['cities'] if c['owner']==owner))
    if 'stored' in spec:
        put(ram,0x49c270,spec['stored'][0]);put(ram,0x49c272,spec['stored'][1])
    u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x300000);u.mem_map(0x800000,0x10000)
    for va,rp,rs in sections:
        if rs:u.mem_write(va,exe[rp:rp+rs])
    u.mem_write(RAM_BASE,bytes(ram));esp=0x80f000;u.mem_write(esp,struct.pack('<I',0x600000));u.reg_write(UC_X86_REG_ESP,esp)
    decision={};draws=[];pending=[]
    def hook(uc,address,size,data):
        if pending and address==pending[-1]['ret']:
            d=pending.pop();d.update(result=uc.reg_read(UC_X86_REG_EAX),seed_after=struct.unpack('<I',uc.mem_read(0x45e030,4))[0]);draws.append(d)
        if address==0x40284c:
            ret=struct.unpack('<I',uc.mem_read(uc.reg_read(UC_X86_REG_ESP),4))[0]
            pending.append(dict(ret=ret,bound=uc.reg_read(UC_X86_REG_EAX),seed_before=struct.unpack('<I',uc.mem_read(0x45e030,4))[0]))
        if address==0x44e1fc:
            ret=struct.unpack('<I',uc.mem_read(uc.reg_read(UC_X86_REG_ESP),4))[0]
            decision.update(site=ret-5,fleet=uc.reg_read(UC_X86_REG_EAX)&65535,goal=list(struct.unpack('<2h',struct.pack('<I',uc.reg_read(UC_X86_REG_EDX)))))
            uc.emu_stop()
    u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x44f608,0x600000,count=5000000)
    assert not pending and (decision or u.reg_read(UC_X86_REG_EIP)==0x600000)
    captured=bytes(u.mem_read(RAM_BASE,len(ram)));b=project(captured)
    folder=OUT/spec['name'];folder.mkdir()
    for name,body in [('input.ram',bytes(ram)),('pre-move.ram',captured),('pre-move.SAV',b)]:
        with (folder/name).open('xb') as f:f.write(body)
    with (folder/'expected.json').open('x') as f:json.dump(sav.parse(b),f)
    rows.append(dict(case=spec['name'],original=decision,draws=draws,mode='stopped before movement; automatic prepass and RNG actually executed'))
with (DATA/'original-fleet-controls-v1.json').open('x') as f:json.dump(rows,f,indent=2)
print(json.dumps(dict(cases=len(rows),choices=[(r['case'],hex(r['original'].get('site',0)),r['original'].get('goal'),len(r['draws'])) for r in rows])))
