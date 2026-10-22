"""Execute original pure threat helper on observed model inputs; this is local rule evidence, not a full original replay."""
import argparse,hashlib,json,struct,sys,datetime
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'patches'))
from battle_hook import sections
p=argparse.ArgumentParser();p.add_argument('--exe',type=Path,required=True);p.add_argument('--dat',type=Path,required=True);p.add_argument('--phases',type=Path,required=True);a=p.parse_args()
raw=a.exe.read_bytes();dat=a.dat.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f'
assert hashlib.sha256(dat).hexdigest()=='94d0ccfc67148d727de4c4e60aefc3c53ba9e67775bd689f0fcb2e23c12e5fbd'
u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x300000);u.mem_map(0x800000,0x100000)
for _,va,vsize,rptr,rsize,_ in sections(raw):
 if rsize:u.mem_write(va,raw[rptr:rptr+rsize])
u.mem_write(0x47946c,dat[0x1f7a6:0x1f7a6+50]);u.mem_write(0x478fb0,dat[0x1f2f0:0x1f2f0+200])
names=['x','y','origin','type','troops','quality','morale','moves','shots','target'];observed={}
def hook(u,address,size,data):
 if address==0x43a8af:
  bp=u.reg_read(UC_X86_REG_EBP);observed.update(keys=list(struct.unpack('<20i',u.mem_read(bp-0x94,80))),order=list(struct.unpack('<20h',u.mem_read(bp-0x44,40))))
u.hook_add(UC_HOOK_CODE,hook,begin=0x43a8af,end=0x43a8af)
def run(slots,grid,slot):
 for i,s in enumerate(slots):u.mem_write(0x4a0344+44*i,struct.pack('<10h',*[s[n] for n in names])+bytes(24))
 u.mem_write(0x4a0a24,struct.pack('<168h',*grid));u.mem_write(0x45e6ac,struct.pack('<h',20 if slot<20 else 0));u.mem_write(0x45e6ae,struct.pack('<h',0 if slot<20 else 20))
 u.mem_write(0x8ff000,struct.pack('<I',0x600000));u.reg_write(UC_X86_REG_ESP,0x8ff000);u.reg_write(UC_X86_REG_EAX,slot);u.reg_write(UC_X86_REG_EDX,0x8ffe00)
 observed.clear();u.emu_start(0x43a718,0x600000,count=1000000);assert u.reg_read(UC_X86_REG_EIP)==0x600000
 return dict(observed,aim=list(struct.unpack('<2h',u.mem_read(0x8ffe00,4))))
rows=[]
for path in sorted(a.phases.glob('*_hook.json')):
 d=json.loads(path.read_text());stage=d['stages'][2]
 for unit in stage['units']:
  slot=unit['slot'];s=unit['before']['slots'][slot]
  if s['moves']<=0 or s['target']>=0:continue
  # Each per-unit view must include its contemporaneous grid; refuse a stage-start grid substitute.
  if 'grid' not in unit['before']:raise ValueError('Observer per-unit grid missing; no substituted grid permitted')
  result=run(unit['before']['slots'],unit['before']['grid'],slot)
  decisions=unit['decisions'];portaim=[decisions[0]['x'],decisions[0]['y']] if decisions else [-1,-1]
  rows.append(dict(trial=d['trial'],counter=d['counter'],actor=slot,input_is_model_phase=True,original=result,port_aim=portaim,port_order=unit['threat_order'],aim_differs=result['aim']!=portaim))
# Original pass 2 on each contemporaneous model stage input. Refuse any shot/UI path.
pass_two=[]
for path in sorted(a.phases.glob('*_hook.json')):
 d=json.loads(path.read_text())
 for stage in (d['stages'][i] for i in [1,3,5]):
  before=stage['before'];side=d['initial']['side_to_move']
  for i,s in enumerate(before['slots']):u.mem_write(0x4a0344+44*i,struct.pack('<10h',*[s[n] for n in names])+bytes(24))
  u.mem_write(0x4a0a24,struct.pack('<168h',*before['grid']));u.mem_write(0x45e6ac,struct.pack('<h',20 if side==0 else 0));u.mem_write(0x45e6ae,struct.pack('<h',0 if side==0 else 20))
  u.mem_write(0x8ff000,struct.pack('<I',0x600000));u.reg_write(UC_X86_REG_ESP,0x8ff000)
  stopped=[]
  def stop_shot(uc,address,size,data):stopped.append(uc.reg_read(UC_X86_REG_EAX)&65535);uc.emu_stop()
  h=u.hook_add(UC_HOOK_CODE,stop_shot,begin=0x43910c,end=0x43910c)
  u.emu_start(0x43a544,0x600000,count=1000000);u.hook_del(h)
  if stopped:pass_two.append(dict(trial=d['trial'],stage=stage['stage'],status='not evaluated: stopped before original shot',actor=stopped[0]));continue
  assert u.reg_read(UC_X86_REG_EIP)==0x600000
  targets=[struct.unpack('<h',u.mem_read(0x4a0344+44*i+18,2))[0] for i in range(40)]
  differences=[dict(actor=i,original_target=t,port_target=stage['after']['slots'][i]['target']) for i,t in enumerate(targets) if t!=stage['after']['slots'][i]['target']]
  pass_two.append(dict(trial=d['trial'],stage=stage['stage'],status='pure original pass completed',original_targets=targets,differences=differences))
