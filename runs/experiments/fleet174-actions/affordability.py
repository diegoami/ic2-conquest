"""Paired original low-level walk inputs differing ONLY in controller byte."""
import json,struct
from common import *
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EDX,UC_X86_REG_ESP,UC_X86_REG_EIP
out=BASE/'affordability-v1';out.mkdir();rows=[]
source=bytearray((BASE/'inputs-v1/rough-human-one/input.ram').read_bytes())
for human in [False,True]:
 ram=bytearray(source);ram[0x474670+1172+0x490-RAM_BASE]=int(human);u=machine(ram)
 u.mem_write(0x80f000,struct.pack('<I',0x600000));u.reg_write(UC_X86_REG_ESP,0x80f000);u.reg_write(UC_X86_REG_EAX,0);u.reg_write(UC_X86_REG_EDX,49|(63<<16))
 u.emu_start(0x44e094,0x600000,count=1000000);assert u.reg_read(UC_X86_REG_EIP)==0x600000
 final=bytes(u.mem_read(RAM_BASE,RAM_SIZE));moves=short(final,0x49c278);assert moves==int(human)
 assert xy(final,0x49c26c)==[49,62]
 folder=out/('human' if human else 'ai');folder.mkdir()
 for name,body in [('before.ram',bytes(ram)),('after.ram',final),('before.SAV',project(ram)),('after.SAV',project(final))]:
  with (folder/name).open('xb') as f:f.write(body)
 rows.append(dict(human=human,original_moves_after=moves,position=[49,62],requested=[49,63],rough_cost=3,budget=1))
left=(out/'ai/before.ram').read_bytes();right=(out/'human/before.ram').read_bytes();diff=[i for i,(a,b) in enumerate(zip(left,right)) if a!=b]
assert diff==[0x474670+1172+0x490-RAM_BASE]
with (DATA/'affordability-original-v1.json').open('x') as f:json.dump(dict(only_input_difference='Carthage controller BYTE',raw_difference_offsets=diff,rows=rows),f,indent=2)
print('PASS original AI/human inputs differ only at controller byte: AI clears1move, human preserves1')
