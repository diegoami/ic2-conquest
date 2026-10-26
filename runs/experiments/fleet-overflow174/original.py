"""Owner-approved174: original unmodified instruction controls, no live game.
Never overwrite/delete any measurement/input/save. Unique --version required.
Full original RAM/SAV/state/hash/trace private; public scalars only. Diagnostic
SAVs are RAM projections, NOT original Save as or Windows acceptance.
"""
from pathlib import Path
import sys,struct,json,argparse,hashlib,time
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'runs/experiments/strategic-tracks'))
import original_support as old
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from state import sav
A=R/'artifacts/run-exp-fleet-overflow174';D=R/'runs/experiments/data/run-exp-fleet-overflow174'
ARMY=0x47c1ec;FLEET=0x49c26c;MAP=0x45e870;N=0x474670+1172
SITES={0x44b79c:'embark',0x44f8fc:'overflow',0x449f08:'allocate',0x4492c0:'landscan',0x44ac3c:'removeunit',0x44acb4:'moveunit',0x44ab90:'deletearmy',0x44abe0:'compactarmy',0x40284c:'random'}
write=old.write;read=old.read;short=old.short;put=old.put;xy=old.xy
REGS={'eax':UC_X86_REG_EAX,'edx':UC_X86_REG_EDX,'ecx':UC_X86_REG_ECX,'ebx':UC_X86_REG_EBX,'esi':UC_X86_REG_ESI,'edi':UC_X86_REG_EDI,'ebp':UC_X86_REG_EBP,'esp':UC_X86_REG_ESP,'eflags':UC_X86_REG_EFLAGS}

def execute(raw,entry=0x44b79c,variant=0):
 u=old.machine(raw);u.mem_write(0x80f000,struct.pack('<I',0x600000));u.reg_write(UC_X86_REG_ESP,0x80f000)
 for reg in [UC_X86_REG_EBX,UC_X86_REG_ESI,UC_X86_REG_EDI]:u.reg_write(reg,0x12345678 if variant else 0)
 u.reg_write(UC_X86_REG_EBP,0x80e000 if variant else 0);u.reg_write(UC_X86_REG_EFLAGS,0x246 if variant else 0x202)
 u.reg_write(UC_X86_REG_EAX,0);u.reg_write(UC_X86_REG_EDX,5000 if entry==0x44f8fc else 0)
 before={k:u.reg_read(v)for k,v in REGS.items()};calls=[];writes=[]
 def hook(uc,pc,size,unused):
  if pc in SITES:calls.append(dict(site=SITES[pc],address=hex(pc),eax=uc.reg_read(UC_X86_REG_EAX)&65535,edx=uc.reg_read(UC_X86_REG_EDX)&65535))
 def mem(uc,access,addr,size,value,unused):
  if ARMY-656<=addr<ARMY or 0x4a0324<=addr<0x4a0326:writes.append(dict(address=addr,size=size,value=value))
 u.hook_add(UC_HOOK_CODE,hook);u.hook_add(UC_HOOK_MEM_WRITE,mem);u.emu_start(entry,0x600000,count=5000000)
 assert u.reg_read(UC_X86_REG_EIP)==0x600000,hex(u.reg_read(UC_X86_REG_EIP))
 after=bytes(u.mem_read(old.RAM_BASE,old.RAM_SIZE));end={k:u.reg_read(v)for k,v in REGS.items()}
 for k in ['ebx','esi','edi','ebp']:assert before[k]==end[k],k
 assert not any(x['site']=='random'for x in calls)
 assert read(raw,0x45e030,4)==read(after,0x45e030,4)
 return after,dict(cpu_before=before,cpu_after=end,calls=calls,watched_writes=writes)

def unit(r,aid,units,name='U'):
 off=ARMY+656*aid-old.RAM_BASE;r[off:off+656]=bytes(656)
 for k,troops in enumerate(units):
  p=off+16+32*k;struct.pack_into('<4h',r,p,0,k%5,troops,7);label=(name+str(k)).encode();r[p+8:p+8+len(label)]=label

