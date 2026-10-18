"""Original-instruction serialized projections; does not run UI or write a SAV."""
import argparse, hashlib, json, struct, sys
from pathlib import Path
import capstone, pefile, unicorn
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EDX,UC_X86_REG_ECX,UC_X86_REG_ESP,UC_X86_REG_EIP
ROOT=Path(__file__).resolve().parents[3]
EXE=Path('/home/diego/projects/ic2-work/resupply31/wine-aboard/prefix/drive_c/IC2/Imperial Conquest 2 fast rollingsave seed.exe')
UNKNOWN=list(range(0x450,0x46b))+[0x46d,0x491,0x492,0x493]
def i16(b,o):return struct.unpack_from('<h',b,o)[0]
def word(u,o,v):u.mem_write(o,struct.pack('<h',v))
def dword(u,o,v):u.mem_write(o,struct.pack('<I',v))
def layout(b):
 na=i16(b,100956);assert 0<=na<=198
 fo=100958+656*na;nf=i16(b,fo);assert 0<=nf<=200
 no=fo+2+26*nf;news=no+16*1172+600;last=i16(b,news);assert -1<=last<=39
 tail=news+2+61*(last+1);assert tail+55==len(b) and b[tail+54]==0
 return na,fo,nf,no,news,last,tail

def spans(b):
 na,fo,nf,no,news,last,tail=layout(b)
 # Exact writer004484D0 stream order, including trailer and conditional tactical spans below.
 blocks=[('map',0x45e870,89600,0),('cities',0x479590,11356,89600),('army_count',0x4a0324,2,100956),('armies',0x47c1ec,na*656,100958),('fleet_count',0x4a0326,2,fo),('fleets',0x49c26c,nf*26,fo+2),('nations',0x474670,16*1172,no),('mercenaries',0x49da10,600,no+16*1172),('news_last',0x4a031e,2,news),('news_slots',0x49f994,(last+1)*61,news+2),('turn_order',0x49efe8,32,tail),('pending_offer',0x49f008,4,tail+32)]
 for name,at,size,off in [('current_nation',0x4a0320,2,36),('seat',0x4a0322,2,38),('week',0x4a0330,2,40),('year',0x4a0332,2,42),('season',0x4a032e,2,44),('main_geometry',0x4a0338,8,46),('battle_flag',0x4a0b7c,1,54)]:blocks.append((name,at,size,tail+off))
 return blocks

