"""CPU-only wrapper ABI/capacity checks; fake callee exists ONLY in this test."""
import json,random,struct
from pathlib import Path
import phase_observer as O
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
source=Path('/home/diego/ic2-work/build/Imperial Conquest 2 fast rollingsave seed.exe').read_bytes();b,caves=O.build(source)
regs=[UC_X86_REG_EDI,UC_X86_REG_ESI,UC_X86_REG_EBP,UC_X86_REG_EBX,UC_X86_REG_EDX,UC_X86_REG_ECX,UC_X86_REG_EAX]
rng=random.Random(176177174);passed=0
for name,sid,site,target in O.SITES:
 for count in [0,92,94,95,96]:
  for trial in range(24):
   u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x2000000);u.mem_map(0x3000000,0x10000)
   u.mem_write(O.A.CODE_VA,b[O.A.CODE_RAW:O.A.CODE_RAW+0x5b400]);u.mem_write(O.A.PATCH_VA,b[O.A.PATCH_RAW:O.A.PATCH_RAW+O.A.RAW_SIZE])
   u.mem_write(O.CTL,struct.pack('<4I',count,O.MAGIC,O.CAP,0))
   esp=0x300f000;stack=rng.randbytes(128);u.mem_write(esp,struct.pack('<I',(site+5))+stack)
   values={r:rng.getrandbits(32) for r in regs}
   for r,v in values.items():u.reg_write(r,v)
   flags=0x202|(rng.getrandbits(32)&0xcd5);u.reg_write(UC_X86_REG_EFLAGS,flags);u.reg_write(UC_X86_REG_ESP,esp)
   before=bytes(u.mem_read(O.ORIGIN,O.SIZE));u.emu_start(caves[name],target)
   assert all(u.reg_read(r)==v for r,v in values.items()) and u.reg_read(UC_X86_REG_ESP)==esp
   assert u.reg_read(UC_X86_REG_EFLAGS)&0xed7==flags&0xed7 and bytes(u.mem_read(esp+4,128))==stack
   # Actual callee return/address depth exercised with a synthetic CPU effect.
   changed=bytearray(before);struct.pack_into('<h',changed,0x49c278-O.ORIGIN,3)
   u.mem_write(target,b'\x66\xc7\x05'+struct.pack('<I',0x49c278)+b'\x03\x00\xb8\x78\x56\x34\x12\xf9\xc3')
   u.emu_start(target,(site+5))
   assert u.reg_read(UC_X86_REG_EAX)==0x12345678 and all(u.reg_read(r)==v for r,v in values.items() if r!=UC_X86_REG_EAX)
   assert u.reg_read(UC_X86_REG_ESP)==esp+4 and bytes(u.mem_read(esp+4,128))==stack
   assert u.reg_read(UC_X86_REG_EFLAGS)&0xed7==(flags|1)&0xed7
   actual,_,_,overflow=struct.unpack('<4I',u.mem_read(O.CTL,16));assert actual==min(count+2,O.CAP) and overflow==int(count+2>O.CAP)
   if count<O.CAP:assert bytes(u.mem_read(O.SNAP+count*O.SIZE,O.SIZE))==before
   if count+1<O.CAP:assert bytes(u.mem_read(O.SNAP+(count+1)*O.SIZE,O.SIZE))==bytes(changed)
   passed+=1
print(json.dumps(dict(passed=passed,entry_and_return_CPU_preserved=True,snapshots_before_after_correct=True,capacity_fail_closed=True,fake_callee_in_CPU_test_only=True)))
