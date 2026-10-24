"""Same retained private boundary: original scores and actual F31C branch.

Only scalar score/branch facts leave private artifacts. No owner hashes/paths,
raw RAM/SAV/full trace in public outputs. Unmodified instructions, no stubs.
"""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'runs/experiments/navigation187'));import core as C
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
D=ROOT/'runs/experiments/data/run-exp-city-army187';P=ROOT/'artifacts/run-exp-city-army187/private'
p=argparse.ArgumentParser();p.add_argument('--version',required=True);p.add_argument('--ram',type=Path,required=True);p.add_argument('--container',type=Path,required=True);p.add_argument('--decoded',type=Path,required=True);a=p.parse_args();out=P/('original-'+a.version);out.mkdir(exist_ok=False)
raw=a.ram.read_bytes();actor=4;ARMY=0x47c1ec+actor*656
assert C.xy(raw,ARMY)==[219,93]
def write(path,value):
 with path.open('x') as f:json.dump(value,f,indent=2)
def score(entry,scored):
 r=C.run(entry,actor,0x80a000,0x80a004,(0x80a008,),ram=raw)
 return dict(target=r['words'][0],score=r['words'][2] if scored else None,distance=r['words'][4] if scored else None)
city=score(0x44ece4,True);enemy=score(0x44ee60,True);supply=score(0x44e670,False)
def branch(full):
 u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x300000);u.mem_map(0x800000,0x10000)
 for va,rp,rs in C.SECTIONS:
  if rs:u.mem_write(va,C.EXE[rp:rp+rs])
 u.mem_write(C.ORIGIN,raw);sp=0x80f000
 if not full:u.mem_write(sp,struct.pack('<7h',supply['target'],city['target'],enemy['target'],enemy['score'],city['score'],enemy['distance'],city['distance']))
 for reg,val in [(UC_X86_REG_ESP,sp),(UC_X86_REG_EBX,ARMY),(UC_X86_REG_ESI,actor)]:u.reg_write(reg,val)
 calls=[];rng=[]
 def hook(uc,address,size,user):
  if address==0x40284c:rng.append(address);uc.emu_stop()
  if address in [0x44dba8,0x44e84c]:
   ret=struct.unpack('<I',uc.mem_read(uc.reg_read(UC_X86_REG_ESP),4))[0];site=ret-5
   words=list(struct.unpack('<7h',uc.mem_read(uc.reg_read(UC_X86_REG_ESP)+4,14)))
   calls.append(dict(site=hex(site),goal=list(struct.unpack('<2h',struct.pack('<I',uc.reg_read(UC_X86_REG_EDX)))),actor=uc.reg_read(UC_X86_REG_EAX)&65535,words=words));uc.emu_stop()
 u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x44f387 if full else 0x44f3b8,0x44f4cc,count=5000000)
 assert calls and not rng and bytes(u.mem_read(C.ORIGIN,C.SIZE))==raw
 write(out/('sequence.json' if full else 'branch.json'),calls)
 site=calls[0]['site'];kind={'0x44f409':'AttackArmy','0x44f43f':'AttackCity','0x44f47c':'MoveToResupplyCity','0x44f485':'MercenaryRun'}[site]
 return dict(kind=kind,call_site=site,actor_matches=calls[0]['actor']==actor,recorded_enemy_destination_matches=calls[0]['goal']==[191,95])
separate=branch(False);sequence=branch(True);assert separate==sequence
# Keep complete per-city score inputs/private owner state out of public outputs.
candidates=[];nation=C.short(raw,ARMY+4)
for i in range(334):
 addr=0x479590+i*34;owner=C.short(raw,addr+18)
 if C.short(raw,0x474670+nation*1172+0x26+2*owner)!=3:continue
 pos=tuple(C.xy(raw,addr+14));eligible=bool(C.run(0x44cab4,actor,C.point(pos),ram=raw)['eax']&255)
 defense=C.run(0x44a98c,i,ram=raw)['eax'];defense=defense if defense<2**31 else defense-2**32
 candidates.append(dict(index=i,eligible=eligible,defense=defense,geography=C.classify(raw,pos),capital=any(C.short(raw,0x474670+n*1172+0x444)==i for n in range(16))))
write(out/'city-inputs.json',candidates)
assault=C.run(0x44a930,actor,ram=raw)['eax']
result=dict(original_city=city,original_enemy=enemy,original_branch=separate,scorer_sequence_branch=sequence,read_only_complete_RAM_identity=True,original_RNG_calls=0,original_assault_strength=assault,scope='same retained private pre-command state; stopped before movement; no whole End turn claim')
write(D/('original-scalar-'+a.version+'.json'),result)
# Reuse previously verified diagnostic container only; owner identity stays private.
for name,source in [('before.SAV',a.container),('before.json',a.decoded)]:
 with (out/name).open('xb') as f:f.write(source.read_bytes())
with (out/'input.ram').open('xb') as f:f.write(raw)
print('PASS original city/army scorers and actual F31C scorer-to-branch sequence; private material retained locally')