def tax_projection(b,n,t,width,height,scroll_x,scroll_y):
 """Reference typed projection ONLY; caller must establish bound-native/stable-UI contract."""
 if type(n)!=int or not 0<=n<16 or type(t)!=int or not 0<=t<=40:raise ValueError('tax/nation outside original minimal profile')
 if not (271<=width<=1295 and 269<=height<=1005 and 0<=scroll_x<=319 and 0<=scroll_y<=139):raise ValueError('UI profile outside bounded projection')
 na,fo,nf,no,news,last,tail=layout(b);out=bytearray(b)
 s3=(width-15)//32;s4=(height-45)//32
 x=max(0,min(scroll_x,319-s3));y=max(0,min(scroll_y,139-s4))
 for off,value in [(0x44a,t),(0x488,x),(0x486,y)]:struct.pack_into('<h',out,no+n*1172+off,value)
 return bytes(out)

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 exe=EXE.read_bytes();assert hashlib.sha256(exe).hexdigest()=='354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f'
 original=(ROOT/'saves/run0-start-AUTO0720-seed12345.SAV').read_bytes();assert hashlib.sha256(original).hexdigest()=='050bc354f1cbbe374b6a627f06054f2043b9f91a268f6fbfbc18ed1e7e65574c'
 na,fo,nf,no,news,last,tail=layout(original);blocks=spans(original);pe=pefile.PE(data=exe)
 def setup():
  u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x300000);u.mem_map(0x700000,0x10000);u.mem_map(0x800000,0x10000)
  for s in pe.sections:
   if s.SizeOfRawData:u.mem_write(0x400000+s.VirtualAddress,s.get_data())
  for name,at,size,off in blocks:u.mem_write(at,original[off:off+size])
  return u
 def snapshot(u):return b''.join(bytes(u.mem_read(at,size)) for name,at,size,off in blocks)
 def call(u,start,stop=0x600000,eax=0,edx=0,ecx=0):
  dword(u,0x80f000,0x600000);u.reg_write(UC_X86_REG_ESP,0x80f000)
  for reg,v in [(UC_X86_REG_EAX,eax),(UC_X86_REG_EDX,edx),(UC_X86_REG_ECX,ecx)]:u.reg_write(reg,v)
  u.emu_start(start,stop,count=1000000);assert u.reg_read(UC_X86_REG_EIP)==stop
 def writes_for(u,operation):
  events=[]
  def hook(uc,access,at,size,value,ctx):
   for name,lo,length,off in blocks:
    if at<lo+length and lo<at+size:events.append(dict(pc=hex(uc.reg_read(UC_X86_REG_EIP)),block=name,address=hex(at),size=size))
  h=u.hook_add(UC_HOOK_MEM_WRITE,hook);operation();u.hook_del(h);return events
 rows=[];u=setup()
 # Width/height cases cover identity, high clamp, and low clamp. Original viewport getter results are explicit inputs, not an emulated GUI.
 for n in range(16):
  for t in range(41):
   for name,at,size,off in blocks:u.mem_write(at,original[off:off+size])
   word(u,0x4a0320,n);word(u,0x700000+0x1f8,t)
   for nn in range(16):
    for k,o in enumerate(UNKNOWN):u.mem_write(0x474670+nn*1172+o,bytes([(nn*31+k)%255+1]))
   before=snapshot(u)
   events=writes_for(u,lambda:call(u,0x4540b8,0x4540dc,eax=0x700000))
   expected=bytearray(before);struct.pack_into('<h',expected,no+n*1172+0x44a,t)
   assert snapshot(u)==expected and len(events)==1 and events[0]['address']==hex(0x474670+n*1172+0x44a)
   rows.append(dict(case='tax-commit-prefix',nation=n,tax=t,serialized_write_events=events))
 viewport=[]
 for width,height,x,y in [(559,365,55,45),(1295,1005,319,139),(271,269,-3,-4),(559,365,400,200)]:
  u=setup();n=0;dword(u,0x700000+0x1bc,0x701000);dword(u,0x700000+0x1c0,0x702000)
  word(u,0x701100,x);word(u,0x702100,y);dword(u,0x80f000,0x700000);word(u,0x80f004,(width-15)//32);word(u,0x80f006,(height-45)//32)
  u.reg_write(UC_X86_REG_ESP,0x80f000);before=snapshot(u)
  def operation():u.emu_start(0x445d89,0x445e01,count=1000)
  events=writes_for(u,operation);assert u.reg_read(UC_X86_REG_EIP)==0x445e01
  expected=bytearray(before);outx=max(0,min(x,319-(width-15)//32));outy=max(0,min(y,139-(height-45)//32))
  struct.pack_into('<h',expected,no+0x488,outx);struct.pack_into('<h',expected,no+0x486,outy);assert snapshot(u)==expected
  viewport.append(dict(width=width,height=height,scroll_x=x,scroll_y=y,result_x=outx,result_y=outy,serialized_write_events=events))
 # Original rename string conversion and whole parent commit; no UI getter/close function is substituted or executed.
 renames=[]
 for name in ['', 'A', 'Legion VII', 'X'*23]:
  u=setup();at=0x47c1ec;parent=0x700000;idx=0
  u.mem_write(parent+0x1da,bytes(u.mem_read(at,656)));word(u,parent+0x1d4,idx);word(u,parent+0x1d8,i16(original,no+0x442))
  slot=0;assert read_word(u,at+16+slot*32)==0 and read_word(u,at+20+slot*32)>0
  dest=parent+0x1da+16+slot*32+8;u.mem_write(0x702000,name.encode()+b'\0')
  before=snapshot(u);call(u,0x405b88,eax=dest,edx=0x702000)
  events=writes_for(u,lambda:call(u,0x445378,0x4453be,eax=parent))
  expected=bytearray(before);offset=100958+16+slot*32+8;expected[offset:offset+len(name)+1]=name.encode()+b'\0'
  assert snapshot(u)==expected
  assert {r['block'] for r in events}=={'nations','armies'}
  renames.append(dict(name_length=len(name),serialized_write_events_count=len(events),unchanged_mobilization_written_back=True,whole_army_copy_bytes=656,changed_allowed_name_prefix_only=True))
 # Entire strategic stream spans, plus all conditional tactical locations used by writer.
 extra=[('attacker',0x4a0b74,2),('defender',0x4a0b76,2),('battle_aux',0x4a0b78,2),('general',0x4a0b7d,1),('battle_phase',0x4a0b7a,2),('tactical_units',0x4a0344,0x6e0),('tactical_terrain',0x4a0a24,0x150)]
 scratch=[('information_strings',0x49f00c,0x988),('information_last',0x4a031c,2)]
 for name,lo,length in scratch:
  assert all(not(lo<at+size and at<lo+length) for _,at,size,*_ in blocks+extra)
 result=dict(method='Original instruction slices, not full dialog/game execution. Tax prefix stops before RefreshForms; viewport slice executes original min/max callees with explicit getter/scroll inputs; rename converter executes whole, parent commit stops before PostMessage wrapper. Serialized stream snapshots assert every byte outside typed effects unchanged; no source/SAV written.',exe_sha256=hashlib.sha256(exe).hexdigest(),public_save_sha256=hashlib.sha256(original).hexdigest(),unicorn_version=unicorn.__version__,tax_cases=len(rows),tax_records=rows,viewport_cases=viewport,rename_cases=renames,strategic_spans=[dict(name=n,address=hex(at),size=s,file_offset=o) for n,at,s,o in blocks],conditional_tactical_spans=[dict(name=n,address=hex(at),size=s) for n,at,s in extra],scratch_outside_all_serialized_spans=[dict(name=n,address=hex(at),size=s) for n,at,s in scratch],full_UI_callbacks_executed=False,Windows_round_trips=0)
 with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps(dict(tax_cases=len(rows),viewport_cases=len(viewport),rename_cases=len(renames),all_assertions_passed=True)))
def read_word(u,at):return i16(u.mem_read(at,2),0)
if __name__=='__main__':
 try:main()
 except Exception:
  import traceback
  out=Path(sys.argv[sys.argv.index('--output')+1])
  if not out.exists():
   with out.open('x') as f:json.dump(dict(status='error',traceback=traceback.format_exc()),f,indent=2);f.write('\n')
  raise
