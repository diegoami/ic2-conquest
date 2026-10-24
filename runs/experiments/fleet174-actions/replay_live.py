"""Replay every actually observed original fleet phase and compare exit RAM.

No game/presentation/RNG helper is replaced. Compare original runtime fields,
not the call's transient stack or the observer's separate scratch buffers.
"""
import json,struct
from common import *
from unicorn.x86_const import *
OUT=BASE/'live-phase-replay-v1';OUT.mkdir(exist_ok=False)
folder=BASE/'live/live-rom-hook-v1';meta=json.loads((DATA/'live-rom-hook-v1/phase-records.json').read_text())
assert len(meta)==30 and all(meta[i]['kind']==i%2 for i in range(30))
rows=[]
for index in range(0,len(meta),2):
 start=meta[index];end=meta[index+1];assert start['nation']==end['nation']
 before=(folder/'snapshots'/f'{index:03}.ram').read_bytes();expected=(folder/'snapshots'/f'{index+1:03}.ram').read_bytes()
 u=machine(before);u.mem_write(0x80f000,struct.pack('<I',0x600000));u.reg_write(UC_X86_REG_ESP,0x80f000)
 for reg,value in zip([UC_X86_REG_EDI,UC_X86_REG_ESI,UC_X86_REG_EBP,UC_X86_REG_EBX,UC_X86_REG_EDX,UC_X86_REG_ECX,UC_X86_REG_EAX],[start['registers'][k] for k in [0,1,2,4,5,6,7]]):u.reg_write(reg,value)
 u.reg_write(UC_X86_REG_EFLAGS,start['flags'])
 row=dict(nation=start['nation'],before_record=index,after_record=index+1)
 try:
  u.emu_start(0x44f608,0x600000,count=50000000)
  assert u.reg_read(UC_X86_REG_EIP)==0x600000,hex(u.reg_read(UC_X86_REG_EIP))
  actual=bytes(u.mem_read(RAM_BASE,RAM_SIZE));diff=[i for i,(x,y) in enumerate(zip(actual,expected)) if x!=y]
  row.update(complete=True,whole_captured_RAM_equal=not diff,differing_bytes=len(diff),first_difference_addresses=[hex(RAM_BASE+i) for i in diff[:12]])
  with (OUT/f'{index:03}-replayed.ram').open('xb') as f:f.write(actual)
 except Exception as e:row.update(complete=False,error=repr(e),eip=hex(u.reg_read(UC_X86_REG_EIP)))
 rows.append(row)
with (DATA/'live-phase-replay-v1.json').open('x') as f:json.dump(rows,f,indent=2)
print(json.dumps(dict(phases=len(rows),complete=sum(r['complete'] for r in rows),whole_RAM_matches=sum(r.get('whole_captured_RAM_equal',False) for r in rows))))
if not all(r.get('whole_captured_RAM_equal',False) for r in rows):raise SystemExit(1)
