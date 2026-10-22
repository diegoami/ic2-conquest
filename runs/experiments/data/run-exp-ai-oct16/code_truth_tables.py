"""Execute pinned original predicate and score-rounding x86 under Unicorn.

Code/emulator evidence only. This is not Wine execution or native confirmation.
"""
import hashlib,json,struct,sys,time
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'patches'))
from battle_hook import sections
DATA=Path(__file__).resolve().parent
exe=Path(sys.argv[1]);raw=exe.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f'
u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x300000);u.mem_map(0x800000,0x10000)
for _,va,vsize,rptr,rsize,_ in sections(raw):
    if rsize:u.mem_write(va,raw[rptr:rptr+rsize])
predicates=[]
for human in (0,1):
 for side in (0,1):
  for general_a in (0,1):
   for general_d in (0,1):
    u.mem_write(0x45e6aa,struct.pack('<h',0))
    u.mem_write(0x474b00,bytes([human]))
    u.mem_write(0x4a0b78,struct.pack('<h',side))
    u.mem_write(0x45e6a4,bytes([general_a,general_d]))
    u.mem_write(0x80f000,struct.pack('<I',0x600000));u.reg_write(UC_X86_REG_ESP,0x80f000)
    u.emu_start(0x438378,0x600000,count=1000)
    observed=u.reg_read(UC_X86_REG_EAX)&255
    expected=int(not human or (general_a if side==0 else general_d))
    assert observed==expected
    predicates.append(dict(human=human,side=side,general_attacker=general_a,general_defender=general_d,original_predicate=observed))
rounding=[]
for score in (-2147483647,-1001,-1000,-9,-8,-7,-3,-2,-1,0,1,2,3,7,8,9,999,1000,1001,2147483647):
    expected=score-(abs(score)//2*(1 if score>=0 else -1))
    u.reg_write(UC_X86_REG_EDI,score&0xffffffff)
    u.emu_start(0x44ef4d,0x44ef58,count=100)
    observed=struct.unpack('<i',struct.pack('<I',u.reg_read(UC_X86_REG_EDI)))[0]
    u.reg_write(UC_X86_REG_EBP,0x80e000)
    u.mem_write(0x80e000-0x1c,struct.pack('<i',score))
    u.emu_start(0x44edd1,0x44edde,count=100)
    city=struct.unpack('<i',u.mem_read(0x80e000-0x1c,4))[0]
    assert observed==expected==city
    rounding.append(dict(input=score,city_original=city,army_original=observed))
record=dict(provenance='pinned original x86 under Unicorn, not Wine/native',exe_sha256=hashlib.sha256(raw).hexdigest(),
            control_function='0x438378',predicate=predicates,
            score_slices=['0x44edd1..0x44edde','0x44ef4d..0x44ef58'],rounding=rounding)
path=DATA/f'code-truth-tables-{time.strftime("%Y%m%d-%H%M%S")}.json'
with path.open('x') as out:json.dump(record,out,indent=2)
print('PASS',len(predicates),'original predicate combinations and',len(rounding),'signed rounding cases;',path.name)
