"""Preservation/capacity checks required before strategic Wine observations."""
import json
import random
import struct
import sys
from pathlib import Path
import observer as O
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from tests import test_ai_hook as T

source=Path('/home/diego/ic2-work/build/Imperial Conquest 2 fast rollingsave seed.exe').read_bytes()
b,sites,caves=O.build(source);rng=random.Random(171);passed=0
for name,sid,site,target in sites:
    for count in (0,O.CAP-1,O.CAP):
        for sn in (0,O.SNAP_CAP-1,O.SNAP_CAP):
            for trial in range(4):
                u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x2000000)
                u.mem_write(O.A.CODE_VA,b[O.A.CODE_RAW:O.A.CODE_RAW+0x5b400])
                u.mem_write(O.A.PATCH_VA,b[O.A.PATCH_RAW:O.A.PATCH_RAW+O.A.RAW_SIZE])
                u.mem_write(O.CTL,struct.pack('<5I',count,O.MAGIC,O.CAP,sn,0))
                regs={r:rng.getrandbits(32) for r in T.REGS};unit=rng.randrange(14)
                regs[T.UC_X86_REG_EAX]=(regs[T.UC_X86_REG_EAX]&0xffff0000)|unit
                table,stride=(O.A.FLEETS,26) if target==0x44e1fc else (O.A.ARMIES,656)
                header=rng.randbytes(32);u.mem_write(table+unit*stride,header)
                nation=rng.randrange(16);u.mem_write(O.A.NATION,struct.pack('<h',nation))
                seed=rng.getrandbits(32);u.mem_write(0x45e030,struct.pack('<I',seed))
                esp=T.STACK_TOP-2048;stack=rng.randbytes(128)
                u.mem_write(esp,struct.pack('<I',site+5)+stack)
                for r,v in regs.items():u.reg_write(r,v)
                flags=0x202|(rng.getrandbits(32)&T.ARITH)
                u.reg_write(T.UC_X86_REG_ESP,esp);u.reg_write(T.UC_X86_REG_EFLAGS,flags)
                before=bytes(u.mem_read(O.SNAP_BASE,O.SNAP_SIZE))
                u.emu_start(caves[name],target)
                assert all(u.reg_read(r)==v for r,v in regs.items())
                assert u.reg_read(T.UC_X86_REG_ESP)==esp
                assert u.reg_read(T.UC_X86_REG_EFLAGS)&(T.ARITH|0x200)==flags&(T.ARITH|0x200)
                assert bytes(u.mem_read(esp,132))==struct.pack('<I',site+5)+stack
                assert bytes(u.mem_read(O.SNAP_BASE,O.SNAP_SIZE))==before
                n,_,_,ns,overflow=struct.unpack('<5I',u.mem_read(O.CTL,20))
                assert n==count+(count<O.CAP)
                capture=count<O.CAP and target==0x44e670 and sn<O.SNAP_CAP
                assert ns==sn+int(capture)
                assert overflow==int(count>=O.CAP or (target==0x44e670 and sn>=O.SNAP_CAP))
                if count<O.CAP:
                    rec=bytes(u.mem_read(O.BUF+count*O.REC,O.REC))
                    assert struct.unpack_from('<IIIiII',rec)==(sid,regs[T.UC_X86_REG_EAX],regs[T.UC_X86_REG_EDX],nation,site+5,seed)
                    assert rec[24:56]==header and rec[64:96]==stack[:32]
                    assert struct.unpack_from('<i',rec,56)[0]==(sn if capture else -1)
                if capture:assert bytes(u.mem_read(O.SNAP+sn*O.SNAP_SIZE,O.SNAP_SIZE))==before
                passed+=1
print(json.dumps(dict(passed=passed,sites=len(sites),snapshot_capacity=O.SNAP_CAP,record_capacity=O.CAP,
    registers_flags_stack_seed_and_game_RAM_preserved=True,full_capacities_fail_closed=True)))
