"""Audit scalar results and verify observers against unobserved original runs.

Raw traces/stack bytes/hash manifest stay private. Never overwrite evidence.
"""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'runs/experiments/navigation187'));import core as C
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EAX,UC_X86_REG_EIP
DATA=ROOT/'runs/experiments/data/run-exp-navigation187-callers';PRIVATE=ROOT/'artifacts/run-exp-navigation187-callers/private'
p=argparse.ArgumentParser();p.add_argument('--version',required=True);options=p.parse_args()
load=lambda n:json.loads((DATA/n).read_text())
iso=load('controls-v1.json');parent=load('parent-controls-v1.json');history=load('history-controls-v1.json');progress=load('progress-controls-v1.json')
assert len(iso)==len(parent)==24 and len(history)==32 and len(progress)==8
for r in iso:
 e=r['entries'][0];assert e['byte_provenance']==[None,None]
 assert e['entry_guard']=={0:0,1:257,255:-1}[r['stack_fill']]
 expected=(108,40) if not r['blocked'] else (100,40) if r['stack_fill']==255 else (100,41)
 assert r['endpoint']==list(expected) and r['moves']==(8 if r['blocked'] and r['stack_fill']==255 else 0)
for r in parent:
 target=next(e for e in r['entries'] if e['return_address'] in ['0x44ec82','0x44ecdb','0x44e918'])
 assert target['entry_guard']==(0 if r['context']=='mercenary' else 40)
 assert r['endpoint']==([100,40] if r['blocked'] else [109,40]) and r['moves']==0
for r in history:
 e=next(e for e in r['entries'] if e['return_address'] in ['0x44ec82','0x44ecdb'])
 assert e['entry_guard']==(-1 if r['offers'] else 0)
 assert e['byte_provenance'][0]['instruction']==('0x44db47' if r['offers'] else '0x44efa7')
 if r['blocked']:assert r['endpoint']==[150,70] and r['moves']==(9 if r['offers'] else 0)
 else:assert r['endpoint']==([154,70] if r['context']=='garrison-nearest' else [159,70])
for r in progress:
 e=next(e for e in r['entries'] if e['return_address'] in ['0x44ec82','0x44ecdb'])
 assert e['entry_guard']==(-1 if r['offers'] else 0)
 assert r['endpoint']==([152,70] if r['offers'] else [152,71]) and r['moves']==(7 if r['offers'] else -1)
# Pair proof: the sole original game-input difference is the mercenary troop word.
pairs=[]
for prefix,group in [('history-v1',history),('progress-v1',progress)]:
 for a in [r for r in group if not r['offers']]:
  b=next(r for r in group if r['offers'] and all(r[k]==a[k] for k in ['context','blocked','stack_fill','stack_top']))
  raw_a=(PRIVATE/prefix/a['case']/'before.ram').read_bytes();raw_b=(PRIVATE/prefix/b['case']/'before.ram').read_bytes()
  diff=[C.ORIGIN+i for i,(x,y) in enumerate(zip(raw_a,raw_b)) if x!=y];assert diff==[0x49da18,0x49da19]
  pairs.append(dict(group=prefix,absent=a['case'],present=b['case'],only_game_input_difference='mercenary0 troop signed WORD at49DA18',differing_bytes=2))
# Rerun every case with NO observation hooks. Compare complete game RAM and all
# stack bytes against the observed write log applied to the initial stack.
identities=[]
for prefix,rows in [('controls-v1',iso),('parent-v1',parent),('history-v1',history),('progress-v1',progress)]:
 for r in rows:
  folder=PRIVATE/prefix/r['case'];before=(folder/'before.ram').read_bytes();after=(folder/'after.ram').read_bytes();trace=json.loads((folder/'trace.json').read_text())
  base=r['stack_top']&~0xffff;stack=bytearray(bytes([r['stack_fill']])*0x10000);struct.pack_into('<I',stack,r['stack_top']-base,0x600000)
  initial=bytes(stack)
  for w in trace['stack_writes']:stack[w['address']-base:w['address']-base+w['size']]=(w['value']&((1<<(8*w['size']))-1)).to_bytes(w['size'],'little')
  u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x300000);u.mem_map(base,0x10000)
  for va,rp,rs in C.SECTIONS:
   if rs:u.mem_write(va,C.EXE[rp:rp+rs])
  u.mem_write(C.ORIGIN,before);u.mem_write(base,initial);u.reg_write(UC_X86_REG_ESP,r['stack_top']);u.reg_write(UC_X86_REG_EAX,2)
  entry=0x44f31c if prefix!='controls-v1' else 0x44e84c if r['context']=='mercenary' else 0x44ebe8
  u.emu_start(entry,0x600000,count=5000000)
  assert u.reg_read(UC_X86_REG_EIP)==0x600000 and bytes(u.mem_read(C.ORIGIN,C.SIZE))==after and bytes(u.mem_read(base,0x10000))==bytes(stack)
  identities.append(dict(group=prefix,case=r['case'],whole_game_RAM_equal=True,whole_stack_equal=True))
summary=dict(isolated_caller_controls=len(iso),full_F31C_parent_controls=len(parent)+len(history)+len(progress),total_controls=len(identities),complete_original_RNG_calls=0,observer_plain_RAM_and_stack_matches=len(identities),single_WORD_offer_pairs=len(pairs),garrison_negative_guard_is_reachable_in_F31C=True,no_universal_zero_initialization=True,progress_then_block_controls=8,original_signed_budget_minus1_observed=True,remaining_limits=['arbitrary standalone caller roots still undefined','not all homeland/interception/combat/embarked callers or every earlier route history','no native caller implementation/parity or whole End turn comparison','Research intake before broadening Main scope'])
for name,value in [('summary',summary),('paired-inputs',pairs),('observer-identity',identities)]:
 with (DATA/(name+'-'+options.version+'.json')).open('x') as f:json.dump(value,f,indent=2)
print(json.dumps(summary))
