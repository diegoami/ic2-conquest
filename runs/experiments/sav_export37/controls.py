"""Bounded unmodified original-x86 controls; synthetic residue, no saves written."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EDX,UC_X86_REG_ECX,UC_X86_REG_ESP,UC_X86_REG_EIP
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'patches'))
from battle_hook import sections
P=argparse.ArgumentParser();P.add_argument('--output',type=Path,required=True);a=P.parse_args()
base=ROOT.parent.parent/'resupply31/wine-aboard/prefix/drive_c/IC2';exe=(base/'Imperial Conquest 2 fast rollingsave seed.exe').read_bytes()
assert hashlib.sha256(exe).hexdigest()=='354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f'
save=ROOT/'saves/run0-start-AUTO0720-seed12345.SAV';b=save.read_bytes();i16=lambda raw,o:struct.unpack_from('<h',raw,o)[0]
na=i16(b,100956);fo=100958+656*na;nf=i16(b,fo);no=fo+2+26*nf

def setup():
 u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x300000);u.mem_map(0x700000,0x10000);u.mem_map(0x800000,0x10000)
 for _,va,vs,rp,rs,_ in sections(exe):
  if rs:u.mem_write(va,exe[rp:rp+rs])
 u.mem_write(0x45e870,b[:89600]);u.mem_write(0x479590,b[89600:100956]);u.mem_write(0x47c1ec,b[100958:fo]);u.mem_write(0x49c26c,b[fo+2:no]);u.mem_write(0x474670,b[no:no+16*1172]);word(u,0x4a0324,na);word(u,0x4a0326,nf)
 return u

def word(u,at,v):u.mem_write(at,struct.pack('<h',v))
def read(u,at):return struct.unpack('<h',u.mem_read(at,2))[0]
def call(u,at,eax=0,edx=0,ecx=0):
 u.mem_write(0x80f000,struct.pack('<I',0x600000));u.reg_write(UC_X86_REG_ESP,0x80f000)
 for reg,v in [(UC_X86_REG_EAX,eax),(UC_X86_REG_EDX,edx),(UC_X86_REG_ECX,ecx)]:u.reg_write(reg,v&0xffffffff)
 u.emu_start(at,0x600000,count=2000000)
 assert u.reg_read(UC_X86_REG_EIP)==0x600000 and u.reg_read(UC_X86_REG_ESP)==0x80f004
 return u.reg_read(UC_X86_REG_EAX)

rows=[]
def run(name,fn):
 try:rows.append(dict(case=name,status='pass',**fn()))
 except Exception as exc:rows.append(dict(case=name,status='error',error=repr(exc)))

def city_transfer():
 u=setup();city=read(u,0x4746b8);old=read(u,0x479590+34*city+18);new=(old+1)%16
 counts=[read(u,0x474ab6+n*1172) for n in (old,new)];before=[list(struct.unpack('<334h',u.mem_read(0x4746b8+n*1172,668))) for n in (old,new)]
 call(u,0x44b8f4,city,new)
 after=[list(struct.unpack('<334h',u.mem_read(0x4746b8+n*1172,668))) for n in (old,new)]
 name=lambda c:bytes(u.mem_read(0x479590+34*c,14)).split(b'\0',1)[0]
 expected=sorted(before[1][:counts[1]]+[city],key=name)
 assert after[0][:counts[0]-1]==[v for v in before[0][:counts[0]] if v!=city]
 assert after[0][counts[0]-1]==-1 and after[1][:counts[1]+1]==expected
 assert [read(u,0x474ab6+n*1172) for n in (old,new)]==counts
 return dict(function='0x44b8f4',city=city,old_owner=old,new_owner=new,counts_before=counts,old_prefix_after=after[0][:counts[0]],new_prefix_after=after[1][:counts[1]+1],result='removes with -1 terminator, inserts by original string comparator; caller updates counts/owner separately')
run('city-list-transfer',city_transfer)

def new_army():
 u=setup();at=0x47c1ec+na*656;u.mem_write(at,bytes([0xa5])*656);writes=set()
 def hook(uc,access,address,size,value,ctx):
  for pos in range(address,address+size):
   if at<=pos<at+656:writes.add(pos-at)
 u.hook_add(UC_HOOK_MEM_WRITE,hook)
 xy=struct.unpack('<I',u.mem_read(0x479590+85*34+14,4))[0];call(u,0x449f08,0,xy,0x700000)
 assert read(u,0x700000)==na and read(u,0x4a0324)==na+1
 raw=bytes(u.mem_read(at,656));expected=set(range(16))|{16+k*32+j for k in range(20) for j in (2,3,4,5)}
 assert writes==expected
 assert all(raw[j]==0xa5 for j in range(656) if j not in writes)
 return dict(function='0x449f08',new_index=na,header_words=list(struct.unpack('<8h',raw[:16])),written_offsets=sorted(writes),retained_synthetic_bytes=656-len(writes),result='only header and type/troop words initialized; origin/quality/names untouched')
run('new-army-residue',new_army)

def army_capacity():
 u=setup();word(u,0x4a0324,198);call(u,0x449f08,0,0x002b0066,0x700000)
 assert read(u,0x700000)==-1 and read(u,0x4a0324)==198
 return dict(function='0x449f08',count=198,returned_index=-1)
run('new-army-capacity',army_capacity)

def new_fleet():
 u=setup();at=0x49c26c+nf*26;u.mem_write(at,bytes([0xa5])*26);before=struct.unpack('<i',u.mem_read(0x474aa8,4))[0];writes=set()
 def hook(uc,access,address,size,value,ctx):
  for pos in range(address,address+size):
   if at<=pos<at+26:writes.add(pos-at)
 u.hook_add(UC_HOOK_MEM_WRITE,hook);call(u,0x44a004,0,85,30)
 assert read(u,0x4a0326)==nf+1 and writes==set(range(8,12))|set(range(18,24))
 after=struct.unpack('<i',u.mem_read(0x474aa8,4))[0];assert after==before-300
 return dict(function='0x44a004',new_index=nf,written_offsets=sorted(writes),retained_synthetic_bytes=26-len(writes),initialized_words={str(o):read(u,at+o) for o in [8,10,18,20,22]},treasury_before=before,treasury_after=after,result='construction record only; positions/destination/moves/supply/money/cell retain residue')
run('new-fleet-residue',new_fleet)

def remove_army():
 u=setup();at=0x47c1ec;before=bytes(u.mem_read(at,656));assert read(u,at+8)>=0;call(u,0x44ab90,0);after=bytes(u.mem_read(at,656));changed=[i for i,(x,y) in enumerate(zip(before,after)) if x!=y]
 assert changed==[4,5] and read(u,at+4)==-1
 return dict(function='0x44ab90',changed_record_bytes=changed,result='only owner becomes -1; other record bytes retained; covered map cell restored')
run('army-tombstone',remove_army)

def compact_army():
 u=setup();last=bytes(u.mem_read(0x47c1ec+(na-1)*656,656));word(u,0x49c282,na-1);call(u,0x44abe0,0)
 assert bytes(u.mem_read(0x47c1ec,656))==last and read(u,0x4a0324)==na-1 and read(u,0x49c282)==0
 return dict(function='0x44abe0',old_last_index=na-1,new_index=0,full_record_copy=True,fleet_army_reference_after=0,result='whole last army copied over removed index and fleet carrier reference rewritten')
run('army-relocation',compact_army)

def compact_fleet():
 u=setup();last=bytes(u.mem_read(0x49c26c+(nf-1)*26,26));call(u,0x44ad7c,0)
 assert bytes(u.mem_read(0x49c26c,26))==last and read(u,0x4a0326)==nf-1
 return dict(function='0x44ad7c',old_last_index=nf-1,new_index=0,full_record_copy=True,result='full last fleet copied and count reduced; no army fleet-index field exists in saved army header')
run('fleet-relocation',compact_fleet)

def copy_text():
 u=setup();u.mem_write(0x700000,bytes([0xa5])*32);u.mem_write(0x700100,b'Hi\0');call(u,0x405b00,0x700000,0x700100);raw=bytes(u.mem_read(0x700000,32));assert raw[:3]==b'Hi\0' and raw[3:]==bytes([0xa5])*29
 return dict(function='0x405b00',text='Hi',written_bytes=3,retained_synthetic_bytes=29,result='unbounded NUL copy leaves trailing residue')
run('text-residue',copy_text)

def finders():
 u=setup();xy=0x00310066
 for i in range(2):u.mem_write(0x47c1ec+656*i,struct.pack('<I',xy));word(u,0x47c1f0+656*i,0)
 assert call(u,0x449920,xy)==0
 word(u,0x47c1f0,-1);assert call(u,0x449920,xy)==1
 for i in range(2):u.mem_write(0x49c26c+26*i,struct.pack('<I',xy));word(u,0x49c274+26*i,0)
 assert call(u,0x449970,xy)==0
 word(u,0x49c274,-1);assert call(u,0x449970,xy)==1
 return dict(functions=['0x449920','0x449970'],first_live_match=0,after_first_tombstoned=1,result='strategic coordinate finders choose FIRST live match, not encoded map index; preserve order or reject ambiguous overlap')
run('strategic-finder-order',finders)

def markers():
 u=setup();word(u,0x47c1f0,3);word(u,0x47c1f4,2);u.mem_write(0x47c1ec,struct.pack('<hh',100,50));army=[]
 for troops in [24999,25000,49999,50000]:
  for k in range(20):word(u,0x47c200+32*k,0)
  word(u,0x47c200,min(25000,troops));word(u,0x47c220,max(0,troops-25000));call(u,0x44a80c,0)
  value=read(u,0x45e870+100*280+50*2);assert value==3+(200 if troops<25000 else 216 if troops<50000 else 232);army.append(dict(troops=troops,marker=value))
 u.mem_write(0x49c26c,struct.pack('<hh',101,50));word(u,0x49c274,3);fleet=[]
 for ships in [24,25,49,50]:
  word(u,0x49c27e,ships);call(u,0x44a878,0);value=read(u,0x45e870+101*280+50*2);assert value==3+(300 if ships<25 else 316 if ships<50 else 332);fleet.append(dict(ships=ships,marker=value))
 return dict(functions=['0x44a80c','0x44a878'],army=army,fleet=fleet,result='map codes contain owner and size band, not pointer/index')
run('map-marker-boundaries',markers)

record=dict(provenance='Separate original-x86 controls, no code patches/stubs or live Wine/Windows execution. Synthetic 0xA5 residue is deliberately not an export prototype. No SAV files emitted.',exe_sha256=hashlib.sha256(exe).hexdigest(),input_save=save.name,input_sha256=hashlib.sha256(b).hexdigest(),runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),records=rows)
with a.output.open('x') as out:json.dump(record,out,indent=2);out.write('\n')
print(json.dumps(dict(passed=sum(r['status']=='pass' for r in rows),errors=[r for r in rows if r['status']!='pass'])))
