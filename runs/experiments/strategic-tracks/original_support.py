"""Conditional original-instruction calls; no game helper or Random replacement."""
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'runs/experiments/fleet174-actions'))
from common import *
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
sys.path.insert(0,str(ROOT));from state import sav
BASE=ROOT/'artifacts/run-exp-strategic-tracks';DATA=ROOT/'runs/experiments/data/run-exp-strategic-tracks'
def execute(raw,entry,eax=0,edx=0,ecx=0,args=(),stop=()):
 u=machine(raw);u.mem_write(0x80f000,struct.pack('<'+'I'*(1+len(args)),0x600000,*args));u.reg_write(UC_X86_REG_ESP,0x80f000)
 for reg,val in [(UC_X86_REG_EAX,eax),(UC_X86_REG_EDX,edx),(UC_X86_REG_ECX,ecx)]:u.reg_write(reg,val)
 draws=[];pending=[];hit=[];relations=[];deficit=[]
 seed=lambda:struct.unpack('<I',u.mem_read(0x45e030,4))[0]
 def hook(uc,address,size,user):
  if pending and address==pending[-1]['return_address']:
   r=pending.pop();value=uc.reg_read(UC_X86_REG_EAX);assert 0<=value<r['bound'];r.update(result=value,seed_after=seed());draws.append(r)
  if address==0x40284c:pending.append(dict(bound=uc.reg_read(UC_X86_REG_EAX),seed_before=seed(),return_address=struct.unpack('<I',uc.mem_read(uc.reg_read(UC_X86_REG_ESP),4))[0]))
  if address==0x449b40:relations.append(dict(actor=uc.reg_read(UC_X86_REG_EAX)&65535,target=uc.reg_read(UC_X86_REG_EDX)&65535,relation=uc.reg_read(UC_X86_REG_ECX)&65535))
  if address==0x45011e:
   sp=uc.reg_read(UC_X86_REG_ESP);own,threat=struct.unpack('<2i',uc.mem_read(sp+4,8));deficit.append(dict(own=own,threat=threat))
  if address in stop:hit.append(address);uc.emu_stop()
 u.hook_add(UC_HOOK_CODE,hook);u.emu_start(entry,0x600000,count=50000000)
 assert hit or u.reg_read(UC_X86_REG_EIP)==0x600000,hex(u.reg_read(UC_X86_REG_EIP))
 return u,bytes(u.mem_read(RAM_BASE,RAM_SIZE)),dict(draws=draws,relation_writes=relations,power=deficit)
def write(p,value):
 with p.open('x') as f:json.dump(value,f,indent=2)
def keep(p,value):
 with p.open('xb') as f:f.write(value)
def container(raw):
 b=bytearray(project(raw));parsed=sav.parse(b);b[parsed['tail_off']:parsed['tail_off']+32]=read(raw,0x49efe8,32);return b
def pair(folder,before,after):
 folder.mkdir(exist_ok=False)
 for name,raw in [('before',before),('expected',after)]:
  b=container(raw);keep(folder/(name+'.SAV'),b);write(folder/(name+'.json'),sav.parse(b));keep(folder/(name+'.ram'),raw)
def diplomacy_facts(raw):
 n=short(raw,0x4a0320);u,after,_=execute(raw,0x44faa0,n,0x80a000,0x80a004,args=(0x80a008,));assert after==raw
 trades=struct.unpack('<h',u.mem_read(0x80a000,2))[0];protected=bool(u.mem_read(0x80a004,1)[0]);war=bool(u.mem_read(0x80a008,1)[0]);mob=short(raw,0x474ab2+n*1172)
 u,after,trace=execute(raw,0x44fb7c,stop=(0x44fd22,));sp=u.reg_read(UC_X86_REG_ESP)
 target=struct.unpack('<h',u.mem_read(sp+8,2))[0]
 return dict(trades=trades,protected=protected,at_war=war,busy=war or mob>40 or short(raw,0x4a032e)==3,war_target=None if target<0 else target,pre_draw_relation_writes=trace['relation_writes'])