# Minimal selection-sort tie example, same type/quality/morale so keys follow troops.
slots=[dict(zip(names,[0,0,0,0,0,0,0,0,0,-1])) for _ in range(40)]
slots[0].update(x=5,y=5,troops=3000,quality=1,morale=100)
for k,t in enumerate([3000,2000,2000,1000]):slots[20+k].update(x=5+k,y=6,troops=t,quality=1,morale=100)
minimal=run(slots,[50]*168,0);assert minimal['order'][:4]==[23,21,22,20]
for k in range(40):slots[k]=dict(zip(names,[0,0,0,0,0,0,0,0,0,-1]))
slots[0].update(x=5,y=5,troops=3000,quality=1,morale=100,moves=1)
slots[20].update(x=5,y=6,type=2,troops=3000,quality=1,morale=100,shots=1)
slots[21].update(x=6,y=6,type=0,troops=1000,quality=1,morale=100)
archer_subject=run(slots,[50]*168,0);assert archer_subject['order'][:2]==[21,20]
# Minimal flank tie: equal-Y enemies count against the original's below balance.
for k in range(40):slots[k]=dict(zip(names,[0,0,0,0,0,0,0,0,0,-1]))
slots[0].update(x=5,y=5,type=1,troops=3000,quality=5,morale=70,moves=2)
for k,(x,y) in enumerate([(8,6),(9,6),(8,5),(9,5)]):slots[20+k].update(x=x,y=y,type=0,troops=1000,quality=5,morale=70)
for i,s in enumerate(slots):u.mem_write(0x4a0344+44*i,struct.pack('<10h',*[s[n] for n in names])+bytes(24))
u.mem_write(0x4a0a24,struct.pack('<168h',*[50]*168));u.mem_write(0x45e6ac,struct.pack('<h',20));u.mem_write(0x45e030,struct.pack('<I',1))
# FUN_0043AA60 receives its parent's captured horizontal-side flag through the stack static link.
u.mem_write(0x8ff000,struct.pack('<II',0x600000,0x8fe000));u.mem_write(0x8fdfff,b'\x00')
u.reg_write(UC_X86_REG_ESP,0x8ff000);u.reg_write(UC_X86_REG_EAX,0)
flank={}
def stop_walk(uc,address,size,data):
 packed=uc.reg_read(UC_X86_REG_EDX);flank.update(actor=uc.reg_read(UC_X86_REG_EAX)&65535,destination=[packed&65535,packed>>16]);uc.emu_stop()
h=u.hook_add(UC_HOOK_CODE,stop_walk,begin=0x438d24,end=0x438d24)
u.emu_start(0x43aa60,0x600000,count=100000);u.hook_del(h)
assert flank==dict(actor=0,destination=[3,3]),flank
out=root/'runs/experiments/data/run-exp-tactical25'/('original-threat-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S')+'.json')
record=dict(provenance='Pinned original x86 under Unicorn on contemporaneous model inputs; not original runtime traces or full replay',source='FUN_0043A718; full pure helper with original line/box helpers, no stubs',phases=str(a.phases.name),exe_sha256=hashlib.sha256(raw).hexdigest(),dat_sha256=hashlib.sha256(dat).hexdigest(),minimal_sort=minimal,minimal_archer_subject=archer_subject,minimal_flank_equal_y=flank,pass_two=pass_two,rows=rows)
with out.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(out,'rows',len(rows),'different aims',sum(r['aim_differs'] for r in rows));print([r for r in rows if r['trial']=='mix-rg_s1_r5_hook'])
