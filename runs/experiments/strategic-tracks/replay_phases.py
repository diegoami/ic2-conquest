"""Actual original phase replay/draw ledger, gated on complete captured exit RAM.

No helper or RNG is replaced. These are conditional replays of observed entry
states, not a native full-turn comparison. Every output uses exclusive creation.
"""
import hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'runs/experiments/fleet174-actions'))
from common import machine,project,RAM_BASE,RAM_SIZE,short
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
sys.path.insert(0,str(ROOT));from state import sav
BASE=ROOT/'artifacts/run-exp-strategic-tracks';DATA=ROOT/'runs/experiments/data/run-exp-strategic-tracks'
OUT=BASE/'phase-replay-v1';OUT.mkdir(exist_ok=False)
meta=json.loads((DATA/'ST-rom-hook-v1/phase-records.json').read_text());rows=[]
entries={'diplomacy':0x44fb7c,'economy':0x44ffbc,'fleet':0x44f608}
regs=[UC_X86_REG_EDI,UC_X86_REG_ESI,UC_X86_REG_EBP,UC_X86_REG_EBX,UC_X86_REG_EDX,UC_X86_REG_ECX,UC_X86_REG_EAX]
def write(p,value):
 with p.open('x') as f:json.dump(value,f,indent=2)
def keep(p,value):
 with p.open('xb') as f:f.write(value)
for index in range(0,len(meta),2):
 a,b=meta[index:index+2];assert a['kind']==0 and b['kind']==1 and (a['phase'],a['nation'])==(b['phase'],b['nation'])
 before=(BASE/'live/ST-rom-hook-v1/snapshots'/f'{index:03}.ram').read_bytes();expected=(BASE/'live/ST-rom-hook-v1/snapshots'/f'{index+1:03}.ram').read_bytes()
 folder=OUT/f'{index:03}-{a["phase"]}-{a["nation"]}';folder.mkdir()
 for label,raw in [('before',before),('expected',expected)]:
  container=bytearray(project(raw));parsed=sav.parse(container);container[parsed['tail_off']:parsed['tail_off']+32]=raw[0x49efe8-RAM_BASE:0x49efe8-RAM_BASE+32]
  keep(folder/(label+'.SAV'),container);write(folder/(label+'.json'),sav.parse(container))
 u=machine(before);u.mem_write(0x80f000,struct.pack('<I',0x600000));u.reg_write(UC_X86_REG_ESP,0x80f000)
 for reg,value in zip(regs,[a['registers'][k] for k in [0,1,2,4,5,6,7]]):u.reg_write(reg,value)
 u.reg_write(UC_X86_REG_EFLAGS,a['flags']);draws=[];pending=[];calls=[]
 def seed(uc):return struct.unpack('<I',uc.mem_read(0x45e030,4))[0]
 def hook(uc,address,size,user):
  if pending and address==pending[-1]['return_address']:
   r=pending.pop();result=uc.reg_read(UC_X86_REG_EAX);assert 0<=result<r['bound'];r.update(result=result,seed_after=seed(uc));draws.append(r)
  if address==0x40284c:
   sp=uc.reg_read(UC_X86_REG_ESP);ret=struct.unpack('<I',uc.mem_read(sp,4))[0]
   pending.append(dict(bound=uc.reg_read(UC_X86_REG_EAX),seed_before=seed(uc),return_address=ret))
  if address in [0x4504f4,0x4502e0,0x4501f4,0x450768,0x450858,0x4509f0,0x450b30,0x449b40]:calls.append(dict(function=hex(address),eax=uc.reg_read(UC_X86_REG_EAX),edx=uc.reg_read(UC_X86_REG_EDX),ecx=uc.reg_read(UC_X86_REG_ECX)))
 u.hook_add(UC_HOOK_CODE,hook);row=dict(index=index,phase=a['phase'],nation=a['nation'],draws=draws,decision_calls=calls)
 try:
  u.emu_start(entries[a['phase']],0x600000,count=50000000);assert u.reg_read(UC_X86_REG_EIP)==0x600000 and not pending
  actual=bytes(u.mem_read(RAM_BASE,RAM_SIZE));diff=[i for i,(x,y) in enumerate(zip(actual,expected)) if x!=y]
  keep(folder/'replayed.ram',actual);row.update(complete=True,whole_captured_RAM_equal=not diff,differing_bytes=len(diff),first_difference_addresses=[hex(RAM_BASE+i) for i in diff[:10]],seed_before=a['seed'],seed_after=seed(u),expected_seed_after=b['seed'])
 except Exception as e:row.update(complete=False,error=repr(e),eip=hex(u.reg_read(UC_X86_REG_EIP)))
 rows.append(row);write(folder/'replay.json',row)
write(DATA/'phase-replay-v1.json',rows)
summary=dict(phases=len(rows),complete=sum(r['complete'] for r in rows),whole_RAM_matches=sum(r.get('whole_captured_RAM_equal',False) for r in rows),draws=sum(len(r['draws']) for r in rows))
write(DATA/'phase-replay-summary-v1.json',summary);print(json.dumps(summary))
if not all(r.get('whole_captured_RAM_equal',False) for r in rows):raise SystemExit(1)
