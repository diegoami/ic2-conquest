"""CPU preservation and capacity controls before any original run."""
import json
import random
import struct
import sys
from pathlib import Path
import observer as O

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tests import test_ai_hook as T

source = Path('/home/diego/ic2-work/build/Imperial Conquest 2 fast rollingsave seed.exe').read_bytes()
b, sites, caves = O.build(source)
rng = random.Random(1388)
passed = 0
for name, sid, site, target in sites:
    for count in (0, 7, O.CAP-1, O.CAP):
        for trial in range(12):
            nation = rng.randrange(16)
            u = T.machine(b, count, nation)
            regs = {r:rng.getrandbits(32) for r in T.REGS}
            army = 4 if trial == 0 else rng.randrange(200)
            regs[T.UC_X86_REG_EAX] = (regs[T.UC_X86_REG_EAX] & 0xffff0000) | army
            header = rng.randbytes(32)
            u.mem_write(O.A.ARMIES + army*O.A.ARMY_LEN, header)
            seed = rng.getrandbits(32)
            u.mem_write(0x45e030, struct.pack('<I', seed))
            stack = rng.randbytes(128)
            esp = T.STACK_TOP - 2048
            u.mem_write(esp, struct.pack('<I', site+5)+stack)
            for r,v in regs.items(): u.reg_write(r,v)
            flags = 0x202 | (rng.getrandbits(32) & T.ARITH)
            u.reg_write(T.UC_X86_REG_ESP,esp)
            u.reg_write(T.UC_X86_REG_EFLAGS,flags)
            expected_snapshot=bytes(u.mem_read(O.SNAP_BASE,O.SNAP_SIZE))
            u.emu_start(caves[name],target)
            assert all(u.reg_read(r)==v for r,v in regs.items())
            assert u.reg_read(T.UC_X86_REG_ESP)==esp
            assert u.reg_read(T.UC_X86_REG_EFLAGS)&(T.ARITH|0x200)==flags&(T.ARITH|0x200)
            assert bytes(u.mem_read(esp,132))==struct.pack('<I',site+5)+stack
            assert bytes(u.mem_read(O.A.ARMIES+army*O.A.ARMY_LEN,32))==header
            assert bytes(u.mem_read(0x45e030,4))==struct.pack('<I',seed)
            n=struct.unpack('<I',u.mem_read(O.CTL,4))[0]
            assert n==count+(count<O.CAP)
            if count<O.CAP:
                rec=bytes(u.mem_read(O.BUF+count*O.REC,O.REC))
                assert struct.unpack_from('<IIIiII',rec)==(sid,regs[T.UC_X86_REG_EAX],regs[T.UC_X86_REG_EDX],nation,site+5,seed)
                assert rec[24:56]==header
                if army==4 and target==0x44d734:
                    assert bytes(u.mem_read(O.SNAP,O.SNAP_SIZE))==expected_snapshot
                    assert struct.unpack('<I',u.mem_read(O.CTL+12,4))[0]==1
            passed+=1
print(json.dumps(dict(passed=passed,sites=len(sites),capacity_cases=[0,7,O.CAP-1,O.CAP],
    registers_flags_stack_army_header_seed_preserved=True)))
