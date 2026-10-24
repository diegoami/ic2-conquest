"""Original garrison/mercenary caller execution with stack-write provenance.

No helper/RNG replacement. All raw RAM, projected SAVs, full traces and hashes
stay private per #187; public rows contain only synthetic scalar observations.
"""
import argparse,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'runs/experiments/navigation187'))
import core as C
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
sys.path.insert(0,str(ROOT/'runs/experiments/fleet174-actions'));from common import project
DATA=ROOT/'runs/experiments/data/run-exp-navigation187-callers';PRIVATE=ROOT/'artifacts/run-exp-navigation187-callers/private'
p=argparse.ArgumentParser();p.add_argument('--version',required=True);options=p.parse_args()
OUT=PRIVATE/('progress-'+options.version);OUT.mkdir(parents=True,exist_ok=False)
ACTOR=2;ARMY=0x47c1ec+ACTOR*656;SPOTS=[0x80f000,0x7fe0f000]
def write(p,value):
 with p.open('x') as f:json.dump(value,f,indent=2)
def keep(p,value):
 with p.open('xb') as f:f.write(value)
from fixtures import history_fixture

def fixture(context,blocked,offers):
 raw,target=history_fixture(context,blocked,offers);r=bytearray(raw)
 for i,pos in zip([0,1,3],[(153,69),(153,70),(153,71)]):C.place_army(r,i,pos,1)
 return bytes(r),target
specs=[dict(context=context,blocked=True,offers=offers,stack_fill=0,stack_top=sp,wall_offset=3) for context in ['garrison-nearest','garrison-capital'] for offers in [False,True] for sp in SPOTS]
write(DATA/('progress-manifest-'+options.version+'.json'),dict(cases=specs,scope='full original F31C on declared generated fixture, no fresh game or native whole-turn parity',preservation='exclusive unique outputs, raw/SAV/full traces/private hashes private; never overwrite/delete measured files'))
rows=[]
with (DATA/('progress-journal-'+options.version+'.jsonl')).open('x') as journal:
 for index,spec in enumerate(specs):
  name=f"{index:03}-{spec['context']}-{'blocked' if spec['blocked'] else 'clear'}-offers{int(spec['offers'])}-fill{spec['stack_fill']}-sp{spec['stack_top']:x}"
  folder=OUT/name;folder.mkdir();raw,target=fixture(spec['context'],spec['blocked'],spec['offers']);keep(folder/'before.ram',raw);keep(folder/'before.SAV',project(raw))
  u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x300000);stack_base=spec['stack_top']&~0xffff;u.mem_map(stack_base,0x10000)
  for va,rp,rs in C.SECTIONS:
   if rs:u.mem_write(va,C.EXE[rp:rp+rs])
  u.mem_write(C.ORIGIN,raw);u.mem_write(stack_base,bytes([spec['stack_fill']])*0x10000);u.mem_write(spec['stack_top'],struct.pack('<I',0x600000));u.reg_write(UC_X86_REG_ESP,spec['stack_top']);u.reg_write(UC_X86_REG_EAX,ACTOR)
  last={};trace=[];entries=[];steps=[];moves=[];rng=[];stops=[];helpers=[]
  def memory(uc,access,address,size,value,user):
   pc=uc.reg_read(UC_X86_REG_EIP)
   if stack_base<=address<stack_base+0x10000:
    event=dict(instruction=hex(pc),address=address,size=size,value=value)
    trace.append(event)
    for b in range(size):last[address+b]=event
   if address in [ARMY,ARMY+2]:steps.append(dict(instruction=hex(pc),field='x' if address==ARMY else 'y',value=value&65535))
   if address==ARMY+6:moves.append(dict(instruction=hex(pc),value=value&65535))
  def code(uc,address,size,user):
   if address==0x40284c:rng.append(address);uc.emu_stop()
   if address in [0x44aee4,0x44b27c]:stops.append(hex(address));uc.emu_stop()
   if address in [0x44ebe8,0x44e84c]:helpers.append(dict(function=hex(address),actor=uc.reg_read(UC_X86_REG_EAX)&65535,return_address=hex(struct.unpack('<I',uc.mem_read(uc.reg_read(UC_X86_REG_ESP),4))[0])))
   if address==0x44dba8:
    sp=uc.reg_read(UC_X86_REG_ESP);slot=sp-14;guard=struct.unpack('<h',uc.mem_read(slot,2))[0];ret=struct.unpack('<I',uc.mem_read(sp,4))[0]
    provenance=[]
    for byte in range(2):
     w=last.get(slot+byte);provenance.append(None if w is None else dict(instruction=w['instruction'],write_size=w['size'],byte_in_write=slot+byte-w['address']))
    entries.append(dict(origin=list(struct.unpack('<2h',uc.mem_read(ARMY,4))),moves_before=struct.unpack('<h',uc.mem_read(ARMY+6,2))[0],actor=uc.reg_read(UC_X86_REG_EAX)&65535,return_address=hex(ret),goal=list(struct.unpack('<2h',struct.pack('<I',uc.reg_read(UC_X86_REG_EDX)))),entry_guard=guard,byte_provenance=provenance))
  u.hook_add(UC_HOOK_MEM_WRITE,memory);u.hook_add(UC_HOOK_CODE,code)
  row=dict(case=name,**spec,requested_target=list(target))
  try:
   u.emu_start(0x44f31c,0x600000,count=5000000)
   assert not rng and not stops and u.reg_read(UC_X86_REG_EIP)==0x600000,(rng,stops,hex(u.reg_read(UC_X86_REG_EIP)))
   after=bytes(u.mem_read(C.ORIGIN,C.SIZE));keep(folder/'after.ram',after);keep(folder/'after.SAV',project(after))
   row.update(complete=True,entries=entries,helpers=helpers,initial_moves=C.short(raw,ARMY+6),endpoint=C.xy(after,ARMY),moves=C.short(after,ARMY+6),coordinate_store_count=len(steps),move_writes=len(moves),original_RNG_calls=0)
  except Exception as e:row.update(complete=False,error=repr(e),entries=entries,helpers=helpers,eip=hex(u.reg_read(UC_X86_REG_EIP)))
  write(folder/'trace.json',dict(stack_writes=trace,movement_stores=steps,move_writes=moves,entries=entries));rows.append(row);journal.write(json.dumps(row)+'\n');journal.flush()
write(DATA/('progress-controls-'+options.version+'.json'),rows)
# Hash manifest stays PRIVATE, never Git/public comments.
write(OUT/'private-hashes.json',[dict(file=p.relative_to(OUT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(OUT.rglob('*')) if p.is_file()])
print(json.dumps(dict(cases=len(rows),complete=sum(r['complete'] for r in rows),first_entries=[dict(case=r['case'],guard=r['entries'][0]['entry_guard'] if r['entries'] else None,endpoint=r.get('endpoint'),moves=r.get('moves')) for r in rows])))
if not all(r['complete'] for r in rows):raise SystemExit(1)
