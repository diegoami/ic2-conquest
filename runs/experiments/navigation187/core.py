"""Pinned original-instruction runner; all raw RAM/trace material stays private."""
import hashlib,struct,sys
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EDX,UC_X86_REG_ECX,UC_X86_REG_EBP,UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_EFLAGS
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));from state import sav
BASE=ROOT/'artifacts/run-exp-navigation187';PRIVATE=BASE/'private';DATA=ROOT/'runs/experiments/data/run-exp-navigation187'
ORIGIN,SIZE=0x45e000,0x43000
RAM=(ROOT/'artifacts/run-exp-strategic-fidelity/original/N-rome-hook-v1/snapshots/000.ram').read_bytes()
EXE=Path('/home/diego/ic2-work/build/Imperial Conquest 2.exe').read_bytes();assert hashlib.sha256(EXE).hexdigest()=='9d753d5de78801f2368d06125cc87f296b92f671b686c39fd6ac149838ebba31'
DUMP=ROOT/'artifacts/cloud-migration-20261021/ic2-research-inputs-20261021/decompile/all_app_functions.txt';assert hashlib.sha256(DUMP.read_bytes()).hexdigest()=='2018c205a4e4ea4a4079f2d166623fb571062832d76e19b72e11d1f0edac87d8'
pe=struct.unpack_from('<I',EXE,0x3c)[0];n,opt=struct.unpack_from('<H',EXE,pe+6)[0],struct.unpack_from('<H',EXE,pe+20)[0];SECTIONS=[]
for i in range(n):
 o=pe+24+opt+40*i;vs,va,rs,rp=struct.unpack_from('<4I',EXE,o+8);SECTIONS.append((0x400000+va,rp,rs))
def read(ram,address,n):return bytes(ram[address-ORIGIN:address-ORIGIN+n])
def short(ram,address):return struct.unpack('<h',read(ram,address,2))[0]
def put(ram,address,value):struct.pack_into('<h',ram,address-ORIGIN,value)
def point(p):return (p[0]&65535)|((p[1]&65535)<<16)
def xy(ram,address):return list(struct.unpack('<2h',read(ram,address,4)))
def cell(ram,p):return short(ram,0x45e870+2*(p[0]*140+p[1]))
def setcell(ram,p,v):put(ram,0x45e870+2*(p[0]*140+p[1]),v)
def fresh_map(code=2):
 r=bytearray(RAM);r[0x45e870-ORIGIN:0x45e870-ORIGIN+89600]=struct.pack('<h',code)*44800;put(r,0x4a0320,1);r[0x4a0340-ORIGIN]=0;put(r,0x4a0326,0);return r
def place_army(r,index,pos,owner=None):
 a=0x47c1ec+index*656;old=xy(r,a);oldcell=short(r,a+8)
 if oldcell>=0 and 0<=old[0]<320 and 0<=old[1]<140 and 200<=cell(r,old)<248:setcell(r,old,oldcell)
 covered=cell(r,pos);put(r,a,pos[0]);put(r,a+2,pos[1]);put(r,a+8,covered)
 if owner is not None:put(r,a+4,owner)
 setcell(r,pos,200+short(r,a+4));return r
def run(entry,eax=0,edx=0,ecx=0,args=(),ram=RAM,fill=0,local_e=None,readonly=True,stop=(),budget=5000000,frame_setup=None):
 u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x300000);u.mem_map(0x800000,0x10000)
 for va,rp,rs in SECTIONS:
  if rs:u.mem_write(va,EXE[rp:rp+rs])
 u.mem_write(ORIGIN,bytes(ram));u.mem_write(0x800000,bytes([fill])*0x10000)
 esp=0x80f000;u.mem_write(esp,struct.pack('<'+'I'*(len(args)+1),0x600000,*args))
 if local_e is not None:u.mem_write(esp-14,struct.pack('<h',local_e))
 # A DB38 ferry static link models the original DBA8 caller fields.
 u.mem_write(0x80b000-2,struct.pack('<h',2));u.mem_write(0x80b000-6,struct.pack('<I',edx))
 if frame_setup:
  for off,value,width in frame_setup:u.mem_write(0x80b000+off,struct.pack('<h' if width==2 else '<I',value))
 for reg,value in [(UC_X86_REG_EAX,eax),(UC_X86_REG_EDX,edx),(UC_X86_REG_ECX,ecx),(UC_X86_REG_ESP,esp)]:u.reg_write(reg,value)
 trace=[];rng=[];hits=[];stores=[]
 def hook(uc,address,size,data):
  if address==0x40284c:rng.append(address)
  if address in [0x44d010,0x44cec8,0x44d9a8,0x44cd08,0x44b79c,0x44d174,0x44d734,0x44aee4,0x44b27c,0x44f6d8,0x44dba8]:
   row=dict(function=hex(address),eax=uc.reg_read(UC_X86_REG_EAX),edx=uc.reg_read(UC_X86_REG_EDX),ecx=uc.reg_read(UC_X86_REG_ECX))
   if address==0x44dba8:
    sp=uc.reg_read(UC_X86_REG_ESP);row['entry_local_e']=struct.unpack('<h',uc.mem_read(sp-14,2))[0]
    ret=struct.unpack('<I',uc.mem_read(sp,4))[0];row['return_address']=ret
    if ret in [0x44f40e,0x44f444,0x44f481,0x44f4a8,0x44f4cc]:row['caller_scored_words']=list(struct.unpack('<7h',uc.mem_read(sp+4,14)))
   trace.append(row)
  if address in stop:hits.append(hex(address));uc.emu_stop()
 def write(uc,access,address,size,value,data):
  for actor in [2,4]:
   if address in [0x47c1ec+actor*656,0x47c1ee+actor*656]:stores.append(dict(actor=actor,field='x' if address==0x47c1ec+actor*656 else 'y',value=value&65535))
 u.hook_add(UC_HOOK_CODE,hook);u.hook_add(UC_HOOK_MEM_WRITE,write);u.emu_start(entry,0x600000,count=budget)
 assert hits or u.reg_read(UC_X86_REG_EIP)==0x600000,hex(u.reg_read(UC_X86_REG_EIP))
 final=bytes(u.mem_read(ORIGIN,SIZE))
 assert not rng,'Unexpected RNG call'
 if readonly:assert final==bytes(ram),'Read-only helper changed game RAM'
 return dict(eax=u.reg_read(UC_X86_REG_EAX),out=list(struct.unpack('<2h',u.mem_read(0x80a000,4))),trace=trace,stop=hits,ram=final,
   words=list(struct.unpack('<8h',u.mem_read(0x80a000,16))),frame_goal_after=list(struct.unpack('<2h',u.mem_read(0x80b000-6,4))),coordinate_stores=stores)
def classify(ram,pos):
 out=run(0x44ca30,point(pos),0x80a000,0x80a004,ram=ram)
 return out['words'][0],out['words'][2]&255
