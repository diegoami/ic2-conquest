"""Replay original scorers/branch from captured RAM; build diagnostic containers.

Projection SAVs are synthetic, never original Save As claims. Original helpers
are executed unchanged; no RNG/game helper is stubbed. Immutable output only.
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EDX,UC_X86_REG_ECX,UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_ESI,UC_X86_REG_EBX
import observer as O
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from state import sav
p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('--version',default='v1');a=p.parse_args()
BASE=ROOT/'artifacts/run-exp-strategic-fidelity';RUN=BASE/'original'/a.label
OUT=BASE/'projections'/(a.label+'-'+a.version);OUT.mkdir(parents=True,exist_ok=False)
DATA=ROOT/'runs/experiments/data/run-exp-strategic-fidelity'/a.label
records=json.loads((DATA/'records.json').read_text())
before=next(RUN.glob('*-before.SAV')).read_bytes();template=sav.parse(before)
exe=Path('/home/diego/ic2-work/build/Imperial Conquest 2.exe').read_bytes()
assert hashlib.sha256(exe).hexdigest()=='9d753d5de78801f2368d06125cc87f296b92f671b686c39fd6ac149838ebba31'
pe=struct.unpack_from('<I',exe,0x3c)[0];n,opt=struct.unpack_from('<H',exe,pe+6)[0],struct.unpack_from('<H',exe,pe+20)[0]
sections=[]
for k in range(n):
    off=pe+24+opt+k*40;vs,va,rs,rp=struct.unpack_from('<4I',exe,off+8);sections.append((0x400000+va,rp,rs))
def read(ram,addr,size):return ram[addr-O.SNAP_BASE:addr-O.SNAP_BASE+size]
def i16(ram,addr):return struct.unpack('<h',read(ram,addr,2))[0]
def machine(ram):
    u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x300000);u.mem_map(0x800000,0x10000)
    for va,rp,rs in sections:
        if rs:u.mem_write(va,exe[rp:rp+rs])
    u.mem_write(O.SNAP_BASE,ram)
    return u
def execute(ram,entry,army,score=False):
    u=machine(ram);esp=0x80f000;out=0x80a000
    u.mem_write(esp,struct.pack('<2I',0x600000,out+8))
    for reg,value in ((UC_X86_REG_EAX,army),(UC_X86_REG_EDX,out),(UC_X86_REG_ECX,out+4),(UC_X86_REG_ESP,esp)):u.reg_write(reg,value)
    random_calls=[]
    def hook(uc,address,size,data):
        if address==0x40284c:random_calls.append(address)
    u.hook_add(UC_HOOK_CODE,hook);u.emu_start(entry,0x600000,count=4000000)
    assert u.reg_read(UC_X86_REG_EIP)==0x600000,hex(u.reg_read(UC_X86_REG_EIP))
    assert not random_calls and bytes(u.mem_read(O.SNAP_BASE,O.SNAP_SIZE))==ram
    target=struct.unpack('<h',u.mem_read(out,2))[0]
    value=struct.unpack('<h',u.mem_read(out+4,2))[0] if score else None
    distance=struct.unpack('<h',u.mem_read(out+8,2))[0] if score else None
    if score and value==-10000:target=None
    return dict(target=target,score=value,distance=distance)
def branch(ram,army,city,enemy,resupply):
    u=machine(ram);esp=0x80f000
    # Exact F31C locals as used at0044F3B8 after the three original scorers.
    words=[resupply['target'],city['target'] if city['target'] is not None else -1,
        enemy['target'] if enemy['target'] is not None else -1,enemy['score'],city['score'],enemy['distance'],city['distance']]
    u.mem_write(esp,struct.pack('<7h',*words))
    u.reg_write(UC_X86_REG_ESP,esp);u.reg_write(UC_X86_REG_EBX,0x47c1ec+army*656);u.reg_write(UC_X86_REG_ESI,army)
    result={};rng=[]
    def hook(uc,address,size,data):
        if address==0x40284c:rng.append(address)
        if address in (0x44dba8,0x44e84c):
            ret=struct.unpack('<I',u.mem_read(u.reg_read(UC_X86_REG_ESP),4))[0]
            site=ret-5
            kind={0x44f409:1,0x44f43f:0,0x44f47c:3}.get(site,2 if address==0x44e84c else None)
            assert kind is not None,(hex(address),hex(site))
            goal=None if kind==2 else list(struct.unpack('<2h',struct.pack('<I',u.reg_read(UC_X86_REG_EDX))))
            result.update(kind=kind,goal=goal,site=site);u.emu_stop()
    u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x44f3b8,0x44f4cc,count=100000)
    assert result and not rng and bytes(u.mem_read(O.SNAP_BASE,O.SNAP_SIZE))==ram
    return result
def project(ram):
    na,nf=i16(ram,0x4a0324),i16(ram,0x4a0326)
    assert 0<=na<199 and 0<=nf<200
    body=read(ram,0x45e870,89600)+read(ram,0x479590,11356)+struct.pack('<h',na)+read(ram,0x47c1ec,na*656)
    body+=struct.pack('<h',nf)+read(ram,0x49c26c,nf*26)+read(ram,0x474670,16*1172)+read(ram,0x49da10,600)
    # News/UI metadata are retained from before.SAV and excluded from decision gates.
    source_news=100958+len(template['armies'])*656+2+len(template['fleets'])*26+16*1172+600
    news=before[source_news:template['tail_off']]
    tail=bytearray(before[template['tail_off']:template['tail_off']+55])
    for offset,address in ((36,0x4a0320),(38,0x4a0322),(40,0x4a0330),(42,0x4a0332),(44,0x4a032e)):
        struct.pack_into('<h',tail,offset,i16(ram,address))
    tail[54]=0
    return body+news+tail
rows=[]
for record in records:
    sn=record['snapshot']
    if sn<0:continue
    ram=(RUN/'snapshots'/f'{sn:03}.ram').read_bytes();assert len(ram)==O.SNAP_SIZE
    army=record['unit'];owner=i16(ram,0x47c1ec+army*656+4)
    assert owner==record['nation']==i16(ram,0x4a0320)
    city=execute(ram,0x44ece4,army,True);enemy=execute(ram,0x44ee60,army,True);resupply=execute(ram,0x44e670,army)
    chosen=branch(ram,army,city,enemy,resupply)
    projection=project(ram);parsed=sav.parse(projection)
    stem=f'{sn:03}'
    with (OUT/(stem+'.SAV')).open('xb') as f:f.write(projection)
    with (OUT/(stem+'.json')).open('x') as f:json.dump(parsed,f)
    following=next((r for r in records if r['seq']>record['seq'] and r['nation']==owner and r['unit']==army and r['site'] in (0x44f409,0x44f43f,0x44f47c,0x44f4a3,0x44f4c7)),None)
    observed_equal=None if chosen['kind']==2 or following is None else chosen['site']==following['site'] and chosen['goal']==following['goal']
    assert observed_equal is not False,(sn,chosen,following)
    rows.append(dict(snapshot=sn,record_seq=record['seq'],army=army,nation=owner,
        city=city,enemy=enemy,resupply=resupply,decision=chosen,observed_first_call_matches=observed_equal,
        random_calls=0,projection='synthetic diagnostic container from captured RAM, not original Save As'))
with (DATA/f'original-decisions-{a.version}.jsonl').open('x') as f:
    for row in rows:f.write(json.dumps(row)+'\n')
with (OUT/'manifest.json').open('x') as f:json.dump(rows,f,indent=2)
print(json.dumps(dict(label=a.label,decisions=len(rows),live_first_calls_verified=sum(r['observed_first_call_matches'] is True for r in rows),random_calls=0)))