def summary(raw):
 b=old.container(raw);s=sav.parse(b);live=[x for x in s['armies']if x['owner']>=0 and x['troops']>0]
 return dict(turn=s['turn'],raw_army_count=len(s['armies']),live_army_count=len(live),troops=sum(x['troops']for x in live),money=sum(x['money']for x in live),supply=sum(x['supplies']for x in live),carrier_link=s['fleets'][0]['army'],source_owner=s['armies'][0]['owner'],source_troops=s['armies'][0]['troops'],army_records=[dict(id=x['id'],owner=x['owner'],x=x['x'],y=x['y'],troops=x['troops'],money=x['money'],supply=x['supplies'])for x in s['armies'][:4]],city315_name_printable=all(32<=ord(c)<=126 for c in s['cities'][315]['name']))

def save_private(folder,name,raw):
 old.keep(folder/(name+'.ram'),raw);b=old.container(raw);old.keep(folder/(name+'.SAV'),b);write(folder/(name+'.json'),sav.parse(b))

def build(spec,source):
 r=bytearray(source);sea=xy(r,FLEET);src=xy(r,ARMY);put(r,0x4a0320,1);r[N+0x490-old.RAM_BASE]=int(spec.get('human',False))
 # Remove valid active army markers before reconstructing controlled rosters.
 for i in range(short(r,0x4a0324)):
  p=ARMY+i*656;x,y=xy(r,p)
  if short(r,p+8)>=0 and 0<=x<320 and 0<=y<140:put(r,MAP+2*(x*140+y),short(r,p+8))
 terrain=lambda x,y:short(r,MAP+2*(x*140+y))
 sourcecell=terrain(*src);assert 2<=sourcecell<=11
 unit(r,0,spec.get('units',[4000,2000]),'C')
 for off,val in [(0,src[0]),(2,src[1]),(4,1),(6,8),(8,sourcecell),(10,90),(12,100),(14,70)]:put(r,ARMY+off,val)
 put(r,MAP+2*(src[0]*140+src[1]),201);put(r,FLEET+22,-1);put(r,FLEET+12,8);put(r,FLEET+18,10)
 count=1;occupied={tuple(src),tuple(sea)}
 def add(pos,owner=1):
  nonlocal count
  p=ARMY+count*656;x,y=pos;covered=terrain(x,y);assert 2<=covered<=11
  unit(r,count,[3000],f'F{count}-')
  for off,val in [(0,x),(2,y),(4,owner),(6,1),(8,covered),(10,21),(12,23),(14,70)]:put(r,p+off,val)
  put(r,MAP+2*(x*140+y),200+owner);occupied.add((x,y));count+=1
 lands=[(x,y)for x in range(sea[0]-1,sea[0]+2)for y in range(sea[1]-1,sea[1]+2)if 2<=terrain(x,y)<=11]
 if spec.get('block_all_other_land'):
  for pos in lands:add(pos,2 if spec.get('enemy')else 1)
 elif spec.get('existing'):
  add(lands[-1],2 if spec.get('enemy')else 1)
 # Populate genuine passable remote cells for raw-table limits, preserving map consistency.
 for x in range(10,310):
  for y in range(10,130):
   if count>=spec.get('table_count',count):break
   if (x,y)not in occupied and max(abs(x-sea[0]),abs(y-sea[1]))>4 and 2<=terrain(x,y)<=11:add((x,y))
  if count>=spec.get('table_count',count):break
 assert count==spec.get('table_count',count)
 if spec.get('tombstone'):
  p=ARMY+(count-1)*656;x,y=xy(r,p);put(r,MAP+2*(x*140+y),short(r,p+8));put(r,p+4,-1);put(r,p+20,0)
 put(r,0x4a0324,count)
 if spec.get('helper_no_land'):
  # Deliberately non-caller fixture: F8FC entry already aboard, all neighboring
  # terrain replaced bysea. Not a reachable adjacent new-embark comparison.
  put(r,MAP+2*(src[0]*140+src[1]),sourcecell)
  for x in range(sea[0]-1,sea[0]+2):
   for y in range(sea[1]-1,sea[1]+2):put(r,MAP+2*(x*140+y),0)
  put(r,MAP+2*(sea[0]*140+sea[1]),301)
  for off,val in [(0,sea[0]),(2,sea[1]),(8,-1)]:put(r,ARMY+off,val)
  put(r,FLEET+22,0)
 return bytes(r),dict(fleet=sea,source=src,near_land_candidates=lands,controlled_army_count=count)

