"""Synthetic original-x86 controls. No process, game, save or private input writes."""
import argparse, hashlib, json, struct, sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EDX, UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP
import unicorn
ROOT = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ROOT/'patches'))
from battle_hook import sections
p=argparse.ArgumentParser(); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
exe_path=Path('/home/diego/projects/ic2-work/resupply31/wine-aboard/prefix/drive_c/IC2/Imperial Conquest 2 fast rollingsave seed.exe')
exe=exe_path.read_bytes(); exe_hash=hashlib.sha256(exe).hexdigest()
assert exe_hash=='354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f'
save=ROOT/'saves/run0-start-AUTO0720-seed12345.SAV'; b=save.read_bytes()
i16=lambda raw,o:struct.unpack_from('<h',raw,o)[0]
na=i16(b,100956); fo=100958+656*na; nf=i16(b,fo); no=fo+2+26*nf
UNKNOWN=list(range(0x450,0x46b))+[0x46d,0x491,0x492,0x493]
def word(u,at,v):u.mem_write(at,struct.pack('<h',v))
def read(u,at):return i16(u.mem_read(at,2),0)
def setup():
 u=Uc(UC_ARCH_X86,UC_MODE_32)
 for at,size in [(0x400000,0x300000),(0x700000,0x10000),(0x800000,0x10000)]:u.mem_map(at,size)
 for _,va,vs,rp,rs,_ in sections(exe):
  if rs:u.mem_write(va,exe[rp:rp+rs])
 for at,raw in [(0x45e870,b[:89600]),(0x479590,b[89600:100956]),(0x47c1ec,b[100958:fo]),(0x49c26c,b[fo+2:no]),(0x474670,b[no:no+16*1172])]:u.mem_write(at,raw)
 word(u,0x4a0324,na);word(u,0x4a0326,nf)
 return u

def call(u,at,eax=0,edx=0,ecx=0):
 u.mem_write(0x80f000,struct.pack('<I',0x600000));u.reg_write(UC_X86_REG_ESP,0x80f000)
 for reg,v in [(UC_X86_REG_EAX,eax),(UC_X86_REG_EDX,edx),(UC_X86_REG_ECX,ecx)]:u.reg_write(reg,v&0xffffffff)
 u.emu_start(at,0x600000,count=2000000)
 assert u.reg_read(UC_X86_REG_EIP)==0x600000 and u.reg_read(UC_X86_REG_ESP)==0x80f004

def observe(u,operation,positive=False):
 # Every unknown byte in every nation gets a distinct nonzero synthetic canary.
 expected={0x474670+n*1172+o:bytes([(n*31+k)%255+1]) for n in range(16) for k,o in enumerate(UNKNOWN)}
 for at,value in expected.items():u.mem_write(at,value)
 events=[]
 def hook(uc,access,address,size,value,ctx):
  hits=[at for at in range(address,address+size) if at in expected]
  if hits:events.append(dict(pc=hex(uc.reg_read(UC_X86_REG_EIP)),access=access,address=hex(address),size=size,unknown_bytes=[hex(at) for at in hits]))
 handle=u.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,hook)
 operation();u.hook_del(handle)
 preserved=all(bytes(u.mem_read(at,1))==value for at,value in expected.items())
 if positive:
  assert events and not preserved and len({e['access'] for e in events})==2
 else:
  assert not events and preserved
 return dict(unknown_canaries=496,unknown_reads_writes=events,all_canaries_preserved=preserved)

rows=[]
def run(name,fn):
 try:rows.append(dict(case=name,status='pass',**fn()))
 except Exception as exc:rows.append(dict(case=name,status='error',error=repr(exc)))

