"""Execute actual original movement/phase. Stop before naval combat only.

No game helper, Random, movement, contact gate or presentation routine stubbed.
Failures retain complete diagnostics; no automatic retry or overwrite.
"""
import argparse,json,struct,traceback
from common import *
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EDX,UC_X86_REG_ESP,UC_X86_REG_EIP
p=argparse.ArgumentParser();p.add_argument('--version',default='v1');a=p.parse_args()
OUT=BASE/('original-'+a.version);OUT.mkdir(exist_ok=False)
manifest=json.loads((DATA/'case-manifest-v1.json').read_text());rows=[]
for spec in manifest['cases']:
 name=spec['name'];r=(BASE/'inputs-v1'/name/'input.ram').read_bytes();u=machine(r);esp=0x80f000
 u.mem_write(esp,struct.pack('<I',0x600000));u.reg_write(UC_X86_REG_ESP,esp)
 if spec['kind']=='human-walk':
  goal=spec['goal'];u.reg_write(UC_X86_REG_EAX,0);u.reg_write(UC_X86_REG_EDX,goal[0]|goal[1]<<16);entry=0x44e094
 else:entry=0x44f608
 row=dict(case=name,status='running',movement_calls=[],coordinate_stores=[],move_writes=[],cargo_stores=[],draws=[]);pending=[];before=[]
 folder=OUT/name;folder.mkdir()
 def state():
  return bytes(u.mem_read(RAM_BASE,RAM_SIZE))
 def hook(uc,address,size,data):
  if pending and address==pending[-1]['return']:
   item=pending.pop();item.update(result=uc.reg_read(UC_X86_REG_EAX),seed_after=struct.unpack('<I',uc.mem_read(0x45e030,4))[0]);row['draws'].append(item)
  if address==0x40284c:
   ret=struct.unpack('<I',uc.mem_read(uc.reg_read(UC_X86_REG_ESP),4))[0]
   pending.append(dict(bound=uc.reg_read(UC_X86_REG_EAX),return_=ret,seed_before=struct.unpack('<I',uc.mem_read(0x45e030,4))[0]));pending[-1]['return']=pending[-1].pop('return_')
  if address==0x44e1fc:
   fleet=uc.reg_read(UC_X86_REG_EAX)&65535;goal=list(struct.unpack('<2h',struct.pack('<I',uc.reg_read(UC_X86_REG_EDX))))
   row['movement_calls'].append(dict(fleet=fleet,goal=goal,origin=list(struct.unpack('<2h',uc.mem_read(0x49c26c+26*fleet,4))),moves=struct.unpack('<h',uc.mem_read(0x49c26c+26*fleet+12,2))[0]))
   if fleet==0 and not before:before.append(state())
  if address==0x44b5d0:row['status']='stopped-before-naval-combat';uc.emu_stop()
 def write(uc,access,address,size,value,data):
  if address in [0x49c26c,0x49c26e]:row['coordinate_stores'].append(dict(field='x' if address==0x49c26c else 'y',value=value&65535,instruction=hex(uc.reg_read(UC_X86_REG_EIP))))
  if address==0x49c278:row['move_writes'].append(dict(value=value&65535,instruction=hex(uc.reg_read(UC_X86_REG_EIP))))
  if address in [0x47c1ec+3*656,0x47c1ee+3*656]:row['cargo_stores'].append(dict(field='x' if address==0x47c1ec+3*656 else 'y',value=value&65535))
 u.hook_add(UC_HOOK_CODE,hook);u.hook_add(UC_HOOK_MEM_WRITE,write)
 try:
  u.emu_start(entry,0x600000,count=50000000)
  if row['status']=='running':
   assert u.reg_read(UC_X86_REG_EIP)==0x600000,hex(u.reg_read(UC_X86_REG_EIP));row['status']='complete'
  assert not pending
 except Exception:row['status']='error';row['error']=traceback.format_exc();row['eip']=hex(u.reg_read(UC_X86_REG_EIP))
 end=state();start=before[0] if before else r
 for stem,body in [('before',start),('after',end)]:
  with (folder/(stem+'.ram')).open('xb') as f:f.write(body)
  b=project(body)
  with (folder/(stem+'.SAV')).open('xb') as f:f.write(b)
  with (folder/(stem+'.json')).open('x') as f:json.dump(sav.parse(b),f)
 row.update(final_fleet0=struct.unpack('<13h',read(end,0x49c26c,26)),final_army3=struct.unpack('<8h',read(end,0x47c1ec+3*656,16)),
   stored_route=xy(end,0x49c270),native_direct_goal=spec.get('goal') if spec['kind']=='human-walk' else next((c['goal'] for c in row['movement_calls'] if c['fleet']==0),None),
   native_input_boundary='original first fleet0 destination call after automatic prepass/selection' if before else 'declared input (no phase move, or low-level human walk)')
 with (folder/'result.json').open('x') as f:json.dump(row,f,indent=2)
 rows.append(row);print(json.dumps(dict(case=name,status=row['status'],xy=row['final_fleet0'][:2],moves=row['final_fleet0'][6],steps=len(row['coordinate_stores'])//2)),flush=True)
with (DATA/('original-actions-'+a.version+'.json')).open('x') as f:json.dump(rows,f,indent=2)
if any(r['status']=='error' for r in rows):raise SystemExit(1)