CASES=[dict(id='free-receiver'),dict(id='vacated-source-only',block_all_other_land=True),dict(id='existing-own',existing=True),dict(id='existing-enemy',existing=True,enemy=True),dict(id='existing-own-source-only',block_all_other_land=True),dict(id='existing-enemy-source-only',block_all_other_land=True,enemy=True),dict(id='raw197',table_count=197),dict(id='raw198',table_count=198),dict(id='raw198-tombstone',table_count=198,tombstone=True),dict(id='raw198-all-overflow',table_count=198,units=[6000]),dict(id='raw198-at-cap',table_count=198,units=[5000]),dict(id='raw198-below-cap',table_count=198,units=[4999]),dict(id='single-all-overflow',units=[6000]),dict(id='human-at-cap',human=True,units=[5000]),dict(id='human-helper-overcap',human=True,units=[6000],not_gui_equivalent=True),dict(id='helper-only-no-land',helper_no_land=True,not_gui_equivalent=True)]

def main():
 p=argparse.ArgumentParser();p.add_argument('--version',required=True);q=p.parse_args();private=A/('private-'+q.version);private.mkdir();write(D/(q.version+'-plan.json'),CASES)
 legacy=R/'artifacts/run-exp-strategic-tracks/fleet-controls-v3/embark-units-4000-2000';raw=(legacy/'before.ram').read_bytes();expected=(legacy/'expected.ram').read_bytes()
 replay,t=execute(raw);assert replay==expected,'old complete RAM baseline differs';write(D/(q.version+'-baseline.json'),dict(legacy='fleet-controls-v3/embark-units-4000-2000',complete_ram_equal=True,original_rng_draws=0,scope='retained synthetic instruction replay, not new game'))
 rows=[]
 for spec in CASES:
  folder=private/spec['id'];folder.mkdir();before,geometry=build(spec,raw);save_private(folder,'before',before)
  try:
   entry=0x44f8fc if spec.get('helper_no_land')else 0x44b79c;after,trace=execute(before,entry);again,trace2=execute(before,entry,1);assert again==after,'register/flags variant changed complete RAM result'
   save_private(folder,'expected',after);write(folder/'instruction-trace.json',trace);write(folder/'variant-trace.json',trace2)
   writes=[dict(city_id=(x['address']-0x479590)//34,city_offset=(x['address']-0x479590)%34,size=x['size'],synthetic_value=x['value'])for x in trace['watched_writes']if ARMY-656<=x['address']<ARMY]
   row=dict(spec=spec,geometry=geometry,before=summary(before),after=summary(after),calls=[x['site']for x in trace['calls']],negative_index_writes=writes,cpu_callee_saved=True,full_ram_register_variant_equal=True,original_rng_draws=0,before_save='before.SAV',expected_save='expected.SAV',save_kind='diagnostic RAM projection, not Original Save as')
   write(D/(q.version+'_'+spec['id']+'.json'),row);rows.append(row);print(spec['id'],row['after']['raw_army_count'],row['after']['troops'],row['negative_index_writes'],flush=True)
  except BaseException as e:write(D/(q.version+'_'+spec['id']+'-failure.json'),dict(type=type(e).__name__,message=str(e)));raise
 write(D/(q.version+'-index.json'),[dict(id=x['spec']['id'],file=q.version+'_'+x['spec']['id']+'.json')for x in rows]);write(private/'hashes.json',{str(p.relative_to(private)):hashlib.sha256(p.read_bytes()).hexdigest()for p in private.rglob('*')if p.is_file()})
if __name__=='__main__':main()