def city():
 u=setup();city=read(u,0x4746b8);old=read(u,0x479590+34*city+18);new=(old+1)%16
 historical=[bytes(u.mem_read(0x474670+n*1172+o,s)) for n in range(16) for o,s in [(0x434,4),(0x43c,4),(0x448,2)]]
 result=observe(u,lambda:call(u,0x44b8f4,city,new))
 assert historical==[bytes(u.mem_read(0x474670+n*1172+o,s)) for n in range(16) for o,s in [(0x434,4),(0x43c,4),(0x448,2)]]
 return dict(function='0044b8f4',city=city,old_owner=old,new_owner=new,historical_baselines_preserved=True,scope='list helper only; not complete transfer or gameplay',**result)
run('city-list-helper-unknown-and-history',city)

def constructor():
 u=setup();at=0x47c1ec+na*656;u.mem_write(at,b'\xa5'*656)
 xy=struct.unpack('<I',u.mem_read(0x479590+85*34+14,4))[0]
 result=observe(u,lambda:call(u,0x449f08,0,xy,0x700000))
 assert read(u,0x700000)==na
 return dict(function='00449f08',scope='one successful army constructor at public start city85',**result)
run('army-constructor-unknown',constructor)

def slot_remove(last):
 u=setup();base=0x47c1ec+16
 # Two live slots with different historic name tails; all later troop words empty.
 for k in range(20):word(u,base+32*k+4,0)
 first=struct.pack('<4h',0,1,1234,80)+b'A\0'+b'X'*22
 second=struct.pack('<4h',1,2,2345,90)+b'B\0'+b'Y'*22
 u.mem_write(base,first+second)
 result=observe(u,lambda:call(u,0x44ac3c,0,1 if last else 0))
 assert bytes(u.mem_read(base,32))==(first if last else second)
 expected=second[:4]+b'\0\0'+second[6:]
 assert bytes(u.mem_read(base+32,32))==expected
 return dict(function='0044ac3c',removed_slot=1 if last else 0,remaining_slot_full_copy=not last,inactive_last_retains_origin_type_quality_and_text=True,inactive_last_changed_offsets=[4,5],scope='two contiguous live slots, remove one; no assertion on every gameplay caller',**result)
run('remove-last-unit-retains-residue',lambda:slot_remove(True))
run('remove-first-unit-moves-residue',lambda:slot_remove(False))

def rename():
 u=setup();left=b'old\0'+b'X'*20;right=b'old\0'+b'Y'*20
 u.mem_write(0x700000,left);u.mem_write(0x700100,right);u.mem_write(0x700200,b'Hi\0')
 for dest in [0x700000,0x700100]:call(u,0x405b00,dest,0x700200)
 l=bytes(u.mem_read(0x700000,24));r=bytes(u.mem_read(0x700100,24))
 assert l[:3]==r[:3]==b'Hi\0' and l[3:]==left[3:] and r[3:]==right[3:] and l!=r
 return dict(function='00405b00',same_visible_input='old',same_visible_output='Hi',buffers_differ_after_same_rename=True,trailing_bytes_retained=21,scope='24-byte synthetic buffers; no universal field/message safety proof')
run('normalized-text-cannot-recover-lineage',rename)

def positive_hook():
 u=setup()
 # Original StrCopy reads a one-byte canary then NUL, writes both to another unknown region.
 def operation():
  u.mem_write(0x474670+0x451,b'\0')
  call(u,0x405b00,0x474670+1172+0x450,0x474670+0x450)
 return dict(function='00405b00',scope='deliberately routed synthetic pointer alias into unknown bytes; instrumentation positive control only',**observe(u,operation,positive=True))
run('unknown-read-write-hook-positive-control',positive_hook)

record=dict(exe_path=str(exe_path),exe_sha256=exe_hash,public_save=save.name,public_save_sha256=hashlib.sha256(b).hexdigest(),unicorn_version=unicorn.__version__,method='Unmodified original x86 helpers, synthetic memory only, with read/write hooks over all 496 unknown nation bytes. No game/Wine/Windows or SAV output. No universal alias inference.',records=rows)
with a.output.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(dict(cases=len(rows),passed=sum(r['status']=='pass' for r in rows),errors=[r for r in rows if r['status']!='pass'])))
if any(r['status']!='pass' for r in rows):raise SystemExit(1)
