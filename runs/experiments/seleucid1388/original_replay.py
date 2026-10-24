"""Run actual original targeting/routing instructions from captured private RAM.

No game launch; no replacement targeting, movement, terrain or random helpers.
The full diagnostic output remains private. Saves/measurements never overwritten.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EDX,UC_X86_REG_ECX,UC_X86_REG_ESP,UC_X86_REG_EIP
import observer as O

p=argparse.ArgumentParser();p.add_argument('ram',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
assert not a.output.exists()
exe=Path('/home/diego/ic2-work/build/Imperial Conquest 2.exe').read_bytes()
assert hashlib.sha256(exe).hexdigest()=='9d753d5de78801f2368d06125cc87f296b92f671b686c39fd6ac149838ebba31'
ram=a.ram.read_bytes();assert len(ram)==O.SNAP_SIZE
pe=struct.unpack_from('<I',exe,0x3c)[0]
n,opt=struct.unpack_from('<H',exe,pe+6)[0],struct.unpack_from('<H',exe,pe+20)[0]
base=struct.unpack_from('<I',exe,pe+24+28)[0]
sections=[]
for k in range(n):
    off=pe+24+opt+40*k
    vs,va,rs,rp=struct.unpack_from('<4I',exe,off+8)
    sections.append((base+va,rp,rs))

def run(entry,eax,edx=0,ecx=0,args=(),walk=False):
    u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x300000);u.mem_map(0x800000,0x10000)
    for va,rp,rs in sections:
        if rs:u.mem_write(va,exe[rp:rp+rs])
    u.mem_write(O.SNAP_BASE,ram)
    esp=0x80f000
    u.mem_write(esp,struct.pack('<'+'I'*(len(args)+1),0x600000,*args))
    for r,v in ((UC_X86_REG_EAX,eax),(UC_X86_REG_EDX,edx),(UC_X86_REG_ECX,ecx),(UC_X86_REG_ESP,esp)):u.reg_write(r,v)
    random_calls=[];steps=[];stores=[]
    def hook(uc,address,size,data):
        if address==0x40284c:random_calls.append(address)
        if walk and address==0x44d420:
            steps.append(list(struct.unpack('<4h',u.mem_read(0x47c1ec+4*656,8))))
    u.hook_add(UC_HOOK_CODE,hook)
    if walk:
        def write(uc,access,address,size,value,data):
            if address in (0x47c1ec+4*656,0x47c1ee+4*656):
                stores.append(dict(field='x' if address==0x47c1ec+4*656 else 'y',value=value&65535,
                    instruction=hex(uc.reg_read(UC_X86_REG_EIP))))
        u.hook_add(UC_HOOK_MEM_WRITE,write)
    u.emu_start(entry,0x600000,count=3000000)
    assert u.reg_read(UC_X86_REG_EIP)==0x600000,hex(u.reg_read(UC_X86_REG_EIP))
    assert not random_calls,'Unexpected random call in deterministic helper'
    if not walk:assert bytes(u.mem_read(O.SNAP_BASE,O.SNAP_SIZE))==ram,'Helper changed game RAM'
    if walk:
        return dict(final=list(struct.unpack('<4h',u.mem_read(0x47c1ec+4*656,8))),steps=steps,coordinate_stores=stores,
            rng_unchanged=bytes(u.mem_read(0x45e030,4))==ram[0x30:0x34],random_calls=len(random_calls),
            army_record_after=bytes(u.mem_read(0x47c1ec+4*656,656)).hex(),
            map_after=list(struct.unpack('<44800h',u.mem_read(0x45e870,89600))))
    return u

def short(u,p):return struct.unpack('<h',u.mem_read(p,2))[0]
def packed(x,y):return (y<<16)|x
def scalar(entry,eax,edx=0):return run(entry,eax,edx).reg_read(UC_X86_REG_EAX)
out={'scope':'Actual unmodified original instructions from atomic pre-walk RAM; no game helpers replaced',
     'army_score':{},'city_score':{},'reachability':[],'waypoint':None,'random_draws':0}
for label,entry in [('army_score',0x44ee60),('city_score',0x44ece4)]:
    u=run(entry,4,0x80a000,0x80a004,(0x80a008,))
    out[label]=dict(target=short(u,0x80a000),score=short(u,0x80a004),distance=short(u,0x80a008))
for target in [(207,95),(191,95)]:
    out['reachability'].append(dict(goal=target,original_can_reach=bool(scalar(0x44cab4,4,packed(*target))&255),
        direct_line=bool(scalar(0x44cb40,packed(219,93),packed(*target))&255)))
u=run(0x44db38,packed(219,93),packed(191,95),0x80a000,(0x80b000,))
out['waypoint']=list(struct.unpack('<2h',u.mem_read(0x80a000,4)))
out['field_strengths']=[dict(army=i,value=scalar(0x44a8cc,i)) for i in (4,9,22,24)]
out['regions']=[]
for goal in [(219,93),(191,95),(207,95)]:
    u=run(0x44ca30,packed(*goal),0x80a000,0x80a004)
    out['regions'].append(dict(goal=goal,region=short(u,0x80a000),coast=int.from_bytes(u.mem_read(0x80a004,1),'little')))
out['walks']=[dict(goal=goal,**run(0x44d734,4,packed(*goal),walk=True)) for goal in [(207,95),(191,95),(189,104)]]
out['full_wrapper']=run(0x44dba8,4,packed(191,95),walk=True)
out['seed_controls']=[]
saved_ram=ram
for seed in (0,1,2,12345,0xffffffff):
    ram=ram[:0x30]+struct.pack('<I',seed)+ram[0x34:]
    u=run(0x44ee60,4,0x80a000,0x80a004,(0x80a008,))
    target=short(u,0x80a000)
    wrapper=run(0x44dba8,4,packed(191,95),walk=True)
    out['seed_controls'].append(dict(seed=seed,target=target,final=wrapper['final'],rng_unchanged=wrapper['rng_unchanged']))
ram=saved_ram
with a.output.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(complete=True,target=out['army_score']['target'],waypoint=out['waypoint'],
    full_wrapper_final=out['full_wrapper']['final'],seed_controls=len(out['seed_controls']),random_draws=0)))
