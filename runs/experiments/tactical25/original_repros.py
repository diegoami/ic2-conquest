"""Pinned original x86 synthetic rule reproductions; not Wine/native playthroughs."""
import argparse,hashlib,json,struct,sys,datetime
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'patches'))
from battle_hook import sections
p=argparse.ArgumentParser();p.add_argument('--exe',type=Path,required=True);p.add_argument('--dat',type=Path,required=True);a=p.parse_args()
raw=a.exe.read_bytes();dat=a.dat.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f'
assert hashlib.sha256(dat).hexdigest()=='94d0ccfc67148d727de4c4e60aefc3c53ba9e67775bd689f0fcb2e23c12e5fbd'
u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x300000);u.mem_map(0x800000,0x100000)
for _,va,vsize,rptr,rsize,_ in sections(raw):
 if rsize:u.mem_write(va,raw[rptr:rptr+rsize])
u.mem_write(0x47946c,dat[0x1f7a6:0x1f7a6+50]);matrix=list(struct.unpack('<25h',u.mem_read(0x47946c,50)))
def word(at,v):u.mem_write(at,struct.pack('<h',v))
def reset():
 u.mem_write(0x4a0344,bytes(40*44));u.mem_write(0x4a0a24,struct.pack('<168h',*[50]*168));u.mem_write(0x45e6b0,b'\xff'*80)
 word(0x45e6ae,0);word(0x45e6ac,20)
 for i in range(40):word(0x4a0344+i*44+18,-1)
def unit(i,**kw):
 names=['x','y','origin','type','troops','quality','morale','moves','shots','target']
 for k,v in kw.items():word(0x4a0344+i*44+2*names.index(k),v)
def call(va):
 u.mem_write(0x8ff000,struct.pack('<I',0x600000));u.reg_write(UC_X86_REG_ESP,0x8ff000);u.emu_start(va,0x600000,count=100000)
 assert u.reg_read(UC_X86_REG_EIP)==0x600000
reset();unit(0,x=5,y=5,type=1,troops=3000,quality=5,morale=70,moves=1)
unit(20,x=5,y=6,type=0,troops=4000,quality=1,morale=50)
unit(21,x=6,y=5,type=1,troops=2000,quality=9,morale=90)
call(0x43a544);target=struct.unpack('<h',u.mem_read(0x4a0344+18,2))[0];assert target==20
rows=[dict(name='weighted-pass2',original_target=target,port_expected_target=21,own=dict(type=1,troops=3000,quality=5,morale=70),enemies=[dict(slot=20,type=0,troops=4000,quality=1,morale=50),dict(slot=21,type=1,troops=2000,quality=9,morale=90)])]
# Observe original threat order after its complete selection-sort, before line/box search.
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
cs=Cs(CS_ARCH_X86,CS_MODE_32)
# Pin the instruction immediately after sorting by checked opcode, derived from original disassembly.
ins=list(cs.disasm(bytes(u.mem_read(0x43a718,0x350)),0x43a718))
for i in ins:
 if 0x43a850<=i.address<=0x43a950:print(hex(i.address),i.mnemonic,i.op_str)
record=dict(provenance='original x86 under Unicorn; synthetic input, not Wine/native',exe_sha256=hashlib.sha256(raw).hexdigest(),dat_sha256=hashlib.sha256(dat).hexdigest(),matrix=matrix,rows=rows)
out=root/'runs/experiments/data/run-exp-tactical25'/('original-repros-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S')+'.json')
with out.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(out)
