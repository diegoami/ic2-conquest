"""Observe original ECE4 candidate arithmetic; raw/component ledger private."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'runs/experiments/navigation187'));import core as C
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
p=argparse.ArgumentParser();p.add_argument('--ram',type=Path,required=True);p.add_argument('--private-output',type=Path,required=True);p.add_argument('--version',required=True);a=p.parse_args();raw=a.ram.read_bytes()
u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x300000);u.mem_map(0x800000,0x10000)
for va,rp,rs in C.SECTIONS:
 if rs:u.mem_write(va,C.EXE[rp:rp+rs])
u.mem_write(C.ORIGIN,raw);u.mem_write(0x80f000,struct.pack('<2I',0x600000,0x80a008))
for reg,value in [(UC_X86_REG_ESP,0x80f000),(UC_X86_REG_EAX,4),(UC_X86_REG_EDX,0x80a000),(UC_X86_REG_ECX,0x80a004)]:u.reg_write(reg,value)
rows=[];rng=[]
def hook(uc,address,size,user):
 if address==0x40284c:rng.append(address);uc.emu_stop()
 if address==0x44ee16:
  ebp=uc.reg_read(UC_X86_REG_EBP);index=uc.reg_read(UC_X86_REG_EDI)&65535
  value=struct.unpack('<i',uc.mem_read(ebp-0x1c,4))[0];distance=struct.unpack('<h',uc.mem_read(ebp-0xe,2))[0]
  pos=tuple(C.xy(raw,0x479590+index*34+14));different=C.classify(raw,pos)!=C.classify(raw,tuple(C.xy(raw,0x47c1ec+4*656)))
  rows.append(dict(index=index,adjusted_defense=struct.unpack('<i',uc.mem_read(ebp-0x18,4))[0],score_before_distance_return=value,distance=distance,geography_differs=different))
u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x44ece4,0x600000,count=5000000)
assert not rng and u.reg_read(UC_X86_REG_EIP)==0x600000 and bytes(u.mem_read(C.ORIGIN,C.SIZE))==raw
with a.private_output.open('x') as f:json.dump(rows,f,indent=2)
public=dict(original_candidate_rows=len(rows),original_RNG_calls=0,complete_RAM_identity=True,score_observation_instruction='0044EE16',scope='private per-candidate values retained; no source/owner state emitted')
with (ROOT/'runs/experiments/data/run-exp-city-army187'/('component-gate-'+a.version+'.json')).open('x') as f:json.dump(public,f,indent=2)
print('PASS original candidate arithmetic observer; game RAM unchanged, no RNG')
