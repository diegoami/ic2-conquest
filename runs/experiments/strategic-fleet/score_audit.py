"""Original hunt scorer replay with actual Random; preserve output separately."""
import json,struct,hashlib
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EDX,UC_X86_REG_ECX,UC_X86_REG_ESP,UC_X86_REG_EIP
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'artifacts/run-exp-strategic-fleet/controls-v1';DATA=ROOT/'runs/experiments/data/run-exp-strategic-fleet'
exe=Path('/home/diego/ic2-work/build/Imperial Conquest 2.exe').read_bytes();assert hashlib.sha256(exe).hexdigest()=='9d753d5de78801f2368d06125cc87f296b92f671b686c39fd6ac149838ebba31'
pe=struct.unpack_from('<I',exe,0x3c)[0];count,opt=struct.unpack_from('<H',exe,pe+6)[0],struct.unpack_from('<H',exe,pe+20)[0];sections=[]
for i in range(count):
 o=pe+24+opt+40*i;vs,va,rs,rp=struct.unpack_from('<4I',exe,o+8);sections.append((0x400000+va,rp,rs))
rows=[]
for name,want in [('peace',-10000),('war',253),('war-stronger',90),('war-weaker',1797),('score100',100),('score101',101)]:
 ram=bytearray((BASE/name/'pre-move.ram').read_bytes());struct.pack_into('<I',ram,0x30,0)
 u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x300000);u.mem_map(0x800000,0x10000)
 for va,rp,rs in sections:
  if rs:u.mem_write(va,exe[rp:rp+rs])
 u.mem_write(0x45e000,bytes(ram));u.mem_write(0x80f000,struct.pack('<I',0x600000))
 for reg,value in [(UC_X86_REG_EAX,0),(UC_X86_REG_EDX,0x80a000),(UC_X86_REG_ECX,0x80a004),(UC_X86_REG_ESP,0x80f000)]:u.reg_write(reg,value)
 u.emu_start(0x44f4f8,0x600000,count=4000000);assert u.reg_read(UC_X86_REG_EIP)==0x600000
 score=struct.unpack('<h',u.mem_read(0x80a004,2))[0];assert score==want,(name,score,want)
 rows.append(dict(case=name,score=score,target=None if score==-10000 else struct.unpack('<h',u.mem_read(0x80a000,2))[0],
   seed_before=0,seed_after=struct.unpack('<I',u.mem_read(0x45e030,4))[0],scope='separate original scorer replay; original Random executes, not a stub'))
with (DATA/'original-score-controls-v1.json').open('x') as f:json.dump(rows,f,indent=2)
print('PASS original hunt score controls including100/101 strict boundary; no strength/RNG replacement')
