"""Compare hooked/unhooked Delphi register-call ABI, outputs, flags and stack."""
import os
import random
import struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
import score_hook as H

SOURCE=Path(os.environ.get('IC2_WORK',Path.home()/'ic2-work'))/'prefix/drive_c/IC2'/H.A.SRC
REGS=(UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESI,
      UC_X86_REG_EDI,UC_X86_REG_EBP,UC_X86_REG_ESP,UC_X86_REG_EFLAGS)
RNG=random.Random(1687)
b,caves=H.build(SOURCE.read_bytes())
fake=(b'\x66\xc7\x02\x07\x00'  # [edx]=7
      b'\x66\xc7\x01\x37\x00' # [ecx]=55
      b'\x8b\x44\x24\x04\x66\xc7\x00\x09\x00' # stack arg distance=9
      b'\xb8\xef\xbe\xad\xde\xb9\x10\x20\x30\x40\xba\x50\x60\x70\x80\x05\x11\x00\x00\x00\xc2\x04\x00')

for name,sid,site,target in H.SITES:
    for count in (0,7,H.CAP-1,H.CAP):
        for trial in range(20):
            initial={r:RNG.getrandbits(32) for r in REGS}
            initial.update({UC_X86_REG_EAX:0,UC_X86_REG_EDX:0x80e000,UC_X86_REG_ECX:0x80e004,
                            UC_X86_REG_ESP:0x80f000,UC_X86_REG_EFLAGS:0x202|(RNG.getrandbits(32)&0xcd5)})
            results=[]
            for hooked in (False,True):
                u=Uc(UC_ARCH_X86,UC_MODE_32)
                u.mem_map(0x400000,0x300000);u.mem_map(0x800000,0x10000)
                for r,v in initial.items():u.reg_write(r,v)
                u.mem_write(0x80f000,struct.pack('<2I',site+5,0x80e008))
                u.mem_write(target,fake)
                u.mem_write(H.CTL,struct.pack('<I',count))
                u.mem_write(H.A.NATION,struct.pack('<h',0))
                if hooked:
                    u.mem_write(caves[name],H.stub(caves[name],sid,target))
                u.emu_start(caves[name] if hooked else target,site+5,count=1000)
                results.append(([u.reg_read(r) for r in REGS],bytes(u.mem_read(0x80e000,12)),
                                bytes(u.mem_read(0x80f008,100)))) # live caller stack after RET 4
                if hooked:
                    assert struct.unpack('<I',u.mem_read(H.CTL,4))[0]==min(count+1,H.CAP)
                    if count<H.CAP:
                        record=u.mem_read(H.BUF+H.REC*count,H.REC)
                        assert struct.unpack_from('<6i',record)==(sid,0,0,7,55,9)
            assert results[0]==results[1],(name,count,trial,results)
print('PASS 160 hooked/unhooked target-call comparisons; ABI, flags, outputs and full-buffer behavior')
